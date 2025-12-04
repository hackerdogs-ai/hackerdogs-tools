# 📦 OSINT Tools Dependencies List

This document lists all dependencies required to implement the OSINT tools as specified in the PRD.

## 🔍 Import Resolution Issue

### Problem
LangChain imports may not resolve in IDE even when installed because:
1. **Package not installed in editable mode**: Run `pip install -e .` from project root
2. **IDE using wrong Python interpreter**: Ensure IDE points to venv Python
3. **Missing type stubs**: LangChain v1.0+ includes type hints, but IDE may need restart
4. **Virtual environment not activated**: Ensure venv is activated in terminal/IDE

### Solution
```bash
# From project root
pip install -e .
# Or with all optional dependencies
pip install -e ".[all,ti,osint]"
```

---

## 🐍 Python Alternatives Available!

**Good News:** Most tools have Python package alternatives! See `PYTHON_ALTERNATIVES.md` for details.

**Key Points:**
- ✅ **Identity tools** (Sherlock, Maigret, GHunt, Holehe) are already Python packages
- ✅ **TheHarvester** is already a Python package
- ✅ **Scrapy** is already a Python package
- ✅ **Subdomain enumeration** can use `sublist3r` or `dnsrecon` (Python)
- ✅ **Wayback Machine** can use `waybackpy` (Python)
- ✅ **Metadata extraction** can use `exifread` or `Pillow` (Python)

**Only tools that really need binaries:**
- ⚠️ **Nuclei** - Template-based scanning (Go templates)
- ⚠️ **Masscan/ZMap** - Extreme speed scanning (but `python-nmap` works for most cases)

---

## 📋 Required Dependencies

### Core LangChain & CrewAI (Already Installed)
- ✅ `langchain>=1.1.0` - Core LangChain framework
- ✅ `langchain-core>=1.1.0` - Core LangChain primitives
- ⚠️ `crewai` - CrewAI framework (needs to be added)
- ✅ `pydantic>=2.12.5` - Data validation
- ✅ `requests>=2.32.5` - HTTP requests

### Infrastructure & Network Recon Tools

#### 1. OWASP Amass
- **Binary**: `amass` (Go binary)
- **Installation**: 
  ```bash
  # macOS
  brew install amass
  # Linux
  wget https://github.com/OWASP/Amass/releases/download/v4.2.0/amass_linux_amd64.zip
  unzip amass_linux_amd64.zip
  sudo mv amass /usr/local/bin/
  # Or via Go
  go install -v github.com/owasp-amass/amass/v4/...@master
  ```

#### 2. Nuclei
- **Binary**: `nuclei` (Go binary)
- **Installation**:
  ```bash
  # macOS
  brew install nuclei
  # Linux
  go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
  # Or download from releases
  ```

#### 3. Subfinder
- **Binary**: `subfinder` (Go binary)
- **Installation**:
  ```bash
  # macOS
  brew install subfinder
  # Linux
  go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
  ```

#### 4. Masscan
- **Binary**: `masscan` (C binary)
- **Installation**:
  ```bash
  # macOS
  brew install masscan
  # Linux
  sudo apt-get install masscan
  # Or compile from source
  git clone https://github.com/robertdavidgraham/masscan
  cd masscan
  make
  ```

#### 5. ZMap
- **Binary**: `zmap` (C binary)
- **Installation**:
  ```bash
  # macOS
  brew install zmap
  # Linux
  sudo apt-get install zmap
  ```

#### 6. TheHarvester
- **Python Package**: `theHarvester`
- **Installation**:
  ```bash
  pip install theHarvester
  # Or from source
  git clone https://github.com/laramies/theHarvester
  cd theHarvester
  pip install -r requirements.txt
  ```

#### 7. DNSDumpster
- **Python Packages**: `requests`, `beautifulsoup4` (already installed)
- **Optional**: Custom wrapper or API client

### Identity & SOCMINT Tools

#### 8. Sherlock
- **Python Package**: `sherlock-project`
- **Installation**:
  ```bash
  pip install sherlock-project
  # Or from source
  git clone https://github.com/sherlock-project/sherlock.git
  cd sherlock
  pip install -r requirements.txt
  ```

#### 9. Maigret
- **Python Package**: `maigret`
- **Installation**:
  ```bash
  pip install maigret
  # Or from source
  git clone https://github.com/soxoj/maigret.git
  cd maigret
  pip install -r requirements.txt
  ```

#### 10. GHunt
- **Python Package**: `ghunt`
- **Installation**:
  ```bash
  pip install ghunt
  # Or from source
  git clone https://github.com/mxrch/GHunt.git
  cd GHunt
  pip install -r requirements.txt
  ```

#### 11. Holehe
- **Python Package**: `holehe`
- **Installation**:
  ```bash
  pip install holehe
  # Or from source
  git clone https://github.com/megadose/holehe.git
  cd holehe
  pip install -r requirements.txt
  ```

### Content & Dark Web Tools

