"""参数验证工具

包含文件验证、参数范围验证等核心验证功能。
此模块可被 CLI、MCP 和核心层共同使用，不依赖任何上层模块。
"""

from pathlib import Path
from typing import List, Union, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import re
import fitz  # PyMuPDF


def validate_pdf_file(file: Union[str, Path]) -> bool:
    """
    验证单个 PDF 文件

    Args:
        file: 文件路径

    Returns:
        是否为有效的 PDF 文件
    """
    try:
        path = Path(file)
        if not path.exists():
            return False
        if not path.is_file():
            return False
        if path.suffix.lower() != '.pdf':
            return False

        # 尝试打开 PDF 文件验证
        doc = fitz.open(path)
        is_valid = doc.page_count > 0
        doc.close()

        return is_valid
    except Exception:
        return False


def validate_pdf_files(files: List[Union[str, Path]]) -> List[Path]:
    """
    验证多个 PDF 文件，返回有效的文件列表

    Args:
        files: 文件路径列表

    Returns:
        有效的 PDF 文件路径列表
    """
    valid_files = []
    for file in files:
        path = Path(file)
        if validate_pdf_file(path):
            valid_files.append(path)
    return valid_files


def check_pdf_encrypted(file: Union[str, Path]) -> tuple[bool, bool]:
    """
    检查 PDF 是否加密

    Args:
        file: 文件路径

    Returns:
        (is_encrypted, needs_password) 元组
        - is_encrypted: 是否已加密
        - needs_password: 是否需要密码才能操作
    """
    try:
        path = Path(file)
        doc = fitz.open(path)
        is_encrypted = doc.is_encrypted
        needs_pass = doc.needs_pass if is_encrypted else False
        doc.close()
        return (is_encrypted, needs_pass)
    except Exception:
        return (False, False)


def require_unlocked_pdf(file: Union[str, Path], operation: str = "操作") -> bool:
    """
    检查 PDF 是否可以访问（未加密或已解锁）
    如果需要密码，打印友好的错误提示并返回 False

    Args:
        file: 文件路径
        operation: 操作名称，用于错误提示

    Returns:
        True 如果可以访问，False 如果需要密码
    """
    from .console import print_error, print_info

    is_encrypted, needs_pass = check_pdf_encrypted(file)
    if needs_pass:
        print_error(f"PDF 文件已加密，需要密码才能{operation}")
        print_info("提示: 使用 pdfkit security decrypt <文件> -p <密码> 解密后再操作")
        return False
    return True

def validate_page_range(page_str: str, total_pages: int) -> List[int]:
    """
    验证并解析页面范围

    Args:
        page_str: 页面范围字符串，如 "1-5,8,10-15"
        total_pages: PDF 总页数

    Returns:
        页码列表（0-based）

    Raises:
        ValueError: 页面范围无效时
    """
    pages = set()
    parts = page_str.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if "-" in part:
            # 处理范围，如 "1-5"
            try:
                start, end = part.split("-")
                start = int(start.strip())
                end = int(end.strip())

                if start < 1 or end < 1:
                    raise ValueError(f"页码必须大于 0: {part}")
                if start > end:
                    raise ValueError(f"范围起始页不能大于结束页: {part}")
                if end > total_pages:
                    raise ValueError(f"页码超出范围 (最大 {total_pages}): {part}")

                # 转换为 0-based 索引
                pages.update(range(start - 1, min(end, total_pages)))
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"无效的页码格式: {part}")
                raise
        else:
            # 处理单页，如 "8"
            try:
                page = int(part.strip())
                if page < 1:
                    raise ValueError(f"页码必须大于 0: {page}")
                if page > total_pages:
                    raise ValueError(f"页码超出范围 (最大 {total_pages}): {page}")
                pages.add(page - 1)  # 转换为 0-based 索引
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"无效的页码格式: {part}")
                raise

    return sorted(pages)


def validate_output_path(
    output: Optional[Path],
    input_file: Path,
    suffix: str = ""
) -> Path:
    """
    验证或生成输出路径

    Args:
        output: 用户指定的输出路径
        input_file: 输入文件路径
        suffix: 自动生成输出文件名时的后缀

    Returns:
        输出文件路径
    """
    if output is None:
        # 自动生成输出文件名
        if suffix:
            output = input_file.parent / f"{input_file.stem}{suffix}{input_file.suffix}"
        else:
            output = input_file.parent / f"{input_file.stem}_out{input_file.suffix}"

    # 检查父目录是否存在
    output.parent.mkdir(parents=True, exist_ok=True)

    # 检查文件是否已存在
    if output.exists():
        from ..utils.config import get_config_value
        overwrite = get_config_value("defaults.overwrite", False)
        if not overwrite:
            raise FileExistsError(f"输出文件已存在: {output}")

    return output


def validate_dpi(dpi: int) -> bool:
    """
    验证 DPI 值

    Args:
        dpi: DPI 值

    Returns:
        是否有效
    """
    return 72 <= dpi <= 600


def validate_quality(quality: str) -> bool:
    """
    验证质量等级

    Args:
        quality: 质量等级 (low, medium, high)

    Returns:
        是否有效
    """
    return quality in ("low", "medium", "high")


def validate_rotation(angle: int) -> bool:
    """
    验证旋转角度

    Args:
        angle: 旋转角度

    Returns:
        是否有效
    """
    return angle in (0, 90, 180, 270)


def validate_image_format(format: str) -> bool:
    """
    验证图片格式

    Args:
        format: 图片格式 (png, jpg, jpeg, webp)

    Returns:
        是否有效
    """
    return format.lower() in ("png", "jpg", "jpeg", "webp")


# ==================== 参数范围验证 ====================
# 以下内容从 pdfkit.mcp.validators 迁移，避免循环导入

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
        max=300,
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

