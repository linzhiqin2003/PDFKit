"""PDF 页眉命令"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF

from ..utils.console import (
    console, print_success, print_error, print_info, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import resolve_path

# 创建 header 子应用
app = typer.Typer(help="添加页眉")


@app.command()
def add(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    text: str = typer.Option(
        ...,
        "--text",
        "-t",
        help="页眉文字",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    font_size: int = typer.Option(
        12,
        "--font-size",
        "-f",
        help="字体大小",
    ),
    align: str = typer.Option(
        "center",
        "--align",
        "-a",
        help="对齐方式: left, center, right",
    ),
    margin_top: float = typer.Option(
        18,
        "--margin-top",
        help="顶部边距（点）",
    ),
    range_str: Optional[str] = typer.Option(
        None,
        "--range",
        "-r",
        help="页面范围",
    ),
):
    """
    添加页眉到 PDF

    示例:
        # 添加居中页眉
        pdfkit header add document.pdf -t "公司名称"

        # 添加左对齐页眉
        pdfkit header add document.pdf -t "机密文件" -a left

        # 只添加到第1-5页
        pdfkit header add document.pdf -t "草稿" -r 1-5
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if align not in ("left", "center", "right"):
        print_error("对齐方式必须是 left, center 或 right")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 确定要添加页眉的页面
        if range_str:
            page_list = validate_page_range(range_str, total_pages)
        else:
            page_list = list(range(total_pages))

        # 获取页面尺寸
        if page_list:
            page_width = doc[page_list[0]].rect.width

        with create_progress() as progress:
            task = progress.add_task(
                f"添加页眉中...",
                total=len(page_list)
            )

            for page_num in page_list:
                page = doc[page_num]
                rect = page.rect

                # y 坐标：从页面顶部 + 边距
                y = rect.y0 + margin_top

                # textbox 高度需要足够大
                tb_height = font_size * 2

                # 计算 textbox 区域
                if align == "left":
                    tb_rect = fitz.Rect(rect.x0 + 36, y, rect.x1 - 36, y + tb_height)
                elif align == "center":
                    margin = 36
                    tb_rect = fitz.Rect(rect.x0 + margin, y, rect.x1 - margin, y + tb_height)
                else:  # right
                    tb_rect = fitz.Rect(rect.x0 + 36, y, rect.x1 - 36, y + tb_height)

                # 设置对齐方式
                align_flag = fitz.TEXT_ALIGN_LEFT
                if align == "center":
                    align_flag = fitz.TEXT_ALIGN_CENTER
                elif align == "right":
                    align_flag = fitz.TEXT_ALIGN_RIGHT

                # 插入文本
                # 使用 helv (Helvetica) 字体，它是 PDF 内置字体
                rc = page.insert_textbox(
                    tb_rect,
                    text,
                    fontsize=font_size,
                    fontname="helv",  # 使用内置字体
                    color=(0, 0, 0),
                    align=align_flag,
                )

                # rc < 0 表示文本不适合 textbox
                if rc < 0:
                    # 如果文本太长，尝试更大的区域
                    tb_rect = fitz.Rect(rect.x0 + 18, y, rect.x1 - 18, y + tb_height * 2)
                    page.insert_textbox(
                        tb_rect,
                        text,
                        fontsize=font_size,
                        fontname="helv",
                        color=(0, 0, 0),
                        align=align_flag,
                    )

                progress.update(task, advance=1)

        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}_header{file.suffix}")
        else:
            output = resolve_path(output)

        # 保存 (使用 deflate 压缩)
        doc.save(output, deflate=True)
        doc.close()

        print_success(f"页眉添加完成: [path]{output}[/]")
        print_info(f"页数: [number]{len(page_list)}[/] 页")
        print_info(f"页眉内容: [text]{text}[/]")

    except Exception as e:
        print_error(f"添加页眉失败: {e}")
        raise typer.Exit(1)
