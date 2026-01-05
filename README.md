# PDFKit

> 全能 PDF 命令行处理工具

PDFKit 是一个功能全面、使用简单、界面美观的 PDF 命令行处理工具，覆盖日常 PDF 操作的所有需求。

## 特性

- **40+ 功能命令** - 覆盖 PDF 处理的所有场景
- **精美 CLI 界面** - 基于 Rich 的现代化终端体验
- **智能 OCR** - 基于阿里百炼 Qwen3-VL 的文字识别
- **批量处理** - 高效的批量操作支持
- **可配置** - 灵活的 YAML 配置文件

## 安装

### 📦 一键配置 (推荐 - 已克隆仓库)

如果您已经克隆了本仓库，可以通过以下脚本一键配置 CLI 工具：

```bash
# macOS/Linux
./scripts/setup.sh

# Windows PowerShell
.\scripts\setup.ps1
```

**脚本功能**：
- ✅ 检查 Python 环境 (需要 3.10+)
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 配置系统命令 (`pdfkit`)
- ✅ 自动添加到 PATH

**安装位置**：`~/.pdfkit-cli` 或当前项目目录

### 基础安装 (pip)

```bash
pip install pdfkit-cli
```

### 完整安装 (包含所有可选功能)

```bash
pip install 'pdfkit-cli[full]'
```

### 可选依赖

某些功能需要额外的依赖包：

| 功能 | 依赖 | 安装命令 | 说明 |
|------|------|---------|------|
| PDF 转图片 | `pdf2image` + Poppler | `pip install 'pdfkit-cli[pdf2image]'` | 需额外安装 Poppler |
| HTML 转 PDF | `weasyprint` + GTK | `pip install 'pdfkit-cli[weasyprint]'` | Windows 需 MSYS2 |
| 网页截图 | `playwright` | `pip install 'pdfkit-cli[playwright]'` | 需 `playwright install` |
| 全部功能 | 以上所有 | `pip install 'pdfkit-cli[full]'` | - |

### Windows 手动安装

Windows 64-bit 用户请参阅详细安装指南：[📖 Windows 安装指南](docs/windows-installation.md)

主要注意事项：
- 配置目录: `%APPDATA%\pdfkit\`
- Poppler: 需手动下载安装
- WeasyPrint: 需安装 MSYS2 + GTK

### 系统诊断

检查安装状态和系统信息：

```bash
pdfkit info system
```


## 快速开始

```bash
# 查看 PDF 信息
pdfkit info document.pdf

# 合并多个 PDF
pdfkit merge file1.pdf file2.pdf -o combined.pdf

# 压缩 PDF
pdfkit compress large.pdf -o small.pdf

# OCR 识别
pdfkit ocr scan.pdf
```

## 命令分类

### 基础操作
- `info` - 查看 PDF 信息
- `extract-text` - 提取文本
- `extract-images` - 提取图片

### 页面操作
- `split` - 拆分 PDF
- `merge` - 合并 PDF
- `extract` - 提取页面
- `delete` - 删除页面
- `rotate` - 旋转页面
- `reorder` - 重排页面
- `reverse` - 反转顺序

### 转换操作
- `to-image` - PDF 转图片
- `from-images` - 图片转 PDF
- `to-word` - PDF 转 Word
- `to-html` - PDF 转 HTML
- `to-markdown` - PDF 转 Markdown
- `from-url` - 网页转 PDF
- `from-html` - HTML 转 PDF

### 编辑操作
- `watermark` - 添加水印
- `header` - 添加页眉
- `footer` - 添加页脚
- `bookmark` - 添加书签
- `crop` - 裁剪页面
- `resize` - 调整大小

### 安全操作
- `encrypt` - 加密 PDF
- `decrypt` - 解密 PDF
- `protect` - 设置权限
- `clean-meta` - 清除元数据

### 优化操作
- `compress` - 压缩 PDF
- `optimize-images` - 优化图片
- `repair` - 修复 PDF

### OCR 功能
- `ocr` - 文字识别 (基于 Qwen3-VL)
- `ocr-table` - 表格提取
- `ocr-layout` - 版面分析

### AI 智能处理
- `ai extract` - 结构化信息抽取（发票、身份证等）
- `ai translate` - PDF 文档翻译（默认 Markdown 模式，可编辑）
- `ai formula` - 数学公式识别（LaTeX 输出）
- `ai extract-images` - 智能图像提取（基于视觉检测）

### 批量处理
- `batch` - 批量处理
- `watch` - 监控目录

## 配置

配置文件位置：
- **macOS/Linux**: `~/.pdfkit/config.yaml`
- **Windows**: `%APPDATA%\pdfkit\config.yaml`

```yaml
ocr:
  api_key: ${DASHSCOPE_API_KEY}
  default_model: flash
  default_region: beijing

