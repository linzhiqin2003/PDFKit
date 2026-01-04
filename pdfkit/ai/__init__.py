"""AI 模块 - 基于视觉大模型的智能信息抽取与翻译"""

from .extract import AIExtractor
from .prompt_builder import build_extract_prompt, FieldTemplate
from .translator import AITranslator, parse_page_range
from .image_translator import QwenImageTranslator, validate_language_pair, LanguageCode
from .uploader import create_uploader, ImageUploader, UploadMethod
from .formula_extractor import AIFormulaExtractor
from .formula_prompt import build_formula_prompt, parse_formulas_from_response
from .image_extractor import AIImageExtractor
from .image_detection_prompt import (
    build_image_detection_prompt,
    parse_detection_result,
    filter_images_by_type,
    normalize_bbox_to_pixels,
    IMAGE_TYPES,
)
from .qwen_mt_translator import QwenMTTranslator
from .markdown_translator import AIMarkdownTranslator

__all__ = [
    # Extract
    "AIExtractor",
    "build_extract_prompt",
    "FieldTemplate",
    # Translate
    "AITranslator",
    "parse_page_range",
    "QwenImageTranslator",
    "validate_language_pair",
    "LanguageCode",
    # Uploader
    "create_uploader",
    "ImageUploader",
    "UploadMethod",
    # Formula
    "AIFormulaExtractor",
    "build_formula_prompt",
    "parse_formulas_from_response",
    # Image Extractor
    "AIImageExtractor",
    "build_image_detection_prompt",
    "parse_detection_result",
    "filter_images_by_type",
    "normalize_bbox_to_pixels",
    "IMAGE_TYPES",
    # Markdown Translate
    "QwenMTTranslator",
    "AIMarkdownTranslator",
]
