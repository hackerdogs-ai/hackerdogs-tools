# 🐍 Python Alternatives to Binary OSINT Tools

## Why Binary Tools?

Many OSINT tools are written in Go, C, or other compiled languages because they:
1. **Need extreme performance** (e.g., Masscan can scan the entire internet in minutes)
2. **Require low-level network access** (raw sockets, packet crafting)
3. **Are maintained by security communities** who prefer compiled languages

However, **Python alternatives exist** for most functionality! This document lists Python packages that can replace binary dependencies.

---

## 🔄 Tool-by-Tool Python Alternatives

### Infrastructure & Network Recon

#### 1. Amass → Python Alternatives
**Binary:** `amass` (Go)  
**Python Alternatives:**
- ✅ **`dnspython`** - DNS toolkit for subdomain enumeration
- ✅ **`subdomain3`** - Python subdomain enumeration tool
- ✅ **`sublist3r`** - Python subdomain enumeration tool
- ✅ **`dnsrecon`** - DNS enumeration tool (Python)

**Recommendation:** Use `sublist3r` or `dnsrecon` for subdomain enumeration. They're pure Python and work well.

```bash
pip install sublist3r dnsrecon dnspython
```

#### 2. Subfinder → Python Alternatives
**Binary:** `subfinder` (Go)  
**Python Alternatives:**
- ✅ **`sublist3r`** - Same as above
- ✅ **`dnsrecon`** - Same as above
- ✅ **`subbrute`** - Subdomain brute-forcing tool

**Recommendation:** `sublist3r` is the best Python alternative.

#### 3. Nuclei → Python Alternatives
**Binary:** `nuclei` (Go)  
**Python Alternatives:**
- ⚠️ **No direct equivalent** - Nuclei uses Go templates
- ✅ **`python-nmap`** - Python wrapper for nmap (vulnerability scanning)
- ✅ **`vulners`** - Python vulnerability scanner API
- ✅ **`requests` + custom templates** - Build your own scanner

**Recommendation:** Use `python-nmap` for port/vulnerability scanning, or build custom scanners with `requests`.

```bash
pip install python-nmap vulners
```

#### 4. Masscan → Python Alternatives
**Binary:** `masscan` (C) - Extremely fast  
**Python Alternatives:**
- ✅ **`python-nmap`** - Slower but Python-native
- ✅ **`scapy`** - Packet manipulation library (can do port scanning)
- ✅ **`masscan`** - Actually has a Python wrapper! `python-masscan`

**Recommendation:** Use `python-nmap` for most cases. For extreme speed, use `python-masscan` wrapper.

```bash
pip install python-nmap python-masscan scapy
```

#### 5. ZMap → Python Alternatives
**Binary:** `zmap` (C)  
**Python Alternatives:**
- ✅ **`python-nmap`** - Same as above
- ✅ **`scapy`** - Can do single-packet scans

**Recommendation:** Use `python-nmap` or `scapy`.

#### 6. TheHarvester → Already Python!
**Status:** ✅ **Already a Python package!**  
**Installation:**
```bash
pip install theHarvester
# Or from source
git clone https://github.com/laramies/theHarvester
cd theHarvester
pip install -r requirements.txt
```

**No binary needed!** This is already pure Python.

#### 7. DNSDumpster → Python Alternatives
**Binary:** None (web service)  
**Python Alternatives:**
- ✅ **`dnspython`** - DNS queries
- ✅ **`requests` + `beautifulsoup4`** - Scrape DNSDumpster website
- ✅ **`dnsdumpster`** - Python wrapper for DNSDumpster API (if exists)

**Recommendation:** Use `dnspython` for DNS queries or scrape DNSDumpster with `requests`.

---

### Identity & SOCMINT

#### 8. Sherlock → Already Python!
**Status:** ✅ **Already a Python package!**  
**Installation:**
```bash
pip install sherlock-project
```

**No binary needed!**

#### 9. Maigret → Already Python!
**Status:** ✅ **Already a Python package!**  
**Installation:**
```bash
pip install maigret
```

**No binary needed!**

#### 10. GHunt → Already Python!
**Status:** ✅ **Already a Python package!**  
**Installation:**
```bash
pip install ghunt
```

**No binary needed!**

#### 11. Holehe → Already Python!
**Status:** ✅ **Already a Python package!**  
**Installation:**
```bash
pip install holehe
```

**No binary needed!**

---

### Content & Dark Web

#### 12. Scrapy → Already Python!
**Status:** ✅ **Already a Python package!**  
**Installation:**
```bash
pip install scrapy
```

**No binary needed!**

#### 13. Waybackurls → Python Alternatives
**Binary:** `waybackurls` (Go)  
**Python Alternatives:**
- ✅ **`waybackpy`** - Python wrapper for Wayback Machine API
- ✅ **`internetarchive`** - Official Internet Archive Python library
- ✅ **`wayback`** - Another Python wrapper

**Recommendation:** Use `waybackpy` or `internetarchive`.

```bash
pip install waybackpy internetarchive
```

#### 14. OnionSearch → Python Alternatives
**Binary:** `onionsearch` (Python script, but needs Tor)  
**Python Alternatives:**
- ✅ **`requests[socks]` + `pysocks`** - Make requests through Tor proxy
- ✅ **`stem`** - Python library for Tor control
- ✅ **`onionsearch`** - May be available as Python package

**Recommendation:** Use `requests` with Tor proxy or `stem` for Tor control.

```bash
pip install requests[socks] pysocks stem
```

---

### File & Metadata Analysis

