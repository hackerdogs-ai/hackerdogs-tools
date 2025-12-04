# 🐳 Docker Implementation Guide for OSINT Tools

## Overview

This guide explains how to implement Docker-based execution for OSINT tools, allowing them to run in isolated containers instead of requiring binaries on the host system.

---

## 🏗️ Architecture

### Execution Flow

```
Python Tool Code
    │
    ├─→ Check: Binary on host?
    │   │
    │   ├─→ YES: Use host binary (subprocess)
    │   │
    │   └─→ NO: Check Docker available?
    │       │
    │       ├─→ YES: Use Docker container (docker exec)
    │       │
    │       └─→ NO: Return error with helpful message
```

### Components

1. **Docker Image** (`docker/Dockerfile`)
   - Contains all OSINT binaries
   - Based on Ubuntu 22.04
   - Includes Go tools (Amass, Nuclei, Subfinder, waybackurls)
   - Includes system packages (Masscan, ZMap, ExifTool, YARA)
   - Includes Python OSINT tools

2. **Docker Client** (`docker_client.py`)
   - Manages container lifecycle
   - Executes tools via `docker exec`
   - Handles errors and timeouts
   - Provides unified interface

3. **Tool Implementation**
   - Checks for host binary first
   - Falls back to Docker if binary not found
   - Transparent to user (same API)

---

## 📝 Implementation Pattern

### Step 1: Import Docker Client

```python
from hackerdogs_tools.osint.docker_client import get_docker_client, execute_in_docker
```

### Step 2: Check Availability

```python
def _check_tool_available() -> bool:
    """Check if tool is available on host or Docker."""
    # Check host binary
    if shutil.which("tool_name"):
        return True
    
    # Check Docker
    client = get_docker_client()
    return client is not None and client.docker_available
```

### Step 3: Execute with Fallback

```python
def _run_tool(args: List[str]) -> Dict[str, Any]:
    """Execute tool with Docker fallback."""
    use_docker = not shutil.which("tool_name")
    
    if use_docker:
        # Execute in Docker
        result = execute_in_docker("tool_name", args, timeout=300)
        if result["status"] != "success":
            return {"status": "error", "message": result.get("stderr")}
        stdout = result.get("stdout", "")
    else:
        # Execute on host
        result = subprocess.run(
            ["tool_name"] + args,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            return {"status": "error", "message": result.stderr}
        stdout = result.stdout
    
    # Process output
    return {"status": "success", "output": stdout}
```

---

## 🔧 Tool Implementation Examples

### Example 1: Amass (Already Implemented)

See `infrastructure/amass_langchain.py` for complete example.

**Key points:**
- Checks for host binary first
- Falls back to Docker automatically
- Returns execution method in result
- Same API regardless of execution method

### Example 2: Nuclei

```python
@tool
def nuclei_scan(runtime: ToolRuntime, target: str, ...) -> str:
    """Scan target with Nuclei."""
    use_docker = not shutil.which("nuclei")
    
    args = ["-u", target, "-jsonl", "-o", "-"]
    if use_docker:
        result = execute_in_docker("nuclei", args, timeout=600)
        stdout = result.get("stdout", "")
    else:
        result = subprocess.run(
            ["nuclei"] + args,
            capture_output=True,
            text=True,
            timeout=600
        )
        stdout = result.stdout
    
    # Parse and return
    ...
```

### Example 3: Subfinder

```python
@tool
def subfinder_enum(runtime: ToolRuntime, domain: str) -> str:
    """Enumerate subdomains with Subfinder."""
    use_docker = not shutil.which("subfinder")
    
    args = ["-d", domain, "-oJ", "-"]
    if use_docker:
        result = execute_in_docker("subfinder", args)
        stdout = result.get("stdout", "")
    else:
        result = subprocess.run(
            ["subfinder"] + args,
            capture_output=True,
            text=True
        )
        stdout = result.stdout
    
    # Parse JSON output
    ...
```

---

## 🚀 Setup Procedure

### 1. Build Docker Image

