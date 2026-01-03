"""MCP OCR 工具

包含所有 OCR 相关的 MCP 工具：
- 文本识别、表格提取、版面分析
"""

import asyncio
from typing import Any, Optional, List, Union
from pathlib import Path
from io import BytesIO
import fitz  # PyMuPDF
from PIL import Image

from ..server import mcp
from ...core.ocr_handler import (
    QwenVLOCR,
    OCRModel,
    OutputFormat,
    pdf_page_to_image,
)
from ..utils import (
    format_error,
    format_success,
    validate_pdf_file,
    report_progress,
    log_info,
    log_warning,
)


# ==================== 自定义异常 ====================

class OCRError(Exception):
    """OCR 错误"""
    pass


class APIKeyError(OCRError):
    """API Key 错误"""
    pass


# ==================== OCR 识别 ====================

@mcp.tool(
    name="pdfkit_ocr_recognize",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,  # 需要访问外部 OCR API
    }
)
async def pdfkit_ocr_recognize(
    file_path: str,
    page_ranges: Optional[str] = None,
    model: str = "flash",
    output_format: str = "text",
    api_key: Optional[str] = None,
    async_mode: bool = False,
    concurrency: int = 10,
    ctx: Optional[Any] = None,
) -> dict:
    """
    使用 OCR 识别 PDF 文本

    Args:
        file_path: PDF 文件路径
        page_ranges: 页面范围（可选），如 "1-5,8,10-15"
        model: 模型选择 (flash/plus/ocr)
        output_format: 输出格式 (text/md/json)
        api_key: OCR API Key（可选）
        async_mode: 是否使用异步模式
        concurrency: 异步模式最大并发数

    Returns:
        识别结果
    """
    await log_info(ctx, f"OCR 识别: {file_path} (模型: {model})")
    await report_progress(ctx, 0.1, "正在初始化...")

    try:
        validate_pdf_file(file_path)

        # 验证模型参数
        if model not in ["flash", "plus", "ocr"]:
            return {
                "success": False,
                "error": f"无效的模型: {model}，可选值: flash, plus, ocr",
                "error_type": "invalid_model",
            }

        # 验证输出格式
        if output_format not in ["text", "md", "json"]:
            return {
                "success": False,
                "error": f"无效的输出格式: {output_format}，可选值: text, md, json",
                "error_type": "invalid_format",
            }

        # 打开 PDF
        doc = fitz.open(file_path)
        total_pages = doc.page_count

        # 确定要处理的页面
        if page_ranges:
            from ...core.pdf_split import parse_page_range
            pages = parse_page_range(page_ranges, total_pages)
        else:
            pages = list(range(total_pages))

        # 映射输出格式
        format_map = {
            "text": OutputFormat.TEXT,
            "md": OutputFormat.MARKDOWN,
            "json": OutputFormat.JSON,
        }
        ocr_format = format_map[output_format]

        # 映射模型
        model_map = {
            "flash": OCRModel.FLASH,
            "plus": OCRModel.PLUS,
            "ocr": OCRModel.OCR,
        }
        ocr_model = model_map[model]

        await report_progress(ctx, 0.2, "正在初始化 OCR 引擎...")

        # 创建 OCR 实例
        try:
            ocr = QwenVLOCR(api_key=api_key, model=ocr_model)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "api_key_missing",
                "suggestion": "请设置 DASHSCOPE_API_KEY 环境变量或提供 api_key 参数",
            }

        # 执行 OCR
        all_text = []

        if async_mode and len(pages) > 1:
            # 异步模式处理多页
            await log_info(ctx, f"使用异步模式处理 {len(pages)} 页，并发数: {concurrency}")

            semaphore = asyncio.Semaphore(concurrency)
            tasks = []

            for page_num in pages:
                task = ocr.ocr_page_async(doc, page_num, output_format=ocr_format, semaphore=semaphore)
                tasks.append(task)

            await report_progress(ctx, 0.3, "正在识别...")

            completed = 0
            total_tasks = len(tasks)

            # 使用 asyncio.as_completed 处理完成的任务
            for coro in asyncio.as_completed(tasks):
                page_num, text = await coro
                all_text.append((page_num + 1, text))  # 转为 1-index
                completed += 1
                progress = 0.3 + (completed / total_tasks) * 0.7
                await report_progress(ctx, progress, f"识别中... ({completed}/{total_tasks})")

            # 关闭异步客户端
            await ocr.close_async_client()

        else:
            # 同步模式处理
            await report_progress(ctx, 0.3, "正在识别...")

            for i, page_num in enumerate(pages):
                page = doc[page_num]
                img = pdf_page_to_image(page)

                if output_format == "json":
                    # JSON 格式需要特殊提示
                    text = await asyncio.to_thread(ocr.ocr_image, img, output_format=OutputFormat.JSON)
                else:
                    text = await asyncio.to_thread(ocr.ocr_image, img, output_format=ocr_format)

                all_text.append((page_num + 1, text))  # 转为 1-index

                progress = 0.3 + ((i + 1) / len(pages)) * 0.7
                await report_progress(ctx, progress, f"识别中... ({i + 1}/{len(pages)})")

        doc.close()

        # 合并结果
        if output_format == "json":
            # JSON 格式可能每个页面都是完整的 JSON，这里直接返回数组
            combined_result = [text for _, text in sorted(all_text)]
        else:
            combined_result = "\n\n".join([f"--- 第 {page_num} 页 ---\n{text}" for page_num, text in sorted(all_text)])

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data={
                "text": combined_result if len(str(combined_result)) < 10000 else str(combined_result)[:10000] + "\n\n... (文本过长，已截断)",
                "page_count": len(pages),
                "truncated": len(str(combined_result)) >= 10000,
            },
            message=f"成功识别 {len(pages)} 页的文本"
        )

    except Exception as e:
        return format_error(e)


