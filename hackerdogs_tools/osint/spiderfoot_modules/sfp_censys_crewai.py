"""
Censys Tool for CrewAI Agents

Obtain host information from Censys.io.
Data Source: https://censys.io/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_censys_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("CENSYS_API_KEY_UID") or
        api_keys.get("censys_api_key_uid") or
        api_keys.get("CENSYS_API_KEY") or
        os.getenv("CENSYS_API_KEY_UID") or
        os.getenv("censys_api_key_uid") or
        os.getenv("CENSYS_API_KEY")
    )
    return key


class SfpCensysToolSchema(BaseModel):
    """Input schema for CensysTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, IPV6_ADDRESS, NETBLOCK_OWNER, NETBLOCKV6_OWNER)")
    censys_api_key_uid: Optional[str] = Field(
        default="",
        description="Censys.io API UID."
    )
    censys_api_key_secret: Optional[str] = Field(
        default="",
        description="Censys.io API Secret."
    )
    delay: Optional[int] = Field(
        default=3,
        description="Delay between requests, in seconds."
    )
    netblocklookup: Optional[bool] = Field(
        default=True,
        description="Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?"
    )
    maxnetblock: Optional[int] = Field(
        default=24,
        description="If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    maxv6netblock: Optional[int] = Field(
        default=120,
        description="If looking up owned netblocks, the maximum IPv6 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    age_limit_days: Optional[int] = Field(
        default=90,
        description="Ignore any records older than this many days. 0 = unlimited."
    )
    api_key: Optional[str] = Field(default=None, description="API key for Censys")


class SfpCensysTool(BaseTool):
    """Tool for Obtain host information from Censys.io.."""
    
    name: str = "Censys"
    description: str = (
        "Obtain host information from Censys.io."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpCensysToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        censys_api_key_uid: Optional[str] = "",
        censys_api_key_secret: Optional[str] = "",
        delay: Optional[int] = 3,
        netblocklookup: Optional[bool] = True,
        maxnetblock: Optional[int] = 24,
        maxv6netblock: Optional[int] = 120,
        age_limit_days: Optional[int] = 90,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute Censys."""
        try:
            safe_log_info(logger, f"[SfpCensysTool] Starting", target=target, has_api_key=bool(api_key))
            
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
                    "note": "API key can be provided via api_key parameter, kwargs['api_keys'], or CENSYS_API_KEY_UID environment variable"
                })
            
            # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
            # Import implementation function dynamically
            from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
                implement_censys
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "api_key": api_key,
                "censys_api_key_uid": censys_api_key_uid,
                "censys_api_key_secret": censys_api_key_secret,
                "delay": delay,
                "netblocklookup": netblocklookup,
                "maxnetblock": maxnetblock,
                "maxv6netblock": maxv6netblock,
                "age_limit_days": age_limit_days,
            }
            
            # Execute migrated implementation
            implementation_result = implement_censys(**implementation_params)
            
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
                "module": "sfp_censys",
                "module_name": "Censys",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Censys tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpCensysTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpCensysTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Censys search failed: {str(e)}",
                "user_id": user_id
            })
