# 🎯 OSINT Tools Implementation PRD
## Product Requirements Document for Multi-Agent OSINT System

**Version:** 1.0  
**Date:** 2024  
**Status:** Planning  
**Target Repositories:** 
- `hackerdogs-tools` (LangChain & CrewAI implementations)
- Reference: `langchain-community` & `crewai-tools`

---

## 📋 Executive Summary

This PRD outlines the implementation of 20+ Open Source Intelligence (OSINT) tools as LangChain and CrewAI-compatible tools. These tools will enable AI agents to perform comprehensive OSINT operations across infrastructure reconnaissance, identity hunting, threat intelligence, and content analysis.

### Key Objectives
1. **Implement 20+ OSINT tools** as both LangChain (`*_langchain.py`) and CrewAI (`*_crewai.py`) tools
2. **Support multi-agent workflows** with specialized agents (Infrastructure, Identity, Threat Intel)
3. **Ensure JSON output** for AI pipeline integration
4. **Maintain security best practices** (rate limiting, proxy support, error handling)
5. **Follow existing tool patterns** from `langchain-community` and `crewai-tools`

---

## 🏗️ Architecture Overview

### Tool Categories

| Category | Tools | Primary Agent | Count |
|----------|-------|---------------|-------|
| **Infrastructure & Network Recon** | Amass, Nuclei, Subfinder, Masscan, ZMap, TheHarvester, DNSDumpster | Infrastructure_Recon_Agent | 7 |
| **Person & Identity (SOCMINT)** | Sherlock, Maigret, GHunt, Holehe | Identity_Hunter_Agent | 4 |
| **Content & Dark Web** | Scrapy, Waybackurls, OnionSearch | Infrastructure_Recon_Agent / Threat_Intel_Agent | 3 |
| **Threat Intelligence Feeds** | OTX, URLHaus, MISP, AbuseIPDB | Threat_Intel_Agent | 4 |
| **File & Metadata Analysis** | ExifTool, YARA | Infrastructure_Recon_Agent / Threat_Intel_Agent | 2 |
| **All-in-One Framework** | SpiderFoot | All Agents | 1 |
| **TOTAL** | | | **21** |

---

## 📦 Tool Specifications

### Category 1: Infrastructure & Network Recon

#### 1.1 OWASP Amass Tool
- **LangChain File:** `amass_langchain.py`
- **CrewAI File:** `amass_crewai.py`
- **Description:** Subdomain enumeration and asset mapping
- **Command:** `amass enum -json report.json`
- **Input Schema:**
  - `domain: str` - Target domain (e.g., "tesla.com")
  - `passive: bool` - Use passive enumeration only (default: False)
  - `active: bool` - Use active enumeration (default: True)
  - `timeout: int` - Timeout in seconds (default: 300)
- **Output:** JSON with subdomains, IPs, and network graph
- **Dependencies:** `amass` (binary), `subprocess`
- **Env Vars:** None (self-hosted binary)

#### 1.2 Nuclei Tool
- **LangChain File:** `nuclei_langchain.py`
- **CrewAI File:** `nuclei_crewai.py`
- **Description:** Template-based vulnerability scanner
- **Command:** `nuclei -u <target> -jsonl -o output.jsonl`
- **Input Schema:**
  - `target: str` - URL or IP to scan
  - `templates: Optional[List[str]]` - Specific template IDs (default: all)
  - `severity: Optional[str]` - Filter by severity (info, low, medium, high, critical)
  - `tags: Optional[List[str]]` - Filter by tags
- **Output:** JSONL with vulnerability findings
- **Dependencies:** `nuclei` (binary), `subprocess`
- **Env Vars:** None

#### 1.3 Subfinder Tool
- **LangChain File:** `subfinder_langchain.py`
- **CrewAI File:** `subfinder_crewai.py`
- **Description:** Fast passive subdomain discovery
- **Command:** `subfinder -d <domain> -oJ -`
- **Input Schema:**
  - `domain: str` - Target domain
  - `recursive: bool` - Recursive enumeration (default: False)
  - `silent: bool` - Silent mode (default: True)
- **Output:** JSON array of subdomains
- **Dependencies:** `subfinder` (binary), `subprocess`
- **Env Vars:** None

