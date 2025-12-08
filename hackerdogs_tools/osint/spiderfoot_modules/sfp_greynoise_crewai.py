"""
GreyNoise Tool for CrewAI Agents

Obtain IP enrichment data from GreyNoise
Data Source: https://greynoise.io/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_greynoise_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("GREYNOISE_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("GREYNOISE_API_KEY")
    )
    return key


class SfpGreynoiseToolSchema(BaseModel):
    """Input schema for GreyNoiseTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, AFFILIATE_IPADDR, NETBLOCK_MEMBER, NETBLOCK_OWNER)")
    age_limit_days: Optional[int] = Field(
        default=30,
        description="Ignore any records older than this many days. 0 = unlimited."
    )
    netblocklookup: Optional[bool] = Field(
        default=True,
        description="Look up netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?"
    )
    maxnetblock: Optional[int] = Field(
        default=24,
        description="If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    subnetlookup: Optional[bool] = Field(
        default=True,
        description="Look up subnets which your target is a part of for blacklisting?"
    )
    maxsubnet: Optional[int] = Field(
        default=24,
        description="If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    api_key: Optional[str] = Field(default=None, description="GreyNoise API Key.")


class SfpGreynoiseTool(BaseTool):
    """Tool for Obtain IP enrichment data from GreyNoise."""
    
    name: str = "GreyNoise"
    description: str = (
        "Obtain IP enrichment data from GreyNoise"
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpGreynoiseToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        age_limit_days: Optional[int] = 30,
        netblocklookup: Optional[bool] = True,
        maxnetblock: Optional[int] = 24,
        subnetlookup: Optional[bool] = True,
        maxsubnet: Optional[int] = 24,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute GreyNoise."""
        try:
            safe_log_info(logger, f"[SfpGreynoiseTool] Starting", target=target, has_api_key=bool(api_key))
            
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
                implement_greynoise
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "api_key": api_key,
                "age_limit_days": age_limit_days,
                "netblocklookup": netblocklookup,
                "maxnetblock": maxnetblock,
                "subnetlookup": subnetlookup,
                "maxsubnet": maxsubnet,
            }
            
            # Execute migrated implementation
            implementation_result = implement_greynoise(**implementation_params)
            
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
                "module": "sfp_greynoise",
                "module_name": "GreyNoise",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from GreyNoise tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpGreynoiseTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpGreynoiseTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"GreyNoise search failed: {str(e)}",
                "user_id": user_id
            })
