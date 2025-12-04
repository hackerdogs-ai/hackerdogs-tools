# OSINT Tools Test Execution Plan

## Overview

This document outlines the test execution strategy based on the 10 OSINT use cases and multi-agent system architecture. Tests are grouped by use case and prioritized by dependency order.

---

## 🎯 Test Execution Priority

### Phase 1: Foundation Tests (Run First)
**Priority: CRITICAL** - These tools are foundational and used by other agents

#### Group 1.1: Infrastructure Recon Core
**Use Case:** #1 - Attack Surface Discovery  
**Agent:** Infrastructure_Recon_Agent  
**Dependencies:** None  
**Execution Order:**
1. `test_subfinder.py` - Fast passive discovery (quickest)
2. `test_amass.py` - Deep subdomain enumeration
3. `test_dnsdumpster.py` - DNS mapping
4. `test_theharvester.py` - Email/host discovery

**Why First:** These tools discover targets that other tools will analyze.

---

#### Group 1.2: Vulnerability & Port Scanning
**Use Case:** #8 - Vulnerability Triage  
**Agent:** Infrastructure_Recon_Agent  
**Dependencies:** Requires subdomains from Group 1.1  
**Execution Order:**
1. `test_nuclei.py` - Vulnerability scanning
2. `test_masscan.py` - Port scanning (fast)
3. `test_zmap.py` - Single-packet scanning

**Why Second:** These tools analyze targets discovered in Phase 1.

---

### Phase 2: Identity & Social Intelligence
**Priority: HIGH** - Identity tools are independent but critical

#### Group 2.1: Username Enumeration
**Use Case:** #6 - Username Enumeration (SOCMINT)  
**Agent:** Identity_Hunter_Agent  
**Dependencies:** None  
**Execution Order:**
1. `test_sherlock.py` - Basic username search (300+ sites)
2. `test_maigret.py` - Advanced username search with metadata

**Why Third:** Independent identity discovery.

---

#### Group 2.2: Email Investigation
**Use Case:** #2 - Executive Protection (VIP Vetting), #5 - Breach Intelligence  
**Agent:** Identity_Hunter_Agent  
**Dependencies:** None  
**Execution Order:**
1. `test_holehe.py` - Email registration check (120+ sites)
2. `test_ghunt.py` - Google account investigation

**Why Fourth:** Email-based identity discovery.

---

### Phase 3: Threat Intelligence
**Priority: HIGH** - Threat intel validates findings from other phases

#### Group 3.1: Threat Reputation Checks
**Use Case:** #3 - Brand Impersonation Detection, #4 - Supply Chain Risk  
**Agent:** Threat_Intel_Agent  
**Dependencies:** Can use results from Phase 1 & 2  
**Execution Order:**
1. `test_abuseipdb.py` - IP reputation checking
2. `test_urlhaus.py` - Malicious URL database check
3. `test_otx.py` - Open Threat Exchange (if implemented)
4. `test_misp.py` - MISP threat intelligence (if implemented)

**Why Fifth:** Validates and enriches findings from infrastructure and identity phases.

---

### Phase 4: Content & Metadata Analysis
**Priority: MEDIUM** - Specialized analysis tools

#### Group 4.1: Content Discovery
**Use Case:** #7 - Cloud Bucket Exposure  
**Agent:** Infrastructure_Recon_Agent  
**Dependencies:** None  
**Execution Order:**
1. `test_waybackurls.py` - Historical URL discovery
2. `test_scrapy.py` - Custom web scraping framework

**Why Sixth:** Content discovery and historical analysis.

---

#### Group 4.2: Dark Web Intelligence
**Use Case:** #9 - Dark Web Monitoring  
**Agent:** Threat_Intel_Agent  
**Dependencies:** None  
**Execution Order:**
1. `test_onionsearch.py` - Dark web search engines

**Why Seventh:** Specialized dark web intelligence.

---

