"""
Error String Extractor Tool for CrewAI Agents

Identify common error messages in content like SQL errors, etc.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_errors_tool.log")




class SfpErrorsToolSchema(BaseModel):
    """Input schema for Error String ExtractorTool."""
    target: str = Field(..., description="Target to investigate (TARGET_WEB_CONTENT)")


class SfpErrorsTool(BaseTool):
    """Tool for Identify common error messages in content like SQL errors, etc.."""
    
    name: str = "Error String Extractor"
    description: str = (
        "Identify common error messages in content like SQL errors, etc."
        "\n\nUse Cases: Footprint, Passive"
        "\nCategories: Content Analysis"
    )
    args_schema: type[BaseModel] = SfpErrorsToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        **kwargs: Any
    ) -> str:
        """Execute Error String Extractor."""
        try:
            safe_log_info(logger, f"[SfpErrorsTool] Starting", target=target)
            
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
                implement_errors
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
            }
            
            # Execute migrated implementation
            implementation_result = implement_errors(**implementation_params)
            
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
                "module": "sfp_errors",
                "module_name": "Error String Extractor",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Error String Extractor tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpErrorsTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpErrorsTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Error String Extractor search failed: {str(e)}",
                "user_id": user_id
            })
