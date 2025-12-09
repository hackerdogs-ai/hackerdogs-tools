"""
Fraudguard Tool for CrewAI Agents

Obtain threat information from Fraudguard.io
Data Source: https://fraudguard.io/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_fraudguard_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("FRAUDGUARD_API_KEY_ACCOUNT") or
        api_keys.get("fraudguard_api_key_account") or
        api_keys.get("FRAUDGUARD_API_KEY") or
        os.getenv("FRAUDGUARD_API_KEY_ACCOUNT") or
        os.getenv("fraudguard_api_key_account") or
        os.getenv("FRAUDGUARD_API_KEY")
    )
    return key


class SfpFraudguardToolSchema(BaseModel):
    """Input schema for FraudguardTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, IPV6_ADDRESS, AFFILIATE_IPADDR, AFFILIATE_IPV6_ADDRESS, NETBLOCK_MEMBER, NETBLOCKV6_MEMBER, NETBLOCK_OWNER, NETBLOCKV6_OWNER)")
    fraudguard_api_key_account: Optional[str] = Field(
        default="",
        description="Fraudguard.io API username."
    )
    fraudguard_api_key_password: Optional[str] = Field(
        default="",
        description="Fraudguard.io API password."
    )
    age_limit_days: Optional[int] = Field(
        default=90,
        description="Ignore any records older than this many days. 0 = unlimited."
    )
    netblocklookup: Optional[bool] = Field(
        default=True,
        description="Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?"
    )
    maxnetblock: Optional[int] = Field(
        default=24,
        description="If looking up owned netblocks, the maximum IPv4 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    maxv6netblock: Optional[int] = Field(
        default=120,
        description="If looking up owned netblocks, the maximum IPv6 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    subnetlookup: Optional[bool] = Field(
        default=True,
        description="Look up all IPs on subnets which your target is a part of for blacklisting?"
    )
    maxsubnet: Optional[int] = Field(
        default=24,
        description="If looking up subnets, the maximum IPv4 subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    maxv6subnet: Optional[int] = Field(
        default=120,
        description="If looking up subnets, the maximum IPv6 subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    checkaffiliates: Optional[bool] = Field(
        default=True,
        description="Apply checks to affiliates?"
    )
    api_key: Optional[str] = Field(default=None, description="API key for Fraudguard")


class SfpFraudguardTool(BaseTool):
    """Tool for Obtain threat information from Fraudguard.io."""
    
    name: str = "Fraudguard"
    description: str = (
        "Obtain threat information from Fraudguard.io"
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpFraudguardToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        fraudguard_api_key_account: Optional[str] = "",
        fraudguard_api_key_password: Optional[str] = "",
        age_limit_days: Optional[int] = 90,
        netblocklookup: Optional[bool] = True,
        maxnetblock: Optional[int] = 24,
        maxv6netblock: Optional[int] = 120,
        subnetlookup: Optional[bool] = True,
        maxsubnet: Optional[int] = 24,
        maxv6subnet: Optional[int] = 120,
        checkaffiliates: Optional[bool] = True,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute Fraudguard."""
        try:
            safe_log_info(logger, f"[SfpFraudguardTool] Starting", target=target, has_api_key=bool(api_key))
            
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
            
            # Get credentials from parameters or environment
            if not fraudguard_api_key_account:
                fraudguard_api_key_account = kwargs.get("fraudguard_api_key_account", "") or os.getenv("FRAUDGUARD_API_KEY_ACCOUNT", "")
            if not fraudguard_api_key_password:
                fraudguard_api_key_password = kwargs.get("fraudguard_api_key_password", "") or os.getenv("FRAUDGUARD_API_KEY_PASSWORD", "")
            
            if not fraudguard_api_key_account or not fraudguard_api_key_password:
                error_msg = "Fraudguard API username and password are required"
                safe_log_error(logger, error_msg, target=target, user_id=user_id)
                return json.dumps({
                    "status": "error",
                    "message": error_msg,
                    "user_id": user_id,
                    "note": "Credentials can be provided via parameters, kwargs, or FRAUDGUARD_API_KEY_ACCOUNT/FRAUDGUARD_API_KEY_PASSWORD environment variables"
                })
            
            # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
            # Import implementation function dynamically
            from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
                implement_fraudguard
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "fraudguard_api_key_account": fraudguard_api_key_account,
                "fraudguard_api_key_password": fraudguard_api_key_password,
                "age_limit_days": age_limit_days,
            }
            
            # Execute migrated implementation
            implementation_result = implement_fraudguard(**implementation_params)
            
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
                "module": "sfp_fraudguard",
                "module_name": "Fraudguard",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Fraudguard tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpFraudguardTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpFraudguardTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Fraudguard search failed: {str(e)}",
                "user_id": user_id
            })
