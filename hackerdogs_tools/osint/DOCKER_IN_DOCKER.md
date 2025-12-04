# 🐳 Docker-in-Docker: Tools Calling Binaries in Another Container

## Question

**Can tools running in Docker call binaries in another Docker container?**

**Answer: YES!** There are several approaches, each with different trade-offs.

---

## 🏗️ Architecture Options

### Option 1: Docker Socket Mounting (Recommended)

**How it works:**
- Mount the host's Docker socket (`/var/run/docker.sock`) into your application container
- Your application container can now execute `docker` commands that control containers on the host
- The OSINT tools run in a separate container managed by your application

```
┌─────────────────────────────────────┐
│  Host Machine                        │
│                                      │
│  ┌──────────────────────────────┐   │
│  │ Application Container         │   │
│  │ (Your Python Tools)           │   │
│  │                               │   │
│  │ docker exec osint-tools ...   │   │
│  └───────────┬───────────────────┘   │
│              │                        │
│              │ Docker Socket          │
│              │ /var/run/docker.sock  │
│              ▼                        │
│  ┌──────────────────────────────┐   │
│  │ Docker Daemon (Host)          │   │
│  └───────────┬──────────────────┘   │
│              │                        │
│              ▼                        │
│  ┌──────────────────────────────┐   │
│  │ OSINT Tools Container          │   │
│  │ (amass, nuclei, etc.)         │   │
│  └──────────────────────────────┘   │
└──────────────────────────────────────┘
```

**Pros:**
- ✅ Simple to implement
- ✅ No Docker daemon in container (lighter)
- ✅ Uses host's Docker (better performance)
- ✅ Standard approach

**Cons:**
- ⚠️ Security risk: Container has full Docker access
- ⚠️ Requires privileged access to socket

**Implementation:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    image: your-app:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Mount Docker socket
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock

  osint-tools:
    image: osint-tools:latest
    # Separate container for OSINT binaries
```

### Option 2: Docker-in-Docker (DinD)

**How it works:**
- Run a full Docker daemon inside your application container
- Your application can create/manage its own containers
- Complete isolation from host Docker

```
┌─────────────────────────────────────┐
│  Host Machine                        │
│                                      │
│  ┌──────────────────────────────┐   │
│  │ Application Container         │   │
│  │                               │   │
│  │  ┌────────────────────────┐  │   │
│  │  │ Docker Daemon (DinD)   │  │   │
│  │  └───────────┬────────────┘  │   │
│  │              │                 │   │
│  │              ▼                 │   │
│  │  ┌────────────────────────┐  │   │
│  │  │ OSINT Tools Container    │  │   │
│  │  └────────────────────────┘  │   │
│  └──────────────────────────────┘   │
└──────────────────────────────────────┘
```

**Pros:**
- ✅ Complete isolation
- ✅ No access to host Docker
- ✅ Can manage containers independently

**Cons:**
- ❌ Heavier (full Docker daemon in container)
- ❌ Requires privileged mode
- ❌ More complex setup
- ❌ Performance overhead

**Implementation:**
```yaml
# docker-compose.yml
services:
  app:
    image: docker:dind  # Docker-in-Docker image
    privileged: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

### Option 3: Sidecar Pattern (Recommended for Production)

**How it works:**
- Application container and OSINT tools container run side-by-side
- Communicate via shared volumes or network
- Application container triggers execution via shared filesystem or API

```
┌─────────────────────────────────────┐
│  Host Machine                        │
│                                      │
│  ┌──────────────────┐  ┌──────────┐│
│  │ App Container     │  │ OSINT     ││
│  │ (Python Tools)    │  │ Container ││
│  │                   │  │ (Binaries)││
│  │ Write: task.json  │  │           ││
│  └────────┬─────────┘  └─────┬─────┘│
│           │                  │      │
│           └─── Shared ──────┘      │
│              Volume                  │
│         /workspace/                  │
└──────────────────────────────────────┘
```

**Pros:**
- ✅ Clean separation of concerns
- ✅ No Docker socket mounting needed
- ✅ Better security
- ✅ Easier to scale independently

**Cons:**
- ⚠️ Requires orchestration (Kubernetes, Docker Compose)
- ⚠️ More complex communication

**Implementation:**
```yaml
# docker-compose.yml
services:
  app:
    image: your-app:latest
    volumes:
      - ./workspace:/workspace
    depends_on:
      - osint-worker

  osint-worker:
    image: osint-tools:latest
    volumes:
      - ./workspace:/workspace
    command: python3 /app/worker.py  # Watches for tasks
```

---

