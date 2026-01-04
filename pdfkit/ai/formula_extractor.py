"""AI 公式提取器 - 基于视觉大模型的数学公式识别

使用阿里百炼 Qwen3-VL 视觉语言模型识别 PDF/图片中的数学公式。
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image

from ..core.ocr_handler import QwenVLOCR, OCRModel, pdf_page_to_image
from .formula_prompt import build_formula_prompt, parse_formulas_from_response


class OutputFormat(str):
    """输出格式"""
    LATEX = "latex"
    MATHML = "mathml"
    JSON = "json"


class AIFormulaExtractor:
    """AI 公式识别器

    从 PDF/图片中识别数学公式、物理公式、化学方程式等，
    输出为 LaTeX/MathML/JSON 格式。
    """

    def __init__(
        self,
        model: str = "plus",
        api_key: Optional[str] = None,
    ):
        """
        初始化公式提取器

        Args:
            model: 模型选择 (flash/plus)
            api_key: API Key
        """
        model_enum = OCRModel.FLASH if model == "flash" else OCRModel.PLUS
        self.ocr = QwenVLOCR(api_key=api_key, model=model_enum)
        self.model = model

    def extract(
        self,
        file_path: Path,
        pages: Optional[List[int]] = None,
        explain: bool = False,
        inline: bool = False,
        output_format: str = "latex",
        dpi: int = 300,
    ) -> str:
        """
        提取文档中的公式

        Args:
            file_path: PDF/图片文件路径
            pages: 页面范围（0-based索引）
            explain: 是否添加公式解释
            inline: 是否使用行内公式格式
            output_format: 输出格式 (latex/mathml/json)
            dpi: 渲染 DPI

        Returns:
            格式化的公式文本
        """
        # 构建提示词
        prompt = build_formula_prompt(
            explain=explain,
            inline=inline,
            output_format=output_format,
        )

        # 处理文件
        if file_path.suffix.lower() == ".pdf":
            results = self._extract_from_pdf(
                file_path, pages, prompt, dpi
            )
        else:
            results = self._extract_from_image(
                file_path, prompt
            )

        # 格式化输出
        return self._format_output(
            file_path, results, output_format, explain
        )

    def _extract_from_pdf(
        self,
        file_path: Path,
        pages: Optional[List[int]],
        prompt: str,
        dpi: int,
    ) -> List[Tuple[int, str]]:
        """从 PDF 中提取公式"""
        doc = fitz.open(file_path)

        if pages is None:
            pages = list(range(doc.page_count))

        results = []

        for page_num in pages:
            page = doc[page_num]
            image = pdf_page_to_image(page, dpi=dpi)

            try:
                response = self.ocr.ocr_image(image, prompt=prompt)
                if response.strip():
                    results.append((page_num + 1, response))
            except Exception as e:
                # 出错时跳过该页
                continue

        doc.close()
        return results

    def _extract_from_image(
        self,
        file_path: Path,
        prompt: str,
    ) -> List[Tuple[int, str]]:
        """从图片中提取公式"""
        image = Image.open(file_path)

        try:
            response = self.ocr.ocr_image(image, prompt=prompt)
            if response.strip():
                return [(1, response)]
        except Exception:
            pass

        return []

    def _format_output(
        self,
        file_path: Path,
        results: List[Tuple[int, str]],
        output_format: str,
        explain: bool,
    ) -> str:
        """格式化输出"""
        if output_format == OutputFormat.JSON:
            return self._format_json(file_path, results)
        elif output_format == OutputFormat.MATHML:
            return self._format_mathml(file_path, results)
        else:
            return self._format_latex(file_path, results, explain)

    def _format_latex(
        self,
        file_path: Path,
        results: List[Tuple[int, str]],
        explain: bool,
    ) -> str:
        """LaTeX 格式输出"""
        lines = [
            f"% 公式提取自: {file_path.name}",
            f"% 提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"% 共提取 {sum(len(parse_formulas_from_response(r, 'latex')) for _, r in results)} 个公式",
            "",
        ]

        for page_num, response in results:
            lines.append(f"%% ========== 第 {page_num} 页 ==========")
            lines.append("")
            lines.append(response)
            lines.append("")

        return "\n".join(lines)

    def _format_json(
        self,
        file_path: Path,
        results: List[Tuple[int, str]],
    ) -> str:
        """JSON 格式输出"""
        all_formulas = []

        for page_num, response in results:
            formulas = parse_formulas_from_response(response, "json")
            for f in formulas:
                f["page"] = page_num
                all_formulas.append(f)

        output = {
            "source": str(file_path),
            "extracted_at": datetime.now().isoformat(),
            "total_count": len(all_formulas),
            "formulas": all_formulas,
        }

        return json.dumps(output, ensure_ascii=False, indent=2)

    def _format_mathml(
        self,
        file_path: Path,
        results: List[Tuple[int, str]],
    ) -> str:
        """MathML 格式输出"""
        lines = [
            f"<!-- 公式提取自: {file_path.name} -->",
            f"<!-- 提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->",
            "",
        ]

        for page_num, response in results:
            lines.append(f"<!-- ========== 第 {page_num} 页 ========== -->")
            lines.append("")
            lines.append(response)
            lines.append("")

        return "\n".join(lines)
