"""OCR 识别命令 - 基于阿里百炼 Qwen3-VL"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF
import asyncio

from ..utils.console import (
    console, print_success, print_error, print_info, create_progress, Icons
)
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from ..utils.validators import validate_pdf_file, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import resolve_path
from ..utils.config import get_config_value
from ..core.ocr_handler import (
    QwenVLOCR, OCRModel, OutputFormat, Region, pdf_page_to_image
)

# 创建 ocr 子应用
app = typer.Typer(help="OCR 文字识别 (基于阿里百炼 Qwen3-VL)")


# ============================================================================
# 异步处理辅助函数
# ============================================================================

async def _process_ocr_async(
    doc: fitz.Document,
    page_list: list[int],
    ocr: "QwenVLOCR",
    dpi: int,
    prompt: Optional[str],
    output_format: "OutputFormat",
) -> list[dict]:
    """
    异步处理多个页面，带并发控制、进度反馈和错误处理

    改进点：
    1. 使用Semaphore限制并发数（默认10），避免触发API限流
    2. 使用return_exceptions=True，单页异常不取消全批
    3. 确保页面渲染在获取信号量后才进行，控制内存
    4. 实时进度条显示（带转圈图标）
    5. 自动清理异步客户端资源
    """
    # 获取配置的并发数（默认10）
    max_concurrent = get_config_value("ocr.concurrency", 10)

    # 创建信号量控制并发数
    semaphore = asyncio.Semaphore(max_concurrent)

    # 进度跟踪
    total_count = len(page_list)
    progress_lock = asyncio.Lock()
    completed_count = 0

    # 创建自定义进度条（支持异步更新）
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TextColumn("({task.completed}/{task.total})"),
        console=console,
        transient=False,  # 完成后保留显示
    )

    task_id = progress.add_task(
        f"[cyan]{Icons.SEARCH}[/] OCR 识别中 (异步模式)...",
        total=total_count
    )

    # 使用Live显示进度条
    live = Live(progress, console=console)

    async def update_progress():
        """更新进度"""
        nonlocal completed_count
        async with progress_lock:
            completed_count += 1
            progress.update(task_id, completed=completed_count)

    # 包装任务，在完成后更新计数
    async def wrapped_task(page_num: int):
        result = await ocr.ocr_page_async(doc, page_num, dpi, prompt, output_format, semaphore)
        await update_progress()
        return result

    try:
        # 启动Live显示
        live.start()

        # 创建所有任务
        tasks = [
            wrapped_task(page_num)
            for page_num in page_list
        ]

        # 并发执行所有任务
        results_with_page_nums = await asyncio.gather(*tasks, return_exceptions=True)

        # 停止Live显示
        live.stop()

        # 处理结果：分离成功和失败
        successful_results = []
        failed_pages = []

        for i, result in enumerate(results_with_page_nums):
            if isinstance(result, Exception):
                page_num = page_list[i]
                failed_pages.append((page_num + 1, str(result)))
            elif isinstance(result, tuple) and len(result) == 2:
                successful_results.append(result)

        # 报告失败的页面
        if failed_pages:
            console.print()
            print_error(f"有 [number]{len(failed_pages)}[/] 页识别失败:")
            for page_num, error in failed_pages[:5]:
                console.print(f"  第 {page_num} 页: {error}", style="dim")
            if len(failed_pages) > 5:
                console.print(f"  ... 及其他 {len(failed_pages) - 5} 页", style="dim")

        # 按页面号排序
        successful_results.sort(key=lambda x: x[0])

        results = [
            {"page": page_num + 1, "text": text}
            for page_num, text in successful_results
        ]

        return results

    finally:
        # 清理异步客户端资源
        await ocr.close_async_client()
        if live.is_started:
            live.stop()


# ============================================================================
# OCR 识别命令
# ============================================================================

@app.command()
def recognize(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    model: OCRModel = typer.Option(
        OCRModel.FLASH,
        "--model",
        "-m",
        help="模型选择: flash(快速)、plus(精准) 或 ocr(专用OCR，适合结构化文本提取)",
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        "-p",
        help="页面范围 (如: 1-5,8,10-15)",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.TEXT,
        "--format",
        "-f",
        help="输出格式: text, md, json",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    dpi: int = typer.Option(
        300,
        "--dpi",
        help="图片转换 DPI",
    ),
    prompt: Optional[str] = typer.Option(
        None,
        "--prompt",
        help="自定义识别提示词",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="DASHSCOPE_API_KEY",
        help="API Key",
    ),
    region: Region = typer.Option(
        Region.BEIJING,
        "--region",
        help="API 地域",
    ),
    async_mode: bool = typer.Option(
        False,
        "--async",
        "-a",
        help="启用异步处理模式（并发处理页面，可显著提升速度）",
    ),
):
    """
    对 PDF 进行 OCR 文字识别

    使用阿里百炼 Qwen3-VL 视觉语言模型进行识别。

    示例:
        # 基础 OCR (结果输出到终端)
        pdfkit ocr recognize document.pdf

        # 保存识别结果到文件
        pdfkit ocr recognize document.pdf -o result.txt

        # 输出为 Markdown 格式
        pdfkit ocr recognize document.pdf -f md -o result.md

        # 输出为 JSON 格式
        pdfkit ocr recognize document.pdf -f json -o result.json

        # 使用更精准的 plus 模型
        pdfkit ocr recognize document.pdf -m plus

        # 使用专用 OCR 模型 (适合结构化文本提取，如票据、表单等)
        pdfkit ocr recognize document.pdf -m ocr

        # 只识别前5页
        pdfkit ocr recognize document.pdf -p 1-5 -o result.txt

        # 使用异步模式加速处理 (多页并发识别)
        pdfkit ocr recognize document.pdf --async -o result.txt

    注意:
        如果不指定 -o/--output 参数，结果将直接输出到终端
        使用 > 重定向也可保存: pdfkit ocr recognize document.pdf > result.txt
        异步模式 (--async) 会并发处理多个页面，可显著提升处理速度
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if not require_unlocked_pdf(file, "OCR 识别"):
        raise typer.Exit(1)

    try:
        # 初始化 OCR 处理器
        ocr = QwenVLOCR(api_key=api_key, model=model, region=region)
        print_info(f"使用模型: [command]{ocr.model_name}[/]")

        # 打开 PDF
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 解析页面范围
        if pages:
            page_list = validate_page_range(pages, total_pages)
        else:
            page_list = list(range(total_pages))

        print_info(f"待识别页数: [number]{len(page_list)}[/] / {total_pages} 页")

        if async_mode:
            print_info(f"模式: [info]异步处理[/] (并发识别 {len(page_list)} 页)")

        # OCR 识别
        if async_mode:
            # 异步处理模式
            results = asyncio.run(_process_ocr_async(
                doc, page_list, ocr, dpi, prompt, output_format
            ))
        else:
            # 同步处理模式
            results = []

            with create_progress() as progress:
                task = progress.add_task(
                    f"{Icons.SEARCH} OCR 识别中...",
                    total=len(page_list)
                )

                for page_num in page_list:
                    page = doc[page_num]

                    # 将页面渲染为图片
                    img = pdf_page_to_image(page, dpi)

                    # OCR 识别
                    text = ocr.ocr_image(
                        img,
                        prompt=prompt,
                        output_format=output_format,
                    )

                    results.append({
                        "page": page_num + 1,
                        "text": text,
                    })

                    progress.update(task, advance=1)

        doc.close()

        # 输出结果
        _output_results(results, output_format, output)

        print_success(f"OCR 识别完成！共识别 [number]{len(page_list)}[/] 页")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"OCR 识别失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# 表格提取
