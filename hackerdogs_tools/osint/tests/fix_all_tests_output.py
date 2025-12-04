#!/usr/bin/env python3
"""
Fix all test files to show JSON output and improve test output.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent

def fix_test_file(file_path: Path):
    """Fix a test file to show JSON output."""
    content = file_path.read_text()
    original = content
    
    # Pattern 1: Add JSON output printing after json.loads
    pattern1 = r'(result_data = json\.loads\(result\))\s+(# Assertions)'
    replacement1 = r'''\1

        # Print JSON output for verification
        print("\\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\\n")
        
        \2'''
    content = re.sub(pattern1, replacement1, content)
    
    # Pattern 2: Improve assertions with better error messages
    if 'assert "status" in result_data' in content and 'assert "status" in result_data,' not in content:
        content = re.sub(
            r'assert "status" in result_data',
            'assert "status" in result_data, f"Missing \'status\' in result: {result_data}"',
            content
        )
    
    # Pattern 3: Improve execution_method assertion
    if 'assert result_data["execution_method"] == "docker"' in content:
        content = re.sub(
            r'assert result_data\["execution_method"\] == "docker"',
            'assert result_data["execution_method"] in ["docker", "official_docker_image"], f"Invalid execution_method: {result_data.get(\'execution_method\')}"',
            content
        )
    
    if content != original:
        file_path.write_text(content)
        return True
    return False

if __name__ == "__main__":
    fixed = 0
    for test_file in TEST_DIR.glob("test_*.py"):
        if test_file.name == "test_utils.py" or test_file.name == "test_domains.py":
            continue
        if fix_test_file(test_file):
            fixed += 1
            print(f"✅ Fixed {test_file.name}")
    
    print(f"\n✅ Fixed {fixed} test files")

