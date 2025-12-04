#!/usr/bin/env python3
"""
Fix all test file imports and function names to match actual tool implementations.
"""

import re
from pathlib import Path

# Correct mapping of tool names to their actual function/class names and categories
TOOL_MAPPING = {
    "abuseipdb": {
        "langchain_func": "abuseipdb_search",
        "langchain_path": "hackerdogs_tools.osint.threat_intel.abuseipdb_langchain",
        "crewai_class": "AbuseIPDBTool",
        "crewai_path": "hackerdogs_tools.osint.threat_intel.abuseipdb_crewai"
    },
    "amass": {
        "langchain_func": "amass_enum",
        "langchain_path": "hackerdogs_tools.osint.infrastructure.amass_langchain",
        "crewai_class": "AmassTool",
        "crewai_path": "hackerdogs_tools.osint.infrastructure.amass_crewai"
    },
    "dnsdumpster": {
        "langchain_func": "dnsdumpster_search",
        "langchain_path": "hackerdogs_tools.osint.infrastructure.dnsdumpster_langchain",
        "crewai_class": "DNSDumpsterTool",
        "crewai_path": "hackerdogs_tools.osint.infrastructure.dnsdumpster_crewai"
    },
    "exiftool": {
        "langchain_func": "exiftool_search",
        "langchain_path": "hackerdogs_tools.osint.metadata.exiftool_langchain",
        "crewai_class": "ExifToolTool",
        "crewai_path": "hackerdogs_tools.osint.metadata.exiftool_crewai"
    },
    "ghunt": {
        "langchain_func": "ghunt_search",
        "langchain_path": "hackerdogs_tools.osint.identity.ghunt_langchain",
        "crewai_class": "GHuntTool",
        "crewai_path": "hackerdogs_tools.osint.identity.ghunt_crewai"
    },
    "holehe": {
        "langchain_func": "holehe_search",
        "langchain_path": "hackerdogs_tools.osint.identity.holehe_langchain",
        "crewai_class": "HoleheTool",
        "crewai_path": "hackerdogs_tools.osint.identity.holehe_crewai"
    },
    "maigret": {
        "langchain_func": "maigret_search",
        "langchain_path": "hackerdogs_tools.osint.identity.maigret_langchain",
        "crewai_class": "MaigretTool",
        "crewai_path": "hackerdogs_tools.osint.identity.maigret_crewai"
    },
    "masscan": {
        "langchain_func": "masscan_scan",
        "langchain_path": "hackerdogs_tools.osint.infrastructure.masscan_langchain",
        "crewai_class": "MasscanTool",
        "crewai_path": "hackerdogs_tools.osint.infrastructure.masscan_crewai"
    },
    "misp": {
        "langchain_func": "misp_search",
        "langchain_path": "hackerdogs_tools.osint.threat_intel.misp_langchain",
        "crewai_class": "MISPTool",
        "crewai_path": "hackerdogs_tools.osint.threat_intel.misp_crewai"
    },
    "nuclei": {
        "langchain_func": "nuclei_scan",
        "langchain_path": "hackerdogs_tools.osint.infrastructure.nuclei_langchain",
        "crewai_class": "NucleiTool",
        "crewai_path": "hackerdogs_tools.osint.infrastructure.nuclei_crewai"
    },
    "onionsearch": {
        "langchain_func": "onionsearch_search",
        "langchain_path": "hackerdogs_tools.osint.content.onionsearch_langchain",
        "crewai_class": "OnionSearchTool",
        "crewai_path": "hackerdogs_tools.osint.content.onionsearch_crewai"
    },
    "otx": {
        "langchain_func": "otx_search",
        "langchain_path": "hackerdogs_tools.osint.threat_intel.otx_langchain",
        "crewai_class": "OTXTool",
        "crewai_path": "hackerdogs_tools.osint.threat_intel.otx_crewai"
    },
    "scrapy": {
        "langchain_func": "scrapy_search",
        "langchain_path": "hackerdogs_tools.osint.content.scrapy_langchain",
        "crewai_class": "ScrapyTool",
        "crewai_path": "hackerdogs_tools.osint.content.scrapy_crewai"
    },
    "sherlock": {
        "langchain_func": "sherlock_enum",
        "langchain_path": "hackerdogs_tools.osint.identity.sherlock_langchain",
        "crewai_class": "SherlockTool",
        "crewai_path": "hackerdogs_tools.osint.identity.sherlock_crewai"
    },
    "spiderfoot": {
        "langchain_func": "spiderfoot_search",
        "langchain_path": "hackerdogs_tools.osint.frameworks.spiderfoot_langchain",
        "crewai_class": "SpiderFootTool",
        "crewai_path": "hackerdogs_tools.osint.frameworks.spiderfoot_crewai"
    },
    "subfinder": {
        "langchain_func": "subfinder_enum",
        "langchain_path": "hackerdogs_tools.osint.infrastructure.subfinder_langchain",
        "crewai_class": "SubfinderTool",
        "crewai_path": "hackerdogs_tools.osint.infrastructure.subfinder_crewai"
    },
    "theharvester": {
        "langchain_func": "theharvester_search",
        "langchain_path": "hackerdogs_tools.osint.infrastructure.theharvester_langchain",
        "crewai_class": "TheHarvesterTool",
        "crewai_path": "hackerdogs_tools.osint.infrastructure.theharvester_crewai"
    },
    "urlhaus": {
        "langchain_func": "urlhaus_search",
        "langchain_path": "hackerdogs_tools.osint.threat_intel.urlhaus_langchain",
        "crewai_class": "URLHausTool",
        "crewai_path": "hackerdogs_tools.osint.threat_intel.urlhaus_crewai"
    },
    "waybackurls": {
        "langchain_func": "waybackurls_search",
        "langchain_path": "hackerdogs_tools.osint.content.waybackurls_langchain",
        "crewai_class": "WaybackurlsTool",
        "crewai_path": "hackerdogs_tools.osint.content.waybackurls_crewai"
    },
    "yara": {
        "langchain_func": "yara_search",
        "langchain_path": "hackerdogs_tools.osint.metadata.yara_langchain",
        "crewai_class": "YARATool",
        "crewai_path": "hackerdogs_tools.osint.metadata.yara_crewai"
    },
    "zmap": {
        "langchain_func": "zmap_scan",
        "langchain_path": "hackerdogs_tools.osint.infrastructure.zmap_langchain",
        "crewai_class": "ZMapTool",
        "crewai_path": "hackerdogs_tools.osint.infrastructure.zmap_crewai"
    }
}

