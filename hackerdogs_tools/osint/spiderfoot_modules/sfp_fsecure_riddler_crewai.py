"""
F-Secure Riddler.io Tool for CrewAI Agents

Obtain network information from F-Secure Riddler.io API.
Data Source: https://riddler.io/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_fsecure_riddler_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("FSECURE_RIDDLER_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("FSECURE_RIDDLER_API_KEY")
    )
    return key


class SfpFsecureriddlerToolSchema(BaseModel):
    """Input schema for F-Secure Riddler.ioTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME, INTERNET_NAME, INTERNET_NAME_UNRESOLVED, IP_ADDRESS)")
    verify: Optional[bool] = Field(
        default=True,
        description="Verify host names resolve"
    )
    username: Optional[str] = Field(
        default="",
        description="F-Secure Riddler.io username"
    )
    password: Optional[str] = Field(
        default="",
        description="F-Secure Riddler.io password"
    )
    api_key: Optional[str] = Field(default=None, description="API key for F-Secure Riddler.io")


class SfpFsecureriddlerTool(BaseTool):
    """Tool for Obtain network information from F-Secure Riddler.io API.."""
    
    name: str = "F-Secure Riddler.io"
    description: str = (
        "Obtain network information from F-Secure Riddler.io API."
        "\n\nUse Cases: Investigate, Footprint, Passive"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpFsecureriddlerToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        verify: Optional[bool] = True,
        username: Optional[str] = "",
        password: Optional[str] = "",
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute F-Secure Riddler.io."""
        try:
            safe_log_info(logger, f"[SfpFsecureriddlerTool] Starting", target=target, has_api_key=bool(api_key))
            
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
            
            # Get credentials from parameters or environment
            if not username:
                username = kwargs.get("fsecure_riddler_username", "") or os.getenv("FSECURE_RIDDLER_USERNAME", "")
            if not password:
                password = kwargs.get("fsecure_riddler_password", "") or os.getenv("FSECURE_RIDDLER_PASSWORD", "")
            
            if not username or not password:
                error_msg = "F-Secure Riddler.io username and password are required"
                safe_log_error(logger, error_msg, target=target, user_id=user_id)
                return json.dumps({
                    "status": "error",
                    "message": error_msg,
                    "user_id": user_id,
                    "note": "Credentials can be provided via parameters, kwargs, or FSECURE_RIDDLER_USERNAME/FSECURE_RIDDLER_PASSWORD environment variables"
                })
            
            # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
            # Import implementation function dynamically
            from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
                implement_fsecure_riddler
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "username": username,
                "password": password,
                "verify": verify,
            }
            
            # Execute migrated implementation
            implementation_result = implement_fsecure_riddler(**implementation_params)
            
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
                "module": "sfp_fsecure_riddler",
                "module_name": "F-Secure Riddler.io",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from F-Secure Riddler.io tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpFsecureriddlerTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpFsecureriddlerTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"F-Secure Riddler.io search failed: {str(e)}",
                "user_id": user_id
            })
