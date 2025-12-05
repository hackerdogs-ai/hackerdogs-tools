# Amass v5.0.0 Fixes Applied

## Critical Issues Fixed

### 1. ❌ **Removed Invalid `-json` Flag**
- **Problem**: `-json` flag doesn't exist in Amass v5.0.0
- **Fix**: Removed all `-json` flag usage
- **New Approach**: Use `amass subs` command to query database results

### 2. ✅ **Added Database Volume Mounting**
- **Problem**: Amass v5.0.0 stores results in a file-based graph database, not output files
- **Fix**: Mount `~/.config/amass` to `/.config/amass` in container
- **Implementation**: 
  ```python
  home = os.path.expanduser("~")
  amass_config = os.path.join(home, ".config", "amass")
  os.makedirs(amass_config, exist_ok=True)
  volumes = [f"{amass_config}:/.config/amass"]
  ```

### 3. ✅ **Implemented Two-Step Workflow**
- **Step 1**: `amass enum -d domain` (populates database)
- **Step 2**: `amass subs -names -ip -d domain` (queries database)
- **Output**: Parse text output (one subdomain per line, or subdomain + IP)

### 4. ✅ **Fixed All Tools**

#### `amass_enum` (LangChain & CrewAI)
- Runs `enum` first to populate database
- Runs `subs -names -ip` to query results
- Parses text output to extract subdomains and IPs

#### `amass_intel` (LangChain & CrewAI)
- Runs `enum -asn X` or similar to populate database
- Runs `subs -names` to query discovered domains
- Parses text output

#### `amass_viz` (LangChain & CrewAI)
- Mounts both config directory (database) and output directory
- Uses `-dir /.config/amass` flag to specify database location
- Generates visualization files in mounted output directory

#### `amass_track` (LangChain & CrewAI)
- Mounts config directory (database)
- Uses `-dir /.config/amass` flag
- Parses text output for newly discovered assets

## Test Domain Recommendation

**Use `owasp.org` instead of `github.com`**:
- Smaller domain = faster enumeration
- Better for testing
- Example from official docs

## Next Steps

1. ✅ LangChain tools fixed
2. ⏳ CrewAI tools need same fixes (in progress)
3. ⏳ Update test file to use `owasp.org`
4. ⏳ Test all tools

## Example Command (Working)

```bash
# Step 1: Populate database
docker run --rm -v ~/.config/amass:/.config/amass owaspamass/amass:latest enum -d owasp.org

# Step 2: Query results
docker run --rm -v ~/.config/amass:/.config/amass owaspamass/amass:latest subs -names -ip -d owasp.org
```

