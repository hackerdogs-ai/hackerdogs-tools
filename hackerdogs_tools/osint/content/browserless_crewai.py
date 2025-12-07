"""
Browserless Tool for CrewAI Agents

Web scraping and browser automation using Browserless REST API service.
This tool provides comprehensive browser capabilities including content extraction,
screenshots, PDF generation, JavaScript execution, and bot detection bypass.

Reference: https://docs.browserless.io/rest-apis/intro
"""

import os
import json
import requests
from pathlib import Path
from typing import Any, Optional, Dict, Literal
from dotenv import load_dotenv
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug

# Load environment variables - same pattern as test_utils.py
# This will search from current working directory and parent directories
load_dotenv(override=True)

logger = setup_logger(__name__, log_file_path="logs/browserless_tool.log")


def _get_browserless_url() -> str:
    """Get Browserless API base URL from environment variable."""
    from urllib.parse import urlparse, urlunparse
    
    # Get URL from environment
    url = os.getenv("BROWSERLESS_URL", "http://localhost:3000")
    
    # Parse URL to extract base (protocol + host + port)
    # This handles both full endpoint URLs and base URLs
    parsed = urlparse(url)
    
    # Reconstruct base URL with only protocol, hostname, and port
    # Remove path, query, and fragment
    base_url = urlunparse((
        parsed.scheme,
        parsed.netloc,  # This includes hostname:port
        "",  # No path
        "",  # No params
        "",  # No query
        ""   # No fragment
    ))
    
    return base_url.rstrip("/")


def _get_browserless_token(**kwargs: Any) -> Optional[str]:
    """Get Browserless API token from kwargs (api_keys) or environment variable."""
    # First try to get from kwargs (CrewAI passes state through kwargs)
    if kwargs:
        api_keys_dict = kwargs.get("api_keys", {})
        if isinstance(api_keys_dict, dict):
            token = api_keys_dict.get("BROWSERLESS_API_KEY")
            if token:
                return token
    
    # Fall back to environment variable
    return os.getenv("BROWSERLESS_API_KEY") or os.getenv("BROWSERLESS_TOKEN")


def _build_headers() -> Dict[str, str]:
    """Build HTTP headers for Browserless API requests."""
    headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
    return headers


def _make_request(endpoint: str, payload: Dict[str, Any], timeout: int = 30, **kwargs: Any) -> Dict[str, Any]:
    """Make HTTP request to Browserless API."""
    base_url = _get_browserless_url()
    api_token = _get_browserless_token(**kwargs)
    
    # Build full endpoint URL
    # Endpoint should start with / (e.g., /content, /scrape)
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    
    url = f"{base_url}{endpoint}"
    
    # Add token as query parameter (Browserless REST API uses ?token=...)
    if api_token:
        if "?" in url:
            url = f"{url}&token={api_token}"
        else:
            url = f"{url}?token={api_token}"
    
    headers = _build_headers()
    
    safe_log_debug(logger, f"[_make_request] Making request", url=url, endpoint=endpoint, has_token=bool(api_token))
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        
        if response.status_code == 403:
            raise ValueError("API token is invalid or missing")
        
        response.raise_for_status()
        # Handle empty responses or non-JSON responses
        if not response.content:
            return {}
        try:
            return response.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            # If response is not JSON, return as text
            return {"raw_text": response.text}
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Request timeout after {timeout} seconds")
    except requests.exceptions.HTTPError as e:
        if hasattr(e, 'response') and e.response is not None:
            error_text = e.response.text[:200] if e.response.text else "No error details"
            error_msg = f"HTTP error {e.response.status_code}: {error_text}"
        else:
            error_msg = f"HTTP error: {str(e)}"
        raise ValueError(error_msg)
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Connection error: {str(e)}")


class BrowserlessContentToolSchema(BaseModel):
    """Input schema for BrowserlessContentTool."""
    url: str = Field(..., description="The URL to extract content from. Must include protocol (http:// or https://).")
    wait_for: Optional[str] = Field(default=None, description="Optional CSS selector to wait for before extracting content.")
    timeout: int = Field(default=30, ge=10, le=300, description="Maximum time to wait in seconds (10-300, default: 30).")


