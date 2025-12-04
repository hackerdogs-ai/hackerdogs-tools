#!/usr/bin/env python3
"""
Fix syntax errors in all test files:
1. Remove duplicate print statements with syntax errors
2. Fix indentation issues with assert statements
"""

from pathlib import Path
import re

test_dir = Path("hackerdogs_tools/osint/tests")
test_files = sorted([f for f in test_dir.glob("test_*.py") 
                    if f.name not in ["__init__.py", "test_utils.py", "test_runtime_helper.py", 
                                     "test_all_tools.py", "save_json_results.py"]])

print(f"Fixing syntax errors in {len(test_files)} test files...\n")

for test_file in test_files:
    content = test_file.read_text()
    original = content
    
    # Fix 1: Remove duplicate print statements with syntax errors
    # Pattern: print(f"...") - Result: {str(result)[:200]}")
    pattern1 = r'print\(f"✅ (LangChain|CrewAI) test passed"\) - Result: \{str\(result\)\[:200\]\}\)'
    replacement1 = r'print(f"✅ \1 test passed")'
    content = re.sub(pattern1, replacement1, content)
    
    # Fix 2: Fix indentation issues with assert statements
    # Pattern: Multiple spaces before assert
    pattern2 = r'(\s{8,})assert result is not None'
    replacement2 = r'        assert result is not None'
    content = re.sub(pattern2, replacement2, content)
    
    if content != original:
        test_file.write_text(content)
        print(f"✅ Fixed {test_file.name}")
    else:
        print(f"⚠️  {test_file.name}: No changes needed")

print(f"\n✅ Fixed all {len(test_files)} test files")

