# PDFKit MCP 工具参考文档

本文档描述了 PDFKit MCP 服务器的所有可用工具。

## 概述

PDFKit MCP 服务器提供了 33 个工具，涵盖 PDF 处理的各个方面：
- 信息查看 (3 个工具)
- 页面操作 (8 个工具)
- 转换操作 (7 个工具)
- 编辑操作 (5 个工具)
- 安全操作 (4 个工具)
- 优化操作 (3 个工具)
- OCR 操作 (3 个工具)

---

## 信息查看工具

### pdfkit_get_info
获取 PDF 文件的基本信息。

**参数:**
- `file_path` (string): PDF 文件路径
- `detailed` (boolean, 可选): 是否返回详细信息（包括元数据）

**返回:**
```json
{
  "success": true,
  "data": {
    "filename": "document.pdf",
    "path": "/path/to/document.pdf",
    "size_bytes": 12345,
    "size_human": "12.1 KB",
    "page_count": 10,
    "version": "1.4",
    "is_encrypted": false,
    ...
  },
  "message": "成功获取 PDF 信息: document.pdf (10 页)"
}
```

### pdfkit_get_page_count
快速获取 PDF 文件的页数。

**参数:**
- `file_path` (string): PDF 文件路径

**返回:**
```json
{
  "success": true,
  "data": {"page_count": 10},
  "message": "PDF 共 10 页"
}
```

### pdfkit_get_metadata
获取 PDF 文件的元数据。

**参数:**
- `file_path` (string): PDF 文件路径

**返回:**
```json
{
  "success": true,
  "data": {
    "title": "文档标题",
    "author": "作者",
    "subject": "主题",
    "keywords": "关键词",
    ...
  }
}
```

---

## 页面操作工具

### pdfkit_merge_files
合并多个 PDF 文件为一个文件。

**参数:**
- `file_paths` (array[string]): 要合并的 PDF 文件路径列表
- `output_path` (string): 输出文件路径
- `bookmark` (boolean, 可选): 是否为每个文件添加书签 (默认: true)
- `sort` (boolean, 可选): 是否按文件名排序 (默认: false)
- `auto_repair` (boolean, 可选): 是否自动修复损坏的 PDF (默认: true)
- `skip_errors` (boolean, 可选): 是否跳过错误继续处理 (默认: false)

### pdfkit_split_by_pages
按指定页面范围拆分 PDF。

**参数:**
- `file_path` (string): PDF 文件路径
- `page_ranges` (string): 页面范围，如 "1-5,8,10-15"
- `output_dir` (string): 输出目录
- `prefix` (string, 可选): 输出文件名前缀

### pdfkit_split_single_pages
将 PDF 的每一页拆分为单独的文件。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_dir` (string): 输出目录
- `prefix` (string, 可选): 输出文件名前缀

### pdfkit_split_by_size
按文件大小拆分 PDF。

**参数:**
- `file_path` (string): PDF 文件路径
- `max_size_mb` (number): 每个文件的最大大小 (MB)
- `output_dir` (string): 输出目录
- `prefix` (string, 可选): 输出文件名前缀

### pdfkit_split_by_count
按固定页数拆分 PDF。

**参数:**
- `file_path` (string): PDF 文件路径
- `pages_per_file` (integer): 每个文件的页数
- `output_dir` (string): 输出目录
- `prefix` (string, 可选): 输出文件名前缀

### pdfkit_extract_pages
提取指定页面到新 PDF 文件。

**参数:**
- `file_path` (string): PDF 文件路径
- `page_ranges` (string): 页面范围，如 "1-5,8,10-15"
- `output_path` (string): 输出文件路径

### pdfkit_extract_text
提取 PDF 文本内容。

**参数:**
- `file_path` (string): PDF 文件路径
- `page_ranges` (string, 可选): 页面范围
- `output_format` (string, 可选): 输出格式 (txt/md)

### pdfkit_extract_images
提取 PDF 中的图片。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_dir` (string): 输出目录
- `page_ranges` (string, 可选): 页面范围
- `format` (string, 可选): 输出格式 (png/jpg)

---

## 转换操作工具

