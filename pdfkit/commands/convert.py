"""PDF 转换命令"""

from pathlib import Path
from typing import Optional, List
import typer
from io import BytesIO
import fitz  # PyMuPDF
from PIL import Image

from ..utils.console import (
    console, print_success, print_error, print_info, print_warning, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, validate_image_format, validate_page_range
from ..utils.file_utils import resolve_path, ensure_dir, format_size
from ..utils.config import load_config

# 创建 convert 子应用
app = typer.Typer(help="格式转换")


# ============================================================================
# PDF 转图片
# ============================================================================

@app.command("to-image")
def pdf_to_image(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="输出目录",
    ),
    format: str = typer.Option(
        "png",
        "--format",
        "-f",
        help="输出格式: png, jpg, webp",
    ),
    dpi: int = typer.Option(
        150,
        "--dpi",
        "-d",
        help="输出 DPI",
    ),
    range_str: Optional[str] = typer.Option(
        None,
        "--range",
        "-r",
        help="页面范围",
    ),
    single: bool = typer.Option(
        False,
        "--single",
        "-s",
        help="合并所有页面为一张图片",
    ),
):
    """
    将 PDF 转换为图片

    示例:
        # 转换所有页面为 PNG
        pdfkit convert to-image document.pdf

        # 转换为 JPG，高 DPI
        pdfkit convert to-image document.pdf -f jpg -d 300

        # 只转换第1-5页
        pdfkit convert to-image document.pdf -r 1-5

        # 合并为一张图片
        pdfkit convert to-image document.pdf --single
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if not validate_image_format(format):
        print_error(f"不支持的图片格式: {format}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 确定要转换的页面
        if range_str:
            page_list = validate_page_range(range_str, total_pages)
        else:
            page_list = list(range(total_pages))

        # 确定输出目录
        if output_dir is None:
            output_dir = resolve_path(file.parent / f"{file.stem}_images")
        else:
            output_dir = resolve_path(output_dir)
        ensure_dir(output_dir)

        if single:
            # 合并为一张图片
            _convert_to_single_image(doc, page_list, output_dir, file.stem, format, dpi)
        else:
            # 每页单独保存
            _convert_to_images(doc, page_list, output_dir, file.stem, format, dpi)

        doc.close()

    except Exception as e:
        print_error(f"转换失败: {e}")
        raise typer.Exit(1)


def _convert_to_images(doc: fitz.Document, page_list: List[int], output_dir: Path, stem: str, format: str, dpi: int):
    """每页转换为单独图片"""
    zoom = dpi / 72  # PyMuPDF 使用 72 作为基准 DPI

    with create_progress() as progress:
        task = progress.add_task(
            f"{Icons.CONVERT} 转换中...",
            total=len(page_list)
        )

        for page_num in page_list:
            page = doc[page_num]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # 转换为 PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # 保存
            output_path = output_dir / f"{stem}_page_{page_num + 1:03d}.{format}"
            img.save(output_path, format.upper() if format != "jpg" else "JPEG")

            progress.update(task, advance=1)

    print_success(f"转换完成!")
    print_info(f"输出数量: [number]{len(page_list)}[/] 张")
    print_info(f"输出目录: [path]{output_dir}[/]")


def _convert_to_single_image(doc: fitz.Document, page_list: List[int], output_dir: Path, stem: str, format: str, dpi: int):
    """合并所有页面为一张图片"""
    zoom = dpi / 72
    images = []

    # 转换所有页面
    for page_num in page_list:
        page = doc[page_num]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    # 垂直拼接
    total_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)

    combined = Image.new("RGB", (max_width, total_height))
    y_offset = 0

    for img in images:
        combined.paste(img, (0, y_offset))
        y_offset += img.height

    # 保存
    output_path = output_dir / f"{stem}_combined.{format}"
    combined.save(output_path, format.upper() if format != "jpg" else "JPEG")

    print_success(f"转换完成!")
    print_info(f"输出文件: [path]{output_path}[/]")
    print_info(f"图片尺寸: [number]{max_width}[/] x [number]{total_height}[/] 像素")


# ============================================================================
# 图片转 PDF
# ============================================================================

@app.command("from-images")
def images_to_pdf(
    inputs: List[Path] = typer.Argument(
        ...,
        help="图片文件路径",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出 PDF 文件路径",
    ),
    sort: bool = typer.Option(
        False,
        "--sort",
        "-s",
        help="按文件名排序",
    ),
):
    """
    将图片合并为 PDF

    示例:
        # 合并图片
        pdfkit convert from-images *.jpg -o output.pdf

        # 排序后合并
        pdfkit convert from-images *.png -s -o output.pdf
    """
    # 过滤图片文件
    image_files = []
    for f in inputs:
        if f.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'):
            image_files.append(f)

    if not image_files:
        print_error("未找到有效的图片文件")
        raise typer.Exit(1)

    if sort:
        image_files.sort(key=lambda x: x.name)

    print_info(f"准备合并 [number]{len(image_files)}[/] 张图片")

    try:
        import img2pdf

        # 确定输出路径
        if output is None:
            output = resolve_path(image_files[0].parent / f"{image_files[0].stem}_combined.pdf")
        else:
            output = resolve_path(output)

        # 使用 img2pdf 转换
        with open(output, "wb") as f:
            f.write(img2pdf.convert([str(f) for f in image_files]))

        print_success(f"转换完成: [path]{output}[/]")
        print_info(f"图片数量: [number]{len(image_files)}[/] 张")

    except ImportError:
        print_error("需要安装 img2pdf: pip install img2pdf")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"转换失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# PDF 转 Word
# ============================================================================

@app.command("to-word")
def pdf_to_word(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
):
    """
    将 PDF 转换为 Word 文档

    示例:
        pdfkit convert to-word document.pdf
        pdfkit convert to-word document.pdf -o output.docx
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        from docx import Document
        from docx.shared import Pt, RGBColor

        doc = fitz.open(file)

        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}.docx")
        else:
            output = resolve_path(output)

        # 创建 Word 文档
        word_doc = Document()

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.CONVERT} 转换中...",
                total=doc.page_count
            )

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

                progress.update(task, advance=1)

        doc.close()

        # 保存
        word_doc.save(output)

        print_success(f"转换完成: [path]{output}[/]")

    except ImportError:
        print_error("需要安装 python-docx: pip install python-docx")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"转换失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# PDF 转 HTML
