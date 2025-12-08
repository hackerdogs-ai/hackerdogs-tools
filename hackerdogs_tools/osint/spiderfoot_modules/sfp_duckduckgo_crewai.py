"""
DuckDuckGo Tool for CrewAI Agents

Query DuckDuckGo's API for descriptive information about your target.
Data Source: https://duckduckgo.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_duckduckgo_tool.log")




class SfpDuckduckgoToolSchema(BaseModel):
    """Input schema for DuckDuckGoTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME, DOMAIN_NAME_PARENT, INTERNET_NAME, AFFILIATE_INTERNET_NAME)")
    affiliatedomains: Optional[bool] = Field(
        default=True,
        description="For affiliates, look up the domain name, not the hostname. This will usually return more meaningful information about the affiliate."
    )


class SfpDuckduckgoTool(BaseTool):
    """Tool for Query DuckDuckGo's API for descriptive information about your target.."""
    
    name: str = "DuckDuckGo"
    description: str = (
        "Query DuckDuckGo's API for descriptive information about your target."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpDuckduckgoToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        affiliatedomains: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute DuckDuckGo."""
        try:
            safe_log_info(logger, f"[SfpDuckduckgoTool] Starting", target=target)
            
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
                implement_duckduckgo
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "affiliatedomains": affiliatedomains,
            }
            
            # Execute migrated implementation
            implementation_result = implement_duckduckgo(**implementation_params)
            
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
                "module": "sfp_duckduckgo",
                "module_name": "DuckDuckGo",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from DuckDuckGo tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDuckduckgoTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDuckduckgoTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"DuckDuckGo search failed: {str(e)}",
                "user_id": user_id
            })
