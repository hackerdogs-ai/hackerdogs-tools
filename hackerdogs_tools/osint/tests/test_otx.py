"""
Test suite for OTX tool

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

from hackerdogs_tools.osint.threat_intel.otx_langchain import otx_search
from hackerdogs_tools.osint.threat_intel.otx_crewai import OTXTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain, get_crewai_llm_from_env


class TestOTXStandalone:
    """Test OTX tool standalone execution."""
    
    def test_otx_standalone(self):
        test_domain = get_random_domain()
        """Test OTX tool execution without agent."""
        runtime = ToolRuntime(state={"user_id": "test_user"})
        
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        result = otx_search(
            runtime=runtime,
            indicator=test_domain,
            indicator_type="domain"
        )
        
        # Parse result
        result_data = json.loads(result)
        
        # Assertions
        assert "status" in result_data
        assert result_data["status"] in ["success", "error"]
        
        if result_data["status"] == "success":
            assert "indicator" in result_data
            assert "threat_verdict" in result_data
            assert result_data["indicator"] == test_domain
        else:
            # If error, should have message (expected if API key not set)
            assert "message" in result_data
            print(f"Tool returned error (expected if OTX_API_KEY not set): {result_data.get('message')}")


class TestOTXLangChain:
    """Test OTX tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with OTX tool."""
        tools = [otx_search]
        agent = create_agent(
            llm=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the OTX tool for threat intelligence operations.")
        return agent
    
    def test_otx_langchain_agent(self, agent):
        """Test OTX tool with LangChain agent."""
        runtime = ToolRuntime(state={"user_id": "test_user"})
        
        # Create agent executor
        executor = AgentExecutor(
            agent=agent,
            tools=[otx_search],
            verbose=True
        )
        
        # Use a random real domain instead of reserved example.com
        test_domain = get_random_domain()
        
        # Execute query
        result = executor.invoke({
            "messages": [HumanMessage(content=f"Check if {test_domain} is malicious using OTX")],
            "runtime": runtime
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        print(f"LangChain agent result: {result}")


class TestOTXCrewAI:
    """Test OTX tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with OTX tool."""
        return Agent(
            role="Threat Intelligence Analyst",
            goal="Perform threat intelligence operations using OTX",
            backstory="You are an expert threat intelligence analyst.",
            tools=[OTXTool()],
            llm=llm,
            verbose=True
        )
    
    def test_otx_crewai_agent(self, agent, llm):
        """Test OTX tool with CrewAI agent."""
        task = Task(
            description=f"Check if {test_domain} is malicious using OTX",
            agent=agent,
            expected_output="Results from OTX tool"
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
    print(f"Running OTX Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestOTXStandalone()
        test.test_otx_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        test = TestOTXLangChain()
        test.test_otx_langchain_agent(test.agent(llm))
        print("✅ LangChain test passed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        llm = get_crewai_llm_from_env()
        test = TestOTXCrewAI()
        test.test_otx_crewai_agent(test.agent(llm), llm)
        print("✅ CrewAI test passed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()

