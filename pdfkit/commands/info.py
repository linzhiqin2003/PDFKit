"""PDF 信息查看命令"""

from pathlib import Path
from typing import Optional
import typer
from rich.table import Table
from rich import box
import fitz  # PyMuPDF

from ..utils.console import (
    console, print_success, print_error, print_info, print_warning, Icons,
    print_table_with_style, print_structured_error
)
from ..utils.validators import validate_pdf_file
from ..utils.file_utils import format_size, format_date
from ..utils.platform import (
    get_system_info, check_dependencies, get_app_config_dir,
    get_documents_dir, get_cache_dir, find_poppler_path
)

# 创建 info 子应用
app = typer.Typer(help="查看 PDF 信息")


@app.command()
def show(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="显示详细信息（包括元数据）",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="JSON 格式输出",
    ),
    pages: bool = typer.Option(
        False,
        "--pages",
        "-p",
        help="仅显示页数",
    ),
    size: bool = typer.Option(
        False,
        "--size",
        "-s",
        help="仅显示文件大小",
    ),
):
    """
    查看 PDF 文件的详细信息

    示例:
        pdfkit info document.pdf
        pdfkit info document.pdf --detailed
        pdfkit info document.pdf --json
        pdfkit info document.pdf --pages
    """
    # 验证文件
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        # 打开 PDF
        doc = fitz.open(file)

        # 检查是否加密且无法访问
        if doc.is_encrypted and doc.needs_pass:
            print_error(f"PDF 文件已加密，需要密码才能读取")
            print_info("提示: 使用 pdfkit security decrypt <文件> -p <密码> 解密后再操作")
            doc.close()
            raise typer.Exit(1)

        # 基础信息
        info = {
            "filename": file.name,
            "path": str(file.absolute()),
            "size": format_size(file.stat().st_size),
            "size_bytes": file.stat().st_size,
            "pages": doc.page_count,
            "version": "PDF",
            "encrypted": doc.is_encrypted,
        }

        # 元数据 (可能为 None)
        metadata = doc.metadata or {}
        if metadata:
            info["version"] = f"PDF {metadata.get('format', 'Unknown')}"
            info["title"] = metadata.get("title", "-")
            info["author"] = metadata.get("author", "-")
            info["subject"] = metadata.get("subject", "-")
            info["keywords"] = metadata.get("keywords", "-")
            info["creator"] = metadata.get("creator", "-")
            info["producer"] = metadata.get("producer", "-")
            info["created"] = metadata.get("creationDate", "-")
            info["modified"] = metadata.get("modDate", "-")

        # 简单输出模式
        if pages:
            console.print(str(info["pages"]))
            doc.close()
            return

        if size:
            console.print(info["size"])
            doc.close()
            return

        # 输出
        if json_output:
            import json
            console.print_json(json.dumps(info, ensure_ascii=False, indent=2))
        else:
            _print_info_table(info, detailed)

        doc.close()

    except Exception as e:
        print_error(f"读取 PDF 失败: {e}")
        raise typer.Exit(1)


