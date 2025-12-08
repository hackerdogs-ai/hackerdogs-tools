"""
AdBlock Check Tool for LangChain Agents

Check if linked pages would be blocked by AdBlock Plus.
Data Source: https://adblockplus.org/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_adblock_tool.log")


class SfpAdblockSecurityAgentState(AgentState):
    """Extended agent state for AdBlock Check operations."""
    user_id: str = ""




@tool
def sfp_adblock(
    runtime: ToolRuntime,
    target: str,
    blocklist: Optional[str] = "https://easylist-downloads.adblockplus.org/easylist.txt",
    cacheperiod: Optional[int] = 24,
    **kwargs: Any
) -> str:
    """
    Check if linked pages would be blocked by AdBlock Plus.
    
    Use Cases: Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (LINKED_URL_INTERNAL, LINKED_URL_EXTERNAL, PROVIDER_JAVASCRIPT)
        blocklist: AdBlockPlus block list.
        cacheperiod: Hours to cache list data before re-fetching.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_adblock] Starting", target=target)
        
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
            implement_adblock
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "blocklist": blocklist,
            "cacheperiod": cacheperiod,
        }
        
        # Execute migrated implementation
        implementation_result = implement_adblock(**implementation_params)
        
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
            "module": "sfp_adblock",
            "module_name": "AdBlock Check",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from AdBlock Check tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_adblock] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_adblock] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"AdBlock Check search failed: {str(e)}",
            "user_id": error_user_id
        })
