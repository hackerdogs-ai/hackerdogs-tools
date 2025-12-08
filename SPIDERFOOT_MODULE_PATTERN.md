# SpiderFoot Module Migration Pattern

## Overview

This document describes the **standard pattern** for migrating SpiderFoot modules into LangChain and CrewAI tools.

## Pattern: 4 Files Per Module

For **every SpiderFoot module**, we create **4 files**:

1. **Implementation** (`_implementations.py`)
2. **LangChain Tool** (`sfp_{module}_langchain.py`)
3. **CrewAI Tool** (`sfp_{module}_crewai.py`)
4. **Test File** (`test_sfp_{module}.py`)

## File Structure

```
hackerdogs_tools/osint/spiderfoot_modules/
├── _implementations.py          # All implementation functions
├── sfp_{module}_langchain.py    # LangChain tool wrapper
├── sfp_{module}_crewai.py       # CrewAI tool wrapper
└── ../tests/
    └── test_sfp_{module}.py     # Test file (standalone, LangChain, CrewAI)
```

## 1. Implementation Function

**Location**: `hackerdogs_tools/osint/spiderfoot_modules/_implementations.py`

**Pattern**:
```python
def implement_{module_name}(target: str, **kwargs) -> Dict[str, Any]:
    """
    {Module Name} implementation - migrated from SpiderFoot sfp_{module_name}.
    
    Logic migrated from: spiderfoot/modules/sfp_{module_name}.py
    - [Brief description of what it does]
    """
    try:
        # Core logic here
        # - Direct Python library calls (requests, socket, dns.resolver, etc.)
        # - NO Docker execution
        # - NO SpiderFoot framework dependencies
        
        return {
            "status": "success",
            "data": result_data
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"{Module name} failed: {str(e)}"
        }
```

**Key Requirements**:
- ✅ Standalone Python function
- ✅ Uses direct Python libraries (requests, socket, dns.resolver, etc.)
- ✅ NO Docker execution
- ✅ NO SpiderFoot framework dependencies
- ✅ Consistent error handling
- ✅ Returns `Dict[str, Any]` with `status` and `data` keys

## 2. LangChain Tool

**Location**: `hackerdogs_tools/osint/spiderfoot_modules/sfp_{module}_langchain.py`

**Pattern**:
```python
from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
    implement_{module_name}
)

@tool
def sfp_{module_name}(
    runtime: ToolRuntime,
    target: str,
    **kwargs: Any
) -> str:
    """
    [Tool description from SpiderFoot meta]
    
    Use Cases: [from meta]
    """
    try:
        # Get user_id from runtime state
        user_id = runtime.state.get("user_id", "unknown")
        
        # Validate inputs
        if not target or not isinstance(target, str):
            return json.dumps({
                "status": "error",
                "message": "Invalid target provided",
                "user_id": user_id
            })
        
        # Build parameters for implementation function
        implementation_params = {
            "target": target,
            **kwargs  # Pass through all other parameters
        }
        
        # Execute migrated implementation
        implementation_result = implement_{module_name}(**implementation_params)
        
        # Return verbatim output
        return json.dumps(implementation_result)
        
    except Exception as e:
        # Error handling
        return json.dumps({
            "status": "error",
            "message": str(e),
            "user_id": user_id
        })
```

**Key Requirements**:
- ✅ Uses `@tool` decorator from LangChain
- ✅ Receives `ToolRuntime` for state management
- ✅ Imports implementation from `_implementations.py`
- ✅ Validates inputs
- ✅ Returns JSON string (verbatim output)
- ✅ Consistent error handling

## 3. CrewAI Tool

**Location**: `hackerdogs_tools/osint/spiderfoot_modules/sfp_{module}_crewai.py`

**Pattern**:
```python
from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
    implement_{module_name}
)

class Sfp{ModuleName}ToolSchema(BaseModel):
    target: str = Field(..., description="Target to investigate")
    # ... other fields from SpiderFoot opts

class Sfp{ModuleName}Tool(BaseTool):
    """Tool for [description from SpiderFoot meta]."""
    
    name: str = "{Module Name}"
    description: str = "[Description from meta]\n\nUse Cases: [from meta]"
    args_schema: type[BaseModel] = Sfp{ModuleName}ToolSchema
    
    def _run(
        self,
        target: str,
        **kwargs: Any
    ) -> str:
        """Execute {Module Name}."""
        try:
            # Get user_id from kwargs
            user_id = kwargs.get("user_id", "")
            
            # Validate inputs
            if not target or not isinstance(target, str):
                return json.dumps({
                    "status": "error",
                    "message": "Invalid target provided",
                    "user_id": user_id
                })
            
            # Build parameters for implementation function
            implementation_params = {
                "target": target,
                **kwargs
            }
            
            # Execute migrated implementation
            implementation_result = implement_{module_name}(**implementation_params)
            
            # Return verbatim output
            return json.dumps(implementation_result)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
                "user_id": user_id
            })
```

