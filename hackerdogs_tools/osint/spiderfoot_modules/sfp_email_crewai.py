"""
E-Mail Address Extractor Tool for CrewAI Agents

Identify e-mail addresses in any obtained data.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_email_tool.log")




class SfpEmailToolSchema(BaseModel):
    """Input schema for E-Mail Address ExtractorTool."""
    target: str = Field(..., description="Target to investigate (TARGET_WEB_CONTENT, BASE64_DATA, AFFILIATE_DOMAIN_WHOIS, CO_HOSTED_SITE_DOMAIN_WHOIS, DOMAIN_WHOIS, NETBLOCK_WHOIS, LEAKSITE_CONTENT, RAW_DNS_RECORDS, RAW_FILE_META_DATA, RAW_RIR_DATA, SIMILARDOMAIN_WHOIS, SSL_CERTIFICATE_RAW, SSL_CERTIFICATE_ISSUED, TCP_PORT_OPEN_BANNER, WEBSERVER_BANNER, WEBSERVER_HTTPHEADERS)")


class SfpEmailTool(BaseTool):
    """Tool for Identify e-mail addresses in any obtained data.."""
    
    name: str = "E-Mail Address Extractor"
    description: str = (
        "Identify e-mail addresses in any obtained data."
        "\n\nUse Cases: Passive, Investigate, Footprint"
        "\nCategories: Content Analysis"
    )
    args_schema: type[BaseModel] = SfpEmailToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        **kwargs: Any
    ) -> str:
        """Execute E-Mail Address Extractor."""
        try:
            safe_log_info(logger, f"[SfpEmailTool] Starting", target=target)
            
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
                implement_email
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
            }
            
            # Execute migrated implementation
            implementation_result = implement_email(**implementation_params)
            
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
                "module": "sfp_email",
                "module_name": "E-Mail Address Extractor",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from E-Mail Address Extractor tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpEmailTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpEmailTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"E-Mail Address Extractor search failed: {str(e)}",
                "user_id": user_id
            })
