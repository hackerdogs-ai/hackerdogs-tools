#!/usr/bin/env python3
"""
Properly fix all __init__.py imports by finding @tool decorated functions.
"""

import re
from pathlib import Path

def get_tool_function_name(file_path: Path):
    """Get the @tool decorated function name from a file."""
    try:
        content = file_path.read_text()
        # Look for @tool followed by def function_name
        pattern = r'@tool\s+def\s+([a-z_]+)\('
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(1)
    except:
        pass
    return None

# Map of correct function names
CORRECT_NAMES = {
    'infrastructure': {
        'amass_langchain': 'amass_enum',
        'nuclei_langchain': 'nuclei_scan',
        'subfinder_langchain': 'subfinder_enum',
        'masscan_langchain': 'masscan_scan',
        'zmap_langchain': 'zmap_scan',
        'theharvester_langchain': 'theharvester_search',
        'dnsdumpster_langchain': 'dnsdumpster_search',
    },
    'identity': {
        'sherlock_langchain': 'sherlock_enum',
        'maigret_langchain': 'maigret_search',
        'ghunt_langchain': 'ghunt_search',
        'holehe_langchain': 'holehe_search',
    },
    'content': {
        'scrapy_langchain': 'scrapy_scrape',
        'waybackurls_langchain': 'waybackurls_query',
        'onionsearch_langchain': 'onionsearch_query',
    },
    'threat_intel': {
        'otx_langchain': 'otx_query',
        'misp_langchain': 'misp_query',
        'urlhaus_langchain': 'urlhaus_check',
        'abuseipdb_langchain': 'abuseipdb_check',
    },
    'metadata': {
        'exiftool_langchain': 'exiftool_extract',
        'yara_langchain': 'yara_search',
    },
    'frameworks': {
        'spiderfoot_langchain': 'spiderfoot_scan',
    },
}

def fix_init_file(init_file: Path, category: str):
    """Fix imports in an __init__.py file."""
    content = init_file.read_text()
    original = content
    
    # Fix each import
    for module_name, correct_func in CORRECT_NAMES.get(category, {}).items():
        # Pattern: from .module_name import wrong_name
        pattern = rf'from \.{module_name} import [a-z_]+'
        replacement = f'from .{module_name} import {correct_func}'
        content = re.sub(pattern, replacement, content)
        
        # Also fix in __all__ if present
        pattern = rf'"{module_name.replace("_langchain", "")}_[a-z_]+"'
        # This is trickier, let's just fix the common ones manually
    
    if content != original:
        init_file.write_text(content)
        return True
    return False

if __name__ == "__main__":
    osint_dir = Path("hackerdogs_tools/osint")
    fixed = 0
    
    for category in ['infrastructure', 'identity', 'content', 'threat_intel', 'metadata', 'frameworks']:
        init_file = osint_dir / category / "__init__.py"
        if init_file.exists():
            if fix_init_file(init_file, category):
                fixed += 1
                print(f"✅ Fixed {category}/__init__.py")
    
    print(f"\n✅ Fixed {fixed} __init__.py files")

