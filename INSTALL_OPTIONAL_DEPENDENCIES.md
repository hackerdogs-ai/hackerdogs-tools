# Installing Optional Dependencies

## Overview

Some tools in `hackerdogs-tools` have optional dependencies that are not installed by default. This document explains which packages to install for specific functionality.

---

## PowerPoint Tools (`python-pptx`)

### Package Name
**`python-pptx`** (not `pptx`)

### Installation

**Using pip:**
```bash
pip install python-pptx
```

**Using uv:**
```bash
uv pip install python-pptx
```

**Using pip with the project:**
```bash
# From project root
pip install python-pptx
```

### What It Provides
- `CreatePresentationTool` - Create PowerPoint presentations
- `AddSlideTool` - Add slides to existing presentations
- `AddChartToSlideTool` - Add charts to PowerPoint slides

### Verification
After installation, verify it works:
```bash
python3 -c "from pptx import Presentation; print('✅ python-pptx installed')"
```

### Minimum Version
- **Recommended:** `python-pptx>=0.6.21`
- **Current stable:** `0.6.23` (as of 2024)

---

## Streamlit (for Visualization Tools)

### Package Name
**`streamlit`**

### Installation
```bash
pip install streamlit
```

### What It Provides
- Chart display capabilities in `visualization_tools.py`
- File download features in `file_operations_tools.py`

### Note
Streamlit is only needed if you're running tools in a Streamlit environment. For standalone use or LangChain/CrewAI agents, it's not required.

---

## Other Optional Dependencies

### For OSINT Tools
See `hackerdogs_tools/osint/DEPENDENCIES.md` for OSINT-specific optional dependencies.

### For OCR Tools
- `pytesseract` - Tesseract OCR wrapper (requires Tesseract binary)
- `easyocr` - EasyOCR library (80+ languages)
- `pdf2image` - PDF to image conversion (requires poppler)

### For Excel Tools
- `openpyxl` - Excel file manipulation (already in dependencies)
- `pandas` - Data operations (already in dependencies)

---

## Quick Install All Optional Dependencies

If you want to install all optional dependencies at once:

```bash
# PowerPoint support
pip install python-pptx

# Streamlit support (if using Streamlit)
pip install streamlit

# Full OCR support
pip install pytesseract easyocr pdf2image

# Note: Some require system binaries:
# - Tesseract: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)
# - Poppler: brew install poppler (macOS) or apt-get install poppler-utils (Linux)
```

---

## Why These Are Optional

1. **Not everyone needs PowerPoint generation** - Only install if you use those tools
2. **Streamlit is environment-specific** - Only needed in Streamlit apps
3. **Reduces installation size** - Keeps base installation lightweight
4. **System dependencies** - Some tools require system binaries (Tesseract, Poppler)

---

## Current Status Check

To check which optional dependencies are installed:

```bash
python3 << 'EOF'
import sys

optional_deps = {
    'python-pptx': 'PowerPoint tools',
    'streamlit': 'Streamlit visualization',
    'pytesseract': 'Tesseract OCR',
    'easyocr': 'EasyOCR',
    'pdf2image': 'PDF to image conversion'
}

print("Optional Dependencies Status:")
print("=" * 50)
for dep, description in optional_deps.items():
    try:
        __import__(dep.replace('-', '_'))
        print(f"✅ {dep:20} - {description}")
    except ImportError:
        print(f"❌ {dep:20} - {description} (not installed)")
EOF
```

---

**Last Updated:** 2024-12-04