# ==================== 表格提取 ====================

@mcp.tool(
    name="pdfkit_ocr_extract_tables",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,  # 需要访问外部 OCR API
    }
)
async def pdfkit_ocr_extract_tables(
    file_path: str,
    page_ranges: Optional[str] = None,
    model: str = "plus",
    api_key: Optional[str] = None,
    async_mode: bool = False,
    concurrency: int = 10,
    ctx: Optional[Any] = None,
) -> dict:
    """
    使用 OCR 提取 PDF 中的表格

    Args:
        file_path: PDF 文件路径
        page_ranges: 页面范围（可选）
        model: 模型选择 (flash/plus/ocr)，推荐使用 plus 获得更好的表格识别效果
        api_key: OCR API Key（可选）
        async_mode: 是否使用异步模式
        concurrency: 异步模式最大并发数

    Returns:
        表格提取结果
    """
    await log_info(ctx, f"OCR 提取表格: {file_path} (模型: {model})")
    await report_progress(ctx, 0.1, "正在初始化...")

    try:
        validate_pdf_file(file_path)

        # 验证模型参数
        if model not in ["flash", "plus", "ocr"]:
            return {
                "success": False,
                "error": f"无效的模型: {model}，可选值: flash, plus, ocr",
                "error_type": "invalid_model",
            }

        # 打开 PDF
        doc = fitz.open(file_path)
        total_pages = doc.page_count

        # 确定要处理的页面
        if page_ranges:
            from ...core.pdf_split import parse_page_range
            pages = parse_page_range(page_ranges, total_pages)
        else:
            pages = list(range(total_pages))

        # 映射模型
        model_map = {
            "flash": OCRModel.FLASH,
            "plus": OCRModel.PLUS,
            "ocr": OCRModel.OCR,
        }
        ocr_model = model_map[model]

        await report_progress(ctx, 0.2, "正在初始化 OCR 引擎...")

        # 创建 OCR 实例
        try:
            ocr = QwenVLOCR(api_key=api_key, model=ocr_model)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "api_key_missing",
                "suggestion": "请设置 DASHSCOPE_API_KEY 环境变量或提供 api_key 参数",
            }

        # 执行 OCR 表格提取
        all_tables = []

        if async_mode and len(pages) > 1:
            # 异步模式处理多页
            await log_info(ctx, f"使用异步模式处理 {len(pages)} 页，并发数: {concurrency}")

            semaphore = asyncio.Semaphore(concurrency)
            tasks = []

            for page_num in pages:
                # 对于表格提取，使用专门的提示词
                task = ocr.ocr_page_async(doc, page_num, output_format=OutputFormat.MARKDOWN, semaphore=semaphore)
                tasks.append(task)

            await report_progress(ctx, 0.3, "正在提取表格...")

            completed = 0
            total_tasks = len(tasks)

            for coro in asyncio.as_completed(tasks):
                page_num, text = await coro
                all_tables.append((page_num + 1, text))
                completed += 1
                progress = 0.3 + (completed / total_tasks) * 0.7
                await report_progress(ctx, progress, f"提取中... ({completed}/{total_tasks})")

            # 关闭异步客户端
            await ocr.close_async_client()

        else:
            # 同步模式处理
            await report_progress(ctx, 0.3, "正在提取表格...")

            for i, page_num in enumerate(pages):
                page = doc[page_num]
                img = pdf_page_to_image(page)

                # 使用专门的表格提取提示词
                text = await asyncio.to_thread(ocr.ocr_table, img)

                all_tables.append((page_num + 1, text))

                progress = 0.3 + ((i + 1) / len(pages)) * 0.7
                await report_progress(ctx, progress, f"提取中... ({i + 1}/{len(pages)})")

        doc.close()

        # 合并结果
        combined_result = "\n\n".join([f"--- 第 {page_num} 页表格 ---\n{text}" for page_num, text in sorted(all_tables)])

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data={
                "tables": combined_result if len(combined_result) < 10000 else combined_result[:10000] + "\n\n... (内容过长，已截断)",
                "page_count": len(pages),
                "truncated": len(combined_result) >= 10000,
            },
            message=f"成功从 {len(pages)} 页提取表格"
        )

    except Exception as e:
        return format_error(e)


