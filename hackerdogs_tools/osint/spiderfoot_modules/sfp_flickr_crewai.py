"""
Flickr Tool for CrewAI Agents

Search Flickr for domains, URLs and emails related to the specified domain.
Data Source: https://www.flickr.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_flickr_tool.log")




class SfpFlickrToolSchema(BaseModel):
    """Input schema for FlickrTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME)")
    pause: Optional[int] = Field(
        default=1,
        description="Number of seconds to pause between fetches."
    )
    per_page: Optional[int] = Field(
        default=100,
        description="Maximum number of results per page."
    )
    maxpages: Optional[int] = Field(
        default=20,
        description="Maximum number of pages of results to fetch."
    )
    dns_resolve: Optional[bool] = Field(
        default=True,
        description="DNS resolve each identified domain."
    )


class SfpFlickrTool(BaseTool):
    """Tool for Search Flickr for domains, URLs and emails related to the specified domain.."""
    
    name: str = "Flickr"
    description: str = (
        "Search Flickr for domains, URLs and emails related to the specified domain."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Social Media"
    )
    args_schema: type[BaseModel] = SfpFlickrToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        pause: Optional[int] = 1,
        per_page: Optional[int] = 100,
        maxpages: Optional[int] = 20,
        dns_resolve: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute Flickr."""
        try:
            safe_log_info(logger, f"[SfpFlickrTool] Starting", target=target)
            
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
                implement_flickr
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "pause": pause,
                "per_page": per_page,
                "maxpages": maxpages,
                "dns_resolve": dns_resolve,
            }
            
            # Execute migrated implementation
            implementation_result = implement_flickr(**implementation_params)
            
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
                "module": "sfp_flickr",
                "module_name": "Flickr",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Flickr tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpFlickrTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpFlickrTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Flickr search failed: {str(e)}",
                "user_id": user_id
            })
