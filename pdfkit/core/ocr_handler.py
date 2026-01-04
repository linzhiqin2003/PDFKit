"""OCR 处理器 - 基于阿里百炼 Qwen3-VL"""

import os
import base64
import asyncio
from typing import Optional, List, Tuple
from enum import Enum
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF
from openai import OpenAI, AsyncOpenAI

# 禁用 MuPDF C 层面的错误和警告输出
# 这些警告如 "cannot create appearance stream for Screen annotations" 是无害的
fitz.TOOLS.mupdf_display_errors(False)
fitz.TOOLS.mupdf_display_warnings(False)

from ..utils.config import load_config


def _clean_json_output(content: str) -> str:
    """清理 JSON 输出，移除 markdown 代码块标记

    Args:
        content: 原始输出内容

    Returns:
        清理后的内容
    """
    if not content:
        return content

    # 移除可能的 markdown 代码块标记
    # ```json ... ``` 或 ``` ... ```
    content = content.strip()

    # 移除开头的标记
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]

    # 移除结尾的标记
    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


class OCRModel(str, Enum):
    """OCR 模型选择"""
    FLASH = "flash"   # 快速模型
    PLUS = "plus"     # 精准模型
    OCR = "ocr"       # 专用 OCR 模型 (适合结构化文本提取)


class OutputFormat(str, Enum):
    """输出格式"""
    TEXT = "text"
    MARKDOWN = "md"
    JSON = "json"


class Region(str, Enum):
    """API 地域"""
    BEIJING = "beijing"
    SINGAPORE = "singapore"


