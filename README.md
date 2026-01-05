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

**macOS/Linux:**
```bash
chmod +x scripts/setup.sh    # 添加可执行权限
./scripts/setup.sh
```

**Windows PowerShell:**
```powershell
.\scripts\setup.ps1
```

**脚本功能**：
- ✅ 检查 Python 环境 (需要 3.10+)
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 配置系统命令 (`pdfkit`)
- ✅ 自动添加到 PATH

**安装位置**：`~/.pdfkit-cli` 或当前项目目录

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

### 基础操作 (3)
- `info` - 查看 PDF 信息
- `info meta` - 查看元数据
- `info system` - 系统诊断

### 提取操作 (3)
- `extract pages` - 提取页面
- `extract text` - 提取文本
- `extract images` - 提取图片

### 页面操作 (8)
- `split` - 拆分 PDF
- `merge` - 合并 PDF
- `merge dir` - 目录合并
- `merge interleave` - 交错合并
- `delete` - 删除页面
- `rotate` - 旋转页面
- `reorder` - 重排页面
- `reverse` - 反转顺序

### 转换操作 (7)
- `to-image` - PDF 转图片
- `from-images` - 图片转 PDF
- `to-word` - PDF 转 Word
- `to-html` - PDF 转 HTML
- `to-markdown` - PDF 转 Markdown
- `from-html` - HTML 转 PDF
- `from-url` - 网页转 PDF

### 编辑操作 (8)
- `watermark` - 添加水印
- `crop` - 裁剪页面
- `resize` - 调整大小
- `header` - 添加页眉
- `footer` - 添加页脚
- `bookmark add` - 添加书签
- `bookmark list` - 列出书签
- `bookmark remove` - 删除书签

### 安全操作 (4)
- `encrypt` - 加密 PDF
- `decrypt` - 解密 PDF
- `protect` - 设置权限
- `clean-meta` - 清除元数据

### 优化操作 (3)
- `compress` - 压缩 PDF
- `optimize-images` - 优化图片
- `repair` - 修复 PDF

### OCR 功能 (3)
- `ocr` - 文字识别
- `ocr table` - 表格提取
- `ocr layout` - 版面分析

### AI 智能处理 (4)
- `ai extract` - 结构化信息抽取（发票、简历等）
- `ai translate` - PDF 文档翻译（Markdown 模式）
- `ai formula` - 数学公式识别（LaTeX）
- `ai extract-images` - 智能图像提取

### 批量处理 (3)
- `batch` - 批量处理
- `batch from-file` - 从任务文件批量处理
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

### v0.8.1 (2026-01-04)
- **Windows 支持**: 全面适配 Windows 64-bit 平台
- **系统诊断**: 新增 `pdfkit info system` 命令
- **CLI UI 重构**: 基于 Industrial 风格的现代化界面（实时进度、结构化错误、操作摘要）
- **AI 进度修复**: 修复 AI 功能进度条跳变问题

### v0.8.0 (2026-01-04)
- **AI 翻译**: Markdown 模式设为默认，支持双语对照

### v0.7.0 ~ v0.4.0 (2026-01-04)
- **AI 图像提取**: 智能检测并提取图表、照片等
- **AI 公式识别**: 数学/物理/化学公式转 LaTeX
- **AI 翻译**: PDF 视觉翻译（保留排版）
- **AI 智能抽取**: 发票、简历等结构化信息抽取

### v0.3.0 (2026-01-03)
- **CLI 优化**: 错误提示中文化
- **问题修复**: 修复 merge 命令 malformed page tree 问题

### v0.2.0 (2026-01-02)
- **MCP 服务器**: 41 个工具，支持远程 HTTP Server
- **错误处理**: 参数验证、超时重试机制

### v0.1.0 (2026-01-01)
- **核心功能**: PDF 拆分、合并、转换、水印、加密等
- **OCR**: 基于 Qwen3-VL 的文字识别

---

## 开发

```bash
# 克隆项目
git clone https://github.com/linzhiqin2003/pdfkit
cd pdfkit

# 运行安装脚本
chmod +x scripts/setup.sh
./scripts/setup.sh

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
