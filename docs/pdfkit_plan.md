# PDF 处理 CLI 工具 - 完整开发计划

## 📋 项目概述

### 项目名称
**PDFKit** - 全能 PDF 命令行处理工具

### 项目愿景
打造一个功能全面、使用简单、界面美观的 PDF 命令行处理工具，覆盖日常 PDF 操作的所有需求。

### 目标用户
- 开发者和技术人员
- 需要批量处理 PDF 的办公人员
- 自动化脚本使用者

---

## 🎯 功能规划

### 一、基础操作

| 功能 | 命令示例 | 说明 |
|------|----------|------|
| 查看信息 | `pdfkit info file.pdf` | 显示 PDF 元数据、页数、大小、加密状态等 |
| 提取文本 | `pdfkit extract-text file.pdf` | 提取 PDF 中的所有文本 |
| 提取图片 | `pdfkit extract-images file.pdf` | 提取 PDF 中的所有图片 |
| 提取表格 | `pdfkit extract-tables file.pdf` | 提取 PDF 中的表格数据 |

### 二、页面操作

| 功能 | 命令示例 | 说明 |
|------|----------|------|
| 拆分 PDF | `pdfkit split file.pdf` | 将 PDF 拆分成单页 |
| 拆分范围 | `pdfkit split file.pdf -r 1-5,10-15` | 按指定范围拆分 |
| 合并 PDF | `pdfkit merge a.pdf b.pdf -o combined.pdf` | 合并多个 PDF |
| 删除页面 | `pdfkit delete file.pdf -p 3,5,7` | 删除指定页面 |
| 提取页面 | `pdfkit extract file.pdf -p 1-10` | 提取指定页面 |
| 旋转页面 | `pdfkit rotate file.pdf -a 90` | 旋转页面（90/180/270度） |
| 重排页面 | `pdfkit reorder file.pdf -o 3,1,2,4` | 重新排列页面顺序 |
| 反转顺序 | `pdfkit reverse file.pdf` | 反转页面顺序 |

### 三、转换操作

| 功能 | 命令示例 | 说明 |
|------|----------|------|
| PDF 转图片 | `pdfkit to-image file.pdf -f png` | 每页转换为图片 |
| 图片转 PDF | `pdfkit from-images *.jpg -o output.pdf` | 图片合并为 PDF |
| PDF 转 Word | `pdfkit to-word file.pdf` | 转换为 docx 格式 |
| PDF 转 HTML | `pdfkit to-html file.pdf` | 转换为 HTML |
| PDF 转 Markdown | `pdfkit to-markdown file.pdf` | 转换为 Markdown |
| 网页转 PDF | `pdfkit from-url https://... -o out.pdf` | 网页转 PDF |
| HTML 转 PDF | `pdfkit from-html file.html -o out.pdf` | HTML 转 PDF |

### 四、编辑操作

| 功能 | 命令示例 | 说明 |
|------|----------|------|
| 添加水印 | `pdfkit watermark file.pdf -t "机密"` | 添加文字水印 |
| 图片水印 | `pdfkit watermark file.pdf -i logo.png` | 添加图片水印 |
| 添加页眉 | `pdfkit header file.pdf -t "公司名称"` | 添加页眉 |
| 添加页脚 | `pdfkit footer file.pdf -t "第{page}页"` | 添加页脚和页码 |
| 添加书签 | `pdfkit bookmark file.pdf -f bookmarks.txt` | 添加书签/目录 |
| 添加注释 | `pdfkit annotate file.pdf` | 添加注释 |
| 添加链接 | `pdfkit add-link file.pdf` | 添加超链接 |
| 裁剪页面 | `pdfkit crop file.pdf -m 10,20,10,20` | 裁剪页面边距 |
| 调整大小 | `pdfkit resize file.pdf -s A4` | 调整页面尺寸 |

### 五、安全操作

| 功能 | 命令示例 | 说明 |
|------|----------|------|
| 加密 PDF | `pdfkit encrypt file.pdf -p password` | 设置密码保护 |
| 解密 PDF | `pdfkit decrypt file.pdf -p password` | 移除密码保护 |
| 设置权限 | `pdfkit protect file.pdf --no-print` | 设置权限限制 |
| 数字签名 | `pdfkit sign file.pdf -c cert.pem` | 添加数字签名 |
| 验证签名 | `pdfkit verify file.pdf` | 验证数字签名 |
| 移除元数据 | `pdfkit clean-meta file.pdf` | 清除敏感元数据 |

### 六、优化操作

| 功能 | 命令示例 | 说明 |
|------|----------|------|
| 压缩 PDF | `pdfkit compress file.pdf` | 压缩文件大小 |
| 压缩质量 | `pdfkit compress file.pdf -q low` | 按质量等级压缩 |
| 优化图片 | `pdfkit optimize-images file.pdf` | 优化内嵌图片 |
| 线性化 | `pdfkit linearize file.pdf` | 优化网络加载 |
| 修复 PDF | `pdfkit repair file.pdf` | 修复损坏的 PDF |

### 七、OCR 和智能处理 (基于阿里百炼 Qwen3-VL)

> **技术方案**: 使用阿里云百炼平台的 **Qwen3-VL** 视觉语言模型进行 OCR 识别，支持中英文混合识别、表格提取、版面分析等。

| 功能 | 命令示例 | 说明 |
|------|----------|------|
| OCR 识别 | `pdfkit ocr file.pdf` | 扫描件/图片 PDF 文字识别 |
| 指定模型 | `pdfkit ocr file.pdf -m qwen3-vl-plus` | 使用更强模型 |
| 指定页面 | `pdfkit ocr file.pdf -p 1-5` | 仅识别指定页面 |
| 输出格式 | `pdfkit ocr file.pdf -f markdown` | 识别结果格式 (text/markdown/json) |
| 表格提取 | `pdfkit ocr-table file.pdf` | 专门提取表格数据 |
| 版面分析 | `pdfkit ocr-layout file.pdf` | 分析文档版面结构 |
| 生成可搜索PDF | `pdfkit ocr file.pdf --searchable` | 生成带文本层的可搜索 PDF |
| 比较 PDF | `pdfkit compare a.pdf b.pdf` | 比较两个 PDF 差异 |
| 搜索内容 | `pdfkit search file.pdf -q "关键词"` | 搜索文本内容 |
| 替换文本 | `pdfkit replace file.pdf -f "旧" -t "新"` | 替换文本内容 |
| 标记高亮 | `pdfkit highlight file.pdf -q "关键词"` | 高亮关键词 |

