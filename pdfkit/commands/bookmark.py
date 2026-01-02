"""PDF 书签命令"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF

from ..utils.console import (
    console, print_success, print_error, print_info, print_warning, Icons
)
from ..utils.validators import validate_pdf_file, require_unlocked_pdf
from ..utils.file_utils import resolve_path

# 创建 bookmark 子应用
app = typer.Typer(help="书签管理")


@app.command("add")
def add_bookmarks(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    bookmarks_file: Path = typer.Option(
        ...,
        "--file",
        "-f",
        help="书签文件路径（每行格式: 页码 标题）",
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
    从文件导入书签

    书签文件格式（每行一条）:
        1 第一章
        5 1.1 小节
        10 第二章

    示例:
        pdfkit bookmark add document.pdf -f bookmarks.txt
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)

        # 读取书签文件
        toc = []
        with open(bookmarks_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue

                try:
                    page_num = int(parts[0])
                    title = parts[1]
                    if 1 <= page_num <= doc.page_count:
                        toc.append([1, title, page_num])
                except ValueError:
                    continue

        if not toc:
            print_warning("未找到有效的书签")
            doc.close()
            return

        # 设置书签
        doc.set_toc(toc)

        # 确定输出路径
        if output is None:
            output = resolve_path(file)
        else:
            output = resolve_path(output)

        # 保存
        doc.save(output)
        doc.close()

        print_success(f"书签添加完成: [path]{output}[/]")
        print_info(f"添加数量: [number]{len(toc)}[/] 个")

    except Exception as e:
        print_error(f"添加书签失败: {e}")
        raise typer.Exit(1)


@app.command("list")
def list_bookmarks(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
):
    """
    列出 PDF 的所有书签

    示例:
        pdfkit bookmark list document.pdf
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        toc = doc.get_toc()
        doc.close()

        if not toc:
            print_info("该 PDF 没有书签")
            return

        from rich.table import Table
        from ..styles.colors import BORDER

        table = Table(
            title=f"{Icons.BOOKMARK} PDF 书签",
            title_style="title",
            border_style=BORDER,  # 直接使用颜色值
            show_header=True,
            header_style="table.header",
        )

        table.add_column("级别", style="number", width=6)
        table.add_column("标题", width=50)
        table.add_column("页码", style="number", width=8)

        for item in toc:
            level, title, page = item
            table.add_row(str(level), title, str(page))

        from ..utils.console import console as pdfkit_console
        pdfkit_console.print(table)

    except Exception as e:
        print_error(f"列出书签失败: {e}")
        raise typer.Exit(1)


@app.command("remove")
def remove_bookmarks(
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
    删除 PDF 的所有书签

    示例:
        pdfkit bookmark remove document.pdf
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)

        # 清除书签
        doc.set_toc([])

        # 确定输出路径
        if output is None:
            output = resolve_path(file)
        else:
            output = resolve_path(output)

        # 保存
        doc.save(output)
        doc.close()

        print_success(f"书签已删除: [path]{output}[/]")

    except Exception as e:
        print_error(f"删除书签失败: {e}")
        raise typer.Exit(1)
