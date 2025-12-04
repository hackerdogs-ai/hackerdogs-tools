# Quick Fix: CrewAI Installation Issue

## ⚠️ Problem

Python 3.14 is **not compatible** with CrewAI due to Pydantic V1 incompatibility.

**Error:**
```
pydantic.v1.errors.ConfigError: unable to infer type for attribute "llm_output"
```

## ✅ Solution: Install Python 3.12

### Step 1: Install Python 3.12

```bash
brew install python@3.12
```

### Step 2: Create New Virtual Environment

```bash
# Remove old venv
rm -rf venv

# Create venv with Python 3.12
/opt/homebrew/bin/python3.12 -m venv venv

# Activate
source venv/bin/activate
```

### Step 3: Install CrewAI

```bash
pip install --upgrade pip
pip install crewai
```

### Step 4: Verify

```bash
python3 -c "from crewai import Agent; print('✅ CrewAI works!')"
```

## One-Liner (After Python 3.12 is Installed)

```bash
rm -rf venv && /opt/homebrew/bin/python3.12 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install crewai
```

## Why Python 3.12?

- ✅ Fully compatible with CrewAI
- ✅ No compatibility flags needed
- ✅ No Pydantic warnings
- ✅ All dependencies work correctly

## Current Status

- ❌ **Python 3.14:** Not compatible (Pydantic V1 issue)
- ✅ **Python 3.12:** Fully compatible (recommended)
- ⚠️ **Python 3.13:** May work but 3.12 is safer

---

**Next Step:** Run `brew install python@3.12` then follow steps above.
