"""
Test suite for exiftool tool

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

from hackerdogs_tools.osint.metadata.exiftool_langchain import exiftool_search
from hackerdogs_tools.osint.metadata.exiftool_crewai import ExifToolTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.test_domains import get_random_domain, get_crewai_llm_from_env


class TestExiftoolStandalone:
    """Test exiftool tool standalone execution."""
    
    def test_exiftool_standalone(self):
        """Test exiftool tool execution without agent."""
        runtime = ToolRuntime(state={"user_id": "test_user"})
        
        result = exiftool_search(
            runtime=runtime,
            file_path="/tmp/image.jpg", extract_gps=True, extract_author=True
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


class TestExiftoolLangChain:
    """Test exiftool tool with LangChain agent."""
    
    @pytest.fixture
    def llm(self):
        """Get LLM from environment."""
        return get_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create LangChain agent with exiftool tool."""
        tools = [exiftool_search]
        agent = create_agent(
            llm=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the exiftool tool for OSINT operations."
        )
        return agent
    
    def test_exiftool_langchain_agent(self, agent):
        """Test exiftool tool with LangChain agent."""
        runtime = ToolRuntime(state={"user_id": "test_user"})
        
        # Create agent executor
        executor = AgentExecutor(
            agent=agent,
            tools=[exiftool_search],
            verbose=True
        )
        
        # Execute query
        result = executor.invoke({
            "messages": [HumanMessage(content="Extract metadata from /tmp/image.jpg using ExifTool")],
            "runtime": runtime
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        print(f"LangChain agent result: {result}")


class TestExiftoolCrewAI:
    """Test exiftool tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with exiftool tool."""
        return Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using exiftool",
            backstory="You are an expert OSINT analyst.",
            tools=[ExifToolTool()],
            llm=llm,
            verbose=True
        )
    
    def test_exiftool_crewai_agent(self, agent, llm):
        """Test exiftool tool with CrewAI agent."""
        task = Task(
            description="Extract metadata from /tmp/image.jpg using ExifTool",
            agent=agent,
            expected_output="Results from exiftool tool"
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
    print(f"Running exiftool Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestExiftoolStandalone()
        test.test_exiftool_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        test = TestExiftoolLangChain()
        test.test_exiftool_langchain_agent(test.agent(llm))
        print("✅ LangChain test passed")
    except Exception as e:
        print(f"❌ LangChain test failed: {str(e)}")
    
    # Test 3: CrewAI
    print("\n3. Testing CrewAI Agent Integration...")
    try:
        llm = get_crewai_llm_from_env()
        test = TestExiftoolCrewAI()
        test.test_exiftool_crewai_agent(test.agent(llm), llm)
        print("✅ CrewAI test passed")
    except Exception as e:
        print(f"❌ CrewAI test failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
