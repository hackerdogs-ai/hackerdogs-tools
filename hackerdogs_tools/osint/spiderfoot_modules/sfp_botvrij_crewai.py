"""
botvrij.eu Tool for CrewAI Agents

Check if a domain is malicious according to botvrij.eu.
Data Source: https://botvrij.eu/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_botvrij_tool.log")




class SfpBotvrijToolSchema(BaseModel):
    """Input schema for botvrij.euTool."""
    target: str = Field(..., description="Target to investigate (INTERNET_NAME, AFFILIATE_INTERNET_NAME, CO_HOSTED_SITE)")
    checkaffiliates: Optional[bool] = Field(
        default=True,
        description="Apply checks to affiliates?"
    )
    checkcohosts: Optional[bool] = Field(
        default=True,
        description="Apply checks to sites found to be co-hosted on the target's IP?"
    )
    cacheperiod: Optional[int] = Field(
        default=18,
        description="Hours to cache list data before re-fetching."
    )


class SfpBotvrijTool(BaseTool):
    """Tool for Check if a domain is malicious according to botvrij.eu.."""
    
    name: str = "botvrij.eu"
    description: str = (
        "Check if a domain is malicious according to botvrij.eu."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpBotvrijToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        checkaffiliates: Optional[bool] = True,
        checkcohosts: Optional[bool] = True,
        cacheperiod: Optional[int] = 18,
        **kwargs: Any
    ) -> str:
        """Execute botvrij.eu."""
        try:
            safe_log_info(logger, f"[SfpBotvrijTool] Starting", target=target)
            
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
                implement_botvrij
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "checkaffiliates": checkaffiliates,
                "checkcohosts": checkcohosts,
                "cacheperiod": cacheperiod,
            }
            
            # Execute migrated implementation
            implementation_result = implement_botvrij(**implementation_params)
            
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
                "module": "sfp_botvrij",
                "module_name": "botvrij.eu",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from botvrij.eu tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpBotvrijTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpBotvrijTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"botvrij.eu search failed: {str(e)}",
                "user_id": user_id
            })
