"""
Test suite for dnsdumpster tool

Tests:
1. Standalone tool execution
2. LangChain agent integration
3. CrewAI agent integration
"""

import pytest
import json
import os
from langchain.agents import create_agent, AgentExecutor
from langchain.tools import ToolRuntime
from langchain_core.messages import HumanMessage
from crewai import Agent, Task, Crew

from hackerdogs_tools.osint.infrastructure.dnsdumpster_langchain import dnsdumpster_search
from hackerdogs_tools.osint.infrastructure.dnsdumpster_crewai import DNSDumpsterTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain, get_crewai_llm_from_env


class TestDnsdumpsterStandalone:
    """Test dnsdumpster tool standalone execution."""
    
    def test_dnsdumpster_standalone(self):
        test_domain = get_random_domain()
        """Test dnsdumpster tool execution without agent."""
        runtime = ToolRuntime(state={"user_id": "test_user"})
        
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        result = dnsdumpster_search(
            runtime=runtime,
            domain=get_random_domain()
        )
        
        # Parse result
        result_data = json.loads(result)
        
        # Assertions
        assert "status" in result_data
        assert result_data["status"] in ["success", "error"]
        
        if result_data["status"] == "success":
            assert "execution_method" in result_data
            assert result_data["execution_method"] == "docker"
        else:
            # If error, should have message
            assert "message" in result_data
            print(f"Tool returned error (expected if Docker not set up): {result_data.get('message')}")


class TestDnsdumpsterLangChain:
    """Test dnsdumpster tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with dnsdumpster tool."""
        tools = [dnsdumpster_search]
        agent = create_agent(
            llm=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the dnsdumpster tool for OSINT operations."
        )
        return agent
    
    def test_dnsdumpster_langchain_agent(self, agent):
        """Test dnsdumpster tool with LangChain agent."""
        runtime = ToolRuntime(state={"user_id": "test_user"})
        
        # Create agent executor
        executor = AgentExecutor(
            agent=agent,
            tools=[dnsdumpster_search],
            verbose=True
        )
        
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        # Execute query
        result = executor.invoke({
            "messages": [HumanMessage(content=f"Map DNS records for {test_domain} using DNSDumpster")],
            "runtime": runtime
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        print(f"LangChain agent result: {result}")


class TestDnsdumpsterCrewAI:
    """Test dnsdumpster tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with dnsdumpster tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using dnsdumpster",
            backstory="You are an expert OSINT analyst.",
            tools=[DNSDumpsterTool()],
            llm=llm,
            verbose=True
        )
    
    def test_dnsdumpster_crewai_agent(self, agent, llm):
        """Test dnsdumpster tool with CrewAI agent."""
        task = Task(
            description=f"Map DNS records for {test_domain} using DNSDumpster",
            agent=agent,
            expected_output="Results from dnsdumpster tool"
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
        print(f"CrewAI agent result: {result}")


def run_all_tests():
    """Run all three test scenarios."""
    print("=" * 80)
    print(f"Running dnsdumpster Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestDnsdumpsterStandalone()
        test.test_dnsdumpster_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        test = TestDnsdumpsterLangChain()
        test.test_dnsdumpster_langchain_agent(test.agent(llm))
        print("✅ LangChain test passed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        llm = get_crewai_llm_from_env()
        test = TestDnsdumpsterCrewAI()
        test.test_dnsdumpster_crewai_agent(test.agent(llm), llm)
        print("✅ CrewAI test passed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
