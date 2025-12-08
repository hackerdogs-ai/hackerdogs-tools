"""
DNS Look-aside Tool for CrewAI Agents

Attempt to reverse-resolve the IP addresses next to your target to see if they are related.
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dnsneighbor_tool.log")




class SfpDnsneighborToolSchema(BaseModel):
    """Input schema for DNS Look-asideTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS)")
    lookasidebits: Optional[int] = Field(
        default=4,
        description="If look-aside is enabled, the netmask size (in CIDR notation) to check. Default is 4 bits (16 hosts)."
    )
    validatereverse: Optional[bool] = Field(
        default=True,
        description="Validate that reverse-resolved hostnames still resolve back to that IP before considering them as aliases of your target."
    )


class SfpDnsneighborTool(BaseTool):
    """Tool for Attempt to reverse-resolve the IP addresses next to your target to see if they are related.."""
    
    name: str = "DNS Look-aside"
    description: str = (
        "Attempt to reverse-resolve the IP addresses next to your target to see if they are related."
        "\n\nUse Cases: Footprint, Investigate"
        "\nCategories: DNS"
    )
    args_schema: type[BaseModel] = SfpDnsneighborToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        lookasidebits: Optional[int] = 4,
        validatereverse: Optional[bool] = True,
        **kwargs: Any
    ) -> str:
        """Execute DNS Look-aside."""
        try:
            safe_log_info(logger, f"[SfpDnsneighborTool] Starting", target=target)
            
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
                implement_dnsneighbor
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "lookasidebits": lookasidebits,
                "validatereverse": validatereverse,
            }
            
            # Execute migrated implementation
            implementation_result = implement_dnsneighbor(**implementation_params)
            
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
                "module": "sfp_dnsneighbor",
                "module_name": "DNS Look-aside",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from DNS Look-aside tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpDnsneighborTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpDnsneighborTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"DNS Look-aside search failed: {str(e)}",
                "user_id": user_id
            })