#### Group 4.3: File & Metadata Analysis
**Use Case:** #10 - Geospatial Recon (GEOINT)  
**Agent:** Infrastructure_Recon_Agent  
**Dependencies:** None  
**Execution Order:**
1. `test_exiftool.py` - Image/PDF metadata extraction
2. `test_yara.py` - Pattern matching for malware classification

**Why Eighth:** File and metadata analysis.

---

### Phase 5: Framework Tests
**Priority: LOW** - Comprehensive frameworks (run last)

#### Group 5.1: All-in-One Framework
**Use Case:** Multiple (comprehensive OSINT)  
**Agent:** All Agents  
**Dependencies:** Can use results from all previous phases  
**Execution Order:**
1. `test_spiderfoot.py` - Comprehensive OSINT framework

**Why Last:** Framework that aggregates multiple sources, best tested after individual tools.

---

## 📊 Test Execution Matrix

| Phase | Group | Use Case | Tools | Priority | Dependencies |
|-------|-------|----------|-------|----------|--------------|
| 1 | 1.1 | #1 Attack Surface Discovery | Subfinder, Amass, DNSDumpster, TheHarvester | CRITICAL | None |
| 1 | 1.2 | #8 Vulnerability Triage | Nuclei, Masscan, ZMap | CRITICAL | Subdomains from 1.1 |
| 2 | 2.1 | #6 Username Enumeration | Sherlock, Maigret | HIGH | None |
| 2 | 2.2 | #2, #5 VIP/Breach Intel | Holehe, GHunt | HIGH | None |
| 3 | 3.1 | #3, #4 Brand/Supply Chain | AbuseIPDB, URLHaus, OTX, MISP | HIGH | Can use Phase 1 & 2 results |
| 4 | 4.1 | #7 Cloud Bucket Exposure | Waybackurls, Scrapy | MEDIUM | None |
| 4 | 4.2 | #9 Dark Web Monitoring | OnionSearch | MEDIUM | None |
| 4 | 4.3 | #10 Geospatial Recon | ExifTool, YARA | MEDIUM | None |
| 5 | 5.1 | Multiple (Comprehensive) | SpiderFoot | LOW | All previous phases |

---

## 🚀 Quick Start: Run Tests by Use Case

### Option 1: Run by Phase (Recommended)

```bash
# Phase 1: Foundation (Infrastructure)
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 1

# Phase 2: Identity
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 2

# Phase 3: Threat Intelligence
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 3

# Phase 4: Content & Metadata
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 4

# Phase 5: Frameworks
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 5
```

### Option 2: Run by Use Case

```bash
# Use Case #1: Attack Surface Discovery
python hackerdogs_tools/osint/tests/run_tests_by_usecase.py --usecase 1

# Use Case #2: Executive Protection
python hackerdogs_tools/osint/tests/run_tests_by_usecase.py --usecase 2

# ... etc
```

### Option 3: Run by Agent

```bash
# Infrastructure Recon Agent
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --agent infrastructure

# Identity Hunter Agent
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --agent identity

# Threat Intel Agent
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --agent threat
```

---

## 📋 Detailed Test Groups

### Phase 1: Foundation Tests

#### Group 1.1: Infrastructure Recon Core
**Execution Time:** ~15-20 minutes  
**Tests:**
- `test_subfinder.py` - Fast passive subdomain discovery
- `test_amass.py` - Deep subdomain enumeration
- `test_dnsdumpster.py` - DNS mapping
- `test_theharvester.py` - Email/host discovery

**Expected Results:**
- Subfinder: Fast JSON output with subdomains
- Amass: Comprehensive subdomain list with IPs
- DNSDumpster: DNS record mapping
- TheHarvester: Emails, subdomains, hosts

#### Group 1.2: Vulnerability & Port Scanning
**Execution Time:** ~20-30 minutes  
**Tests:**
- `test_nuclei.py` - Vulnerability scanning
- `test_masscan.py` - Port scanning
- `test_zmap.py` - Single-packet scanning