test_dir = Path("hackerdogs_tools/osint/tests")
test_files = sorted([f for f in test_dir.glob("test_*.py") 
                    if f.name not in ["__init__.py", "test_utils.py", "test_runtime_helper.py", 
                                     "test_all_tools.py", "save_json_results.py"]])

print(f"Fixing imports and function names in {len(test_files)} test files...\n")

for test_file in test_files:
    tool_name = test_file.stem.replace("test_", "")
    
    if tool_name not in TOOL_MAPPING:
        print(f"⚠️  {test_file.name}: Tool '{tool_name}' not in mapping, skipping")
        continue
    
    mapping = TOOL_MAPPING[tool_name]
    content = test_file.read_text()
    original = content
    
    # Fix LangChain import
    langchain_import_pattern = r'from\s+hackerdogs_tools\.osint\.[^ ]+\.' + tool_name + r'_langchain\s+import\s+\w+'
    langchain_import_new = f'from {mapping["langchain_path"]} import {mapping["langchain_func"]}'
    content = re.sub(langchain_import_pattern, langchain_import_new, content)
    
    # Fix CrewAI import
    crewai_import_pattern = r'from\s+hackerdogs_tools\.osint\.[^ ]+\.' + tool_name + r'_crewai\s+import\s+\w+'
    crewai_import_new = f'from {mapping["crewai_path"]} import {mapping["crewai_class"]}'
    content = re.sub(crewai_import_pattern, crewai_import_new, content)
    
    # Fix function name usage (replace {tool}_enum with correct function name)
    # Replace all occurrences of wrong function names
    wrong_patterns = [
        (rf'\b{tool_name}_enum\b', mapping["langchain_func"]),
        (rf'\b{tool_name}_search\b', mapping["langchain_func"]),
        (rf'\b{tool_name}_scan\b', mapping["langchain_func"]),
    ]
    
    for wrong_pattern, correct_name in wrong_patterns:
        if wrong_pattern != rf'\b{correct_name}\b':  # Don't replace if already correct
            content = re.sub(wrong_pattern, correct_name, content)
    
    # Fix class name usage
    wrong_class_patterns = [
        (rf'\b{tool_name.title()}Tool\b', mapping["crewai_class"]),
        (rf'\b{tool_name.capitalize()}Tool\b', mapping["crewai_class"]),
        (rf'\bAbuseipdbTool\b', "AbuseIPDBTool"),
        (rf'\bMispTool\b', "MISPTool"),
    ]
    
    for wrong_pattern, correct_class in wrong_class_patterns:
        if wrong_pattern != rf'\b{correct_class}\b':
            content = re.sub(wrong_pattern, correct_class, content)
    
    # Fix in run_all_tests function - replace tool name references
    content = re.sub(
        rf'\b{tool_name}_enum\b',
        mapping["langchain_func"],
        content
    )
    content = re.sub(
        rf'\b{tool_name.title()}Tool\(\)',
        f'{mapping["crewai_class"]}()',
        content
    )
    
    if content != original:
        test_file.write_text(content)
        print(f"✅ Fixed {test_file.name}")
    else:
        print(f"⚠️  {test_file.name}: No changes needed (may already be correct)")

print(f"\n✅ Fixed all {len(test_files)} test files")

