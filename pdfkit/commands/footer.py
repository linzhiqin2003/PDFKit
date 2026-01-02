"""PDF 页脚命令"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF
from datetime import datetime

from ..utils.console import (
    console, print_success, print_error, print_info, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import resolve_path

# 创建 footer 子应用
app = typer.Typer(help="添加页脚")


@app.command()
def add(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    text: str = typer.Option(
        ...,
        "--text",
        "-t",
        help="页脚文字（支持变量: {page}, {total}, {date}, {time}）",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    font_size: int = typer.Option(
        10,
        "--font-size",
        "-f",
        help="字体大小",
    ),
    align: str = typer.Option(
        "center",
        "--align",
        "-a",
        help="对齐方式: left, center, right",
    ),
    margin_bottom: float = typer.Option(
        18,
        "--margin-bottom",
        help="底部边距（点）",
    ),
    range_str: Optional[str] = typer.Option(
        None,
        "--range",
        "-r",
        help="页面范围",
    ),
):
    """
    添加页脚到 PDF

    支持的变量:
        {page}  - 当前页码
        {total} - 总页数
        {date}  - 当前日期
        {time}  - 当前时间

    示例:
        # 添加页码
        pdfkit footer add document.pdf -t "第 {page} / {total} 页"

        # 添加带日期的页脚
        pdfkit footer add document.pdf -t "打印时间: {date} {time}"

        # 右对齐
        pdfkit footer add document.pdf -t "{page}" -a right
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if align not in ("left", "center", "right"):
        print_error("对齐方式必须是 left, center 或 right")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 确定要添加页脚的页面
        if range_str:
            page_list = validate_page_range(range_str, total_pages)
        else:
            page_list = list(range(total_pages))

        # 准备变量
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        with create_progress() as progress:
            task = progress.add_task(
                f"添加页脚中...",
                total=len(page_list)
            )

            for page_num in page_list:
                page = doc[page_num]
                rect = page.rect

                # 替换变量
                page_text = text.format(
                    page=page_num + 1,
                    total=total_pages,
                    date=date_str,
                    time=time_str
                )

                # textbox 高度
                tb_height = font_size * 2

                # y 坐标：从页面底部往上
                y = rect.y1 - margin_bottom - tb_height

                # 计算 textbox 区域（页脚在底部，横跨页面宽度）
                if align == "left":
                    tb_rect = fitz.Rect(rect.x0 + 36, y, rect.x1 - 36, y + tb_height)
                elif align == "center":
                    tb_rect = fitz.Rect(rect.x0 + 36, y, rect.x1 - 36, y + tb_height)
                else:  # right
                    tb_rect = fitz.Rect(rect.x0 + 36, y, rect.x1 - 36, y + tb_height)

                # 设置对齐方式
                align_flag = fitz.TEXT_ALIGN_LEFT
                if align == "center":
                    align_flag = fitz.TEXT_ALIGN_CENTER
                elif align == "right":
                    align_flag = fitz.TEXT_ALIGN_RIGHT

                # 插入文本
                rc = page.insert_textbox(
                    tb_rect,
                    page_text,
                    fontsize=font_size,
                    fontname="helv",  # 使用内置字体
                    color=(0.3, 0.3, 0.3),
                    align=align_flag,
                )

                # rc < 0 表示文本不适合 textbox
                if rc < 0:
                    tb_rect = fitz.Rect(rect.x0 + 18, y, rect.x1 - 18, y + tb_height * 2)
                    page.insert_textbox(
                        tb_rect,
                        page_text,
                        fontsize=font_size,
                        fontname="helv",
                        color=(0.3, 0.3, 0.3),
                        align=align_flag,
                    )

                progress.update(task, advance=1)

        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}_footer{file.suffix}")
        else:
            output = resolve_path(output)

        # 保存
        doc.save(output, deflate=True)
        doc.close()

        print_success(f"页脚添加完成: [path]{output}[/]")
        print_info(f"页数: [number]{len(page_list)}[/] 页")
        print_info(f"页脚内容: [text]{text}[/]")

    except Exception as e:
        print_error(f"添加页脚失败: {e}")
        raise typer.Exit(1)
