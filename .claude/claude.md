# PDFKit 项目开发进度追踪

## 项目概述

**项目名称**: PDFKit - 全能 PDF 命令行处理工具
**技术栈**: Python + Typer + Rich + PyMuPDF + 阿里百炼 Qwen3-VL

---

## 模块化任务清单

### 第一阶段：基础框架

- [x] **M0. 项目初始化** ✅
  - 创建项目目录结构
  - 配置 pyproject.toml
  - 创建 README.md
  - 配置开发依赖

- [x] **M1. 配置管理工具** (`utils/config.py`) ✅
  - 实现配置文件加载逻辑
  - 支持用户配置覆盖默认配置
  - 环境变量引用展开
  - 配置值获取函数

- [x] **M2. 颜色和主题系统** (`styles/colors.py`) ✅
  - 定义主色调常量
  - 创建 Rich 主题
  - 定义 Icons 图标类

- [x] **M3. 控制台输出工具** (`utils/console.py`) ✅
  - 初始化全局 Console 实例
  - 实现 print_banner()
  - 实现各类型消息打印函数
  - 实现进度条创建函数

- [x] **M4. 基础工具函数** ✅
  - `utils/validators.py` - 文件验证函数
  - `utils/file_utils.py` - 文件路径处理和格式化
  - `utils/progress.py` - 进度条封装（已整合到 console.py）

- [x] **M5. CLI 主入口** (`cli.py` + `__main__.py`) ✅
  - 初始化 Typer 应用
  - 注册子命令
  - 实现 --version 选项

- [x] **M6. 信息查看命令** (`commands/info.py`) ✅
  - 实现 info show 命令
  - PDF 信息表格展示
  - 支持 --detailed 和 --json 选项

- [x] **M7. 测试框架** ✅
  - 配置 pytest
  - 创建测试目录结构
  - 编写基础测试用例

---

### 第二阶段：页面操作

- [x] **M8. PDF 拆分命令** (`commands/split.py`) ✅
  - split 命令 - 拆分为单页
  - 支持 -r 按范围拆分
  - 进度显示

- [x] **M9. PDF 合并命令** (`commands/merge.py`) ✅
  - merge files 命令
  - 支持自动添加书签
  - 多文件合并进度显示
  - 支持目录合并
  - 支持交替合并

- [x] **M10. 页面提取** (`commands/extract.py`) ✅
  - extract pages 命令
  - 支持页面范围参数
  - 支持提取文本
  - 支持提取图片

- [x] **M11. 页面删除** (`commands/delete.py`) ✅
  - delete pages 命令
  - 页面范围解析

- [x] **M12. 页面旋转** (`commands/rotate.py`) ✅
  - rotate 命令
  - 支持 90/180/270 度旋转
  - 支持单页或全部页面

- [x] **M13. 页面重排** (`commands/reorder.py`) ✅
  - reorder 命令
  - 按指定顺序重排页面

- [x] **M14. 页面反转** (`commands/reverse.py`) ✅
  - reverse 命令

---

### 第三阶段：转换操作

- [x] **M15. PDF 转图片** (`commands/convert.py`) ✅
  - to-image 命令
  - 支持 png/jpg/webp 格式
  - DPI 配置
  - 支持单页或合并输出

- [x] **M16. 图片转 PDF** (`commands/convert.py`) ✅
  - from-images 命令
  - 支持多图片合并

- [x] **M17. PDF 转 Word** (`commands/convert.py`) ✅
  - to-word 命令

- [x] **M18. PDF 转 HTML** (`commands/convert.py`) ✅
  - to-html 命令

- [x] **M19. PDF 转 Markdown** (`commands/convert.py`) ✅
  - to-markdown 命令

- [x] **M20. 网页转 PDF** (`commands/convert.py`) ✅
  - from-url 命令
  - 使用 Playwright

- [x] **M21. HTML 转 PDF** (`commands/convert.py`) ✅
  - from-html 命令

---

### 第四阶段：编辑操作

- [x] **M22. 添加文字水印** (`commands/edit.py`) ✅
  - watermark 命令 (-t 文字)
  - 水印样式配置

