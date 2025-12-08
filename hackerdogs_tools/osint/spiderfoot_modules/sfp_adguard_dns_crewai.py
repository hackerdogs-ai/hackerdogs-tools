"""
AdGuard DNS Tool for CrewAI Agents

Check if a host would be blocked by AdGuard DNS.
Data Source: https://adguard.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_adguard_dns_tool.log")




class SfpAdguarddnsToolSchema(BaseModel):
    """Input schema for AdGuard DNSTool."""
    target: str = Field(..., description="Target to investigate (INTERNET_NAME, AFFILIATE_INTERNET_NAME, CO_HOSTED_SITE)")


class SfpAdguarddnsTool(BaseTool):
    """Tool for Check if a host would be blocked by AdGuard DNS.."""
    
    name: str = "AdGuard DNS"
    description: str = (
        "Check if a host would be blocked by AdGuard DNS."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpAdguarddnsToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        **kwargs: Any
    ) -> str:
        """Execute AdGuard DNS."""
        try:
            safe_log_info(logger, f"[SfpAdguarddnsTool] Starting", target=target)
            
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
                implement_adguard_dns
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
            }
            
            # Execute migrated implementation
            implementation_result = implement_adguard_dns(**implementation_params)
            
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
                "module": "sfp_adguard_dns",
                "module_name": "AdGuard DNS",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from AdGuard DNS tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAdguarddnsTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAdguarddnsTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"AdGuard DNS search failed: {str(e)}",
                "user_id": user_id
            })
