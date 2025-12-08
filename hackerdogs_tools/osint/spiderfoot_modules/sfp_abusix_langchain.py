"""
Abusix Mail Intelligence Tool for LangChain Agents

Check if a netblock or IP address is in the Abusix Mail Intelligence blacklist.
Data Source: https://abusix.org/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_abusix_tool.log")


class SfpAbusixSecurityAgentState(AgentState):
    """Extended agent state for Abusix Mail Intelligence operations."""
    user_id: str = ""


def _get_api_key(runtime: ToolRuntime) -> Optional[str]:
    """Get API key from runtime state or environment variable."""
    api_keys = runtime.state.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("ABUSIX_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("ABUSIX_API_KEY")
    )
    return key


@tool
def sfp_abusix(
    runtime: ToolRuntime,
    target: str,
    checkaffiliates: Optional[bool] = True,
    checkcohosts: Optional[bool] = True,
    netblocklookup: Optional[bool] = True,
    maxnetblock: Optional[int] = 24,
    maxv6netblock: Optional[int] = 120,
    subnetlookup: Optional[bool] = True,
    maxsubnet: Optional[int] = 24,
    maxv6subnet: Optional[int] = 120,
    api_key: Optional[str] = None,
    **kwargs: Any
) -> str:
    """
    Check if a netblock or IP address is in the Abusix Mail Intelligence blacklist.
    
    Use Cases: Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (IP_ADDRESS, IPV6_ADDRESS, AFFILIATE_IPADDR, AFFILIATE_IPV6_ADDRESS, NETBLOCK_MEMBER, NETBLOCKV6_MEMBER, NETBLOCK_OWNER, NETBLOCKV6_OWNER, INTERNET_NAME, AFFILIATE_INTERNET_NAME, CO_HOSTED_SITE)
        checkaffiliates: Apply checks to affiliates?
        checkcohosts: Apply checks to sites found to be co-hosted on the target's IP?
        netblocklookup: Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?
        maxnetblock: If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        maxv6netblock: If looking up owned netblocks, the maximum IPv6 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        subnetlookup: Look up all IPs on subnets which your target is a part of for blacklisting?
        maxsubnet: If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        maxv6subnet: If looking up subnets, the maximum IPv6 subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        api_key: Abusix Mail Intelligence API key.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_abusix] Starting", target=target, has_api_key=bool(api_key))
        
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
            implement_abusix
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "api_key": api_key,
            "checkaffiliates": checkaffiliates,
            "checkcohosts": checkcohosts,
            "netblocklookup": netblocklookup,
            "maxnetblock": maxnetblock,
            "maxv6netblock": maxv6netblock,
            "subnetlookup": subnetlookup,
            "maxsubnet": maxsubnet,
            "maxv6subnet": maxv6subnet,
        }
        
        # Execute migrated implementation
        implementation_result = implement_abusix(**implementation_params)
        
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
            "module": "sfp_abusix",
            "module_name": "Abusix Mail Intelligence",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Abusix Mail Intelligence tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_abusix] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_abusix] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Abusix Mail Intelligence search failed: {str(e)}",
            "user_id": error_user_id
        })
