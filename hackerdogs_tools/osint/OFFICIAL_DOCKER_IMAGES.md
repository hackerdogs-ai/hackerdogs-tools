# Official Docker Images for OSINT Tools

## Overview

Many OSINT tools provide official Docker images that can be used directly without building custom containers. This approach offers several advantages:

- ✅ **Always up-to-date** - Official images are maintained by tool authors
- ✅ **No build required** - Pull and run immediately
- ✅ **Reliable** - Tested and maintained by the tool maintainers
- ✅ **Simpler** - No need to manage custom Dockerfiles

---

## Supported Official Images

### ProjectDiscovery Tools

#### Subfinder
- **Image:** `projectdiscovery/subfinder:latest`
- **Documentation:** https://docs.projectdiscovery.io/opensource/subfinder/running
- **Usage:**
  ```bash
  docker run --rm projectdiscovery/subfinder:latest -d example.com -oJ -
  ```
- **Status:** ✅ Implemented - Uses official image automatically

#### Nuclei
- **Image:** `projectdiscovery/nuclei:latest`
- **Documentation:** https://docs.projectdiscovery.io/opensource/nuclei/running
- **Usage:**
  ```bash
  docker run --rm projectdiscovery/nuclei:latest -u https://example.com -jsonl
  ```
- **Status:** ✅ Implemented - Uses official image automatically

---

## How It Works

The `docker_client.py` module automatically detects when a tool has an official Docker image and uses it instead of the custom `osint-tools` container.

### Execution Flow

1. **Check for Official Image**
   - If tool has an official image → Use `docker run` with official image
   - Otherwise → Use `docker exec` in custom `osint-tools` container

2. **Official Image Execution**
   - Uses `docker run --rm` (auto-removes container after execution)
   - No need for persistent container
   - Each execution is isolated

3. **Custom Container Execution**
   - Uses existing `osint-tools:latest` container
   - Requires container to be running
   - Shared container for multiple tools

---

## Adding More Official Images

To add support for more official Docker images, update `docker_client.py`:

```python
official_images = {
    "subfinder": "projectdiscovery/subfinder:latest",
    "nuclei": "projectdiscovery/nuclei:latest",
    # Add more here:
    # "amass": "caffix/amass:latest",  # Example
}
```

---

## Benefits

### For Subfinder
- ✅ Uses official ProjectDiscovery image
- ✅ Always latest version
- ✅ No need to build custom image
- ✅ Reference: https://docs.projectdiscovery.io/opensource/subfinder/running

### For Nuclei
- ✅ Uses official ProjectDiscovery image
- ✅ Always latest templates
- ✅ Official support

---

## Migration Path

Tools will automatically use official images when available:

1. **First run:** Pulls official image (if not already pulled)
2. **Subsequent runs:** Uses cached image
3. **Fallback:** If official image fails, can fall back to custom container

---

## Example: Subfinder with Official Image

```python
from hackerdogs_tools.osint.docker_client import execute_in_docker

# Automatically uses projectdiscovery/subfinder:latest
result = execute_in_docker("subfinder", ["-d", "example.com", "-oJ", "-"])

# Result includes execution_method: "official_docker_image"
print(result["execution_method"])  # "official_docker_image"
```

---

## References

- **Subfinder Docker:** https://docs.projectdiscovery.io/opensource/subfinder/running
- **Nuclei Docker:** https://docs.projectdiscovery.io/opensource/nuclei/running
- **ProjectDiscovery Images:** https://hub.docker.com/u/projectdiscovery

---

*Last Updated: 2024*

