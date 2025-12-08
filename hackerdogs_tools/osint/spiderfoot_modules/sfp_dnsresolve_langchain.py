"""
DNS Resolver Tool for LangChain Agents

Resolves hosts and IP addresses identified, also extracted from raw content.
"""

import json
import os
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/spiderfoot_dnsresolve_tool.log")


class SfpDnsresolveSecurityAgentState(AgentState):
    """Extended agent state for DNS Resolver operations."""
    user_id: str = ""


@tool
def sfp_dnsresolve(
    runtime: ToolRuntime,
    target: str,
    validatereverse: Optional[bool] = True,
    skipcommononwildcard: Optional[bool] = True,
    netblocklookup: Optional[bool] = True,
    maxnetblock: Optional[int] = 24,
    maxv6netblock: Optional[int] = 120,
    **kwargs: Any
) -> str:
    """
    Resolves hosts and IP addresses identified, also extracted from raw content.
    
    Use Cases: Footprint, Investigate, Passive
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        target: Target to investigate (CO_HOSTED_SITE, AFFILIATE_INTERNET_NAME, NETBLOCK_OWNER, NETBLOCKV6_OWNER, IP_ADDRESS, IPV6_ADDRESS, INTERNET_NAME, AFFILIATE_IPADDR, AFFILIATE_IPV6_ADDRESS, TARGET_WEB_CONTENT, BASE64_DATA, AFFILIATE_DOMAIN_WHOIS, CO_HOSTED_SITE_DOMAIN_WHOIS, DOMAIN_WHOIS, NETBLOCK_WHOIS, LEAKSITE_CONTENT, RAW_DNS_RECORDS, RAW_FILE_META_DATA, RAW_RIR_DATA, SIMILARDOMAIN_WHOIS, SSL_CERTIFICATE_RAW, SSL_CERTIFICATE_ISSUED, TCP_PORT_OPEN_BANNER, WEBSERVER_BANNER, WEBSERVER_HTTPHEADERS)
        skipcommononwildcard: If wildcard DNS is detected, only attempt to look up the first common sub-domain from the common sub-domain list.
        validatereverse: Validate that reverse-resolved hostnames still resolve back to that IP before considering them as aliases of your target.
        netblocklookup: Look up all IPs on netblocks deemed to be owned by your target for possible hosts on the same target subdomain/domain?
        maxnetblock: Maximum owned IPv4 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
        maxv6netblock: Maximum owned IPv6 netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)
    
    Returns:
        JSON string with results.
    """
    try:
        safe_log_info(logger, f"[sfp_dnsresolve] Starting", target=target)
        
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
        
        
        # MIGRATED IMPLEMENTATION - Direct execution, no Docker, no SpiderFoot dependencies
        # Import implementation function dynamically
        from hackerdogs_tools.osint.spiderfoot_modules._implementations import (
            implement_dnsresolve
        )
        
        # Build parameters for the implementation function
        implementation_params = {
            "target": target,
            "validatereverse": validatereverse,
            "skipcommononwildcard": skipcommononwildcard,
            "netblocklookup": netblocklookup,
            "maxnetblock": maxnetblock,
            "maxv6netblock": maxv6netblock,
        }
        
        # Execute migrated implementation
        implementation_result = implement_dnsresolve(**implementation_params)
        
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
            "module": "sfp_dnsresolve",
            "module_name": "DNS Resolver",
            "target": target,
            "raw_response": result_data,
            "user_id": user_id,
            "note": "Raw output from DNS Resolver tool - migrated standalone implementation"
        }
        
        safe_log_info(logger, f"[sfp_dnsresolve] Complete", target=target, user_id=user_id)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        # Safely get variables for error handling
        error_target = target if 'target' in locals() else kwargs.get("target", "unknown")
        error_user_id = runtime.state.get("user_id", "unknown") if 'runtime' in locals() else "unknown"
        safe_log_error(logger, f"[sfp_dnsresolve] Error: {str(e)}", target=error_target, user_id=error_user_id, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"DNS Resolver search failed: {str(e)}",
            "user_id": error_user_id
        })
