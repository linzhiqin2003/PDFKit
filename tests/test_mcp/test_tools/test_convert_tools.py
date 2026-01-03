"""MCP 工具集成测试 - 转换工具"""

import pytest

from pdfkit.mcp.tools.convert_tools import (
    pdfkit_pdf_to_images,
    pdfkit_images_to_pdf,
    pdfkit_pdf_to_word,
)


class TestMCPConvertTools:
    """MCP 转换工具集成测试"""

    @pytest.mark.asyncio
    async def test_pdfkit_pdf_to_images_with_invalid_pdf(self):
        """测试转换无效 PDF"""
        result = await pdfkit_pdf_to_images(
            file_path="/nonexistent/document.pdf",
            output_dir="/tmp/output",
        )

        # 应该返回错误
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_pdfkit_pdf_to_word_with_invalid_pdf(self):
        """测试 PDF 转 Word"""
        result = await pdfkit_pdf_to_word(
            file_path="/nonexistent/document.pdf",
            output_path="/tmp/output.docx",
        )

        # 应该返回错误
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_pdfkit_images_to_pdf_with_no_images(self):
        """测试无图片转 PDF"""
        result = await pdfkit_images_to_pdf(
            image_paths=[],
            output_path="/tmp/output.pdf",
        )

        # 应该返回错误
        assert result["success"] is False


class TestMCPConvertToolRegistration:
    """MCP 转换工具注册测试"""

    @pytest.mark.asyncio
    async def test_all_convert_tools_registered(self):
        """测试所有转换工具已注册"""
        from pdfkit.mcp.server import mcp

        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "pdfkit_pdf_to_images",
            "pdfkit_images_to_pdf",
            "pdfkit_pdf_to_word",
            "pdfkit_pdf_to_html",
            "pdfkit_pdf_to_markdown",
            "pdfkit_html_to_pdf",
            "pdfkit_url_to_pdf",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names, f"工具 {tool_name} 未注册"
