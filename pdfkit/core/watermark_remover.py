"""
AI 水印检测与去除核心模块

流程: Qwen3-VL 定位水印 → 生成 Mask → LaMa Inpainting 修复
支持图片和 PDF 两种输入
"""

import os
import json
import base64
import re
import time
from pathlib import Path
from io import BytesIO
from typing import Optional
from dataclasses import dataclass, field

import numpy as np
import cv2
import fitz  # PyMuPDF
from PIL import Image
from openai import OpenAI

# LaMa 依赖延迟导入 (torch 较重)
_lama_inpainter = None


# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────

@dataclass
class Detection:
    label: str
    bbox: list[int]  # [x1, y1, x2, y2] 千分比坐标


@dataclass
class RemoveResult:
    """单张图片的去水印结果"""
    result_img: Optional[Image.Image] = None
    detections: list[Detection] = field(default_factory=list)
    had_watermark: bool = False
    t_detect: float = 0.0
    t_inpaint: float = 0.0
    t_total: float = 0.0


@dataclass
class PageResult:
    """PDF 单页结果"""
    page_num: int
    remove_result: RemoveResult
    t_render: float = 0.0


# ─────────────────────────────────────────────
# VL 模型水印定位
# ─────────────────────────────────────────────

DETECT_PROMPT = """你是一个图像水印检测专家。请找出图中所有水印元素，包括：
1. 平台 logo 图标（如小红书、抖音、快手等）
2. 平台账号/ID 文字（如"小红书号: XXXXXXXXX"）
3. 其他半透明或叠加的水印文字

要求：
- 每个水印元素单独标注
- 坐标使用千分比坐标系 (0-999)，格式 [x1, y1, x2, y2]，左上角到右下角
- 只输出 JSON，不要其他文字

输出格式：
{"detections": [{"label": "描述", "bbox": [x1, y1, x2, y2]}]}

示例：
{"detections": [{"label": "小红书logo", "bbox": [900, 950, 970, 990]}, {"label": "小红书号", "bbox": [750, 970, 999, 999]}]}

如果没有找到任何水印，输出：
{"detections": []}"""


def _build_client() -> OpenAI:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("请设置环境变量 DASHSCOPE_API_KEY")
    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


def _image_to_data_url(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="JPEG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def detect_watermarks(client: OpenAI, model: str, img: Image.Image) -> list[Detection]:
    """用 VL 模型检测图中水印"""
    data_url = _image_to_data_url(img)

    completion = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": DETECT_PROMPT},
            ],
        }],
    )
    raw = completion.choices[0].message.content

    # 多策略解析 JSON
    for attempt_fn in [
        lambda: json.loads(raw),
        lambda: json.loads(re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL).group(1)),
        lambda: json.loads(re.search(r"\{.*\}", raw, re.DOTALL).group(0)),
    ]:
        try:
            data = attempt_fn()
            return [
                Detection(label=d.get("label", ""), bbox=d.get("bbox", []))
                for d in data.get("detections", [])
                if len(d.get("bbox", [])) == 4
            ]
        except (json.JSONDecodeError, AttributeError):
            continue

    return []


# ─────────────────────────────────────────────
# Mask 生成
# ─────────────────────────────────────────────

def create_mask(img_size: tuple[int, int], detections: list[Detection],
                dilate_px: int = 15) -> np.ndarray:
    w, h = img_size
    mask = np.zeros((h, w), dtype=np.uint8)

    for det in detections:
        x1, y1, x2, y2 = det.bbox
        px1, px2 = sorted([int(x1 * w / 999), int(x2 * w / 999)])
        py1, py2 = sorted([int(y1 * h / 999), int(y2 * h / 999)])
        mask[py1:py2, px1:px2] = 255

    if dilate_px > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (dilate_px * 2 + 1, dilate_px * 2 + 1)
        )
        mask = cv2.dilate(mask, kernel, iterations=1)

    return mask


# ─────────────────────────────────────────────
# LaMa Inpainting
# ─────────────────────────────────────────────

