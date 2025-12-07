"""
onionsearch Tool for LangChain Agents

Scrape Dark Web search engines
"""

import json
import os
import csv
import io
from typing import Optional, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error

logger = setup_logger(__name__, log_file_path="logs/onionsearch_tool.log")


class OnionSearchSecurityAgentState(AgentState):
    """Extended agent state for OnionSearch operations."""
    user_id: str = ""


@tool
def onionsearch_search(
    runtime: ToolRuntime,
    query: str,
    engines: Optional[List[str]] = None,
    limit: int = 10,
    output_format: str = "csv"
) -> str:
    """
    Search Dark Web (.onion) search engines for URLs.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        query: Search query string.
        engines: Optional list of specific search engines to use (default: all).
        limit: Maximum number of pages per engine to load (default: 10).
        output_format: Output format - "csv" (default) or "json".
    
    Returns:
        CSV or JSON string with search results. Returns verbatim output from OnionSearch.
    """
    try:
        safe_log_info(logger, f"[onionsearch_search] Starting", query=query, engines=engines, limit=limit, output_format=output_format)
        
        # Validate inputs
        if not query or not isinstance(query, str) or len(query.strip()) == 0:
            error_msg = "query must be a non-empty string"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if limit < 1 or limit > 100:
            error_msg = "limit must be between 1 and 100"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if output_format not in ["csv", "json"]:
            error_msg = "output_format must be 'csv' or 'json'"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Check Docker availability (Docker-only execution)
        from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker
        docker_client = get_docker_client()
        
        if not docker_client or not docker_client.docker_available:
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Build command arguments
        # OnionSearch CLI: onionsearch "query" [options]
        args = [query]
        
        # Add Tor proxy (required for OnionSearch)
        # In Docker network, use service name; fallback to host IP if running on host
        tor_proxy = os.getenv("TOR_PROXY", "tor-proxy:9050")
        # If running on host (not in Docker), use 127.0.0.1:9050
        # If running in Docker network, use tor-proxy:9050 (service name)
        args.extend(["--proxy", tor_proxy])
        
        # Add limit
        args.extend(["--limit", str(limit)])
        
        # Add specific engines if provided
        if engines and len(engines) > 0:
            args.extend(["--engines"] + engines)
        
        # Output to stdout (use - to write to stdout instead of file)
        args.extend(["--output", "-"])
        
        # Execute in Docker using custom osint-tools container
        # OnionSearch doesn't have an official Docker image
        # Timeout: 5 minutes (can take time to scrape multiple engines)
        docker_result = execute_in_docker("onionsearch", args, timeout=300)
        
        if docker_result["status"] != "success":
            error_msg = f"OnionSearch failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Parse output
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        
        # OnionSearch outputs CSV mixed with status/error messages
        # Extract only CSV lines (lines that look like CSV: contain commas and quotes)
        csv_lines = []
        for line in stdout.split('\n'):
            line = line.strip()
            # Skip empty lines, status messages, and error messages
            if not line:
                continue
            # Skip lines that are clearly not CSV (status messages, errors)
            if line.startswith('search.py') or line.startswith('Exception') or 'SOCKS' in line or 'Report:' in line or 'Execution time:' in line or 'Results per engine:' in line or 'Total:' in line:
                continue
            # CSV lines should contain commas and typically start with quoted values
            if ',' in line and ('"' in line or line.startswith('engine')):
                csv_lines.append(line)
        
        csv_output = '\n'.join(csv_lines)
        
        # OnionSearch outputs CSV format by default: "engine","name","url"
        # Return verbatim CSV output
        if output_format == "csv":
            if csv_output:
                safe_log_info(logger, f"[onionsearch_search] Complete - returning CSV verbatim", query=query)
                return csv_output
            else:
                safe_log_info(logger, f"[onionsearch_search] Complete - no results", query=query)
                return "engine,name,url\n"  # Empty CSV header
        
        # For JSON format, parse CSV to JSON
        if output_format == "json":
            if csv_output:
                try:
                    results = []
                    csv_reader = csv.DictReader(io.StringIO(csv_output))
                    for row in csv_reader:
                        results.append(row)
                    safe_log_info(logger, f"[onionsearch_search] Complete - returning JSON", query=query, results_count=len(results))
                    return json.dumps(results, indent=2)
                except Exception as e:
                    safe_log_error(logger, f"[onionsearch_search] Error parsing CSV: {str(e)}", exc_info=True)
                    # Return raw CSV if parsing fails
                    return csv_output
            else:
                safe_log_info(logger, f"[onionsearch_search] Complete - no results", query=query)
                return json.dumps([])
        
        # Fallback: return CSV output
        safe_log_info(logger, f"[onionsearch_search] Complete - returning CSV verbatim", query=query)
        return csv_output if csv_output else stderr
        
    except Exception as e:
        safe_log_error(logger, f"[onionsearch_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"OnionSearch failed: {str(e)}"})
