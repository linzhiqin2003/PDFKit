"""PDFKit MCP 服务器

将 PDFKit CLI 工具扩展为 MCP (Model Context Protocol) 服务器，
使 AI 模型能够直接调用 PDF 处理功能。

使用方式:
    pdfkit-mcp              # stdio 模式
    pdfkit-mcp --http       # HTTP 模式
"""

__version__ = "0.1.0"

from .server import mcp, main

__all__ = ["mcp", "main"]
