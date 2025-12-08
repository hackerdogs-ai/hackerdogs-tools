#!/usr/bin/env python3
"""
SpiderFoot Module Code Generator

Generates LangChain and CrewAI tools from SpiderFoot modules using Jinja2 templates.

Usage:
    python generate_spiderfoot_tools.py [--spiderfoot-path PATH] [--dry-run] [--modules MODULE1,MODULE2]
"""

import ast
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import jinja2
from hd_logging import setup_logger

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_generator.log")


class SpiderFootModuleParser:
    """Parser for SpiderFoot module files to extract metadata."""
    
    def __init__(self, spiderfoot_root: str):
        """
        Initialize parser with SpiderFoot root directory.
        
        Args:
            spiderfoot_root: Path to SpiderFoot root directory
        """
        self.spiderfoot_root = Path(spiderfoot_root)
        self.modules_dir = self.spiderfoot_root / "modules"
        
        if not self.modules_dir.exists():
            raise ValueError(f"SpiderFoot modules directory not found: {self.modules_dir}")
    
    def find_modules(self) -> List[str]:
        """Find all SpiderFoot module files."""
        modules = []
        for file in self.modules_dir.glob("sfp_*.py"):
            if file.name.startswith("sfp__"):  # Skip internal modules
                continue
            modules.append(file.stem)  # e.g., "sfp_dnsbrute"
        return sorted(modules)
    
    def parse_module_file(self, module_name: str) -> Dict[str, Any]:
        """
        Parse a SpiderFoot module file to extract metadata.
        
        Args:
            module_name: Module name (e.g., "sfp_dnsbrute")
            
        Returns:
            Dictionary with extracted metadata
        """
        module_file = self.modules_dir / f"{module_name}.py"
        
        if not module_file.exists():
            raise FileNotFoundError(f"Module file not found: {module_file}")
        
        try:
            # Read and parse Python file
            with open(module_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(module_file))
            
            # Extract metadata
            metadata = {
                'module_name': module_name,
                'module_class_name': None,
                'meta': {},
                'opts': {},
                'optdescs': {},
                'watched_events': [],
                'produced_events': [],
                'has_api_key': False,
                'api_key_name': None
            }
            
            # Find the module class
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it inherits from SpiderFootPlugin
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == 'SpiderFootPlugin':
                            metadata['module_class_name'] = node.name
                            
                            # Extract class attributes
                            for item in node.body:
                                if isinstance(item, ast.Assign):
                                    # Extract meta dict
                                    if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                                        if item.targets[0].id == 'meta':
                                            metadata['meta'] = self._extract_dict(item.value)
                                        
                                        # Extract opts dict
                                        elif item.targets[0].id == 'opts':
                                            metadata['opts'] = self._extract_dict(item.value)
                                        
                                        # Extract optdescs dict
                                        elif item.targets[0].id == 'optdescs':
                                            metadata['optdescs'] = self._extract_dict(item.value)
                                
                                # Extract methods
                                elif isinstance(item, ast.FunctionDef):
                                    if item.name == 'watchedEvents':
                                        metadata['watched_events'] = self._extract_list_from_method(item)
                                    elif item.name == 'producedEvents':
                                        metadata['produced_events'] = self._extract_list_from_method(item)
            
            # Check for API key requirement
            if 'flags' in metadata['meta'] and 'apikey' in metadata['meta'].get('flags', []):
                metadata['has_api_key'] = True
                # Find API key option name
                for opt_name in metadata['opts'].keys():
                    if 'api' in opt_name.lower() and 'key' in opt_name.lower():
                        metadata['api_key_name'] = opt_name
                        break
                if not metadata['api_key_name']:
                    metadata['api_key_name'] = 'api_key'  # Default
            
            # Extract short module name (remove sfp_ prefix)
            if metadata['module_name'].startswith('sfp_'):
                metadata['short_name'] = metadata['module_name'][4:]  # Remove "sfp_" prefix
            else:
                metadata['short_name'] = metadata['module_name']
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error parsing module {module_name}: {str(e)}", exc_info=True)
            raise
    
    def _extract_dict(self, node: ast.AST) -> Dict[str, Any]:
        """Extract dictionary from AST node."""
        if isinstance(node, ast.Dict):
            result = {}
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant):
                    key_str = key.value
                elif isinstance(key, ast.Str):  # Python < 3.8
                    key_str = key.s
                else:
                    continue
                
                if isinstance(value, ast.Constant):
                    result[key_str] = value.value
                elif isinstance(value, ast.Str):  # Python < 3.8
                    result[key_str] = value.s
                elif isinstance(value, ast.Num):  # Python < 3.8
                    result[key_str] = value.n
                elif isinstance(value, ast.NameConstant):  # Python < 3.8
                    result[key_str] = value.value
                elif isinstance(value, ast.List):
                    result[key_str] = self._extract_list(value)
                elif isinstance(value, ast.Dict):
                    result[key_str] = self._extract_dict(value)
                else:
                    result[key_str] = None
            return result
        return {}
    
    def _extract_list(self, node: ast.List) -> List[Any]:
        """Extract list from AST node."""
        result = []
        for elt in node.elts:
            if isinstance(elt, ast.Constant):
                result.append(elt.value)
            elif isinstance(elt, ast.Str):  # Python < 3.8
                result.append(elt.s)
            elif isinstance(elt, ast.Num):  # Python < 3.8
                result.append(elt.n)
        return result
    
    def _extract_list_from_method(self, node: ast.FunctionDef) -> List[str]:
        """Extract return list from method (watchedEvents/producedEvents)."""
        for item in node.body:
            if isinstance(item, ast.Return) and item.value:
                if isinstance(item.value, ast.List):
                    return self._extract_list(item.value)
                elif isinstance(item.value, ast.Name):
                    # Variable reference - try to find it
                    var_name = item.value.id
                    # Look for assignment to this variable
                    for stmt in node.body:
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Name) and target.id == var_name:
                                    if isinstance(stmt.value, ast.List):
                                        return self._extract_list(stmt.value)
        return []


