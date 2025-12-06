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
        
        # Read raw JSON output if available (return verbatim, no parsing)
        raw_json_results = {}
        if report_format == "json" and temp_dir:
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
                        # Read raw JSON file and return as-is (verbatim)
                        with open(json_file, 'r', encoding='utf-8') as f:
                            if json_type == "simple":
                                # Simple format: single JSON object
                                raw_json_results[username] = json.load(f)
                            else:  # ndjson
                                # NDJSON format: one JSON object per line
                                raw_json_results[username] = [json.loads(line) for line in f if line.strip()]
            except Exception as e:
                safe_log_error(logger, f"[maigret_search] Error reading JSON: {str(e)}", exc_info=True)
        
        # If we have raw JSON results, return them verbatim
        if raw_json_results:
            result_data = {
                "status": "success",
                "usernames": usernames,
                "results": raw_json_results,  # Raw JSON as-is, no parsing/reformatting
                "report_format": report_format,
                "json_type": json_type,
                "execution_method": docker_result.get("execution_method", "docker"),
                "user_id": runtime.state.get("user_id", "")
            }
            safe_log_info(logger, f"[maigret_search] Complete - returning raw JSON", usernames=usernames)
            return json.dumps(result_data, indent=2)
        
        # Fallback: Parse stdout for results if JSON files not found or not using JSON format
        results = {username: [] for username in usernames}
        total_count = 0
        
        if stdout:
            # Parse stdout text output
            # Format: "[+] SiteName: URL" with optional metadata
            for username in usernames:
                # Look for sections for this username
                username_pattern = rf'Checking username\s+{re.escape(username)}\s+on:'
                if username_pattern in stdout:
                    # Extract results for this username
                    # Pattern: "[+] SiteName: URL" or "[+] SiteName: URL | metadata"
                    pattern = rf'\[\+\]\s+([^:]+):\s+(https?://[^\s\|]+)(?:\s*\|\s*(.+))?'
                    matches = re.findall(pattern, stdout)
                    
                    for site_name, url, metadata in matches:
                        # Try to extract metadata from the metadata string or from following lines
                        metadata_dict = {}
                        if metadata:
                            # Parse metadata like "id: 123, username: test"
                            metadata_items = re.findall(r'(\w+):\s*([^\s,]+)', metadata)
                            for key, value in metadata_items:
                                metadata_dict[key] = value
                        
                        results[username].append({
                            "name": site_name.strip(),
                            "url": url,
                            "urlMain": url,
                            "exists": True,
                            "metadata": metadata_dict
                        })
                        total_count += 1
        
        # If still no results, check if there's any output
        if not any(results.values()) and stdout:
            # Try to extract any found sites
            for username in usernames:
                if username in stdout:
                    # Look for any [+] markers
                    pattern = r'\[\+\]\s+([^:]+):\s+(https?://[^\s]+)'
                    matches = re.findall(pattern, stdout)
                    for site_name, url in matches:
                        if username.lower() in url.lower():
                            results[username].append({
                                "name": site_name.strip(),
                                "url": url,
                                "urlMain": url,
                                "exists": True
                            })
                            total_count += 1
        
        result_data = {
            "status": "success",
            "usernames": usernames,
            "results": results,
            "count": total_count,
            "report_format": report_format,
            "execution_method": docker_result.get("execution_method", "docker"),
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[maigret_search] Complete", usernames=usernames, count=total_count)
        return json.dumps(result_data, indent=2)
        
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
