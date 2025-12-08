"""
ThreatMiner Tool for LangChain Agents

Obtain information from ThreatMiner's database for passive DNS and threat intelligence.
Data Source: https://www.threatminer.org/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_threatminer_tool.log")


class SfpThreatminerSecurityAgentState(AgentState):
    """Extended agent state for ThreatMiner operations."""
    user_id: str = ""




@tool
def sfp_threatminer(
    runtime: ToolRuntime,
    target: str,
    verify: Optional[bool] = True,
    netblocklookup: Optional[bool] = False,
    maxnetblock: Optional[int] = 24,
    subnetlookup: Optional[bool] = False,
    maxsubnet: Optional[int] = 24,
    maxcohost: Optional[int] = 100,
    age_limit_days: Optional[int] = 90,
    **kwargs: Any
) -> str:
    """
    Obtain information from ThreatMiner's database for passive DNS and threat intelligence.
    
    Use Cases: Footprint, Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (IP_ADDRESS, DOMAIN_NAME, NETBLOCK_OWNER, NETBLOCK_MEMBER)
        verify: Verify that any hostnames found on the target domain still resolve?
        netblocklookup: Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?
        maxnetblock: If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        subnetlookup: Look up all IPs on subnets which your target is a part of?
        maxsubnet: If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        maxcohost: Stop reporting co-hosted sites after this many are found, as it would likely indicate web hosting.
        age_limit_days: Ignore records older than this many days. 0 = Unlimited.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_threatminer] Starting", target=target)
        
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
            implement_threatminer
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "verify": verify,
            "netblocklookup": netblocklookup,
            "maxnetblock": maxnetblock,
            "subnetlookup": subnetlookup,
            "maxsubnet": maxsubnet,
            "maxcohost": maxcohost,
            "age_limit_days": age_limit_days,
        }
        
        # Execute migrated implementation
        implementation_result = implement_threatminer(**implementation_params)
        
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
            "module": "sfp_threatminer",
            "module_name": "ThreatMiner",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from ThreatMiner tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_threatminer] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_threatminer] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"ThreatMiner search failed: {str(e)}",
            "user_id": error_user_id
        })
