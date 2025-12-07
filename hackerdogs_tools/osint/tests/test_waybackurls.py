"""
Test suite for waybackurls tool

Tests:
1. Standalone tool execution
2. LangChain agent integration
3. CrewAI agent integration
"""

import pytest
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from crewai import Agent, Task, Crew

from hackerdogs_tools.osint.content.waybackurls_langchain import waybackurls_search, WaybackurlsSecurityAgentState
from hackerdogs_tools.osint.content.waybackurls_crewai import WaybackurlsTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result, serialize_langchain_result, serialize_crewai_result


class TestWaybackurlsStandalone:
    """Test waybackurls tool standalone execution."""
    
    def test_waybackurls_standalone(self):
        """Test waybackurls tool execution without agent."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        # Tools are StructuredTool objects - use invoke() method
        result = waybackurls_search.invoke({
            "runtime": runtime,
            "domain": test_domain,
            "no_subs": False
        })
        
        # Parse result
        try:
            result_data = json.loads(result)
        except json.JSONDecodeError:
            result_data = {"raw_output": result}
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        # Save result
        try:
            result_file = save_test_result("waybackurls", "standalone", result_data, test_domain)
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        # Basic assertions
        assert result is not None, "Result should not be None"
        assert isinstance(result, str), "Result should be a string"
        
        # Check if result contains expected structure
        if isinstance(result_data, dict):
            assert "status" in result_data, "Result should contain 'status' field"


class TestWaybackurlsCrewAI:
    """Test waybackurls tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with waybackurls tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using waybackurls",
            backstory="You are an expert OSINT analyst.",
            tools=[WaybackurlsTool()],
            llm=llm,
            verbose=True
        )
    
    def test_waybackurls_crewai_agent(self, agent, llm):
        """Test waybackurls tool with CrewAI agent."""
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        task = Task(
            description=f"Find subdomains for {test_domain} using Waybackurls",
            agent=agent,
            expected_output="Results from waybackurls tool"
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            llm=llm,
            verbose=True
        )
        
        # Execute task
        result = crew.kickoff()
        
        # Assertions
        assert result is not None, "CrewAI returned None"
        # Save CrewAI agent result
        try:
            result_data = serialize_crewai_result(result) if result else None
            result_file = save_test_result("waybackurls", "crewai", result_data, test_domain)
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
        
                
        # Print CrewAI result for verification
        print("\n" + "=" * 80)
        print("CREWAI AGENT RESULT:")
        print("=" * 80)
        print(str(result)[:500])
        print("=" * 80 + "\n")


def run_all_tests():
    """Run all three test scenarios."""
    print("=" * 80)
    print(f"Running Waybackurls Tool Tests")
    print("=" * 80)
    
    # Initialize LLMs
    llm = get_llm_from_env()
    crewai_llm = get_crewai_llm_from_env()
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestWaybackurlsStandalone()
        test.test_waybackurls_standalone()
        print("✅ Standalone test completed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        tools = [waybackurls_search]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=(
                "You are an OSINT analyst. Your ONLY job is to execute tools and return their output EXACTLY as provided, "
                "without summarization, interpretation, or modification. When a tool returns JSON, you MUST copy the "
                "complete JSON string verbatim into your Final Answer. Do NOT summarize, do NOT extract points, "
                "do NOT reformat - return raw output only."
            ),
            state_schema=WaybackurlsSecurityAgentState
        )
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Find historical URLs for {test_domain} using Waybackurls. IMPORTANT: Return the complete JSON output from the tool verbatim. Do NOT summarize or interpret the results.")],
            "user_id": "test_user"
        })
        
        # Extract tool output from messages and save
        try:
            # Find the tool message with the actual JSON output
            tool_output = None
            if "messages" in result:
                for msg in result["messages"]:
                    if hasattr(msg, 'type') and msg.type == "tool" and hasattr(msg, 'content'):
                        try:
                            # Try to parse the content as JSON
                            import json
                            tool_output = json.loads(msg.content)
                            break
                        except:
                            pass
            
            # If we found tool output, use it; otherwise serialize the full result
            if tool_output:
                result_data = tool_output
            else:
                result_data = serialize_langchain_result(result)
            
            result_file = save_test_result("waybackurls", "langchain", result_data, test_domain)
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
            import traceback
            traceback.print_exc()
        
        print("✅ LangChain test completed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        agent = Agent(
            role="OSINT Analyst",
            goal="Execute OSINT tools and return raw output verbatim without any modification",
            backstory=(
                "You are a data collection specialist. Your ONLY job is to execute tools and return "
                "their output EXACTLY as provided, without summarization, interpretation, or modification. "
                "When a tool returns JSON, you MUST copy the complete JSON string verbatim into your Final Answer. "
                "Do NOT summarize, do NOT extract points, do NOT reformat - return raw output only."
            ),
            tools=[WaybackurlsTool()],
            llm=crewai_llm,
            verbose=True
        )
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        task = Task(
            description=f"Find historical URLs for {test_domain} using Waybackurls. IMPORTANT: When the tool returns JSON output, you MUST return the complete JSON string verbatim in your Final Answer. Do NOT summarize, do NOT extract key points, do NOT reformat. Return the exact JSON output from the tool.",
            agent=agent,
            expected_output="Complete raw JSON output from waybackurls tool, returned verbatim without any modification. Must include status, domain, urls array, count, and all other fields exactly as returned by the tool."
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Serialize and save result
        try:
            serialized = serialize_crewai_result(result)
            result_file = save_test_result("waybackurls", "crewai", serialized, test_domain)
            print(f"📁 JSON result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save result: {e}")
        
        print("✅ CrewAI test completed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("All tests completed")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
