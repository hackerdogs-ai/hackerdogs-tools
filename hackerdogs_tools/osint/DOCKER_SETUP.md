# 🐳 Docker-Based OSINT Tools Architecture

## Overview

Instead of installing binaries on the host OS, we run them in isolated Docker containers. This provides:
- ✅ **Security**: Tools run in isolated containers
- ✅ **Consistency**: Same environment across dev/staging/prod
- ✅ **Easy Deployment**: No binary installation needed
- ✅ **Scalability**: Can run multiple containers in parallel
- ✅ **Clean Host**: No binary dependencies on host system

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Python Application              │
│  (LangChain/CrewAI Tools)              │
└──────────────┬──────────────────────────┘
               │
               │ Docker API / docker exec
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌─────────┐         ┌─────────┐
│ Amass   │         │ Nuclei  │
│ Container│        │ Container│
└─────────┘         └─────────┘
    │                     │
    └──────────┬──────────┘
               │
               ▼
        ┌──────────────┐
        │  Docker      │
        │  Engine      │
        └──────────────┘
```

---

## 📦 Docker Images Strategy

### Option 1: Single Multi-Tool Image (Recommended)
One Docker image with all OSINT binaries installed.

**Pros:**
- Single image to manage
- Faster startup (image already pulled)
- Less disk space

**Cons:**
- Larger image size
- All tools in one container

### Option 2: Individual Tool Images
Separate Docker image for each tool.

**Pros:**
- Smaller individual images
- Better isolation
- Can update tools independently

**Cons:**
- More images to manage
- More Docker pulls

**Recommendation:** Use **Option 1** (single multi-tool image) for simplicity.

---

## 🚀 Quick Start

### 1. Build Docker Image

```bash
cd hackerdogs_tools/osint/docker
docker build -t osint-tools:latest .
```

### 2. Start Docker Container

```bash
docker run -d --name osint-tools \
  -v /var/run/docker.sock:/var/run/docker.sock \
  osint-tools:latest
```

### 3. Use in Python Code

```python
from hackerdogs_tools.osint.infrastructure.amass_langchain import amass_enum

# Tool automatically uses Docker if binary not found
result = amass_enum(runtime, domain="example.com")
```

---

## 📁 File Structure

```
hackerdogs_tools/osint/
├── docker/
│   ├── Dockerfile              # Multi-tool OSINT image
│   ├── docker-compose.yml      # Orchestration
│   ├── requirements.txt        # Python dependencies for container
│   └── entrypoint.sh           # Container entrypoint
├── docker_client.py            # Docker client utility
└── ...
```

---

## 🔧 Implementation Details

### Docker Client Utility

The `docker_client.py` module provides:
- Docker container management
- Tool execution via `docker exec`
- Automatic container lifecycle management
- Error handling and logging

### Tool Implementation Pattern

Tools check for binary availability:
1. **First**: Try to use binary on host (if available)
2. **Fallback**: Use Docker container
3. **Error**: If Docker not available, return helpful error

---

## 🛠️ Setup Instructions

### Step 1: Create Docker Image

See `docker/Dockerfile` for complete setup.

### Step 2: Configure Docker Client

Set environment variables:
```bash
export OSINT_DOCKER_IMAGE="osint-tools:latest"
export OSINT_DOCKER_RUNTIME="docker"  # or "podman"
```

### Step 3: Test Docker Setup

```bash
python -c "from hackerdogs_tools.osint.docker_client import DockerOSINTClient; client = DockerOSINTClient(); print(client.test())"
```

---

## 🔒 Security Considerations

1. **Container Isolation**: Tools run in isolated containers
2. **Network Policies**: Containers have limited network access
3. **Resource Limits**: Set CPU/memory limits per container
4. **Read-Only Filesystem**: Containers use read-only filesystem where possible
5. **No Privileged Mode**: Containers run without --privileged

---

## 📊 Performance

- **Container Startup**: ~1-2 seconds (if image cached)
- **Tool Execution**: Same as native binary (minimal overhead)
- **Parallel Execution**: Can run multiple containers simultaneously

---

## 🚨 Troubleshooting

### Docker Not Running
```bash
# Check Docker status
docker ps

# Start Docker
# macOS: Open Docker Desktop
# Linux: sudo systemctl start docker
```

### Permission Denied
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

### Container Not Found
```bash
# Pull/build image
docker build -t osint-tools:latest hackerdogs_tools/osint/docker/
```

---

**See `docker/Dockerfile` and `docker_client.py` for implementation details.**

