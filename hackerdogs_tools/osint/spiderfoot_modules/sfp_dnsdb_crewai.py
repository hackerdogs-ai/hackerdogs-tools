"""
DNSDB Tool for CrewAI Agents

Query FarSight's DNSDB for historical and passive DNS data.
Data Source: https://www.farsightsecurity.com
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dnsdb_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("DNSDB_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("DNSDB_API_KEY")
    )
    return key


class SfpDnsdbToolSchema(BaseModel):
    """Input schema for DNSDBTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, IPV6_ADDRESS, DOMAIN_NAME)")
    age_limit_days: Optional[int] = Field(
        default=0,
        description="Ignore any DNSDB records older than this many days. 0 = unlimited."
    )
    verify: Optional[bool] = Field(
        default=True,
        description="Verify co-hosts are valid by checking if they still resolve to the shared IP."
    )
    cohostsamedomain: Optional[bool] = Field(
        default=False,
        description="Treat co-hosted sites on the same target domain as co-hosting?"
    )
    maxcohost: Optional[int] = Field(
        default=100,
        description="Stop reporting co-hosted sites after this many are found, as it would likely indicate web hosting."
    )
    api_key: Optional[str] = Field(default=None, description="DNSDB API Key.")


class SfpDnsdbTool(BaseTool):
    """Tool for Query FarSight's DNSDB for historical and passive DNS data.."""
    
    name: str = "DNSDB"
    description: str = (
        "Query FarSight's DNSDB for historical and passive DNS data."
        "\n\nUse Cases: Passive, Footprint, Investigate"
        "\nCategories: Passive DNS"
    )
    args_schema: type[BaseModel] = SfpDnsdbToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        age_limit_days: Optional[int] = 0,
        verify: Optional[bool] = True,
        cohostsamedomain: Optional[bool] = False,
        maxcohost: Optional[int] = 100,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute DNSDB."""
        try:
            safe_log_info(logger, f"[SfpDnsdbTool] Starting", target=target, has_api_key=bool(api_key))
            
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
            
            # Get API key
            api_key = api_key or _get_api_key(**kwargs)
            if not api_key:
                error_msg = "API key required but not provided"
                safe_log_error(logger, error_msg, target=target, user_id=user_id)
                return json.dumps({
                    "status": "error",
                    "message": error_msg,
                    "user_id": user_id,
                    "note": "API key can be provided via api_key parameter, kwargs['api_keys'], or API_KEY environment variable"
                })
            
            # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
            # Import implementation function dynamically
            from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
                implement_dnsdb
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "api_key": api_key,
                "age_limit_days": age_limit_days,
                "verify": verify,
                "cohostsamedomain": cohostsamedomain,
                "maxcohost": maxcohost,
            }
            
            # Execute migrated implementation
            implementation_result = implement_dnsdb(**implementation_params)
            
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
                "module": "sfp_dnsdb",
                "module_name": "DNSDB",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from DNSDB tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDnsdbTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDnsdbTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"DNSDB search failed: {str(e)}",
                "user_id": user_id
            })
