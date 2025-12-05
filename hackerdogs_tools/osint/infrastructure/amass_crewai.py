"""
OWASP Amass Tools for CrewAI Agents

This module provides CrewAI tools for all OWASP Amass modules:
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
from typing import Any, Optional
from crewai.tools import BaseTool
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


# ============================================================================
# Intel Tool
# ============================================================================

class AmassIntelToolSchema(BaseModel):
    """Input schema for AmassIntelTool."""
    domain: Optional[str] = Field(default=None, description="Target domain to enumerate (required if org not provided)")
    org: Optional[str] = Field(default=None, description="Organization name substring to search (e.g., 'uber') - used as domain if domain not provided")
    asn: Optional[str] = Field(default=None, description="ASN number to filter by (e.g., '63086') - works as filter with domain")
    cidr: Optional[str] = Field(default=None, description="CIDR range to filter by (e.g., '104.154.0.0/15') - works as filter with domain")
    addr: Optional[str] = Field(default=None, description="IP address or range to filter by (e.g., '192.168.1.1-254') - works as filter with domain")
    whois: bool = Field(default=False, description="Enable reverse WHOIS lookup (NOTE: Not supported in Amass v5.0.0 - parameter accepted but ignored)")
    show_sources: bool = Field(default=False, description="Show data sources used for discovery")
    timeout: int = Field(default=300, ge=60, le=3600, description="Timeout in seconds (60-3600)")


class AmassIntelTool(BaseTool):
    """Tool for intelligence gathering using OWASP Amass."""
    
    name: str = "Amass Intelligence Gathering"
    description: str = (
        "⚠️ REQUIRES domain parameter. ASN/CIDR/addr are optional filters.\n"
        "Find domains by organization, ASN, CIDR, or IP range using OWASP Amass.\n"
        "Use this for discovering root domains associated with companies, network ranges, or ASNs.\n"
        "Example: domain='cloudflare.com', asn='13374' to filter results by ASN."
    )
    args_schema: type[BaseModel] = AmassIntelToolSchema
    
    def _run(
        self,
        domain: Optional[str] = None,
        org: Optional[str] = None,
        asn: Optional[str] = None,
        cidr: Optional[str] = None,
        addr: Optional[str] = None,
        whois: bool = False,
        show_sources: bool = False,
        timeout: int = 300,
        **kwargs: Any
    ) -> str:
        """Execute Amass intel in Docker container."""
        try:
            # Determine target domain for logging
            target_domain_for_log = domain if domain else (org if org else "NOT_PROVIDED")
            safe_log_info(logger, f"[AmassIntelTool] Starting intelligence gathering",
                         domain=target_domain_for_log, asn=asn, cidr=cidr, addr=addr)
            
            docker_client = get_docker_client()
            if not docker_client or not docker_client.docker_available:
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
            # 1. Mount ~/.config/amass to /.config/amass (where database is stored)
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
            safe_log_debug(logger, "[AmassIntelTool] Running enum to populate database")
            enum_result = execute_in_docker("amass", enum_args, timeout=timeout, volumes=volumes)
            
            if enum_result["status"] != "success":
                error_msg = f"Amass intel enum failed: {enum_result.get('stderr', enum_result.get('message', 'Unknown error'))}"
                safe_log_error(logger, f"[AmassIntelTool] Enum failed: {error_msg}")
                return json.dumps({
                    "status": "error",
                    "message": error_msg
                })
            
            # Step 2: Query database - get all discovered domains
            subs_args = ["subs", "-names"]
            
            safe_log_debug(logger, "[AmassIntelTool] Querying database for discovered domains")
            subs_result = execute_in_docker("amass", subs_args, timeout=60, volumes=volumes)
            
            if subs_result["status"] != "success":
                error_msg = f"Amass intel subs query failed: {subs_result.get('stderr', subs_result.get('message', 'Unknown error'))}"
                safe_log_error(logger, f"[AmassIntelTool] Subs query failed: {error_msg}")
                return json.dumps({
                    "status": "error",
                    "message": error_msg
                })
            
            # Step 3: Parse text output
            domains = []
            stdout = subs_result.get("stdout", "")
            for line in stdout.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Parse line: domain name
                domain_name = line.split()[0] if line.split() else line
                domains.append({
                    "domain": domain_name,
                    "ip": "",
                    "source": []
                })
            
            result_data = {
                "status": "success",
                "query": {
                    "org": org,
                    "asn": asn,
                    "cidr": cidr,
                    "addr": addr
                },
                "domains": domains,
                "domain_count": len(domains),
                "execution_method": subs_result.get("execution_method", "docker")
            }
            
            safe_log_info(logger, f"[AmassIntelTool] Intelligence gathering complete",
                         domain_count=result_data["domain_count"])
            
            return json.dumps(result_data, indent=2)
            
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


# ============================================================================
# Enum Tool
# ============================================================================

class AmassEnumToolSchema(BaseModel):
    """Input schema for AmassEnumTool."""
    domain: str = Field(..., description="Target domain to enumerate (e.g., 'tesla.com')")
    passive: bool = Field(default=False, description="Use passive enumeration only")
    active: bool = Field(default=True, description="Use active enumeration")
    brute: bool = Field(default=False, description="Execute brute forcing after searches")
    show_sources: bool = Field(default=False, description="Show data sources used for discovery (NOTE: Not supported in Amass v5.0.0 - parameter accepted but ignored)")
    show_ips: bool = Field(default=False, description="Show IP addresses for discovered names")
    timeout: int = Field(default=300, ge=60, le=3600, description="Timeout in seconds (60-3600)")


class AmassEnumTool(BaseTool):
    """Tool for subdomain enumeration using OWASP Amass."""
    
    name: str = "Amass Subdomain Enumeration"
    description: str = (
        "Enumerate subdomains for a domain using OWASP Amass. "
        "Provides comprehensive subdomain discovery and asset mapping. "
        "Use this for thorough subdomain enumeration and attack surface mapping."
    )
    args_schema: type[BaseModel] = AmassEnumToolSchema
    
    def _run(
        self,
        domain: str,
        passive: bool = False,
        active: bool = True,
        brute: bool = False,
        show_sources: bool = False,
        show_ips: bool = False,
        timeout: int = 300,
        **kwargs: Any
    ) -> str:
        """Execute Amass enumeration in Docker container."""
        try:
            safe_log_info(logger, f"[AmassEnumTool] Starting enumeration", domain=domain)
            
            docker_client = get_docker_client()
            if not docker_client or not docker_client.docker_available:
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
            
            # Get project-relative Amass data directory
            amass_data_dir = get_amass_data_dir()
            
            # Mount data directory to container at /.config/amass (Amass default location)
            volumes = [f"{amass_data_dir}:/.config/amass"]
            
            # Step 1: Build enum command (populate database)
            enum_args = ["enum", "-d", domain]
            if passive:
                enum_args.append("-passive")
            if active:
                enum_args.append("-active")
            if brute:
                enum_args.append("-brute")
            
            # Execute enum to populate database
            safe_log_debug(logger, "[AmassEnumTool] Running enum to populate database", domain=domain)
            enum_result = execute_in_docker("amass", enum_args, timeout=timeout, volumes=volumes)
            
            if enum_result["status"] != "success":
                error_msg = f"Amass enum failed: {enum_result.get('stderr', enum_result.get('message', 'Unknown error'))}"
                safe_log_error(logger, f"[AmassEnumTool] Enum failed: {error_msg}")
                return json.dumps({
                    "status": "error",
                    "message": error_msg
                })
            
            # Step 2: Query database using subs command
            subs_args = ["subs", "-names", "-d", domain]
            if show_ips:
                subs_args.insert(2, "-ip")  # Insert -ip after -names
            
            safe_log_debug(logger, "[AmassEnumTool] Querying database for results", domain=domain)
            subs_result = execute_in_docker("amass", subs_args, timeout=60, volumes=volumes)
            
            if subs_result["status"] != "success":
                error_msg = f"Amass subs query failed: {subs_result.get('stderr', subs_result.get('message', 'Unknown error'))}"
                safe_log_error(logger, f"[AmassEnumTool] Subs query failed: {error_msg}")
                return json.dumps({
                    "status": "error",
                    "message": error_msg
                })
            
            # Step 3: Parse text output (one subdomain per line, or subdomain + IP)
            subdomains = []
            ips = []
            sources_map = {}
            
            stdout = subs_result.get("stdout", "")
            for line in stdout.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Parse line: could be "subdomain" or "subdomain IP"
                parts = line.split()
                if len(parts) >= 1:
                    subdomain = parts[0]
                    subdomains.append(subdomain)
                    
                    # If IP is present, extract it
                    if len(parts) >= 2 and show_ips:
                        ip = parts[1]
                        # Validate IP format
                        if '.' in ip or ':' in ip:
                            ips.append(ip)
            
            result_data = {
                "status": "success",
                "domain": domain,
                "subdomains": list(set(subdomains)),
                "ip_addresses": list(set(ips)),
                "subdomain_count": len(set(subdomains)),
                "ip_count": len(set(ips)),
                "sources": sources_map if show_sources else {},
                "execution_method": subs_result.get("execution_method", "docker")
            }
            
            safe_log_info(logger, f"[AmassEnumTool] Enumeration complete", 
                         domain=domain, subdomain_count=result_data["subdomain_count"])
            
            return json.dumps(result_data, indent=2)
            
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


# ============================================================================
# Visualization Tool
# ============================================================================

class AmassVizToolSchema(BaseModel):
    """Input schema for AmassVizTool."""
    domain: str = Field(..., description="Target domain to visualize")
    format: str = Field(default="json", description="Output format: 'json', 'd3', 'dot', or 'gexf'")
    output_dir: Optional[str] = Field(default=None, description="Directory for output files (default: temp directory)")
    since: Optional[str] = Field(default=None, description="Include only assets validated after (format: '01/02 15:04:05 2006 MST')")
    timeout: int = Field(default=300, ge=60, le=3600, description="Timeout in seconds (60-3600)")


class AmassVizTool(BaseTool):
    """Tool for generating graph visualizations using OWASP Amass."""
    
    name: str = "Amass Graph Visualization"
    description: str = (
        "Generate graph visualization of Amass enumeration data. "
        "Creates visual representations of network graphs showing relationships "
        "between domains, subdomains, and IPs. Outputs graph data in JSON format."
    )
    args_schema: type[BaseModel] = AmassVizToolSchema
    
    def _run(
        self,
        domain: str,
        format: str = "json",
        output_dir: Optional[str] = None,
        since: Optional[str] = None,
        timeout: int = 300,
        **kwargs: Any
    ) -> str:
        """Execute Amass viz in Docker container."""
        try:
            safe_log_info(logger, f"[AmassVizTool] Starting visualization", domain=domain, format=format)
            
            docker_client = get_docker_client()
            if not docker_client or not docker_client.docker_available:
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
            
            # Build Amass viz command
            args = ["viz", "-dir", "/.config/amass", "-d", domain]
            
            # Mount both data directory (database) and results directory (output)
            abs_output_dir = os.path.abspath(output_dir)
            container_output_dir = "/output"
            volumes = [
                f"{amass_data_dir}:/.config/amass",
                f"{abs_output_dir}:{container_output_dir}"
            ]
            
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
            
            # Execute in Docker container
            safe_log_debug(logger, "[AmassVizTool] Executing in Docker container")
            docker_result = execute_in_docker("amass", args, timeout=timeout, volumes=volumes)
            
            if docker_result["status"] != "success":
                error_msg = docker_result.get("stderr", docker_result.get("message", "Unknown error"))
                safe_log_error(logger, f"[AmassVizTool] Docker execution failed: {error_msg}")
                return json.dumps({
                    "status": "error",
                    "message": f"Amass viz failed: {error_msg}"
                })
            
            # Read generated files and convert to JSON
            graph_data = {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "domain": domain,
                    "format": format,
                    "output_dir": output_dir
                }
            }
            
            # Try to find generated files
            output_files = []
            for ext in [".html", ".dot", ".gexf"]:
                for file in os.listdir(output_dir):
                    if file.endswith(ext):
                        output_files.append(os.path.join(output_dir, file))
            
            # Parse formats (same logic as LangChain version)
            if format.lower() == "d3" or format.lower() == "json":
                for file_path in output_files:
                    if file_path.endswith(".html"):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                html_content = f.read()
                                import re
                                # Look for JSON data in script tags - use more robust pattern
                                # Try multiple patterns to handle different D3 HTML formats
                                patterns = [
                                    r'var\s+data\s*=\s*(\{.*?\});',  # var data = {...};
                                    r'data\s*=\s*(\{.*?\});',  # data = {...};
                                    r'const\s+data\s*=\s*(\{.*?\});',  # const data = {...};
                                    r'let\s+data\s*=\s*(\{.*?\});',  # let data = {...};
                                ]
                                graph_json = None
                                for pattern in patterns:
                                    json_match = re.search(pattern, html_content, re.DOTALL)
                                    if json_match:
                                        try:
                                            graph_json = json.loads(json_match.group(1))
                                            break
                                        except json.JSONDecodeError:
                                            continue
                                
                                if graph_json:
                                    graph_data["nodes"] = graph_json.get("nodes", [])
                                    graph_data["edges"] = graph_json.get("links", graph_json.get("edges", []))
                        except Exception as e:
                            safe_log_error(logger, f"[AmassVizTool] Error parsing HTML: {str(e)}")
            
            elif format.lower() == "dot":
                for file_path in output_files:
                    if file_path.endswith(".dot"):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                dot_content = f.read()
                                import re
                                nodes = set()
                                edges = []
                                for line in dot_content.split('\n'):
                                    node_match = re.search(r'"([^"]+)"', line)
                                    if node_match:
                                        nodes.add(node_match.group(1))
                                    edge_match = re.search(r'"([^"]+)"\s*->\s*"([^"]+)"', line)
                                    if edge_match:
                                        edges.append({
                                            "source": edge_match.group(1),
                                            "target": edge_match.group(2)
                                        })
                                graph_data["nodes"] = [{"id": n, "label": n} for n in nodes]
                                graph_data["edges"] = edges
                        except Exception as e:
                            safe_log_error(logger, f"[AmassVizTool] Error parsing DOT: {str(e)}")
            
            elif format.lower() == "gexf":
                for file_path in output_files:
                    if file_path.endswith(".gexf"):
                        try:
                            import xml.etree.ElementTree as ET
                            tree = ET.parse(file_path)
                            root = tree.getroot()
                            graph_elem = root.find('.//{http://www.gexf.net/1.2}graph')
                            if graph_elem is not None:
                                for node in graph_elem.findall('.//{http://www.gexf.net/1.2}node'):
                                    node_id = node.get('id')
                                    label = node.find('.//{http://www.gexf.net/1.2}label')
                                    graph_data["nodes"].append({
                                        "id": node_id,
                                        "label": label.text if label is not None else node_id
                                    })
                                for edge in graph_elem.findall('.//{http://www.gexf.net/1.2}edge'):
                                    graph_data["edges"].append({
                                        "source": edge.get('source'),
                                        "target": edge.get('target')
                                    })
                        except Exception as e:
                            safe_log_error(logger, f"[AmassVizTool] Error parsing GEXF: {str(e)}")
            
            result_data = {
                "status": "success",
                "domain": domain,
                "format": format,
                "graph": graph_data,
                "output_files": output_files,
                "node_count": len(graph_data["nodes"]),
                "edge_count": len(graph_data["edges"]),
                "execution_method": docker_result.get("execution_method", "docker")
            }
            
            safe_log_info(logger, f"[AmassVizTool] Visualization complete",
                         domain=domain, node_count=result_data["node_count"])
            
            return json.dumps(result_data, indent=2)
            
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


# ============================================================================
# Track Tool
# ============================================================================

class AmassTrackToolSchema(BaseModel):
    """Input schema for AmassTrackTool."""
    domain: str = Field(..., description="Target domain to track")
    since: Optional[str] = Field(default=None, description="Exclude all assets discovered before (format: '01/02 15:04:05 2006 MST')")
    timeout: int = Field(default=300, ge=60, le=3600, description="Timeout in seconds (60-3600)")


class AmassTrackTool(BaseTool):
    """Tool for tracking newly discovered assets using OWASP Amass."""
    
    name: str = "Amass Asset Tracking"
    description: str = (
        "Track newly discovered assets over time using OWASP Amass. "
        "Analyzes Amass database data to identify newly discovered assets "
        "for a domain by comparing current enumeration results with historical data."
    )
    args_schema: type[BaseModel] = AmassTrackToolSchema
    
    def _run(
        self,
        domain: str,
        since: Optional[str] = None,
        timeout: int = 300,
        **kwargs: Any
    ) -> str:
        """Execute Amass track in Docker container."""
        try:
            safe_log_info(logger, f"[AmassTrackTool] Starting tracking", domain=domain, since=since)
            
            docker_client = get_docker_client()
            if not docker_client or not docker_client.docker_available:
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
            # 1. Mount ~/.config/amass to /.config/amass (database location)
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
            safe_log_debug(logger, "[AmassTrackTool] Executing in Docker container")
            docker_result = execute_in_docker("amass", args, timeout=timeout, volumes=volumes)
            
            if docker_result["status"] != "success":
                error_msg = docker_result.get("stderr", docker_result.get("message", "Unknown error"))
                safe_log_error(logger, f"[AmassTrackTool] Docker execution failed: {error_msg}")
                return json.dumps({
                    "status": "error",
                    "message": f"Amass track failed: {error_msg}"
                })
            
            stdout = docker_result.get("stdout", "")
            
            # Parse track output (text format, not JSON)
            new_assets = []
            for line in stdout.strip().split('\n'):
                if line.strip() and not line.startswith('.'):
                    parts = line.strip().split()
                    if parts:
                        new_assets.append({
                            "asset": parts[0],
                            "discovered": True
                        })
            
            result_data = {
                "status": "success",
                "domain": domain,
                "since": since,
                "new_assets": new_assets,
                "new_asset_count": len(new_assets),
                "raw_output": stdout,
                "execution_method": docker_result.get("execution_method", "docker")
            }
            
            safe_log_info(logger, f"[AmassTrackTool] Tracking complete",
                         domain=domain, new_asset_count=result_data["new_asset_count"])
            
            return json.dumps(result_data, indent=2)
            
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
