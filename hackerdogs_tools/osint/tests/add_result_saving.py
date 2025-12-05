"""
Script to add result saving to all test files for LangChain and CrewAI tests.
"""
import re
from pathlib import Path

test_dir = Path(__file__).parent
test_files = [f for f in test_dir.glob("test_*.py") 
              if f.name not in ["test_utils.py", "test_runtime_helper.py", "test_all_tools.py"]]

def add_langchain_saving(content: str, tool_name: str) -> str:
    """Add result saving to LangChain test method."""
    # Pattern to find LangChain test method
    pattern = r'(def test_\w+_langchain_agent\([^)]+\):.*?)(print\("=" \* 80 \+ "\\n"\))'
    
    def replace_func(match):
        method_body = match.group(1)
        print_stmt = match.group(2)
        
        # Check if already has save_test_result
        if 'save_test_result' in method_body:
            return match.group(0)
        
        # Add saving code before the print statement
        saving_code = f'''        # Save LangChain agent result
        try:
            # Extract messages for better visibility
            messages_data = []
            if isinstance(result, dict) and "messages" in result:
                for msg in result["messages"]:
                    messages_data.append({{
                        "type": msg.__class__.__name__,
                        "content": str(msg.content)[:500] if hasattr(msg, 'content') else str(msg)[:500]
                    }})
            
            result_data = {{
                "status": "success",
                "agent_type": "langchain",
                "result": str(result)[:1000] if result else None,
                "messages": messages_data,
                "messages_count": len(result.get("messages", [])) if isinstance(result, dict) and "messages" in result else 0,
                "domain": test_domain
            }}
            result_file = save_test_result("{tool_name}", "langchain", result_data, test_domain)
            print(f"📁 LangChain result saved to: {{result_file}}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {{e}}")
        
        '''
        return method_body + saving_code + print_stmt
    
    return re.sub(pattern, replace_func, content, flags=re.DOTALL)

def add_crewai_saving(content: str, tool_name: str) -> str:
    """Add result saving to CrewAI test method."""
    # Pattern to find CrewAI test method
    pattern = r'(def test_\w+_crewai_agent\([^)]+\):.*?result = crew\.kickoff\(\)\s+.*?# Assertions.*?assert result is not None[^\n]*\n)(\s+# Print CrewAI)'
    
    def replace_func(match):
        method_body = match.group(1)
        print_stmt_start = match.group(2)
        
        # Check if already has save_test_result
        if 'save_test_result' in method_body:
            return match.group(0)
        
        # Add saving code before the print statement
        saving_code = f'''        # Save CrewAI agent result
        try:
            result_data = {{
                "status": "success",
                "agent_type": "crewai",
                "result": str(result)[:2000] if result else None,
                "domain": test_domain
            }}
            result_file = save_test_result("{tool_name}", "crewai", result_data, test_domain)
            print(f"📁 CrewAI result saved to: {{result_file}}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {{e}}")
        
        '''
        return method_body + saving_code + print_stmt_start
    
    return re.sub(pattern, replace_func, content, flags=re.DOTALL)

# Process each test file
for test_file in sorted(test_files):
    tool_name = test_file.stem.replace("test_", "")
    content = test_file.read_text()
    
    # Check if already has saves
    has_langchain_save = 'save_test_result' in content and 'langchain' in content
    has_crewai_save = 'save_test_result' in content and 'crewai' in content
    
    if not has_langchain_save or not has_crewai_save:
        print(f"Updating {test_file.name}...")
        content = add_langchain_saving(content, tool_name)
        content = add_crewai_saving(content, tool_name)
        test_file.write_text(content)
        print(f"  ✅ Updated {test_file.name}")

print("\n✅ All test files updated!")

