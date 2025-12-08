"""
ThreatMiner Tool for CrewAI Agents

Obtain information from ThreatMiner's database for passive DNS and threat intelligence.
Data Source: https://www.threatminer.org/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_threatminer_tool.log")




class SfpThreatminerToolSchema(BaseModel):
    """Input schema for ThreatMinerTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, DOMAIN_NAME, NETBLOCK_OWNER, NETBLOCK_MEMBER)")
    verify: Optional[bool] = Field(
        default=True,
        description="Verify that any hostnames found on the target domain still resolve?"
    )
    netblocklookup: Optional[bool] = Field(
        default=False,
        description="Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?"
    )
    maxnetblock: Optional[int] = Field(
        default=24,
        description="If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    subnetlookup: Optional[bool] = Field(
        default=False,
        description="Look up all IPs on subnets which your target is a part of?"
    )
    maxsubnet: Optional[int] = Field(
        default=24,
        description="If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    maxcohost: Optional[int] = Field(
        default=100,
        description="Stop reporting co-hosted sites after this many are found, as it would likely indicate web hosting."
    )
    age_limit_days: Optional[int] = Field(
        default=90,
        description="Ignore records older than this many days. 0 = Unlimited."
    )


class SfpThreatminerTool(BaseTool):
    """Tool for Obtain information from ThreatMiner's database for passive DNS and threat intelligence.."""
    
    name: str = "ThreatMiner"
    description: str = (
        "Obtain information from ThreatMiner's database for passive DNS and threat intelligence."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpThreatminerToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        verify: Optional[bool] = True,
        netblocklookup: Optional[bool] = False,
        maxnetblock: Optional[int] = 24,
        subnetlookup: Optional[bool] = False,
        maxsubnet: Optional[int] = 24,
        maxcohost: Optional[int] = 100,
        age_limit_days: Optional[int] = 90,
        **kwargs: Any
    ) -> str:
        """Execute ThreatMiner."""
        try:
            safe_log_info(logger, f"[SfpThreatminerTool] Starting", target=target)
            
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
                implement_threatminer
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "verify": verify,
                "netblocklookup": netblocklookup,
                "maxnetblock": maxnetblock,
                "subnetlookup": subnetlookup,
                "maxsubnet": maxsubnet,
                "maxcohost": maxcohost,
                "age_limit_days": age_limit_days,
            }
            
            # Execute migrated implementation
            implementation_result = implement_threatminer(**implementation_params)
            
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
                "module": "sfp_threatminer",
                "module_name": "ThreatMiner",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from ThreatMiner tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpThreatminerTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpThreatminerTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"ThreatMiner search failed: {str(e)}",
                "user_id": user_id
            })
