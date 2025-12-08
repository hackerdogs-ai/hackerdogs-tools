"""
Bitcoin Finder Tool for CrewAI Agents

Identify bitcoin addresses in scraped webpages.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_bitcoin_tool.log")




class SfpBitcoinToolSchema(BaseModel):
    """Input schema for Bitcoin FinderTool."""
    target: str = Field(..., description="Target to investigate (TARGET_WEB_CONTENT)")


class SfpBitcoinTool(BaseTool):
    """Tool for Identify bitcoin addresses in scraped webpages.."""
    
    name: str = "Bitcoin Finder"
    description: str = (
        "Identify bitcoin addresses in scraped webpages."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Content Analysis"
    )
    args_schema: type[BaseModel] = SfpBitcoinToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        **kwargs: Any
    ) -> str:
        """Execute Bitcoin Finder."""
        try:
            safe_log_info(logger, f"[SfpBitcoinTool] Starting", target=target)
            
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
                implement_bitcoin
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
            }
            
            # Execute migrated implementation
            implementation_result = implement_bitcoin(**implementation_params)
            
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
                "module": "sfp_bitcoin",
                "module_name": "Bitcoin Finder",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Bitcoin Finder tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpBitcoinTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpBitcoinTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Bitcoin Finder search failed: {str(e)}",
                "user_id": user_id
            })
