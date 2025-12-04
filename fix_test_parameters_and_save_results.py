#!/usr/bin/env python3
"""
Fix test parameters to match actual tool signatures and add result saving for LangChain/CrewAI tests.
"""

import re
from pathlib import Path

# Tool parameter mappings - what each tool actually expects
TOOL_PARAMS = {
    "nuclei": {
        "required": "target",  # Not "domain"
        "optional": ["templates", "severity", "tags"]
    },
    "abuseipdb": {
        "required": "ip",  # Not "domain"
        "optional": ["max_age_in_days", "verbose"]
    },
    "misp": {
        "required": "query",  # Not "domain"
        "optional": ["query_type", "limit"]
    },
    "subfinder": {
        "required": "domain",
        "optional": ["recursive", "silent"]
    },
    "amass": {
        "required": "domain",
        "optional": ["passive", "active", "timeout"]
    },
    # Add more as needed
}

test_dir = Path("hackerdogs_tools/osint/tests")
test_files = sorted([f for f in test_dir.glob("test_*.py") 
                    if f.name not in ["__init__.py", "test_utils.py", "test_runtime_helper.py", 
                                     "test_all_tools.py", "save_json_results.py"]])

print(f"Fixing test parameters and adding result saving in {len(test_files)} test files...\n")

for test_file in test_files:
    tool_name = test_file.stem.replace("test_", "")
    content = test_file.read_text()
    original = content
    
    if tool_name in TOOL_PARAMS:
        params = TOOL_PARAMS[tool_name]
        required_param = params["required"]
        
        # Fix standalone test - replace "domain" with correct parameter if needed
        if required_param != "domain":
            # Find the invoke call in standalone test
            pattern = rf'(\w+)\.invoke\(\s*\{{[^}}]*)"domain":\s*(\w+)'
            replacement = rf'\1.invoke({{\n            "runtime": runtime,\n            "{required_param}": \2'
            content = re.sub(pattern, replacement, content, count=1)
            
            # Also fix if it's using test_domain variable
            pattern2 = rf'(\w+)\.invoke\(\s*\{{[^}}]*)"domain":\s*test_domain'
            replacement2 = rf'\1.invoke({{\n            "runtime": runtime,\n            "{required_param}": test_domain'
            content = re.sub(pattern2, replacement2, content, count=1)
    
    # Add result saving for LangChain test
    langchain_result_pattern = r'(assert\s+result\s+is\s+not\s+None[^\n]*\n\s+assert[^\n]*\n\s+print\(f"✅ LangChain test passed)'
    if re.search(langchain_result_pattern, content):
        # Extract result data if possible
        langchain_save = f'''        assert result is not None
        assert "messages" in result or "output" in result
        
        # Save LangChain agent result
        try:
            result_data = {{
                "status": "success",
                "agent_type": "langchain",
                "result": str(result)[:1000] if result else None,
                "messages_count": len(result.get("messages", [])) if isinstance(result, dict) and "messages" in result else 0
            }}
            result_file = save_test_result("{tool_name}", "langchain", result_data, test_domain if 'test_domain' in locals() else None)
            print(f"📁 LangChain result saved to: {{result_file}}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {{e}}")
        
        print(f"✅ LangChain test passed - Result: {{str(result)[:200]}}")'''
        content = re.sub(langchain_result_pattern, langchain_save, content, count=1)
    
    # Add result saving for CrewAI test
    crewai_result_pattern = r'(assert\s+result\s+is\s+not\s+None[^\n]*\n\s+print\(f"✅ CrewAI test passed)'
    if re.search(crewai_result_pattern, content):
        crewai_save = f'''        assert result is not None
        
        # Save CrewAI agent result
        try:
            result_data = {{
                "status": "success",
                "agent_type": "crewai",
                "result": str(result)[:1000] if result else None
            }}
            result_file = save_test_result("{tool_name}", "crewai", result_data, test_domain if 'test_domain' in locals() else None)
            print(f"📁 CrewAI result saved to: {{result_file}}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {{e}}")
        
        print(f"✅ CrewAI test passed - Result: {{str(result)[:200]}}")'''
        content = re.sub(crewai_result_pattern, crewai_save, content, count=1)
    
    if content != original:
        test_file.write_text(content)
        print(f"✅ Fixed {test_file.name}")
    else:
        print(f"⚠️  {test_file.name}: No changes needed")

print(f"\n✅ Fixed all {len(test_files)} test files")

