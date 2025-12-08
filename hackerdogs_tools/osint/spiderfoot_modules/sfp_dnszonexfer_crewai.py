"""
DNS Zone Transfer Tool for CrewAI Agents

Attempts to perform a full DNS zone transfer.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dnszonexfer_tool.log")




class SfpDnszonexferToolSchema(BaseModel):
    """Input schema for DNS Zone TransferTool."""
    target: str = Field(..., description="Target to investigate (PROVIDER_DNS)")
    timeout: Optional[int] = Field(
        default=30,
        description="Timeout in seconds"
    )


class SfpDnszonexferTool(BaseTool):
    """Tool for Attempts to perform a full DNS zone transfer.."""
    
    name: str = "DNS Zone Transfer"
    description: str = (
        "Attempts to perform a full DNS zone transfer."
        "\n\nUse Cases: Footprint, Investigate"
        "\nCategories: DNS"
    )
    args_schema: type[BaseModel] = SfpDnszonexferToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        timeout: Optional[int] = 30,
        **kwargs: Any
    ) -> str:
        """Execute DNS Zone Transfer."""
        try:
            safe_log_info(logger, f"[SfpDnszonexferTool] Starting", target=target)
            
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
                implement_dnszonexfer
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "timeout": timeout,
            }
            
            # Execute migrated implementation
            implementation_result = implement_dnszonexfer(**implementation_params)
            
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
                "module": "sfp_dnszonexfer",
                "module_name": "DNS Zone Transfer",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from DNS Zone Transfer tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDnszonexferTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDnszonexferTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"DNS Zone Transfer search failed: {str(e)}",
                "user_id": user_id
            })
