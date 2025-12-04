# Fix for CrewAI Installation with Python 3.14

## Problem

When installing `crewai` with Python 3.14, you encounter two issues:

1. **PyO3 Compatibility Error:**
   ```
   error: the configured Python interpreter version (3.14) is newer than PyO3's maximum supported version (3.12)
   ```

2. **Externally-Managed Environment (PEP 668):**
   ```
   error: externally-managed-environment
   ```

## Solution: Use Virtual Environment + Compatibility Flag

### Step 1: Create/Activate Virtual Environment

```bash
# Create virtual environment (if not exists)
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

### Step 2: Install with Compatibility Flag

```bash
# Set the compatibility flag and install
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install crewai

# Or in one command:
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install crewai
```

### Step 3: Verify Installation

```bash
python3 -c "import crewai; print('✅ CrewAI installed successfully!')"
```

## Complete Installation Script

```bash
#!/bin/bash
# install_crewai.sh

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install with compatibility flag
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install --upgrade pip
pip install crewai

# Verify
python3 -c "import crewai; print('✅ CrewAI installed successfully!')"
```

## Alternative: Use Python 3.12 (Recommended for Production)

For better long-term compatibility, consider using Python 3.12:

```bash
# Using pyenv
pyenv install 3.12.7
pyenv local 3.12.7

# Create venv with Python 3.12
python3.12 -m venv venv
source venv/bin/activate
pip install crewai  # No compatibility flag needed
```

## Why This Works

1. **Virtual Environment:** Solves the externally-managed-environment error by isolating packages
2. **PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1:** Tells PyO3 to use the stable ABI which is forward-compatible with Python 3.14

## Quick Fix for Current Session

If you're already in a virtual environment:

```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install crewai
```

## Add to Shell Profile (Permanent)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# CrewAI compatibility for Python 3.14
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
```

Then reload:
```bash
source ~/.zshrc
```

---

*Last Updated: 2024*
