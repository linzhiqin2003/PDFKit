"""MCP 工具函数

包含 MCP 专用的错误处理、验证函数和辅助工具。
"""

from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Callable
from functools import wraps
import asyncio

# 导入错误码系统
from pdfkit.mcp.errors import (
    ErrorCode,
    ErrorDetail,
    file_not_found,
    invalid_pdf,
    encrypted_pdf,
    get_error_type,
)


# ==================== 自定义异常 ====================

class MCPError(Exception):
    """MCP 工具错误基类"""

    def __init__(self, message: str, suggestion: str = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


class FileNotFoundError(MCPError):
    """文件不存在"""

    def __init__(self, path: str):
        super().__init__(
            message=f"文件不存在: {path}",
            suggestion="请检查文件路径是否正确"
        )


class InvalidPDFError(MCPError):
    """无效的 PDF 文件"""

    def __init__(self, path: str):
        super().__init__(
            message=f"不是有效的 PDF 文件: {path}",
            suggestion="请确保文件是 PDF 格式且未损坏"
        )


class EncryptedPDFError(MCPError):
    """PDF 已加密"""

    def __init__(self, path: str):
        super().__init__(
            message=f"PDF 文件已加密: {path}",
            suggestion="请使用 pdfkit_decrypt 解密后再操作"
        )


class ProcessingError(MCPError):
    """处理错误"""

    def __init__(self, message: str, suggestion: str = None):
        super().__init__(message=message, suggestion=suggestion)


# ==================== 错误格式化 ====================

def format_error(
    error: Exception,
    error_code: ErrorCode = None,
    **context
) -> Dict[str, Any]:
    """
    格式化错误信息，提供可操作的建议

    Args:
        error: 异常对象
        error_code: 可选的错误码，用于提供更精确的错误分类
        **context: 额外的上下文信息

    Returns:
        包含错误信息的字典，格式:
        {
            "success": False,
            "error": True,
            "error_code": "ERR_XXX_XXX",
            "error_type": "ErrorTypeName",
            "message": "错误描述",
            "suggestion": "修复建议",
            "context": {...}  # 可选
        }
    """
    # 如果是自定义 MCP 错误
    if isinstance(error, MCPError):
        result = {
            "success": False,
            "error": True,
            "message": error.message,
            "error_type": error.__class__.__name__,
        }
        if error.suggestion:
            result["suggestion"] = error.suggestion

        # 如果提供了错误码，添加到响应中
        if error_code:
            result["error_code"] = error_code.value
        else:
            # 根据错误类型推断错误码
            error_name = error.__class__.__name__
            if "FileNotFound" in error_name:
                result["error_code"] = ErrorCode.FILE_NOT_FOUND.value
            elif "InvalidPDF" in error_name:
                result["error_code"] = ErrorCode.FILE_INVALID_PDF.value
            elif "EncryptedPDF" in error_name:
                result["error_code"] = ErrorCode.FILE_ENCRYPTED.value

        if context:
            result["context"] = context

        return result

    # Python 标准异常处理
    error_type = type(error)

    # 文件相关错误
    if error_type is FileNotFoundError:
        result = {
            "success": False,
            "error": True,
            "error_code": error_code.value if error_code else ErrorCode.FILE_NOT_FOUND.value,
            "error_type": "FileNotFoundError",
            "message": f"文件不存在: {error}",
            "suggestion": "请检查文件路径是否正确",
        }
        if context:
            result["context"] = context
        return result

    if error_type is PermissionError:
        result = {
            "success": False,
            "error": True,
            "error_code": error_code.value if error_code else ErrorCode.FILE_PERMISSION_DENIED.value,
            "error_type": "PermissionDeniedError",
            "message": f"权限不足: {error}",
            "suggestion": "请检查文件权限或目录写入权限",
        }
        if context:
            result["context"] = context
        return result

    # 值错误 (通常是参数验证失败)
    if error_type is ValueError:
        result = {
            "success": False,
            "error": True,
            "error_code": error_code.value if error_code else ErrorCode.PARAM_INVALID_VALUE.value,
            "error_type": "ValueError",
            "message": str(error),
            "suggestion": "请检查参数值是否有效",
        }
        if context:
            result["context"] = context
        return result

    # 类型错误
    if error_type is TypeError:
        result = {
            "success": False,
            "error": True,
            "error_code": error_code.value if error_code else ErrorCode.PARAM_INVALID_FORMAT.value,
            "error_type": "TypeError",
            "message": str(error),
            "suggestion": "请检查参数类型是否正确",
        }
        if context:
            result["context"] = context
        return result

    # 未知错误
    result = {
        "success": False,
        "error": True,
        "error_code": error_code.value if error_code else "ERR_UNKNOWN",
        "error_type": error_type.__name__,
        "message": str(error),
        "suggestion": "请检查输入参数和文件状态",
    }
    if context:
        result["context"] = context

    return result


def format_success(data: Dict[str, Any], message: str = "操作成功") -> Dict[str, Any]:
    """
    格式化成功响应

    Args:
        data: 返回数据
        message: 成功消息

    Returns:
        包含成功信息的字典
    """
    return {
        "success": True,
        "error": False,
        "message": message,
        "data": data,
    }


# ==================== 文件验证 ====================

def validate_pdf_file(file_path: str) -> Path:
    """
    验证 PDF 文件

    Args:
        file_path: 文件路径

    Returns:
        Path 对象

    Raises:
        FileNotFoundError: 文件不存在
        InvalidPDFError: 不是 PDF 文件
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(file_path)

    if not path.is_file():
        raise InvalidPDFError(file_path)

    if path.suffix.lower() != '.pdf':
        raise InvalidPDFError(file_path)

    return path


def validate_output_path(output_path: str) -> Path:
    """
    验证输出路径，确保父目录存在

    Args:
        output_path: 输出路径

    Returns:
        Path 对象
    """
    path = Path(output_path)
    parent = path.parent

    # 创建父目录
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)

    return path


# ==================== 异步处理 ====================

T = TypeVar('T')


async def run_in_executor(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    在线程池中执行同步函数

    Args:
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        函数返回值
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


def sync_to_async(func: Callable[..., T]) -> Callable[..., T]:
    """
    将同步函数包装为异步函数

    Args:
        func: 同步函数

    Returns:
        异步函数
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        return await run_in_executor(func, *args, **kwargs)

    return wrapper


# ==================== 进度报告 ====================

async def report_progress(
    ctx: Optional[Any],
    progress: float,
    message: str,
) -> None:
    """
    报告进度（如果上下文可用）

    Args:
        ctx: MCP 上下文对象
        progress: 进度值 (0.0 - 1.0)
        message: 进度消息
    """
    if ctx and hasattr(ctx, 'report_progress'):
        try:
            await ctx.report_progress(progress, message)
        except Exception:
            pass  # 忽略进度报告错误


async def log_info(
    ctx: Optional[Any],
    message: str,
) -> None:
    """
    记录信息（如果上下文可用）

    Args:
        ctx: MCP 上下文对象
        message: 日志消息
    """
    if ctx and hasattr(ctx, 'log_info'):
        try:
            await ctx.log_info(message)
        except Exception:
            pass


async def log_warning(
    ctx: Optional[Any],
    message: str,
) -> None:
    """
    记录警告（如果上下文可用）

    Args:
        ctx: MCP 上下文对象
        message: 警告消息
    """
    if ctx and hasattr(ctx, 'log_warning'):
        try:
            await ctx.log_warning(message)
        except Exception:
            pass


async def log_error(
    ctx: Optional[Any],
    message: str,
) -> None:
    """
    记录错误（如果上下文可用）

    Args:
        ctx: MCP 上下文对象
        message: 错误消息
    """
    if ctx and hasattr(ctx, 'log_error'):
        try:
            await ctx.log_error(message)
        except Exception:
            pass


# ==================== 文件大小格式化 ====================

def format_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


# ==================== 导出 ====================

__all__ = [
    # 异常
    "MCPError",
    "FileNotFoundError",
    "InvalidPDFError",
    "EncryptedPDFError",
    "ProcessingError",
    # 格式化
    "format_error",
    "format_success",
    # 验证
    "validate_pdf_file",
    "validate_output_path",
    # 异步
    "run_in_executor",
    "sync_to_async",
    # 进度/日志
    "report_progress",
    "log_info",
    "log_warning",
    "log_error",
    # 工具
    "format_size",
    # 错误码 (重新导出)
    "ErrorCode",
]
