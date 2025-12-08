"""
BinaryEdge Tool for LangChain Agents

Obtain information from BinaryEdge.io Internet scanning systems, including breaches, vulnerabilities, torrents and passive DNS.
Data Source: https://www.binaryedge.io/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_binaryedge_tool.log")


class SfpBinaryedgeSecurityAgentState(AgentState):
    """Extended agent state for BinaryEdge operations."""
    user_id: str = ""


def _get_api_key(runtime: ToolRuntime) -> Optional[str]:
    """Get API key from runtime state or environment variable."""
    api_keys = runtime.state.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("BINARYEDGE_API_KEY") or
        api_keys.get("binaryedge_api_key") or
        api_keys.get("BINARYEDGE_API_KEY") or
        os.getenv("BINARYEDGE_API_KEY") or
        os.getenv("binaryedge_api_key") or
        os.getenv("BINARYEDGE_API_KEY")
    )
    return key


@tool
def sfp_binaryedge(
    runtime: ToolRuntime,
    target: str,
    binaryedge_api_key: Optional[str] = "",
    torrent_age_limit_days: Optional[int] = 30,
    cve_age_limit_days: Optional[int] = 30,
    port_age_limit_days: Optional[int] = 90,
    maxpages: Optional[int] = 10,
    verify: Optional[bool] = True,
    netblocklookup: Optional[bool] = False,
    maxnetblock: Optional[int] = 24,
    subnetlookup: Optional[bool] = False,
    maxsubnet: Optional[int] = 24,
    maxcohost: Optional[int] = 100,
    api_key: Optional[str] = None,
    **kwargs: Any
) -> str:
    """
    Obtain information from BinaryEdge.io Internet scanning systems, including breaches, vulnerabilities, torrents and passive DNS.
    
    Use Cases: Footprint, Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (IP_ADDRESS, DOMAIN_NAME, EMAILADDR, NETBLOCK_OWNER, NETBLOCK_MEMBER)
        binaryedge_api_key: BinaryEdge.io API Key.
        torrent_age_limit_days: Ignore any torrent records older than this many days. 0 = unlimited.
        cve_age_limit_days: Ignore any vulnerability records older than this many days. 0 = unlimited.
        port_age_limit_days: Ignore any discovered open ports/banners older than this many days. 0 = unlimited.
        verify: Verify that any hostnames found on the target domain still resolve?
        maxpages: Maximum number of pages to iterate through, to avoid exceeding BinaryEdge API usage limits. APIv2 has a maximum of 500 pages (10,000 results).
        netblocklookup: Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?
        maxnetblock: If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        subnetlookup: Look up all IPs on subnets which your target is a part of?
        maxsubnet: If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        maxcohost: Stop reporting co-hosted sites after this many are found, as it would likely indicate web hosting.
        api_key: API key for BinaryEdge
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_binaryedge] Starting", target=target, has_api_key=bool(api_key))
        
        # Get user_id from runtime state
        user_id = runtime.state.get("user_id", "unknown")
        
        # Validate inputs
        if not target or not isinstance(target, str) or len(target.strip()) == 0:
            error_msg = "Invalid target provided"
            safe_log_error(logger, error_msg, target=target, user_id=user_id)
            return json.dumps({
                "status": "error",
                "message": error_msg,
                "user_id": user_id
            })
        
        # Get API key
        api_key = api_key or _get_api_key(runtime)
        if not api_key:
            error_msg = "API key required but not provided"
            safe_log_error(logger, error_msg, target=target, user_id=user_id)
            return json.dumps({
                "status": "error",
                "message": error_msg,
                "user_id": user_id,
                "note": "API key can be provided via api_key parameter, runtime.state['api_keys'], or BINARYEDGE_API_KEY environment variable"
            })
        
        # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
        # Import implementation function dynamically
        from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
            implement_binaryedge
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "api_key": api_key,
            "binaryedge_api_key": binaryedge_api_key,
            "torrent_age_limit_days": torrent_age_limit_days,
            "cve_age_limit_days": cve_age_limit_days,
            "port_age_limit_days": port_age_limit_days,
            "maxpages": maxpages,
            "verify": verify,
            "netblocklookup": netblocklookup,
            "maxnetblock": maxnetblock,
            "subnetlookup": subnetlookup,
            "maxsubnet": maxsubnet,
            "maxcohost": maxcohost,
        }
        
        # Execute migrated implementation
        implementation_result = implement_binaryedge(**implementation_params)
        
        # Use implementation result
        if implementation_result.get("status") == "error":
            error_msg = implementation_result.get("message", "Unknown error")
            safe_log_error(logger, error_msg, target=target, user_id=user_id)
            return json.dumps({
                "status": "error",
                "message": error_msg,
                "user_id": user_id
            })
        
        result_data = implementation_result
        
        # Return verbatim output with consistent structure
        result = {
            "status": "success",
            "module": "sfp_binaryedge",
            "module_name": "BinaryEdge",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from BinaryEdge tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_binaryedge] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_binaryedge] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"BinaryEdge search failed: {str(e)}",
            "user_id": error_user_id
        })
