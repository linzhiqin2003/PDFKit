"""阿里百炼专用翻译模型客户端

使用 qwen-mt-plus 模型进行文本翻译，支持领域提示和术语表。
"""

import os
from typing import Optional, List, Dict
from openai import OpenAI

from ..utils.config import load_config


class QwenMTTranslator:
    """阿里百炼专用翻译模型客户端"""

    # 语言代码到英文名称的映射
    LANG_NAMES = {
        "zh": "Chinese",
        "en": "English",
        "ja": "Japanese",
        "ko": "Korean",
        "de": "German",
        "fr": "French",
        "es": "Spanish",
        "ru": "Russian",
        "pt": "Portuguese",
        "it": "Italian",
        "ar": "Arabic",
        "vi": "Vietnamese",
        "th": "Thai",
        "id": "Indonesian",
        "ms": "Malay",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        region: str = "beijing",
        model: str = "qwen-mt-plus",
    ):
        """
        初始化翻译器

        Args:
            api_key: API密钥，默认从环境变量 DASHSCOPE_API_KEY 读取
            region: 区域，beijing 或 singapore
            model: 模型名称，默认 qwen-mt-plus
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API Key 未找到。请设置环境变量 DASHSCOPE_API_KEY "
                "或传入 api_key 参数。"
            )

        self.model = model

        # 地域配置
        self.region_config = {
            "beijing": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "singapore": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        }
        self.base_url = self.region_config.get(region, self.region_config["beijing"])

        # 创建客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def _get_lang_name(self, lang_code: str) -> str:
        """获取语言的英文名称

        Args:
            lang_code: 语言代码

        Returns:
            语言的英文名称
        """
        return self.LANG_NAMES.get(lang_code, lang_code)

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "auto",
        domain: Optional[str] = None,
        terminologies: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        使用 qwen-mt-plus 翻译文本

        Args:
            text: 待翻译的文本
            target_lang: 目标语言代码
            source_lang: 源语言代码，默认 auto 自动检测
            domain: 领域提示（英文描述）
            terminologies: 术语表，格式为 [{"src": "原文", "tgt": "译文"}, ...]

        Returns:
            翻译后的文本

        Raises:
            ValueError: 参数错误
            RuntimeError: 翻译失败
        """
        if not text or not text.strip():
            return text

        if not target_lang:
            raise ValueError("target_lang 参数不能为空")

        # 构建 translation_options
        translation_options = {
            "target_lang": self._get_lang_name(target_lang),
        }

        # 源语言（如果不是 auto）
        if source_lang and source_lang != "auto":
            translation_options["source_lang"] = self._get_lang_name(source_lang)

        # 领域提示
        if domain:
            translation_options["domains"] = domain

        # 构建请求体
        extra_body = {
            "translation_options": translation_options,
        }

        # 术语表（通过 system message 传递）
        messages = [{"role": "user", "content": text}]

        if terminologies:
            # 构建术语表提示
            terms = [f"{t['src']} → {t['tgt']}" for t in terminologies if t.get("src") and t.get("tgt")]
            if terms:
                glossary_prompt = "请使用以下术语翻译：\n" + "\n".join(terms[:30])  # 限制30条
                messages.insert(0, {"role": "system", "content": glossary_prompt})

        try:
            # 调用翻译模型
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                extra_body=extra_body,
            )

            return completion.choices[0].message.content

        except Exception as e:
            raise RuntimeError(f"翻译失败: {e}")

    def validate_language_pair(self, source_lang: str, target_lang: str) -> tuple[bool, str]:
        """
        验证语言对是否支持

        Args:
            source_lang: 源语言代码
            target_lang: 目标语言代码

        Returns:
            (是否有效, 错误消息)
        """
        # 检查目标语言
        if target_lang not in self.LANG_NAMES:
            return False, f"不支持的目标语言: {target_lang}"

        # 检查源语言
        if source_lang != "auto" and source_lang not in self.LANG_NAMES:
            return False, f"不支持的源语言: {source_lang}"

        return True, ""
