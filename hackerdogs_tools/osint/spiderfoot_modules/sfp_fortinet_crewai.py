"""
FortiGuard Antispam Tool for CrewAI Agents

Check if an IP address is malicious according to FortiGuard Antispam.
Data Source: https://www.fortiguard.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_fortinet_tool.log")




class SfpFortinetToolSchema(BaseModel):
    """Input schema for FortiGuard AntispamTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, IPV6_ADDRESS, AFFILIATE_IPADDR, AFFILIATE_IPV6_ADDRESS)")
    checkaffiliates: Optional[bool] = Field(
        default=True,
        description="Apply checks to affiliates?"
    )


class SfpFortinetTool(BaseTool):
    """Tool for Check if an IP address is malicious according to FortiGuard Antispam.."""
    
    name: str = "FortiGuard Antispam"
    description: str = (
        "Check if an IP address is malicious according to FortiGuard Antispam."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpFortinetToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        checkaffiliates: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute FortiGuard Antispam."""
        try:
            safe_log_info(logger, f"[SfpFortinetTool] Starting", target=target)
            
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
                implement_fortinet
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "checkaffiliates": checkaffiliates,
            }
            
            # Execute migrated implementation
            implementation_result = implement_fortinet(**implementation_params)
            
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
                "module": "sfp_fortinet",
                "module_name": "FortiGuard Antispam",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from FortiGuard Antispam tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpFortinetTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpFortinetTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"FortiGuard Antispam search failed: {str(e)}",
                "user_id": user_id
            })
