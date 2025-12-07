"""
Crawl4AI Tool for CrewAI Agents

Advanced web crawling and content extraction using Crawl4AI API service.
This tool provides intelligent web scraping with JavaScript execution, CSS selectors,
structured extraction, LLM-based extraction, and screenshot capabilities.

Reference: https://github.com/unclecode/crawl4ai
"""

import os
import json
import time
import requests
from typing import Any, Optional, Dict, List, Literal
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug

logger = setup_logger(__name__, log_file_path="logs/crawl4ai_tool.log")


def _get_crawl4ai_url() -> str:
    """Get Crawl4AI API URL from environment variable."""
    # Check both CRAWL4AI_URL and CRAWL4AI_BASE_URL for compatibility
    url = os.getenv("CRAWL4AI_URL") or os.getenv("CRAWL4AI_BASE_URL", "http://localhost:11235")
    return url.rstrip("/")


def _get_crawl4ai_token() -> Optional[str]:
    """Get Crawl4AI API token from environment variable."""
    return os.getenv("CRAWL4AI_API_TOKEN")


def _build_headers(api_token: Optional[str] = None) -> Dict[str, str]:
    """Build request headers with optional API token."""
    headers = {"Content-Type": "application/json"}
    token = api_token or _get_crawl4ai_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class Crawl4AIToolSchema(BaseModel):
    """Input schema for Crawl4AITool."""
    url: str = Field(..., description="The URL to crawl. Must include protocol (http:// or https://). Example: 'https://www.example.com/page'")
    mode: Literal["direct", "sync", "async"] = Field(default="direct", description="Execution mode: 'direct' (immediate, fastest), 'sync' (waits for completion), 'async' (polls for result)")
    priority: int = Field(default=10, ge=1, le=10, description="Task priority (1-10, default: 10). Higher priority tasks execute first.")
    session_id: Optional[str] = Field(default=None, description="Optional session ID for maintaining browser state across requests")
    js_code: Optional[List[str]] = Field(default=None, description="Optional list of JavaScript code snippets to execute before scraping. Example: ['document.querySelector(\".load-more\").click()']")
    wait_for: Optional[str] = Field(default=None, description="Optional CSS selector to wait for before scraping. Example: 'article.content'")
    css_selector: Optional[str] = Field(default=None, description="Optional CSS selector to extract specific elements. Example: '.article-content'")
    extraction_config: Optional[Dict[str, Any]] = Field(default=None, description="Optional extraction configuration for structured data. Types: 'json_css', 'llm', 'cosine'")
    screenshot: bool = Field(default=False, description="If True, capture a screenshot of the page")
    crawler_params: Optional[Dict[str, Any]] = Field(default=None, description="Optional crawler parameters (headless, word_count_threshold, etc.)")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra parameters for advanced configuration")
    cache_mode: Optional[Literal["enabled", "disabled", "bypass", "read_only", "write_only"]] = Field(default=None, description="Optional cache mode")
    timeout: int = Field(default=30, ge=10, le=600, description="Maximum time to wait for completion in seconds (10-600, default: 30)")


