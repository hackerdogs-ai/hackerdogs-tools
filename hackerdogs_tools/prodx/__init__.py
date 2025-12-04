"""
Productivity Tools (prodx) - LangChain Tools

This module contains LangChain tools for productivity and file operations:
- Excel file manipulation and chart creation
- PowerPoint presentation generation
- Streamlit Plotly visualization
- OCR text extraction
- File operations and format conversion
"""

from .excel_tools import (
    ReadExcelStructuredTool,
    ModifyExcelTool,
    CreateExcelChartTool,
    AnalyzeExcelSecurityTool,
)
from .powerpoint_tools import (
    CreatePresentationTool,
    AddSlideTool,
    AddChartToSlideTool,
)
# Visualization tools are functions, not classes
# Import them conditionally to avoid breaking if dependencies are missing
try:
    from .visualization_tools import (
        create_line_chart,
        create_bar_chart,
        create_pie_chart,
        create_scatter_plot,
        create_heatmap,
        create_histogram,
        recommend_chart_type,
        create_chart_from_file,
    )
    # For backward compatibility, create aliases
    CreatePlotlyChartTool = create_line_chart  # Default to line chart
    CreateChartFromFileTool = create_chart_from_file
    VISUALIZATION_TOOLS_AVAILABLE = True
except ImportError:
    VISUALIZATION_TOOLS_AVAILABLE = False
    # Create dummy classes if import fails
    CreatePlotlyChartTool = None
    CreateChartFromFileTool = None
from .ocr_tools import (
    ExtractTextFromImageTool,
    ExtractTextFromPDFImagesTool,
    AnalyzeDocumentStructureTool,
)
from .file_operations_tools import (
    SaveFileForDownloadTool,
    ConvertFileFormatTool,
)

__all__ = [
    # Excel tools
    "ReadExcelStructuredTool",
    "ModifyExcelTool",
    "CreateExcelChartTool",
    "AnalyzeExcelSecurityTool",
    # PowerPoint tools
    "CreatePresentationTool",
    "AddSlideTool",
    "AddChartToSlideTool",
    # Visualization tools
    "CreatePlotlyChartTool",
    "CreateChartFromFileTool",
    # OCR tools
    "ExtractTextFromImageTool",
    "ExtractTextFromPDFImagesTool",
    "AnalyzeDocumentStructureTool",
    # File operations
    "SaveFileForDownloadTool",
    "ConvertFileFormatTool",
]

__version__ = "0.1.0"
