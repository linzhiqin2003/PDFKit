"""PDF 信息查看命令"""

from pathlib import Path
from typing import Optional
import typer
from rich.table import Table
import fitz  # PyMuPDF

from ..utils.console import (
    console, print_success, print_error, print_info, Icons
)
from ..utils.validators import validate_pdf_file
from ..utils.file_utils import format_size, format_date

# 创建 info 子应用
app = typer.Typer(help="查看 PDF 信息")


@app.command()
def show(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="显示详细信息（包括元数据）",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="JSON 格式输出",
    ),
    pages: bool = typer.Option(
        False,
        "--pages",
        "-p",
        help="仅显示页数",
    ),
    size: bool = typer.Option(
        False,
        "--size",
        "-s",
        help="仅显示文件大小",
    ),
):
    """
    查看 PDF 文件的详细信息

    示例:
        pdfkit info document.pdf
        pdfkit info document.pdf --detailed
        pdfkit info document.pdf --json
        pdfkit info document.pdf --pages
    """
    # 验证文件
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        # 打开 PDF
        doc = fitz.open(file)

        # 检查是否加密且无法访问
        if doc.is_encrypted and doc.needs_pass:
            print_error(f"PDF 文件已加密，需要密码才能读取")
            print_info("提示: 使用 pdfkit security decrypt <文件> -p <密码> 解密后再操作")
            doc.close()
            raise typer.Exit(1)

        # 基础信息
        info = {
            "filename": file.name,
            "path": str(file.absolute()),
            "size": format_size(file.stat().st_size),
            "size_bytes": file.stat().st_size,
            "pages": doc.page_count,
            "version": "PDF",
            "encrypted": doc.is_encrypted,
        }

        # 元数据 (可能为 None)
        metadata = doc.metadata or {}
        if metadata:
            info["version"] = f"PDF {metadata.get('format', 'Unknown')}"
            info["title"] = metadata.get("title", "-")
            info["author"] = metadata.get("author", "-")
            info["subject"] = metadata.get("subject", "-")
            info["keywords"] = metadata.get("keywords", "-")
            info["creator"] = metadata.get("creator", "-")
            info["producer"] = metadata.get("producer", "-")
            info["created"] = metadata.get("creationDate", "-")
            info["modified"] = metadata.get("modDate", "-")

        # 简单输出模式
        if pages:
            console.print(str(info["pages"]))
            doc.close()
            return

        if size:
            console.print(info["size"])
            doc.close()
            return

        # 输出
        if json_output:
            import json
            console.print_json(json.dumps(info, ensure_ascii=False, indent=2))
        else:
            _print_info_table(info, detailed)

        doc.close()

    except Exception as e:
        print_error(f"读取 PDF 失败: {e}")
        raise typer.Exit(1)


@app.command("meta")
def metadata(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="JSON 格式输出",
    ),
):
    """
    仅显示 PDF 元数据

    示例:
        pdfkit info meta document.pdf
        pdfkit info meta document.pdf --json
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)

        # 检查是否加密且无法访问
        if doc.is_encrypted and doc.needs_pass:
            print_error(f"PDF 文件已加密，需要密码才能读取元数据")
            print_info("提示: 使用 pdfkit security decrypt <文件> -p <密码> 解密后再操作")
            doc.close()
            raise typer.Exit(1)

        meta = doc.metadata or {}

        if not meta:
            print_info("该 PDF 没有元数据")
            doc.close()
            return

        if json_output:
            import json
            console.print_json(json.dumps(meta, ensure_ascii=False, indent=2))
        else:
            table = Table(
                title=f"{Icons.PDF} PDF 元数据",
                title_style="bold magenta",
                border_style="dim",
                show_header=True,
                header_style="bold cyan",
            )

            table.add_column("属性", style="bold cyan", width=15)
            table.add_column("值", style="white")

            for key, value in meta.items():
                if value:
                    table.add_row(key, str(value))

            console.print(table)

        doc.close()

    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"读取元数据失败: {e}")
        raise typer.Exit(1)


def _print_info_table(info: dict, detailed: bool):
    """打印信息表格"""

    # 创建表格
    table = Table(
        title=f"{Icons.PDF} PDF 文件信息",
        title_style="bold magenta",
        border_style="dim",
        show_header=True,
        header_style="bold cyan",
        padding=(0, 1),
    )

    table.add_column("属性", style="bold cyan", width=15)
    table.add_column("值", style="white")

    # 基础信息
    table.add_row("文件名", f"[cyan]{info['filename']}[/]")
    table.add_row("路径", f"[dim]{info['path']}[/]")
    table.add_row("文件大小", f"[green]{info['size']}[/]")
    table.add_row("页数", f"[yellow]{info['pages']}[/] 页")
    table.add_row("PDF 版本", info['version'])

    # 加密状态
    if info['encrypted']:
        table.add_row("加密状态", f"[pdf.encrypted]{Icons.ENCRYPT} 已加密[/]")
    else:
        table.add_row("加密状态", f"[success]{Icons.DECRYPT} 未加密[/]")

    # 详细信息
    if detailed:
        table.add_section()
        table.add_row("[title]元数据[/]", "")
        table.add_row("标题", info.get('title', '-'))
        table.add_row("作者", info.get('author', '-'))
        table.add_row("主题", info.get('subject', '-'))
        table.add_row("关键词", info.get('keywords', '-'))
        table.add_row("创建程序", info.get('creator', '-'))
        table.add_row("PDF 生成器", info.get('producer', '-'))
        table.add_row("创建时间", f"[date]{info.get('created', '-')}[/]")
        table.add_row("修改时间", f"[date]{info.get('modified', '-')}[/]")

    console.print(table)
