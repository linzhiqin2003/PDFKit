"""MCP 工具函数

包含 MCP 专用的错误处理、验证函数和辅助工具。
"""

from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Callable
from functools import wraps
import asyncio


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

def format_error(error: Exception) -> Dict[str, Any]:
    """
    格式化错误信息，提供可操作的建议

    Args:
        error: 异常对象

    Returns:
        包含错误信息的字典
    """
    if isinstance(error, MCPError):
        return {
            "success": False,
            "error": True,
            "message": error.message,
            "suggestion": error.suggestion or "请检查输入参数和文件状态",
            "error_type": error.__class__.__name__,
        }
    elif isinstance(error, FileNotFoundError):
        return {
            "success": False,
            "error": True,
            "message": str(error),
            "suggestion": "请检查文件路径是否正确",
            "error_type": "file_not_found",
        }
    elif isinstance(error, PermissionError):
        return {
            "success": False,
            "error": True,
            "message": f"权限不足: {error}",
            "suggestion": "请检查文件权限",
            "error_type": "permission_denied",
        }
    else:
        return {
            "success": False,
            "error": True,
            "message": str(error),
            "suggestion": "请检查输入参数和文件状态",
            "error_type": "unknown",
        }


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
]
