"""
Browserless Tool for LangChain Agents

Web scraping and browser automation using Browserless REST API service.
This tool provides comprehensive browser capabilities including content extraction,
screenshots, PDF generation, JavaScript execution, and bot detection bypass.

Reference: https://docs.browserless.io/rest-apis/intro

Key Features:
- Content extraction from web pages
- Screenshot capture
- PDF generation
- JavaScript function execution
- Structured data scraping
- Bot detection bypass (/unblock)
- Performance metrics
- File downloads
- Session exports

Usage:
    from langchain.agents import create_agent
    from hackerdogs_tools.osint.content.browserless_langchain import (
        browserless_content,
        browserless_scrape,
        browserless_screenshot,
        browserless_pdf
    )
    
    agent = create_agent(
        model=llm,
        tools=[browserless_content, browserless_scrape, browserless_screenshot, browserless_pdf],
        system_prompt="You are a web scraping specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Extract content from https://example.com"}],
        "user_id": "analyst_001"
    })
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
from dotenv import load_dotenv
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug

# Load environment variables - same pattern as test_utils.py
# This will search from current working directory and parent directories
load_dotenv(override=True)

logger = setup_logger(__name__, log_file_path="logs/browserless_tool.log")


class BrowserlessSecurityAgentState(AgentState):
    """Extended agent state for Browserless operations."""
    user_id: str = ""


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


def _get_browserless_token(runtime: Optional[ToolRuntime] = None) -> Optional[str]:
    """Get Browserless API token from ToolRuntime state or environment variable."""
    # First try to get from ToolRuntime state (like virustotal)
    if runtime and runtime.state:
        api_keys_dict = runtime.state.get("api_keys", {})
        if isinstance(api_keys_dict, dict):
            token = api_keys_dict.get("BROWSERLESS_API_KEY")
            if token is None or token == "":
                token = api_keys_dict.get("API_KEY") or api_keys_dict.get("api_key") or os.getenv("BROWSERLESS_TOKEN")
            if token:
                return token
    
    # Fall back to environment variable
    return os.getenv("BROWSERLESS_API_KEY") or os.getenv("BROWSERLESS_TOKEN")


def _build_headers() -> Dict[str, str]:
    """Build HTTP headers for Browserless API requests."""
    headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
    return headers


def _make_request(endpoint: str, payload: Dict[str, Any], runtime: Optional[ToolRuntime] = None, timeout: int = 30) -> Dict[str, Any]:
    """Make HTTP request to Browserless API."""
    base_url = _get_browserless_url()
    api_token = _get_browserless_token(runtime)
    
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


@tool
def browserless_content(
    runtime: ToolRuntime,
    url: str,
    wait_for: Optional[str] = None,
    timeout: int = 30,
    **kwargs: Any
) -> str:
    """
    Extract content from a web page using Browserless /content endpoint.
    
    This tool fetches HTML content from a URL and returns it as text.
    Perfect for simple content extraction without JavaScript execution.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        url: The URL to extract content from. Must include protocol (http:// or https://).
        wait_for: Optional CSS selector to wait for before extracting content.
        timeout: Maximum time to wait in seconds (default: 30).
    
    Returns:
        JSON string with extracted content.
    """
    try:
        safe_log_info(logger, f"[browserless_content] Starting", url=url)
        
        if not url or not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        payload = {"url": url.strip()}
        if wait_for:
            payload["waitFor"] = wait_for
        
        result = _make_request("/content", payload, runtime, timeout)
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/content",
            "raw_response": result,
            "user_id": runtime.state.get("user_id", ""),
            "note": "Raw API response returned verbatim - no parsing applied"
        }
        
        safe_log_info(logger, f"[browserless_content] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_content: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def browserless_scrape(
    runtime: ToolRuntime,
    url: str,
    selector: Optional[str] = None,
    wait_for: Optional[str] = None,
    timeout: int = 30,
    **kwargs: Any
) -> str:
    """
    Scrape structured data from a web page using Browserless /scrape endpoint.
    
    This tool extracts structured data from web pages using CSS selectors.
    Returns JSON data matching the specified selectors.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        url: The URL to scrape. Must include protocol (http:// or https://).
        selector: Optional CSS selector to extract specific elements.
        wait_for: Optional CSS selector to wait for before scraping.
        timeout: Maximum time to wait in seconds (default: 30).
    
    Returns:
        JSON string with scraped data.
    """
    try:
        safe_log_info(logger, f"[browserless_scrape] Starting", url=url, selector=selector)
        
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
        
        result = _make_request("/scrape", payload, runtime, timeout)
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/scrape",
            "raw_response": result,
            "user_id": runtime.state.get("user_id", ""),
            "note": "Raw API response returned verbatim - no parsing applied"
        }
        
        safe_log_info(logger, f"[browserless_scrape] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_scrape: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def browserless_screenshot(
    runtime: ToolRuntime,
    url: str,
    wait_for: Optional[str] = None,
    full_page: bool = False,
    timeout: int = 30,
    **kwargs: Any
) -> str:
    """
    Capture a screenshot of a web page using Browserless /screenshot endpoint.
    
    This tool takes a screenshot of the specified URL and returns it as base64-encoded image.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        url: The URL to screenshot. Must include protocol (http:// or https://).
        wait_for: Optional CSS selector to wait for before taking screenshot.
        full_page: If True, capture full page screenshot (default: False).
        timeout: Maximum time to wait in seconds (default: 30).
    
    Returns:
        JSON string with base64-encoded screenshot.
    """
    try:
        safe_log_info(logger, f"[browserless_screenshot] Starting", url=url, full_page=full_page)
        
        if not url or not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        payload = {"url": url.strip(), "options": {"fullPage": full_page}}
        if wait_for:
            payload["waitFor"] = wait_for
        
        result = _make_request("/screenshot", payload, runtime, timeout)
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/screenshot",
            "raw_response": result,
            "user_id": runtime.state.get("user_id", ""),
            "note": "Raw API response returned verbatim - no parsing applied"
        }
        
        safe_log_info(logger, f"[browserless_screenshot] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_screenshot: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def browserless_pdf(
    runtime: ToolRuntime,
    url: str,
    wait_for: Optional[str] = None,
    format: str = "A4",
    timeout: int = 30,
    **kwargs: Any
) -> str:
    """
    Generate a PDF from a web page using Browserless /pdf endpoint.
    
    This tool converts a web page to PDF format and returns it as base64-encoded data.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        url: The URL to convert to PDF. Must include protocol (http:// or https://).
        wait_for: Optional CSS selector to wait for before generating PDF.
        format: PDF format (default: "A4"). Options: "A4", "Letter", etc.
        timeout: Maximum time to wait in seconds (default: 30).
    
    Returns:
        JSON string with base64-encoded PDF.
    """
    try:
        safe_log_info(logger, f"[browserless_pdf] Starting", url=url, format=format)
        
        if not url or not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        payload = {"url": url.strip(), "options": {"format": format}}
        if wait_for:
            payload["waitFor"] = wait_for
        
        result = _make_request("/pdf", payload, runtime, timeout)
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/pdf",
            "raw_response": result,
            "user_id": runtime.state.get("user_id", ""),
            "note": "Raw API response returned verbatim - no parsing applied"
        }
        
        safe_log_info(logger, f"[browserless_pdf] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_pdf: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def browserless_function(
    runtime: ToolRuntime,
    url: str,
    function: str,
    wait_for: Optional[str] = None,
    timeout: int = 30,
    **kwargs: Any
) -> str:
    """
    Execute a JavaScript function on a web page using Browserless /function endpoint.
    
    This tool allows you to run custom JavaScript code on a page and return the result.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        url: The URL to execute function on. Must include protocol (http:// or https://).
        function: JavaScript function code to execute. Should return a value.
        wait_for: Optional CSS selector to wait for before executing function.
        timeout: Maximum time to wait in seconds (default: 30).
    
    Returns:
        JSON string with function execution result.
    """
    try:
        safe_log_info(logger, f"[browserless_function] Starting", url=url)
        
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
        
        result = _make_request("/function", payload, runtime, timeout)
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/function",
            "raw_response": result,
            "user_id": runtime.state.get("user_id", ""),
            "note": "Raw API response returned verbatim - no parsing applied"
        }
        
        safe_log_info(logger, f"[browserless_function] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_function: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})


@tool
def browserless_unblock(
    runtime: ToolRuntime,
    url: str,
    wait_for: Optional[str] = None,
    timeout: int = 60,
    **kwargs: Any
) -> str:
    """
    Bypass bot detection and unblock a website using Browserless /unblock endpoint.
    
    This tool uses advanced techniques to bypass Cloudflare and other bot detection systems.
    Use this when regular scraping fails due to bot detection.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        url: The URL to unblock. Must include protocol (http:// or https://).
        wait_for: Optional CSS selector to wait for after unblocking.
        timeout: Maximum time to wait in seconds (default: 60, longer for unblock).
    
    Returns:
        JSON string with unblocked content.
    """
    try:
        safe_log_info(logger, f"[browserless_unblock] Starting", url=url)
        
        if not url or not url.startswith(("http://", "https://")):
            error_msg = "url must include protocol (http:// or https://)"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        payload = {"url": url.strip()}
        if wait_for:
            payload["waitFor"] = wait_for
        
        result = _make_request("/unblock", payload, runtime, timeout)
        
        result_data = {
            "status": "success",
            "url": url,
            "endpoint": "/unblock",
            "raw_response": result,
            "user_id": runtime.state.get("user_id", ""),
            "note": "Raw API response returned verbatim - no parsing applied"
        }
        
        safe_log_info(logger, f"[browserless_unblock] Complete", url=url)
        return json.dumps(result_data, indent=2)
        
    except Exception as e:
        error_msg = f"Error in browserless_unblock: {str(e)}"
        safe_log_error(logger, error_msg, url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})

