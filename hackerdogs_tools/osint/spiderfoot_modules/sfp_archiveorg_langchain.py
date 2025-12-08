"""
Archive.org Tool for LangChain Agents

Identifies historic versions of interesting files/pages from the Wayback Machine.
Data Source: https://archive.org/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_archiveorg_tool.log")


class SfpArchiveorgSecurityAgentState(AgentState):
    """Extended agent state for Archive.org operations."""
    user_id: str = ""




@tool
def sfp_archiveorg(
    runtime: ToolRuntime,
    target: str,
    farback: Optional[str] = "30,60,90",
    intfiles: Optional[bool] = True,
    passwordpages: Optional[bool] = True,
    formpages: Optional[bool] = False,
    flashpages: Optional[bool] = False,
    javapages: Optional[bool] = False,
    staticpages: Optional[bool] = False,
    uploadpages: Optional[bool] = False,
    webframeworkpages: Optional[bool] = False,
    javascriptpages: Optional[bool] = False,
    **kwargs: Any
) -> str:
    """
    Identifies historic versions of interesting files/pages from the Wayback Machine.
    
    Use Cases: Footprint, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (INTERESTING_FILE, URL_PASSWORD, URL_FORM, URL_FLASH, URL_STATIC, URL_JAVA_APPLET, URL_UPLOAD, URL_JAVASCRIPT, URL_WEB_FRAMEWORK)
        farback: Number of days back to look for older versions of files/pages in the Wayback Machine snapshots. Comma-separate the values, so for example 30,60,90 means to look for snapshots 30 days, 60 days and 90 days back.
        intfiles: Query the Wayback Machine for historic versions of Interesting Files.
        passwordpages: Query the Wayback Machine for historic versions of URLs with passwords.
        formpages: Query the Wayback Machine for historic versions of URLs with forms.
        uploadpages: Query the Wayback Machine for historic versions of URLs accepting uploads.
        flashpages: Query the Wayback Machine for historic versions of URLs containing Flash.
        javapages: Query the Wayback Machine for historic versions of URLs using Java Applets.
        staticpages: Query the Wayback Machine for historic versions of purely static URLs.
        webframeworkpages: Query the Wayback Machine for historic versions of URLs using Javascript frameworks.
        javascriptpages: Query the Wayback Machine for historic versions of URLs using Javascript.
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_archiveorg] Starting", target=target)
        
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
            implement_archiveorg
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "farback": farback,
            "intfiles": intfiles,
            "passwordpages": passwordpages,
            "formpages": formpages,
            "flashpages": flashpages,
            "javapages": javapages,
            "staticpages": staticpages,
            "uploadpages": uploadpages,
            "webframeworkpages": webframeworkpages,
            "javascriptpages": javascriptpages,
        }
        
        # Execute migrated implementation
        implementation_result = implement_archiveorg(**implementation_params)
        
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
            "module": "sfp_archiveorg",
            "module_name": "Archive.org",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Archive.org tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_archiveorg] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_archiveorg] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Archive.org search failed: {str(e)}",
            "user_id": error_user_id
        })
