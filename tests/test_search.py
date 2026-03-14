"""search 命令测试"""

import json
from pathlib import Path

from typer.testing import CliRunner

from pdfkit.cli import app


runner = CliRunner()


def _run_search(tmp_path: Path, args: list[str]) -> dict:
    output = tmp_path / "search_result.json"
    result = runner.invoke(app, args + ["--format", "json", "-o", str(output)])

    assert result.exit_code == 0
    assert output.exists()

    return json.loads(output.read_text(encoding="utf-8"))


def test_search_basic(sample_pdf: Path, tmp_path: Path):
    data = _run_search(tmp_path, ["search", str(sample_pdf), "-q", "PDFKit"])

    assert data["total_matches"] >= 1
    assert data["matches"]
    assert data["matches"][0]["page"] == 1


def test_search_case_sensitive_no_match(sample_pdf: Path, tmp_path: Path):
    data = _run_search(
        tmp_path,
        ["search", str(sample_pdf), "-q", "pdfkit", "--case-sensitive"],
    )

    assert data["total_matches"] == 0
    assert data["matches"] == []


def test_search_highlight_output(sample_pdf: Path, tmp_path: Path):
    highlight_path = tmp_path / "highlight.pdf"

    data = _run_search(
        tmp_path,
        [
            "search",
            str(sample_pdf),
            "-q",
            "PDFKit",
            "--highlight",
            "--highlight-output",
            str(highlight_path),
        ],
    )

    assert highlight_path.exists()
    assert data["highlight_output"] == str(highlight_path.resolve())


def test_search_invalid_regex(sample_pdf: Path, tmp_path: Path):
    output = tmp_path / "out.json"
    result = runner.invoke(
        app,
        [
            "search",
            str(sample_pdf),
            "-q",
            "(",
            "--regex",
            "--format",
            "json",
            "-o",
            str(output),
        ],
    )

    assert result.exit_code == 1
