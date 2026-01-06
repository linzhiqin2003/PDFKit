"""文件处理工具"""

import os
import re
from pathlib import Path
from typing import Any, List, Optional, Union
from datetime import datetime


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_date(timestamp: Optional[float]) -> str:
    """
    格式化时间戳

    Args:
        timestamp: Unix 时间戳

    Returns:
        格式化后的日期字符串
    """
    if timestamp is None:
        return "-"
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "-"


def generate_output_path(
    input_file: Path,
    suffix: str = "",
    prefix: str = "",
    output_dir: Optional[Path] = None,
    new_extension: Optional[str] = None
) -> Path:
    """
    生成输出文件路径

    Args:
        input_file: 输入文件路径
        suffix: 文件名后缀
        prefix: 文件名前缀
        output_dir: 输出目录（默认与输入文件同目录）
        new_extension: 新扩展名（默认与输入文件相同）

    Returns:
        输出文件路径
    """
    # 确定输出目录
    if output_dir is None:
        output_dir = input_file.parent

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    stem = input_file.stem
    if prefix:
        name = f"{prefix}{stem}{suffix}"
    else:
        name = f"{stem}{suffix}"

    # 确定扩展名
    if new_extension:
        if not new_extension.startswith("."):
            new_extension = f".{new_extension}"
        extension = new_extension
    else:
        extension = input_file.suffix

    return output_dir / f"{name}{extension}"


def get_file_hash(file: Path, algorithm: str = "md5") -> str:
    """
    计算文件哈希值

    Args:
        file: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256)

    Returns:
        文件哈希值
    """
    import hashlib

    hash_obj = hashlib.new(algorithm)
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        目录路径
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(illegal_chars, '_', filename)

    # 移除前后空格
    cleaned = cleaned.strip()

    # 限制文件名长度
    max_length = 255
    if len(cleaned) > max_length:
        name, ext = os.path.splitext(cleaned)
        cleaned = name[:max_length - len(ext)] + ext

    return cleaned


def find_files_by_pattern(
    directory: Path,
    pattern: str = "*.pdf",
    recursive: bool = False
) -> List[Path]:
    """
    按模式查找文件

    Args:
        directory: 搜索目录
        pattern: 文件模式
        recursive: 是否递归搜索

    Returns:
        文件路径列表
    """
    if recursive:
        files = list(directory.rglob(pattern))
    else:
        files = list(directory.glob(pattern))
    return [f for f in files if f.is_file()]


def get_unique_filename(path: Path) -> Path:
    """
    获取唯一的文件名（如果文件已存在，自动添加数字后缀）

    Args:
        path: 原始文件路径

    Returns:
        唯一的文件路径
    """
    if not path.exists():
        return path

    counter = 1
    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def split_path(path: Path) -> tuple:
    """
    分解路径为多个部分

    Args:
        path: 文件路径

    Returns:
        (目录, 文件名, 文件名主干, 扩展名)
    """
    return (
        path.parent,
        path.name,
        path.stem,
        path.suffix
    )


def resolve_path(path: Union[str, Path]) -> Path:
    """
    解析路径为绝对路径

    Args:
        path: 路径

    Returns:
        绝对路径
    """
    return Path(path).expanduser().resolve()


def get_relative_path(path: Path, base: Path) -> Path:
    """
    获取相对路径

    Args:
        path: 目标路径
        base: 基准路径

    Returns:
        相对路径
    """
    try:
        return path.relative_to(base)
    except ValueError:
        # 如果不在同一个目录树下，返回绝对路径
        return path


def get_file_info(file: Path) -> dict:
    """
    获取文件详细信息

    Args:
        file: 文件路径

    Returns:
        文件信息字典
    """
    stat = file.stat()

    return {
        "name": file.name,
        "path": str(file.absolute()),
        "size": stat.st_size,
        "size_formatted": format_size(stat.st_size),
        "created": stat.st_ctime,
        "created_formatted": format_date(stat.st_ctime),
        "modified": stat.st_mtime,
        "modified_formatted": format_date(stat.st_mtime),
        "is_file": file.is_file(),
        "is_dir": file.is_dir(),
        "extension": file.suffix,
    }


def generate_ocr_output_paths(
    input_file: Path,
    output_spec: Optional[Path] = None,
    output_format: Optional[Any] = None,
) -> tuple[Path, Path]:
    """
    为 OCR 功能生成输出路径（文件夹组织结构）

    Args:
        input_file: 输入 PDF 文件路径
        output_spec: 用户指定的输出路径（通过 -o 参数）
            - None: 使用默认行为（与 PDF 同名的文件夹）
            - Path with suffix: 视为文件夹路径（忽略 suffix）
            - Path without suffix: 视为文件夹路径
        output_format: 输出格式（决定文件扩展名）

    Returns:
        (output_file_path, images_dir_path)

    Examples:
        >>> # 默认: input = doc.pdf
        >>> from pdfkit.core.ocr_handler import OutputFormat
        >>> generate_ocr_output_paths(Path("doc.pdf"), None, OutputFormat.MARKDOWN)
        (PosixPath('doc/doc.md'), PosixPath('doc/images'))

        >>> # 指定文件夹: input = doc.pdf, output = myfolder
        >>> generate_ocr_output_paths(Path("doc.pdf"), Path("myfolder"), OutputFormat.TEXT)
        (PosixPath('myfolder/doc.txt'), PosixPath('myfolder/images'))

        >>> # 嵌套路径: input = path/to/doc.pdf
        >>> generate_ocr_output_paths(Path("path/to/doc.pdf"), None, OutputFormat.MARKDOWN)
        (PosixPath('path/to/doc/doc.md'), PosixPath('path/to/doc/images'))
    """
    # 循环导入避免：在这里导入 OutputFormat
    from pdfkit.core.ocr_handler import OutputFormat

    # 如果没有提供格式，使用 TEXT 作为默认值
    if output_format is None:
        output_format = OutputFormat.TEXT

    # 确定文件扩展名
    ext_map = {
        OutputFormat.TEXT: ".txt",
        OutputFormat.MARKDOWN: ".md",
        OutputFormat.JSON: ".json",
    }
    ext = ext_map.get(output_format, ".txt")

    # PDF 文件名（不含扩展名，保持特殊字符）
    pdf_stem = input_file.stem  # "2406.05946v1(3)"

    # 确定输出目录
    if output_spec is None:
        # 默认：在 PDF 同目录下创建同名文件夹
        output_dir = input_file.parent / pdf_stem
    else:
        # -o 参数指定：使用该路径作为文件夹
        output_dir = output_spec

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成输出文件路径
    output_file = output_dir / f"{pdf_stem}{ext}"

    # 生成图像目录路径
    images_dir = output_dir / "images"

    return output_file, images_dir
