"""
Whois Tool for CrewAI Agents

Perform a WHOIS look-up on domain names and owned netblocks.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_whois_tool.log")


class SfpWhoisToolSchema(BaseModel):
    """Input schema for WhoisTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME, DOMAIN_NAME_PARENT, NETBLOCK_OWNER, NETBLOCKV6_OWNER, CO_HOSTED_SITE_DOMAIN, AFFILIATE_DOMAIN_NAME, SIMILARDOMAIN)")


class SfpWhoisTool(BaseTool):
    """Tool for Perform a WHOIS look-up on domain names and owned netblocks.."""
    
    name: str = "Whois"
    description: str = (
        "Perform a WHOIS look-up on domain names and owned netblocks."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Public Registries"
    )
    args_schema: type[BaseModel] = SfpWhoisToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        **kwargs: Any
    ) -> str:
        """Execute Whois."""
        try:
            safe_log_info(logger, f"[SfpWhoisTool] Starting", target=target)
            
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
            # Import implementation function based on module type
            from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
                implement_whois
            )
            
            # Execute migrated implementation
            implementation_result = implement_whois(target=target)
            
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
                "module": "sfp_whois",
                "module_name": "Whois",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Whois tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpWhoisTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpWhoisTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Whois search failed: {str(e)}",
                "user_id": user_id
            })
