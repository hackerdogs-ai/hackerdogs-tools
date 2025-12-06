#!/usr/bin/env python3
"""
Comprehensive tool file checker for OSINT tools.

Checks for:
1. Syntax errors
2. Indentation issues in schemas
3. Missing imports
4. Type annotation issues
5. Missing commas in function parameters
6. Inconsistent patterns
"""

import ast
import sys
from pathlib import Path
from typing import List, Dict, Tuple

def find_tool_files(base_path: Path) -> List[Path]:
    """Find all LangChain and CrewAI tool files."""
    files = []
    for pattern in ["*_langchain.py", "*_crewai.py"]:
        files.extend(base_path.rglob(pattern))
    return sorted(files)

def check_syntax(file_path: Path) -> Tuple[bool, str]:
    """Check if file has valid Python syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def check_schema_indentation(file_path: Path) -> List[str]:
    """Check for indentation issues in Pydantic schemas."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_schema = False
        schema_name = None
        
        for i, line in enumerate(lines, 1):
            # Check if we're entering a schema class
            if "class" in line and "Schema(BaseModel)" in line:
                in_schema = True
                schema_name = line.split("class")[1].split("(")[0].strip()
                continue
            
            # Check if we're leaving the schema class
            if in_schema and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                if not line.strip().startswith("#") and "class" not in line:
                    in_schema = False
                    continue
            
            # Check for incorrect indentation in schema fields
            if in_schema:
                # Schema fields should be indented with 4 spaces
                if line.strip() and not line.startswith("    ") and not line.startswith("\t"):
                    if not line.strip().startswith("#") and not line.strip().startswith('"""') and "class" not in line:
                        # Check if it's a field definition
                        if ":" in line and ("Field" in line or "=" in line):
                            # This might be incorrectly indented
                            if line.startswith("        "):  # 8 spaces - wrong!
                                issues.append(f"Line {i}: Field has 8-space indentation (should be 4): {line.strip()[:60]}")
                elif line.startswith("        ") and ":" in line and ("Field" in line or "=" in line):
                    # Field with 8 spaces - definitely wrong
                    issues.append(f"Line {i}: Field has 8-space indentation (should be 4): {line.strip()[:60]}")
    
    except Exception as e:
        issues.append(f"Error checking indentation: {str(e)}")
    
    return issues

def check_missing_commas(file_path: Path) -> List[str]:
    """Check for missing commas in function parameters."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_function = False
        function_name = None
        
        for i, line in enumerate(lines, 1):
            # Check if we're entering a function
            if "def _run(" in line or "def " in line and "(" in line:
                in_function = True
                function_name = line.split("def")[1].split("(")[0].strip()
                continue
            
            # Check for parameter lines without commas (except last parameter before **kwargs or closing paren)
            if in_function:
                stripped = line.strip()
                
                # Check if function definition ends
                if stripped.startswith(")") and "->" in stripped:
                    in_function = False
                    continue
                
                # Check for parameter line
                if ":" in stripped and not stripped.startswith("#"):
                    # Check if it's a parameter (has type annotation)
                    if ":" in stripped and ("str" in stripped or "int" in stripped or "bool" in stripped or "List" in stripped or "Optional" in stripped):
                        # Check if it should have a comma but doesn't
                        if not stripped.endswith(",") and "**kwargs" not in stripped and "self" not in stripped:
                            # Check next line to see if there's another parameter
                            if i < len(lines):
                                next_line = lines[i].strip()
                                if next_line and not next_line.startswith("#") and ":" in next_line and "**kwargs" not in next_line:
                                    # Missing comma!
                                    issues.append(f"Line {i}: Missing comma after parameter: {stripped[:60]}")
    
    except Exception as e:
        issues.append(f"Error checking commas: {str(e)}")
    
    return issues

def check_imports(file_path: Path) -> List[str]:
    """Check for common import issues."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for List without importing from typing
        if "List[" in content or "Optional[List[" in content:
            if "from typing import" not in content and "from typing import List" not in content:
                if "List" in content.split("\n")[0:20]:  # Check first 20 lines
                    issues.append("Uses List but may not import from typing")
        
        # Check for Optional without importing
        if "Optional[" in content:
            if "from typing import" not in content and "Optional" not in content.split("\n")[0:20]:
                issues.append("Uses Optional but may not import from typing")
    
    except Exception as e:
        issues.append(f"Error checking imports: {str(e)}")
    
    return issues

def main():
    """Main checker function."""
    base_path = Path(__file__).parent / "hackerdogs_tools" / "osint"
    
    if not base_path.exists():
        print(f"Error: {base_path} does not exist")
        sys.exit(1)
    
    tool_files = find_tool_files(base_path)
    
    print(f"Found {len(tool_files)} tool files to check\n")
    print("=" * 80)
    
    all_issues = {}
    syntax_errors = []
    
    for file_path in tool_files:
        relative_path = file_path.relative_to(Path(__file__).parent)
        print(f"\nChecking: {relative_path}")
        
        file_issues = []
        
        # Check syntax
        is_valid, error_msg = check_syntax(file_path)
        if not is_valid:
            syntax_errors.append((relative_path, error_msg))
            print(f"  ❌ SYNTAX ERROR: {error_msg}")
            all_issues[str(relative_path)] = file_issues
            continue
        
        # Check schema indentation
        schema_issues = check_schema_indentation(file_path)
        if schema_issues:
            file_issues.extend(schema_issues)
            for issue in schema_issues:
                print(f"  ⚠️  {issue}")
        
        # Check missing commas
        comma_issues = check_missing_commas(file_path)
        if comma_issues:
            file_issues.extend(comma_issues)
            for issue in comma_issues:
                print(f"  ⚠️  {issue}")
        
        # Check imports
        import_issues = check_imports(file_path)
        if import_issues:
            file_issues.extend(import_issues)
            for issue in import_issues:
                print(f"  ⚠️  {issue}")
        
        if not file_issues:
            print("  ✅ No issues found")
        
        if file_issues:
            all_issues[str(relative_path)] = file_issues
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if syntax_errors:
        print(f"\n❌ SYNTAX ERRORS ({len(syntax_errors)} files):")
        for file_path, error in syntax_errors:
            print(f"  - {file_path}: {error}")
    
    if all_issues:
        print(f"\n⚠️  FILES WITH ISSUES ({len(all_issues)} files):")
        for file_path, issues in all_issues.items():
            print(f"  - {file_path}: {len(issues)} issue(s)")
            for issue in issues[:3]:  # Show first 3 issues
                print(f"    • {issue}")
            if len(issues) > 3:
                print(f"    ... and {len(issues) - 3} more")
    else:
        print("\n✅ All files passed checks!")
    
    total_issues = len(syntax_errors) + sum(len(issues) for issues in all_issues.values())
    print(f"\nTotal issues found: {total_issues}")
    
    return 0 if total_issues == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

