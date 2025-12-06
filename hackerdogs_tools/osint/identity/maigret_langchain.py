"""
Maigret Tool for LangChain Agents

Advanced username search with metadata extraction across 3000+ sites
"""

import json
import tempfile
import os
import shutil
import re
from typing import Optional, List, Literal
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/maigret_tool.log")


class MaigretSecurityAgentState(AgentState):
    """Extended agent state for Maigret operations."""
    user_id: str = ""


def _check_docker_available() -> bool:
    """Check if Docker is available."""
    docker_client = get_docker_client()
    if docker_client is None:
        return False
    return docker_client.docker_available


@tool
def maigret_search(
    runtime: ToolRuntime,
    usernames: List[str],
    report_format: Literal["txt", "csv", "html", "xmind", "pdf", "graph", "json"] = "json",
    json_type: Literal["simple", "ndjson"] = "simple",
    timeout: int = 30,
    retries: int = 3,
    max_connections: int = 100,
    all_sites: bool = False,
    top_sites: Optional[int] = None,
    tags: Optional[str] = None,
    sites: Optional[List[str]] = None,
    use_disabled_sites: bool = False,
    no_recursion: bool = False,
    no_extracting: bool = False,
    with_domains: bool = False,
    permute: bool = False,
    proxy: Optional[str] = None,
    tor_proxy: Optional[str] = None,
    i2p_proxy: Optional[str] = None,
    print_not_found: bool = False,
    print_errors: bool = False,
    verbose: bool = False
) -> str:
    """
    Advanced username search with metadata extraction across 3000+ sites using Maigret.
    
    Maigret collects a dossier on a person by username only, checking for accounts on a huge
    number of sites and gathering all available information from web pages. Supports profile
    page parsing, extraction of personal info, links to other profiles, and recursive search.
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        usernames: List of usernames to search (required).
        report_format: Report format - "txt", "csv", "html", "xmind", "pdf", "graph", or "json" (default: "json").
        json_type: JSON report type - "simple" (default) or "ndjson" (only used when report_format="json").
        timeout: Time in seconds to wait for response to requests (default: 30, range: 1-300).
        retries: Attempts to restart temporarily failed requests (default: 3, range: 0-10).
        max_connections: Allowed number of concurrent connections (default: 100, range: 1-1000).
        all_sites: Use all available sites for scan (default: False). If True, ignores top_sites.
        top_sites: Count of sites for scan ranked by Alexa Top (default: 500, range: 1-3000). Ignored if all_sites=True.
        tags: Comma-separated tags of sites to filter by (e.g., "photo,dating" or "us").
        sites: Optional list of specific site names to limit analysis to (multiple sites).
        use_disabled_sites: Use disabled sites to search (may cause many false positives, default: False).
        no_recursion: Disable recursive search by additional data extracted from pages (default: False).
        no_extracting: Disable parsing pages for additional data and other usernames (default: False).
        with_domains: Enable experimental feature of checking domains on usernames (default: False).
        permute: Permute at least 2 usernames to generate more possible usernames (default: False).
        proxy: Make requests over a proxy (e.g., "socks5://127.0.0.1:1080").
        tor_proxy: Specify URL of your Tor gateway (default: "socks5://127.0.0.1:9050").
        i2p_proxy: Specify URL of your I2P gateway (default: "http://127.0.0.1:4444").
        print_not_found: Print sites where the username was not found (default: False).
        print_errors: Print error messages: connection, captcha, site country ban, etc. (default: False).
        verbose: Display extra information and metrics (default: False).
    
    Returns:
        JSON string with results including:
        - status: "success" or "error"
        - usernames: List of searched usernames
        - results: Dictionary mapping username to found sites with metadata
        - count: Total number of sites found
        - execution_method: "docker" or "official_docker_image"
    """
    temp_dir = None
    volumes = []
    
    try:
        safe_log_info(logger, f"[maigret_search] Starting", usernames=usernames, report_format=report_format, timeout=timeout)
        
        # Validate inputs
        if not usernames or not isinstance(usernames, list) or len(usernames) == 0:
            error_msg = "usernames must be a non-empty list"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        for username in usernames:
            if not isinstance(username, str) or len(username.strip()) == 0:
                error_msg = f"Invalid username in list: {username}"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
        
        if report_format not in ["txt", "csv", "html", "xmind", "pdf", "graph", "json"]:
            error_msg = "report_format must be one of: txt, csv, html, xmind, pdf, graph, json"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if json_type not in ["simple", "ndjson"]:
            error_msg = "json_type must be 'simple' or 'ndjson'"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not (1 <= timeout <= 300):
            error_msg = "timeout must be between 1 and 300 seconds"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not (0 <= retries <= 10):
            error_msg = "retries must be between 0 and 10"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if not (1 <= max_connections <= 1000):
            error_msg = "max_connections must be between 1 and 1000"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Docker-only execution
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Pull Docker image: docker pull soxoj/maigret:latest\n"
                "2. Ensure Docker is running"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Build command arguments
        args = []
        
        # Timeout
        args.extend(["--timeout", str(timeout)])
        
        # Retries
        if retries > 0:
            args.extend(["--retries", str(retries)])
        
        # Max connections
        args.extend(["-n", str(max_connections)])
        
        # Recursion/extraction options
        if no_recursion:
            args.append("--no-recursion")
        
        if no_extracting:
            args.append("--no-extracting")
        
        # Domain checking
        if with_domains:
            args.append("--with-domains")
        
        # Permute
        if permute and len(usernames) >= 2:
            args.append("--permute")
        
        # Proxy options
        if proxy:
            args.extend(["--proxy", proxy])
        
        if tor_proxy:
            args.extend(["--tor-proxy", tor_proxy])
        
        if i2p_proxy:
            args.extend(["--i2p-proxy", i2p_proxy])
        
        # Site filtering
        if all_sites:
            args.append("-a")
        elif top_sites is not None:
            if not (1 <= top_sites <= 3000):
                error_msg = "top_sites must be between 1 and 3000"
                safe_log_error(logger, error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            args.extend(["--top-sites", str(top_sites)])
        
        if tags:
            args.extend(["--tags", tags])
        
        if sites:
            for site in sites:
                args.extend(["--site", site])
        
        if use_disabled_sites:
            args.append("--use-disabled-sites")
        
        # Output options
        if print_not_found:
            args.append("--print-not-found")
        
        if print_errors:
            args.append("--print-errors")
        
        if verbose:
            args.append("--verbose")
        
        # Report formats
        if report_format == "txt":
            args.append("-T")
        elif report_format == "csv":
            args.append("-C")
        elif report_format == "html":
            args.append("-H")
        elif report_format == "xmind":
            args.append("-X")
        elif report_format == "pdf":
            args.append("-P")
        elif report_format == "graph":
            args.append("-G")
        elif report_format == "json":
            args.extend(["-J", json_type])
        
        # Setup output directory for reports
        if report_format in ["txt", "csv", "html", "xmind", "pdf", "graph", "json"]:
            temp_dir = tempfile.mkdtemp()
            container_output_path = "/app/reports"
            volumes.append(f"{temp_dir}:{container_output_path}")
            args.extend(["--folderoutput", container_output_path])
        
        # Add usernames (positional arguments)
        args.extend(usernames)
        
        # Execute in Docker using official soxoj/maigret image
        # Calculate timeout: (timeout per request * number of usernames * sites) + buffer
        # For top 500 sites with 30s timeout: 500 * 30 = 15000s worst case, but concurrent connections reduce this
        # Use a more reasonable timeout based on max_connections
        estimated_sites = top_sites if top_sites and not all_sites else 500
        if all_sites:
            estimated_sites = 3000  # Max sites in database
        execution_timeout = (timeout * estimated_sites / max_connections) + (retries * timeout) + 300  # Buffer
        execution_timeout = min(execution_timeout, 3600)  # Cap at 1 hour
        
        docker_result = execute_in_docker("maigret", args, timeout=int(execution_timeout), volumes=volumes if volumes else None)
        
        if docker_result["status"] != "success":
            error_msg = f"Maigret failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Parse output
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        
        results = {username: [] for username in usernames}
        total_count = 0
        
        # For JSON format with single username: return the JSON file content directly, verbatim
        if report_format == "json" and temp_dir and len(usernames) == 1:
            try:
                username = usernames[0]
                json_file = None
                # Try Maigret's naming pattern: report_{username}_{type}.json
                if json_type == "simple":
                    json_file = os.path.join(temp_dir, f"report_{username}_simple.json")
                    # Fallback to old naming
                    if not os.path.exists(json_file):
                        json_file = os.path.join(temp_dir, f"{username}.json")
                else:  # ndjson
                    json_file = os.path.join(temp_dir, f"report_{username}_ndjson.json")
                    # Fallback to old naming
                    if not os.path.exists(json_file):
                        json_file = os.path.join(temp_dir, f"{username}.ndjson")
                
                if json_file and os.path.exists(json_file):
                    # Read raw JSON file and return directly, verbatim - no wrapper
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_content = f.read()
                    # Cleanup temp directory
                    if os.path.exists(temp_dir):
                        try:
                            shutil.rmtree(temp_dir)
                        except Exception:
                            pass
                    # Return JSON file content directly, verbatim - no wrapper
                    safe_log_info(logger, f"[maigret_search] Complete - returning JSON file content verbatim", usernames=usernames)
                    return json_content
            except Exception as e:
                safe_log_error(logger, f"[maigret_search] Error reading JSON file: {str(e)}", exc_info=True)
                # Fall through to wrapper format
        
        # For multiple usernames: return JSON files directly as dictionary (no wrapper)
        if report_format == "json" and temp_dir:
            json_results = {}
            try:
                # Look for JSON files in the output directory
                # Maigret saves files as: report_{username}_{json_type}.json
                for username in usernames:
                    json_file = None
                    # Try Maigret's naming pattern: report_{username}_{type}.json
                    if json_type == "simple":
                        json_file = os.path.join(temp_dir, f"report_{username}_simple.json")
                        # Fallback to old naming
                        if not os.path.exists(json_file):
                            json_file = os.path.join(temp_dir, f"{username}.json")
                    else:  # ndjson
                        json_file = os.path.join(temp_dir, f"report_{username}_ndjson.json")
                        # Fallback to old naming
                        if not os.path.exists(json_file):
                            json_file = os.path.join(temp_dir, f"{username}.ndjson")
                    
                    if os.path.exists(json_file):
                        # Read raw JSON file and return as-is (verbatim, no parsing)
                        with open(json_file, 'r', encoding='utf-8') as f:
                            json_results[username] = f.read()  # Return as raw string, not parsed
            except Exception as e:
                safe_log_error(logger, f"[maigret_search] Error reading JSON files: {str(e)}", exc_info=True)
            
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
            
            # Return JSON files as dictionary mapping username to JSON content - no wrapper
            if json_results:
                safe_log_info(logger, f"[maigret_search] Complete - returning JSON files verbatim", usernames=usernames)
                return json.dumps(json_results, indent=2)
        
        # For CSV format: check for CSV files in output directory
        if report_format == "csv" and temp_dir and os.path.exists(temp_dir):
            csv_results = {}
            try:
                # Look for CSV files in the output directory
                # Maigret saves files as: report_{username}.csv or {username}.csv
                for username in usernames:
                    csv_file = None
                    # Try Maigret's naming pattern: report_{username}.csv
                    csv_file = os.path.join(temp_dir, f"report_{username}.csv")
                    # Fallback to simple naming
                    if not os.path.exists(csv_file):
                        csv_file = os.path.join(temp_dir, f"{username}.csv")
                    
                    if os.path.exists(csv_file):
                        # Read raw CSV file and return as-is (verbatim)
                        with open(csv_file, 'r', encoding='utf-8') as f:
                            csv_results[username] = f.read()
            except Exception as e:
                safe_log_error(logger, f"[maigret_search] Error reading CSV files: {str(e)}", exc_info=True)
            
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
            
            # Return CSV files as dictionary mapping username to CSV content - no wrapper
            if csv_results:
                if len(csv_results) == 1 and len(usernames) == 1:
                    # Single CSV file - return it verbatim
                    safe_log_info(logger, f"[maigret_search] Complete - returning CSV file content verbatim", usernames=usernames)
                    return list(csv_results.values())[0]
                else:
                    # Multiple CSV files - return as dict
                    safe_log_info(logger, f"[maigret_search] Complete - returning CSV files verbatim", usernames=usernames)
                    return json.dumps(csv_results, indent=2)
        
        # For other non-JSON formats (txt, html, xmind, pdf, graph) or if files not found: return stdout/stderr verbatim
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
        
        # Return stdout/stderr verbatim - no wrapper
        safe_log_info(logger, f"[maigret_search] Complete - returning stdout verbatim", usernames=usernames)
        return stdout if stdout else stderr
        
    except Exception as e:
        safe_log_error(logger, f"[maigret_search] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Maigret search failed: {str(e)}"})
    finally:
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                safe_log_info(logger, f"[maigret_search] Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                safe_log_error(logger, f"[maigret_search] Error cleaning up temporary directory {temp_dir}: {str(e)}", exc_info=True)
