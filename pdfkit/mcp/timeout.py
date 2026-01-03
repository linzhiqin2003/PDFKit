"""MCP 工具超时和重试机制

提供超时控制和重试装饰器，增强长时间运行操作的稳定性。
"""

import asyncio
import functools
import signal
import time
from typing import Callable, TypeVar, Any, Optional, List, Type
from dataclasses import dataclass


# ==================== 自定义异常 ====================

class TimeoutError(Exception):
    """操作超时错误"""

    def __init__(self, message: str, timeout_seconds: int = None):
        self.timeout_seconds = timeout_seconds
        super().__init__(message)


class MaxRetriesExceededError(Exception):
    """超过最大重试次数错误"""

    def __init__(self, message: str, max_retries: int = None, last_error: Exception = None):
        self.max_retries = max_retries
        self.last_error = last_error
        super().__init__(message)


# ==================== 超时装饰器 ====================

T = TypeVar('T')


def with_timeout(seconds: int = 300, error_message: str = None):
    """
    超时装饰器，为同步和异步函数添加超时控制

    Args:
        seconds: 超时秒数 (默认 5 分钟)
        error_message: 自定义错误消息 (可选)

    Examples:
        @with_timeout(seconds=120)
        def long_running_operation():
            ...

        @with_timeout(seconds=60)
        async def async_operation():
            ...

    Note:
        - 在 Windows 上，异步超时使用 asyncio.wait_for
        - 在 Unix 上，同步超时使用 signal.SIGALRM
        - 在 Windows 上，同步超时使用 threading 方式（简化处理）
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 处理异步函数
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=seconds
                    )
                except asyncio.TimeoutError:
                    msg = error_message or (
                        f"操作超时 ({seconds}秒)。"
                        f"文件可能过大，请尝试处理更小的范围或增加超时时间。"
                    )
                    raise TimeoutError(msg, timeout_seconds=seconds)

            return async_wrapper

        # 处理同步函数
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 使用线程池方式实现超时（跨平台兼容）
                import concurrent.futures
                import threading

                result = None
                exception = None
                completed = threading.Event()

                def run_function():
                    nonlocal result, exception
                    try:
                        result = func(*args, **kwargs)
                    except Exception as e:
                        exception = e
                    finally:
                        completed.set()

                thread = threading.Thread(target=run_function, daemon=True)
                thread.start()

                # 等待完成或超时
                if not completed.wait(timeout=seconds):
                    msg = error_message or (
                        f"操作超时 ({seconds}秒)。"
                        f"文件可能过大，请尝试处理更小的范围或增加超时时间。"
                    )
                    raise TimeoutError(msg, timeout_seconds=seconds)

                thread.join(timeout=1)  # 等待线程结束

                if exception:
                    raise exception

                return result

            return sync_wrapper

    return decorator


# ==================== 重试装饰器 ====================

@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential: bool = True
    jitter: bool = True
    retry_on: Optional[List[Type[Exception]]] = None


def with_retry(config: RetryConfig = None, **kwargs):
    """
    重试装饰器，为函数添加自动重试能力

    Args:
        config: 重试配置对象
        **kwargs: 直接传递 RetryConfig 参数（优先级高于 config）

    Examples:
        @with_retry(max_retries=3, base_delay=2.0)
        def unstable_operation():
            ...

        @with_retry(retry_on=[ConnectionError, TimeoutError])
        def network_operation():
            ...

    配置说明:
        max_retries: 最大重试次数（默认 3）
        base_delay: 基础延迟秒数（默认 1.0）
        max_delay: 最大延迟秒数（默认 60.0）
        exponential: 是否使用指数退避（默认 True）
        jitter: 是否添加随机抖动（默认 True）
        retry_on: 需要重试的异常类型列表（默认 None，全部重试）
    """
    if config is None:
        config = RetryConfig(**{k: v for k, v in kwargs.items() if v is not None})
    elif kwargs:
        # 合并配置
        for key, value in kwargs.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 处理异步函数
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_error = None

                for attempt in range(config.max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_error = e

                        # 检查是否应该重试此异常
                        if config.retry_on and not any(
                            isinstance(e, retry_type) for retry_type in config.retry_on
                        ):
                            raise

                        # 最后一次尝试失败
                        if attempt == config.max_retries:
                            break

                        # 计算延迟
                        if config.exponential:
                            delay = min(config.base_delay * (2 ** attempt), config.max_delay)
                        else:
                            delay = config.base_delay

                        # 添加抖动
                        if config.jitter:
                            import random
                            delay = delay * (0.5 + random.random() * 0.5)

                        await asyncio.sleep(delay)

                # 所有重试都失败
                raise MaxRetriesExceededError(
                    f"操作失败，已重试 {config.max_retries} 次。最后错误: {last_error}",
                    max_retries=config.max_retries,
                    last_error=last_error
                )

            return async_wrapper

        # 处理同步函数
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_error = None

                for attempt in range(config.max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e

                        # 检查是否应该重试此异常
                        if config.retry_on and not any(
                            isinstance(e, retry_type) for retry_type in config.retry_on
                        ):
                            raise

                        # 最后一次尝试失败
                        if attempt == config.max_retries:
                            break

                        # 计算延迟
                        if config.exponential:
                            delay = min(config.base_delay * (2 ** attempt), config.max_delay)
                        else:
                            delay = config.base_delay

                        # 添加抖动
                        if config.jitter:
                            import random
                            delay = delay * (0.5 + random.random() * 0.5)

                        time.sleep(delay)

                # 所有重试都失败
                raise MaxRetriesExceededError(
                    f"操作失败，已重试 {config.max_retries} 次。最后错误: {last_error}",
                    max_retries=config.max_retries,
                    last_error=last_error
                )

            return sync_wrapper

    return decorator


# ==================== 组合装饰器 ====================

def with_timeout_and_retry(
    timeout_seconds: int = 300,
    max_retries: int = 3,
    base_delay: float = 1.0,
    retry_on: Optional[List[Type[Exception]]] = None
):
    """
    组合超时和重试装饰器

    Args:
        timeout_seconds: 单次尝试的超时秒数
        max_retries: 最大重试次数
        base_delay: 重试基础延迟
        retry_on: 需要重试的异常类型

    Examples:
        @with_timeout_and_retry(timeout_seconds=120, max_retries=2)
        def reliable_operation():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 先应用重试，再应用超时
        return with_timeout(seconds=timeout_seconds)(
            with_retry(
                max_retries=max_retries,
                base_delay=base_delay,
                retry_on=retry_on
            )(func)
        )

    return decorator