class BrowserlessContentTool(BaseTool):
    """Tool for extracting content from web pages using Browserless /content endpoint."""
    
    name: str = "Browserless_Content"
    description: str = (
        "Extract HTML content from a web page. "
        "Use this tool to fetch content from URLs without JavaScript execution. "
        "IMPORTANT: Provide full URLs with http:// or https:// protocol. "
        "Best for: simple content extraction, static HTML pages. "
        "NOT suitable for: JavaScript-heavy pages, dynamic content."
    )
    args_schema: type[BaseModel] = BrowserlessContentToolSchema
    
    def _run(self, url: str, wait_for: Optional[str] = None, timeout: int = 30, **kwargs: Any) -> str:
        """Execute Browserless content extraction."""
        try:
            safe_log_info(logger, f"[BrowserlessContentTool] Starting", url=url)
            
            if not url or not url.startswith(("http://", "https://")):
                error_msg = "url must include protocol (http:// or https://)"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            payload = {"url": url.strip()}
            if wait_for:
                payload["waitFor"] = wait_for
            
            result = _make_request("/content", payload, timeout, **kwargs)
            
            # Get user_id from kwargs if available (CrewAI may pass it)
            user_id = kwargs.get("user_id", "") if kwargs else ""
            
            result_data = {
                "status": "success",
                "url": url,
                "endpoint": "/content",
                "raw_response": result,
                "user_id": user_id,
                "note": "Raw API response returned verbatim - no parsing applied"
            }
            
            safe_log_info(logger, f"[BrowserlessContentTool] Complete", url=url)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            error_msg = f"Error in BrowserlessContentTool: {str(e)}"
            safe_log_error(logger, error_msg, url=url, exc_info=True)
            return json.dumps({"status": "error", "message": error_msg})


class BrowserlessScrapeToolSchema(BaseModel):
    """Input schema for BrowserlessScrapeTool."""
    url: str = Field(..., description="The URL to scrape. Must include protocol (http:// or https://).")
    selector: Optional[str] = Field(default=None, description="Optional CSS selector to extract specific elements.")
    wait_for: Optional[str] = Field(default=None, description="Optional CSS selector to wait for before scraping.")
    timeout: int = Field(default=30, ge=10, le=300, description="Maximum time to wait in seconds (10-300, default: 30).")


class BrowserlessScrapeTool(BaseTool):
    """Tool for scraping structured data from web pages using Browserless /scrape endpoint."""
    
    name: str = "Browserless_Scrape"
    description: str = (
        "Scrape structured data from a web page using CSS selectors. "
        "Use this tool to extract specific elements from web pages. "
        "IMPORTANT: Provide full URLs with http:// or https:// protocol. "
        "Best for: structured data extraction, specific element selection. "
        "NOT suitable for: complex nested structures, authenticated sites."
    )
    args_schema: type[BaseModel] = BrowserlessScrapeToolSchema
    
    def _run(self, url: str, selector: Optional[str] = None, wait_for: Optional[str] = None, timeout: int = 30, **kwargs: Any) -> str:
        """Execute Browserless scraping."""
        try:
            safe_log_info(logger, f"[BrowserlessScrapeTool] Starting", url=url, selector=selector)
            
            if not url or not url.startswith(("http://", "https://")):
                error_msg = "url must include protocol (http:// or https://)"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            payload = {"url": url.strip()}
            # Browserless API expects "elements" array, not "selector" string
            if selector:
                # Convert selector string to elements array format
                # e.g., "h1, h2, h3" -> [{"selector": "h1"}, {"selector": "h2"}, {"selector": "h3"}]
                selectors = [s.strip() for s in selector.split(",")]
                payload["elements"] = [{"selector": s} for s in selectors if s]
            if wait_for:
                payload["waitFor"] = wait_for
            
            result = _make_request("/scrape", payload, timeout, **kwargs)
            
            # Get user_id from kwargs if available (CrewAI may pass it)
            user_id = kwargs.get("user_id", "") if kwargs else ""
            
            result_data = {
                "status": "success",
                "url": url,
                "endpoint": "/scrape",
                "raw_response": result,
                "user_id": user_id,
                "note": "Raw API response returned verbatim - no parsing applied"
            }
            
            safe_log_info(logger, f"[BrowserlessScrapeTool] Complete", url=url)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            error_msg = f"Error in BrowserlessScrapeTool: {str(e)}"
            safe_log_error(logger, error_msg, url=url, exc_info=True)
            return json.dumps({"status": "error", "message": error_msg})


class BrowserlessScreenshotToolSchema(BaseModel):
    """Input schema for BrowserlessScreenshotTool."""
    url: str = Field(..., description="The URL to screenshot. Must include protocol (http:// or https://).")
    wait_for: Optional[str] = Field(default=None, description="Optional CSS selector to wait for before taking screenshot.")
    full_page: bool = Field(default=False, description="If True, capture full page screenshot.")
    timeout: int = Field(default=30, ge=10, le=300, description="Maximum time to wait in seconds (10-300, default: 30).")


