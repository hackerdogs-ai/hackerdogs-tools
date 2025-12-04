# Complete CrewAI Installation Guide

## ⚠️ Issue: CrewAI Version Mismatch

The problem is **not Python 3.14** - it's the **CrewAI version**!

- ❌ **CrewAI 0.11.2** (old) - Requires langchain<0.2.0 (Pydantic V1, incompatible with Python 3.14)
- ✅ **CrewAI 0.28.8+** (newer) - Works with Python 3.14 and langchain>=1.1.0

**Error with old version:**
```
pydantic.v1.errors.ConfigError: unable to infer type for attribute "llm_output"
```

## ✅ Solution: Upgrade CrewAI (Keep Python 3.14!)

### Quick Fix (Recommended)

```bash
# Activate your venv
source venv/bin/activate

# Upgrade CrewAI to version compatible with Python 3.14
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install --upgrade 'crewai>=0.28.0'

# Verify
python3 -c "from crewai import Agent; print('✅ CrewAI works!')"
```

### Alternative: Use Python 3.12 (If upgrade doesn't work)

#### Step 1: Install Python 3.12

**Option A: Using pyenv (Recommended)**
```bash
# Install pyenv if not installed
brew install pyenv

# Install Python 3.12.7
pyenv install 3.12.7

# Set as local version
cd /Users/tejaswiredkar/Documents/GitHub/hackerdogs-tools
pyenv local 3.12.7
```

**Option B: Using Homebrew**
```bash
brew install python@3.12
```

#### Step 2: Create Virtual Environment

```bash
# Remove old venv
rm -rf venv

# Create new venv with Python 3.12
python3.12 -m venv venv
# OR if using pyenv:
python3 -m venv venv

# Activate
source venv/bin/activate
```

#### Step 3: Install CrewAI

```bash
# Upgrade pip
pip install --upgrade pip

# Install crewai (no compatibility flags needed!)
pip install crewai
```

#### Step 4: Verify

```bash
python3 -c "from crewai import Agent, Task, Crew; print('✅ CrewAI works!')"
```

## Why Upgrade CrewAI?

1. ✅ **Works with Python 3.14** - No Python version change needed
2. ✅ **Matches your dependencies** - Your `pyproject.toml` specifies `langchain>=1.1.0`
3. ✅ **Uses Pydantic V2** - Compatible with Python 3.14
4. ✅ **Latest features** - CrewAI 0.28.8+ has newer features
5. ✅ **Same as your other project** - Consistency across projects

## Version Comparison

| Version | LangChain | Pydantic | Python 3.14 | Status |
|---------|-----------|----------|-------------|--------|
| CrewAI 0.11.2 | <0.2.0 (V1) | V1 | ❌ No | Old |
| CrewAI 0.28.8+ | >=1.0.0 | V2 | ✅ Yes | Current |

## Your Project Setup

Your `pyproject.toml` already has the right dependencies:
- `langchain>=1.1.0` ✅
- `langchain-core>=1.1.0` ✅  
- `pydantic>=2.12.5` ✅

These work with CrewAI 0.28.8+ and Python 3.14!

## Check Your Python Version

```bash
python3 --version
```

If it shows `Python 3.14.x`, you need to switch to Python 3.12.

## Verify Installation

After setup, test:

```bash
source venv/bin/activate
python3 << 'EOF'
from crewai import Agent, Task, Crew

agent = Agent(
    role="Test Agent",
    goal="Test installation",
    backstory="Testing CrewAI"
)

print("✅ CrewAI is fully functional!")
EOF
```

## Troubleshooting

### If setup script fails:

1. **Check Python 3.12 is installed:**
   ```bash
   python3.12 --version
   ```

2. **Use pyenv:**
   ```bash
   pyenv install 3.12.7
   pyenv local 3.12.7
   ```

3. **Manual venv creation:**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   pip install crewai
   ```

---

**Recommendation:** Upgrade CrewAI to 0.28.8+ to match your other project and work with Python 3.14.

*Last Updated: 2024*
