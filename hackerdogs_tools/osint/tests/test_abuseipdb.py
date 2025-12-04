"""
Test suite for abuseipdb tool

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

from hackerdogs_tools.osint.threat_intel.abuseipdb_langchain import abuseipdb_search
from hackerdogs_tools.osint.threat_intel.abuseipdb_crewai import AbuseIPDBTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import save_test_result


class TestAbuseipdbStandalone:
    """Test abuseipdb tool standalone execution."""
    
    def test_abuseipdb_standalone(self):
        """Test abuseipdb tool execution without agent."""
        # Use mock runtime since ToolRuntime is auto-injected in LangChain 1.x
        runtime = create_mock_runtime(state={"user_id": "test_user"})
        
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        # Tools are StructuredTool objects - use invoke() method
        # AbuseIPDB requires "ip" parameter, not "domain"
        # Use a test IP address (8.8.8.8 - Google DNS)
        test_ip = "8.8.8.8"
        result = abuseipdb_search.invoke({
            "runtime": runtime,
            "ip": test_ip,
            "max_age_in_days": 90,
            "verbose": False
        })
        
        # Parse result
        result_data = json.loads(result)
        
        # Print JSON output for verification
        print("\n" + "=" * 80)
        print("TOOL JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result_data, indent=2))
        print("=" * 80 + "\n")
        
        # Save JSON result to file
        result_file = save_test_result("abuseipdb", "standalone", result_data, test_domain)
        print(f"📁 JSON result saved to: {result_file}")
        
        # Assertions
        assert "status" in result_data, f"Missing 'status' in result: {result_data}"
        assert result_data["status"] in ["success", "error"], f"Invalid status: {result_data.get('status')}"
        
        if result_data["status"] == "success":
            assert "execution_method" in result_data, f"Missing 'execution_method' in result: {result_data}"
            # Tool can return "docker" or "official_docker_image" depending on execution method
            assert result_data["execution_method"] in ["docker", "official_docker_image"], \
                f"Invalid execution_method: {result_data.get('execution_method')}"
            assert "domain" in result_data, f"Missing 'domain' in result: {result_data}"
            assert "subdomains" in result_data, f"Missing 'subdomains' in result: {result_data}"
            assert isinstance(result_data["subdomains"], list), f"subdomains must be a list: {type(result_data.get('subdomains'))}"
            print(f"✅ Tool executed successfully")
            print(f"   Domain: {result_data.get('domain')}")
            print(f"   Subdomains found: {result_data.get('count', 0)}")
            print(f"   Execution method: {result_data.get('execution_method')}")
        else:
            # If error, should have message
            assert "message" in result_data, f"Error status but no message: {result_data}"
            print(f"⚠️  Tool returned error: {result_data.get('message')}")


class TestAbuseipdbLangChain:
    """Test abuseipdb tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with abuseipdb tool."""
        tools = [abuseipdb_search]
        agent = create_agent(
            llm=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the abuseipdb tool for OSINT operations."
        )
        return agent
    
    def test_abuseipdb_langchain_agent(self, agent):
        """Test abuseipdb tool with LangChain agent."""
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Find subdomains for {test_domain} using Abuseipdb")]
        })
        
        # Assertions        assert result is not None, "Agent returned None"
        assert "messages" in result or "output" in result, f"Invalid agent result structure: {result}"
        
        # Print agent result for verification
        print("\n" + "=" * 80)
        print("LANGCHAIN AGENT RESULT:")
        print("=" * 80)
        if "messages" in result:
            for msg in result["messages"]:
                print(f"  {msg.__class__.__name__}: {str(msg.content)[:200]}")
        print("=" * 80 + "\n")


class TestAbuseipdbCrewAI:
    """Test abuseipdb tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with abuseipdb tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using abuseipdb",
            backstory="You are an expert OSINT analyst.",
            tools=[AbuseIPDBTool()],
            llm=llm,
            verbose=True
        )
    
    def test_abuseipdb_crewai_agent(self, agent, llm):
        """Test abuseipdb tool with CrewAI agent."""
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        task = Task(
            description=f"Find subdomains for {test_domain} using Abuseipdb",
            agent=agent,
            expected_output="Results from abuseipdb tool"
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
        
        # Print CrewAI result for verification
        print("\n" + "=" * 80)
        print("CREWAI AGENT RESULT:")
        print("=" * 80)
        print(str(result)[:500])
        print("=" * 80 + "\n")


def run_all_tests():
    """Run all three test scenarios."""
    print("=" * 80)
    print(f"Running abuseipdb Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestAbuseipdbStandalone()
        test.test_abuseipdb_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        # Create agent directly (not using pytest fixtures)
        tools = [abuseipdb_search]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the abuseipdb tool for OSINT operations."
        )
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Find subdomains for {test_domain} using Abuseipdb")]
        })
        
        # Assertions        assert result is not None
        assert "messages" in result or "output" in result
        
        # Save LangChain agent result
        try:
            result_data = {
                "status": "success",
                "agent_type": "langchain",
                "result": str(result)[:1000] if result else None,
                "messages_count": len(result.get("messages", [])) if isinstance(result, dict) and "messages" in result else 0,
                "domain": test_domain
            }
            result_file = save_test_result("abuseipdb", "langchain", result_data, test_domain)
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
            goal="Perform OSINT operations using abuseipdb",
            backstory="You are an expert OSINT analyst.",
            tools=[AbuseIPDBTool()],
            llm=llm,
            verbose=True
        )
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        task = Task(
            description=f"Find subdomains for {test_domain} using Abuseipdb",
            agent=agent,
            expected_output="Results from abuseipdb tool"
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
                "result": str(result)[:1000] if result else None,
                "domain": test_domain
            }
            result_file = save_test_result("abuseipdb", "crewai", result_data, test_domain)
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