#### 1.4 Masscan Tool
- **LangChain File:** `masscan_langchain.py`
- **CrewAI File:** `masscan_crewai.py`
- **Description:** Fast Internet port scanner
- **Command:** `masscan <ip_range> -p <ports> -oJ output.json`
- **Input Schema:**
  - `ip_range: str` - IP range or CIDR (e.g., "192.168.1.0/24")
  - `ports: str` - Port range (e.g., "1-1000" or "80,443,8080")
  - `rate: int` - Packets per second (default: 1000, max: 10000)
- **Output:** JSON with open ports and services
- **Dependencies:** `masscan` (binary), `subprocess`
- **Env Vars:** None
- **⚠️ Warning:** Rate limiting required, may be "loud"

#### 1.5 ZMap Tool
- **LangChain File:** `zmap_langchain.py`
- **CrewAI File:** `zmap_crewai.py`
- **Description:** Single-packet scanning
- **Command:** `zmap -p <port> <ip_range> -o output.csv`
- **Input Schema:**
  - `ip_range: str` - IP range or CIDR
  - `port: int` - Target port
  - `bandwidth: str` - Bandwidth limit (e.g., "10M")
- **Output:** CSV/JSON with scan results
- **Dependencies:** `zmap` (binary), `subprocess`
- **Env Vars:** None

#### 1.6 TheHarvester Tool
- **LangChain File:** `theharvester_langchain.py`
- **CrewAI File:** `theharvester_crewai.py`
- **Description:** Gathers emails, subdomains, hosts, employee names from search engines
- **Command:** `theHarvester -d <domain> -f filename -o json`
- **Input Schema:**
  - `domain: str` - Target domain
  - `sources: Optional[List[str]]` - Data sources (google, bing, linkedin, etc.)
  - `limit: int` - Result limit (default: 500)
- **Output:** JSON with emails, subdomains, hosts, names
- **Dependencies:** `theHarvester` (Python package), `subprocess`
- **Env Vars:** None

#### 1.7 DNSDumpster Tool
- **LangChain File:** `dnsdumpster_langchain.py`
- **CrewAI File:** `dnsdumpster_crewai.py`
- **Description:** DNS mapping via DNSDumpster API
- **API:** Unofficial Python wrapper or web scraping
- **Input Schema:**
  - `domain: str` - Target domain
- **Output:** JSON with DNS records, subdomains, MX records
- **Dependencies:** `requests`, `beautifulsoup4` (or API wrapper)
- **Env Vars:** None (free API)

---

### Category 2: Person & Identity (SOCMINT)

#### 2.1 Sherlock Tool
- **LangChain File:** `sherlock_langchain.py`
- **CrewAI File:** `sherlock_crewai.py`
- **Description:** Username enumeration across 300+ social media sites
- **Command:** `python3 sherlock --json <username>`
- **Input Schema:**
  - `username: str` - Username to search
  - `sites: Optional[List[str]]` - Specific sites to check (default: all)
  - `timeout: int` - Request timeout (default: 60)
- **Output:** JSON with found profiles and URLs
- **Dependencies:** `sherlock-project` (Python package), `subprocess`
- **Env Vars:** None
- **⚠️ Warning:** Requires proxy rotation for production

#### 2.2 Maigret Tool
- **LangChain File:** `maigret_langchain.py`
- **CrewAI File:** `maigret_crewai.py`
- **Description:** Advanced username search with metadata extraction
- **Command:** `maigret <username> --json`
- **Input Schema:**
  - `username: str` - Username to search
  - `extract_metadata: bool` - Extract profile metadata (default: True)
  - `sites: Optional[List[str]]` - Specific sites (default: all)
- **Output:** JSON with profiles, metadata, IDs, names
- **Dependencies:** `maigret` (Python package), `subprocess`
- **Env Vars:** None

#### 2.3 GHunt Tool
- **LangChain File:** `ghunt_langchain.py`
- **CrewAI File:** `ghunt_crewai.py`
- **Description:** Google Account investigation from Gmail address
- **Command:** `ghunt email <email>`
- **Input Schema:**
  - `email: str` - Gmail address
  - `extract_reviews: bool` - Extract Google Maps reviews (default: True)
  - `extract_photos: bool` - Extract Google Photos (default: False)
