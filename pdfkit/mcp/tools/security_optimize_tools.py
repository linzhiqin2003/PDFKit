"""MCP 安全和优化工具

包含所有安全和优化相关的 MCP 工具：
- 加密、解密、权限设置、清除元数据
- 压缩、优化图片、修复
"""

from typing import Any, Optional, List, Union
from pathlib import Path

from ..server import mcp
from ...core import (
    encrypt_pdf,
    decrypt_pdf,
    protect_pdf,
    clean_metadata,
    compress_pdf,
    optimize_images,
    repair_pdf,
    EncryptResult,
    DecryptResult,
    ProtectResult,
    CleanMetadataResult,
    CompressResult,
    OptimizeImagesResult,
    RepairResult,
    PDFSecurityError,
    PasswordError,
    PDFOptimizeError,
    OptimizeInvalidParameterError,
    RepairFailedError,
)
from ..utils import (
    format_error,
    format_success,
    validate_pdf_file,
    report_progress,
    log_info,
)


# ==================== 加密 PDF ====================

@mcp.tool(
    name="pdfkit_encrypt_pdf",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_encrypt_pdf(
    file_path: str,
    output_path: str,
    password: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    加密 PDF 文件

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        password: 设置密码

    Returns:
        加密结果
    """
    await log_info(ctx, f"加密 PDF: {file_path}")
    await report_progress(ctx, 0.1, "正在加密...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行加密
        result: EncryptResult = encrypt_pdf(
            file_path,
            output_path,
            password,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功加密 PDF"
        )

    except PDFSecurityError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 解密 PDF ====================

@mcp.tool(
    name="pdfkit_decrypt_pdf",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_decrypt_pdf(
    file_path: str,
    output_path: str,
    password: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    解密 PDF 文件

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        password: PDF 密码

    Returns:
        解密结果
    """
    await log_info(ctx, f"解密 PDF: {file_path}")
    await report_progress(ctx, 0.1, "正在解密...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行解密
        result: DecryptResult = decrypt_pdf(
            file_path,
            output_path,
            password,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功解密 PDF"
        )

    except PasswordError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "password_error",
            "suggestion": "请检查密码是否正确",
        }
    except PDFSecurityError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 设置权限 ====================

@mcp.tool(
    name="pdfkit_protect_pdf",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_protect_pdf(
    file_path: str,
    output_path: str,
    owner_password: str,
    user_password: str = "",
    no_print: bool = False,
    no_copy: bool = False,
    no_modify: bool = False,
    ctx: Optional[Any] = None,
) -> dict:
    """
    设置 PDF 权限

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        owner_password: 所有者密码
        user_password: 用户密码（可选）
        no_print: 禁止打印
        no_copy: 禁止复制
        no_modify: 禁止修改

    Returns:
        设置结果
    """
    await log_info(ctx, f"设置 PDF 权限: {file_path}")
    await report_progress(ctx, 0.1, "正在设置...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行权限设置
        result: ProtectResult = protect_pdf(
            file_path,
            output_path,
            owner_password,
            user_password,
            no_print,
            no_copy,
            no_modify,
        )

        await report_progress(ctx, 1.0, "完成")

        restrictions_str = ", ".join(result.restrictions) if result.restrictions else "无限制"

        return format_success(
            data=result.to_dict(),
            message=f"成功设置 PDF 权限，限制: {restrictions_str}"
        )

    except PDFSecurityError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 清除元数据 ====================

@mcp.tool(
    name="pdfkit_clean_metadata",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_clean_metadata(
    file_path: str,
    output_path: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    清除 PDF 元数据

    删除可能包含敏感信息的元数据，如：
    - 作者
    - 创建程序
    - 创建/修改日期
    - 标题、主题、关键词

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径

    Returns:
        清除结果
    """
    await log_info(ctx, f"清除元数据: {file_path}")
    await report_progress(ctx, 0.1, "正在清除...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行清除元数据
        result: CleanMetadataResult = clean_metadata(
            file_path,
            output_path,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功清除 PDF 元数据"
        )

    except PDFSecurityError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "encrypted_pdf",
            "suggestion": "请先解密 PDF 文件",
        }
    except Exception as e:
        return format_error(e)


# ==================== 压缩 PDF ====================

@mcp.tool(
    name="pdfkit_compress_pdf",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_compress_pdf(
    file_path: str,
    output_path: str,
    quality: str = "medium",
    ctx: Optional[Any] = None,
) -> dict:
    """
    压缩 PDF 文件大小

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        quality: 压缩质量 (low/medium/high)

    Returns:
        压缩结果
    """
    await log_info(ctx, f"压缩 PDF: {file_path}")
    await report_progress(ctx, 0.1, "正在压缩...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行压缩
        result: CompressResult = compress_pdf(
            file_path,
            output_path,
            quality,
        )

        await report_progress(ctx, 1.0, "完成")

        # 格式化文件大小
        def format_size(size_bytes: int) -> str:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"

        original_size = format_size(result.original_size)
        compressed_size = format_size(result.compressed_size)

        return format_success(
            data=result.to_dict(),
            message=f"成功压缩 PDF: {original_size} → {compressed_size} (减少 {result.reduction_percent:.1f}%)"
        )

    except OptimizeInvalidParameterError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "invalid_parameter",
        }
    except PDFOptimizeError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 优化图片 ====================

@mcp.tool(
    name="pdfkit_optimize_images",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_optimize_images(
    file_path: str,
    output_path: str,
    dpi: int = 150,
    quality: int = 85,
    ctx: Optional[Any] = None,
) -> dict:
    """
    优化 PDF 中的图片

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        dpi: 目标 DPI（降低 DPI 可减小文件大小）
        quality: JPEG 质量 (1-100)

    Returns:
        优化结果
    """
    await log_info(ctx, f"优化图片: {file_path}")
    await report_progress(ctx, 0.1, "正在优化...")

    try:
        validate_pdf_file(file_path)

        await report_progress(ctx, 0.5, "正在处理...")

        # 执行优化
        result: OptimizeImagesResult = optimize_images(
            file_path,
            output_path,
            dpi,
            quality,
        )

        await report_progress(ctx, 1.0, "完成")

        # 格式化文件大小
        def format_size(size_bytes: int) -> str:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} TB"

        original_size = format_size(result.original_size)
        optimized_size = format_size(result.optimized_size)

        return format_success(
            data=result.to_dict(),
            message=f"成功优化 {result.images_processed} 张图片: {original_size} → {optimized_size} (减少 {result.reduction_percent:.1f}%)"
        )

    except OptimizeInvalidParameterError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "invalid_parameter",
        }
    except PDFOptimizeError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)


# ==================== 修复 PDF ====================

@mcp.tool(
    name="pdfkit_repair_pdf",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def pdfkit_repair_pdf(
    file_path: str,
    output_path: str,
    ctx: Optional[Any] = None,
) -> dict:
    """
    修复损坏的 PDF 文件

    尝试修复以下问题:
    - 损坏的 PDF 结构
    - 损坏的对象
    - 损坏的交叉引用表

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径

    Returns:
        修复结果
    """
    await log_info(ctx, f"修复 PDF: {file_path}")
    await report_progress(ctx, 0.1, "正在修复...")

    try:
        await report_progress(ctx, 0.5, "正在处理...")

        # 执行修复
        result: RepairResult = repair_pdf(
            file_path,
            output_path,
        )

        await report_progress(ctx, 1.0, "完成")

        return format_success(
            data=result.to_dict(),
            message=f"成功修复 PDF"
        )

    except RepairFailedError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "repair_failed",
            "suggestion": "PDF 文件可能已严重损坏，无法修复",
        }
    except PDFOptimizeError as e:
        return format_error(e)
    except Exception as e:
        return format_error(e)