**Key Requirements**:
- ✅ Extends `BaseTool` from CrewAI
- ✅ Uses Pydantic `BaseModel` for schema
- ✅ Imports implementation from `_implementations.py`
- ✅ Validates inputs
- ✅ Returns JSON string (verbatim output)
- ✅ Consistent error handling

## 4. Test File

**Location**: `hackerdogs_tools/osint/tests/test_sfp_{module}.py`

**Pattern**:
```python
import pytest
from hackerdogs_tools.osint.spiderfoot_modules.sfp_{module}_langchain import sfp_{module_name}
from hackerdogs_tools.osint.spiderfoot_modules.sfp_{module}_crewai import Sfp{ModuleName}Tool

def test_sfp_{module}_standalone():
    """Test standalone implementation."""
    from hackerdogs_tools.osint.spiderfoot_modules._implementations import implement_{module_name}
    
    result = implement_{module_name}(target="test_target")
    assert result["status"] in ["success", "error"]
    assert "data" in result or "message" in result

def test_sfp_{module}_langchain():
    """Test LangChain tool."""
    # Setup runtime
    runtime = ToolRuntime(...)
    
    result_json = sfp_{module_name}(runtime, target="test_target")
    result = json.loads(result_json)
    assert result["status"] in ["success", "error"]

def test_sfp_{module}_crewai():
    """Test CrewAI tool."""
    tool = Sfp{ModuleName}Tool()
    result_json = tool._run(target="test_target", user_id="test_user")
    result = json.loads(result_json)
    assert result["status"] in ["success", "error"]
```

**Key Requirements**:
- ✅ Tests standalone implementation
- ✅ Tests LangChain tool
- ✅ Tests CrewAI tool
- ✅ Uses appropriate test data
- ✅ Validates output structure

## Generation Process

### Step 1: Parse SpiderFoot Module

Use `generate_spiderfoot_tools.py` to parse the SpiderFoot module:
- Extracts `meta`, `opts`, `optdescs`, `watchedEvents`, `producedEvents`
- Detects API key requirements
- Identifies parameter types

### Step 2: Generate Implementation

Manually create implementation function in `_implementations.py`:
- Extract core logic from SpiderFoot module
- Reimplement using direct Python libraries
- Follow error handling pattern
- Test independently

### Step 3: Generate Tool Files

Run generator:
```bash
python hackerdogs_tools/osint/generate_spiderfoot_tools.py --modules sfp_{module_name}
```

This automatically generates:
- `sfp_{module}_langchain.py`
- `sfp_{module}_crewai.py`
- `test_sfp_{module}.py`

### Step 4: Verify

1. ✅ Implementation compiles
2. ✅ LangChain tool imports successfully
3. ✅ CrewAI tool imports successfully
4. ✅ Test file runs successfully
5. ✅ All files follow the pattern

## Checklist for Each Module

- [ ] Implementation function created in `_implementations.py`
- [ ] LangChain tool generated (`sfp_{module}_langchain.py`)
- [ ] CrewAI tool generated (`sfp_{module}_crewai.py`)
- [ ] Test file generated (`test_sfp_{module}.py`)
- [ ] All files compile/import successfully
- [ ] Implementation matches SpiderFoot module logic
- [ ] Error handling is consistent
- [ ] Documentation is clear

## Current Status

**Total SpiderFoot Modules**: 231
**Implemented**: 75
**Generated Tools**: 75 (LangChain + CrewAI)
**Test Files**: 75
**Coverage**: 32.5% (75/231)

## Notes

- All implementations must be **standalone** (no SpiderFoot dependencies)
- Use **direct Python libraries** (requests, socket, dns.resolver, etc.)
- **NO Docker execution** for implementations
- **Consistent error handling** across all modules
- **Verbatim output** - return tool results exactly as generated
- **Pattern compliance** - every module must follow this 4-file pattern

