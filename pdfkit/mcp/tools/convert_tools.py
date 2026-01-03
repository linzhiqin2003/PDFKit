"""MCP 转换工具

包含所有转换相关的 MCP 工具：
- PDF 转图片、图片转 PDF
- PDF 转 Word、HTML、Markdown
- HTML/网页转 PDF
"""

from typing import Any, Optional, List, Union
from pathlib import Path

from ..server import mcp
from ...core import (
    pdf_to_images,
    images_to_pdf,
    pdf_to_word,
    pdf_to_html,
    pdf_to_markdown,
    html_to_pdf,
    url_to_pdf,
    ConvertToImagesResult,
    ImagesToPDFResult,
    ConvertToWordResult,
    ConvertToHTMLResult,
    ConvertToMarkdownResult,
    HTMLToPDFResult,
    URLToPDFResult,
    PDFConvertError,
    DependencyNotFoundError,
    UnsupportedFormatError,
    ConvertEncryptedPDFError,
)
from ..utils import (
    format_error,
    format_success,
    validate_pdf_file,
    validate_output_path,
    report_progress,
    log_info,
    log_warning,
)


# ==================== PDF 转图片 ====================

@mcp.tool(
    name="pdfkit_pdf_to_images",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_pdf_to_images(
    file_path: str,
    output_dir: str,
    format: str = "png",
    dpi: int = 150,
    page_ranges: Optional[str] = None,
    single: bool = False,
    ctx: Optional[Any] = None,
) -> dict:
    """
    将 PDF 转换为图片

    Args:
        file_path: PDF 文件路径
        output_dir: 输出目录
        format: 输出格式 (png/jpg/webp)
        dpi: 输出 DPI
        page_ranges: 页面范围（可选），如 "1-5,8,10-15"
        single: 是否合并为一张图片

    Returns:
        转换结果
    """
    await log_info(ctx, f"PDF 转图片: {file_path}")
    await report_progress(ctx, 0.1, "正在转换...")

    try:
        validate_pdf_file(file_path)

        # 确定页面范围
        pages = None
        if page_ranges:
            from ...core.pdf_info import get_page_count
            from ...core.pdf_split import parse_page_range
            total_pages = get_page_count(file_path)
            pages = parse_page_range(page_ranges, total_pages)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行转换
        result: ConvertToImagesResult = pdf_to_images(
            file_path,
            output_dir,
            format=format,
            dpi=dpi,
            pages=pages,
            single=single,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功转换 {result.image_count} 张图片到 {result.output_dir}"
        )

    except PDFConvertError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 图片转 PDF ====================

@mcp.tool(
    name="pdfkit_images_to_pdf",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_images_to_pdf(
    image_paths: List[str],
    output_path: str,
    sort: bool = False,
    ctx: Optional[Any] = None,
) -> dict:
    """
    将图片合并为 PDF

    Args:
        image_paths: 图片文件路径列表
        output_path: 输出 PDF 文件路径
        sort: 是否按文件名排序

    Returns:
        转换结果
    """
    await log_info(ctx, f"图片转 PDF: {len(image_paths)} 张图片")
    await report_progress(ctx, 0.1, "正在处理...")

    try:
        # 执行转换
        result: ImagesToPDFResult = images_to_pdf(
            image_paths,
            output_path,
            sort=sort,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功将 {result.image_count} 张图片合并为 PDF"
        )

    except DependencyNotFoundError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "dependency_not_found",
            "suggestion": "请安装所需的依赖包",
        }
    except PDFConvertError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== PDF 转 Word ====================

@mcp.tool(
    name="pdfkit_pdf_to_word",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_pdf_to_word(
    file_path: str,
    output_path: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    将 PDF 转换为 Word 文档

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径

    Returns:
        转换结果
    """
    await log_info(ctx, f"PDF 转 Word: {file_path}")
    await report_progress(ctx, 0.1, "正在转换...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行转换
        result: ConvertToWordResult = pdf_to_word(
            file_path,
            output_path,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功转换 PDF 为 Word 文档，共 {result.page_count} 页"
        )

    except DependencyNotFoundError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "dependency_not_found",
            "suggestion": "请安装 python-docx: pip install python-docx",
        }
    except PDFConvertError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== PDF 转 HTML ====================

@mcp.tool(
    name="pdfkit_pdf_to_html",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_pdf_to_html(
    file_path: str,
    output_path: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    将 PDF 转换为 HTML

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径

    Returns:
        转换结果
    """
    await log_info(ctx, f"PDF 转 HTML: {file_path}")
    await report_progress(ctx, 0.1, "正在转换...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行转换
        result: ConvertToHTMLResult = pdf_to_html(
            file_path,
            output_path,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功转换 PDF 为 HTML，共 {result.page_count} 页"
        )

    except PDFConvertError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== PDF 转 Markdown ====================

@mcp.tool(
    name="pdfkit_pdf_to_markdown",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_pdf_to_markdown(
    file_path: str,
    output_path: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    将 PDF 转换为 Markdown

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径

    Returns:
        转换结果
    """
    await log_info(ctx, f"PDF 转 Markdown: {file_path}")
    await report_progress(ctx, 0.1, "正在转换...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行转换
        result: ConvertToMarkdownResult = pdf_to_markdown(
            file_path,
            output_path,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功转换 PDF 为 Markdown，共 {result.page_count} 页"
        )

    except PDFConvertError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== HTML 转 PDF ====================

@mcp.tool(
    name="pdfkit_html_to_pdf",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_html_to_pdf(
    html_path: str,
    output_path: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    将 HTML 文件转换为 PDF

    Args:
        html_path: HTML 文件路径
        output_path: 输出 PDF 文件路径

    Returns:
        转换结果
    """
    await log_info(ctx, f"HTML 转 PDF: {html_path}")
    await report_progress(ctx, 0.1, "正在转换...")

    try:
        await report_progress(ctx, 0.5, "正在处理...")

        # 执行转换
        result: HTMLToPDFResult = html_to_pdf(
            html_path,
            output_path,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功转换 HTML 为 PDF"
        )

    except DependencyNotFoundError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "dependency_not_found",
            "suggestion": "请安装 pdfkit: pip install pdfkit",
        }
    except PDFConvertError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 网页转 PDF ====================

@mcp.tool(
    name="pdfkit_url_to_pdf",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,  # 需要访问外部服务
    }
)
async def pdfkit_url_to_pdf(
    url: str,
    output_path: str,
    wait_time: float = 3.0,
    full_page: bool = True,
    width: int = 1920,
    ctx: Optional[Any] = None,
) -> dict:
    """
    将网页转换为 PDF

    Args:
        url: 网页 URL
        output_path: 输出 PDF 文件路径
        wait_time: 等待页面加载时间（秒）
        full_page: 是否截取完整页面
        width: 视口宽度

    Returns:
        转换结果
    """
    await log_info(ctx, f"网页转 PDF: {url}")
    await report_progress(ctx, 0.1, "正在加载网页...")

    try:
        await report_progress(ctx, 0.3, "正在转换...")

        # 执行转换（异步）
        result: URLToPDFResult = await url_to_pdf(
            url,
            output_path,
            wait_time=wait_time,
            full_page=full_page,
            width=width,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功转换网页为 PDF"
        )

    except DependencyNotFoundError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "dependency_not_found",
            "suggestion": "请安装 playwright: pip install playwright",
        }
    except PDFConvertError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)
