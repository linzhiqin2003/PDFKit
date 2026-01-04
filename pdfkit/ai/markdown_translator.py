"""AI Markdown 翻译器 - VL识别 + MT翻译的两阶段架构

使用 Qwen3-VL 视觉模型提取原文结构，再使用 qwen-mt-plus 专用翻译模型进行翻译。
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from PIL import Image
import fitz  # PyMuPDF

from .qwen_mt_translator import QwenMTTranslator
from ..core.ocr_handler import QwenVLOCR


# VL模型识别提示词 - 保留Markdown结构
OCR_EXTRACT_PROMPT = """请识别并提取图片中的所有文字内容。

要求：
1. 保持原文的段落结构
2. 标题使用 # ## ### 等 Markdown 格式
3. 列表保持 - 或 1. 2. 格式
4. 表格使用 Markdown 表格格式
5. 代码块使用 ``` 包裹
6. 公式使用 $...$ 或 $$...$$ 格式
7. 只输出原文，不要翻译，不要添加解释

直接输出识别到的文字内容。
"""


def pdf_page_to_image(page: fitz.Page, dpi: int = 300) -> Image.Image:
    """将 PDF 页面转换为 PIL Image

    Args:
        page: PyMuPDF 页面对象
        dpi: 渲染 DPI

    Returns:
        PIL Image 对象
    """
    pix = page.get_pixmap(dpi=dpi)
    img_data = pix.tobytes("png")
    return Image.open(fitz.io.BytesIO(img_data))


class AIMarkdownTranslator:
    """AI文档翻译器 - Markdown模式（VL识别 + MT翻译）"""

    def __init__(
        self,
        vl_model: str = "plus",
        mt_model: str = "qwen-mt-plus",
        region: str = "beijing",
        dpi: int = 300,
        api_key: Optional[str] = None,
    ):
        """
        初始化翻译器

        Args:
            vl_model: VL模型选择 (flash/plus/ocr)
            mt_model: 翻译模型名称
            region: 区域 (beijing/singapore)
            dpi: PDF渲染DPI
            api_key: API密钥
        """
        self.dpi = dpi

        # VL模型用于文档识别
        self.ocr = QwenVLOCR(model=vl_model, region=region, api_key=api_key)

        # 专用翻译模型
        self.translator = QwenMTTranslator(api_key=api_key, region=region, model=mt_model)

    def translate(
        self,
        file_path: Path,
        target_lang: str,
        source_lang: str = "auto",
        pages: Optional[List[int]] = None,
        domain: Optional[str] = None,
        glossary_path: Optional[Path] = None,
        preserve_original: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> str:
        """
        翻译PDF文档为Markdown

        Args:
            file_path: PDF文件路径
            target_lang: 目标语言代码
            source_lang: 源语言代码，默认 auto 自动检测
            pages: 页面列表（0-based索引），None 表示全部
            domain: 领域提示（英文描述）
            glossary_path: 术语表CSV文件路径
            preserve_original: 是否在输出中保留原文
            progress_callback: 进度回调函数，签名为 (current, total, description, advance)

        Returns:
            Markdown格式的翻译结果
        """
        # 验证语言对
        is_valid, error = self.translator.validate_language_pair(source_lang, target_lang)
        if not is_valid:
            raise ValueError(error)

        # 打开PDF
        doc = fitz.open(file_path)
        if pages is None:
            pages = list(range(doc.page_count))

        total = len(pages)
        results = []

        # 加载术语表
        terminologies = self._load_glossary(glossary_path) if glossary_path else None

        # 构建领域提示
        domain_prompt = self._build_domain_prompt(domain, terminologies)

        for idx, page_num in enumerate(pages):
            # 阶段1: VL模型提取原文
            if progress_callback:
                progress_callback(idx, total, f"[warning]提取[/][black]第[/] [bold_text]{page_num + 1}[/] [black]页原文[/]", False)

            image = pdf_page_to_image(doc[page_num], dpi=self.dpi)
            original_text = self.ocr.ocr_image(image, prompt=OCR_EXTRACT_PROMPT)

            if not original_text or not original_text.strip():
                # 更新进度
                if progress_callback:
                    progress_callback(idx + 1, total, f"[success]完成第 {page_num + 1} 页空白[/]", True)
                continue

            # 阶段2: 专用模型翻译
            if progress_callback:
                progress_callback(idx, total, f"[info]翻译[/][black]第[/] [bold_text]{page_num + 1}[/] [black]页[/]", False)

            translated_text = self.translator.translate(
                text=original_text,
                target_lang=target_lang,
                source_lang=source_lang,
                domain=domain_prompt,
                terminologies=terminologies,
            )

            results.append({
                "page": page_num + 1,
                "original": original_text if preserve_original else None,
                "translated": translated_text,
            })

            # 更新进度
            if progress_callback:
                progress_callback(idx + 1, total, f"[success]完成第 {page_num + 1} 页[/]", True)

        doc.close()

        return self._format_output(
            file_path, target_lang, source_lang, results, preserve_original
        )

    def _build_domain_prompt(
        self,
        domain: Optional[str],
        terminologies: Optional[List[Dict[str, str]]],
    ) -> str:
        """构建领域提示

        Args:
            domain: 领域提示
            terminologies: 术语表

        Returns:
            合并后的领域提示
        """
        parts = []

        if domain:
            parts.append(domain)

        # 术语表提示会在 translate 方法中通过 system message 传递
        # 这里不需要重复添加

        return " ".join(parts) if parts else None

    def _load_glossary(self, path: Path) -> List[Dict[str, str]]:
        """加载术语表CSV

        Args:
            path: CSV文件路径

        Returns:
            术语表列表，格式为 [{"src": "...", "tgt": "..."}, ...]
        """
        glossary = []
        try:
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    src = row.get("src", "").strip()
                    tgt = row.get("tgt", "").strip()
                    if src and tgt:
                        glossary.append({"src": src, "tgt": tgt})
        except Exception as e:
            raise ValueError(f"加载术语表失败: {e}")

        return glossary

    def _format_output(
        self,
        file_path: Path,
        target_lang: str,
        source_lang: str,
        results: List[Dict],
        preserve_original: bool,
    ) -> str:
        """格式化Markdown输出

        Args:
            file_path: 源文件路径
            target_lang: 目标语言
            source_lang: 源语言
            results: 翻译结果列表
            preserve_original: 是否保留原文

        Returns:
            格式化后的Markdown文本
        """
        lines = [
            "# 文档翻译\n",
            f"**源文件**: {file_path.name}  ",
            f"**翻译方向**: {source_lang} → {target_lang}  ",
            f"**翻译时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**翻译模式**: Markdown (VL + MT)\n",
            "---\n",
        ]

        for item in results:
            lines.append(f"## 第 {item['page']} 页\n")

            # 保留原文（折叠显示）
            if preserve_original and item.get("original"):
                lines.append("<details>")
                lines.append("<summary>📄 查看原文</summary>\n")
                lines.append(item["original"])
                lines.append("\n</details>\n")

            # 翻译结果
            lines.append(item["translated"])
            lines.append("\n---\n")

        return "\n".join(lines)
