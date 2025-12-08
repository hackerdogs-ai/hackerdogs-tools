"""
Base64 Decoder Tool for CrewAI Agents

Identify Base64-encoded strings in URLs, often revealing interesting hidden information.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_base64_tool.log")




class SfpBase64ToolSchema(BaseModel):
    """Input schema for Base64 DecoderTool."""
    target: str = Field(..., description="Target to investigate (LINKED_URL_INTERNAL)")
    minlength: Optional[int] = Field(
        default=10,
        description="The minimum length a string that looks like a base64-encoded string needs to be."
    )


class SfpBase64Tool(BaseTool):
    """Tool for Identify Base64-encoded strings in URLs, often revealing interesting hidden information.."""
    
    name: str = "Base64 Decoder"
    description: str = (
        "Identify Base64-encoded strings in URLs, often revealing interesting hidden information."
        "\n\nUse Cases: Investigate, Passive"
        "\nCategories: Content Analysis"
    )
    args_schema: type[BaseModel] = SfpBase64ToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        minlength: Optional[int] = 10,
        **kwargs: Any
    ) -> str:
        """Execute Base64 Decoder."""
        try:
            safe_log_info(logger, f"[SfpBase64Tool] Starting", target=target)
            
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
                implement_base64
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "minlength": minlength,
            }
            
            # Execute migrated implementation
            implementation_result = implement_base64(**implementation_params)
            
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
                "module": "sfp_base64",
                "module_name": "Base64 Decoder",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Base64 Decoder tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpBase64Tool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpBase64Tool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Base64 Decoder search failed: {str(e)}",
                "user_id": user_id
            })
