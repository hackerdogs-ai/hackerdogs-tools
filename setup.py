"""
Setup script for hackerdogs-tools package.
This provides compatibility with older pip versions that don't support pyproject.toml.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
if (this_directory / "requirements.txt").exists():
    with open(this_directory / "requirements.txt", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="hackerdogs-tools",
    version="0.1.0",
    author="HackerDogs",
    author_email="info@hackerdogs.ai",
    description="LangChain, CrewAI, and MCP Server Tools for hackerdogs.ai Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hackerdogs/hackerdogs-tools",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=9.0.1",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "ti": [
            "OTXv2",
            "pycti",
            "pymisp",
        ],
        "all": [
            "hackerdogs-tools[dev,ti]",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

