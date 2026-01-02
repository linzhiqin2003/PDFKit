"""PDF 页面删除命令"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF

from ..utils.console import (
    console, print_success, print_error, print_info, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import resolve_path

# 创建 delete 子应用
app = typer.Typer(help="删除 PDF 页面")


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
    range_str: str = typer.Option(
        ...,
        "--range",
        "-r",
        help="要删除的页面范围，如 '1-5,8,10-15'",
    ),
):
    """
    删除 PDF 中的指定页面

    示例:
        # 删除第3页
        pdfkit delete pages document.pdf -r 3

        # 删除第1-5页和第10页
        pdfkit delete pages document.pdf -r 1-5,10

        # 删除并保存到新文件
        pdfkit delete pages document.pdf -r 1-5 -o new.pdf
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 解析要删除的页面
        pages_to_delete = validate_page_range(range_str, total_pages)

        if not pages_to_delete:
            print_error("没有有效的页面范围")
            raise typer.Exit(1)

        print_info(f"原始页数: [number]{total_pages}[/] 页")
        print_info(f"将删除: [number]{len(pages_to_delete)}[/] 页")
        print_info(f"删除后: [number]{total_pages - len(pages_to_delete)}[/] 页")

        # 创建新文档（排除要删除的页面）
        new_doc = fitz.open()

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.CROSS} 删除页面中...",
                total=total_pages
            )

            for page_num in range(total_pages):
                if page_num not in pages_to_delete:
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

        print_success(f"页面删除完成: [path]{output}[/]")
        print_info(f"原始页数: [number]{total_pages}[/] → 新页数: [number]{total_pages - len(pages_to_delete)}[/]")

    except Exception as e:
        print_error(f"删除失败: {e}")
        raise typer.Exit(1)
