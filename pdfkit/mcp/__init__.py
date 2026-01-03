"""PDFKit MCP 服务器

将 PDFKit CLI 工具扩展为 MCP (Model Context Protocol) 服务器，
使 AI 模型能够直接调用 PDF 处理功能。

使用方式:
    pdfkit-mcp              # stdio 模式
    pdfkit-mcp --http       # HTTP 模式

版本历史:
    v0.2.0 (2026-01-03) - 添加错误码系统、参数验证、友好错误消息、超时重试机制
    v0.1.0 - 初始版本
"""

__version__ = "0.2.0"

from .server import mcp, main

# 内部模块（供工具使用）
# - errors: 错误码和错误详情定义
# - validators: 参数验证框架
# - messages: 友好错误消息模板
# - timeout: 超时和重试机制
# - utils: 工具函数和格式化

__all__ = ["mcp", "main"]
