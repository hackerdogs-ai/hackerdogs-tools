"""
DNS Brute-forcer Tool for CrewAI Agents

Attempts to identify hostnames through brute-forcing common names and iterations.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dnsbrute_tool.log")


class SfpDnsbruteToolSchema(BaseModel):
    """Input schema for DNS Brute-forcerTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME)")
    skipcommonwildcard: Optional[bool] = Field(
        default=True,
        description="If wildcard DNS is detected, don't bother brute-forcing."
    )
    domainonly: Optional[bool] = Field(
        default=True,
        description="Only attempt to brute-force names on domain names, not hostnames (some hostnames are also sub-domains)."
    )
    commons: Optional[bool] = Field(
        default=True,
        description="Try a list of about 750 common hostnames/sub-domains."
    )
    top10000: Optional[bool] = Field(
        default=False,
        description="Try a further 10,000 common hostnames/sub-domains. Will make the scan much slower."
    )
    numbersuffix: Optional[bool] = Field(
        default=True,
        description="For any host found, try appending 1, 01, 001, -1, -01, -001, 2, 02, etc. (up to 10)"
    )
    numbersuffixlimit: Optional[bool] = Field(
        default=True,
        description="Limit using the number suffixes for hosts that have already been resolved? If disabled this will significantly extend the duration of scans."
    )


class SfpDnsbruteTool(BaseTool):
    """Tool for Attempts to identify hostnames through brute-forcing common names and iterations.."""
    
    name: str = "DNS Brute-forcer"
    description: str = (
        "Attempts to identify hostnames through brute-forcing common names and iterations."
        "\n\nUse Cases: Footprint, Investigate"
        "\nCategories: DNS"
    )
    args_schema: type[BaseModel] = SfpDnsbruteToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        skipcommonwildcard: Optional[bool] = True,
        domainonly: Optional[bool] = True,
        commons: Optional[bool] = True,
        top10000: Optional[bool] = False,
        numbersuffix: Optional[bool] = True,
        numbersuffixlimit: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute DNS Brute-forcer."""
        try:
            safe_log_info(logger, f"[SfpDnsbruteTool] Starting", target=target)
            
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
                implement_dnsbrute
            )
            
            # Execute migrated implementation
            implementation_result = implement_dnsbrute(
                target=target,
                skipcommonwildcard=skipcommonwildcard,
                domainonly=domainonly,
                commons=commons,
                top10000=top10000,
                numbersuffix=numbersuffix,
                numbersuffixlimit=numbersuffixlimit
            )
            
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
                "module": "sfp_dnsbrute",
                "module_name": "DNS Brute-forcer",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from DNS Brute-forcer tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDnsbruteTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDnsbruteTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"DNS Brute-forcer search failed: {str(e)}",
                "user_id": user_id
            })
