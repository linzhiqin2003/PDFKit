"""PDF 页面反转命令"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF

from ..utils.console import (
    console, print_success, print_error, print_info, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, require_unlocked_pdf
from ..utils.file_utils import resolve_path

# 创建 reverse 子应用
app = typer.Typer(help="反转 PDF 页面顺序")


@app.command()
def pages(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径（默认覆盖原文件）",
    ),
):
    """
    反转 PDF 页面顺序

    示例:
        # 反转所有页面
        pdfkit reverse document.pdf

        # 反转并保存到新文件
        pdfkit reverse document.pdf -o reversed.pdf
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        print_info(f"将 [number]{total_pages}[/] 页顺序反转")

        # 创建新文档（反向插入）
        new_doc = fitz.open()

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.ARROW_LEFT} 反转中...",
                total=total_pages
            )

            for page_num in reversed(range(total_pages)):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                progress.update(task, advance=1)

        doc.close()

        # 确定输出路径
        if output is None:
            output = resolve_path(file)
        else:
            output = resolve_path(output)

        # 保存
        new_doc.save(output)
        new_doc.close()

        print_success(f"页面反转完成: [path]{output}[/]")
        print_info(f"页数: [number]{total_pages}[/] 页")

    except Exception as e:
        print_error(f"反转失败: {e}")
        raise typer.Exit(1)
