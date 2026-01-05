"""控制台输出工具"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskID, ProgressColumn
from rich.text import Text
from typing import Optional, List, Dict, Any, Callable

from ..styles.colors import get_theme, Icons, BORDER
from .platform import setup_windows_console, is_windows

# Windows 控制台初始化 (启用 ANSI 颜色和 UTF-8)
setup_windows_console()

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


def print_structured_error(
    title: str,
    error_message: str,
    causes: Optional[List[str]] = None,
    suggestions: Optional[List[str]] = None,
    docs_link: Optional[str] = None
):
    """打印结构化错误信息，包含原因和建议

    Args:
        title: 错误标题
        error_message: 错误消息
        causes: 可能的原因列表
        suggestions: 建议操作列表
        docs_link: 文档链接
    """
    console.print(f"{Icons.ERROR} {title}", style="error")

    if causes:
        console.print()  # 空行
        console.print("可能的原因:", style="emphasis")
        for i, cause in enumerate(causes, 1):
            console.print(f"  {Icons.DOT} {cause}")

    if suggestions:
        console.print()  # 空行
        console.print("建议操作:", style="emphasis")
        for i, suggestion in enumerate(suggestions, 1):
            console.print(f"  {i}. {suggestion}")

    if docs_link:
        console.print()  # 空行
        console.print(f"文档: [url]{docs_link}[/]")

    console.print()  # 结尾空行


def print_security_warning(
    operation: str,
    risk_level: str = "medium",
    details: Optional[str] = None,
    risks: Optional[List[str]] = None,
    confirmation_required: bool = False
) -> Optional[bool]:
    """打印安全警告

    Args:
        operation: 操作名称
        risk_level: 风险等级 ("low", "medium", "high")
        details: 详细说明
        risks: 风险列表
        confirmation_required: 是否需要用户确认

    Returns:
        如果需要确认，返回用户选择；否则返回 None
    """
    # 根据风险等级选择样式
    risk_styles = {
        "low": "warning",
        "medium": "warning",
        "high": "error"
    }
    risk_icons = {
        "low": "⚠",
        "medium": "⚠",
        "high": "☢"
    }

    style = risk_styles.get(risk_level, "warning")
    icon = risk_icons.get(risk_level, "⚠")

    console.print(f"{icon} 安全警告: {operation}", style=style)

    if details:
        console.print()  # 空行
        console.print(details)

    if risks:
        console.print()  # 空行
        console.print("此操作可能:", style="emphasis")
        for risk in risks:
            console.print(f"  {Icons.DOT} {risk}")

    if confirmation_required:
        console.print()  # 空行
        result = confirm("确认继续?", default=False)
        return result

    console.print()  # 结尾空行
    return None


class StageProgress:
    """多阶段进度显示器

    用于显示批处理操作的分层进度，如:
    [1/3] ✓ 验证文件 ──────────── 5/5 文件
    [2/3] ◐ 处理文件 ──────────── file3.pdf
          ├── file1.pdf ✓ (1.2 MB)
          ├── file2.pdf ✓ (2.1 MB)
          └── file3.pdf ◐ (处理中...)
    [3/3] ○ 生成输出 ──────────── 待处理
    """

    def __init__(self, stages: List[Dict[str, Any]]):
        """初始化阶段进度

        Args:
            stages: 阶段列表，每个阶段包含:
                - name: 阶段名称
                - status: "pending", "running", "done", "failed"
                - detail: 阶段详情 (可选)
                - subitems: 子项目列表 (可选)
        """
        self.stages = stages
        self.current_stage = 0

    def print(self):
        """打印当前进度状态"""
        for i, stage in enumerate(self.stages, 1):
            status = stage.get("status", "pending")
            name = stage.get("name", f"阶段 {i}")
            detail = stage.get("detail", "")
            subitems = stage.get("subitems", [])

            # 状态图标
            status_icons = {
                "pending": Icons.PENDING,
                "running": Icons.RUNNING,
                "done": Icons.SUCCESS,
                "failed": Icons.ERROR,
                "skipped": Icons.WARNING
            }
            icon = status_icons.get(status, Icons.PENDING)

            # 状态样式
            status_styles = {
                "pending": "status.pending",
                "running": "status.running",
                "done": "status.success",
                "failed": "status.failed",
                "skipped": "status.skipped"
            }
            style = status_styles.get(status, "status.pending")

            # 打印阶段行
            total = len(self.stages)
            prefix = f"[{i}/{total}]"
            console.print(f"{prefix} {icon} {name} ──────────── {detail}", style=style)

            # 如果有子项目，打印树状结构
            if subitems and status in ("running", "done"):
                for item in subitems:
                    item_name = item.get("name", "")
                    item_status = item.get("status", "pending")
                    item_detail = item.get("detail", "")

                    item_icon = status_icons.get(item_status, Icons.PENDING)
                    item_style = status_styles.get(item_status, "status.pending")

                    if item_detail:
                        console.print(f"      {Icons.DOT} {item_name} {item_icon} ({item_detail})", style=item_style)
                    else:
                        console.print(f"      {Icons.DOT} {item_name} {item_icon}", style=item_style)

    def update_stage(self, index: int, **kwargs):
        """更新阶段状态

        Args:
            index: 阶段索引 (0-based)
            **kwargs: 要更新的字段 (status, detail, subitems)
        """
        if 0 <= index < len(self.stages):
            self.stages[index].update(kwargs)


def print_stage_progress(stages: List[Dict[str, Any]]):
    """打印分阶段进度（快捷函数）

    Args:
        stages: 阶段列表，每个阶段包含:
            - name: 阶段名称
            - status: "pending", "running", "done", "failed"
            - detail: 阶段详情 (可选)
            - subitems: 子项目列表 (可选)
    """
    progress = StageProgress(stages)
    progress.print()


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
    from rich.progress import TimeElapsedColumn

    return Progress(
        SpinnerColumn(style="info", finished_text="[success]✓[/]"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(
            complete_style="progress.bar.complete",
            finished_style="success",
            bar_width=None,
        ),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        expand=True,
    )


def create_indeterminate_progress(description: str = "处理中") -> Progress:
    """创建不确定进度条（用于未知时长的操作）

    只显示 spinner 和时间，不显示进度百分比

    Args:
        description: 进度描述

    Returns:
        Progress 对象
    """
    from rich.progress import TimeElapsedColumn

    return Progress(
        SpinnerColumn(style="info"),
        TextColumn(f"[progress.description]{description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def create_industrial_progress(total: Optional[int] = None) -> Progress:
    """创建工业风格进度条（使用工业橙色）

    Args:
        total: 总任务数，None 表示不确定进度

    Returns:
        Progress 对象
    """
    from rich.progress import TimeElapsedColumn

    return Progress(
        SpinnerColumn(style="industrial", finished_text="[success]✓[/]"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(
            complete_style="progress.bar.industrial",
            finished_style="industrial",
            bar_width=None,
        ),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        expand=True,
    )


def print_file_queue_progress(files: List[Dict[str, Any]]):
    """打印文件队列进度（列表形式，显示每个文件状态）

    Args:
        files: 文件列表，每个文件包含:
            - name: 文件名
            - status: "pending", "running", "success", "failed", "skipped"
            - detail: 详情 (可选，如文件大小)
    """
    status_icons = {
        "pending": Icons.PENDING,
        "running": Icons.RUNNING,
        "success": Icons.SUCCESS,
        "failed": Icons.ERROR,
        "skipped": Icons.WARNING
    }
    status_styles = {
        "pending": "status.pending",
        "running": "status.running",
        "success": "status.success",
        "failed": "status.failed",
        "skipped": "status.skipped"
    }

    for file_info in files:
        name = file_info.get("name", "")
        status = file_info.get("status", "pending")
        detail = file_info.get("detail", "")

        icon = status_icons.get(status, Icons.PENDING)
        style = status_styles.get(status, "status.pending")

        if detail:
            console.print(f"  {icon} {name} ({detail})", style=style)
        else:
            console.print(f"  {icon} {name}", style=style)


class LiveProgress:
    """实时进度显示（单行更新）

    用于处理过程中的实时进度更新，每次更新会覆盖前一行。

    示例:
        with LiveProgress("处理中...", total=100) as progress:
            for i in range(100):
                progress.update(advance=1, detail=f"文件 {i + 1}/100")
                time.sleep(0.1)
    """

    def __init__(
        self,
        description: str = "处理中",
        total: int = 100,
        show_percentage: bool = True,
        show_bar: bool = True,
        show_elapsed: bool = True
    ):
        """初始化实时进度

        Args:
            description: 进度描述
            total: 总任务数
            show_percentage: 是否显示百分比
            show_bar: 是否显示进度条
            show_elapsed: 是否显示已用时间
        """
        self.description = description
        self.total = total
        self.show_percentage = show_percentage
        self.show_bar = show_bar
        self.show_elapsed = show_elapsed
        self.progress: Optional[Progress] = None
        self.task_id: Optional[TaskID] = None

    def __enter__(self):
        # 创建进度列
        columns = [SpinnerColumn(style="info")]

        # 进度描述列 - 使用固定的 task.description 占位符
        columns.append(TextColumn("[progress.description]{task.description}"))

        # 进度条
        if self.show_bar:
            columns.append(BarColumn(
                complete_style="progress.bar.complete",
                finished_style="success",
                bar_width=40,
            ))

        # 百分比
        if self.show_percentage:
            columns.append(TextColumn("[progress.percentage]{task.percentage:>3.0f}%"))

        # 已用时间
        if self.show_elapsed:
            from rich.progress import TimeElapsedColumn
            columns.append(TimeElapsedColumn())

        # 创建 Progress 对象（自动刷新）
        self.progress = Progress(
            *columns,
            console=console,
            refresh_per_second=10,
        )

        # 使用 start() 启动刷新线程（而不是 __enter__）
        self.progress.start()

        # 添加任务
        initial_desc = f"{Icons.RUNNING} {self.description}"
        self.task_id = self.progress.add_task(
            initial_desc,
            total=self.total,
            completed=0
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            try:
                if self.task_id is not None:
                    # 如果是中断，保持当前进度；否则显示完成
                    if exc_type is KeyboardInterrupt:
                        # 中断时保持当前进度，不强制设置为100%
                        pass
                    else:
                        # 正常完成，设置为100%
                        self.progress.update(self.task_id, completed=self.total)
                    self.progress.refresh()
                self.progress.stop()
            except Exception:
                # 如果 progress 已经关闭，忽略异常
                pass

    def update(
        self,
        advance: int = 1,
        completed: Optional[int] = None,
        detail: Optional[str] = None
    ):
        """更新进度

        Args:
            advance: 增加的进度数
            completed: 直接设置完成数（优先级高于 advance）
            detail: 详情描述
        """
        if self.progress and self.task_id:
            # Rich Progress 的 advance 参数直接增量更新
            if completed is not None:
                self.progress.update(self.task_id, completed=completed)
                if detail is not None:
                    self.progress.update(self.task_id, description=f"{Icons.RUNNING} {self.description} - {detail}")
            else:
                if detail is not None:
                    self.progress.update(self.task_id, advance=advance, description=f"{Icons.RUNNING} {self.description} - {detail}")
                else:
                    self.progress.update(self.task_id, advance=advance)


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


def print_operation_summary_panel(
    total: int,
    success: int,
    failed: int,
    skipped: int = 0,
    duration: float = 0.0,
    output_path: Optional[str] = None
):
    """打印操作摘要面板（带边框的面板样式）

    Args:
        total: 总文件数
        success: 成功数
        failed: 失败数
        skipped: 跳过数
        duration: 耗时（秒）
        output_path: 输出路径
    """
    # 构建内容
    lines = [
        f"{Icons.SUCCESS} 成功: [number]{success}[/] 个文件",
    ]

    if skipped > 0:
        lines.append(f"{Icons.WARNING} 跳过: [number]{skipped}[/] 个文件 (加密/损坏)")

    if failed > 0:
        lines.append(f"{Icons.ERROR} 失败: [number]{failed}[/] 个文件")

    lines.append("")  # 空行

    if duration > 0:
        lines.append(f"总耗时: [size]{duration:.1f}[/] 秒")

    if output_path:
        lines.append(f"输出: [path]{output_path}[/]")

    content = "\n".join(lines)

    # 创建面板
    panel = Panel(
        content,
        title="操作摘要",
        border_style="info",
        padding=(1, 2)
    )
    console.print(panel)


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


# 表格边框样式映射 (使用 rich.box 类型)
from rich import box as rich_box

TABLE_BOX_STYLES = {
    "industrial": rich_box.HEAVY,       # 粗边框 - 工业风格
    "minimal": rich_box.SIMPLE,         # 极简
    "compact": rich_box.MARKDOWN,       # 紧凑 - Markdown 风格
    "classic": rich_box.ASCII,          # 经典 ASCII
    "rounded": rich_box.ROUNDED,        # 圆角
    "double": rich_box.DOUBLE,          # 双线
    "none": None,                       # 无边框
}


def print_table_with_style(
    title: str,
    columns: List[str],
    rows: List[List[str]],
    style: str = "industrial",
    column_styles: Optional[List[str]] = None,
    show_header: bool = True
):
    """使用指定样式打印表格

    Args:
        title: 表格标题
        columns: 列名列表
        rows: 行数据列表
        style: 表格样式 (industrial, minimal, compact, classic, rounded, double, none)
        column_styles: 列样式列表
        show_header: 是否显示表头
    """
    box_style = TABLE_BOX_STYLES.get(style, rich_box.HEAVY)

    table = Table(
        title=title,
        title_style="title",
        box=box_style,
        border_style="dim",  # 边框颜色，不是边框类型
        show_header=show_header,
        header_style="table.header"
    )

    # 添加列
    for i, col in enumerate(columns):
        col_style = column_styles[i] if column_styles and i < len(column_styles) else None
        table.add_column(col, style=col_style)

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