**Expected Results:**
- Nuclei: JSONL with vulnerability findings
- Masscan: JSON with open ports
- ZMap: JSON with scan results

---

### Phase 2: Identity & Social Intelligence

#### Group 2.1: Username Enumeration
**Execution Time:** ~10-15 minutes  
**Tests:**
- `test_sherlock.py` - Username search (300+ sites)
- `test_maigret.py` - Advanced username search

**Expected Results:**
- Sherlock: JSON with found profiles
- Maigret: JSON with profiles and metadata

#### Group 2.2: Email Investigation
**Execution Time:** ~10-15 minutes  
**Tests:**
- `test_holehe.py` - Email registration check
- `test_ghunt.py` - Google account investigation

**Expected Results:**
- Holehe: JSON with registered sites
- GHunt: JSON with Google account details

---

### Phase 3: Threat Intelligence

#### Group 3.1: Threat Reputation Checks
**Execution Time:** ~10-15 minutes  
**Tests:**
- `test_abuseipdb.py` - IP reputation
- `test_urlhaus.py` - Malicious URL check
- `test_otx.py` - OTX threat intel (AlienVault Open Threat Exchange)
- `test_misp.py` - MISP platform (Malware Information Sharing Platform)

**Expected Results:**
- AbuseIPDB: JSON with IP reputation score
- URLHaus: JSON with URL threat status
- OTX: JSON with threat pulses and verdict (MALICIOUS/CLEAN)
- MISP: JSON with threat events and attributes

---

### Phase 4: Content & Metadata Analysis

#### Group 4.1: Content Discovery
**Execution Time:** ~10-15 minutes  
**Tests:**
- `test_waybackurls.py` - Historical URLs
- `test_scrapy.py` - Web scraping

**Expected Results:**
- Waybackurls: JSON with historical URLs
- Scrapy: JSON with scraped content

#### Group 4.2: Dark Web Intelligence
**Execution Time:** ~5-10 minutes  
**Tests:**
- `test_onionsearch.py` - Dark web search

**Expected Results:**
- OnionSearch: JSON with dark web results

#### Group 4.3: File & Metadata Analysis
**Execution Time:** ~5-10 minutes  
**Tests:**
- `test_exiftool.py` - Metadata extraction
- `test_yara.py` - Pattern matching

**Expected Results:**
- ExifTool: JSON with EXIF metadata
- YARA: JSON with pattern matches

---

### Phase 5: Framework Tests

#### Group 5.1: All-in-One Framework
**Execution Time:** ~20-30 minutes  
**Tests:**
- `test_spiderfoot.py` - Comprehensive OSINT

**Expected Results:**
- SpiderFoot: JSON with comprehensive OSINT results

---

## ⚠️ Important Notes

1. **Docker Required:** Most binary tools require Docker. Ensure Docker is running before Phase 1.
2. **Rate Limiting:** Some tools (Masscan, ZMap) are "loud" - use carefully in production.
3. **API Keys:** Threat intel tools (AbuseIPDB, OTX) may require API keys.
4. **Test Data:** Use test domains/emails (e.g., "example.com", "test@example.com") to avoid rate limits.
5. **Execution Time:** Total test suite execution time: ~2-3 hours (if run sequentially).

---

## 🔄 Continuous Integration Strategy

For CI/CD, run tests in this order:
1. **Smoke Tests:** Phase 1, Group 1.1 (Subfinder, Amass) - Quick validation
2. **Full Suite:** All phases sequentially
3. **Integration Tests:** Run by use case to validate workflows

---

## 📈 Success Criteria

- ✅ All Phase 1 tests pass (foundation)
- ✅ All Phase 2 tests pass (identity)
- ✅ All Phase 3 tests pass (threat intel)
- ✅ All Phase 4 tests pass (content/metadata)
- ✅ All Phase 5 tests pass (frameworks)
- ✅ No crashes or unhandled exceptions
- ✅ All tools return valid JSON

---

*Last Updated: 2024*