```bash
cd hackerdogs_tools/osint/docker
docker build -t osint-tools:latest .
```

**Or use the script:**
```bash
./BUILD_AND_RUN.sh
```

### 2. Start Container

```bash
# Option A: Docker Compose
docker-compose up -d

# Option B: Manual
docker run -d \
  --name osint-tools \
  -v $(pwd)/workspace:/workspace \
  osint-tools:latest
```

### 3. Verify Setup

```python
from hackerdogs_tools.osint.docker_client import DockerOSINTClient

client = DockerOSINTClient()
test_result = client.test()
print(json.dumps(test_result, indent=2))
```

### 4. Use Tools

```python
from hackerdogs_tools.osint.infrastructure.amass_langchain import amass_enum

# Automatically uses Docker if binary not on host
result = amass_enum(runtime, domain="example.com")
```

---

## 🔄 Container Lifecycle

### Automatic Management

The Docker client automatically:
1. **Checks** if container exists
2. **Creates** container if it doesn't exist
3. **Starts** container if it's stopped
4. **Reuses** existing running container

### Manual Management

```bash
# Start container
docker start osint-tools

# Stop container
docker stop osint-tools

# Remove container
docker rm osint-tools

# View logs
docker logs osint-tools

# Execute command manually
docker exec osint-tools amass enum -d example.com
```

---

## 📊 Performance Considerations

### Container Startup
- **First run**: ~1-2 seconds (container creation)
- **Subsequent runs**: ~0.1 seconds (container already running)

### Tool Execution
- **Overhead**: Minimal (~0.05-0.1 seconds per execution)
- **Performance**: Same as native binary (tools run natively in container)

### Parallel Execution
- **Multiple containers**: Can run multiple containers for parallel execution
- **Single container**: Can execute multiple tools sequentially in same container

---

## 🔒 Security Best Practices

### 1. Container Isolation
- Tools run in isolated containers
- No access to host filesystem (except mounted volumes)
- Limited network access

### 2. Resource Limits
```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

### 3. Network Policies
- Containers have limited network access
- Can restrict to specific networks
- No privileged mode

### 4. Volume Mounts
- Only mount necessary directories
- Use read-only mounts where possible
- Don't mount sensitive host directories

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check Docker is running
docker ps

# Check image exists
docker images | grep osint-tools

# View build logs
docker build -t osint-tools:latest . 2>&1 | tee build.log
```

### Tool Execution Fails

```bash
# Check container logs
docker logs osint-tools

# Test tool manually
docker exec osint-tools amass -version

# Check workspace permissions
docker exec osint-tools ls -la /workspace
```

### Permission Issues

```bash
# Fix workspace permissions
chmod 777 workspace/

# Or run container with specific user
docker run -u $(id -u):$(id -g) ...
```

---

## 📈 Scaling

### Single Container (Current)
- One container handles all tool executions
- Sequential execution
- Good for low-medium load

### Multiple Containers (Future)
- Create container pool
- Load balance tool executions
- Better for high load

### Kubernetes Deployment
- Deploy as Kubernetes pods
- Auto-scaling based on load
- Production-ready

---

## ✅ Checklist for New Tools

When implementing Docker support for a new tool:

- [ ] Import `docker_client` module
- [ ] Check for host binary availability
- [ ] Check for Docker availability
- [ ] Implement Docker execution path
- [ ] Implement host execution path
- [ ] Handle errors from both paths
- [ ] Return execution method in result
- [ ] Add logging for both paths
- [ ] Test with Docker
- [ ] Test without Docker (host binary)
- [ ] Test error cases (neither available)

---

## 📚 Reference

- **Docker Client**: `hackerdogs_tools/osint/docker_client.py`
- **Docker Setup**: `hackerdogs_tools/osint/docker/Dockerfile`
- **Example Implementation**: `hackerdogs_tools/osint/infrastructure/amass_langchain.py`
- **Docker Compose**: `hackerdogs_tools/osint/docker/docker-compose.yml`

---

**Last Updated:** 2024