- **Output:** JSON with name, reviews, photos, calendar details
- **Dependencies:** `ghunt` (Python package), `subprocess`
- **Env Vars:** None
- **⚠️ Warning:** Requires Google session cookies

#### 2.4 Holehe Tool
- **LangChain File:** `holehe_langchain.py`
- **CrewAI File:** `holehe_crewai.py`
- **Description:** Check email registration on 120+ sites via "forgot password"
- **Command:** `holehe <email>`
- **Input Schema:**
  - `email: str` - Email address to check
  - `only_used: bool` - Return only sites where email is registered (default: True)
- **Output:** JSON with site names and registration status
- **Dependencies:** `holehe` (Python package), `subprocess`
- **Env Vars:** None

---

### Category 3: Content & Dark Web

#### 3.1 Scrapy Framework Tool
- **LangChain File:** `scrapy_langchain.py`
- **CrewAI File:** `scrapy_crewai.py`
- **Description:** Custom web scraping framework wrapper
- **Note:** Not a direct tool, but a framework wrapper for building custom scrapers
- **Input Schema:**
  - `url: str` - Target URL
  - `spider_name: str` - Spider name or "generic"
  - `follow_links: bool` - Follow links (default: False)
  - `max_pages: int` - Maximum pages to scrape (default: 10)
- **Output:** JSON with scraped content
- **Dependencies:** `scrapy` (Python package)
- **Env Vars:** None

#### 3.2 Waybackurls Tool
- **LangChain File:** `waybackurls_langchain.py`
- **CrewAI File:** `waybackurls_crewai.py`
- **Description:** Fetch all known URLs for a domain from Wayback Machine
- **Command:** `waybackurls <domain>`
- **Input Schema:**
  - `domain: str` - Target domain
  - `no_subs: bool` - Exclude subdomains (default: False)
  - `dates: Optional[str]` - Date range filter (e.g., "20180101-20181231")
- **Output:** JSON array of URLs
- **Dependencies:** `waybackurls` (Go binary), `subprocess`
- **Env Vars:** None

#### 3.3 OnionSearch Tool
- **LangChain File:** `onionsearch_langchain.py`
- **CrewAI File:** `onionsearch_crewai.py`
- **Description:** Scrape Dark Web search engines (Ahmia, Torch, etc.)
- **Command:** `onionsearch <query>`
- **Input Schema:**
  - `query: str` - Search query
  - `engines: Optional[List[str]]` - Search engines (ahmia, torch, etc.)
  - `max_results: int` - Maximum results (default: 50)
- **Output:** JSON with search results and URLs
- **Dependencies:** `onionsearch` (Python package), `subprocess`
- **Env Vars:** None
- **⚠️ Warning:** Requires Tor proxy configuration

---

### Category 4: Threat Intelligence Feeds

#### 4.1 AlienVault OTX Tool
- **LangChain File:** `otx_langchain.py` (may already exist)
- **CrewAI File:** `otx_crewai.py`
- **Description:** Query AlienVault Open Threat Exchange
- **API:** REST API
- **Input Schema:**
  - `indicator: str` - IP, domain, hash, or URL
  - `indicator_type: str` - Type: "IPv4", "domain", "hostname", "url", "hash"
- **Output:** JSON with pulses, tags, reputation
- **Dependencies:** `OTXv2` (Python package), `requests`
- **Env Vars:** `OTX_API_KEY` (optional, free tier available)

#### 4.2 URLHaus Tool
- **LangChain File:** `urlhaus_langchain.py`
- **CrewAI File:** `urlhaus_crewai.py`
- **Description:** Check if URL is in malicious URL database
- **API:** CSV download or API
- **Input Schema:**
  - `url: str` - URL to check
  - `download_feed: bool` - Download full feed (default: False)
- **Output:** JSON with threat status and metadata
- **Dependencies:** `requests`, `csv`
- **Env Vars:** None

