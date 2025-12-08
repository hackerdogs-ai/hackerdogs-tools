"""
ARIN Tool for CrewAI Agents

Queries ARIN registry for contact information.
Data Source: https://www.arin.net/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_arin_tool.log")




class SfpArinToolSchema(BaseModel):
    """Input schema for ARINTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME, HUMAN_NAME)")


class SfpArinTool(BaseTool):
    """Tool for Queries ARIN registry for contact information.."""
    
    name: str = "ARIN"
    description: str = (
        "Queries ARIN registry for contact information."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Public Registries"
    )
    args_schema: type[BaseModel] = SfpArinToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        **kwargs: Any
    ) -> str:
        """Execute ARIN."""
        try:
            safe_log_info(logger, f"[SfpArinTool] Starting", target=target)
            
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
                implement_arin
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
            }
            
            # Execute migrated implementation
            implementation_result = implement_arin(**implementation_params)
            
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
                "module": "sfp_arin",
                "module_name": "ARIN",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from ARIN tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpArinTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpArinTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"ARIN search failed: {str(e)}",
                "user_id": user_id
            })
