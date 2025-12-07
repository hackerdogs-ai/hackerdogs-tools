# 🐳 Docker Quick Start for OSINT Tools

## Why Docker?

Instead of installing binaries on your host OS, run them in isolated Docker containers:
- ✅ **No host dependencies** - Keep your system clean
- ✅ **Isolation** - Tools run in secure containers
- ✅ **Consistency** - Same environment everywhere
- ✅ **Easy deployment** - One Docker image contains everything

---

## 🚀 3-Step Setup

### Step 1: Build Docker Image

```bash
cd hackerdogs_tools/osint/docker
docker build -t osint-tools:latest .
```

**Time:** ~5-10 minutes (downloads and compiles all tools)

### Step 2: Start Container

```bash
# Option A: Docker Compose (recommended)
# This automatically starts Tor proxy for OnionSearch
docker-compose up -d

# Option B: Manual (without Tor proxy)
docker run -d --name osint-tools osint-tools:latest

# Option C: Manual with Tor proxy (for OnionSearch)
# First, start Tor proxy
docker run -d --name tor-proxy -p 9050:9050 dperson/torproxy:latest

# Then start osint-tools with Tor proxy
docker run -d \
  --name osint-tools \
  --network host \
  -e TOR_PROXY=127.0.0.1:9050 \
  osint-tools:latest
```

### Step 3: Use Tools

```python
from hackerdogs_tools.osint.infrastructure.amass_langchain import amass_enum

# Automatically uses Docker if binary not on host
result = amass_enum(runtime, domain="example.com")
```

**That's it!** Tools automatically detect and use Docker.

---

## 🔍 How It Works

### Automatic Detection

Tools check in this order:
1. **Host binary** - If `amass` exists on host, use it
2. **Docker container** - If binary not found, use Docker
3. **Error** - If neither available, return helpful error

### Execution Flow

```
Tool Call
    │
    ├─→ Binary on host? → YES → Use subprocess
    │
    └─→ NO → Docker available? → YES → Use docker exec
        │
        └─→ NO → Return error with setup instructions
```

---

## 📦 What's in the Docker Image?

### Binary Tools (Go/C)
- Amass, Nuclei, Subfinder, Masscan, ZMap
- waybackurls, ExifTool, YARA

### Python Tools
- sublist3r, dnsrecon, theHarvester
- sherlock-project, maigret, ghunt, holehe
- onionsearch (Dark Web search - requires Tor proxy)
- scrapy, waybackpy, exifread

**Total:** All 22 OSINT tools in one image!

---

## 🧪 Test Setup

```bash
# Test Docker client
python -c "
from hackerdogs_tools.osint.docker_client import DockerOSINTClient
client = DockerOSINTClient()
print(client.test())
"

# Test a tool
python -c "
from hackerdogs_tools.osint.infrastructure.amass_langchain import amass_enum
from langchain.tools import ToolRuntime
runtime = ToolRuntime(state={'user_id': 'test'})
result = amass_enum(runtime, domain='example.com')
print(result)
"
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Docker image name
export OSINT_DOCKER_IMAGE="osint-tools:latest"

# Container name
export OSINT_DOCKER_CONTAINER="osint-tools"

# Docker runtime (docker or podman)
export OSINT_DOCKER_RUNTIME="docker"
```

### Docker Compose

Edit `docker/docker-compose.yml` to adjust:
- **Tor Proxy** - Required for OnionSearch (Dark Web searches)
- Resource limits (CPU/memory)
- Volume mounts
- Network settings

**Tor Proxy Configuration:**
- Automatically included in `docker-compose.yml`
- Uses `dperson/torproxy:latest` image
- Exposes SOCKS5 proxy on port `9050`
- Health check ensures Tor is ready before OSINT tools start
- OnionSearch automatically connects via `tor-proxy:9050` (Docker service name)

---

## 📊 Performance

- **Container startup**: ~1-2 seconds (if image cached)
- **Tool execution**: Same speed as native binary
- **Overhead**: Minimal (~0.05-0.1s per execution)

---

## 🐛 Troubleshooting

### Docker Not Running

```bash
# Check Docker
docker ps

# Start Docker Desktop (macOS) or
sudo systemctl start docker  # Linux
```

### Container Not Found

```bash
# Rebuild image
cd hackerdogs_tools/osint/docker
docker build -t osint-tools:latest .
```

### Permission Denied

```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

### OnionSearch Not Working (Tor Proxy Issues)

```bash
# Check Tor proxy is running
docker ps | grep tor-proxy

# Check Tor logs
docker logs tor-proxy

# Test Tor connection
docker exec osint-tools curl --socks5-hostname tor-proxy:9050 https://check.torproject.org/api/ip

# If Tor not running, restart services
docker-compose restart tor-proxy
```

---

## 📚 More Information

- **Full Setup Guide**: `DOCKER_SETUP.md`
- **Implementation Guide**: `DOCKER_IMPLEMENTATION_GUIDE.md`
- **Docker README**: `docker/README.md`

---

**Ready to go!** Build the image and start using tools. 🚀

