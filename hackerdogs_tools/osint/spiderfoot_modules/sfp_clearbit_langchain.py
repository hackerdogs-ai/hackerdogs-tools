"""
Clearbit Tool for LangChain Agents

Check for names, addresses, domains and more based on lookups of e-mail addresses on clearbit.com.
Data Source: https://clearbit.com/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_clearbit_tool.log")


class SfpClearbitSecurityAgentState(AgentState):
    """Extended agent state for Clearbit operations."""
    user_id: str = ""


def _get_api_key(runtime: ToolRuntime) -> Optional[str]:
    """Get API key from runtime state or environment variable."""
    api_keys = runtime.state.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("CLEARBIT_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("CLEARBIT_API_KEY")
    )
    return key


@tool
def sfp_clearbit(
    runtime: ToolRuntime,
    target: str,
    api_key: Optional[str] = None,
    **kwargs: Any
) -> str:
    """
    Check for names, addresses, domains and more based on lookups of e-mail addresses on clearbit.com.
    
    Use Cases: Footprint, Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (EMAILADDR)
        api_key: Clearbit.com API key.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_clearbit] Starting", target=target, has_api_key=bool(api_key))
        
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
            implement_clearbit
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "api_key": api_key,
        }
        
        # Execute migrated implementation
        implementation_result = implement_clearbit(**implementation_params)
        
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
            "module": "sfp_clearbit",
            "module_name": "Clearbit",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Clearbit tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_clearbit] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_clearbit] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Clearbit search failed: {str(e)}",
            "user_id": error_user_id
        })
