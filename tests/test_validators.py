"""验证器测试"""

import pytest
from pathlib import Path
from pdfkit.utils.validators import (
    validate_page_range,
    validate_output_path,
    validate_quality,
    validate_rotation,
    validate_image_format,
)


def test_validate_page_range():
    """测试页面范围验证"""
    # 单页
    pages = validate_page_range("1", 10)
    assert pages == [0]

    # 多个单页
    pages = validate_page_range("1,3,5", 10)
    assert pages == [0, 2, 4]

    # 范围
    pages = validate_page_range("1-5", 10)
    assert pages == [0, 1, 2, 3, 4]

    # 混合
    pages = validate_page_range("1-3,5,7-9", 10)
    assert pages == [0, 1, 2, 4, 6, 7, 8]

    # 边界测试
    pages = validate_page_range("1-10", 10)
    assert len(pages) == 10

    # 超出范围应抛出异常
    with pytest.raises(ValueError):
        validate_page_range("1-15", 10)

    # 无效页码应抛出异常
    with pytest.raises(ValueError):
        validate_page_range("0", 10)

    with pytest.raises(ValueError):
        validate_page_range("abc", 10)


def test_validate_quality():
    """验证质量等级"""
    assert validate_quality("low") is True
    assert validate_quality("medium") is True
    assert validate_quality("high") is True
    assert validate_quality("invalid") is False


def test_validate_rotation():
    """验证旋转角度"""
    assert validate_rotation(0) is True
    assert validate_rotation(90) is True
    assert validate_rotation(180) is True
    assert validate_rotation(270) is True
    assert validate_rotation(45) is False


def test_validate_image_format():
    """验证图片格式"""
    assert validate_image_format("png") is True
    assert validate_image_format("jpg") is True
    assert validate_image_format("jpeg") is True
    assert validate_image_format("webp") is True
    assert validate_image_format("gif") is False


def test_validate_output_path(tmp_path: Path):
    """验证输出路径"""
    input_file = tmp_path / "input.pdf"

    # 自动生成输出路径
    output = validate_output_path(None, input_file, suffix="_out")
    assert "_out" in output.name

    # 指定输出路径
    output = validate_output_path(tmp_path / "output.pdf", input_file)
    assert output.name == "output.pdf"
