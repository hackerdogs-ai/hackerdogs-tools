"""
AlienVault OTX Tool for LangChain Agents

Obtain information from AlienVault Open Threat Exchange (OTX)
Data Source: https://otx.alienvault.com/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_alienvault_tool.log")


class SfpAlienvaultSecurityAgentState(AgentState):
    """Extended agent state for AlienVault OTX operations."""
    user_id: str = ""


def _get_api_key(runtime: ToolRuntime) -> Optional[str]:
    """Get API key from runtime state or environment variable."""
    api_keys = runtime.state.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("ALIENVAULT_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("ALIENVAULT_API_KEY")
    )
    return key


@tool
def sfp_alienvault(
    runtime: ToolRuntime,
    target: str,
    verify: Optional[bool] = True,
    reputation_age_limit_days: Optional[int] = 30,
    cohost_age_limit_days: Optional[int] = 30,
    threat_score_min: Optional[int] = 2,
    netblocklookup: Optional[bool] = True,
    maxnetblock: Optional[int] = 24,
    maxv6netblock: Optional[int] = 120,
    subnetlookup: Optional[bool] = True,
    maxsubnet: Optional[int] = 24,
    maxv6subnet: Optional[int] = 120,
    max_pages: Optional[int] = 50,
    maxcohost: Optional[int] = 100,
    checkaffiliates: Optional[bool] = True,
    api_key: Optional[str] = None,
    **kwargs: Any
) -> str:
    """
    Obtain information from AlienVault Open Threat Exchange (OTX)
    
    Use Cases: Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (INTERNET_NAME, IP_ADDRESS, IPV6_ADDRESS, AFFILIATE_IPADDR, AFFILIATE_IPV6_ADDRESS, NETBLOCK_OWNER, NETBLOCKV6_OWNER, NETBLOCK_MEMBER, NETBLOCKV6_MEMBER, NETBLOCK_OWNER, NETBLOCK_MEMBER)
        verify: Verify co-hosts are valid by checking if they still resolve to the shared IP.
        reputation_age_limit_days: Ignore any reputation records older than this many days. 0 = unlimited.
        cohost_age_limit_days: Ignore any co-hosts older than this many days. 0 = unlimited.
        threat_score_min: Minimum AlienVault threat score.
        netblocklookup: Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?
        maxnetblock: If looking up owned netblocks, the maximum IPv4 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        maxv6netblock: If looking up owned netblocks, the maximum IPv6 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        subnetlookup: Look up all IPs on subnets which your target is a part of for blacklisting?
        maxsubnet: If looking up subnets, the maximum IPv4 subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        maxv6subnet: If looking up subnets, the maximum IPv6 subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        max_pages: Maximum number of pages of URL results to fetch.
        maxcohost: Stop reporting co-hosted sites after this many are found, as it would likely indicate web hosting.
        checkaffiliates: Apply checks to affiliates?
        api_key: AlienVault OTX API Key.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_alienvault] Starting", target=target, has_api_key=bool(api_key))
        
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
                "note": "API key can be provided via api_key parameter, runtime.state['api_keys'], or API_KEY environment variable"
            })
        
        # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
        # Import implementation function dynamically
        from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
            implement_alienvault
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "api_key": api_key,
            "verify": verify,
            "reputation_age_limit_days": reputation_age_limit_days,
            "cohost_age_limit_days": cohost_age_limit_days,
            "threat_score_min": threat_score_min,
            "netblocklookup": netblocklookup,
            "maxnetblock": maxnetblock,
            "maxv6netblock": maxv6netblock,
            "subnetlookup": subnetlookup,
            "maxsubnet": maxsubnet,
            "maxv6subnet": maxv6subnet,
            "max_pages": max_pages,
            "maxcohost": maxcohost,
            "checkaffiliates": checkaffiliates,
        }
        
        # Execute migrated implementation
        implementation_result = implement_alienvault(**implementation_params)
        
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
            "module": "sfp_alienvault",
            "module_name": "AlienVault OTX",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from AlienVault OTX tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_alienvault] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_alienvault] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"AlienVault OTX search failed: {str(e)}",
            "user_id": error_user_id
        })
