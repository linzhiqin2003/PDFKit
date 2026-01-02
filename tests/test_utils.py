"""工具函数测试"""

from pathlib import Path
from pdfkit.utils.file_utils import (
    format_size,
    format_date,
    generate_output_path,
    clean_filename,
    get_file_info,
)


def test_format_size():
    """测试文件大小格式化"""
    assert format_size(1024) == "1.00 KB"
    assert format_size(1024 * 1024) == "1.00 MB"
    assert format_size(1024 * 1024 * 1024) == "1.00 GB"
    assert format_size(500) == "500.00 B"


def test_format_date():
    """测试日期格式化"""
    import time
    timestamp = time.time()
    formatted = format_date(timestamp)
    assert formatted != "-"


def test_clean_filename():
    """测试文件名清理"""
    assert clean_filename("test<>file.pdf") == "test__file.pdf"
    assert clean_filename('test:file.pdf') == "test_file.pdf"
    assert clean_filename("  test.pdf  ") == "test.pdf"


def test_generate_output_path(tmp_path: Path):
    """测试输出路径生成"""
    input_file = tmp_path / "input.pdf"

    # 测试基本后缀
    output = generate_output_path(input_file, suffix="_out")
    assert output.name == "input_out.pdf"

    # 测试前缀
    output = generate_output_path(input_file, prefix="new_")
    assert output.name == "new_input.pdf"

    # 测试扩展名更改
    output = generate_output_path(input_file, new_extension=".txt")
    assert output.name == "input.txt"


def test_get_file_info(tmp_path: Path):
    """测试获取文件信息"""
    # 创建测试文件
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    info = get_file_info(test_file)

    assert info["name"] == "test.txt"
    assert info["is_file"] is True
    assert info["is_dir"] is False
    assert "size" in info
