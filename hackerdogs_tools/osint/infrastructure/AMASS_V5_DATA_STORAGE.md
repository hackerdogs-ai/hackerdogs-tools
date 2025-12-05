# Amass v5.0 Data Storage Architecture

## Overview

Based on official OWASP Amass documentation and source code analysis, Amass v5.0 uses a **file-based graph database** for data storage. This is different from earlier assumptions about SQLite.

## Storage Architecture

### Default Storage: File-Based Graph Database

**Key Points:**
- Amass v5.0 stores data in a **graph database file** (not SQLite)
- By default, the database is created in the **output directory** specified during execution
- **No PostgreSQL required** - Amass defaults to file-based storage when PostgreSQL is unavailable
- The database is **persistent** and can be reused across sessions

### Default Database Location

**On Host System:**
- **Linux/macOS**: `~/.config/amass/` (operating system's default user configuration directory)
- **Windows**: `%APPDATA%\amass\` or similar
- This is the **default** location where Amass creates its graph database

**In Docker Container:**
- Amass expects the database at `/.config/amass/` (default location)
- We mount our project directory to this location: `{project_data_dir}:/.config/amass`

### Database Structure

The graph database stores:
- **Nodes**: Domains, subdomains, IP addresses, ASNs, CIDR blocks
- **Edges**: Relationships between assets (e.g., subdomain → domain, domain → IP)
- **Metadata**: Sources, timestamps, validation status

### How Data is Stored and Accessed

#### 1. **Enumeration (`amass enum`)**
```bash
amass enum -d example.com -dir /.config/amass
```
- Populates the graph database with discovered subdomains
- Stores relationships: subdomain → domain, domain → IP
- Data persists in the database file

#### 2. **Querying (`amass subs`)**
```bash
amass subs -names -d example.com -dir /.config/amass
```
- Queries the graph database for stored results
- Returns text output (one subdomain per line)
- No need to re-enumerate - uses existing database

#### 3. **Visualization (`amass viz`)**
```bash
amass viz -dir /.config/amass -d example.com -d3 -o /output
```
- Reads from the graph database
- Generates network graphs showing relationships
- Outputs HTML/DOT/GEXF files

#### 4. **Tracking (`amass track`)**
```bash
amass track -dir /.config/amass -d example.com
```
- Compares current database state with historical data
- Identifies newly discovered assets
- Requires persistent database across sessions

## PostgreSQL vs File-Based Storage

### When PostgreSQL is Available
- Amass can connect to a PostgreSQL database server
- Provides centralized storage for multiple users/instances
- Better for enterprise deployments
- Requires external database server setup

### When PostgreSQL is NOT Available (Default)
- **Amass automatically uses file-based graph database**
- No external dependencies required
- Database file stored locally in specified directory
- **This is what we're using** - no PostgreSQL needed

## Using PostgreSQL with Amass in Docker

### Overview

When you want to use PostgreSQL instead of the file-based graph database, you need to:
1. Set up a PostgreSQL container
2. Configure Amass to connect to PostgreSQL via `config.yaml`
3. Mount the config file into the Amass container
4. Ensure network connectivity between containers

### Step 1: Set Up PostgreSQL Container

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  postgres:
    container_name: amass_postgres
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: amass
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      POSTGRES_DB: amassdb
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - amass_network

volumes:
  postgres_data:
    driver: local

networks:
  amass_network:
    driver: bridge
```

Start PostgreSQL:
```bash
docker-compose up -d postgres
```

### Step 2: Create Amass Configuration File

Create `config.yaml` in your project (e.g., `hackerdogs_tools/osint/data/amass/config.yaml`):

```yaml
# Amass Configuration for PostgreSQL
database:
  system: postgres
  url: postgres://amass:changeme@amass_postgres:5432/amassdb?sslmode=disable

# Optional: Configure data sources
scope:
  domains:
    - example.com
    - example.org
```

**Important Notes:**
- **Hostname**: Use container name (`amass_postgres`) when containers are on the same Docker network
- **Hostname**: Use `host.docker.internal` or `172.17.0.1` to connect to PostgreSQL on host
- **Hostname**: Use `localhost` only if PostgreSQL is in the same container (not recommended)
- **SSL**: Set `sslmode=disable` for local development (use SSL in production)

### Step 3: Run Amass with PostgreSQL Configuration

#### Option A: Using Docker Network (Recommended)

```bash
# Run Amass container on the same network
docker run --rm \
  --network amass_network \
  -v $(pwd)/hackerdogs_tools/osint/data/amass/config.yaml:/.config/amass/config.yaml:ro \
  -v $(pwd)/hackerdogs_tools/osint/tests/results/amass:/output \
  owaspamass/amass:latest \
  enum -d example.com -config /.config/amass/config.yaml
```

#### Option B: Connecting to Host PostgreSQL

If PostgreSQL is running on the host (not in Docker):

```yaml
# config.yaml
database:
  system: postgres
  url: postgres://amass:changeme@host.docker.internal:5432/amassdb?sslmode=disable
```

Then run:
```bash
docker run --rm \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/hackerdogs_tools/osint/data/amass/config.yaml:/.config/amass/config.yaml:ro \
  -v $(pwd)/hackerdogs_tools/osint/tests/results/amass:/output \
  owaspamass/amass:latest \
  enum -d example.com -config /.config/amass/config.yaml
```

**Note**: `--add-host=host.docker.internal:host-gateway` works on Linux. On macOS/Windows, `host.docker.internal` works by default.

### Step 4: Update Our Tools to Support PostgreSQL

To use PostgreSQL in our implementation, you can:

1. **Set environment variable**:
   ```bash
   export AMASS_USE_POSTGRES=true
   export AMASS_POSTGRES_URL="postgres://amass:changeme@amass_postgres:5432/amassdb?sslmode=disable"
   ```

2. **Modify `amass_config.py`** to check for PostgreSQL config:
   ```python
   def get_amass_config_path() -> Optional[str]:
       """Get path to Amass config.yaml if PostgreSQL is configured."""
       if os.getenv("AMASS_USE_POSTGRES") == "true":
           config_path = os.path.join(get_amass_data_dir(), "config.yaml")
           if os.path.exists(config_path):
               return config_path
       return None
   ```

3. **Update tool execution** to include `-config` flag:
   ```python
   config_path = get_amass_config_path()
   if config_path:
       # Mount config file and use it
       volumes.append(f"{config_path}:/.config/amass/config.yaml:ro")
       args.extend(["-config", "/.config/amass/config.yaml"])
   ```

### Step 5: Verify PostgreSQL Connection

Test the connection:

```bash
# Check if PostgreSQL is accessible
docker run --rm \
  --network amass_network \
  postgres:15-alpine \
  psql -h amass_postgres -U amass -d amassdb -c "SELECT version();"

# Run Amass enumeration (data will be stored in PostgreSQL)
docker run --rm \
  --network amass_network \
  -v $(pwd)/hackerdogs_tools/osint/data/amass/config.yaml:/.config/amass/config.yaml:ro \
  owaspamass/amass:latest \
  enum -d example.com -config /.config/amass/config.yaml

# Query results from PostgreSQL
docker run --rm \
  --network amass_network \
  -v $(pwd)/hackerdogs_tools/osint/data/amass/config.yaml:/.config/amass/config.yaml:ro \
  owaspamass/amass:latest \
  subs -names -d example.com -config /.config/amass/config.yaml
```

### Benefits of PostgreSQL

1. **Centralized Storage**: Multiple Amass instances can share the same database
2. **Scalability**: Better performance for large datasets
3. **Backup & Recovery**: Standard PostgreSQL backup tools
4. **Concurrent Access**: Multiple users/processes can query simultaneously
5. **Enterprise Features**: Replication, clustering, monitoring

### Migration from File-Based to PostgreSQL

To migrate existing file-based database to PostgreSQL:

1. **Export from file-based database**:
   ```bash
   docker run --rm \
     -v $(pwd)/hackerdogs_tools/osint/data/amass:/.config/amass \
     owaspamass/amass:latest \
     subs -names -d example.com > subdomains.txt
   ```

2. **Set up PostgreSQL** (as above)

3. **Re-enumerate with PostgreSQL**:
   ```bash
   docker run --rm \
     --network amass_network \
     -v $(pwd)/hackerdogs_tools/osint/data/amass/config.yaml:/.config/amass/config.yaml:ro \
     owaspamass/amass:latest \
     enum -d example.com -config /.config/amass/config.yaml
   ```

### Troubleshooting

**Connection Refused:**
- Ensure PostgreSQL container is running: `docker ps | grep postgres`
- Check network connectivity: `docker network inspect amass_network`
- Verify connection string in `config.yaml`

**Authentication Failed:**
- Verify `POSTGRES_USER` and `POSTGRES_PASSWORD` match config.yaml
- Check PostgreSQL logs: `docker logs amass_postgres`

**Config File Not Found:**
- Ensure config.yaml is mounted correctly
- Check file path: `docker exec <container> ls -la /.config/amass/`

### Example: Complete Docker Compose Setup

```yaml
version: '3.8'

services:
  postgres:
    container_name: amass_postgres
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: amass
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      POSTGRES_DB: amassdb
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - amass_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U amass"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Optional: Amass CLI container for easy access
  amass:
    image: owaspamass/amass:latest
    container_name: amass_cli
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - amass_network
    volumes:
      - ./hackerdogs_tools/osint/data/amass/config.yaml:/.config/amass/config.yaml:ro
      - ./hackerdogs_tools/osint/tests/results/amass:/output
    command: tail -f /dev/null  # Keep container running
    # Usage: docker exec amass_cli amass enum -d example.com -config /.config/amass/config.yaml

volumes:
  postgres_data:
    driver: local

networks:
  amass_network:
    driver: bridge
```

**Usage:**
```bash
# Start services
docker-compose up -d

# Run enumeration
docker exec amass_cli amass enum -d example.com -config /.config/amass/config.yaml

# Query results
docker exec amass_cli amass subs -names -d example.com -config /.config/amass/config.yaml
```

## Our Implementation

### Current Setup
1. **Database Directory**: `hackerdogs_tools/osint/data/amass/`
   - Mounted to `/.config/amass` in Docker container
   - Stores the graph database file(s)

2. **Results Directory**: `hackerdogs_tools/osint/tests/results/amass/`
   - Mounted to `/output` in Docker container
   - Stores visualization outputs (HTML, DOT, GEXF)

### Why `/.config/amass` in Container?

- This is Amass's **default database location**
- The `-dir` flag specifies where the database directory is located
- We mount our project directory to this default location
- Amass creates/accesses the graph database file in this directory

### Database File Format

The graph database is stored as:
- **File-based format** (exact format depends on Amass implementation)
- Likely uses a graph database library (possibly BadgerDB, BoltDB, or similar)
- **Not SQLite** - it's a graph database optimized for relationship queries

## Key Takeaways

1. ✅ **No PostgreSQL Required**: Amass defaults to file-based graph database
2. ✅ **Persistent Storage**: Database persists across tool invocations
3. ✅ **Default Location**: `~/.config/amass/` on host, `/.config/amass/` in container
4. ✅ **Our Mount is Correct**: `{project_data_dir}:/.config/amass` is the right approach
5. ✅ **Graph Database**: Stores nodes (domains, IPs) and edges (relationships)

## References

- [OWASP Amass User Guide](https://github.com/OWASP/Amass/wiki/User-Guide)
- [Amass v5.0 Architecture](https://deepwiki.com/owasp-amass/amass/1.1-architecture-overview)
- [Amass v5.0 First Look](https://www.devious-plan.com/blog/owasp-amass-5-first-look)

## Verification

To verify the database location and format:

```bash
# Check what files Amass creates
docker run --rm -v ~/.config/amass:/.config/amass owaspamass/amass:latest enum -d example.com
ls -la ~/.config/amass/

# Query the database
docker run --rm -v ~/.config/amass:/.config/amass owaspamass/amass:latest subs -names -d example.com
```

The database files will be created in the mounted directory, confirming our mount strategy is correct.

