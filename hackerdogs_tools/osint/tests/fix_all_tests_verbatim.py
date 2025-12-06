"""
Script to fix ALL test files to output verbatim results without wrappers.
Removes all test metadata (status, agent_type, test_type, etc.) and saves only raw results.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))
# Exclude utility files
EXCLUDE = {"test_utils.py", "test_runtime_helper.py", "test_all_tools.py"}
TEST_FILES = [f for f in TEST_FILES if f.name not in EXCLUDE]

def fix_langchain_save(result_data_pattern):
    """Fix LangChain result saving to be verbatim."""
    # Pattern 1: result_data = { "status": ..., "agent_type": "langchain", "result": serialize_langchain_result(result), ... }
    pattern1 = r'result_data\s*=\s*\{\s*"status":\s*"success",\s*"agent_type":\s*"langchain",\s*"result":\s*serialize_langchain_result\(result\)[^}]*\}'
    replacement1 = 'result_data = serialize_langchain_result(result)'
    
    # Pattern 2: result_data = { "status": ..., "agent_type": "langchain", "result": serialize_langchain_result(result), "test_type": ..., ... }
    pattern2 = r'result_data\s*=\s*\{\s*"status":\s*"[^"]*",\s*"agent_type":\s*"langchain",\s*"result":\s*serialize_langchain_result\(result\)[^}]*\}'
    replacement2 = 'result_data = serialize_langchain_result(result)'
    
    # Try pattern 1 first
    if re.search(pattern1, result_data_pattern, re.MULTILINE | re.DOTALL):
        return re.sub(pattern1, replacement1, result_data_pattern, flags=re.MULTILINE | re.DOTALL)
    # Then pattern 2
    elif re.search(pattern2, result_data_pattern, re.MULTILINE | re.DOTALL):
        return re.sub(pattern2, replacement2, result_data_pattern, flags=re.MULTILINE | re.DOTALL)
    
    return result_data_pattern

def fix_crewai_save(result_data_pattern):
    """Fix CrewAI result saving to be verbatim."""
    # Pattern: result_data = { "status": ..., "agent_type": "crewai", "result": serialize_crewai_result(result), ... }
    pattern = r'result_data\s*=\s*\{\s*"status":\s*"[^"]*",\s*"agent_type":\s*"crewai",\s*"result":\s*serialize_crewai_result\(result\)[^}]*\}'
    replacement = 'result_data = serialize_crewai_result(result) if result else None'
    
    return re.sub(pattern, replacement, result_data_pattern, flags=re.MULTILINE | re.DOTALL)

def fix_test_file(file_path):
    """Fix a single test file to output verbatim results."""
    print(f"Fixing {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix LangChain saves - look for the save_test_result calls with langchain
    # Find all sections that save LangChain results
    langchain_pattern = r'(# Save LangChain[^\n]*\n\s*try:\s*\n\s*)(result_data\s*=\s*\{[^}]*"agent_type":\s*"langchain"[^}]*\})'
    
    def replace_langchain_save(match):
        comment = match.group(1)
        result_data_block = match.group(2)
        fixed = fix_langchain_save(result_data_block)
        # Add comment about verbatim
        if 'VERBATIM' not in comment:
            comment = comment.rstrip() + ' - VERBATIM, no wrapper\n        '
        return comment + fixed
    
    content = re.sub(langchain_pattern, replace_langchain_save, content, flags=re.MULTILINE)
    
    # Fix CrewAI saves
    crewai_pattern = r'(# Save CrewAI[^\n]*\n\s*try:\s*\n\s*)(result_data\s*=\s*\{[^}]*"agent_type":\s*"crewai"[^}]*\})'
    
    def replace_crewai_save(match):
        comment = match.group(1)
        result_data_block = match.group(2)
        fixed = fix_crewai_save(result_data_block)
        # Add comment about verbatim
        if 'VERBATIM' not in comment:
            comment = comment.rstrip() + ' - VERBATIM, no wrapper\n        '
        return comment + fixed
    
    content = re.sub(crewai_pattern, replace_crewai_save, content, flags=re.MULTILINE)
    
    # More aggressive pattern matching for result_data assignments
    # Fix any result_data = { ... "agent_type": "langchain" ... }
    langchain_aggressive = r'result_data\s*=\s*\{\s*"status":\s*"[^"]*",\s*"agent_type":\s*"langchain",\s*"result":\s*serialize_langchain_result\(result\)[^}]*\}'
    content = re.sub(langchain_aggressive, 'result_data = serialize_langchain_result(result)', content, flags=re.MULTILINE)
    
    # Fix any result_data = { ... "agent_type": "crewai" ... }
    crewai_aggressive = r'result_data\s*=\s*\{\s*"status":\s*"[^"]*",\s*"agent_type":\s*"crewai",\s*"result":\s*serialize_crewai_result\(result\)[^}]*\}'
    content = re.sub(crewai_aggressive, 'result_data = serialize_crewai_result(result) if result else None', content, flags=re.MULTILINE)
    
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
    print("FIXING ALL TEST FILES FOR VERBATIM OUTPUT")
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