#### OCR 模型选择

| 模型 | 参数值 | 特点 | 适用场景 |
|------|--------|------|----------|
| **qwen3-vl-flash** | `flash` (默认) | 速度快、成本低 | 日常文档、简单表格 |
| **qwen3-vl-plus** | `plus` | 精度高、能力强 | 复杂排版、手写体、专业文档 |

#### OCR 命令详细选项

```bash
pdfkit ocr <file.pdf> [OPTIONS]

选项:
  -m, --model [flash|plus]    模型选择 (默认: flash)
  -p, --pages TEXT            页面范围 (如: 1-5,8,10-15)
  -f, --format [text|md|json] 输出格式 (默认: text)
  -o, --output PATH           输出文件路径
  --searchable                生成可搜索 PDF
  --language TEXT             识别语言提示 (如: 中文、英文、中英混合)
  --dpi INTEGER               图片转换 DPI (默认: 300)
  --prompt TEXT               自定义识别提示词
  --api-key TEXT              API Key (或使用环境变量)
  --region [beijing|singapore] API 地域 (默认: beijing)
```


### 八、批量处理

| 功能 | 命令示例 | 说明 |
|------|----------|------|
| 批量转换 | `pdfkit batch to-image *.pdf` | 批量转换 |
| 批量压缩 | `pdfkit batch compress *.pdf` | 批量压缩 |
| 批量水印 | `pdfkit batch watermark *.pdf -t "机密"` | 批量添加水印 |
| 任务文件 | `pdfkit batch -f tasks.yaml` | 从配置文件执行批量任务 |
| 监控目录 | `pdfkit watch ./input -c "pdfkit compress {}"` | 监控目录自动处理 |

### 九、其他功能

| 功能 | 命令示例 | 说明 |
|------|----------|------|
| 交互模式 | `pdfkit interactive` | 进入交互式 shell |
| 生成报告 | `pdfkit report *.pdf -o report.html` | 生成批量处理报告 |
| 模板处理 | `pdfkit template file.pdf -d data.json` | 使用模板填充数据 |
| 表单填充 | `pdfkit fill-form file.pdf -d data.json` | 填充 PDF 表单 |

---

## 🏗️ 技术架构

### 核心依赖库

```python
# PDF 处理核心
PyMuPDF (fitz)      # 主要 PDF 操作库，功能最全面
pypdf               # PDF 基础操作
pdfplumber          # 表格提取
pdf2image           # PDF 转图片
img2pdf             # 图片转 PDF
pikepdf             # 底层 PDF 操作

# OCR (阿里百炼 Qwen3-VL)
openai              # OpenAI 兼容 SDK (阿里百炼使用 OpenAI 协议)
pdf2image           # PDF 转图片供 OCR
Pillow              # 图片处理
base64              # 图片编码 (内置库)

# 转换
python-docx         # Word 处理
pdfkit/weasyprint   # HTML 转 PDF
playwright          # 网页转 PDF (headless browser)

# CLI 框架
typer               # 现代 CLI 框架
rich                # 终端美化
click               # CLI 基础

# 其他
Pillow              # 图片处理
tqdm                # 进度条
watchdog            # 文件监控
pyyaml              # YAML 配置
```

### 项目结构

```
pdfkit/
├── pyproject.toml              # 项目配置
├── README.md                   # 项目说明
├── LICENSE                     # 开源协议
│
├── pdfkit/                     # 主包
│   ├── __init__.py
│   ├── __main__.py             # 入口点
│   ├── cli.py                  # CLI 主程序
│   │
│   ├── commands/               # 命令模块
│   │   ├── __init__.py
│   │   ├── info.py             # 信息查看
│   │   ├── split.py            # 拆分
│   │   ├── merge.py            # 合并
│   │   ├── extract.py          # 提取
│   │   ├── convert.py          # 转换
│   │   ├── edit.py             # 编辑
│   │   ├── security.py         # 安全
│   │   ├── optimize.py         # 优化
│   │   ├── ocr.py              # OCR
│   │   └── batch.py            # 批量
│   │
│   ├── core/                   # 核心功能
│   │   ├── __init__.py
│   │   ├── pdf_handler.py      # PDF 处理器
│   │   ├── image_handler.py    # 图片处理器
│   │   ├── text_handler.py     # 文本处理器
│   │   ├── table_handler.py    # 表格处理器
│   │   ├── ocr_handler.py      # OCR 处理器
│   │   └── converter.py        # 格式转换器
│   │
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── console.py          # 控制台输出
│   │   ├── validators.py       # 参数验证
│   │   ├── file_utils.py       # 文件工具
│   │   ├── progress.py         # 进度显示
│   │   └── config.py           # 配置管理
│   │
│   ├── styles/                 # 样式定义
│   │   ├── __init__.py
│   │   ├── colors.py           # 颜色方案
│   │   └── themes.py           # 主题
│   │
│   └── templates/              # 模板文件
│       ├── report.html         # 报告模板
│       └── watermark.svg       # 水印模板
│
├── tests/                      # 测试
│   ├── __init__.py
│   ├── test_split.py
│   ├── test_merge.py
│   └── ...
│
└── docs/                       # 文档
    ├── installation.md
    ├── usage.md
    └── examples.md
```

---

## 🎨 CLI 界面设计

### 颜色方案

