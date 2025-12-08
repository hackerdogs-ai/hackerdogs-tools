# SpiderFoot Migration Approach - CORRECTED

## Critical Understanding: MIGRATIONS, NOT WRAPPERS

**What we're doing:**
- ✅ **MIGRATING** SpiderFoot module functionality to standalone LangChain/CrewAI tools
- ✅ Reimplementing the same functionality using direct Python libraries/APIs
- ✅ Clean, standalone code with no SpiderFoot dependencies
- ✅ Direct execution (no Docker)

**What we're NOT doing:**
- ❌ Wrapping SpiderFoot modules
- ❌ Calling SpiderFoot code
- ❌ Using Docker to execute SpiderFoot
- ❌ Referencing SpiderFoot legacy code

## Migration Strategy

### Example 1: `sfp_dnsbrute` → DNS Brute-forcer Tool

**What `sfp_dnsbrute` does:**
- Takes a domain name as input
- Tries common subdomain names (www, mail, ftp, etc.)
- Performs DNS lookups to find valid subdomains
- Returns list of discovered subdomains

**Migrated Implementation:**
```python
import socket
import dns.resolver  # or dnspython

def sfp_dnsbrute(target: str, commons: bool = True, ...):
    """DNS brute-forcer - MIGRATED from SpiderFoot, standalone implementation."""
    results = []
    
    # Load common subdomain list (from file or hardcoded)
    subdomains = ["www", "mail", "ftp", "admin", ...]  # ~750 common names
    
    for subdomain in subdomains:
        hostname = f"{subdomain}.{target}"
        try:
            # Direct DNS lookup - no SpiderFoot code
            ip = socket.gethostbyname(hostname)
            results.append({
                "hostname": hostname,
                "ip": ip,
                "type": "A"
            })
        except socket.gaierror:
            pass  # Not found
    
    return results
```

**No references to:**
- `SpiderFootPlugin`
- `SpiderFootEvent`
- `handleEvent()`
- `sendEvent()`
- SpiderFoot database
- SpiderFoot controller

### Example 2: `sfp_abuseipdb` → AbuseIPDB Tool

**What `sfp_abuseipdb` does:**
- Takes an IP address
- Calls AbuseIPDB API
- Returns reputation data

**Migrated Implementation:**
```python
import requests

def sfp_abuseipdb(target: str, api_key: str, ...):
    """AbuseIPDB checker - MIGRATED from SpiderFoot, standalone implementation."""
    url = "https://api.abuseipdb.com/api/v2/check"
    headers = {"Key": api_key, "Accept": "application/json"}
    params = {"ipAddress": target, "maxAgeInDays": 90}
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()
```

**No references to:**
- SpiderFoot API wrapper
- SpiderFoot event system
- Any SpiderFoot code

### Example 3: `sfp_whois` → Whois Tool

**What `sfp_whois` does:**
- Takes a domain name
- Performs WHOIS lookup
- Returns registration information

**Migrated Implementation:**
```python
import whois  # python-whois library

def sfp_whois(target: str):
    """Whois lookup - MIGRATED from SpiderFoot, standalone implementation."""
    domain = whois.whois(target)
    return {
        "domain": target,
        "registrar": domain.registrar,
        "creation_date": str(domain.creation_date),
        "expiration_date": str(domain.expiration_date),
        # ... other fields
    }
```

## Template Changes Required

### Remove:
1. ❌ All Docker execution code
2. ❌ All SpiderFoot imports
3. ❌ All references to `SpiderFootEvent`, `SpiderFootPlugin`, etc.
4. ❌ All placeholder comments about SpiderFoot execution

### Add:
1. ✅ Direct Python library imports (requests, socket, whois, etc.)
2. ✅ Standalone implementation of module functionality
3. ✅ Direct API calls or library usage
4. ✅ Clean, self-contained code

## Implementation Steps

1. **Analyze each SpiderFoot module** to understand what it does
2. **Identify the underlying libraries/APIs** it uses
3. **Reimplement the functionality** directly in the tool
4. **Remove all SpiderFoot dependencies**
5. **Test with real inputs** to ensure same results

## Example: Updated Template Structure

```python
@tool
def sfp_dnsbrute(
    runtime: ToolRuntime,
    target: str,
    commons: Optional[bool] = True,
    ...
) -> str:
    """DNS Brute-forcer - Standalone implementation."""
    try:
        safe_log_info(logger, f"[sfp_dnsbrute] Starting", target=target)
        
        user_id = runtime.state.get("user_id", "unknown")
        
        # Validate inputs
        if not target or not isinstance(target, str):
            return json.dumps({"status": "error", "message": "Invalid target"})
        
        # DIRECT IMPLEMENTATION - No SpiderFoot code
        results = []
        subdomains = load_common_subdomains() if commons else []
        
        for subdomain in subdomains:
            hostname = f"{subdomain}.{target}"
            try:
                ip = socket.gethostbyname(hostname)
                results.append({"hostname": hostname, "ip": ip})
            except:
                pass
        
        # Return results
        return json.dumps({
            "status": "success",
            "module": "sfp_dnsbrute",
            "target": target,
            "results": results,
            "user_id": user_id
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
```

## Key Principles

1. **Standalone**: Each tool is self-contained
2. **Direct**: Uses Python libraries/APIs directly
3. **Clean**: No legacy code references
4. **Functional**: Replicates SpiderFoot module behavior
5. **Native**: Runs in Python environment, no Docker

