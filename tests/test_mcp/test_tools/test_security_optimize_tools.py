"""MCP 工具集成测试 - 安全和优化工具"""

import pytest

from pdfkit.mcp.tools.security_optimize_tools import (
    pdfkit_encrypt_pdf,
    pdfkit_decrypt_pdf,
    pdfkit_compress_pdf,
    pdfkit_repair_pdf,
)


class TestMCPSecurityTools:
    """MCP 安全工具集成测试"""

    @pytest.mark.asyncio
    async def test_pdfkit_encrypt_pdf_with_invalid_pdf(self):
        """测试加密无效 PDF"""
        result = await pdfkit_encrypt_pdf(
            file_path="/nonexistent/document.pdf",
            output_path="/tmp/output.pdf",
            password="test123",
        )

        # 应该返回错误
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_pdfkit_decrypt_pdf_with_invalid_pdf(self):
        """测试解密无效 PDF"""
        result = await pdfkit_decrypt_pdf(
            file_path="/nonexistent/document.pdf",
            output_path="/tmp/output.pdf",
            password="test123",
        )

        # 应该返回错误
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_pdfkit_protect_pdf(self):
        """测试设置权限"""
        result = await pdfkit_protect_pdf(
            file_path="/nonexistent/document.pdf",
            output_path="/tmp/output.pdf",
            owner_password="owner123",
            no_print=True,
        )

        # 应该返回错误
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_pdfkit_clean_metadata(self):
        """测试清除元数据"""
        result = await pdfkit_clean_metadata(
            file_path="/nonexistent/document.pdf",
            output_path="/tmp/output.pdf",
        )

        # 应该返回错误
        assert result["success"] is False


class TestMCPOptimizeTools:
    """MCP 优化工具集成测试"""

    @pytest.mark.asyncio
    async def test_pdfkit_compress_pdf_invalid_quality(self):
        """测试压缩无效质量参数"""
        result = await pdfkit_compress_pdf(
            file_path="/nonexistent/document.pdf",
            output_path="/tmp/output.pdf",
            quality="invalid",
        )

        # 应该返回错误
        assert result["success"] is False
        assert result.get("error_type") == "invalid_parameter"

    @pytest.mark.asyncio
    async def test_pdfkit_optimize_images(self):
        """测试优化图片"""
        result = await pdfkit_optimize_images(
            file_path="/nonexistent/document.pdf",
            output_path="/tmp/output.pdf",
        )

        # 应该返回错误
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_pdfkit_repair_pdf(self):
        """测试修复 PDF"""
        result = await pdfkit_repair_pdf(
            file_path="/nonexistent/document.pdf",
            output_path="/tmp/output.pdf",
        )

        # 应该返回错误
        assert result["success"] is False


class TestMCPSecurityOptimizeToolRegistration:
    """MCP 安全/优化工具注册测试"""

    @pytest.mark.asyncio
    async def test_all_security_tools_registered(self):
        """测试所有安全工具已注册"""
        from pdfkit.mcp.server import mcp

        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "pdfkit_encrypt_pdf",
            "pdfkit_decrypt_pdf",
            "pdfkit_protect_pdf",
            "pdfkit_clean_metadata",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names, f"工具 {tool_name} 未注册"

    @pytest.mark.asyncio
    async def test_all_optimize_tools_registered(self):
        """测试所有优化工具已注册"""
        from pdfkit.mcp.server import mcp

        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "pdfkit_compress_pdf",
            "pdfkit_optimize_images",
            "pdfkit_repair_pdf",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names, f"工具 {tool_name} 未注册"