## 🔧 Implementation for Your OSINT Tools

### Current Architecture

Your current `docker_client.py` uses **Docker Socket Mounting** approach:

```python
# docker_client.py executes:
subprocess.run(["docker", "exec", "osint-tools", "amass", ...])
```

This works when:
- ✅ Running on host (current setup)
- ✅ Running in container with socket mounted

### Updated for Container Deployment

To make it work when your tools run in Docker:

```python
# docker_client.py
class DockerOSINTClient:
    def __init__(self):
        # Check if we're in a container
        self.in_container = os.path.exists("/.dockerenv")
        
        if self.in_container:
            # Use Docker socket if mounted
            self.docker_socket = "/var/run/docker.sock"
            if not os.path.exists(self.docker_socket):
                raise ValueError(
                    "Docker socket not mounted. "
                    "Add: -v /var/run/docker.sock:/var/run/docker.sock"
                )
```

### Docker Compose for Full Stack

```yaml
version: '3.8'

services:
  # Your application (LangChain/CrewAI agents)
  app:
    build: .
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Mount socket
      - ./workspace:/workspace
    environment:
      - OSINT_DOCKER_IMAGE=osint-tools:latest
      - OSINT_DOCKER_CONTAINER=osint-tools
    depends_on:
      - osint-tools

  # OSINT binaries container
  osint-tools:
    build:
      context: ./hackerdogs_tools/osint/docker
      dockerfile: Dockerfile
    image: osint-tools:latest
    volumes:
      - ./workspace:/workspace
    command: tail -f /dev/null  # Keep running
```

---

## 🔒 Security Considerations

### Docker Socket Mounting Risks

**⚠️ CRITICAL SECURITY RISK:**

Mounting `/var/run/docker.sock` gives the container **full control** over the host's Docker daemon:

- Can create/delete any container
- Can access host filesystem
- Can escape container isolation
- Can access other containers

**Mitigation:**
1. **Use read-only socket** (if supported)
2. **Limit container capabilities**
3. **Use Docker API with authentication**
4. **Run in isolated network**
5. **Use Docker context/namespace isolation**

### Safer Alternative: Docker API with Auth

```python
import docker

client = docker.DockerClient(
    base_url='unix:///var/run/docker.sock',
    # Add authentication/authorization
)
```

### Best Practice: Sidecar Pattern

For production, use **Sidecar Pattern** instead:
- No Docker socket access needed
- Communication via shared volumes or API
- Better security boundaries

---

## 📊 Comparison Table

| Approach | Complexity | Security | Performance | Use Case |
|----------|-----------|----------|--------------|----------|
| **Socket Mounting** | Low | ⚠️ Medium | ✅ High | Development, trusted environments |
| **Docker-in-Docker** | High | ✅ High | ⚠️ Medium | Complete isolation needed |
| **Sidecar Pattern** | Medium | ✅ High | ✅ High | Production, scalable systems |

---

## 🚀 Recommended Approach

### For Development: Docker Socket Mounting

```yaml
# docker-compose.dev.yml
services:
  app:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

### For Production: Sidecar Pattern

```yaml
# docker-compose.prod.yml
services:
  app:
    # No socket mounting
    volumes:
      - ./workspace:/workspace
    
  osint-worker:
    # Separate worker service
    volumes:
      - ./workspace:/workspace
```

---

## 💡 Code Example: Updated docker_client.py

```python
import os
import subprocess
from typing import Optional

class DockerOSINTClient:
    def __init__(self):
        # Detect if running in container
        self.in_container = os.path.exists("/.dockerenv")
        self.docker_socket = "/var/run/docker.sock"
        
        if self.in_container:
            # Check if socket is mounted
            if not os.path.exists(self.docker_socket):
                raise ValueError(
                    "Running in container but Docker socket not mounted.\n"
                    "Add to docker-compose.yml:\n"
                    "  volumes:\n"
                    "    - /var/run/docker.sock:/var/run/docker.sock"
                )
        
        # Check Docker availability
        self.docker_available = self._check_docker_available()
    
    def execute(self, tool: str, args: list) -> dict:
        """Execute tool in Docker container."""
        # Works the same whether in container or on host
        cmd = ["docker", "exec", "osint-tools", tool] + args
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr
        }
```

---

## ✅ Summary

**Yes, tools in Docker can call binaries in another Docker container!**

**Best Approaches:**
1. **Development**: Docker socket mounting (simple, fast)
2. **Production**: Sidecar pattern (secure, scalable)

**Your current `docker_client.py` already supports this!** Just mount the Docker socket when running your application in a container.

---

**Last Updated:** 2024

