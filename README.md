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

```bash
pip install pdfkit-cli
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

### 批量处理
- `batch` - 批量处理
- `watch` - 监控目录

## 配置

配置文件位于 `~/.pdfkit/config.yaml`：

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

## 开发

```bash
# 克隆项目
git clone https://github.com/your/pdfkit
cd pdfkit

# 开发模式安装
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black pdfkit
ruff check pdfkit
```

## 许可证

MIT License
