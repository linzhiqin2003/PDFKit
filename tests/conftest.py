"""Pytest 配置和共享 fixtures"""

import pytest
from pathlib import Path
import fitz


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """创建一个测试用的 PDF 文件"""
    pdf_path = tmp_path / "test.pdf"

    # 创建一个简单的测试 PDF
    doc = fitz.open()
    page = doc.new_page()

    # 添加一些内容
    page.insert_text(
        (50, 50),
        "PDFKit Test Document",
        fontsize=24,
        color=(0, 0, 0)
    )
    page.insert_text(
        (50, 100),
        "This is a test PDF for unit testing.",
        fontsize=12,
        color=(0, 0, 0)
    )

    # 添加元数据
    doc.set_metadata({
        "title": "Test PDF",
        "author": "PDFKit",
        "subject": "Testing",
    })

    doc.save(pdf_path)
    doc.close()

    return pdf_path


@pytest.fixture
def multi_page_pdf(tmp_path: Path) -> Path:
    """创建一个多页测试 PDF"""
    pdf_path = tmp_path / "multi_page.pdf"

    doc = fitz.open()

    for i in range(5):
        page = doc.new_page()
        page.insert_text(
            (50, 50),
            f"Page {i + 1}",
            fontsize=24,
            color=(0, 0, 0)
        )

    doc.save(pdf_path)
    doc.close()

    return pdf_path


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """创建临时输出目录"""
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir
