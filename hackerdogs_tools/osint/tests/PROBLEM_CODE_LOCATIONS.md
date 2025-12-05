# Problem Code Locations

## Issue 1: CrewAI Result Extraction - Finding System Prompt Instead of Tool Output

### Problem Location: `extract_crewai_tool_output.py`

**Lines 31-56:** The extraction logic searches through messages but finds the agent's system prompt instead of tool output.

```python:31:56:hackerdogs_tools/osint/tests/extract_crewai_tool_output.py
    # Try to extract from tasks_output messages
    if hasattr(result, 'tasks_output') and result.tasks_output:
        for task_output in result.tasks_output:
            # Check messages for tool output
            if hasattr(task_output, 'messages') and task_output.messages:
                for msg in task_output.messages:
                    # Look for tool output in message content
                    content = None
                    if hasattr(msg, 'content'):
                        content = msg.content
                    elif isinstance(msg, dict):
                        content = msg.get('content')
                    elif isinstance(msg, str):
                        content = msg
                    
                    if content and isinstance(content, str):
                        # Try to parse JSON from content
                        try:
                            parsed = json.loads(content)
                            if isinstance(parsed, dict) and parsed.get('status'):
                                tool_output_json = parsed
                                break
                        except (json.JSONDecodeError, AttributeError, TypeError):
                            # Not JSON, might be tool output text
                            if not tool_output:
                                tool_output = content[:2000]  # ❌ PROBLEM: This captures system prompt
```

**Problem:**
- Line 55: When content is not JSON, it saves it as `tool_output`
- This captures the agent's system prompt ("You are OSINT Analyst...") instead of the actual tool output
- The tool output JSON is likely in a different message type or location

**Evidence from Results:**
- `amass_enum_crewai_cash-win-casino_fr_20251205_014928.json`:
  ```json
  {
    "result": "You are OSINT Analyst. You are an expert...",  // ❌ System prompt
    "raw_result": "No subdomains were discovered..."  // ✅ Actual result is here!
  }
  ```

**Fix Needed:**
- The actual tool output is in `raw_result`, not in the extracted `result`
- Need to parse `raw_result` more carefully or look for tool output in a different message type
- May need to check `result.tasks_output[].raw` which contains the final answer

---

## Issue 2: CrewAI Test Result Saving - Using Wrong Extracted Value

### Problem Location: `test_amass.py` - All CrewAI test methods

**Line 547 (amass_enum):**
```python:544:551:hackerdogs_tools/osint/tests/test_amass.py
            result_data = {
                "status": "success",
                "agent_type": "crewai",
                "result": extracted["tool_output_json"] if extracted["tool_output_json"] else extracted["tool_output"],
                #                                                                         ^^^^^^^^^^^^^^^^^^^^^^^^
                #                                                                         ❌ PROBLEM: This is system prompt
                "raw_result": extracted["raw_result"],
                #            ^^^^^^^^^^^^^^^^^^^^^^^^
                #            ✅ This contains the actual result!
                "domain": test_domain,
                "tool": "amass_enum"
            }
```

**Same issue in:**
- Line 481: `test_amass_intel_crewai_agent`
- Line 547: `test_amass_enum_crewai_agent` (shown above)
- Line 600: `test_amass_viz_crewai_agent`
- Line 661: `test_amass_track_crewai_agent`

**Problem:**
- When `tool_output_json` is `None`, it falls back to `tool_output`
- But `tool_output` contains the system prompt, not the tool output
- The actual tool result is in `raw_result` (e.g., "No subdomains were discovered...")

**Fix Needed:**
- Parse `raw_result` to extract tool output JSON
- Or improve extraction logic to find tool output in the correct location
- Check if `raw_result` contains JSON that can be parsed

---

## Issue 3: Intel Standalone Test - May Have Domain Parameter Issue

### Problem Location: `test_amass.py` line 61-65

```python:54:76:hackerdogs_tools/osint/tests/test_amass.py
    def test_amass_intel_standalone(self):
        """Test amass_intel tool execution without agent."""
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Test with ASN (known working ASN)
        # Note: Amass v5.0 requires -d DOMAIN, ASN is a filter
        # Use owasp.org which is smaller and faster than cloudflare.com
        result = amass_intel.invoke({
            "runtime": runtime,
            "domain": "owasp.org",  # ✅ Domain is provided
            "asn": None,  # ✅ ASN is None
            "timeout": 600  # Increased timeout for intel operations
        })
        
        result_data = json.loads(result)
        
        print("\n" + "=" * 80)
        print("AMASS INTEL - TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        result_file = save_test_result("amass_intel", "standalone", result_data, "asn_13374")
        #                                                                        ^^^^^^^^^^^^
        #                                                                        ❌ Wrong domain in filename
```