# ============================================================================

@app.command("to-html")
def pdf_to_html(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
):
    """
    将 PDF 转换为 HTML

    示例:
        pdfkit convert to-html document.pdf
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)

        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}.html")
        else:
            output = resolve_path(output)

        html_parts = ['<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n']
        html_parts.append(f'<title>{file.stem}</title>\n')
        html_parts.append('<style>\n')
        html_parts.append('body { font-family: Arial, sans-serif; margin: 20px; }\n')
        html_parts.append('.page { margin-bottom: 40px; padding: 20px; border: 1px solid #ccc; }\n')
        html_parts.append('.page-number { color: #999; font-size: 12px; }\n')
        html_parts.append('</style>\n</head>\n<body>\n')

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.CONVERT} 转换中...",
                total=doc.page_count
            )

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
                progress.update(task, advance=1)

        html_parts.append('</body>\n</html>')

        doc.close()

        # 保存
        output.write_text("".join(html_parts), encoding="utf-8")

        print_success(f"转换完成: [path]{output}[/]")

    except Exception as e:
        print_error(f"转换失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# PDF 转 Markdown
# ============================================================================

@app.command("to-markdown")
def pdf_to_markdown(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
):
    """
    将 PDF 转换为 Markdown

    示例:
        pdfkit convert to-markdown document.pdf
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)

        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}.md")
        else:
            output = resolve_path(output)

        md_lines = []

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.CONVERT} 转换中...",
                total=doc.page_count
            )

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
                progress.update(task, advance=1)

        doc.close()

        # 保存
        output.write_text("\n".join(md_lines), encoding="utf-8")

        print_success(f"转换完成: [path]{output}[/]")

    except Exception as e:
        print_error(f"转换失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# HTML 转 PDF
# ============================================================================

@app.command("from-html")
def html_to_pdf(
    file: Path = typer.Argument(
        ...,
        help="HTML 文件路径",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出 PDF 文件路径",
    ),
):
    """
    将 HTML 文件转换为 PDF

    示例:
        pdfkit convert from-html document.html
        pdfkit convert from-html document.html -o output.pdf
    """
    if file.suffix.lower() not in ('.html', '.htm'):
        print_warning("文件可能不是 HTML 文件")

    try:
        import pdfkit as html_to_pdf_lib

        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}.pdf")
        else:
            output = resolve_path(output)

        # 读取 HTML
        html_content = file.read_text(encoding="utf-8")

        # 转换
        config = load_config()
        pdfkit_options = {
            'quiet': '',
            'encoding': 'UTF-8',
        }

        html_to_pdf_lib.from_string(html_content, str(output), options=pdfkit_options)

        print_success(f"转换完成: [path]{output}[/]")

    except ImportError:
        print_error("需要安装 pdfkit: pip install pdfkit")
        print_info("同时需要安装 wkhtmltopdf: brew install wkhtmltopdf")
        print_info("注意: 本项目的 pdfkit-cli 与 pdfkit 包名冲突，需要手动安装外部 pdfkit 包")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"转换失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# 网页转 PDF
# ============================================================================

@app.command("from-url")
def url_to_pdf(
    url: str = typer.Argument(
        ...,
        help="网页 URL",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出 PDF 文件路径",
    ),
    wait_time: float = typer.Option(
        3.0,
        "--wait",
        "-w",
        help="等待页面加载时间（秒）",
    ),
    full_page: bool = typer.Option(
        True,
        "--full-page/--no-full-page",
        help="截取完整页面",
    ),
    width: int = typer.Option(
        1920,
        "--width",
        help="视口宽度",
    ),
):
    """
    将网页转换为 PDF

    示例:
        # 转换网页
        pdfkit convert from-url https://example.com

        # 指定输出文件
        pdfkit convert from-url https://example.com -o output.pdf

        # 增加等待时间
        pdfkit convert from-url https://example.com -w 5
    """
    try:
        from playwright.sync_api import sync_playwright

        # 确定输出路径
        if output is None:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            filename = parsed.netloc.replace(".", "_") + ".pdf"
            output = resolve_path(Path.cwd() / filename)
        else:
            output = resolve_path(output)

        print_info(f"正在加载网页: [url]{url}[/]")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 1080})

            page.goto(url)
            page.wait_for_timeout(int(wait_time * 1000))

            # PDF 选项
            pdf_options = {
                "path": str(output),
                "format": "A4",
                "print_background": True,
            }

            if full_page:
                page.emulate_media(media="print")
                page.pdf(**pdf_options)
            else:
                page.pdf(**pdf_options)

            browser.close()

        print_success(f"转换完成: [path]{output}[/]")

    except ImportError:
        print_error("需要安装 playwright: pip install playwright")
        print_info("然后运行: playwright install chromium")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"转换失败: {e}")
        raise typer.Exit(1)
