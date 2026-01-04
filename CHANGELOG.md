# Changelog

All notable changes to PDFKit will be documented in this file.

## [Unreleased]

### Added - Windows 支持与系统诊断 (2026-01-04)

- **Windows 64-bit 完整支持**: 全面适配 Windows 平台，解决路径、控制台和依赖问题。
  - 智能识别 Windows 系统路径 (%APPDATA%, Documents)。
  - 自动启用 Windows 10+ 控制台 ANSI 颜色支持。
  - 可充依赖分离：WeasyPrint 和 pdf2image 移至可选依赖。
- **系统诊断工具**: 新增 `pdfkit info system` 命令，用于检查环境信息、路径配置和依赖状态，支持 JSON 输出。
- **文档**: 新增 `docs/windows-installation.md` 指南。

### Added - CLI UI 全面优化 (2026-01-04)

基于 `cli-ui-design` 最佳实践，采用工业实用主义美学风格重构 CLI 界面。

- **LiveProgress 实时进度**: 新增单行实时更新进度条，不产生滚动输出（应用于 `split`, `compress`, `ai` 等命令）。
- **StageProgress 多阶段进度**: 树状进度显示，清晰展示复杂任务的分阶段状态。
- **操作摘要面板**: 任务结束后显示带边框的统计摘要（成功/失败/耗时）。
- **结构化错误**: 提供包含原因分析和建议操作的友好错误提示。
- **安全警告**: 针对加密、权限修改等高风险操作添加分级安全警告。
- **工业风格表格**: 信息展示采用粗边框、高对比度的工业风格表格。
- **颜色主题**: 新增 Industrial 橙色主题系统。

UI 改造已覆盖 `merge`, `split`, `delete`, `optimize`, `info`, `convert`, `ocr`, `security` 等核心命令。

### Fixed - v0.8.1 (2026-01-04)

- **AI 进度显示**: 修复 AI 功能（公式识别、图像提取、翻译）进度条从 0% 跳变到 100% 的问题，实现真实的逐页实时进度与动态任务描述。

---

## [0.8.0] - 2026-01-04

### Added
- **AI Markdown 翻译模式**: 新增两阶段翻译架构（VL 识别 + MT 翻译），输出可编辑 Markdown，完美保留文档结构。
  - 支持双语对照 (`--preserve-original`)。
  - 支持专业领域提示和术语表。
  - 设为默认翻译模式，原图像模式标记为 Beta。

---

## [0.7.1] - 2026-01-04

### Fixed
- **文档一致性**: 移除文档中未实现的 markdown 输出模式说明。
- **依赖提示**: 增强 `requests` 库缺失时的错误提示和安装指引。
- **JSON 清理**: 自动清理 OCR JSON 输出中的 Markdown 代码块标记。

---

## [0.7.0] - 2026-01-04

### Added
- **AI 智能图像提取**: 新增 `pdfkit ai extract-images` 命令。
  - 基于 Qwen3-VL 视觉大模型进行目标检测。
  - 支持按类型过滤（图表、照片、表格等）和页面范围选择。
  - 自动生成提取元数据。

---

## [0.6.0] - 2026-01-04

### Added
- **AI 公式识别**: 新增 `pdfkit ai formula` 命令。
  - 识别数学/物理/化学公式并输出 LaTeX 代码。
  - 支持 PDF 和图片输入，支持公式解释模式。

---

## [0.5.0] - 2026-01-04

### Added
- **AI 智能翻译 (图像模式)**: 新增 `pdfkit ai translate` 命令（基于 qwen-mt-image）。
  - 实现 PDF 视觉翻译，完美保留原始排版。
  - 支持 OSS/Local 上传，支持术语表。

---

## [0.4.0] - 2026-01-04

### Added
- **AI 智能抽取**: 新增 `pdfkit ai extract` 命令。
  - 基于 Qwen3-VL 抽取结构化信息（发票、简历等）。
  - 支持自定义字段和复杂 JSON/YAML 模板。

---

## [0.3.0] - 2026-01-03

### Changed
- CLI 交互体验优化，错误提示全面中文化。

### Fixed
- 修复 `merge` 命令在特定文件下的 malformed page tree 问题。

---

## [0.2.0] - 2026-01-02

### Added
- **MCP 服务器**: 完整实现 41 个 MCP 工具，支持远程 HTTP Server。
- MCP 错误处理、参数验证和重试机制。

### Fixed
- 修复多个 MCP 工具的 "document closed" 错误。
- 修复 `url_to_pdf` 同步调用问题。

---

## [0.1.0] - 2026-01-01

### Added
- **核心功能**: PDF 拆分、合并、转换、水印、加密等基础功能。
- **OCR**: 基于 Qwen3-VL 的文字识别、表格提取。
- **CLI 框架**: 基于 Typer 和 Rich 的命令行界面。