#### 15. ExifTool → Python Alternatives
**Binary:** `exiftool` (Perl)  
**Python Alternatives:**
- ✅ **`exifread`** - Pure Python EXIF reader
- ✅ **`piexif`** - Pure Python EXIF manipulation
- ✅ **`Pillow` (PIL)** - Image library with EXIF support (already installed)
- ✅ **`pyexiv2`** - Python binding to Exiv2 (requires binary library)

**Recommendation:** Use `exifread` or `Pillow` for most cases. They're pure Python.

```bash
pip install exifread piexif
# Pillow is already in dependencies
```

#### 16. YARA → Python Package Available!
**Status:** ✅ **Has Python bindings!**  
**Installation:**
```bash
# Requires YARA library installed first
# macOS: brew install yara
# Linux: sudo apt-get install yara libyara-dev
pip install yara-python
```

**Note:** Still requires YARA C library, but has Python bindings.

---

## 📊 Summary: Binary vs Python

| Tool | Binary Required? | Python Alternative | Status |
|------|------------------|-------------------|--------|
| **Amass** | ❌ No | `sublist3r`, `dnsrecon` | ✅ Python available |
| **Nuclei** | ⚠️ Recommended | `python-nmap`, custom | ⚠️ Limited |
| **Subfinder** | ❌ No | `sublist3r`, `dnsrecon` | ✅ Python available |
| **Masscan** | ⚠️ For speed | `python-nmap`, `python-masscan` | ✅ Python available |
| **ZMap** | ⚠️ For speed | `python-nmap`, `scapy` | ✅ Python available |
| **TheHarvester** | ✅ Already Python | N/A | ✅ Pure Python |
| **DNSDumpster** | ❌ No | `dnspython`, `requests` | ✅ Python available |
| **Sherlock** | ✅ Already Python | N/A | ✅ Pure Python |
| **Maigret** | ✅ Already Python | N/A | ✅ Pure Python |
| **GHunt** | ✅ Already Python | N/A | ✅ Pure Python |
| **Holehe** | ✅ Already Python | N/A | ✅ Pure Python |
| **Scrapy** | ✅ Already Python | N/A | ✅ Pure Python |
| **Waybackurls** | ❌ No | `waybackpy`, `internetarchive` | ✅ Python available |
| **OnionSearch** | ⚠️ Needs Tor | `requests[socks]`, `stem` | ✅ Python available |
| **ExifTool** | ❌ No | `exifread`, `piexif`, `Pillow` | ✅ Python available |
| **YARA** | ⚠️ Needs library | `yara-python` (bindings) | ⚠️ Requires C library |

---

## 🎯 Recommended Approach

### Option 1: Pure Python (No Binaries)
Use Python alternatives for everything:
- ✅ **Subdomain Enumeration:** `sublist3r` or `dnsrecon`
- ✅ **Port Scanning:** `python-nmap`
- ✅ **Vulnerability Scanning:** `python-nmap` + custom scripts
- ✅ **Wayback Machine:** `waybackpy`
- ✅ **Metadata Extraction:** `exifread` or `Pillow`
- ✅ **Identity Tools:** Already Python (Sherlock, Maigret, GHunt, Holehe)

**Pros:**
- No binary dependencies
- Easier deployment
- Cross-platform compatible
- All pip-installable

**Cons:**
- Slower for high-speed scanning (Masscan, ZMap)
- Less comprehensive than specialized tools (Amass, Nuclei)

### Option 2: Hybrid (Python + Binaries for Performance)
Use Python where possible, binaries for performance-critical tools:
- ✅ **Python:** Identity tools, metadata, wayback, DNS
- ⚠️ **Binaries:** Amass (comprehensive), Nuclei (templates), Masscan (speed)

**Pros:**
- Best of both worlds
- Performance where needed
- Python simplicity elsewhere

**Cons:**
- Requires binary installation
- Platform-specific binaries

---

## 📦 Updated Python-Only Dependencies

If you want to avoid all binaries, use these Python packages:

```bash
pip install \
  sublist3r \
  dnsrecon \
  dnspython \
  python-nmap \
  theHarvester \
  sherlock-project \
  maigret \
  ghunt \
  holehe \
  scrapy \
  waybackpy \
  internetarchive \
  requests[socks] \
  pysocks \
  stem \
  exifread \
  piexif \
  yara-python
```

**Note:** `yara-python` still requires the YARA C library, but it's a Python binding.

---

## 🔧 Implementation Strategy

### For LangChain/CrewAI Tools:

1. **Prefer Python packages** - Easier to integrate, no subprocess calls
2. **Use subprocess only when necessary** - For binaries that have no Python alternative
3. **Provide both options** - Allow users to choose Python or binary versions

### Example: Subdomain Enumeration Tool

```python
# Option 1: Pure Python (sublist3r)
from sublist3r import sublist3r

def enumerate_subdomains(domain: str) -> list:
    subdomains = sublist3r.main(
        domain, 
        threads=40, 
        savefile=None, 
        ports=None, 
        silent=False, 
        verbose=False, 
        enable_bruteforce=False, 
        engines=None
    )
    return subdomains

# Option 2: Binary (amass via subprocess)
import subprocess
import json

def enumerate_subdomains_amass(domain: str) -> list:
    result = subprocess.run(
        ["amass", "enum", "-d", domain, "-json", "-o", "-"],
        capture_output=True,
        text=True
    )
    # Parse JSON output
    ...
```

---

## ✅ Recommendation

**For your OSINT SaaS:** Use **Python packages** for everything except:
- **Nuclei** (if you need template-based scanning)
- **Masscan** (if you need extreme speed)

Everything else has good Python alternatives that are:
- ✅ Easier to deploy
- ✅ Cross-platform
- ✅ No binary dependencies
- ✅ pip-installable

---

**Last Updated:** 2024

