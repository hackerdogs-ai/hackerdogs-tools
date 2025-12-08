"""
AlienVault IP Reputation Tool for CrewAI Agents

Check if an IP or netblock is malicious according to the AlienVault IP Reputation database.
Data Source: https://cybersecurity.att.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_alienvaultiprep_tool.log")




class SfpAlienvaultiprepToolSchema(BaseModel):
    """Input schema for AlienVault IP ReputationTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, AFFILIATE_IPADDR, NETBLOCK_MEMBER, NETBLOCK_OWNER)")
    checkaffiliates: Optional[bool] = Field(
        default=True,
        description="Apply checks to affiliates?"
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


class SfpAlienvaultiprepTool(BaseTool):
    """Tool for Check if an IP or netblock is malicious according to the AlienVault IP Reputation database.."""
    
    name: str = "AlienVault IP Reputation"
    description: str = (
        "Check if an IP or netblock is malicious according to the AlienVault IP Reputation database."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpAlienvaultiprepToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        checkaffiliates: Optional[bool] = True,
        cacheperiod: Optional[int] = 18,
        checknetblocks: Optional[bool] = True,
        checksubnets: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute AlienVault IP Reputation."""
        try:
            safe_log_info(logger, f"[SfpAlienvaultiprepTool] Starting", target=target)
            
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
                implement_alienvaultiprep
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "checkaffiliates": checkaffiliates,
                "cacheperiod": cacheperiod,
                "checknetblocks": checknetblocks,
                "checksubnets": checksubnets,
            }
            
            # Execute migrated implementation
            implementation_result = implement_alienvaultiprep(**implementation_params)
            
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
                "module": "sfp_alienvaultiprep",
                "module_name": "AlienVault IP Reputation",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from AlienVault IP Reputation tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAlienvaultiprepTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAlienvaultiprepTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"AlienVault IP Reputation search failed: {str(e)}",
                "user_id": user_id
            })