```python
# styles/colors.py

from rich.theme import Theme
from rich.style import Style

# ============================================================================
# 主色调定义
# ============================================================================

# 主色 - 蓝色系 (品牌色)
PRIMARY = "#3B82F6"         # 主要操作、标题
PRIMARY_LIGHT = "#60A5FA"   # 悬停、次要
PRIMARY_DARK = "#1D4ED8"    # 强调

# 成功色 - 绿色系
SUCCESS = "#10B981"         # 成功消息
SUCCESS_LIGHT = "#34D399"
SUCCESS_DARK = "#059669"

# 警告色 - 黄色系  
WARNING = "#F59E0B"         # 警告消息
WARNING_LIGHT = "#FBBF24"
WARNING_DARK = "#D97706"

# 错误色 - 红色系
ERROR = "#EF4444"           # 错误消息
ERROR_LIGHT = "#F87171"
ERROR_DARK = "#DC2626"

# 信息色 - 青色系
INFO = "#06B6D4"            # 信息提示
INFO_LIGHT = "#22D3EE"
INFO_DARK = "#0891B2"

# 中性色 - 灰色系
TEXT = "#E5E7EB"            # 主文本
TEXT_MUTED = "#9CA3AF"      # 次要文本
TEXT_DIM = "#6B7280"        # 暗淡文本
BORDER = "#374151"          # 边框
BACKGROUND = "#1F2937"      # 背景

# 特殊色
HIGHLIGHT = "#A855F7"       # 高亮 (紫色)
LINK = "#3B82F6"            # 链接
CODE = "#F472B6"            # 代码 (粉色)
PATH = "#34D399"            # 文件路径 (绿色)
NUMBER = "#FBBF24"          # 数字 (黄色)
SIZE = "#60A5FA"            # 文件大小 (浅蓝)


# ============================================================================
# Rich 主题定义
# ============================================================================

PDFKIT_THEME = Theme({
    # 基础样式
    "info": f"bold {INFO}",
    "warning": f"bold {WARNING}",
    "error": f"bold {ERROR}",
    "success": f"bold {SUCCESS}",
    
    # 标题和强调
    "title": f"bold {PRIMARY}",
    "subtitle": f"{PRIMARY_LIGHT}",
    "heading": f"bold {TEXT}",
    "emphasis": f"italic {TEXT_MUTED}",
    
    # 命令和代码
    "command": f"bold {CODE}",
    "option": f"{INFO}",
    "argument": f"{WARNING_LIGHT}",
    "code": f"{CODE}",
    
    # 文件和路径
    "path": f"{PATH}",
    "filename": f"bold {PATH}",
    "url": f"underline {LINK}",
    
    # 数据
    "number": f"{NUMBER}",
    "size": f"{SIZE}",
    "percent": f"{SUCCESS}",
    "date": f"{TEXT_MUTED}",
    
    # 状态
    "status.pending": f"{TEXT_MUTED}",
    "status.running": f"bold {INFO}",
    "status.success": f"bold {SUCCESS}",
    "status.failed": f"bold {ERROR}",
    "status.skipped": f"{WARNING}",
    
    # 进度条
    "progress.description": f"{TEXT}",
    "progress.percentage": f"bold {PRIMARY}",
    "progress.bar.complete": f"{SUCCESS}",
    "progress.bar.incomplete": f"{BORDER}",
    
    # 表格
    "table.header": f"bold {PRIMARY}",
    "table.border": f"{BORDER}",
    "table.row.odd": f"{TEXT}",
    "table.row.even": f"{TEXT_MUTED}",
    
    # PDF 相关特殊样式
    "pdf.pages": f"bold {NUMBER}",
    "pdf.size": f"{SIZE}",
    "pdf.encrypted": f"bold {ERROR}",
    "pdf.metadata": f"{TEXT_MUTED}",
})


# ============================================================================
# 图标定义 (Nerd Font / Unicode)
# ============================================================================

class Icons:
    # 状态图标
    SUCCESS = "✓"           # ✓ 或 
    ERROR = "✗"             # ✗ 或 
    WARNING = "⚠"           # ⚠ 或 
    INFO = "ℹ"              # ℹ 或 
    PENDING = "○"           # ○ 或 
    RUNNING = "◐"           # ◐ 或 
    
    # 文件图标
    PDF = "📄"              # 或 
    IMAGE = "🖼"            # 或 
    FOLDER = "📁"           # 或 
    FILE = "📄"             # 或 
    
    # 操作图标
    SPLIT = "✂"             # 或 󰗈
    MERGE = "🔗"            # 或 
    CONVERT = "🔄"          # 或 
    COMPRESS = "📦"         # 或 
    ENCRYPT = "🔒"          # 或 
    DECRYPT = "🔓"          # 或 
    
    # 箭头
    ARROW_RIGHT = "→"
    ARROW_LEFT = "←"
    ARROW_DOWN = "↓"
    ARROW_UP = "↑"
    
    # 其他
    CHECK = "✓"
    CROSS = "✗"
    DOT = "•"
    STAR = "★"
    CLOCK = "⏱"
    SEARCH = "🔍"
```

### 控制台输出样式

```python
# utils/console.py

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.syntax import Syntax
from rich.tree import Tree
from ..styles.colors import PDFKIT_THEME, Icons

# 全局控制台实例
console = Console(theme=PDFKIT_THEME)


def print_banner():
    """打印程序 Banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ██████╗ ██████╗ ███████╗██╗  ██╗██╗████████╗               ║
    ║   ██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██║╚══██╔══╝               ║
    ║   ██████╔╝██║  ██║█████╗  █████╔╝ ██║   ██║                  ║
    ║   ██╔═══╝ ██║  ██║██╔══╝  ██╔═██╗ ██║   ██║                  ║
    ║   ██║     ██████╔╝██║     ██║  ██╗██║   ██║                  ║
    ║   ╚═╝     ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝   ╚═╝                  ║
    ║                                                               ║
    ║         全能 PDF 命令行处理工具 v1.0.0                        ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="title")


def print_success(message: str):
    """打印成功消息"""
    console.print(f"{Icons.SUCCESS} {message}", style="success")


def print_error(message: str):
    """打印错误消息"""
    console.print(f"{Icons.ERROR} {message}", style="error")


def print_warning(message: str):
    """打印警告消息"""
    console.print(f"{Icons.WARNING} {message}", style="warning")


def print_info(message: str):
    """打印信息消息"""
    console.print(f"{Icons.INFO} {message}", style="info")


def print_file_info(pdf_info: dict):
    """打印 PDF 文件信息"""
    table = Table(
        title="PDF 文件信息",
        title_style="title",
        border_style="border",
        show_header=True,
        header_style="table.header"
    )
    
    table.add_column("属性", style="emphasis", width=20)
    table.add_column("值", style="text")
    
    table.add_row("文件名", f"[filename]{pdf_info['filename']}[/]")
    table.add_row("文件大小", f"[size]{pdf_info['size']}[/]")
    table.add_row("页数", f"[pdf.pages]{pdf_info['pages']}[/] 页")
    table.add_row("PDF 版本", pdf_info['version'])
    table.add_row("创建时间", f"[date]{pdf_info['created']}[/]")
    table.add_row("修改时间", f"[date]{pdf_info['modified']}[/]")
    table.add_row("作者", pdf_info.get('author', '-'))
    table.add_row("标题", pdf_info.get('title', '-'))
    
    # 加密状态
    if pdf_info.get('encrypted'):
        table.add_row("加密状态", "[pdf.encrypted]已加密 🔒[/]")
    else:
        table.add_row("加密状态", "[success]未加密[/]")
    
    console.print(table)


def create_progress():
    """创建进度条"""
    return Progress(
        SpinnerColumn(style="info"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="progress.bar.complete", finished_style="success"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    )


def print_result_panel(title: str, content: str, success: bool = True):
    """打印结果面板"""
    style = "success" if success else "error"
    icon = Icons.SUCCESS if success else Icons.ERROR
    
    panel = Panel(
        content,
        title=f"{icon} {title}",
        border_style=style,
        padding=(1, 2)
    )
    console.print(panel)


def print_operation_summary(operations: list):
    """打印操作摘要"""
    table = Table(
        title="操作摘要",
        title_style="title",
        border_style="border"
    )
    
    table.add_column("操作", style="command", width=20)
    table.add_column("输入", style="path", width=30)
    table.add_column("输出", style="path", width=30)
    table.add_column("状态", justify="center", width=10)
    
    for op in operations:
        status_style = "status.success" if op['success'] else "status.failed"
        status_icon = Icons.SUCCESS if op['success'] else Icons.ERROR
        
        table.add_row(
            op['operation'],
            op['input'],
            op['output'],
            f"[{status_style}]{status_icon}[/]"
        )
    
    console.print(table)
```

### CLI 帮助信息样式

```python
# cli.py 样式示例

import typer
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns

app = typer.Typer(
    name="pdfkit",
    help="🔧 全能 PDF 命令行处理工具",
    add_completion=True,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
)


# 帮助信息的自定义格式
HELP_TEMPLATE = """
[bold blue]PDFKit[/] - 全能 PDF 命令行处理工具

[bold cyan]用法:[/]
    pdfkit [OPTIONS] COMMAND [ARGS]...

[bold cyan]命令分类:[/]

  [bold green]📋 基础操作[/]
    info          查看 PDF 信息
    extract-text  提取文本内容
    extract-images 提取图片

  [bold green]📄 页面操作[/]
    split         拆分 PDF
    merge         合并 PDF
    extract       提取页面
    rotate        旋转页面
    delete        删除页面

  [bold green]🔄 格式转换[/]
    to-image      PDF 转图片
    to-word       PDF 转 Word
    from-images   图片转 PDF
    from-html     HTML 转 PDF

  [bold green]✏️ 编辑[/]
    watermark     添加水印
    header        添加页眉
    footer        添加页脚
    bookmark      添加书签

  [bold green]🔒 安全[/]
    encrypt       加密 PDF
    decrypt       解密 PDF
    sign          数字签名

  [bold green]⚡ 优化[/]
    compress      压缩 PDF
    repair        修复 PDF
    ocr           OCR 识别

  [bold green]📦 批量[/]
    batch         批量处理

[bold cyan]全局选项:[/]
    --help, -h    显示帮助信息
    --version     显示版本号
    --verbose     详细输出
    --quiet       静默模式
    --config      指定配置文件

[bold cyan]示例:[/]
    [dim]# 查看 PDF 信息[/]
    $ pdfkit info document.pdf

    [dim]# 合并多个 PDF[/]
    $ pdfkit merge file1.pdf file2.pdf -o combined.pdf

    [dim]# 压缩 PDF[/]
    $ pdfkit compress large.pdf -o small.pdf

[bold cyan]更多帮助:[/]
    pdfkit COMMAND --help    查看命令详细帮助
    pdfkit docs              打开在线文档
"""
```

---

## 💻 实现示例

### 0. 配置加载工具 (utils/config.py)

```python
"""配置管理 - 从配置文件加载所有可配置项"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache

# 配置文件路径
CONFIG_DIR = Path.home() / ".pdfkit"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
DEFAULT_CONFIG_FILE = Path(__file__).parent.parent / "templates" / "default_config.yaml"


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Any]:
    """
    加载配置文件
    
    优先级:
    1. 用户配置 (~/.pdfkit/config.yaml)
    2. 默认配置 (内置)
    
    Returns:
        配置字典
    """
    config = _get_default_config()
    
    # 加载用户配置
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            # 深度合并配置
            config = _deep_merge(config, user_config)
        except Exception as e:
            print(f"警告: 加载配置文件失败: {e}")
    
    # 处理环境变量引用
    config = _expand_env_vars(config)
    
    return config


def _get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "defaults": {
            "output_dir": str(Path.home() / "Documents" / "pdfkit_output"),
            "quality": "medium",
            "overwrite": False,
            "verbose": False,
        },
        "ocr": {
            "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
            "models": {
                "flash": "qwen3-vl-flash",
                "plus": "qwen3-vl-plus",
            },
            "regions": {
                "beijing": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "singapore": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            },
            "default_model": "flash",
            "default_region": "beijing",
            "default_dpi": 300,
            "default_format": "text",
            "timeout": 60,
            "max_retries": 3,
            "prompts": {
                "text": "请识别并提取图片中的所有文字内容，保持原有的格式和布局。只输出识别到的文字，不要添加任何解释。",
                "markdown": "请识别图片中的所有文字内容，并以 Markdown 格式输出。保持标题、列表、表格等结构。",
                "json": "请识别图片中的所有文字内容，以 JSON 格式输出。",
                "table": "请识别图片中的表格数据，并以 Markdown 表格格式输出。",
                "layout": "请分析文档图片的版面结构，以 JSON 格式输出。",
            },
        },
        "ui": {
            "colors": {
                "primary": "#3B82F6",
                "success": "#10B981",
                "warning": "#F59E0B",
                "error": "#EF4444",
                "info": "#06B6D4",
            },
            "show_progress": True,
            "use_emoji": True,
        },
    }


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """深度合并两个字典"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _expand_env_vars(config: Any) -> Any:
    """递归展开环境变量引用 (${VAR_NAME})"""
    if isinstance(config, dict):
        return {k: _expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_expand_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        env_var = config[2:-1]
        return os.getenv(env_var, "")
    return config


def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    获取配置值
    
    Args:
        key_path: 配置路径，如 "ocr.models.flash"
        default: 默认值
        
    Returns:
        配置值
    """
    config = load_config()
    keys = key_path.split(".")
    
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def init_config():
    """初始化配置文件（如果不存在）"""
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True)
    
    if not CONFIG_FILE.exists():
        default_config = _get_default_config()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
        print(f"已创建配置文件: {CONFIG_FILE}")


def reload_config():
    """重新加载配置（清除缓存）"""
    load_config.cache_clear()
    return load_config()
```

