"""
MISP Tool for CrewAI Agents

This module provides CrewAI tools for querying MISP threat intelligence platform.
"""

import json
import os
from typing import Any, Optional, List
from crewai.tools import BaseTool, EnvVar
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


class MISPToolSchema(BaseModel):
    """Input schema for MISPTool."""
    query: str = Field(..., description="Search query (indicator, tag, etc.)")
    query_type: str = Field(
        default="indicator",
        description="Type: 'indicator', 'event', 'attribute', 'tag'"
    )
    limit: int = Field(default=100, ge=1, le=1000, description="Result limit (1-1000)")


class MISPTool(BaseTool):
    """Tool for querying MISP threat intelligence platform."""
    
    name: str = "MISP Threat Intelligence"
    description: str = (
        "Query MISP (Malware Information Sharing Platform) for threat intelligence. "
        "Search for indicators, events, attributes, and tags in your MISP instance."
    )
    args_schema: type[BaseModel] = MISPToolSchema
    
    env_vars: list[EnvVar] = [
        EnvVar(
            name="MISP_URL",
            description="MISP instance URL (e.g., https://misp.example.com)",
            required=True,
        ),
        EnvVar(
            name="MISP_API_KEY",
            description="MISP API key",
            required=True,
        ),
    ]
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if not MISP_AVAILABLE:
            raise ImportError(
                "pymisp not available. Install with: pip install pymisp"
            )
        
        misp_url = os.getenv("MISP_URL")
        misp_key = os.getenv("MISP_API_KEY")
        
        if not misp_url or not misp_key:
            raise ValueError(
                "MISP_URL and MISP_API_KEY environment variables are required"
            )
    
    def _run(
        self,
        query: str,
        query_type: str = "indicator",
        limit: int = 100,
        **kwargs: Any
    ) -> str:
        """Execute MISP query."""
        try:
            safe_log_info(logger, f"[MISPTool] Querying", query=query, type=query_type)
            
            misp_url = os.getenv("MISP_URL", "")
            misp_key = os.getenv("MISP_API_KEY", "")
            
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
            
            result_data = {
                "status": "success",
                "query": query,
                "query_type": query_type,
                "event_count": len(events),
                "attribute_count": len(attributes),
                "events": events[:limit],
                "attributes": attributes[:limit]
            }
            
            safe_log_info(logger, f"[MISPTool] Query complete", 
                         query=query, event_count=result_data["event_count"])
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[MISPTool] Error: {str(e)}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

