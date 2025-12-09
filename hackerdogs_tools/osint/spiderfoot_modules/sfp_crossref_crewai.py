"""
Cross-Referencer Tool for CrewAI Agents

Identify whether other domains are associated ('Affiliates') of the target by looking for links back to the target site(s).
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_crossref_tool.log")




class SfpCrossrefToolSchema(BaseModel):
    """Input schema for Cross-ReferencerTool."""
    target: str = Field(..., description="Target to investigate (LINKED_URL_EXTERNAL, SIMILARDOMAIN, CO_HOSTED_SITE, DARKNET_MENTION_URL)")
    checkbase: Optional[bool] = Field(
        default=True,
        description="Check the base URL of the potential affiliate if no direct affiliation found?"
    )


class SfpCrossrefTool(BaseTool):
    """Tool for Identify whether other domains are associated ('Affiliates') of the target by looking for links back to the target site(s).."""
    
    name: str = "Cross-Referencer"
    description: str = (
        "Identify whether other domains are associated ('Affiliates') of the target by looking for links back to the target site(s)."
        "\n\nUse Cases: Footprint"
        "\nCategories: Crawling and Scanning"
    )
    args_schema: type[BaseModel] = SfpCrossrefToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        checkbase: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute Cross-Referencer."""
        try:
            safe_log_info(logger, f"[SfpCrossrefTool] Starting", target=target)
            
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
                implement_crossref
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "checkbase": checkbase,
                "timeout": 30,  # Default timeout
            }
            
            # Execute migrated implementation
            implementation_result = implement_crossref(**implementation_params)
            
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
                "module": "sfp_crossref",
                "module_name": "Cross-Referencer",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Cross-Referencer tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpCrossrefTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpCrossrefTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Cross-Referencer search failed: {str(e)}",
                "user_id": user_id
            })
