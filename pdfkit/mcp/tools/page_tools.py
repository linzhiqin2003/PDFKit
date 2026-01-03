"""MCP 页面操作工具

包含所有页面操作相关的 MCP 工具：
- 合并、拆分、提取等
"""

from typing import Any, Optional, List, Union
from pathlib import Path

from ..server import mcp
from ...core import (
    merge_files,
    split_by_pages,
    split_by_chunks,
    split_single_pages,
    split_by_count,
    split_by_size,
    extract_pages,
    extract_text,
    extract_images,
    parse_page_range,
    parse_chunks,
    MergeResult,
    SplitResult,
    ExtractPagesResult,
    ExtractTextResult,
    ExtractImagesResult,
    PDFMergeError,
    PDFSplitError,
    PDFExtractError,
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
from ..schemas import (
    CompressionQuality,
    ImageFormat,
)


# ==================== 合并工具 ====================

@mcp.tool(
    name="pdfkit_merge_files",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_merge_files(
    file_paths: List[str],
    output_path: str,
    bookmark: bool = True,
    sort: bool = False,
    auto_repair: bool = True,
    skip_errors: bool = False,
    ctx: Optional[Any] = None,
) -> dict:
    """
    合并多个 PDF 文件为一个文件。

    Args:
        file_paths: 要合并的 PDF 文件路径列表
        output_path: 输出文件路径
        bookmark: 是否为每个文件添加书签
        sort: 是否按文件名排序
        auto_repair: 是否自动修复损坏的 PDF
        skip_errors: 是否跳过错误继续处理

    Returns:
        合并结果:
        {
            "success": bool,
            "data": {
                "output_path": str,
                "total_files": int,
                "merged_files": int,
                "total_pages": int,
                "failed_files": list
            },
            "message": str
        }
    """
    await log_info(ctx, f"准备合并 {len(file_paths)} 个 PDF 文件")
    await report_progress(ctx, 0.1, "正在验证文件...")

    # 验证所有文件
    valid_files = []
    for f in file_paths:
        try:
            valid_files.append(validate_pdf_file(f))
        except Exception as e:
            if not skip_errors:
                return format_error(e)
            await log_warning(ctx, f"跳过无效文件: {f}")

    if not valid_files:
        return {
            "success": False,
            "error": "没有有效的 PDF 文件",
            "error_type": "no_valid_files",
        }

    # 排序
    if sort:
        valid_files.sort(key=lambda x: x.name)

    await report_progress(ctx, 0.3, "正在合并...")

    try:
        result: MergeResult = merge_files(
            valid_files,
            output_path,
            bookmark=bookmark,
            auto_repair=auto_repair,
            skip_errors=skip_errors,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功合并 {result.merged_files}/{result.total_files} 个文件，共 {result.total_pages} 页"
        )

    except PDFMergeError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 拆分工具 ====================

@mcp.tool(
    name="pdfkit_split_by_pages",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_split_by_pages(
    file_path: str,
    page_ranges: str,
    output_dir: str,
    prefix: str = "",
    ctx: Optional[Any] = None,
) -> dict:
    """
    按指定页面范围拆分 PDF。

    Args:
        file_path: PDF 文件路径
        page_ranges: 页面范围，如 "1-5,8,10-15"
        output_dir: 输出目录
        prefix: 输出文件名前缀

    Returns:
        拆分结果
    """
    await log_info(ctx, f"拆分 PDF: {file_path}")
    await report_progress(ctx, 0.1, "正在解析页面范围...")

    try:
        validate_pdf_file(file_path)

        # 获取总页数
        from ...core.pdf_info import get_page_count
        total_pages = get_page_count(file_path)

        await report_progress(ctx, 0.3, "正在拆分...")

        # 解析页面范围
        pages = parse_page_range(page_ranges, total_pages)

        # 执行拆分
        result: SplitResult = split_by_pages(
            file_path,
            output_dir,
            pages,
            prefix,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功拆分为 {result.total_output} 个文件"
        )

    except Exception as e:
        return format_error(e)


@mcp.tool(
    name="pdfkit_split_single_pages",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_split_single_pages(
    file_path: str,
    output_dir: str,
    prefix: str = "",
    ctx: Optional[Any] = None,
) -> dict:
    """
    将 PDF 的每一页拆分为单独的文件。

    Args:
        file_path: PDF 文件路径
        output_dir: 输出目录
        prefix: 输出文件名前缀

    Returns:
        拆分结果
    """
    await log_info(ctx, f"拆分 PDF 为单页文件: {file_path}")
    await report_progress(ctx, 0.1, "正在拆分...")

    try:
        validate_pdf_file(file_path)

        result: SplitResult = split_single_pages(
            file_path,
            output_dir,
            prefix,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功拆分为 {result.total_output} 个单页文件"
        )

    except Exception as e:
        return format_error(e)


@mcp.tool(
    name="pdfkit_split_by_size",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_split_by_size(
    file_path: str,
    max_size_mb: float,
    output_dir: str,
    prefix: str = "",
    ctx: Optional[Any] = None,
) -> dict:
    """
    按文件大小拆分 PDF。

    Args:
        file_path: PDF 文件路径
        max_size_mb: 每个文件的最大大小 (MB)
        output_dir: 输出目录
        prefix: 输出文件名前缀

    Returns:
        拆分结果
    """
    await log_info(ctx, f"按大小拆分 PDF ({max_size_mb}MB/文件): {file_path}")
    await report_progress(ctx, 0.1, "正在拆分...")

    try:
        validate_pdf_file(file_path)

        result: SplitResult = split_by_size(
            file_path,
            output_dir,
            max_size_mb,
            prefix,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功拆分为 {result.total_output} 个文件"
        )

    except Exception as e:
        return format_error(e)


@mcp.tool(
    name="pdfkit_split_by_count",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_split_by_count(
    file_path: str,
    pages_per_file: int,
    output_dir: str,
    prefix: str = "",
    ctx: Optional[Any] = None,
) -> dict:
    """
    按固定页数拆分 PDF。

    Args:
        file_path: PDF 文件路径
        pages_per_file: 每个文件的页数
        output_dir: 输出目录
        prefix: 输出文件名前缀

    Returns:
        拆分结果
    """
    await log_info(ctx, f"按页数拆分 PDF ({pages_per_file}页/文件): {file_path}")
    await report_progress(ctx, 0.1, "正在拆分...")

    try:
        validate_pdf_file(file_path)

        result: SplitResult = split_by_count(
            file_path,
            output_dir,
            pages_per_file,
            prefix,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功拆分为 {result.total_output} 个文件"
        )

    except Exception as e:
        return format_error(e)


# ==================== 提取工具 ====================

@mcp.tool(
    name="pdfkit_extract_pages",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_extract_pages(
    file_path: str,
    page_ranges: str,
    output_path: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    提取指定页面到新 PDF 文件。

    Args:
        file_path: PDF 文件路径
        page_ranges: 页面范围，如 "1-5,8,10-15"
        output_path: 输出文件路径

    Returns:
        提取结果
    """
    await log_info(ctx, f"提取页面: {file_path}")
    await report_progress(ctx, 0.1, "正在解析页面范围...")

    try:
        validate_pdf_file(file_path)

        # 获取总页数
        from ...core.pdf_info import get_page_count
        total_pages = get_page_count(file_path)

        await report_progress(ctx, 0.3, "正在提取...")

        # 解析页面范围
        pages = parse_page_range(page_ranges, total_pages)

        # 执行提取
        result: ExtractPagesResult = extract_pages(
            file_path,
            pages,
            output_path,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功提取 {result.page_count} 页到 {result.output_path}"
        )

    except Exception as e:
        return format_error(e)


@mcp.tool(
    name="pdfkit_extract_text",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def pdfkit_extract_text(
    file_path: str,
    page_ranges: Optional[str] = None,
    output_format: str = "txt",
    ctx: Optional[Any] = None,
) -> dict:
    """
    提取 PDF 文本内容。

    Args:
        file_path: PDF 文件路径
        page_ranges: 页面范围（可选），如 "1-5,8,10-15"，不指定则提取全部
        output_format: 输出格式 (txt/md)

    Returns:
        提取结果:
        {
            "success": bool,
            "data": {
                "text": str,
                "page_count": int,
                "char_count": int
            },
            "message": str
        }
    """
    await log_info(ctx, f"提取文本: {file_path}")
    await report_progress(ctx, 0.1, "正在提取...")

    try:
        validate_pdf_file(file_path)

        # 确定页面范围
        pages = None
        if page_ranges:
            from ...core.pdf_info import get_page_count
            total_pages = get_page_count(file_path)
            pages = parse_page_range(page_ranges, total_pages)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行提取
        result: ExtractTextResult = extract_text(
            file_path,
            pages=pages,
            output=None,
            format=output_format,
        )

        await report_progress(ctx, 1.0, "完成")

        # 返回时限制文本长度
        text_preview = result.text
        if len(text_preview) > 10000:
            text_preview = text_preview[:10000] + "\n\n... (文本过长，已截断)"

        return format_success(
            data={
                "text": text_preview,
                "page_count": result.page_count,
                "char_count": result.char_count,
                "truncated": len(result.text) > 10000,
            },
            message=f"成功提取 {result.page_count} 页的文本，共 {result.char_count} 个字符"
        )

    except Exception as e:
        return format_error(e)


@mcp.tool(
    name="pdfkit_extract_images",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_extract_images(
    file_path: str,
    output_dir: str,
    page_ranges: Optional[str] = None,
    format: str = "png",
    ctx: Optional[Any] = None,
) -> dict:
    """
    提取 PDF 中的图片。

    Args:
        file_path: PDF 文件路径
        output_dir: 输出目录
        page_ranges: 页面范围（可选）
        format: 输出格式 (png/jpg)

    Returns:
        提取结果
    """
    await log_info(ctx, f"提取图片: {file_path}")
    await report_progress(ctx, 0.1, "正在扫描...")

    try:
        validate_pdf_file(file_path)

        # 确定页面范围
        pages = None
        if page_ranges:
            from ...core.pdf_info import get_page_count
            total_pages = get_page_count(file_path)
            pages = parse_page_range(page_ranges, total_pages)

        await report_progress(ctx, 0.3, "正在提取...")

        # 执行提取
        result: ExtractImagesResult = extract_images(
            file_path,
            output_dir,
            pages=pages,
            format=format,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data={
                "total_images": result.total_images,
                "output_dir": result.output_dir,
                "images": [
                    {
                        "output_path": img.output_path,
                        "page_number": img.page_number,
                        "image_index": img.image_index,
                    }
                    for img in result.images[:10]  # 只返回前10个
                ],
            },
            message=f"成功提取 {result.total_images} 张图片到 {result.output_dir}"
        )

    except Exception as e:
        return format_error(e)
