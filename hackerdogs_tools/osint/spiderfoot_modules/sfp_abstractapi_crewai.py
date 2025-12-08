"""
AbstractAPI Tool for CrewAI Agents

Look up domain, phone and IP address information from AbstractAPI.
Data Source: https://app.abstractapi.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_abstractapi_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("COMPANYENRICHMENT_API_KEY") or
        api_keys.get("companyenrichment_api_key") or
        api_keys.get("ABSTRACTAPI_API_KEY") or
        os.getenv("COMPANYENRICHMENT_API_KEY") or
        os.getenv("companyenrichment_api_key") or
        os.getenv("ABSTRACTAPI_API_KEY")
    )
    return key


class SfpAbstractapiToolSchema(BaseModel):
    """Input schema for AbstractAPITool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME, PHONE_NUMBER, IP_ADDRESS, IPV6_ADDRESS)")
    companyenrichment_api_key: Optional[str] = Field(
        default="",
        description="AbstractAPI Company Enrichment API key."
    )
    phonevalidation_api_key: Optional[str] = Field(
        default="",
        description="AbstractAPI Phone Validation API key."
    )
    ipgeolocation_api_key: Optional[str] = Field(
        default="",
        description="AbstractAPI IP Geolocation API key."
    )
    api_key: Optional[str] = Field(default=None, description="API key for AbstractAPI")


class SfpAbstractapiTool(BaseTool):
    """Tool for Look up domain, phone and IP address information from AbstractAPI.."""
    
    name: str = "AbstractAPI"
    description: str = (
        "Look up domain, phone and IP address information from AbstractAPI."
        "\n\nUse Cases: Passive, Footprint, Investigate"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpAbstractapiToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        companyenrichment_api_key: Optional[str] = "",
        phonevalidation_api_key: Optional[str] = "",
        ipgeolocation_api_key: Optional[str] = "",
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute AbstractAPI."""
        try:
            safe_log_info(logger, f"[SfpAbstractapiTool] Starting", target=target, has_api_key=bool(api_key))
            
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
                    "note": "API key can be provided via api_key parameter, kwargs['api_keys'], or COMPANYENRICHMENT_API_KEY environment variable"
                })
            
            # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
            # Import implementation function dynamically
            from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
                implement_abstractapi
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "api_key": api_key,
                "companyenrichment_api_key": companyenrichment_api_key,
                "phonevalidation_api_key": phonevalidation_api_key,
                "ipgeolocation_api_key": ipgeolocation_api_key,
            }
            
            # Execute migrated implementation
            implementation_result = implement_abstractapi(**implementation_params)
            
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
                "module": "sfp_abstractapi",
                "module_name": "AbstractAPI",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from AbstractAPI tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpAbstractapiTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpAbstractapiTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"AbstractAPI search failed: {str(e)}",
                "user_id": user_id
            })
