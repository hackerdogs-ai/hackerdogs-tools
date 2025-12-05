# Amass v5.0.0 Workflow - Correct Implementation

## Critical Changes in v5.0.0

1. **No `-json` flag** - This flag doesn't exist in v5.0.0
2. **Graph database storage** - Results are stored in a file-based graph database (not SQLite, not PostgreSQL)
3. **Two-step process**:
   - Step 1: `amass enum -d domain` (populates graph database)
   - Step 2: `amass subs -names -d domain` (queries graph database)

## Required Volume Mount

**CRITICAL**: Must mount Amass config directory:
```bash
-v ~/.config/amass:/.config/amass
```

This is where Amass stores its database.

## Correct Workflow

### 1. Enumeration (Populate Database)
```bash
docker run --rm -v ~/.config/amass:/.config/amass owaspamass/amass:latest enum -d owasp.org
```

### 2. Query Results (Get Subdomains)
```bash
docker run --rm -v ~/.config/amass:/.config/amass owaspamass/amass:latest subs -names -d owasp.org
```

### 3. Query Results with IPs
```bash
docker run --rm -v ~/.config/amass:/.config/amass owaspamass/amass:latest subs -names -ip -d owasp.org
```

### 4. Query Summary (ASN/Netblocks)
```bash
docker run --rm -v ~/.config/amass:/.config/amass owaspamass/amass:latest subs -summary -d owasp.org
```

## Output Format

- `subs -names` returns: One subdomain per line (text)
- `subs -names -ip` returns: Subdomain and IP on same line (text)
- `subs -summary` returns: ASN table with netblocks (text)

**NO JSON OUTPUT** - Must parse text output.

## Implementation Strategy

1. **Create/ensure Amass config directory exists** on host: `~/.config/amass`
2. **Mount it to container**: `/.config/amass`
3. **Run enum first** to populate database
4. **Run subs to query** results
5. **Parse text output** to extract data
6. **Return JSON** (our format, not Amass's)

## Example Implementation

```python
# Step 1: Ensure config directory exists
import os
home = os.path.expanduser("~")
amass_config = os.path.join(home, ".config", "amass")
os.makedirs(amass_config, exist_ok=True)

# Step 2: Mount volume
volumes = [f"{amass_config}:/.config/amass"]

# Step 3: Run enum (populate DB)
enum_result = execute_in_docker("amass", ["enum", "-d", domain], volumes=volumes, timeout=timeout)

# Step 4: Run subs (query DB)
subs_result = execute_in_docker("amass", ["subs", "-names", "-ip", "-d", domain], volumes=volumes, timeout=60)

# Step 5: Parse text output
subdomains = []
ips = []
for line in subs_result["stdout"].strip().split('\n'):
    parts = line.strip().split()
    if len(parts) >= 1:
        subdomains.append(parts[0])
    if len(parts) >= 2:
        ips.append(parts[1])

# Step 6: Return JSON
return json.dumps({
    "status": "success",
    "domain": domain,
    "subdomains": subdomains,
    "ips": ips,
    "count": len(subdomains)
})
```

## Intel Tool

For intel (ASN/CIDR), use:
```bash
amass enum -asn 13374  # Populate DB
amass subs -names -d <discovered_domains>  # Query results
```

## Viz Tool

Viz needs database with enumeration data:
```bash
amass viz -d3 -dir /.config/amass -d domain
```

## Track Tool

Track compares database snapshots:
```bash
amass track -dir /.config/amass -d domain
```

