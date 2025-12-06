"""
Fix syntax errors introduced by the previous script.
Fixes "try: - VERBATIM, no wrapper" syntax errors.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))
EXCLUDE = {"test_utils.py", "test_runtime_helper.py", "test_all_tools.py", "fix_all_tests_verbatim.py", "fix_syntax_errors.py"}
TEST_FILES = [f for f in TEST_FILES if f.name not in EXCLUDE]

def fix_test_file(file_path):
    """Fix syntax errors in a test file."""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix "try: - VERBATIM, no wrapper" syntax errors
    # Pattern: "try: - VERBATIM, no wrapper" should be "try:\n            # VERBATIM, no wrapper"
    content = re.sub(
        r'try:\s*-\s*VERBATIM,\s*no\s*wrapper',
        'try:\n            # VERBATIM, no wrapper',
        content
    )
    
    # Fix any remaining result_data blocks that still have wrappers
    # Pattern: result_data = { "status": ..., "agent_type": "langchain", "result": result, ... }
    langchain_pattern = r'result_data\s*=\s*\{\s*"status":\s*"[^"]*",\s*"agent_type":\s*"langchain",\s*"result":\s*result[^}]*\}'
    content = re.sub(
        langchain_pattern,
        'result_data = serialize_langchain_result(result)',
        content,
        flags=re.MULTILINE
    )
    
    # Pattern: result_data = { "status": ..., "agent_type": "crewai", "result": serialize_crewai_result(result), ... }
    crewai_pattern = r'result_data\s*=\s*\{\s*"status":\s*"[^"]*",\s*"agent_type":\s*"crewai",\s*"result":\s*serialize_crewai_result\(result\)[^}]*\}'
    content = re.sub(
        crewai_pattern,
        'result_data = serialize_crewai_result(result) if result else None',
        content,
        flags=re.MULTILINE
    )
    
    # Ensure imports are present
    if 'serialize_langchain_result' in content and 'from hackerdogs_tools.osint.tests.save_json_results import' not in content:
        # Find the import line for save_test_result
        if 'from hackerdogs_tools.osint.tests.save_json_results import save_test_result' in content:
            content = content.replace(
                'from hackerdogs_tools.osint.tests.save_json_results import save_test_result',
                'from hackerdogs_tools.osint.tests.save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result'
            )
        elif 'from .save_json_results import save_test_result' in content:
            content = content.replace(
                'from .save_json_results import save_test_result',
                'from .save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result'
            )
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fixed {file_path.name}")
        return True
    else:
        print(f"  ⏭️  No changes needed for {file_path.name}")
        return False

def main():
    """Fix all test files."""
    print("=" * 80)
    print("FIXING SYNTAX ERRORS IN ALL TEST FILES")
    print("=" * 80)
    print(f"Found {len(TEST_FILES)} test files to check\n")
    
    fixed_count = 0
    for test_file in sorted(TEST_FILES):
        if fix_test_file(test_file):
            fixed_count += 1
    
    print("\n" + "=" * 80)
    print(f"✅ Fixed {fixed_count} out of {len(TEST_FILES)} test files")
    print("=" * 80)

if __name__ == "__main__":
    main()

