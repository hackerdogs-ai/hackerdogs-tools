#!/usr/bin/env python3
"""
Comprehensive review of all OSINT tools and tests for bugs.
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Tuple

def check_tool_file(file_path: Path) -> List[str]:
    """Check a tool file for common bugs."""
    issues = []
    try:
        content = file_path.read_text()
        
        # Check 1: Must have @tool decorator
        if '@tool' not in content:
            issues.append("Missing @tool decorator")
        
        # Check 2: Must have runtime parameter
        if 'runtime: ToolRuntime' not in content:
            issues.append("Missing runtime: ToolRuntime parameter")
        
        # Check 3: Must return JSON string
        if 'json.dumps' not in content and 'return json.dumps' not in content:
            issues.append("May not return JSON string")
        
        # Check 4: Must have try/except
        if 'try:' not in content:
            issues.append("Missing try/except error handling")
        
        # Check 5: Must use hd_logging
        if 'from hd_logging import' not in content and 'hd_logging' not in content:
            issues.append("Not using hd_logging")
        
        # Check 6: Must import execute_in_docker or have docker client
        if 'execute_in_docker' not in content and 'docker_client' not in content.lower():
            if 'infrastructure' in str(file_path) or 'content' in str(file_path):
                issues.append("May be missing Docker execution")
        
        # Check 7: Check for common syntax errors
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
        
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    
    return issues

def check_test_file(file_path: Path) -> List[str]:
    """Check a test file for common bugs."""
    issues = []
    try:
        content = file_path.read_text()
        
        # Check 1: Must import tool function
        tool_name = file_path.stem.replace('test_', '')
        if f'from hackerdogs_tools.osint' not in content:
            issues.append("Missing tool import")
        
        # Check 2: Must have 3 test classes
        test_classes = re.findall(r'class Test\w+', content)
        if len(test_classes) < 3:
            issues.append(f"Expected 3 test classes, found {len(test_classes)}")
        
        # Check 3: Must use get_random_domain for domain tests
        if 'domain' in content.lower() and 'get_random_domain' not in content:
            issues.append("Should use get_random_domain() for domain tests")
        
        # Check 4: Must not use AgentExecutor (LangChain 1.x)
        if 'AgentExecutor' in content:
            issues.append("Should not use AgentExecutor (LangChain 1.x)")
        
        # Check 5: Check for undefined variables
        if 'test_domain' in content:
            # Check if it's defined before use in each method
            methods = re.finditer(r'def test_\w+\([^)]*\):', content)
            for method in methods:
                method_start = method.end()
                next_method = re.search(r'\n    def |\nclass ', content[method_start:])
                method_end = method_start + (next_method.start() if next_method else len(content[method_start:]))
                method_content = content[method_start:method_end]
                
                if 'test_domain' in method_content and 'test_domain = get_random_domain()' not in method_content:
                    before_content = content[:method_start]
                    if 'test_domain = get_random_domain()' not in before_content:
                        issues.append(f"test_domain used but not defined in {method.group(0)}")
        
        # Check 6: Syntax check
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
        
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    
    return issues

def main():
    """Review all tools and tests."""
    osint_dir = Path("hackerdogs_tools/osint")
    
    tool_issues = {}
    test_issues = {}
    
    # Review all tool files
    for langchain_file in osint_dir.rglob("*_langchain.py"):
        if 'test' in str(langchain_file) or 'docker' in str(langchain_file):
            continue
        issues = check_tool_file(langchain_file)
        if issues:
            tool_issues[str(langchain_file)] = issues
    
    # Review all test files
    for test_file in (osint_dir / "tests").glob("test_*.py"):
        issues = check_test_file(test_file)
        if issues:
            test_issues[str(test_file)] = issues
    
    # Print results
    print("=" * 80)
    print("TOOL FILES REVIEW")
    print("=" * 80)
    if tool_issues:
        for file, issues in tool_issues.items():
            print(f"\n❌ {file}:")
            for issue in issues:
                print(f"   - {issue}")
    else:
        print("✅ No issues found in tool files")
    
    print("\n" + "=" * 80)
    print("TEST FILES REVIEW")
    print("=" * 80)
    if test_issues:
        for file, issues in test_issues.items():
            print(f"\n❌ {file}:")
            for issue in issues:
                print(f"   - {issue}")
    else:
        print("✅ No issues found in test files")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(tool_issues)} tool files with issues, {len(test_issues)} test files with issues")
    print("=" * 80)

if __name__ == "__main__":
    main()

