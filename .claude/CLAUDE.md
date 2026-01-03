# PDFKit 项目开发进度追踪

## 项目概述

**项目名称**: PDFKit - 全能 PDF 命令行处理工具  
**技术栈**: Python + Typer + Rich + PyMuPDF + 阿里百炼 Qwen3-VL

---

## CLI 模块完成状态

| 阶段 | 模块 | 状态 |
|------|------|------|
| 第一阶段 | M0-M7 基础框架 | ✅ 完成 |
| 第二阶段 | M8-M14 页面操作 (split/merge/extract/delete/rotate/reorder/reverse) | ✅ 完成 |
| 第三阶段 | M15-M21 转换操作 (PDF↔图片/Word/HTML/Markdown/网页) | ✅ 完成 |
| 第四阶段 | M22-M28 编辑操作 (水印/页眉/页脚/书签/裁剪/调整大小) | ✅ 完成 |
| 第五阶段 | M29-M32 安全操作 (加密/解密/权限/清除元数据) | ✅ 完成 |
| 第六阶段 | M33-M35 优化操作 (压缩/优化图片/修复) | ✅ 完成 |
| 第七阶段 | M36-M40 OCR功能 (识别/表格提取/版面分析) | ✅ 完成 |
| 第八阶段 | M41-M43 批量处理 (batch/任务文件/监控目录) | ✅ 完成 |
| 第九阶段 | M44-M46 其他功能 (交互模式/报告/表单填充) | ⏳ 待开发 |
| 第十阶段 | M47-M50 完善发布 (文档/配置模板/性能优化/打包) | ⏳ 待开发 |

**CLI 完成进度**: 43/50 模块

---

## MCP 服务器完成状态

> 详细规划见: `docs/mcp_expansion_plan.md`

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 1 | 基础架构 (server.py, schemas.py, utils.py) | ✅ 完成 |
| Phase 2 | 核心层抽取 (pdf_info/merge/split/extract.py) | ✅ 完成 |
| Phase 3-6 | 全部 MCP 工具实现 | ✅ 完成 |
| Phase 7 | 测试与文档 | ✅ 完成 |

**MCP 工具总数**: 41 个 (全部可用)

### 核心模块清单

| 模块 | 主要功能 |
|------|----------|
| `core/pdf_info.py` | get_pdf_info, get_page_count, get_metadata |
| `core/pdf_merge.py` | merge_files (三层容错: pypdf→PyMuPDF→pikepdf) |
| `core/pdf_split.py` | split_by_pages/chunks/count/size |
| `core/pdf_extract.py` | extract_pages/text/images |
| `core/pdf_convert.py` | pdf_to_images/word/html/markdown, html_to_pdf (weasyprint), url_to_pdf (async playwright) |
| `core/pdf_edit.py` | add_watermark, crop_pages, resize_pages |
| `core/pdf_header.py` | add_header, add_footer |
| `core/pdf_security.py` | encrypt_pdf, decrypt_pdf, protect_pdf, clean_metadata |
| `core/pdf_optimize.py` | compress_pdf, optimize_images, repair_pdf |
| `core/ocr_handler.py` | QwenVLOCR (同步/异步，阿里百炼 Qwen3-VL) |

---

## 重要修复记录

### 2026-01-01: 代码审计修复

**致命问题 (5个)**:
- convert.py: 函数定义语法错误
- ocr.py: 未定义变量 output_format
- edit.py: 使用了未定义的 icons
- security.py: 拼写错误 ownr
- colors.py: 添加缺失图标常量

**重要问题 (4个)**:
- 多文件缺少 print_warning 导入
- 添加 "text" 样式到 theme
- 移除未使用的导入
- img2pdf 导入移到函数内部

### 2026-01-03: MCP 工具修复 🔧

**修复前**: 78% (32/41) → **修复后**: 100% (41/41)

| 问题 | 工具 | 修复方案 |
|------|------|----------|
| document closed | pdf_to_word/html/markdown | 在 close() 前保存 page_count |
| document closed | add_watermark/crop/resize | 在 close() 前保存 page_count |
| 命名冲突 | html_to_pdf | 改用 weasyprint/PyMuPDF Story |
| Sync API in async | url_to_pdf | 改用 async playwright API |
| malformed page tree | merge_files | 三层容错: pypdf→PyMuPDF→pikepdf |

**修改文件**:
- `pdfkit/core/pdf_convert.py`
- `pdfkit/core/pdf_edit.py`
- `pdfkit/core/pdf_merge.py`
- `pdfkit/mcp/tools/convert_tools.py`
- `pyproject.toml` (weasyprint 替代 pdfkit)

---

## 关键配置

### OCR 配置 (config.yaml)
```yaml
ocr:
  concurrency: 10  # 异步模式最大并发数
  timeout: 60      # API超时秒数
  max_retries: 3   # 最大重试次数
```

### Claude Desktop 配置

**注意**: `command` 需要指向 `pdfkit-mcp` 的完整路径。可通过 `which pdfkit-mcp` 查找。

```json
{
  "mcpServers": {
    "pdfkit": {
      "type": "stdio",
      "command": "/path/to/your/pdfkit-env/bin/pdfkit-mcp",
      "env": {
        "DASHSCOPE_API_KEY": "your-api-key"
      }
    }
  }
}
```

**示例（本项目虚拟环境）**:
```json
{
  "mcpServers": {
    "pdfkit": {
      "type": "stdio",
      "command": "/Users/linzhiqin/Documents/Code/pdftools/pdfkit-env/bin/pdfkit-mcp",
      "env": {
        "DASHSCOPE_API_KEY": "your-api-key"
      }
    }
  }
}
```

---

## 待办事项

- [ ] M44-M50: 第九、十阶段 CLI 功能
- [ ] 完善单元测试覆盖率 (目标 80%+)
- [ ] 添加端到端集成测试
- [ ] 性能优化 (大文件处理)
- [ ] 发布到 PyPI

---

## 审计报告索引

| 日期 | 报告文件 | 内容 |
|------|----------|------|
| 2026-01-01 | `docs/code_audit_report.md` | CLI 代码审计 |
| 2026-01-03 | `docs/code_audit_report_2026-01-03.md` | MCP 代码审计 |

---

*最后更新: 2026-01-03*