"""OCR 识别命令 - 基于阿里百炼 Qwen3-VL"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF
import asyncio
import sys
import signal

from ..utils.console import (
    console, print_success, print_error, print_info, print_warning, create_progress, Icons,
    print_structured_error, print_security_warning
)
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from ..utils.validators import validate_pdf_file, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import resolve_path, generate_ocr_output_paths
from ..utils.config import get_config_value
from ..core.ocr_handler import (
    QwenVLOCR, OCRModel, OutputFormat, Region, pdf_page_to_image,
    build_prompt_with_images, DEFAULT_PROMPTS
)

# 创建 ocr 子应用
app = typer.Typer(help="OCR 文字识别 (基于阿里百炼 Qwen3-VL)")


# ============================================================================
# 参数验证辅助函数
# ============================================================================

def validate_ocr_model(value: str) -> OCRModel:
    """验证 OCR 模型参数，提供中文错误提示"""
    try:
        return OCRModel(value)
    except ValueError:
        print_structured_error(
            title=f"无效的模型: {value}",
            error_message="指定的 OCR 模型不存在",
            causes=[
                "模型名称拼写错误",
                "该模型暂不支持"
            ],
            suggestions=[
                "flash: 快速模式（推荐，速度快）",
                "plus: 高精度模式（精度更高，约30%提升）",
                "ocr: 专用OCR模式（适合结构化文本，如票据、表单）"
            ]
        )
        raise typer.Exit(1)


def validate_output_format(value: str) -> OutputFormat:
    """验证输出格式参数，提供中文错误提示"""
    try:
        return OutputFormat(value)
    except ValueError:
        print_structured_error(
            title=f"无效的输出格式: {value}",
            error_message="指定的输出格式不存在",
            causes=[
                "格式名称拼写错误",
                "该格式暂不支持"
            ],
            suggestions=[
                "text: 纯文本格式（默认）",
                "md: Markdown 格式（保留结构）",
                "json: JSON 格式（便于程序处理）"
            ]
        )
        raise typer.Exit(1)


def validate_region(value: str) -> Region:
    """验证地域参数，提供中文错误提示"""
    try:
        return Region(value)
    except ValueError:
        print_structured_error(
            title=f"无效的地域: {value}",
            error_message="指定的 API 地域不存在",
            causes=[
                "地域名称拼写错误",
                "该地域暂不支持"
            ],
            suggestions=[
                "beijing: 北京（国内推荐，延迟低）",
                "singapore: 新加坡（海外推荐）"
            ]
        )
        raise typer.Exit(1)


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
    pages_to_process: int,
    page_images_map: dict[int, list[dict]] | None = None,
) -> tuple[list[dict], bool]:
    """
    异步处理多个页面，带并发控制、进度反馈和错误处理

    改进点：
    1. 使用Semaphore限制并发数（默认10），避免触发API限流
    2. 使用return_exceptions=True，单页异常不取消全批
    3. 确保页面渲染在获取信号量后才进行，控制内存
    4. 实时进度条显示（带转圈图标）
    5. 自动清理异步客户端资源
    6. 支持图像融合 OCR（通过 page_images_map）

    Args:
        page_images_map: 页面图像映射 {page_num: [image_info]}，用于图像融合 OCR

    Returns:
        (results, interrupted): 结果列表和是否被中断的标志
    """
    # 获取配置的并发数（默认10）
    max_concurrent = get_config_value("ocr.concurrency", 10)

    # 创建信号量控制并发数
    semaphore = asyncio.Semaphore(max_concurrent)

    # 进度跟踪
    total_count = len(page_list)
    progress_lock = asyncio.Lock()
    completed_count = 0
    interrupted = False

    # 创建自定义进度条（使用 transient=True 避免重复显示）
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TextColumn("({task.completed}/{task.total})"),
        console=console,
        transient=True,  # 中断或完成后不保留
    )

    task_id = progress.add_task(
        f"[cyan]{Icons.SEARCH}[/] OCR 识别中 (异步模式)... (剩余 {pages_to_process}/{pages_to_process} 页)",
        total=total_count
    )

    # 使用Live显示进度条
    live = Live(progress, console=console, transient=True)

    async def update_progress():
        """更新进度"""
        nonlocal completed_count
        async with progress_lock:
            completed_count += 1
            remaining = pages_to_process - completed_count
            progress.update(
                task_id,
                completed=completed_count,
                description=f"[cyan]{Icons.SEARCH}[/] OCR 识别中 (异步模式)... (剩余 {remaining}/{pages_to_process} 页)"
            )

    # 包装任务，在完成后更新计数
    async def wrapped_task(page_num: int):
        # 获取该页的图像信息（如果有）
        page_images = page_images_map.get(page_num) if page_images_map else None
        result = await ocr.ocr_page_async(doc, page_num, dpi, prompt, output_format, semaphore, page_images)
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

        return results, False

    except (KeyboardInterrupt, asyncio.CancelledError):
        # 用户中断，停止 Live 显示
        interrupted = True
        if live.is_started:
            live.stop()
        return [], True
    finally:
        # 清理异步客户端资源
        await ocr.close_async_client()


# ============================================================================
# 图像提取辅助函数
# ============================================================================

def _extract_images_traditional(
    doc: fitz.Document,
    page_list: list[int],
    images_dir: Path,
) -> dict[int, list[dict]]:
    """
    传统图像提取（默认方案）
    
    优点：极快（秒级）、免费（本地处理）、原始质量
    缺点：只能提取嵌入的图像对象，无法处理扫描件，无类型识别
    
    Args:
        doc: PDF 文档对象
        page_list: 页面列表（0-based）
        images_dir: 图像输出目录
        
    Returns:
        页面图像映射 {page_num: [image_info]}
    """
    page_images_map = {}
    global_image_counter = 0
    
    for page_num in page_list:
        page = doc[page_num]
        image_list = page.get_images(full=True)
        
        if not image_list:
            continue
        
        page_images = []
        for img_index, img in enumerate(image_list):
            xref = img[0]
            
            try:
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue
                    
                # 检查图像数据
                image_data = base_image.get("image")
                if not image_data:
                    continue
                
                # 检查尺寸（跳过太小的图像，如图标）
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)
                if width < 50 or height < 50:
                    continue
                
                # 确定文件扩展名
                ext = base_image.get("ext", "png")
                if ext == "jpeg":
                    ext = "jpg"
                
                # 保存图像
                global_image_counter += 1
                filename = f"page_{page_num + 1}_img_{global_image_counter}.{ext}"
                output_path = images_dir / filename
                
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                page_images.append({
                    "file": f"images/{filename}",
                    "type": "image",  # 传统方法无类型识别
                    "description": "",
                    "bbox": [],
                    "method": "extract",
                    "size": [width, height],
                })
                
            except Exception:
                # 跳过无法提取的图像
                continue
        
        if page_images:
            page_images_map[page_num] = page_images
    
    return page_images_map


def _extract_images_ai(
    doc: fitz.Document,
    page_list: list[int],
    images_dir: Path,
    dpi: int,
    include_types: list[str] | None,
    api_key: str | None,
    pages_to_process: int,
) -> dict[int, list[dict]]:
    """
    AI 图像提取（备选方案）
    
    优点：智能识别、支持扫描件、类型分类
    缺点：较慢（分钟级）、收费（API 调用）、渲染质量
    
    Args:
        doc: PDF 文档对象
        page_list: 页面列表（0-based）
        images_dir: 图像输出目录
        dpi: 渲染 DPI
        include_types: 图像类型过滤
        api_key: API Key
        pages_to_process: 待处理页数（用于进度显示）
        
    Returns:
        页面图像映射 {page_num: [image_info]}
    """
    from ..ai.image_extractor import AIImageExtractor
    from ..ai.image_detection_prompt import normalize_bbox_to_pixels
    from PIL import Image
    from rich.progress import TimeElapsedColumn
    
    # 使用 plus 模型进行图像检测（精度更高）
    extractor = AIImageExtractor(model="plus", api_key=api_key)
    
    page_images_map = {}
    total_images_extracted = 0
    image_counter = 0
    
    # 创建进度条
    img_progress = Progress(
        SpinnerColumn(style="warning"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(
            complete_style="progress.bar.complete",
            finished_style="warning",
            bar_width=None,
        ),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        expand=True,
        transient=True,
    )
    
    try:
        img_progress.start()
        img_task = img_progress.add_task(
            f"{Icons.IMAGE} AI 检测图像中... (剩余 {pages_to_process}/{pages_to_process} 页)",
            total=pages_to_process
        )
        
        for idx, page_num in enumerate(page_list):
            page = doc[page_num]
            
            # 渲染页面
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            page_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # AI 检测图像
            detected = extractor._detect_images(page_image, include_types, None)
            
            page_images = []
            for img_info in detected:
                bbox = img_info.get("bbox", [])
                if not bbox:
                    continue
                
                # 转换坐标
                pixel_bbox = normalize_bbox_to_pixels(
                    bbox, pix.width, pix.height, padding=5
                )
                
                # 检查尺寸
                width = pixel_bbox[2] - pixel_bbox[0]
                height = pixel_bbox[3] - pixel_bbox[1]
                if width < 50 or height < 50:
                    continue
                
                # 裁切并保存
                image_counter += 1
                total_images_extracted += 1
                filename = f"page_{page_num + 1}_img_{image_counter}.png"
                output_file = images_dir / filename
                
                cropped = page_image.crop(pixel_bbox)
                cropped.save(output_file, "PNG")
                
                # 记录图像信息
                page_images.append({
                    "file": f"images/{filename}",
                    "type": img_info.get("type", "unknown"),
                    "description": img_info.get("description", ""),
                    "bbox": list(pixel_bbox),
                    "method": "ai",
                })
            
            if page_images:
                page_images_map[page_num] = page_images
            
            # 更新进度
            remaining = pages_to_process - idx - 1
            img_progress.update(
                img_task, 
                advance=1,
                description=f"{Icons.IMAGE} AI 检测图像中... (剩余 {remaining}/{pages_to_process} 页)"
            )
            
    finally:
        img_progress.stop()
    
    return page_images_map, total_images_extracted


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
    model: str = typer.Option(
        "flash",
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
    output_format: str = typer.Option(
        "text",
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
    region: str = typer.Option(
        "beijing",
        "--region",
        help="API 地域",
    ),
    async_mode: bool = typer.Option(
        False,
        "--async",
        "-a",
        help="启用异步处理模式（并发处理页面，可显著提升速度）",
    ),
    with_images: bool = typer.Option(
        False,
        "--with-images",
        "-i",
        help="同时提取图像并在 Markdown 中引用（仅对 md 格式有效）",
    ),
    image_method: str = typer.Option(
        "extract",
        "--image-method",
        help="图像提取方法: extract(传统快速,免费,默认) 或 ai(智能精准,收费)",
    ),
    image_types: Optional[str] = typer.Option(
        None,
        "--image-types",
        help="图像类型过滤（仅 --image-method ai 时有效）: chart,photo,diagram,table,illustration,logo,screenshot",
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

        # OCR 并提取图像（默认使用传统快速方法）
        pdfkit ocr recognize document.pdf -f md --with-images -o result.md

        # 使用 AI 智能提取图像（支持扫描件，精准但收费）
        pdfkit ocr recognize document.pdf -f md --with-images --image-method ai -o result.md

        # AI 提取 + 类型过滤
        pdfkit ocr recognize document.pdf -f md --with-images --image-method ai --image-types chart,table -o result.md

    注意:
        如果不指定 -o/--output 参数，结果将直接输出到终端
        使用 > 重定向也可保存: pdfkit ocr recognize document.pdf > result.txt
        异步模式 (--async) 会并发处理多个页面，可显著提升处理速度
        --with-images 选项仅在 -f md 格式下有效
        --image-method extract: 快速免费，适合嵌入式图像的 PDF
        --image-method ai: 智能精准，适合扫描件或复杂布局
    """
    # 验证参数
    model_enum = validate_ocr_model(model)
    format_enum = validate_output_format(output_format)
    region_enum = validate_region(region)

    # 验证 --with-images 参数
    if with_images and format_enum != OutputFormat.MARKDOWN:
        print_warning("--with-images 选项仅在 -f md 格式下有效，已自动切换为 markdown 格式")
        format_enum = OutputFormat.MARKDOWN
    
    # 解析图像类型过滤
    include_types = None
    if image_types:
        include_types = [t.strip() for t in image_types.split(",") if t.strip()]
        valid_types = {"chart", "photo", "diagram", "table", "illustration", "logo", "screenshot"}
        invalid = [t for t in include_types if t not in valid_types]
        if invalid:
            print_warning(f"忽略无效的图像类型: {', '.join(invalid)}")
            include_types = [t for t in include_types if t in valid_types]

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

    if not require_unlocked_pdf(file, "OCR 识别"):
        raise typer.Exit(1)

    # API Key 安全警告
    if api_key and "--api-key" in str(sys.argv):
        print_security_warning(
            operation="命令行传递 API Key",
            risk_level="medium",
            details="您在命令行中直接传递 API Key，这可能会被 shell 历史记录记录。",
            risks=[
                "API Key 可能被保存到 ~/.bash_history 或 ~/.zsh_history",
                "其他用户可能通过 ps 命令看到您的 API Key",
                "API Key 可能被日志系统记录"
            ],
            confirmation_required=False
        )

    try:
        # 初始化 OCR 处理器
        ocr = QwenVLOCR(api_key=api_key, model=model_enum, region=region_enum)
        print_info(f"使用模型: [command]{ocr.model_name}[/]")

        # 打开 PDF
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 解析页面范围
        if pages:
            page_list = validate_page_range(pages, total_pages)
        else:
            page_list = list(range(total_pages))

        pages_to_process = len(page_list)
        print_info(f"待识别页数: [number]{pages_to_process}[/] 页")
        if pages_to_process < total_pages:
            print_info(f"PDF 总页数: [number]{total_pages}[/] 页 (识别指定范围)")

        if async_mode:
            print_info(f"模式: [info]异步处理[/] (并发识别 {pages_to_process} 页)")

        # ====================================================================
        # 确定输出路径（文件夹组织结构）
        # ====================================================================
        output_file_path, images_dir = generate_ocr_output_paths(
            input_file=file,
            output_spec=Path(output) if output else None,
            output_format=format_enum,
        )

        # ====================================================================
        # 图像预提取阶段（如果启用 --with-images）
        # ====================================================================
        page_images_map = {}  # 页面号 -> 图像列表

        if with_images:
            # 验证 image_method 参数
            if image_method not in ("extract", "ai"):
                print_structured_error(
                    title=f"无效的图像提取方法: {image_method}",
                    error_message="指定的图像提取方法不存在",
                    causes=["方法名称拼写错误"],
                    suggestions=[
                        "extract: 传统快速方法（默认，免费）",
                        "ai: AI 智能方法（精准，收费）"
                    ]
                )
                raise typer.Exit(1)

            # 如果使用传统方法但指定了 image_types，给出提示
            if image_method == "extract" and image_types:
                print_warning("--image-types 参数仅在 --image-method ai 时有效，已忽略")

            # 创建 images 目录
            images_dir.mkdir(parents=True, exist_ok=True)
            
            # 根据方法选择提取方式
            if image_method == "extract":
                # 传统方法：快速、免费
                print_info(f"使用传统方法提取图像（快速免费）...")
                page_images_map = _extract_images_traditional(doc, page_list, images_dir)
                total_images = sum(len(imgs) for imgs in page_images_map.values())
                
                if total_images > 0:
                    print_success(f"图像提取完成！共提取 [number]{total_images}[/] 个图像")
                else:
                    print_info("传统方法未找到嵌入图像")
                    print_info("提示: 如果是扫描件 PDF，可尝试 [command]--image-method ai[/] 进行智能提取")
                    
            else:
                # AI 方法：智能、收费
                print_info(f"使用 AI 方法提取图像（智能精准，将产生 API 费用）...")
                if include_types:
                    print_info(f"图像类型过滤: [info]{', '.join(include_types)}[/]")
                
                page_images_map, total_images = _extract_images_ai(
                    doc, page_list, images_dir, dpi, include_types, api_key, pages_to_process
                )
                
                if total_images > 0:
                    print_success(f"AI 图像提取完成！共提取 [number]{total_images}[/] 个图像")
                else:
                    print_info("AI 方法未检测到图像")

        # ====================================================================
        # OCR 识别阶段
        # ====================================================================
        interrupted = False
        if async_mode:
            # 异步处理模式（现已支持图像融合）
            results, interrupted = asyncio.run(_process_ocr_async(
                doc, page_list, ocr, dpi, prompt, format_enum, pages_to_process,
                page_images_map if with_images else None
            ))
            if interrupted:
                doc.close()
                print_warning(f"{Icons.WARNING} OCR 识别中... [yellow]进度中断...[/]")
                raise typer.Exit(130)
        
        if not async_mode:
            # 同步处理模式
            results = []
            # 使用 transient=True 的进度条，避免中断时重复显示
            from rich.progress import TimeElapsedColumn
            progress = Progress(
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
                transient=True,  # 中断后消失，避免重复显示
            )
            task = None

            try:
                progress.start()
                task = progress.add_task(
                    f"{Icons.SEARCH} OCR 识别中... (剩余 {pages_to_process}/{pages_to_process} 页)",
                    total=pages_to_process
                )

                for idx, page_num in enumerate(page_list):
                    page = doc[page_num]

                    # 将页面渲染为图片
                    img = pdf_page_to_image(page, dpi)

                    # 构建提示词（如果有图像信息，则融合）
                    current_prompt = prompt
                    if with_images and page_num in page_images_map:
                        page_images = page_images_map[page_num]
                        base_prompt = prompt or DEFAULT_PROMPTS.get("markdown_with_images", DEFAULT_PROMPTS["markdown"])
                        current_prompt = build_prompt_with_images(base_prompt, page_images, "images")

                    # OCR 识别
                    text = ocr.ocr_image(
                        img,
                        prompt=current_prompt,
                        output_format=format_enum,
                    )

                    results.append({
                        "page": page_num + 1,
                        "text": text,
                    })

                    # 更新进度，显示剩余页数
                    remaining = pages_to_process - idx - 1
                    progress.update(task, advance=1, description=f"{Icons.SEARCH} OCR 识别中... (剩余 {remaining}/{pages_to_process} 页)")

            except KeyboardInterrupt:
                # 用户中断
                interrupted = True
            finally:
                progress.stop()

            if interrupted:
                doc.close()
                print_warning(f"{Icons.WARNING} OCR 识别中... [yellow]进度中断...[/]")
                raise typer.Exit(130)

        doc.close()

        # 输出结果
        _output_results(results, format_enum, output_file_path)

        # 完成消息
        print_success(f"OCR 识别完成！共识别 [number]{len(results)}[/] 页")
        print_info(f"结果文件: [path]{output_file_path}[/]")
        if with_images and page_images_map:
            print_info(f"图像文件夹: [path]{images_dir}[/]")

    except KeyboardInterrupt:
        # 中断已在内部处理
        raise typer.Exit(130)
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
        help="输出文件夹路径（将在文件夹内创建与 PDF 同名的输出文件）",
    ),
    model: str = typer.Option(
        "plus",
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
    # 验证参数
    model_enum = validate_ocr_model(model)

    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        ocr = QwenVLOCR(api_key=api_key, model=model_enum)

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

        # 确定输出路径
        output_file_path, _ = generate_ocr_output_paths(
            input_file=file,
            output_spec=Path(output) if output else None,
            output_format=OutputFormat.TEXT,
        )

        # 输出结果
        _output_results(results, OutputFormat.TEXT, output_file_path)

        print_success(f"表格提取完成！共处理 [number]{len(page_list)}[/] 页")
        if output:
            print_info(f"结果文件: [path]{output_file_path}[/]")

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
        help="输出文件夹路径（将在文件夹内创建与 PDF 同名的 JSON 文件）",
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

        # 确定输出路径
        output_file_path, _ = generate_ocr_output_paths(
            input_file=file,
            output_spec=Path(output) if output else None,
            output_format=OutputFormat.JSON,
        )

        # 输出结果 (JSON 格式)
        import json
        content = json.dumps(results, ensure_ascii=False, indent=2)

        if output:
            output_file_path.write_text(content, encoding="utf-8")
            print_success(f"版面分析完成！共处理 [number]{len(page_list)}[/] 页")
            print_info(f"结果文件: [path]{output_file_path}[/]")
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
    elif output_format == OutputFormat.MARKDOWN:
        # Markdown 格式：使用 HTML 注释作为分隔符，不影响渲染
        # 只有多个页面时才添加分隔符
        if len(results) == 1:
            content = results[0]['text']
        else:
            parts = []
            for r in results:
                # 使用 HTML 注释标记页码，不影响 Markdown 渲染
                parts.append(f"<!-- Page {r['page']} -->\n\n{r['text']}")
            content = "\n\n---\n\n".join(parts)  # 用 Markdown 分隔线分隔各页
    else:
        # TEXT 格式：使用明显的分隔符
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


# ============================================================================
# 提示词查看
# ============================================================================

@app.command("prompts")
def show_prompts(
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="显示指定模型的提示词（flash/plus/ocr）",
    ),
):
    """
    显示当前使用的 OCR 提示词配置

    示例:
        # 查看通用提示词
        pdfkit ocr prompts

        # 查看 plus 模型的提示词
        pdfkit ocr prompts -m plus

    提示:
        配置文件位置: ~/.pdfkit/config.yaml (macOS/Linux)
                         %APPDATA%\\pdfkit\\config.yaml (Windows)
    """
    from ..utils.config import CONFIG_FILE
    from ..core.ocr_handler import DEFAULT_PROMPTS

    config = load_config()
    ocr_config = config.get("ocr", {})
    config_prompts = ocr_config.get("prompts", {})

    console.print(f"\n[info]配置文件位置:[/] [path]{CONFIG_FILE}[/]\n")

    if model:
        # 显示特定模型的提示词
        if model not in ["flash", "plus", "ocr"]:
            print_error(f"无效的模型: {model}（可选: flash, plus, ocr）")
            raise typer.Exit(1)

        model_specific = config_prompts.get("models", {}).get(model, {})
        if model_specific:
            console.print(f"[info]{model.upper()} 模型专用提示词:[/]\n")
            for fmt, prompt in model_specific.items():
                console.print(f"  [info]{fmt}:[/]")
                if len(prompt) > 100:
                    console.print(f"    {prompt[:100]}...")
                else:
                    console.print(f"    {prompt}")
                console.print()
        else:
            console.print(f"[info]{model.upper()} 模型使用通用提示词（无特定覆盖）[/]")
            console.print(f"[dim]提示: 编辑 {CONFIG_FILE} 添加 models.{model} 配置[/]\n")
    else:
        # 显示通用提示词
        console.print(f"[info]通用提示词（所有模型共用）:[/]\n")
        for fmt, prompt in config_prompts.items():
            if fmt == "models":
                continue  # 跳过 models 配置
            console.print(f"  [info]{fmt}:[/]")
            if len(str(prompt)) > 100:
                preview = str(prompt)[:100].replace("\n", " ")
                console.print(f"    {preview}...")
            else:
                console.print(f"    {prompt}")
            console.print()

        # 提示模型特定配置
        has_model_specific = any(config_prompts.get("models", {}).values())
        if has_model_specific:
            console.print(f"[info]提示: 使用 [command]-m <模型>[/] 查看模型特定提示词[/]\n")
