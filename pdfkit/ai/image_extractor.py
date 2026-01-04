"""AI 智能图像提取器 - 基于视觉大模型的 PDF 图像智能提取

使用 Qwen3-VL 模型的物体定位能力，智能识别 PDF 页面中的图像、图表、照片等。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

from ..core.ocr_handler import QwenVLOCR, OCRModel
from .image_detection_prompt import (
    build_image_detection_prompt,
    parse_detection_result,
    filter_images_by_type,
    normalize_bbox_to_pixels,
)
from .translator import parse_page_range


class AIImageExtractor:
    """AI 智能图像提取器

    利用 Qwen3-VL 模型的物体定位能力，智能识别并提取 PDF 中的图像。
    """

    # 图像检测提示词
    DETECT_PROMPT = """检测图中所有的图像、图表、照片、插图，并返回每个图像的边界框坐标。

要求：
1. 识别所有视觉内容（照片、图表、示意图、插图、截图等）
2. 不要包含纯文字区域、页眉页脚、页码、水印
3. 只检测有实际视觉内容的区域
4. 以 JSON 格式返回结果

返回格式：
```json
{
  "images": [
    {
      "type": "photo|chart|diagram|illustration|table|logo|screenshot",
      "description": "简短描述这个图像的内容",
      "bbox": [x1, y1, x2, y2]
    }
  ]
}
```

bbox 坐标格式：[左上角x, 左上角y, 右下角x, 右下角y]
坐标值范围是 0-1000，表示相对于图像宽高的千分比位置。

如果没有检测到任何图像，返回空数组：{"images": []}

请直接输出 JSON，不要添加任何解释。
"""

    def __init__(
        self,
        model: str = "plus",
        api_key: Optional[str] = None,
    ):
        """
        初始化图像提取器

        Args:
            model: 模型选择 (flash/plus)
            api_key: API Key
        """
        model_enum = OCRModel.FLASH if model == "flash" else OCRModel.PLUS
        self.ocr = QwenVLOCR(api_key=api_key, model=model_enum)
        self.model = model

    def extract_images(
        self,
        pdf_path: Path,
        output_dir: Path,
        pages: Optional[List[int]] = None,
        types: Optional[List[str]] = None,
        exclude_types: Optional[List[str]] = None,
        min_size: int = 50,
        dpi: int = 300,
        padding: int = 0,
        output_format: str = "png",
        quality: int = 95,
        progress_callback: Optional[callable] = None,
    ) -> List[dict]:
        """
        从 PDF 中智能提取图像

        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录
            pages: 页面列表（0-based 索引）
            types: 要提取的图像类型
            exclude_types: 要排除的图像类型
            min_size: 最小图像尺寸（像素）
            dpi: 渲染 DPI
            padding: 边界框扩展像素
            output_format: 输出格式 (png/jpg/webp)
            quality: JPG/WebP 质量
            progress_callback: 进度回调函数，签名为 (current, total, description, advance)

        Returns:
            提取的图像信息列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(pdf_path)
        if pages is None:
            pages = list(range(doc.page_count))

        total = len(pages)
        all_extracted = []
        image_counter = 0

        for idx, page_num in enumerate(pages):
            page = doc[page_num]

            # 开始处理该页
            if progress_callback:
                progress_callback(idx, total, f"[black]处理[/][black]第[/] [bold_text]{page_num + 1}[/] [black]页[/]", False)

            # 1. 渲染页面为图像（很快，不需要单独显示状态）
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            page_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # 2. 调用 VL 模型检测图像（耗时操作）
            if progress_callback:
                progress_callback(idx, total, f"[info]检测[/][black]第[/] [bold_text]{page_num + 1}[/] [black]页图像[/]", False)

            detected = self._detect_images(page_image, types, exclude_types)

            if not detected:
                # 没有检测到图像
                if progress_callback:
                    progress_callback(idx + 1, total, f"[success]完成第 {page_num + 1} 页无图像[/]", True)
                continue

            # 3. 裁切并保存图像
            if progress_callback:
                progress_callback(idx, total, f"[warning]提取[/][black]第[/] [bold_text]{page_num + 1}[/] [black]页图像[/]", False)

            page_extracted = 0
            for img_info in detected:
                bbox = img_info["bbox"]

                # 转换坐标
                pixel_bbox = normalize_bbox_to_pixels(
                    bbox, pix.width, pix.height, padding
                )

                # 检查尺寸
                width = pixel_bbox[2] - pixel_bbox[0]
                height = pixel_bbox[3] - pixel_bbox[1]
                if width < min_size or height < min_size:
                    continue

                # 裁切图像
                cropped = page_image.crop(pixel_bbox)

                # 保存图像
                image_counter += 1
                page_extracted += 1
                filename = f"page{page_num + 1:03d}_img{image_counter:03d}.{output_format}"
                output_path = output_dir / filename

                if output_format in ["jpg", "jpeg"]:
                    cropped.save(output_path, "JPEG", quality=quality)
                elif output_format == "webp":
                    cropped.save(output_path, "WEBP", quality=quality)
                else:
                    cropped.save(output_path, "PNG")

                # 记录提取信息
                all_extracted.append({
                    "file": str(output_path),
                    "page": page_num + 1,
                    "type": img_info.get("type", "unknown"),
                    "description": img_info.get("description", ""),
                    "size": [width, height],
                    "bbox": pixel_bbox,
                })

            # 页面完成，advance 进度
            if progress_callback:
                progress_callback(idx + 1, total, f"[success]完成第 {page_num + 1} 页({page_extracted}个图像)[/]", True)

        doc.close()

        # 保存元数据
        if all_extracted:
            metadata = {
                "source": str(pdf_path),
                "extracted_at": datetime.now().isoformat(),
                "total_images": len(all_extracted),
                "images": all_extracted,
            }
            meta_path = output_dir / "metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

        return all_extracted

    def _detect_images(
        self,
        image: Image.Image,
        include_types: Optional[List[str]] = None,
        exclude_types: Optional[List[str]] = None,
    ) -> List[dict]:
        """使用 VL 模型检测图像中的所有视觉内容

        Args:
            image: PIL Image 对象
            include_types: 要包含的图像类型
            exclude_types: 要排除的图像类型

        Returns:
            检测到的图像列表
        """
        # 构建提示词
        prompt = build_image_detection_prompt(include_types, exclude_types)

        try:
            # 调用 OCR 模型
            response = self.ocr.ocr_image(image, prompt=prompt)

            # 解析结果
            detected = parse_detection_result(response)

            # 过滤类型
            return filter_images_by_type(detected, include_types, exclude_types)

        except Exception as e:
            # 出错时返回空列表
            return []
