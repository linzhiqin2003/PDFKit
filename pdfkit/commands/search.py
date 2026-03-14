"""PDF 文本搜索命令"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import re

import typer
import fitz  # PyMuPDF

from ..utils.console import (
    console,
    print_success,
    print_error,
    print_info,
    print_warning,
    create_progress,
    Icons,
)
from ..utils.validators import validate_pdf_file, validate_page_range, require_unlocked_pdf
from ..utils.file_utils import resolve_path


def _compact_text(text: str) -> str:
    """压缩文本空白为单空格，便于展示"""
    return " ".join(text.split())


def _build_context(text: str, start: int, end: int, context: int) -> Optional[str]:
    """截取匹配上下文"""
    if context <= 0:
        return None
    left = max(0, start - context)
    right = min(len(text), end + context)
    snippet = text[left:right]
    return _compact_text(snippet)


def _format_text_output(matches: List[Dict[str, Any]], total_matches: int, total_pages: int) -> str:
    """格式化文本输出"""
    lines = [f"找到 {total_matches} 处匹配（共 {total_pages} 页）"]
    if total_matches == 0:
        return "\n".join(lines)

    for item in matches:
        context = item.get("context") or item.get("match") or ""
        context = _compact_text(context)
        lines.append(f"第 {item['page']} 页: {context}")

    return "\n".join(lines)


def search(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    query: str = typer.Option(
        ...,
        "--query",
        "-q",
        help="搜索关键词或正则表达式",
    ),
    regex: bool = typer.Option(
        False,
        "--regex",
        help="将查询作为正则表达式",
    ),
    case_sensitive: bool = typer.Option(
        False,
        "--case-sensitive",
        help="区分大小写",
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        "-p",
        help="页面范围，如 1-5,8,10-12",
    ),
    context: int = typer.Option(
        20,
        "--context",
        "-c",
        help="上下文字符数（0 表示不输出上下文）",
    ),
    max_hits: int = typer.Option(
        0,
        "--max-hits",
        help="最大匹配数（0 表示不限制）",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="输出格式: text, json",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出结果文件路径",
    ),
    highlight: bool = typer.Option(
        False,
        "--highlight",
        help="生成高亮 PDF（仅支持非正则搜索）",
    ),
    highlight_output: Optional[Path] = typer.Option(
        None,
        "--highlight-output",
        help="高亮 PDF 输出路径",
    ),
):
    """
    搜索 PDF 文本内容

    示例:
        # 普通搜索
        pdfkit search document.pdf -q "invoice"

        # 正则搜索（不支持高亮）
        pdfkit search document.pdf -q "\\d{4}-\\d{2}-\\d{2}" --regex --format json

        # 生成高亮 PDF
        pdfkit search document.pdf -q "CONFIDENTIAL" --highlight -o hits.json
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    if not require_unlocked_pdf(file, "搜索"):
        raise typer.Exit(1)

    if context < 0:
        print_error("--context 不能为负数")
        raise typer.Exit(1)

    if max_hits < 0:
        print_error("--max-hits 不能为负数")
        raise typer.Exit(1)

    if output_format not in ("text", "json"):
        print_error(f"无效的输出格式: {output_format}")
        print_info("支持的格式: text, json")
        raise typer.Exit(1)

    if regex and highlight:
        print_error("正则搜索暂不支持高亮输出")
        raise typer.Exit(1)

    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern_text = query if regex else re.escape(query)
        pattern = re.compile(pattern_text, flags)
    except re.error as e:
        print_error(f"正则表达式错误: {e}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)
        total_pages = doc.page_count

        # 确定页面范围
        if pages:
            page_list = validate_page_range(pages, total_pages)
        else:
            page_list = list(range(total_pages))

        if not page_list:
            print_error("没有有效的页面范围")
            raise typer.Exit(1)

        results: List[Dict[str, Any]] = []
        total_matches = 0

        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.SEARCH} 搜索中...",
                total=len(page_list),
            )

            stop = False
            for page_num in page_list:
                if stop:
                    break

                page = doc[page_num]
                page_text = page.get_text("text")

                page_matches = []
                for match in pattern.finditer(page_text):
                    page_matches.append(match)
                    if max_hits and (total_matches + len(page_matches)) >= max_hits:
                        break

                rects: List[fitz.Rect] = []
                if not regex and page_matches:
                    rects = page.search_for(query)
                    if case_sensitive:
                        rects = [r for r in rects if page.get_textbox(r) == query]

                    if highlight:
                        for rect in rects[: len(page_matches)]:
                            annot = page.add_highlight_annot(rect)
                            annot.set_colors(stroke=(1, 1, 0), fill=(1, 1, 0))
                            annot.update()

                for idx, match in enumerate(page_matches, start=1):
                    start, end = match.start(), match.end()
                    context_text = _build_context(page_text, start, end, context)

                    bbox = None
                    if rects and idx - 1 < len(rects):
                        rect = rects[idx - 1]
                        bbox = [rect.x0, rect.y0, rect.x1, rect.y1]

                    results.append(
                        {
                            "page": page_num + 1,
                            "index": idx,
                            "match": match.group(0),
                            "start": start,
                            "end": end,
                            "context": context_text,
                            "bbox": bbox,
                        }
                    )

                total_matches += len(page_matches)
                if max_hits and total_matches >= max_hits:
                    stop = True

                progress.update(task, advance=1)

        # 保存高亮 PDF
        highlight_path = None
        if highlight and not regex:
            if highlight_output is None:
                highlight_output = resolve_path(file.parent / f"{file.stem}_highlighted{file.suffix}")
            else:
                highlight_output = resolve_path(highlight_output)

            if resolve_path(file) == highlight_output:
                print_error("高亮输出不能覆盖原文件")
                raise typer.Exit(1)

            doc.save(highlight_output)
            highlight_path = str(highlight_output)

        doc.close()

        output_payload: Dict[str, Any] = {
            "file": str(resolve_path(file)),
            "query": query,
            "regex": regex,
            "case_sensitive": case_sensitive,
            "pages": [p + 1 for p in page_list],
            "total_pages": total_pages,
            "total_matches": total_matches,
            "matches": results,
        }

        if highlight_path:
            output_payload["highlight_output"] = highlight_path

        if output_format == "json":
            output_str = json.dumps(output_payload, ensure_ascii=False, indent=2)
        else:
            output_str = _format_text_output(results, total_matches, total_pages)

        if output:
            output = resolve_path(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(output_str, encoding="utf-8")
            print_success(f"搜索结果已保存: [path]{output}[/]")
        else:
            if output_format == "json":
                console.print_json(output_str)
            else:
                console.print(output_str)

        if total_matches == 0:
            print_warning("未找到匹配内容")
        else:
            print_success(f"搜索完成: [number]{total_matches}[/] 处匹配")

        if highlight_path:
            print_success(f"高亮 PDF 已生成: [path]{highlight_path}[/]")

    except Exception as e:
        print_error(f"搜索失败: {e}")
        raise typer.Exit(1)
