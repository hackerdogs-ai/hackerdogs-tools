"""
Crobat API Tool for CrewAI Agents

Search Crobat API for subdomains.
Data Source: https://sonar.omnisint.io/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_crobat_api_tool.log")




class SfpCrobatapiToolSchema(BaseModel):
    """Input schema for Crobat APITool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME)")
    verify: Optional[bool] = Field(
        default=True,
        description="DNS resolve each identified subdomain."
    )
    max_pages: Optional[int] = Field(
        default=10,
        description="Maximum number of pages of results to fetch."
    )
    delay: Optional[int] = Field(
        default=1,
        description="Delay between requests, in seconds."
    )


class SfpCrobatapiTool(BaseTool):
    """Tool for Search Crobat API for subdomains.."""
    
    name: str = "Crobat API"
    description: str = (
        "Search Crobat API for subdomains."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Passive DNS"
    )
    args_schema: type[BaseModel] = SfpCrobatapiToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        verify: Optional[bool] = True,
        max_pages: Optional[int] = 10,
        delay: Optional[int] = 1,
        **kwargs: Any
    ) -> str:
        """Execute Crobat API."""
        try:
            safe_log_info(logger, f"[SfpCrobatapiTool] Starting", target=target)
            
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
                implement_crobat_api
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "verify": verify,
                "max_pages": max_pages,
                "delay": delay,
            }
            
            # Execute migrated implementation
            implementation_result = implement_crobat_api(**implementation_params)
            
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
                "module": "sfp_crobat_api",
                "module_name": "Crobat API",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Crobat API tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpCrobatapiTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpCrobatapiTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Crobat API search failed: {str(e)}",
                "user_id": user_id
            })