# ==================== 版面分析 ====================

@mcp.tool(
    name="pdfkit_ocr_analyze_layout",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,  # 需要访问外部 OCR API
    }
)
async def pdfkit_ocr_analyze_layout(
    file_path: str,
    page_ranges: Optional[str] = None,
    model: str = "plus",
    api_key: Optional[str] = None,
    async_mode: bool = False,
    concurrency: int = 10,
    ctx: Optional[Any] = None,
) -> dict:
    """
    使用 OCR 分析 PDF 文档版面结构

    识别文档中的标题、正文、表格、图片等元素，返回结构化的版面分析结果。

    Args:
        file_path: PDF 文件路径
        page_ranges: 页面范围（可选）
        model: 模型选择 (flash/plus/ocr)，推荐使用 plus 获得更好的版面分析效果
        api_key: OCR API Key（可选）
        async_mode: 是否使用异步模式
        concurrency: 异步模式最大并发数

    Returns:
        版面分析结果 (JSON 格式)
    """
    await log_info(ctx, f"OCR 版面分析: {file_path} (模型: {model})")
    await report_progress(ctx, 0.1, "正在初始化...")

    try:
        validate_pdf_file(file_path)

        # 验证模型参数
        if model not in ["flash", "plus", "ocr"]:
            return {
                "success": False,
                "error": f"无效的模型: {model}，可选值: flash, plus, ocr",
                "error_type": "invalid_model",
            }

        # 打开 PDF
        doc = fitz.open(file_path)
        total_pages = doc.page_count

        # 确定要处理的页面
        if page_ranges:
            from ...core.pdf_split import parse_page_range
            pages = parse_page_range(page_ranges, total_pages)
        else:
            pages = list(range(total_pages))

        # 映射模型
        model_map = {
            "flash": OCRModel.FLASH,
            "plus": OCRModel.PLUS,
            "ocr": OCRModel.OCR,
        }
        ocr_model = model_map[model]

        await report_progress(ctx, 0.2, "正在初始化 OCR 引擎...")

        # 创建 OCR 实例
        try:
            ocr = QwenVLOCR(api_key=api_key, model=ocr_model)
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "api_key_missing",
                "suggestion": "请设置 DASHSCOPE_API_KEY 环境变量或提供 api_key 参数",
            }

        # 执行版面分析
        all_layouts = []

        if async_mode and len(pages) > 1:
            # 异步模式处理多页
            await log_info(ctx, f"使用异步模式处理 {len(pages)} 页，并发数: {concurrency}")

            semaphore = asyncio.Semaphore(concurrency)
            tasks = []

            for page_num in pages:
                # 对于版面分析，使用 JSON 格式
                task = ocr.ocr_page_async(doc, page_num, output_format=OutputFormat.JSON, semaphore=semaphore)
                tasks.append(task)

            await report_progress(ctx, 0.3, "正在分析版面...")

            completed = 0
            total_tasks = len(tasks)

            for coro in asyncio.as_completed(tasks):
                page_num, text = await coro
                all_layouts.append((page_num + 1, text))
                completed += 1
                progress = 0.3 + (completed / total_tasks) * 0.7
                await report_progress(ctx, progress, f"分析中... ({completed}/{total_tasks})")

            # 关闭异步客户端
            await ocr.close_async_client()

        else:
            # 同步模式处理
            await report_progress(ctx, 0.3, "正在分析版面...")

            for i, page_num in enumerate(pages):
                page = doc[page_num]
                img = pdf_page_to_image(page)

                # 使用专门的版面分析
                text = await asyncio.to_thread(ocr.ocr_layout, img)

                all_layouts.append((page_num + 1, text))

                progress = 0.3 + ((i + 1) / len(pages)) * 0.7
                await report_progress(ctx, progress, f"分析中... ({i + 1}/{len(pages)})")

        doc.close()

        # 合并结果 (JSON 格式)
        combined_result = {
            f"page_{page_num}": text
            for page_num, text in sorted(all_layouts)
        }

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data={
                "layouts": combined_result,
                "page_count": len(pages),
            },
            message=f"成功分析 {len(pages)} 页的版面结构"
        )

    except Exception as e:
        return format_error(e)
