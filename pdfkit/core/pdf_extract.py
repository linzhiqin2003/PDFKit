"""PDF 提取服务 - 核心业务逻辑

此模块包含与 PDF 内容提取相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, List, Union, Tuple
from dataclasses import dataclass, field
from io import BytesIO

import fitz  # PyMuPDF
from PIL import Image


# ==================== 数据模型 ====================

@dataclass
class ExtractPagesResult:
    """页面提取结果"""
    output_path: str
    pages_extracted: List[int]
    page_count: int
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "pages_extracted": self.pages_extracted,
            "page_count": self.page_count,
            "success": self.success,
        }


@dataclass
class ExtractTextResult:
    """文本提取结果"""
    text: str
    page_count: int
    char_count: int
    output_path: Optional[str] = None
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "page_count": self.page_count,
            "char_count": self.char_count,
            "output_path": str(self.output_path) if self.output_path else None,
            "success": self.success,
        }


@dataclass
class ExtractedImageInfo:
    """提取的图片信息"""
    output_path: str
    page_number: int
    image_index: int
    size_bytes: int


@dataclass
class ExtractImagesResult:
    """图片提取结果"""
    images: List[ExtractedImageInfo]
    total_images: int
    output_dir: str
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "images": [
                {
                    "output_path": str(img.output_path),
                    "page_number": img.page_number,
                    "image_index": img.image_index,
                    "size_bytes": img.size_bytes,
                }
                for img in self.images
            ],
            "total_images": self.total_images,
            "output_dir": str(self.output_dir),
            "success": self.success,
        }


# ==================== 自定义异常 ====================

class PDFExtractError(Exception):
    """PDF 提取错误"""
    pass


class InvalidPageRangeError(PDFExtractError):
    """无效的页面范围"""
    pass


class EncryptedPDFError(PDFExtractError):
    """PDF 加密错误"""
    pass


# ==================== 工具函数 ====================

def convert_to_markdown(page: fitz.Page, text: str) -> str:
    """
    简单的 PDF 文本转 Markdown

    Args:
        page: PyMuPDF 页面对象
        text: 页面文本

    Returns:
        Markdown 格式的文本
    """
    # 获取字体信息来推断标题
    blocks = page.get_text("dict")["blocks"]
    md_lines = []

    for block in blocks:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    font_size = span["size"]

                    # 根据字体大小判断是否为标题
                    if font_size > 20:
                        md_lines.append(f"## {text}")
                    elif font_size > 16:
                        md_lines.append(f"### {text}")
                    else:
                        md_lines.append(text)

                md_lines.append("")  # 段落间空行

    return "\n".join(md_lines)


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

    for part in range_str.split(','):
        part = part.strip()
        if not part:
            continue

        if '-' in part:
            # 范围如 "1-5"
            try:
                start, end = part.split('-')
                start_page = int(start.strip()) - 1
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


# ==================== 核心函数 ====================

def extract_pages(
    file_path: Union[str, Path],
    pages: List[int],
    output: Union[str, Path],
) -> ExtractPagesResult:
    """
    提取指定页面到新 PDF

    Args:
        file_path: PDF 文件路径
        pages: 页码列表 (0-indexed)
        output: 输出文件路径

    Returns:
        ExtractPagesResult: 提取结果
    """
    file_path = Path(file_path)
    output_path = Path(output)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        # 创建新文档
        new_doc = fitz.open()

        for page_num in pages:
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        doc.close()

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存
        new_doc.save(output_path)
        new_doc.close()

        return ExtractPagesResult(
            output_path=str(output_path),
            pages_extracted=[p + 1 for p in pages],  # 转为 1-index
            page_count=len(pages),
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFExtractError(f"提取页面失败: {e}")


def extract_text(
    file_path: Union[str, Path],
    pages: Optional[List[int]] = None,
    output: Optional[Union[str, Path]] = None,
    format: str = "txt",
) -> ExtractTextResult:
    """
    提取 PDF 文本内容

    Args:
        file_path: PDF 文件路径
        pages: 页码列表 (0-indexed)，None 表示全部页面
        output: 输出文件路径，None 表示不保存
        format: 输出格式 (txt/md)

    Returns:
        ExtractTextResult: 提取结果
    """
    file_path = Path(file_path)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        total_pages = doc.page_count

        # 确定要提取的页面
        if pages is None:
            pages = list(range(total_pages))

        all_text = []

        for page_num in pages:
            page = doc[page_num]
            text = page.get_text()

            if format == "md":
                text = convert_to_markdown(page, text)

            all_text.append(f"--- 第 {page_num + 1} 页 ---\n{text}")

        doc.close()

        # 合并文本
        combined_text = "\n\n".join(all_text)

        # 保存到文件
        output_path_str = None
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(combined_text, encoding="utf-8")
            output_path_str = str(output_path)

        return ExtractTextResult(
            text=combined_text,
            page_count=len(pages),
            char_count=len(combined_text),
            output_path=output_path_str,
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFExtractError(f"提取文本失败: {e}")


def extract_images(
    file_path: Union[str, Path],
    output_dir: Union[str, Path],
    pages: Optional[List[int]] = None,
    format: str = "png",
) -> ExtractImagesResult:
    """
    提取 PDF 中的图片

    Args:
        file_path: PDF 文件路径
        output_dir: 输出目录
        pages: 页码列表 (0-indexed)，None 表示全部页面
        format: 输出格式 (png/jpg)

    Returns:
        ExtractImagesResult: 提取结果
    """
    file_path = Path(file_path)
    output_dir_path = Path(output_dir)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        total_pages = doc.page_count

        # 确定要提取的页面
        if pages is None:
            pages = list(range(total_pages))

        # 确保输出目录存在
        output_dir_path.mkdir(parents=True, exist_ok=True)

        images = []

        for page_num in pages:
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]

                # 提取图片
                base_image = doc.extract_image(xref)
                image_data = base_image["image"]
                image_ext = base_image["ext"]

                # 转换格式
                if format != "auto" and format != image_ext:
                    pil_image = Image.open(BytesIO(image_data))
                    output_file_name = f"page_{page_num + 1}_img_{img_index + 1}.{format}"
                    output_path = output_dir_path / output_file_name
                    pil_image.save(output_path, format.upper() if format == "jpg" else format)
                    image_size = len(image_data)
                else:
                    output_file_name = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                    output_path = output_dir_path / output_file_name
                    output_path.write_bytes(image_data)
                    image_size = len(image_data)

                images.append(ExtractedImageInfo(
                    output_path=str(output_path),
                    page_number=page_num + 1,
                    image_index=img_index + 1,
                    size_bytes=image_size,
                ))

        doc.close()

        return ExtractImagesResult(
            images=images,
            total_images=len(images),
            output_dir=str(output_dir_path),
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFExtractError(f"提取图片失败: {e}")


def extract_all_text(
    file_path: Union[str, Path],
) -> str:
    """
    快速提取全部文本（简化版）

    Args:
        file_path: PDF 文件路径

    Returns:
        提取的文本内容
    """
    result = extract_text(file_path)
    return result.text
