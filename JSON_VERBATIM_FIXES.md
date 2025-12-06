# JSON Verbatim Output Fixes

## Problem
Some tools were wrapping JSON file output in metadata structures instead of returning the JSON content directly and verbatim.

## Fixed Tools

### 1. ✅ Sherlock (`sherlock_langchain.py` & `sherlock_crewai.py`)
**Issue:** When `output_format="json"` with single username, tool was wrapping JSON file in metadata structure.

**Fix:** 
- For single username + JSON format: Returns JSON file content directly, verbatim
- For multiple usernames or other formats: Still returns wrapper (needed for metadata)

**Files Fixed:**
- `hackerdogs_tools/osint/identity/sherlock_langchain.py`
- `hackerdogs_tools/osint/identity/sherlock_crewai.py`

### 2. ✅ Maigret (`maigret_langchain.py`)
**Issue:** When `report_format="json"` with single username, tool was parsing JSON and wrapping it in metadata structure.

**Fix:**
- For single username + JSON format: Returns JSON file content directly, verbatim (no parsing)
- For multiple usernames: Still returns wrapper with parsed JSON (needed for multiple files)

**Files Fixed:**
- `hackerdogs_tools/osint/identity/maigret_langchain.py`

## Pattern Applied

When a tool generates a JSON file and there's a single result:
1. Read the JSON file as raw text (don't parse it)
2. Return the file content directly, verbatim
3. No wrapper, no metadata, no parsing

When there are multiple files or other formats:
- Keep the wrapper structure (needed for metadata about multiple results)

## Tools That Don't Need Fixing

These tools either:
- Don't output JSON files
- Already return verbatim output correctly
- Need wrapper structures for their use case

- **Amass**: Returns visualization files in wrapper (needed for multiple file types)
- **Subfinder**: Returns stdout directly (no JSON files)
- **Nuclei**: Returns JSON in stdout (no file parsing)
- **Other tools**: Don't generate JSON files

## Testing

After fixes:
- ✅ Sherlock single username JSON: Returns raw JSON file content
- ✅ Maigret single username JSON: Returns raw JSON file content
- ✅ Multiple usernames: Still returns wrapper (as expected)

