"""PDF 转换服务 - 核心业务逻辑

此模块包含与 PDF 格式转换相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, List, Union, Tuple
from dataclasses import dataclass, field
from io import BytesIO
from datetime import datetime

import fitz  # PyMuPDF
from PIL import Image


# ==================== 数据模型 ====================

@dataclass
class ConvertToImagesResult:
    """PDF 转图片结果"""
    output_dir: str
    image_count: int
    format: str
    dpi: int
    images: List[str] = field(default_factory=list)
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_dir": str(self.output_dir),
            "image_count": self.image_count,
            "format": self.format,
            "dpi": self.dpi,
            "images": self.images,
            "success": self.success,
        }


@dataclass
class ImagesToPDFResult:
    """图片转 PDF 结果"""
    output_path: str
    image_count: int
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "image_count": self.image_count,
            "success": self.success,
        }


@dataclass
class ConvertToWordResult:
    """PDF 转 Word 结果"""
    output_path: str
    page_count: int
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "page_count": self.page_count,
            "success": self.success,
        }


@dataclass
class ConvertToHTMLResult:
    """PDF 转 HTML 结果"""
    output_path: str
    page_count: int
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "page_count": self.page_count,
            "success": self.success,
        }


@dataclass
class ConvertToMarkdownResult:
    """PDF 转 Markdown 结果"""
    output_path: str
    page_count: int
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "page_count": self.page_count,
            "success": self.success,
        }


@dataclass
class HTMLToPDFResult:
    """HTML 转 PDF 结果"""
    output_path: str
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "success": self.success,
        }


@dataclass
class URLToPDFResult:
    """网页转 PDF 结果"""
    output_path: str
    url: str
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "url": self.url,
            "success": self.success,
        }


# ==================== 自定义异常 ====================

class PDFConvertError(Exception):
    """PDF 转换错误"""
    pass


class UnsupportedFormatError(PDFConvertError):
    """不支持的格式"""
    pass


class DependencyNotFoundError(PDFConvertError):
    """依赖包未找到"""
    pass


class EncryptedPDFError(PDFConvertError):
    """PDF 加密错误"""
    pass


# ==================== 工具函数 ====================

def _parse_color(color_str: str) -> Tuple[float, float, float]:
    """解析颜色字符串为 RGB 元组"""
    color_str = color_str.lstrip("#")
    if len(color_str) != 6:
        return (1, 0, 0)  # 默认红色

    r = int(color_str[0:2], 16) / 255
    g = int(color_str[2:4], 16) / 255
    b = int(color_str[4:6], 16) / 255
    return (r, g, b)


# ==================== 核心函数 ====================

def pdf_to_images(
    file_path: Union[str, Path],
    output_dir: Union[str, Path],
    format: str = "png",
    dpi: int = 150,
    pages: Optional[List[int]] = None,
    single: bool = False,
) -> ConvertToImagesResult:
    """
    将 PDF 转换为图片

    Args:
        file_path: PDF 文件路径
        output_dir: 输出目录
        format: 输出格式 (png/jpg/webp)
        dpi: 输出 DPI
        pages: 页码列表 (0-indexed)，None 表示全部页面
        single: 是否合并为一张图片

    Returns:
        ConvertToImagesResult: 转换结果
    """
    file_path = Path(file_path)
    output_dir_path = Path(output_dir)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        total_pages = doc.page_count

        # 确定要转换的页面
        if pages is None:
            pages = list(range(total_pages))

        # 确保输出目录存在
        output_dir_path.mkdir(parents=True, exist_ok=True)

        zoom = dpi / 72  # PyMuPDF 使用 72 作为基准 DPI
        images = []

        if single:
            # 合并为一张图片
            pil_images = []
            for page_num in pages:
                page = doc[page_num]
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                pil_images.append(img)

            # 垂直拼接
            total_height = sum(img.height for img in pil_images)
            max_width = max(img.width for img in pil_images)

            combined = Image.new("RGB", (max_width, total_height))
            y_offset = 0

            for img in pil_images:
                combined.paste(img, (0, y_offset))
                y_offset += img.height

            output_path = output_dir_path / f"{file_path.stem}_combined.{format}"
            combined.save(output_path, format.upper() if format != "jpg" else "JPEG")
            images.append(str(output_path))

        else:
            # 每页单独保存
            for page_num in pages:
                page = doc[page_num]
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                # 转换为 PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # 保存
                output_path = output_dir_path / f"{file_path.stem}_page_{page_num + 1:03d}.{format}"
                img.save(output_path, format.upper() if format != "jpg" else "JPEG")
                images.append(str(output_path))

        doc.close()

        return ConvertToImagesResult(
            output_dir=str(output_dir_path),
            image_count=len(images),
            format=format,
            dpi=dpi,
            images=images,
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFConvertError(f"PDF 转图片失败: {e}")


def images_to_pdf(
    image_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
    sort: bool = False,
) -> ImagesToPDFResult:
    """
    将图片合并为 PDF

    Args:
        image_paths: 图片文件路径列表
        output_path: 输出 PDF 文件路径
        sort: 是否按文件名排序

    Returns:
        ImagesToPDFResult: 转换结果
    """
    output_path = Path(output_path)

    # 过滤图片文件
    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')
    image_files = [Path(f) for f in image_paths if Path(f).suffix.lower() in valid_extensions]

    if not image_files:
        raise PDFConvertError("未找到有效的图片文件")

    if sort:
        image_files.sort(key=lambda x: x.name)

    try:
        import img2pdf

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用 img2pdf 转换
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert([str(f) for f in image_files]))

        return ImagesToPDFResult(
            output_path=str(output_path),
            image_count=len(image_files),
            success=True,
        )

    except ImportError:
        raise DependencyNotFoundError("需要安装 img2pdf: pip install img2pdf")
    except Exception as e:
        raise PDFConvertError(f"图片转 PDF 失败: {e}")


def pdf_to_word(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
) -> ConvertToWordResult:
    """
    将 PDF 转换为 Word 文档

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径

    Returns:
        ConvertToWordResult: 转换结果
    """
    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        from docx import Document
        from docx.shared import Pt, RGBColor

        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建 Word 文档
        word_doc = Document()

        for page_num in range(doc.page_count):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"]
                            if text.strip():
                                # 添加段落
                                para = word_doc.add_paragraph(text)
                                # 设置字体
                                run = para.runs[0]
                                font_size = span["size"]
                                run.font.size = Pt(font_size)

                                # 设置颜色
                                if "color" in span:
                                    color = span["color"]
                                    run.font.color.rgb = RGBColor(
                                        (color >> 16) & 0xFF,
                                        (color >> 8) & 0xFF,
                                        color & 0xFF
                                    )

        # 保存页数后关闭文档
        page_count = doc.page_count
        doc.close()

        # 保存
        word_doc.save(output_path)

        return ConvertToWordResult(
            output_path=str(output_path),
            page_count=page_count,
            success=True,
        )

    except ImportError:
        raise DependencyNotFoundError("需要安装 python-docx: pip install python-docx")
    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFConvertError(f"PDF 转 Word 失败: {e}")


def pdf_to_html(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
) -> ConvertToHTMLResult:
    """
    将 PDF 转换为 HTML

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径

    Returns:
        ConvertToHTMLResult: 转换结果
    """
    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html_parts = ['<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n']
        html_parts.append(f'<title>{file_path.stem}</title>\n')
        html_parts.append('<style>\n')
        html_parts.append('body { font-family: Arial, sans-serif; margin: 20px; }\n')
        html_parts.append('.page { margin-bottom: 40px; padding: 20px; border: 1px solid #ccc; }\n')
        html_parts.append('.page-number { color: #999; font-size: 12px; }\n')
        html_parts.append('</style>\n</head>\n<body>\n')

        for page_num in range(doc.page_count):
            page = doc[page_num]
            html_parts.append(f'<div class="page">\n')
            html_parts.append(f'<div class="page-number">第 {page_num + 1} 页</div>\n')

            # 获取文本块
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        html_parts.append('<p>')
                        for span in line["spans"]:
                            text = span["text"].replace("<", "&lt;").replace(">", "&gt;")
                            font_size = span["size"]
                            html_parts.append(f'<span style="font-size: {font_size}pt;">{text}</span>')
                        html_parts.append('</p>\n')

            html_parts.append('</div>\n')

        html_parts.append('</body>\n</html>')

        # 保存页数后关闭文档
        page_count = doc.page_count
        doc.close()

        # 保存
        output_path.write_text("".join(html_parts), encoding="utf-8")

        return ConvertToHTMLResult(
            output_path=str(output_path),
            page_count=page_count,
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFConvertError(f"PDF 转 HTML 失败: {e}")


def pdf_to_markdown(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
) -> ConvertToMarkdownResult:
    """
    将 PDF 转换为 Markdown

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径

    Returns:
        ConvertToMarkdownResult: 转换结果
    """
    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        md_lines = []

        for page_num in range(doc.page_count):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"]
                            font_size = span["size"]

                            # 根据字体大小判断标题级别
                            if font_size > 20:
                                md_lines.append(f"## {text}\n")
                            elif font_size > 16:
                                md_lines.append(f"### {text}\n")
                            elif text.strip():
                                md_lines.append(f"{text}\n")

                        md_lines.append("")  # 段落间空行

            md_lines.append(f"\n---\n")  # 页面分隔符

        # 保存页数后关闭文档
        page_count = doc.page_count
        doc.close()

        # 保存
        output_path.write_text("\n".join(md_lines), encoding="utf-8")

        return ConvertToMarkdownResult(
            output_path=str(output_path),
            page_count=page_count,
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFConvertError(f"PDF 转 Markdown 失败: {e}")


def html_to_pdf(
    html_path: Union[str, Path],
    output_path: Union[str, Path],
) -> HTMLToPDFResult:
    """
    将 HTML 文件转换为 PDF

    Args:
        html_path: HTML 文件路径
        output_path: 输出 PDF 文件路径

    Returns:
        HTMLToPDFResult: 转换结果
    """
    html_path = Path(html_path)
    output_path = Path(output_path)

    try:
        # 尝试使用 weasyprint（更可靠，无需外部依赖如 wkhtmltopdf）
        try:
            from weasyprint import HTML
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换
            HTML(filename=str(html_path)).write_pdf(str(output_path))
            
            return HTMLToPDFResult(
                output_path=str(output_path),
                success=True,
            )
        except ImportError:
            pass
        
        # 回退方案：使用 PyMuPDF 内置的 HTML 转 PDF 功能
        # 注意：PyMuPDF 对复杂 HTML 支持有限
        html_content = html_path.read_text(encoding="utf-8")
        
        # 创建 PDF 文档
        doc = fitz.open()
        
        # 使用 fitz 的 story 功能（如果可用）
        # 这是 PyMuPDF 1.21+ 的功能
        try:
            from fitz import Story
            
            # 创建 Story 对象
            story = Story(html=html_content)
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建 PDF
            writer = fitz.DocumentWriter(str(output_path))
            mediabox = fitz.paper_rect("a4")
            where = mediabox + (36, 36, -36, -36)  # 边距
            
            more = True
            while more:
                device = writer.begin_page(mediabox)
                more, _ = story.place(where)
                story.draw(device)
                writer.end_page()
            
            writer.close()
            
            return HTMLToPDFResult(
                output_path=str(output_path),
                success=True,
            )
        except (ImportError, AttributeError):
            # PyMuPDF 版本不支持 Story
            # 使用简单方法：将 HTML 作为文本处理
            page = doc.new_page()
            
            # 简单的 HTML 文本提取
            import re
            # 移除 HTML 标签
            text = re.sub(r'<[^>]+>', '', html_content)
            text = text.strip()
            
            # 插入文本
            rect = page.rect
            text_rect = fitz.Rect(50, 50, rect.width - 50, rect.height - 50)
            page.insert_textbox(text_rect, text, fontsize=11)
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            doc.save(output_path)
            doc.close()
            
            return HTMLToPDFResult(
                output_path=str(output_path),
                success=True,
            )

    except Exception as e:
        raise PDFConvertError(f"HTML 转 PDF 失败: {e}。建议安装 weasyprint: pip install weasyprint")


async def url_to_pdf(
    url: str,
    output_path: Union[str, Path],
    wait_time: float = 3.0,
    full_page: bool = True,
    width: int = 1920,
) -> URLToPDFResult:
    """
    将网页转换为 PDF（异步版本）

    Args:
        url: 网页 URL
        output_path: 输出 PDF 文件路径
        wait_time: 等待页面加载时间（秒）
        full_page: 是否截取完整页面
        width: 视口宽度

    Returns:
        URLToPDFResult: 转换结果
    """
    output_path = Path(output_path)

    try:
        from playwright.async_api import async_playwright

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": 1080})

            await page.goto(url)
            await page.wait_for_timeout(int(wait_time * 1000))

            # PDF 选项
            pdf_options = {
                "path": str(output_path),
                "format": "A4",
                "print_background": True,
            }

            if full_page:
                await page.emulate_media(media="print")
                await page.pdf(**pdf_options)
            else:
                await page.pdf(**pdf_options)

            await browser.close()

        return URLToPDFResult(
            output_path=str(output_path),
            url=url,
            success=True,
        )

    except ImportError:
        raise DependencyNotFoundError("需要安装 playwright: pip install playwright")
    except Exception as e:
        raise PDFConvertError(f"网页转 PDF 失败: {e}")
