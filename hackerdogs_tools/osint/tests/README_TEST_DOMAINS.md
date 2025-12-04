# Test Domains Utility

## Overview

The `test_domains.py` module provides random domain selection from **mixed legitimate and malicious domains** for testing OSINT tools. This ensures tests use **real, valid domains** instead of reserved domains like `example.com`, and allows testing against both legitimate and known malicious domains.

## Domain Sources

### Legitimate Domains
- **Source:** `opendns-random-domains.txt`
- **Count:** ~10,000 domains
- **Purpose:** Test tools against normal, legitimate domains

### Malicious Domains
- **Sources:**
  - `blackbook/blackbook.txt` (~18,150 domains)
  - `malicious-domains/full-domains-aa.txt` (~120,261 domains)
  - `malicious-domains/full-domains-ab.txt` (~19,073 domains)
  - `malicious-domains/full-domains-ac.txt` (~2,212 domains)
- **Total:** ~160,000 malicious domains (deduplicated to ~144,236)
- **Purpose:** Test tools against known malicious/compromised domains

### Mixed Pool
- **Total:** ~154,236 domains (good + malicious combined)
- **Default:** Returns random domains from mixed pool

## Why Not example.com?

`example.com` is a **reserved domain** (RFC 2606) that:
- ❌ May not resolve properly in all contexts
- ❌ May be blocked by some security tools
- ❌ Doesn't provide realistic test scenarios
- ❌ May not have actual DNS records

## Usage

### Basic Usage (Mixed - Default)

```python
from hackerdogs_tools.osint.test_domains import get_random_domain

# Get a single random domain (mixed: good or malicious)
domain = get_random_domain()
print(domain)  # e.g., "webmagnat.ro" or "statsrvv.com"
```

### Domain Type Selection

```python
from hackerdogs_tools.osint.test_domains import get_random_domain

# Get only legitimate domains
good_domain = get_random_domain("good")
print(good_domain)  # e.g., "webmagnat.ro"

# Get only malicious domains
malicious_domain = get_random_domain("malicious")
print(malicious_domain)  # e.g., "statsrvv.com"

# Get mixed (default)
mixed_domain = get_random_domain("mixed")  # or just get_random_domain()
```

### In Tests

```python
from hackerdogs_tools.osint.test_domains import get_random_domain

def test_subfinder_standalone(self):
    runtime = ToolRuntime(state={"user_id": "test_user"})
    
    # Use a random real domain (mixed by default)
    test_domain = get_random_domain()
    
    result = subfinder_enum(
        runtime=runtime,
        domain=test_domain, recursive=False, silent=True
    )
    # ... rest of test
```

### Multiple Domains

```python
from hackerdogs_tools.osint.test_domains import get_random_domains

# Get 5 unique random domains (mixed)
domains = get_random_domains(count=5, unique=True)
print(domains)  # Mix of good and malicious domains

# Get only good domains
good_domains = get_random_domains(count=5, domain_type="good")

# Get only malicious domains
malicious_domains = get_random_domains(count=5, domain_type="malicious")

# Get mixed with specific ratio (80% good, 20% malicious)
balanced = get_random_domains(count=10, ratio=0.8)
```

## Available Functions

### `get_random_domain(domain_type: str = "mixed") -> str`
Get a single random domain from the specified pool.
- `domain_type`: `"good"`, `"malicious"`, or `"mixed"` (default)
- Returns: A random domain name

### `get_random_domains(count: int = 1, unique: bool = True, domain_type: str = "mixed", ratio: float = None) -> List[str]`
Get multiple random domains.
- `count`: Number of domains to return
- `unique`: If True, ensure all domains are unique
- `domain_type`: `"good"`, `"malicious"`, or `"mixed"` (default)
- `ratio`: For `"mixed"` type, ratio of good to malicious (0.0-1.0)
  - `0.5` = 50% good, 50% malicious
  - `0.8` = 80% good, 20% malicious
  - `None` = Random mix (default)

### `get_domains_count(domain_type: str = "mixed") -> int`
Get the total number of available domains.
- `domain_type`: `"good"`, `"malicious"`, or `"mixed"` (default)
- Returns: Count of domains in specified pool

### `reset_cache() -> None`
Reset all domain caches (useful if files are updated).

## Domain Statistics

Current domain counts:
- **Good domains:** ~10,000 (from OpenDNS)
- **Malicious domains:** ~144,236 (from blackbook + malicious-domains files)
- **Total (mixed):** ~154,236 domains

All domains are:
- Real, resolvable domains
- One domain per line
- Deduplicated (malicious domains are deduplicated across all sources)

## Benefits

✅ **Real domains** - Actual, resolvable domains  
✅ **Variety** - 154,000+ different domains  
✅ **Mixed testing** - Test against both legitimate and malicious domains  
✅ **Random** - Different domain each test run  
✅ **No conflicts** - Not reserved or special-purpose domains  
✅ **Realistic** - Better test coverage with real-world scenarios  
✅ **Malicious domain testing** - Test threat intelligence tools against known bad domains  

## Migration

All test files should be updated to use `get_random_domain()` instead of hardcoded `"example.com"`.

**Before:**
```python
domain="example.com"
```

**After:**
```python
from hackerdogs_tools.osint.test_domains import get_random_domain

test_domain = get_random_domain()
domain=test_domain
```

## Example: Updated Test File

```python
from hackerdogs_tools.osint.test_domains import get_random_domain

class TestSubfinderStandalone:
    def test_subfinder_standalone(self):
        runtime = ToolRuntime(state={"user_id": "test_user"})
        test_domain = get_random_domain()  # Random real domain
        
        result = subfinder_enum(
            runtime=runtime,
            domain=test_domain, recursive=False, silent=True
        )
        # ... assertions
```

---

*Last Updated: 2024*

