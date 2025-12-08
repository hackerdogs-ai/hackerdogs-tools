"""
DNS Raw Records Tool for CrewAI Agents

Retrieves raw DNS records such as MX, TXT and others.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dnsraw_tool.log")




class SfpDnsrawToolSchema(BaseModel):
    """Input schema for DNS Raw RecordsTool."""
    target: str = Field(..., description="Target to investigate (INTERNET_NAME, DOMAIN_NAME, DOMAIN_NAME_PARENT)")
    verify: Optional[bool] = Field(
        default=True,
        description="Verify identified hostnames resolve."
    )


class SfpDnsrawTool(BaseTool):
    """Tool for Retrieves raw DNS records such as MX, TXT and others.."""
    
    name: str = "DNS Raw Records"
    description: str = (
        "Retrieves raw DNS records such as MX, TXT and others."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: DNS"
    )
    args_schema: type[BaseModel] = SfpDnsrawToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        verify: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute DNS Raw Records."""
        try:
            safe_log_info(logger, f"[SfpDnsrawTool] Starting", target=target)
            
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
                implement_dnsraw
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "verify": verify,
            }
            
            # Execute migrated implementation
            implementation_result = implement_dnsraw(**implementation_params)
            
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
                "module": "sfp_dnsraw",
                "module_name": "DNS Raw Records",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from DNS Raw Records tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDnsrawTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDnsrawTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"DNS Raw Records search failed: {str(e)}",
                "user_id": user_id
            })
