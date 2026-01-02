"""PDF 合并命令"""

from pathlib import Path
from typing import Optional, List
import typer
import fitz  # PyMuPDF
import pikepdf
import tempfile

from ..utils.console import (
    console, print_success, print_error, print_info, create_progress, Icons
)
from ..utils.validators import validate_pdf_files
from ..utils.file_utils import resolve_path

# 创建 merge 子应用
app = typer.Typer(help="合并 PDF")


def _repair_pdf_with_pikepdf(pdf_path: Path) -> Optional[Path]:
    """
    使用 pikepdf 尝试修复损坏的PDF
    返回修复后的临时文件路径，失败返回 None
    """
    temp_fd = None
    try:
        # 创建临时文件
        temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        temp_file = Path(temp_path)

        # 使用 pikepdf 打开并重新保存（这会修复一些结构问题）
        with pikepdf.open(pdf_path, allow_overwriting_input=True) as pdf:
            pdf.save(temp_file)

        return temp_file
    except Exception:
        return None
    finally:
        # 关闭文件描述符
        if temp_fd is not None:
            try:
                import os
                os.close(temp_fd)
            except:
                pass


def _merge_with_pikepdf(
    pdf_files: List[Path],
    output: Path,
    bookmark: bool = True,
) -> tuple[int, list]:
    """
    使用 pikepdf 合并 PDF 文件
    pikepdf 对非标准 PDF 结构的容错性更好

    返回: (成功合并的文件数, 失败的文件列表)
    """
    merged_count = 0
    failed_files = []

    try:
        # 创建新的 PDF
        merged_pdf = pikepdf.Pdf.new()

        for pdf_file in pdf_files:
            try:
                # pikepdf 打开 PDF（容错模式）
                with pikepdf.open(pdf_file) as src_pdf:
                    # 获取页面范围
                    start_page = len(merged_pdf.pages)

                    # 逐页添加
                    merged_pdf.pages.extend(src_pdf.pages)

                    # 添加书签（大纲）
                    if bookmark:
                        with merged_pdf.open_outline() as outline:
                            # 添加指向该文件第一页的书签
                            outline.root.append(
                                pikepdf.OutlineItem(
                                    pdf_file.stem,
                                    start_page
                                )
                            )

                    merged_count += 1

            except Exception as e:
                failed_files.append((pdf_file, str(e)))

        # 保存结果
        if merged_count > 0:
            merged_pdf.save(output)

        return merged_count, failed_files

    except Exception as e:
        raise Exception(f"合并过程出错: {e}")


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
    tolerant: bool = typer.Option(
        False,
        "--tolerant",
        "-t",
        help="使用宽松模式（对非标准PDF格式容错性更好）",
    ),
):
    """
    合并多个 PDF 文件

    示例:
        # 合并多个文件
        pdfkit merge files file1.pdf file2.pdf file3.pdf -o combined.pdf

        # 合并并排序
        pdfkit merge files *.pdf -o combined.pdf --sort

        # 不添加书签
        pdfkit merge files file1.pdf file2.pdf -o combined.pdf --no-bookmark

        # 宽松模式 (对非标准PDF格式容错性更好，推荐遇到"损坏"问题时使用)
        pdfkit merge files *.pdf -o combined.pdf --tolerant

        # 跳过损坏的文件继续合并
        pdfkit merge files *.pdf -o combined.pdf --skip-errors
    """
    # 验证文件
    valid_files = validate_pdf_files(inputs)
    if not valid_files:
        print_error("没有找到有效的 PDF 文件")
        raise typer.Exit(1)

    # 排序
    if sort:
        valid_files.sort(key=lambda x: x.name)

    print_info(f"准备合并 [number]{len(valid_files)}[/] 个 PDF 文件")

    # 生成输出路径
    if output is None:
        output = resolve_path(valid_files[0].parent / f"{valid_files[0].stem}_merged.pdf")
    else:
        output = resolve_path(output)

    # 确保输出目录存在
    output.parent.mkdir(parents=True, exist_ok=True)

    # ========== 宽松模式：使用 pikepdf ==========
    if tolerant:
        print_info("使用宽松模式 (pikepdf)")

        try:
            merged_count, failed_files = _merge_with_pikepdf(valid_files, output, bookmark)

            if merged_count == 0:
                print_error("没有任何文件成功合并")
                raise typer.Exit(1)

            print_success(f"合并完成: [path]{output}[/]")
            print_info(f"成功合并: [success]{merged_count}[/] / {len(valid_files)} 个文件")

            # 获取总页数
            with pikepdf.open(output) as result_pdf:
                total_pages = len(result_pdf.pages)
            print_info(f"总页数: [pdf.pages]{total_pages}[/] 页")

            if failed_files:
                from ..utils.console import print_warning
                print_warning(f"跳过了 {len(failed_files)} 个无法处理的文件:")
                for pdf_file, error in failed_files[:3]:
                    console.print(f"  [path]{pdf_file.name}[/]: {error[:50]}...", style="dim")
                if len(failed_files) > 3:
                    console.print(f"  ... 及其他 {len(failed_files) - 3} 个文件", style="dim")

        except Exception as e:
            print_error(f"合并失败: {e}")
            raise typer.Exit(1)

        return

    # ========== 标准模式：使用 fitz + 自动修复 ==========
    # 验证PDF完整性（仅做预检，最终会在合并时再处理）
    if not skip_errors and not tolerant:
        print_info("验证PDF文件完整性...")
        corrupted_files = []
        for pdf_file in valid_files:
            try:
                with fitz.open(pdf_file) as doc:
                    # 尝试访问第一页来验证结构
                    if doc.page_count > 0:
                        _ = doc[0].rect
            except Exception as e:
                corrupted_files.append((pdf_file, str(e)))

        if corrupted_files:
            from ..utils.console import print_warning
            print_warning(f"发现 {len(corrupted_files)} 个可能有问题的PDF文件:")
            for pdf_file, error in corrupted_files:
                console.print(f"  [path]{pdf_file}[/]", style="dim")
            print_info("提示: 如果合并失败，请尝试使用 --tolerant 选项")

    try:
        # 创建新文档
        merged_doc = fitz.open()

        # 跟踪成功/失败的文件
        merged_count = 0
        failed_files = []

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.MERGE} 合并中...",
                total=len(valid_files)
            )

            for idx, pdf_file in enumerate(valid_files, 1):
                src_doc = None
                repaired_file = None

                try:
                    # 尝试打开源文件
                    src_doc = fitz.open(pdf_file)

                    # 添加书签（在合并前，指向当前文档的第一页）
                    if bookmark and src_doc.page_count > 0:
                        bookmark_page = len(merged_doc) + 1  # 书签页码从1开始
                        merged_doc.set_toc(
                            merged_doc.get_toc() + [[1, pdf_file.stem, bookmark_page]]
                        )

                    # 合并页面
                    merged_doc.insert_pdf(src_doc)
                    src_doc.close()
                    src_doc = None
                    merged_count += 1

                    progress.update(task, advance=1)

                except Exception as e:
                    # 清理未关闭的文档
                    if src_doc:
                        try:
                            src_doc.close()
                        except:
                            pass

                    # 尝试自动修复
                    print_info(f"文件 [path]{pdf_file.name}[/] 可能损坏，尝试自动修复...")
                    repaired_file = _repair_pdf_with_pikepdf(pdf_file)

                    if repaired_file:
                        try:
                            # 使用修复后的文件
                            src_doc = fitz.open(repaired_file)

                            if bookmark and src_doc.page_count > 0:
                                bookmark_page = len(merged_doc) + 1
                                merged_doc.set_toc(
                                    merged_doc.get_toc() + [[1, pdf_file.stem, bookmark_page]]
                                )

                            merged_doc.insert_pdf(src_doc)
                            src_doc.close()
                            src_doc = None
                            merged_count += 1

                            print_success(f"文件 [path]{pdf_file.name}[/] 修复成功并合并")
                            progress.update(task, advance=1)

                        except Exception as repair_error:
                            if src_doc:
                                try:
                                    src_doc.close()
                                except:
                                    pass

                            error_msg = str(repair_error)
                            failed_files.append((pdf_file, error_msg))
                            print_error(f"修复失败: {error_msg}")

                            if not skip_errors:
                                # 清理临时文件后退出
                                if repaired_file and repaired_file.exists():
                                    try:
                                        repaired_file.unlink()
                                    except:
                                        pass
                                merged_doc.close()
                                raise typer.Exit(1)
                            else:
                                progress.update(task, advance=1)
                        finally:
                            # 清理临时文件
                            if repaired_file and repaired_file.exists():
                                try:
                                    repaired_file.unlink()
                                except:
                                    pass
                    else:
                        # pikepdf 也无法打开，记录错误
                        error_msg = str(e)
                        failed_files.append((pdf_file, error_msg))
                        print_error(f"无法处理文件 [path]{pdf_file.name}[/]: {error_msg}")

                        if not skip_errors:
                            print_info("建议:")
                            print_info("  1. 使用其他工具（如 Adobe Acrobat）打开并另存为PDF")
                            print_info("  2. 使用 --skip-errors 跳过损坏的文件继续合并")
                            merged_doc.close()
                            raise typer.Exit(1)
                        else:
                            progress.update(task, advance=1)

        # 检查是否有成功合并的文件
        if merged_count == 0:
            merged_doc.close()
            print_error("没有任何文件成功合并")
            raise typer.Exit(1)

        # 保存
        merged_doc.save(output)
        merged_doc.close()

        print_success(f"合并完成: [path]{output}[/]")

        # 显示结果
        result_doc = fitz.open(output)
        total_pages = result_doc.page_count
        result_doc.close()

        print_info(f"成功合并: [success]{merged_count}[/] / {len(valid_files)} 个文件")
        print_info(f"总页数: [pdf.pages]{total_pages}[/] 页")

        if failed_files:
            from ..utils.console import print_warning
            print_warning(f"跳过了 {len(failed_files)} 个无法处理的文件:")
            for pdf_file, error in failed_files[:3]:
                console.print(f"  [path]{pdf_file.name}[/]", style="dim")
            if len(failed_files) > 3:
                console.print(f"  ... 及其他 {len(failed_files) - 3} 个文件", style="dim")

    except Exception as e:
        print_error(f"合并失败: {e}")
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

    try:
        # 打开所有文档
        docs = [fitz.open(f) for f in valid_files]
        max_pages = max(doc.page_count for doc in docs)

        # 创建新文档
        merged_doc = fitz.open()

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.MERGE} 交替合并中...",
                total=max_pages * len(docs)
            )

            for page_idx in range(max_pages):
                for doc_idx, doc in enumerate(docs):
                    if page_idx < doc.page_count:
                        merged_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)
                        progress.update(task, advance=1)

        # 关闭所有文档
        for doc in docs:
            doc.close()

        # 生成输出路径
        if output is None:
            output = resolve_path(
                valid_files[0].parent / f"{valid_files[0].stem}_interleaved.pdf"
            )
        else:
            output = resolve_path(output)

        # 保存
        merged_doc.save(output)
        merged_doc.close()

        print_success(f"交替合并完成: [path]{output}[/]")

        # 显示结果
        result_doc = fitz.open(output)
        total_pages = result_doc.page_count
        result_doc.close()

        print_info(f"总页数: [pdf.pages]{total_pages}[/] 页")

    except Exception as e:
        print_error(f"交替合并失败: {e}")
        raise typer.Exit(1)
