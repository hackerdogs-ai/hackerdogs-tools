# CrewAI Inputs Parameter Usage

## Overview

CrewAI supports passing structured input data to crews using the `inputs` parameter in `crew.kickoff()`. This allows you to use placeholders in task descriptions that are automatically replaced with actual values.

## How It Works

### **1. Use Placeholders in Task Descriptions**

Instead of embedding values directly in the task description, use `{variable_name}` placeholders:

```python
task = Task(
    description="Find domains for {domain} using Amass Intel. Use domain parameter when calling the tool.",
    agent=agent,
    expected_output="List of domains discovered for {domain}"
)
```

### **2. Pass Inputs to `crew.kickoff()`**

Pass a dictionary with the values to replace the placeholders:

```python
crew = Crew(
    agents=[agent],
    tasks=[task],
    llm=llm,
    verbose=True
)

# Pass inputs - CrewAI automatically replaces {domain} with "owasp.org"
result = crew.kickoff(inputs={"domain": "owasp.org"})
```

### **3. CrewAI Interpolates Placeholders**

CrewAI automatically:
- Finds all `{variable_name}` placeholders in task descriptions
- Replaces them with values from the `inputs` dictionary
- Makes the interpolated description available to the agent

---

## Benefits

### ✅ **Reliable Parameter Passing**

**Before (unreliable):**
```python
# Domain embedded in natural language - LLM must extract it
task = Task(description="Find domains for owasp.org using Amass Intel")
# LLM might miss the domain or use wrong parameter name
```

**After (reliable):**
```python
# Domain passed as structured input - guaranteed to be available
task = Task(description="Find domains for {domain} using Amass Intel")
crew.kickoff(inputs={"domain": "owasp.org"})
# CrewAI replaces {domain} before agent sees it
```

### ✅ **No LLM Extraction Required**

- No need for LLM to parse natural language
- No risk of missing parameters
- No risk of wrong parameter names

### ✅ **Reusable Task Templates**

Tasks can be defined once and reused with different inputs:

```python
# Define task template once
task_template = Task(
    description="Find subdomains for {domain} using Amass Enum",
    agent=agent
)

# Reuse with different domains
for domain in ["owasp.org", "example.com", "test.com"]:
    crew.kickoff(inputs={"domain": domain})
```

---

## Example: Updated Amass Tests

### **Intel Tool Test**

```python
def test_amass_intel_crewai_agent(self, agent, llm):
    """Test AmassIntelTool with CrewAI agent."""
    # Use {domain} placeholder
    task = Task(
        description="Find domains for {domain} using Amass Intel. Use domain parameter when calling the tool.",
        agent=agent,
        expected_output="List of domains discovered for {domain}"
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        llm=llm,
        verbose=True
    )
    
    # Pass domain via inputs - CrewAI replaces {domain}
    result = crew.kickoff(inputs={"domain": "owasp.org"})
```

### **Enum Tool Test**

```python
def test_amass_enum_crewai_agent(self, agent, llm):
    """Test AmassEnumTool with CrewAI agent."""
    test_domain = get_random_domain()
    
    # Use {domain} placeholder
    task = Task(
        description="Find subdomains for {domain} using Amass Enum. Use the domain parameter when calling the tool.",
        agent=agent,
        expected_output="List of subdomains discovered for {domain}"
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        llm=llm,
        verbose=True
    )
    
    # Pass domain via inputs
    result = crew.kickoff(inputs={"domain": test_domain})
```

---

## Multiple Inputs

You can pass multiple inputs:

```python
task = Task(
    description="Find domains for {domain} filtered by ASN {asn} using Amass Intel",
    agent=agent
)

result = crew.kickoff(inputs={
    "domain": "cloudflare.com",
    "asn": "13374"
})
```

---

## Where Placeholders Work

Placeholders can be used in:
- ✅ Task `description`
- ✅ Task `expected_output`
- ✅ Agent `role` (if defined with placeholders)
- ✅ Agent `goal` (if defined with placeholders)
- ✅ Agent `backstory` (if defined with placeholders)

---

## Important Notes

1. **Placeholder Names Must Match Input Keys**
   - `{domain}` in description → `inputs={"domain": "value"}`
   - Case-sensitive!

2. **Missing Inputs**
   - If placeholder exists but input is missing, CrewAI will raise an error
   - Always provide all required inputs

3. **Type Safety**
   - Inputs can be strings, numbers, dicts, or lists
   - CrewAI converts them to strings for interpolation

---

## Comparison: Before vs After

### **Before (Natural Language Extraction)**

```python
# ❌ Unreliable - LLM must extract domain from text
task = Task(description="Find domains for cloudflare.com using Amass Intel")
crew.kickoff()
# Agent might call: amass_intel(asn="13374")  # Missing domain!
```

### **After (Structured Inputs)**

```python
# ✅ Reliable - Domain passed as structured input
task = Task(description="Find domains for {domain} using Amass Intel")
crew.kickoff(inputs={"domain": "cloudflare.com"})
# CrewAI replaces {domain} before agent sees it
# Agent sees: "Find domains for cloudflare.com using Amass Intel"
# Agent correctly calls: amass_intel(domain="cloudflare.com")
```

---

## References

- CrewAI Documentation: https://docs.crewai.com
- CrewAI Quickstart: https://docs.crewai.com/en/quickstart
- Source: `crewai/src/crewai/crew.py` - `kickoff()` method with `inputs` parameter

---

**Date:** 2025-12-05  
**Status:** Implemented in all Amass CrewAI tests

