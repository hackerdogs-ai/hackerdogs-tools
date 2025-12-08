# SpiderFoot Module Migration Design
## Updated Design Summary

### Key Design Decisions

1. **Single Folder Structure**
   - All modules in `hackerdogs_tools/osint/spiderfoot_modules/`
   - No subfolder categorization
   - Simple, flat structure for easier maintenance

2. **Phase 1: Modules Only**
   - Focus exclusively on migrating 233+ SpiderFoot modules
   - Correlation rules deferred to future phase
   - 8-week timeline for module migration

3. **Jinja2 Template-Based Generation**
   - Templates match existing tool patterns exactly
   - Same logging, exception handling, result format
   - Automated code generation reduces errors

---

## Directory Structure

```
hackerdogs_tools/osint/
├── spiderfoot_modules/
│   ├── __init__.py
│   ├── sfp_dnsbrute_langchain.py
│   ├── sfp_dnsbrute_crewai.py
│   ├── sfp_abuseipdb_langchain.py
│   ├── sfp_abuseipdb_crewai.py
│   └── ... (all 233+ modules)
├── templates/
│   ├── spiderfoot_langchain_tool.j2
│   └── spiderfoot_crewai_tool.j2
└── frameworks/
    ├── spiderfoot_langchain.py  # Existing orchestrator
    └── spiderfoot_crewai.py     # Existing orchestrator
```

---

## Template Architecture

### Matching Existing Patterns

**Templates follow these existing tool patterns:**
- `holehe_langchain.py` / `holehe_crewai.py`
- `crawl4ai_langchain.py` / `crawl4ai_crewai.py`
- `browserless_langchain.py` / `browserless_crewai.py`

### Key Template Features

1. **Logging Pattern**
   ```python
   from hd_logging import setup_logger
   from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
   
   logger = setup_logger(__name__, log_file_path="logs/spiderfoot_{module_name}_tool.log")
   
   safe_log_info(logger, f"[sfp_{module_name}] Starting", target=target, user_id=user_id)
   safe_log_error(logger, error_msg, target=target, user_id=user_id, exc_info=True)
   ```

2. **Exception Handling**
   ```python
   try:
       # Tool logic
   except Exception as e:
       safe_log_error(logger, f"Error: {str(e)}", exc_info=True)
       return json.dumps({"status": "error", "message": str(e), "user_id": user_id})
   ```

3. **Result Format**
   ```python
   {
       "status": "success",
       "module": "sfp_{module_name}",
       "module_name": "{meta.name}",
       "target": target,
       "raw_response": {...},
       "user_id": user_id,
       "note": "Raw output from SpiderFoot {meta.name} module - no parsing applied"
   }
   ```

4. **API Key Handling**
   - LangChain: `runtime.state.get("api_keys", {})`
   - CrewAI: `kwargs.get("api_keys", {})`
   - Fallback: `os.getenv()`

5. **Docker Execution**
   - Uses `execute_in_docker()` from `docker_client.py`
   - Same pattern as other tools
   - Timeout: 300 seconds (5 minutes)

---

## Code Generator Structure

**File**: `hackerdogs_tools/osint/generate_spiderfoot_tools.py`

**Process:**
1. Scan `spiderfoot/modules/` directory
2. Import each module class dynamically
3. Extract metadata:
   - `meta` dict
   - `opts` dict
   - `optdescs` dict
   - `watchedEvents()` return value
   - `producedEvents()` return value
4. Generate tools using Jinja2 templates
5. Write to `spiderfoot_modules/` directory

**Generator Output:**
- `sfp_{module_name}_langchain.py`
- `sfp_{module_name}_crewai.py`

---

## Implementation Phases

### Phase 1: Foundation & Module Migration (Weeks 1-8)

**Week 1-2: Foundation**
- Create Jinja2 templates
- Build code generator script
- Test with 5-10 pilot modules
- Validate generated code matches patterns

**Week 3-4: Core Modules (Priority 1)**
- DNS modules (~30)
- Reputation/Threat Intel (~40)
- Infrastructure (~30)

**Week 5-6: Extended Modules (Priority 2)**
- Web Scraping (~35)
- Social Media (~25)
- Cloud/Storage (~15)

**Week 7-8: Remaining Modules (Priority 3)**
- Metadata/File Analysis (~20)
- Email/Phone (~15)
- Whois/Registration (~10)
- Miscellaneous (~13)

### Phase 2: Testing & Integration (Weeks 9-10)
- Unit tests for all tools
- Integration tests
- Documentation
- Performance optimization

---

## Template Variables

**Jinja2 Template Context:**
```python
{
    'module_name': 'dnsbrute',  # Short name
    'module_class_name': 'sfp_dnsbrute',  # Full class name
    'meta': {...},  # Module metadata
    'opts': {...},  # Configuration options
    'optdescs': {...},  # Option descriptions
    'watched_events': ['DOMAIN_NAME'],  # Input events
    'produced_events': ['INTERNET_NAME'],  # Output events
    'api_key_name': 'api_key',  # API key field name (if applicable)
    'has_api_key': True  # Boolean flag
}
```

---

## Execution Method (To Be Determined)

**Options:**
1. **Direct Python Import**: Import SpiderFoot module, create events, execute
2. **Docker CLI**: Run SpiderFoot CLI via Docker
3. **API Direct**: For modules that call external APIs, bypass SpiderFoot

**Template Placeholder:**
- Templates include TODO comments for execution logic
- Actual implementation method will be determined during Phase 1
- May vary by module type

---

## Success Criteria

- [ ] All 233+ modules have LangChain tools
- [ ] All 233+ modules have CrewAI tools
- [ ] All tools match existing patterns exactly
- [ ] All tools use same logging/exception handling
- [ ] All tools return consistent JSON format
- [ ] Code generator successfully processes all modules
- [ ] Templates produce valid Python code

---

## Next Steps

1. **Review Templates**: Validate Jinja2 templates match existing patterns
2. **Build Generator**: Create code generator script
3. **Pilot Test**: Generate 5-10 modules and test
4. **Refine**: Update templates based on pilot results
5. **Generate All**: Run generator for all 233+ modules
6. **Test**: Comprehensive testing of generated tools