### 1. 主入口 (cli.py)

```python
#!/usr/bin/env python3
"""PDFKit - 全能 PDF 命令行处理工具"""

import typer
from typing import Optional, List
from pathlib import Path
from rich.console import Console

from .commands import info, split, merge, extract, convert, edit, security, optimize, ocr, batch
from .utils.console import console, print_banner
from .styles.colors import Icons

app = typer.Typer(
    name="pdfkit",
    help="🔧 全能 PDF 命令行处理工具",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# 注册子命令
app.add_typer(info.app, name="info")
app.add_typer(split.app, name="split")
app.add_typer(merge.app, name="merge")
app.add_typer(extract.app, name="extract")
app.add_typer(convert.app, name="convert")
app.add_typer(edit.app, name="edit")
app.add_typer(security.app, name="security")
app.add_typer(optimize.app, name="optimize")
app.add_typer(ocr.app, name="ocr")
app.add_typer(batch.app, name="batch")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="显示版本号"),
    verbose: bool = typer.Option(False, "--verbose", help="详细输出"),
):
    """PDFKit - 全能 PDF 命令行处理工具"""
    if version:
        console.print("[title]PDFKit[/] version [number]1.0.0[/]")
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        print_banner()


if __name__ == "__main__":
    app()
```

### 2. 信息查看命令 (commands/info.py)

```python
"""PDF 信息查看命令"""

import typer
from pathlib import Path
from rich.table import Table
from rich.panel import Panel
import fitz  # PyMuPDF

from ..utils.console import console, print_success, print_error, Icons
from ..utils.validators import validate_pdf_file
from ..utils.file_utils import format_size

app = typer.Typer(help="查看 PDF 信息")


@app.command()
def show(
    file: Path = typer.Argument(..., help="PDF 文件路径"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="显示详细信息"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON 格式输出"),
):
    """
    查看 PDF 文件的详细信息
    
    示例:
        pdfkit info document.pdf
        pdfkit info document.pdf --detailed
    """
    # 验证文件
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)
    
    try:
        # 打开 PDF
        doc = fitz.open(file)
        
        # 基础信息
        info = {
            "filename": file.name,
            "path": str(file.absolute()),
            "size": format_size(file.stat().st_size),
            "pages": doc.page_count,
            "version": f"PDF {doc.metadata.get('format', 'Unknown')}",
            "encrypted": doc.is_encrypted,
        }
        
        # 元数据
        metadata = doc.metadata
        if metadata:
            info["title"] = metadata.get("title", "-")
            info["author"] = metadata.get("author", "-")
            info["subject"] = metadata.get("subject", "-")
            info["keywords"] = metadata.get("keywords", "-")
            info["creator"] = metadata.get("creator", "-")
            info["producer"] = metadata.get("producer", "-")
            info["created"] = metadata.get("creationDate", "-")
            info["modified"] = metadata.get("modDate", "-")
        
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


def _print_info_table(info: dict, detailed: bool):
    """打印信息表格"""
    
    # 创建表格
    table = Table(
        title=f"{Icons.PDF} PDF 文件信息",
        title_style="title",
        border_style="border",
        show_header=True,
        header_style="table.header",
        padding=(0, 1),
    )
    
    table.add_column("属性", style="emphasis", width=15)
    table.add_column("值", style="text")
    
    # 基础信息
    table.add_row("文件名", f"[filename]{info['filename']}[/]")
    table.add_row("路径", f"[path]{info['path']}[/]")
    table.add_row("文件大小", f"[size]{info['size']}[/]")
    table.add_row("页数", f"[pdf.pages]{info['pages']}[/] 页")
    table.add_row("PDF 版本", info['version'])
    
    # 加密状态
    if info['encrypted']:
        table.add_row("加密状态", f"[pdf.encrypted]{Icons.ENCRYPT} 已加密[/]")
    else:
        table.add_row("加密状态", f"[success]{Icons.DECRYPT} 未加密[/]")
    
    # 详细信息
    if detailed:
        table.add_section()
        table.add_row("[title]元数据[/]", "")
        table.add_row("标题", info.get('title', '-'))
        table.add_row("作者", info.get('author', '-'))
        table.add_row("主题", info.get('subject', '-'))
        table.add_row("关键词", info.get('keywords', '-'))
        table.add_row("创建程序", info.get('creator', '-'))
        table.add_row("PDF 生成器", info.get('producer', '-'))
        table.add_row("创建时间", f"[date]{info.get('created', '-')}[/]")
        table.add_row("修改时间", f"[date]{info.get('modified', '-')}[/]")
    
    console.print(table)
```

### 3. 合并命令 (commands/merge.py)

```python
"""PDF 合并命令"""

import typer
from pathlib import Path
from typing import List, Optional
import fitz

from ..utils.console import console, print_success, print_error, print_info, create_progress, Icons
from ..utils.validators import validate_pdf_files
from ..utils.file_utils import generate_output_path

app = typer.Typer(help="合并 PDF 文件")


@app.command()
def files(
    inputs: List[Path] = typer.Argument(..., help="要合并的 PDF 文件"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    bookmark: bool = typer.Option(True, "--bookmark/--no-bookmark", help="是否为每个文件添加书签"),
):
    """
    合并多个 PDF 文件
    
    示例:
        pdfkit merge file1.pdf file2.pdf file3.pdf -o combined.pdf
        pdfkit merge *.pdf -o all.pdf
    """
    # 验证文件
    valid_files = validate_pdf_files(inputs)
    if not valid_files:
        print_error("没有找到有效的 PDF 文件")
        raise typer.Exit(1)
    
    # 生成输出路径
    if output is None:
        output = generate_output_path(valid_files[0], suffix="_merged")
    
    print_info(f"准备合并 [number]{len(valid_files)}[/] 个 PDF 文件")
    
    try:
        # 创建新文档
        merged_doc = fitz.open()
        
        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.MERGE} 合并中...", 
                total=len(valid_files)
            )
            
            for pdf_file in valid_files:
                # 打开源文件
                src_doc = fitz.open(pdf_file)
                
                # 添加书签
                if bookmark:
                    # 在合并前的页数位置添加书签
                    toc = merged_doc.get_toc()
                    toc.append([1, pdf_file.stem, len(merged_doc) + 1])
                    merged_doc.set_toc(toc)
                
                # 合并页面
                merged_doc.insert_pdf(src_doc)
                src_doc.close()
                
                progress.update(task, advance=1)
        
        # 保存
        merged_doc.save(output)
        merged_doc.close()
        
        print_success(f"合并完成: [path]{output}[/]")
        print_info(f"总页数: [pdf.pages]{fitz.open(output).page_count}[/] 页")
        
    except Exception as e:
        print_error(f"合并失败: {e}")
        raise typer.Exit(1)
```