#### 4.3 MISP Tool
- **LangChain File:** `misp_langchain.py` (may already exist)
- **CrewAI File:** `misp_crewai.py`
- **Description:** Query self-hosted MISP threat intelligence platform
- **API:** MISP REST API
- **Input Schema:**
  - `query: str` - Search query (indicator, tag, etc.)
  - `query_type: str` - Type: "indicator", "event", "attribute", "tag"
  - `limit: int` - Result limit (default: 100)
- **Output:** JSON with MISP events and attributes
- **Dependencies:** `pymisp` (Python package)
- **Env Vars:** `MISP_URL`, `MISP_API_KEY`

#### 4.4 AbuseIPDB Tool
- **LangChain File:** `abuseipdb_langchain.py`
- **CrewAI File:** `abuseipdb_crewai.py`
- **Description:** IP reputation and abuse checking
- **API:** AbuseIPDB REST API
- **Input Schema:**
  - `ip: str` - IP address
  - `max_age_in_days: int` - Maximum age of reports (default: 90)
  - `verbose: bool` - Include verbose output (default: True)
- **Output:** JSON with confidence score (0-100) and abuse categories
- **Dependencies:** `requests`
- **Env Vars:** `ABUSEIPDB_API_KEY`

---

### Category 5: File & Metadata Analysis

#### 5.1 ExifTool Tool
- **LangChain File:** `exiftool_langchain.py`
- **CrewAI File:** `exiftool_crewai.py`
- **Description:** Extract metadata from images/PDFs (GPS, author, software)
- **Command:** `exiftool -j <file>`
- **Input Schema:**
  - `file_path: str` - Path to file
  - `extract_gps: bool` - Extract GPS coordinates (default: True)
  - `extract_author: bool` - Extract author information (default: True)
- **Output:** JSON with all metadata fields
- **Dependencies:** `exiftool` (binary), `subprocess`
- **Env Vars:** None

#### 5.2 YARA Tool
- **LangChain File:** `yara_langchain.py`
- **CrewAI File:** `yara_crewai.py`
- **Description:** Pattern matching for malware classification
- **Command:** `yara -s <rules> <file>`
- **Input Schema:**
  - `file_path: str` - Path to file to scan
  - `rules_path: str` - Path to YARA rules file
  - `rules_content: Optional[str]` - Inline YARA rules
- **Output:** JSON with matched rules and strings
- **Dependencies:** `yara-python` (Python package)
- **Env Vars:** None

---

### Category 6: All-in-One Framework

#### 6.1 SpiderFoot Tool
- **LangChain File:** `spiderfoot_langchain.py`
- **CrewAI File:** `spiderfoot_crewai.py`
- **Description:** Comprehensive OSINT framework aggregating 50+ sources
- **API:** SpiderFoot REST API (self-hosted)
- **Input Schema:**
  - `target: str` - Target (domain, IP, email, etc.)
  - `target_type: str` - Type: "domain", "ip", "email", "username"
  - `modules: Optional[List[str]]` - Specific modules to run (default: all)
  - `scan_type: str` - "footprint" or "investigate" (default: "footprint")
- **Output:** JSON with comprehensive OSINT data
- **Dependencies:** `requests` (for API), or `spiderfoot` (Python package)
- **Env Vars:** `SPIDERFOOT_URL`, `SPIDERFOOT_API_KEY` (if using API)

---

## 🔧 Technical Requirements

### Code Structure

#### LangChain Tools Pattern
```python
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, List

class ToolInput(BaseModel):
    """Input schema for Tool."""
    param1: str = Field(..., description="Description")
    param2: Optional[int] = Field(default=10, description="Optional param")

class ToolLangChain(BaseTool):
    name: str = "tool_name"
    description: str = "Tool description for LLM"
    args_schema: type[BaseModel] = ToolInput
    
    def _run(
        self,
        param1: str,
        param2: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute tool and return JSON string."""
        # Implementation
        return json.dumps(result)
```

