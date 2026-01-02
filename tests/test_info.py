"""info 命令测试"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from pdfkit.cli import app

runner = CliRunner()


def test_info_command(sample_pdf: Path):
    """测试 info 命令"""
    result = runner.invoke(app, ["info", str(sample_pdf)])

    assert result.exit_code == 0
    assert "PDF 文件信息" in result.stdout
    assert "页数" in result.stdout


def test_info_detailed(sample_pdf: Path):
    """测试 --detailed 选项"""
    result = runner.invoke(app, ["info", str(sample_pdf), "--detailed"])

    assert result.exit_code == 0
    assert "元数据" in result.stdout


def test_info_json(sample_pdf: Path):
    """测试 --json 选项"""
    result = runner.invoke(app, ["info", str(sample_pdf), "--json"])

    assert result.exit_code == 0
    # JSON 输出应该包含 filename
    assert "filename" in result.stdout


def test_info_pages_only(sample_pdf: Path):
    """测试 --pages 选项"""
    result = runner.invoke(app, ["info", str(sample_pdf), "--pages"])

    assert result.exit_code == 0
    # 应该只输出页数
    assert result.stdout.strip().isdigit()


def test_info_size_only(sample_pdf: Path):
    """测试 --size 选项"""
    result = runner.invoke(app, ["info", str(sample_pdf), "--size"])

    assert result.exit_code == 0
    # 应该只输出大小
    assert "KB" in result.stdout or "B" in result.stdout


def test_info_invalid_file():
    """测试无效文件"""
    result = runner.invoke(app, ["info", "nonexistent.pdf"])

    assert result.exit_code == 1
    assert "错误" in result.stdout or "不存在" in result.stdout


def test_meta_command(sample_pdf: Path):
    """测试 meta 子命令"""
    result = runner.invoke(app, ["info", "meta", str(sample_pdf)])

    assert result.exit_code == 0
    assert "元数据" in result.stdout
