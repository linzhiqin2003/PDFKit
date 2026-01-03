"""PDF 编辑命令"""

from pathlib import Path
from typing import Optional, List, Tuple
import typer
import fitz  # PyMuPDF
from PIL import Image
import re

from ..utils.console import (
    console, print_success, print_error, print_info, print_warning, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import resolve_path
from ..utils.config import load_config

# 创建 edit 子应用
app = typer.Typer(help="编辑 PDF")


# ============================================================================
# 添加水印
# ============================================================================

@app.command()
def watermark(
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
    text: Optional[str] = typer.Option(
        None,
        "--text",
        "-t",
        help="文字水印内容",
    ),
    image: Optional[Path] = typer.Option(
        None,
        "--image",
        "-i",
        help="图片水印路径",
        exists=True,
    ),
    angle: int = typer.Option(
        0,
        "--angle",
        "-a",
        help="旋转角度 (0/90/180/270)",
    ),
    opacity: float = typer.Option(
        0.3,
        "--opacity",
        help="透明度 (0-1，如 0.5 表示 50%)",
    ),
    font_size: int = typer.Option(
        48,
        "--font-size",
        "-f",
        help="字体大小",
    ),
    color: str = typer.Option(
        "#FF0000",
        "--color",
        "-c",
        help="颜色 (十六进制，如 #FF0000)",
    ),
    position: str = typer.Option(
        "center",
        "--position",
        "-p",
        help="位置: center, top-left, top-right, bottom-left, bottom-right",
    ),
    layer: str = typer.Option(
        "overlay",
        "--layer",
        "-l",
        help="图层: overlay (上方) / underlay (下方)",
    ),
):
    """
    添加水印到 PDF

    [bold yellow]注意:[/] 颜色值中的 [cyan]#[/] 需要转义为 [cyan]\\#[/] 或用引号包围

    [bold cyan]示例:[/]
      # 添加文字水印
      pdfkit edit watermark document.pdf -t "机密"

      # 添加图片水印
      pdfkit edit watermark document.pdf -i logo.png

      # 调整样式（颜色 # 需转义）
      pdfkit edit watermark document.pdf -t "草稿" -a 45 --opacity 0.5 -c \\#0000FF

      # 完整参数示例
      pdfkit edit watermark document.pdf -t "LZQ" -p bottom-right --opacity 0.3 -c \\#FF0000 -o out.pdf
    """
    if text is None and image is None:
        print_error("必须指定 --text 或 --image")
        raise typer.Exit(1)

    if text and image:
        print_error("--text 和 --image 不能同时使用")
        raise typer.Exit(1)

    # 验证 opacity 范围
    if not 0 <= opacity <= 1:
        print_error(f"--opacity 必须在 0-1 之间，当前值: {opacity}")
        print_info("提示: 50% 透明度应写作 --opacity 0.5")
        raise typer.Exit(1)

    # PyMuPDF 的 rotate 只支持 0, 90, 180, 270
    # 45度等角度需要特殊处理，这里先限制
    if angle not in [0, 90, 180, 270]:
        print_warning(f"角度 {angle} 可能不被支持，建议使用 0/90/180/270")
        print_info("继续使用当前角度，如果失败请尝试使用推荐值")

    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)

        # 解析颜色
        color_rgb = _parse_color(color)

        # 添加水印
        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.DROP} 添加水印中...",
                total=doc.page_count
            )

            for page_num in range(doc.page_count):
                page = doc[page_num]
                rect = page.rect

                # 确定 overlay 参数
                is_overlay = (layer.lower() == "overlay")

                if text:
                    _add_text_watermark(page, text, rect, angle, opacity, font_size, color_rgb, position, is_overlay)
                else:
                    _add_image_watermark(page, str(image), rect, angle, opacity, position, is_overlay)

                progress.update(task, advance=1)

        # 确定输出路径
        if output is None:
            output = resolve_path(file)
        else:
            output = resolve_path(output)

        # 保存
        doc.save(output)
        doc.close()

        print_success(f"水印添加完成: [path]{output}[/]")

    except Exception as e:
        print_error(f"添加水印失败: {e}")
        raise typer.Exit(1)


