#!/usr/bin/env python3
"""
Fix all test files to use proper ToolRuntime and fix run_all_tests functions.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))

def fix_test_file(file_path: Path):
    """Fix a test file."""
    content = file_path.read_text()
    original = content
    
    # Fix 1: Add import for create_mock_runtime
    if 'from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime' not in content:
        # Find the test_domains import line
        pattern = r'(from hackerdogs_tools\.osint\.test_domains import get_random_domain)'
        replacement = r'\1\nfrom hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime'
        content = re.sub(pattern, replacement, content)
    
    # Fix 2: Remove ToolRuntime import if present
    content = re.sub(r'from langchain\.tools import ToolRuntime\n', '', content)
    content = re.sub(r'from langchain\.tools import tool, ToolRuntime\n', 'from langchain.tools import tool\n', content)
    
    # Fix 3: Replace ToolRuntime() calls with create_mock_runtime()
    content = re.sub(
        r'runtime = ToolRuntime\(state=\{"user_id": "test_user"\}\)',
        'runtime = create_mock_runtime(state={"user_id": "test_user"})',
        content
    )
    
    # Fix 4: Fix standalone test to use .invoke()
    # Pattern: result = tool_name(runtime=runtime, ...)
    tool_pattern = r'result = (\w+)\(\s*runtime=runtime,'
    replacement = r'result = \1.invoke({\n            "runtime": runtime,'
    content = re.sub(tool_pattern, replacement, content)
    
    # Fix 5: Fix run_all_tests to not call fixtures directly
    # This is more complex, so we'll do it manually for each file
    
    if content != original:
        file_path.write_text(content)
        print(f"✅ Fixed {file_path.name}")
        return True
    return False

if __name__ == "__main__":
    fixed = 0
    for test_file in TEST_FILES:
        if fix_test_file(test_file):
            fixed += 1
    
    print(f"\n✅ Fixed {fixed} test files")
    print("\n⚠️  Note: run_all_tests() functions need manual fixes for pytest fixtures")

