"""
Test suite for misp tool

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

# Add project root to path for direct execution
project_root = Path(__file__).parent.parent.parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from crewai import Agent, Task, Crew

from hackerdogs_tools.osint.threat_intel.misp_langchain import misp_search
from hackerdogs_tools.osint.threat_intel.misp_crewai import MISPTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result


class TestMispStandalone:
    """Test misp tool standalone execution."""
    
    def test_misp_standalone(self):
        """Test misp tool execution without agent."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        # Tools are StructuredTool objects - use invoke() method
        # MISP requires "query" parameter, not "domain"
        result = misp_search.invoke({
            "runtime": runtime,
            "query": test_domain,
            "query_type": "attribute",
            "limit": 100
        })
        
        # Parse result
        result_data = json.loads(result)
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
                # Save LangChain agent result - complete result as-is, no truncation, no decoration
        try:
            result_data = {
                "status": "success",
                "agent_type": "langchain",
                "result": result,  # Complete result dict as-is, no truncation, no decoration
                "domain": test_domain
            }
            result_file = save_test_result("misp", "langchain", result_data, test_domain)
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
        
                
        # Print agent result for verification
        print("\n" + "=" * 80)
        print("LANGCHAIN AGENT RESULT:")
        print("=" * 80)
        if "messages" in result:
            for msg in result["messages"]:
                print(f"  {msg.__class__.__name__}: {str(msg.content)[:200]}")
        print("=" * 80 + "\n")


class TestMispCrewAI:
    """Test misp tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with misp tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using misp",
            backstory="You are an expert OSINT analyst.",
            tools=[MISPTool()],
            llm=llm,
            verbose=True
        )
    
    def test_misp_crewai_agent(self, agent, llm):
        """Test misp tool with CrewAI agent."""
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        task = Task(
            description=f"Find subdomains for {test_domain} using Misp",
            agent=agent,
            expected_output="Results from misp tool"
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            llm=llm,
            verbose=True
        )
        
        # Execute task
        result = crew.kickoff()
        
        # Assertions        assert result is not None, "CrewAI returned None"
        # Save CrewAI agent result
        try:
            result_data = {
                "status": "success",
                "agent_type": "crewai",
                "result": serialize_crewai_result(result) if result else None  # Complete result as-is, no truncation,
                "domain": test_domain
            }
            result_file = save_test_result("misp", "crewai", result_data, test_domain)
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
    print(f"Running misp Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestMispStandalone()
        test.test_misp_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        # Create agent directly (not using pytest fixtures)
        tools = [misp_search]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the misp tool for OSINT operations."
        )
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Find subdomains for {test_domain} using Misp")]
        })
        
        # Assertions        assert result is not None
        assert "messages" in result or "output" in result
        
        # Save LangChain agent result
        try:
            result_data = {
                "status": "success",
                "agent_type": "langchain",
                "result": serialize_crewai_result(result) if result else None  # Complete result as-is, no truncation,
                "messages_count": len(result.get("messages", [])) if isinstance(result, dict) and "messages" in result else 0,
                "domain": test_domain
            }
            result_file = save_test_result("misp", "langchain", result_data, test_domain)
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
        
        print(f"✅ LangChain test passed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        llm = get_crewai_llm_from_env()
        # Create agent directly (not using pytest fixtures)
        agent = Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using misp",
            backstory="You are an expert OSINT analyst.",
            tools=[MISPTool()],
            llm=llm,
            verbose=True
        )
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        task = Task(
            description=f"Find subdomains for {test_domain} using Misp",
            agent=agent,
            expected_output="Results from misp tool"
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            llm=llm,
            verbose=True
        )
        
        # Execute task
        result = crew.kickoff()
        
        # Assertions        assert result is not None
        
        # Save CrewAI agent result
        try:
            result_data = {
                "status": "success",
                "agent_type": "crewai",
                "result": serialize_crewai_result(result) if result else None  # Complete result as-is, no truncation,
                "domain": test_domain
            }
            result_file = save_test_result("misp", "crewai", result_data, test_domain)
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
        
        print(f"✅ CrewAI test passed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
