# OSINT Tests Quick Start Guide

## 🚀 Start Here: Run Tests in Order

### Step 1: Foundation Tests (Run FIRST)

These are the core infrastructure tools that discover targets:

```bash
# Phase 1, Group 1.1: Infrastructure Recon Core
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 1 --group 1.1
```

**Tests:** Subfinder → Amass → DNSDumpster → TheHarvester

**Why First:** These tools discover subdomains and infrastructure that other tools analyze.

---

### Step 2: Vulnerability Scanning

After discovering targets, scan for vulnerabilities:

```bash
# Phase 1, Group 1.2: Vulnerability & Port Scanning
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 1 --group 1.2
```

**Tests:** Nuclei → Masscan → ZMap

**Why Second:** These tools analyze targets discovered in Step 1.

---

### Step 3: Identity Discovery

Independent identity tools:

```bash
# Phase 2: Identity & Social Intelligence
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 2
```

**Tests:** Sherlock → Maigret → Holehe → GHunt

**Why Third:** Identity tools are independent but critical.

---

### Step 4: Threat Intelligence

Validate findings with threat intel:

```bash
# Phase 3: Threat Intelligence
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 3
```

**Tests:** AbuseIPDB → URLHaus → OTX → MISP

**Why Fourth:** Validates and enriches findings from previous phases.

---

### Step 5: Content & Metadata

Specialized analysis tools:

```bash
# Phase 4: Content & Metadata Analysis
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 4
```

**Tests:** Waybackurls → Scrapy → OnionSearch → ExifTool → YARA

**Why Fifth:** Specialized tools for content and file analysis.

---

### Step 6: Framework Tests

Comprehensive framework (run last):

```bash
# Phase 5: Framework Tests
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 5
```

**Tests:** SpiderFoot

**Why Last:** Framework aggregates multiple sources, best tested after individual tools.

---

## 📊 Test Execution Summary

| Phase | Priority | Time | Tools |
|-------|----------|------|-------|
| 1.1 | CRITICAL | ~15-20 min | Subfinder, Amass, DNSDumpster, TheHarvester |
| 1.2 | CRITICAL | ~20-30 min | Nuclei, Masscan, ZMap |
| 2 | HIGH | ~20-30 min | Sherlock, Maigret, Holehe, GHunt |
| 3 | HIGH | ~10-15 min | AbuseIPDB, URLHaus, OTX, MISP |
| 4 | MEDIUM | ~20-30 min | Waybackurls, Scrapy, OnionSearch, ExifTool, YARA |
| 5 | LOW | ~20-30 min | SpiderFoot |

**Total Time:** ~2-3 hours (if run sequentially)

---

## 🎯 Run by Use Case

If you want to test a specific use case:

```bash
# Use Case #1: Attack Surface Discovery
python hackerdogs_tools/osint/tests/run_tests_by_usecase.py --usecase 1

# Use Case #2: Executive Protection
python hackerdogs_tools/osint/tests/run_tests_by_usecase.py --usecase 2

# ... etc
```

---

## 🤖 Run by Agent

If you want to test all tools for a specific agent:

```bash
# Infrastructure Recon Agent (The Mapper)
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --agent infrastructure

# Identity Hunter Agent (The Detective)
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --agent identity

# Threat Intel Agent (The Defender)
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --agent threat
```

---

## ⚡ Quick Commands

```bash
# List all phases
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --list

# List all use cases
python hackerdogs_tools/osint/tests/run_tests_by_usecase.py --list

# List all agents
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --list

# Run everything (all phases)
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --all
```

---

## 📚 More Information

- **Detailed Plan:** See [TEST_EXECUTION_PLAN.md](TEST_EXECUTION_PLAN.md)
- **Full Documentation:** See [README.md](README.md)

