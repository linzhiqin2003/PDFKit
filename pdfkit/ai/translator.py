"""AI 文档翻译器 - 支持图像翻译和 Markdown 翻译两种模式

图像翻译模式：使用 qwen-mt-image 模型，保留原始排版
Markdown 模式：使用 VL + MT 两阶段翻译，输出可编辑的 Markdown
"""

import csv
from pathlib import Path
from typing import Optional, List, Tuple, Union

import fitz  # PyMuPDF

from .image_translator import QwenImageTranslator, validate_language_pair
from .uploader import create_uploader, UploadMethod
from .markdown_translator import AIMarkdownTranslator


def _import_requests():
    """Lazy import requests for optional dependency"""
    try:
        import requests
        return requests
    except ImportError:
        raise ImportError(
            "AI Translate 功能需要安装 requests 库。\n"
            "请运行以下命令安装:\n"
            "  pip install requests\n"
            "或:\n"
            "  pip3 install requests"
        )


class OutputMode(str):
    """输出模式"""
    PDF = "pdf"
    IMAGES = "images"
    MARKDOWN = "markdown"


class AITranslator:
    """AI 文档翻译器 - 图像翻译模式

    PDF → 逐页渲染图片 → 图像翻译 → 翻译后图片 → 合成新PDF
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        upload_method: str = "base64",
        upload_config: Optional[dict] = None,
        dpi: int = 200,
        timeout: int = 120,
        poll_interval: int = 5,
    ):
        """
        初始化翻译器

        Args:
            api_key: API Key
            upload_method: 图片上传方法
            upload_config: 上传器配置
            dpi: 页面渲染 DPI
            timeout: 单页翻译超时（秒）
            poll_interval: 轮询间隔（秒）
        """
        self.image_translator = QwenImageTranslator(
            api_key=api_key,
            timeout=timeout,
            poll_interval=poll_interval,
        )

        self.upload_method = upload_method
        self.upload_config = upload_config or {}
        self.dpi = dpi

    def translate_pdf(
        self,
        input_path: Path,
        output_path: Path,
        target_lang: str,
        source_lang: str = "auto",
        pages: Optional[List[int]] = None,
        domain_hint: Optional[str] = None,
        glossary_path: Optional[Path] = None,
        skip_main_subject: bool = False,
        mode: str = "pdf",
        preserve_original: bool = False,
    ) -> Union[Path, str]:
        """
        翻译 PDF 文档

        Args:
            input_path: 输入PDF路径
            output_path: 输出路径
            target_lang: 目标语言
            source_lang: 源语言
            pages: 页面范围（0-based索引）
            domain_hint: 领域提示
            glossary_path: 术语表路径
            skip_main_subject: 翻译主体文字（仅图像翻译模式）
            mode: 输出模式 pdf/images/markdown
            preserve_original: 是否保留原文（仅 markdown 模式）

        Returns:
            输出文件路径 (pdf/images 模式) 或 Markdown 内容 (markdown 模式)
        """
        # Markdown 模式使用两阶段翻译
        if mode == OutputMode.MARKDOWN:
            return self._translate_to_markdown(
                input_path=input_path,
                output_path=output_path,
                target_lang=target_lang,
                source_lang=source_lang,
                pages=pages,
                domain=domain_hint,
                glossary_path=glossary_path,
                preserve_original=preserve_original,
            )

        # 图像翻译模式
        # 验证语言对
        is_valid, error = validate_language_pair(source_lang, target_lang)
        if not is_valid:
            raise ValueError(error)

        # 加载术语表
        terminologies = self._load_glossary(glossary_path) if glossary_path else None

        # 打开 PDF
        doc = fitz.open(input_path)
        if pages is None:
            pages = list(range(doc.page_count))

        translated_images: List[Tuple[int, bytes]] = []

        # 创建上传器
        uploader = create_uploader(self.upload_method, **self.upload_config)

        for page_num in pages:
            # 1. 渲染页面为图片
            page = doc[page_num]
            pix = page.get_pixmap(dpi=self.dpi)
            img_bytes = pix.tobytes("png")

            # 2. 上传图片获取 URL
            filename = f"page_{page_num}.png"
            image_url = uploader.upload(img_bytes, filename)

            # 3. 调用图像翻译 API
            try:
                translated_url = self.image_translator.translate_image(
                    image_url=image_url,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    domain_hint=domain_hint,
                    terminologies=terminologies,
                    skip_main_subject=skip_main_subject,
                )

                if translated_url:
                    # 4. 下载翻译后的图片
                    translated_img = self._download_image(translated_url)
                    translated_images.append((page_num, translated_img))
                else:
                    # 无文字页面，使用原图
                    translated_images.append((page_num, img_bytes))

            except Exception as e:
                # 失败时使用原图
                translated_images.append((page_num, img_bytes))
                # 可以选择抛出异常或继续
                raise RuntimeError(f"页面 {page_num + 1} 翻译失败: {e}")

        doc.close()

        # 5. 根据模式输出
        if mode == OutputMode.PDF:
            return self._save_as_pdf(translated_images, output_path)
        elif mode == OutputMode.IMAGES:
            return self._save_as_images(translated_images, output_path)
        else:
            raise ValueError(f"不支持的输出模式: {mode}")

    def _translate_to_markdown(
        self,
        input_path: Path,
        output_path: Path,
        target_lang: str,
        source_lang: str = "auto",
        pages: Optional[List[int]] = None,
        domain: Optional[str] = None,
        glossary_path: Optional[Path] = None,
        preserve_original: bool = False,
    ) -> str:
        """翻译为 Markdown 格式

        Args:
            input_path: 输入PDF路径
            output_path: 输出文件路径
            target_lang: 目标语言
            source_lang: 源语言
            pages: 页面范围（0-based索引）
            domain: 领域提示
            glossary_path: 术语表路径
            preserve_original: 是否保留原文

        Returns:
            Markdown 内容
        """
        # 创建 Markdown 翻译器
        translator = AIMarkdownTranslator(
            vl_model="plus",
            mt_model="qwen-mt-plus",
        )

        # 执行翻译
        markdown_content = translator.translate(
            file_path=input_path,
            target_lang=target_lang,
            source_lang=source_lang,
            pages=pages,
            domain=domain,
            glossary_path=glossary_path,
            preserve_original=preserve_original,
        )

        # 保存到文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")

        return markdown_content

    def _download_image(self, url: str) -> bytes:
        """下载图片"""
        requests = _import_requests()
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content

    def _save_as_pdf(self, images: List[Tuple[int, bytes]], output_path: Path) -> Path:
        """将图片合成为 PDF"""
        doc = fitz.open()

        for page_num, img_bytes in images:
            # 从字节创建图片页面
            img_doc = fitz.open(stream=img_bytes, filetype="png")
            rect = img_doc[0].rect
            pdf_page = doc.new_page(width=rect.width, height=rect.height)
            pdf_page.insert_image(rect, stream=img_bytes)
            img_doc.close()

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc.save(output_path)
        doc.close()
        return output_path

    def _save_as_images(self, images: List[Tuple[int, bytes]], output_dir: Path) -> Path:
        """保存为图片目录"""
        output_dir.mkdir(parents=True, exist_ok=True)

        for page_num, img_bytes in images:
            img_path = output_dir / f"page_{page_num + 1:04d}.png"
            img_path.write_bytes(img_bytes)

        return output_dir

    def _load_glossary(self, path: Path) -> List[dict]:
        """加载术语表"""
        terminologies = []

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = row.get("src", "")
                tgt = row.get("tgt", "")
                if src and tgt:
                    terminologies.append({
                        "src": src,
                        "tgt": tgt,
                    })

        # API 限制：最多 50 个术语
        return terminologies[:50]


def parse_page_range(range_str: str, total_pages: int) -> List[int]:
    """
    解析页面范围字符串

    Args:
        range_str: 页面范围字符串，如 "1-5,8,10-15"
        total_pages: PDF 总页数

    Returns:
        页面索引列表（0-based）
    """
    pages = []

    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            start = int(start.strip()) - 1  # 转为 0-based
            end = int(end.strip()) - 1
            pages.extend(range(start, min(end + 1, total_pages)))
        else:
            page = int(part) - 1  # 转为 0-based
            if 0 <= page < total_pages:
                pages.append(page)

    return sorted(set(pages))
