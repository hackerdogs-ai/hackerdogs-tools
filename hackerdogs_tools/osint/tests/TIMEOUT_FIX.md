# Timeout Fix for CrewAI Tests

## Problem
CrewAI tests with multiple usernames (5) were timing out after 600 seconds (10 minutes) with:
```
litellm.APIConnectionError: OllamaException - litellm.Timeout: Connection timed out after 600.0 seconds.
```

## Root Cause
1. **Tool Execution Time**: Sherlock with 5 usernames takes ~336 seconds (5.6 minutes)
2. **LLM Call Timeout**: LiteLLM (used by CrewAI) defaults to 600 seconds per LLM API call
3. **Multiple LLM Calls**: CrewAI makes multiple LLM calls:
   - Initial call to decide to use the tool
   - Post-execution call to process results
4. **Total Time**: Tool execution (336s) + LLM processing can exceed 600s timeout

## Solution Applied

### 1. Increased LLM Timeout
Updated `get_crewai_llm_from_env()` in `test_utils.py` to set timeout to **900 seconds (15 minutes)** for Ollama:
```python
return LLM(
    model=f"ollama/{model_name}",
    base_url=base_url,
    timeout=900  # 15 minutes per LLM call
)
```

### 2. Reduced Username Count for CrewAI Test
Changed CrewAI multiple usernames test from **5 usernames to 2 usernames** to reduce execution time:
- Tool execution: ~130 seconds (2.2 minutes) instead of ~336 seconds
- Total time with LLM calls: ~300-400 seconds (5-7 minutes) instead of 600+ seconds

## Impact
- ✅ CrewAI tests should complete within timeout
- ✅ Still tests multiple usernames (2 is sufficient for testing multiple username functionality)
- ✅ Standalone and LangChain tests still use 5 usernames (they don't have LLM timeout issues)

## Notes
- The timeout is **per LLM API call**, not total execution time
- Tool execution time varies based on:
  - Number of usernames
  - Network latency
  - Site response times
- If tests still timeout, consider:
  - Using a faster LLM model
  - Running tests with fewer concurrent operations
  - Further increasing timeout (currently 900 seconds)

