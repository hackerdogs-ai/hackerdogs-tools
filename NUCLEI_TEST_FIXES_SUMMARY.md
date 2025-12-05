# Nuclei Test Results Fixes - Summary

**Date:** 2025-12-05  
**Issue:** Test results were being truncated and wrapped, not saving verbatim tool responses

---

## Problems Identified

### 1. LangChain Results ❌
- **Issue:** Tool responses truncated to 1000 characters
- **Issue:** ToolMessage content was incomplete (cut off mid-JSON)
- **Issue:** Results wrapped in custom structure instead of verbatim tool JSON

### 2. CrewAI Results ❌
- **Issue:** Only saving final answer string, not tool outputs
- **Issue:** Missing all intermediate tool calls (CrewAI called tool 3 times)
- **Issue:** No access to actual tool JSON responses

---

## Fixes Applied

### 1. Updated `test_nuclei.py`

#### LangChain Test Fixes:
- ✅ Import `ToolMessage` to properly extract tool responses
- ✅ Extract **complete** ToolMessage content (no truncation)
- ✅ Parse tool JSON responses and save verbatim
- ✅ Save complete agent result object
- ✅ Save all messages with full content (not truncated to 500 chars)

**New Structure:**
```python
result_data = {
    "agent_result": result,  # Complete result object
    "messages": full_messages,  # All messages with FULL content
    "tool_responses": tool_responses,  # Verbatim JSON from tool
    "messages_count": ...,
    "domain": test_domain
}
```

#### CrewAI Test Fixes:
- ✅ Extract all tool outputs from multiple sources
- ✅ Method 1: Extract from `tasks_output.messages`
- ✅ Method 2: Extract from `tasks_output.raw`
- ✅ Method 3: Parse JSON patterns from raw output (fallback)
- ✅ Save complete CrewAI result object
- ✅ Save all tool outputs in array (one per tool call)

**New Structure:**
```python
result_data = {
    "crew_result": result,  # Complete CrewAI result object
    "raw_output": str(result.raw),  # Raw output
    "tool_outputs": tool_outputs,  # All tool responses (verbatim JSON)
    "tool_executions": tool_executions,  # Tool execution details
    "domain": test_domain
}
```

### 2. Updated `save_json_results.py`

- ✅ Added `CustomJSONEncoder` to handle complex objects
- ✅ Added `serialize_object()` function to recursively serialize:
  - LangChain message objects
  - CrewAI result objects
  - Pydantic models
  - Custom objects with `__dict__`
- ✅ No truncation - saves complete content
- ✅ Handles non-serializable objects gracefully

---

## Expected Results After Fix

### LangChain Results Should Now Include:

1. **Complete Tool Responses (Verbatim):**
   ```json
   "tool_responses": [
     {
       "status": "success",
       "target": "hodsonbaywatersports.com",
       "findings": [...],
       "count": 0,
       "execution_method": "official_docker_image",
       "user_id": "..."
     }
   ]
   ```

2. **Complete Messages (No Truncation):**
   ```json
   "messages": [
     {
       "type": "HumanMessage",
       "content": "Scan hodsonbaywatersports.com for vulnerabilities using Nuclei",
       "id": "..."
     },
     {
       "type": "AIMessage",
       "content": "",
       "id": "...",
       "tool_calls": [...]
     },
     {
       "type": "ToolMessage",
       "content": "{\"status\": \"success\", \"target\": \"...\", \"findings\": [...], \"count\": 0, \"execution_method\": \"official_docker_image\"}",  // FULL CONTENT
       "tool_response_json": {
         "status": "success",
         "target": "...",
         "findings": [...],
         "count": 0,
         "execution_method": "official_docker_image"
       },
       "id": "...",
       "name": "nuclei_scan"
     }
   ]
   ```

### CrewAI Results Should Now Include:

1. **All Tool Outputs (Verbatim):**
   ```json
   "tool_outputs": [
     {
       "status": "success",
       "target": "mbplc.com",
       "findings": [],
       "count": 0,
       "execution_method": "official_docker_image"
     },
     {
       "status": "success",
       "target": "mbplc.com",
       "findings": [],
       "count": 0,
       "execution_method": "official_docker_image"
     },
     {
       "status": "success",
       "target": "mbplc.com",
       "findings": [],
       "count": 0,
       "execution_method": "official_docker_image"
     }
   ]
   ```

2. **Complete Crew Result:**
   - Full result object with all execution details
   - Raw output string
   - All intermediate tool calls

---

## Verification Checklist

After running tests, verify:

- [ ] Tool responses are complete JSON (not truncated)
- [ ] All tool calls from CrewAI are captured (should be 3 for nuclei)
- [ ] No content is cut off or wrapped unnecessarily
- [ ] Tool JSON responses are verbatim (exactly as tool returns)
- [ ] Complete agent/crew result objects are saved
- [ ] ToolMessage content is full (not cut off at "findings")
- [ ] All messages have complete content (not truncated to 500 chars)

---

## Next Steps

1. Run tests again: `python hackerdogs_tools/osint/tests/test_nuclei.py`
2. Check the generated JSON files in `hackerdogs_tools/osint/tests/results/`
3. Verify:
   - `tool_responses` array contains complete JSON
   - `tool_outputs` array contains all 3 tool calls
   - No truncation in any fields
   - Verbatim tool responses without wrappers

