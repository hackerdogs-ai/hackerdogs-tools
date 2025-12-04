"""
Script to generate OSINT tool files from templates.

This script generates LangChain and CrewAI tool files for all OSINT tools
based on the patterns established in the PRD.
"""

import os
from pathlib import Path

# Tool definitions
TOOLS = {
    'infrastructure': [
        ('masscan', 'Masscan', 'Fast Internet port scanner', 'ip_range:str, ports:str, rate:int=1000'),
        ('zmap', 'ZMap', 'Single-packet scanning', 'ip_range:str, port:int, bandwidth:str'),
        ('theharvester', 'TheHarvester', 'Gathers emails, subdomains, hosts from search engines', 'domain:str, sources:Optional[List[str]], limit:int=500'),
        ('dnsdumpster', 'DNSDumpster', 'DNS mapping via DNSDumpster', 'domain:str'),
    ],
    'identity': [
        ('sherlock', 'Sherlock', 'Username enumeration across 300+ sites', 'username:str, sites:Optional[List[str]], timeout:int=60'),
        ('maigret', 'Maigret', 'Advanced username search with metadata', 'username:str, extract_metadata:bool=True, sites:Optional[List[str]]'),
        ('ghunt', 'GHunt', 'Google Account investigation', 'email:str, extract_reviews:bool=True, extract_photos:bool=False'),
        ('holehe', 'Holehe', 'Check email registration on 120+ sites', 'email:str, only_used:bool=True'),
    ],
    'content': [
        ('scrapy', 'Scrapy', 'Custom web scraping framework', 'url:str, spider_name:str="generic", follow_links:bool=False, max_pages:int=10'),
        ('waybackurls', 'Waybackurls', 'Fetch URLs from Wayback Machine', 'domain:str, no_subs:bool=False, dates:Optional[str]'),
        ('onionsearch', 'OnionSearch', 'Scrape Dark Web search engines', 'query:str, engines:Optional[List[str]], max_results:int=50'),
    ],
    'threat_intel': [
        ('urlhaus', 'URLHaus', 'Check if URL is in malicious database', 'url:str, download_feed:bool=False'),
        ('abuseipdb', 'AbuseIPDB', 'IP reputation and abuse checking', 'ip:str, max_age_in_days:int=90, verbose:bool=True'),
    ],
    'metadata': [
        ('exiftool', 'ExifTool', 'Extract metadata from images/PDFs', 'file_path:str, extract_gps:bool=True, extract_author:bool=True'),
        ('yara', 'YARA', 'Pattern matching for malware classification', 'file_path:str, rules_path:str, rules_content:Optional[str]'),
    ],
    'frameworks': [
        ('spiderfoot', 'SpiderFoot', 'Comprehensive OSINT framework', 'target:str, target_type:str, modules:Optional[List[str]], scan_type:str="footprint"'),
    ],
}

LANGCHAIN_TEMPLATE = '''"""
{name} Tool for LangChain Agents

{description}
"""

import json
import subprocess
import shutil
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/{module}_tool.log")


class {Name}SecurityAgentState(AgentState):
    """Extended agent state for {Name} operations."""
    user_id: str = ""


def _check_{module}_installed() -> bool:
    """Check if {Name} binary/package is installed."""
    return shutil.which("{module}") is not None or True  # Adjust based on tool type


@tool
def {module}_{action}(
    runtime: ToolRuntime,
    {params}
) -> str:
    """
    {description}
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        {param_docs}
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[{module}_{action}] Starting", {log_params})
        
        if not _check_{module}_installed():
            error_msg = "{Name} not found. Please install it."
            safe_log_error(logger, error_msg)
            return json.dumps({{"status": "error", "message": error_msg}})
        
        # TODO: Implement tool-specific logic
        # This is a template - implement actual tool execution
        
        result_data = {{
            "status": "success",
            "message": "Tool execution not yet implemented",
            "user_id": runtime.state.get("user_id", "")
        }}
        
        safe_log_info(logger, f"[{module}_{action}] Complete")
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        safe_log_error(logger, f"[{module}_{action}] Error: {{str(e)}}", exc_info=True)
        return json.dumps({{"status": "error", "message": str(e)}})
'''

