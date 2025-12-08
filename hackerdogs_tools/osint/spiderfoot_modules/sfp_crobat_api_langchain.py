"""
Crobat API Tool for LangChain Agents

Search Crobat API for subdomains.
Data Source: https://sonar.omnisint.io/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_crobat_api_tool.log")


class SfpCrobatapiSecurityAgentState(AgentState):
    """Extended agent state for Crobat API operations."""
    user_id: str = ""




@tool
def sfp_crobat_api(
    runtime: ToolRuntime,
    target: str,
    verify: Optional[bool] = True,
    max_pages: Optional[int] = 10,
    delay: Optional[int] = 1,
    **kwargs: Any
) -> str:
    """
    Search Crobat API for subdomains.
    
    Use Cases: Footprint, Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (DOMAIN_NAME)
        verify: DNS resolve each identified subdomain.
        max_pages: Maximum number of pages of results to fetch.
        delay: Delay between requests, in seconds.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_crobat_api] Starting", target=target)
        
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
            implement_crobat_api
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "verify": verify,
            "max_pages": max_pages,
            "delay": delay,
        }
        
        # Execute migrated implementation
        implementation_result = implement_crobat_api(**implementation_params)
        
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
            "module": "sfp_crobat_api",
            "module_name": "Crobat API",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Crobat API tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_crobat_api] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_crobat_api] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Crobat API search failed: {str(e)}",
            "user_id": error_user_id
        })
