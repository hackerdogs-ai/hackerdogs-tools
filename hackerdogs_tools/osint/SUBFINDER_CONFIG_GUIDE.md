# Subfinder Configuration Guide

## Overview

Subfinder supports extensive configuration options for API keys, sources, rate limiting, and more. This guide explains how to use custom configurations with the Docker-based execution.

## Configuration Files

According to the [ProjectDiscovery documentation](https://docs.projectdiscovery.io/opensource/subfinder/install#post-install-configuration), Subfinder uses two types of config files:

### 1. Provider Config (`provider-config.yaml`)

**Default location:** `$HOME/.config/subfinder/provider-config.yaml`

This file stores API keys for various passive sources. Example:

```yaml
binaryedge:
  - 0bf8919b-aab9-42e3-9574-d3b639324597
  - ac244e2f-b635-4581-878a-33f4e79a2c13
censys:
  - ac244e2f-b635-4581-878a-33f4e79a2c13:dd510d6e-1b6e-4655-83f6-f347b363def9
certspotter: []
passivetotal:
  - [email protected]:sample_password
securitytrails: []
shodan:
  - AAAAClP1bJJSRMEYJazgwhJKrggRwKA
github:
  - ghp_lkyJGU3jv1xmwk4SDXavrLDJ4dl2pSJMzj4X
  - ghp_gkUuhkIYdQPj13ifH4KA3cXRn8JD2lqir2d4
zoomeyeapi:
  - zoomeye.hk:4f73021d-ff95-4f53-937f-83d6db719eec
quake:
  - 0cb9030c-0a40-48a3-b8c4-fca28e466ba3
```

**Note:** Composite keys (Censys, PassiveTotal, Fofa, Intelx, 360quake) need to be separated with a colon (`:`).

### 2. Flag Config (`config.yaml`)

**Default location:** `$CONFIG/subfinder/config.yaml`

This file stores default flag values.

## Using Custom Config Files

### Option 1: Mount Config Files into Docker Container

When using Docker execution, you need to mount your config files into the container:

```bash
# Mount provider config
docker run -v $HOME/.config/subfinder/provider-config.yaml:/root/.config/subfinder/provider-config.yaml \
  projectdiscovery/subfinder:latest -d example.com

# Or mount entire config directory
docker run -v $HOME/.config:/root/.config \
  projectdiscovery/subfinder:latest -d example.com
```

### Option 2: Use Custom Paths in Tool

The tools now support `provider_config` and `config` parameters:

```python
# LangChain
result = subfinder_enum.invoke({
    "runtime": runtime,
    "domain": "example.com",
    "provider_config": "/path/to/custom-provider-config.yaml",
    "config": "/path/to/custom-config.yaml"
})

# CrewAI
tool = SubfinderTool()
result = tool._run(
    domain="example.com",
    provider_config="/path/to/custom-provider-config.yaml",
    config="/path/to/custom-config.yaml"
)
```

**Important:** The config file paths must be accessible inside the Docker container. You'll need to:
1. Mount the config files when creating the container, OR
2. Copy config files into the container image, OR
3. Use volume mounts in your Docker setup

## Available Options

### Source Selection

- `sources`: Comma-separated list of specific sources (e.g., `"crtsh,github"`)
- `exclude_sources`: Comma-separated list of sources to exclude
- `all_sources`: Use all sources (slow but comprehensive)
- `recursive`: Use only sources that handle subdomains recursively

### Rate Limiting

- `rate_limit`: Maximum HTTP requests per second (e.g., `10`)

### Timeouts

- `timeout`: Seconds to wait before timing out (default: `30`)
- `max_time`: Minutes to wait for enumeration results (default: `10`)

### Output Options

- `silent`: Show only subdomains in output (default: `True`)
- `active`: Display active subdomains only (requires DNS resolution)
- `include_ip`: Include host IP in output (active only)
- `collect_sources`: Include all sources in JSON output

## Example Usage

### Basic Enumeration

```python
result = subfinder_enum.invoke({
    "runtime": runtime,
    "domain": "example.com"
})
```

### With Specific Sources

```python
result = subfinder_enum.invoke({
    "runtime": runtime,
    "domain": "example.com",
    "sources": "crtsh,github,shodan"
})
```

### With Custom Provider Config

```python
result = subfinder_enum.invoke({
    "runtime": runtime,
    "domain": "example.com",
    "provider_config": "/custom/path/provider-config.yaml",
    "sources": "shodan,github"  # Use sources that require API keys
})
```

### Active Subdomain Discovery

```python
result = subfinder_enum.invoke({
    "runtime": runtime,
    "domain": "example.com",
    "active": True,
    "include_ip": True
})
```

## Docker Setup for Config Files

To use custom config files with Docker execution, update your `docker-compose.yml`:

```yaml
services:
  osint-tools:
    image: projectdiscovery/subfinder:latest
    volumes:
      - $HOME/.config/subfinder:/root/.config/subfinder:ro
    # ... other config
```

Or when using the official Docker image directly:

```bash
docker run --rm \
  -v $HOME/.config/subfinder:/root/.config/subfinder:ro \
  projectdiscovery/subfinder:latest \
  -d example.com -s shodan,github
```

## Listing Available Sources

To see all available sources:

```bash
docker run --rm projectdiscovery/subfinder:latest -ls
```

## References

- [Subfinder Installation Guide](https://docs.projectdiscovery.io/opensource/subfinder/install#post-install-configuration)
- [Subfinder Usage Documentation](https://docs.projectdiscovery.io/opensource/subfinder/usage)

