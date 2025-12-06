"""
AlienVault OTX Tool for CrewAI Agents

This module provides CrewAI tools for querying AlienVault OTX's threat intelligence API.
"""

import json
import os
from typing import Any, Optional
from crewai.tools import BaseTool, EnvVar
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/otx_tool.log")

# Import OTX SDK
try:
    from OTXv2 import OTXv2Cached, OTXv2  # type: ignore
    OTX_AVAILABLE = True
except ImportError:
    OTX_AVAILABLE = False


class OTXToolSchema(BaseModel):
    """Input schema for OTXTool."""
    indicator: str = Field(..., description="IP, domain, hash, or URL to check")
    indicator_type: str = Field(
        default="domain",
        description="Type: 'IPv4', 'domain', 'hostname', 'url', 'hash'"
    )


class OTXTool(BaseTool):
    """Tool for querying AlienVault OTX threat intelligence."""
    
    name: str = "AlienVault OTX Threat Intelligence"
    description: str = (
        "Query AlienVault Open Threat Exchange for threat intelligence. "
        "Check if indicators (IPs, domains, URLs, hashes) are associated with known threats."
    )
    args_schema: type[BaseModel] = OTXToolSchema
    
    env_vars: list[EnvVar] = [
        EnvVar(
            name="OTX_API_KEY",
            description="AlienVault OTX API key (optional, free tier available)",
            required=False,
        ),
    ]
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if not OTX_AVAILABLE:
            raise ImportError(
                "OTXv2 SDK not available. Install with: pip install OTXv2"
            )
    
    def _run(
        self,
        indicator: str,
        indicator_type: str = "domain",
        **kwargs: Any
    ) -> str:
        """Execute OTX query."""
        try:
            safe_log_info(logger, f"[OTXTool] Querying indicator", indicator=indicator, type=indicator_type)
            
            api_key = os.getenv("OTX_API_KEY", "")
            if not api_key:
                return json.dumps({
                    "status": "error",
                    "message": "OTX_API_KEY environment variable not set. Get free API key from https://otx.alienvault.com"
                })
            
            # Create OTX client
            try:
                otx = OTXv2Cached(api_key, server="https://otx.alienvault.com")
            except Exception:
                otx = OTXv2(api_key, server="https://otx.alienvault.com")
            
            # Query based on indicator type
            if indicator_type.lower() == "ipv4":
                result = otx.get_indicator_details_full("IPv4", indicator)
            elif indicator_type.lower() == "domain":
                result = otx.get_indicator_details_full("domain", indicator)
            elif indicator_type.lower() == "url":
                result = otx.get_indicator_details_full("url", indicator)
            elif indicator_type.lower() == "hash":
                result = otx.get_indicator_details_full("file", indicator)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unsupported indicator type: {indicator_type}"
                })
            
            # Return raw API response verbatim - no parsing, no reformatting
            safe_log_info(logger, f"[OTXTool] Complete - returning raw API response verbatim", indicator=indicator)
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            safe_log_error(logger, f"[OTXTool] Error: {str(e)}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

