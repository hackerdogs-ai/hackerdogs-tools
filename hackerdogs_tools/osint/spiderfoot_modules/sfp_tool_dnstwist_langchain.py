"""
Tool - DNSTwist Tool for LangChain Agents

Identify bit-squatting, typo and other similar domains to the target using a local DNSTwist installation.
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_tool_dnstwist_tool.log")


class SfpTooldnstwistSecurityAgentState(AgentState):
    """Extended agent state for Tool - DNSTwist operations."""
    user_id: str = ""




@tool
def sfp_tool_dnstwist(
    runtime: ToolRuntime,
    target: str,
    pythonpath: Optional[str] = "python",
    dnstwistpath: Optional[str] = "",
    skipwildcards: Optional[bool] = True,
    **kwargs: Any
) -> str:
    """
    Identify bit-squatting, typo and other similar domains to the target using a local DNSTwist installation.
    
    Use Cases: Footprint, Investigate
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (DOMAIN_NAME)
        pythonpath: Path to Python interpreter to use for DNSTwist. If just 'python' then it must be in your PATH.
        dnstwistpath: Path to the where the dnstwist.py file lives. Optional.
        skipwildcards: Skip TLDs and sub-TLDs that have wildcard DNS.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_tool_dnstwist] Starting", target=target)
        
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
            implement_tool_dnstwist
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "pythonpath": pythonpath,
            "dnstwistpath": dnstwistpath,
            "skipwildcards": skipwildcards,
        }
        
        # Execute migrated implementation
        implementation_result = implement_tool_dnstwist(**implementation_params)
        
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
            "module": "sfp_tool_dnstwist",
            "module_name": "Tool - DNSTwist",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Tool - DNSTwist tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_tool_dnstwist] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_tool_dnstwist] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Tool - DNSTwist search failed: {str(e)}",
            "user_id": error_user_id
        })
