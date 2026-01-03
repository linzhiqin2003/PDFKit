"""PDF 合并服务 - 核心业务逻辑

此模块包含与 PDF 合并相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, List, Union, Tuple
from dataclasses import dataclass, field
import tempfile
import os

import fitz  # PyMuPDF
import pikepdf


# ==================== 数据模型 ====================

@dataclass
class MergeResult:
    """合并结果"""
    output_path: str
    total_files: int
    merged_files: int
    total_pages: int
    failed_files: List[Tuple[str, str]] = field(default_factory=list)
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "total_files": self.total_files,
            "merged_files": self.merged_files,
            "total_pages": self.total_pages,
            "failed_files": [(str(f), e) for f, e in self.failed_files],
            "success": self.success,
        }


# ==================== 自定义异常 ====================

class PDFMergeError(Exception):
    """PDF 合并错误"""
    pass


class NoValidFilesError(PDFMergeError):
    """没有有效的 PDF 文件"""
    pass


class MergeFailedError(PDFMergeError):
    """合并失败"""
    pass


# ==================== 核心函数 ====================

def repair_pdf_with_pikepdf(pdf_path: Path) -> Optional[Path]:
    """
    使用 pikepdf 尝试修复损坏的 PDF

    Args:
        pdf_path: PDF 文件路径

    Returns:
        修复后的临时文件路径，失败返回 None
    """
    temp_fd = None
    try:
        # 创建临时文件
        temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        temp_file = Path(temp_path)

        # 使用 pikepdf 打开并重新保存（这会修复一些结构问题）
        with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
            pdf.save(temp_file)

        return temp_file
    except Exception:
        return None
    finally:
        # 关闭文件描述符
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except:
                pass


def merge_files_with_pikepdf(
    pdf_files: List[Path],
    output: Path,
    bookmark: bool = True,
) -> MergeResult:
    """
    使用 pikepdf 合并 PDF 文件
    pikepdf 对非标准 PDF 结构的容错性更好

    Args:
        pdf_files: PDF 文件路径列表
        output: 输出文件路径
        bookmark: 是否添加书签

    Returns:
        MergeResult: 合并结果
    """
    merged_count = 0
    failed_files = []
    total_pages = 0

    try:
        # 创建新的 PDF
        merged_pdf = pikepdf.Pdf.new()

        for pdf_file in pdf_files:
            try:
                # pikepdf 打开 PDF（容错模式）
                with pikepdf.open(pdf_file) as src_pdf:
                    # 获取页面范围
                    start_page = len(merged_pdf.pages)

                    # 逐页添加
                    merged_pdf.pages.extend(src_pdf.pages)

                    # 添加书签（大纲）
                    if bookmark:
                        with merged_pdf.open_outline() as outline:
                            # 添加指向该文件第一页的书签
                            outline.root.append(
                                pikepdf.OutlineItem(
                                    pdf_file.stem,
                                    start_page
                                )
                            )

                    merged_count += 1

            except Exception as e:
                failed_files.append((pdf_file, str(e)))

        # 保存结果
        if merged_count > 0:
            merged_pdf.save(output)
            total_pages = len(merged_pdf.pages)

        return MergeResult(
            output_path=str(output),
            total_files=len(pdf_files),
            merged_files=merged_count,
            total_pages=total_pages,
            failed_files=failed_files,
            success=merged_count > 0,
        )

    except Exception as e:
        raise MergeFailedError(f"合并过程出错: {e}")


def _merge_with_pypdf2(
    pdf_files: List[Path],
    output: Path,
    bookmark: bool = True,
) -> MergeResult:
    """
    使用 PyPDF2 合并 PDF 文件（备用方案）
    PyPDF2 对某些 PDF 格式有更好的兼容性

    Args:
        pdf_files: PDF 文件路径列表
        output: 输出文件路径
        bookmark: 是否添加书签

    Returns:
        MergeResult: 合并结果
    """
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfMerger, PdfReader
            # 使用 PyPDF2 的 PdfMerger
            merger = PdfMerger()
            merged_count = 0
            failed_files = []
            total_pages = 0

            for pdf_file in pdf_files:
                try:
                    if bookmark:
                        merger.append(str(pdf_file), outline_item=pdf_file.stem)
                    else:
                        merger.append(str(pdf_file))
                    
                    # 统计页数
                    with open(pdf_file, 'rb') as f:
                        reader = PdfReader(f)
                        total_pages += len(reader.pages)
                    
                    merged_count += 1
                except Exception as e:
                    failed_files.append((pdf_file, str(e)))

            if merged_count == 0:
                raise MergeFailedError("PyPDF2: 没有任何文件成功合并")

            merger.write(str(output))
            merger.close()

            return MergeResult(
                output_path=str(output),
                total_files=len(pdf_files),
                merged_files=merged_count,
                total_pages=total_pages,
                failed_files=failed_files,
                success=True,
            )
        except ImportError:
            raise MergeFailedError("需要安装 pypdf 或 PyPDF2: pip install pypdf")

    # 使用 pypdf (PyPDF2 的新版本)
    writer = PdfWriter()
    merged_count = 0
    failed_files = []
    total_pages = 0
    outline_items = []

    for pdf_file in pdf_files:
        try:
            reader = PdfReader(str(pdf_file))
            
            # 记录书签位置
            if bookmark:
                outline_items.append((pdf_file.stem, total_pages))
            
            # 添加所有页面
            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1
            
            merged_count += 1
        except Exception as e:
            failed_files.append((pdf_file, str(e)))

    if merged_count == 0:
        raise MergeFailedError("pypdf: 没有任何文件成功合并")

    # 添加书签
    if bookmark:
        for title, page_num in outline_items:
            try:
                writer.add_outline_item(title, page_num)
            except:
                pass  # 书签添加失败不影响合并

    # 保存
    with open(output, 'wb') as f:
        writer.write(f)

    return MergeResult(
        output_path=str(output),
        total_files=len(pdf_files),
        merged_files=merged_count,
        total_pages=total_pages,
        failed_files=failed_files,
        success=True,
    )


def merge_files(
    pdf_files: List[Union[str, Path]],
    output: Union[str, Path],
    bookmark: bool = True,
    auto_repair: bool = True,
    skip_errors: bool = False,
) -> MergeResult:
    """
    合并多个 PDF 文件

    使用三层容错策略（按兼容性排序）:
    1. pypdf - 最宽松，对 malformed page tree 容错性最好
    2. PyMuPDF (fitz) - 快速高效，但对格式要求较严格
    3. pikepdf - 中等容错性

    Args:
        pdf_files: PDF 文件路径列表
        output: 输出文件路径
        bookmark: 是否为每个文件添加书签
        auto_repair: 是否自动修复损坏的 PDF
        skip_errors: 是否跳过错误继续处理

    Returns:
        MergeResult: 合并结果

    Raises:
        NoValidFilesError: 没有有效的 PDF 文件
        MergeFailedError: 合并失败
    """
    # 转换路径
    pdf_paths = [Path(f) for f in pdf_files]
    output_path = Path(output)

    # 验证文件
    valid_files = [f for f in pdf_paths if f.exists() and f.suffix.lower() == '.pdf']

    if not valid_files:
        raise NoValidFilesError("没有找到有效的 PDF 文件")

    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    errors = {}

    # ========== 策略 1: 优先使用 pypdf（最宽松）==========
    try:
        return _merge_with_pypdf2(valid_files, output_path, bookmark)
    except Exception as pypdf_error:
        errors['pypdf'] = str(pypdf_error)

    # ========== 策略 2: 尝试使用 PyMuPDF ==========
    try:
        merged_count = 0
        failed_files = []
        merged_doc = fitz.open()

        for pdf_file in valid_files:
            src_doc = None
            repaired_file = None

            try:
                # 尝试打开源文件
                src_doc = fitz.open(pdf_file)

                # 添加书签（在合并前，指向当前文档的第一页）
                if bookmark and src_doc.page_count > 0:
                    bookmark_page = len(merged_doc) + 1  # 书签页码从1开始
                    merged_doc.set_toc(
                        merged_doc.get_toc() + [[1, pdf_file.stem, bookmark_page]]
                    )

                # 合并页面
                merged_doc.insert_pdf(src_doc)
                src_doc.close()
                src_doc = None
                merged_count += 1

            except Exception as e:
                # 清理未关闭的文档
                if src_doc:
                    try:
                        src_doc.close()
                    except:
                        pass

                # 尝试自动修复
                if auto_repair:
                    repaired_file = repair_pdf_with_pikepdf(pdf_file)

                    if repaired_file:
                        try:
                            # 使用修复后的文件
                            src_doc = fitz.open(repaired_file)

                            if bookmark and src_doc.page_count > 0:
                                bookmark_page = len(merged_doc) + 1
                                merged_doc.set_toc(
                                    merged_doc.get_toc() + [[1, pdf_file.stem, bookmark_page]]
                                )

                            merged_doc.insert_pdf(src_doc)
                            src_doc.close()
                            src_doc = None
                            merged_count += 1

                        except Exception:
                            # 修复失败
                            if src_doc:
                                try:
                                    src_doc.close()
                                except:
                                    pass

                            error_msg = str(e)
                            failed_files.append((pdf_file, error_msg))

                            if not skip_errors:
                                # 清理临时文件后，抛出异常触发备用方案
                                if repaired_file and repaired_file.exists():
                                    try:
                                        repaired_file.unlink()
                                    except:
                                        pass
                                merged_doc.close()
                                raise  # 抛出异常触发备用方案
                        finally:
                            # 清理临时文件
                            if repaired_file and repaired_file.exists():
                                try:
                                    repaired_file.unlink()
                                except:
                                    pass
                    else:
                        # pikepdf 也无法打开，记录错误
                        error_msg = str(e)
                        failed_files.append((pdf_file, error_msg))

                        if not skip_errors:
                            merged_doc.close()
                            raise  # 抛出异常触发备用方案
                else:
                    # 不自动修复，直接记录错误
                    error_msg = str(e)
                    failed_files.append((pdf_file, error_msg))

                    if not skip_errors:
                        merged_doc.close()
                        raise  # 抛出异常触发备用方案

        # 检查是否有成功合并的文件
        if merged_count == 0:
            merged_doc.close()
            raise MergeFailedError("PyMuPDF: 没有任何文件成功合并")

        # 保存
        merged_doc.save(output_path)
        total_pages = merged_doc.page_count
        merged_doc.close()

        return MergeResult(
            output_path=str(output_path),
            total_files=len(valid_files),
            merged_files=merged_count,
            total_pages=total_pages,
            failed_files=failed_files,
            success=True,
        )

    except Exception as pymupdf_error:
        errors['PyMuPDF'] = str(pymupdf_error)

    # ========== 策略 3: 使用 pikepdf 直接合并 ==========
    try:
        return merge_files_with_pikepdf(valid_files, output_path, bookmark)
    except Exception as pikepdf_error:
        errors['pikepdf'] = str(pikepdf_error)

    # 所有方案都失败了
    error_details = "\n".join([f"  - {k}: {v}" for k, v in errors.items()])
    raise MergeFailedError(f"合并失败，已尝试所有方案:\n{error_details}")


def merge_directory(
    directory: Union[str, Path],
    output: Union[str, Path],
    pattern: str = "*.pdf",
    bookmark: bool = True,
    sort: bool = True,
    **kwargs
) -> MergeResult:
    """
    合并目录中的所有 PDF 文件

    Args:
        directory: 目录路径
        output: 输出文件路径
        pattern: 文件匹配模式
        bookmark: 是否添加书签
        sort: 是否按文件名排序
        **kwargs: 传递给 merge_files 的其他参数

    Returns:
        MergeResult: 合并结果
    """
    dir_path = Path(directory)

    if not dir_path.exists() or not dir_path.is_dir():
        raise PDFMergeError(f"目录不存在或不是目录: {directory}")

    # 获取所有 PDF 文件
    pdf_files = list(dir_path.glob(pattern))

    if not pdf_files:
        raise NoValidFilesError(f"目录中没有找到 PDF 文件: {directory}")

    # 排序
    if sort:
        pdf_files.sort(key=lambda x: x.name)

    return merge_files(pdf_files, output, bookmark=bookmark, **kwargs)


def interleave_files(
    file1: Union[str, Path],
    file2: Union[str, Path],
    output: Union[str, Path],
) -> MergeResult:
    """
    交替合并两个 PDF 文件

    Args:
        file1: 第一个 PDF 文件
        file2: 第二个 PDF 文件
        output: 输出文件路径

    Returns:
        MergeResult: 合并结果
    """
    path1 = Path(file1)
    path2 = Path(file2)
    output_path = Path(output)

    # 验证文件
    for f, name in [(path1, "file1"), (path2, "file2")]:
        if not f.exists():
            raise PDFMergeError(f"{name} 不存在: {f}")
        if f.suffix.lower() != '.pdf':
            raise PDFMergeError(f"{name} 不是 PDF 文件: {f}")

    try:
        # 打开源文件
        doc1 = fitz.open(path1)
        doc2 = fitz.open(path2)

        # 创建新文档
        merged_doc = fitz.open()

        # 获取最大页数
        max_pages = max(doc1.page_count, doc2.page_count)

        # 交替添加页面
        for i in range(max_pages):
            if i < doc1.page_count:
                merged_doc.insert_pdf(doc1, from_page=i, to_page=i)
            if i < doc2.page_count:
                merged_doc.insert_pdf(doc2, from_page=i, to_page=i)

        # 保存
        merged_doc.save(output_path)
        total_pages = merged_doc.page_count

        # 关闭文档
        doc1.close()
        doc2.close()
        merged_doc.close()

        return MergeResult(
            output_path=str(output_path),
            total_files=2,
            merged_files=2,
            total_pages=total_pages,
            success=True,
        )

    except Exception as e:
        raise MergeFailedError(f"交替合并失败: {e}")
