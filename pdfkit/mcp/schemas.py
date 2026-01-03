"""MCP 输入输出模型定义

使用 Pydantic 定义所有 MCP 工具的输入和输出模型。
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any, Union
from enum import Enum
from pathlib import Path


# ==================== 通用模型 ====================

class PageRangeInput(BaseModel):
    """页面范围输入"""
    start: int = Field(description="起始页（1-indexed）", ge=1)
    end: Optional[int] = Field(None, description="结束页（含），不填则为单页", ge=1)


class CompressionQuality(str, Enum):
    """压缩质量等级"""
    LOW = "low"           # 最小文件，较低质量
    MEDIUM = "medium"     # 平衡
    HIGH = "high"         # 高质量，较大文件


class ImageFormat(str, Enum):
    """图片格式"""
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"
    BMP = "bmp"


class OCRModel(str, Enum):
    """OCR 模型"""
    FLASH = "flash"   # 快速模型
    PLUS = "plus"     # 高精度模型


class OCRFormat(str, Enum):
    """OCR 输出格式"""
    TEXT = "text"     # 纯文本
    MARKDOWN = "md"   # Markdown
    JSON = "json"     # JSON 格式


class WatermarkLayer(str, Enum):
    """水印层级"""
    FOREGROUND = "foreground"   # 前景
    BACKGROUND = "background"   # 背景


class RotationAngle(int, Enum):
    """旋转角度"""
    D90 = 90
    D180 = 180
    D270 = 270


class PageSize(str, Enum):
    """页面大小预设"""
    A4 = "a4"
    A3 = "a3"
    LETTER = "letter"
    LEGAL = "legal"


class Alignment(str, Enum):
    """对齐方式"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


# ==================== 输出模型 ====================

class PDFInfo(BaseModel):
    """PDF 基本信息"""
    filename: str = Field(description="文件名")
    path: str = Field(description="完整路径")
    size_bytes: int = Field(description="文件大小（字节）")
    size_human: str = Field(description="文件大小（人类可读）")
    page_count: int = Field(description="页数")
    version: str = Field(description="PDF 版本")
    is_encrypted: bool = Field(description="是否加密")
    # 元数据（可选）
    title: Optional[str] = Field(None, description="标题")
    author: Optional[str] = Field(None, description="作者")
    subject: Optional[str] = Field(None, description="主题")
    keywords: Optional[str] = Field(None, description="关键词")
    creator: Optional[str] = Field(None, description="创建工具")
    producer: Optional[str] = Field(None, description="PDF 生成器")
    created: Optional[str] = Field(None, description="创建时间")
    modified: Optional[str] = Field(None, description="修改时间")


class MergeResult(BaseModel):
    """合并结果"""
    output_path: str = Field(description="输出文件路径")
    total_files: int = Field(description="合并的文件数量")
    total_pages: int = Field(description="总页数")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


class SplitResult(BaseModel):
    """拆分结果"""
    output_files: List[str] = Field(description="输出文件路径列表")
    total_output: int = Field(description="输出文件数量")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


class ExtractPagesResult(BaseModel):
    """页面提取结果"""
    output_path: str = Field(description="输出文件路径")
    pages_extracted: List[int] = Field(description="提取的页码列表")
    page_count: int = Field(description="提取的页数")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


class DeletePagesResult(BaseModel):
    """页面删除结果"""
    output_path: str = Field(description="输出文件路径")
    pages_deleted: List[int] = Field(description="删除的页码列表")
    remaining_pages: int = Field(description="剩余页数")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


class RotatePagesResult(BaseModel):
    """页面旋转结果"""
    output_path: str = Field(description="输出文件路径")
    pages_rotated: List[int] = Field(description="旋转的页码列表")
    angle: int = Field(description="旋转角度")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


class ConvertToImagesResult(BaseModel):
    """PDF 转图片结果"""
    output_dir: str = Field(description="输出目录")
    output_files: List[str] = Field(description="输出图片路径列表")
    total_images: int = Field(description="生成图片数量")
    format: str = Field(description="图片格式")
    dpi: int = Field(description="DPI")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


class OCRResult(BaseModel):
    """OCR 识别结果"""
    page_results: List[Dict[str, Any]] = Field(description="每页识别结果")
    total_pages: int = Field(description="总页数")
    model_used: str = Field(description="使用的模型")
    format: str = Field(description="输出格式")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


class CompressResult(BaseModel):
    """压缩结果"""
    output_path: str = Field(description="输出文件路径")
    original_size: int = Field(description="原始大小（字节）")
    compressed_size: int = Field(description="压缩后大小（字节）")
    compression_ratio: float = Field(description="压缩比例 (%)")
    quality: str = Field(description="质量等级")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


class EncryptResult(BaseModel):
    """加密结果"""
    output_path: str = Field(description="输出文件路径")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


class DecryptResult(BaseModel):
    """解密结果"""
    output_path: str = Field(description="输出文件路径")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


class WatermarkResult(BaseModel):
    """水印添加结果"""
    output_path: str = Field(description="输出文件路径")
    watermark_type: str = Field(description="水印类型 (text/image)")
    success: bool = Field(description="是否成功")
    message: str = Field(description="状态消息")


# ==================== 工具响应模型 ====================

class ToolResponse(BaseModel):
    """通用工具响应"""
    success: bool = Field(description="操作是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="返回数据")
    error: Optional[str] = Field(None, description="错误信息")
    error_type: Optional[str] = Field(None, description="错误类型")
    suggestion: Optional[str] = Field(None, description="处理建议")


# ==================== 导出所有模型 ====================

__all__ = [
    # 通用模型
    "PageRangeInput",
    "CompressionQuality",
    "ImageFormat",
    "OCRModel",
    "OCRFormat",
    "WatermarkLayer",
    "RotationAngle",
    "PageSize",
    "Alignment",
    # 输出模型
    "PDFInfo",
    "MergeResult",
    "SplitResult",
    "ExtractPagesResult",
    "DeletePagesResult",
    "RotatePagesResult",
    "ConvertToImagesResult",
    "OCRResult",
    "CompressResult",
    "EncryptResult",
    "DecryptResult",
    "WatermarkResult",
    # 工具响应
    "ToolResponse",
]