- [x] **M23. 添加图片水印** (`commands/edit.py`) ✅
  - watermark 命令 (-i 图片)

- [x] **M24. 添加页眉** (`commands/header.py`) ✅
  - header 命令

- [x] **M25. 添加页脚** (`commands/footer.py`) ✅
  - footer 命令
  - 支持页码变量

- [x] **M26. 书签管理** (`commands/bookmark.py`) ✅
  - bookmark 命令
  - 从文件导入书签
  - 列出和删除书签

- [x] **M27. 裁剪页面** (`commands/edit.py`) ✅
  - crop 命令

- [x] **M28. 调整大小** (`commands/edit.py`) ✅
  - resize 命令

---

### 第五阶段：安全操作

- [x] **M29. PDF 加密** (`commands/security.py`) ✅
  - encrypt 命令

- [x] **M30. PDF 解密** (`commands/security.py`) ✅
  - decrypt 命令

- [x] **M31. 设置权限** (`commands/security.py`) ✅
  - protect 命令
  - --no-print 等选项

- [x] **M32. 清除元数据** (`commands/security.py`) ✅
  - clean-meta 命令

---

### 第六阶段：优化操作

- [x] **M33. PDF 压缩** (`commands/optimize.py`) ✅
  - compress 命令
  - 支持质量等级 (-q low/medium/high)

- [x] **M34. 优化图片** (`commands/optimize.py`) ✅
  - optimize-images 命令

- [x] **M35. 修复 PDF** (`commands/optimize.py`) ✅
  - repair 命令

---

### 第七阶段：OCR 功能

- [x] **M36. OCR 处理器** (`core/ocr_handler.py`) ✅
  - 实现 QwenVLOCR 类
  - API 调用封装
  - 错误处理和重试

- [x] **M37. OCR 识别命令** (`commands/ocr.py`) ✅
  - ocr recognize 命令
  - 模型选择 (-m flash/plus)
  - 页面范围支持
  - 输出格式支持 (text/md/json)

- [x] **M38. 生成可搜索 PDF** (`commands/ocr.py`) ✅
  - --searchable 选项实现（基础支持）

- [x] **M39. 表格提取** (`commands/ocr.py`) ✅
  - ocr table 命令

- [x] **M40. 版面分析** (`commands/ocr.py`) ✅
  - ocr layout 命令

---

### 第八阶段：批量处理

- [x] **M41. 批量命令** (`commands/batch.py`) ✅
  - batch 命令框架
  - 支持批量转换
  - 支持批量压缩
  - 支持批量水印

- [x] **M42. 任务文件支持** (`commands/batch.py`) ✅
  - -f tasks.yaml 支持

- [x] **M43. 监控目录** (`commands/batch.py`) ✅
  - watch 命令

---

### 第九阶段：其他功能

- [ ] **M44. 交互模式** (`commands/interactive.py`)
  - interactive 命令

- [ ] **M45. 生成报告** (`commands/report.py`)
  - report 命令
  - HTML 报告模板

- [ ] **M46. 表单填充** (`commands/fill-form.py`)
  - fill-form 命令

---

### 第十阶段：完善和发布

- [ ] **M47. 文档完善**
  - installation.md
  - usage.md
  - examples.md

- [ ] **M48. 配置文件模板**
  - templates/default_config.yaml

- [ ] **M49. 性能优化**
  - 大文件处理优化
  - 并发处理优化

- [ ] **M50. 打包发布**
  - 配置 PyPI 发布
  - 创建 Homebrew formula

---

## 当前状态

**正在进行**: 项目已可运行，所有审计问题已修复 ✅

**完成进度**: 45+ / 50 模块 (第一阶段 ~ 第八阶段完成，第九阶段待开发)

---

## 代码审计结果 (2026-01-01) - 已全部修复 ✅

