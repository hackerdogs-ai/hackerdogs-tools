"""
Account Finder Tool for LangChain Agents

Look for possible associated accounts on over 500 social and other websites such as Instagram, Reddit, etc.
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_accounts_tool.log")


class SfpAccountsSecurityAgentState(AgentState):
    """Extended agent state for Account Finder operations."""
    user_id: str = ""




@tool
def sfp_accounts(
    runtime: ToolRuntime,
    target: str,
    ignorenamedict: Optional[bool] = True,
    ignoreworddict: Optional[bool] = True,
    musthavename: Optional[bool] = True,
    userfromemail: Optional[bool] = True,
    permutate: Optional[bool] = False,
    usernamesize: Optional[int] = 4,
    **kwargs: Any
) -> str:
    """
    Look for possible associated accounts on over 500 social and other websites such as Instagram, Reddit, etc.
    
    Use Cases: Footprint, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (EMAILADDR, DOMAIN_NAME, HUMAN_NAME, USERNAME)
        ignorenamedict: Don't bother looking up names that are just stand-alone first names (too many false positives).
        ignoreworddict: Don't bother looking up names that appear in the dictionary.
        musthavename: The username must be mentioned on the social media page to consider it valid (helps avoid false positives).
        userfromemail: Extract usernames from e-mail addresses at all? If disabled this can reduce false positives for common usernames but for highly unique usernames it would result in missed accounts.
        permutate: Look for the existence of account name permutations. Useful to identify fraudulent social media accounts or account squatting.
        usernamesize: The minimum length of a username to query across social media sites. Helps avoid false positives for very common short usernames.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_accounts] Starting", target=target)
        
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
            implement_accounts
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "ignorenamedict": ignorenamedict,
            "ignoreworddict": ignoreworddict,
            "musthavename": musthavename,
            "userfromemail": userfromemail,
            "permutate": permutate,
            "usernamesize": usernamesize,
        }
        
        # Execute migrated implementation
        implementation_result = implement_accounts(**implementation_params)
        
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
            "module": "sfp_accounts",
            "module_name": "Account Finder",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Account Finder tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_accounts] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_accounts] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Account Finder search failed: {str(e)}",
            "user_id": error_user_id
        })
