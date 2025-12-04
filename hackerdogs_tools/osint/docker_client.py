"""
Docker Client for OSINT Tools

This module provides a Docker-based execution layer for OSINT binary tools.
Tools can run in isolated Docker containers instead of requiring binaries
on the host system.
"""

import os
import json
import subprocess
import shutil
from typing import Optional, Dict, Any, List
from hd_logging import setup_logger
from hackerdogs_tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug

logger = setup_logger(__name__, log_file_path="logs/docker_client.log")


class DockerOSINTClient:
    """
    Docker client for executing OSINT tools in containers.
    
    This client manages Docker container lifecycle and executes tools
    via `docker exec` commands. It automatically handles:
    - Container creation/startup
    - Tool execution
    - Output parsing
    - Error handling
    - Container cleanup (optional)
    """
    
    def __init__(
        self,
        image_name: Optional[str] = None,
        container_name: str = "osint-tools",
        docker_runtime: str = "docker",
        auto_start: bool = True,
        workspace: str = "/tmp/osint-workspace"
    ):
        """
        Initialize Docker OSINT client.
        
        This client works both on host and inside Docker containers.
        When running in a container, ensure Docker socket is mounted:
        -v /var/run/docker.sock:/var/run/docker.sock
        
        Args:
            image_name: Docker image name (default: from env or "osint-tools:latest")
            container_name: Container name to use/create
            docker_runtime: Docker runtime ("docker" or "podman")
            auto_start: Automatically start container if not running
            workspace: Host workspace directory to mount
        """
        self.image_name = image_name or os.getenv("OSINT_DOCKER_IMAGE", "osint-tools:latest")
        self.container_name = container_name
        self.docker_runtime = docker_runtime
        self.auto_start = auto_start
        self.workspace = workspace
        
        # Detect if running in Docker container
        self.in_container = os.path.exists("/.dockerenv")
        self.docker_socket = "/var/run/docker.sock"
        
        # Check if Docker is available
        self.docker_available = self._check_docker_available()
        
        if self.docker_available:
            execution_context = "container" if self.in_container else "host"
            safe_log_info(logger, f"[DockerOSINTClient] Initialized", 
                         image=self.image_name, 
                         container=self.container_name,
                         context=execution_context)
            
            if self.in_container:
                # Check if Docker socket is mounted (recommended for container execution)
                if os.path.exists(self.docker_socket):
                    safe_log_debug(logger, "[DockerOSINTClient] Docker socket mounted - can control host Docker")
                else:
                    safe_log_info(logger, "[DockerOSINTClient] Running in container without socket mount - using docker command")
        else:
            if self.in_container:
                safe_log_error(logger, 
                    "[DockerOSINTClient] Docker not available in container. "
                    "Mount Docker socket: -v /var/run/docker.sock:/var/run/docker.sock")
            else:
                safe_log_error(logger, "[DockerOSINTClient] Docker not available on host")
    
    def _check_docker_available(self) -> bool:
        """Check if Docker/Podman is available and running."""
        try:
            result = subprocess.run(
                [self.docker_runtime, "ps"],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _container_exists(self) -> bool:
        """Check if container exists."""
        try:
            result = subprocess.run(
                [self.docker_runtime, "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            return self.container_name in result.stdout
        except Exception:
            return False
    
    def _container_running(self) -> bool:
        """Check if container is running."""
        try:
            result = subprocess.run(
                [self.docker_runtime, "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            return self.container_name in result.stdout
        except Exception:
            return False
    
    def _ensure_container(self) -> bool:
        """Ensure container exists and is running."""
        if not self.docker_available:
            return False
        
        # Check if container exists
        if not self._container_exists():
            safe_log_info(logger, f"[DockerOSINTClient] Creating container: {self.container_name}")
            return self._create_container()
        
        # Check if container is running
        if not self._container_running():
            if self.auto_start:
                safe_log_info(logger, f"[DockerOSINTClient] Starting container: {self.container_name}")
                return self._start_container()
            else:
                safe_log_error(logger, f"[DockerOSINTClient] Container exists but not running: {self.container_name}")
                return False
        
        return True
    
    def _create_container(self) -> bool:
        """Create Docker container."""
        try:
            # Create workspace directory
            os.makedirs(self.workspace, exist_ok=True)
            
            cmd = [
                self.docker_runtime, "run",
                "-d",
                "--name", self.container_name,
                "-v", f"{os.path.abspath(self.workspace)}:/workspace",
                "--restart", "unless-stopped",
                self.image_name
            ]
            
            safe_log_debug(logger, f"[DockerOSINTClient] Creating container", cmd=" ".join(cmd))
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            
            if result.returncode == 0:
                safe_log_info(logger, f"[DockerOSINTClient] Container created: {self.container_name}")
                return True
            else:
                safe_log_error(logger, f"[DockerOSINTClient] Failed to create container: {result.stderr}")
                return False
                
        except Exception as e:
            safe_log_error(logger, f"[DockerOSINTClient] Error creating container: {str(e)}", exc_info=True)
            return False
    
    def _start_container(self) -> bool:
        """Start existing container."""
        try:
            result = subprocess.run(
                [self.docker_runtime, "start", self.container_name],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode == 0:
                safe_log_info(logger, f"[DockerOSINTClient] Container started: {self.container_name}")
                return True
            else:
                safe_log_error(logger, f"[DockerOSINTClient] Failed to start container: {result.stderr}")
                return False
                
        except Exception as e:
            safe_log_error(logger, f"[DockerOSINTClient] Error starting container: {str(e)}", exc_info=True)
            return False
    
    def execute(
        self,
        tool: str,
        args: List[str],
        timeout: int = 300,
        workdir: str = "/workspace",
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a tool in the Docker container.
        
        Args:
            tool: Tool name (e.g., "amass", "nuclei")
            args: List of arguments for the tool
            timeout: Execution timeout in seconds
            workdir: Working directory inside container
            capture_output: Whether to capture stdout/stderr
        
        Returns:
            Dictionary with:
            - status: "success" or "error"
            - stdout: Standard output (if capture_output=True)
            - stderr: Standard error (if capture_output=True)
            - returncode: Exit code
            - execution_time: Execution time in seconds
        """
        if not self.docker_available:
            return {
                "status": "error",
                "message": "Docker not available",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }
        
        if not self._ensure_container():
            return {
                "status": "error",
                "message": f"Failed to ensure container {self.container_name} is running",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }
        
        import time
        start_time = time.time()
        
        try:
            # Build docker exec command
            cmd = [
                self.docker_runtime, "exec",
                "-w", workdir,
                self.container_name,
                tool
            ] + args
            
            safe_log_debug(logger, f"[DockerOSINTClient] Executing", tool=tool, args=args)
            
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False
            )
            
            execution_time = time.time() - start_time
            
            response = {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "returncode": result.returncode,
                "execution_time": execution_time
            }
            
            safe_log_info(logger, f"[DockerOSINTClient] Execution complete", 
                         tool=tool, returncode=result.returncode, time=execution_time)
            
            return response
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            safe_log_error(logger, f"[DockerOSINTClient] Execution timed out", tool=tool, timeout=timeout)
            return {
                "status": "error",
                "message": f"Execution timed out after {timeout} seconds",
                "stdout": "",
                "stderr": "",
                "returncode": -1,
                "execution_time": execution_time
            }
        except Exception as e:
            execution_time = time.time() - start_time
            safe_log_error(logger, f"[DockerOSINTClient] Execution error: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "stdout": "",
                "stderr": "",
                "returncode": -1,
                "execution_time": execution_time
            }
    
    def test(self) -> Dict[str, Any]:
        """Test Docker setup by running a simple command."""
        result = self.execute("echo", ["test"], timeout=5)
        return {
            "docker_available": self.docker_available,
            "container_exists": self._container_exists() if self.docker_available else False,
            "container_running": self._container_running() if self.docker_available else False,
            "test_execution": result
        }


# Global instance (lazy initialization)
_docker_client: Optional[DockerOSINTClient] = None


def get_docker_client() -> Optional[DockerOSINTClient]:
    """Get or create global Docker client instance."""
    global _docker_client
    if _docker_client is None:
        _docker_client = DockerOSINTClient()
    return _docker_client


def execute_in_docker(
    tool: str,
    args: List[str],
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Convenience function to execute a tool in Docker.
    
    This function first checks if the tool has an official Docker image.
    If available, uses the official image. Otherwise, uses the custom osint-tools container.
    
    Official images supported:
    - subfinder: projectdiscovery/subfinder:latest
    - nuclei: projectdiscovery/nuclei:latest
    - (add more as needed)
    
    Args:
        tool: Tool name
        args: Tool arguments
        timeout: Execution timeout
    
    Returns:
        Execution result dictionary
    """
    # Check for official Docker images
    official_images = {
        "subfinder": "projectdiscovery/subfinder:latest",
        "nuclei": "projectdiscovery/nuclei:latest",
    }
    
    # Try official image first if available
    if tool in official_images:
        return execute_official_docker_image(official_images[tool], args, timeout=timeout)
    
    # Fall back to custom container
    client = get_docker_client()
    if client is None:
        return {
            "status": "error",
            "message": "Docker client not available",
            "stdout": "",
            "stderr": "",
            "returncode": -1
        }
    return client.execute(tool, args, timeout=timeout)


def execute_official_docker_image(
    image: str,
    args: List[str],
    timeout: int = 300,
    docker_runtime: str = "docker",
    volumes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Execute a command using an official Docker image (docker run).
    
    This is preferred for tools with official images as they are:
    - Always up-to-date
    - Maintained by the tool authors
    - No need to build custom images
    
    Reference: https://docs.projectdiscovery.io/opensource/subfinder/running
    
    Args:
        image: Docker image name (e.g., "projectdiscovery/subfinder:latest")
        args: Command arguments
        timeout: Execution timeout
        docker_runtime: Docker runtime ("docker" or "podman")
        volumes: Optional list of volume mounts (e.g., ["/host/path:/container/path:ro"])
    
    Returns:
        Execution result dictionary
    """
    import time
    import os
    start_time = time.time()
    
    try:
        # Build docker run command
        # Use --rm to auto-remove container after execution
        cmd = [
            docker_runtime, "run",
            "--rm",
            "-i",  # Interactive mode for stdin
        ]
        
        # Add volume mounts if provided
        if volumes:
            for volume in volumes:
                cmd.extend(["-v", volume])
        else:
            # Auto-mount subfinder config if it exists
            home = os.path.expanduser("~")
            config_dir = os.path.join(home, ".config", "subfinder")
            if os.path.exists(config_dir):
                # Mount config directory to default location in container
                cmd.extend(["-v", f"{config_dir}:/root/.config/subfinder:ro"])
        
        cmd.append(image)
        cmd.extend(args)
        
        safe_log_debug(logger, f"[execute_official_docker_image] Running", image=image, args=args)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        
        execution_time = time.time() - start_time
        
        response = {
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "execution_time": execution_time,
            "execution_method": "official_docker_image"
        }
        
        safe_log_info(logger, f"[execute_official_docker_image] Execution complete", 
                     image=image, returncode=result.returncode, time=execution_time)
        
        return response
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        safe_log_error(logger, f"[execute_official_docker_image] Execution timed out", image=image, timeout=timeout)
        return {
            "status": "error",
            "message": f"Execution timed out after {timeout} seconds",
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "execution_time": execution_time,
            "execution_method": "official_docker_image"
        }
    except FileNotFoundError:
        safe_log_error(logger, f"[execute_official_docker_image] Docker not found", docker_runtime=docker_runtime)
        return {
            "status": "error",
            "message": f"{docker_runtime} not found. Please install Docker.",
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "execution_time": 0,
            "execution_method": "official_docker_image"
        }
    except Exception as e:
        execution_time = time.time() - start_time
        safe_log_error(logger, f"[execute_official_docker_image] Execution error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "execution_time": execution_time,
            "execution_method": "official_docker_image"
        }

