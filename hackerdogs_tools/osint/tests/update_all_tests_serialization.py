"""
Script to update all test files to use consistent serialization for LangChain, CrewAI, and standalone tests.

This script:
1. Updates LangChain tests to use serialize_langchain_result()
2. Updates CrewAI tests to use serialize_crewai_result()
3. Removes all truncation and decoration from result saving
"""

import re
from pathlib import Path
from typing import List, Tuple

TEST_DIR = Path(__file__).parent
ALREADY_UPDATED = {"test_amass.py", "test_subfinder.py"}


def update_langchain_test_saving(content: str) -> Tuple[str, bool]:
    """
    Update LangChain test result saving to use proper serialization.
    
    Returns:
        (updated_content, was_changed)
    """
    changed = False
    
    # Pattern 1: Old pattern with messages_data extraction and truncation
    old_pattern1 = re.compile(
        r'(# Save.*LangChain.*?result.*?try:.*?messages_data = \[\].*?if isinstance\(result, dict\) and "messages" in result:.*?for msg in result\["messages"\]:.*?messages_data\.append\(\{.*?"type": msg\.__class__\.__name__.*?"content": str\(msg\.content\)\[:\d+\].*?\}\).*?result_data = \{.*?"status": "success".*?"agent_type": "langchain".*?"result": str\(result\)\[:\d+\] if result else None.*?"messages": messages_data.*?"messages_count":.*?\})',
        re.DOTALL
    )
    
    new_pattern1 = '''        # Save LangChain agent result - complete result as-is, no truncation, no decoration
        try:
            result_data = {
                "status": "success",
                "agent_type": "langchain",
                "result": result,  # Complete result dict as-is, no truncation, no decoration
                "domain": test_domain
            }'''
    
    if old_pattern1.search(content):
        content = old_pattern1.sub(new_pattern1, content)
        changed = True
    
    # Pattern 2: Simple truncation pattern
    old_pattern2 = re.compile(
        r'("result":\s*)str\(result\)\[:\d+\]( if result else None)',
        re.MULTILINE
    )
    
    def replace_truncation(match):
        return f'{match.group(1)}result{match.group(2)}  # Complete result as-is, no truncation'
    
    if old_pattern2.search(content):
        content = old_pattern2.sub(replace_truncation, content)
        changed = True
    
    # Pattern 3: Remove messages_data and messages_count decoration
    content = re.sub(
        r',\s*"messages": messages_data,\s*"messages_count":.*?\)',
        '',
        content,
        flags=re.DOTALL
    )
    
    return content, changed


def update_crewai_test_saving(content: str) -> Tuple[str, bool]:
    """
    Update CrewAI test result saving to use serialize_crewai_result().
    
    Returns:
        (updated_content, was_changed)
    """
    changed = False
    
    # Pattern 1: Old pattern with str(result)[:N] truncation
    old_pattern1 = re.compile(
        r'(# Save.*CrewAI.*?result.*?try:.*?result_data = \{.*?"status": "success".*?"agent_type": "crewai".*?"result":\s*)str\(result\)\[:\d+\]( if result else None.*?"domain": test_domain.*?\})',
        re.DOTALL
    )
    
    new_pattern1 = '''        # Save CrewAI agent result - complete result as-is
        try:
            from .save_json_results import serialize_crewai_result
            result_data = {
                "status": "success",
                "agent_type": "crewai",
                "result": serialize_crewai_result(result) if result else None,
                "domain": test_domain
            }'''
    
    if old_pattern1.search(content):
        content = old_pattern1.sub(new_pattern1, content)
        changed = True
    
    # Pattern 2: Simple truncation in CrewAI
    old_pattern2 = re.compile(
        r'(# Save.*CrewAI.*?"result":\s*)str\(result\)\[:\d+\]( if result else None)',
        re.MULTILINE
    )
    
    def replace_crewai_truncation(match):
        return f'{match.group(1)}serialize_crewai_result(result) if result else None'
    
    if old_pattern2.search(content):
        # Need to add import first
        if 'from .save_json_results import serialize_crewai_result' not in content:
            # Find the try block and add import before it
            content = re.sub(
                r'(# Save.*CrewAI.*?try:)',
                r'\1\n            from .save_json_results import serialize_crewai_result',
                content,
                flags=re.MULTILINE
            )
        content = old_pattern2.sub(replace_crewai_truncation, content)
        changed = True
    
    return content, changed


def update_standalone_test_saving(content: str) -> Tuple[str, bool]:
    """
    Update standalone test result saving to ensure no truncation.
    
    Returns:
        (updated_content, was_changed)
    """
    changed = False
    
    # Standalone tests should already be saving complete JSON, but check for any truncation
    old_pattern = re.compile(
        r'("result":\s*)str\(.*?\)\[:\d+\]',
        re.MULTILINE
    )
    
    if old_pattern.search(content):
        # Standalone tests should save result_data directly, not str(result)
        content = old_pattern.sub(r'\1result_data', content)
        changed = True
    
    return content, changed


def update_test_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Update a single test file.
    
    Returns:
        (was_changed, list_of_changes)
    """
    try:
        content = file_path.read_text()
        original_content = content
        changes = []
        
        # Update LangChain tests
        content, langchain_changed = update_langchain_test_saving(content)
        if langchain_changed:
            changes.append("Updated LangChain result saving")
        
        # Update CrewAI tests
        content, crewai_changed = update_crewai_test_saving(content)
        if crewai_changed:
            changes.append("Updated CrewAI result saving")
        
        # Update standalone tests
        content, standalone_changed = update_standalone_test_saving(content)
        if standalone_changed:
            changes.append("Updated standalone result saving")
        
        if content != original_content:
            file_path.write_text(content)
            return True, changes
        
        return False, []
    
    except Exception as e:
        print(f"Error updating {file_path.name}: {e}")
        return False, [f"Error: {e}"]


def main():
    """Update all test files."""
    test_files = list(TEST_DIR.glob("test_*.py"))
    test_files = [f for f in test_files if f.name not in ALREADY_UPDATED]
    
    print(f"Found {len(test_files)} test files to check")
    print(f"Already updated: {', '.join(ALREADY_UPDATED)}")
    print()
    
    updated_count = 0
    total_changes = []
    
    for test_file in sorted(test_files):
        was_changed, changes = update_test_file(test_file)
        if was_changed:
            updated_count += 1
            print(f"✅ Updated: {test_file.name}")
            for change in changes:
                print(f"   - {change}")
            total_changes.extend(changes)
        else:
            print(f"⏭️  Skipped: {test_file.name} (no changes needed or already correct)")
    
    print()
    print("="*80)
    print(f"Summary: Updated {updated_count}/{len(test_files)} files")
    print("="*80)


if __name__ == "__main__":
    main()