#### 12. Scrapy
- **Python Package**: `scrapy`
- **Installation**:
  ```bash
  pip install scrapy
  ```

#### 13. Waybackurls
- **Binary**: `waybackurls` (Go binary)
- **Installation**:
  ```bash
  # macOS
  brew install waybackurls
  # Linux
  go install github.com/tomnomnom/waybackurls@latest
  ```

#### 14. OnionSearch
- **Python Package**: `onionsearch` (may need custom implementation)
- **Installation**:
  ```bash
  # Check if package exists, otherwise use custom implementation
  pip install onionsearch  # May not exist
  # Alternative: Use requests with Tor proxy
  pip install requests[socks] pysocks
  ```

### Threat Intelligence Tools

#### 15. AlienVault OTX
- **Python Package**: `OTXv2` (already in optional dependencies)
- **Installation**:
  ```bash
  pip install OTXv2
  ```

#### 16. URLHaus
- **Python Packages**: `requests`, `csv` (already installed)
- **No additional packages needed** (uses API or CSV download)

#### 17. MISP
- **Python Package**: `pymisp` (already in optional dependencies)
- **Installation**:
  ```bash
  pip install pymisp
  ```

#### 18. AbuseIPDB
- **Python Packages**: `requests` (already installed)
- **No additional packages needed** (uses REST API)

### File & Metadata Analysis Tools

#### 19. ExifTool
- **Binary**: `exiftool` (Perl script)
- **Installation**:
  ```bash
  # macOS
  brew install exiftool
  # Linux
  sudo apt-get install libimage-exiftool-perl
  # Or download from https://exiftool.org/
  ```

#### 20. YARA
- **Python Package**: `yara-python`
- **Binary**: `yara` (C library)
- **Installation**:
  ```bash
  # macOS
  brew install yara
  pip install yara-python
  # Linux
  sudo apt-get install yara libyara-dev
  pip install yara-python
  ```

### Framework Tools

#### 21. SpiderFoot
- **Python Package**: `spiderfoot` (or use REST API)
- **Installation**:
  ```bash
  # Option 1: Python package (if available)
  pip install spiderfoot
  # Option 2: Self-hosted instance with REST API
  # Follow SpiderFoot installation guide
  ```

---

## 📝 Complete Installation Script

### Python Packages
```bash
pip install \
  theHarvester \
  sherlock-project \
  maigret \
  ghunt \
  holehe \
  scrapy \
  OTXv2 \
  pymisp \
  yara-python \
  requests[socks] \
  pysocks
```

### Binaries (macOS with Homebrew)
```bash
brew install \
  amass \
  nuclei \
  subfinder \
  masscan \
  zmap \
  waybackurls \
  exiftool \
  yara
```

### Binaries (Linux/Debian)
```bash
sudo apt-get update && sudo apt-get install -y \
  masscan \
  zmap \
  exiftool \
  yara \
  libyara-dev

# Go binaries (requires Go installed)
go install -v github.com/owasp-amass/amass/v4/...@master
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/tomnomnom/waybackurls@latest
```

---

## 🔧 Additional Dependencies for Production

### Proxy Support (Required for Identity Tools)
```bash
pip install requests[socks] pysocks
```

### Tor Support (For OnionSearch)
```bash
# Install Tor
# macOS
brew install tor
# Linux
sudo apt-get install tor

# Python packages
pip install requests[socks] pysocks stem
```

### CrewAI (If not already installed)
```bash
pip install crewai crewai-tools
```

---

## 📦 Update pyproject.toml

Add to `[project.optional-dependencies]`:

```toml
osint = [
    "theHarvester",
    "sherlock-project",
    "maigret",
    "ghunt",
    "holehe",
    "scrapy",
    "OTXv2",
    "pymisp",
    "yara-python",
    "requests[socks]",
    "pysocks",
    "stem",  # For Tor support
    "crewai",
    "crewai-tools",
]
```

---

## ✅ Verification Checklist

After installation, verify each tool:

```bash
# Binaries
amass -version
nuclei -version
subfinder -version
masscan --version
zmap --version
waybackurls -h
exiftool -ver
yara --version

# Python packages
python -c "import theHarvester; print('theHarvester OK')"
python -c "import sherlock; print('sherlock OK')"
python -c "import maigret; print('maigret OK')"
python -c "import ghunt; print('ghunt OK')"
python -c "import holehe; print('holehe OK')"
python -c "import scrapy; print('scrapy OK')"
python -c "import OTXv2; print('OTXv2 OK')"
python -c "import pymisp; print('pymisp OK')"
python -c "import yara; print('yara OK')"
```

---

## 🚨 Important Notes

1. **Binary Tools**: Some tools require system-level installation (not pip)
2. **Go Tools**: Require Go compiler for installation from source
3. **Tor**: Required for OnionSearch, must be running separately
4. **Proxy Rotation**: Production use requires proxy service for identity tools
5. **Rate Limiting**: All tools should implement rate limiting
6. **Legal Compliance**: Ensure you have permission to scan targets

---

**Last Updated:** 2024

