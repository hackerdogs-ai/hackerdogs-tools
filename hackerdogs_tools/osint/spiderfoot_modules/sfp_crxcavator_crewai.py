"""
CRXcavator Tool for CrewAI Agents

Search CRXcavator for Chrome extensions.
Data Source: https://crxcavator.io/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_crxcavator_tool.log")




class SfpCrxcavatorToolSchema(BaseModel):
    """Input schema for CRXcavatorTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME)")
    verify: Optional[bool] = Field(
        default=True,
        description="Verify identified hostnames resolve."
    )


class SfpCrxcavatorTool(BaseTool):
    """Tool for Search CRXcavator for Chrome extensions.."""
    
    name: str = "CRXcavator"
    description: str = (
        "Search CRXcavator for Chrome extensions."
        "\n\nUse Cases: Investigate, Footprint, Passive"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpCrxcavatorToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        verify: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute CRXcavator."""
        try:
            safe_log_info(logger, f"[SfpCrxcavatorTool] Starting", target=target)
            
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
                implement_crxcavator
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "verify": verify,
            }
            
            # Execute migrated implementation
            implementation_result = implement_crxcavator(**implementation_params)
            
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
                "module": "sfp_crxcavator",
                "module_name": "CRXcavator",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from CRXcavator tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpCrxcavatorTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpCrxcavatorTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"CRXcavator search failed: {str(e)}",
                "user_id": user_id
            })
