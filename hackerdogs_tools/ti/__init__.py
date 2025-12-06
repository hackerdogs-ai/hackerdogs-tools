"""
Threat Intelligence (TI) Tools for LangChain Agents

This module provides LangChain tools for querying various threat intelligence platforms:
- AlienVault OTX (Open Threat Exchange)
- VirusTotal
- MISP (Malware Information Sharing Platform)
- OpenCTI (Open Cyber Threat Intelligence)

All tools use ToolRuntime to securely access API keys from agent state.
"""

from .otx import (
    otx_file_report,
    otx_url_report,
    otx_domain_report,
    otx_ip_report,
    otx_submit_url,
    OTXSecurityAgentState,
)

from .virus_total import (
    virustotal_file_report,
    virustotal_url_report,
    virustotal_domain_report,
    virustotal_ip_report,
    scan_url,
    get_analysis,
    VirusTotalSecurityAgentState,
)

from .misp import (
    misp_file_report,
    misp_url_report,
    misp_domain_report,
    misp_ip_report,
    misp_submit_url,
    MISPSecurityAgentState,
)

from .opencti import (
    opencti_search_indicators,
    opencti_search_malware,
    opencti_search_threat_actors,
    opencti_get_report,
    opencti_list_attack_patterns,
    OpenCTISecurityAgentState,
)

__all__ = [
    # OTX tools
    "otx_file_report",
    "otx_url_report",
    "otx_domain_report",
    "otx_ip_report",
    "otx_submit_url",
    "OTXSecurityAgentState",
    # VirusTotal tools
    "virustotal_file_report",
    "virustotal_url_report",
    "virustotal_domain_report",
    "virustotal_ip_report",
    "scan_url",
    "get_analysis",
    "VirusTotalSecurityAgentState",
    # MISP tools
    "misp_file_report",
    "misp_url_report",
    "misp_domain_report",
    "misp_ip_report",
    "misp_submit_url",
    "MISPSecurityAgentState",
    # OpenCTI tools
    "opencti_search_indicators",
    "opencti_search_malware",
    "opencti_search_threat_actors",
    "opencti_get_report",
    "opencti_list_attack_patterns",
    "OpenCTISecurityAgentState",
]