#### CrewAI Tools Pattern
```python
from crewai.tools import BaseTool, EnvVar
from pydantic import BaseModel, Field
from typing import Any, List

class ToolInput(BaseModel):
    """Input schema for Tool."""
    param1: str = Field(..., description="Description")
    param2: int = Field(default=10, ge=1, le=100, description="Optional param")

class ToolCrewAI(BaseTool):
    name: str = "Tool Name"
    description: str = "Tool description for agent"
    args_schema: type[BaseModel] = ToolInput
    
    env_vars: List[EnvVar] = [
        EnvVar(name="API_KEY", description="API key", required=True),
    ]
    package_dependencies: List[str] = ["package-name"]
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Validate env vars and dependencies
    
    def _run(self, param1: str, param2: int = 10, **kwargs: Any) -> str:
        """Execute tool and return JSON string."""
        # Implementation
        return json.dumps(result)
```

### Common Requirements

1. **JSON Output:** All tools must return JSON strings for AI pipeline integration
2. **Error Handling:** Comprehensive try/except with clear error messages
3. **Logging:** Use structured logging (e.g., `hd_logging`)
4. **Rate Limiting:** Implement rate limiting for tools that make external requests
5. **Proxy Support:** Tools that scrape websites must support proxy configuration
6. **Timeout Handling:** All subprocess calls must have timeouts
7. **Input Validation:** Validate all inputs using Pydantic schemas
8. **Async Support:** Implement `_arun()` for async contexts (LangChain)

### Dependencies Management

- **Binary Tools:** Document installation requirements in README
- **Python Packages:** Add to `requirements.txt` or `pyproject.toml`
- **Optional Dependencies:** Use `try/except ImportError` with helpful messages
- **Environment Variables:** Document all required/optional env vars

### Security Considerations

1. **API Keys:** Never hardcode, use environment variables
2. **Proxy Rotation:** Required for tools that scrape (Sherlock, GHunt, etc.)
3. **Rate Limiting:** Prevent IP bans and API abuse
4. **Input Sanitization:** Validate and sanitize all user inputs
5. **Subprocess Security:** Use `shell=False` and validate command arguments
6. **Error Messages:** Don't expose sensitive information in error messages

---

## 📁 File Structure

```
hackerdogs_tools/
├── osint/
│   ├── __init__.py
│   ├── top10-scenarios.md
│   ├── OSINT_TOOLS_PRD.md (this file)
│   ├── IMPLEMENTATION_TRACKER.md
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── amass_langchain.py
│   │   ├── amass_crewai.py
│   │   ├── nuclei_langchain.py
│   │   ├── nuclei_crewai.py
│   │   ├── subfinder_langchain.py
│   │   ├── subfinder_crewai.py
│   │   ├── masscan_langchain.py
│   │   ├── masscan_crewai.py
│   │   ├── zmap_langchain.py
│   │   ├── zmap_crewai.py
│   │   ├── theharvester_langchain.py
│   │   ├── theharvester_crewai.py
│   │   ├── dnsdumpster_langchain.py
│   │   ├── dnsdumpster_crewai.py
│   │   └── README.md
│   │
│   ├── identity/
│   │   ├── __init__.py
│   │   ├── sherlock_langchain.py
│   │   ├── sherlock_crewai.py
│   │   ├── maigret_langchain.py
│   │   ├── maigret_crewai.py
│   │   ├── ghunt_langchain.py
│   │   ├── ghunt_crewai.py
│   │   ├── holehe_langchain.py
│   │   ├── holehe_crewai.py
│   │   └── README.md
│   │
│   ├── content/
│   │   ├── __init__.py
│   │   ├── scrapy_langchain.py
│   │   ├── scrapy_crewai.py
│   │   ├── waybackurls_langchain.py
│   │   ├── waybackurls_crewai.py
│   │   ├── onionsearch_langchain.py
│   │   ├── onionsearch_crewai.py
│   │   └── README.md
│   │
│   ├── threat_intel/
│   │   ├── __init__.py
│   │   ├── otx_langchain.py (may exist in ti/)
│   │   ├── otx_crewai.py
│   │   ├── urlhaus_langchain.py
│   │   ├── urlhaus_crewai.py
│   │   ├── misp_langchain.py (may exist in ti/)
│   │   ├── misp_crewai.py
│   │   ├── abuseipdb_langchain.py
│   │   ├── abuseipdb_crewai.py
│   │   └── README.md
│   │
│   ├── metadata/
│   │   ├── __init__.py
│   │   ├── exiftool_langchain.py
│   │   ├── exiftool_crewai.py
│   │   ├── yara_langchain.py
│   │   ├── yara_crewai.py
│   │   └── README.md
│   │
│   └── frameworks/
│       ├── __init__.py
│       ├── spiderfoot_langchain.py
│       ├── spiderfoot_crewai.py
│       └── README.md
│
└── tests/
    └── osint/
        ├── __init__.py
        ├── test_infrastructure_tools.py
        ├── test_identity_tools.py
        ├── test_content_tools.py
        ├── test_threat_intel_tools.py
        ├── test_metadata_tools.py
        └── test_frameworks_tools.py
```

