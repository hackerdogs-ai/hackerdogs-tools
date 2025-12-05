# Amass Data Directory Structure

## Overview

Amass tools use a project-relative directory structure for storing database and results, following the project's folder conventions.

**Important**: Amass v5.0 uses a **file-based graph database** (not SQLite). When PostgreSQL is not available, Amass automatically defaults to this file-based storage. No external database server is required.

## Directory Structure

```
hackerdogs_tools/osint/
├── data/
│   └── amass/              # Amass graph database storage (file-based)
│       └── *.db            # Graph database files (created by Amass)
├── tests/
│   └── results/
│       └── amass/          # Amass visualization and output files
│           └── *.html      # D3 visualizations
│           └── *.dot       # Graphviz files
│           └── *.gexf      # Gephi files
```

## Configuration

### Default Locations

1. **Database Directory**: `hackerdogs_tools/osint/data/amass/`
   - Stores Amass **graph database file** (file-based, no PostgreSQL required)
   - Created automatically on first use
   - Mounted to `/.config/amass` in Docker container (Amass default location)

2. **Results Directory**: `hackerdogs_tools/osint/tests/results/amass/`
   - Stores visualization outputs (HTML, DOT, GEXF)
   - Created automatically on first use
   - Mounted to `/output` in Docker container

### Custom Locations (Environment Variables)

You can override default locations using environment variables:

```bash
# Custom database directory
export AMASS_DATA_DIR="/path/to/custom/amass/data"

# Custom results directory
export AMASS_RESULTS_DIR="/path/to/custom/amass/results"
```

## Docker Volume Mounts

The tools automatically mount:

1. **Database Volume**: `{AMASS_DATA_DIR}:/.config/amass`
   - Where Amass stores its graph database (file-based)
   - Required for `enum`, `intel`, `viz`, and `track` operations

2. **Results Volume**: `{AMASS_RESULTS_DIR}:/output` (for viz only)
   - Where visualization files are written
   - Only used by `amass_viz` tool

## Usage in Code

```python
from hackerdogs_tools.osint.amass_config import get_amass_data_dir, get_amass_results_dir

# Get database directory
db_dir = get_amass_data_dir()
# Returns: /path/to/hackerdogs_tools/osint/data/amass

# Get results directory
results_dir = get_amass_results_dir()
# Returns: /path/to/hackerdogs_tools/osint/tests/results/amass
```

## Why Project-Relative?

1. **Version Control**: Database can be excluded via `.gitignore`, but structure is clear
2. **Portability**: Works across different machines without hardcoding user paths
3. **Organization**: Follows project structure conventions
4. **Results Location**: Visualization files stored alongside test results for easy access

## Migration from `~/.config/amass`

If you have existing Amass data in `~/.config/amass`, you can:

1. **Copy data**:
   ```bash
   cp -r ~/.config/amass/* hackerdogs_tools/osint/data/amass/
   ```

2. **Or set environment variable**:
   ```bash
   export AMASS_DATA_DIR="$HOME/.config/amass"
   ```

## Notes

- Directories are created automatically if they don't exist
- Database persists across tool invocations
- Results directory is separate from database for clarity
- All paths are absolute when passed to Docker

