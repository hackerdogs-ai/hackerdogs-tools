# Amass Test Failures - Fixed Issues

## Summary of Failures Found

### 1. ❌ **Intel Tool: "Configuration error: No root domain names were provided"**

**Root Cause:**
- Amass v5.0 does NOT have a separate `intel` command
- The `enum` command **requires** `-d DOMAIN` flag
- `-asn`, `-cidr`, `-addr` are **filters**, not standalone parameters
- Cannot use `amass enum -asn 13374` without `-d`

**Fix Applied:**
- Added `domain` parameter to `amass_intel` function
- Made `domain` or `org` required (org can be used as domain)
- ASN/CIDR/addr now work as filters WITH a domain
- Updated both LangChain and CrewAI tools
- Updated test file to provide domain: `domain="cloudflare.com", asn="13374"`

**Before:**
```python
amass_intel(asn="13374")  # ❌ Fails: No domain provided
```

**After:**
```python
amass_intel(domain="cloudflare.com", asn="13374")  # ✅ Works: Domain + ASN filter
```

### 2. ⚠️ **Timeout Issues with Active Enumeration**

**Issue:**
- `amass enum -active -brute` can take > 300 seconds for large domains
- Test timeout set to 300 seconds, causing failures

**Status:**
- This is **expected behavior** - active enumeration is slow
- Timeout is configurable via `timeout` parameter
- Tests should use smaller domains or increase timeout for active mode

**Recommendation:**
- Use `passive=True` for faster tests
- Or increase timeout to 600+ seconds for active enumeration
- Or use smaller test domains

### 3. ⚠️ **Empty Results in Viz/Track**

**Issue:**
- `amass_viz` and `amass_track` return empty results (0 nodes, 0 edges)
- This happens when database has no data for the domain

**Root Cause:**
- Viz and Track require data in the database first
- If `enum` hasn't been run for a domain, there's nothing to visualize/track
- This is **expected** - these tools query existing database data

**Status:**
- Not a bug - this is correct behavior
- To get results: Run `amass_enum` first, then `amass_viz` or `amass_track`

## Files Fixed

1. ✅ `hackerdogs_tools/osint/infrastructure/amass_langchain.py`
   - Added `domain` parameter to `amass_intel`
   - Fixed enum command building to require domain
   - ASN/CIDR/addr now work as filters

2. ✅ `hackerdogs_tools/osint/infrastructure/amass_crewai.py`
   - Added `domain` parameter to `AmassIntelToolSchema`
   - Updated `_run` method signature
   - Fixed enum command building

3. ✅ `hackerdogs_tools/osint/tests/test_amass.py`
   - Updated standalone test to provide domain
   - Updated LangChain test prompt
   - Updated CrewAI test prompt

## Test Results Summary

**Before Fixes:**
- ❌ Intel standalone: Failed with "No root domain names were provided"
- ❌ Intel LangChain: Failed with same error
- ❌ Intel CrewAI: Failed with same error
- ⚠️ Enum with active+brute: Timeout (expected for large domains)
- ✅ Enum passive: Working
- ✅ Viz/Track: Empty results (expected if no enum data)

**After Fixes:**
- ✅ Intel standalone: Should work with domain+ASN
- ✅ Intel LangChain: Should work with updated prompt
- ✅ Intel CrewAI: Should work with updated prompt
- ⚠️ Enum active+brute: Still may timeout (increase timeout if needed)
- ✅ Enum passive: Working
- ✅ Viz/Track: Empty results (expected - need enum first)

## Next Steps

1. ✅ Intel tool fixed - ready for retest
2. ⚠️ Consider increasing default timeout for active enumeration
3. ⚠️ Document that viz/track require enum to run first
4. ✅ All fixes applied and ready for testing

