"""
ThreatCrowd Tool for LangChain Agents

Obtain information from ThreatCrowd about identified IP addresses, domains and e-mail addresses.
Data Source: https://www.threatcrowd.org
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_threatcrowd_tool.log")


class SfpThreatcrowdSecurityAgentState(AgentState):
    """Extended agent state for ThreatCrowd operations."""
    user_id: str = ""




@tool
def sfp_threatcrowd(
    runtime: ToolRuntime,
    target: str,
    checkcohosts: Optional[bool] = True,
    checkaffiliates: Optional[bool] = True,
    netblocklookup: Optional[bool] = True,
    maxnetblock: Optional[int] = 24,
    subnetlookup: Optional[bool] = True,
    maxsubnet: Optional[int] = 24,
    **kwargs: Any
) -> str:
    """
    Obtain information from ThreatCrowd about identified IP addresses, domains and e-mail addresses.
    
    Use Cases: Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (IP_ADDRESS, AFFILIATE_IPADDR, INTERNET_NAME, CO_HOSTED_SITE, NETBLOCK_OWNER, EMAILADDR, NETBLOCK_MEMBER, AFFILIATE_INTERNET_NAME)
        checkcohosts: Check co-hosted sites?
        checkaffiliates: Check affiliates?
        netblocklookup: Look up all IPs on netblocks deemed to be owned by your target for possible hosts on the same target subdomain/domain?
        maxnetblock: If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        subnetlookup: Look up all IPs on subnets which your target is a part of?
        maxsubnet: If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_threatcrowd] Starting", target=target)
        
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
        
        
        # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
        # Import implementation function dynamically
        from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
            implement_threatcrowd
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "checkcohosts": checkcohosts,
            "checkaffiliates": checkaffiliates,
            "netblocklookup": netblocklookup,
            "maxnetblock": maxnetblock,
            "subnetlookup": subnetlookup,
            "maxsubnet": maxsubnet,
        }
        
        # Execute migrated implementation
        implementation_result = implement_threatcrowd(**implementation_params)
        
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
            "module": "sfp_threatcrowd",
            "module_name": "ThreatCrowd",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from ThreatCrowd tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_threatcrowd] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_threatcrowd] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"ThreatCrowd search failed: {str(e)}",
            "user_id": error_user_id
        })
