# OSINT Tools Test Suite

Comprehensive test suite for all OSINT tools with three test scenarios:
1. **Standalone** - Direct tool execution
2. **LangChain** - Tool integration with LangChain agents
3. **CrewAI** - Tool integration with CrewAI agents

## Setup

### 1. Environment Variables

Create a `.env` file in the project root with:

```bash
# Model configuration
MODEL="ollama/gemma2:2b"  # or "openai/gpt-4", "anthropic/claude-3-5-sonnet"
LLM_API_KEY="your-api-key-here"  # Required for OpenAI/Anthropic
PROVIDER_BASE_URL="http://localhost:11434"  # Required for Ollama
```

### 2. Install Dependencies

```bash
pip install -e ".[osint,test]"
```

### 3. Docker Setup (for binary tools)

```bash
cd hackerdogs_tools/osint/docker
docker build -t osint-tools:latest .
docker-compose up -d
```

## Running Tests

### ⭐ Recommended: Run by Phase (Use Case Based)

Tests are organized by execution phases based on use cases. **Start with Phase 1**:

```bash
# Phase 1: Foundation (Infrastructure Recon) - RUN FIRST
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 1

# Phase 2: Identity & Social Intelligence
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 2

# Phase 3: Threat Intelligence
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 3

# Phase 4: Content & Metadata Analysis
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 4

# Phase 5: Framework Tests
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --phase 5

# List all phases
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --list

# Run all phases sequentially
python hackerdogs_tools/osint/tests/run_tests_by_phase.py --all
```

### Run by Use Case

```bash
# Use Case #1: Attack Surface Discovery
python hackerdogs_tools/osint/tests/run_tests_by_usecase.py --usecase 1

# List all use cases
python hackerdogs_tools/osint/tests/run_tests_by_usecase.py --list

# Run all use cases
python hackerdogs_tools/osint/tests/run_tests_by_usecase.py --all
```

### Run by Agent

```bash
# Infrastructure Recon Agent
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --agent infrastructure

# Identity Hunter Agent
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --agent identity

# Threat Intel Agent
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --agent threat

# List all agents
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --list

# Run all agents
python hackerdogs_tools/osint/tests/run_tests_by_agent.py --all
```

### Run All Tests (Legacy)

```bash
python hackerdogs_tools/osint/tests/run_all_tests.py
```

### Run Individual Tool Test

```bash
python hackerdogs_tools/osint/tests/test_amass.py
python hackerdogs_tools/osint/tests/test_subfinder.py
# ... etc
```

### Run with pytest

```bash
pytest hackerdogs_tools/osint/tests/test_amass.py -v
pytest hackerdogs_tools/osint/tests/ -v
```

## Test Structure

Each test file (`test_<tool>.py`) contains:

1. **TestStandalone** - Direct tool execution test
2. **TestLangChain** - LangChain agent integration test
3. **TestCrewAI** - CrewAI agent integration test
4. **run_all_tests()** - Function to run all three scenarios

## 📋 Test Execution Plan

**See [TEST_EXECUTION_PLAN.md](TEST_EXECUTION_PLAN.md) for detailed execution strategy.**

### Quick Start Priority

1. **Phase 1 (Foundation)** - Run FIRST
   - Group 1.1: Subfinder, Amass, DNSDumpster, TheHarvester
   - Group 1.2: Nuclei, Masscan, ZMap

2. **Phase 2 (Identity)** - Run SECOND
   - Group 2.1: Sherlock, Maigret
   - Group 2.2: Holehe, GHunt

3. **Phase 3 (Threat Intel)** - Run THIRD
   - Group 3.1: AbuseIPDB, URLHaus

4. **Phase 4 (Content/Metadata)** - Run FOURTH
   - Group 4.1: Waybackurls, Scrapy
   - Group 4.2: OnionSearch
   - Group 4.3: ExifTool, YARA

5. **Phase 5 (Frameworks)** - Run LAST
   - Group 5.1: SpiderFoot

## Test Files

- `test_utils.py` - Utility functions for LLM configuration
- `test_amass.py` - Amass subdomain enumeration tests
- `test_subfinder.py` - Subfinder subdomain discovery tests
- `test_nuclei.py` - Nuclei vulnerability scanning tests
- `test_masscan.py` - Masscan port scanning tests
- `test_zmap.py` - ZMap single-packet scanning tests
- `test_theharvester.py` - TheHarvester information gathering tests
- `test_dnsdumpster.py` - DNSDumpster DNS mapping tests
- `test_sherlock.py` - Sherlock username enumeration tests
- `test_maigret.py` - Maigret username search tests
- `test_ghunt.py` - GHunt Google account investigation tests
- `test_holehe.py` - Holehe email registration check tests
- `test_scrapy.py` - Scrapy web scraping tests
- `test_waybackurls.py` - Waybackurls URL fetching tests
- `test_onionsearch.py` - OnionSearch dark web search tests
- `test_spiderfoot.py` - SpiderFoot OSINT framework tests
- `test_yara.py` - YARA pattern matching tests
- `test_exiftool.py` - ExifTool metadata extraction tests
- `test_abuseipdb.py` - AbuseIPDB IP reputation tests
- `test_urlhaus.py` - URLHaus malicious URL check tests
- `test_otx.py` - AlienVault OTX threat intelligence tests
- `test_misp.py` - MISP threat intelligence platform tests

## Expected Behavior

- **Standalone tests** should execute the tool directly and return JSON results
- **LangChain tests** should create an agent that uses the tool to answer queries
- **CrewAI tests** should create a crew with an agent that uses the tool to complete tasks

## Troubleshooting

### Docker Not Available
If Docker is not set up, standalone tests will return errors. This is expected. The tests will still validate error handling.

### LLM Configuration Issues
- Ensure `MODEL` is set correctly
- For Ollama: Ensure `PROVIDER_BASE_URL` points to your Ollama instance
- For OpenAI/Anthropic: Ensure `LLM_API_KEY` is set

### Import Errors
- Ensure the package is installed: `pip install -e .`
- Check that all dependencies are installed: `pip install -e ".[osint]"`

