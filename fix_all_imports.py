#!/usr/bin/env python3
"""
Fix all import mismatches in __init__.py files by checking actual function names.
"""

import re
from pathlib import Path
import ast

def get_function_names(file_path: Path):
    """Get all function names from a Python file."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        return functions
    except:
        return []

def fix_init_file(init_file: Path):
    """Fix imports in an __init__.py file."""
    content = init_file.read_text()
    original = content
    
    # Find all from .xxx import yyy patterns
    pattern = r'from \.([a-z_]+_langchain) import ([a-z_]+)'
    
    def replace_import(match):
        module_name = match.group(1)
        imported_name = match.group(2)
        
        # Find the actual langchain file
        langchain_file = init_file.parent / f"{module_name}.py"
        if langchain_file.exists():
            functions = get_function_names(langchain_file)
            if functions:
                # Use the first function (usually the main one)
                actual_name = functions[0]
                if actual_name != imported_name:
                    print(f"  Fixing {init_file.name}: {imported_name} -> {actual_name}")
                    return f"from .{module_name} import {actual_name}"
        return match.group(0)
    
    new_content = re.sub(pattern, replace_import, content)
    
    if new_content != original:
        init_file.write_text(new_content)
        return True
    return False

if __name__ == "__main__":
    osint_dir = Path("hackerdogs_tools/osint")
    fixed = 0
    
    for init_file in osint_dir.rglob("__init__.py"):
        if fix_init_file(init_file):
            fixed += 1
    
    print(f"\n✅ Fixed {fixed} __init__.py files")

