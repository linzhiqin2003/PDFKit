"""核心服务单元测试 - PDF 转换"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pdfkit.core.pdf_convert import (
    ConvertToImagesResult,
    ImagesToPDFResult,
    PDFConvertError,
    DependencyNotFoundError,
    UnsupportedFormatError,
)
from pdfkit.mcp.utils import format_size


class TestFormatSize:
    """文件大小格式化测试"""

    def test_format_bytes(self):
        """测试字节格式化"""
        result = format_size(500)
        assert result == "500.0 B"

    def test_format_kb(self):
        """测试 KB 格式化"""
        result = format_size(2048)
        assert result == "2.0 KB"

    def test_format_mb(self):
        """测试 MB 格式化"""
        result = format_size(2 * 1024 * 1024)
        assert result == "2.0 MB"

    def test_format_gb(self):
        """测试 GB 格式化"""
        result = format_size(2 * 1024 * 1024 * 1024)
        assert result == "2.0 GB"


class TestConvertToImagesResult:
    """ConvertToImagesResult 数据类测试"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = ConvertToImagesResult(
            output_dir="/test/output",
            image_count=5,
            format="png",
            dpi=150,
            images=["/test/output/img1.png", "/test/output/img2.png"],
            success=True,
        )
        data = result.to_dict()

        assert data["output_dir"] == "/test/output"
        assert data["image_count"] == 5
        assert data["format"] == "png"
        assert data["dpi"] == 150
        assert len(data["images"]) == 2
        assert data["success"] is True


class TestPDFConvertError:
    """PDFConvertError 测试"""

    def test_error_message(self):
        """测试错误消息"""
        error = PDFConvertError("转换失败")
        assert str(error) == "转换失败"


class TestDependencyNotFoundError:
    """DependencyNotFoundError 测试"""

    def test_inheritance(self):
        """测试继承关系"""
        error = DependencyNotFoundError("缺少依赖")
        assert isinstance(error, PDFConvertError)
        assert str(error) == "缺少依赖"
