# SpiderFoot Module Migration Tracker

## Status Legend
- ⏳ **Pending**: Not started
- 🔄 **In Progress**: Currently working on
- ✅ **Complete**: Finished and tested
- ❌ **Blocked**: Waiting on dependency
- ⚠️ **Issue**: Problem encountered

---

## Phase 1: Foundation Setup

### Week 1-2: Foundation

#### Step 1.1: Template Creation
- [ ] ⏳ Review existing tool patterns (holehe, crawl4ai, browserless)
- [ ] ⏳ Create `spiderfoot_langchain_tool.j2` template
- [ ] ⏳ Create `spiderfoot_crewai_tool.j2` template
- [ ] ⏳ Validate template syntax (Jinja2)
- [ ] ⏳ Test template with sample module metadata
- [ ] ⏳ Verify generated code matches existing patterns

**Status**: 🔄 Templates created, need validation

#### Step 1.2: Module Parser
- [ ] ⏳ Create module parser script
- [ ] ⏳ Implement dynamic module import
- [ ] ⏳ Extract `meta` dict
- [ ] ⏳ Extract `opts` dict
- [ ] ⏳ Extract `optdescs` dict
- [ ] ⏳ Extract `watchedEvents()` return value
- [ ] ⏳ Extract `producedEvents()` return value
- [ ] ⏳ Handle API key detection (from `meta['flags']`)
- [ ] ⏳ Test parser on 5-10 sample modules

**Status**: ⏳ Not started

#### Step 1.3: Code Generator
- [ ] ⏳ Create `generate_spiderfoot_tools.py` script
- [ ] ⏳ Integrate Jinja2 template rendering
- [ ] ⏳ Implement file writing logic
- [ ] ⏳ Add error handling for module parsing
- [ ] ⏳ Add logging for generation process
- [ ] ⏳ Create output directory structure
- [ ] ⏳ Test generator on 5-10 pilot modules
- [ ] ⏳ Validate generated Python code syntax
- [ ] ⏳ Verify generated tools import correctly

**Status**: ⏳ Not started

#### Step 1.4: Pilot Testing
- [ ] ⏳ Select 5-10 diverse pilot modules
  - [ ] DNS module (e.g., `sfp_dnsbrute`)
  - [ ] Reputation module (e.g., `sfp_abuseipdb`)
  - [ ] API-based module (e.g., `sfp_virustotal`)
  - [ ] Simple module (e.g., `sfp_whois`)
  - [ ] Complex module (e.g., `sfp_portscan_tcp`)
- [ ] ⏳ Generate tools for pilot modules
- [ ] ⏳ Test LangChain tool imports
- [ ] ⏳ Test CrewAI tool imports
- [ ] ⏳ Fix any template/generator issues
- [ ] ⏳ Update templates based on findings

**Status**: ⏳ Not started

---

## Phase 2: Module Generation

### Week 3-4: Core Modules (Priority 1)

#### Step 2.1: DNS Modules (~30 modules)
- [ ] ⏳ Generate LangChain tools for all DNS modules
- [ ] ⏳ Generate CrewAI tools for all DNS modules
- [ ] ⏳ Validate syntax for all generated files
- [ ] ⏳ Test imports for all DNS tools
- [ ] ⏳ Document any special cases

**Modules List**:
- [ ] ⏳ sfp_dnsbrute
- [ ] ⏳ sfp_dnsresolve
- [ ] ⏳ sfp_dnszone
- [ ] ⏳ sfp_dnsresolve6
- [ ] ⏳ ... (remaining DNS modules)

**Status**: ⏳ Not started

#### Step 2.2: Reputation/Threat Intel Modules (~40 modules)
- [ ] ⏳ Generate LangChain tools for all reputation modules
- [ ] ⏳ Generate CrewAI tools for all reputation modules
- [ ] ⏳ Validate syntax for all generated files
- [ ] ⏳ Test imports for all reputation tools
- [ ] ⏳ Handle API key requirements
- [ ] ⏳ Document API key setup for each module

**Key Modules**:
- [ ] ⏳ sfp_abuseipdb
- [ ] ⏳ sfp_virustotal
- [ ] ⏳ sfp_alienvault
- [ ] ⏳ sfp_greynoise
- [ ] ⏳ ... (remaining reputation modules)

**Status**: ⏳ Not started

#### Step 2.3: Infrastructure Modules (~30 modules)
- [ ] ⏳ Generate LangChain tools for all infrastructure modules
- [ ] ⏳ Generate CrewAI tools for all infrastructure modules
- [ ] ⏳ Validate syntax for all generated files
- [ ] ⏳ Test imports for all infrastructure tools
- [ ] ⏳ Handle special execution requirements

