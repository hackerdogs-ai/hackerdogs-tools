"""
Tool - DNSTwist Tool for CrewAI Agents

Identify bit-squatting, typo and other similar domains to the target using a local DNSTwist installation.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_tool_dnstwist_tool.log")




class SfpTooldnstwistToolSchema(BaseModel):
    """Input schema for Tool - DNSTwistTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME)")
    pythonpath: Optional[str] = Field(
        default="python",
        description="Path to Python interpreter to use for DNSTwist. If just 'python' then it must be in your PATH."
    )
    dnstwistpath: Optional[str] = Field(
        default="",
        description="Path to the where the dnstwist.py file lives. Optional."
    )
    skipwildcards: Optional[bool] = Field(
        default=True,
        description="Skip TLDs and sub-TLDs that have wildcard DNS."
    )


class SfpTooldnstwistTool(BaseTool):
    """Tool for Identify bit-squatting, typo and other similar domains to the target using a local DNSTwist installation.."""
    
    name: str = "Tool - DNSTwist"
    description: str = (
        "Identify bit-squatting, typo and other similar domains to the target using a local DNSTwist installation."
        "\n\nUse Cases: Footprint, Investigate"
        "\nCategories: DNS"
    )
    args_schema: type[BaseModel] = SfpTooldnstwistToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        pythonpath: Optional[str] = "python",
        dnstwistpath: Optional[str] = "",
        skipwildcards: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute Tool - DNSTwist."""
        try:
            safe_log_info(logger, f"[SfpTooldnstwistTool] Starting", target=target)
            
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
                implement_tool_dnstwist
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "pythonpath": pythonpath,
                "dnstwistpath": dnstwistpath,
                "skipwildcards": skipwildcards,
            }
            
            # Execute migrated implementation
            implementation_result = implement_tool_dnstwist(**implementation_params)
            
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
                "module": "sfp_tool_dnstwist",
                "module_name": "Tool - DNSTwist",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Tool - DNSTwist tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpTooldnstwistTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpTooldnstwistTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Tool - DNSTwist search failed: {str(e)}",
                "user_id": user_id
            })
