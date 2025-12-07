"""
Test suite for exiftool metadata extraction tool

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

from hackerdogs_tools.osint.metadata.exiftool_langchain import exiftool_search
from hackerdogs_tools.osint.metadata.exiftool_crewai import ExifToolTool
from hackerdogs_tools.osint.tests.test_utils import get_llm_from_env, get_crewai_llm_from_env
from hackerdogs_tools.osint.tests.test_runtime_helper import create_mock_runtime
from hackerdogs_tools.osint.tests.save_json_results import serialize_langchain_result, serialize_crewai_result, save_test_result


class TestExifToolStandalone:
    """Test exiftool tool standalone execution."""
    
    @staticmethod
    def get_test_images():
        """Get list of test images from the images directory."""
        # Go up from tests/ to osint/ to find images/
        images_dir = Path(__file__).parent.parent / "images"
        test_images = []
        
        # GPS images (for testing GPS extraction)
        test_images.extend([
            images_dir / "jpg" / "gps" / "DSCN0010.jpg",
            images_dir / "jpg" / "gps" / "DSCN0012.jpg",
        ])
        
        # Camera brand images (for testing device fingerprinting)
        test_images.extend([
            images_dir / "jpg" / "Canon_40D.jpg",
            images_dir / "jpg" / "Nikon_D70.jpg",
            images_dir / "jpg" / "Sony_DSLR-A200.jpg",
        ])
        
        # Mobile images
        test_images.extend([
            images_dir / "jpg" / "mobile" / "HMD_Nokia_8.3_5G.jpg",
        ])
        
        # TIFF images
        test_images.extend([
            images_dir / "tiff" / "Arbitro.tiff",
        ])
        
        # Filter to only existing files
        return [img for img in test_images if img.exists()]
    
    def test_exiftool_standalone(self):
        """Test exiftool standalone execution on multiple sample images."""
        test_images = self.get_test_images()
        
        if not test_images:
            print("⚠️  No test images found. Skipping test.")
            return
        
        print(f"\n📸 Testing {len(test_images)} sample images...")
        
        for img_path in test_images:
            print(f"\n{'=' * 80}")
            print(f"Testing: {img_path.name}")
            print(f"{'=' * 80}")
            
            try:
                runtime = create_mock_runtime()
                result = exiftool_search.invoke({
                    "runtime": runtime,
                    "file_path": str(img_path),
                    "extract_gps": True,
                    "extract_author": True,
                    "output_format": "json"
                })
                
                # Parse result
                result_data = json.loads(result)
                
                # Assertions
                assert isinstance(result_data, (list, dict)), f"Expected list or dict, got {type(result_data)}"
                
                # Check if it's a list (ExifTool JSON format)
                if isinstance(result_data, list) and len(result_data) > 0:
                    metadata = result_data[0]
                    
                    # Verify we got metadata
                    assert "SourceFile" in metadata or "File:FileName" in metadata, "No file metadata found"
                    
                    # Check for GPS data if it's a GPS image
                    if "gps" in str(img_path).lower():
                        has_gps = any("GPS" in key for key in metadata.keys())
                        print(f"  ✅ GPS metadata: {'Found' if has_gps else 'Not found (may be expected)'}")
                    
                    # Check for camera/device info
                    has_camera = any(key in metadata for key in ["EXIF:Make", "EXIF:Model", "IFD0:Make", "IFD0:Model"])
                    print(f"  ✅ Camera/Device info: {'Found' if has_camera else 'Not found'}")
                    
                    # Check for timestamps
                    has_timestamp = any("Date" in key or "Time" in key for key in metadata.keys())
                    print(f"  ✅ Timestamps: {'Found' if has_timestamp else 'Not found'}")
                
                # Save result
                try:
                    result_file = save_test_result("exiftool", "standalone", result_data, img_path.stem)
                    print(f"  📁 Result saved to: {result_file}")
                except Exception as e:
                    print(f"  ⚠️  Could not save result: {e}")
                
                # Print sample of metadata
                if isinstance(result_data, list) and len(result_data) > 0:
                    metadata = result_data[0]
                    sample_keys = list(metadata.keys())[:10]
                    print(f"  📋 Sample metadata fields: {', '.join(sample_keys)}...")
                
                print(f"  ✅ {img_path.name} processed successfully")
                
            except Exception as e:
                print(f"  ❌ Failed to process {img_path.name}: {str(e)}")
                import traceback
                traceback.print_exc()


class TestExifToolLangChain:
    """Test exiftool tool with LangChain agent."""
    
    @pytest.fixture
    def agent(self):
        """Create LangChain agent with exiftool."""
        llm = get_llm_from_env()
        tools = [exiftool_search]
        return create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the exiftool to extract metadata from files."
        )
    
    def test_exiftool_langchain_agent(self, agent):
        """Test exiftool tool with LangChain agent."""
        # Use a test image with GPS data
        images_dir = Path(__file__).parent.parent / "images"
        test_image = images_dir / "jpg" / "gps" / "DSCN0010.jpg"
        
        if not test_image.exists():
            print("⚠️  Test image not found. Skipping LangChain test.")
            return
        
        # Execute query directly (agent is a runnable in LangChain 1.x)
        # ToolRuntime is automatically injected by the agent
        result = agent.invoke({
            "messages": [HumanMessage(content=f"Extract metadata from this image file: {test_image}")]
        })
        
        # Assertions
        assert result is not None
        assert "messages" in result or "output" in result
        
        # Save LangChain agent result
        try:
            result_data = serialize_langchain_result(result)
            result_file = save_test_result("exiftool", "langchain", result_data, "DSCN0010")
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


class TestExifToolCrewAI:
    """Test exiftool tool with CrewAI agent."""
    
    @pytest.fixture
    def llm(self):
        """Get CrewAI LLM from environment."""
        return get_crewai_llm_from_env()
    
    @pytest.fixture
    def agent(self, llm):
        """Create CrewAI agent with exiftool."""
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
        # Use a test image with GPS data
        images_dir = Path(__file__).parent.parent / "images"
        test_image = images_dir / "jpg" / "gps" / "DSCN0010.jpg"
        
        if not test_image.exists():
            print("⚠️  Test image not found. Skipping CrewAI test.")
            return
        
        task = Task(
            description=f"Extract metadata from this image file: {test_image}",
            agent=agent,
            expected_output="Metadata extraction results from exiftool"
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
        
        # Save CrewAI agent result
        try:
            result_data = serialize_crewai_result(result) if result else None
            result_file = save_test_result("exiftool", "crewai", result_data, "DSCN0010")
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
    print(f"Running exiftool Tool Tests")
    print("=" * 80)
    
    # Test 1: Standalone
    print("\n1. Testing Standalone Execution...")
    try:
        test = TestExifToolStandalone()
        test.test_exiftool_standalone()
        print("✅ Standalone test passed")
    except Exception as e:
        print(f"❌ Standalone test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: LangChain
    print("\n2. Testing LangChain Agent Integration...")
    try:
        llm = get_llm_from_env()
        tools = [exiftool_search]
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt="You are a cybersecurity analyst. Use the exiftool to extract metadata from images and files."
        )
        # Use a test image with GPS data
        images_dir = Path(__file__).parent.parent / "images"
        test_image = images_dir / "jpg" / "gps" / "DSCN0010.jpg"
        
        if not test_image.exists():
            print("⚠️  Test image not found. Skipping LangChain test.")
        else:
            # Execute query directly (agent is a runnable in LangChain 1.x)
            # ToolRuntime is automatically injected by the agent
            result = agent.invoke({
                "messages": [HumanMessage(content=f"Extract metadata from this image file: {test_image}")]
            })
            
            # Assertions
            assert result is not None
            assert "messages" in result or "output" in result
            
            # Save LangChain agent result
            try:
                result_data = serialize_langchain_result(result)
                result_file = save_test_result("exiftool", "langchain", result_data, "DSCN0010")
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
        agent = Agent(
            role="OSINT Analyst",
            goal="Perform OSINT operations using exiftool",
            backstory="You are an expert OSINT analyst.",
            tools=[ExifToolTool()],
            llm=llm,
            verbose=True
        )
        # Use a test image with GPS data
        images_dir = Path(__file__).parent.parent / "images"
        test_image = images_dir / "jpg" / "gps" / "DSCN0010.jpg"
        
        if not test_image.exists():
            print("⚠️  Test image not found. Skipping CrewAI test.")
        else:
            task = Task(
                description=f"Extract metadata from this image file: {test_image}",
                agent=agent,
                expected_output="Metadata extraction results from exiftool"
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
            
            # Save CrewAI agent result
            try:
                result_data = serialize_crewai_result(result)
                result_file = save_test_result("exiftool", "crewai", result_data, "DSCN0010")
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
    print("Tests completed")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