CREWAI_TEMPLATE = '''"""
{Name} Tool for CrewAI Agents

{description}
"""

import json
import subprocess
import shutil
from typing import Any, Optional, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/{module}_tool.log")


class {Name}ToolSchema(BaseModel):
    """Input schema for {Name}Tool."""
    {schema_fields}


class {Name}Tool(BaseTool):
    """Tool for {description}."""
    
    name: str = "{Name}"
    description: str = "{description}"
    args_schema: type[BaseModel] = {Name}ToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Add validation if needed
        # if not shutil.which("{module}"):
        #     raise ValueError("{Name} not found. Please install it.")
    
    def _run(
        self,
        {params},
        **kwargs: Any
    ) -> str:
        """Execute {Name}."""
        try:
            safe_log_info(logger, f"[{Name}Tool] Starting", {log_params})
            
            # TODO: Implement tool-specific logic
            # This is a template - implement actual tool execution
            
            result_data = {{
                "status": "success",
                "message": "Tool execution not yet implemented"
            }}
            
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[{Name}Tool] Error: {{str(e)}}", exc_info=True)
            return json.dumps({{"status": "error", "message": str(e)}})
'''

def parse_params(param_string: str) -> tuple:
    """Parse parameter string into fields and docs."""
    # Simple parser - can be enhanced
    params = []
    param_docs = []
    schema_fields = []
    log_params = []
    
    for param in param_string.split(','):
        param = param.strip()
        if ':' in param:
            name, type_val = param.split(':', 1)
            name = name.strip()
            type_val = type_val.strip()
            
            # Extract default value
            if '=' in type_val:
                type_part, default_part = type_val.split('=', 1)
                default_val = default_part.strip()
                has_default = True
            else:
                type_part = type_val
                default_val = None
                has_default = False
            
            params.append(f"{name}: {type_part}" + (f" = {default_val}" if has_default else ""))
            param_docs.append(f"        {name}: {type_part.replace('Optional[', '').replace(']', '')} - Parameter description")
            
            # Schema field
            if has_default:
                schema_fields.append(f'    {name}: {type_part} = Field(default={default_val}, description="Parameter description")')
            else:
                schema_fields.append(f'    {name}: {type_part} = Field(..., description="Parameter description")')
            
            log_params.append(name)
    
    return '\n    '.join(params), '\n'.join(param_docs), '\n    '.join(schema_fields), ', '.join(log_params)


def generate_files():
    """Generate all tool files."""
    base_path = Path(__file__).parent
    
    for category, tools in TOOLS.items():
        category_path = base_path / category
        category_path.mkdir(exist_ok=True)
        
        for module, name, description, params in tools:
            # Parse parameters
            param_list, param_docs, schema_fields, log_params = parse_params(params)
            
            # Determine action name
            action = 'scan' if 'scan' in description.lower() else 'enum' if 'enum' in description.lower() else 'query' if 'query' in description.lower() else 'search'
            
            # Generate LangChain file
            langchain_content = LANGCHAIN_TEMPLATE.format(
                module=module,
                Name=name,
                name=name.lower(),
                description=description,
                action=action,
                params=param_list,
                param_docs=param_docs,
                log_params=log_params
            )
            
            langchain_file = category_path / f"{module}_langchain.py"
            if not langchain_file.exists():
                langchain_file.write_text(langchain_content)
                print(f"Created: {langchain_file}")
            
            # Generate CrewAI file
            crewai_content = CREWAI_TEMPLATE.format(
                module=module,
                Name=name,
                name=name.lower(),
                description=description,
                params=param_list,
                schema_fields=schema_fields,
                log_params=log_params
            )
            
            crewai_file = category_path / f"{module}_crewai.py"
            if not crewai_file.exists():
                crewai_file.write_text(crewai_content)
                print(f"Created: {crewai_file}")


if __name__ == "__main__":
    generate_files()
    print("\nTool file generation complete!")
    print("Note: Generated files are templates. Implement actual tool logic for each.")

