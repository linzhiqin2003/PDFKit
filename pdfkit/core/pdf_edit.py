"""PDF 编辑服务 - 核心业务逻辑

此模块包含与 PDF 编辑相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, List, Union, Tuple
from dataclasses import dataclass

import fitz  # PyMuPDF
from PIL import Image


# ==================== 数据模型 ====================

@dataclass
class WatermarkResult:
    """水印添加结果"""
    output_path: str
    page_count: int
    watermark_type: str  # "text" or "image"
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "page_count": self.page_count,
            "watermark_type": self.watermark_type,
            "success": self.success,
        }


@dataclass
class CropResult:
    """裁剪结果"""
    output_path: str
    page_count: int
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "page_count": self.page_count,
            "success": self.success,
        }


@dataclass
class ResizeResult:
    """调整大小结果"""
    output_path: str
    page_count: int
    new_width: float
    new_height: float
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "page_count": self.page_count,
            "new_width": self.new_width,
            "new_height": self.new_height,
            "success": self.success,
        }


# ==================== 自定义异常 ====================

class PDFEditError(Exception):
    """PDF 编辑错误"""
    pass


class EncryptedPDFError(PDFEditError):
    """PDF 加密错误"""
    pass


class InvalidParameterError(PDFEditError):
    """无效参数"""
    pass


# ==================== 工具函数 ====================

def _parse_color(color_str: str) -> Tuple[float, float, float]:
    """解析颜色字符串为 RGB 元组"""
    color_str = color_str.lstrip("#")
    if len(color_str) != 6:
        return (1, 0, 0)  # 默认红色

    r = int(color_str[0:2], 16) / 255
    g = int(color_str[2:4], 16) / 255
    b = int(color_str[4:6], 16) / 255
    return (r, g, b)


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
    page.insert_image(img_rect, filename=image_path, overlay=overlay)


# ==================== 核心函数 ====================

def add_watermark(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    text: Optional[str] = None,
    image_path: Optional[Union[str, Path]] = None,
    angle: int = 0,
    opacity: float = 0.3,
    font_size: int = 48,
    color: str = "#FF0000",
    position: str = "center",
    layer: str = "overlay",
) -> WatermarkResult:
    """
    添加水印到 PDF

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        text: 文字水印内容
        image_path: 图片水印路径
        angle: 旋转角度 (0/90/180/270)
        opacity: 透明度 (0-1)
        font_size: 字体大小
        color: 颜色 (十六进制，如 #FF0000)
        position: 位置 (center/top-left/top-right/bottom-left/bottom-right)
        layer: 图层 (overlay/underlay)

    Returns:
        WatermarkResult: 添加结果
    """
    if text is None and image_path is None:
        raise InvalidParameterError("必须指定 text 或 image_path")

    if text and image_path:
        raise InvalidParameterError("text 和 image_path 不能同时使用")

    if not 0 <= opacity <= 1:
        raise InvalidParameterError(f"opacity 必须在 0-1 之间，当前值: {opacity}")

    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        # 解析颜色
        color_rgb = _parse_color(color)

        # 确定 overlay 参数
        is_overlay = (layer.lower() == "overlay")

        watermark_type = "text" if text else "image"

        for page_num in range(doc.page_count):
            page = doc[page_num]
            rect = page.rect

            if text:
                _add_text_watermark(page, text, rect, angle, opacity, font_size, color_rgb, position, is_overlay)
            else:
                _add_image_watermark(page, str(image_path), rect, angle, opacity, position, is_overlay)

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存页数后关闭文档
        page_count = doc.page_count

        # 保存
        doc.save(output_path)
        doc.close()

        return WatermarkResult(
            output_path=str(output_path),
            page_count=page_count,
            watermark_type=watermark_type,
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFEditError(f"添加水印失败: {e}")


def crop_pages(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    margin: Optional[List[float]] = None,
    box: Optional[List[float]] = None,
) -> CropResult:
    """
    裁剪 PDF 页面

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        margin: 边距 [top, right, bottom, left]
        box: 裁剪框 [x0, y0, x1, y1]

    Returns:
        CropResult: 裁剪结果
    """
    if margin is None and box is None:
        raise InvalidParameterError("必须指定 margin 或 box")

    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        for page_num in range(doc.page_count):
            page = doc[page_num]
            rect = page.rect

            if box:
                # 使用裁剪框
                new_rect = fitz.Rect(box[0], box[1], box[2], box[3])
            else:
                # 使用边距
                new_rect = fitz.Rect(
                    rect.x0 + margin[3],  # left
                    rect.y0 + margin[0],  # top
                    rect.x1 - margin[1],  # right
                    rect.y1 - margin[2]   # bottom
                )

            page.set_cropbox(new_rect)

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存页数后关闭文档
        page_count = doc.page_count

        # 保存
        doc.save(output_path)
        doc.close()

        return CropResult(
            output_path=str(output_path),
            page_count=page_count,
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFEditError(f"裁剪失败: {e}")


def resize_pages(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    size: str = "A4",
    scale: float = 1.0,
) -> ResizeResult:
    """
    调整 PDF 页面大小

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        size: 页面大小 (A4/Letter/A3/A5 或 宽x高)
        scale: 缩放比例

    Returns:
        ResizeResult: 调整结果
    """
    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        # 解析页面大小
        if "x" in size.lower():
            width, height = map(float, size.lower().split("x"))
        else:
            # 预设尺寸
            sizes = {
                "A4": (595, 842),
                "A3": (842, 1191),
                "A5": (420, 595),
                "LETTER": (612, 792),
                "LEGAL": (612, 1008),
            }
            size_key = size.upper()
            if size_key not in sizes:
                raise InvalidParameterError(f"不支持的页面大小: {size}")
            width, height = sizes[size_key]

        # 创建新文档
        new_doc = fitz.open()

        for page_num in range(doc.page_count):
            # 创建新页面，尺寸按缩放比例调整
            scaled_width = width * scale
            scaled_height = height * scale
            new_page = new_doc.new_page(width=scaled_width, height=scaled_height)

            # 显示原始页面内容
            new_page.show_pdf_page(new_page.rect, doc, page_num)

        # 保存原始页数
        original_page_count = doc.page_count
        doc.close()

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存
        new_doc.save(output_path)
        new_doc.close()

        return ResizeResult(
            output_path=str(output_path),
            page_count=original_page_count,
            new_width=width,
            new_height=height,
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFEditError(f"调整大小失败: {e}")
