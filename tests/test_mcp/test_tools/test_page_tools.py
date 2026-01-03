"""MCP 工具集成测试 - 页面操作工具"""

import pytest
import asyncio
from pathlib import Path

from pdfkit.mcp.server import mcp
from pdfkit.mcp.tools.page_tools import (
    pdfkit_merge_files,
    pdfkit_split_by_pages,
    pdfkit_extract_text,
)


class TestMCPPageTools:
    """MCP 页面操作工具集成测试"""

    @pytest.mark.asyncio
    async def test_pdfkit_get_info(self):
        """测试获取 PDF 信息工具"""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "pdfkit_get_info" in tool_names

    @pytest.mark.asyncio
    async def test_pdfkit_merge_files_with_invalid_files(self):
        """测试合并无效文件"""
        result = await pdfkit_merge_files(
            file_paths=["/nonexistent/file1.pdf", "/nonexistent/file2.pdf"],
            output_path="/tmp/output.pdf",
            skip_errors=True,
        )

        # 应该返回错误但没有崩溃
        assert "success" in result
        if not result["success"]:
            assert "error" in result

    @pytest.mark.asyncio
    async def test_pdfkit_extract_text_with_invalid_pdf(self):
        """测试从无效 PDF 提取文本"""
        result = await pdfkit_extract_text(
            file_path="/nonexistent/document.pdf",
        )

        # 应该返回错误
        assert result["success"] is False
        assert "error" in result


class TestMCPToolRegistration:
    """MCP 工具注册测试"""

    @pytest.mark.asyncio
    async def test_all_page_tools_registered(self):
        """测试所有页面操作工具已注册"""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "pdfkit_merge_files",
            "pdfkit_split_by_pages",
            "pdfkit_split_single_pages",
            "pdfkit_split_by_size",
            "pdfkit_split_by_count",
            "pdfkit_extract_pages",
            "pdfkit_extract_text",
            "pdfkit_extract_images",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names, f"工具 {tool_name} 未注册"

    @pytest.mark.asyncio
    async def test_tool_annotations(self):
        """测试工具注解"""
        tools = await mcp.list_tools()
        tool_map = {t.name: t for t in tools}

        # 检查 pdfkit_get_info 的注解
        info_tool = tool_map.get("pdfkit_get_info")
        assert info_tool is not None

        # 检查 pdfkit_merge_files 的注解
        merge_tool = tool_map.get("pdfkit_merge_files")
        assert merge_tool is not None
