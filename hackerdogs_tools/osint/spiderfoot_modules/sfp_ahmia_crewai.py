"""
Ahmia Tool for CrewAI Agents

Search Tor 'Ahmia' search engine for mentions of the target.
Data Source: https://ahmia.fi/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_ahmia_tool.log")




class SfpAhmiaToolSchema(BaseModel):
    """Input schema for AhmiaTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME, HUMAN_NAME, EMAILADDR)")
    fetchlinks: Optional[bool] = Field(
        default=True,
        description="Fetch the darknet pages (via TOR, if enabled) to verify they mention your target."
    )
    fullnames: Optional[bool] = Field(
        default=True,
        description="Search for human names?"
    )


class SfpAhmiaTool(BaseTool):
    """Tool for Search Tor 'Ahmia' search engine for mentions of the target.."""
    
    name: str = "Ahmia"
    description: str = (
        "Search Tor 'Ahmia' search engine for mentions of the target."
        "\n\nUse Cases: Footprint, Investigate"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpAhmiaToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        fetchlinks: Optional[bool] = True,
        fullnames: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute Ahmia."""
        try:
            safe_log_info(logger, f"[SfpAhmiaTool] Starting", target=target)
            
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
                implement_ahmia
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "fetchlinks": fetchlinks,
                "fullnames": fullnames,
            }
            
            # Execute migrated implementation
            implementation_result = implement_ahmia(**implementation_params)
            
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
                "module": "sfp_ahmia",
                "module_name": "Ahmia",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Ahmia tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAhmiaTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAhmiaTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Ahmia search failed: {str(e)}",
                "user_id": user_id
            })