### pdfkit_pdf_to_images
将 PDF 转换为图片。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_dir` (string): 输出目录
- `format` (string, 可选): 输出格式 (png/jpg/webp)
- `dpi` (integer, 可选): 输出 DPI (默认: 150)
- `page_ranges` (string, 可选): 页面范围
- `single` (boolean, 可选): 是否合并为一张图片

### pdfkit_images_to_pdf
将图片合并为 PDF。

**参数:**
- `image_paths` (array[string]): 图片文件路径列表
- `output_path` (string): 输出 PDF 文件路径
- `sort` (boolean, 可选): 是否按文件名排序

### pdfkit_pdf_to_word
将 PDF 转换为 Word 文档。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径

### pdfkit_pdf_to_html
将 PDF 转换为 HTML。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径

### pdfkit_pdf_to_markdown
将 PDF 转换为 Markdown。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径

### pdfkit_html_to_pdf
将 HTML 文件转换为 PDF。

**参数:**
- `html_path` (string): HTML 文件路径
- `output_path` (string): 输出 PDF 文件路径

### pdfkit_url_to_pdf
将网页转换为 PDF。

**参数:**
- `url` (string): 网页 URL
- `output_path` (string): 输出 PDF 文件路径
- `wait_time` (number, 可选): 等待页面加载时间（秒）
- `full_page` (boolean, 可选): 是否截取完整页面
- `width` (integer, 可选): 视口宽度

---

## 编辑操作工具

### pdfkit_add_watermark
添加水印到 PDF。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径
- `text` (string, 可选): 文字水印内容
- `image_path` (string, 可选): 图片水印路径
- `angle` (integer, 可选): 旋转角度 (0/90/180/270)
- `opacity` (number, 可选): 透明度 (0-1)
- `font_size` (integer, 可选): 字体大小
- `color` (string, 可选): 颜色 (十六进制，如 #FF0000)
- `position` (string, 可选): 位置 (center/top-left/top-right/bottom-left/bottom-right)
- `layer` (string, 可选): 图层 (overlay/underlay)

### pdfkit_crop_pages
裁剪 PDF 页面。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径
- `margin` (array[number], 可选): 边距 [top, right, bottom, left]
- `box` (array[number], 可选): 裁剪框 [x0, y0, x1, y1]

### pdfkit_resize_pages
调整 PDF 页面大小。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径
- `size` (string, 可选): 页面大小 (A4/Letter/A3/A5 或 宽x高)
- `scale` (number, 可选): 缩放比例

### pdfkit_add_header
添加页眉到 PDF。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径
- `text` (string): 页眉文字
- `font_size` (integer, 可选): 字体大小
- `align` (string, 可选): 对齐方式 (left/center/right)
- `margin_top` (number, 可选): 顶部边距（点）
- `page_ranges` (string, 可选): 页面范围

### pdfkit_add_footer
添加页脚到 PDF。

支持的变量: {page} - 当前页码, {total} - 总页数, {date} - 当前日期, {time} - 当前时间

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径
- `text` (string): 页脚文字（支持变量）
- `font_size` (integer, 可选): 字体大小
- `align` (string, 可选): 对齐方式 (left/center/right)
- `margin_bottom` (number, 可选): 底部边距（点）
- `page_ranges` (string, 可选): 页面范围

---

## 安全操作工具

### pdfkit_encrypt_pdf
加密 PDF 文件。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径
- `password` (string): 设置密码

### pdfkit_decrypt_pdf
解密 PDF 文件。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径
- `password` (string): PDF 密码

### pdfkit_protect_pdf
设置 PDF 权限。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径
- `owner_password` (string): 所有者密码
- `user_password` (string, 可选): 用户密码
- `no_print` (boolean, 可选): 禁止打印
- `no_copy` (boolean, 可选): 禁止复制
- `no_modify` (boolean, 可选): 禁止修改

### pdfkit_clean_metadata
清除 PDF 元数据。

删除可能包含敏感信息的元数据，如作者、创建程序、创建/修改日期、标题、主题、关键词。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径

---

## 优化操作工具

### pdfkit_compress_pdf
压缩 PDF 文件大小。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径
- `quality` (string, 可选): 压缩质量 (low/medium/high)

### pdfkit_optimize_images
优化 PDF 中的图片。

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径
- `dpi` (integer, 可选): 目标 DPI（降低 DPI 可减小文件大小）
- `quality` (integer, 可选): JPEG 质量 (1-100)

### pdfkit_repair_pdf
修复损坏的 PDF 文件。

尝试修复以下问题: 损坏的 PDF 结构、损坏的对象、损坏的交叉引用表

**参数:**
- `file_path` (string): PDF 文件路径
- `output_path` (string): 输出文件路径

---

## OCR 操作工具

### pdfkit_ocr_recognize
使用 OCR 识别 PDF 文本。

**参数:**
- `file_path` (string): PDF 文件路径
- `page_ranges` (string, 可选): 页面范围
- `model` (string, 可选): 模型选择 (flash/plus/ocr)
- `output_format` (string, 可选): 输出格式 (text/md/json)
- `api_key` (string, 可选): OCR API Key
- `async_mode` (boolean, 可选): 是否使用异步模式
- `concurrency` (integer, 可选): 异步模式最大并发数

**注意**: 需要设置 `DASHSCOPE_API_KEY` 环境变量或提供 `api_key` 参数。

### pdfkit_ocr_extract_tables
使用 OCR 提取 PDF 中的表格。

**参数:**
- `file_path` (string): PDF 文件路径
- `page_ranges` (string, 可选): 页面范围
- `model` (string, 可选): 模型选择，推荐使用 plus 获得更好的表格识别效果
- `api_key` (string, 可选): OCR API Key
- `async_mode` (boolean, 可选): 是否使用异步模式
- `concurrency` (integer, 可选): 异步模式最大并发数

### pdfkit_ocr_analyze_layout
使用 OCR 分析 PDF 文档版面结构。

识别文档中的标题、正文、表格、图片等元素，返回结构化的版面分析结果。

**参数:**
- `file_path` (string): PDF 文件路径
- `page_ranges` (string, 可选): 页面范围
- `model` (string, 可选): 模型选择，推荐使用 plus 获得更好的版面分析效果
- `api_key` (string, 可选): OCR API Key
- `async_mode` (boolean, 可选): 是否使用异步模式
- `concurrency` (integer, 可选): 异步模式最大并发数

---

## 通用返回格式

所有工具返回以下格式的字典：

### 成功响应
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功描述"
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误描述",
  "error_type": "错误类型",
  "suggestion": "解决建议（可选）"
}
```

---

## 使用示例

### Claude Desktop 配置

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "pdfkit": {
      "command": "python",
      "args": ["-m", "pdfkit.mcp.server"],
      "env": {
        "DASHSCOPE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 基本使用

```
用户: 请读取 document.pdf 的信息
Claude: 好的，让我使用 pdfkit_get_info 工具...

用户: 将 document.pdf 的第 1-5 页提取到一个新文件
Claude: 好的，让我使用 pdfkit_extract_pages 工具...

用户: 将所有 PDF 文件合并为一个
Claude: 好的，让我使用 pdfkit_merge_files 工具...
```
