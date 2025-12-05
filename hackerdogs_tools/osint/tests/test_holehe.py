"""
Test suite for holehe tool

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

from hackerdogs_tools.osint.identity.holehe_langchain import holehe_search
from hackerdogs_tools.osint.identity.holehe_crewai import HoleheTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain
from hackerdogs_tools.osint.test_identity_data import get_random_email
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result


class TestHoleheStandalone:
    """Test holehe tool standalone execution."""
    
    def test_holehe_standalone(self):
        """Test holehe tool execution without agent."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Use a random realistic email (holehe checks email registration on sites)
        test_email = get_random_email()
        
        # Tools are StructuredTool objects - use invoke() method
        # Holehe requires "email" parameter, not "domain"
        result = holehe_search.invoke({
            "runtime": runtime,
            "email": test_email,
            "only_used": True
        })
        
        # Parse result
        result_data = json.loads(result)
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        # Save JSON result to file - VERBATIM without wrappers
        result_file = save_test_result("holehe", "standalone", result_data, test_email.replace("@", "_at_"))
        print(f"📁 JSON result saved to: {result_file}")
        
        # Assertions
        assert "status" in result_data, f"Missing 'status' in result: {result_data}"
        assert result_data["status"] in ["success", "error"], f"Invalid status: {result_data.get('status')}"
        
        if result_data["status"] == "success":
            assert "email" in result_data, f"Missing 'email' in result: {result_data}"
            print(f"✅ Tool executed successfully")
            print(f"   Email: {result_data.get('email')}")
            print(f"   Execution method: {result_data.get('execution_method', 'docker')}")
        else:
            # If error, should have message
            assert "message" in result_data, f"Error status but no message: {result_data}"
            print(f"⚠️  Tool returned error: {result_data.get('message')}")


class TestHoleheLangChain:
    """Test holehe tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with holehe tool."""
        tools = [holehe_search]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the holehe tool for email registration checking."
        )
        return agent
    
    def test_holehe_langchain_agent(self, agent):
        """Test holehe tool with LangChain agent."""
        # Use a random realistic email (holehe checks email registration on sites)
        test_email = get_random_email()
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Check if email {test_email} is registered on sites using Holehe")]
        })
        
        # Assertions
        assert result is not None, "Agent returned None"
        assert "messages" in result or "output" in result, f"Invalid agent result structure: {result}"
        
        # Save LangChain agent result - complete result as-is, no truncation, no decoration
        try:
            result_data = {
                "status": "success",
                "agent_type": "langchain",
                "result": result,  # Complete result dict as-is, no truncation, no decoration
                "domain": test_email.replace("@", "_at_")
            }
            result_file = save_test_result("holehe", "langchain", result_data, test_email.replace("@", "_at_"))
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
            import traceback
            traceback.print_exc()
        
                
        # Print agent result for verification
        print("\n" + "=" * 80)
        print("LANGCHAIN AGENT RESULT:")
        print("=" * 80)
        if "messages" in result:
            for msg in result["messages"]:
                print(f"  {msg.__class__.__name__}: {str(msg.content)[:200]}")
        print("=" * 80 + "\n")


class TestHoleheCrewAI:
    """Test holehe tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with holehe tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using holehe",
            backstory="You are an expert OSINT analyst.",
            tools=[HoleheTool()],
            llm=llm,
            verbose=True
        )
    
    def test_holehe_crewai_agent(self, agent, llm):
        """Test holehe tool with CrewAI agent."""
        # Use a random realistic email (holehe checks email registration on sites)
        test_email = get_random_email()
        
        task = Task(
            description=f"Check if email {test_email} is registered on sites using Holehe",
            agent=agent,
            expected_output="Email registration check results from holehe tool"
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
        
        # Save CrewAI agent result - complete result as-is
        try:
            from .save_json_results import serialize_crewai_result
            result_data = {
                "status": "success",
                "agent_type": "crewai",
                "result": serialize_crewai_result(result) if result else None,
                "domain": test_email.replace("@", "_at_")
            }
            result_file = save_test_result("holehe", "crewai", result_data, test_email.replace("@", "_at_"))
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
        
                
        # Print CrewAI result for verification
        print("\n" + "=" * 80)
        print("CREWAI AGENT RESULT:")
        print("=" * 80)
        print(str(result)[:500])
        print("=" * 80 + "\n")


def run_all_tests():
    """Run all three test scenarios."""
    print("=" * 80)
    print(f"Running holehe Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestHoleheStandalone()
        test.test_holehe_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        # Create agent directly (not using pytest fixtures)
        tools = [holehe_search]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the holehe tool for email registration checking."
        )
        # Use a random realistic email (holehe checks email registration on sites)
        test_email = get_random_email()
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Check if email {test_email} is registered on sites using Holehe")]
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        
        # Save LangChain agent result - complete result as-is, no truncation, no decoration
        try:
            result_data = {
                "status": "success",
                "agent_type": "langchain",
                "result": result,  # Complete result dict as-is, no truncation, no decoration
                "domain": test_email.replace("@", "_at_")
            }
            result_file = save_test_result("holehe", "langchain", result_data, test_email.replace("@", "_at_"))
            print(f"📁 LangChain result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save LangChain result: {e}")
            import traceback
            traceback.print_exc()
        
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
            goal="Perform OSINT operations using holehe",
            backstory="You are an expert OSINT analyst.",
            tools=[HoleheTool()],
            llm=llm,
            verbose=True
        )
        # Use a random realistic email (holehe checks email registration on sites)
        test_email = get_random_email()
        
        task = Task(
            description=f"Check if email {test_email} is registered on sites using Holehe",
            agent=agent,
            expected_output="Email registration check results from holehe tool"
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
        assert result is not None
        
        # Save CrewAI agent result - complete result as-is
        try:
            from .save_json_results import serialize_crewai_result
            result_data = {
                "status": "success",
                "agent_type": "crewai",
                "result": serialize_crewai_result(result) if result else None,
                "domain": test_email.replace("@", "_at_")
            }
            result_file = save_test_result("holehe", "crewai", result_data, test_email.replace("@", "_at_"))
            print(f"📁 CrewAI result saved to: {result_file}")
        except Exception as e:
            print(f"⚠️  Could not save CrewAI result: {e}")
            import traceback
            traceback.print_exc()
        
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