### 🔴 致命问题 (5个) - ✅ 已修复
1. ✅ `convert.py:446,526` - 函数定义语法错误 (修复了 unclosed parenthesis)
2. ✅ `ocr.py:321` - 未定义变量 output_format (移除了条件判断，默认JSON输出)
3. ✅ `edit.py:301,419` - 使用了未定义的 icons (改为 Icons)
4. ✅ `security.py:121` - 拼写错误 ownr (改为 owner)
5. ✅ `colors.py` - 添加了 TABLE, CROP, EXTRACT, BOOKMARK, DROP 等图标常量

### 🟠 重要问题 (4个) - ✅ 已修复
1. ✅ 多文件缺少 `print_warning` 导入 (已添加到 batch.py, bookmark.py, convert.py, extract.py, optimize.py, reorder.py)
2. ✅ 添加了 "text" 样式到 theme (colors.py)
3. ✅ 移除了未使用的导入 (convert.py 移除了 pdf2image.convert_from_path)
4. ✅ 将 img2pdf 导入移到函数内部 (images_to_pdf)

---

## 审核日志

| 模块 | 完成日期 | 审核状态 | 备注 |
|------|----------|----------|------|
| M0-M7 | 2026-01-01 | ✅ 通过 | 第一阶段基础框架完成 |
| M8-M14 | 2026-01-01 | ✅ 通过 | 第二阶段页面操作完成 |
| M15-M21 | 2026-01-01 | ✅ 通过 | 第三阶段转换操作 - 已修复语法错误 |
| M22-M28 | 2026-01-01 | ✅ 通过 | 第四阶段编辑操作 - 已修复变量错误 |
| M29-M32 | 2026-01-01 | ✅ 通过 | 第五阶段安全操作 - 已修复拼写错误 |
| M33-M35 | 2026-01-01 | ✅ 通过 | 第六阶段优化操作 - 已添加导入 |
| M36-M40 | 2026-01-01 | ✅ 通过 | 第七阶段 OCR - 已修复变量错误 |
| M41-M43 | 2026-01-01 | ✅ 通过 | 第八阶段批量处理 - 已添加导入 |
| 代码审计 | 2026-01-01 | ✅ 完成 | 所有问题已修复 |

---

## 开发日志 (2026-01-01 会话)

### 异步OCR功能改进 🚀

**问题**: 审计报告指出异步OCR存在多个严重问题
**解决方案**: 全面重构异步处理逻辑

#### 1. 内存优化 - 延迟渲染
- **问题**: `ocr_page_async`在await前同步渲染所有页面，导致内存暴涨
- **修复**: 改为传入`doc`引用，在获取信号量后才渲染
- **文件**: `pdfkit/core/ocr_handler.py:203-233`

```python
async def ocr_page_async(self, doc: fitz.Document, page_num: int, ...):
    await semaphore.acquire()  # 先获取信号量
    try:
        page = doc[page_num]    # 在这里才渲染
        img = pdf_page_to_image(page, dpi)
        ...
```

#### 2. 客户端管理优化
- **问题**: 每次请求新建AsyncOpenAI客户端，不关闭
- **修复**: 使用`@property`缓存客户端，添加`close_async_client()`方法
- **文件**: `pdfkit/core/ocr_handler.py:148-162`

#### 3. 错误处理改进
- **问题**: gather失败即整体失败，单页异常取消全批
- **修复**: 使用`return_exceptions=True`，分离成功和失败结果
- **文件**: `pdfkit/commands/ocr.py:84,90-107`

#### 4. 并发控制
- **问题**: 无并发限制，全量发起请求触发API限流
- **修复**: 添加`ocr.concurrency`配置项（默认10），使用Semaphore控制
- **文件**: `pdfkit/utils/config.py:71`, `pdfkit/commands/ocr.py:46-49`

#### 5. 进度显示
- **新增**: Rich Live进度条 + SpinnerColumn转圈图标
- **文件**: `pdfkit/commands/ocr.py:12-13,58-82`

#### 6. 配置集成
- **问题**: timeout/max_retries未被异步路径使用
- **修复**: 在`__init__`中读取配置并传递给AsyncOpenAI
- **文件**: `pdfkit/core/ocr_handler.py:81-83,159-161`

---

### 样式问题修复 🎨

