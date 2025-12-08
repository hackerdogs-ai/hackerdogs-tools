"""
Abusix Mail Intelligence Tool for CrewAI Agents

Check if a netblock or IP address is in the Abusix Mail Intelligence blacklist.
Data Source: https://abusix.org/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_abusix_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("ABUSIX_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("ABUSIX_API_KEY")
    )
    return key


class SfpAbusixToolSchema(BaseModel):
    """Input schema for Abusix Mail IntelligenceTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, IPV6_ADDRESS, AFFILIATE_IPADDR, AFFILIATE_IPV6_ADDRESS, NETBLOCK_MEMBER, NETBLOCKV6_MEMBER, NETBLOCK_OWNER, NETBLOCKV6_OWNER, INTERNET_NAME, AFFILIATE_INTERNET_NAME, CO_HOSTED_SITE)")
    checkaffiliates: Optional[bool] = Field(
        default=True,
        description="Apply checks to affiliates?"
    )
    checkcohosts: Optional[bool] = Field(
        default=True,
        description="Apply checks to sites found to be co-hosted on the target's IP?"
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
    subnetlookup: Optional[bool] = Field(
        default=True,
        description="Look up all IPs on subnets which your target is a part of for blacklisting?"
    )
    maxsubnet: Optional[int] = Field(
        default=24,
        description="If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    maxv6subnet: Optional[int] = Field(
        default=120,
        description="If looking up subnets, the maximum IPv6 subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    api_key: Optional[str] = Field(default=None, description="Abusix Mail Intelligence API key.")


class SfpAbusixTool(BaseTool):
    """Tool for Check if a netblock or IP address is in the Abusix Mail Intelligence blacklist.."""
    
    name: str = "Abusix Mail Intelligence"
    description: str = (
        "Check if a netblock or IP address is in the Abusix Mail Intelligence blacklist."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpAbusixToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        checkaffiliates: Optional[bool] = True,
        checkcohosts: Optional[bool] = True,
        netblocklookup: Optional[bool] = True,
        maxnetblock: Optional[int] = 24,
        maxv6netblock: Optional[int] = 120,
        subnetlookup: Optional[bool] = True,
        maxsubnet: Optional[int] = 24,
        maxv6subnet: Optional[int] = 120,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute Abusix Mail Intelligence."""
        try:
            safe_log_info(logger, f"[SfpAbusixTool] Starting", target=target, has_api_key=bool(api_key))
            
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
                implement_abusix
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "api_key": api_key,
                "checkaffiliates": checkaffiliates,
                "checkcohosts": checkcohosts,
                "netblocklookup": netblocklookup,
                "maxnetblock": maxnetblock,
                "maxv6netblock": maxv6netblock,
                "subnetlookup": subnetlookup,
                "maxsubnet": maxsubnet,
                "maxv6subnet": maxv6subnet,
            }
            
            # Execute migrated implementation
            implementation_result = implement_abusix(**implementation_params)
            
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
                "module": "sfp_abusix",
                "module_name": "Abusix Mail Intelligence",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Abusix Mail Intelligence tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAbusixTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAbusixTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Abusix Mail Intelligence search failed: {str(e)}",
                "user_id": user_id
            })