### 4. OCR 识别命令 (commands/ocr.py) - 基于阿里百炼 Qwen3-VL

```python
"""OCR 识别命令 - 基于阿里百炼 Qwen3-VL 视觉语言模型"""

import os
import base64
import typer
from pathlib import Path
from typing import Optional, List
from enum import Enum
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from openai import OpenAI

from ..utils.console import console, print_success, print_error, print_info, print_warning, create_progress, Icons
from ..utils.validators import validate_pdf_file
from ..utils.file_utils import generate_output_path

app = typer.Typer(help="OCR 文字识别 (基于阿里百炼 Qwen3-VL)")


# ============================================================================
# 配置
# ============================================================================

class OCRModel(str, Enum):
    """OCR 模型选择"""
    FLASH = "flash"   # 快速模型
    PLUS = "plus"     # 精准模型


class OutputFormat(str, Enum):
    """输出格式"""
    TEXT = "text"
    MARKDOWN = "md"
    JSON = "json"


class Region(str, Enum):
    """API 地域"""
    BEIJING = "beijing"
    SINGAPORE = "singapore"


# ============================================================================
# 配置加载 - 从配置文件读取，避免硬编码
# ============================================================================

from ..utils.config import load_config

def get_ocr_config() -> dict:
    """
    获取 OCR 配置
    配置优先级: 命令行参数 > 环境变量 > 配置文件 > 默认值
    """
    config = load_config()
    
    return config.get("ocr", {
        # 默认配置 (仅在配置文件不存在时使用)
        "models": {
            "flash": "qwen3-vl-flash",
            "plus": "qwen3-vl-plus",
        },
        "regions": {
            "beijing": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "singapore": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        },
        "default_model": "flash",
        "default_region": "beijing",
        "default_dpi": 300,
        "default_format": "text",
        "prompts": {
            "text": "请识别并提取图片中的所有文字内容，保持原有的格式和布局。只输出识别到的文字，不要添加任何解释。",
            "markdown": "请识别图片中的所有文字内容，并以 Markdown 格式输出。保持标题、列表、表格等结构。",
            "json": "请识别图片中的所有文字内容，以 JSON 格式输出，包含 text（完整文本）、paragraphs（段落数组）、tables（表格数组，如果有）字段。",
            "table": "请识别图片中的表格数据，并以 Markdown 表格格式输出。如果有多个表格，请依次输出。只输出 Markdown 表格，不要添加其他解释。",
            "layout": "请分析这张文档图片的版面结构，识别出标题、正文、表格、图片说明、页眉页脚等，以 JSON 格式输出结构化的版面分析结果。",
        },
    })


# 获取配置
OCR_CONFIG = get_ocr_config()

# 从配置文件加载模型映射 (不再硬编码)
MODEL_MAP = OCR_CONFIG.get("models", {
    "flash": "qwen3-vl-flash",
    "plus": "qwen3-vl-plus",
})

# 从配置文件加载 API 地域 (不再硬编码)
REGION_CONFIG = OCR_CONFIG.get("regions", {
    "beijing": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "singapore": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
})

# 从配置文件加载提示词 (不再硬编码)
PROMPTS = OCR_CONFIG.get("prompts", {})


# ============================================================================
# OCR 处理器
# ============================================================================

class QwenVLOCR:
    """Qwen3-VL OCR 处理器"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: OCRModel = OCRModel.FLASH,
        region: Region = Region.BEIJING,
    ):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API Key 未配置。请设置环境变量 DASHSCOPE_API_KEY 或使用 --api-key 参数\n"
                "获取 API Key: https://help.aliyun.com/zh/model-studio/get-api-key"
            )
        
        self.model_name = MODEL_MAP[model]
        self.base_url = REGION_CONFIG[region]
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
    
    def ocr_image(
        self,
        image: Image.Image,
        prompt: str = "请识别并提取图片中的所有文字内容，保持原有的格式和布局。",
        output_format: OutputFormat = OutputFormat.TEXT,
    ) -> str:
        """对单张图片进行 OCR 识别"""
        
        # 将图片转为 base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        img_url = f"data:image/png;base64,{img_base64}"
        
        # 根据输出格式调整提示词
        format_prompts = {
            OutputFormat.TEXT: "请识别并提取图片中的所有文字内容，保持原有的格式和布局。只输出识别到的文字，不要添加任何解释。",
            OutputFormat.MARKDOWN: "请识别图片中的所有文字内容，并以 Markdown 格式输出。保持标题、列表、表格等结构。",
            OutputFormat.JSON: "请识别图片中的所有文字内容，以 JSON 格式输出，包含 text（完整文本）、paragraphs（段落数组）、tables（表格数组，如果有）字段。",
        }
        
        final_prompt = prompt if prompt != "请识别并提取图片中的所有文字内容，保持原有的格式和布局。" else format_prompts[output_format]
        
        # 调用 API
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": img_url},
                        },
                        {
                            "type": "text",
                            "text": final_prompt,
                        },
                    ],
                },
            ],
        )
        
        return completion.choices[0].message.content
    
    def ocr_table(self, image: Image.Image) -> str:
        """专门提取表格数据"""
        prompt = """请识别图片中的表格数据，并以 Markdown 表格格式输出。
如果有多个表格，请依次输出。
如果表格有合并单元格，请尽量还原结构。
只输出 Markdown 表格，不要添加其他解释。"""
        
        return self.ocr_image(image, prompt=prompt)
    
    def ocr_layout(self, image: Image.Image) -> str:
        """分析文档版面结构"""
        prompt = """请分析这张文档图片的版面结构，识别出：
1. 标题和子标题
2. 正文段落
3. 表格（如果有）
4. 图片说明（如果有）
5. 页眉页脚（如果有）

请以 JSON 格式输出结构化的版面分析结果。"""
        
        return self.ocr_image(image, prompt=prompt, output_format=OutputFormat.JSON)


# ============================================================================
# CLI 命令
# ============================================================================

@app.command()
def recognize(
    file: Path = typer.Argument(..., help="PDF 文件路径"),
    model: OCRModel = typer.Option(OCRModel.FLASH, "--model", "-m", help="模型选择: flash(快速) 或 plus(精准)"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="页面范围 (如: 1-5,8,10-15)"),
    output_format: OutputFormat = typer.Option(OutputFormat.TEXT, "--format", "-f", help="输出格式"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    searchable: bool = typer.Option(False, "--searchable", help="生成可搜索 PDF"),
    dpi: int = typer.Option(300, "--dpi", help="图片转换 DPI"),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="自定义识别提示词"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="DASHSCOPE_API_KEY", help="API Key"),
    region: Region = typer.Option(Region.BEIJING, "--region", help="API 地域"),
):
    """
    对 PDF 进行 OCR 文字识别
    
    使用阿里百炼 Qwen3-VL 视觉语言模型进行识别。
    
    示例:
        # 基础 OCR (使用默认 flash 模型)
        pdfkit ocr document.pdf
        
        # 使用更精准的 plus 模型
        pdfkit ocr document.pdf -m plus
        
        # 只识别前5页，输出为 Markdown
        pdfkit ocr document.pdf -p 1-5 -f md
        
        # 生成可搜索的 PDF
        pdfkit ocr scan.pdf --searchable -o scan_searchable.pdf
    """
    # 验证文件
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)
    
    try:
        # 初始化 OCR 处理器
        ocr = QwenVLOCR(api_key=api_key, model=model, region=region)
        print_info(f"使用模型: [command]{MODEL_MAP[model]}[/]")
        
        # 打开 PDF
        doc = fitz.open(file)
        total_pages = doc.page_count
        
        # 解析页面范围
        page_list = _parse_page_range(pages, total_pages) if pages else list(range(total_pages))
        print_info(f"待识别页数: [number]{len(page_list)}[/] / {total_pages} 页")
        
        # OCR 识别
        results = []
        
        with create_progress() as progress:
            task = progress.add_task(
                f"{Icons.SEARCH} OCR 识别中...",
                total=len(page_list)
            )
            
            for page_num in page_list:
                page = doc[page_num]
                
                # 将页面渲染为图片
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # OCR 识别
                text = ocr.ocr_image(
                    img,
                    prompt=prompt or "请识别并提取图片中的所有文字内容，保持原有的格式和布局。",
                    output_format=output_format,
                )
                
                results.append({
                    "page": page_num + 1,
                    "text": text,
                })
                
                progress.update(task, advance=1)
        
        doc.close()
        
        # 输出结果
        if searchable:
            # 生成可搜索 PDF
            _create_searchable_pdf(file, results, output or generate_output_path(file, suffix="_searchable"))
        else:
            # 输出文本
            _output_results(results, output_format, output)
        
        print_success(f"OCR 识别完成！共识别 [number]{len(page_list)}[/] 页")
        
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"OCR 识别失败: {e}")
        raise typer.Exit(1)


@app.command("table")
def extract_table(
    file: Path = typer.Argument(..., help="PDF 文件路径"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="页面范围"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    model: OCRModel = typer.Option(OCRModel.PLUS, "--model", "-m", help="模型选择 (表格建议用 plus)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="DASHSCOPE_API_KEY"),
    region: Region = typer.Option(Region.BEIJING, "--region"),
):
    """
    从 PDF 中提取表格数据
    
    示例:
        pdfkit ocr table financial_report.pdf -p 5-10 -o tables.md
    """
    # 类似 recognize 命令，使用 ocr.ocr_table() 方法
    print_info("表格提取功能...")
    # ... 实现代码 ...


@app.command("layout")
def analyze_layout(
    file: Path = typer.Argument(..., help="PDF 文件路径"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="页面范围"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="DASHSCOPE_API_KEY"),
    region: Region = typer.Option(Region.BEIJING, "--region"),
):
    """
    分析 PDF 文档的版面结构
    
    示例:
        pdfkit ocr layout document.pdf -o layout.json
    """
    print_info("版面分析功能...")
    # ... 实现代码 ...


# ============================================================================
# 辅助函数
# ============================================================================

def _parse_page_range(page_str: str, total_pages: int) -> List[int]:
    """解析页面范围字符串"""
    pages = set()
    for part in page_str.split(","):
        if "-" in part:
            start, end = part.split("-")
            pages.update(range(int(start) - 1, min(int(end), total_pages)))
        else:
            page = int(part) - 1
            if 0 <= page < total_pages:
                pages.add(page)
    return sorted(pages)


def _output_results(results: List[dict], output_format: OutputFormat, output_path: Optional[Path]):
    """输出识别结果"""
    if output_format == OutputFormat.JSON:
        import json
        content = json.dumps(results, ensure_ascii=False, indent=2)
    else:
        content = "\n\n".join([
            f"--- 第 {r['page']} 页 ---\n{r['text']}" 
            for r in results
        ])
    
    if output_path:
        output_path.write_text(content, encoding="utf-8")
        print_success(f"结果已保存到: [path]{output_path}[/]")
    else:
        console.print(content)


def _create_searchable_pdf(src_file: Path, results: List[dict], output_path: Path):
    """创建可搜索的 PDF（添加隐藏文本层）"""
    doc = fitz.open(src_file)
    
    for result in results:
        page_num = result["page"] - 1
        text = result["text"]
        page = doc[page_num]
        
        # 在页面上添加隐藏的文本层
        # 这里简化处理，实际需要更精确的位置映射
        rect = page.rect
        page.insert_textbox(
            rect,
            text,
            fontsize=1,
            color=(1, 1, 1),  # 白色（不可见）
            overlay=True,
        )
    
    doc.save(output_path)
    doc.close()
    
    print_success(f"可搜索 PDF 已生成: [path]{output_path}[/]")
```

