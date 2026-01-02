"""控制台输出工具"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskID
from rich.text import Text
from typing import Optional, List, Dict, Any

from ..styles.colors import get_theme, Icons, BORDER

# 全局控制台实例
console = Console(theme=get_theme())


def print_banner():
    """打印程序 Banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██████╗ ██████╗ ███████╗██╗  ██╗██╗████████╗               ║
    ║   ██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██║╚══██╔══╝               ║
    ║   ██████╔╝██║  ██║█████╗  █████╔╝ ██║   ██║                  ║
    ║   ██╔═══╝ ██║  ██║██╔══╝  ██╔═██╗ ██║   ██║                  ║
    ║   ██║     ██████╔╝██║     ██║  ██╗██║   ██║                  ║
    ║   ╚═╝     ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝   ╚═╝                  ║
    ║                                                               ║
    ║         全能 PDF 命令行处理工具 v1.0.0                        ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="title")


def print_success(message: str):
    """打印成功消息"""
    console.print(f"{Icons.SUCCESS} {message}", style="success")


def print_error(message: str):
    """打印错误消息"""
    console.print(f"{Icons.ERROR} {message}", style="error")


def print_warning(message: str):
    """打印警告消息"""
    console.print(f"{Icons.WARNING} {message}", style="warning")


def print_info(message: str):
    """打印信息消息"""
    console.print(f"{Icons.INFO} {message}", style="info")


def print_file_info(pdf_info: dict):
    """打印 PDF 文件信息"""
    table = Table(
        title="PDF 文件信息",
        title_style="title",
        border_style=BORDER,
        show_header=True,
        header_style="table.header"
    )

    table.add_column("属性", style="emphasis", width=20)
    table.add_column("值", style="text")

    table.add_row("文件名", f"[filename]{pdf_info['filename']}[/]")
    table.add_row("文件大小", f"[size]{pdf_info['size']}[/]")
    table.add_row("页数", f"[pdf.pages]{pdf_info['pages']}[/] 页")
    table.add_row("PDF 版本", pdf_info['version'])
    table.add_row("创建时间", f"[date]{pdf_info['created']}[/]")
    table.add_row("修改时间", f"[date]{pdf_info['modified']}[/]")
    table.add_row("作者", pdf_info.get('author', '-'))
    table.add_row("标题", pdf_info.get('title', '-'))

    # 加密状态
    if pdf_info.get('encrypted'):
        table.add_row("加密状态", "[pdf.encrypted]已加密 🔒[/]")
    else:
        table.add_row("加密状态", "[success]未加密[/]")

    console.print(table)


class ProgressBar:
    """进度条上下文管理器"""

    def __init__(self, description: str = "处理中"):
        self.description = description
        self.progress: Optional[Progress] = None
        self.task_id: Optional[TaskID] = None
        self.total = 0

    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(style="info"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(
                complete_style="progress.bar.complete",
                finished_style="success",
                bar_width=None,
            ),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        )
        self.progress.__enter__()
        return self

    def __exit__(self, *args):
        if self.progress:
            self.progress.__exit__(*args)

    def add_task(self, total: int, description: Optional[str] = None) -> TaskID:
        """添加任务"""
        self.total = total
        desc = description or self.description
        self.task_id = self.progress.add_task(
            f"{Icons.RUNNING} {desc}",
            total=total
        )
        return self.task_id

    def update(self, advance: int = 1, description: Optional[str] = None):
        """更新进度"""
        if self.task_id:
            kwargs = {"advance": advance}
            if description:
                kwargs["description"] = f"{Icons.RUNNING} {description}"
            self.progress.update(self.task_id, **kwargs)


def create_progress() -> Progress:
    """创建进度条（兼容旧代码）"""
    return Progress(
        SpinnerColumn(style="info"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(
            complete_style="progress.bar.complete",
            finished_style="success",
        ),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    )


def print_result_panel(title: str, content: str, success: bool = True):
    """打印结果面板"""
    style = "success" if success else "error"
    icon = Icons.SUCCESS if success else Icons.ERROR

    panel = Panel(
        content,
        title=f"{icon} {title}",
        border_style=style,
        padding=(1, 2)
    )
    console.print(panel)


def print_operation_summary(operations: List[Dict[str, Any]]):
    """打印操作摘要"""
    table = Table(
        title="操作摘要",
        title_style="title",
        border_style=BORDER
    )

    table.add_column("操作", style="command", width=20)
    table.add_column("输入", style="path", width=30)
    table.add_column("输出", style="path", width=30)
    table.add_column("状态", justify="center", width=10)

    for op in operations:
        status_style = "status.success" if op['success'] else "status.failed"
        status_icon = Icons.SUCCESS if op['success'] else Icons.ERROR

        table.add_row(
            op['operation'],
            op['input'],
            op['output'],
            f"[{status_style}]{status_icon}[/]"
        )

    console.print(table)


def print_table(
    title: str,
    columns: List[str],
    rows: List[List[str]],
    column_styles: Optional[List[str]] = None
):
    """打印通用表格"""
    table = Table(
        title=title,
        title_style="title",
        border_style=BORDER,
        show_header=True,
        header_style="table.header"
    )

    # 添加列
    for i, col in enumerate(columns):
        style = column_styles[i] if column_styles and i < len(column_styles) else None
        table.add_column(col, style=style)

    # 添加行
    for row in rows:
        table.add_row(*row)

    console.print(table)


def print_json(data: Any):
    """打印 JSON 数据"""
    try:
        import json
        console.print_json(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        console.print(str(data))


def confirm(prompt: str, default: bool = False) -> bool:
    """确认提示"""
    from rich.prompt import Confirm

    return Confirm.ask(prompt, console=console, default=default)


def prompt_text(prompt: str, default: str = "", password: bool = False) -> str:
    """文本输入提示"""
    from rich.prompt import Prompt

    if password:
        from rich.prompt import PromptAskError
        # Rich doesn't have built-in password prompt, use getpass
        import getpass
        return getpass.getpass(prompt)
    else:
        return Prompt.ask(prompt, default=default, console=console)


def print_markdown(text: str):
    """打印 Markdown 内容"""
    from rich.markdown import Markdown
    console.print(Markdown(text))


def print_syntax(code: str, lexer: str = "python", line_numbers: bool = True):
    """打印语法高亮代码"""
    from rich.syntax import Syntax
    syntax = Syntax(code, lexer, line_numbers=line_numbers)
    console.print(syntax)


def get_console() -> Console:
    """获取全局控制台实例"""
    return console
