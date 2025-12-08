"""
Certificate Transparency Tool for CrewAI Agents

Gather hostnames from historical certificates in crt.sh.
Data Source: https://crt.sh/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_crt_tool.log")




class SfpCrtToolSchema(BaseModel):
    """Input schema for Certificate TransparencyTool."""
    target: str = Field(..., description="Target to investigate (DOMAIN_NAME, INTERNET_NAME)")
    verify: Optional[bool] = Field(
        default=True,
        description="Verify certificate subject alternative names resolve."
    )
    fetchcerts: Optional[bool] = Field(
        default=True,
        description="Fetch each certificate found, for processing by other modules."
    )


class SfpCrtTool(BaseTool):
    """Tool for Gather hostnames from historical certificates in crt.sh.."""
    
    name: str = "Certificate Transparency"
    description: str = (
        "Gather hostnames from historical certificates in crt.sh."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpCrtToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        verify: Optional[bool] = True,
        fetchcerts: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute Certificate Transparency."""
        try:
            safe_log_info(logger, f"[SfpCrtTool] Starting", target=target)
            
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
                implement_crt
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "verify": verify,
                "fetchcerts": fetchcerts,
            }
            
            # Execute migrated implementation
            implementation_result = implement_crt(**implementation_params)
            
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
                "module": "sfp_crt",
                "module_name": "Certificate Transparency",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Certificate Transparency tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpCrtTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpCrtTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Certificate Transparency search failed: {str(e)}",
                "user_id": user_id
            })
