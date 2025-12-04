"""
Threat Intelligence OSINT Tools

This module provides tools for threat intelligence including:
- URLHaus malicious URL database
- AbuseIPDB IP reputation
- OTX (AlienVault Open Threat Exchange) - CrewAI version
- MISP (Malware Information Sharing Platform) - CrewAI version
"""

from .urlhaus_langchain import urlhaus_check
from .urlhaus_crewai import URLHausTool
from .abuseipdb_langchain import abuseipdb_check
from .abuseipdb_crewai import AbuseIPDBTool
# OTX and MISP LangChain versions are in hackerdogs_tools.ti
from .otx_crewai import OTXTool
from .misp_crewai import MISPTool

__all__ = [
    "urlhaus_check",
    "URLHausTool",
    "abuseipdb_check",
    "AbuseIPDBTool",
    "OTXTool",
    "MISPTool",
]