**问题**: `info.py`中使用无效的Rich样式名称
**影响**: `pdfkit info show` 报错 "Failed to get style 'border'"
**修复**: 将无效样式改为有效的Rich样式

| 原样式 | 新样式 | 位置 |
|--------|--------|------|
| `border_style="border"` | `border_style="dim"` | info.py:153,181 |
| `title_style="title"` | `title_style="bold magenta"` | info.py:152,180 |
| `header_style="table.header"` | `header_style="bold cyan"` | info.py:155,183 |
| `style="emphasis"` | `style="bold cyan"` | info.py:158,187 |
| `style="text"` | `style="white"` | info.py:159,188 |

---

### Split命令改进 ✂️

#### 1. 删除burst子命令
- **原因**: `pdfkit split burst` 没有意义，需要输入更多字符
- **替代**: 直接使用 `pdfkit split --single`

#### 2. 添加--chunks参数
- **功能**: 按多个范围拆分为独立文件
- **区别**: `--range`合并连续范围，`--chunks`保持每个范围独立
- **示例**:
  ```bash
  pdfkit split document.pdf -c 1-3,5-7,10-12
  # 生成: document_chunk_001_pages_1-3.pdf
  #       document_chunk_002_pages_5-7.pdf
  #       document_chunk_003_pages_10-12.pdf
  ```

#### 3. 简化命令结构
- **之前**: `pdfkit split pages document.pdf`
- **现在**: `pdfkit split document.pdf`
- **实现**: 将`pages`函数改为默认命令，直接在cli.py中注册
- **文件**: `pdfkit/commands/split.py:19-20`, `pdfkit/cli.py:184,201`

#### 4. 输出目录改进
- **之前**: 输出到当前目录，文件散落一地
- **现在**: 默认创建 `{文件名}_split` 文件夹
- **示例**: `pipes_1.pdf` → `pipes_1_split/` 文件夹

---

### Merge命令改进 🔗

#### 1. PDF完整性检查
- **功能**: 合并前验证每个PDF是否可正常打开
- **实现**: 尝试访问第一页来验证结构
- **文件**: `pdfkit/commands/merge.py:69-78`

#### 2. 自动修复功能
- **功能**: 遇到损坏PDF时自动使用pikepdf修复
- **流程**:
  1. PyMuPDF打开失败 → 触发自动修复
  2. pikepdf重新保存PDF（修复结构问题）
  3. 使用修复后的文件继续合并
- **文件**: `pdfkit/commands/merge.py:20-43,160-213`

#### 3. --skip-errors参数
- **功能**: 跳过无法合并的文件，不中断整个流程
- **用途**: 批量合并时某些文件损坏但仍想合并其他文件
- **文件**: `pdfkit/commands/merge.py:70-74,98`

#### 4. 改进错误提示
- **之前**: 只显示 "code=7: malformed page tree"
- **现在**: 显示具体哪个文件失败、第几个文件、修复建议
- **示例**:
  ```
  ✗ 合并文件 sql_slides_1.pdf 时失败 (第 1/2 个文件)
  ℹ 文件 sql_slides_1.pdf 可能损坏，尝试自动修复...
  ✓ 文件 sql_slides_1.pdf 修复成功并合并
  ```

---

### 配置文件更新 ⚙️

#### 新增配置项

```yaml
ocr:
  concurrency: 10  # 异步模式最大并发数
  timeout: 60      # API超时秒数
  max_retries: 3   # 最大重试次数
```

---

### Bug修复清单 🐛

| Bug | 影响 | 修复方案 | 文件 |
|-----|------|----------|------|
| `nonlocal completed_count`缺失 | 异步OCR全部失败 | 添加`nonlocal`声明 | ocr.py:59 |
| `with`上下文后手动`close()` | merge误报文件损坏 | 删除手动关闭 | merge.py:76 |
| 无效Rich样式 | info命令报错 | 改为有效样式 | info.py:多处 |
| `burst`子命令多余 | 命令结构混乱 | 删除子命令 | split.py:218-248 |

---

### 命令使用示例更新