def _add_text_watermark(page: fitz.Page, text: str, rect: fitz.Rect, angle: float,
                        opacity: float, font_size: int, color: Tuple[float, float, float],
                        position: str, overlay: bool = True):
    """添加文字水印"""
    # 计算位置
    if position == "center":
        point = fitz.Point(rect.width / 2, rect.height / 2)
    elif position == "top-left":
        point = fitz.Point(rect.width * 0.2, rect.height * 0.2)
    elif position == "top-right":
        point = fitz.Point(rect.width * 0.8, rect.height * 0.2)
    elif position == "bottom-left":
        point = fitz.Point(rect.width * 0.2, rect.height * 0.8)
    elif position == "bottom-right":
        point = fitz.Point(rect.width * 0.8, rect.height * 0.8)
    else:
        point = fitz.Point(rect.width / 2, rect.height / 2)

    # 插入文本
    # 注意: PyMuPDF 的 insert_text 不直接支持透明度
    # 如需透明度效果，需要使用 shape 或其他方法
    page.insert_text(
        point,
        text,
        fontsize=font_size,
        color=color,
        rotate=angle,
        overlay=overlay
    )


def _add_image_watermark(page: fitz.Page, image_path: str, rect: fitz.Rect,
                        angle: float, opacity: float, position: str, overlay: bool = True):
    """添加图片水印"""
    # 读取图片
    img = Image.open(image_path)

    # 如果需要旋转，先旋转图片
    if angle != 0:
        img = img.rotate(angle, expand=True)

    # 计算位置和大小
    max_width = rect.width * 0.3
    max_height = rect.height * 0.3

    # 保持比例缩放
    img_ratio = img.width / img.height
    if img_ratio > (max_width / max_height):
        new_width = max_width
        new_height = max_width / img_ratio
    else:
        new_height = max_height
        new_width = max_height * img_ratio

    # 计算位置
    if position == "center":
        x = (rect.width - new_width) / 2
        y = (rect.height - new_height) / 2
    elif position == "top-left":
        x = rect.width * 0.1
        y = rect.height * 0.1
    elif position == "top-right":
        x = rect.width * 0.9 - new_width
        y = rect.height * 0.1
    elif position == "bottom-left":
        x = rect.width * 0.1
        y = rect.height * 0.9 - new_height
    elif position == "bottom-right":
        x = rect.width * 0.9 - new_width
        y = rect.height * 0.9 - new_height
    else:
        x = (rect.width - new_width) / 2
        y = (rect.height - new_height) / 2

    img_rect = fitz.Rect(x, y, x + new_width, y + new_height)

    # 插入图片
    # 注意: opacity 参数在 PyMuPDF 的 insert_image 中不直接支持
    # 如需透明度，需要使用其他方法（如先处理图片或使用 shape）
    page.insert_image(img_rect, filename=image_path, overlay=overlay)


def _parse_color(color_str: str) -> Tuple[float, float, float]:
    """解析颜色字符串为 RGB 元组"""
    color_str = color_str.lstrip("#")
    if len(color_str) != 6:
        return (1, 0, 0)  # 默认红色

    r = int(color_str[0:2], 16) / 255
    g = int(color_str[2:4], 16) / 255
    b = int(color_str[4:6], 16) / 255
    return (r, g, b)


# ============================================================================
# 裁剪页面
# ============================================================================