---

## 📅 开发计划

### 第一阶段：基础框架 (1-2周)

- [ ] 项目初始化和结构搭建
- [ ] CLI 框架和颜色系统
- [ ] 基础 PDF 信息读取
- [ ] split 和 merge 命令
- [ ] 基础测试框架

### 第二阶段：核心功能 (2-3周)

- [ ] 页面操作 (提取、删除、旋转、重排)
- [ ] 文本和图片提取
- [ ] PDF 转图片
- [ ] 图片转 PDF
- [ ] 压缩功能
- [ ] 水印功能

### 第三阶段：进阶功能 (2-3周)

- [ ] 加密/解密
- [ ] 书签管理
- [ ] 页眉页脚
- [ ] HTML 转 PDF
- [ ] 批量处理

### 第四阶段：智能功能 (2-3周)

- [ ] OCR 识别
- [ ] 表格提取
- [ ] PDF 比较
- [ ] 搜索和替换
- [ ] 表单填充

### 第五阶段：完善 (1-2周)

- [ ] 完善文档
- [ ] 性能优化
- [ ] 打包发布到 PyPI
- [ ] 制作 Homebrew formula

---

## 📦 安装方式设计

```bash
# 通过 pip 安装
pip install pdfkit-cli

# 通过 Homebrew 安装 (macOS)
brew install pdfkit

# 通过 pipx 安装 (推荐)
pipx install pdfkit-cli

# 开发模式安装
git clone https://github.com/your/pdfkit
cd pdfkit
pip install -e ".[dev]"
```

