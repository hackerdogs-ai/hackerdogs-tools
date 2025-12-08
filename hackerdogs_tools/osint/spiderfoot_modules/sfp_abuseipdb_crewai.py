"""
AbuseIPDB Tool for CrewAI Agents

Check if an IP address is malicious according to AbuseIPDB.com blacklist.
Data Source: https://www.abuseipdb.com
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_abuseipdb_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("ABUSEIPDB_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("ABUSEIPDB_API_KEY")
    )
    return key


class SfpAbuseipdbToolSchema(BaseModel):
    """Input schema for AbuseIPDBTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, IPV6_ADDRESS, AFFILIATE_IPADDR, AFFILIATE_IPV6_ADDRESS)")
    confidenceminimum: Optional[int] = Field(
        default=90,
        description="The minimium AbuseIPDB confidence level to require."
    )
    checkaffiliates: Optional[bool] = Field(
        default=True,
        description="Apply checks to affiliates?"
    )
    limit: Optional[int] = Field(
        default=10000,
        description="Maximum number of results to retrieve."
    )
    api_key: Optional[str] = Field(default=None, description="AbuseIPDB.com API key.")


class SfpAbuseipdbTool(BaseTool):
    """Tool for Check if an IP address is malicious according to AbuseIPDB.com blacklist.."""
    
    name: str = "AbuseIPDB"
    description: str = (
        "Check if an IP address is malicious according to AbuseIPDB.com blacklist."
        "\n\nUse Cases: Passive, Investigate"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpAbuseipdbToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        confidenceminimum: Optional[int] = 90,
        checkaffiliates: Optional[bool] = True,
        limit: Optional[int] = 10000,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute AbuseIPDB."""
        try:
            safe_log_info(logger, f"[SfpAbuseipdbTool] Starting", target=target, has_api_key=bool(api_key))
            
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
                implement_abuseipdb
            )
            
            # Execute migrated implementation
            implementation_result = implement_abuseipdb(
                target=target,
                api_key=api_key,
                confidenceminimum=confidenceminimum,
                checkaffiliates=checkaffiliates,
                limit=limit
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
                "module": "sfp_abuseipdb",
                "module_name": "AbuseIPDB",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from AbuseIPDB tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAbuseipdbTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAbuseipdbTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"AbuseIPDB search failed: {str(e)}",
                "user_id": user_id
            })
