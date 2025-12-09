"""
Custom Threat Feed Tool for CrewAI Agents

Check if a host/domain, netblock, ASN or IP is malicious according to your custom feed.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_customfeed_tool.log")




class SfpCustomfeedToolSchema(BaseModel):
    """Input schema for Custom Threat FeedTool."""
    target: str = Field(..., description="Target to investigate (INTERNET_NAME, IP_ADDRESS, AFFILIATE_INTERNET_NAME, AFFILIATE_IPADDR, CO_HOSTED_SITE)")
    checkaffiliates: Optional[bool] = Field(
        default=True,
        description="Apply checks to affiliates?"
    )
    checkcohosts: Optional[bool] = Field(
        default=True,
        description="Apply checks to sites found to be co-hosted on the target's IP?"
    )
    url: Optional[str] = Field(
        default="",
        description="The URL where the feed can be found. Exact matching is performed so the format must be a single line per host, ASN, domain, IP or netblock."
    )
    cacheperiod: Optional[int] = Field(
        default=0,
        description="Maximum age of data in hours before re-downloading. 0 to always download."
    )


class SfpCustomfeedTool(BaseTool):
    """Tool for Check if a host/domain, netblock, ASN or IP is malicious according to your custom feed.."""
    
    name: str = "Custom Threat Feed"
    description: str = (
        "Check if a host/domain, netblock, ASN or IP is malicious according to your custom feed."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpCustomfeedToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        checkaffiliates: Optional[bool] = True,
        checkcohosts: Optional[bool] = True,
        url: Optional[str] = "",
        cacheperiod: Optional[int] = 0,
        **kwargs: Any
    ) -> str:
        """Execute Custom Threat Feed."""
        try:
            safe_log_info(logger, f"[SfpCustomfeedTool] Starting", target=target)
            
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
                implement_customfeed
            )
            
            # Build parameters for the implementation function
            # Note: checkaffiliates and checkcohosts are event-level filters, not implementation parameters
            implementation_params = {
                "target": target,
                "url": url,
                "target_type": None,  # Auto-detected in implementation
                "cacheperiod": cacheperiod,
            }
            
            # Execute migrated implementation
            implementation_result = implement_customfeed(**implementation_params)
            
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
                "module": "sfp_customfeed",
                "module_name": "Custom Threat Feed",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Custom Threat Feed tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpCustomfeedTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpCustomfeedTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Custom Threat Feed search failed: {str(e)}",
                "user_id": user_id
            })