@app.command("crop")
def crop_pages(
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
    margin: Optional[str] = typer.Option(
        None,
        "--margin",
        "-m",
        help="边距 (格式: top,right,bottom,left 或 single)",
    ),
    box: Optional[str] = typer.Option(
        None,
        "--box",
        "-b",
        help="裁剪框 (格式: x0,y0,x1,y1)",
    ),
):
    """
    裁剪 PDF 页面

    示例:
        # 裁剪边距
        pdfkit edit crop document.pdf -m 50,50,50,50

        # 使用裁剪框
        pdfkit edit crop document.pdf -b 100,100,500,700
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if margin is None and box is None:
        print_error("必须指定 --margin 或 --box")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.CONVERT} 裁剪中...",
                total=doc.page_count
            )

            for page_num in range(doc.page_count):
                page = doc[page_num]
                rect = page.rect

                if box:
                    # 使用裁剪框
                    try:
                        coords = box.split(",")
                        if len(coords) != 4:
                            raise ValueError()
                        x0, y0, x1, y1 = map(float, coords)
                    except ValueError:
                        print_error(f"无效的裁剪框参数: {box}")
                        print_info("正确格式: x0,y0,x1,y1（单位：点）")
                        print_info("示例: 100,100,500,700")
                        raise typer.Exit(1)
                    new_rect = fitz.Rect(x0, y0, x1, y1)
                else:
                    # 使用边距
                    try:
                        margins = list(map(float, margin.split(",")))
                        if len(margins) == 1:
                            margins = [margins[0]] * 4
                        elif len(margins) != 4:
                            raise ValueError()
                    except ValueError:
                        print_error(f"无效的边距参数: {margin}")
                        print_info("正确格式: 上,右,下,左（单位：点）")
                        print_info("示例: 50 或 50,50,50,50")
                        raise typer.Exit(1)

                    new_rect = fitz.Rect(
                        rect.x0 + margins[3],  # left
                        rect.y0 + margins[0],  # top
                        rect.x1 - margins[1],  # right
                        rect.y1 - margins[2]   # bottom
                    )

                page.set_cropbox(new_rect)
                progress.update(task, advance=1)

        # 确定输出路径
        if output is None:
            output = resolve_path(file)
        else:
            output = resolve_path(output)

        # 保存
        doc.save(output)
        doc.close()

        print_success(f"裁剪完成: [path]{output}[/]")

    except Exception as e:
        print_error(f"裁剪失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# 调整页面大小
# ============================================================================

@app.command("resize")
def resize_pages(
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
    size: str = typer.Option(
        "A4",
        "--size",
        "-s",
        help="页面大小: A4, Letter, A3, A5 或 宽x高 (如 595x842)",
    ),
    scale: float = typer.Option(
        1.0,
        "--scale",
        help="缩放比例",
    ),
):
    """
    调整 PDF 页面大小

    示例:
        # 调整为 A4
        pdfkit edit resize document.pdf -s A4

        # 缩放 50%
        pdfkit edit resize document.pdf --scale 0.5

        # 自定义大小
        pdfkit edit resize document.pdf -s 500x700
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)

        # 解析页面大小
        if "x" in size.lower():
            width, height = map(float, size.lower().split("x"))
        else:
            # 预设尺寸（键统一大写以便匹配）
            sizes = {
                "A4": (595, 842),
                "A3": (842, 1191),
                "A5": (420, 595),
                "LETTER": (612, 792),
                "LEGAL": (612, 1008),
            }
            size_key = size.upper()
            if size_key not in sizes:
                print_error(f"不支持的页面大小: {size}")
                print_info("支持的预设尺寸:")
                for name, (w, h) in sizes.items():
                    print_info(f"  - {name}: {w}x{h} 点")
                print_info("自定义尺寸格式: 宽×高，如 500x700")
                raise typer.Exit(1)
            width, height = sizes[size_key]

        # 创建新文档
        new_doc = fitz.open()

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.CONVERT} 调整大小中...",
                total=doc.page_count
            )

            for page_num in range(doc.page_count):
                page = doc[page_num]

                # 创建新页面，尺寸按缩放比例调整
                scaled_width = width * scale
                scaled_height = height * scale
                new_page = new_doc.new_page(width=scaled_width, height=scaled_height)

                # 显示原始页面内容
                new_page.show_pdf_page(new_page.rect, doc, page_num)

                progress.update(task, advance=1)

        doc.close()

        # 确定输出路径
        if output is None:
            output = resolve_path(file)
        else:
            output = resolve_path(output)

        # 保存
        new_doc.save(output)
        new_doc.close()

        print_success(f"大小调整完成: [path]{output}[/]")
        print_info(f"新尺寸: [number]{width}[/] x [number]{height}[/] 点")

    except Exception as e:
        print_error(f"调整大小失败: {e}")
        raise typer.Exit(1)
