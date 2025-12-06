"""
Comprehensive fix for all syntax errors in test files.
Fixes malformed try blocks and missing imports.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))
EXCLUDE = {"test_utils.py", "test_runtime_helper.py", "test_all_tools.py", "fix_all_tests_verbatim.py", "fix_syntax_errors.py", "fix_all_syntax_errors.py"}
TEST_FILES = [f for f in TEST_FILES if f.name not in EXCLUDE]

def fix_test_file(file_path):
    """Fix syntax errors in a test file."""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = []
    
    # Fix 1: Malformed try blocks - "try:\n            # VERBATIM" without proper indentation
    # Pattern: try:\n            # VERBATIM, no wrapper\n        result_data = ...
    pattern1 = r'try:\s*\n\s*# VERBATIM[^\n]*\n\s*result_data\s*='
    replacement1 = 'try:\n            result_data ='
    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement1, content)
        changes_made.append("Fixed malformed try blocks")
    
    # Fix 2: Missing imports - ensure serialize functions are imported
    if 'serialize_langchain_result' in content or 'serialize_crewai_result' in content:
        # Check if imports exist
        has_import = 'from hackerdogs_tools.osint.tests.save_json_results import' in content or 'from .save_json_results import' in content
        
        if has_import:
            # Check if serialize functions are in the import
            if 'serialize_langchain_result' in content and 'serialize_langchain_result' not in content.split('import')[1].split('\n')[0]:
                # Add to existing import
                if 'from hackerdogs_tools.osint.tests.save_json_results import save_test_result' in content:
                    content = content.replace(
                        'from hackerdogs_tools.osint.tests.save_json_results import save_test_result',
                        'from hackerdogs_tools.osint.tests.save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result'
                    )
                    changes_made.append("Added serialize imports")
                elif 'from .save_json_results import save_test_result' in content:
                    content = content.replace(
                        'from .save_json_results import save_test_result',
                        'from .save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result'
                    )
                    changes_made.append("Added serialize imports")
    
    # Fix 3: Remove any leftover dictionary wrappers in result_data assignments
    # Pattern: result_data = { "status": ..., "agent_type": "langchain", "result": serialize_langchain_result(result), ... }
    langchain_wrapper = r'result_data\s*=\s*\{\s*"status":\s*"[^"]*",\s*"agent_type":\s*"langchain",\s*"result":\s*serialize_langchain_result\(result\)[^}]*\}'
    if re.search(langchain_wrapper, content, re.MULTILINE | re.DOTALL):
        content = re.sub(langchain_wrapper, 'result_data = serialize_langchain_result(result)', content, flags=re.MULTILINE | re.DOTALL)
        changes_made.append("Removed LangChain wrappers")
    
    crewai_wrapper = r'result_data\s*=\s*\{\s*"status":\s*"[^"]*",\s*"agent_type":\s*"crewai",\s*"result":\s*serialize_crewai_result\(result\)[^}]*\}'
    if re.search(crewai_wrapper, content, re.MULTILINE | re.DOTALL):
        content = re.sub(crewai_wrapper, 'result_data = serialize_crewai_result(result) if result else None', content, flags=re.MULTILINE | re.DOTALL)
        changes_made.append("Removed CrewAI wrappers")
    
    # Fix 4: Fix incomplete try blocks - ensure they have proper except clauses
    # Look for try blocks that are missing except
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)
        
        # Check if this is a try: line
        if re.match(r'^\s+try:\s*$', line):
            # Check if next line is a comment or empty, then result_data
            j = i + 1
            found_code = False
            while j < len(lines) and j < i + 5:
                next_line = lines[j]
                # Skip comments and empty lines
                if next_line.strip().startswith('#') or not next_line.strip():
                    j += 1
                    continue
                # Check if it's result_data assignment
                if 'result_data' in next_line:
                    found_code = True
                    # Check indentation - should be same as try
                    try_indent = len(line) - len(line.lstrip())
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= try_indent:
                        # Fix indentation
                        fixed_lines.append(' ' * (try_indent + 4) + next_line.lstrip())
                        j += 1
                        # Skip the original line
                        if j < len(lines):
                            continue
                    break
                j += 1
            
            if not found_code and j < len(lines):
                # Look ahead for the actual code
                pass
        
        i += 1
    
    # Actually, let's use a simpler approach - fix specific patterns
    # Pattern: try:\n            # comment\n        result_data (wrong indentation)
    pattern_try_fix = r'(try:\s*\n\s*# [^\n]*\n)(\s+)(result_data\s*=)'
    def fix_indent(match):
        comment_block = match.group(1)
        indent = match.group(2)
        result_line = match.group(3)
        # Ensure proper indentation (12 spaces for try block content)
        return comment_block + '            ' + result_line
    
    content = re.sub(pattern_try_fix, fix_indent, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fixed {file_path.name}: {', '.join(changes_made) if changes_made else 'syntax errors'}")
        return True
    else:
        print(f"  ⏭️  No changes needed for {file_path.name}")
        return False

def main():
    """Fix all test files."""
    print("=" * 80)
    print("FIXING ALL SYNTAX ERRORS IN TEST FILES")
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

