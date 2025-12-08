# SpiderFoot Module Execution - What's Not Implemented

## Current Status

**What's Generated**: ✅ Complete tool boilerplate
- LangChain tool functions with correct signatures
- CrewAI tool classes with Pydantic schemas
- API key handling
- Error handling and logging
- Docker client integration
- Result JSON structure

**What's Missing**: ❌ Actual SpiderFoot module execution

## The Gap: Lines 90-113 in Generated Tools

Currently, all generated tools have this placeholder code:

```python
# Build command arguments for SpiderFoot module
# Note: This is a placeholder - actual execution method depends on module type
# Options: Direct Python import, Docker CLI, or API call
# For now, using Docker execution pattern similar to other tools

# TODO: Implement actual SpiderFoot module execution
# This may require:
# 1. Importing SpiderFoot module class directly
# 2. Creating SpiderFootEvent objects
# 3. Calling handleEvent() method
# 4. Collecting produced events as results

# Placeholder: Execute via Docker (if SpiderFoot CLI is available)
# args = ["python3", "-m", "spiderfoot.cli", "--module", "sfp_dnsbrute", "--target", target]
# docker_result = execute_in_docker("python3", args, timeout=300)

# For now, return placeholder indicating implementation needed
result_data = {
    "message": "SpiderFoot module execution not yet implemented",
    "module": "sfp_dnsbrute",
    "target": target,
    "note": "This tool needs to be implemented with actual SpiderFoot module execution logic"
}
```

## What Needs to Be Implemented

### Option 1: Direct Python Import (Recommended for Simple Modules)

**What it means:**
- Import the actual SpiderFoot module class (e.g., `from spiderfoot.modules.sfp_dnsbrute import sfp_dnsbrute`)
- Instantiate the module class
- Configure it with options (API keys, settings)
- Create a `SpiderFootEvent` object representing the input target
- Call the module's `handleEvent()` method
- Collect the events produced by the module
- Convert those events to JSON results

**Example Implementation:**
```python
# Import SpiderFoot module
from spiderfoot.modules.sfp_dnsbrute import sfp_dnsbrute
from spiderfoot import SpiderFootEvent, SpiderFootTarget

# Create module instance
module = sfp_dnsbrute()

# Configure module with options
module.setup({
    'skipcommonwildcard': skipcommonwildcard,
    'domainonly': domainonly,
    'commons': commons,
    # ... other options
})

# Create target
target_obj = SpiderFootTarget(target)

# Create input event
input_event = SpiderFootEvent(
    eventType="DOMAIN_NAME",
    eventData=target,
    module="sfp_dnsbrute",
    sourceEvent=None
)

# Execute module
module.handleEvent(input_event)

# Collect produced events
results = []
for event in module.producedEvents():
    results.append({
        "event_type": event.eventType,
        "data": event.eventData,
        "confidence": event.confidence,
        "risk": event.risk
    })

result_data = {
    "module": "sfp_dnsbrute",
    "target": target,
    "events": results
}
```

**Challenges:**
- Requires SpiderFoot Python package to be installed
- Need to handle SpiderFoot's event-driven architecture
- Modules may depend on SpiderFoot database for caching
- Some modules require full SpiderFoot environment

### Option 2: Docker Execution (For Complex Modules)

**What it means:**
- Run SpiderFoot CLI via Docker container
- Pass module name and target as command-line arguments
- Parse JSON/CSV output from SpiderFoot CLI
- Return parsed results

**Example Implementation:**
```python
# Execute via Docker
args = [
    "python3", "-m", "spiderfoot.cli",
    "--module", "sfp_dnsbrute",
    "--target", target,
    "--format", "json"
]
docker_result = execute_in_docker("python3", args, timeout=300)

if docker_result["status"] == "success":
    # Parse JSON output
    result_data = json.loads(docker_result["stdout"])
else:
    result_data = {"error": docker_result.get("stderr", "Unknown error")}
```

**Challenges:**
- SpiderFoot CLI may not support all modules
- Output format may vary
- Slower than direct import
- Requires Docker

### Option 3: Direct API Calls (For API-Based Modules)

**What it means:**
- For modules like `sfp_abuseipdb` and `sfp_virustotal`
- Bypass SpiderFoot module entirely
- Call the external API directly (AbuseIPDB API, VirusTotal API)
- Return API response as-is

**Example Implementation:**
```python
# For sfp_abuseipdb
import requests

api_url = f"https://api.abuseipdb.com/api/v2/check"
headers = {"Key": api_key, "Accept": "application/json"}
params = {"ipAddress": target, "maxAgeInDays": 90}

response = requests.get(api_url, headers=headers, params=params)
result_data = response.json()
```

**Challenges:**
- Need to understand each API's format
- May lose SpiderFoot-specific processing
- Only works for API-based modules

## Why It's Not Implemented Yet

1. **Architecture Decision Needed**: Which execution method(s) to use?
   - Direct import: Fastest, but requires SpiderFoot dependencies
   - Docker: Isolated, but slower
   - API calls: Fastest for APIs, but bypasses SpiderFoot

2. **Event System Complexity**: SpiderFoot uses event-driven architecture
   - Modules produce events that feed into other modules
   - Need to handle event creation and collection
   - Some modules depend on previous events

3. **Dependency Management**: 
   - Direct import requires SpiderFoot Python package
   - Need to ensure compatibility with existing environment
   - May conflict with other dependencies

4. **Testing Strategy**:
   - Need to test with real SpiderFoot modules
   - Verify event production and collection
   - Ensure results match SpiderFoot's native output

## Next Steps to Implement

1. **Choose Execution Method(s)**:
   - Start with Option 3 (Direct API) for API-based modules
   - Use Option 1 (Direct Import) for simple modules
   - Use Option 2 (Docker) as fallback

2. **Create Execution Helper Functions**:
   ```python
   def execute_spiderfoot_module(module_name, target, options):
       """Execute SpiderFoot module and return results."""
       # Implementation here
   ```

3. **Update Templates**:
   - Replace placeholder code with actual execution calls
   - Handle different execution methods based on module type

4. **Test with Real Modules**:
   - Test with `sfp_dnsbrute` (simple DNS module)
   - Test with `sfp_abuseipdb` (API-based module)
   - Test with `sfp_whois` (simple lookup module)

## Current Workaround

The tools currently return placeholder JSON indicating execution is not implemented. This allows:
- ✅ Testing tool structure and integration
- ✅ Validating LangChain/CrewAI agent integration
- ✅ Verifying result format and saving
- ❌ No actual OSINT data collection (yet)

Once execution is implemented, the same tests will validate real SpiderFoot module output.

