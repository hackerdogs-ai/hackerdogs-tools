# How Root Domain is Passed to Agents

## Current Implementation

### **LangChain Agents**

The domain is **embedded in natural language** within the user message:

```python
result = agent.invoke({
    "messages": [HumanMessage(content="Find domains for cloudflare.com filtered by ASN 13374 using Amass Intel")]
})
```

**Process:**
1. Agent receives natural language prompt: `"Find domains for cloudflare.com filtered by ASN 13374 using Amass Intel"`
2. LLM must **extract** the domain (`cloudflare.com`) from the text
3. LLM must **map** it to the tool's `domain` parameter
4. LLM calls tool: `amass_intel(domain="cloudflare.com", asn="13374")`

**Problem:** The LLM sometimes fails to extract the domain correctly, resulting in calls like:
- ❌ `amass_intel(asn="13374")` - Missing domain!
- ❌ `amass_intel(org="cloudflare.com")` - Wrong parameter name!

---

### **CrewAI Agents**

Similar approach - domain is in the **task description**:

```python
task = Task(
    description="Find domains for owasp.org using Amass Intel",
    agent=agent,
    expected_output="List of domains discovered for owasp.org"
)
```

**Process:**
1. Agent receives task description: `"Find domains for owasp.org using Amass Intel"`
2. LLM must **extract** the domain (`owasp.org`) from the description
3. LLM must **map** it to the tool's `domain` parameter
4. LLM calls tool: `amass_intel(domain="owasp.org")`

**Problem:** Same issue - LLM may not extract domain correctly.

---

## Why This Fails

### **Root Cause:**
The LLM is doing **natural language understanding** to extract parameters, which is:
- ❌ Error-prone (may miss the domain)
- ❌ Inconsistent (may use wrong parameter name)
- ❌ Context-dependent (depends on prompt wording)

### **Evidence from Test Failures:**
```
2025-12-05T05:51:55-0800 - ERROR - Configuration error: No root domain names were provided
Log shows: org=None, asn=13374  # Domain was NOT extracted from prompt!
```

The agent received: `"Find domains for cloudflare.com filtered by ASN 13374"`
But called: `amass_intel(asn="13374")` - **Domain missing!**

---

## Solutions

### **Option 1: More Explicit Prompts (Current Fix)**

Make prompts more explicit about parameter format:

```python
# Before (ambiguous):
"Find domains for cloudflare.com filtered by ASN 13374 using Amass Intel"

# After (explicit):
"Use amass_intel tool with domain='cloudflare.com' and asn='13374' to find domains"
```

**Pros:**
- ✅ Easy to implement
- ✅ No code changes needed

**Cons:**
- ⚠️ Still relies on LLM parsing
- ⚠️ May not work 100% of the time

---

### **Option 2: Structured Input (Better)**

Pass domain as structured data if possible:

```python
# LangChain (if supported):
result = agent.invoke({
    "messages": [HumanMessage(content="Find domains using Amass Intel")],
    "domain": "cloudflare.com",  # Structured parameter
    "asn": "13374"
})

# CrewAI:
task = Task(
    description="Find domains using Amass Intel",
    agent=agent,
    context={"domain": "owasp.org"}  # Structured context
)
```

**Pros:**
- ✅ More reliable
- ✅ No parsing needed

**Cons:**
- ⚠️ May not be supported by all agent frameworks
- ⚠️ Requires framework changes

---

### **Option 3: Tool Description Enhancement (Applied)**

Make tool description extremely explicit:

```python
description = (
    "⚠️ REQUIRES domain parameter. ASN/CIDR/addr are optional filters.\n"
    "Example: domain='example.com', asn='13374' to filter results by ASN."
)
```

**Pros:**
- ✅ Guides LLM to use correct format
- ✅ No test changes needed

**Cons:**
- ⚠️ Still relies on LLM following instructions

---

### **Option 4: Pre-processing Layer (Best)**

Add a pre-processing step that extracts domain from prompt:

```python
def extract_domain_from_prompt(prompt: str) -> Optional[str]:
    """Extract domain from natural language prompt."""
    # Use regex or NLP to find domain patterns
    domain_pattern = r'\b([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
    matches = re.findall(domain_pattern, prompt)
    return matches[0] if matches else None

# In test:
prompt = "Find domains for cloudflare.com using Amass Intel"
domain = extract_domain_from_prompt(prompt)
# Then explicitly pass domain to tool or include in structured format
```

**Pros:**
- ✅ Most reliable
- ✅ Works regardless of LLM behavior

**Cons:**
- ⚠️ Requires code changes
- ⚠️ More complex implementation

---

## Current Status

**What We're Doing:**
1. ✅ Enhanced tool descriptions (Option 3)
2. ✅ Improved error messages
3. ✅ Made prompts more explicit (Option 1)

**What's Still Happening:**
- ⚠️ LLM sometimes still misses domain extraction
- ⚠️ Relies on LLM understanding natural language

---

## Recommendation

For **production use**, consider **Option 4** (pre-processing layer) to extract domain before passing to agent, or use **structured input** if the framework supports it.

For **testing**, the current approach (explicit prompts + enhanced descriptions) should work better, but may still have occasional failures.

---

**Date:** 2025-12-05  
**Status:** Current implementation relies on LLM natural language extraction, which is error-prone.