compress:
  quality: medium
  image_quality: 85

watermark:
  font_size: 48
  opacity: 0.3
```

## 更新日志

### v0.3.0 (2026-01-03)
- **CLI 优化**: 全面测试并修复用户体验问题
- **错误提示**: 中文化技术性错误信息，添加修复建议
- **批量水印**: 支持命令行参数 `--text`、`--font-size`、`--opacity`、`--angle`
- **图片优化**: 优化后文件增大时给出警告和建议
- **测试覆盖**: 71+ 测试用例，95% 功能覆盖率

### v0.2.0 (2026-01-02)
- **MCP 服务器**: 新增错误处理、参数验证、超时重试机制
- **安全增强**: 加密功能密码验证 (最少 4 字符)
- **工具修复**: 修复 9 个 MCP 工具问题，100% 可用率
- **代码质量**: 修复 CLI 加密检查缺失、测试断言不匹配等问题

### v0.1.0 (2026-01-01)
- **CLI**: 43/50 模块完成 (86%)
- **核心功能**: 页面操作、转换、编辑、安全、优化、OCR、批量处理

---

## 开发

```bash
# 克隆项目
git clone https://github.com/linzhiqin2003/pdfkit
cd pdfkit

# 开发模式安装
pip install -e ".[dev]"

# 运行测试
pytest
```

---

## MCP 服务器

PDFKit 还提供了 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) 服务器，可以与 AI 助手（如 Claude Desktop）集成，提供强大的 PDF 处理能力。

### 功能特性

- **41 个 MCP 工具** - 覆盖所有 PDF 操作场景
- **完整功能对齐** - 与 CLI 命令功能 100% 对齐
- **异步支持** - 支持异步 OCR 处理，提高大文件处理效率
- **错误处理** - 友好的错误提示和解决建议
- **参数验证** - 完善的输入验证系统，防止无效操作
- **超时重试** - 可配置的超时和重试机制

### 工具分类

| 分类 | 工具数 | 功能 |
|------|--------|------|
| 信息查看 | 3 | 获取 PDF 信息、页数、元数据 |
| 页面操作 | 8 | 合并、拆分、提取页面/文本/图片 |
| 转换操作 | 9 | PDF 与图片/Word/HTML/Markdown/网页互转 |
| 编辑操作 | 5 | 添加水印、页眉页脚、裁剪、调整大小 |
| 安全操作 | 4 | 加密、解密、权限设置、清除元数据 |
| 优化操作 | 3 | 压缩、优化图片、修复 PDF |
| OCR 操作 | 3 | 文字识别、表格提取、版面分析 |

### 配置 Claude Desktop

在 Claude Desktop 配置文件中添加：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pdfkit": {
      "command": "/path/to/your/pdfkit-env/bin/pdfkit-mcp",
      "env": {
        "DASHSCOPE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

> **注意**: `command` 需要指向 `pdfkit-mcp` 的完整路径。可通过 `which pdfkit-mcp` 查找。

### 使用示例

配置完成后，可以在 Claude Desktop 中直接使用自然语言操作 PDF：

```
用户: 请读取 document.pdf 的信息
Claude: 好的，让我读取这个 PDF 文件... [调用 pdfkit_get_info]

用户: 将 document.pdf 的第 1-5 页提取到一个新文件
Claude: 我来帮您提取页面... [调用 pdfkit_extract_pages]

用户: 压缩这个 PDF 文件
Claude: 我来压缩文件... [调用 pdfkit_compress_pdf]
```

---

## 许可证

MIT License
