"""
Crawl4AI Tool for LangChain Agents

Advanced web crawling and content extraction using Crawl4AI API service.
This tool provides intelligent web scraping with JavaScript execution, CSS selectors,
structured extraction, LLM-based extraction, and screenshot capabilities.

Reference: https://github.com/unclecode/crawl4ai

Key Features:
- JavaScript execution support for dynamic content
- CSS selector-based content extraction
- Structured data extraction (JSON-CSS, LLM-based)
- Screenshot capture
- Multiple crawl modes (direct, sync, async)
- User tracking and audit logging via agent state

Usage:
    from langchain.agents import create_agent
    from hackerdogs_tools.osint.content.crawl4ai_langchain import crawl4ai_crawl
    
    agent = create_agent(
        model=llm,
        tools=[crawl4ai_crawl],
        system_prompt="You are a web scraping specialist..."
    )
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": "Crawl https://example.com"}],
        "user_id": "analyst_001"
    })
"""

import os
import json
import time
import requests
from typing import Optional, Dict, Any, List, Literal
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug

logger = setup_logger(__name__, log_file_path="logs/crawl4ai_tool.log")


class Crawl4AISecurityAgentState(AgentState):
    """Extended agent state for Crawl4AI operations."""
    user_id: str = ""


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


@tool
def crawl4ai_crawl(
    runtime: ToolRuntime,
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
    """
    Crawl a website using Crawl4AI API service with advanced extraction capabilities.
    
    This tool provides intelligent web scraping with support for:
    - JavaScript execution for dynamic content
    - CSS selector-based content filtering
    - Structured data extraction (JSON-CSS, LLM-based, cosine similarity)
    - Screenshot capture
    - Multiple execution modes (direct, sync, async)
    
    When to use:
        - Need to scrape dynamic websites with JavaScript rendering
        - Extract structured data from web pages
        - Capture screenshots of web pages
        - Scrape content that requires interaction (click buttons, wait for elements)
        - Extract specific elements using CSS selectors
        - Use LLM-based extraction for complex data structures
    
    When NOT to use:
        - Simple static HTML scraping (use browserless_tool instead)
        - Websites requiring authentication/login
        - Very large websites or pages (may timeout)
        - Websites that block automated access
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        url: The URL to crawl. Must include protocol (http:// or https://).
            Example: "https://www.example.com/page"
        mode: Execution mode:
            - "direct": Immediate execution, returns result directly (default, fastest)
            - "sync": Synchronous execution, waits for completion (good for medium pages)
            - "async": Asynchronous execution with polling (best for long-running crawls)
        priority: Task priority (1-10, default: 10). Higher priority tasks execute first.
        session_id: Optional session ID for maintaining browser state across requests.
        js_code: Optional list of JavaScript code snippets to execute before scraping.
            Example: ["document.querySelector('.load-more').click()"]
        wait_for: Optional CSS selector to wait for before scraping.
            Example: "article.content" (waits for this element to appear)
        css_selector: Optional CSS selector to extract specific elements.
            Example: ".article-content" (only extracts matching elements)
        extraction_config: Optional extraction configuration for structured data:
            - Type "json_css": Extract structured data using CSS selectors
            - Type "llm": Use LLM to extract structured data
            - Type "cosine": Semantic similarity-based extraction
            Example: {"type": "json_css", "params": {"schema": {...}}}
        screenshot: If True, capture a screenshot of the page (default: False).
        crawler_params: Optional crawler parameters (headless, word_count_threshold, etc.).
        extra: Optional extra parameters for advanced configuration.
        cache_mode: Optional cache mode: "enabled", "disabled", "bypass", "read_only", "write_only".
        timeout: Maximum time to wait for completion in seconds (default: 300).
    
    Returns:
        JSON string containing:
        {
            "status": "success" | "error",
            "url": str,
            "mode": str,
            "result": {
                "success": bool,
                "markdown": str (extracted content in markdown),
                "extracted_content": str (structured data if extraction_config provided),
                "screenshot": str (base64-encoded if screenshot=True),
                "url": str (final URL after redirects),
                "status_code": int (HTTP status code)
            },
            "user_id": str
        }
    
    Errors:
        - "Crawl4AI URL not configured" - CRAWL4AI_URL environment variable not set
        - "Request timeout" - Crawl did not complete within timeout
        - "API error {code}" - Crawl4AI API returned an error
        - "Connection error" - Failed to connect to Crawl4AI service
    
    Example:
        User: "Crawl https://example.com and extract all article titles"
        Tool call: crawl4ai_crawl(
            url="https://example.com",
            css_selector=".article-title"
        )
        Returns: JSON with markdown content and extracted titles
    """
    try:
        safe_log_info(logger, f"[crawl4ai_crawl] Starting", url=url, mode=mode, priority=priority)
        
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
        safe_log_debug(logger, f"[crawl4ai_crawl] Using /crawl endpoint", endpoint=endpoint, mode=mode)
        
        try:
            response = requests.post(endpoint, json=request_data, headers=headers, timeout=timeout)
            
            if response.status_code == 403:
                error_msg = "API token is invalid or missing"
                safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url)
                return json.dumps({"status": "error", "message": error_msg})
            
            response.raise_for_status()
            result = response.json()
            
            # API returns: {"success": true, "results": [{"url": "...", "markdown": "...", ...}]}
            success = result.get("success", False)
            results = result.get("results", [])
            
            safe_log_info(logger, f"[crawl4ai_crawl] Crawl complete", 
                         url=url, mode=mode, success=success, results_count=len(results))
            
            result_data = {
                "status": "success",
                "url": url,
                "mode": mode,
                "raw_response": result,  # Return raw API response verbatim
                "user_id": runtime.state.get("user_id", ""),
                "note": "Raw API response returned verbatim - no parsing applied"
            }
            return json.dumps(result_data, indent=2)
            
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {timeout} seconds"
            safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url)
            return json.dumps({"status": "error", "message": error_msg})
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                error_text = e.response.text[:200] if e.response.text else "No error details"
                error_msg = f"HTTP error {e.response.status_code}: {error_text}"
            else:
                error_msg = f"HTTP error: {str(e)}"
            safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url)
            return json.dumps({"status": "error", "message": error_msg})
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection error: {str(e)}"
            safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url, exc_info=True)
            return json.dumps({"status": "error", "message": error_msg})
        
    except Exception as e:
        error_msg = f"Unexpected error in crawl4ai_crawl: {str(e)}"
        safe_log_error(logger, f"[crawl4ai_crawl] {error_msg}", url=url, exc_info=True)
        return json.dumps({"status": "error", "message": error_msg})

