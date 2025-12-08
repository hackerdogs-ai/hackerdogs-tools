"""
AlienVault IP Reputation Tool for LangChain Agents

Check if an IP or netblock is malicious according to the AlienVault IP Reputation database.
Data Source: https://cybersecurity.att.com/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_alienvaultiprep_tool.log")


class SfpAlienvaultiprepSecurityAgentState(AgentState):
    """Extended agent state for AlienVault IP Reputation operations."""
    user_id: str = ""




@tool
def sfp_alienvaultiprep(
    runtime: ToolRuntime,
    target: str,
    checkaffiliates: Optional[bool] = True,
    cacheperiod: Optional[int] = 18,
    checknetblocks: Optional[bool] = True,
    checksubnets: Optional[bool] = True,
    **kwargs: Any
) -> str:
    """
    Check if an IP or netblock is malicious according to the AlienVault IP Reputation database.
    
    Use Cases: Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (IP_ADDRESS, AFFILIATE_IPADDR, NETBLOCK_MEMBER, NETBLOCK_OWNER)
        checkaffiliates: Apply checks to affiliates?
        cacheperiod: Hours to cache list data before re-fetching.
        checknetblocks: Report if any malicious IPs are found within owned netblocks?
        checksubnets: Check if any malicious IPs are found within the same subnet of the target?
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_alienvaultiprep] Starting", target=target)
        
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
            implement_alienvaultiprep
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "checkaffiliates": checkaffiliates,
            "cacheperiod": cacheperiod,
            "checknetblocks": checknetblocks,
            "checksubnets": checksubnets,
        }
        
        # Execute migrated implementation
        implementation_result = implement_alienvaultiprep(**implementation_params)
        
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
            "module": "sfp_alienvaultiprep",
            "module_name": "AlienVault IP Reputation",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from AlienVault IP Reputation tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_alienvaultiprep] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_alienvaultiprep] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"AlienVault IP Reputation search failed: {str(e)}",
            "user_id": error_user_id
        })
