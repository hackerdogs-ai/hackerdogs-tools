"""
Bing (Shared IPs) Tool for CrewAI Agents

Search Bing for hosts sharing the same IP.
Data Source: https://www.bing.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_bingsharedip_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("BINGSHAREDIP_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("BINGSHAREDIP_API_KEY")
    )
    return key


class SfpBingsharedipToolSchema(BaseModel):
    """Input schema for Bing (Shared IPs)Tool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, NETBLOCK_OWNER)")
    cohostsamedomain: Optional[bool] = Field(
        default=False,
        description="Treat co-hosted sites on the same target domain as co-hosting?"
    )
    pages: Optional[int] = Field(
        default=20,
        description="Number of max bing results to request from API."
    )
    verify: Optional[bool] = Field(
        default=True,
        description="Verify co-hosts are valid by checking if they still resolve to the shared IP."
    )
    maxcohost: Optional[int] = Field(
        default=100,
        description="Stop reporting co-hosted sites after this many are found, as it would likely indicate web hosting."
    )
    api_key: Optional[str] = Field(default=None, description="Bing API Key for shared IP search.")


class SfpBingsharedipTool(BaseTool):
    """Tool for Search Bing for hosts sharing the same IP.."""
    
    name: str = "Bing (Shared IPs)"
    description: str = (
        "Search Bing for hosts sharing the same IP."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpBingsharedipToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        cohostsamedomain: Optional[bool] = False,
        pages: Optional[int] = 20,
        verify: Optional[bool] = True,
        maxcohost: Optional[int] = 100,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute Bing (Shared IPs)."""
        try:
            safe_log_info(logger, f"[SfpBingsharedipTool] Starting", target=target, has_api_key=bool(api_key))
            
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
                implement_bingsharedip
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "api_key": api_key,
                "cohostsamedomain": cohostsamedomain,
                "pages": pages,
                "verify": verify,
                "maxcohost": maxcohost,
            }
            
            # Execute migrated implementation
            implementation_result = implement_bingsharedip(**implementation_params)
            
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
                "module": "sfp_bingsharedip",
                "module_name": "Bing (Shared IPs)",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Bing (Shared IPs) tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpBingsharedipTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpBingsharedipTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Bing (Shared IPs) search failed: {str(e)}",
                "user_id": user_id
            })
