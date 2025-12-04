"""
Script to update all test files to use random domains from test_domains module.

This replaces hardcoded "example.com" with random real domains from opendns-random-domains.txt
"""

import re
from pathlib import Path

# Test files directory
TEST_DIR = Path(__file__).parent

# Patterns to replace
REPLACEMENTS = [
    # Import statements
    (
        r'from hackerdogs_tools\.osint\.tests\.test_utils import',
        r'from hackerdogs_tools.osint.tests.test_utils import\nfrom hackerdogs_tools.osint.test_domains import get_random_domain'
    ),
    # Domain in standalone tests
    (
        r'domain="example\.com"',
        r'test_domain = get_random_domain()\n        result = tool_call(\n            runtime=runtime,\n            domain=test_domain'
    ),
    # Domain in function calls (simpler replacement)
    (
        r'domain="example\.com"',
        r'domain=get_random_domain()'
    ),
    # URL with example.com
    (
        r'url="https://example\.com"',
        r'url=f"https://{get_random_domain()}"'
    ),
    (
        r'target="https://example\.com"',
        r'target=f"https://{get_random_domain()}"'
    ),
    # Domain in messages
    (
        r'example\.com',
        r'{test_domain}'
    ),
    # Email addresses
    (
        r'email="test@example\.com"',
        r'email=f"test@{get_random_domain()}"'
    ),
]

def update_test_file(file_path: Path):
    """Update a single test file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if already updated
        if 'from hackerdogs_tools.osint.test_domains import' in content:
            print(f"⏭️  {file_path.name} - Already updated")
            return False
        
        # Add import if not present
        if 'from hackerdogs_tools.osint.test_domains import' not in content:
            # Find the test_utils import line
            if 'from hackerdogs_tools.osint.tests.test_utils import' in content:
                content = content.replace(
                    'from hackerdogs_tools.osint.tests.test_utils import',
                    'from hackerdogs_tools.osint.tests.test_utils import\nfrom hackerdogs_tools.osint.test_domains import get_random_domain'
                )
        
        # Replace example.com with get_random_domain() calls
        # First, handle standalone test methods
        content = re.sub(
            r'(def test_\w+_standalone\(self\):.*?)(domain="example\.com")',
            r'\1test_domain = get_random_domain()\n        \n        result = \w+\(\n            runtime=runtime,\n            domain=test_domain',
            content,
            flags=re.DOTALL
        )
        
        # Replace simple domain="example.com" patterns
        content = re.sub(
            r'domain="example\.com"',
            r'domain=get_random_domain()',
            content
        )
        
        # Replace URL patterns
        content = re.sub(
            r'url="https://example\.com"',
            r'url=f"https://{get_random_domain()}"',
            content
        )
        content = re.sub(
            r'target="https://example\.com"',
            r'target=f"https://{get_random_domain()}"',
            content
        )
        
        # Replace email patterns
        content = re.sub(
            r'email="test@example\.com"',
            r'email=f"test@{get_random_domain()}"',
            content
        )
        
        # Replace in message strings (need to add test_domain variable first)
        # This is more complex - we'll do it per method
        if 'example.com' in content and 'test_domain = get_random_domain()' not in content:
            # Find methods that use example.com in messages
            methods = re.finditer(
                r'(def test_\w+_langchain_agent\(self, agent\):.*?)(HumanMessage\(content="[^"]*example\.com[^"]*"\))',
                content,
                flags=re.DOTALL
            )
            for match in methods:
                method_start = match.start(1)
                # Add test_domain before the message
                insert_pos = content.find('HumanMessage', method_start)
                if insert_pos > 0:
                    # Check if test_domain already defined in this method
                    method_content = content[method_start:insert_pos]
                    if 'test_domain = get_random_domain()' not in method_content:
                        content = content[:insert_pos] + '        test_domain = get_random_domain()\n        \n        ' + content[insert_pos:]
                        # Now replace example.com in the message
                        content = content.replace(
                            'HumanMessage(content="',
                            'HumanMessage(content=f"',
                            1
                        )
                        content = re.sub(
                            r'HumanMessage\(content=f"([^"]*)example\.com([^"]*)"\)',
                            r'HumanMessage(content=f"\1{test_domain}\2")',
                            content,
                            count=1
                        )
        
        # Similar for CrewAI tasks
        if 'example.com' in content:
            content = re.sub(
                r'description="([^"]*)example\.com([^"]*)"',
                r'description=f"\1{test_domain}\2"',
                content
            )
            # Ensure test_domain is defined before Task
            if 'description=f"' in content and 'test_domain = get_random_domain()' not in content:
                # Find Task creation
                task_matches = list(re.finditer(r'def test_\w+_crewai_agent\(self, agent, llm\):', content))
                for match in task_matches:
                    method_start = match.end()
                    # Find Task( in this method
                    task_pos = content.find('task = Task(', method_start)
                    if task_pos > 0:
                        method_content = content[method_start:task_pos]
                        if 'test_domain = get_random_domain()' not in method_content:
                            content = content[:task_pos] + '        test_domain = get_random_domain()\n        \n        ' + content[task_pos:]
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path.name} - Updated")
            return True
        else:
            print(f"⏭️  {file_path.name} - No changes needed")
            return False
            
    except Exception as e:
        print(f"❌ {file_path.name} - Error: {e}")
        return False


def main():
    """Update all test files."""
    test_files = list(TEST_DIR.glob("test_*.py"))
    test_files = [f for f in test_files if f.name != "test_utils.py" and f.name != "test_subfinder.py"]  # Skip utils and already updated
    
    print(f"Found {len(test_files)} test files to update")
    print("=" * 60)
    
    updated = 0
    for test_file in test_files:
        if update_test_file(test_file):
            updated += 1
    
    print("=" * 60)
    print(f"Updated {updated} files")
    print("\nNote: Some files may need manual review for complex patterns")


if __name__ == "__main__":
    main()

