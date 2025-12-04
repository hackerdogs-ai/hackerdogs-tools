#!/usr/bin/env python3
"""
Add project root to sys.path in all test files for direct execution.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))

def fix_file(file_path: Path):
    """Add project root to sys.path in test file."""
    content = file_path.read_text()
    original = content
    
    # Check if already has the fix
    if "project_root = Path(__file__).parent" in content:
        return False
    
    # Find the import section
    import_pattern = r'(import pytest\nimport json\nimport os)'
    
    replacement = r'''import pytest
import json
import os
import sys
from pathlib import Path

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))'''
    
    content = re.sub(import_pattern, replacement, content, count=1)
    
    if content != original:
        file_path.write_text(content)
        print(f"✅ Fixed {file_path.name}")
        return True
    return False

if __name__ == "__main__":
    fixed_count = 0
    for test_file in TEST_FILES:
        if fix_file(test_file):
            fixed_count += 1
    
    print(f"\n✅ Fixed {fixed_count} test files")

