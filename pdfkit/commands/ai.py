"""AI 命令 - 基于视觉大模型的智能信息抽取与翻译"""

from pathlib import Path
from typing import Optional
import typer

from ..utils.console import (
    console, print_success, print_error, print_info, create_progress, Icons
)
from ..utils.validators import validate_pdf_file, require_unlocked_pdf
from ..utils.config import load_config
from ..ai.extract import AIExtractor, format_output
from ..ai.translator import AITranslator, parse_page_range
from ..ai.formula_extractor import AIFormulaExtractor
from ..ai.image_extractor import AIImageExtractor
from ..ai.image_detection_prompt import IMAGE_TYPES

# 创建 ai 子应用
app = typer.Typer(help="AI 智能处理 (基于阿里百炼 Qwen3-VL)")


def validate_output_format(value: str) -> str:
    """验证输出格式参数，提供中文错误提示"""
    valid_formats = ["json", "yaml", "csv"]
    if value not in valid_formats:
        print_error(f"无效的输出格式: {value}")
        print_info("支持的格式:")
        for fmt in valid_formats:
            print_info(f"  - {fmt}")
        raise typer.Exit(1)
    return value


@app.command()
def extract(
    file: Path = typer.Argument(
        ...,
        help="PDF/图片文件路径",
        exists=True,
    ),
    fields: Optional[str] = typer.Option(
        None,
        "--fields",
        "-f",
        help="字段列表，逗号分隔 (如: 姓名,电话,地址)",
    ),
    template: Optional[Path] = typer.Option(
        None,
        "--template",
        "-t",
        help="模板文件路径 (JSON/YAML)",
        exists=True,
    ),
    page: int = typer.Option(
        1,
        "--page",
        "-p",
        help="目标页码 (PDF专用，从1开始)",
        min=1,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        help="输出格式: json, yaml, csv",
        callback=validate_output_format,
    ),
    model: str = typer.Option(
        "plus",
        "--model",
        "-m",
        help="模型: flash(快速) 或 plus(精准)",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="DASHSCOPE_API_KEY",
        help="API Key",
    ),
):
    """
    从 PDF/图片中抽取结构化信息

    使用阿里百炼 Qwen3-VL 视觉语言模型进行智能抽取。

    示例:
        # 快速提取 - 指定字段名
        pdfkit ai extract invoice.pdf -f "发票号码,开票日期,金额,购买方,销售方"

        # 使用模板文件 - 复杂场景
        pdfkit ai extract invoice.pdf --template invoice_template.json

        # 从图片提取
        pdfkit ai extract id_card.jpg -f "姓名,性别,民族,出生日期,住址,身份证号"

        # 指定页码
        pdfkit ai extract contract.pdf -f "甲方,乙方,金额" --page 3

        # 输出为 YAML 格式
        pdfkit ai extract doc.pdf -f "字段1,字段2" --format yaml

        # 保存到文件
        pdfkit ai extract doc.pdf -f "字段1,字段2" -o result.json

    注意:
        - --fields 和 --template 二选一
        - 简单场景用 --fields，复杂场景用 --template
        - YAML 格式需要安装 pyyaml: pip install pyyaml
    """
    # 验证参数
    if not fields and not template:
        print_error("必须指定 --fields 或 --template 参数")
        print_info()
        print_info("快速模式:")
        print_info("  pdfkit ai extract doc.pdf -f \"字段1,字段2,字段3\"")
        print_info()
        print_info("模板模式:")
        print_info("  pdfkit ai extract doc.pdf --template template.json")
        raise typer.Exit(1)

    if fields and template:
        print_error("--fields 和 --template 不能同时使用")
        raise typer.Exit(1)

    # 验证模型
    if model not in ["flash", "plus"]:
        print_error(f"无效的模型: {model}")
        print_info("支持的模型:")
        print_info("  - flash: 快速模式")
        print_info("  - plus: 精准模式")
        raise typer.Exit(1)

    # PDF 特殊检查
    if file.suffix.lower() == '.pdf':
        if not validate_pdf_file(file):
            print_error(f"文件不存在或不是有效的 PDF: {file}")
            raise typer.Exit(1)

        if not require_unlocked_pdf(file, "AI 抽取"):
            raise typer.Exit(1)

    try:
        # 解析字段列表
        fields_list = None
        if fields:
            fields_list = [f.strip() for f in fields.split(",") if f.strip()]

        # 初始化抽取器
        print_info(f"使用模型: [command]{model}[/]")
        extractor = AIExtractor(model=model, api_key=api_key)

        # 执行抽取
        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.MAGIC} AI 抽取中...",
                total=1
            )

            result = extractor.extract(
                file_path=file,
                fields=fields_list,
                template=template,
                page=page,
            )

            progress.update(task, advance=1)

        # 格式化输出
        output_str = format_output(result, format)

        # 保存或显示结果
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(output_str, encoding="utf-8")
            print_success(f"结果已保存到: [path]{output}[/]")
        else:
            if format == "json":
                console.print_json(output_str)
            else:
                console.print(output_str)

        print_success("AI 抽取完成！")

    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except ValueError as e:
        print_error(f"参数错误: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"AI 抽取失败: {e}")
        raise typer.Exit(1)


@app.command("translate")
def translate(
    file: Path = typer.Argument(
        ...,
        help="PDF文件路径",
        exists=True,
    ),
    to: str = typer.Option(
        ...,
        "--to",
        help="目标语言代码 (zh/en/ja/ko/fr/es/ru/pt/it/vi/th/ar/id/ms)",
    ),
    from_lang: str = typer.Option(
        "auto",
        "--from",
        help="源语言代码 (默认auto自动检测)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    mode: str = typer.Option(
        "markdown",
        "--mode",
        help="输出模式: markdown(默认), pdf(beta), images(beta)",
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        "-p",
        help="页面范围 (如: 1-5,8,10-15)",
    ),
    domain: Optional[str] = typer.Option(
        None,
        "--domain",
        "-d",
        help="领域提示 (英文描述，如: Medical literature)",
    ),
    glossary: Optional[Path] = typer.Option(
        None,
        "--glossary",
        "-g",
        help="术语表CSV文件路径",
        exists=True,
    ),
    skip_main_subject: bool = typer.Option(
        False,
        "--skip-main-subject",
        help="翻译主体（人物/商品/Logo）上的文字",
    ),
    preserve_original: bool = typer.Option(
        False,
        "--preserve-original",
        help="保留原文（仅markdown模式，输出双语对照）",
    ),
    upload_method: str = typer.Option(
        "base64",
        "--upload-method",
        help="图片上传方法: base64(默认), oss, local",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="DASHSCOPE_API_KEY",
        help="API Key",
    ),
):
    """
    翻译PDF文档

    默认使用 Markdown 模式（推荐），输出可编辑的文本。
    图像翻译模式（pdf/images）为 Beta 功能，排版保留效果可能不理想。

    **Markdown 翻译模式** (默认):
    使用 VL 识别 + MT 翻译，输出可编辑的 Markdown 文本。

        # 直接翻译（默认 markdown 模式）
        pdfkit ai translate paper.pdf --to zh

        # 保留原文（双语对照）
        pdfkit ai translate paper.pdf --to zh --preserve-original

        # 技术文档翻译（添加领域提示）
        pdfkit ai translate api_docs.pdf --to zh \\
            --domain "Software API documentation. Keep technical terms unchanged."

        # 使用术语表
        pdfkit ai translate tech_paper.pdf --to zh --glossary terms.csv

        # 指定页面范围
        pdfkit ai translate book.pdf --to zh --pages 1-20

    **图像翻译模式** (Beta, --mode pdf/--mode images):
    使用 qwen-mt-image 模型，保留原始排版，输出 PDF/图片。
    注意：图像翻译结果可能不理想，建议使用 Markdown 模式。

        # 输出为 PDF（Beta）
        pdfkit ai translate paper.pdf --to zh --mode pdf

        # 输出为图片目录（Beta）
        pdfkit ai translate doc.pdf --to zh --mode images -o translated_images/

    模式选择建议:
        - 需要后续编辑修改 → 使用默认 Markdown 模式 ✅
        - 需要双语对照 → 使用 --preserve-original ✅
        - 需要完美保留原排版 → 使用 --mode pdf（Beta，效果可能不理想）

    注意:
        - 源语言或目标语言必须有一个是中文或英文
        - Markdown 翻译约需 8-12秒/页
        - 图像翻译为 Beta 功能，约需 10-15秒/页
    """
    # 验证模式
    valid_modes = ["pdf", "images", "markdown"]
    if mode not in valid_modes:
        print_error(f"无效的输出模式: {mode}")
        print_info("支持的模式:")
        for m in valid_modes:
            print_info(f"  - {m}")
        raise typer.Exit(1)

    # 验证 preserve-original 参数
    if preserve_original and mode != "markdown":
        print_error("--preserve-original 选项仅适用于 markdown 模式")
        print_info("请使用: --mode markdown --preserve-original")
        raise typer.Exit(1)

    # 验证 skip-main-subject 参数
    if skip_main_subject and mode == "markdown":
        print_error("--skip-main-subject 选项仅适用于图像翻译模式 (pdf/images)")
        raise typer.Exit(1)

    # PDF 检查
    if file.suffix.lower() != '.pdf':
        print_error("translate 命令仅支持 PDF 文件")
        raise typer.Exit(1)

    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if not require_unlocked_pdf(file, "AI 翻译"):
        raise typer.Exit(1)

    try:
        # 确定输出路径
        if output is None:
            if mode == "pdf":
                output = file.with_stem(f"{file.stem}_{to}")
            elif mode == "images":
                output = file.parent / f"{file.stem}_{to}_images"
            elif mode == "markdown":
                output = file.with_suffix(".md")

        # 解析页面范围
        page_list = None
        total_pages_to_translate = 0
        if pages:
            import fitz
            doc = fitz.open(file)
            total_pages = doc.page_count
            doc.close()
            page_list = parse_page_range(pages, total_pages)
            total_pages_to_translate = len(page_list)
        else:
            # 如果没有指定页面，需要获取总页数
            import fitz
            doc = fitz.open(file)
            total_pages_to_translate = doc.page_count
            doc.close()

        # Markdown 模式使用不同的提示信息
        if mode == "markdown":
            print_info(f"翻译方向: [info]{from_lang}[/] → [command]{to}[/]")
            print_info(f"输出模式: [command]Markdown (VL + MT)[/]")
            if preserve_original:
                print_info("[info]保留原文: 是 (双语对照)[/]")
            print_info(f"输出文件: [path]{output}[/]")
            print_info(f"翻译页数: [info]{total_pages_to_translate}[/]")
        else:
            # 获取上传配置
            config = load_config()
            translate_config = config.get("ai", {}).get("translate", {})
            upload_config = translate_config.get("upload", {}).get(upload_method, {})

            print_info(f"翻译方向: [info]{from_lang}[/] → [command]{to}[/]")
            print_info(f"输出模式: [command]{mode} (Beta)[/]")
            print_info(f"上传方法: [command]{upload_method}[/]")

            translator = AITranslator(
                api_key=api_key,
                upload_method=upload_method,
                upload_config=upload_config,
                dpi=translate_config.get("default_dpi", 200),
                timeout=translate_config.get("timeout", 120),
                poll_interval=translate_config.get("poll_interval", 5),
            )

        # 执行翻译
        try:
            with create_progress() as progress:
                if mode == "markdown":
                    task_msg = f"{Icons.MAGIC} AI Markdown 翻译中..."
                    # Markdown 模式显示实际进度
                    task = progress.add_task(task_msg, total=total_pages_to_translate)

                    # 定义进度回调（签名：current, total, description, advance）
                    def progress_callback(current: int, total: int, description: str, advance: bool):
                        if advance:
                            progress.update(task, completed=current, description=description)
                        else:
                            progress.update(task, description=description)

                    # Markdown 模式使用 AIMarkdownTranslator
                    from ..ai.markdown_translator import AIMarkdownTranslator

                    md_translator = AIMarkdownTranslator(api_key=api_key)

                    result = md_translator.translate(
                        file_path=file,
                        target_lang=to,
                        source_lang=from_lang,
                        pages=page_list,
                        domain=domain,
                        glossary_path=glossary,
                        preserve_original=preserve_original,
                        progress_callback=progress_callback,
                    )

                    # 保存到文件
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_text(result, encoding="utf-8")
                    result_path = output
                else:
                    # 图像翻译模式
                    result_path = translator.translate_pdf(
                        input_path=file,
                        output_path=output,
                        target_lang=to,
                        source_lang=from_lang,
                        pages=page_list,
                        domain_hint=domain,
                        glossary_path=glossary,
                        skip_main_subject=skip_main_subject,
                        mode=mode,
                        preserve_original=preserve_original,
                    )

                progress.update(task, completed=1, total=1)

            print_success(f"翻译完成: [path]{result_path}[/]")
        except KeyboardInterrupt:
            from ..utils.console import console
            console.print()
            print_warning("翻译已取消")
            raise typer.Exit(130)

    except ValueError as e:
        print_error(f"参数错误: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"AI 翻译失败: {e}")
        raise typer.Exit(1)


@app.command("formula")
def formula(
    file: Path = typer.Argument(
        ...,
        help="PDF/图片文件路径",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    format: str = typer.Option(
        "latex",
        "--format",
        "-f",
        help="输出格式: latex(默认), mathml, json",
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        "-p",
        help="页面范围 (如: 1-5,8,10-15)",
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        "-e",
        help="添加公式解释",
    ),
    inline: bool = typer.Option(
        False,
        "--inline",
        help="使用行内公式格式 ($...$)",
    ),
    model: str = typer.Option(
        "plus",
        "--model",
        "-m",
        help="模型: flash(快速) 或 plus(精准)",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="DASHSCOPE_API_KEY",
        help="API Key",
    ),
):
    """
    识别文档中的数学公式，输出 LaTeX 代码

    使用阿里百炼 Qwen3-VL 视觉语言模型识别数学公式、物理公式、化学方程式等。

    示例:
        # 从PDF提取所有公式
        pdfkit ai formula textbook.pdf

        # 从图片识别公式
        pdfkit ai formula equation.png

        # 输出到文件
        pdfkit ai formula paper.pdf -o formulas.tex

        # 带解释的公式识别
        pdfkit ai formula physics.pdf --explain

        # 只提取特定页面的公式
        pdfkit ai formula textbook.pdf --pages 10-20

        # JSON格式输出
        pdfkit ai formula doc.pdf --format json

    注意:
        - 输出格式支持 LaTeX（默认）、MathML、JSON
        - LaTeX 公式可在 Overleaf 等编辑器中使用
        - 复杂公式建议使用 plus 模型
    """
    # 验证格式
    valid_formats = ["latex", "mathml", "json"]
    if format not in valid_formats:
        print_error(f"无效的输出格式: {format}")
        print_info("支持的格式:")
        for f in valid_formats:
            print_info(f"  - {f}")
        raise typer.Exit(1)

    # 验证模型
    if model not in ["flash", "plus"]:
        print_error(f"无效的模型: {model}")
        print_info("支持的模型:")
        print_info("  - flash: 快速模式")
        print_info("  - plus: 精准模式")
        raise typer.Exit(1)

    # PDF 特殊检查
    if file.suffix.lower() == '.pdf':
        if not validate_pdf_file(file):
            print_error(f"文件不存在或不是有效的 PDF: {file}")
            raise typer.Exit(1)

        if not require_unlocked_pdf(file, "AI 公式识别"):
            raise typer.Exit(1)

    try:
        # 解析页面范围并获取实际要处理的页数
        page_list = None
        total_pages_to_process = 0
        if pages:
            import fitz
            doc = fitz.open(file)
            total_pdf_pages = doc.page_count
            doc.close()
            page_list = parse_page_range(pages, total_pdf_pages)
            total_pages_to_process = len(page_list)
        else:
            # 如果没有指定页面，获取总页数
            import fitz
            doc = fitz.open(file)
            total_pages_to_process = doc.page_count
            doc.close()

        # 初始化公式提取器
        print_info(f"使用模型: [command]{model}[/]")
        print_info(f"输出格式: [command]{format}[/]")
        if pages:
            print_info(f"页面范围: [info]{pages}[/]")
        print_info(f"待处理页数: [info]{total_pages_to_process}[/]")

        extractor = AIFormulaExtractor(model=model, api_key=api_key)

        # 执行提取
        try:
            with create_progress() as progress:
                task = progress.add_task(
                    f"{Icons.MAGIC} AI 公式识别中...",
                    total=total_pages_to_process,
                )

                # 定义进度回调（签名：current, total, description, advance）
                def progress_callback(current: int, total: int, description: str, advance: bool):
                    if advance:
                        progress.update(task, completed=current, description=description)
                    else:
                        progress.update(task, description=description)

                result = extractor.extract(
                    file_path=file,
                    pages=page_list,
                    explain=explain,
                    inline=inline,
                    output_format=format,
                    progress_callback=progress_callback,
                )

            # 保存或显示结果
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(result, encoding="utf-8")
                print_success(f"公式已保存到: [path]{output}[/]")
            else:
                if format == "json":
                    console.print_json(result)
                else:
                    console.print(result)

            print_success("AI 公式识别完成！")
        except KeyboardInterrupt:
            console.print()
            print_warning("公式识别已取消")
            raise typer.Exit(130)

    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except ValueError as e:
        print_error(f"参数错误: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"AI 公式识别失败: {e}")
        raise typer.Exit(1)


@app.command("extract-images")
def extract_images(
    file: Path = typer.Argument(
        ...,
        help="PDF文件路径",
        exists=True,
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="输出目录路径",
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        "-p",
        help="页面范围 (如: 1-5,8,10-15)",
    ),
    types: Optional[str] = typer.Option(
        None,
        "--types",
        "-t",
        help=f"要提取的图像类型，逗号分隔: {', '.join(IMAGE_TYPES.keys())}",
    ),
    exclude: Optional[str] = typer.Option(
        None,
        "--exclude",
        "-e",
        help=f"要排除的图像类型，逗号分隔: {', '.join(IMAGE_TYPES.keys())}",
    ),
    min_size: int = typer.Option(
        50,
        "--min-size",
        help="最小图像尺寸（像素）",
        min=10,
    ),
    output_format: str = typer.Option(
        "png",
        "--format",
        "-f",
        help="输出格式: png(默认), jpg, webp",
    ),
    quality: int = typer.Option(
        95,
        "--quality",
        "-q",
        help="JPG/WebP 质量 (1-100)",
        min=1,
        max=100,
    ),
    dpi: int = typer.Option(
        200,
        "--dpi",
        help="渲染 DPI (默认200，越低越快但检测精度降低)",
        min=72,
        max=600,
    ),
    padding: int = typer.Option(
        0,
        "--padding",
        help="边界框扩展像素",
        min=0,
        max=100,
    ),
    model: str = typer.Option(
        "plus",
        "--model",
        "-m",
        help="模型: flash(快速) 或 plus(精准)",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        envvar="DASHSCOPE_API_KEY",
        help="API Key",
    ),
):
    """
    智能提取PDF中的图像

    使用阿里百炼 Qwen3-VL 视觉语言模型智能识别并提取 PDF 中的图像、
    图表、照片、插图等视觉内容，而非简单提取嵌入图像对象。

    图像类型:
        photo       照片、图片
        chart       图表（柱状图、折线图、饼图等）
        diagram     示意图、流程图
        illustration 插图、手绘图
        table       表格（作为图像）
        logo        Logo、图标
        screenshot  截图

    示例:
        # 提取所有图像到默认目录
        pdfkit ai extract-images paper.pdf
        # 输出到: paper_images/

        # 指定输出目录
        pdfkit ai extract-images paper.pdf -o ./extracted_images/

        # 只提取图表和照片
        pdfkit ai extract-images report.pdf --types chart,photo

        # 排除 Logo 和截图
        pdfkit ai extract-images doc.pdf --exclude logo,screenshot

        # 指定页面范围
        pdfkit ai extract-images book.pdf --pages 1-10
        pdfkit ai extract-images book.pdf --pages 1,3,5-8,10

        # 输出为高质量 JPG
        pdfkit ai extract-images doc.pdf --format jpg --quality 95

        # 输出为 WebP（更小文件体积）
        pdfkit ai extract-images doc.pdf --format webp --quality 85

        # 使用快速模型（适合大量页面）
        pdfkit ai extract-images book.pdf --model flash

        # 设置最小尺寸（忽略小图）
        pdfkit ai extract-images.pdf --min-size 200

        # 添加边距（扩展裁剪区域）
        pdfkit ai extract-images.pdf --padding 20

        # 组合多个选项
        pdfkit ai extract-images paper.pdf \\
            --types chart,diagram \\
            --pages 1-20 \\
            --format jpg \\
            --quality 90 \\
            --min-size 100 \\
            --padding 10 \\
            -o ./figures/

    注意:
        - 使用视觉大模型检测图像，非传统图像提取
        - 可检测页面渲染后的所有视觉内容（包括绘制内容）
        - 约需 5-10秒/页（取决于模型和网络）
        - 会自动生成 metadata.json 元数据文件

    性能优化建议:
        - 使用 flash 模型更快（但精度略低）
        - 降低 DPI 可加快速度（默认200，最低72）
        - 限制页面范围（--pages）可减少处理时间
        - 需要快速提取？使用传统命令（无法检测绘制内容）：
          pdfkit extract images input.pdf -o output/  # 秒级完成
    """
    # 验证格式
    valid_formats = ["png", "jpg", "jpeg", "webp"]
    if output_format not in valid_formats:
        print_error(f"无效的输出格式: {output_format}")
        print_info("支持的格式:")
        for f in valid_formats:
            print_info(f"  - {f}")
        raise typer.Exit(1)

    # 验证模型
    if model not in ["flash", "plus"]:
        print_error(f"无效的模型: {model}")
        print_info("支持的模型:")
        print_info("  - flash: 快速模式")
        print_info("  - plus: 精准模式")
        raise typer.Exit(1)

    # 解析图像类型
    types_list = None
    if types:
        types_list = [t.strip() for t in types.split(",") if t.strip()]
        for t in types_list:
            if t not in IMAGE_TYPES and t != "all":
                print_error(f"无效的图像类型: {t}")
                print_info(f"支持的类型: {', '.join(list(IMAGE_TYPES.keys()) + ['all'])}")
                raise typer.Exit(1)

    exclude_list = None
    if exclude:
        exclude_list = [e.strip() for e in exclude.split(",") if e.strip()]
        for e in exclude_list:
            if e not in IMAGE_TYPES:
                print_error(f"无效的排除类型: {e}")
                print_info(f"支持的类型: {', '.join(IMAGE_TYPES.keys())}")
                raise typer.Exit(1)

    # PDF 检查
    if file.suffix.lower() != '.pdf':
        print_error("extract-images 命令仅支持 PDF 文件")
        raise typer.Exit(1)

    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if not require_unlocked_pdf(file, "AI 图像提取"):
        raise typer.Exit(1)

    try:
        # 确定输出目录
        if output is None:
            output = file.parent / f"{file.stem}_images"
        else:
            output = Path(output)

        # 解析页面范围并获取实际要处理的页数
        page_list = None
        total_pages_to_process = 0
        if pages:
            import fitz
            doc = fitz.open(file)
            total_pdf_pages = doc.page_count
            doc.close()
            page_list = parse_page_range(pages, total_pdf_pages)
            total_pages_to_process = len(page_list)
        else:
            # 如果没有指定页面，获取总页数
            import fitz
            doc = fitz.open(file)
            total_pages_to_process = doc.page_count
            doc.close()

        # 初始化图像提取器
        print_info(f"使用模型: [command]{model}[/]")
        print_info(f"输出格式: [command]{output_format}[/]")
        print_info(f"输出目录: [path]{output}[/]")
        if pages:
            print_info(f"页面范围: [info]{pages}[/]")
        print_info(f"待处理页数: [info]{total_pages_to_process}[/]")

        extractor = AIImageExtractor(model=model, api_key=api_key)

        # 执行提取
        try:
            with create_progress() as progress:
                task = progress.add_task(
                    f"{Icons.MAGIC} AI 图像检测与提取中...",
                    total=total_pages_to_process,
                )

                # 定义进度回调（签名：current, total, description, advance）
                def progress_callback(current: int, total: int, description: str, advance: bool):
                    if advance:
                        progress.update(task, completed=current, description=description)
                    else:
                        progress.update(task, description=description)

                extracted = extractor.extract_images(
                    pdf_path=file,
                    output_dir=output,
                    pages=page_list,
                    types=types_list,
                    exclude_types=exclude_list,
                    min_size=min_size,
                    dpi=dpi,
                    padding=padding,
                    output_format=output_format,
                    quality=quality,
                    progress_callback=progress_callback,
                )

            # 显示结果
            if not extracted:
                print_info("未检测到任何图像")
                raise typer.Exit(0)

            print_success(f"成功提取 [success]{len(extracted)}[/] 个图像")

            # 按类型统计
            type_counts = {}
            for img in extracted:
                img_type = img.get("type", "unknown")
                type_counts[img_type] = type_counts.get(img_type, 0) + 1

            print_info("图像类型统计:")
            for img_type, count in sorted(type_counts.items()):
                type_name = IMAGE_TYPES.get(img_type, img_type)
                print_info(f"  - {type_name}: {count}")

            print_success(f"图像已保存到: [path]{output}[/]")
            print_info(f"元数据已保存到: [path]{output / 'metadata.json'}[/]")
        except KeyboardInterrupt:
            console.print()
            print_warning("图像提取已取消")
            raise typer.Exit(130)

    except ValueError as e:
        print_error(f"参数错误: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"AI 图像提取失败: {e}")
        raise typer.Exit(1)
