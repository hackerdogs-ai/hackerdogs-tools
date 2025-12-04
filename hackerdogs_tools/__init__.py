"""
HackerDogs Tools - LangChain, CrewAI, and MCP Server Tools for hackerdogs.ai Platform

This package provides comprehensive tools for:
- Threat Intelligence (TI) tools (OTX, VirusTotal, MISP, OpenCTI)
- OSINT tools (Infrastructure, Identity, Content, Threat Intel, Metadata, Frameworks)
- VictoriaLogs querying and analysis
- Productivity tools (Excel, PowerPoint, OCR, Visualization)
- Browser automation and web scraping
- File operations and format conversion

All tools are designed to work with LangChain agents and follow best practices
for secure API key management, error handling, and logging.
"""

__version__ = "0.1.0"

# Import main modules
from . import ti
# Import prodx with warnings suppressed
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=DeprecationWarning, module='pptx')
    warnings.filterwarnings('ignore', category=DeprecationWarning, message='.*PyPDF2.*')
    warnings.filterwarnings('ignore', category=UserWarning, module='pptx')
    from . import prodx
from . import osint
from . import victorialogs_tools
from . import browserless_tool
from . import tool_logging

__all__ = [
    "ti",
    "prodx",
    "osint",
    "victorialogs_tools",
    "browserless_tool",
    "tool_logging",
    "__version__",
]

