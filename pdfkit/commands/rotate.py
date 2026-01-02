"""PDF 页面旋转命令"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF

from ..utils.console import (
    console, print_success, print_error, print_info, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, validate_rotation, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import resolve_path

# 创建 rotate 子应用
app = typer.Typer(help="旋转 PDF 页面")


@app.command()
def pages(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    angle: int = typer.Argument(
        ...,
        help="旋转角度: 0, 90, 180, 270",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径（默认覆盖原文件）",
    ),
    range_str: Optional[str] = typer.Option(
        None,
        "--range",
        "-r",
        help="页面范围（默认所有页面）",
    ),
):
    """
    旋转 PDF 页面

    示例:
        # 将所有页面顺时针旋转90度
        pdfkit rotate document.pdf 90

        # 将第1-5页旋转180度
        pdfkit rotate document.pdf 180 -r 1-5

        # 旋转并保存到新文件
        pdfkit rotate document.pdf 270 -o rotated.pdf
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if not require_unlocked_pdf(file, "旋转页面"):
        raise typer.Exit(1)

    if not validate_rotation(angle):
        print_error(f"无效的旋转角度: {angle}。必须是 0, 90, 180 或 270")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 确定要旋转的页面
        if range_str:
            page_list = validate_page_range(range_str, total_pages)
        else:
            page_list = list(range(total_pages))

        print_info(f"将 [number]{len(page_list)}[/] 页旋转 [number]{angle}[/] 度")

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.ARROW_RIGHT} 旋转中...",
                total=len(page_list)
            )

            for page_num in page_list:
                page = doc[page_num]
                page.set_rotation(angle)
                progress.update(task, advance=1)

        # 确定输出路径
        if output is None:
            output = resolve_path(file)
        else:
            output = resolve_path(output)

        # 保存
        doc.save(output)
        doc.close()

        print_success(f"页面旋转完成: [path]{output}[/]")
        print_info(f"旋转页数: [number]{len(page_list)}[/] 页")
        print_info(f"旋转角度: [number]{angle}[/] 度")

    except Exception as e:
        print_error(f"旋转失败: {e}")
        raise typer.Exit(1)
