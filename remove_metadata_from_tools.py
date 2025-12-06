#!/usr/bin/env python3
"""
Remove unnecessary metadata from all tool files.
Returns verbatim output only - no status, execution_method, user_id, etc.
"""

import re
from pathlib import Path

def fix_tool_file(file_path: Path):
    """Remove metadata wrappers from tool file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    changed = False
    
    # Pattern 1: Remove result_data wrappers that return stdout/stderr
    # Replace: result_data = {...} return json.dumps(result_data) with: return stdout
    pattern1 = r'result_data\s*=\s*\{[^}]*"stdout":\s*stdout[^}]*"stderr":\s*stderr[^}]*\}\s*.*?return\s+json\.dumps\(result_data[^)]*\)'
    if re.search(pattern1, content, re.DOTALL):
        # Find the stdout/stderr assignment
        stdout_match = re.search(r'stdout\s*=\s*docker_result\.get\("stdout",\s*""\)', content)
        stderr_match = re.search(r'stderr\s*=\s*docker_result\.get\("stderr",\s*""\)', content)
        
        if stdout_match:
            # Replace the entire result_data block with direct return
            replacement = 'return stdout if stdout else stderr'
            content = re.sub(
                r'result_data\s*=\s*\{[^}]*"stdout":\s*stdout[^}]*"stderr":\s*stderr[^}]*\}\s*.*?return\s+json\.dumps\(result_data[^)]*\)',
                replacement,
                content,
                flags=re.DOTALL
            )
            changed = True
    
    # Pattern 2: For JSON files - return them directly, not wrapped
    # This is already handled in sherlock/maigret, but check others
    
    # Pattern 3: Remove metadata from error returns (keep only message)
    # Replace: {"status": "error", "message": "...", "execution_method": ..., "user_id": ...}
    # With: {"status": "error", "message": "..."}
    content = re.sub(
        r'\{"status":\s*"error",\s*"message":\s*([^,}]+)(?:,\s*"[^"]+":\s*[^,}]+)*\}',
        r'{"status": "error", "message": \1}',
        content
    )
    
    if content != original:
        changed = True
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return changed

# Find all tool files
base = Path('hackerdogs_tools/osint')
tool_files = list(base.rglob('*_langchain.py')) + list(base.rglob('*_crewai.py'))

print(f"Found {len(tool_files)} tool files")
print("Removing unnecessary metadata...")

for tool_file in sorted(tool_files):
    if fix_tool_file(tool_file):
        print(f"  Fixed: {tool_file}")

print("Done!")

