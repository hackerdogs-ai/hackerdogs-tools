#!/usr/bin/env python3
"""
Fix LangChain 1.x imports in test files.
Removes AgentExecutor (doesn't exist in 1.x) and updates agent invocation.
"""

import re
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_FILES = list(TEST_DIR.glob("test_*.py"))

def fix_file(file_path: Path):
    """Fix imports and agent executor usage in a test file."""
    content = file_path.read_text()
    original = content
    
    # Fix import: remove AgentExecutor
    content = re.sub(
        r'from langchain\.agents import create_agent, AgentExecutor',
        'from langchain.agents import create_agent',
        content
    )
    
    # Fix AgentExecutor usage - replace with direct agent invocation
    # Pattern: executor = AgentExecutor(...) ... executor.invoke(...)
    # Replace with: agent.invoke(...)
    
    # Find and replace AgentExecutor pattern
    pattern = r'# Create agent executor\s+executor = AgentExecutor\(\s+agent=agent,\s+tools=\[.*?\],\s+verbose=True\s+\)\s+.*?# Execute query\s+result = executor\.invoke\('
    
    replacement = r'# Execute query directly (agent is a runnable in LangChain 1.x)\n        result = agent.invoke('
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Also handle simpler pattern without the comment
    content = re.sub(
        r'executor = AgentExecutor\(\s+agent=agent,\s+tools=\[.*?\],\s+verbose=True\s+\)',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Replace executor.invoke with agent.invoke
    content = re.sub(r'executor\.invoke\(', 'agent.invoke(', content)
    
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

