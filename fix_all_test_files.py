#!/usr/bin/env python3
"""
Fix all test files: syntax errors and update with CrewAI changes from subfinder.
"""

import re
from pathlib import Path

test_dir = Path("hackerdogs_tools/osint/tests")
subfinder_file = test_dir / "test_subfinder.py"
subfinder_content = subfinder_file.read_text()

# Get all test files to fix (excluding working ones)
test_files = sorted([f for f in test_dir.glob("test_*.py") 
                    if f.name not in ["__init__.py", "test_utils.py", "test_runtime_helper.py", 
                                     "test_subfinder.py", "test_all_tools.py"]])

print(f"Fixing {len(test_files)} test files...\n")

for test_file in test_files:
    print(f"Processing {test_file.name}...")
    content = test_file.read_text()
    original_content = content
    
    # Fix 1: Fix the invoke call syntax - find the problematic pattern
    # The error is: closing parenthesis ')' does not match opening parenthesis '{'
    # This happens when invoke({ is on one line but parameters span multiple lines incorrectly
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has the problematic pattern
        if '.invoke({' in line and 'runtime' in line:
            # Check if there's a mismatched brace issue
            # Look ahead to see the structure
            tool_match = re.search(r'(\w+)\.invoke\(', line)
            if tool_match:
                tool_name = tool_match.group(1)
                indent = len(line) - len(line.lstrip())
                
                # Check if the line has mismatched braces
                if line.count('{') > line.count('}'):
                    # This is the problematic line - fix it
                    # Extract what comes before invoke
                    before_invoke = line.split('.invoke(')[0]
                    # The rest should be parameters
                    after_invoke = line.split('.invoke(')[1] if '.invoke(' in line else ''
                    
                    # Check if it ends with ) but has unmatched {
                    if after_invoke.strip().endswith(')') and '{' in after_invoke:
                        # Split it properly
                        fixed_lines.append(before_invoke + f'{tool_name}.invoke({{')
                        # Extract parameters from the rest
                        params_part = after_invoke.rstrip(')').lstrip('{').strip()
                        if params_part:
                            # Split by comma but be careful with nested structures
                            # For now, just put runtime on one line and close properly
                            if 'runtime' in params_part:
                                fixed_lines.append(' ' * (indent + 4) + '"runtime": runtime,')
                            # Add other params if any
                            if ',' in params_part and 'runtime' in params_part:
                                other_params = params_part.split(',', 1)[1].strip()
                                if other_params:
                                    fixed_lines.append(' ' * (indent + 4) + other_params)
                            fixed_lines.append(' ' * indent + '})')
                        else:
                            fixed_lines.append(' ' * indent + '})')
                        i += 1
                        continue
        
        fixed_lines.append(line)
        i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Fix 2: Update with subfinder patterns for CrewAI and other fixes
    # Replace the test methods with the working versions from subfinder
    
    # Get tool name from filename
    tool_name = test_file.stem.replace('test_', '')
    
    # Extract sections from subfinder
    # Standalone test
    standalone_match = re.search(
        r'(    def test_standalone\(self\):.*?)(?=\n    def |\nclass |\Z)',
        subfinder_content,
        re.DOTALL
    )
    
    # LangChain test
    langchain_match = re.search(
        r'(    def test_langchain_agent\(self, agent\):.*?)(?=\n    def |\nclass |\Z)',
        subfinder_content,
        re.DOTALL
    )
    
    # CrewAI test  
    crewai_match = re.search(
        r'(    def test_crewai_agent\(self, agent\):.*?)(?=\n    def |\nclass |\Z)',
        subfinder_content,
        re.DOTALL
    )
    
    # Run all tests function
    run_all_match = re.search(
        r'(def run_all_tests\(\):.*?)(?=\n\Z|\ndef |\nclass )',
        subfinder_content,
        re.DOTALL
    )
    
    if standalone_match:
        standalone_section = standalone_match.group(1)
        # Replace tool-specific names
        standalone_section = standalone_section.replace('subfinder_enum', f'{tool_name}_enum')
        standalone_section = standalone_section.replace('SubfinderTool', f'{tool_name.title()}Tool')
        standalone_section = standalone_section.replace('subfinder', tool_name)
        standalone_section = standalone_section.replace('Subfinder', tool_name.title())
        
        # Replace in content
        pattern = r'    def test_standalone\(self\):.*?(?=\n    def |\nclass |\Z)'
        content = re.sub(pattern, standalone_section, content, flags=re.DOTALL)
    
    if langchain_match:
        langchain_section = langchain_match.group(1)
        langchain_section = langchain_section.replace('subfinder_enum', f'{tool_name}_enum')
        langchain_section = langchain_section.replace('Subfinder', tool_name.title())
        langchain_section = langchain_section.replace('subfinder', tool_name)
        
        pattern = r'    def test_langchain_agent\(self, agent\):.*?(?=\n    def |\nclass |\Z)'
        content = re.sub(pattern, langchain_section, content, flags=re.DOTALL)
    
    if crewai_match:
        crewai_section = crewai_match.group(1)
        crewai_section = crewai_section.replace('SubfinderTool', f'{tool_name.title()}Tool')
        crewai_section = crewai_section.replace('subfinder', tool_name)
        crewai_section = crewai_section.replace('Subfinder', tool_name.title())
        
        pattern = r'    def test_crewai_agent\(self, agent\):.*?(?=\n    def |\nclass |\Z)'
        content = re.sub(pattern, crewai_section, content, flags=re.DOTALL)
    
    if run_all_match:
        run_all_section = run_all_match.group(1)
        run_all_section = run_all_section.replace('subfinder_enum', f'{tool_name}_enum')
        run_all_section = run_all_section.replace('SubfinderTool', f'{tool_name.title()}Tool')
        run_all_section = run_all_section.replace('subfinder', tool_name)
        run_all_section = run_all_section.replace('Subfinder', tool_name.title())
        
        pattern = r'def run_all_tests\(\):.*?(?=\n\Z|\ndef |\nclass )'
        content = re.sub(pattern, run_all_section, content, flags=re.DOTALL)
    
    # Write back
    if content != original_content:
        test_file.write_text(content)
        print(f"  ✅ Fixed {test_file.name}")
    else:
        print(f"  ⚠️  No changes needed for {test_file.name}")

print(f"\n✅ Fixed all {len(test_files)} test files")

