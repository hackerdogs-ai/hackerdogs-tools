# 🚀 OSINT Tools Quick Start Guide

## TL;DR: Python Packages vs Binaries

**Most tools have Python packages!** You don't need binaries for most functionality.

### ✅ Pure Python Installation (Recommended)

```bash
# Install all Python packages
pip install -e ".[osint]"

# Or install individually
pip install \
  sublist3r dnsrecon dnspython python-nmap \
  theHarvester sherlock-project maigret ghunt holehe \
  scrapy waybackpy internetarchive \
  requests[socks] pysocks stem \
  exifread piexif yara-python
```

**That's it!** No binaries needed for 90% of functionality.

### ⚠️ When You Need Binaries

Only if you need:
- **Nuclei** - Template-based vulnerability scanning (Go templates)
- **Masscan** - Extreme speed port scanning (1000x faster than nmap)
- **Amass** - Most comprehensive subdomain enumeration

For everything else, Python packages work great!

---

## 📦 Installation Options

### Option 1: Pure Python (Recommended for SaaS)
```bash
pip install -e ".[osint]"
```

**Pros:**
- ✅ No binary dependencies
- ✅ Cross-platform
- ✅ Easy deployment
- ✅ Works in containers

**Tools Available:**
- ✅ Subdomain enumeration (sublist3r, dnsrecon)
- ✅ Port scanning (python-nmap)
- ✅ Identity tools (Sherlock, Maigret, GHunt, Holehe)
- ✅ Content scraping (Scrapy, waybackpy)
- ✅ Metadata extraction (exifread, Pillow)

### Option 2: Python + Binaries (Maximum Performance)
```bash
# Python packages
pip install -e ".[osint]"

# Binaries (macOS)
brew install amass nuclei subfinder masscan zmap waybackurls exiftool yara
```

**Pros:**
- ✅ Best performance
- ✅ Most comprehensive results
- ✅ Industry-standard tools

**Cons:**
- ⚠️ Requires binary installation
- ⚠️ Platform-specific

---

## 🎯 Tool Status

| Tool | Python Package? | Binary Needed? | Status |
|------|----------------|----------------|--------|
| **Amass** | ✅ sublist3r | ⚠️ Optional | Python alternative available |
| **Nuclei** | ⚠️ Limited | ⚠️ Recommended | Use python-nmap for basic scanning |
| **Subfinder** | ✅ sublist3r | ❌ No | Python alternative available |
| **Masscan** | ✅ python-nmap | ⚠️ For speed | Python works for most cases |
| **TheHarvester** | ✅ Yes | ❌ No | Pure Python |
| **Sherlock** | ✅ Yes | ❌ No | Pure Python |
| **Maigret** | ✅ Yes | ❌ No | Pure Python |
| **GHunt** | ✅ Yes | ❌ No | Pure Python |
| **Holehe** | ✅ Yes | ❌ No | Pure Python |
| **Scrapy** | ✅ Yes | ❌ No | Pure Python |
| **Waybackurls** | ✅ waybackpy | ❌ No | Python alternative available |
| **ExifTool** | ✅ exifread | ❌ No | Python alternative available |

---

## 💡 Recommendation

**For your OSINT SaaS:** Start with **pure Python packages**. They're:
- Easier to deploy
- No binary dependencies
- Cross-platform
- Sufficient for most use cases

Only add binaries if you specifically need:
- Nuclei's template-based scanning
- Masscan's extreme speed

Everything else works great with Python packages!

---

See `PYTHON_ALTERNATIVES.md` for detailed alternatives and `DEPENDENCIES.md` for full installation guide.