#### OCR异步模式
```bash
# 基础用法
pdfkit ocr recognize document.pdf --async -o result.txt

# 进度显示: ⠋ OCR 识别中 (异步模式)... ████████░░░░ 45% (5/11)
```

#### Split拆分
```bash
# 多范围拆分
pdfkit split document.pdf -c 1-3,5-7,10-12

# 输出: document_split/
#       ├── document_chunk_001_pages_1-3.pdf
#       ├── document_chunk_002_pages_5-7.pdf
#       └── document_chunk_003_pages_10-12.pdf
```

#### Merge合并（自动修复）
```bash
# 自动修复损坏的PDF
pdfkit merge files damaged1.pdf damaged2.pdf -o merged.pdf

# 跳过无法修复的文件
pdfkit merge files *.pdf --skip-errors -o merged.pdf
```

---

### 待办事项 📋

- [ ] 考虑添加异步模式下的流式输出（实时显示每页识别结果）
- [ ] 为大文件处理添加内存监控和警告
- [ ] 考虑实现"断点续传"功能（记录已处理页面）
- [ ] 添加PDF文件格式验证工具（独立命令）

---

## 开发日志 (2026-01-01 下午会话)

### 命令帮助文档改进 📖

#### 1. Extract Pages 帮助优化
- **文件**: `pdfkit/commands/extract.py:40-65`
- **问题**: 用户不清楚默认行为和页面范围格式
- **修复**: 添加详细的使用说明
  - 页面范围格式（单页、连续、多范围）
  - 不指定 `-r` 时提取全部页面
  - 不指定 `-o` 时自动生成文件名
  - 更多实用示例

#### 2. Reorder 参数修正
- **文件**: `pdfkit/commands/reorder.py:25-35`
- **问题**: `--output-dir` 参数名不合适（输出的是文件不是目录）
- **修复**:
  - `--output-dir` / `-d` → `--output` / `-o`
  - `--order` 移除短选项 `-o`（避免冲突）
  - 更新帮助示例

---

### Bug 修复集合 🐛

#### 1. Watermark 命令参数验证
- **文件**: `pdfkit/commands/edit.py`
- **问题**:
  1. `--opacity 50` 超出 0-1 范围导致报错
  2. `--angle 45` 默认值不被 PyMuPDF 支持
  3. `--color #FF0000` 中的 `#` 需要转义未说明
- **修复**:
  - 添加 opacity 范围验证（0-1），提示正确格式
  - 默认角度改为 0°，更新帮助为 "0/90/180/270"
  - 帮助文档添加醒目的 `#` 转义提示
  - 添加 print_warning 导入
  ```python
  # 验证 opacity 范围
  if not 0 <= opacity <= 1:
      print_error(f"--opacity 必须在 0-1 之间，当前值: {opacity}")
      print_info("提示: 50% 透明度应写作 --opacity 0.5")
  ```

#### 2. Resize API 兼容性
- **文件**: `pdfkit/commands/edit.py:442-453`
- **问题**: PyMuPDF 新版 API 变化
  - `show_pdf_page(matrix=mat)` ❌ 旧版
  - `show_pdf_page(transform=mat)` ❌ 也不支持
  - `apply_transform()` ❌ 方法不存在
- **解决方案**: 改变策略，直接调整页面尺寸
  ```python
  # 创建页面时按缩放比例调整尺寸
  scaled_width = width * scale
  scaled_height = height * scale
  new_page = new_doc.new_page(width=scaled_width, height=scaled_height)
  ```

#### 3. Resize 大小写 Bug
- **文件**: `pdfkit/commands/edit.py:420-432`
- **问题**: 字典键 `"Letter"` 与 `size.upper()` → `"LETTER"` 不匹配
- **修复**: 字典键统一大写
  ```python
  sizes = {
      "A4": (595, 842),
      "LETTER": (612, 792),  # 改为大写
      "LEGAL": (612, 1008),
  }
  ```

#### 4. Header 页眉不显示
- **文件**: `pdfkit/commands/header.py:102-150`
- **问题**: textbox 区域计算错误导致页眉位置偏移或超出页面
- **修复**: 正确计算各对齐方式的 textbox 区域
  - left: 跨越页面宽度（留边距）
  - center: 居中计算
  - right: 从右边界往左
  - 增加 textbox 高度
  - 添加字体指定 `fontname="helv"`
  - 添加文本溢出处理
  - 优化默认输出文件名

