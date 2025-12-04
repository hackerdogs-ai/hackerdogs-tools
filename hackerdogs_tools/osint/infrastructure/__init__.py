"""
Infrastructure & Network Reconnaissance OSINT Tools

This module provides tools for infrastructure reconnaissance including:
- Subdomain enumeration (Amass, Subfinder)
- Vulnerability scanning (Nuclei)
- Port scanning (Masscan, ZMap)
- Information gathering (TheHarvester, DNSDumpster)
"""

from .amass_langchain import amass_enum
from .amass_crewai import AmassTool
from .nuclei_langchain import nuclei_scan
from .nuclei_crewai import NucleiTool
from .subfinder_langchain import subfinder_enum
from .subfinder_crewai import SubfinderTool
from .masscan_langchain import masscan_scan
from .masscan_crewai import MasscanTool
from .zmap_langchain import zmap_scan
from .zmap_crewai import ZMapTool
from .theharvester_langchain import theharvester_search
from .theharvester_crewai import TheHarvesterTool
from .dnsdumpster_langchain import dnsdumpster_search
from .dnsdumpster_crewai import DNSDumpsterTool

__all__ = [
    # LangChain tools
    "amass_enum",
    "nuclei_scan",
    "subfinder_enum",
    "masscan_scan",
    "zmap_scan",
    "theharvester_search",
    "dnsdumpster_search",
    # CrewAI tools
    "AmassTool",
    "NucleiTool",
    "SubfinderTool",
    "MasscanTool",
    "ZMapTool",
    "TheHarvesterTool",
    "DNSDumpsterTool",
]

