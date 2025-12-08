"""
AlienVault OTX Tool for CrewAI Agents

Obtain information from AlienVault Open Threat Exchange (OTX)
Data Source: https://otx.alienvault.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_alienvault_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("ALIENVAULT_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("ALIENVAULT_API_KEY")
    )
    return key


class SfpAlienvaultToolSchema(BaseModel):
    """Input schema for AlienVault OTXTool."""
    target: str = Field(..., description="Target to investigate (INTERNET_NAME, IP_ADDRESS, IPV6_ADDRESS, AFFILIATE_IPADDR, AFFILIATE_IPV6_ADDRESS, NETBLOCK_OWNER, NETBLOCKV6_OWNER, NETBLOCK_MEMBER, NETBLOCKV6_MEMBER, NETBLOCK_OWNER, NETBLOCK_MEMBER)")
    verify: Optional[bool] = Field(
        default=True,
        description="Verify co-hosts are valid by checking if they still resolve to the shared IP."
    )
    reputation_age_limit_days: Optional[int] = Field(
        default=30,
        description="Ignore any reputation records older than this many days. 0 = unlimited."
    )
    cohost_age_limit_days: Optional[int] = Field(
        default=30,
        description="Ignore any co-hosts older than this many days. 0 = unlimited."
    )
    threat_score_min: Optional[int] = Field(
        default=2,
        description="Minimum AlienVault threat score."
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
    max_pages: Optional[int] = Field(
        default=50,
        description="Maximum number of pages of URL results to fetch."
    )
    maxcohost: Optional[int] = Field(
        default=100,
        description="Stop reporting co-hosted sites after this many are found, as it would likely indicate web hosting."
    )
    checkaffiliates: Optional[bool] = Field(
        default=True,
        description="Apply checks to affiliates?"
    )
    api_key: Optional[str] = Field(default=None, description="AlienVault OTX API Key.")


class SfpAlienvaultTool(BaseTool):
    """Tool for Obtain information from AlienVault Open Threat Exchange (OTX)."""
    
    name: str = "AlienVault OTX"
    description: str = (
        "Obtain information from AlienVault Open Threat Exchange (OTX)"
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpAlienvaultToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        verify: Optional[bool] = True,
        reputation_age_limit_days: Optional[int] = 30,
        cohost_age_limit_days: Optional[int] = 30,
        threat_score_min: Optional[int] = 2,
        netblocklookup: Optional[bool] = True,
        maxnetblock: Optional[int] = 24,
        maxv6netblock: Optional[int] = 120,
        subnetlookup: Optional[bool] = True,
        maxsubnet: Optional[int] = 24,
        maxv6subnet: Optional[int] = 120,
        max_pages: Optional[int] = 50,
        maxcohost: Optional[int] = 100,
        checkaffiliates: Optional[bool] = True,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute AlienVault OTX."""
        try:
            safe_log_info(logger, f"[SfpAlienvaultTool] Starting", target=target, has_api_key=bool(api_key))
            
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
                implement_alienvault
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "api_key": api_key,
                "verify": verify,
                "reputation_age_limit_days": reputation_age_limit_days,
                "cohost_age_limit_days": cohost_age_limit_days,
                "threat_score_min": threat_score_min,
                "netblocklookup": netblocklookup,
                "maxnetblock": maxnetblock,
                "maxv6netblock": maxv6netblock,
                "subnetlookup": subnetlookup,
                "maxsubnet": maxsubnet,
                "maxv6subnet": maxv6subnet,
                "max_pages": max_pages,
                "maxcohost": maxcohost,
                "checkaffiliates": checkaffiliates,
            }
            
            # Execute migrated implementation
            implementation_result = implement_alienvault(**implementation_params)
            
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
                "module": "sfp_alienvault",
                "module_name": "AlienVault OTX",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from AlienVault OTX tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAlienvaultTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAlienvaultTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"AlienVault OTX search failed: {str(e)}",
                "user_id": user_id
            })
