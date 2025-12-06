"""
AlienVault OTX Tool for LangChain Agents

Query AlienVault Open Threat Exchange for threat intelligence
"""

import json
import os
from typing import Optional
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/otx_tool.log")

# Import OTX SDK
try:
    from OTXv2 import OTXv2Cached, OTXv2  # type: ignore
    OTX_AVAILABLE = True
except ImportError:
    OTX_AVAILABLE = False


class OTXSecurityAgentState(AgentState):
    """Extended agent state for OTX operations."""
    user_id: str = ""


@tool
def otx_search(
    runtime: ToolRuntime,
    indicator: str,
    indicator_type: str = "domain"
) -> str:
    """
    Query AlienVault OTX for threat intelligence.
    
    Check if indicators (IPs, domains, URLs, hashes) are associated with known threats.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        indicator: IP, domain, hash, or URL to check
        indicator_type: Type of indicator (IPv4, domain, hostname, url, hash)
    
    Returns:
        JSON string with threat intelligence results.
    """
    try:
        safe_log_info(logger, f"[otx_search] Starting", indicator=indicator, indicator_type=indicator_type)
        
        # Validate inputs
        if not indicator or not isinstance(indicator, str):
            error_msg = "Invalid indicator provided"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if indicator_type not in ["IPv4", "domain", "hostname", "url", "hash"]:
            error_msg = f"Invalid indicator_type: {indicator_type}. Must be: IPv4, domain, hostname, url, or hash"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not OTX_AVAILABLE:
            error_msg = (
                "OTXv2 SDK not available. Install with: pip install OTXv2\n"
                "Get free API key from https://otx.alienvault.com"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        api_key = os.getenv("OTX_API_KEY", "")
        if not api_key:
            error_msg = (
                "OTX_API_KEY environment variable not set. "
                "Get free API key from https://otx.alienvault.com"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Create OTX client
        try:
            otx = OTXv2Cached(api_key, server="https://otx.alienvault.com")
        except Exception:
            otx = OTXv2(api_key, server="https://otx.alienvault.com")
        
        # Query based on indicator type
        otx_type_map = {
            "IPv4": "IPv4",
            "domain": "domain",
            "hostname": "domain",
            "url": "url",
            "hash": "file"
        }
        otx_type = otx_type_map.get(indicator_type, "domain")
        
        result = otx.get_indicator_details_full(otx_type, indicator)
        
        # Return raw API response verbatim - no parsing, no reformatting
        safe_log_info(logger, f"[otx_search] Complete - returning raw API response verbatim", indicator=indicator)
        return json.dumps(result, indent=2, default=str)
        
    except Exception as e:
        safe_log_error(logger, f"[otx_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"OTX query failed: {str(e)}"})

