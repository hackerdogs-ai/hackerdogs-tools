# SpiderFoot Migration - Understanding

## ✅ CORRECTED APPROACH

**These are MIGRATIONS, not WRAPPERS.**

### What This Means:

1. **No Docker Execution**
   - ❌ Remove all Docker code
   - ❌ Remove `docker_client` imports
   - ❌ Remove `execute_in_docker()` calls
   - ✅ Direct Python execution only

2. **No SpiderFoot Legacy Code References**
   - ❌ No `SpiderFootPlugin` imports
   - ❌ No `SpiderFootEvent` references
   - ❌ No `handleEvent()` calls
   - ❌ No SpiderFoot database dependencies
   - ✅ Standalone Python implementations

3. **Direct Implementation**
   - ✅ Use same underlying libraries SpiderFoot uses
   - ✅ Implement functionality directly
   - ✅ Clean, self-contained code
   - ✅ No external dependencies on SpiderFoot

## Migration Examples

### Example 1: `sfp_abuseipdb` Migration

**SpiderFoot does:**
- Calls AbuseIPDB API via `urllib.request`
- Parses JSON response
- Returns reputation data

**Migrated Implementation:**
```python
import requests

def sfp_abuseipdb(target: str, api_key: str, ...):
    """AbuseIPDB checker - MIGRATED standalone implementation."""
    url = "https://api.abuseipdb.com/api/v2/check"
    headers = {"Key": api_key, "Accept": "application/json"}
    params = {"ipAddress": target, "maxAgeInDays": 90}
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()
```

**No references to:**
- SpiderFoot
- Docker
- `SpiderFootPlugin`
- `SpiderFootEvent`

### Example 2: `sfp_whois` Migration

**SpiderFoot does:**
- Uses `whois` library for domains
- Uses `ipwhois` library for IPs
- Returns WHOIS data

**Migrated Implementation:**
```python
import whois
import ipwhois

def sfp_whois(target: str):
    """Whois lookup - MIGRATED standalone implementation."""
    # Check if target is IP or domain
    if is_ip(target):
        r = ipwhois.IPWhois(target)
        data = r.lookup_rdap(depth=1)
    else:
        data = whois.whois(target)
    
    return data
```

**No references to:**
- SpiderFoot
- Docker
- SpiderFoot event system

### Example 3: `sfp_dnsbrute` Migration

**SpiderFoot does:**
- Loads common subdomain list
- Performs DNS lookups using `self.sf.resolveHost()`
- Returns discovered subdomains

**Migrated Implementation:**
```python
import socket
import dns.resolver

def sfp_dnsbrute(target: str, commons: bool = True, ...):
    """DNS brute-forcer - MIGRATED standalone implementation."""
    results = []
    
    # Load common subdomains (from file or hardcoded list)
    subdomains = load_common_subdomains() if commons else []
    
    for subdomain in subdomains:
        hostname = f"{subdomain}.{target}"
        try:
            # Direct DNS lookup - no SpiderFoot code
            ip = socket.gethostbyname(hostname)
            results.append({"hostname": hostname, "ip": ip})
        except socket.gaierror:
            pass
    
    return results
```

**No references to:**
- SpiderFoot
- Docker
- `self.sf.resolveHost()`

## Template Changes Made

1. ✅ Removed all Docker code
2. ✅ Removed all SpiderFoot references
3. ✅ Added placeholder for direct implementation
4. ✅ Updated notes to clarify migration approach

## Next Steps

1. **Analyze each SpiderFoot module** to understand what it does
2. **Identify underlying libraries** (requests, socket, whois, etc.)
3. **Implement functionality directly** in the template or as helper functions
4. **Test with real inputs** to ensure same results as SpiderFoot

## Key Principle

**MIGRATION = Reimplement functionality using same libraries, but standalone code**
**WRAPPER = Call existing SpiderFoot code (NOT what we want)**