class LamaInpainter:
    """LaMa 模型封装，局部裁剪优化"""

    def __init__(self, model_path: str):
        import torch
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.model = torch.jit.load(model_path, map_location=self.device)
        self.model.eval()
        self._torch = torch

    def _pad8(self, arr: np.ndarray) -> np.ndarray:
        h, w = arr.shape[:2]
        ph = (8 - h % 8) % 8
        pw = (8 - w % 8) % 8
        pad_width = ((0, ph), (0, pw), (0, 0)) if len(arr.shape) == 3 else ((0, ph), (0, pw))
        return np.pad(arr, pad_width, mode="reflect")

    def _run(self, img: np.ndarray, mask: np.ndarray) -> np.ndarray:
        oh, ow = img.shape[:2]
        img_t = self._torch.from_numpy(
            self._pad8(img.astype(np.float32) / 255.0)
        ).permute(2, 0, 1).unsqueeze(0).to(self.device)
        mask_t = self._torch.from_numpy(
            self._pad8(mask.astype(np.float32) / 255.0)
        ).unsqueeze(0).unsqueeze(0).to(self.device)

        with self._torch.no_grad():
            result = self.model(img_t, mask_t)

        result = result[0].permute(1, 2, 0).cpu().numpy()
        return np.clip(result * 255, 0, 255).astype(np.uint8)[:oh, :ow]

    def inpaint(self, img: np.ndarray, mask: np.ndarray,
                crop_padding: int = 100) -> np.ndarray:
        h, w = img.shape[:2]
        ys, xs = np.where(mask > 0)
        if len(ys) == 0:
            return img.copy()

        my1, my2 = int(ys.min()), int(ys.max())
        mx1, mx2 = int(xs.min()), int(xs.max())
        cy1, cy2 = max(0, my1 - crop_padding), min(h, my2 + crop_padding)
        cx1, cx2 = max(0, mx1 - crop_padding), min(w, mx2 + crop_padding)

        crop_result = self._run(img[cy1:cy2, cx1:cx2], mask[cy1:cy2, cx1:cx2])

        result = img.copy()
        region = mask[cy1:cy2, cx1:cx2] > 0
        result[cy1:cy2, cx1:cx2][region] = crop_result[region]
        return result


def _get_inpainter(model_path: str) -> LamaInpainter:
    """单例获取 LaMa inpainter"""
    global _lama_inpainter
    if _lama_inpainter is None:
        _lama_inpainter = LamaInpainter(model_path)
    return _lama_inpainter


# ─────────────────────────────────────────────
# Pipeline: 单张图片去水印
# ─────────────────────────────────────────────

def remove_watermark_image(
    img: Image.Image,
    client: OpenAI,
    inpainter: LamaInpainter,
    model: str = "qwen3-vl-flash",
    dilate_px: int = 15,
    crop_padding: int = 100,
) -> RemoveResult:
    """对单张 PIL Image 执行水印去除"""
    w, h = img.size
    t_start = time.time()

    # 定位
    t0 = time.time()
    detections = detect_watermarks(client, model, img)
    t_detect = time.time() - t0

    if not detections:
        return RemoveResult(
            result_img=img,
            had_watermark=False,
            t_detect=t_detect,
            t_total=time.time() - t_start,
        )

    # Mask + Inpaint
    mask = create_mask((w, h), detections, dilate_px)
    t0 = time.time()
    result_np = inpainter.inpaint(np.array(img), mask, crop_padding)
    t_inpaint = time.time() - t0

    return RemoveResult(
        result_img=Image.fromarray(result_np),
        detections=detections,
        had_watermark=True,
        t_detect=t_detect,
        t_inpaint=t_inpaint,
        t_total=time.time() - t_start,
    )


# ─────────────────────────────────────────────
# Pipeline: PDF 去水印
# ─────────────────────────────────────────────

def remove_watermark_pdf(
    pdf_path: Path,
    output_path: Path,
    client: OpenAI,
    inpainter: LamaInpainter,
    model: str = "qwen3-vl-flash",
    dpi: int = 150,
    pages: Optional[list[int]] = None,
    dilate_px: int = 15,
    crop_padding: int = 100,
    on_page_done: Optional[callable] = None,
) -> list[PageResult]:
    """
    对 PDF 逐页去水印。

    Args:
        pages: 0-based 页码列表，None 表示全部
        on_page_done: 每页完成时的回调，接收 PageResult
    """
    doc = fitz.open(str(pdf_path))
    total = len(doc)
    target_pages = pages if pages is not None else list(range(total))

    results = []
    processed = {}  # page_idx → PIL Image

    for page_idx in target_pages:
        page = doc[page_idx]

        # 渲染
        t0 = time.time()
        zoom = dpi / 72.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        page_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        t_render = time.time() - t0

        # 去水印
        r = remove_watermark_image(
            page_img, client, inpainter,
            model=model, dilate_px=dilate_px, crop_padding=crop_padding,
        )

        processed[page_idx] = r.result_img if r.had_watermark else page_img
        pr = PageResult(page_num=page_idx + 1, remove_result=r, t_render=t_render)
        results.append(pr)

        if on_page_done:
            on_page_done(pr)

    # 合并 PDF
    output_doc = fitz.open()
    for page_idx in range(total):
        if page_idx in processed:
            img = processed[page_idx]
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=92)
            rect = doc[page_idx].rect
            new_page = output_doc.new_page(width=rect.width, height=rect.height)
            new_page.insert_image(rect, stream=buf.getvalue())
        else:
            output_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)

    output_doc.save(str(output_path), garbage=3, deflate=True)
    output_doc.close()
    doc.close()

    return results


def parse_page_range(page_str: Optional[str], total_pages: int) -> Optional[list[int]]:
    """解析页码范围，返回 0-based 列表"""
    if not page_str:
        return None

    pages = set()
    for part in page_str.split(","):
        part = part.strip()
        if "-" in part:
            s, e = part.split("-", 1)
            pages.update(range(max(1, int(s)) - 1, min(total_pages, int(e))))
        else:
            p = int(part) - 1
            if 0 <= p < total_pages:
                pages.add(p)
    return sorted(pages)
