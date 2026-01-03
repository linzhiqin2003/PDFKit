"""MCP 工具参数验证模块

提供参数范围定义、验证函数和装饰器。
"""

from typing import Any, Optional, Tuple, List, Union, Callable
from dataclasses import dataclass
from enum import Enum
import re


# ==================== 参数范围定义 ====================

@dataclass
class ParamRange:
    """参数范围定义

    Attributes:
        min: 最小值 (数字类型)
        max: 最大值 (数字类型)
        allowed_values: 允许的值列表
        pattern: 正则表达式模式
        description: 参数描述
    """
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    description: str = ""


# 预定义参数范围

PARAM_RANGES = {
    # ========== 水印参数 ==========
    "angle": ParamRange(
        allowed_values=[0, 90, 180, 270],
        description="水印旋转角度（仅支持特定角度以避免渲染问题）"
    ),
    "opacity": ParamRange(
        min=0.0,
        max=1.0,
        description="水印透明度（0.0 完全透明，1.0 完全不透明）"
    ),
    "font_size": ParamRange(
        min=6,
        max=72,
        description="字体大小（点）"
    ),

    # ========== 转换参数 ==========
    "dpi": ParamRange(
        min=72,
        max=300,  # 根据测试报告建议，降低上限以避免连接中断
        description="输出分辨率（DPI）"
    ),
    "quality": ParamRange(
        min=1,
        max=100,
        description="JPEG 质量（1-100）"
    ),
    "format": ParamRange(
        allowed_values=["png", "jpg", "jpeg", "webp"],
        description="图片输出格式"
    ),
    "image_format": ParamRange(
        allowed_values=["png", "jpg", "jpeg", "webp"],
        description="图片提取格式"
    ),

    # ========== 页面参数 ==========
    "page_ranges": ParamRange(
        pattern=r"^(\d+(-\d+)?)(,(\d+(-\d+)?))*$",
        description="页面范围，格式: '1-3,5,7-9'"
    ),

    # ========== 对齐参数 ==========
    "align": ParamRange(
        allowed_values=["left", "center", "right"],
        description="对齐方式"
    ),
    "position": ParamRange(
        allowed_values=["center", "top-left", "top-right", "bottom-left", "bottom-right"],
        description="水印位置"
    ),

    # ========== 层级参数 ==========
    "layer": ParamRange(
        allowed_values=["overlay", "underlay"],
        description="图层位置"
    ),

    # ========== 输出格式 ==========
    "output_format": ParamRange(
        allowed_values=["txt", "md"],
        description="文本提取输出格式"
    ),
    "extract_format": ParamRange(
        allowed_values=["txt", "md"],
        description="提取格式"
    ),

    # ========== 压缩质量 ==========
    "compress_quality": ParamRange(
        allowed_values=["low", "medium", "high"],
        description="压缩质量级别"
    ),

    # ========== OCR 参数 ==========
    "model": ParamRange(
        allowed_values=["flash", "plus", "ocr"],
        description="OCR 模型选择"
    ),
    "ocr_output_format": ParamRange(
        allowed_values=["text", "md", "json"],
        description="OCR 输出格式"
    ),
    "concurrency": ParamRange(
        min=1,
        max=50,
        description="异步模式最大并发数"
    ),

    # ========== 页面大小 ==========
    "page_size": ParamRange(
        allowed_values=["A4", "Letter", "A3", "A5", "Legal", "Tabloid"],
        description="页面尺寸"
    ),
    "scale": ParamRange(
        min=0.1,
        max=3.0,
        description="页面缩放比例"
    ),
}


# ==================== 验证错误 ====================

class ValidationError(Exception):
    """参数验证错误

    用于在参数不符合预期时抛出清晰的错误信息。
    """

    def __init__(self, message: str, param_name: str = None, param_value: Any = None):
        self.message = message
        self.param_name = param_name
        self.param_value = param_value
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {"message": self.message}
        if self.param_name:
            result["param_name"] = self.param_name
        if self.param_value is not None:
            result["param_value"] = str(self.param_value)
        return result


# ==================== 验证函数 ====================

