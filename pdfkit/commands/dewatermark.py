"""AI 水印去除命令 (Qwen3-VL + LaMa)

两步流程:
  Step 1: detect  - VL 模型定位水印，输出标记图供检验
  Step 2: remove  - 基于检测结果执行 LaMa 去水印
"""

from pathlib import Path
from typing import Optional
import json

import typer

from ..utils.console import (
    console, print_success, print_error, print_info, print_warning,
    Icons,
)
from ..utils.file_utils import resolve_path

app = typer.Typer(help="AI 水印去除 (两步流程)")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

MODEL_MAP = {
    "flash": "qwen3-vl-flash",
    "plus": "qwen3-vl-plus",
}


def _resolve_lama_path() -> str:
    """查找 LaMa 模型路径"""
    candidates = [
        Path.home() / ".pdfkit" / "models" / "big-lama.pt",
        Path.home() / ".pdfkit" / "big-lama.pt",
        Path("models") / "big-lama.pt",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    print_error(
        f"未找到 LaMa 模型文件\n"
        f"  请下载到: {candidates[0]}\n"
        f"  下载: https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt"
    )
    raise typer.Exit(1)


def _collect_images(path: Path) -> list[Path]:
    p = path.resolve()
    if p.is_dir():
        return sorted(f for f in p.iterdir() if f.suffix.lower() in IMAGE_EXTS)
    elif p.is_file() and p.suffix.lower() in IMAGE_EXTS:
        return [p]
    return []


def _draw_boxes(img, detections, label_prefix: str = "") -> 'Image':
    """在图片上绘制红色标记框"""
    from PIL import ImageDraw, ImageFont
    result = img.copy()
    draw = ImageDraw.Draw(result)
    w, h = result.size

    try:
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 18)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except (OSError, IOError):
            font = ImageFont.load_default()

    for det in detections:
        x1, y1, x2, y2 = det.bbox
        px1, px2 = int(x1 * w / 999), int(x2 * w / 999)
        py1, py2 = int(y1 * h / 999), int(y2 * h / 999)

        draw.rectangle([px1, py1, px2, py2], outline="red", width=3)
        label = f"{label_prefix}{det.label}" if label_prefix else det.label
        tb = draw.textbbox((px1, py1 - 22), label, font=font)
        draw.rectangle([tb[0] - 2, tb[1] - 2, tb[2] + 2, tb[3] + 2], fill="red")
        draw.text((px1, py1 - 22), label, fill="white", font=font)

    return result


# ============================================================================
# Step 1: 检测水印并输出标记图
# ============================================================================

