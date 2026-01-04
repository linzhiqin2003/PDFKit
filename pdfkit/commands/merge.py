"""PDF 合并命令"""

from pathlib import Path
from typing import Optional, List
import typer
import fitz  # PyMuPDF

from ..core.pdf_merge import merge_files, MergeResult, interleave_files
from ..utils.console import (
    console, print_success, print_error, print_info, create_progress, Icons, print_warning,
    StageProgress, print_operation_summary_panel, print_structured_error
)
from ..utils.validators import validate_pdf_files
from ..utils.file_utils import resolve_path
import time

# 创建 merge 子应用
app = typer.Typer(help="合并 PDF")


@app.command()
def files(
    inputs: List[Path] = typer.Argument(
        ...,
        help="要合并的 PDF 文件",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    bookmark: bool = typer.Option(
        True,
        "--bookmark/--no-bookmark",
        help="是否为每个文件添加书签",
    ),
    sort: bool = typer.Option(
        False,
        "--sort",
        "-s",
        help="按文件名排序",
    ),
    skip_errors: bool = typer.Option(
        False,
        "--skip-errors",
        help="跳过无法合并的文件（不中断整个合并过程）",
    ),
):
    """
    合并多个 PDF 文件

    使用三层容错策略（按兼容性排序）:
    1. pypdf - 最宽松，对 malformed page tree 容错性最好
    2. PyMuPDF (fitz) - 快速高效
    3. pikepdf - 中等容错性

    示例:
        # 合并多个文件
        pdfkit merge files file1.pdf file2.pdf file3.pdf -o combined.pdf

        # 合并并排序
        pdfkit merge files *.pdf -o combined.pdf --sort

        # 不添加书签
        pdfkit merge files file1.pdf file2.pdf -o combined.pdf --no-bookmark

        # 跳过损坏的文件继续合并
        pdfkit merge files *.pdf -o combined.pdf --skip-errors
    """
    # 验证文件
    valid_files = validate_pdf_files(inputs)
    if not valid_files:
        print_structured_error(
            title="没有找到有效的 PDF 文件",
            error_message="提供的输入中没有有效的 PDF 文件",
            causes=[
                "文件路径拼写错误",
                "文件可能已损坏",
                "文件格式不是 PDF"
            ],
            suggestions=[
                "检查文件路径是否正确",
                "使用 pdfkit info 命令检查文件状态",
                "确认文件扩展名是 .pdf"
            ]
        )
        raise typer.Exit(1)

    # 排序
    if sort:
        valid_files.sort(key=lambda x: x.name)

    # 生成输出路径
    if output is None:
        output = resolve_path(valid_files[0].parent / f"{valid_files[0].stem}_merged.pdf")
    else:
        output = resolve_path(output)

    # 确保输出目录存在
    output.parent.mkdir(parents=True, exist_ok=True)

    # 使用核心模块的三层容错策略
    start_time = time.time()

    # 初始化多阶段进度（完成后统一显示）
    stages = [
        {"name": "验证文件", "status": "done", "detail": f"{len(valid_files)} 个文件"},
        {"name": "合并文件", "status": "running", "detail": f"{len(valid_files)} 个文件 → {output.name}"},
        {"name": "生成输出", "status": "pending", "detail": "等待中"},
    ]

    print_info(f"正在合并 [number]{len(valid_files)}[/] 个 PDF 文件...")

    try:
        result: MergeResult = merge_files(
            valid_files,
            output,
            bookmark=bookmark,
            auto_repair=True,
            skip_errors=skip_errors,
        )

        # 更新所有阶段为完成状态
        stages[1]["status"] = "done"
        stages[2]["status"] = "done"
        stages[2]["detail"] = f"{result.total_pages} 页"

        # 打印最终阶段进度（只打印一次）
        console.print()
        StageProgress(stages).print()

        # 打印操作摘要面板
        console.print()
        duration = time.time() - start_time
        print_operation_summary_panel(
            total=result.total_files,
            success=result.merged_files,
            failed=len(result.failed_files),
            skipped=0,
            duration=duration,
            output_path=str(output)
        )

    except Exception as e:
        print_structured_error(
            title="合并失败",
            error_message=str(e),
            causes=[
                "某些 PDF 文件可能已损坏",
                "文件加密导致无法读取",
                "磁盘空间不足",
                "输出路径无写入权限"
            ],
            suggestions=[
                "使用 --skip-errors 跳过损坏文件",
                "检查磁盘空间: df -h",
                "确认输出目录有写入权限",
                "尝试单独处理有问题的文件"
            ]
        )
        raise typer.Exit(1)


@app.command("dir")
def directory(
    dir: Path = typer.Argument(
        ...,
        help="包含 PDF 文件的目录",
        exists=True,
        file_okay=False,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    pattern: str = typer.Option(
        "*.pdf",
        "--pattern",
        "-p",
        help="文件匹配模式",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="递归搜索子目录",
    ),
    bookmark: bool = typer.Option(
        True,
        "--bookmark/--no-bookmark",
        help="是否为每个文件添加书签",
    ),
    sort: bool = typer.Option(
        True,
        "--sort/--no-sort",
        help="按文件名排序",
    ),
):
    """
    合并目录中的所有 PDF 文件

    示例:
        # 合并当前目录的所有 PDF
        pdfkit merge dir .

        # 递归合并
        pdfkit merge dir . -r

        # 使用自定义模式
        pdfkit merge dir . -p "chapter_*.pdf"
    """
    dir = resolve_path(dir)

    # 查找文件
    if recursive:
        pdf_files = list(dir.rglob(pattern))
    else:
        pdf_files = list(dir.glob(pattern))

    if not pdf_files:
        print_error(f"未找到匹配的 PDF 文件: {pattern}")
        raise typer.Exit(1)

    # 调用主合并命令
    files(pdf_files, output, bookmark, sort)


@app.command("interleave")
def interleave(
    inputs: List[Path] = typer.Argument(
        ...,
        help="要交替合并的 PDF 文件",
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
    交替合并 PDF 页面

    例如，将两个 PDF 的页面交替合并：file1 的第1页，file2 的第1页，
    file1 的第2页，file2 的第2页，依此类推。

    示例:
        pdfkit merge interleave file1.pdf file2.pdf -o interleaved.pdf
    """
    # 验证文件
    valid_files = validate_pdf_files(inputs)
    if len(valid_files) < 2:
        print_error("至少需要 2 个 PDF 文件进行交替合并")
        raise typer.Exit(1)

    # 生成输出路径
    if output is None:
        output = resolve_path(
            valid_files[0].parent / f"{valid_files[0].stem}_interleaved.pdf"
        )
    else:
        output = resolve_path(output)

    # 使用核心模块的 interleave_files
    try:
        result: MergeResult = interleave_files(
            valid_files[0],
            valid_files[1],
            output,
        )

        print_success(f"交替合并完成: [path]{output}[/]")
        print_info(f"总页数: [pdf.pages]{result.total_pages}[/] 页")

    except Exception as e:
        print_error(f"交替合并失败: {e}")
        raise typer.Exit(1)
