"""
Fix indentation errors in all test files.
Fixes: try:\n            # VERBATIM\n        result_data (wrong indentation)
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))
EXCLUDE = {"test_utils.py", "test_runtime_helper.py", "test_all_tools.py", "fix_*.py"}
TEST_FILES = [f for f in TEST_FILES if f.name not in EXCLUDE]

def fix_indentation(file_path):
    """Fix indentation errors in a test file."""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    changed = False
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a try: line
        if re.match(r'^\s+try:\s*$', line):
            try_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            i += 1
            
            # Look for the comment and result_data line
            if i < len(lines):
                comment_line = lines[i]
                # Check if it's a VERBATIM comment
                if '# VERBATIM' in comment_line:
                    fixed_lines.append(comment_line)
                    i += 1
                    
                    # Next line should be result_data with proper indentation
                    if i < len(lines):
                        result_line = lines[i]
                        current_indent = len(result_line) - len(result_line.lstrip())
                        expected_indent = try_indent + 4  # 4 spaces inside try block
                        
                        # If indentation is wrong (too little), fix it
                        if 'result_data' in result_line and current_indent < expected_indent:
                            fixed_line = ' ' * expected_indent + result_line.lstrip()
                            fixed_lines.append(fixed_line)
                            changed = True
                            i += 1
                            continue
        
        fixed_lines.append(line)
        i += 1
    
    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(fixed_lines)
        print(f"  ✅ Fixed indentation in {file_path.name}")
        return True
    else:
        print(f"  ⏭️  No changes needed for {file_path.name}")
        return False

def main():
    """Fix all test files."""
    print("=" * 80)
    print("FIXING INDENTATION ERRORS IN ALL TEST FILES")
    print("=" * 80)
    print(f"Found {len(TEST_FILES)} test files to check\n")
    
    fixed_count = 0
    for test_file in sorted(TEST_FILES):
        if fix_indentation(test_file):
            fixed_count += 1
    
    print("\n" + "=" * 80)
    print(f"✅ Fixed {fixed_count} out of {len(TEST_FILES)} test files")
    print("=" * 80)

if __name__ == "__main__":
    main()

