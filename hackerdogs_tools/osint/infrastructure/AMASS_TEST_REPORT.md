# Amass Test Results Report

**Test Run Date:** 2025-12-05  
**Total Tests:** 12  
**Test Duration:** 1 hour 14 minutes 37 seconds (4477.62s)

## Summary

✅ **All 12 tests PASSED** (pytest reports success)  
⚠️ **However, there are significant functional failures within the tests**

---

## Critical Failures

### 1. ❌ **Intel Tool: Still Getting "No root domain names" Error**

**Issue Count:** Multiple occurrences

**Root Cause:**
- LangChain/CrewAI agents are calling `amass_intel` with **only ASN** (e.g., `asn="13374"`) without providing `domain` or `org`
- The tool correctly rejects this, but agents keep retrying with the same invalid parameters
- The logging shows: `org=None, asn=13374` - meaning no domain was provided

**Evidence:**
```
2025-12-05T05:51:55-0800 - ERROR - Amass intel enum failed: Configuration error: No root domain names were provided
2025-12-05T06:11:15-0800 - ERROR - Amass intel enum failed: Configuration error: No root domain names were provided
```

**Fix Required:**
- Update tool description to be more explicit: "REQUIRES domain parameter. ASN/CIDR/addr are optional filters."
- Improve error message to guide agents: "Domain is required. Use domain='example.com' with optional asn='13374' filter."

---

### 2. ⚠️ **Intel Tool: Timeout Issues (300+ seconds)**

**Issue Count:** 5+ timeouts

**Root Cause:**
- Even when domain is provided correctly, `amass enum -d cloudflare.com -asn 13374 -passive` is taking > 300 seconds
- Cloudflare.com is a large domain with many subdomains
- Passive enumeration with ASN filter still takes a long time

**Evidence:**
```
2025-12-05T05:46:38-0800 - ERROR - Execution timed out | timeout=300
Command: ['docker', 'run', '--rm', '-i', '-v', '...', 'owaspamass/amass:latest', 'enum', '-d', 'cloudflare.com', '-asn', '13374', '-passive']
```

**Fix Required:**
- Increase default timeout for intel operations to 600 seconds
- Or use smaller test domains (e.g., `owasp.org` instead of `cloudflare.com`)
- Document that intel operations can be slow

---

### 3. ⚠️ **Enum Tool: Multiple Timeouts with Active+Brute Mode**

**Issue Count:** 10+ timeouts

**Root Cause:**
- `amass enum -active -brute` is extremely slow (can take 10+ minutes for large domains)
- CrewAI agents are trying multiple combinations and all timing out
- Default timeout of 300 seconds is insufficient for active enumeration

**Evidence:**
```
2025-12-05T06:26:37-0800 - ERROR - Execution timed out | timeout=300
Command: ['docker', 'run', '--rm', '-i', '-v', '...', 'owaspamass/amass:latest', 'enum', '-d', 'maccazine.nl', '-passive', '-active', '-brute']
```

**Fix Required:**
- Increase timeout for active enumeration to 900+ seconds
- Or make active enumeration opt-in with explicit warning about time
- Use passive mode by default in tests

---

### 4. ⚠️ **Logging Parameter Mismatch**

**Issue:**
- Logging shows `org=cloudflare.com` but the function parameter is `domain`
- This is confusing when debugging

**Evidence:**
```
2025-12-05T05:41:38-0800 - INFO - [amass_intel] Starting intelligence gathering | org=cloudflare.com, asn=13374
```

**Fix Required:**
- Update logging to show `domain` parameter instead of `org`
- Or log both if `org` is used as fallback for `domain`

---

## Test Results Breakdown

### ✅ Standalone Tests (4/4 PASSED)
1. ✅ `test_amass_intel_standalone` - **PASSED** (but with timeout/error in some runs)
2. ✅ `test_amass_enum_standalone` - **PASSED**
3. ✅ `test_amass_viz_standalone` - **PASSED** (empty results expected)
4. ✅ `test_amass_track_standalone` - **PASSED** (empty results expected)

### ✅ LangChain Agent Tests (4/4 PASSED)
1. ✅ `test_amass_intel_langchain_agent` - **PASSED** (but agent retried multiple times due to timeouts)
2. ✅ `test_amass_enum_langchain_agent` - **PASSED**
3. ✅ `test_amass_viz_langchain_agent` - **PASSED** (empty results expected)
4. ✅ `test_amass_track_langchain_agent` - **PASSED** (empty results expected)

### ✅ CrewAI Agent Tests (4/4 PASSED)
1. ✅ `test_amass_intel_crewai_agent` - **PASSED** (but agent retried 6+ times due to timeouts)
2. ✅ `test_amass_enum_crewai_agent` - **PASSED** (but agent retried 6+ times due to timeouts)
3. ✅ `test_amass_viz_crewai_agent` - **PASSED** (empty results expected)
4. ✅ `test_amass_track_crewai_agent` - **PASSED** (empty results expected)

---

## Issues by Category

### **Functional Issues (Must Fix)**
1. ❌ Intel tool still receiving calls without domain parameter
2. ❌ Logging shows wrong parameter name (`org` vs `domain`)

### **Performance Issues (Should Fix)**
1. ⚠️ Intel operations timing out on large domains (cloudflare.com)
2. ⚠️ Enum operations timing out with active+brute mode
3. ⚠️ Default timeout (300s) too short for comprehensive enumeration

### **Expected Behavior (No Fix Needed)**
1. ✅ Empty viz/track results (expected if enum hasn't run)
2. ✅ Tests passing despite timeouts (pytest marks as passed if no assertion fails)

---

## Recommendations

### Immediate Fixes

1. **Fix Intel Tool Parameter Handling**
   ```python
   # Update tool description to be explicit:
   description = "REQUIRES domain parameter. ASN/CIDR/addr are optional filters. Example: domain='example.com', asn='13374'"
   ```

2. **Fix Logging**
   ```python
   # Change from:
   safe_log_info(logger, f"[amass_intel] Starting", org=org, asn=asn, ...)
   # To:
   safe_log_info(logger, f"[amass_intel] Starting", domain=target_domain, asn=asn, ...)
   ```

3. **Increase Timeouts**
   ```python
   # Intel operations:
   timeout: int = 600  # Increase from 300 to 600
   
   # Enum with active+brute:
   timeout: int = 900  # Increase from 300 to 900
   ```

4. **Use Smaller Test Domains**
   - Change `cloudflare.com` to `owasp.org` in tests
   - Or use domains from test_domains.py that are known to be smaller

### Long-term Improvements

1. **Better Error Messages**
   - Provide actionable guidance when domain is missing
   - Suggest correct parameter format

2. **Timeout Strategy**
   - Make timeout configurable per operation type
   - Provide progress updates for long-running operations

3. **Agent Guidance**
   - Update tool descriptions to be more explicit about requirements
   - Add examples in tool descriptions

---

## Test Statistics

- **Total Test Time:** 1h 14m 37s
- **Timeout Errors:** 15+
- **Configuration Errors:** 3+
- **Successful Completions:** 12 (all tests passed)
- **Agent Retries:** 20+ (due to timeouts and errors)

---

## Conclusion

While all tests technically **PASSED**, there are significant functional issues:

1. **Intel tool** is still being called incorrectly by agents
2. **Timeouts** are causing excessive retries and long test duration
3. **Logging** needs to be fixed for better debugging

**Priority:** Fix the intel tool parameter handling and increase timeouts to improve test reliability and reduce execution time.

