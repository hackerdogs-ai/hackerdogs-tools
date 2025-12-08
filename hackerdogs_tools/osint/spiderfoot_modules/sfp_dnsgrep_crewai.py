"""
DNSGrep Tool for CrewAI Agents

Obtain Passive DNS information from Rapid7 Sonar Project using DNSGrep API.
Data Source: https://opendata.rapid7.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dnsgrep_tool.log")




class SfpDnsgrepToolSchema(BaseModel):
    """Input schema for DNSGrepTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME)")
    timeout: Optional[int] = Field(
        default=30,
        description="Query timeout, in seconds."
    )
    dns_resolve: Optional[bool] = Field(
        default=True,
        description="DNS resolve each identified domain."
    )


class SfpDnsgrepTool(BaseTool):
    """Tool for Obtain Passive DNS information from Rapid7 Sonar Project using DNSGrep API.."""
    
    name: str = "DNSGrep"
    description: str = (
        "Obtain Passive DNS information from Rapid7 Sonar Project using DNSGrep API."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Passive DNS"
    )
    args_schema: type[BaseModel] = SfpDnsgrepToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        timeout: Optional[int] = 30,
        dns_resolve: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute DNSGrep."""
        try:
            safe_log_info(logger, f"[SfpDnsgrepTool] Starting", target=target)
            
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
                implement_dnsgrep
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "timeout": timeout,
                "dns_resolve": dns_resolve,
            }
            
            # Execute migrated implementation
            implementation_result = implement_dnsgrep(**implementation_params)
            
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
                "module": "sfp_dnsgrep",
                "module_name": "DNSGrep",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from DNSGrep tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDnsgrepTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDnsgrepTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"DNSGrep search failed: {str(e)}",
                "user_id": user_id
            })
