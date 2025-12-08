"""
Base64 Decoder Tool for LangChain Agents

Identify Base64-encoded strings in URLs, often revealing interesting hidden information.
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_base64_tool.log")


class SfpBase64SecurityAgentState(AgentState):
    """Extended agent state for Base64 Decoder operations."""
    user_id: str = ""




@tool
def sfp_base64(
    runtime: ToolRuntime,
    target: str,
    minlength: Optional[int] = 10,
    **kwargs: Any
) -> str:
    """
    Identify Base64-encoded strings in URLs, often revealing interesting hidden information.
    
    Use Cases: Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (LINKED_URL_INTERNAL)
        minlength: The minimum length a string that looks like a base64-encoded string needs to be.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_base64] Starting", target=target)
        
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
            implement_base64
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "minlength": minlength,
        }
        
        # Execute migrated implementation
        implementation_result = implement_base64(**implementation_params)
        
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
            "module": "sfp_base64",
            "module_name": "Base64 Decoder",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Base64 Decoder tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_base64] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_base64] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Base64 Decoder search failed: {str(e)}",
            "user_id": error_user_id
        })
