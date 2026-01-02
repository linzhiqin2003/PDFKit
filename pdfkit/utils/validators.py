"""参数验证工具"""

from pathlib import Path
from typing import List, Union, Optional
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
