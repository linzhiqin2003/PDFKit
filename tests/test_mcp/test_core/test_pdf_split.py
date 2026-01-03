"""核心服务单元测试 - PDF 拆分"""

import pytest
from pathlib import Path

from pdfkit.core.pdf_split import (
    parse_page_range,
    InvalidPageRangeError,
)


class TestParsePageRange:
    """页面范围解析测试"""

    def test_single_page(self):
        """测试单页"""
        result = parse_page_range("1", 10)
        assert result == [0]

    def test_range(self):
        """测试范围"""
        result = parse_page_range("1-3", 10)
        assert result == [0, 1, 2]

    def test_multiple_ranges(self):
        """测试多个范围"""
        result = parse_page_range("1-3,5,7-9", 10)
        assert result == [0, 1, 2, 4, 6, 7, 8]

    def test_invalid_range(self):
        """测试无效范围"""
        with pytest.raises(InvalidPageRangeError):
            parse_page_range("1-15", 10)

    def test_invalid_page(self):
        """测试无效页码"""
        with pytest.raises(InvalidPageRangeError):
            parse_page_range("15", 10)
