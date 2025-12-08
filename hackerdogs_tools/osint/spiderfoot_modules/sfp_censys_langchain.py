"""
Censys Tool for LangChain Agents

Obtain host information from Censys.io.
Data Source: https://censys.io/
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_censys_tool.log")


class SfpCensysSecurityAgentState(AgentState):
    """Extended agent state for Censys operations."""
    user_id: str = ""


def _get_api_key(runtime: ToolRuntime) -> Optional[str]:
    """Get API key from runtime state or environment variable."""
    api_keys = runtime.state.get("api_keys", {})
    # Try multiple key name variations
    key = (
        api_keys.get("CENSYS_API_KEY_UID") or
        api_keys.get("censys_api_key_uid") or
        api_keys.get("CENSYS_API_KEY") or
        os.getenv("CENSYS_API_KEY_UID") or
        os.getenv("censys_api_key_uid") or
        os.getenv("CENSYS_API_KEY")
    )
    return key


@tool
def sfp_censys(
    runtime: ToolRuntime,
    target: str,
    censys_api_key_uid: Optional[str] = "",
    censys_api_key_secret: Optional[str] = "",
    delay: Optional[int] = 3,
    netblocklookup: Optional[bool] = True,
    maxnetblock: Optional[int] = 24,
    maxv6netblock: Optional[int] = 120,
    age_limit_days: Optional[int] = 90,
    api_key: Optional[str] = None,
    **kwargs: Any
) -> str:
    """
    Obtain host information from Censys.io.
    
    Use Cases: Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (IP_ADDRESS, IPV6_ADDRESS, NETBLOCK_OWNER, NETBLOCKV6_OWNER)
        censys_api_key_uid: Censys.io API UID.
        censys_api_key_secret: Censys.io API Secret.
        delay: Delay between requests, in seconds.
        netblocklookup: Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?
        maxnetblock: If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        maxv6netblock: If looking up owned netblocks, the maximum IPv6 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        age_limit_days: Ignore any records older than this many days. 0 = unlimited.
        api_key: API key for Censys
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_censys] Starting", target=target, has_api_key=bool(api_key))
        
        # Get user_id from runtime state
        user_id = runtime.state.get("user_id", "unknown")
        
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
        api_key = api_key or _get_api_key(runtime)
        if not api_key:
            error_msg = "API key required but not provided"
            safe_log_error(logger, error_msg, target=target, user_id=user_id)
            return json.dumps({
                "status": "error",
                "message": error_msg,
                "user_id": user_id,
                "note": "API key can be provided via api_key parameter, runtime.state['api_keys'], or CENSYS_API_KEY_UID environment variable"
            })
        
        # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
        # Import implementation function dynamically
        from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
            implement_censys
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "api_key": api_key,
            "censys_api_key_uid": censys_api_key_uid,
            "censys_api_key_secret": censys_api_key_secret,
            "delay": delay,
            "netblocklookup": netblocklookup,
            "maxnetblock": maxnetblock,
            "maxv6netblock": maxv6netblock,
            "age_limit_days": age_limit_days,
        }
        
        # Execute migrated implementation
        implementation_result = implement_censys(**implementation_params)
        
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
            "module": "sfp_censys",
            "module_name": "Censys",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from Censys tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_censys] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_censys] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Censys search failed: {str(e)}",
            "user_id": error_user_id
        })
