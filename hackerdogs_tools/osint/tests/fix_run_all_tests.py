"""
Fix all run_all_tests() functions to properly define variables before use.
Fixes: NameError for 'test', 'llm', 'result_data', etc.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))
EXCLUDE = {"test_utils.py", "test_runtime_helper.py", "test_all_tools.py", "fix_*.py", "comprehensive_fix.py", "update_*.py", "add_*.py", "generate_*.py"}
TEST_FILES = [f for f in TEST_FILES if not any(f.name.startswith(ex.replace('*', '')) or f.name == ex for ex in EXCLUDE)]

def fix_run_all_tests(file_path):
    """Fix run_all_tests function in a test file."""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # Pattern 1: test.test_*() without test = TestClass() defined
    # Look for: test.test_*() and ensure test = TestClass() is defined before
    if 'def run_all_tests' in content:
        # Find the class name from test class definitions
        class_match = re.search(r'class (Test\w+Standalone)', content)
        if class_match:
            class_name = class_match.group(1)
            # Fix: test.test_*() -> test = ClassName(); test.test_*()
            pattern = r'(try:\s*\n\s+)(test\.test_\w+\(\))'
            def fix_test_var(match):
                indent = match.group(1)
                call = match.group(2)
                return indent + f'test = {class_name}()\n' + ' ' * (len(indent) - len(indent.lstrip()) + 4) + call
            if re.search(pattern, content):
                content = re.sub(pattern, fix_test_var, content)
                changes.append("fixed test variable")
        
        # Pattern 2: model=llm or llm=llm without llm = get_*_from_env() defined
        # Fix LangChain: model=llm -> llm = get_llm_from_env()\n        model=llm
        langchain_pattern = r'(try:\s*\n\s+)(tools\s*=.*?\n\s+agent\s*=\s*create_agent\(\s*\n\s+model=llm,)'
        def fix_langchain_llm(match):
            indent = match.group(1)
            rest = match.group(2)
            return indent + 'llm = get_llm_from_env()\n' + ' ' * (len(indent) - len(indent.lstrip()) + 4) + rest
        if re.search(langchain_pattern, content, re.MULTILINE | re.DOTALL):
            content = re.sub(langchain_pattern, fix_langchain_llm, content, flags=re.MULTILINE | re.DOTALL)
            changes.append("fixed LangChain llm")
        
        # Fix CrewAI: llm=llm -> llm = get_crewai_llm_from_env()\n        llm=llm
        crewai_pattern = r'(try:\s*\n\s+)(agent\s*=\s*Agent\(\s*\n\s+role=.*?\n\s+llm=llm,)'
        def fix_crewai_llm(match):
            indent = match.group(1)
            rest = match.group(2)
            return indent + 'llm = get_crewai_llm_from_env()\n' + ' ' * (len(indent) - len(indent.lstrip()) + 4) + rest
        if re.search(crewai_pattern, content, re.MULTILINE | re.DOTALL):
            content = re.sub(crewai_pattern, fix_crewai_llm, content, flags=re.MULTILINE | re.DOTALL)
            changes.append("fixed CrewAI llm")
        
        # Pattern 3: result_data used without definition
        # Fix: save_test_result(..., result_data, ...) -> result_data = serialize_*_result(result)\n        save_test_result(..., result_data, ...)
        result_data_pattern = r'(try:\s*\n\s+)(result_file\s*=\s*save_test_result\([^,]+,\s*result_data,)'
        def fix_result_data(match):
            indent = match.group(1)
            rest = match.group(2)
            # Determine if it's langchain or crewai based on context
            if 'langchain' in rest.lower():
                return indent + 'result_data = serialize_langchain_result(result)\n' + ' ' * (len(indent) - len(indent.lstrip()) + 4) + rest
            elif 'crewai' in rest.lower():
                return indent + 'result_data = serialize_crewai_result(result) if result else None\n' + ' ' * (len(indent) - len(indent.lstrip()) + 4) + rest
            return match.group(0)
        if re.search(result_data_pattern, content):
            content = re.sub(result_data_pattern, fix_result_data, content)
            changes.append("fixed result_data")
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fixed: {', '.join(changes) if changes else 'undefined variables'}")
        return True
    else:
        print(f"  ⏭️  No changes")
        return False

def main():
    print("=" * 80)
    print("FIXING run_all_tests() FUNCTIONS")
    print("=" * 80)
    print(f"Found {len(TEST_FILES)} test files\n")
    
    fixed = 0
    for f in sorted(TEST_FILES):
        if fix_run_all_tests(f):
            fixed += 1
    
    print(f"\n✅ Fixed {fixed}/{len(TEST_FILES)} files")

if __name__ == "__main__":
    main()