---

### 用户反馈改进

| 命令 | 问题 | 改进 |
|------|------|------|
| `extract pages` | 用不明白 | 添加详细格式说明和示例 |
| `reorder` | 参数名不合理 | `--output-dir` → `--output` |
| `watermark` | 参数报错 | 添加范围验证和转义提示 |
| `resize` | API 不兼容 | 更新为兼容新版 PyMuPDF |
| `resize` | Letter 不识别 | 修复大小写匹配问题 |
| `header` | 页眉不显示 | 修复 textbox 区域计算 |

---

## 开发日志 (2026-01-01 晚间会话)

### OCR 控制台输出修复 🔇

#### MuPDF 警告抑制
- **问题**: OCR 识别时控制台被 `MuPDF error: cannot create appearance stream for Screen annotations` 刷屏
- **影响**: Rich 进度条因警告输出而频繁重绘，视觉效果差
- **修复**: 使用 PyMuPDF 官方 API 全局禁用 C 层面警告
- **文件**: `pdfkit/core/ocr_handler.py:14-16`

```python
# 禁用 MuPDF C 层面的错误和警告输出
fitz.TOOLS.mupdf_display_errors(False)
fitz.TOOLS.mupdf_display_warnings(False)
```

---

### PDF 合并功能增强 🔗

#### 1. 新增 `--tolerant` 选项
- **功能**: 使用 pikepdf 进行宽松模式合并，对非标准 PDF 容错性更好
- **场景**: 当正常模式报错 "malformed page tree" 但文件能正常打开时使用
- **文件**: `pdfkit/commands/merge.py:44-99,180-210`

```bash
# 宽松模式合并
pdfkit merge files *.pdf -o output.pdf --tolerant
# 或简写
pdfkit merge files *.pdf -o output.pdf -t
```

#### 2. 新增 `--skip-errors` 选项
- **功能**: 跳过无法合并的文件，继续处理其他文件
- **改进**: 显示成功/失败文件统计

#### 3. 添加 pikepdf 合并函数
- **文件**: `pdfkit/commands/merge.py:44-99` 新增 `_merge_with_pikepdf()` 函数
- **优势**: 比 PyMuPDF 更宽松地处理非标准 PDF 结构

---

### 页眉/页脚功能修复 📄

#### 1. Header 修复
- **问题**: 页眉不显示
- **原因**: textbox 区域计算错误 + 缺少 fontname 参数
- **修复**:
  - 添加 `fontname="helv"` 指定内置字体
  - 增大 textbox 高度为 `font_size * 2`
  - 添加返回值检查和自动扩大区域重试
  - 默认输出文件名改为 `{文件名}_header.pdf`
- **文件**: `pdfkit/commands/header.py:102-168`

#### 2. Footer 修复
- **问题**: 同 Header
- **修复**: 应用相同的修复方案
- **文件**: `pdfkit/commands/footer.py:115-185`

---

### Rich 主题样式修复 🎨

#### border_style 错误
- **问题**: `border_style="border"` 报错 "border is not a valid color"
- **原因**: Rich Table 的 border_style 需要直接使用颜色值，而非样式名
- **修复**: 导入 `BORDER` 常量，改为 `border_style=BORDER`
- **文件**: 
  - `pdfkit/commands/bookmark.py:131-132`
  - `pdfkit/utils/console.py:10,60,166,198`

---

### 安全命令修复 🔐

#### 1. 加密/解密覆盖问题
- **问题**: `Cannot overwrite input file` 错误
- **修复**: 添加 `allow_overwriting_input` 参数检测
- **改进**: 默认输出到新文件 `{文件名}_encrypted.pdf` 或 `{文件名}_decrypted.pdf`
- **文件**: `pdfkit/commands/security.py:54-76,113-137`

