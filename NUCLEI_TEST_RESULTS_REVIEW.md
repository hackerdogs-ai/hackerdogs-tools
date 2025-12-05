# Nuclei Test Results Review & Fixes

**Date:** 2025-12-05  
**Issue:** Test results were being truncated and wrapped, not saving verbatim tool responses

---

## Issues Found in Test Results

### 1. LangChain Results ❌

**Problem:**
- Tool responses were truncated to 1000 characters
- ToolMessage content was cut off (showing `"findings"` but incomplete)
- Results wrapped in custom structure instead of verbatim tool JSON

**Example from saved file:**
```json
{
  "result": "{'messages': [..., ToolMessage(content='{\\n  \"status\": \"success\",\\n  \"target\": \"hodsonbaywatersports.com\",\\n  \"findings"
  // Content truncated!
}
```

**What Should Be Saved:**
- Complete ToolMessage content (full JSON from tool)
- All messages with complete content (no truncation)
- Verbatim tool JSON responses in separate array

### 2. CrewAI Results ❌

**Problem:**
- Only saving final answer string, not tool outputs
- Missing all intermediate tool calls and responses
- No access to actual tool JSON responses

**Example from saved file:**
```json
{
  "result": "No vulnerabilities were detected during the scan..."
  // Only the final answer, no tool outputs!
}
```

**What Should Be Saved:**
- All tool outputs from all tool calls (CrewAI called tool 3 times)
- Complete CrewAI result object
- Verbatim tool JSON responses from each call

---

## Fixes Applied

### 1. Updated Test File (`test_nuclei.py`)

**Changes:**
- ✅ Import `ToolMessage` to properly extract tool responses
- ✅ Extract complete ToolMessage content (no truncation)
- ✅ Parse tool JSON responses and save verbatim
- ✅ Save complete agent result objects
- ✅ Extract all tool outputs from CrewAI (not just final answer)

**New Structure for LangChain:**
```python
result_data = {
    "agent_result": result,  # Complete result object
    "messages": full_messages,  # All messages with FULL content
    "tool_responses": tool_responses,  # Verbatim JSON from tool
    "messages_count": ...,
    "domain": test_domain
}
```

**New Structure for CrewAI:**
```python
result_data = {
    "crew_result": result,  # Complete CrewAI result object
    "raw_output": str(result.raw),  # Raw output
    "tool_outputs": tool_outputs,  # All tool responses (verbatim JSON)
    "domain": test_domain
}
```

### 2. Updated Save Function (`save_json_results.py`)

**Changes:**
- ✅ Added `CustomJSONEncoder` to handle complex objects
- ✅ Added `serialize_object()` function to recursively serialize objects
- ✅ Handles LangChain message objects
- ✅ Handles CrewAI result objects
- ✅ Handles Pydantic models
- ✅ No truncation - saves complete content

---

## Expected Results After Fix

### LangChain Results Should Include:

1. **Complete Tool Responses:**
   ```json
   "tool_responses": [
     {
       "status": "success",
       "target": "hodsonbaywatersports.com",
       "findings": [...],
       "count": 0,
       "execution_method": "official_docker_image"
     }
   ]
   ```

2. **Complete Messages:**
   ```json
   "messages": [
     {
       "type": "HumanMessage",
       "content": "Scan ... for vulnerabilities using Nuclei",
       "id": "..."
     },
     {
       "type": "AIMessage",
       "content": "",
       "tool_calls": [...]
     },
     {
       "type": "ToolMessage",
       "content": "{\"status\": \"success\", ...}",  // FULL CONTENT
       "tool_response_json": {...}  // Parsed JSON
     }
   ]
   ```

### CrewAI Results Should Include:

1. **All Tool Outputs:**
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

## Verification Steps

After running tests, verify:

1. ✅ Tool responses are complete JSON (not truncated)
2. ✅ All tool calls from CrewAI are captured
3. ✅ No content is cut off or wrapped unnecessarily
4. ✅ Tool JSON responses are verbatim (exactly as tool returns)
5. ✅ Complete agent/crew result objects are saved

---

## Next Steps

1. Run tests again to generate new result files
2. Verify tool responses are complete and verbatim
3. Check that all CrewAI tool calls are captured
4. Confirm no truncation or wrapping

