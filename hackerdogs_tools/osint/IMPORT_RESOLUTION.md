# 🔧 LangChain Import Resolution Guide

## Problem

LangChain imports may not resolve in your IDE even when `langchain` is installed in your virtual environment. This is a common issue with Python IDEs and package resolution.

## Common Causes

1. **Package not installed in editable mode**
   - The IDE may not recognize the package structure
   - Solution: Install in editable mode

2. **IDE using wrong Python interpreter**
   - IDE may be pointing to system Python instead of venv
   - Solution: Configure IDE to use venv Python

3. **Virtual environment not activated**
   - Terminal/IDE may not have venv activated
   - Solution: Activate venv before running/editing

4. **Missing type stubs or package metadata**
   - IDE may need package metadata for autocomplete
   - Solution: Reinstall package or restart IDE

5. **IDE cache issues**
   - IDE may have cached old import paths
   - Solution: Clear IDE cache and restart

## Solutions

### 1. Install Package in Editable Mode

```bash
# From project root
cd /Users/tejaswiredkar/Documents/GitHub/hackerdogs-tools
pip install -e .

# Or with all optional dependencies
pip install -e ".[all,ti,osint]"
```

### 2. Verify Python Interpreter in IDE

**VS Code:**
1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type "Python: Select Interpreter"
3. Choose the venv Python: `./venv/bin/python` or `./venv/bin/python3`

**PyCharm:**
1. Go to Settings → Project → Python Interpreter
2. Select the venv interpreter: `./venv/bin/python`

**Cursor:**
1. Check bottom-right corner for Python version
2. Click to change interpreter
3. Select venv Python

### 3. Activate Virtual Environment

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 4. Verify LangChain Installation

```bash
# Check if langchain is installed
pip list | grep langchain

# Should show:
# langchain
# langchain-core
# langchain-community (if installed)

# Test import
python -c "from langchain.tools import tool; print('OK')"
python -c "from langchain_core.tools import BaseTool; print('OK')"
```

### 5. Clear IDE Cache and Restart

**VS Code/Cursor:**
- Close and reopen IDE
- Or: `Cmd+Shift+P` → "Developer: Reload Window"

**PyCharm:**
- File → Invalidate Caches / Restart

### 6. Check Import Paths

The working tools use these import patterns:

```python
# For @tool decorator (like virus_total.py, otx.py)
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState

# For BaseTool class (like browserless_tool.py)
from langchain_core.tools import BaseTool
```

Both patterns are valid. The `@tool` decorator is for LangChain v1.0+ with state management, while `BaseTool` is the base class.

### 7. Verify Package Structure

Ensure your project structure matches:

```
hackerdogs-tools/
├── hackerdogs_tools/
│   ├── __init__.py
│   ├── osint/
│   │   ├── __init__.py
│   │   └── ...
│   └── ti/
│       ├── __init__.py
│       └── ...
├── venv/
├── pyproject.toml
└── setup.py
```

### 8. Check pyproject.toml

Ensure `langchain` and `langchain-core` are in dependencies:

```toml
dependencies = [
    "langchain>=1.1.0",
    "langchain-core>=1.1.0",
    # ... other deps
]
```

### 9. Reinstall Dependencies

If all else fails:

```bash
# Remove and reinstall
pip uninstall langchain langchain-core -y
pip install langchain>=1.1.0 langchain-core>=1.1.0

# Or reinstall everything
pip install -r requirements.txt
```

## Why It Works in `hackerdogs_tools` Folder

The imports work in the `hackerdogs_tools` folder because:
1. The package is structured as a Python package with `__init__.py`
2. When you `import hackerdogs_tools.ti.virus_total`, Python resolves it from the package structure
3. The IDE may have indexed the local files, making them available for autocomplete

## Testing Import Resolution

Create a test file to verify imports:

```python
# test_imports.py
try:
    from langchain.tools import tool, ToolRuntime
    from langchain.agents import AgentState
    from langchain_core.tools import BaseTool
    print("✅ All LangChain imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
```

Run: `python test_imports.py`

## Still Not Working?

1. **Check Python version**: LangChain requires Python 3.8+
   ```bash
   python --version
   ```

2. **Check if package is in sys.path**:
   ```python
   import sys
   print(sys.path)
   # Should include your venv site-packages
   ```

3. **Check IDE Python extension**: Ensure Python extension is installed and updated

4. **Try absolute imports**: Sometimes relative imports cause issues
   ```python
   # Instead of: from .ti import otx
   # Use: from hackerdogs_tools.ti import otx
   ```

## Quick Fix Checklist

- [ ] Virtual environment activated
- [ ] Package installed in editable mode: `pip install -e .`
- [ ] IDE using correct Python interpreter (venv)
- [ ] LangChain installed: `pip list | grep langchain`
- [ ] IDE cache cleared and restarted
- [ ] Python version is 3.8+

---

**Last Updated:** 2024

