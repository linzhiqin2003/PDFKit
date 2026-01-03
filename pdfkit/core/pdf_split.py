"""PDF 拆分服务 - 核心业务逻辑

此模块包含与 PDF 拆分相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, List, Union, Tuple
from dataclasses import dataclass, field
import re

import fitz  # PyMuPDF


# ==================== 数据模型 ====================

@dataclass
class SplitResult:
    """拆分结果"""
    output_files: List[str]
    total_output: int
    output_dir: str
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_files": self.output_files,
            "total_output": self.total_output,
            "output_dir": str(self.output_dir),
            "success": self.success,
        }


@dataclass
class ChunkResult:
    """单个拆分结果"""
    output_path: str
    pages: List[int]
    page_count: int


# ==================== 自定义异常 ====================

class PDFSplitError(Exception):
    """PDF 拆分错误"""
    pass


class InvalidPageRangeError(PDFSplitError):
    """无效的页面范围"""
    pass


class EncryptedPDFError(PDFSplitError):
    """PDF 加密错误"""
    pass


# ==================== 工具函数 ====================

def is_consecutive(pages: List[int]) -> bool:
    """检查页码是否连续"""
    if len(pages) <= 1:
        return True
    return all(pages[i] + 1 == pages[i + 1] for i in range(len(pages) - 1))


def group_consecutive(pages: List[int]) -> List[List[int]]:
    """将连续页码分组"""
    if not pages:
        return []

    groups = []
    current_group = [pages[0]]

    for i in range(1, len(pages)):
        if pages[i] == pages[i - 1] + 1:
            current_group.append(pages[i])
        else:
            groups.append(current_group)
            current_group = [pages[i]]

    groups.append(current_group)
    return groups


def parse_page_range(range_str: str, total_pages: int) -> List[int]:
    """
    解析页面范围字符串

    Args:
        range_str: 页面范围字符串，如 "1-5,8,10-15"
        total_pages: 总页数

    Returns:
        页码列表 (0-indexed)

    Raises:
        InvalidPageRangeError: 无效的页面范围
    """
    pages = set()

    # 分割逗号分隔的部分
    for part in range_str.split(','):
        part = part.strip()
        if not part:
            continue

        if '-' in part:
            # 范围如 "1-5"
            try:
                start, end = part.split('-')
                start_page = int(start.strip()) - 1  # 转为0-index
                end_page = int(end.strip()) - 1

                if start_page < 0 or end_page >= total_pages or start_page > end_page:
                    raise InvalidPageRangeError(f"无效的页面范围: {part}")

                pages.update(range(start_page, end_page + 1))
            except ValueError:
                raise InvalidPageRangeError(f"无效的页面范围: {part}")
        else:
            # 单页如 "8"
            try:
                page_num = int(part.strip()) - 1
                if page_num < 0 or page_num >= total_pages:
                    raise InvalidPageRangeError(f"页码超出范围: {part}")
                pages.add(page_num)
            except ValueError:
                raise InvalidPageRangeError(f"无效的页码: {part}")

    if not pages:
        raise InvalidPageRangeError("没有有效的页面范围")

    return sorted(list(pages))


def parse_chunks(chunks_str: str, total_pages: int) -> List[Tuple[int, int]]:
    """
    解析 chunks 字符串，返回多个范围

    Args:
        chunks_str: chunks 字符串，如 "1-5,10-15,20-25"
        total_pages: 总页数

    Returns:
        范围列表 [(start, end), ...] (0-indexed)

    Raises:
        InvalidPageRangeError: 无效的页面范围
    """
    chunk_ranges = []

    for part in chunks_str.split(','):
        part = part.strip()
        if not part:
            continue

        if '-' in part:
            # 范围如 "1-5"
            try:
                start, end = part.split('-')
                start_page = int(start.strip()) - 1  # 转为0-index
                end_page = int(end.strip()) - 1

                if (start_page < 0 or end_page >= total_pages or
                    start_page > end_page):
                    raise InvalidPageRangeError(f"无效的页面范围: {part}")

                chunk_ranges.append((start_page, end_page))
            except ValueError:
                raise InvalidPageRangeError(f"无效的页面范围: {part}")
        else:
            # 单页如 "8"
            try:
                page_num = int(part.strip()) - 1
                if page_num < 0 or page_num >= total_pages:
                    raise InvalidPageRangeError(f"页码超出范围: {part}")
                chunk_ranges.append((page_num, page_num))
            except ValueError:
                raise InvalidPageRangeError(f"无效的页码: {part}")

    if not chunk_ranges:
        raise InvalidPageRangeError("没有有效的页面范围")

    return chunk_ranges


# ==================== 核心函数 ====================

def split_by_pages(
    file_path: Union[str, Path],
    output_dir: Union[str, Path],
    pages: List[int],
    prefix: str = "",
) -> SplitResult:
    """
    按指定页码拆分 PDF

    Args:
        file_path: PDF 文件路径
        output_dir: 输出目录
        pages: 页码列表 (0-indexed)
        prefix: 文件名前缀

    Returns:
        SplitResult: 拆分结果
    """
    file_path = Path(file_path)
    output_dir = Path(output_dir)

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        stem = file_path.stem
        output_files = []

        # 检查是否连续
        if is_consecutive(pages):
            # 连续页码，生成一个文件
            new_doc = fitz.open()

            for page_num in pages:
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            output_name = f"{prefix}{stem}_pages_{pages[0] + 1}-{pages[-1] + 1}.pdf"
            output_path = output_dir / output_name
            new_doc.save(output_path)
            new_doc.close()

            output_files.append(str(output_path))
        else:
            # 非连续页码，按连续范围分组
            ranges = group_consecutive(pages)

            for r in ranges:
                new_doc = fitz.open()

                for page_num in r:
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

                output_name = f"{prefix}{stem}_pages_{r[0] + 1}-{r[-1] + 1}.pdf"
                output_path = output_dir / output_name
                new_doc.save(output_path)
                new_doc.close()

                output_files.append(str(output_path))

        doc.close()

        return SplitResult(
            output_files=output_files,
            total_output=len(output_files),
            output_dir=str(output_dir),
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFSplitError(f"拆分失败: {e}")


def split_by_chunks(
    file_path: Union[str, Path],
    output_dir: Union[str, Path],
    chunks: List[Tuple[int, int]],
    prefix: str = "",
) -> SplitResult:
    """
    按多个范围拆分 PDF，每个范围生成一个独立文件

    Args:
        file_path: PDF 文件路径
        output_dir: 输出目录
        chunks: 范围列表 [(start, end), ...] (0-indexed)
        prefix: 文件名前缀

    Returns:
        SplitResult: 拆分结果
    """
    file_path = Path(file_path)
    output_dir = Path(output_dir)

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        stem = file_path.stem
        output_files = []

        for i, (start_page, end_page) in enumerate(chunks, 1):
            new_doc = fitz.open()

            # 复制范围内的所有页面
            for page_num in range(start_page, end_page + 1):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            # 生成文件名
            if start_page == end_page:
                output_name = f"{prefix}{stem}_chunk_{i:03d}_page_{start_page + 1}.pdf"
            else:
                output_name = f"{prefix}{stem}_chunk_{i:03d}_pages_{start_page + 1}-{end_page + 1}.pdf"

            output_path = output_dir / output_name
            new_doc.save(output_path)
            new_doc.close()

            output_files.append(str(output_path))

        doc.close()

        return SplitResult(
            output_files=output_files,
            total_output=len(output_files),
            output_dir=str(output_dir),
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFSplitError(f"拆分失败: {e}")


def split_single_pages(
    file_path: Union[str, Path],
    output_dir: Union[str, Path],
    prefix: str = "",
) -> SplitResult:
    """
    将 PDF 的每一页拆分为单独的文件

    Args:
        file_path: PDF 文件路径
        output_dir: 输出目录
        prefix: 文件名前缀

    Returns:
        SplitResult: 拆分结果
    """
    file_path = Path(file_path)
    output_dir = Path(output_dir)

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        total_pages = doc.page_count
        stem = file_path.stem
        output_files = []

        for page_num in range(total_pages):
            # 创建新文档
            new_doc = fitz.open()

            # 复制页面
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            # 生成文件名
            output_name = f"{prefix}{stem}_page_{page_num + 1:03d}.pdf"
            output_path = output_dir / output_name

            # 保存
            new_doc.save(output_path)
            new_doc.close()

            output_files.append(str(output_path))

        doc.close()

        return SplitResult(
            output_files=output_files,
            total_output=len(output_files),
            output_dir=str(output_dir),
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFSplitError(f"拆分失败: {e}")


def split_by_count(
    file_path: Union[str, Path],
    output_dir: Union[str, Path],
    pages_per_file: int,
    prefix: str = "",
) -> SplitResult:
    """
    按固定页数拆分 PDF

    Args:
        file_path: PDF 文件路径
        output_dir: 输出目录
        pages_per_file: 每个文件的页数
        prefix: 文件名前缀

    Returns:
        SplitResult: 拆分结果
    """
    file_path = Path(file_path)
    output_dir = Path(output_dir)

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    if pages_per_file < 1:
        raise InvalidPageRangeError("每个文件的页数必须大于 0")

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        total_pages = doc.page_count
        stem = file_path.stem
        output_files = []

        # 计算需要拆分的文件数
        file_count = (total_pages + pages_per_file - 1) // pages_per_file

        for i in range(file_count):
            start_page = i * pages_per_file
            end_page = min(start_page + pages_per_file - 1, total_pages - 1)

            new_doc = fitz.open()

            # 复制页面
            for page_num in range(start_page, end_page + 1):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            # 生成文件名
            output_name = f"{prefix}{stem}_part_{i + 1:03d}_pages_{start_page + 1}-{end_page + 1}.pdf"
            output_path = output_dir / output_name

            # 保存
            new_doc.save(output_path)
            new_doc.close()

            output_files.append(str(output_path))

        doc.close()

        return SplitResult(
            output_files=output_files,
            total_output=len(output_files),
            output_dir=str(output_dir),
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFSplitError(f"拆分失败: {e}")


def split_by_size(
    file_path: Union[str, Path],
    output_dir: Union[str, Path],
    max_size_mb: float,
    prefix: str = "",
) -> SplitResult:
    """
    按文件大小拆分 PDF（尽量保持每个文件不超过指定大小）

    Args:
        file_path: PDF 文件路径
        output_dir: 输出目录
        max_size_mb: 最大文件大小 (MB)
        prefix: 文件名前缀

    Returns:
        SplitResult: 拆分结果

    Note:
        这是一个近似实现，实际大小可能会略有超出
    """
    file_path = Path(file_path)
    output_dir = Path(output_dir)

    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    if max_size_mb < 0.01:
        raise InvalidPageRangeError("文件大小必须至少为 0.01 MB")

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        total_pages = doc.page_count
        stem = file_path.stem

        # 估算每个文件可以包含的页数
        # 先获取平均每页大小
        file_size = file_path.stat().st_size / (1024 * 1024)  # MB
        avg_page_size = file_size / total_pages if total_pages > 0 else 0

        # 计算每份大约多少页
        if avg_page_size > 0:
            pages_per_file = max(1, int(max_size_mb / avg_page_size))
        else:
            pages_per_file = 10

        output_files = []

        # 使用 split_by_count 进行拆分
        result = split_by_count(file_path, output_dir, pages_per_file, prefix)

        doc.close()

        return result

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFSplitError(f"拆分失败: {e}")
