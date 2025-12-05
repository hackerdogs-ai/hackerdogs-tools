# Amass Fixes Summary

## Issues Fixed

### 1. ✅ Fixed `-src` Flag Issue

**Problem:**
- Amass v5.0.0 does NOT support the `-src` flag
- Code was adding `-src` when `show_sources=True`, causing failures

**Fix Applied:**
- Removed `-src` flag from `amass enum` command in both `amass_langchain.py` and `amass_crewai.py`
- Updated parameter descriptions to note that `show_sources` is not supported in v5.0.0
- Added comments explaining why the flag is commented out

**Files Changed:**
- `hackerdogs_tools/osint/infrastructure/amass_langchain.py`
  - Line 165: Commented out `enum_args.append("-src")`
  - Line 185: Commented out `-src` flag for `subs` command
  - Updated `show_sources` parameter description
  
- `hackerdogs_tools/osint/infrastructure/amass_crewai.py`
  - Line 147: Commented out `enum_args.append("-src")`
  - Updated `show_sources` parameter descriptions in both `AmassIntelToolSchema` and `AmassEnumToolSchema`

### 2. ✅ Fixed CrewAI Result Extraction

**Problem:**
- CrewAI tests were saving `str(result)` which is just the string representation
- This did NOT contain the actual tool output (JSON data)
- Example: `"- moc-kraju.info"` instead of structured JSON with subdomains

**Fix Applied:**
- Created helper function `extract_crewai_tool_output.py` to extract actual tool output from CrewAI result object
- Updated all 4 CrewAI test methods to use the helper function
- Now extracts JSON from `result.tasks_output[].messages[]` or `result.raw`

**Files Changed:**
- `hackerdogs_tools/osint/tests/extract_crewai_tool_output.py` (NEW)
  - Helper function to extract tool output from CrewAI result
  - Handles multiple extraction strategies:
    1. Parse JSON from task messages
    2. Parse JSON from task raw output
    3. Parse JSON from result raw output
    4. Fallback to raw string if no JSON found

- `hackerdogs_tools/osint/tests/test_amass.py`
  - Updated `test_amass_intel_crewai_agent` to use helper
  - Updated `test_amass_enum_crewai_agent` to use helper
  - Updated `test_amass_viz_crewai_agent` to use helper
  - Updated `test_amass_track_crewai_agent` to use helper

**Result Structure Now:**
```json
{
  "status": "success",
  "agent_type": "crewai",
  "result": {
    "status": "success",
    "domain": "example.com",
    "subdomains": [...],
    "subdomain_count": 5
  },
  "raw_result": "...",
  "domain": "example.com",
  "tool": "amass_enum"
}
```

## Test Output Location

All test results are saved to:
```
hackerdogs_tools/osint/tests/results/
```

**File Naming:**
- `{tool_name}_{test_type}_{domain}_{timestamp}.json`
- Example: `amass_enum_crewai_owasp_org_20251205_120000.json`

**Test Types:**
1. **`standalone`**: Direct tool execution (JSON output from tool) ✅ Working
2. **`langchain`**: LangChain agent execution (message history with tool output) ✅ Working
3. **`crewai`**: CrewAI agent execution (now extracts actual tool output) ✅ Fixed

## Verification

To verify the fixes:

1. **Check `-src` flag is removed:**
   ```bash
   grep -n "-src" hackerdogs_tools/osint/infrastructure/amass_*.py
   # Should show only commented lines
   ```

2. **Check CrewAI result extraction:**
   ```bash
   # Run a test
   pytest hackerdogs_tools/osint/tests/test_amass.py::TestAmassEnumCrewAI::test_amass_enum_crewai_agent -v
   
   # Check the result file
   cat hackerdogs_tools/osint/tests/results/amass_enum_crewai_*.json | jq '.result.result'
   # Should show structured JSON, not just a string
   ```

## Next Steps

1. **Re-run tests** to verify fixes work
2. **Check result files** to ensure they contain actual tool output
3. **Verify empty results** are legitimate (domain has no data) not errors

