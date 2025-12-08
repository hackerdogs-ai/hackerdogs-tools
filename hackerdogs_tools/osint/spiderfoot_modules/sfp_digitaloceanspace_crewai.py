"""
Digital Ocean Space Finder Tool for CrewAI Agents

Search for potential Digital Ocean Spaces associated with the target and attempt to list their contents.
Data Source: https://www.digitalocean.com/products/spaces/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_digitaloceanspace_tool.log")




class SfpDigitaloceanspaceToolSchema(BaseModel):
    """Input schema for Digital Ocean Space FinderTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME, LINKED_URL_EXTERNAL)")
    endpoints: Optional[str] = Field(
        default="nyc3.digitaloceanspaces.com,sgp1.digitaloceanspaces.com,ams3.digitaloceanspaces.com",
        description="Different Digital Ocean locations to check where spaces may exist."
    )
    suffixes: Optional[str] = Field(
        default="test,dev,web,beta,bucket,space,files,content,data,prod,staging,production,stage,app,media,development,-test,-dev,-web,-beta,-bucket,-space,-files,-content,-data,-prod,-staging,-production,-stage,-app,-media,-development",
        description="List of suffixes to append to domains tried as space names"
    )
    maxthreads: Optional[int] = Field(
        default=20,
        description="Maximum threads"
    )


class SfpDigitaloceanspaceTool(BaseTool):
    """Tool for Search for potential Digital Ocean Spaces associated with the target and attempt to list their contents.."""
    
    name: str = "Digital Ocean Space Finder"
    description: str = (
        "Search for potential Digital Ocean Spaces associated with the target and attempt to list their contents."
        "\n\nUse Cases: Footprint, Passive"
        "\nCategories: Crawling and Scanning"
    )
    args_schema: type[BaseModel] = SfpDigitaloceanspaceToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        endpoints: Optional[str] = "nyc3.digitaloceanspaces.com,sgp1.digitaloceanspaces.com,ams3.digitaloceanspaces.com",
        suffixes: Optional[str] = "test,dev,web,beta,bucket,space,files,content,data,prod,staging,production,stage,app,media,development,-test,-dev,-web,-beta,-bucket,-space,-files,-content,-data,-prod,-staging,-production,-stage,-app,-media,-development",
        maxthreads: Optional[int] = 20,
        **kwargs: Any
    ) -> str:
        """Execute Digital Ocean Space Finder."""
        try:
            safe_log_info(logger, f"[SfpDigitaloceanspaceTool] Starting", target=target)
            
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
                implement_digitaloceanspace
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "endpoints": endpoints,
                "suffixes": suffixes,
                "maxthreads": maxthreads,
            }
            
            # Execute migrated implementation
            implementation_result = implement_digitaloceanspace(**implementation_params)
            
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
                "module": "sfp_digitaloceanspace",
                "module_name": "Digital Ocean Space Finder",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Digital Ocean Space Finder tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDigitaloceanspaceTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDigitaloceanspaceTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Digital Ocean Space Finder search failed: {str(e)}",
                "user_id": user_id
            })
