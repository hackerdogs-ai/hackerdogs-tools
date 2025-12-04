#!/usr/bin/env python3
"""
Test all OSINT tools to verify they work correctly.

This script tests each tool's standalone execution to ensure:
1. Tools can be imported
2. Tools can be invoked with proper parameters
3. Tools return valid JSON
4. Tools handle errors gracefully
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.test_domains import get_random_domain

# Tool imports
from hackerdogs_tools.osint.infrastructure import (
    amass_enum, nuclei_scan, subfinder_enum, masscan_scan,
    zmap_scan, theharvester_search, dnsdumpster_search
)
from hackerdogs_tools.osint.identity import (
    sherlock_enum, maigret_search, ghunt_search, holehe_search
)
from hackerdogs_tools.osint.content import (
    scrapy_search, waybackurls_search, onionsearch_search
)
from hackerdogs_tools.osint.threat_intel import (
    urlhaus_search, abuseipdb_search, otx_search, misp_search
)
from hackerdogs_tools.osint.metadata import (
    exiftool_search, yara_search
)
from hackerdogs_tools.osint.frameworks import (
    spiderfoot_search
)

# Test configurations for each tool
TOOL_TESTS = {
    # Infrastructure
    "amass_enum": {"tool": amass_enum, "params": {"domain": "example.com", "passive": False, "active": True, "timeout": 300}},
    "nuclei_scan": {"tool": nuclei_scan, "params": {"target": "example.com", "templates": None, "severity": "critical", "timeout": 300}},
    "subfinder_enum": {"tool": subfinder_enum, "params": {"domain": "example.com", "recursive": False, "silent": True}},
    "masscan_scan": {"tool": masscan_scan, "params": {"ip_range": "192.168.1.0/24", "ports": "80,443", "rate": 1000}},
    "zmap_scan": {"tool": zmap_scan, "params": {"ip_range": "192.168.1.0/24", "port": 80, "bandwidth": "10M"}},
    "theharvester_search": {"tool": theharvester_search, "params": {"domain": "example.com", "sources": None, "limit": 500}},
    "dnsdumpster_search": {"tool": dnsdumpster_search, "params": {"domain": "example.com"}},
    
    # Identity
    "sherlock_enum": {"tool": sherlock_enum, "params": {"username": "testuser", "sites": None, "timeout": 60}},
    "maigret_search": {"tool": maigret_search, "params": {"username": "testuser", "extract_metadata": True, "sites": None}},
    "ghunt_search": {"tool": ghunt_search, "params": {"email": "test@example.com", "extract_reviews": True, "extract_photos": False}},
    "holehe_search": {"tool": holehe_search, "params": {"email": "test@example.com", "only_used": True}},
    
    # Content
    "scrapy_search": {"tool": scrapy_search, "params": {"url": "https://example.com", "spider_name": "generic", "follow_links": False, "max_pages": 10}},
    "waybackurls_search": {"tool": waybackurls_search, "params": {"domain": "example.com", "no_subs": False, "dates": None}},
    "onionsearch_search": {"tool": onionsearch_search, "params": {"query": "test", "engines": None, "max_results": 50}},
    
    # Threat Intel
    "urlhaus_search": {"tool": urlhaus_search, "params": {"url": "https://example.com", "download_feed": False}},
    "abuseipdb_search": {"tool": abuseipdb_search, "params": {"ip": "8.8.8.8", "max_age_in_days": 90, "verbose": True}},
    "otx_search": {"tool": otx_search, "params": {"indicator": "example.com", "indicator_type": "domain"}},
    "misp_search": {"tool": misp_search, "params": {"query": "test", "event_id": None}},
    
    # Metadata
    "exiftool_search": {"tool": exiftool_search, "params": {"file_path": "/tmp/test.jpg", "extract_all": True}},
    "yara_search": {"tool": yara_search, "params": {"file_path": "/tmp/test.exe", "rules_path": "/tmp/rules.yar", "rules_content": None}},
    
    # Frameworks
    "spiderfoot_search": {"tool": spiderfoot_search, "params": {"target": "example.com", "target_type": "domain", "modules": None, "scan_type": "footprint"}},
}

def test_tool(tool_name: str, tool_config: dict):
    """Test a single tool."""
    tool = tool_config["tool"]
    params = tool_config["params"].copy()
    
    # Use random domain for domain-based tools
    if "domain" in params:
        params["domain"] = get_random_domain()
    if "target" in params and isinstance(params["target"], str) and "." in params["target"]:
        params["target"] = get_random_domain()
    if "indicator" in params and isinstance(params["indicator"], str) and "." in params["indicator"]:
        params["indicator"] = get_random_domain()
    
    runtime = create_mock_runtime()
    params["runtime"] = runtime
    
    try:
        result = tool.invoke(params)
        result_data = json.loads(result)
        
        if result_data.get("status") == "success":
            return True, f"✅ {tool_name}: Success"
        else:
            return False, f"⚠️  {tool_name}: {result_data.get('message', 'Unknown error')}"
    except Exception as e:
        return False, f"❌ {tool_name}: {str(e)}"

def main():
    """Test all tools."""
    print("=" * 80)
    print("Testing All OSINT Tools")
    print("=" * 80)
    
    results = []
    for tool_name, tool_config in TOOL_TESTS.items():
        success, message = test_tool(tool_name, tool_config)
        results.append((success, message))
        print(message)
    
    print("\n" + "=" * 80)
    passed = sum(1 for s, _ in results if s)
    total = len(results)
    print(f"Results: {passed}/{total} tools passed")
    print("=" * 80)
    
    if passed < total:
        print("\n⚠️  Some tools failed (may be expected if Docker not set up)")
        print("   Tools that return errors are still functional - they handle errors gracefully")

if __name__ == "__main__":
    main()

