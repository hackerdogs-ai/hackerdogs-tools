"""
BinaryEdge Tool for CrewAI Agents

Obtain information from BinaryEdge.io Internet scanning systems, including breaches, vulnerabilities, torrents and passive DNS.
Data Source: https://www.binaryedge.io/
"""

import json
import os
from typing import Any, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_binaryedge_tool.log")


def _get_api_key(**kwargs: Any) -> Optional[str]:
    """Get API key from kwargs or environment variable."""
    api_keys = kwargs.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("BINARYEDGE_API_KEY") or
        api_keys.get("binaryedge_api_key") or
        api_keys.get("BINARYEDGE_API_KEY") or
        os.getenv("BINARYEDGE_API_KEY") or
        os.getenv("binaryedge_api_key") or
        os.getenv("BINARYEDGE_API_KEY")
    )
    return key


class SfpBinaryedgeToolSchema(BaseModel):
    """Input schema for BinaryEdgeTool."""
    target: str = Field(..., description="Target to investigate (IP_ADDRESS, DOMAIN_NAME, EMAILADDR, NETBLOCK_OWNER, NETBLOCK_MEMBER)")
    binaryedge_api_key: Optional[str] = Field(
        default="",
        description="BinaryEdge.io API Key."
    )
    torrent_age_limit_days: Optional[int] = Field(
        default=30,
        description="Ignore any torrent records older than this many days. 0 = unlimited."
    )
    cve_age_limit_days: Optional[int] = Field(
        default=30,
        description="Ignore any vulnerability records older than this many days. 0 = unlimited."
    )
    port_age_limit_days: Optional[int] = Field(
        default=90,
        description="Ignore any discovered open ports/banners older than this many days. 0 = unlimited."
    )
    maxpages: Optional[int] = Field(
        default=10,
        description="Maximum number of pages to iterate through, to avoid exceeding BinaryEdge API usage limits. APIv2 has a maximum of 500 pages (10,000 results)."
    )
    verify: Optional[bool] = Field(
        default=True,
        description="Verify that any hostnames found on the target domain still resolve?"
    )
    netblocklookup: Optional[bool] = Field(
        default=False,
        description="Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?"
    )
    maxnetblock: Optional[int] = Field(
        default=24,
        description="If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    subnetlookup: Optional[bool] = Field(
        default=False,
        description="Look up all IPs on subnets which your target is a part of?"
    )
    maxsubnet: Optional[int] = Field(
        default=24,
        description="If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)"
    )
    maxcohost: Optional[int] = Field(
        default=100,
        description="Stop reporting co-hosted sites after this many are found, as it would likely indicate web hosting."
    )
    api_key: Optional[str] = Field(default=None, description="API key for BinaryEdge")


class SfpBinaryedgeTool(BaseTool):
    """Tool for Obtain information from BinaryEdge.io Internet scanning systems, including breaches, vulnerabilities, torrents and passive DNS.."""
    
    name: str = "BinaryEdge"
    description: str = (
        "Obtain information from BinaryEdge.io Internet scanning systems, including breaches, vulnerabilities, torrents and passive DNS."
        "\n\nUse Cases: Footprint, Investigate, Passive"
        "\nCategories: Search Engines"
    )
    args_schema: type[BaseModel] = SfpBinaryedgeToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
        target: str,
        binaryedge_api_key: Optional[str] = "",
        torrent_age_limit_days: Optional[int] = 30,
        cve_age_limit_days: Optional[int] = 30,
        port_age_limit_days: Optional[int] = 90,
        maxpages: Optional[int] = 10,
        verify: Optional[bool] = True,
        netblocklookup: Optional[bool] = False,
        maxnetblock: Optional[int] = 24,
        subnetlookup: Optional[bool] = False,
        maxsubnet: Optional[int] = 24,
        maxcohost: Optional[int] = 100,
        api_key: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Execute BinaryEdge."""
        try:
            safe_log_info(logger, f"[SfpBinaryedgeTool] Starting", target=target, has_api_key=bool(api_key))
            
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
                    "note": "API key can be provided via api_key parameter, kwargs['api_keys'], or BINARYEDGE_API_KEY environment variable"
                })
            
            # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
            # Import implementation function dynamically
            from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
                implement_binaryedge
            )
            
            # Build parameters for the implementation function
            implementation_params = {
                "target": target,
                "api_key": api_key,
                "binaryedge_api_key": binaryedge_api_key,
                "torrent_age_limit_days": torrent_age_limit_days,
                "cve_age_limit_days": cve_age_limit_days,
                "port_age_limit_days": port_age_limit_days,
                "maxpages": maxpages,
                "verify": verify,
                "netblocklookup": netblocklookup,
                "maxnetblock": maxnetblock,
                "subnetlookup": subnetlookup,
                "maxsubnet": maxsubnet,
                "maxcohost": maxcohost,
            }
            
            # Execute migrated implementation
            implementation_result = implement_binaryedge(**implementation_params)
            
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
                "module": "sfp_binaryedge",
                "module_name": "BinaryEdge",
                "target": target,
                "raw_response": result_data,
                "user_id": user_id,
                "note": "Raw output from BinaryEdge tool - migrated standalone implementation"
            }
            
            safe_log_info(logger, f"[SfpBinaryedgeTool] Complete", target=target, user_id=user_id)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            target = kwargs.get("target", "unknown")
            user_id = kwargs.get("user_id", "")
            safe_log_error(logger, f"[SfpBinaryedgeTool] Error: {str(e)}", target=target, user_id=user_id, exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"BinaryEdge search failed: {str(e)}",
                "user_id": user_id
            })
