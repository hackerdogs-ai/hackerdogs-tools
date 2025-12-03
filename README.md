# HackerDogs Tools

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/hackerdogs-tools)](https://pypi.org/project/hackerdogs-tools/)

Comprehensive LangChain, CrewAI, and MCP Server tools for the hackerdogs.ai platform. This library provides production-ready tools for threat intelligence, log analysis, productivity automation, and more.

## Features

### 🛡️ Threat Intelligence (TI) Tools
- **AlienVault OTX**: Query threat intelligence for files, URLs, domains, and IP addresses
- **VirusTotal**: Comprehensive malware analysis and threat detection
- **MISP**: Malware Information Sharing Platform integration
- **OpenCTI**: Open Cyber Threat Intelligence platform with STIX 2.1 support

### 📊 VictoriaLogs Tools
- Query VictoriaLogs using LogsQL syntax
- Stats queries for aggregations and metrics
- Hits analysis for time-series data
- Multi-tenancy support
- Stream discovery and field analysis

### 📈 Productivity Tools (prodx)
- **Excel Tools**: Read, modify, create charts, and analyze Excel files
- **PowerPoint Tools**: Generate presentations and add slides with charts
- **OCR Tools**: Extract text from images and PDFs using EasyOCR and Tesseract
- **Visualization Tools**: Create interactive Plotly charts
- **File Operations**: File format conversion and management

### 🌐 Browser Tools
- Web scraping and content analysis
- Browserless integration for headless browsing

## Installation

### From PyPI

```bash
pip install hackerdogs-tools
```

### With Optional Dependencies

```bash
# With threat intelligence tools
pip install hackerdogs-tools[ti]

# With all optional dependencies
pip install hackerdogs-tools[all]

# Development dependencies
pip install hackerdogs-tools[dev]
```

### From Source

```bash
git clone https://github.com/hackerdogs/hackerdogs-tools.git
cd hackerdogs-tools
pip install -e .
```

## Quick Start

### Threat Intelligence Example

```python
from langchain.agents import create_agent
from hackerdogs_tools.ti import (
    otx_file_report,
    otx_url_report,
    virustotal_domain_report,
)

# Create agent with TI tools
agent = create_agent(
    model=llm,
    tools=[otx_file_report, otx_url_report, virustotal_domain_report],
    system_prompt="You are a cybersecurity threat intelligence analyst."
)

# Initialize state with API keys
result = agent.invoke({
    "messages": [{"role": "user", "content": "Check if example.com is malicious"}],
    "api_keys": {
        "API_KEY": "your_otx_api_key",  # For OTX tools
        "VT_API_KEY": "your_vt_api_key"  # For VirusTotal tools
    },
    "user_id": "analyst_001"
})
```

### VictoriaLogs Example

```python
from langchain.agents import create_agent
from hackerdogs_tools.victorialogs_tools import (
    victorialogs_query,
    victorialogs_stats,
    victorialogs_hits,
)

agent = create_agent(
    model=llm,
    tools=[victorialogs_query, victorialogs_stats, victorialogs_hits],
    system_prompt="You are a log analyst."
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Show me errors from the last hour"}]
})
```

### Productivity Tools Example

```python
from langchain.agents import create_agent
from hackerdogs_tools.prodx import (
    ReadExcelStructuredTool,
    CreateExcelChartTool,
    ExtractTextFromImageTool,
)

agent = create_agent(
    model=llm,
    tools=[
        ReadExcelStructuredTool(),
        CreateExcelChartTool(),
        ExtractTextFromImageTool(),
    ],
    system_prompt="You are a productivity assistant."
)
```

## Package Structure

```
hackerdogs_tools/
├── __init__.py
├── ti/                    # Threat Intelligence tools
│   ├── otx.py            # AlienVault OTX integration
│   ├── virus_total.py    # VirusTotal integration
│   ├── misp.py           # MISP integration
│   └── opencti.py        # OpenCTI integration
├── prodx/                # Productivity tools
│   ├── excel_tools.py
│   ├── powerpoint_tools.py
│   ├── ocr_tools.py
│   ├── visualization_tools.py
│   └── file_operations_tools.py
├── victorialogs_tools.py  # VictoriaLogs querying
├── browserless_tool.py    # Web scraping
└── tool_logging.py        # Logging utilities
```

## API Key Management

All tools use LangChain's `ToolRuntime` to securely access API keys from agent state. API keys are never exposed to the LLM and are stored securely in the agent state.

### Example State Configuration

```python
initial_state = {
    "messages": [...],
    "user_id": "analyst_001",
    "api_keys": {
        "API_KEY": "your_api_key",      # For OTX, MISP, OpenCTI
        "VT_API_KEY": "your_vt_key",    # For VirusTotal
    },
    # OpenCTI specific
    "opencti_url": "https://your-opencti-instance.com",
}
```

## Testing

The repository includes comprehensive test suites for all tools:

### Running Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest hackerdogs_tools/ti/test_otx.py
pytest hackerdogs_tools/prodx/test_excel_tools.py

# Run with coverage
pytest --cov=hackerdogs_tools --cov-report=html
```

### LLM-Based Testing

The repository includes LLM-based testing using DirectL and LLM APIs:

```bash
# Run LLM integration tests
python hackerdogs_tools/prodx/run_llm_tests.py

# Run comprehensive real-world tests
python hackerdogs_tools/prodx/execute_comprehensive_tests.py
```

## Documentation

### Threat Intelligence Tools

- [OTX Tools Documentation](hackerdogs_tools/ti/otx.py) - AlienVault OTX integration
- [VirusTotal Tools Documentation](hackerdogs_tools/ti/virus_total.py) - VirusTotal API integration
- [MISP Tools Documentation](hackerdogs_tools/ti/misp.py) - MISP platform integration
- [OpenCTI Tools Documentation](hackerdogs_tools/ti/opencti.py) - OpenCTI STIX 2.1 integration

### Productivity Tools

- [Excel Tools](hackerdogs_tools/prodx/excel_tools.py) - Excel file manipulation
- [PowerPoint Tools](hackerdogs_tools/prodx/powerpoint_tools.py) - Presentation generation
- [OCR Tools](hackerdogs_tools/prodx/ocr_tools.py) - Text extraction from images/PDFs
- [Visualization Tools](hackerdogs_tools/prodx/visualization_tools.py) - Plotly chart creation
- [File Operations](hackerdogs_tools/prodx/file_operations_tools.py) - File format conversion

### VictoriaLogs Tools

- [VictoriaLogs Documentation](hackerdogs_tools/victorialogs_tools.py) - LogsQL querying and analysis

## Requirements

### Core Dependencies
- Python 3.8+
- LangChain 1.1.0+
- Pydantic 2.12.5+
- Requests 2.32.5+

### Optional Dependencies
- **Threat Intelligence**: OTXv2, pycti, pymisp
- **OCR**: EasyOCR, Tesseract, pdf2image
- **Excel**: openpyxl, pandas
- **PowerPoint**: python-pptx
- **Visualization**: plotly

See [requirements.txt](requirements.txt) for the complete list.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/hackerdogs/hackerdogs-tools.git
cd hackerdogs-tools

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black hackerdogs_tools/
ruff check hackerdogs_tools/
```

## Security

- API keys are never exposed to LLMs
- All tools use secure state management via ToolRuntime
- Sensitive data is masked in logs
- Comprehensive error handling prevents information leakage

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [GitHub Wiki](https://github.com/hackerdogs/hackerdogs-tools/wiki)
- **Issues**: [GitHub Issues](https://github.com/hackerdogs/hackerdogs-tools/issues)
- **Email**: info@hackerdogs.ai

## Roadmap

- [ ] CrewAI tool integration
- [ ] MCP Server implementation
- [ ] Additional threat intelligence sources
- [ ] Enhanced visualization capabilities
- [ ] More file format support
- [ ] Performance optimizations
- [ ] Comprehensive documentation site

## Acknowledgments

- Built for the [hackerdogs.ai](https://hackerdogs.ai) platform
- Uses [LangChain](https://www.langchain.com/) for agent orchestration
- Integrates with leading threat intelligence platforms
- Powered by open-source security tools

---

**Made with ❤️ by the HackerDogs team**