# ==================== 超时上下文管理器 ====================

class timeout_context:
    """超时上下文管理器

    用于代码块级别的超时控制。

    Examples:
        with timeout_context(seconds=30):
            long_running_code()
    """

    def __init__(self, seconds: int):
        self.seconds = seconds
        self._timer = None

    def __enter__(self):
        import threading
        self._start_time = time.time()
        self._timed_out = False

        def timeout_handler():
            self._timed_out = True
            raise TimeoutError(
                f"操作超时 ({self.seconds}秒)",
                timeout_seconds=self.seconds
            )

        self._timer = threading.Timer(self.seconds, timeout_handler)
        self._timer.daemon = True
        self._timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._timer:
            self._timer.cancel()
        return False


# ==================== 进度回调支持 ====================

def with_timeout_and_progress(
    seconds: int = 300,
    progress_callback: Optional[Callable[[float, str], Any]] = None
):
    """
    带进度报告的超时装饰器

    Args:
        seconds: 超时秒数
        progress_callback: 进度回调函数 (progress, message) -> None

    Examples:
        def report_progress(progress, message):
            print(f"[{progress*100:.1f}%] {message}")

        @with_timeout_and_progress(seconds=120, progress_callback=report_progress)
        def long_operation():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()

                async def wrapped():
                    if progress_callback:
                        progress_callback(0.0, f"开始执行 {func.__name__}")
                    result = await func(*args, **kwargs)
                    if progress_callback:
                        progress_callback(1.0, f"完成 {func.__name__}")
                    return result

                try:
                    return await asyncio.wait_for(
                        wrapped(),
                        timeout=seconds
                    )
                except asyncio.TimeoutError:
                    if progress_callback:
                        elapsed = time.time() - start_time
                        progress_callback(
                            min(elapsed / seconds, 1.0),
                            f"超时: {func.__name__}"
                        )
                    raise TimeoutError(
                        f"操作超时 ({seconds}秒)",
                        timeout_seconds=seconds
                    )

            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()

                if progress_callback:
                    progress_callback(0.0, f"开始执行 {func.__name__}")

                try:
                    result = func(*args, **kwargs)
                    if progress_callback:
                        progress_callback(1.0, f"完成 {func.__name__}")
                    return result
                except Exception as e:
                    if progress_callback:
                        elapsed = time.time() - start_time
                        progress_callback(
                            min(elapsed / seconds, 1.0),
                            f"失败: {func.__name__}"
                        )
                    raise

            return sync_wrapper

    return decorator


# ==================== 预定义配置 ====================

# 快速操作（小文件）
QUICK_TIMEOUT = 30
QUICK_RETRY = RetryConfig(max_retries=1, base_delay=0.5)

# 标准操作（中等文件）
DEFAULT_TIMEOUT = 120
DEFAULT_RETRY = RetryConfig(max_retries=2, base_delay=1.0)

# 慢速操作（大文件或复杂转换）
LONG_TIMEOUT = 300
LONG_RETRY = RetryConfig(max_retries=3, base_delay=2.0, max_delay=30.0)

# 网络操作（URL 转 PDF 等）
NETWORK_TIMEOUT = 180
NETWORK_RETRY = RetryConfig(
    max_retries=3,
    base_delay=2.0,
    retry_on=[ConnectionError, TimeoutError, OSError]
)

# OCR 操作
OCR_TIMEOUT = 300
OCR_RETRY = RetryConfig(max_retries=2, base_delay=3.0)


# ==================== 导出 ====================

__all__ = [
    # 异常
    "TimeoutError",
    "MaxRetriesExceededError",
    # 配置
    "RetryConfig",
    # 装饰器
    "with_timeout",
    "with_retry",
    "with_timeout_and_retry",
    "with_timeout_and_progress",
    # 上下文管理器
    "timeout_context",
    # 预定义配置
    "QUICK_TIMEOUT",
    "QUICK_RETRY",
    "DEFAULT_TIMEOUT",
    "DEFAULT_RETRY",
    "LONG_TIMEOUT",
    "LONG_RETRY",
    "NETWORK_TIMEOUT",
    "NETWORK_RETRY",
    "OCR_TIMEOUT",
    "OCR_RETRY",
]
