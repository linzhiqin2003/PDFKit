"""MCP 编辑工具

包含所有编辑相关的 MCP 工具：
- 添加水印、裁剪、调整大小
- 添加页眉页脚
"""

from typing import Any, Optional, List, Union
from pathlib import Path

from ..server import mcp
from ...core import (
    add_watermark,
    crop_pages,
    resize_pages,
    add_header,
    add_footer,
    WatermarkResult,
    CropResult,
    ResizeResult,
    HeaderResult,
    FooterResult,
    PDFEditError,
    EditEncryptedPDFError,
    InvalidParameterError,
    PDFHeaderError,
    HeaderEncryptedPDFError,
    HeaderInvalidParameterError,
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


# ==================== 添加水印 ====================

@mcp.tool(
    name="pdfkit_add_watermark",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_add_watermark(
    file_path: str,
    output_path: str,
    text: Optional[str] = None,
    image_path: Optional[str] = None,
    angle: int = 0,
    opacity: float = 0.3,
    font_size: int = 48,
    color: str = "#FF0000",
    position: str = "center",
    layer: str = "overlay",
    ctx: Optional[Any] = None,
) -> dict:
    """
    添加水印到 PDF

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        text: 文字水印内容
        image_path: 图片水印路径
        angle: 旋转角度 (0/90/180/270)
        opacity: 透明度 (0-1)
        font_size: 字体大小
        color: 颜色 (十六进制，如 #FF0000)
        position: 位置 (center/top-left/top-right/bottom-left/bottom-right)
        layer: 图层 (overlay/underlay)

    Returns:
        添加结果
    """
    await log_info(ctx, f"添加水印: {file_path}")
    await report_progress(ctx, 0.1, "正在添加水印...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行添加水印
        result: WatermarkResult = add_watermark(
            file_path,
            output_path,
            text=text,
            image_path=image_path,
            angle=angle,
            opacity=opacity,
            font_size=font_size,
            color=color,
            position=position,
            layer=layer,
        )

        await report_progress(ctx, 1.0, "完成")

        watermark_type = "文字" if text else "图片"
        return format_success(
            data=result.to_dict(),
            message=f"成功添加{watermark_type}水印，共 {result.page_count} 页"
        )

    except InvalidParameterError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "invalid_parameter",
        }
    except PDFEditError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 裁剪页面 ====================

@mcp.tool(
    name="pdfkit_crop_pages",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_crop_pages(
    file_path: str,
    output_path: str,
    margin: Optional[List[float]] = None,
    box: Optional[List[float]] = None,
    ctx: Optional[Any] = None,
) -> dict:
    """
    裁剪 PDF 页面

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        margin: 边距 [top, right, bottom, left]
        box: 裁剪框 [x0, y0, x1, y1]

    Returns:
        裁剪结果
    """
    await log_info(ctx, f"裁剪页面: {file_path}")
    await report_progress(ctx, 0.1, "正在裁剪...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行裁剪
        result: CropResult = crop_pages(
            file_path,
            output_path,
            margin=margin,
            box=box,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功裁剪 PDF，共 {result.page_count} 页"
        )

    except InvalidParameterError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "invalid_parameter",
        }
    except PDFEditError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 调整大小 ====================

@mcp.tool(
    name="pdfkit_resize_pages",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_resize_pages(
    file_path: str,
    output_path: str,
    size: str = "A4",
    scale: float = 1.0,
    ctx: Optional[Any] = None,
) -> dict:
    """
    调整 PDF 页面大小

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        size: 页面大小 (A4/Letter/A3/A5 或 宽x高)
        scale: 缩放比例

    Returns:
        调整结果
    """
    await log_info(ctx, f"调整页面大小: {file_path}")
    await report_progress(ctx, 0.1, "正在调整...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行调整大小
        result: ResizeResult = resize_pages(
            file_path,
            output_path,
            size=size,
            scale=scale,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功调整页面大小为 {result.new_width}x{result.new_height}，共 {result.page_count} 页"
        )

    except InvalidParameterError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "invalid_parameter",
        }
    except PDFEditError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 添加页眉 ====================

@mcp.tool(
    name="pdfkit_add_header",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_add_header(
    file_path: str,
    output_path: str,
    text: str,
    font_size: int = 12,
    align: str = "center",
    margin_top: float = 18,
    page_ranges: Optional[str] = None,
    ctx: Optional[Any] = None,
) -> dict:
    """
    添加页眉到 PDF

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        text: 页眉文字
        font_size: 字体大小
        align: 对齐方式 (left/center/right)
        margin_top: 顶部边距（点）
        page_ranges: 页面范围（可选），如 "1-5,8,10-15"

    Returns:
        添加结果
    """
    await log_info(ctx, f"添加页眉: {file_path}")
    await report_progress(ctx, 0.1, "正在添加页眉...")

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

        # 执行添加页眉
        result: HeaderResult = add_header(
            file_path,
            output_path,
            text=text,
            font_size=font_size,
            align=align,
            margin_top=margin_top,
            pages=pages,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功添加页眉到 {result.page_count} 页"
        )

    except HeaderInvalidParameterError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "invalid_parameter",
        }
    except PDFHeaderError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 添加页脚 ====================

@mcp.tool(
    name="pdfkit_add_footer",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_add_footer(
    file_path: str,
    output_path: str,
    text: str,
    font_size: int = 10,
    align: str = "center",
    margin_bottom: float = 18,
    page_ranges: Optional[str] = None,
    ctx: Optional[Any] = None,
) -> dict:
    """
    添加页脚到 PDF

    支持的变量:
        {page}  - 当前页码
        {total} - 总页数
        {date}  - 当前日期
        {time}  - 当前时间

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        text: 页脚文字（支持变量）
        font_size: 字体大小
        align: 对齐方式 (left/center/right)
        margin_bottom: 底部边距（点）
        page_ranges: 页面范围（可选），如 "1-5,8,10-15"

    Returns:
        添加结果
    """
    await log_info(ctx, f"添加页脚: {file_path}")
    await report_progress(ctx, 0.1, "正在添加页脚...")

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

        # 执行添加页脚
        result: FooterResult = add_footer(
            file_path,
            output_path,
            text=text,
            font_size=font_size,
            align=align,
            margin_bottom=margin_bottom,
            pages=pages,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功添加页脚到 {result.page_count} 页"
        )

    except HeaderInvalidParameterError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "invalid_parameter",
        }
    except PDFHeaderError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)
