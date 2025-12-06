"""
Maigret Tool for CrewAI Agents

Advanced username search with metadata extraction across 3000+ sites
"""

import json
import tempfile
import os
import shutil
import re
from typing import Any, Optional, List, Literal
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/maigret_tool.log")


class MaigretToolSchema(BaseModel):
    """Input schema for MaigretTool."""
    usernames: List[str] = Field(..., description="List of usernames to search across 3000+ sites")
    report_format: Literal["txt", "csv", "html", "xmind", "pdf", "graph", "json"] = Field(default="json", description="Report format: txt, csv, html, xmind, pdf, graph, or json (default: json)")
    json_type: Literal["simple", "ndjson"] = Field(default="simple", description="JSON report type: simple (default) or ndjson (only used when report_format='json')")
    timeout: int = Field(default=30, ge=1, le=300, description="Time in seconds to wait for response to requests (default: 30, range: 1-300)")
    retries: int = Field(default=3, ge=0, le=10, description="Attempts to restart temporarily failed requests (default: 3, range: 0-10)")
    max_connections: int = Field(default=100, ge=1, le=1000, description="Allowed number of concurrent connections (default: 100, range: 1-1000)")
    all_sites: bool = Field(default=False, description="Use all available sites for scan (default: False). If True, ignores top_sites")
    top_sites: Optional[int] = Field(default=None, ge=1, le=3000, description="Count of sites for scan ranked by Alexa Top (default: 500, range: 1-3000). Ignored if all_sites=True")
    tags: Optional[str] = Field(default=None, description="Comma-separated tags of sites to filter by (e.g., 'photo,dating' or 'us')")
    sites: Optional[List[str]] = Field(default=None, description="Optional list of specific site names to limit analysis to (multiple sites)")
    use_disabled_sites: bool = Field(default=False, description="Use disabled sites to search (may cause many false positives, default: False)")
    no_recursion: bool = Field(default=False, description="Disable recursive search by additional data extracted from pages (default: False)")
    no_extracting: bool = Field(default=False, description="Disable parsing pages for additional data and other usernames (default: False)")
    with_domains: bool = Field(default=False, description="Enable experimental feature of checking domains on usernames (default: False)")
    permute: bool = Field(default=False, description="Permute at least 2 usernames to generate more possible usernames (default: False)")
    proxy: Optional[str] = Field(default=None, description="Make requests over a proxy (e.g., 'socks5://127.0.0.1:1080')")
    tor_proxy: Optional[str] = Field(default=None, description="Specify URL of your Tor gateway (default: 'socks5://127.0.0.1:9050')")
    i2p_proxy: Optional[str] = Field(default=None, description="Specify URL of your I2P gateway (default: 'http://127.0.0.1:4444')")
    print_not_found: bool = Field(default=False, description="Print sites where the username was not found (default: False)")
    print_errors: bool = Field(default=False, description="Print error messages: connection, captcha, site country ban, etc. (default: False)")
    verbose: bool = Field(default=False, description="Display extra information and metrics (default: False)")


class MaigretTool(BaseTool):
    """Tool for Advanced username search with metadata extraction across 3000+ sites."""
    
    name: str = "Maigret"
    description: str = "Advanced username search with metadata extraction across 3000+ sites using Maigret. Collects a dossier on a person by username only, checking for accounts on a huge number of sites and gathering all available information from web pages. Supports profile page parsing, extraction of personal info, links to other profiles, and recursive search."
    args_schema: type[BaseModel] = MaigretToolSchema
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
    
    def _run(
        self,
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
        verbose: bool = False,
        **kwargs: Any
    ) -> str:
        """Execute Maigret username search."""
        temp_dir = None
        volumes = []
        
        try:
            safe_log_info(logger, f"[MaigretTool] Starting", usernames=usernames, report_format=report_format, timeout=timeout)
            
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
            
            # Check Docker availability (Docker-only execution)
            docker_client = get_docker_client()
            
            if not docker_client or not docker_client.docker_available:
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
            
            # Parse JSON output if available
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
                            with open(json_file, 'r', encoding='utf-8') as f:
                                if json_type == "simple":
                                    data = json.load(f)
                                    # Maigret JSON format: {"SiteName": {"username": "...", "url_user": "...", "status": {...}, ...}}
                                    if isinstance(data, dict):
                                        for site_name, site_data in data.items():
                                            if isinstance(site_data, dict):
                                                # Check if this is a found account (has url_user and status)
                                                url_user = site_data.get("url_user") or site_data.get("urlUser", "")
                                                status_info = site_data.get("status", {})
                                                
                                                if url_user:
                                                    # Extract metadata from status or site_data
                                                    ids = status_info.get("ids", {}) if isinstance(status_info, dict) else {}
                                                    tags = status_info.get("tags", []) if isinstance(status_info, dict) else []
                                                    
                                                    # Also check for ids in site_data directly
                                                    if not ids:
                                                        ids = site_data.get("ids", {})
                                                    if not tags:
                                                        tags = site_data.get("tags", [])
                                                    
                                                    results[username].append({
                                                        "name": site_name,
                                                        "url": url_user,
                                                        "urlMain": site_data.get("url_main") or site_data.get("urlMain", ""),
                                                        "exists": True,
                                                        "status": status_info.get("status", "Claimed") if isinstance(status_info, dict) else "Claimed",
                                                        "ids": ids,
                                                        "tags": tags,
                                                        "metadata": site_data.get("status", {}),
                                                        "http_status": site_data.get("http_status", 200)
                                                    })
                                                    total_count += 1
                                else:  # ndjson
                                    for line in f:
                                        if line.strip():
                                            site_data = json.loads(line)
                                            if isinstance(site_data, dict) and site_data.get("urlUser"):
                                                results[username].append({
                                                    "name": site_data.get("site", ""),
                                                    "url": site_data.get("urlUser", ""),
                                                    "urlMain": site_data.get("urlMain", ""),
                                                    "exists": True,
                                                    "status": site_data.get("status", ""),
                                                    "ids": site_data.get("ids", {}),
                                                    "tags": site_data.get("tags", []),
                                                    "metadata": site_data.get("ids", {})
                                                })
                                                total_count += 1
                except Exception as e:
                    safe_log_error(logger, f"[MaigretTool] Error parsing JSON: {str(e)}", exc_info=True)
            
            # Parse stdout for results if JSON parsing failed or not using JSON format
            if not any(results.values()) and stdout:
                # Parse stdout text output
                for username in usernames:
                    # Look for sections for this username
                    username_pattern = rf'Checking username\s+{re.escape(username)}\s+on:'
                    if username_pattern in stdout:
                        # Extract results for this username
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
                "execution_method": docker_result.get("execution_method", "docker")
            }
            
            safe_log_info(logger, f"[MaigretTool] Complete", usernames=usernames, count=total_count)
            return json.dumps(result_data, indent=2)
            
        except Exception as e:
            safe_log_error(logger, f"[MaigretTool] Error: {str(e)}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Maigret search failed: {str(e)}"})
        finally:
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    safe_log_info(logger, f"[MaigretTool] Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    safe_log_error(logger, f"[MaigretTool] Error cleaning up temporary directory {temp_dir}: {str(e)}", exc_info=True)
