"""PDF 拆分命令"""

from pathlib import Path
from typing import Optional, List
import typer
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
import fitz  # PyMuPDF

from ..utils.console import (
    console, print_success, print_error, print_info, create_progress, Icons,
    LiveProgress, print_operation_summary_panel, print_structured_error
)
from ..utils.validators import validate_pdf_file, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import generate_output_path, resolve_path
import time


def split(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="输出目录（默认在当前目录创建 {文件名}_split 文件夹）",
    ),
    range_str: Optional[str] = typer.Option(
        None,
        "--range",
        "-r",
        help="页面范围，如 '1-5,8,10-15'（连续范围合并为一个文件）",
    ),
    chunks: Optional[str] = typer.Option(
        None,
        "--chunks",
        "-c",
        help="按多个范围拆分为独立文件，如 '1-5,10-15,20-25'（每个范围生成一个文件）",
    ),
    single: bool = typer.Option(
        False,
        "--single",
        "-s",
        help="将每一页保存为单独的文件",
    ),
    prefix: str = typer.Option(
        "",
        "--prefix",
        "-p",
        help="输出文件名前缀",
    ),
):
    """
    拆分 PDF 文件

    示例:
        # 拆分为单页文件（输出到 {文件名}_split 文件夹）
        pdfkit split document.pdf --single

        # 按范围拆分（连续范围合并为一个文件）
        pdfkit split document.pdf -r 1-5,8,10-15

        # 按多个范围拆分（每个范围生成独立文件）
        pdfkit split document.pdf -c 1-3,5-7,10-12

        # 拆分到指定目录
        pdfkit split document.pdf -o ./output --single
    """
    # 验证文件
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

    if not require_unlocked_pdf(file, "拆分"):
        raise typer.Exit(1)

    start_time = time.time()

    try:
        # 打开 PDF
        doc = fitz.open(file)
        total_pages = doc.page_count
        print_info(f"PDF 共 [number]{total_pages}[/] 页")

        # 确定输出目录
        if output_dir is None:
            # 默认在当前目录创建以PDF文件名命名的文件夹
            output_dir = Path.cwd() / f"{file.stem}_split"
        else:
            output_dir = resolve_path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if single:
            # 拆分为单页文件
            file_count = _split_single_pages(doc, file, output_dir, prefix)
        elif chunks:
            # 按多个范围拆分（每个范围独立文件）
            file_count = _split_by_chunks(doc, file, output_dir, chunks, prefix)
        elif range_str:
            # 按范围拆分（连续范围合并）
            page_list = validate_page_range(range_str, total_pages)
            file_count = _split_by_range(doc, file, output_dir, page_list, prefix)
        else:
            # 默认拆分为单页
            file_count = _split_single_pages(doc, file, output_dir, prefix)

        doc.close()

        # 打印操作摘要
        console.print()
        duration = time.time() - start_time
        print_operation_summary_panel(
            total=total_pages,
            success=file_count,
            failed=0,
            skipped=0,
            duration=duration,
            output_path=str(output_dir)
        )

    except Exception as e:
        print_structured_error(
            title="拆分失败",
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


def _split_single_pages(
    doc: fitz.Document,
    input_file: Path,
    output_dir: Path,
    prefix: str
) -> int:
    """拆分为单页文件，返回生成的文件数"""
    total_pages = doc.page_count
    stem = input_file.stem

    with LiveProgress("拆分中", total=total_pages) as progress:
        for page_num in range(total_pages):
            # 创建新文档
            new_doc = fitz.open()

            # 复制页面
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            # 生成文件名
            output_name = f"{prefix}{stem}_page_{page_num + 1:03d}.pdf"
            output_path = output_dir / output_name

            # 保存
            new_doc.save(output_path)
            new_doc.close()

            # 更新进度，显示当前处理的文件
            progress.update(advance=1, detail=f"保存 {output_name}")

    return total_pages


def _split_by_chunks(
    doc: fitz.Document,
    input_file: Path,
    output_dir: Path,
    chunks_str: str,
    prefix: str
) -> int:
    """按多个范围拆分，每个范围生成一个独立文件，返回生成的文件数"""
    stem = input_file.stem
    total_pages = doc.page_count

    # 解析chunks字符串，每个逗号分隔的部分是一个chunk
    chunk_ranges = []
    for part in chunks_str.split(','):
        part = part.strip()
        if '-' in part:
            # 范围如 "1-5"
            try:
                start, end = part.split('-')
                start_page = int(start.strip()) - 1  # 转为0-index
                end_page = int(end.strip()) - 1
                if 0 <= start_page < total_pages and 0 <= end_page < total_pages and start_page <= end_page:
                    chunk_ranges.append((start_page, end_page))
            except ValueError:
                continue
        else:
            # 单页如 "8"
            try:
                page_num = int(part.strip()) - 1
                if 0 <= page_num < total_pages:
                    chunk_ranges.append((page_num, page_num))
            except ValueError:
                continue

    if not chunk_ranges:
        print_structured_error(
            title="没有有效的页面范围",
            error_message=f"无法解析范围: {chunks_str}",
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

    # 为每个chunk生成一个文件
    with LiveProgress("拆分中", total=len(chunk_ranges)) as progress:
        for i, (start_page, end_page) in enumerate(chunk_ranges, 1):
            new_doc = fitz.open()

            # 复制范围内的所有页面
            for page_num in range(start_page, end_page + 1):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            # 生成文件名，使用chunk标识
            if start_page == end_page:
                output_name = f"{prefix}{stem}_chunk_{i:03d}_page_{start_page + 1}.pdf"
            else:
                output_name = f"{prefix}{stem}_chunk_{i:03d}_pages_{start_page + 1}-{end_page + 1}.pdf"

            output_path = output_dir / output_name
            new_doc.save(output_path)
            new_doc.close()

            progress.update(advance=1, detail=f"保存 {output_name}")

    return len(chunk_ranges)


def _split_by_range(
    doc: fitz.Document,
    input_file: Path,
    output_dir: Path,
    page_list: List[int],
    prefix: str
) -> int:
    """按页面范围拆分，返回生成的文件数"""
    if not page_list:
        print_structured_error(
            title="没有有效的页面范围",
            error_message="页面范围为空",
            causes=[
                "指定的页面范围不包含任何页",
                "页面范围格式可能不正确"
            ],
            suggestions=[
                "检查页面范围格式",
                "使用 pdfkit info 查看文档总页数"
            ]
        )
        raise typer.Exit(1)

    stem = input_file.stem

    # 如果范围是连续的，生成一个文件
    if _is_consecutive(page_list):
        new_doc = fitz.open()

        for page_num in page_list:
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        output_name = f"{prefix}{stem}_pages_{page_list[0] + 1}-{page_list[-1] + 1}.pdf"
        output_path = output_dir / output_name
        new_doc.save(output_path)
        new_doc.close()

        return 1
    else:
        # 非连续范围，每个范围生成一个文件
        ranges = _group_consecutive(page_list)

        with LiveProgress("拆分中", total=len(ranges)) as progress:
            for r in ranges:
                new_doc = fitz.open()

                for page_num in r:
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

                output_name = f"{prefix}{stem}_pages_{r[0] + 1}-{r[-1] + 1}.pdf"
                output_path = output_dir / output_name
                new_doc.save(output_path)
                new_doc.close()

                progress.update(advance=1, detail=f"保存 {output_name}")

        return len(ranges)


def _is_consecutive(pages: List[int]) -> bool:
    """检查页码是否连续"""
    if len(pages) <= 1:
        return True
    return all(pages[i] + 1 == pages[i + 1] for i in range(len(pages) - 1))


def _group_consecutive(pages: List[int]) -> List[List[int]]:
    """将连续页码分组"""
    if not pages:
        return []

    groups = []
    current_group = [pages[0]]

    for i in range(1, len(pages)):
        if pages[i] == pages[i - 1] + 1:
            current_group.append(pages[i])
        else:
            groups.append(current_group)
            current_group = [pages[i]]

    groups.append(current_group)
    return groups
