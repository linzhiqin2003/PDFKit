"""PDF 优化命令"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF
import pikepdf

from ..utils.console import (
    console, print_success, print_error, print_info, print_warning, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, require_unlocked_pdf
from ..utils.file_utils import resolve_path, format_size
from ..utils.config import load_config

# 创建 optimize 子应用
app = typer.Typer(help="优化操作")


# ============================================================================
# 压缩 PDF
# ============================================================================

@app.command("compress")
def compress_pdf(
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
    quality: str = typer.Option(
        "medium",
        "--quality",
        "-q",
        help="压缩质量: low, medium, high",
    ),
):
    """
    压缩 PDF 文件大小

    示例:
        # 中等质量压缩
        pdfkit optimize compress document.pdf

        # 高质量压缩（文件较大）
        pdfkit optimize compress document.pdf -q high

        # 低质量压缩（文件最小）
        pdfkit optimize compress document.pdf -q low
    """
    if quality not in ("low", "medium", "high"):
        print_error("质量必须是 low, medium 或 high")
        raise typer.Exit(1)

    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        # 获取原始文件大小
        original_size = file.stat().st_size

        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}_compressed.pdf")
        else:
            output = resolve_path(output)

        # 使用 pikepdf 进行压缩
        pdf = pikepdf.open(file)

        # 根据质量设置保存选项
        if quality == "low":
            # 最低质量，最小文件：压缩流 + 对象流 + 去除冗余
            pdf.save(
                output,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                recompress_flate=True,
            )
        elif quality == "medium":
            # 中等质量
            pdf.save(
                output,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.preserve,
            )
        else:  # high
            # 高质量：保持更多原始结构
            pdf.save(
                output,
                compress_streams=False,
                object_stream_mode=pikepdf.ObjectStreamMode.disable,
            )

        pdf.close()

        # 获取压缩后大小
        compressed_size = output.stat().st_size
        reduction = (1 - compressed_size / original_size) * 100

        print_success(f"压缩完成: [path]{output}[/]")
        print_info(f"原始大小: [size]{format_size(original_size)}[/]")
        print_info(f"压缩后: [size]{format_size(compressed_size)}[/]")

        if reduction > 0:
            print_info(f"减少: [success]{reduction:.1f}%[/]")
        else:
            print_info(f"文件大小增加了 {-reduction:.1f}%（可能已经是最优压缩）")

    except Exception as e:
        print_error(f"压缩失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# 优化图片
# ============================================================================

@app.command("optimize-images")
def optimize_images(
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
    dpi: int = typer.Option(
        150,
        "--dpi",
        "-d",
        help="目标 DPI（降低 DPI 可减小文件大小）",
    ),
    quality: int = typer.Option(
        85,
        "--quality",
        "-q",
        help="JPEG 质量 (1-100)",
    ),
):
    """
    优化 PDF 中的图片

    示例:
        # 优化图片为 150 DPI
        pdfkit optimize optimize-images document.pdf

        # 优化图片为 72 DPI（更小）
        pdfkit optimize optimize-images document.pdf -d 72
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if dpi < 72 or dpi > 300:
        print_error("DPI 必须在 72-300 之间")
        raise typer.Exit(1)

    if quality < 1 or quality > 100:
        print_error("质量必须在 1-100 之间")
        raise typer.Exit(1)

    try:
        # 获取原始文件大小
        original_size = file.stat().st_size

        doc = fitz.open(file)

        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}_optimized.pdf")
        else:
            output = resolve_path(output)

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.COMPRESS} 优化图片中...",
                total=doc.page_count
            )

            for page_num in range(doc.page_count):
                page = doc[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    xref = img[0]

                    # 提取图片
                    base_image = doc.extract_image(xref)
                    image_data = base_image["image"]
                    image_ext = base_image["ext"]

                    # 如果是 JPEG，可以重新压缩
                    if image_ext == "jpeg":
                        from PIL import Image as PILImage
                        from io import BytesIO

                        pil_img = PILImage.open(BytesIO(image_data))

                        # 重新保存为 JPEG
                        output_buffer = BytesIO()
                        pil_img.save(output_buffer, format="JPEG", quality=quality)
                        output_buffer.seek(0)

                        # 替换图片
                        page.insert_image(
                            page.rect,
                            stream=output_buffer.read(),
                            xref=xref
                        )

                progress.update(task, advance=1)

        # 保存
        doc.save(output, deflate=True)
        doc.close()

        # 获取优化后大小
        optimized_size = output.stat().st_size
        reduction = (1 - optimized_size / original_size) * 100

        print_info(f"原始大小: [size]{format_size(original_size)}[/]")
        print_info(f"优化后: [size]{format_size(optimized_size)}[/]")

        if reduction > 0:
            print_success(f"优化完成: [path]{output}[/]")
            print_info(f"减少: [success]{reduction:.1f}%[/]")
        else:
            # 文件变大了，给出警告
            print_warning(f"优化后文件增大了 {-reduction:.1f}%")
            print_warning("可能原因: 原始图片已经是最优压缩，或 DPI/质量设置过高")
            print_info(f"建议: 尝试降低 DPI (当前: {dpi}) 或质量 (当前: {quality})")
            print_success(f"文件已保存: [path]{output}[/]")

    except Exception as e:
        print_error(f"优化失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# 修复 PDF
# ============================================================================

@app.command("repair")
def repair_pdf(
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
    修复损坏的 PDF 文件

    尝试修复以下问题:
    - 损坏的 PDF 结构
    - 损坏的对象
    - 损坏的交叉引用表

    示例:
        pdfkit optimize repair damaged.pdf
    """
    if not file.exists():
        print_error(f"文件不存在: {file}")
        raise typer.Exit(1)

    try:
        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}_repaired.pdf")
        else:
            output = resolve_path(output)

        print_info("尝试修复 PDF...")

        # 使用 pikepdf 尝试打开并重新保存
        try:
            pdf = pikepdf.open(file, allow_overwriting_input=True)
            pdf.save(output)
            pdf.close()

            print_success(f"修复完成: [path]{output}[/]")

        except Exception as e:
            # 如果 pikepdf 失败，尝试 PyMuPDF
            print_warning(f"pikepdf 修复失败: {e}，尝试使用 PyMuPDF...")

            try:
                doc = fitz.open(file)
                doc.save(output)
                doc.close()

                print_success(f"修复完成: [path]{output}[/]")

            except Exception as e2:
                print_error(f"修复失败: {e2}")
                raise typer.Exit(1)

    except Exception as e:
        print_error(f"修复失败: {e}")
        raise typer.Exit(1)
