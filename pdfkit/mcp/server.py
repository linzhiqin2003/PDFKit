"""PDFKit MCP 服务器

使用 FastMCP 实现 MCP 协议服务器，提供 PDF 处理工具集。
"""

import sys
from contextlib import asynccontextmanager
from typing import Any, Optional

# MCP 服务器
from mcp.server.fastmcp import FastMCP

# 核心服务
from ..core.pdf_info import get_pdf_info, PDFInfoError, PDFEncryptedError

# MCP 工具
from .utils import (
    format_error,
    format_success,
    validate_pdf_file,
    report_progress,
    log_info,
)
from .schemas import PDFInfo


# ==================== 服务生命周期 ====================

@asynccontextmanager
async def app_lifespan(app: FastMCP):
    """服务生命周期管理"""
    # 初始化配置
    from ..utils.config import load_config
    config = load_config()

    # 这里可以添加其他初始化逻辑
    # 例如：数据库连接、缓存初始化等

    yield {"config": config}

    # 清理资源
    # 这里可以添加清理逻辑


# ==================== MCP 服务器初始化 ====================

mcp = FastMCP(
    "pdfkit_mcp",
    lifespan=app_lifespan,
)


# ==================== MCP 工具 ====================

@mcp.tool(
    name="pdfkit_get_info",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def pdfkit_get_info(
    file_path: str,
    detailed: bool = False,
    ctx: Optional[Any] = None,
) -> dict:
    """
    获取 PDF 文件的基本信息。

    返回文件名、大小、页数、加密状态等信息。
    如果 detailed=True，还会返回元数据（标题、作者等）。

    Args:
        file_path: PDF 文件路径（绝对路径或相对路径）
        detailed: 是否返回详细信息（包括元数据）

    Returns:
        包含 PDF 信息的字典:
        {
            "success": bool,
            "data": {
                "filename": str,
                "path": str,
                "size_bytes": int,
                "size_human": str,
                "page_count": int,
                "version": str,
                "is_encrypted": bool,
                "title": str | null,
                "author": str | null,
                ...
            },
            "error": str | null,
            "message": str
        }
    """
    await log_info(ctx, f"获取 PDF 信息: {file_path}")
    await report_progress(ctx, 0.1, "正在读取文件...")

    try:
        # 验证文件
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在解析 PDF...")

        # 获取信息
        info = get_pdf_info(file_path, detailed=detailed)

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=info.to_dict(),
            message=f"成功获取 PDF 信息: {info.filename} ({info.page_count} 页)"
        )

    except PDFEncryptedError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "encrypted_pdf",
            "suggestion": "请使用 pdfkit_decrypt 解密后再操作",
        }

    except PDFInfoError as e:
        return format_error(e)

    except Exception as e:
        return format_error(e)


@mcp.tool(
    name="pdfkit_get_page_count",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def pdfkit_get_page_count(
    file_path: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    快速获取 PDF 文件的页数。

    这比 pdfkit_get_info 更快，因为它只读取页数而不获取其他信息。

    Args:
        file_path: PDF 文件路径

    Returns:
        包含页数的字典:
        {
            "success": bool,
            "data": {"page_count": int},
            "message": str
        }
    """
    await log_info(ctx, f"获取 PDF 页数: {file_path}")

    try:
        # 验证文件
        validate_pdf_file(file_path)

        # 获取页数
        from ..core.pdf_info import get_page_count
        page_count = get_page_count(file_path)

        return format_success(
            data={"page_count": page_count},
            message=f"PDF 共 {page_count} 页"
        )

    except Exception as e:
        return format_error(e)


@mcp.tool(
    name="pdfkit_get_metadata",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def pdfkit_get_metadata(
    file_path: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    获取 PDF 文件的元数据。

    返回标题、作者、主题、关键词等元信息。

    Args:
        file_path: PDF 文件路径

    Returns:
        包含元数据的字典:
        {
            "success": bool,
            "data": {
                "title": str | null,
                "author": str | null,
                "subject": str | null,
                "keywords": str | null,
                "creator": str | null,
                "producer": str | null,
                "created": str | null,
                "modified": str | null
            },
            "message": str
        }
    """
    await log_info(ctx, f"获取 PDF 元数据: {file_path}")

    try:
        # 验证文件
        validate_pdf_file(file_path)

        # 获取元数据
        from ..core.pdf_info import get_metadata
        metadata = get_metadata(file_path)

        # 清理空值
        cleaned_metadata = {k: v or None for k, v in metadata.items()}

        return format_success(
            data=cleaned_metadata,
            message="成功获取 PDF 元数据"
        )

    except Exception as e:
        return format_error(e)


# ==================== 导入工具模块 ====================
# 导入工具模块以注册到 MCP 服务器
from .tools import page_tools
from .tools import convert_tools
from .tools import edit_tools
from .tools import security_optimize_tools
from .tools import ocr_tools


# ==================== 主入口 ====================

def main():
    """MCP 服务器入口"""
    # 检查命令行参数
    if "--http" in sys.argv:
        # HTTP 模式（用于开发测试）
        import uvicorn

        port = 8000
        if "--port" in sys.argv:
            idx = sys.argv.index("--port")
            if idx + 1 < len(sys.argv):
                port = int(sys.argv[idx + 1])

        print(f"Starting PDFKit MCP Server in HTTP mode on port {port}...", file=sys.stderr)
        uvicorn.run(mcp.sse_app, host="127.0.0.1", port=port)
    else:
        # stdio 模式（默认）
        mcp.run()


if __name__ == "__main__":
    main()
