"""
DroneBL Tool for CrewAI Agents

Query the DroneBL database for open relays, open proxies, vulnerable servers, etc.
Data Source: https://dronebl.org/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dronebl_tool.log")




class SfpDroneblToolSchema(BaseModel):
    """Input schema for DroneBLTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, AFFILIATE_IPADDR, NETBLOCK_OWNER, NETBLOCK_MEMBER)")
    netblocklookup: Optional[bool] = Field(
        default=True,
        description="Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?"
    )
    maxnetblock: Optional[int] = Field(
        default=24,
        description="If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    subnetlookup: Optional[bool] = Field(
        default=True,
        description="Look up all IPs on subnets which your target is a part of for blacklisting?"
    )
    maxsubnet: Optional[int] = Field(
        default=24,
        description="If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )


class SfpDroneblTool(BaseTool):
    """Tool for Query the DroneBL database for open relays, open proxies, vulnerable servers, etc.."""
    
    name: str = "DroneBL"
    description: str = (
        "Query the DroneBL database for open relays, open proxies, vulnerable servers, etc."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpDroneblToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        netblocklookup: Optional[bool] = True,
        maxnetblock: Optional[int] = 24,
        subnetlookup: Optional[bool] = True,
        maxsubnet: Optional[int] = 24,
        **kwargs: Any
    ) -> str:
        """Execute DroneBL."""
        try:
            safe_log_info(logger, f"[SfpDroneblTool] Starting", target=target)
            
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
                implement_dronebl
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "netblocklookup": netblocklookup,
                "maxnetblock": maxnetblock,
                "subnetlookup": subnetlookup,
                "maxsubnet": maxsubnet,
            }
            
            # Execute migrated implementation
            implementation_result = implement_dronebl(**implementation_params)
            
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
                "module": "sfp_dronebl",
                "module_name": "DroneBL",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from DroneBL tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDroneblTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDroneblTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"DroneBL search failed: {str(e)}",
                "user_id": user_id
            })
