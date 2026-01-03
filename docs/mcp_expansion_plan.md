# PDFKit MCP 服务器扩展项目规划书

> 将 PDFKit CLI 工具扩展为 MCP (Model Context Protocol) 服务器，使 AI 模型能够直接调用 PDF 处理功能

## 📋 目录

1. [项目概述](#1-项目概述)
2. [现状分析](#2-现状分析)
3. [架构设计](#3-架构设计)
   - [3.5 核心层抽取方案](#35-核心层抽取方案)
   - [3.6 代码复用示例](#36-代码复用示例)
4. [MCP Tools 设计](#4-mcp-tools-设计)
5. [实施计划](#5-实施计划)
6. [技术规范](#6-技术规范)
7. [测试策略](#7-测试策略)
8. [风险与缓解](#8-风险与缓解)

---

## 1. 项目概述

### 1.1 项目背景

PDFKit 是一个功能全面的 PDF 命令行处理工具，包含 40+ 功能命令，覆盖 PDF 处理的所有场景。现希望将其扩展为 MCP 服务器，使 LLM 可以直接调用这些功能，实现 AI 驱动的 PDF 自动化处理。

### 1.2 项目目标

1. **保持现有功能完整**：不破坏现有 CLI 工具的工作能力
2. **新增 MCP 服务器**：提供标准 MCP 协议接口
3. **代码复用**：最大化复用现有业务逻辑
4. **易于维护**：采用清晰的模块分离架构

### 1.3 预期成果

- 一个可独立运行的 MCP 服务器
- 支持 stdio 和 Streamable HTTP 两种传输模式
- 覆盖所有核心 PDF 操作的 MCP Tools
- 完整的文档和测试覆盖

---

## 2. 现状分析

### 2.1 现有项目结构

```
pdftools/
├── pdfkit/
│   ├── __init__.py          # 版本信息
│   ├── __main__.py           # CLI 入口
│   ├── cli.py                # Typer CLI 主应用
│   ├── commands/             # 命令模块 (18 个文件)
│   │   ├── info.py           # 信息查看
│   │   ├── merge.py          # 合并
│   │   ├── split.py          # 拆分
│   │   ├── extract.py        # 提取
│   │   ├── ocr.py            # OCR 识别
│   │   └── ...               # 更多命令
│   ├── core/                 # 核心业务逻辑
│   │   └── ocr_handler.py    # OCR 处理器
│   ├── utils/                # 工具函数
│   │   ├── config.py         # 配置管理
│   │   ├── console.py        # 终端输出
│   │   ├── file_utils.py     # 文件工具
│   │   └── validators.py     # 验证器
│   ├── styles/               # 样式定义
│   └── templates/            # 模板文件
├── tests/                    # 测试
├── docs/                     # 文档
├── pyproject.toml            # 项目配置
└── README.md
```

### 2.2 现有功能清单

| 分类 | 命令 | 功能描述 |
|------|------|----------|
| 基础操作 | `info` | 查看 PDF 信息 |
| 基础操作 | `extract` | 提取内容 (text/images/tables/pages) |
| 页面操作 | `split` | 拆分 PDF |
| 页面操作 | `merge` | 合并 PDF |
| 页面操作 | `delete` | 删除页面 |
| 页面操作 | `rotate` | 旋转页面 |
| 页面操作 | `reorder` | 重排页面 |
| 页面操作 | `reverse` | 反转顺序 |
| 格式转换 | `convert to-image` | PDF 转图片 |
| 格式转换 | `convert from-images` | 图片转 PDF |
| 格式转换 | `convert to-word` | PDF 转 Word |
| 格式转换 | `convert to-html` | PDF 转 HTML |
| 格式转换 | `convert from-html` | HTML 转 PDF |
| 编辑 | `edit watermark` | 添加水印 |
| 编辑 | `header` | 添加页眉 |
| 编辑 | `footer` | 添加页脚 |
| 编辑 | `edit crop` | 裁剪页面 |
| 编辑 | `edit resize` | 调整大小 |
| 安全 | `security encrypt` | 加密 PDF |
| 安全 | `security decrypt` | 解密 PDF |
| 优化 | `optimize compress` | 压缩 PDF |
| 优化 | `optimize images` | 优化图片 |
| 优化 | `optimize repair` | 修复 PDF |
| OCR | `ocr recognize` | 文字识别 |
| OCR | `ocr table` | 表格提取 |
| OCR | `ocr layout` | 版面分析 |
| 批量 | `batch` | 批量处理 |

### 2.3 技术栈

- **Python**: >= 3.10
- **CLI 框架**: Typer + Rich
- **PDF 处理**: PyMuPDF, pypdf, pdfplumber, pikepdf
- **OCR**: 阿里百炼 Qwen3-VL

---

## 3. 架构设计

### 3.1 设计原则

1. **关注点分离**：MCP 层仅负责协议适配，业务逻辑保持在 core 层
2. **向后兼容**：不修改现有 CLI 命令的行为
3. **渐进式增强**：分阶段添加 MCP 支持

### 3.2 目标架构

```
pdftools/
├── pdfkit/
│   ├── __init__.py
│   ├── __main__.py           # CLI 入口（保持不变）
│   ├── cli.py                # CLI 应用（保持不变）
│   ├── commands/             # CLI 命令（保持不变）
│   ├── core/                 # 核心业务逻辑（抽取共享）
│   │   ├── __init__.py
│   │   ├── ocr_handler.py    # OCR 处理器
│   │   ├── pdf_info.py       # ★ 新增：PDF 信息服务
│   │   ├── pdf_merge.py      # ★ 新增：PDF 合并服务
│   │   ├── pdf_split.py      # ★ 新增：PDF 拆分服务
│   │   ├── pdf_extract.py    # ★ 新增：内容提取服务
│   │   ├── pdf_convert.py    # ★ 新增：格式转换服务
│   │   ├── pdf_edit.py       # ★ 新增：编辑服务
│   │   ├── pdf_security.py   # ★ 新增：安全服务
│   │   └── pdf_optimize.py   # ★ 新增：优化服务
│   ├── mcp/                  # ★ 新增：MCP 服务器模块
│   │   ├── __init__.py
│   │   ├── server.py         # MCP 服务器主入口
│   │   ├── tools/            # MCP Tools 定义
│   │   │   ├── __init__.py
│   │   │   ├── info_tools.py     # 信息查看工具
│   │   │   ├── page_tools.py     # 页面操作工具
│   │   │   ├── convert_tools.py  # 格式转换工具
│   │   │   ├── edit_tools.py     # 编辑工具
│   │   │   ├── security_tools.py # 安全工具
│   │   │   ├── optimize_tools.py # 优化工具
│   │   │   └── ocr_tools.py      # OCR 工具
│   │   ├── schemas.py        # Pydantic 输入输出模型
│   │   └── utils.py          # MCP 专用工具函数
│   ├── utils/                # 共享工具（保持不变）
│   └── styles/               # 样式定义（保持不变）
├── tests/
│   ├── test_cli/             # CLI 测试（现有）
│   └── test_mcp/             # ★ 新增：MCP 测试
├── docs/
│   └── mcp_tools_reference.md # ★ 新增：MCP 工具参考
└── pyproject.toml            # 更新依赖和入口点
```

### 3.3 模块依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                      用户接口层                              │
│  ┌─────────────────────┐    ┌─────────────────────────┐     │
│  │   CLI (Typer)       │    │   MCP Server (FastMCP)  │     │
│  │   pdfkit/cli.py     │    │   pdfkit/mcp/server.py  │     │
│  └──────────┬──────────┘    └───────────┬─────────────┘     │
└─────────────┼───────────────────────────┼───────────────────┘
              │                           │
              ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      核心业务层                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  pdfkit/core/                        │    │
│  │  pdf_info.py │ pdf_merge.py │ pdf_split.py │ ...    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                      基础设施层                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐   │
│  │ pdfkit/utils/  │  │ 第三方库       │  │ 外部服务     │   │
│  │ config, file.. │  │ PyMuPDF, etc.  │  │ 阿里百炼 OCR │   │
│  └────────────────┘  └────────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 重构策略

为了最小化对现有代码的影响，采用以下策略：

1. **提取核心逻辑**：从 `commands/*.py` 中提取业务逻辑到 `core/*.py`
2. **保留 CLI 接口**：`commands/*.py` 调用 `core/*.py` 的服务
3. **新增 MCP 层**：`mcp/tools/*.py` 同样调用 `core/*.py` 的服务

### 3.5 核心层抽取方案

#### 3.5.1 现有代码问题分析

现有 CLI 命令函数**不能直接被 MCP 调用**，原因如下：

| 问题 | 示例代码 | 影响 |
|------|----------|------|
| **耦合 CLI 框架** | `typer.Exit(1)`, `typer.Argument` | MCP 需要返回数据，不能抛 Exit |
| **耦合终端输出** | `console.print()`, `print_success()` | MCP 不需要终端美化输出 |
| **混合业务逻辑和展示** | 获取信息 + 打印表格在同一函数 | 逻辑和展示没分离 |

**现有代码示例（`commands/info.py`）**:

```python
@app.command()
def show(file: Path, detailed: bool = False):
    # ❌ 耦合验证逻辑
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)  # ❌ 抛出 CLI 异常

    try:
        doc = fitz.open(file)
        
        # ✅ 这部分是核心业务逻辑，可以抽取
        info = {
            "filename": file.name,
            "path": str(file.absolute()),
            "size": format_size(file.stat().st_size),
            "pages": doc.page_count,
            ...
        }
        
        # ❌ 耦合终端输出
        if json_output:
            console.print_json(json.dumps(info))
        else:
            _print_info_table(info, detailed)
            
    except Exception as e:
        print_error(f"读取 PDF 失败: {e}")  # ❌ 终端输出
        raise typer.Exit(1)  # ❌ CLI 异常
```

#### 3.5.2 抽取后的核心层设计

**核心服务模块（`core/pdf_info.py`）**:

```python
"""PDF 信息服务 - 核心业务逻辑

此模块包含与 PDF 信息获取相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass
import fitz  # PyMuPDF

from ..utils.file_utils import format_size


@dataclass
class PDFInfo:
    """PDF 文件信息"""
    filename: str
    path: str
    size_bytes: int
    size_human: str
    page_count: int
    version: str
    is_encrypted: bool
    # 元数据（可选）
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "filename": self.filename,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "size_human": self.size_human,
            "page_count": self.page_count,
            "version": self.version,
            "is_encrypted": self.is_encrypted,
            "title": self.title,
            "author": self.author,
            # ...
        }


# ============ 自定义异常 ============

class PDFInfoError(Exception):
    """PDF 信息获取错误"""
    pass

class PDFEncryptedError(PDFInfoError):
    """PDF 加密错误"""
    pass

class PDFNotFoundError(PDFInfoError):
    """PDF 文件不存在"""
    pass


# ============ 核心函数 ============

def get_pdf_info(
    file_path: Union[str, Path],
    detailed: bool = False,
) -> PDFInfo:
    """
    获取 PDF 文件的基本信息
    
    Args:
        file_path: PDF 文件路径
        detailed: 是否获取详细元数据
        
    Returns:
        PDFInfo: PDF 文件信息对象
        
    Raises:
        PDFNotFoundError: 文件不存在
        PDFEncryptedError: 文件加密且无法读取
        PDFInfoError: 其他读取错误
    """
    path = Path(file_path)
    
    # 验证文件存在
    if not path.exists():
        raise PDFNotFoundError(f"文件不存在: {file_path}")
    
    if not path.suffix.lower() == '.pdf':
        raise PDFInfoError(f"不是 PDF 文件: {file_path}")
    
    try:
        doc = fitz.open(path)
        
        # 检查加密
        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise PDFEncryptedError(
                f"PDF 文件已加密，需要密码才能读取: {file_path}"
            )
        
        # 构建信息对象
        info = PDFInfo(
            filename=path.name,
            path=str(path.absolute()),
            size_bytes=path.stat().st_size,
            size_human=format_size(path.stat().st_size),
            page_count=doc.page_count,
            version="PDF",
            is_encrypted=doc.is_encrypted,
        )
        
        # 元数据
        if detailed:
            metadata = doc.metadata or {}
            info.title = metadata.get("title") or None
            info.author = metadata.get("author") or None
            # ...
        
        doc.close()
        return info
        
    except PDFInfoError:
        raise
    except Exception as e:
        raise PDFInfoError(f"读取 PDF 失败: {e}")


def get_page_count(file_path: Union[str, Path]) -> int:
    """快速获取 PDF 页数"""
    info = get_pdf_info(file_path, detailed=False)
    return info.page_count


def get_metadata(file_path: Union[str, Path]) -> dict:
    """获取 PDF 元数据"""
    path = Path(file_path)
    
    if not path.exists():
        raise PDFNotFoundError(f"文件不存在: {file_path}")
    
    try:
        doc = fitz.open(path)
        metadata = doc.metadata or {}
        doc.close()
        return metadata
    except Exception as e:
        raise PDFInfoError(f"读取元数据失败: {e}")
```

### 3.6 代码复用示例

#### 3.6.1 复用架构图

```
                    ┌─────────────────────────────────────┐
                    │           pdfkit/core/              │
                    │  ┌─────────────────────────────┐    │
                    │  │  pdf_info.py                │    │
                    │  │  ・get_pdf_info()           │    │
                    │  │  ・get_page_count()         │    │  ← 核心业务逻辑
                    │  │  ・get_metadata()           │    │    (纯数据处理)
                    │  └─────────────────────────────┘    │
                    └──────────────┬──────────────────────┘
                                   │
               ┌───────────────────┴───────────────────┐
               │                                       │
               ▼                                       ▼
    ┌─────────────────────┐             ┌─────────────────────┐
    │   CLI 命令           │             │   MCP 工具          │
    │   commands/info.py   │             │   mcp/tools/info.py │
    │                      │             │                      │
    │   from ..core import │             │   from ...core import│
    │     get_pdf_info     │             │     get_pdf_info    │
    │                      │             │                      │
    │   + CLI 装饰器       │             │   + MCP 装饰器       │
    │   + 终端美化输出     │             │   + 返回结构化数据   │
    │   + typer.Exit 处理  │             │   + 错误格式化       │
    └─────────────────────┘             └─────────────────────┘
```

#### 3.6.2 CLI 调用 core 示例

```python
# pdfkit/commands/info.py (重构后)

from pathlib import Path
import typer

from ..core import get_pdf_info, PDFInfoError, PDFEncryptedError
from ..utils.console import console, print_error, print_info

app = typer.Typer(help="查看 PDF 信息")

@app.command()
def show(
    file: Path = typer.Argument(..., help="PDF 文件路径"),
    detailed: bool = typer.Option(False, "--detailed", "-d"),
    json_output: bool = typer.Option(False, "--json", "-j"),
):
    """查看 PDF 文件的详细信息"""
    try:
        # 👉 调用核心函数（一行代码）
        info = get_pdf_info(file, detailed=detailed)
        
        # CLI 专用：格式化输出
        if json_output:
            import json
            console.print_json(json.dumps(info.to_dict()))
        else:
            _print_info_table(info.to_dict(), detailed)
            
    except PDFEncryptedError:
        print_error("PDF 已加密，需要密码")
        print_info("提示: 使用 pdfkit security decrypt <文件> -p <密码> 解密后再操作")
        raise typer.Exit(1)
        
    except PDFInfoError as e:
        print_error(str(e))
        raise typer.Exit(1)
```

#### 3.6.3 MCP 调用 core 示例

```python
# pdfkit/mcp/tools/info_tools.py

from ...core import get_pdf_info, PDFInfoError, PDFEncryptedError
from ..server import mcp

@mcp.tool(
    name="pdfkit_get_info",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def pdfkit_get_info(
    file_path: str,
    detailed: bool = False,
) -> dict:
    """
    获取 PDF 文件的基本信息。
    
    返回文件名、大小、页数、加密状态等信息。
    """
    try:
        # 👉 同一个核心函数
        info = get_pdf_info(file_path, detailed=detailed)
        return {
            "success": True,
            "data": info.to_dict()
        }
        
    except PDFEncryptedError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "encrypted_pdf",
            "suggestion": "请使用 pdfkit_decrypt 解密后再操作"
        }
        
    except PDFInfoError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "pdf_error"
        }
```

#### 3.6.4 核心模块清单

需要抽取的核心服务模块：

| 核心模块 | 对应命令 | 主要函数 | 状态 |
|----------|----------|----------|------|
| `core/pdf_info.py` | `info` | `get_pdf_info()`, `get_page_count()`, `get_metadata()` | ✅ 已完成 |
| `core/pdf_merge.py` | `merge` | `merge_files()`, `merge_directory()`, `interleave()` | 待开发 |
| `core/pdf_split.py` | `split` | `split_by_pages()`, `split_by_size()`, `split_by_count()` | 待开发 |
| `core/pdf_extract.py` | `extract` | `extract_text()`, `extract_images()`, `extract_pages()` | 待开发 |
| `core/pdf_rotate.py` | `rotate` | `rotate_pages()` | 待开发 |
| `core/pdf_delete.py` | `delete` | `delete_pages()` | 待开发 |
| `core/pdf_reorder.py` | `reorder` | `reorder_pages()`, `reverse_pages()` | 待开发 |
| `core/pdf_convert.py` | `convert` | `to_images()`, `from_images()`, `to_word()`, `to_html()` | 待开发 |
| `core/pdf_edit.py` | `edit` | `add_watermark()`, `crop_pages()`, `resize_pages()` | 待开发 |
| `core/pdf_header.py` | `header/footer` | `add_header()`, `add_footer()` | 待开发 |
| `core/pdf_security.py` | `security` | `encrypt()`, `decrypt()`, `check_encryption()` | 待开发 |
| `core/pdf_optimize.py` | `optimize` | `compress()`, `optimize_images()`, `repair()` | 待开发 |
| `core/ocr_handler.py` | `ocr` | `recognize()`, `extract_tables()`, `analyze_layout()` | 已存在，需适配 |

#### 3.6.5 抽取原则

1. **纯函数优先**：核心函数应尽量是纯函数，输入参数 → 返回结果
2. **异常而非退出**：使用自定义异常而非 `typer.Exit()`
3. **返回数据对象**：返回 dataclass 或 Pydantic 模型，而非直接打印
4. **无 IO 副作用**：核心函数不应包含 `console.print()` 等输出
5. **可配置**：通过参数控制行为，而非硬编码

## 4. MCP Tools 设计

### 4.1 工具命名规范

遵循 MCP 最佳实践：

- 使用 `snake_case` 命名
- 带服务前缀：`pdfkit_{action}_{resource}`
- 动词开头：get, list, create, merge, split, etc.

### 4.2 工具分类与定义

#### 4.2.1 信息查看工具

| 工具名 | 描述 | 输入 | 输出 |
|--------|------|------|------|
| `pdfkit_get_info` | 获取 PDF 基本信息 | file_path, detailed | PDFInfo 对象 |
| `pdfkit_get_metadata` | 获取 PDF 元数据 | file_path | Metadata 对象 |
| `pdfkit_get_page_count` | 获取页数 | file_path | 页数数字 |

#### 4.2.2 页面操作工具

| 工具名 | 描述 | 输入 | 输出 | 注解 |
|--------|------|------|------|------|
| `pdfkit_merge_files` | 合并多个 PDF | file_paths, output_path, bookmark | 输出文件路径 | destructive |
| `pdfkit_split_by_pages` | 按页拆分 | file_path, pages, output_dir | 输出文件列表 | destructive |
| `pdfkit_split_by_size` | 按大小拆分 | file_path, max_size_mb, output_dir | 输出文件列表 | destructive |
| `pdfkit_extract_pages` | 提取指定页 | file_path, pages, output_path | 输出文件路径 | destructive |
| `pdfkit_delete_pages` | 删除页面 | file_path, pages, output_path | 输出文件路径 | destructive |
| `pdfkit_rotate_pages` | 旋转页面 | file_path, pages, angle, output_path | 输出文件路径 | destructive |
| `pdfkit_reorder_pages` | 重排页面 | file_path, order, output_path | 输出文件路径 | destructive |
| `pdfkit_reverse_pages` | 反转顺序 | file_path, output_path | 输出文件路径 | destructive |

#### 4.2.3 内容提取工具

| 工具名 | 描述 | 输入 | 输出 | 注解 |
|--------|------|------|------|------|
| `pdfkit_extract_text` | 提取文本 | file_path, pages | 文本内容 | readOnly |
| `pdfkit_extract_images` | 提取图片 | file_path, output_dir | 图片文件列表 | destructive |
| `pdfkit_extract_tables` | 提取表格 | file_path, pages | 表格数据 | readOnly |

#### 4.2.4 格式转换工具

| 工具名 | 描述 | 输入 | 输出 | 注解 |
|--------|------|------|------|------|
| `pdfkit_to_images` | PDF 转图片 | file_path, format, dpi, output_dir | 图片文件列表 | destructive |
| `pdfkit_from_images` | 图片转 PDF | image_paths, output_path | PDF 文件路径 | destructive |
| `pdfkit_to_word` | PDF 转 Word | file_path, output_path | Word 文件路径 | destructive |
| `pdfkit_to_html` | PDF 转 HTML | file_path, output_path | HTML 文件路径 | destructive |
| `pdfkit_from_html` | HTML 转 PDF | html_content_or_path, output_path | PDF 文件路径 | destructive |

#### 4.2.5 编辑工具

| 工具名 | 描述 | 输入 | 输出 | 注解 |
|--------|------|------|------|------|
| `pdfkit_add_watermark` | 添加水印 | file_path, text, options, output_path | 输出文件路径 | destructive |
| `pdfkit_add_header` | 添加页眉 | file_path, text, options, output_path | 输出文件路径 | destructive |
| `pdfkit_add_footer` | 添加页脚 | file_path, text, options, output_path | 输出文件路径 | destructive |
| `pdfkit_crop_pages` | 裁剪页面 | file_path, margins, output_path | 输出文件路径 | destructive |
| `pdfkit_resize_pages` | 调整大小 | file_path, width, height, output_path | 输出文件路径 | destructive |

#### 4.2.6 安全工具

| 工具名 | 描述 | 输入 | 输出 | 注解 |
|--------|------|------|------|------|
| `pdfkit_encrypt` | 加密 PDF | file_path, password, permissions, output_path | 输出文件路径 | destructive |
| `pdfkit_decrypt` | 解密 PDF | file_path, password, output_path | 输出文件路径 | destructive |
| `pdfkit_check_encryption` | 检查加密状态 | file_path | 加密状态信息 | readOnly |

#### 4.2.7 优化工具

| 工具名 | 描述 | 输入 | 输出 | 注解 |
|--------|------|------|------|------|
| `pdfkit_compress` | 压缩 PDF | file_path, quality, output_path | 输出文件路径和压缩比 | destructive |
| `pdfkit_optimize_images` | 优化图片 | file_path, quality, output_path | 输出文件路径 | destructive |
| `pdfkit_repair` | 修复 PDF | file_path, output_path | 输出文件路径 | destructive |

#### 4.2.8 OCR 工具

| 工具名 | 描述 | 输入 | 输出 | 注解 |
|--------|------|------|------|------|
| `pdfkit_ocr_recognize` | 文字识别 | file_path, pages, model, format | 识别文本 | readOnly, openWorld |
| `pdfkit_ocr_extract_tables` | 表格提取 | file_path, pages, model | 表格数据 | readOnly, openWorld |
| `pdfkit_ocr_analyze_layout` | 版面分析 | file_path, pages | 版面结构 | readOnly, openWorld |

### 4.3 工具注解说明

所有工具遵循 MCP 最佳实践提供以下注解：

| 注解 | 含义 |
|------|------|
| `readOnlyHint` | 工具仅读取数据，不修改任何文件 |
| `destructiveHint` | 工具会创建或修改文件 |
| `idempotentHint` | 相同参数多次调用结果相同 |
| `openWorldHint` | 工具与外部服务交互（如 OCR API） |

### 4.4 输入/输出 Schema 设计

使用 Pydantic 定义所有模型：

```python
# pdfkit/mcp/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum

# ==================== 通用模型 ====================

class PageRange(BaseModel):
    """页面范围"""
    start: int = Field(description="起始页（1-indexed）")
    end: Optional[int] = Field(None, description="结束页（含），不填则为单页")

class CompressionQuality(str, Enum):
    """压缩质量"""
    LOW = "low"         # 最小文件，较低质量
    MEDIUM = "medium"   # 平衡
    HIGH = "high"       # 高质量，较大文件

class ImageFormat(str, Enum):
    """图片格式"""
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"

class OCRModel(str, Enum):
    """OCR 模型"""
    FLASH = "flash"   # 快速模型
    PLUS = "plus"     # 高精度模型

# ==================== 输出模型 ====================

class PDFInfo(BaseModel):
    """PDF 基本信息"""
    filename: str
    path: str
    size_bytes: int
    size_human: str
    page_count: int
    version: str
    is_encrypted: bool
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None

class MergeResult(BaseModel):
    """合并结果"""
    output_path: str
    total_files: int
    total_pages: int
    success: bool
    message: str

class SplitResult(BaseModel):
    """拆分结果"""
    output_files: List[str]
    total_output: int
    success: bool
    message: str

class OCRResult(BaseModel):
    """OCR 识别结果"""
    page_results: List[dict]
    total_pages: int
    model_used: str
    format: str
```

---

## 5. 实施计划

### 5.1 开发阶段

#### Phase 1: 基础架构 (1-2 天)

**目标**: 建立 MCP 服务器基础框架

- [ ] 添加 MCP 依赖到 `pyproject.toml`
- [ ] 创建 `pdfkit/mcp/` 目录结构
- [ ] 实现基础 MCP 服务器 (`server.py`)
- [ ] 添加第一个简单工具 (`pdfkit_get_info`)
- [ ] 验证服务器启动和工具调用

**关键代码**:

```python
# pdfkit/mcp/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pdfkit_mcp")

@mcp.tool()
async def pdfkit_get_info(file_path: str) -> dict:
    """获取 PDF 文件的基本信息"""
    ...
```

#### Phase 2: 核心层抽取 (2-3 天)

**目标**: 从现有命令中抽取可复用的核心服务

- [ ] 创建 `pdfkit/core/pdf_info.py` - 信息服务
- [ ] 创建 `pdfkit/core/pdf_merge.py` - 合并服务
- [ ] 创建 `pdfkit/core/pdf_split.py` - 拆分服务
- [ ] 创建 `pdfkit/core/pdf_extract.py` - 提取服务
- [ ] 重构 `commands/*.py` 调用新的 core 服务
- [ ] 确保 CLI 功能不受影响

#### Phase 3: 页面操作工具 (2-3 天)

**目标**: 实现所有页面操作相关的 MCP 工具

- [ ] `pdfkit_merge_files`
- [ ] `pdfkit_split_by_pages`
- [ ] `pdfkit_split_by_size`
- [ ] `pdfkit_extract_pages`
- [ ] `pdfkit_delete_pages`
- [ ] `pdfkit_rotate_pages`
- [ ] `pdfkit_reorder_pages`
- [ ] `pdfkit_reverse_pages`

#### Phase 4: 转换与编辑工具 (2-3 天)

**目标**: 实现格式转换和编辑相关工具

- [ ] 核心层: `pdfkit/core/pdf_convert.py`
- [ ] 核心层: `pdfkit/core/pdf_edit.py`
- [ ] 转换工具组
- [ ] 编辑工具组 (水印、页眉、页脚等)

#### Phase 5: 安全与优化工具 (1-2 天)

**目标**: 实现安全和优化相关工具

- [ ] 核心层: `pdfkit/core/pdf_security.py`
- [ ] 核心层: `pdfkit/core/pdf_optimize.py`
- [ ] 安全工具组
- [ ] 优化工具组

#### Phase 6: OCR 工具 (1-2 天)

**目标**: 实现 OCR 相关 MCP 工具

- [ ] 适配现有 `core/ocr_handler.py`
- [ ] `pdfkit_ocr_recognize`
- [ ] `pdfkit_ocr_extract_tables`
- [ ] `pdfkit_ocr_analyze_layout`

#### Phase 7: 测试与文档 (2-3 天)

**目标**: 完善测试和文档

- [ ] 单元测试: 所有核心服务
- [ ] 集成测试: MCP 工具端到端测试
- [ ] MCP Inspector 测试
- [ ] 编写 MCP 工具参考文档
- [ ] 更新 README.md

### 5.2 时间估算

| 阶段 | 工作量 | 预计时间 |
|------|--------|----------|
| Phase 1: 基础架构 | 基础框架搭建 | 1-2 天 |
| Phase 2: 核心层抽取 | 重构核心逻辑 | 2-3 天 |
| Phase 3: 页面操作工具 | 8 个工具 | 2-3 天 |
| Phase 4: 转换与编辑工具 | 10 个工具 | 2-3 天 |
| Phase 5: 安全与优化工具 | 6 个工具 | 1-2 天 |
| Phase 6: OCR 工具 | 3 个工具 | 1-2 天 |
| Phase 7: 测试与文档 | 测试 + 文档 | 2-3 天 |
| **总计** | | **11-18 天** |

---

## 6. 技术规范

### 6.1 依赖更新

在 `pyproject.toml` 中添加 MCP 依赖：

```toml
[project]
dependencies = [
    # 现有依赖...
    
    # MCP 服务器
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "httpx>=0.25.0",  # 用于异步 HTTP
]

[project.scripts]
pdfkit = "pdfkit.__main__:main"
pdfkit-cli = "pdfkit.__main__:main"
pdfkit-mcp = "pdfkit.mcp.server:main"  # 新增 MCP 入口
```

### 6.2 MCP 服务器配置

```python
# pdfkit/mcp/server.py

from mcp.server.fastmcp import FastMCP
from contextlib import asynccontextmanager

@asynccontextmanager
async def app_lifespan():
    """服务生命周期管理"""
    # 初始化配置
    from ..utils.config import load_config
    config = load_config()
    
    yield {"config": config}
    
    # 清理资源

mcp = FastMCP(
    "pdfkit_mcp",
    lifespan=app_lifespan,
    version="0.1.0",
)

def main():
    """MCP 服务器入口"""
    import sys
    
    if "--http" in sys.argv:
        mcp.run(transport="streamable_http", port=8000)
    else:
        mcp.run()  # 默认 stdio

if __name__ == "__main__":
    main()
```

### 6.3 工具实现模板

```python
# pdfkit/mcp/tools/info_tools.py

from pydantic import BaseModel, Field
from mcp.server.fastmcp import Context
from ..server import mcp
from ...core.pdf_info import get_pdf_info

class GetInfoInput(BaseModel):
    """获取 PDF 信息的输入参数"""
    file_path: str = Field(
        description="PDF 文件的绝对路径或相对路径"
    )
    detailed: bool = Field(
        default=False,
        description="是否返回详细信息（包括元数据）"
    )

@mcp.tool(
    name="pdfkit_get_info",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def pdfkit_get_info(
    file_path: str,
    detailed: bool = False,
    ctx: Context = None,
) -> dict:
    """
    获取 PDF 文件的基本信息。
    
    返回文件名、大小、页数、加密状态等信息。
    如果 detailed=True，还会返回元数据（标题、作者等）。
    
    Args:
        file_path: PDF 文件路径
        detailed: 是否返回详细信息
        
    Returns:
        PDFInfo: 包含 PDF 基本信息的字典
        
        Schema:
        {
            "filename": str,
            "path": str,
            "size_bytes": int,
            "size_human": str,
            "page_count": int,
            "version": str,
            "is_encrypted": bool,
            "title": str | null,
            "author": str | null,
            ...
        }
    """
    if ctx:
        await ctx.report_progress(0.1, "正在读取文件...")
    
    result = get_pdf_info(file_path, detailed=detailed)
    
    if ctx:
        await ctx.report_progress(1.0, "完成")
    
    return result
```

### 6.4 错误处理规范

```python
# pdfkit/mcp/utils.py

from typing import TypeVar, Callable
from functools import wraps

T = TypeVar('T')

class MCPError(Exception):
    """MCP 工具错误基类"""
    def __init__(self, message: str, suggestion: str = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)

class FileNotFoundError(MCPError):
    """文件不存在"""
    pass

class InvalidPDFError(MCPError):
    """无效的 PDF 文件"""
    pass

class EncryptedPDFError(MCPError):
    """PDF 已加密"""
    pass

def format_error(error: Exception) -> dict:
    """格式化错误信息，提供可操作的建议"""
    if isinstance(error, FileNotFoundError):
        return {
            "error": True,
            "message": str(error.message),
            "suggestion": error.suggestion or "请检查文件路径是否正确",
            "error_type": "file_not_found",
        }
    elif isinstance(error, EncryptedPDFError):
        return {
            "error": True,
            "message": str(error.message),
            "suggestion": "请使用 pdfkit_decrypt 解密后再操作",
            "error_type": "encrypted_pdf",
        }
    else:
        return {
            "error": True,
            "message": str(error),
            "suggestion": "请检查输入参数和文件状态",
            "error_type": "unknown",
        }
```

---

## 7. 测试策略

### 7.1 测试层级

```
测试金字塔
         /\
        /  \  E2E 测试 (MCP Inspector)
       /----\
      /      \  集成测试 (MCP 工具 + Core)
     /--------\
    /          \  单元测试 (Core 服务)
   --------------
```

### 7.2 单元测试

```python
# tests/test_mcp/test_core/test_pdf_info.py

import pytest
from pathlib import Path
from pdfkit.core.pdf_info import get_pdf_info

class TestPDFInfo:
    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """创建测试 PDF"""
        # 使用 PyMuPDF 创建简单测试 PDF
        ...
    
    def test_get_info_basic(self, sample_pdf):
        """测试基本信息获取"""
        info = get_pdf_info(sample_pdf)
        assert info["page_count"] == 1
        assert info["is_encrypted"] == False
    
    def test_get_info_detailed(self, sample_pdf):
        """测试详细信息获取"""
        info = get_pdf_info(sample_pdf, detailed=True)
        assert "title" in info
        assert "author" in info
```

### 7.3 MCP 工具测试

```python
# tests/test_mcp/test_tools/test_info_tools.py

import pytest
from pdfkit.mcp.tools.info_tools import pdfkit_get_info

class TestInfoTools:
    @pytest.mark.asyncio
    async def test_pdfkit_get_info(self, sample_pdf_path):
        """测试 MCP 工具"""
        result = await pdfkit_get_info(
            file_path=str(sample_pdf_path),
            detailed=False
        )
        assert "page_count" in result
        assert result["is_encrypted"] == False
```

### 7.4 MCP Inspector 测试

使用 MCP Inspector 进行端到端测试：

```bash
# 启动 MCP Inspector
npx @modelcontextprotocol/inspector

# 连接到本地 MCP 服务器
# 测试各个工具的调用
```

### 7.5 评估问题集

根据 MCP 最佳实践，创建 10 个评估问题：

```xml
<!-- tests/evaluation/pdfkit_eval.xml -->
<evaluation>
  <qa_pair>
    <question>
      获取 document.pdf 的页数，然后将其拆分为每 5 页一个文件
    </question>
    <answer>
      使用 pdfkit_get_info 获取页数，然后使用 pdfkit_split_by_pages 拆分
    </answer>
  </qa_pair>
  
  <qa_pair>
    <question>
      将目录中所有 PDF 合并为一个文件，按文件名排序，并添加书签
    </question>
    <answer>
      使用 pdfkit_merge_files 合并，设置 bookmark=True
    </answer>
  </qa_pair>
  
  <!-- 更多评估问题... -->
</evaluation>
```

---

## 8. 风险与缓解

### 8.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 核心层抽取影响现有 CLI | 高 | 中 | 全面的 CLI 回归测试 |
| 异步/同步混合调用问题 | 中 | 高 | 统一使用异步包装器 |
| OCR API 调用失败 | 中 | 中 | 完善的错误处理和重试机制 |
| 大文件处理内存问题 | 高 | 低 | 流式处理、进度报告 |

### 8.2 依赖风险

| 风险 | 缓解措施 |
|------|----------|
| MCP SDK 版本不稳定 | 锁定版本，定期更新 |
| 第三方 PDF 库 API 变化 | 封装适配层 |

### 8.3 缓解策略详情

#### 策略 1: 渐进式迁移

1. 先实现 MCP 服务器基础框架
2. 逐个命令进行核心层抽取
3. 每次抽取后运行完整 CLI 测试
4. 确认无问题后再进行下一个

#### 策略 2: 异步处理

```python
import asyncio
from functools import wraps

def sync_to_async(func):
    """将同步函数包装为异步"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper
```

#### 策略 3: 文件处理安全

```python
async def safe_process_pdf(file_path: str, operation, ctx: Context = None):
    """安全的 PDF 处理包装器"""
    path = Path(file_path)
    
    # 验证文件存在
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 验证是 PDF
    if path.suffix.lower() != '.pdf':
        raise InvalidPDFError(f"不是 PDF 文件: {file_path}")
    
    # 检查文件大小
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > 500:  # 超过 500MB
        if ctx:
            await ctx.log_info(f"大文件警告: {size_mb:.1f} MB，处理可能较慢")
    
    # 执行操作
    return await operation(path)
```

---

## 附录

### A. 参考资料

1. [MCP Protocol Specification](https://modelcontextprotocol.io/specification)
2. [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
3. [FastMCP Documentation](https://github.com/jlowin/fastmcp)
4. MCP Best Practices (参考 `.claude/skills/mcp-builder/reference/`)

### B. 相关项目

- PDFKit CLI: 当前项目
- 阿里百炼 Qwen3-VL: OCR 服务提供商

### C. 更新日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-01-02 | 1.0 | 初始版本 |

---

**文档维护者**: PDFKit Team  
**最后更新**: 2026-01-02