@app.command("meta")
def metadata(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="JSON 格式输出",
    ),
):
    """
    仅显示 PDF 元数据

    示例:
        pdfkit info meta document.pdf
        pdfkit info meta document.pdf --json
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        doc = fitz.open(file)

        # 检查是否加密且无法访问
        if doc.is_encrypted and doc.needs_pass:
            print_error(f"PDF 文件已加密，需要密码才能读取元数据")
            print_info("提示: 使用 pdfkit security decrypt <文件> -p <密码> 解密后再操作")
            doc.close()
            raise typer.Exit(1)

        meta = doc.metadata or {}

        if not meta:
            print_info("该 PDF 没有元数据")
            doc.close()
            return

        if json_output:
            import json
            console.print_json(json.dumps(meta, ensure_ascii=False, indent=2))
        else:
            # 使用工业风格表格
            columns = ["属性", "值"]
            rows = [[key, str(value)] for key, value in meta.items() if value]

            print_table_with_style(
                title=f"{Icons.PDF} PDF 元数据",
                columns=columns,
                rows=rows,
                style="industrial"
            )

        doc.close()

    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"读取元数据失败: {e}")
        raise typer.Exit(1)


def _print_info_table(info: dict, detailed: bool):
    """打印信息表格 - 使用工业风格"""

    # 使用工业风格表格
    columns = ["属性", "值"]
    rows = [
        ["文件名", info['filename']],
        ["路径", f"[dim]{info['path']}[/]"],
        ["文件大小", f"[size]{info['size']}[/]"],
        ["页数", f"{info['pages']} 页"],
        ["PDF 版本", info['version']],
        ["加密状态", f"[pdf.encrypted]{Icons.ENCRYPT} 已加密[/]" if info['encrypted'] else f"[success]{Icons.DECRYPT} 未加密[/]"],
    ]

    # 详细信息
    if detailed:
        rows.append(["", ""])  # 空行分隔
        rows.append(["[title]• 元数据[/]", ""])
        rows.append(["标题", info.get('title', '-')])
        rows.append(["作者", info.get('author', '-')])
        rows.append(["主题", info.get('subject', '-')])
        rows.append(["关键词", info.get('keywords', '-')])
        rows.append(["创建程序", info.get('creator', '-')])
        rows.append(["PDF 生成器", info.get('producer', '-')])
        rows.append(["创建时间", f"[date]{info.get('created', '-')}[/]"])
        rows.append(["修改时间", f"[date]{info.get('modified', '-')}[/]"])

    print_table_with_style(
        title=f"{Icons.PDF} PDF 文件信息",
        columns=columns,
        rows=rows,
        style="industrial"
    )


@app.command("system")
def system_info(
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="JSON 格式输出",
    ),
):
    """
    显示系统信息和依赖安装状态

    用于诊断安装问题或提交 Bug 报告时附上系统信息。

    示例:
        pdfkit info system
        pdfkit info system --json
    """
    import json as json_module
    from .. import __version__

    # 收集系统信息
    sys_info = get_system_info()
    
    # 收集路径信息
    paths = {
        "config_dir": str(get_app_config_dir()),
        "documents_dir": str(get_documents_dir()),
        "cache_dir": str(get_cache_dir()),
    }
    
    # 检查 Poppler
    poppler = find_poppler_path()
    paths["poppler_path"] = str(poppler) if poppler else None
    
    # 检查依赖
    deps = check_dependencies()
    
    # JSON 输出
    if json_output:
        output = {
            "pdfkit_version": __version__,
            "system": sys_info,
            "paths": paths,
            "dependencies": {k: {"installed": v[0], "info": v[1]} for k, v in deps.items()},
        }
        console.print_json(json_module.dumps(output, ensure_ascii=False, indent=2))
        return
    
    # 表格输出
    # 系统信息表
    sys_columns = ["属性", "值"]
    sys_rows = [
        ["PDFKit 版本", f"[success]{__version__}[/]"],
        ["操作系统", f"[info]{sys_info['platform']}[/]"],
        ["系统版本", sys_info['platform_version']],
        ["架构", sys_info['architecture']],
        ["Python 版本", f"[number]{sys_info['python_version']}[/]"],
    ]

    if sys_info.get('windows_edition'):
        sys_rows.append(["Windows 版本", sys_info['windows_edition']])
        sys_rows.append(["64-bit", "✓" if sys_info.get('is_64bit') else "✗"])
    elif sys_info.get('macos_version'):
        sys_rows.append(["macOS 版本", sys_info['macos_version']])

    print_table_with_style(
        title="🖥️ 系统信息",
        columns=sys_columns,
        rows=sys_rows,
        style="industrial"
    )

    console.print()

    # 路径信息表
    path_columns = ["路径类型", "位置"]
    path_rows = [
        ["配置目录", f"[path]{paths['config_dir']}[/]"],
        ["文档目录", f"[path]{paths['documents_dir']}[/]"],
        ["缓存目录", f"[path]{paths['cache_dir']}[/]"],
    ]

    if paths['poppler_path']:
        path_rows.append(["Poppler 路径", f"[success]{paths['poppler_path']}[/]"])
    else:
        path_rows.append(["Poppler 路径", "[warning]未找到[/]"])

    print_table_with_style(
        title="📁 配置路径",
        columns=path_columns,
        rows=path_rows,
        style="industrial"
    )

    console.print()

    # 依赖状态表
    dep_columns = ["依赖", "状态", "信息"]
    dep_rows = []

    for name, (installed, info_text) in deps.items():
        if installed:
            status = f"[success]{Icons.SUCCESS}[/]"
            info_display = f"[dim]{info_text}[/]"
        else:
            status = f"[error]{Icons.ERROR}[/]"
            info_display = f"[warning]{info_text[:50]}...[/]" if len(info_text) > 50 else f"[warning]{info_text}[/]"

        dep_rows.append([name, status, info_display])

    print_table_with_style(
        title="📦 可选依赖状态",
        columns=dep_columns,
        rows=dep_rows,
        style="industrial"
    )
    
    # 提示信息
    console.print()
    
    missing_deps = [name for name, (installed, _) in deps.items() if not installed]
    if missing_deps:
        print_warning("以下可选依赖未安装:")
        for dep in missing_deps:
            console.print(f"  • {dep}", style="dim")
        console.print()
        print_info("安装可选依赖:")
        # 使用 \\[ 来转义方括号，防止 Rich 把 [full] 当作样式标签
        print_info("  pip install 'pdfkit-cli\\[full]'  # 安装所有可选依赖")
        print_info("  pip install 'pdfkit-cli\\[weasyprint]'  # 仅安装 WeasyPrint")
        
        if sys_info['platform'] == 'Windows':
            console.print()
            print_info("Windows 用户请参阅: docs/windows-installation.md")
    else:
        print_success("所有可选依赖已安装！")

