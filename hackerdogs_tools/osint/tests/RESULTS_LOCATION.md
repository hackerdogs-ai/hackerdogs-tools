# Test Results Storage Location

## Where Results Are Stored

All test results (tool return values) are saved to:

```
hackerdogs_tools/osint/tests/results/
```

## Result File Naming Convention

Results are saved with the following naming pattern:

```
{tool_name}_{test_type}_{domain}_{timestamp}.json
```

For example:
- `subfinder_standalone_apple_macos_help_20251204_093318.json`
- `amass_langchain_example_com_20251204_100000.json`
- `nuclei_crewai_target_com_20251204_100000.json`

## Test Types

Three types of results are saved:

1. **`standalone`**: Direct tool execution results (JSON output from the tool)
2. **`langchain`**: LangChain agent execution results (agent messages and tool outputs)
3. **`crewai`**: CrewAI agent execution results (crew output and tool results)

## Result File Structure

Each JSON file contains:

```json
{
  "tool": "subfinder",
  "test_type": "standalone",
  "timestamp": "20251204_093318",
  "domain": "example.com",
  "result": {
    "status": "success",
    "execution_method": "docker",
    "domain": "example.com",
    "subdomains": [...],
    "count": 42
  }
}
```

For LangChain/CrewAI results:

```json
{
  "tool": "subfinder",
  "test_type": "langchain",
  "timestamp": "20251204_100000",
  "domain": "example.com",
  "result": {
    "status": "success",
    "agent_type": "langchain",
    "result": "...",
    "messages_count": 3
  }
}
```

## Viewing Results

### List all results:
```bash
ls -lh hackerdogs_tools/osint/tests/results/
```

### View a specific result:
```bash
cat hackerdogs_tools/osint/tests/results/subfinder_standalone_example_com_*.json | jq .
```

### Find results by tool:
```bash
ls hackerdogs_tools/osint/tests/results/*subfinder*.json
```

### Find results by test type:
```bash
ls hackerdogs_tools/osint/tests/results/*langchain*.json
ls hackerdogs_tools/osint/tests/results/*crewai*.json
ls hackerdogs_tools/osint/tests/results/*standalone*.json
```

## Current Status

- ✅ **Standalone tests**: Saving results (working)
- ✅ **LangChain tests**: Now saving results (updated in all test files)
- ✅ **CrewAI tests**: Now saving results (updated in all test files)

## Notes

- Results are automatically saved during test execution
- Each test run creates a new file with a unique timestamp
- The `domain` field may be `null` for tools that don't use domains (e.g., `abuseipdb` uses IPs, `nuclei` uses targets)
- LangChain/CrewAI results contain the full agent conversation and tool outputs

