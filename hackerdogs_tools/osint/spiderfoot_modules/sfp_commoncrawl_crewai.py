"""
CommonCrawl Tool for CrewAI Agents

Searches for URLs found through CommonCrawl.org.
Data Source: http://commoncrawl.org/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_commoncrawl_tool.log")




class SfpCommoncrawlToolSchema(BaseModel):
    """Input schema for CommonCrawlTool."""
    target: str = Field(..., description="Target to investigate (INTERNET_NAME)")
    indexes: Optional[int] = Field(
        default=6,
        description="Number of most recent indexes to attempt, because results tend to be occasionally patchy."
    )


class SfpCommoncrawlTool(BaseTool):
    """Tool for Searches for URLs found through CommonCrawl.org.."""
    
    name: str = "CommonCrawl"
    description: str = (
        "Searches for URLs found through CommonCrawl.org."
        "\n\nUse Cases: Footprint, Passive"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpCommoncrawlToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        indexes: Optional[int] = 6,
        **kwargs: Any
    ) -> str:
        """Execute CommonCrawl."""
        try:
            safe_log_info(logger, f"[SfpCommoncrawlTool] Starting", target=target)
            
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
                implement_commoncrawl
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "indexes": indexes,
            }
            
            # Execute migrated implementation
            implementation_result = implement_commoncrawl(**implementation_params)
            
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
                "module": "sfp_commoncrawl",
                "module_name": "CommonCrawl",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from CommonCrawl tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpCommoncrawlTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpCommoncrawlTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"CommonCrawl search failed: {str(e)}",
                "user_id": user_id
            })