**Problem:**
- Line 61-65: The test is actually correct - it passes `domain="owasp.org"` and `asn=None`
- But the error result shows: `"message": "Amass intel enum failed: "` (empty message)
- Line 76: The filename uses `"asn_13374"` but the actual domain is `"owasp.org"`

**Possible Issues:**
1. The tool might be failing for a different reason (not domain parameter)
2. The error message is empty, suggesting the tool execution failed silently
3. Need to check the actual tool execution logs

**Fix Needed:**
- Check why `amass_intel` is failing even with domain provided
- Update filename to use actual domain: `"owasp_org"` instead of `"asn_13374"`
- Add better error handling to capture full error message

---

## Issue 4: Extraction Logic Not Checking Final Answer

### Problem Location: `extract_crewai_tool_output.py` lines 68-76

```python:68:76:hackerdogs_tools/osint/tests/extract_crewai_tool_output.py
    # Fallback to raw output if no JSON found
    if not tool_output_json and hasattr(result, 'raw') and result.raw:
        raw_output = result.raw
        # Try to parse JSON from raw output
        try:
            tool_output_json = json.loads(raw_output)
        except (json.JSONDecodeError, AttributeError, TypeError):
            if not tool_output:
                tool_output = raw_output[:2000]  # ❌ This captures the full raw output
```

**Problem:**
- Line 75: When `raw_output` is not JSON, it saves the entire raw output
- But `result.raw` contains the agent's final answer (text), not tool output JSON
- The tool output JSON is embedded somewhere in the message chain, not in `result.raw`

**Evidence:**
- `raw_result` contains: "No subdomains were discovered for cash-win-casino.fr..."
- This is the agent's final answer, not the tool's JSON output
- The tool's JSON output is likely in a `ToolMessage` or similar message type

---

## Summary of Problem Locations

| Issue | File | Lines | Problem |
|-------|------|-------|---------|
| **1. Extraction finds system prompt** | `extract_crewai_tool_output.py` | 46-56 | Saves non-JSON content as `tool_output` (captures system prompt) |
| **2. Wrong fallback value** | `test_amass.py` | 481, 547, 600, 661 | Uses `tool_output` (system prompt) instead of parsing `raw_result` |
| **3. Intel test error** | `test_amass.py` | 61-76 | Tool fails with empty error message, filename uses wrong domain |
| **4. Raw output fallback** | `extract_crewai_tool_output.py` | 68-76 | Saves entire `result.raw` which is agent's answer, not tool JSON |

---

## Recommended Fixes

### Fix 1: Improve Message Type Detection
```python
# In extract_crewai_tool_output.py, line 36-56
for msg in task_output.messages:
    # Skip system/user messages, only check tool/assistant messages
    msg_type = type(msg).__name__ if hasattr(msg, '__class__') else str(type(msg))
    if 'Tool' not in msg_type and 'Assistant' not in msg_type:
        continue  # Skip system/user messages
    
    # Look for tool output in message content
    content = None
    # ... rest of extraction logic
```

### Fix 2: Parse raw_result for Tool Output
```python
# In test_amass.py, line 547
# Instead of:
"result": extracted["tool_output_json"] if extracted["tool_output_json"] else extracted["tool_output"],

# Try:
if extracted["tool_output_json"]:
    result_value = extracted["tool_output_json"]
elif extracted["raw_result"]:
    # Try to extract JSON from raw_result
    raw = extracted["raw_result"]
    # Look for JSON pattern in raw_result
    import re
    json_match = re.search(r'\{[^{}]*"status"[^{}]*\}', raw)
    if json_match:
        try:
            result_value = json.loads(json_match.group())
        except:
            result_value = raw[:500]  # Fallback to text
else:
    result_value = extracted["tool_output"]  # Last resort
```

### Fix 3: Add Debug Logging
```python
# In extract_crewai_tool_output.py, add at line 32
import logging
logger = logging.getLogger(__name__)

# After line 33
logger.debug(f"DEBUG: tasks_output count: {len(result.tasks_output)}")
for i, task in enumerate(result.tasks_output):
    logger.debug(f"DEBUG: Task {i} messages: {len(task.messages) if hasattr(task, 'messages') else 0}")
    if hasattr(task, 'messages'):
        for j, msg in enumerate(task.messages):
            msg_type = type(msg).__name__
            logger.debug(f"DEBUG: Message {j} type: {msg_type}")
            if hasattr(msg, 'content'):
                logger.debug(f"DEBUG: Message {j} content (first 200): {str(msg.content)[:200]}")
```

---

**Last Updated:** 2025-12-05

