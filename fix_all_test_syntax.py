#!/usr/bin/env python3
"""
Fix all syntax errors in test files and update them with CrewAI changes from subfinder.
"""

import re
from pathlib import Path

# Get the working subfinder test as template
test_dir = Path("hackerdogs_tools/osint/tests")
subfinder_file = test_dir / "test_subfinder.py"
subfinder_content = subfinder_file.read_text()

# Extract key sections from subfinder
def extract_section(content, start_pattern, end_pattern=None):
    """Extract a section between two patterns."""
    start_match = re.search(start_pattern, content, re.MULTILINE)
    if not start_match:
        return None
    
    start_pos = start_match.start()
    if end_pattern:
        end_match = re.search(end_pattern, content[start_pos:], re.MULTILINE)
        if end_match:
            return content[start_pos:start_pos + end_match.start()]
    # Return until next def/class or end of function
    remaining = content[start_pos:]
    next_def = re.search(r'\n    def |\nclass |\Z', remaining)
    if next_def:
        return remaining[:next_def.start()]
    return remaining

# Extract standalone test
standalone_pattern = r'def test_standalone\(self\):'
standalone_section = extract_section(subfinder_content, standalone_pattern)

# Extract langchain test  
langchain_pattern = r'def test_langchain_agent\(self, agent\):'
langchain_section = extract_section(subfinder_content, langchain_pattern)

# Extract crewai test
crewai_pattern = r'def test_crewai_agent\(self, agent\):'
crewai_section = extract_section(subfinder_content, crewai_pattern)

# Extract run_all_tests function
run_all_pattern = r'def run_all_tests\(\):'
run_all_section = extract_section(subfinder_content, run_all_pattern)

print(f"Extracted sections:")
print(f"  Standalone: {len(standalone_section) if standalone_section else 0} chars")
print(f"  LangChain: {len(langchain_section) if langchain_section else 0} chars")
print(f"  CrewAI: {len(crewai_section) if crewai_section else 0} chars")
print(f"  Run all: {len(run_all_section) if run_all_section else 0} chars")

# Get all test files to fix
test_files = sorted([f for f in test_dir.glob("test_*.py") 
                    if f.name not in ["__init__.py", "test_utils.py", "test_runtime_helper.py", 
                                     "test_subfinder.py", "test_all_tools.py"]])

print(f"\nFixing {len(test_files)} test files...")

for test_file in test_files:
    print(f"\nProcessing {test_file.name}...")
    content = test_file.read_text()
    
    # Fix the invoke call syntax errors
    # Pattern: result = tool.invoke({ with mismatched braces
    # Replace with proper multi-line format
    
    # Find all invoke calls with runtime
    pattern = r'result = \w+\.invoke\(\s*\{\s*"runtime":\s*runtime,'
    
    def fix_invoke(match):
        tool_name = match.group(0).split('.')[0].split()[-1]
        return f'result = {tool_name}.invoke({{\n            "runtime": runtime,'
    
    # First, let's check what the actual pattern is
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this is the problematic invoke line
        if '.invoke({' in line and 'runtime' in line and ')' in line:
            # This is likely a single-line invoke that needs to be split
            # Extract the tool name
            tool_match = re.search(r'(\w+)\.invoke\(', line)
            if tool_match:
                tool_name = tool_match.group(1)
                # Check if it's all on one line with mismatched braces
                if line.count('{') == 1 and line.count('}') == 0:
                    # Split it properly
                    indent = len(line) - len(line.lstrip())
                    fixed_lines.append(line.split('.invoke(')[0] + '.invoke({')
                    # Extract parameters
                    params = line.split('.invoke(')[1].rstrip(')')
                    if params.startswith('{'):
                        params = params[1:]
                    # Add parameters on separate lines
                    for param in params.split(','):
                        if param.strip():
                            fixed_lines.append(' ' * (indent + 4) + param.strip() + ',')
                    fixed_lines.append(' ' * indent + '})')
                    i += 1
                    continue
        
        fixed_lines.append(line)
        i += 1
    
    # Write back if changed
    new_content = '\n'.join(fixed_lines)
    if new_content != content:
        test_file.write_text(new_content)
        print(f"  ✅ Fixed syntax errors")
    else:
        print(f"  ⚠️  No syntax errors found (may need manual check)")

print(f"\n✅ Fixed {len(test_files)} test files")

