"""PDF 页面删除命令"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF

from ..utils.console import (
    console, print_success, print_info, Icons, LiveProgress,
    print_operation_summary_panel, print_structured_error
)
from ..utils.validators import validate_pdf_file, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import resolve_path
import time

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
    confirm: bool = typer.Option(
        False,
        "--confirm",
        "-y",
        help="跳过确认提示",
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

        # 跳过确认提示
        pdfkit delete pages document.pdf -r 1-5 -y
    """
    if not validate_pdf_file(file):
        print_structured_error(
            title="无效的 PDF 文件",
            error_message=f"文件不存在或不是有效的 PDF: {file}",
            causes=[
                "文件路径拼写错误",
                "文件已损坏",
                "文件格式不是 PDF"
            ],
            suggestions=[
                "检查文件路径是否正确",
                "使用 pdfkit info 命令检查文件状态"
            ]
        )
        raise typer.Exit(1)

    if not require_unlocked_pdf(file, "删除页面"):
        raise typer.Exit(1)

    start_time = time.time()

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 解析要删除的页面
        pages_to_delete = validate_page_range(range_str, total_pages)

        if not pages_to_delete:
            print_structured_error(
                title="没有有效的页面范围",
                error_message=f"无法解析范围: {range_str}",
                causes=[
                    "范围格式不正确",
                    "页码超出文档范围"
                ],
                suggestions=[
                    "正确格式: 1-5,8,10-15",
                    "页码从 1 开始",
                    "使用 pdfkit info 查看文档总页数"
                ]
            )
            raise typer.Exit(1)

        # 确定输出路径
        if output is None:
            output = resolve_path(file)
        else:
            output = resolve_path(output)

        remaining_pages = total_pages - len(pages_to_delete)

        # 显示操作确认
        console.print()
        print_info(f"原始页数: [number]{total_pages}[/] 页")
        print_info(f"将删除: [number]{len(pages_to_delete)}[/] 页")
        print_info(f"删除后: [number]{remaining_pages}[/] 页")
        print_info(f"输出路径: [path]{output}[/]")

        # 如果没有 --confirm 选项，显示确认提示
        if not confirm:
            console.print()
            typer.confirm(f"确认删除这 [number]{len(pages_to_delete)}[/] 页吗？", abort=True)

        # 创建新文档（排除要删除的页面）
        new_doc = fitz.open()

        with LiveProgress("删除页面中", total=total_pages) as progress:
            for page_num in range(total_pages):
                if page_num not in pages_to_delete:
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                    progress.update(advance=1, detail=f"保留第 {page_num + 1} 页")
                else:
                    progress.update(advance=1, detail=f"删除第 {page_num + 1} 页")

        doc.close()

        # 保存
        new_doc.save(output)
        new_doc.close()

        # 打印操作摘要
        console.print()
        duration = time.time() - start_time
        print_operation_summary_panel(
            total=total_pages,
            success=remaining_pages,
            failed=0,
            skipped=len(pages_to_delete),
            duration=duration,
            output_path=str(output)
        )

    except Exception as e:
        print_structured_error(
            title="删除失败",
            error_message=str(e),
            causes=[
                "PDF 文件可能已损坏",
                "磁盘空间不足",
                "输出目录无写入权限",
                "文件加密导致无法读取"
            ],
            suggestions=[
                "使用 pdfkit info 检查文件状态",
                "检查磁盘空间: df -h",
                "确认输出目录有写入权限",
                "如果文件加密，先使用 pdfkit decrypt 解密"
            ]
        )
        raise typer.Exit(1)
