"""
Final comprehensive fix - removes nested try blocks and fixes all indentation.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))
EXCLUDE = {"test_utils.py", "test_runtime_helper.py", "test_all_tools.py"}
TEST_FILES = [f for f in TEST_FILES if not any(f.name.startswith(ex.replace('*', '')) or f.name == ex or 'fix' in f.name.lower() or 'update' in f.name.lower() or 'add' in f.name.lower() or 'comprehensive' in f.name.lower() for ex in EXCLUDE)]

def fix_file(file_path):
    """Fix all issues in a test file."""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    i = 0
    changed = False
    
    while i < len(lines):
        line = lines[i]
        
        # Fix nested try blocks: try:\n            try:
        if re.match(r'^\s+try:\s*$', line) and i + 1 < len(lines):
            next_line = lines[i + 1]
            if re.match(r'^\s+try:\s*$', next_line):
                # Remove the duplicate try
                fixed_lines.append(line)
                i += 2  # Skip both try lines
                changed = True
                continue
        
        # Fix try blocks with missing content
        if re.match(r'^\s+try:\s*$', line):
            try_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            i += 1
            
            # Check next few lines
            if i < len(lines):
                next_line = lines[i]
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If next line is another try, we already handled it above
                if re.match(r'^\s+try:\s*$', next_line):
                    continue
                
                # If next line has wrong indentation (too little), fix it
                if next_line.strip() and not next_line.strip().startswith('#') and next_indent <= try_indent:
                    # This is wrong - should be indented inside try
                    expected_indent = try_indent + 4
                    fixed_lines.append(' ' * expected_indent + next_line.lstrip())
                    changed = True
                    i += 1
                    continue
        
        fixed_lines.append(line)
        i += 1
    
    # Also fix imports
    content = ''.join(fixed_lines)
    original_content = content
    
    # Add serialize imports if needed
    if ('serialize_langchain_result' in content or 'serialize_crewai_result' in content):
        if 'from hackerdogs_tools.osint.tests.save_json_results import' in content:
            if 'serialize_langchain_result' not in content.split('import')[1].split('\n')[0]:
                content = re.sub(
                    r'(from hackerdogs_tools\.osint\.tests\.save_json_results import [^\n]+)',
                    r'\1, serialize_langchain_result, serialize_crewai_result',
                    content
                )
        elif 'from .save_json_results import' in content:
            if 'serialize_langchain_result' not in content.split('import')[1].split('\n')[0]:
                content = re.sub(
                    r'(from \.save_json_results import [^\n]+)',
                    r'\1, serialize_langchain_result, serialize_crewai_result',
                    content
                )
    
    if content != original_content or changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fixed")
        return True
    else:
        print(f"  ⏭️  OK")
        return False

def main():
    print("=" * 80)
    print("FINAL FIX FOR ALL TEST FILES")
    print("=" * 80)
    print(f"Found {len(TEST_FILES)} test files\n")
    
    fixed = 0
    for f in sorted(TEST_FILES):
        if fix_file(f):
            fixed += 1
    
    print(f"\n✅ Fixed {fixed}/{len(TEST_FILES)} files")

if __name__ == "__main__":
    main()