@app.command("detect")
def detect_cmd(
    file: Path = typer.Argument(
        ...,
        help="图片/文件夹/PDF 路径",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="输出目录 (默认: <原位置>_marked/)",
    ),
    model: str = typer.Option(
        "flash", "--model", "-m",
        help="VL 模型: flash (快速) 或 plus (精准)",
    ),
    dpi: int = typer.Option(
        150, "--dpi",
        help="PDF 渲染 DPI (仅 PDF 模式)",
    ),
    pages: Optional[str] = typer.Option(
        None, "--pages", "-p",
        help="PDF 页码范围，如 '1-5' (仅 PDF 模式)",
    ),
    prompt: Optional[str] = typer.Option(
        None, "--prompt",
        help="自定义水印检测提示词 (默认: 通用水印检测 prompt)",
    ),
):
    """
    Step 1: 检测水印位置，输出标记图供检验

    自动识别输入类型 (图片/PDF)，用红框标注水印位置，
    同时保存检测结果 JSON 供 remove 命令使用。

    示例:

        pdfkit dewatermark detect photo.jpg

        pdfkit dewatermark detect photos/

        pdfkit dewatermark detect document.pdf --pages 1-3

        pdfkit dewatermark detect photo.jpg --prompt "找出所有文字水印"

    检查标记图确认无误后，执行 remove 命令去水印:

        pdfkit dewatermark remove photo_marked/
    """
    from PIL import Image as PILImage
    from ..core.watermark_remover import (
        _build_client, detect_watermarks, parse_page_range, DETECT_PROMPT,
    )
    import fitz

    vl_model = MODEL_MAP.get(model, model)
    custom_prompt = prompt  # None 时 detect_watermarks 使用内置 DETECT_PROMPT
    file = resolve_path(file)
    is_pdf = file.is_file() and file.suffix.lower() == ".pdf"

    # 确定输出目录
    if output:
        out_dir = output.resolve()
    elif is_pdf:
        out_dir = file.parent / f"{file.stem}_marked"
    elif file.is_dir():
        out_dir = file.parent / f"{file.name}_marked"
    else:
        out_dir = file.parent / f"{file.stem}_marked"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = _build_client()
    all_detections = {}  # filename → [{label, bbox}]

    if is_pdf:
        # PDF 模式: 逐页渲染检测
        doc = fitz.open(str(file))
        total = len(doc)
        targets = parse_page_range(pages, total) or list(range(total))

        console.print(f"{Icons.INFO} PDF: [bold]{file.name}[/] ({total} 页, 处理 {len(targets)} 页)")
        console.print(f"  模型: [cyan]{vl_model}[/], DPI: {dpi}")

        for idx in targets:
            page = doc[idx]
            page_num = idx + 1
            zoom = dpi / 72.0
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            page_img = PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)

            console.print(f"\n  第 {page_num}/{total} 页...")
            dets = detect_watermarks(client, vl_model, page_img, prompt=custom_prompt)

            page_key = f"page_{page_num:03d}"
            if dets:
                console.print(f"    检测到 {len(dets)} 个水印:")
                for d in dets:
                    console.print(f"      {Icons.SUCCESS} {d.label}: {d.bbox}")
                all_detections[page_key] = [{"label": d.label, "bbox": d.bbox} for d in dets]

                marked = _draw_boxes(page_img, dets)
                marked.save(out_dir / f"{page_key}_marked.png")
            else:
                console.print(f"    未检测到水印")
                all_detections[page_key] = []

        doc.close()

    else:
        # 图片模式
        images = _collect_images(file)
        if not images:
            print_error(f"未找到图片: {file}")
            raise typer.Exit(1)

        console.print(f"{Icons.INFO} 共 [number]{len(images)}[/] 张图片, 模型=[cyan]{vl_model}[/]")

        for img_path in images:
            console.print(f"\n  {img_path.name}...")
            pil_img = PILImage.open(img_path).convert("RGB")
            dets = detect_watermarks(client, vl_model, pil_img, prompt=custom_prompt)

            if dets:
                console.print(f"    检测到 {len(dets)} 个水印:")
                for d in dets:
                    console.print(f"      {Icons.SUCCESS} {d.label}: {d.bbox}")
                all_detections[img_path.name] = [{"label": d.label, "bbox": d.bbox} for d in dets]

                marked = _draw_boxes(pil_img, dets)
                marked.save(out_dir / f"{img_path.stem}_marked.png")
            else:
                console.print(f"    未检测到水印")
                all_detections[img_path.name] = []

    # 保存检测结果 JSON
    meta = {
        "source": str(file),
        "model": vl_model,
        "is_pdf": is_pdf,
        "dpi": dpi if is_pdf else None,
        "detections": all_detections,
    }
    meta_path = out_dir / "detections.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    total_wm = sum(len(v) for v in all_detections.values())
    console.print()
    print_success(f"检测完成! 共发现 {total_wm} 个水印")
    print_info(f"标记图输出: {out_dir}")
    print_info(f"检测结果: {meta_path}")
    console.print()
    console.print("[dim]检查标记图确认无误后，执行去水印:[/]")
    console.print(f"  [bold cyan]pdfkit dewatermark remove {out_dir}[/]")


# ============================================================================
# Step 2: 基于检测结果去水印
# ============================================================================