class BrowserlessScreenshotTool(BaseTool):
    """Tool for capturing screenshots using Browserless /screenshot endpoint."""
    
    name: str = "Browserless_Screenshot"
    description: str = (
        "Capture a screenshot of a web page. "
        "Use this tool to take screenshots of web pages for documentation or analysis. "
        "IMPORTANT: Provide full URLs with http:// or https:// protocol. "
        "Best for: visual documentation, page verification, visual analysis."
    )
    args_schema: type[BaseModel] = BrowserlessScreenshotToolSchema
    
    def _run(self, url: str, wait_for: Optional[str] = None, full_page: bool = False, timeout: int = 30, **kwargs: Any) -> str:
        """Execute Browserless screenshot capture."""
        try:
            safe_log_info(logger, f"[BrowserlessScreenshotTool] Starting", url=url, full_page=full_page)
            
            if not url or not url.startswith(("http://", "https://")):
                error_msg = "url must include protocol (http:// or https://)"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            payload = {"url": url.strip(), "options": {"fullPage": full_page}}
            if wait_for:
                payload["waitFor"] = wait_for
            
            result = _make_request("/screenshot", payload, timeout, **kwargs)
            
            # Get user_id from kwargs if available (CrewAI may pass it)
            user_id = kwargs.get("user_id", "") if kwargs else ""
            
            result_data = {
                "status": "success",
                "url": url,
                "endpoint": "/screenshot",
                "raw_response": result,
                "user_id": user_id,
                "note": "Raw API response returned verbatim - no parsing applied"
            }
            
            safe_log_info(logger, f"[BrowserlessScreenshotTool] Complete", url=url)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            error_msg = f"Error in BrowserlessScreenshotTool: {str(e)}"
            safe_log_error(logger, error_msg, url=url, exc_info=True)
            return json.dumps({"status": "error", "message": error_msg})


class BrowserlessPDFToolSchema(BaseModel):
    """Input schema for BrowserlessPDFTool."""
    url: str = Field(..., description="The URL to convert to PDF. Must include protocol (http:// or https://).")
    wait_for: Optional[str] = Field(default=None, description="Optional CSS selector to wait for before generating PDF.")
    format: str = Field(default="A4", description="PDF format (default: 'A4'). Options: 'A4', 'Letter', etc.")
    timeout: int = Field(default=30, ge=10, le=300, description="Maximum time to wait in seconds (10-300, default: 30).")


class BrowserlessPDFTool(BaseTool):
    """Tool for generating PDFs from web pages using Browserless /pdf endpoint."""
    
    name: str = "Browserless_PDF"
    description: str = (
        "Generate a PDF from a web page. "
        "Use this tool to convert web pages to PDF format for archiving or sharing. "
        "IMPORTANT: Provide full URLs with http:// or https:// protocol. "
        "Best for: document archiving, PDF generation, page preservation."
    )
    args_schema: type[BaseModel] = BrowserlessPDFToolSchema
    
    def _run(self, url: str, wait_for: Optional[str] = None, format: str = "A4", timeout: int = 30, **kwargs: Any) -> str:
        """Execute Browserless PDF generation."""
        try:
            safe_log_info(logger, f"[BrowserlessPDFTool] Starting", url=url, format=format)
            
            if not url or not url.startswith(("http://", "https://")):
                error_msg = "url must include protocol (http:// or https://)"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            payload = {"url": url.strip(), "options": {"format": format}}
            if wait_for:
                payload["waitFor"] = wait_for
            
            result = _make_request("/pdf", payload, timeout, **kwargs)
            
            # Get user_id from kwargs if available (CrewAI may pass it)
            user_id = kwargs.get("user_id", "") if kwargs else ""
            
            result_data = {
                "status": "success",
                "url": url,
                "endpoint": "/pdf",
                "raw_response": result,
                "user_id": user_id,
                "note": "Raw API response returned verbatim - no parsing applied"
            }
            
            safe_log_info(logger, f"[BrowserlessPDFTool] Complete", url=url)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            error_msg = f"Error in BrowserlessPDFTool: {str(e)}"
            safe_log_error(logger, error_msg, url=url, exc_info=True)
            return json.dumps({"status": "error", "message": error_msg})