class Crawl4AITool(BaseTool):
    """Tool for advanced web crawling and content extraction using Crawl4AI API service."""
    
    name: str = "Crawl4AI_Web_Crawler"
    description: str = (
        "Advanced web crawling and content extraction with JavaScript execution, CSS selectors, "
        "structured extraction, LLM-based extraction, and screenshot capabilities. "
        "Use this tool to scrape dynamic websites, extract structured data, capture screenshots, "
        "and interact with JavaScript-heavy pages. "
        "IMPORTANT: Provide full URLs with http:// or https:// protocol. "
        "Best for: dynamic websites, structured data extraction, JavaScript-heavy pages, screenshots. "
        "NOT suitable for: authenticated sites, very large pages, or sites that block automated access."
    )
    args_schema: type[BaseModel] = Crawl4AIToolSchema
    
    def _run(
        self,
        url: str,
        mode: Literal["direct", "sync", "async"] = "direct",
        priority: int = 10,
        session_id: Optional[str] = None,
        js_code: Optional[List[str]] = None,
        wait_for: Optional[str] = None,
        css_selector: Optional[str] = None,
        extraction_config: Optional[Dict[str, Any]] = None,
        screenshot: bool = False,
        crawler_params: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        cache_mode: Optional[Literal["enabled", "disabled", "bypass", "read_only", "write_only"]] = None,
        timeout: int = 30,  # Reduced default timeout for faster responses
        **kwargs: Any
    ) -> str:
        """Execute Crawl4AI web crawl."""
        try:
            safe_log_info(logger, f"[Crawl4AITool] Starting", url=url, mode=mode, priority=priority)
            
            # Validate URL
            if not url or not isinstance(url, str) or len(url.strip()) == 0:
                error_msg = "url must be a non-empty string"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            url = url.strip()
            if not url.startswith(("http://", "https://")):
                error_msg = "url must include protocol (http:// or https://)"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            # Get Crawl4AI URL from environment
            base_url = _get_crawl4ai_url()
            
            # Build request payload
            # API expects urls as a list, not a string
            request_data: Dict[str, Any] = {
                "urls": [url],  # Must be a list
                "priority": priority
            }
            
            if session_id:
                request_data["session_id"] = session_id
            if js_code:
                request_data["js_code"] = js_code
            if wait_for:
                request_data["wait_for"] = wait_for
            if css_selector:
                request_data["css_selector"] = css_selector
            if extraction_config:
                request_data["extraction_config"] = extraction_config
            if screenshot:
                request_data["screenshot"] = True
            if crawler_params:
                request_data["crawler_params"] = crawler_params
            if extra:
                request_data["extra"] = extra
            if cache_mode:
                request_data["cache_mode"] = cache_mode
            
            headers = _build_headers()
            
            # Execute based on mode
            # Note: The API only has /crawl endpoint which returns results directly
            # /crawl_direct and /crawl_sync don't exist in this API version
            # All modes use /crawl endpoint which returns results synchronously
            endpoint = f"{base_url}/crawl"
            safe_log_debug(logger, f"[Crawl4AITool] Using /crawl endpoint", endpoint=endpoint, mode=mode)
            
            try:
                response = requests.post(endpoint, json=request_data, headers=headers, timeout=timeout)
                
                if response.status_code == 403:
                    error_msg = "API token is invalid or missing"
                    safe_log_error(logger, f"[Crawl4AITool] {error_msg}", url=url)
                    return json.dumps({"status": "error", "message": error_msg})
                
                response.raise_for_status()
                result = response.json()
                
                # API returns: {"success": true, "results": [{"url": "...", "markdown": "...", ...}]}
                success = result.get("success", False)
                results = result.get("results", [])
                
                safe_log_info(logger, f"[Crawl4AITool] Crawl complete", 
                             url=url, mode=mode, success=success, results_count=len(results))
                
                result_data = {
                    "status": "success",
                    "url": url,
                    "mode": mode,
                    "raw_response": result,  # Return raw API response verbatim
                    "note": "Raw API response returned verbatim - no parsing applied"
                }
                return json.dumps(result_data, indent=2)
                
            except requests.exceptions.Timeout:
                error_msg = f"Request timeout after {timeout} seconds"
                safe_log_error(logger, f"[Crawl4AITool] {error_msg}", url=url)
                return json.dumps({"status": "error", "message": error_msg})
            except requests.exceptions.HTTPError as e:
                if hasattr(e, 'response') and e.response is not None:
                    error_text = e.response.text[:200] if e.response.text else "No error details"
                    error_msg = f"HTTP error {e.response.status_code}: {error_text}"
                else:
                    error_msg = f"HTTP error: {str(e)}"
                safe_log_error(logger, f"[Crawl4AITool] {error_msg}", url=url)
                return json.dumps({"status": "error", "message": error_msg})
            except requests.exceptions.RequestException as e:
                error_msg = f"Connection error: {str(e)}"
                safe_log_error(logger, f"[Crawl4AITool] {error_msg}", url=url, exc_info=True)
                return json.dumps({"status": "error", "message": error_msg})
            
        except Exception as e:
            error_msg = f"Unexpected error in Crawl4AITool: {str(e)}"
            safe_log_error(logger, f"[Crawl4AITool] {error_msg}", url=url, exc_info=True)
            return json.dumps({"status": "error", "message": error_msg})

