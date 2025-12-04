# Test Domains Utility

## Overview

The `test_domains.py` module provides random domain selection from the OpenDNS random domains list (`opendns-random-domains.txt`) for testing OSINT tools. This ensures tests use **real, valid domains** instead of reserved domains like `example.com`.

## Why Not example.com?

`example.com` is a **reserved domain** (RFC 2606) that:
- ❌ May not resolve properly in all contexts
- ❌ May be blocked by some security tools
- ❌ Doesn't provide realistic test scenarios
- ❌ May not have actual DNS records

## Usage

### Basic Usage

```python
from hackerdogs_tools.osint.test_domains import get_random_domain

# Get a single random domain
domain = get_random_domain()
print(domain)  # e.g., "webmagnat.ro"
```

### In Tests

```python
from hackerdogs_tools.osint.test_domains import get_random_domain

def test_subfinder_standalone(self):
    runtime = ToolRuntime(state={"user_id": "test_user"})
    
    # Use a random real domain instead of reserved example.com
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

# Get 5 unique random domains
domains = get_random_domains(count=5, unique=True)
print(domains)  # ['webmagnat.ro', 'nickelfreesolutions.com', ...]
```

## Available Functions

### `get_random_domain() -> str`
Get a single random domain from the list.

### `get_random_domains(count: int = 1, unique: bool = True) -> List[str]`
Get multiple random domains.
- `count`: Number of domains to return
- `unique`: If True, ensure all domains are unique

### `get_domains_count() -> int`
Get the total number of available domains (currently ~10,000).

### `reset_cache() -> None`
Reset the domains cache (useful if file is updated).

## Domain Source

The domains come from `opendns-random-domains.txt` which contains:
- **10,000 real domains** from OpenDNS
- One domain per line
- Real, resolvable domains suitable for testing

## Benefits

✅ **Real domains** - Actual, resolvable domains  
✅ **Variety** - 10,000 different domains  
✅ **Random** - Different domain each test run  
✅ **No conflicts** - Not reserved or special-purpose domains  
✅ **Realistic** - Better test coverage  

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