class BrowserlessFunctionToolSchema(BaseModel):
    """Input schema for BrowserlessFunctionTool."""
    url: str = Field(..., description="The URL to execute function on. Must include protocol (http:// or https://).")
    function: str = Field(..., description="JavaScript function code to execute. Should return a value.")
    wait_for: Optional[str] = Field(default=None, description="Optional CSS selector to wait for before executing function.")
    timeout: int = Field(default=30, ge=10, le=300, description="Maximum time to wait in seconds (10-300, default: 30).")


class BrowserlessFunctionTool(BaseTool):
    """Tool for executing JavaScript functions on web pages using Browserless /function endpoint."""
    
    name: str = "Browserless_Function"
    description: str = (
        "Execute a JavaScript function on a web page. "
        "Use this tool to run custom JavaScript code and extract dynamic data. "
        "IMPORTANT: Provide full URLs with http:// or https:// protocol. "
        "Best for: dynamic content extraction, custom JavaScript execution, interactive pages."
    )
    args_schema: type[BaseModel] = BrowserlessFunctionToolSchema
    
    def _run(self, url: str, function: str, wait_for: Optional[str] = None, timeout: int = 30, **kwargs: Any) -> str:
        """Execute Browserless JavaScript function."""
        try:
            safe_log_info(logger, f"[BrowserlessFunctionTool] Starting", url=url)
            
            if not url or not url.startswith(("http://", "https://")):
                error_msg = "url must include protocol (http:// or https://)"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            if not function:
                error_msg = "function parameter is required"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            payload = {"url": url.strip(), "function": function}
            if wait_for:
                payload["waitFor"] = wait_for
            
            result = _make_request("/function", payload, timeout, **kwargs)
            
            # Get user_id from kwargs if available (CrewAI may pass it)
            user_id = kwargs.get("user_id", "") if kwargs else ""
            
            result_data = {
                "status": "success",
                "url": url,
                "endpoint": "/function",
                "raw_response": result,
                "user_id": user_id,
                "note": "Raw API response returned verbatim - no parsing applied"
            }
            
            safe_log_info(logger, f"[BrowserlessFunctionTool] Complete", url=url)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            error_msg = f"Error in BrowserlessFunctionTool: {str(e)}"
            safe_log_error(logger, error_msg, url=url, exc_info=True)
            return json.dumps({"status": "error", "message": error_msg})


class BrowserlessUnblockToolSchema(BaseModel):
    """Input schema for BrowserlessUnblockTool."""
    url: str = Field(..., description="The URL to unblock. Must include protocol (http:// or https://).")
    wait_for: Optional[str] = Field(default=None, description="Optional CSS selector to wait for after unblocking.")
    timeout: int = Field(default=60, ge=10, le=300, description="Maximum time to wait in seconds (10-300, default: 60).")


class BrowserlessUnblockTool(BaseTool):
    """Tool for bypassing bot detection using Browserless /unblock endpoint."""
    
    name: str = "Browserless_Unblock"
    description: str = (
        "Bypass bot detection and unblock a website. "
        "Use this tool when regular scraping fails due to Cloudflare or other bot detection systems. "
        "IMPORTANT: Provide full URLs with http:// or https:// protocol. "
        "Best for: Cloudflare-protected sites, bot-detected pages, blocked access."
    )
    args_schema: type[BaseModel] = BrowserlessUnblockToolSchema
    
    def _run(self, url: str, wait_for: Optional[str] = None, timeout: int = 60, **kwargs: Any) -> str:
        """Execute Browserless unblock."""
        try:
            safe_log_info(logger, f"[BrowserlessUnblockTool] Starting", url=url)
            
            if not url or not url.startswith(("http://", "https://")):
                error_msg = "url must include protocol (http:// or https://)"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            
            payload = {"url": url.strip()}
            if wait_for:
                payload["waitFor"] = wait_for
            
            result = _make_request("/unblock", payload, timeout, **kwargs)
            
            # Get user_id from kwargs if available (CrewAI may pass it)
            user_id = kwargs.get("user_id", "") if kwargs else ""
            
            result_data = {
                "status": "success",
                "url": url,
                "endpoint": "/unblock",
                "raw_response": result,
                "user_id": user_id,
                "note": "Raw API response returned verbatim - no parsing applied"
            }
            
            safe_log_info(logger, f"[BrowserlessUnblockTool] Complete", url=url)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            error_msg = f"Error in BrowserlessUnblockTool: {str(e)}"
            safe_log_error(logger, error_msg, url=url, exc_info=True)
            return json.dumps({"status": "error", "message": error_msg})