class QwenVLOCR:
    """Qwen3-VL OCR 处理器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: OCRModel = OCRModel.FLASH,
        region: Region = Region.BEIJING,
    ):
        # 加载配置
        config = load_config()
        ocr_config = config.get("ocr", {})

        # 获取 API Key
        self.api_key = api_key or ocr_config.get("api_key") or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API Key 未配置。请设置环境变量 DASHSCOPE_API_KEY 或使用 --api-key 参数\n"
                "获取 API Key: https://help.aliyun.com/zh/model-studio/get-api-key"
            )

        # 获取模型映射
        self.model_map = ocr_config.get("models", {
            "flash": "qwen3-vl-flash",
            "plus": "qwen3-vl-plus",
            "ocr": "qwen-vl-ocr-latest",
        })

        # 获取地域配置
        self.region_config = ocr_config.get("regions", {
            "beijing": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "singapore": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        })

        self.model_name = self.model_map[model]
        self.base_url = self.region_config[region]

        # 获取提示词
        self.prompts = ocr_config.get("prompts", {})

        # 获取超时和重试配置
        self.timeout = ocr_config.get("timeout", 60)
        self.max_retries = ocr_config.get("max_retries", 3)

        # 创建客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    def ocr_image(
        self,
        image: Image.Image,
        prompt: Optional[str] = None,
        output_format: OutputFormat = OutputFormat.TEXT,
    ) -> str:
        """对单张图片进行 OCR 识别"""

        # 将图片转为 base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        img_url = f"data:image/png;base64,{img_base64}"

        # 根据输出格式调整提示词
        if prompt:
            final_prompt = prompt
        else:
            format_prompts = {
                OutputFormat.TEXT: self.prompts.get("text", "请识别并提取图片中的所有文字内容，保持原有的格式和布局。只输出识别到的文字，不要添加任何解释。"),
                OutputFormat.MARKDOWN: self.prompts.get("markdown", "请识别图片中的所有文字内容，并以 Markdown 格式输出。保持标题、列表、表格等结构。"),
                OutputFormat.JSON: self.prompts.get("json", "请识别图片中的所有文字内容，以 JSON 格式输出。"),
            }
            final_prompt = format_prompts.get(output_format, format_prompts[OutputFormat.TEXT])

        # 调用 API
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": img_url},
                        },
                        {
                            "type": "text",
                            "text": final_prompt,
                        },
                    ],
                },
            ],
        )

        content = completion.choices[0].message.content

        # 对于 JSON 格式输出，清理可能的 markdown 代码块标记
        if output_format == OutputFormat.JSON:
            content = _clean_json_output(content)

        return content

    def ocr_table(self, image: Image.Image) -> str:
        """专门提取表格数据"""
        prompt = self.prompts.get("table", "请识别图片中的表格数据，并以 Markdown 表格格式输出。如果有多个表格，请依次输出。只输出 Markdown 表格，不要添加其他解释。")
        return self.ocr_image(image, prompt=prompt)

    def ocr_layout(self, image: Image.Image) -> str:
        """分析文档版面结构"""
        prompt = self.prompts.get("layout", "请分析这张文档图片的版面结构，识别出标题、正文、表格等，以 JSON 格式输出结构化的版面分析结果。")
        return self.ocr_image(image, prompt=prompt, output_format=OutputFormat.JSON)

    # ========================================================================
    # 异步 OCR 方法
    # ========================================================================

    @property
    def _async_client(self) -> AsyncOpenAI:
        """获取或创建缓存的异步客户端"""
        if not hasattr(self, '_async_client_cached') or self._async_client_cached is None:
            self._async_client_cached = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
        return self._async_client_cached

    async def close_async_client(self):
        """关闭异步客户端，释放资源"""
        if hasattr(self, '_async_client_cached') and self._async_client_cached is not None:
            await self._async_client_cached.close()
            self._async_client_cached = None

    async def ocr_image_async(
        self,
        image: Image.Image,
        prompt: Optional[str] = None,
        output_format: OutputFormat = OutputFormat.TEXT,
    ) -> str:
        """异步对单张图片进行 OCR 识别"""

        # 将图片转为 base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        img_url = f"data:image/png;base64,{img_base64}"

        # 根据输出格式调整提示词
        if prompt:
            final_prompt = prompt
        else:
            format_prompts = {
                OutputFormat.TEXT: self.prompts.get("text", "请识别并提取图片中的所有文字内容，保持原有的格式和布局。只输出识别到的文字，不要添加任何解释。"),
                OutputFormat.MARKDOWN: self.prompts.get("markdown", "请识别图片中的所有文字内容，并以 Markdown 格式输出。保持标题、列表、表格等结构。"),
                OutputFormat.JSON: self.prompts.get("json", "请识别图片中的所有文字内容，以 JSON 格式输出。"),
            }
            final_prompt = format_prompts.get(output_format, format_prompts[OutputFormat.TEXT])

        # 调用异步 API (使用缓存的客户端)
        completion = await self._async_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": img_url},
                        },
                        {
                            "type": "text",
                            "text": final_prompt,
                        },
                    ],
                },
            ],
        )

        content = completion.choices[0].message.content

        # 对于 JSON 格式输出，清理可能的 markdown 代码块标记
        if output_format == OutputFormat.JSON:
            content = _clean_json_output(content)

        return content

    async def ocr_page_async(
        self,
        doc: fitz.Document,
        page_num: int,
        dpi: int = 300,
        prompt: Optional[str] = None,
        output_format: OutputFormat = OutputFormat.TEXT,
        semaphore: Optional[asyncio.Semaphore] = None,
    ) -> Tuple[int, str]:
        """
        异步处理单个 PDF 页面，返回 (页面号, 识别结果)

        关键改进：传入doc引用而非page对象，确保页面渲染在获取信号量之后才进行，
        避免所有页面预先渲染导致内存暴涨。
        """
        # 获取信号量（控制并发数）
        if semaphore:
            await semaphore.acquire()

        try:
            # 关键：在这里才渲染页面，而不是在创建任务时
            # 这样配合信号量可以限制同时驻留内存的页面数
            page = doc[page_num]
            img = pdf_page_to_image(page, dpi)

            text = await self.ocr_image_async(img, prompt=prompt, output_format=output_format)
            return (page_num, text)
        finally:
            # 释放信号量
            if semaphore:
                semaphore.release()


def suppress_mupdf_warnings():
    """
    创建一个上下文管理器来抑制 MuPDF C 层面的警告
    MuPDF 的警告是在 C 层面输出到 stderr，普通的 Python redirect 无法拦截
    需要在文件描述符层面重定向
    """
    import contextlib
    import sys

    @contextlib.contextmanager
    def _suppress():
        # 保存原始的 stderr 文件描述符
        stderr_fd = sys.stderr.fileno()
        saved_stderr_fd = os.dup(stderr_fd)

        try:
            # 打开 /dev/null 并将 stderr 重定向到它
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, stderr_fd)
            os.close(devnull)
            yield
        finally:
            # 恢复原始的 stderr
            os.dup2(saved_stderr_fd, stderr_fd)
            os.close(saved_stderr_fd)

    return _suppress()


def pdf_page_to_image(page: fitz.Page, dpi: int = 300) -> Image.Image:
    """将 PDF 页面转换为图片"""
    mat = fitz.Matrix(dpi / 72, dpi / 72)

    # 抑制 PyMuPDF C 层面的警告输出 (如 Screen annotations 警告)
    with suppress_mupdf_warnings():
        pix = page.get_pixmap(matrix=mat)

    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
