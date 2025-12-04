"""
Subfinder Tool for LangChain Agents

Fast passive subdomain discovery using ProjectDiscovery Subfinder.
"""

import json
import subprocess
import shutil
from typing import Optional
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from pydantic import BaseModel, Field
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/subfinder_tool.log")


class SubfinderSecurityAgentState(AgentState):
    """Extended agent state for Subfinder operations."""
    user_id: str = ""


def _check_docker_available() -> bool:
    """Check if Docker is available for running Subfinder in container."""
    client = get_docker_client()
    return client is not None and client.docker_available


@tool
def subfinder_enum(
    runtime: ToolRuntime,
    domain: str,
    recursive: bool = False,
    silent: bool = True,
    sources: Optional[str] = None,
    exclude_sources: Optional[str] = None,
    all_sources: bool = False,
    rate_limit: Optional[int] = None,
    timeout: int = 30,
    max_time: int = 10,
    provider_config: Optional[str] = None,
    config: Optional[str] = None,
    active: bool = False,
    include_ip: bool = False,
    collect_sources: bool = False
) -> str:
    """
    Enumerate subdomains using Subfinder (fast passive discovery).
    
    Subfinder is extremely fast for passive subdomain discovery using
    multiple passive sources. Use this for quick subdomain enumeration.
    
    Reference: https://docs.projectdiscovery.io/opensource/subfinder/install
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        domain: Target domain to find subdomains for.
        recursive: Use only sources that can handle subdomains recursively (default: False).
        silent: Show only subdomains in output (default: True).
        sources: Comma-separated list of specific sources to use (e.g., "crtsh,github").
        exclude_sources: Comma-separated list of sources to exclude (e.g., "alienvault,zoomeyeapi").
        all_sources: Use all sources for enumeration (slow) (default: False).
        rate_limit: Maximum number of HTTP requests per second (default: None).
        timeout: Seconds to wait before timing out (default: 30).
        max_time: Minutes to wait for enumeration results (default: 10).
        provider_config: Path to custom provider config file (default: $HOME/.config/subfinder/provider-config.yaml).
        config: Path to custom flag config file (default: $CONFIG/subfinder/config.yaml).
        active: Display active subdomains only (default: False).
        include_ip: Include host IP in output (active only) (default: False).
        collect_sources: Include all sources in the output (JSON only) (default: False).
    
    Returns:
        JSON string with subdomains and metadata.
    """
    try:
        safe_log_info(logger, f"[subfinder_enum] Starting enumeration", domain=domain)
        
        # Docker-only execution
        if not _check_docker_available():
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd hackerdogs_tools/osint/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Build command arguments
        args = ["-d", domain, "-oJ", "-"]
        
        # Source options
        if all_sources:
            args.append("-all")
        elif sources:
            args.extend(["-s"] + sources.split(","))
        
        if exclude_sources:
            args.extend(["-es"] + exclude_sources.split(","))
        
        if recursive:
            args.append("-recursive")
        
        # Rate limiting
        if rate_limit:
            args.extend(["-rl", str(rate_limit)])
        
        # Timeouts
        if timeout:
            args.extend(["-timeout", str(timeout)])
        if max_time:
            args.extend(["-max-time", str(max_time)])
        
        # Config files
        if provider_config:
            args.extend(["-pc", provider_config])
        if config:
            args.extend(["-config", config])
        
        # Output options
        if active:
            args.append("-nW")
        if include_ip:
            args.append("-oI")
        if collect_sources:
            args.append("-cs")
        if silent:
            args.append("-silent")
        
        # Execute in Docker using official ProjectDiscovery image
        # Reference: https://docs.projectdiscovery.io/opensource/subfinder/running
        # Note: Config files must be mounted into container or use default locations
        docker_result = execute_in_docker("subfinder", args, timeout=(max_time * 60) + 60)
        
        if docker_result["status"] != "success":
            error_msg = f"Subfinder failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
            safe_log_error(logger, error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        subdomains = []
        stdout = docker_result.get("stdout", "")
        
        # Parse JSON output (one JSON object per line)
        for line in stdout.strip().split('\n'):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if 'host' in data:
                    subdomains.append(data['host'])
            except json.JSONDecodeError:
                # If not JSON, might be plain text subdomain
                line_clean = line.strip()
                if line_clean and '.' in line_clean:
                    subdomains.append(line_clean)
                continue
        
        result_data = {
            "status": "success",
            "domain": domain,
            "subdomains": list(set(subdomains)),
            "count": len(set(subdomains)),
            "execution_method": docker_result.get("execution_method", "docker"),
            "user_id": runtime.state.get("user_id", "")
        }
        
        safe_log_info(logger, f"[subfinder_enum] Complete", domain=domain, count=result_data["count"])
        return json.dumps(result_data, indent=2)
        
    except subprocess.TimeoutExpired:
        return json.dumps({"status": "error", "message": "Subfinder timed out"})
    except Exception as e:
        safe_log_error(logger, f"[subfinder_enum] Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e)})

