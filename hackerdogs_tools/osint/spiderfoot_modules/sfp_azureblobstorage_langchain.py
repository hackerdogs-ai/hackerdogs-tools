"""
Azure Blob Finder Tool for LangChain Agents

Search for potential Azure blobs associated with the target and attempt to list their contents.
Data Source: https://azure.microsoft.com/en-in/services/storage/blobs/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_azureblobstorage_tool.log")


class SfpAzureblobstorageSecurityAgentState(AgentState):
    """Extended agent state for Azure Blob Finder operations."""
    user_id: str = ""




@tool
def sfp_azureblobstorage(
    runtime: ToolRuntime,
    target: str,
    suffixes: Optional[str] = "test,dev,web,beta,bucket,space,files,content,data,prod,staging,production,stage,app,media,development,-test,-dev,-web,-beta,-bucket,-space,-files,-content,-data,-prod,-staging,-production,-stage,-app,-media,-development",
    **kwargs: Any
) -> str:
    """
    Search for potential Azure blobs associated with the target and attempt to list their contents.
    
    Use Cases: Footprint, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (DOMAIN_NAME, LINKED_URL_EXTERNAL)
        suffixes: List of suffixes to append to domains tried as blob storage names
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_azureblobstorage] Starting", target=target)
        
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
            implement_azureblobstorage
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "suffixes": suffixes,
        }
        
        # Execute migrated implementation
        implementation_result = implement_azureblobstorage(**implementation_params)
        
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
            "module": "sfp_azureblobstorage",
            "module_name": "Azure Blob Finder",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Azure Blob Finder tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_azureblobstorage] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_azureblobstorage] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Azure Blob Finder search failed: {str(e)}",
            "user_id": error_user_id
        })
