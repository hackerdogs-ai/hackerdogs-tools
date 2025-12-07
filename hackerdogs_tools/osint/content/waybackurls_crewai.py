"""
Waybackurls Tool for CrewAI Agents

Fetch URLs from Wayback Machine using waybackpy Python package.
This tool queries the Wayback Machine to retrieve historical URLs for a given domain.

Reference: https://github.com/akamhy/waybackpy
"""

import json
from typing import Any, Optional
from urllib.parse import urlparse
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug
from waybackpy import WaybackMachineCDXServerAPI

logger = setup_logger(__name__, log_file_path="logs/waybackurls_tool.log")


class WaybackurlsToolSchema(BaseModel):
    """Input schema for WaybackurlsTool."""
    domain: str = Field(..., description="Domain name to fetch URLs for (e.g., 'example.com').")
    no_subs: bool = Field(default=False, description="If True, exclude subdomains (default: False).")
    dates: Optional[str] = Field(default=None, description="Optional date range filter in format 'YYYYMMDD-YYYYMMDD'.")
    get_versions: bool = Field(default=False, description="If True, list URLs for crawled versions of input URL(s) (default: False).")


class WaybackurlsTool(BaseTool):
    """Tool for fetching URLs from Wayback Machine."""
    
    name: str = "Waybackurls"
    description: str = (
        "Fetch URLs from Wayback Machine for a given domain. "
        "Use this tool to discover historical URLs, find deleted pages, and map website structure over time. "
        "IMPORTANT: Provide domain name without protocol (e.g., 'example.com', not 'https://example.com'). "
        "Best for: historical URL discovery, deleted page recovery, website structure mapping. "
        "Note: get_versions parameter is currently not implemented - all snapshots are returned."
    )
    args_schema: type[BaseModel] = WaybackurlsToolSchema
    
    def _run(
        self,
        domain: str,
        no_subs: bool = False,
        dates: Optional[str] = None,
        get_versions: bool = False,
        **kwargs: Any
    ) -> str:
        """Execute Waybackurls URL fetching."""
        try:
            # Get user_id from kwargs if available (CrewAI may pass it)
            user_id = kwargs.get("user_id", "") if kwargs else ""
            
            safe_log_info(logger, f"[WaybackurlsTool] Starting", domain=domain, no_subs=no_subs, dates=dates, get_versions=get_versions, user_id=user_id)
            
            # Validate inputs
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
                        safe_log_info(logger, f"[WaybackurlsTool] Reached limit of 10000 snapshots", domain=domain)
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
            
            safe_log_info(logger, f"[WaybackurlsTool] Complete", domain=domain, urls_found=len(urls))
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            # Get user_id from kwargs if available
            user_id = kwargs.get("user_id", "") if kwargs else ""
            safe_log_error(logger, f"[WaybackurlsTool] Error: {str(e)}", exc_info=True, user_id=user_id)
            return json.dumps({"status": "error", "message": f"Waybackurls failed: {str(e)}", "user_id": user_id})
