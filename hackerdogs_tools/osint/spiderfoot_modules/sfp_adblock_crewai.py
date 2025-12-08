"""
AdBlock Check Tool for CrewAI Agents

Check if linked pages would be blocked by AdBlock Plus.
Data Source: https://adblockplus.org/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_adblock_tool.log")




class SfpAdblockToolSchema(BaseModel):
    """Input schema for AdBlock CheckTool."""
    target: str = Field(..., description="Target to investigate (LINKED_URL_INTERNAL, LINKED_URL_EXTERNAL, PROVIDER_JAVASCRIPT)")
    blocklist: Optional[str] = Field(
        default="https://easylist-downloads.adblockplus.org/easylist.txt",
        description="AdBlockPlus block list."
    )
    cacheperiod: Optional[int] = Field(
        default=24,
        description="Hours to cache list data before re-fetching."
    )


class SfpAdblockTool(BaseTool):
    """Tool for Check if linked pages would be blocked by AdBlock Plus.."""
    
    name: str = "AdBlock Check"
    description: str = (
        "Check if linked pages would be blocked by AdBlock Plus."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpAdblockToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        blocklist: Optional[str] = "https://easylist-downloads.adblockplus.org/easylist.txt",
        cacheperiod: Optional[int] = 24,
        **kwargs: Any
    ) -> str:
        """Execute AdBlock Check."""
        try:
            safe_log_info(logger, f"[SfpAdblockTool] Starting", target=target)
            
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
                implement_adblock
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "blocklist": blocklist,
                "cacheperiod": cacheperiod,
            }
            
            # Execute migrated implementation
            implementation_result = implement_adblock(**implementation_params)
            
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
                "module": "sfp_adblock",
                "module_name": "AdBlock Check",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from AdBlock Check tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAdblockTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAdblockTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"AdBlock Check search failed: {str(e)}",
                "user_id": user_id
            })
