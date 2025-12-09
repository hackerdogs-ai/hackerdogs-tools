"""
DNS for Family Tool for CrewAI Agents

Check if a host would be blocked by DNS for Family.
Data Source: https://dnsforfamily.com/
"""

import json
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dns_for_family_tool.log")




class SfpDnsforfamilyToolSchema(BaseModel):
    """Input schema for DNS for FamilyTool."""
    target: str = Field(..., description="Target to investigate (INTERNET_NAME, AFFILIATE_INTERNET_NAME, CO_HOSTED_SITE)")


class SfpDnsforfamilyTool(BaseTool):
    """Tool for Check if a host would be blocked by DNS for Family.."""
    
    name: str = "DNS for Family"
    description: str = (
        "Check if a host would be blocked by DNS for Family."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpDnsforfamilyToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        **kwargs: Any
    ) -> str:
        """Execute DNS for Family."""
        try:
            safe_log_info(logger, f"[SfpDnsforfamilyTool] Starting", target=target)
            
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
                implement_dns_for_family
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
            }
            
            # Execute migrated implementation
            implementation_result = implement_dns_for_family(**implementation_params)
            
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
                "module": "sfp_dns_for_family",
                "module_name": "DNS for Family",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from DNS for Family tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDnsforfamilyTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDnsforfamilyTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"DNS for Family search failed: {str(e)}",
                "user_id": user_id
            })
