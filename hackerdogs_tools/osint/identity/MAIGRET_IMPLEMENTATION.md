# Maigret Tool Implementation

## Overview

Maigret has been fully implemented following the same pattern as Sherlock, providing advanced username search with metadata extraction across 3000+ sites.

## Implementation Details

### Docker Image
- **Official Image**: `soxoj/maigret:latest`
- Added to `docker_client.py` official_images dictionary
- Uses Docker volume mounting for report outputs (`/app/reports`)

### Features Implemented

#### Core Functionality
- ✅ Multiple username support (list of usernames)
- ✅ Profile page parsing and metadata extraction
- ✅ Recursive search by additional data extracted from pages
- ✅ Support for 3000+ sites

#### Report Formats
All 7 report formats are supported:
- `txt` - Text report (one per username)
- `csv` - CSV report (one per username)
- `html` - HTML report (general report on all usernames)
- `xmind` - XMind 8 mindmap report (one per username)
- `pdf` - PDF report (general report on all usernames)
- `graph` - Graph report (general report on all usernames)
- `json` - JSON report with two types:
  - `simple` - Single JSON object with all sites
  - `ndjson` - Newline-delimited JSON (one per username)

#### Site Filtering Options
- `all_sites` - Use all available sites (3000+)
- `top_sites` - Count of sites ranked by Alexa Top (default: 500, range: 1-3000)
- `tags` - Comma-separated tags to filter sites (e.g., "photo,dating" or "us")
- `sites` - List of specific site names to limit analysis to
- `use_disabled_sites` - Use disabled sites (may cause false positives)

#### Performance Options
- `timeout` - Time in seconds to wait for response (default: 30, range: 1-300)
- `retries` - Attempts to restart failed requests (default: 3, range: 0-10)
- `max_connections` - Concurrent connections (default: 100, range: 1-1000)

#### Advanced Features
- `no_recursion` - Disable recursive search by additional data
- `no_extracting` - Disable parsing pages for additional data
- `with_domains` - Enable experimental domain checking on usernames
- `permute` - Permute at least 2 usernames to generate more possibilities

#### Proxy Support
- `proxy` - Make requests over a proxy (e.g., "socks5://127.0.0.1:1080")
- `tor_proxy` - Specify Tor gateway URL (default: "socks5://127.0.0.1:9050")
- `i2p_proxy` - Specify I2P gateway URL (default: "http://127.0.0.1:4444")

#### Output Options
- `print_not_found` - Print sites where username was not found
- `print_errors` - Print error messages (connection, captcha, country ban, etc.)
- `verbose` - Display extra information and metrics

### JSON Output Parsing

The tool correctly parses Maigret's JSON output format:
```json
{
  "SiteName": {
    "username": "testuser",
    "url_user": "https://...",
    "url_main": "https://...",
    "status": {
      "username": "testuser",
      "site_name": "SiteName",
      "url": "https://...",
      "status": "Claimed",
      "ids": {},
      "tags": ["video"]
    },
    "http_status": 200,
    ...
  }
}
```

The parser extracts:
- Site name
- User URL and main URL
- Status (Claimed/Not Found)
- IDs (extracted metadata)
- Tags (site categories)
- HTTP status code

### File Naming

Maigret saves reports with the pattern: `report_{username}_{type}.json`
- Example: `report_testuser_simple.json`
- The tool handles both the official naming and fallback to `{username}.json`

### Timeout Calculation

The execution timeout is calculated based on:
- Number of sites to check (top_sites or 3000 for all_sites)
- Timeout per request
- Max concurrent connections
- Retries
- Buffer time (300 seconds)

Formula: `(timeout * estimated_sites / max_connections) + (retries * timeout) + 300`
Capped at 3600 seconds (1 hour)

## Files Created/Modified

1. **`hackerdogs_tools/osint/identity/maigret_langchain.py`**
   - LangChain tool implementation with `@tool` decorator
   - Full parameter support
   - JSON parsing logic

2. **`hackerdogs_tools/osint/identity/maigret_crewai.py`**
   - CrewAI tool implementation with `BaseTool`
   - Full parameter support
   - JSON parsing logic

3. **`hackerdogs_tools/osint/docker_client.py`**
   - Added `"maigret": "soxoj/maigret:latest"` to official_images

4. **`hackerdogs_tools/osint/identity/__init__.py`**
   - Already had imports (no changes needed)

## Usage Examples

### LangChain
```python
from hackerdogs_tools.osint.identity.maigret_langchain import maigret_search

result = maigret_search.invoke({
    "runtime": runtime,
    "usernames": ["testuser"],
    "report_format": "json",
    "json_type": "simple",
    "top_sites": 100,
    "timeout": 30
})
```

### CrewAI
```python
from hackerdogs_tools.osint.identity.maigret_crewai import MaigretTool

tool = MaigretTool()
result = tool._run(
    usernames=["testuser"],
    report_format="json",
    json_type="simple",
    top_sites=100,
    timeout=30
)
```

## Testing

The implementation follows the same pattern as Sherlock and should be tested with:
1. Standalone execution
2. LangChain agent integration
3. CrewAI agent integration

Test files should be created following the pattern in `test_sherlock.py`.

## References

- **GitHub**: https://github.com/soxoj/maigret
- **Documentation**: https://maigret.readthedocs.io/
- **Docker Image**: `soxoj/maigret:latest`
- **Command-line Options**: https://maigret.readthedocs.io/en/latest/command-line-options.html

