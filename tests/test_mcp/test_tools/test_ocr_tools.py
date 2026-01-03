"""MCP 工具集成测试 - OCR 工具"""

import pytest

from pdfkit.mcp.tools.ocr_tools import (
    pdfkit_ocr_recognize,
    pdfkit_ocr_extract_tables,
    pdfkit_ocr_analyze_layout,
)


class TestMCPOCRTools:
    """MCP OCR 工具集成测试"""

    @pytest.mark.asyncio
    async def test_pdfkit_ocr_recognize_with_invalid_pdf(self):
        """测试 OCR 无效 PDF"""
        result = await pdfkit_ocr_recognize(
            file_path="/nonexistent/document.pdf",
        )

        # 应该返回错误
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_pdfkit_ocr_recognize_invalid_model(self):
        """测试 OCR 无效模型"""
        result = await pdfkit_ocr_recognize(
            file_path="/nonexistent/document.pdf",
            model="invalid_model",
        )

        # 应该返回错误
        assert result["success"] is False
        assert result.get("error_type") == "invalid_model"

    @pytest.mark.asyncio
    async def test_pdfkit_ocr_extract_tables(self):
        """测试表格提取"""
        result = await pdfkit_ocr_extract_tables(
            file_path="/nonexistent/document.pdf",
        )

        # 应该返回错误（文件不存在）
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_pdfkit_ocr_analyze_layout(self):
        """测试版面分析"""
        result = await pdfkit_ocr_analyze_layout(
            file_path="/nonexistent/document.pdf",
        )

        # 应该返回错误（文件不存在）
        assert result["success"] is False


class TestMCPOCRToolRegistration:
    """MCP OCR 工具注册测试"""

    @pytest.mark.asyncio
    async def test_all_ocr_tools_registered(self):
        """测试所有 OCR 工具已注册"""
        from pdfkit.mcp.server import mcp

        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "pdfkit_ocr_recognize",
            "pdfkit_ocr_extract_tables",
            "pdfkit_ocr_analyze_layout",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names, f"工具 {tool_name} 未注册"
