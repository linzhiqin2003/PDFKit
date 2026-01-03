"""MCP 测试配置"""

import pytest
from pathlib import Path


# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def sample_pdf_path():
    """示例 PDF 文件路径"""
    # 使用项目中现有的测试 PDF
    project_root = Path(__file__).parent.parent.parent
    return project_root / "docs" / "test_data.pdf"


@pytest.fixture
def output_dir(tmp_path):
    """临时输出目录"""
    output = tmp_path / "output"
    output.mkdir()
    return output