---

## 🧪 Testing Requirements

### Unit Tests
- Mock subprocess calls and API requests
- Test input validation
- Test error handling
- Test JSON output format

### Integration Tests
- Test with real binaries (if available in CI)
- Test API integrations (with test keys)
- Test error scenarios

### Test Structure
```python
import pytest
from unittest.mock import patch, MagicMock
from hackerdogs_tools.osint.infrastructure.amass_langchain import AmassLangChain

class TestAmassLangChain:
    def test_input_validation(self):
        """Test that invalid inputs are rejected."""
        pass
    
    @patch('subprocess.run')
    def test_successful_enumeration(self, mock_subprocess):
        """Test successful subdomain enumeration."""
        pass
    
    def test_json_output_format(self):
        """Test that output is valid JSON."""
        pass
```

---

## 📚 Documentation Requirements

### Per-Tool Documentation
Each tool must have:
1. **README.md** in its category folder with:
   - Tool description
   - Installation instructions
   - Usage examples
   - Required environment variables
   - Input/output schemas
   - Known limitations

2. **Docstrings** in code:
   - Class-level docstring with full description
   - Method docstrings with parameters and return types
   - Example usage in docstrings

### Main Documentation
- Update main `README.md` with OSINT tools section
- Add examples for multi-agent workflows
- Document agent-to-tool mapping

---

## 🚀 Implementation Phases

### Phase 1: Infrastructure Tools (Weeks 1-2)
- Amass, Subfinder, Nuclei, TheHarvester
- **Priority:** High (core functionality)

### Phase 2: Identity Tools (Weeks 3-4)
- Sherlock, Maigret, GHunt, Holehe
- **Priority:** High (core functionality)

### Phase 3: Threat Intelligence (Weeks 5-6)
- OTX, URLHaus, AbuseIPDB, MISP
- **Priority:** Medium (some may already exist)

### Phase 4: Content & Metadata (Weeks 7-8)
- Scrapy, Waybackurls, OnionSearch, ExifTool, YARA
- **Priority:** Medium

### Phase 5: Frameworks & Polish (Weeks 9-10)
- SpiderFoot, comprehensive testing, documentation
- **Priority:** Low (nice-to-have)

---

## ✅ Success Criteria

1. **All 21 tools implemented** as both LangChain and CrewAI tools
2. **100% test coverage** for core functionality
3. **Complete documentation** for all tools
4. **Multi-agent workflows** demonstrated with examples
5. **JSON output** validated for all tools
6. **Error handling** comprehensive and user-friendly
7. **Security best practices** implemented (rate limiting, proxies, etc.)

---

## 🔄 Maintenance & Updates

- **Versioning:** Follow semantic versioning
- **Changelog:** Maintain CHANGELOG.md for each category
- **Dependencies:** Keep dependencies up-to-date
- **Security:** Regular security audits of subprocess calls and API integrations
- **Performance:** Monitor and optimize slow tools (Amass, Nuclei)

---

## 📞 Support & Questions

For questions or issues:
- Create GitHub issues with `[OSINT]` prefix
- Reference this PRD in discussions
- Update PRD as requirements evolve

---

## 📚 Related Documentation

- **Recon Scenarios & Automation:** See `RECON_SCENARIOS.md` for detailed reconnaissance workflows, API key configuration guides, and automation examples based on real-world bug bounty methodologies.
  - Source: https://dhiyaneshgeek.github.io/bug/bounty/2020/02/06/recon-with-me/
  - Includes: 15+ free API key sources, automation workflows, and integration examples

---

**Last Updated:** 2024  
**Next Review:** After Phase 1 completion

