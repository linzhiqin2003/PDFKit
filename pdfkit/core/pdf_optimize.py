"""PDF 优化服务 - 核心业务逻辑

此模块包含与 PDF 优化相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass

import fitz  # PyMuPDF
import pikepdf
from PIL import Image as PILImage
from io import BytesIO


# ==================== 数据模型 ====================

@dataclass
class CompressResult:
    """压缩结果"""
    output_path: str
    original_size: int
    compressed_size: int
    reduction_percent: float
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "original_size": self.original_size,
            "compressed_size": self.compressed_size,
            "reduction_percent": self.reduction_percent,
            "success": self.success,
        }


@dataclass
class OptimizeImagesResult:
    """优化图片结果"""
    output_path: str
    original_size: int
    optimized_size: int
    reduction_percent: float
    images_processed: int
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "original_size": self.original_size,
            "optimized_size": self.optimized_size,
            "reduction_percent": self.reduction_percent,
            "images_processed": self.images_processed,
            "success": self.success,
        }


@dataclass
class RepairResult:
    """修复结果"""
    output_path: str
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "success": self.success,
        }


# ==================== 自定义异常 ====================

class PDFOptimizeError(Exception):
    """PDF 优化错误"""
    pass


class InvalidParameterError(PDFOptimizeError):
    """无效参数"""
    pass


class EncryptedPDFError(PDFOptimizeError):
    """PDF 加密错误"""
    pass


class RepairFailedError(PDFOptimizeError):
    """修复失败"""
    pass


# ==================== 工具函数 ====================

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


# ==================== 核心函数 ====================

def compress_pdf(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    quality: str = "medium",
) -> CompressResult:
    """
    压缩 PDF 文件大小

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        quality: 压缩质量 (low/medium/high)

    Returns:
        CompressResult: 压缩结果
    """
    if quality not in ("low", "medium", "high"):
        raise InvalidParameterError("质量必须是 low, medium 或 high")

    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        # 获取原始文件大小
        original_size = file_path.stat().st_size

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用 pikepdf 进行压缩
        pdf = pikepdf.open(file_path)

        # 根据质量设置保存选项
        if quality == "low":
            # 最低质量，最小文件：压缩流 + 对象流 + 去除冗余
            pdf.save(
                output_path,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
                recompress_flate=True,
            )
        elif quality == "medium":
            # 中等质量
            pdf.save(
                output_path,
                compress_streams=True,
                object_stream_mode=pikepdf.ObjectStreamMode.preserve,
            )
        else:  # high
            # 高质量：保持更多原始结构
            pdf.save(
                output_path,
                compress_streams=False,
                object_stream_mode=pikepdf.ObjectStreamMode.disable,
            )

        pdf.close()

        # 获取压缩后大小
        compressed_size = output_path.stat().st_size
        reduction = (1 - compressed_size / original_size) * 100

        return CompressResult(
            output_path=str(output_path),
            original_size=original_size,
            compressed_size=compressed_size,
            reduction_percent=reduction,
            success=True,
        )

    except Exception as e:
        raise PDFOptimizeError(f"压缩失败: {e}")


def optimize_images(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    dpi: int = 150,
    quality: int = 85,
) -> OptimizeImagesResult:
    """
    优化 PDF 中的图片

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        dpi: 目标 DPI（降低 DPI 可减小文件大小）
        quality: JPEG 质量 (1-100)

    Returns:
        OptimizeImagesResult: 优化结果
    """
    if dpi < 72 or dpi > 300:
        raise InvalidParameterError("DPI 必须在 72-300 之间")

    if quality < 1 or quality > 100:
        raise InvalidParameterError("质量必须在 1-100 之间")

    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        # 获取原始文件大小
        original_size = file_path.stat().st_size

        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        images_processed = 0

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

                images_processed += 1

        # 保存
        doc.save(output_path, deflate=True)
        doc.close()

        # 获取优化后大小
        optimized_size = output_path.stat().st_size
        reduction = (1 - optimized_size / original_size) * 100

        return OptimizeImagesResult(
            output_path=str(output_path),
            original_size=original_size,
            optimized_size=optimized_size,
            reduction_percent=reduction,
            images_processed=images_processed,
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFOptimizeError(f"优化失败: {e}")


def repair_pdf(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
) -> RepairResult:
    """
    修复损坏的 PDF 文件

    尝试修复以下问题:
    - 损坏的 PDF 结构
    - 损坏的对象
    - 损坏的交叉引用表

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径

    Returns:
        RepairResult: 修复结果
    """
    file_path = Path(file_path)
    output_path = Path(output_path)

    if not file_path.exists():
        raise PDFOptimizeError(f"文件不存在: {file_path}")

    try:
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用 pikepdf 尝试打开并重新保存
        try:
            pdf = pikepdf.open(file_path, allow_overwriting_input=True)
            pdf.save(output_path)
            pdf.close()

            return RepairResult(
                output_path=str(output_path),
                success=True,
            )

        except Exception as e:
            # 如果 pikepdf 失败，尝试 PyMuPDF
            # 如果 pikepdf 失败，尝试 PyMuPDF
            try:
                doc = fitz.open(file_path)
                doc.save(output_path)
                doc.close()

                return RepairResult(
                    output_path=str(output_path),
                    success=True,
                )

            except Exception as e2:
                raise RepairFailedError(f"修复失败: {e2}")

    except RepairFailedError:
        raise
    except Exception as e:
        raise PDFOptimizeError(f"修复失败: {e}")
