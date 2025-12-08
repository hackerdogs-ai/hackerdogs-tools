"""
ThreatCrowd Tool for CrewAI Agents

Obtain information from ThreatCrowd about identified IP addresses, domains and e-mail addresses.
Data Source: https://www.threatcrowd.org
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_threatcrowd_tool.log")




class SfpThreatcrowdToolSchema(BaseModel):
    """Input schema for ThreatCrowdTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, AFFILIATE_IPADDR, INTERNET_NAME, CO_HOSTED_SITE, NETBLOCK_OWNER, EMAILADDR, NETBLOCK_MEMBER, AFFILIATE_INTERNET_NAME)")
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


class SfpThreatcrowdTool(BaseTool):
    """Tool for Obtain information from ThreatCrowd about identified IP addresses, domains and e-mail addresses.."""
    
    name: str = "ThreatCrowd"
    description: str = (
        "Obtain information from ThreatCrowd about identified IP addresses, domains and e-mail addresses."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpThreatcrowdToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        checkcohosts: Optional[bool] = True,
        checkaffiliates: Optional[bool] = True,
        netblocklookup: Optional[bool] = True,
        maxnetblock: Optional[int] = 24,
        subnetlookup: Optional[bool] = True,
        maxsubnet: Optional[int] = 24,
        **kwargs: Any
    ) -> str:
        """Execute ThreatCrowd."""
        try:
            safe_log_info(logger, f"[SfpThreatcrowdTool] Starting", target=target)
            
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
                implement_threatcrowd
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "checkcohosts": checkcohosts,
                "checkaffiliates": checkaffiliates,
                "netblocklookup": netblocklookup,
                "maxnetblock": maxnetblock,
                "subnetlookup": subnetlookup,
                "maxsubnet": maxsubnet,
            }
            
            # Execute migrated implementation
            implementation_result = implement_threatcrowd(**implementation_params)
            
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
                "module": "sfp_threatcrowd",
                "module_name": "ThreatCrowd",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from ThreatCrowd tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpThreatcrowdTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpThreatcrowdTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"ThreatCrowd search failed: {str(e)}",
                "user_id": user_id
            })