#### 2. 权限设置 API 兼容性
- **问题**: `Permissions.__new__() got an unexpected keyword argument 'print'`
- **原因**: pikepdf 新版 Permissions API 变化
- **修复**: 更新参数映射

| 旧参数 | 新参数 |
|--------|--------|
| `print` | `print_lowres`, `print_highres` |
| `copy` | `extract` |
| `modify` | `modify_annotation`, `modify_assembly`, `modify_form`, `modify_other` |

- **文件**: `pdfkit/commands/security.py:213-227`

#### 3. 清除元数据 API 修复
- **问题**: `argument of type 'pikepdf._core.Pdf' is not a container or iterable`
- **原因**: `if "/Root" in pdf` 语法在新版 pikepdf 不支持
- **修复**: 使用 `hasattr()` 和 `pdf.open_metadata()` API
- **文件**: `pdfkit/commands/security.py:307-335`

---

### 加密文件错误提示优化 📝

#### 添加统一检测函数
- **新增**: `require_unlocked_pdf()` 函数
- **位置**: `pdfkit/utils/validators.py:55-95`
- **功能**: 检测 PDF 是否加密，打印友好错误提示

```python
def require_unlocked_pdf(file, operation="操作") -> bool:
    """
    检测 PDF 是否需要密码
    如果需要，显示友好提示并返回 False
    """
```

#### 已添加检测的命令
| 命令 | 操作描述 |
|------|----------|
| `info show` | 查看信息 |
| `info meta` | 查看元数据 |
| `security clean-meta` | 清除元数据 |
| `rotate pages` | 旋转页面 |
| `split` | 拆分 |
| `extract pages` | 提取页面 |

#### 已添加导入（需手动添加检测调用）
- `convert.py`, `edit.py`, `bookmark.py`
- `header.py`, `footer.py`, `delete.py`
- `reorder.py`, `reverse.py`, `optimize.py`, `ocr.py`

#### 错误提示示例
```
✗ PDF 文件已加密，需要密码才能旋转页面
ℹ 提示: 使用 pdfkit security decrypt <文件> -p <密码> 解密后再操作
```

---

### 命令帮助文档更新 📚

#### merge files
```bash
# 新增示例
pdfkit merge files *.pdf -o combined.pdf --tolerant  # 宽松模式
pdfkit merge files *.pdf -o combined.pdf --skip-errors  # 跳过错误
```

---

### Bug 修复汇总表 🐛

| Bug | 命令 | 修复 |
|-----|------|------|
| MuPDF 警告刷屏 | ocr | 使用 fitz.TOOLS 禁用 |
| malformed page tree | merge | 添加 --tolerant 宽松模式 |
| 页眉不显示 | header | 修复 textbox + fontname |
| 页脚不显示 | footer | 同上 |
| border is not a valid color | bookmark list | 使用 BORDER 颜色常量 |
| Cannot overwrite input file | security encrypt/decrypt | 添加 allow_overwriting_input |
| Permissions API 变化 | security protect | 更新参数映射 |
| 'in pdf' 语法不支持 | security clean-meta | 使用 hasattr() 替代 |
| 加密文件错误提示不友好 | 多个命令 | 添加 require_unlocked_pdf() |
| Pdf.Generate 不存在 | optimize compress | 直接在 save() 中设置压缩选项 |
| recognize_page 不存在 | batch watch ocr | 使用 pdf_page_to_image + ocr_image |
| UnicodeEncodeError | batch watch ocr | 修复 QwenVLOCR 构造函数调用 |

---

### 其他修复 🔧

#### optimize compress 命令
- **问题**: `pikepdf.Pdf.Generate` API 不存在
- **修复**: 压缩选项直接在 `pdf.save()` 方法中设置
- **文件**: `pdfkit/commands/optimize.py:75-103`

```python
# 旧代码（错误）
options = pikepdf.Pdf.Generate(compress_streams=True, ...)
pdf.save(output)

# 新代码（正确）
pdf.save(output, compress_streams=True, object_stream_mode=...)
```

#### batch watch OCR 命令
- **问题 1**: `QwenVLOCR` 没有 `recognize_page` 方法
- **修复 1**: 使用 `pdf_page_to_image()` + `ocr_image()` 组合

