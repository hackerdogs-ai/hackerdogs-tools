"""
Run OSINT tool tests grouped by use case

Based on the 10 OSINT use cases from top10-scenarios.md
"""

import sys
import argparse
from pathlib import Path

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass  # dotenv not required

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# Use case definitions
USE_CASES = {
    1: {
        "name": "Attack Surface Discovery",
        "description": "Map every subdomain, IP, and cloud asset belonging to Company X",
        "agent": "Infrastructure_Recon_Agent",
        "tools": ["subfinder", "amass", "dnsdumpster", "theharvester", "nuclei", "masscan"]
    },
    2: {
        "name": "Executive Protection (VIP Vetting)",
        "description": "Find leaked passwords and home addresses exposed for the CEO",
        "agent": "Identity_Hunter_Agent",
        "tools": ["holehe", "ghunt", "sherlock", "maigret"]
    },
    3: {
        "name": "Brand Impersonation Detection",
        "description": "Find phishing domains and fake social media accounts pretending to be us",
        "agent": "Threat_Intel_Agent + Identity_Hunter_Agent",
        "tools": ["abuseipdb", "urlhaus", "otx", "sherlock", "maigret"]
    },
    4: {
        "name": "Supply Chain Risk",
        "description": "Does our vendor 'Acme Corp' have open ports or malware infections?",
        "agent": "Infrastructure_Recon_Agent + Threat_Intel_Agent",
        "tools": ["subfinder", "amass", "nuclei", "abuseipdb", "urlhaus", "otx", "misp"]
    },
    5: {
        "name": "Breach Intelligence",
        "description": "Which employee emails were exposed in the 'MOAB' leak?",
        "agent": "Identity_Hunter_Agent",
        "tools": ["holehe", "ghunt"]
    },
    6: {
        "name": "Username Enumeration (SOCMINT)",
        "description": "Find all social profiles associated with the handle 'hacker_123'",
        "agent": "Identity_Hunter_Agent",
        "tools": ["sherlock", "maigret"]
    },
    7: {
        "name": "Cloud Bucket Exposure",
        "description": "Scan for open AWS S3 buckets or Azure blobs linked to this domain",
        "agent": "Infrastructure_Recon_Agent",
        "tools": ["waybackurls", "scrapy", "subfinder"]
    },
    8: {
        "name": "Vulnerability Triage",
        "description": "Does this specific subdomain have the 'Log4Shell' vulnerability?",
        "agent": "Infrastructure_Recon_Agent",
        "tools": ["nuclei", "subfinder", "amass"]
    },
    9: {
        "name": "Dark Web Monitoring",
        "description": "Is our company mentioned in recent ransomware leak sites?",
        "agent": "Threat_Intel_Agent",
        "tools": ["onionsearch"]
    },
    10: {
        "name": "Geospatial Recon (GEOINT)",
        "description": "Where was this photo taken? (Geolocation via EXIF/Landmarks)",
        "agent": "Infrastructure_Recon_Agent",
        "tools": ["exiftool"]
    }
}


def run_tool_test(tool_name: str) -> bool:
    """Run test for a specific tool."""
    try:
        import importlib
        test_module = importlib.import_module(f"hackerdogs_tools.osint.tests.test_{tool_name}")
        
        if hasattr(test_module, 'run_all_tests'):
            print(f"\n{'='*80}")
            print(f"Running {tool_name.upper()} Tests")
            print('='*80)
            test_module.run_all_tests()
            return True
        else:
            print(f"⚠️  test_{tool_name}.py does not have run_all_tests() function")
            return False
    except ImportError as e:
        print(f"❌ Failed to import test_{tool_name}: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error running test_{tool_name}: {str(e)}")
        return False


def run_usecase(usecase_num: int):
    """Run tests for a specific use case."""
    if usecase_num not in USE_CASES:
        print(f"❌ Invalid use case number: {usecase_num}")
        print(f"Valid use cases: {list(USE_CASES.keys())}")
        return
    
    usecase = USE_CASES[usecase_num]
    print("\n" + "="*80)
    print(f"USE CASE #{usecase_num}: {usecase['name']}")
    print("="*80)
    print(f"Description: {usecase['description']}")
    print(f"Agent(s): {usecase['agent']}")
    print(f"Tools: {', '.join(usecase['tools'])}")
    print()
    
    results = {}
    for tool_name in usecase['tools']:
        print(f"\n📋 Testing: {tool_name}")
        success = run_tool_test(tool_name)
        results[tool_name] = "✅ Passed" if success else "❌ Failed"
    
    # Summary
    print("\n" + "="*80)
    print(f"USE CASE #{usecase_num} SUMMARY")
    print("="*80)
    for tool, status in results.items():
        print(f"  {status} {tool}")
    
    return results


def list_usecases():
    """List all available use cases."""
    print("\n" + "="*80)
    print("Available OSINT Use Cases")
    print("="*80)
    
    for usecase_num, usecase in USE_CASES.items():
        print(f"\n#{usecase_num}: {usecase['name']}")
        print(f"  Description: {usecase['description']}")
        print(f"  Agent(s): {usecase['agent']}")
        print(f"  Tools: {', '.join(usecase['tools'])}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run OSINT tool tests by use case",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run Use Case #1 (Attack Surface Discovery)
  python run_tests_by_usecase.py --usecase 1
  
  # List all use cases
  python run_tests_by_usecase.py --list
  
  # Run all use cases sequentially
  python run_tests_by_usecase.py --all
        """
    )
    
    parser.add_argument(
        '--usecase',
        type=int,
        help='Use case number to run (1-10)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available use cases'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all use cases sequentially'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_usecases()
        return
    
    if args.all:
        print("="*80)
        print("Running ALL Use Cases Sequentially")
        print("="*80)
        for usecase_num in sorted(USE_CASES.keys()):
            run_usecase(usecase_num)
        return
    
    if args.usecase:
        run_usecase(args.usecase)
    else:
        parser.print_help()
        print("\n💡 Tip: Use --list to see all available use cases")


if __name__ == "__main__":
    main()

