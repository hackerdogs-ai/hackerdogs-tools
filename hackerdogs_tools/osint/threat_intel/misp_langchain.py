"""
MISP Tool for LangChain Agents

Query MISP threat intelligence platform
"""

import json
import os
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/misp_tool.log")

# Import MISP SDK
try:
    from pymisp import ExpandedPyMISP  # type: ignore
    MISP_AVAILABLE = True
except ImportError:
    MISP_AVAILABLE = False


class MISPSecurityAgentState(AgentState):
    """Extended agent state for MISP operations."""
    user_id: str = ""


@tool
def misp_search(
    runtime: ToolRuntime,
    query: str,
    query_type: str = "indicator",
    limit: int = 100
) -> str:
    """
    Query MISP threat intelligence platform.
    
    Search for indicators, events, attributes, and tags in your MISP instance.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        query: Search query (indicator, tag, etc.)
        query_type: Type of query (indicator, event, attribute, tag)
        limit: Result limit (1-1000)
    
    Returns:
        JSON string with MISP search results.
    """
    try:
        safe_log_info(logger, f"[misp_search] Starting", query=query, query_type=query_type, limit=limit)
        
        # Validate inputs
        if not query or not isinstance(query, str):
            error_msg = "Invalid query provided"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if query_type not in ["indicator", "event", "attribute", "tag"]:
            error_msg = f"Invalid query_type: {query_type}. Must be: indicator, event, attribute, or tag"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if limit < 1 or limit > 1000:
            error_msg = "Limit must be between 1 and 1000"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not MISP_AVAILABLE:
            error_msg = (
                "pymisp not available. Install with: pip install pymisp\n"
                "MISP_URL and MISP_API_KEY environment variables are required"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        misp_url = os.getenv("MISP_URL", "")
        misp_key = os.getenv("MISP_API_KEY", "")
        
        if not misp_url or not misp_key:
            error_msg = (
                "MISP_URL and MISP_API_KEY environment variables are required. "
                "Set up your MISP instance URL and API key."
            )
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Create MISP client
        misp = ExpandedPyMISP(misp_url, misp_key, ssl=True)
        
        # Query based on type
        if query_type == "indicator":
            results = misp.search(controller="attributes", value=query, limit=limit)
        elif query_type == "event":
            results = misp.search(controller="events", eventinfo=query, limit=limit)
        elif query_type == "attribute":
            results = misp.search(controller="attributes", value=query, limit=limit)
        elif query_type == "tag":
            results = misp.search_tags(tagname=query)
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unsupported query type: {query_type}"
            })
        
        # Format results
        if isinstance(results, dict):
            events = results.get("Event", []) if "Event" in results else []
            attributes = results.get("Attribute", []) if "Attribute" in results else []
        elif isinstance(results, list):
            events = results
            attributes = []
        else:
            events = []
            attributes = []
        
        # Return raw API response verbatim - no parsing, no reformatting
        safe_log_info(logger, f"[misp_search] Complete", query=query, event_count=len(events))
        return json.dumps(results, indent=2, default=str)
        
    except Exception as e:
        safe_log_error(logger, f"[misp_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"MISP query failed: {str(e)}"})