class SpiderFootToolGenerator:
    """Generator for SpiderFoot LangChain and CrewAI tools."""
    
    def __init__(self, templates_dir: Path, output_dir: Path):
        """
        Initialize generator.
        
        Args:
            templates_dir: Directory containing Jinja2 templates
            output_dir: Directory to write generated tools
        """
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        
        # Setup Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Load templates
        self.langchain_template = self.env.get_template('spiderfoot_langchain_tool.j2')
        self.crewai_template = self.env.get_template('spiderfoot_crewai_tool.j2')
        self.test_template = self.env.get_template('spiderfoot_test.j2')
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_python_type(self, value: Any) -> str:
        """Get Python type string for a value."""
        if value is None:
            return "Optional[Any]"
        elif isinstance(value, bool):  # Check bool BEFORE int (bool is subclass of int)
            return "Optional[bool]"
        elif isinstance(value, str):
            return "Optional[str]"
        elif isinstance(value, int):
            return "Optional[int]"
        elif isinstance(value, float):
            return "Optional[float]"
        elif isinstance(value, list):
            return "Optional[List[Any]]"
        elif isinstance(value, dict):
            return "Optional[Dict[str, Any]]"
        else:
            return "Optional[Any]"
    
    def _prepare_opts_for_template(self, opts: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Prepare opts dict with type information for template."""
        prepared = {}
        for opt_name, opt_value in opts.items():
            # Convert to Python literal string for template
            if isinstance(opt_value, bool):
                python_value = "True" if opt_value else "False"
            elif opt_value is None:
                python_value = "None"
            elif isinstance(opt_value, str):
                python_value = json.dumps(opt_value)  # Keep strings as JSON strings for quotes
            else:
                python_value = str(opt_value)  # Numbers and other types as literals
            
            prepared[opt_name] = {
                'value': opt_value,
                'type': self._get_python_type(opt_value),
                'json_value': python_value
            }
        return prepared
    
    def generate_tool(self, metadata: Dict[str, Any], dry_run: bool = False, generate_test: bool = True) -> Tuple[str, str, Optional[str]]:
        """
        Generate LangChain and CrewAI tools from module metadata.
        
        Args:
            metadata: Module metadata from parser
            dry_run: If True, don't write files, just return code
            generate_test: If True, also generate test file
            
        Returns:
            Tuple of (langchain_code, crewai_code, test_code)
        """
        # Prepare opts with type information
        prepared_opts = self._prepare_opts_for_template(metadata['opts'])
        
        # Prepare template context
        context = {
            'module_name': metadata['short_name'],
            'module_class_name': metadata['module_class_name'],
            'meta': metadata['meta'],
            'opts': metadata['opts'],  # Keep original for compatibility
            'prepared_opts': prepared_opts,  # New: with type info
            'optdescs': metadata['optdescs'],
            'watched_events': metadata['watched_events'],
            'produced_events': metadata['produced_events'],
            'has_api_key': metadata['has_api_key'],
            'api_key_name': metadata.get('api_key_name', 'api_key')
        }
        
        # Render templates
        langchain_code = self.langchain_template.render(**context)
        crewai_code = self.crewai_template.render(**context)
        test_code = None
        
        if generate_test:
            test_code = self.test_template.render(**context)
        
        if not dry_run:
            # Write files
            langchain_file = self.output_dir / f"{metadata['module_name']}_langchain.py"
            crewai_file = self.output_dir / f"{metadata['module_name']}_crewai.py"
            
            langchain_file.write_text(langchain_code, encoding='utf-8')
            crewai_file.write_text(crewai_code, encoding='utf-8')
            
            logger.info(f"Generated: {langchain_file.name} and {crewai_file.name}")
            
            # Write test file if requested
            if generate_test and test_code:
                # Test files go in hackerdogs_tools/osint/tests/
                test_output_dir = Path(__file__).parent / "tests"
                test_output_dir.mkdir(parents=True, exist_ok=True)
                test_file = test_output_dir / f"test_{metadata['module_name']}.py"
                test_file.write_text(test_code, encoding='utf-8')
                logger.info(f"Generated: {test_file.name}")
        
        return langchain_code, crewai_code, test_code


def main():
    """Main entry point for code generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate SpiderFoot LangChain/CrewAI tools')
    parser.add_argument(
        '--spiderfoot-path',
        type=str,
        default='/Users/tejaswiredkar/Documents/GitHub/spiderfoot',
        help='Path to SpiderFoot root directory'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for generated tools (default: hackerdogs_tools/osint/spiderfoot_modules)'
    )
    parser.add_argument(
        '--templates-dir',
        type=str,
        default=None,
        help='Templates directory (default: hackerdogs_tools/osint/templates)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - generate code but don\'t write files'
    )
    parser.add_argument(
        '--modules',
        type=str,
        default=None,
        help='Comma-separated list of specific modules to generate (e.g., sfp_dnsbrute,sfp_abuseipdb)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup paths
    script_dir = Path(__file__).parent
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = script_dir / "spiderfoot_modules"
    
    if args.templates_dir:
        templates_dir = Path(args.templates_dir)
    else:
        templates_dir = script_dir / "templates"
    
    # Initialize parser and generator
    try:
        parser_obj = SpiderFootModuleParser(args.spiderfoot_path)
        generator = SpiderFootToolGenerator(templates_dir, output_dir)
        
        # Find modules
        if args.modules:
            module_names = [m.strip() for m in args.modules.split(',')]
        else:
            module_names = parser_obj.find_modules()
        
        logger.info(f"Found {len(module_names)} modules to process")
        
        # Generate tools
        success_count = 0
        error_count = 0
        
        for module_name in module_names:
            try:
                logger.info(f"Processing module: {module_name}")
                
                # Parse module
                metadata = parser_obj.parse_module_file(module_name)
                
                if args.verbose:
                    logger.info(f"  Meta: {metadata['meta'].get('name', 'N/A')}")
                    logger.info(f"  Watched Events: {metadata['watched_events']}")
                    logger.info(f"  Produced Events: {metadata['produced_events']}")
                    logger.info(f"  Has API Key: {metadata['has_api_key']}")
                
                # Generate tools and test
                generator.generate_tool(metadata, dry_run=args.dry_run, generate_test=True)
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {module_name}: {str(e)}", exc_info=True)
                error_count += 1
        
        logger.info(f"Generation complete: {success_count} succeeded, {error_count} failed")
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No files were written")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

