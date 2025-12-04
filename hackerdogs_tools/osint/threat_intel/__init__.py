"""
Threat Intelligence OSINT Tools

This module provides tools for threat intelligence including:
- URLHaus malicious URL database
- AbuseIPDB IP reputation
- OTX (AlienVault Open Threat Exchange) - CrewAI version
- MISP (Malware Information Sharing Platform) - CrewAI version
"""

from .urlhaus_langchain import urlhaus_search
from .urlhaus_crewai import URLHausTool
from .abuseipdb_langchain import abuseipdb_search
from .abuseipdb_crewai import AbuseIPDBTool
from .otx_langchain import otx_search
from .otx_crewai import OTXTool
from .misp_langchain import misp_search
from .misp_crewai import MISPTool

__all__ = [
    "urlhaus_search",
    "URLHausTool",
    "abuseipdb_search",
    "AbuseIPDBTool",
    "otx_search",
    "OTXTool",
    "misp_search",
    "MISPTool",
]

