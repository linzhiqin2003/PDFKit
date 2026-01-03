"""MCP 工具参数验证模块

此模块从 pdfkit.utils.validators 重新导出验证工具，
保持向后兼容性。

注意：核心验证功能已迁移到 pdfkit.utils.validators，
以避免核心层和 MCP 层之间的循环导入。
"""

# 从 utils.validators 重新导出所有内容
from ..utils.validators import (
    # 参数范围
    ParamRange,
    PARAM_RANGES,
    # 验证错误
    ValidationError,
    # 验证函数
    validate_param,
)

# 额外的 MCP 专用验证函数（如果需要）
def validate_params(
    params: dict,
    definitions: dict = None,
    allow_extra: bool = True
) -> None:
    """
    批量验证参数

    Args:
        params: 参数字典
        definitions: 参数定义字典 {参数名: ParamRange 或 None}
        allow_extra: 是否允许未定义的额外参数

    Raises:
        ValidationError: 任意参数无效时
    """
    errors = []

    for name, value in params.items():
        if value is None:
            continue

        # 获取参数定义
        if definitions:
            range_def = definitions.get(name, PARAM_RANGES.get(name))
        else:
            range_def = PARAM_RANGES.get(name)

        if not range_def and not allow_extra:
            errors.append(f"  - {name}: 未定义的参数")
            continue

        try:
            validate_param(name, value, range_def)
        except ValidationError as e:
            errors.append(f"  - {name}: {e.message}")

    if errors:
        error_msg = "参数验证失败:\n" + "\n".join(errors)
        raise ValidationError(error_msg)


def validate_angle(angle: int) -> None:
    """验证角度参数"""
    validate_param("angle", angle)


def validate_opacity(opacity: float) -> None:
    """验证透明度参数"""
    validate_param("opacity", opacity)


def validate_dpi(dpi: int) -> None:
    """验证 DPI 参数"""
    validate_param("dpi", dpi)


def validate_page_range_format(range_str: str) -> None:
    """验证页面范围格式"""
    validate_param("page_ranges", range_str)


# ==================== 验证装饰器 ====================

from typing import Callable, Any


def validate_tool(*param_names, **param_definitions):
    """
    参数验证装饰器

    Args:
        *param_names: 需要验证的参数名列表
        **param_definitions: 参数名到 ParamRange 的映射
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # 验证命名参数
            for name in param_names:
                if name in kwargs:
                    validate_param(name, kwargs[name])

            for name, range_def in param_definitions.items():
                if name in kwargs:
                    validate_param(name, kwargs[name], range_def)

            return func(*args, **kwargs)

        return wrapper
    return decorator


def validate_watermark_params(func: Callable) -> Callable:
    """水印参数验证装饰器"""
    def wrapper(*args, **kwargs):
        for param in ["angle", "opacity", "font_size", "position", "layer"]:
            if param in kwargs and kwargs[param] is not None:
                validate_param(param, kwargs[param])
        return func(*args, **kwargs)
    return wrapper


def validate_convert_params(func: Callable) -> Callable:
    """转换参数验证装饰器"""
    def wrapper(*args, **kwargs):
        if "format" in kwargs and kwargs["format"] is not None:
            validate_param("format", kwargs["format"])
        if "dpi" in kwargs and kwargs["dpi"] is not None:
            validate_param("dpi", kwargs["dpi"])
        return func(*args, **kwargs)
    return wrapper


# ==================== 导出 ====================

__all__ = [
    # 参数范围
    "ParamRange",
    "PARAM_RANGES",
    # 验证错误
    "ValidationError",
    # 验证函数
    "validate_param",
    "validate_params",
    "validate_angle",
    "validate_opacity",
    "validate_dpi",
    "validate_page_range_format",
    # 装饰器
    "validate_tool",
    "validate_watermark_params",
    "validate_convert_params",
]
