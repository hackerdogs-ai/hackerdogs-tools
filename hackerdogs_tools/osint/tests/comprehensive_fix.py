"""
Comprehensive fix for all test files - fixes indentation, imports, and syntax errors.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))
EXCLUDE = {"test_utils.py", "test_runtime_helper.py", "test_all_tools.py", "fix_*.py", "comprehensive_fix.py", "update_*.py", "add_*.py"}
TEST_FILES = [f for f in TEST_FILES if not any(f.name.startswith(ex.replace('*', '')) or f.name == ex for ex in EXCLUDE)]

def fix_file(file_path):
    """Comprehensively fix a test file."""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changes = []
    
    # Fix 1: Remove duplicate try statements
    content = re.sub(r'try:\s*\ntry:', 'try:', content)
    if content != original:
        changes.append("removed duplicate try")
        original = content
    
    # Fix 2: Fix try blocks with wrong indentation after comment
    # Pattern: try:\n            # VERBATIM\n        result_data (8 spaces, should be 12)
    pattern = r'(try:\s*\n\s+# VERBATIM[^\n]*\n)(\s{8})(result_data\s*=)'
    def fix_try_indent(match):
        prefix = match.group(1)
        indent = match.group(2)
        code = match.group(3)
        # Use 12 spaces (same as try block)
        return prefix + '            ' + code
    content = re.sub(pattern, fix_try_indent, content)
    if content != original:
        changes.append("fixed try block indentation")
        original = content
    
    # Fix 3: Add missing imports
    needs_serialize = 'serialize_langchain_result' in content or 'serialize_crewai_result' in content
    
    if needs_serialize:
        # Check if import exists
        if 'from hackerdogs_tools.osint.tests.save_json_results import' in content:
            if 'serialize_langchain_result' not in content.split('import')[1].split('\n')[0]:
                # Add to import
                content = re.sub(
                    r'from hackerdogs_tools\.osint\.tests\.save_json_results import ([^\n]+)',
                    lambda m: f"from hackerdogs_tools.osint.tests.save_json_results import {m.group(1)}, serialize_langchain_result, serialize_crewai_result" if 'serialize_langchain_result' not in m.group(1) else m.group(0),
                    content
                )
                if content != original:
                    changes.append("added serialize imports")
                    original = content
        elif 'from .save_json_results import' in content:
            if 'serialize_langchain_result' not in content.split('import')[1].split('\n')[0]:
                content = re.sub(
                    r'from \.save_json_results import ([^\n]+)',
                    lambda m: f"from .save_json_results import {m.group(1)}, serialize_langchain_result, serialize_crewai_result" if 'serialize_langchain_result' not in m.group(1) else m.group(0),
                    content
                )
                if content != original:
                    changes.append("added serialize imports")
                    original = content
    
    # Fix 4: Fix standalone try blocks (no except) - these are in run_all_tests functions
    # Look for try: followed by code but no except in the next 10 lines
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for standalone try: (not in a function, or in run_all_tests)
        if re.match(r'^\s+try:\s*$', line):
            # Check if this is in run_all_tests or similar
            context_start = max(0, i - 20)
            context = '\n'.join(lines[context_start:i])
            
            # Look ahead for except
            found_except = False
            for j in range(i + 1, min(i + 15, len(lines))):
                if 'except' in lines[j] and lines[j].strip().startswith('except'):
                    found_except = True
                    break
                if lines[j].strip() and not lines[j].strip().startswith('#') and 'result_data' not in lines[j]:
                    # Non-comment, non-result_data line means we're past the try block
                    break
            
            if not found_except:
                # This try has no except - check if next line is properly indented
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    try_indent = len(line) - len(line.lstrip())
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    if next_indent <= try_indent and next_line.strip():
                        # Fix indentation
                        fixed_lines.append(line)
                        i += 1
                        # Fix the next few lines
                        while i < len(lines) and i < i + 10:
                            curr_line = lines[i]
                            if 'except' in curr_line:
                                break
                            if curr_line.strip() and not curr_line.strip().startswith('#'):
                                curr_indent = len(curr_line) - len(curr_line.lstrip())
                                if curr_indent <= try_indent:
                                    # Fix indentation
                                    fixed_lines.append(' ' * (try_indent + 4) + curr_line.lstrip())
                                    i += 1
                                    continue
                            fixed_lines.append(curr_line)
                            i += 1
                        continue
        
        fixed_lines.append(line)
        i += 1
    
    if '\n'.join(fixed_lines) != content:
        content = '\n'.join(fixed_lines)
        changes.append("fixed standalone try blocks")
    
    if changes:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fixed: {', '.join(changes)}")
        return True
    else:
        print(f"  ⏭️  No changes")
        return False

def main():
    print("=" * 80)
    print("COMPREHENSIVE FIX FOR ALL TEST FILES")
    print("=" * 80)
    print(f"Found {len(TEST_FILES)} test files\n")
    
    fixed = 0
    for f in sorted(TEST_FILES):
        if fix_file(f):
            fixed += 1
    
    print(f"\n✅ Fixed {fixed}/{len(TEST_FILES)} files")

if __name__ == "__main__":
    main()