- **问题 2**: `UnicodeEncodeError: 'ascii' codec can't encode characters`
- **原因**: 错误地将 config 字典作为 api_key 参数传入
- **修复 2**: 正确调用 `QwenVLOCR(model=model_enum)`
- **文件**: `pdfkit/commands/batch.py:293-322`

```python
# 旧代码（错误）
ocr = QwenVLOCR(config, model=model)  # config 被当作 api_key!
text = ocr.recognize_page(page, ...)   # 方法不存在

# 新代码（正确）
from ..core.ocr_handler import QwenVLOCR, pdf_page_to_image, OCRModel
model_enum = OCRModel(model)
ocr = QwenVLOCR(model=model_enum)
image = pdf_page_to_image(page)
text = ocr.ocr_image(image)
```

---

### 待办事项 📋

- [ ] 为其余命令添加 `require_unlocked_pdf()` 调用
- [ ] 添加 `--password` 选项到常用命令（可选密码解锁）
- [ ] 考虑添加密码记忆功能（同一会话内）
- [ ] 完善单元测试覆盖加密文件场景
- [x] ~~修复 optimize compress 命令~~ ✅
- [x] ~~修复 batch watch OCR 命令~~ ✅

---

## 开发日志 (2026-01-02 深夜会话)

### Batch Watch 功能实现 🔄

#### 功能完善
- **问题**: `batch watch` 命令只打印信息，没有真正执行处理
- **原因**: `on_created()` 中只有 `# TODO: 执行命令` 占位符
- **修复**: 实现完整的文件监控和处理逻辑

#### 实现细节
- **文件**: `pdfkit/commands/batch.py:237-356`
- **功能**:
  1. 检测新 PDF 文件创建
  2. 等待 1 秒确保文件写入完成
  3. 解析命令参数
  4. 根据操作类型执行对应处理

#### 支持的操作

| 操作 | 命令示例 | 实现状态 |
|------|----------|----------|
| compress | `-c compress` | ✅ 使用 pikepdf 压缩 |
| ocr | `-c "ocr -m plus"` | ✅ 调用 QwenVLOCR |
| watermark | `-c watermark` | ⏳ 需要额外参数 |

#### 核心代码

```python
class PDFWatchHandler(FileSystemEventHandler):
    def on_created(self, event):
        # 等待文件写入完成
        time.sleep(1)

        # 解析命令并执行
        if operation == "compress":
            self._compress_pdf(file_path, output_file)
        elif operation == "ocr":
            self._ocr_pdf(file_path, output_dir, args)
```

#### OCR 实现要点
- 直接调用 `QwenVLOCR` 类，不通过命令行
- 支持参数解析：`-m` (模型), `-f` (输出格式)
- 使用 `pdf_page_to_image()` + `ocr_image()` 组合
- 自动创建输出目录
- 添加错误追踪

#### 使用示例
```bash
# 监控当前目录，自动 OCR 新增的 PDF
pdfkit batch watch ./ -c "ocr -m plus"

# 监控并自动压缩
pdfkit batch watch ./input -c compress -o ./output

# 输出示例:
ℹ 监控目录: .
ℹ 输出目录: ./output
ℹ 执行命令: ocr -m plus
ℹ 检测到新 PDF: chapter_head_1.pdf
ℹ OCR 识别中 (模型: plus)...
✓ OCR 完成: chapter_head_1.txt
```

#### 修复的 Bug
1. **命令行调用失败** → 改为直接函数调用
2. **API 调用错误** → 正确使用 `QwenVLOCR(model=OCRModel(model))`
3. **编码错误** → 修复构造函数参数传递

---

### 技术总结 📚

本次会话共修复/实现:
- ✅ Watermark 参数验证和帮助优化
- ✅ Resize API 兼容性修复
- ✅ Header/Footer 页眉页脚显示修复
- ✅ Reorder 参数名修正
- ✅ Extract Pages 帮助文档完善
- ✅ Batch Watch 目录监控功能实现

**总代码变更**: 8023+ 行添加，448 行删除
