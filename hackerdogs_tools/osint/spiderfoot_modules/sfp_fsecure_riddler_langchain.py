"""
F-Secure Riddler.io Tool for LangChain Agents

Obtain network information from F-Secure Riddler.io API.
Data Source: https://riddler.io/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_fsecure_riddler_tool.log")


class SfpFsecureriddlerSecurityAgentState(AgentState):
    """Extended agent state for F-Secure Riddler.io operations."""
    user_id: str = ""


def _get_api_key(runtime: ToolRuntime) -> Optional[str]:
    """Get API key from runtime state or environment variable."""
    api_keys = runtime.state.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("FSECURE_RIDDLER_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("FSECURE_RIDDLER_API_KEY")
    )
    return key


@tool
def sfp_fsecure_riddler(
    runtime: ToolRuntime,
    target: str,
    verify: Optional[bool] = True,
    username: Optional[str] = "",
    password: Optional[str] = "",
    api_key: Optional[str] = None,
    **kwargs: Any
) -> str:
    """
    Obtain network information from F-Secure Riddler.io API.
    
    Use Cases: Investigate, Footprint, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (DOMAIN_NAME, INTERNET_NAME, INTERNET_NAME_UNRESOLVED, IP_ADDRESS)
        verify: Verify host names resolve
        username: F-Secure Riddler.io username
        password: F-Secure Riddler.io password
        api_key: API key for F-Secure Riddler.io
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_fsecure_riddler] Starting", target=target, has_api_key=bool(api_key))
        
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
        
        # Get credentials from parameters or runtime
        if not username:
            username = runtime.state.get("fsecure_riddler_username", "") or os.getenv("FSECURE_RIDDLER_USERNAME", "")
        if not password:
            password = runtime.state.get("fsecure_riddler_password", "") or os.getenv("FSECURE_RIDDLER_PASSWORD", "")
        
        if not username or not password:
            error_msg = "F-Secure Riddler.io username and password are required"
            safe_log_error(logger, error_msg, target=target, user_id=user_id)
            return json.dumps({
                "status": "error",
                "message": error_msg,
                "user_id": user_id,
                "note": "Credentials can be provided via parameters, runtime.state, or FSECURE_RIDDLER_USERNAME/FSECURE_RIDDLER_PASSWORD environment variables"
            })
        
        # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
        # Import implementation function dynamically
        from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
            implement_fsecure_riddler
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "username": username,
            "password": password,
            "verify": verify,
        }
        
        # Execute migrated implementation
        implementation_result = implement_fsecure_riddler(**implementation_params)
        
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
            "module": "sfp_fsecure_riddler",
            "module_name": "F-Secure Riddler.io",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from F-Secure Riddler.io tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_fsecure_riddler] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_fsecure_riddler] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"F-Secure Riddler.io search failed: {str(e)}",
            "user_id": error_user_id
        })
