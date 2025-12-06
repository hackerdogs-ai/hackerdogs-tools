"""
Fix ALL run_all_tests() functions to properly define variables before use.
This fixes the regression where test and llm variables were removed.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))
EXCLUDE = {"test_utils.py", "test_runtime_helper.py", "test_all_tools.py", "fix_*.py", "comprehensive_fix.py", "update_*.py", "add_*.py", "generate_*.py"}
TEST_FILES = [f for f in TEST_FILES if not any(f.name.startswith(ex.replace('*', '')) or f.name == ex for ex in EXCLUDE)]

def get_test_class_name(content):
    """Extract the test class name from content."""
    match = re.search(r'class (Test\w+Standalone)', content)
    if match:
        return match.group(1)
    return None

def fix_run_all_tests(file_path):
    """Fix run_all_tests function in a test file."""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    original_lines = lines.copy()
    fixed_lines = []
    i = 0
    changed = False
    
    # Find run_all_tests function
    in_run_all_tests = False
    test_class_name = get_test_class_name(''.join(lines))
    
    while i < len(lines):
        line = lines[i]
        
        # Detect start of run_all_tests
        if 'def run_all_tests' in line:
            in_run_all_tests = True
            fixed_lines.append(line)
            i += 1
            continue
        
        # Detect end of run_all_tests (next def or if __name__)
        if in_run_all_tests:
            if (line.strip().startswith('def ') and 'run_all_tests' not in line) or line.strip().startswith('if __name__'):
                in_run_all_tests = False
        
        if in_run_all_tests:
            # Fix 1: test.test_*() without test = TestClass() defined
            if re.match(r'^\s+test\.test_\w+\(\)', line):
                # Check if previous line defines test
                if i > 0 and 'test = ' not in lines[i-1]:
                    # Insert test definition
                    indent = len(line) - len(line.lstrip())
                    fixed_lines.append(' ' * indent + f'test = {test_class_name}()\n')
                    changed = True
            
            # Fix 2: model=llm or llm=llm without llm definition
            # Check if this line uses llm and previous lines don't define it
            if ('model=llm' in line or 'llm=llm' in line) and i > 0:
                # Look back to see if llm was defined in this try block
                found_llm_def = False
                j = i - 1
                while j >= 0 and j > i - 20:  # Look back up to 20 lines
                    if 'llm = get_' in lines[j] or 'llm = ' in lines[j]:
                        found_llm_def = True
                        break
                    if lines[j].strip().startswith('try:'):
                        break  # Reached start of try block
                    j -= 1
                
                if not found_llm_def:
                    # Insert llm definition
                    indent = len(line) - len(line.lstrip())
                    # Determine if LangChain or CrewAI
                    if 'create_agent' in ''.join(lines[max(0, i-5):i+1]):
                        fixed_lines.append(' ' * indent + 'llm = get_llm_from_env()\n')
                    elif 'Agent(' in ''.join(lines[max(0, i-5):i+1]) or 'Crew(' in ''.join(lines[max(0, i-5):i+1]):
                        fixed_lines.append(' ' * indent + 'llm = get_crewai_llm_from_env()\n')
                    changed = True
            
            # Fix 3: result_data used without definition
            if 'save_test_result' in line and 'result_data' in line and i > 0:
                # Check if result_data was defined
                found_result_data = False
                j = i - 1
                while j >= 0 and j > i - 10:
                    if 'result_data = ' in lines[j]:
                        found_result_data = True
                        break
                    if lines[j].strip().startswith('try:'):
                        break
                    j -= 1
                
                if not found_result_data:
                    # Insert result_data definition
                    indent = len(line) - len(line.lstrip())
                    # Determine if LangChain or CrewAI
                    if 'langchain' in line.lower():
                        fixed_lines.append(' ' * indent + 'result_data = serialize_langchain_result(result)\n')
                    elif 'crewai' in line.lower():
                        fixed_lines.append(' ' * indent + 'result_data = serialize_crewai_result(result) if result else None\n')
                    changed = True
        
        fixed_lines.append(line)
        i += 1
    
    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        print(f"  ✅ Fixed undefined variables")
        return True
    else:
        print(f"  ⏭️  No changes")
        return False

def main():
    print("=" * 80)
    print("FIXING ALL run_all_tests() FUNCTIONS")
    print("=" * 80)
    print(f"Found {len(TEST_FILES)} test files\n")
    
    fixed = 0
    for f in sorted(TEST_FILES):
        if fix_run_all_tests(f):
            fixed += 1
    
    print(f"\n✅ Fixed {fixed}/{len(TEST_FILES)} files")

if __name__ == "__main__":
    main()

