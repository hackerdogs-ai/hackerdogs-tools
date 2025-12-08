"""
abuse.ch Tool for CrewAI Agents

Check if a host/domain, IP address or netblock is malicious according to Abuse.ch.
Data Source: https://www.abuse.ch
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_abusech_tool.log")




class SfpAbusechToolSchema(BaseModel):
    """Input schema for abuse.chTool."""
    target: str = Field(..., description="Target to investigate (INTERNET_NAME, IP_ADDRESS, NETBLOCK_MEMBER, AFFILIATE_INTERNET_NAME, AFFILIATE_IPADDR, CO_HOSTED_SITE, NETBLOCK_OWNER)")
    abusefeodoip: Optional[bool] = Field(
        default=True,
        description="Enable abuse.ch Feodo IP check?"
    )
    abusesslblip: Optional[bool] = Field(
        default=True,
        description="Enable abuse.ch SSL Backlist IP check?"
    )
    abuseurlhaus: Optional[bool] = Field(
        default=True,
        description="Enable abuse.ch URLhaus check?"
    )
    checkaffiliates: Optional[bool] = Field(
        default=True,
        description="Apply checks to affiliates?"
    )
    checkcohosts: Optional[bool] = Field(
        default=True,
        description="Apply checks to sites found to be co-hosted on the target's IP?"
    )
    cacheperiod: Optional[int] = Field(
        default=18,
        description="Hours to cache list data before re-fetching."
    )
    checknetblocks: Optional[bool] = Field(
        default=True,
        description="Report if any malicious IPs are found within owned netblocks?"
    )
    checksubnets: Optional[bool] = Field(
        default=True,
        description="Check if any malicious IPs are found within the same subnet of the target?"
    )


class SfpAbusechTool(BaseTool):
    """Tool for Check if a host/domain, IP address or netblock is malicious according to Abuse.ch.."""
    
    name: str = "abuse.ch"
    description: str = (
        "Check if a host/domain, IP address or netblock is malicious according to Abuse.ch."
        "\n\nUse Cases: Passive, Investigate"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpAbusechToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        abusefeodoip: Optional[bool] = True,
        abusesslblip: Optional[bool] = True,
        abuseurlhaus: Optional[bool] = True,
        checkaffiliates: Optional[bool] = True,
        checkcohosts: Optional[bool] = True,
        cacheperiod: Optional[int] = 18,
        checknetblocks: Optional[bool] = True,
        checksubnets: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute abuse.ch."""
        try:
            safe_log_info(logger, f"[SfpAbusechTool] Starting", target=target)
            
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
                implement_abusech
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "abusefeodoip": abusefeodoip,
                "abusesslblip": abusesslblip,
                "abuseurlhaus": abuseurlhaus,
                "checkaffiliates": checkaffiliates,
                "checkcohosts": checkcohosts,
                "cacheperiod": cacheperiod,
                "checknetblocks": checknetblocks,
                "checksubnets": checksubnets,
            }
            
            # Execute migrated implementation
            implementation_result = implement_abusech(**implementation_params)
            
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
                "module": "sfp_abusech",
                "module_name": "abuse.ch",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from abuse.ch tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAbusechTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAbusechTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"abuse.ch search failed: {str(e)}",
                "user_id": user_id
            })
