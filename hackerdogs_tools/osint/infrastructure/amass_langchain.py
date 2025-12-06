"""
OWASP Amass Tools for LangChain Agents

This module provides LangChain tools for all OWASP Amass modules:
- intel: Intelligence gathering (find domains by org, ASN, CIDR, etc.)
- enum: Subdomain enumeration and asset mapping
- viz: Graph visualization (D3, DOT, GEXF formats converted to JSON)
- track: Track newly discovered assets over time

Reference: https://github.com/OWASP/Amass
Blog: https://danielmiessler.com/blog/amass
"""

import json
import subprocess
import os
import tempfile
from typing import Optional, Dict, Any
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import (
    safe_log_debug,
    safe_log_info,
    safe_log_error
)
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker
from hackerdogs_tools.osint.amass_config import get_amass_data_dir, get_amass_results_dir

logger = setup_logger(__name__, log_file_path="logs/amass_tool.log")


class AmassSecurityAgentState(AgentState):
    """Extended agent state for Amass operations."""
    user_id: str = ""
    api_keys: Dict[str, str] = {}


def _check_docker_available() -> bool:
    """Check if Docker is available for running Amass in container."""
    client = get_docker_client()
    return client is not None and client.docker_available


@tool
def amass_intel(
    runtime: ToolRuntime,
    domain: Optional[str] = None,
    org: Optional[str] = None,
    asn: Optional[str] = None,
    cidr: Optional[str] = None,
    addr: Optional[str] = None,
    whois: bool = False,
    show_sources: bool = False,
    timeout: int = 600  # Increased for intel operations which can be slow on large domains
) -> str:
    """
    Intelligence gathering: Find domains by organization, ASN, CIDR, or IP range.
    
    ⚠️ REQUIRES domain parameter. ASN/CIDR/addr are optional filters.
    
    This tool uses Amass to discover root domains associated with:
    - Organizations (by name substring)
    - ASN numbers (as filter)
    - CIDR ranges (as filter)
    - IP addresses or ranges (as filter)
    
    Note: In Amass v5.0.0, 'enum' requires a domain (-d). ASN/CIDR/addr are filters.
    
    When to use:
        - Finding all domains owned by a company (e.g., "uber")
        - Discovering domains on a specific CIDR range
        - Finding domains by ASN
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        domain: Target domain to enumerate (REQUIRED - provide this or org).
        org: Organization name substring to search (e.g., "uber") - used as domain if domain not provided.
        asn: ASN number to filter by (e.g., "63086") - OPTIONAL filter, requires domain.
        cidr: CIDR range to filter by (e.g., "104.154.0.0/15") - OPTIONAL filter, requires domain.
        addr: IP address or range to filter by (e.g., "192.168.1.1-254") - OPTIONAL filter, requires domain.
        whois: Enable reverse WHOIS lookup (NOTE: Not supported in Amass v5.0.0 - parameter accepted but ignored).
        show_sources: Show data sources used for discovery (NOTE: Not supported in Amass v5.0.0 - parameter accepted but ignored).
        timeout: Timeout in seconds (default: 600 for intel operations).
    
    Returns:
        JSON string with discovered domains and metadata.
    
    Example:
        domain="cloudflare.com", asn="13374"  # Enumerate cloudflare.com filtered by ASN 13374
    """
    try:
        # Determine target domain for logging
        target_domain_for_log = domain if domain else (org if org else "NOT_PROVIDED")
        safe_log_info(logger, f"[amass_intel] Starting intelligence gathering",
                      domain=target_domain_for_log, asn=asn, cidr=cidr, addr=addr)
        
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Ensure Docker is running: docker ps\n"
                "2. Official Amass image will be pulled automatically"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Amass v5.0.0 workflow for intel:
        # 1. Mount project data directory to /.config/amass (where database is stored)
        # 2. Run 'amass enum -asn X' or similar to populate database
        # 3. Run 'amass subs -names -d <discovered_domains>' to query results
        # 4. Parse text output (no JSON flag in v5.0.0)
        
        # Get project-relative Amass data directory
        amass_data_dir = get_amass_data_dir()
        
        # Mount data directory to container at /.config/amass (Amass default location)
        volumes = [f"{amass_data_dir}:/.config/amass"]
        
        # Build enum command with intel-like options
        # CRITICAL: Amass v5.0 requires -d DOMAIN. ASN/CIDR/addr are filters, not replacements.
        # In v5.0, there is NO separate 'intel' command - intel functionality uses 'enum' with filters.
        enum_args = ["enum"]
        
        # Determine the domain to use
        # Priority: domain > org > error if neither provided
        target_domain = domain
        if not target_domain and org:
            # Use org as domain (will search for domains containing org name)
            target_domain = org
        elif not target_domain:
            # Cannot enumerate without a domain - ASN/CIDR/addr are filters only
            error_msg = (
                "Domain is REQUIRED. ASN/CIDR/addr are optional filters.\n"
                "Example: domain='example.com', asn='13374' to filter results by ASN.\n"
                "You provided: " + (f"asn={asn}" if asn else "") + 
                (f", cidr={cidr}" if cidr else "") + 
                (f", addr={addr}" if addr else "") + 
                " - but no domain was provided."
            )
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Add domain (REQUIRED by Amass v5.0)
        enum_args.extend(["-d", target_domain])
        
        # Add filters (optional, but help narrow results)
        # These work WITH the domain, not as replacements
        if asn:
            enum_args.extend(["-asn", asn])
        if cidr:
            enum_args.extend(["-cidr", cidr])
        if addr:
            enum_args.extend(["-addr", addr])
        
        # Use passive mode for intel (faster, less intrusive)
        enum_args.append("-passive")
        
        # Note: -src flag is NOT supported in Amass v5.0.0
        # show_sources parameter is accepted but ignored
        # if show_sources:
        #     enum_args.append("-src")  # Not supported in v5.0.0
        
        # Step 1: Run enum to populate database
        safe_log_debug(logger, "[amass_intel] Running enum to populate database")
        enum_result = execute_in_docker("amass", enum_args, timeout=timeout, volumes=volumes)
        
        if enum_result["status"] != "success":
            error_msg = f"Amass intel enum failed: {enum_result.get('stderr', enum_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Step 2: Query database - get all discovered domains
        # For intel, we need to query all domains in the database
        # Use subs without -d to get all, or query by the search criteria
        subs_args = ["subs", "-names"]
        if show_sources:
            # Note: -src flag might not work with subs, but try
            pass
        
        safe_log_debug(logger, "[amass_intel] Querying database for discovered domains")
        subs_result = execute_in_docker("amass", subs_args, timeout=60, volumes=volumes)
        
        if subs_result["status"] != "success":
            error_msg = f"Amass intel subs query failed: {subs_result.get('stderr', subs_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Return raw output verbatim - no parsing, no reformatting
        stdout = subs_result.get("stdout", "")
        stderr = subs_result.get("stderr", "")
        
        safe_log_info(logger, f"[amass_intel] Complete - returning raw output verbatim")
        return stdout if stdout else stderr
        
    except subprocess.TimeoutExpired:
        error_msg = f"Amass intel timed out after {timeout} seconds"
        safe_log_error(logger, error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error running Amass intel: {str(e)}"
        safe_log_error(logger, error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def amass_enum(
    runtime: ToolRuntime,
    domain: str,
    passive: bool = False,
    active: bool = True,
    brute: bool = False,
    show_sources: bool = False,
    show_ips: bool = False,
    timeout: int = 300
) -> str:
    """
    Enumerate subdomains for a domain using OWASP Amass.
    
    This tool uses OWASP Amass to perform comprehensive subdomain enumeration
    and asset mapping. Amass combines multiple data sources including passive
    DNS, certificate transparency logs, and active enumeration techniques.
    
    When to use:
        - User asks to find all subdomains for a domain
        - Need comprehensive subdomain enumeration
        - Mapping attack surface for a target domain
        - Security assessment: discovering all assets
    
    When NOT to use:
        - Need fast, lightweight enumeration (use Subfinder instead)
        - Domain format is invalid
        - Timeout is too short for large domains
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        domain: Target domain (e.g., "tesla.com").
        passive: Use passive enumeration only (default: False).
        active: Use active enumeration (default: True).
        brute: Execute brute forcing after searches (default: False).
        show_sources: Show data sources used for discovery (default: False).
        show_ips: Show IP addresses for discovered names (default: False).
        timeout: Timeout in seconds (default: 300).
    
    Returns:
        JSON string with subdomains, IPs, and network graph.
    """
    try:
        safe_log_info(logger, f"[amass_enum] Starting enumeration", domain=domain)
        
        # Docker-only execution - no host binaries allowed
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Ensure Docker is running: docker ps\n"
                "2. Official Amass image will be pulled automatically"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Amass v5.0.0 workflow:
        # 1. Mount ~/.config/amass to /.config/amass (where database is stored)
        # 2. Run 'amass enum -d domain' to populate database
        # 3. Run 'amass subs -names -ip -d domain' to query results
        # 4. Parse text output (no JSON flag in v5.0.0)
        
        # Ensure Amass config directory exists on host
        home = os.path.expanduser("~")
        amass_config = os.path.join(home, ".config", "amass")
        os.makedirs(amass_config, exist_ok=True)
        
        # Mount config directory to container (where Amass stores database)
        volumes = [f"{amass_config}:/.config/amass"]
        
        # Step 1: Build enum command (populate database)
        enum_args = ["enum", "-d", domain]
        if passive:
            enum_args.append("-passive")
        if active:
            enum_args.append("-active")
        if brute:
            enum_args.append("-brute")
        
        # Execute enum to populate database
        safe_log_debug(logger, "[amass_enum] Running enum to populate database", domain=domain)
        enum_result = execute_in_docker("amass", enum_args, timeout=timeout, volumes=volumes)
        
        if enum_result["status"] != "success":
            error_msg = f"Amass enum failed: {enum_result.get('stderr', enum_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Step 2: Query database using subs command
        subs_args = ["subs", "-names", "-d", domain]
        if show_ips:
            subs_args.insert(2, "-ip")  # Insert -ip after -names
        
        safe_log_debug(logger, "[amass_enum] Querying database for results", domain=domain)
        subs_result = execute_in_docker("amass", subs_args, timeout=60, volumes=volumes)
        
        if subs_result["status"] != "success":
            error_msg = f"Amass subs query failed: {subs_result.get('stderr', subs_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Return raw output verbatim - no parsing, no reformatting
        stdout = subs_result.get("stdout", "")
        stderr = subs_result.get("stderr", "")
        
        return stdout if stdout else stderr
        
    except subprocess.TimeoutExpired:
        error_msg = f"Amass enumeration timed out after {timeout} seconds"
        safe_log_error(logger, error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error running Amass: {str(e)}"
        safe_log_error(logger, error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def amass_viz(
    runtime: ToolRuntime,
    domain: str,
    format: str = "json",
    output_dir: Optional[str] = None,
    since: Optional[str] = None,
    timeout: int = 300
) -> str:
    """
    Generate graph visualization of Amass enumeration data.
    
    This tool creates visual representations of the network graph discovered
    by Amass. The graph shows relationships between domains, subdomains, and IPs.
    
    Supported formats:
    - json: Graph data in JSON format (nodes and edges)
    - d3: D3.js HTML visualization (converted to JSON structure)
    - dot: Graphviz DOT format (converted to JSON structure)
    - gexf: Gephi GEXF format (converted to JSON structure)
    
    When to use:
        - Visualizing attack surface
        - Understanding domain relationships
        - Creating network graphs for reports
        - Analyzing subdomain structure
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        domain: Target domain to visualize.
        format: Output format - "json", "d3", "dot", or "gexf" (default: "json").
        output_dir: Directory for output files (default: temp directory).
        since: Include only assets validated after (format: "01/02 15:04:05 2006 MST").
        timeout: Timeout in seconds (default: 300).
    
    Returns:
        JSON string with graph data (nodes and edges).
    """
    try:
        safe_log_info(logger, f"[amass_viz] Starting visualization", domain=domain, format=format)
        
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Ensure Docker is running: docker ps\n"
                "2. Official Amass image will be pulled automatically"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Amass v5.0.0 viz workflow:
        # 1. Mount project data directory to /.config/amass (database location)
        # 2. Mount results directory for viz files
        # 3. Run 'amass viz -dir /.config/amass -d domain -d3 -o /output'
        
        # Get project-relative Amass data directory (database)
        amass_data_dir = get_amass_data_dir()
        
        # Get or create output directory in project results folder
        if not output_dir:
            output_dir = get_amass_results_dir()
        os.makedirs(output_dir, exist_ok=True)
        
        # Mount both data directory (database) and results directory (output)
        abs_output_dir = os.path.abspath(output_dir)
        container_output_dir = "/output"
        volumes = [
            f"{amass_data_dir}:/.config/amass",
            f"{abs_output_dir}:{container_output_dir}"
        ]
        
        # Build Amass viz command
        args = ["viz", "-dir", "/.config/amass", "-d", domain]
        
        # Select format
        if format.lower() == "d3":
            args.append("-d3")
        elif format.lower() == "dot":
            args.append("-dot")
        elif format.lower() == "gexf":
            args.append("-gexf")
        else:
            # Default to d3
            args.append("-d3")
        
        args.extend(["-o", container_output_dir])
        
        if since:
            args.extend(["-since", since])
        
        safe_log_debug(logger, "[amass_viz] Executing in Docker container")
        docker_result = execute_in_docker("amass", args, timeout=timeout, volumes=volumes)
        
        if docker_result["status"] != "success":
            error_msg = f"Amass viz failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Return raw output verbatim - no parsing, no reformatting
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        
        # Find generated files and return their paths and raw contents
        output_files = {}
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                file_path = os.path.join(output_dir, file)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            output_files[file] = f.read()
                    except Exception as e:
                        safe_log_error(logger, f"[amass_viz] Error reading file {file}: {str(e)}")
                        output_files[file] = f"Error reading file: {str(e)}"
        
        return stdout if stdout else stderr
        
    except subprocess.TimeoutExpired:
        error_msg = f"Amass viz timed out after {timeout} seconds"
        safe_log_error(logger, error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error running Amass viz: {str(e)}"
        safe_log_error(logger, error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })


@tool
def amass_track(
    runtime: ToolRuntime,
    domain: str,
    since: Optional[str] = None,
    timeout: int = 300
) -> str:
    """
    Track newly discovered assets over time.
    
    This tool analyzes Amass database data to identify newly discovered assets
    for a domain. It compares current enumeration results with historical data
    to detect changes.
    
    When to use:
        - Monitoring for new subdomains
        - Tracking asset changes over time
        - Detecting newly registered domains
        - Continuous monitoring workflows
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        domain: Target domain to track.
        since: Exclude all assets discovered before (format: "01/02 15:04:05 2006 MST").
        timeout: Timeout in seconds (default: 300).
    
    Returns:
        JSON string with newly discovered assets and changes.
    """
    try:
        safe_log_info(logger, f"[amass_track] Starting tracking", domain=domain, since=since)
        
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Ensure Docker is running: docker ps\n"
                "2. Official Amass image will be pulled automatically"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        # Amass v5.0.0 track workflow:
        # 1. Mount project data directory to /.config/amass (database location)
        # 2. Run 'amass track -dir /.config/amass -d domain'
        
        # Get project-relative Amass data directory
        amass_data_dir = get_amass_data_dir()
        
        # Mount data directory to container at /.config/amass (Amass default location)
        volumes = [f"{amass_data_dir}:/.config/amass"]
        
        # Build Amass track command
        args = ["track", "-dir", "/.config/amass", "-d", domain]
        
        if since:
            args.extend(["-since", since])
        
        # Execute in Docker container
        safe_log_debug(logger, "[amass_track] Executing in Docker container")
        docker_result = execute_in_docker("amass", args, timeout=timeout, volumes=volumes)
        
        if docker_result["status"] != "success":
            error_msg = f"Amass track failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg
            })
        
        stdout = docker_result.get("stdout", "")
        stderr = docker_result.get("stderr", "")
        
        # Return raw output verbatim - no parsing, no reformatting
        return stdout if stdout else stderr
        
    except subprocess.TimeoutExpired:
        error_msg = f"Amass track timed out after {timeout} seconds"
        safe_log_error(logger, error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
    except Exception as e:
        error_msg = f"Unexpected error running Amass track: {str(e)}"
        safe_log_error(logger, error_msg, exc_info=True)
        return json.dumps({
            "status": "error",
            "message": error_msg
        })
