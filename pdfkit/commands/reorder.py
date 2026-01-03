"""PDF 页面重排命令"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF

from ..utils.console import (
    console, print_success, print_error, print_info, print_warning, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, require_unlocked_pdf
from ..utils.file_utils import resolve_path

# 创建 reorder 子应用
app = typer.Typer(help="重排 PDF 页面")


@app.command()
def pages(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    order: str = typer.Option(
        ...,
        "--order",
        help="新的页面顺序，逗号分隔，如 '3,1,2,4'",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径（默认覆盖原文件）",
    ),
):
    """
    按指定顺序重新排列 PDF 页面

    示例:
        # 将页面顺序改为 3,1,2,4
        pdfkit reorder document.pdf --order 3,1,2,4

        # 将第5页移到最前面，保存到新文件
        pdfkit reorder document.pdf --order 5,1-4 -o reordered.pdf
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if not require_unlocked_pdf(file, "重排页面"):
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 解析顺序
        new_order = _parse_order(order, total_pages)

        if not new_order:
            print_error("无效的页面顺序")
            raise typer.Exit(1)

        if len(new_order) != total_pages:
            print_warning(f"指定的页数 ({len(new_order)}) 与总页数 ({total_pages}) 不匹配")

        print_info(f"新顺序: [command]{','.join(str(p + 1) for p in new_order)}[/]")

        # 创建新文档
        new_doc = fitz.open()

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.ARROW_RIGHT} 重排中...",
                total=len(new_order)
            )

            for page_num in new_order:
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

        print_success(f"页面重排完成: [path]{output}[/]")

    except Exception as e:
        print_error(f"重排失败: {e}")
        raise typer.Exit(1)


def _parse_order(order_str: str, total_pages: int) -> list:
    """解析页面顺序字符串"""
    result = []
    parts = order_str.split(",")

    for part in parts:
        part = part.strip()
        if "-" in part:
            # 处理范围，如 "1-4"
            try:
                start, end = part.split("-")
                start = int(start.strip()) - 1
                end = int(end.strip()) - 1
                if 0 <= start < total_pages and 0 <= end < total_pages:
                    result.extend(range(start, end + 1))
            except ValueError:
                pass
        else:
            # 处理单页
            try:
                page = int(part) - 1
                if 0 <= page < total_pages:
                    result.append(page)
            except ValueError:
                pass

    return result
