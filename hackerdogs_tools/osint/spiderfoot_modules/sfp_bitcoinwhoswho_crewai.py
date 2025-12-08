"""
Bitcoin Who's Who Tool for CrewAI Agents

Check for Bitcoin addresses against the Bitcoin Who's Who database of suspect/malicious addresses.
Data Source: https://bitcoinwhoswho.com/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_bitcoinwhoswho_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("API_KEY") or
        api_keys.get("api_key") or
        api_keys.get("BITCOINWHOSWHO_API_KEY") or
        os.getenv("API_KEY") or
        os.getenv("api_key") or
        os.getenv("BITCOINWHOSWHO_API_KEY")
    )
    return key


class SfpBitcoinwhoswhoToolSchema(BaseModel):
    """Input schema for Bitcoin Who's WhoTool."""
    target: str = Field(..., description="Target to investigate (BITCOIN_ADDRESS)")
    api_key: Optional[str] = Field(default=None, description="Bitcoin Who's Who API Key.")


class SfpBitcoinwhoswhoTool(BaseTool):
    """Tool for Check for Bitcoin addresses against the Bitcoin Who's Who database of suspect/malicious addresses.."""
    
    name: str = "Bitcoin Who's Who"
    description: str = (
        "Check for Bitcoin addresses against the Bitcoin Who's Who database of suspect/malicious addresses."
        "\n\nUse Cases: Passive, Investigate"
        "\nCategories: Reputation Systems"
    )
    args_schema: type[BaseModel] = SfpBitcoinwhoswhoToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute Bitcoin Who's Who."""
        try:
            safe_log_info(logger, f"[SfpBitcoinwhoswhoTool] Starting", target=target, has_api_key=bool(api_key))
            
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
                implement_bitcoinwhoswho
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "api_key": api_key,
            }
            
            # Execute migrated implementation
            implementation_result = implement_bitcoinwhoswho(**implementation_params)
            
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
                "module": "sfp_bitcoinwhoswho",
                "module_name": "Bitcoin Who's Who",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from Bitcoin Who's Who tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpBitcoinwhoswhoTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpBitcoinwhoswhoTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Bitcoin Who's Who search failed: {str(e)}",
                "user_id": user_id
            })
