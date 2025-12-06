# Maigret Verbatim Output Implementation

## Why Return Raw JSON Instead of Parsing?

### Original Approach (Incorrect)
The initial implementation was **parsing and reformatting** the JSON output from Maigret:
- Reading JSON files
- Extracting specific fields (url_user, status, ids, tags)
- Reformatting into a custom structure
- Losing original data structure and fields

**Problem**: This violates the principle of returning **verbatim output** - the tool's actual results should be returned as-is, not transformed.

### Correct Approach (Current)
The tool now returns **raw JSON output verbatim**:

1. **For JSON format** (`report_format="json"`):
   - Reads the JSON file(s) directly: `report_{username}_{json_type}.json`
   - Returns the raw JSON structure as-is
   - No parsing, no reformatting, no field extraction
   - Preserves the complete original data structure

2. **For non-JSON formats** (txt, csv, html, etc.):
   - Returns raw stdout/stderr verbatim
   - No parsing or extraction
   - User can process the output as needed

## Implementation Details

### JSON Output Structure

When `report_format="json"` and `json_type="simple"`:
```json
{
  "status": "success",
  "usernames": ["testuser"],
  "results": {
    "testuser": {
      "SiteName1": {
        "username": "testuser",
        "url_user": "https://...",
        "url_main": "https://...",
        "status": {
          "username": "testuser",
          "site_name": "SiteName1",
          "url": "https://...",
          "status": "Claimed",
          "ids": {},
          "tags": ["video"]
        },
        "http_status": 200,
        ...
      },
      "SiteName2": { ... }
    }
  },
  "report_format": "json",
  "json_type": "simple",
  "execution_method": "official_docker_image"
}
```

When `json_type="ndjson"`:
```json
{
  "status": "success",
  "usernames": ["testuser"],
  "results": {
    "testuser": [
      { "site": "SiteName1", "url_user": "https://...", ... },
      { "site": "SiteName2", "url_user": "https://...", ... }
    ]
  },
  ...
}
```

### Benefits

1. **Complete Data**: All fields from Maigret are preserved
2. **No Data Loss**: Nothing is filtered or reformatted
3. **Consistency**: Matches the tool's actual output format
4. **Flexibility**: Users can parse/extract what they need
5. **Transparency**: Raw output shows exactly what Maigret returned

## Comparison with Other Tools

### Sherlock
- Also returns raw output (though it parses stdout because Sherlock's JSON output is actually text URLs)
- No reformatting of the tool's actual output

### Maigret (Fixed)
- Returns raw JSON from files verbatim
- No parsing or reformatting
- Preserves complete data structure

## Code Changes

**Before** (Parsing):
```python
# Parse JSON and extract fields
data = json.load(f)
for site_name, site_data in data.items():
    url_user = site_data.get("url_user")
    # Extract and reformat...
    results[username].append({
        "name": site_name,
        "url": url_user,
        # ... custom structure
    })
```

**After** (Verbatim):
```python
# Read raw JSON and return as-is
if json_type == "simple":
    raw_json_results[username] = json.load(f)  # Raw JSON object
else:  # ndjson
    raw_json_results[username] = [json.loads(line) for line in f if line.strip()]

# Return verbatim
result_data = {
    "status": "success",
    "usernames": usernames,
    "results": raw_json_results,  # Raw JSON as-is
    ...
}
```

## Rationale

**Why not parse?**
1. **Data Loss**: Parsing might miss fields or nested structures
2. **Format Changes**: Maigret's format might change, breaking parsing logic
3. **User Control**: Users should decide how to process the data
4. **Transparency**: Raw output shows exactly what the tool produced
5. **Consistency**: Matches the "verbatim output" requirement for all tools

**When parsing might be needed:**
- Only if the tool's output format is inconsistent or broken
- Only if we need to extract specific fields for compatibility
- But in this case, Maigret's JSON is well-structured and complete

## Conclusion

The tool now returns **verbatim output** - the raw JSON exactly as Maigret produces it, with no parsing, reformatting, or field extraction. This ensures:
- Complete data preservation
- No data loss
- Maximum flexibility for users
- Consistency with the "verbatim output" principle

