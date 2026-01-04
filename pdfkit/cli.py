#!/usr/bin/env python3
"""PDFKit - 全能 PDF 命令行处理工具"""

import sys
from typing import Optional

import typer
from rich.console import Console

from .utils.console import console, print_banner
from .styles.colors import Icons
from . import __version__

# 创建主应用
app = typer.Typer(
    name="pdfkit",
    help="🔧 全能 PDF 命令行处理工具",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=False,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
)


# 版本回调
def version_callback(value: bool):
    """显示版本号"""
    if value:
        console.print(f"[title]PDFKit[/] version [number]{__version__}[/]")
        raise typer.Exit()


# 全局选项回调
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="显示版本号",
        callback=version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="详细输出",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="静默模式",
    ),
):
    """
    PDFKit - 全能 PDF 命令行处理工具

    使用 [bold cyan]pdfkit COMMAND --help[/] 查看具体命令的帮助信息。
    """
    # 保存全局选项到 context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    # 如果没有子命令，显示 banner
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print()
        _print_usage()


def _print_usage():
    """打印使用说明"""
    from rich.table import Table
    from rich.columns import Columns

    # 命令分类表格
    table = Table(
        show_header=False,
        show_edge=False,
        show_footer=False,
        padding=(0, 1),
        box=None,
    )

    table.add_column("category", style="title", width=20)
    table.add_column("commands", style="text")

    # 基础操作
    table.add_row(
        "[bold green]📋 基础操作[/]",
        "info       查看 PDF 信息\n"
        "extract    提取内容 (text/images/tables/pages)"
    )

    # 页面操作
    table.add_row(
        "[bold green]📄 页面操作[/]",
        "split      拆分 PDF\n"
        "merge      合并 PDF\n"
        "delete     删除页面\n"
        "rotate     旋转页面\n"
        "reorder    重排页面\n"
        "reverse    反转顺序"
    )

    # 转换操作
    table.add_row(
        "[bold green]🔄 格式转换[/]",
        "to-image   PDF 转图片\n"
        "from-images 图片转 PDF\n"
        "to-word    PDF 转 Word\n"
        "to-html    PDF 转 HTML\n"
        "from-html  HTML 转 PDF"
    )

    # 编辑操作
    table.add_row(
        "[bold green]✏️ 编辑[/]",
        "watermark  添加水印\n"
        "header     添加页眉\n"
        "footer     添加页脚\n"
        "crop       裁剪页面\n"
        "resize     调整大小"
    )

    # 安全操作
    table.add_row(
        "[bold green]🔒 安全[/]",
        "encrypt    加密 PDF\n"
        "decrypt    解密 PDF"
    )

    # 优化操作
    table.add_row(
        "[bold green]⚡ 优化[/]",
        "compress   压缩 PDF\n"
        "optimize   优化图片\n"
        "repair     修复 PDF"
    )

    # OCR 功能
    table.add_row(
        "[bold green]🔍 OCR[/]",
        "ocr        文字识别\n"
        "ocr-table  表格提取\n"
        "ocr-layout 版面分析"
    )

    # AI 功能
    table.add_row(
        "[bold green]✨ AI[/]",
        "ai         智能抽取\n"
    )

    # 批量处理
    table.add_row(
        "[bold green]📦 批量[/]",
        "batch      批量处理\n"
        "watch      监控目录"
    )

    console.print(table)

    console.print()
    console.print("[bold cyan]全局选项:[/")
    console.print("  --help, -h    显示帮助信息")
    console.print("  --version, -v 显示版本号")
    console.print("  --verbose     详细输出")
    console.print("  --quiet, -q   静默模式")
    console.print()
    console.print("[bold cyan]示例:[/]")
    console.print("  [dim]# 查看 PDF 信息[/]")
    console.print("  $ pdfkit info document.pdf")
    console.print()
    console.print("  [dim]# 合并多个 PDF[/]")
    console.print("  $ pdfkit merge file1.pdf file2.pdf -o combined.pdf")
    console.print()
    console.print("  [dim]# 压缩 PDF[/]")
    console.print("  $ pdfkit compress large.pdf -o small.pdf")
    console.print()
    console.print("[dim]使用 [bold cyan]pdfkit COMMAND --help[/] 查看命令详细帮助[/]")


# 注册子命令
from .commands.info import app as info_app
from .commands.split import split as split_cmd
from .commands.merge import app as merge_app
from .commands.extract import app as extract_app
from .commands.delete import app as delete_app
from .commands.rotate import app as rotate_app
from .commands.reorder import app as reorder_app
from .commands.reverse import app as reverse_app
from .commands.convert import app as convert_app
from .commands.edit import app as edit_app
from .commands.header import app as header_app
from .commands.footer import app as footer_app
from .commands.bookmark import app as bookmark_app
from .commands.security import app as security_app
from .commands.optimize import app as optimize_app
from .commands.ocr import app as ocr_app
from .commands.ai import app as ai_app
from .commands.batch import app as batch_app
app.add_typer(info_app, name="info")
app.command(name="split")(split_cmd)
app.add_typer(merge_app, name="merge")
app.add_typer(extract_app, name="extract")
app.add_typer(delete_app, name="delete")
app.add_typer(rotate_app, name="rotate")
app.add_typer(reorder_app, name="reorder")
app.add_typer(reverse_app, name="reverse")
app.add_typer(convert_app, name="convert")
app.add_typer(edit_app, name="edit")
app.add_typer(header_app, name="header")
app.add_typer(footer_app, name="footer")
app.add_typer(bookmark_app, name="bookmark")
app.add_typer(security_app, name="security")
app.add_typer(optimize_app, name="optimize")
app.add_typer(ocr_app, name="ocr")
app.add_typer(ai_app, name="ai")
app.add_typer(batch_app, name="batch")


def run():
    """运行 CLI"""
    app()
