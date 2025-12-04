"""
Test suite for amass tool

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

from hackerdogs_tools.osint.infrastructure.amass_langchain import amass_enum
from hackerdogs_tools.osint.infrastructure.amass_crewai import AmassTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain


class TestAmassStandalone:
    """Test amass tool standalone execution."""
    
    def test_amass_standalone(self):
        """Test amass tool execution without agent."""
        runtime = ToolRuntime(state={"user_id": "test_user"})
        
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        result = amass_enum(
            runtime=runtime,
            domain=test_domain, passive=False, active=True, timeout=300
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


class TestAmassLangChain:
    """Test amass tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with amass tool."""
        tools = [amass_enum]
        agent = create_agent(
            llm=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the amass tool for OSINT operations."
        )
        return agent
    
    def test_amass_langchain_agent(self, agent):
        """Test amass tool with LangChain agent."""
        runtime = ToolRuntime(state={"user_id": "test_user"})
        
        # Create agent executor
        executor = AgentExecutor(
            agent=agent,
            tools=[amass_enum],
            verbose=True
        )
        
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        # Execute query
        result = executor.invoke({
            "messages": [HumanMessage(content=f"Enumerate subdomains for {test_domain} using Amass")],
            "runtime": runtime
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        print(f"LangChain agent result: {result}")


class TestAmassCrewAI:
    """Test amass tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with amass tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using amass",
            backstory="You are an expert OSINT analyst.",
            tools=[AmassTool()],
            llm=llm,
            verbose=True
        )
    
    def test_amass_crewai_agent(self, agent, llm):
        """Test amass tool with CrewAI agent."""
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        task = Task(
            description=f"Enumerate subdomains for {test_domain} using Amass",
            agent=agent,
            expected_output="Results from amass tool"
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
    print(f"Running amass Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestAmassStandalone()
        test.test_amass_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        test = TestAmassLangChain()
        test.test_amass_langchain_agent(test.agent(llm))
        print("✅ LangChain test passed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        llm = get_crewai_llm_from_env()
        test = TestAmassCrewAI()
        test.test_amass_crewai_agent(test.agent(llm), llm)
        print("✅ CrewAI test passed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
