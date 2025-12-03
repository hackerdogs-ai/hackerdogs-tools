# Migration Guide: `tools/` to `hackerdogs_tools/`

## Why the Change?

The package was restructured from `tools/` to `hackerdogs_tools/` for the following reasons:

### 1. **PyPI Package Naming Requirements**
- **PyPI package name**: `hackerdogs-tools` (with hyphen)
- **Python import name**: `hackerdogs_tools` (with underscore)
- When users install: `pip install hackerdogs-tools`
- They import: `import hackerdogs_tools` (not `import tools`)

### 2. **Python Package Best Practices**
- Package directory name should match the PyPI package name (hyphen → underscore)
- Generic names like `tools` can conflict with other packages
- Makes the package more discoverable and professional

### 3. **Import Consistency**
- All imports now use: `from hackerdogs_tools.ti import ...`
- Consistent with package name and PyPI distribution
- Clear namespace for the package

## Current Structure

```
hackerdogs-tools/
├── hackerdogs_tools/     # ✅ Package directory (for PyPI)
│   ├── __init__.py
│   ├── ti/
│   ├── prodx/
│   └── ...
└── tools/                # ⚠️  Old directory (can be removed)
    ├── ti/
    ├── prodx/
    └── ...
```

## Migration Options

### Option 1: Remove `tools/` Directory (Recommended)
Since `hackerdogs_tools/` has all the fixed imports and proper structure:

```bash
# Remove the old directory
rm -rf tools/
```

**Pros:**
- Clean structure
- No duplication
- Single source of truth

**Cons:**
- Any code referencing `tools/` will break (but imports were already broken)

### Option 2: Keep `tools/` as Symlink (Backward Compatibility)
For projects that might still reference `tools/`:

```bash
# Remove old tools directory
rm -rf tools/

# Create symlink
ln -s hackerdogs_tools tools
```

**Pros:**
- Backward compatible
- Both imports work: `from tools.ti import ...` and `from hackerdogs_tools.ti import ...`

**Cons:**
- Can be confusing
- Not recommended for PyPI packages

### Option 3: Keep Both (Not Recommended)
Keep both directories but maintain only `hackerdogs_tools/`:

**Pros:**
- No immediate breaking changes

**Cons:**
- Duplication
- Maintenance burden
- Confusion about which to use

## Recommended Action

**Remove the `tools/` directory** since:
1. All imports have been fixed to use `hackerdogs_tools`
2. The package structure is complete in `hackerdogs_tools/`
3. No code should reference `tools/` anymore (all imports were updated)

## Import Changes

### Before (Old - Broken)
```python
from shared.modules.tools.ti.otx import otx_file_report
from shared.modules.tools.prodx.excel_tools import ReadExcelStructuredTool
```

### After (New - Fixed)
```python
from hackerdogs_tools.ti import otx_file_report
from hackerdogs_tools.prodx import ReadExcelStructuredTool
```

## Verification

After migration, verify imports work:

```python
# Test imports
from hackerdogs_tools.ti import otx_file_report
from hackerdogs_tools.prodx import ReadExcelStructuredTool
from hackerdogs_tools.victorialogs_tools import victorialogs_query

print("✅ All imports working!")
```

