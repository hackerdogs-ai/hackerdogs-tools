"""
DNSDumpster Tool for CrewAI Agents

Passive subdomain enumeration using HackerTarget's DNSDumpster
Data Source: https://dnsdumpster.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dnsdumpster_tool.log")




class SfpDnsdumpsterToolSchema(BaseModel):
    """Input schema for DNSDumpsterTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME, INTERNET_NAME)")


class SfpDnsdumpsterTool(BaseTool):
    """Tool for Passive subdomain enumeration using HackerTarget's DNSDumpster."""
    
    name: str = "DNSDumpster"
    description: str = (
        "Passive subdomain enumeration using HackerTarget's DNSDumpster"
        "\n\nUse Cases: Investigate, Footprint, Passive"
        "\nCategories: Passive DNS"
    )
    args_schema: type[BaseModel] = SfpDnsdumpsterToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        **kwargs: Any
    ) -> str:
        """Execute DNSDumpster."""
        try:
            safe_log_info(logger, f"[SfpDnsdumpsterTool] Starting", target=target)
            
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
                implement_dnsdumpster
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
            }
            
            # Execute migrated implementation
            implementation_result = implement_dnsdumpster(**implementation_params)
            
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
                "module": "sfp_dnsdumpster",
                "module_name": "DNSDumpster",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from DNSDumpster tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDnsdumpsterTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDnsdumpsterTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"DNSDumpster search failed: {str(e)}",
                "user_id": user_id
            })
