"""
CIRCL.LU Tool for LangChain Agents

Obtain information from CIRCL.LU's Passive DNS and Passive SSL databases.
Data Source: https://www.circl.lu/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_circllu_tool.log")


class SfpCirclluSecurityAgentState(AgentState):
    """Extended agent state for CIRCL.LU operations."""
    user_id: str = ""


def _get_api_key(runtime: ToolRuntime) -> Optional[str]:
    """Get API key from runtime state or environment variable."""
    api_keys = runtime.state.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY_LOGIN") or
        api_keys.get("api_key_login") or
        api_keys.get("CIRCLLU_API_KEY") or
        os.getenv("API_KEY_LOGIN") or
        os.getenv("api_key_login") or
        os.getenv("CIRCLLU_API_KEY")
    )
    return key


@tool
def sfp_circllu(
    runtime: ToolRuntime,
    target: str,
    api_key_login: Optional[str] = "",
    api_key_password: Optional[str] = "",
    age_limit_days: Optional[int] = 0,
    verify: Optional[bool] = True,
    cohostsamedomain: Optional[bool] = False,
    maxcohost: Optional[int] = 100,
    api_key: Optional[str] = None,
    **kwargs: Any
) -> str:
    """
    Obtain information from CIRCL.LU's Passive DNS and Passive SSL databases.
    
    Use Cases: Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (INTERNET_NAME, NETBLOCK_OWNER, IP_ADDRESS, DOMAIN_NAME)
        api_key_login: CIRCL.LU login.
        api_key_password: CIRCL.LU password.
        age_limit_days: Ignore any Passive DNS records older than this many days. 0 = unlimited.
        verify: Verify co-hosts are valid by checking if they still resolve to the shared IP.
        cohostsamedomain: Treat co-hosted sites on the same target domain as co-hosting?
        maxcohost: Stop reporting co-hosted sites after this many are found, as it would likely indicate web hosting.
        api_key: API key for CIRCL.LU
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_circllu] Starting", target=target, has_api_key=bool(api_key))
        
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
                "note": "API key can be provided via api_key parameter, runtime.state['api_keys'], or API_KEY_LOGIN environment variable"
            })
        
        # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
        # Import implementation function dynamically
        from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
            implement_circllu
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "api_key": api_key,
            "api_key_login": api_key_login,
            "api_key_password": api_key_password,
            "age_limit_days": age_limit_days,
            "verify": verify,
            "cohostsamedomain": cohostsamedomain,
            "maxcohost": maxcohost,
        }
        
        # Execute migrated implementation
        implementation_result = implement_circllu(**implementation_params)
        
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
            "module": "sfp_circllu",
            "module_name": "CIRCL.LU",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from CIRCL.LU tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_circllu] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_circllu] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"CIRCL.LU search failed: {str(e)}",
            "user_id": error_user_id
        })
