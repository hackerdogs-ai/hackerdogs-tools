"""
VirusTotal Tool for CrewAI Agents

Obtain information from VirusTotal about identified IP addresses.
Data Source: https://www.virustotal.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_virustotal_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("VIRUSTOTAL_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("VIRUSTOTAL_API_KEY")
    )
    return key


class SfpVirustotalToolSchema(BaseModel):
    """Input schema for VirusTotalTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, AFFILIATE_IPADDR, INTERNET_NAME, CO_HOSTED_SITE, NETBLOCK_OWNER, NETBLOCK_MEMBER)")
    verify: Optional[bool] = Field(
        default=True,
        description="Verify that any hostnames found on the target domain still resolve?"
    )
    publicapi: Optional[bool] = Field(
        default=True,
        description="Are you using a public key? If so SpiderFoot will pause for 15 seconds after each query to avoid VirusTotal dropping requests."
    )
    checkcohosts: Optional[bool] = Field(
        default=True,
        description="Check co-hosted sites?"
    )
    checkaffiliates: Optional[bool] = Field(
        default=True,
        description="Check affiliates?"
    )
    netblocklookup: Optional[bool] = Field(
        default=True,
        description="Look up all IPs on netblocks deemed to be owned by your target for possible hosts on the same target subdomain/domain?"
    )
    maxnetblock: Optional[int] = Field(
        default=24,
        description="If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    subnetlookup: Optional[bool] = Field(
        default=True,
        description="Look up all IPs on subnets which your target is a part of?"
    )
    maxsubnet: Optional[int] = Field(
        default=24,
        description="If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    api_key: Optional[str] = Field(default=None, description="VirusTotal API Key.")


class SfpVirustotalTool(BaseTool):
    """Tool for Obtain information from VirusTotal about identified IP addresses.."""
    
    name: str = "VirusTotal"
    description: str = (
        "Obtain information from VirusTotal about identified IP addresses."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpVirustotalToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        verify: Optional[bool] = True,
        publicapi: Optional[bool] = True,
        checkcohosts: Optional[bool] = True,
        checkaffiliates: Optional[bool] = True,
        netblocklookup: Optional[bool] = True,
        maxnetblock: Optional[int] = 24,
        subnetlookup: Optional[bool] = True,
        maxsubnet: Optional[int] = 24,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute VirusTotal."""
        try:
            safe_log_info(logger, f"[SfpVirustotalTool] Starting", target=target, has_api_key=bool(api_key))
            
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
            # Import implementation function based on module type
            from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
                implement_virustotal
            )
            
            # Execute migrated implementation
            implementation_result = implement_virustotal(
                target=target,
                api_key=api_key,
                verify=verify,
                publicapi=publicapi,
                checkcohosts=checkcohosts,
                checkaffiliates=checkaffiliates,
                netblocklookup=netblocklookup,
                maxnetblock=maxnetblock,
                subnetlookup=subnetlookup,
                maxsubnet=maxsubnet
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
                "module": "sfp_virustotal",
                "module_name": "VirusTotal",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from VirusTotal tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpVirustotalTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpVirustotalTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"VirusTotal search failed: {str(e)}",
                "user_id": user_id
            })