---

## 📄 配置文件设计

```yaml
# ~/.pdfkit/config.yaml
# PDFKit 配置文件 - 所有可能变更的选项都在此配置，避免硬编码

# ============================================================================
# 默认设置
# ============================================================================
defaults:
  output_dir: ~/Documents/pdfkit_output
  quality: medium              # low, medium, high
  overwrite: false
  verbose: false
  
# ============================================================================
# 压缩设置
# ============================================================================
compress:
  quality: medium              # low, medium, high
  image_quality: 85            # 图片压缩质量 (1-100)
  downscale_images: true       # 缩小大图片
  max_image_size: 1920         # 最大图片尺寸 (像素)
  
# ============================================================================
# 水印设置
# ============================================================================
watermark:
  font: "Helvetica"            # 字体 (Helvetica, Arial, SimHei 等)
  font_size: 48
  color: "#00000033"           # 颜色 (支持透明度)
  rotation: 45                 # 旋转角度
  position: center             # center, top-left, top-right, bottom-left, bottom-right
  opacity: 0.3                 # 透明度 (0-1)
  
# ============================================================================
# OCR 设置 (阿里百炼 Qwen3-VL)
# 所有模型相关配置都在此处，便于未来更换模型
# ============================================================================
ocr:
  # API 配置
  api_key: ${DASHSCOPE_API_KEY}    # 环境变量引用，或直接填写 API Key
  
  # 模型配置 - 可配置多个模型，便于切换
  models:
    flash: "qwen3-vl-flash"        # 快速模型 - 日常文档
    plus: "qwen3-vl-plus"          # 精准模型 - 复杂文档
    # 未来可以添加更多模型
    # ultra: "qwen3-vl-ultra"      # 超精准模型 (示例)
    # custom: "your-custom-model"  # 自定义模型
    
  # API 地域配置
  regions:
    beijing: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    singapore: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    # 可扩展其他地域
    
  # 默认值
  default_model: flash             # 默认使用的模型
  default_region: beijing          # 默认地域
  default_dpi: 300                 # PDF 转图片 DPI
  default_format: text             # 默认输出格式 (text/md/json)
  
  # 提示词模板 - 可自定义优化识别效果
  prompts:
    text: |
      请识别并提取图片中的所有文字内容，保持原有的格式和布局。
      只输出识别到的文字，不要添加任何解释。
    markdown: |
      请识别图片中的所有文字内容，并以 Markdown 格式输出。
      保持标题、列表、表格等结构。
    json: |
      请识别图片中的所有文字内容，以 JSON 格式输出，包含：
      - text: 完整文本
      - paragraphs: 段落数组
      - tables: 表格数组（如果有）
    table: |
      请识别图片中的表格数据，并以 Markdown 表格格式输出。
      如果有多个表格，请依次输出。
      只输出 Markdown 表格，不要添加其他解释。
    layout: |
      请分析这张文档图片的版面结构，识别出：
      1. 标题和子标题
      2. 正文段落
      3. 表格（如果有）
      4. 图片说明（如果有）
      5. 页眉页脚（如果有）
      请以 JSON 格式输出结构化的版面分析结果。
    # 自定义提示词
    custom: ""
    
  # 高级配置
  timeout: 60                      # API 超时时间 (秒)
  max_retries: 3                   # 失败重试次数
  retry_delay: 1                   # 重试间隔 (秒)
  
# ============================================================================
# 转换设置
# ============================================================================
convert:
  # PDF 转图片
  to_image:
    format: png                    # png, jpg, webp
    dpi: 150                       # 输出 DPI
    quality: 90                    # 图片质量 (jpg/webp)
    
  # 图片转 PDF  
  from_image:
    page_size: A4                  # A4, Letter, 或具体尺寸如 "210x297"
    margin: 10                     # 页边距 (mm)
    
  # PDF 转 Word
  to_word:
    preserve_layout: true          # 保留版面布局
    extract_images: true           # 提取图片
    
  # 网页转 PDF
  from_url:
    wait_time: 3                   # 等待页面加载 (秒)
    viewport_width: 1920           # 视口宽度
    viewport_height: 1080          # 视口高度
    full_page: true                # 截取完整页面
    
# ============================================================================
# 批量处理
# ============================================================================
batch:
  parallel: 4                      # 并行处理数
  continue_on_error: true          # 出错时继续处理其他文件
  log_file: ~/.pdfkit/batch.log    # 批量处理日志
  
# ============================================================================
# 界面设置
# ============================================================================
ui:
  # 颜色主题 (可自定义)
  colors:
    primary: "#3B82F6"             # 主色
    success: "#10B981"             # 成功
    warning: "#F59E0B"             # 警告
    error: "#EF4444"               # 错误
    info: "#06B6D4"                # 信息
    
  # 是否显示进度条
  show_progress: true
  
  # 是否使用 emoji 图标
  use_emoji: true
  
# ============================================================================
# 日志设置
# ============================================================================
logging:
  level: INFO                      # DEBUG, INFO, WARNING, ERROR
  file: ~/.pdfkit/pdfkit.log       # 日志文件路径
  max_size: 10M                    # 单个日志文件最大大小
  backup_count: 5                  # 保留的日志文件数量
```

---

## ✅ 总结

这是一个全面的 PDF 处理 CLI 工具计划，包含：

1. **40+ 个功能命令**，覆盖所有常见 PDF 操作
2. **精心设计的颜色系统**，基于现代 UI 色彩理论
3. **完整的项目结构**，便于维护和扩展
4. **详细的实现示例**，可直接参考开发
5. **清晰的开发计划**，分阶段交付

是否需要我开始创建这个项目的基础代码框架？
