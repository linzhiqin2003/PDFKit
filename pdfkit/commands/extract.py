"""PDF 内容提取命令"""

from pathlib import Path
from typing import Optional, List
import typer
from io import BytesIO
import fitz  # PyMuPDF
from PIL import Image

from ..utils.console import (
    console, print_success, print_error, print_info, print_warning, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import resolve_path, ensure_dir, format_size

# 创建 extract 子应用
app = typer.Typer(help="提取 PDF 内容")


@app.command("pages")
def extract_pages(
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
    range_str: Optional[str] = typer.Option(
        None,
        "--range",
        "-r",
        help="页面范围，如 '1-5,8,10-15'",
    ),
):
    """
    提取指定页面到新 PDF

    [bold cyan]页面范围格式:[/]
      - 单页:           [yellow]3[/]
      - 连续范围:       [yellow]1-5[/]
      - 多个范围:       [yellow]1-3,5,8-10[/]
      - 不指定则提取全部

    [bold cyan]输出文件:[/]
      - 不指定 -o 时自动生成: [dim]原文件名_pages_起始-结束页.pdf[/]

    [bold cyan]示例:[/]
      # 提取第1-5页到一个新PDF
      pdfkit extract pages document.pdf -r 1-5 -o chapter1.pdf

      # 提取不连续的页面（第1,3,5页）
      pdfkit extract pages document.pdf -r 1,3,5

      # 提取全部页面（相当于复制）
      pdfkit extract pages document.pdf -o copy.pdf

      # 不指定输出文件名，自动生成
      pdfkit extract pages document.pdf -r 1-3
      # 输出: document_pages_1-3.pdf
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if not require_unlocked_pdf(file, "提取页面"):
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 确定要提取的页面
        if range_str:
            page_list = validate_page_range(range_str, total_pages)
        else:
            print_info("未指定页面范围，将提取所有页面")
            page_list = list(range(total_pages))

        if not page_list:
            print_error("没有有效的页面范围")
            raise typer.Exit(1)

        # 创建新文档
        new_doc = fitz.open()

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.EXTRACT} 提取页面中...",
                total=len(page_list)
            )

            for page_num in page_list:
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                progress.update(task, advance=1)

        doc.close()

        # 确定输出路径
        if output is None:
            stem = file.stem
            suffix = f"_pages_{page_list[0] + 1}-{page_list[-1] + 1}"
            output = resolve_path(file.parent / f"{stem}{suffix}.pdf")
        else:
            output = resolve_path(output)

        # 保存
        new_doc.save(output)
        new_doc.close()

        print_success(f"页面提取完成: [path]{output}[/]")
        print_info(f"提取页数: [number]{len(page_list)}[/] 页 (第 {page_list[0] + 1}-{page_list[-1] + 1} 页)")

    except Exception as e:
        print_error(f"提取失败: {e}")
        raise typer.Exit(1)


@app.command("text")
def extract_text(
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
    range_str: Optional[str] = typer.Option(
        None,
        "--range",
        "-r",
        help="页面范围",
    ),
    format: str = typer.Option(
        "txt",
        "--format",
        "-f",
        help="输出格式: txt, md (markdown)",
    ),
):
    """
    提取 PDF 文本内容

    示例:
        # 提取所有文本
        pdfkit extract text document.pdf

        # 提取为 Markdown
        pdfkit extract text document.pdf -f md -o output.md

        # 提取指定页面
        pdfkit extract text document.pdf -r 1-5
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 确定要提取的页面
        if range_str:
            page_list = validate_page_range(range_str, total_pages)
        else:
            page_list = list(range(total_pages))

        all_text = []

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.EXTRACT} 提取文本中...",
                total=len(page_list)
            )

            for page_num in page_list:
                page = doc[page_num]
                text = page.get_text()

                if format == "md":
                    # 简单的 Markdown 转换
                    text = _convert_to_markdown(page, text)

                all_text.append(f"--- 第 {page_num + 1} 页 ---\n{text}")
                progress.update(task, advance=1)

        doc.close()

        # 合并文本
        combined_text = "\n\n".join(all_text)

        # 确定输出路径
        if output is None:
            ext = ".md" if format == "md" else ".txt"
            output = resolve_path(file.parent / f"{file.stem}_text{ext}")
        else:
            output = resolve_path(output)

        # 保存
        output.write_text(combined_text, encoding="utf-8")

        print_success(f"文本提取完成: [path]{output}[/]")
        print_info(f"提取页数: [number]{len(page_list)}[/] 页")
        print_info(f"文本大小: [size]{format_size(len(combined_text))}[/]")

    except Exception as e:
        print_error(f"提取失败: {e}")
        raise typer.Exit(1)


@app.command("images")
def extract_images(
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
    range_str: Optional[str] = typer.Option(
        None,
        "--range",
        "-r",
        help="页面范围",
    ),
    format: str = typer.Option(
        "png",
        "--format",
        "-f",
        help="输出格式: png, jpg",
    ),
):
    """
    提取 PDF 中的图片

    示例:
        # 提取所有图片
        pdfkit extract images document.pdf

        # 提取为 JPG 格式
        pdfkit extract images document.pdf -f jpg

        # 提取指定页面的图片
        pdfkit extract images document.pdf -r 1-5
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 确定要提取的页面
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

        # 提取图片
        image_count = 0

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.IMAGE} 提取图片中...",
                total=len(page_list)
            )

            for page_num in page_list:
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
                        output_path = output_dir / f"page_{page_num + 1}_img_{img_index + 1}.{format}"
                        pil_image.save(output_path, format.upper() if format == "jpg" else format)
                    else:
                        output_path = output_dir / f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                        output_path.write_bytes(image_data)

                    image_count += 1

                progress.update(task, advance=1)

        doc.close()

        if image_count == 0:
            print_warning("未找到任何图片")
        else:
            print_success(f"图片提取完成!")
            print_info(f"提取数量: [number]{image_count}[/] 张")
            print_info(f"输出目录: [path]{output_dir}[/]")

    except Exception as e:
        print_error(f"提取失败: {e}")
        raise typer.Exit(1)


def _convert_to_markdown(page: fitz.Page, text: str) -> str:
    """简单的 PDF 文本转 Markdown"""
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
