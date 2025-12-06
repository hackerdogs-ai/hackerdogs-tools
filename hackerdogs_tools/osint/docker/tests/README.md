# OSINT Tools Docker Container Test Suite

Comprehensive test suite to verify all installed tools in the `osint-tools` Docker container.

## Overview

This test suite validates that all OSINT tools are correctly installed and functional in the Docker container using `docker exec` mode.

## Test Categories

### 1. Go Tools (`test_go_tools.py`)
Tests Go-based binary tools:
- ✅ **Amass** - Subdomain enumeration
- ✅ **Nuclei** - Vulnerability scanner
- ✅ **Subfinder** - Fast subdomain discovery
- ✅ **waybackurls** - Wayback Machine URL fetcher

### 2. System Tools (`test_system_tools.py`)
Tests system-installed binary tools:
- ✅ **Masscan** - Port scanner
- ✅ **ZMap** - Single-packet scanner
- ✅ **YARA** - Pattern matching
- ✅ **ExifTool** - Metadata extraction

### 3. Python Tools (`test_python_tools.py`)
Tests Python-based tools (both modules and CLI):
- ✅ **sublist3r** - Subdomain enumeration
- ✅ **dnsrecon** - DNS enumeration
- ✅ **theHarvester** - Information gathering
- ✅ **sherlock-project** - Username enumeration
- ✅ **maigret** - Advanced username search
- ✅ **ghunt** - Google account investigation
- ✅ **holehe** - Email registration checker
- ✅ **scrapy** - Web scraping framework
- ✅ **waybackpy** - Wayback Machine API
- ✅ **internetarchive** - Internet Archive API
- ✅ **exifread** - EXIF metadata reader
- ✅ **piexif** - EXIF manipulation
- ✅ **yara-python** - YARA Python bindings

## Prerequisites

1. **Docker container must be built and running:**
   ```bash
   cd hackerdogs_tools/osint/docker
   docker build -t osint-tools:latest .
   docker-compose up -d
   ```

2. **Verify container is running:**
   ```bash
   docker ps | grep osint-tools
   ```

## Running Tests

### Run All Tests (Recommended)

```bash
cd hackerdogs_tools/osint/docker/tests
python3 run_all_tests.py
```

This will:
- Check if the container is running
- Run all three test suites sequentially
- Display a summary of results
- Save detailed results to a JSON file

### Run Individual Test Suites

```bash
# Test Go tools only
python3 test_go_tools.py

# Test system tools only
python3 test_system_tools.py

# Test Python tools only
python3 test_python_tools.py
```

### Make Scripts Executable

```bash
chmod +x test_go_tools.py test_system_tools.py test_python_tools.py run_all_tests.py
```

Then run directly:
```bash
./run_all_tests.py
```

## Test Output

### Console Output

```
================================================================================
OSINT Tools Docker Container Test Suite
================================================================================
Container: osint-tools
Test directory: /path/to/tests
Timestamp: 2025-12-06T12:00:00

✅ Container 'osint-tools' is running

================================================================================
Running Go Tools Tests
================================================================================
  Testing Amass...
    ✅ Amass: Amass Version 4.2.0
  Testing Nuclei...
    ✅ Nuclei: nuclei version 3.2.0
  ...

✅ All Go tools passed!
```

### JSON Results File

Results are saved to `test_results_YYYYMMDD_HHMMSS.json` with detailed information:

```json
{
  "timestamp": "2025-12-06T12:00:00",
  "container": "osint-tools",
  "overall_success": true,
  "summary": {
    "total_tests": 21,
    "passed_tests": 21,
    "failed_tests": 0
  },
  "results": {
    "Go Tools": { ... },
    "System Tools": { ... },
    "Python Tools": { ... }
  }
}
```

## Test Details

### How Tests Work

1. **Container Check**: Verifies `osint-tools` container is running
2. **Tool Execution**: Uses `docker exec osint-tools <tool> <args>` to test each tool
3. **Result Validation**: Checks return codes, output content, and error messages
4. **Summary Report**: Provides pass/fail status for each tool

### Test Methods

- **Version Checks**: Most tools tested with `--version` or `-version` flags
- **Help Checks**: CLI tools tested with `--help` or `-h` flags
- **Import Tests**: Python modules tested with `python3 -c "import module; print('OK')"`

## Troubleshooting

### Container Not Running

```
❌ ERROR: Container 'osint-tools' is not running!

To start the container:
  cd hackerdogs_tools/osint/docker
  docker-compose up -d
```

### Tool Not Found

If a tool test fails with "command not found":
1. Check if the tool is installed in the Dockerfile
2. Verify the tool's binary path is in `$PATH`
3. Rebuild the Docker image: `docker build -t osint-tools:latest .`

### Import Errors (Python Tools)

If a Python module import fails:
1. Check if the package is listed in Dockerfile `pip3 install` section
2. Verify the package name matches the import name
3. Rebuild the Docker image

## Integration with CI/CD

The test suite can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Build Docker image
  run: |
    cd hackerdogs_tools/osint/docker
    docker build -t osint-tools:latest .

- name: Start container
  run: docker-compose up -d

- name: Run tests
  run: |
    cd hackerdogs_tools/osint/docker/tests
    python3 run_all_tests.py
```

## Adding New Tools

To add tests for new tools:

1. **For Go/System tools**: Add test function to `test_go_tools.py` or `test_system_tools.py`
2. **For Python tools**: Add to `test_python_tools.py` module list
3. **Update README**: Add tool to the appropriate category list

Example:
```python
def test_new_tool() -> Tuple[bool, str]:
    """Test NewTool."""
    print("  Testing NewTool...")
    result = run_docker_exec("newtool", ["--version"], timeout=10)
    if result["status"] == "success":
        return True, f"✅ NewTool: {result['stdout'].strip()[:50]}"
    else:
        return False, f"❌ NewTool failed: {result['stderr']}"
```

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

Useful for scripting:
```bash
python3 run_all_tests.py && echo "All tests passed!" || echo "Tests failed!"
```

