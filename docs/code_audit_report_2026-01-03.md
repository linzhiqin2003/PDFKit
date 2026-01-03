# PDFKit 代码审计报告 (2026-01-03)

- 审计日期: 2026-01-03
- 项目版本: 0.1.0
- 审计范围: `pdfkit/`, `tests/`, `README.md`, `pyproject.toml`, `docs/`
- 审计方式: 静态代码审阅 (未执行测试或运行命令)

## 代码库解读

### 架构与职责
- CLI 入口: `pdfkit/__main__.py` -> `pdfkit/cli.py`，基于 Typer 注册命令并用 Rich 输出。
- 命令层: `pdfkit/commands/*`，负责参数解析与交互输出，部分命令直接操作 PyMuPDF/pikepdf。
- 核心层: `pdfkit/core/*`，提供可复用的 PDF 处理逻辑（合并、拆分、转换、OCR、安全、优化等）。
- MCP 服务器: `pdfkit/mcp/server.py` + `pdfkit/mcp/tools/*`，将核心能力封装为 MCP 工具。
- 工具与配置: `pdfkit/utils/*`，包含配置加载、验证器、文件工具、控制台输出。
- 测试: `tests/*`，覆盖 CLI 基础、验证器、MCP 工具注册与错误路径。

### 关键数据流
- CLI: Typer 解析参数 -> `utils.validators` 校验 -> 命令层或核心层执行 -> 写入输出文件。
- MCP: 工具函数 -> `mcp.utils.validate_pdf_file` -> 核心层 -> `format_success/format_error` 返回。
- OCR: `core/ocr_handler.QwenVLOCR` -> OpenAI 兼容 API (DashScope) -> 文本拼接输出。

## 审计发现摘要

| 严重级别 | 数量 | 说明 |
| --- | --- | --- |
| High | 1 | MCP 侧文件/网络访问缺少范围限制 |
| Medium | 4 | 错误响应规范、加密处理、覆盖策略、测试失配 |
| Low | 3 | 未使用参数、超时配置缺失、解析逻辑分叉 |
| Info | 1 | 批量任务存在占位实现 |

## 详细问题

### High
1. MCP 工具对本地路径与 URL 缺乏范围限制，存在潜在数据访问/SSRF 风险  
   - 影响: 若 MCP 服务暴露给非可信客户端，可读取任意 `.pdf` 路径或访问任意 URL。  
   - 证据: `pdfkit/mcp/utils.py:123`, `pdfkit/mcp/tools/convert_tools.py:402`  
   - 建议: 增加允许目录白名单、URL scheme 校验与配置开关；默认禁用 `file://` 或内网地址。

### Medium
2. MCP 错误响应缺少 `success: false`，与 schema/测试预期不一致  
   - 影响: 客户端/测试通过 `result["success"]` 判断时会失败或 KeyError。  
   - 证据: `pdfkit/mcp/utils.py:62`, `pdfkit/mcp/schemas.py:146`, `tests/test_mcp/test_tools/test_convert_tools.py:18`  
   - 建议: `format_error` 统一返回 `success: False`，并保持与 `ToolResponse` 一致。

3. CLI 加密检查不一致，部分命令未调用 `require_unlocked_pdf`  
   - 影响: 加密 PDF 会出现模糊异常或行为不确定。  
   - 证据: `pdfkit/commands/delete.py:55`, `pdfkit/commands/reorder.py:51`, `pdfkit/commands/ocr.py:251`  
   - 建议: 在命令入口统一执行加密可读性检查，并提示解密路径。

4. `defaults.overwrite` 配置未被 CLI 广泛使用，存在意外覆盖风险  
   - 影响: 默认配置建议不覆盖，但多数命令直接保存/覆盖原文件。  
   - 证据: `pdfkit/utils/validators.py:158`, `pdfkit/commands/delete.py:86`, `pdfkit/commands/edit.py:158`  
   - 建议: CLI 输出路径统一走 `validate_output_path`，或显式加 `--overwrite` 开关。

5. 测试与实现不一致，CI 易失败  
   - 影响: 测试导入错误或断言不匹配。  
   - 证据: `tests/test_mcp/test_core/test_pdf_merge.py:7`, `tests/test_mcp/test_core/test_pdf_convert.py:7`, `tests/test_validators.py:36`  
   - 建议: 修复测试导入与断言，或补齐实现/导出。

### Low
6. `optimize_images` 中的 `dpi` 参数未生效  
   - 影响: 用户认为 DPI 会影响压缩结果，实际仅重压 JPEG。  
   - 证据: `pdfkit/core/pdf_optimize.py:181`  
   - 建议: 实现基于 DPI 的重采样，或移除参数并更新文档。

7. OCR 同步客户端未设置超时/重试  
   - 影响: API 卡顿时可能长时间阻塞。  
   - 证据: `pdfkit/core/ocr_handler.py:85`  
   - 建议: 同步客户端也使用 `timeout` 和 `max_retries` 配置。

8. 页面范围解析逻辑多处重复且语义不一致  
   - 影响: CLI/MCP 不同入口对同一输入行为不同，增加维护成本。  
   - 证据: `pdfkit/utils/validators.py:99`, `pdfkit/core/pdf_split.py:87`, `pdfkit/core/pdf_extract.py:142`  
   - 建议: 统一解析逻辑并在不同层共享。

### Info
9. 批量相关功能仍为占位实现  
   - 影响: 用户可见命令与实际行为不一致。  
   - 证据: `pdfkit/commands/batch.py:152`, `pdfkit/commands/batch.py:218`  
   - 建议: 明确标注未实现或完善处理流程。

## 优先级建议

1. 统一 MCP 错误响应结构并修复测试导入错误。  
2. 补齐 CLI 加密检查与输出覆盖策略。  
3. 为 MCP 增加路径/URL 访问约束。  
4. 收敛页面范围解析逻辑，减少重复实现。  

## 测试建议

- 建议执行: `pytest`  
- 如果不方便执行测试，至少运行 `python -m py_compile pdfkit/**/*.py` 验证语法。