# ============================================================================

@app.command("table")
def extract_table(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        "-p",
        help="页面范围",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    model: OCRModel = typer.Option(
        OCRModel.PLUS,
        "--model",
        "-m",
        help="模型选择 (表格建议用 plus)",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="DASHSCOPE_API_KEY",
    ),
):
    """
    从 PDF 中提取表格数据

    示例:
        # 提取表格 (结果输出到终端)
        pdfkit ocr table document.pdf

        # 保存表格到文件
        pdfkit ocr table document.pdf -o tables.md

        # 只处理第5-10页
        pdfkit ocr table document.pdf -p 5-10 -o tables.md

    注意:
        如果不指定 -o/--output 参数，结果将直接输出到终端
        使用 > 重定向也可保存: pdfkit ocr table document.pdf > tables.md
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        ocr = QwenVLOCR(api_key=api_key, model=model)

        doc = fitz.open(file)
        total_pages = doc.page_count

        if pages:
            page_list = validate_page_range(pages, total_pages)
        else:
            page_list = list(range(total_pages))

        results = []

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.TABLE} 提取表格中...",
                total=len(page_list)
            )

            for page_num in page_list:
                page = doc[page_num]
                img = pdf_page_to_image(page)

                text = ocr.ocr_table(img)
                results.append({
                    "page": page_num + 1,
                    "text": text,
                })

                progress.update(task, advance=1)

        doc.close()

        # 输出结果
        _output_results(results, OutputFormat.TEXT, output)

        print_success(f"表格提取完成！共处理 [number]{len(page_list)}[/] 页")

    except Exception as e:
        print_error(f"表格提取失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# 版面分析
# ============================================================================

@app.command("layout")
def analyze_layout(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        "-p",
        help="页面范围",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="DASHSCOPE_API_KEY",
    ),
):
    """
    分析 PDF 文档的版面结构

    示例:
        # 分析版面 (结果输出到终端)
        pdfkit ocr layout document.pdf

        # 保存版面分析到 JSON 文件
        pdfkit ocr layout document.pdf -o layout.json

    注意:
        layout 命令默认输出 JSON 格式的版面分析结果
        如果不指定 -o/--output 参数，结果将直接输出到终端
        使用 > 重定向也可保存: pdfkit ocr layout document.pdf > layout.json
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        ocr = QwenVLOCR(api_key=api_key)

        doc = fitz.open(file)
        total_pages = doc.page_count

        if pages:
            page_list = validate_page_range(pages, total_pages)
        else:
            page_list = list(range(total_pages))

        results = []

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.SEARCH} 分析版面中...",
                total=len(page_list)
            )

            for page_num in page_list:
                page = doc[page_num]
                img = pdf_page_to_image(page)

                text = ocr.ocr_layout(img)
                results.append({
                    "page": page_num + 1,
                    "text": text,
                })

                progress.update(task, advance=1)

        doc.close()

        # 输出结果 (JSON 格式)
        import json
        content = json.dumps(results, ensure_ascii=False, indent=2)

        if output:
            output.write_text(content, encoding="utf-8")
            print_success(f"版面分析完成: [path]{output}[/]")
        else:
            from ..utils.console import console as pdfkit_console
            pdfkit_console.print_json(content)

    except Exception as e:
        print_error(f"版面分析失败: {e}")
        raise typer.Exit(1)


def _output_results(results: list, output_format: OutputFormat, output_path: Optional[Path]):
    """输出识别结果"""
    if output_format == OutputFormat.JSON:
        import json
        content = json.dumps(results, ensure_ascii=False, indent=2)
    else:
        content = "\n\n".join([
            f"--- 第 {r['page']} 页 ---\n{r['text']}"
            for r in results
        ])

    if output_path:
        output_path.write_text(content, encoding="utf-8")
        print_success(f"结果已保存到: [path]{output_path}[/]")
    else:
        if output_format == OutputFormat.JSON:
            from ..utils.console import console as pdfkit_console
            pdfkit_console.print_json(content)
        else:
            console.print(content)
