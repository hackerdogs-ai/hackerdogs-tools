"""
CallerName Tool for CrewAI Agents

Lookup US phone number location and reputation information.
Data Source: http://callername.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_callername_tool.log")




class SfpCallernameToolSchema(BaseModel):
    """Input schema for CallerNameTool."""
    target: str = Field(..., description="Target to investigate (PHONE_NUMBER)")


class SfpCallernameTool(BaseTool):
    """Tool for Lookup US phone number location and reputation information.."""
    
    name: str = "CallerName"
    description: str = (
        "Lookup US phone number location and reputation information."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Real World"
    )
    args_schema: type[BaseModel] = SfpCallernameToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        **kwargs: Any
    ) -> str:
        """Execute CallerName."""
        try:
            safe_log_info(logger, f"[SfpCallernameTool] Starting", target=target)
            
            # Get user_id from kwargs
            user_id = kwargs.get("user_id", "")
            
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
                implement_callername
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
            }
            
            # Execute migrated implementation
            implementation_result = implement_callername(**implementation_params)
            
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
                "module": "sfp_callername",
                "module_name": "CallerName",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from CallerName tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpCallernameTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpCallernameTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"CallerName search failed: {str(e)}",
                "user_id": user_id
            })