@app.command("remove")
def remove_cmd(
    marked_dir: Path = typer.Argument(
        ...,
        help="detect 命令输出的目录 (包含 detections.json)",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="输出路径 (默认: 原文件旁 <原名>_clean.<ext>)",
    ),
    lama_path: Optional[str] = typer.Option(
        None, "--lama-path",
        help="LaMa 模型路径",
    ),
    dilate: int = typer.Option(
        15, "--dilate",
        help="mask 膨胀像素",
    ),
    crop_padding: int = typer.Option(
        100, "--crop-padding",
        help="局部裁剪 padding 像素",
    ),
):
    """
    Step 2: 基于检测结果执行去水印

    读取 detect 命令输出的 detections.json，执行 LaMa 修复。

    示例:

        pdfkit dewatermark remove photo_marked/

        pdfkit dewatermark remove document_marked/ -o clean.pdf
    """
    import time
    from io import BytesIO
    import numpy as np
    from PIL import Image as PILImage
    from ..core.watermark_remover import (
        _get_inpainter, create_mask, Detection, parse_page_range,
    )

    marked_dir = marked_dir.resolve()
    meta_path = marked_dir / "detections.json"
    if not meta_path.exists():
        print_error(f"未找到 detections.json，请先执行 detect 命令\n  目录: {marked_dir}")
        raise typer.Exit(1)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    source = Path(meta["source"])
    is_pdf = meta.get("is_pdf", False)
    dpi = meta.get("dpi", 150)
    all_dets = meta["detections"]

    # 检查是否有水印
    total_wm = sum(len(v) for v in all_dets.values())
    if total_wm == 0:
        print_warning("检测结果中无水印，无需处理")
        raise typer.Exit(0)

    model_path = lama_path or _resolve_lama_path()
    console.print(f"{Icons.INFO} 加载 LaMa 模型...")
    inpainter = _get_inpainter(model_path)
    console.print(f"{Icons.SUCCESS} LaMa 就绪 (device={inpainter.device})")
    console.print(f"{Icons.INFO} 源文件: {source}")
    console.print(f"{Icons.INFO} 待去除: {total_wm} 个水印")

    t_start = time.time()

    if is_pdf:
        import fitz

        if not source.exists():
            print_error(f"源 PDF 不存在: {source}")
            raise typer.Exit(1)

        out_path = output.resolve() if output else source.parent / f"{source.stem}_clean.pdf"

        doc = fitz.open(str(source))
        total_pages = len(doc)
        output_doc = fitz.open()

        for page_idx in range(total_pages):
            page_key = f"page_{page_idx + 1:03d}"
            dets_raw = all_dets.get(page_key, [])
            page = doc[page_idx]

            if dets_raw:
                dets = [Detection(label=d["label"], bbox=d["bbox"]) for d in dets_raw]
                zoom = dpi / 72.0
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                page_img = PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)
                w, h = page_img.size

                mask = create_mask((w, h), dets, dilate_px=dilate)
                img_np = np.array(page_img)
                result_np = inpainter.inpaint(img_np, mask, crop_padding)
                result_img = PILImage.fromarray(result_np)

                buf = BytesIO()
                result_img.save(buf, format="JPEG", quality=92)
                rect = page.rect
                new_page = output_doc.new_page(width=rect.width, height=rect.height)
                new_page.insert_image(rect, stream=buf.getvalue())

                console.print(f"  第 {page_idx + 1} 页: 去除 {len(dets)} 个水印")
            else:
                output_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)

        output_doc.save(str(out_path), garbage=3, deflate=True)
        output_doc.close()
        doc.close()

        input_size = source.stat().st_size / 1024 / 1024
        output_size = out_path.stat().st_size / 1024 / 1024
        t_total = time.time() - t_start

        console.print()
        print_success(f"PDF 去水印完成! ({t_total:.1f}s)")
        console.print(f"  {Icons.INFO} 大小: {input_size:.1f}MB → {output_size:.1f}MB")
        print_success(f"输出: {out_path}")

    else:
        # 图片模式
        if output and len(all_dets) > 1:
            out_dir = output.resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
        else:
            out_dir = None

        processed = 0
        for filename, dets_raw in all_dets.items():
            if not dets_raw:
                continue

            img_path = source if source.is_file() else source / filename
            if not img_path.exists():
                print_warning(f"源文件不存在: {img_path}")
                continue

            pil_img = PILImage.open(img_path).convert("RGB")
            w, h = pil_img.size
            dets = [Detection(label=d["label"], bbox=d["bbox"]) for d in dets_raw]

            mask = create_mask((w, h), dets, dilate_px=dilate)
            result_np = inpainter.inpaint(np.array(pil_img), mask, crop_padding)
            result_img = PILImage.fromarray(result_np)

            # 输出路径
            if output and source.is_file():
                out_path = output.resolve()
            elif out_dir:
                out_path = out_dir / f"{Path(filename).stem}_clean{Path(filename).suffix}"
            else:
                out_path = img_path.parent / f"{img_path.stem}_clean{img_path.suffix}"

            out_path.parent.mkdir(parents=True, exist_ok=True)

            if img_path.suffix.lower() in (".jpg", ".jpeg"):
                result_img.save(out_path, quality=95)
            else:
                result_img.save(out_path)

            console.print(f"  {Icons.SUCCESS} {filename} → {out_path}")
            processed += 1

        t_total = time.time() - t_start
        console.print()
        print_success(f"图片去水印完成! 处理 {processed} 张 ({t_total:.1f}s)")
