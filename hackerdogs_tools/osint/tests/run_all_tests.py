"""
Run all OSINT tool tests

This script runs all three test scenarios for each tool:
1. Standalone execution
2. LangChain agent integration
3. CrewAI agent integration

Environment variables required:
- MODEL: Model identifier (e.g., "ollama/gemma2:2b", "openai/gpt-4")
- LLM_API_KEY: API key for the provider
- PROVIDER_BASE_URL: Base URL (important for Ollama)
"""

import os
import sys
import importlib
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def run_tool_tests(tool_name: str):
    """Run all tests for a specific tool."""
    print(f"\n{'=' * 80}")
    print(f"Testing {tool_name.upper()} Tool")
    print('=' * 80)
    
    try:
        # Import test module
        test_module = importlib.import_module(f"hackerdogs_tools.osint.tests.test_{tool_name}")
        
        # Run all tests
        if hasattr(test_module, 'run_all_tests'):
            test_module.run_all_tests()
        else:
            print(f"⚠️  test_{tool_name}.py does not have run_all_tests() function")
            
    except ImportError as e:
        print(f"❌ Failed to import test_{tool_name}: {str(e)}")
    except Exception as e:
        print(f"❌ Error running tests for {tool_name}: {str(e)}")


def main():
    """Run all tool tests."""
    # Check environment variables
    model = os.getenv("MODEL", "").strip()
    if not model:
        print("⚠️  WARNING: MODEL environment variable not set")
        print("   Set MODEL in .env file (e.g., MODEL=ollama/gemma2:2b)")
        print("   Continuing anyway...\n")
    
    # Get all test files
    test_dir = Path(__file__).parent
    test_files = sorted(test_dir.glob("test_*.py"))
    test_files = [f for f in test_files if f.name != "test_utils.py" and f.name != "test_amass.py"]
    
    # Add test_amass.py first (example)
    test_files.insert(0, test_dir / "test_amass.py")
    
    print("=" * 80)
    print("OSINT Tools Test Suite")
    print("=" * 80)
    print(f"\nFound {len(test_files)} test files")
    print(f"Model: {model or 'Not set'}")
    print(f"API Key: {'Set' if os.getenv('LLM_API_KEY') else 'Not set'}")
    print(f"Base URL: {os.getenv('PROVIDER_BASE_URL', 'Not set')}")
    print("\n" + "=" * 80)
    
    # Run tests for each tool
    results = {}
    for test_file in test_files:
        tool_name = test_file.stem.replace("test_", "")
        print(f"\n📋 Running tests for: {tool_name}")
        try:
            run_tool_tests(tool_name)
            results[tool_name] = "completed"
        except Exception as e:
            print(f"❌ Failed to run tests for {tool_name}: {str(e)}")
            results[tool_name] = f"error: {str(e)}"
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    for tool_name, status in results.items():
        status_icon = "✅" if status == "completed" else "❌"
        print(f"{status_icon} {tool_name}: {status}")
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()