def validate_param(
    name: str,
    value: Any,
    custom_range: ParamRange = None,
    allow_none: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    验证单个参数

    Args:
        name: 参数名
        value: 参数值
        custom_range: 自定义范围 (可选，覆盖预定义范围)
        allow_none: 是否允许 None 值

    Returns:
        (是否有效, 错误消息)

    Raises:
        ValidationError: 参数无效时

    Examples:
        >>> validate_param("angle", 45)  # 会抛出 ValidationError
        >>> validate_param("angle", 90)  # 通过
        >>> validate_param("dpi", 150)  # 通过
        >>> validate_param("dpi", 1000)  # 会抛出 ValidationError
    """
    # 允许 None 值
    if value is None:
        if allow_none:
            return True, None
        raise ValidationError(
            f"参数 '{name}' 不能为空",
            param_name=name,
            param_value=value
        )

    # 获取范围定义
    range_def = custom_range or PARAM_RANGES.get(name)

    if not range_def:
        # 未定义范围的参数，跳过验证
        return True, None

    # 检查允许值列表
    if range_def.allowed_values is not None:
        if value not in range_def.allowed_values:
            allowed = ", ".join(str(v) for v in range_def.allowed_values)
            raise ValidationError(
                f"参数 '{name}' 的值 '{value}' 无效。允许的值: {allowed}",
                param_name=name,
                param_value=value
            )

    # 检查数值范围
    if range_def.min is not None or range_def.max is not None:
        try:
            num_value = float(value)
        except (TypeError, ValueError):
            raise ValidationError(
                f"参数 '{name}' 必须是数字类型，收到: {type(value).__name__}",
                param_name=name,
                param_value=value
            )

        if range_def.min is not None and num_value < range_def.min:
            raise ValidationError(
                f"参数 '{name}' 的值 {value} 小于最小值 {range_def.min}",
                param_name=name,
                param_value=value
            )

        if range_def.max is not None and num_value > range_def.max:
            raise ValidationError(
                f"参数 '{name}' 的值 {value} 大于最大值 {range_def.max}",
                param_name=name,
                param_value=value
            )

    # 检查正则表达式
    if range_def.pattern:
        if not re.match(range_def.pattern, str(value)):
            raise ValidationError(
                f"参数 '{name}' 的格式无效: '{value}'。期望格式: {range_def.pattern}",
                param_name=name,
                param_value=value
            )

    return True, None


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

    Examples:
        >>> validate_params(
        ...     {"angle": 90, "opacity": 0.5},
        ...     {"angle": PARAM_RANGES["angle"], "opacity": PARAM_RANGES["opacity"]}
        ... )
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
    valid_angles = [0, 90, 180, 270]
    if angle not in valid_angles:
        raise ValidationError(
            f"角度参数只支持 {valid_angles} 度，收到: {angle}",
            param_name="angle",
            param_value=angle
        )


def validate_opacity(opacity: float) -> None:
    """验证透明度参数"""
    if not 0.0 <= opacity <= 1.0:
        raise ValidationError(
            f"透明度必须在 0.0 到 1.0 之间，收到: {opacity}",
            param_name="opacity",
            param_value=opacity
        )


def validate_dpi(dpi: int) -> None:
    """验证 DPI 参数"""
    if not 72 <= dpi <= 600:
        raise ValidationError(
            f"DPI 必须在 72 到 600 之间，收到: {dpi}",
            param_name="dpi",
            param_value=dpi
        )


def validate_page_range_format(range_str: str) -> None:
    """验证页面范围格式"""
    pattern = r"^(\d+(-\d+)?)(,(\d+(-\d+))?)*$"
    if not re.match(pattern, range_str):
        raise ValidationError(
            f"页面范围格式无效: '{range_str}'。正确格式: '1-3', '5', '1-3,5,7-9'",
            param_name="page_ranges",
            param_value=range_str
        )


# ==================== 验证装饰器 ====================

def validate_tool(*param_names, **param_definitions):
    """
    参数验证装饰器

    Args:
        *param_names: 需要验证的参数名列表
        **param_definitions: 参数名到 ParamRange 的映射

    Examples:
        @validate_tool("angle", "opacity")
        def add_watermark(..., angle=0, opacity=0.3):
            ...

        @validate_tool(dpi=PARAM_RANGES["dpi"])
        def pdf_to_images(..., dpi=150):
            ...
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
            # 兼容 format 和 image_format 两种命名
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