**Key Modules**:
- [ ] ⏳ sfp_portscan_tcp
- [ ] ⏳ sfp_nmap
- [ ] ⏳ sfp_shodan
- [ ] ⏳ ... (remaining infrastructure modules)

**Status**: ⏳ Not started

### Week 5-6: Extended Modules (Priority 2)

#### Step 2.4: Web Scraping Modules (~35 modules)
- [ ] ⏳ Generate all web scraping tools
- [ ] ⏳ Validate and test
- [ ] ⏳ Document special cases

**Status**: ⏳ Not started

#### Step 2.5: Social Media Modules (~25 modules)
- [ ] ⏳ Generate all social media tools
- [ ] ⏳ Validate and test
- [ ] ⏳ Document special cases

**Status**: ⏳ Not started

#### Step 2.6: Cloud/Storage Modules (~15 modules)
- [ ] ⏳ Generate all cloud/storage tools
- [ ] ⏳ Validate and test
- [ ] ⏳ Document special cases

**Status**: ⏳ Not started

### Week 7-8: Remaining Modules (Priority 3)

#### Step 2.7: Metadata/File Analysis (~20 modules)
- [ ] ⏳ Generate all metadata tools
- [ ] ⏳ Validate and test

**Status**: ⏳ Not started

#### Step 2.8: Email/Phone Modules (~15 modules)
- [ ] ⏳ Generate all email/phone tools
- [ ] ⏳ Validate and test

**Status**: ⏳ Not started

#### Step 2.9: Whois/Registration (~10 modules)
- [ ] ⏳ Generate all whois tools
- [ ] ⏳ Validate and test

**Status**: ⏳ Not started

#### Step 2.10: Miscellaneous (~13 modules)
- [ ] ⏳ Generate all misc tools
- [ ] ⏳ Validate and test

**Status**: ⏳ Not started

---

## Phase 3: Testing & Integration

### Week 9-10: Testing

#### Step 3.1: Unit Tests
- [ ] ⏳ Create test structure for SpiderFoot tools
- [ ] ⏳ Write unit tests for pilot modules
- [ ] ⏳ Write unit tests for core modules
- [ ] ⏳ Test API key handling
- [ ] ⏳ Test error handling
- [ ] ⏳ Test Docker execution
- [ ] ⏳ Test result format

**Status**: ⏳ Not started

#### Step 3.2: Integration Tests
- [ ] ⏳ Test tool chains (DNS → Reputation)
- [ ] ⏳ Test with LangChain agents
- [ ] ⏳ Test with CrewAI agents
- [ ] ⏳ Test with real targets
- [ ] ⏳ Performance testing

**Status**: ⏳ Not started

#### Step 3.3: Documentation
- [ ] ⏳ Document all generated tools
- [ ] ⏳ Create usage examples
- [ ] ⏳ Document API key requirements
- [ ] ⏳ Create migration guide
- [ ] ⏳ Update main README

**Status**: ⏳ Not started

---

## Module Execution Implementation

### Execution Method Research
- [ ] ⏳ Research SpiderFoot CLI execution
- [ ] ⏳ Research direct Python import method
- [ ] ⏳ Research API direct method
- [ ] ⏳ Determine best approach per module type
- [ ] ⏳ Implement execution logic in templates
- [ ] ⏳ Test execution with pilot modules

**Status**: ⏳ Not started

---

## Progress Summary

**Total Modules**: 233+
**Generated**: 0
**Tested**: 0
**Complete**: 0

**Current Phase**: Phase 1 - Foundation Setup
**Current Step**: Step 1.1 - Template Creation

---

## Issues & Blockers

### Current Issues
- None yet

### Blockers
- None yet

---

## Notes

### Template Validation
- Templates created but need testing with actual module metadata
- Need to verify Jinja2 syntax is correct
- Need to ensure generated code is valid Python

### Module Parser
- Need to handle edge cases in module metadata
- Some modules may have complex opts structures
- API key detection needs to be robust

### Code Generator
- Should include dry-run mode
- Should include verbose logging
- Should handle errors gracefully
- Should create backup of existing files

---

## Daily Progress Log

### 2025-12-07
- ✅ Created migration plan document
- ✅ Created design document
- ✅ Created Jinja2 templates (LangChain & CrewAI)
- ✅ Created module parser (AST-based, no imports needed)
- ✅ Created code generator script
- ✅ Fixed template type handling (Python types vs JSON)
- ✅ Fixed boolean value serialization (True/False vs true/false)
- ✅ Generated pilot modules: sfp_dnsbrute, sfp_abuseipdb, sfp_whois, sfp_virustotal
- ✅ Validated generated code syntax
- 🔄 Testing pilot modules with imports

