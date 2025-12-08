"""
Whois Tool for LangChain Agents

Perform a WHOIS look-up on domain names and owned netblocks.
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_whois_tool.log")


class SfpWhoisSecurityAgentState(AgentState):
    """Extended agent state for Whois operations."""
    user_id: str = ""


@tool
def sfp_whois(
    runtime: ToolRuntime,
    target: str,
    **kwargs: Any
) -> str:
    """
    Perform a WHOIS look-up on domain names and owned netblocks.
    
    Use Cases: Footprint, Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (DOMAIN_NAME, DOMAIN_NAME_PARENT, NETBLOCK_OWNER, NETBLOCKV6_OWNER, CO_HOSTED_SITE_DOMAIN, AFFILIATE_DOMAIN_NAME, SIMILARDOMAIN)
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_whois] Starting", target=target)
        
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
        # Import implementation function based on module type
        from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
            implement_whois
        )
        
        # Execute migrated implementation
        implementation_result = implement_whois(target=target)
        
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
            "module": "sfp_whois",
            "module_name": "Whois",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Whois tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_whois] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_whois] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Whois search failed: {str(e)}",
            "user_id": error_user_id
        })
