"""
Flickr Tool for LangChain Agents

Search Flickr for domains, URLs and emails related to the specified domain.
Data Source: https://www.flickr.com/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_flickr_tool.log")


class SfpFlickrSecurityAgentState(AgentState):
    """Extended agent state for Flickr operations."""
    user_id: str = ""




@tool
def sfp_flickr(
    runtime: ToolRuntime,
    target: str,
    pause: Optional[int] = 1,
    per_page: Optional[int] = 100,
    maxpages: Optional[int] = 20,
    dns_resolve: Optional[bool] = True,
    **kwargs: Any
) -> str:
    """
    Search Flickr for domains, URLs and emails related to the specified domain.
    
    Use Cases: Footprint, Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (DOMAIN_NAME)
        pause: Number of seconds to pause between fetches.
        per_page: Maximum number of results per page.
        maxpages: Maximum number of pages of results to fetch.
        dns_resolve: DNS resolve each identified domain.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_flickr] Starting", target=target)
        
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
            implement_flickr
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "pause": pause,
            "per_page": per_page,
            "maxpages": maxpages,
            "dns_resolve": dns_resolve,
        }
        
        # Execute migrated implementation
        implementation_result = implement_flickr(**implementation_params)
        
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
            "module": "sfp_flickr",
            "module_name": "Flickr",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Flickr tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_flickr] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_flickr] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Flickr search failed: {str(e)}",
            "user_id": error_user_id
        })
