"""
Waybackurls Tool for LangChain Agents

Fetch URLs from Wayback Machine using waybackpy Python package.
This tool queries the Wayback Machine to retrieve historical URLs for a given domain.

Reference: https://github.com/akamhy/waybackpy

Key Features:
- Fetch all URLs archived in Wayback Machine for a domain
- Exclude subdomains option
- Date filtering support
- Get versions of specific URLs

Usage:
    from langchain.agents import create_agent
    from hackerdogs_tools.osint.content.waybackurls_langchain import waybackurls_search
    
    agent = create_agent(
        model=llm,
        tools=[waybackurls_search],
        system_prompt="You are an OSINT specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Get Wayback URLs for example.com"}],
        "user_id": "analyst_001"
    })
"""

import json
from typing import Optional, Any
from urllib.parse import urlparse
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug
from waybackpy import WaybackMachineCDXServerAPI

logger = setup_logger(__name__, log_file_path="logs/waybackurls_tool.log")


class WaybackurlsSecurityAgentState(AgentState):
    """Extended agent state for Waybackurls operations."""
    user_id: str = ""


@tool
def waybackurls_search(
    runtime: ToolRuntime,
    domain: str,
    no_subs: bool = False,
    dates: Optional[str] = None,
    get_versions: bool = False,
    **kwargs: Any
) -> str:
    """
    Fetch URLs from Wayback Machine for a given domain.
    
    This tool queries the Wayback Machine archive to retrieve all URLs that have been
    archived for the specified domain. Useful for discovering historical endpoints,
    finding deleted pages, and mapping website structure over time.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        domain: Domain name to fetch URLs for (e.g., "example.com").
        no_subs: If True, exclude subdomains (default: False).
        dates: Optional date range filter in format "YYYYMMDD-YYYYMMDD".
        get_versions: If True, list URLs for crawled versions of input URL(s) (default: False).
            Note: Currently not implemented - all snapshots are returned regardless of this flag.
    
    Returns:
        JSON string with list of URLs found in Wayback Machine.
    """
    try:
        safe_log_info(logger, f"[waybackurls_search] Starting", domain=domain, no_subs=no_subs, dates=dates, get_versions=get_versions)
        
        # Validate inputs
        user_id = runtime.state.get("user_id", "") if runtime and runtime.state else ""
        
        if not domain or not isinstance(domain, str) or len(domain.strip()) == 0:
            error_msg = "domain must be a non-empty string"
            safe_log_error(logger, error_msg, user_id=user_id)
            return json.dumps({"status": "error", "message": error_msg, "user_id": user_id})
        
        domain = domain.strip()
        
        # Use waybackpy Python package instead of Docker
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
        # Parse date range if provided
        start_timestamp = None
        end_timestamp = None
        if dates:
            try:
                # Format: YYYYMMDD-YYYYMMDD
                dates = dates.strip()
                parts = dates.split("-")
                if len(parts) == 2:
                    start_str = parts[0].strip()
                    end_str = parts[1].strip()
                    # Validate format (must be 8 digits)
                    if len(start_str) == 8 and len(end_str) == 8 and start_str.isdigit() and end_str.isdigit():
                        start_timestamp = int(start_str)  # YYYYMMDD
                        end_timestamp = int(end_str)    # YYYYMMDD
                    else:
                        raise ValueError("Date must be in YYYYMMDD format (8 digits)")
                else:
                    raise ValueError("Date range must be in format YYYYMMDD-YYYYMMDD")
            except (ValueError, AttributeError) as e:
                error_msg = f"Invalid date format: {dates}. Expected YYYYMMDD-YYYYMMDD. Error: {str(e)}"
                safe_log_error(logger, error_msg, user_id=user_id)
                return json.dumps({"status": "error", "message": error_msg, "user_id": user_id})
        
        # Create CDX API instance
        try:
            cdx_api = WaybackMachineCDXServerAPI(
                url=f"https://{domain}",
                user_agent=user_agent,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp
            )
            
            # Get snapshots
            urls = []
            snapshot_count = 0
            for snapshot in cdx_api.snapshots():
                snapshot_count += 1
                original_url = snapshot.original
                timestamp = snapshot.timestamp
                
                # Filter subdomains if no_subs is True
                if no_subs:
                    # Extract domain from URL
                    parsed = urlparse(original_url)
                    url_domain = parsed.netloc
                    if not url_domain:
                        # If netloc is empty, skip this URL (invalid URL format)
                        continue
                    
                    # Remove port if present
                    if ":" in url_domain:
                        url_domain = url_domain.split(":")[0]
                    
                    # Only include if domain exactly matches base domain or www.base_domain
                    # Skip all other subdomains
                    if url_domain != domain and url_domain != f"www.{domain}":
                        # This is a subdomain, skip it
                        continue
                
                # Add URL with timestamp
                urls.append({
                    "url": original_url,
                    "date": timestamp,
                    "archive_url": snapshot.archive_url
                })
                
                # Limit results to prevent excessive memory usage
                if snapshot_count >= 10000:  # Reasonable limit
                    safe_log_info(logger, f"[waybackurls_search] Reached limit of 10000 snapshots", domain=domain)
                    break
            
        except Exception as e:
            error_msg = f"Waybackpy failed: {str(e)}"
            safe_log_error(logger, error_msg, exc_info=True, user_id=user_id)
            return json.dumps({"status": "error", "message": error_msg, "user_id": user_id})
        
        # Return results as JSON
        result_data = {
            "status": "success",
            "domain": domain,
            "no_subs": no_subs,
            "dates": dates,
            "get_versions": get_versions,
            "urls": urls,
            "count": len(urls),
            "user_id": user_id,
            "note": "Raw URLs returned verbatim from Wayback Machine using waybackpy Python package"
        }
        
        safe_log_info(logger, f"[waybackurls_search] Complete", domain=domain, urls_found=len(urls))
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        # Get user_id from runtime if available
        user_id = ""
        try:
            if runtime and runtime.state:
                user_id = runtime.state.get("user_id", "")
        except:
            pass
        safe_log_error(logger, f"[waybackurls_search] Error: {str(e)}", exc_info=True, user_id=user_id)
        return json.dumps({"status": "error", "message": f"Waybackurls search failed: {str(e)}", "user_id": user_id})
