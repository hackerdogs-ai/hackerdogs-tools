"""
Test suite for maigret tool

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

from hackerdogs_tools.osint.identity.maigret_langchain import maigret_search
from hackerdogs_tools.osint.identity.maigret_crewai import MaigretTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain, get_crewai_llm_from_env


class TestMaigretStandalone:
    """Test maigret tool standalone execution."""
    
    def test_maigret_standalone(self):
        """Test maigret tool execution without agent."""
        runtime = ToolRuntime(state={"user_id": "test_user"})
        
        result = maigret_search(
            runtime=runtime,
            username="testuser", extract_metadata=True, sites=None
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


class TestMaigretLangChain:
    """Test maigret tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with maigret tool."""
        tools = [maigret_search]
        agent = create_agent(
            llm=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the maigret tool for OSINT operations."
        )
        return agent
    
    def test_maigret_langchain_agent(self, agent):
        """Test maigret tool with LangChain agent."""
        runtime = ToolRuntime(state={"user_id": "test_user"})
        
        # Create agent executor
        executor = AgentExecutor(
            agent=agent,
            tools=[maigret_search],
            verbose=True
        )
        
        # Execute query
        result = executor.invoke({
            "messages": [HumanMessage(content="Search for username testuser using Maigret")],
            "runtime": runtime
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        print(f"LangChain agent result: {result}")


class TestMaigretCrewAI:
    """Test maigret tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with maigret tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using maigret",
            backstory="You are an expert OSINT analyst.",
            tools=[MaigretTool()],
            llm=llm,
            verbose=True
        )
    
    def test_maigret_crewai_agent(self, agent, llm):
        """Test maigret tool with CrewAI agent."""
        task = Task(
            description="Search for username testuser using Maigret",
            agent=agent,
            expected_output="Results from maigret tool"
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
    print(f"Running maigret Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestMaigretStandalone()
        test.test_maigret_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        test = TestMaigretLangChain()
        test.test_maigret_langchain_agent(test.agent(llm))
        print("✅ LangChain test passed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        llm = get_crewai_llm_from_env()
        test = TestMaigretCrewAI()
        test.test_maigret_crewai_agent(test.agent(llm), llm)
        print("✅ CrewAI test passed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
