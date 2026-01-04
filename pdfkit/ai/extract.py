"""AI 抽取器 - 基于视觉大模型的智能信息抽取核心逻辑"""

import json
import re
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
from PIL import Image

from ..core.ocr_handler import QwenVLOCR, OCRModel, pdf_page_to_image
from .prompt_builder import build_extract_prompt, validate_template


class OutputFormat(str):
    """输出格式"""
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"


class AIExtractor:
    """AI 信息抽取器

    使用视觉大模型从 PDF/图片中抽取结构化信息
    """

    def __init__(
        self,
        model: str = "plus",
        api_key: Optional[str] = None,
    ):
        """
        初始化抽取器

        Args:
            model: 模型选择 (flash/plus)
            api_key: API Key
        """
        # 映射模型名称
        model_enum = OCRModel.FLASH if model == "flash" else OCRModel.PLUS

        self.ocr = QwenVLOCR(api_key=api_key, model=model_enum)
        self.model = model

    def extract(
        self,
        file_path: Path,
        fields: Optional[List[str]] = None,
        template: Optional[Path] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        从文件中抽取信息

        Args:
            file_path: 文件路径 (PDF 或图片)
            fields: 字段列表（简单模式）
            template: 模板文件路径（复杂模式）
            page: 目标页码（PDF 专用，从 1 开始）

        Returns:
            抽取结果（字典格式）
        """
        # 1. 加载模板
        template_config = self._load_template(fields, template)

        # 2. 验证模板
        is_valid, error_msg = validate_template(template_config)
        if not is_valid:
            raise ValueError(f"模板格式错误: {error_msg}")

        # 3. 获取图像
        image = self._get_image(file_path, page)

        # 4. 构建提示词
        prompt = build_extract_prompt(template_config)

        # 5. 调用模型
        response = self.ocr.ocr_image(image, prompt=prompt)

        # 6. 解析 JSON 结果
        return self._parse_json(response)

    def extract_batch(
        self,
        file_paths: List[Path],
        fields: Optional[List[str]] = None,
        template: Optional[Path] = None,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        批量抽取多个文件

        Args:
            file_paths: 文件路径列表
            fields: 字段列表（简单模式）
            template: 模板文件路径（复杂模式）
            page: 目标页码（PDF 专用）

        Returns:
            抽取结果列表，每个元素包含 {"_file": 文件名, ...抽取字段}
        """
        results = []

        for file_path in file_paths:
            try:
                data = self.extract(file_path, fields, template, page)
                data["_file"] = file_path.name
                results.append(data)
            except Exception as e:
                # 出错时记录文件名和错误
                results.append({
                    "_file": file_path.name,
                    "_error": str(e)
                })

        return results

    def _load_template(
        self,
        fields: Optional[List[str]],
        template_path: Optional[Path]
    ) -> Dict[str, Any]:
        """
        加载模板配置

        Args:
            fields: 字段列表
            template_path: 模板文件路径

        Returns:
            模板配置字典
        """
        if template_path:
            # 从文件加载
            template_path = Path(template_path)
            if not template_path.exists():
                raise FileNotFoundError(f"模板文件不存在: {template_path}")

            content = template_path.read_text(encoding="utf-8")

            # 判断格式
            if template_path.suffix in ['.yaml', '.yml']:
                import yaml
                try:
                    return yaml.safe_load(content)
                except ImportError:
                    raise ImportError(
                        "YAML 支持需要安装 pyyaml: pip install pyyaml"
                    )
            else:
                # 默认 JSON
                return json.loads(content)

        elif fields:
            # 从字段列表构建简单模板
            return {"fields": fields}

        else:
            raise ValueError("需要指定 fields 或 template 参数")

    def _get_image(self, file_path: Path, page: int) -> Image.Image:
        """
        从文件获取图像

        Args:
            file_path: 文件路径
            page: 页码（从 1 开始）

        Returns:
            PIL Image 对象
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 根据文件类型处理
        suffix = file_path.suffix.lower()

        if suffix in ['.pdf']:
            # PDF 文件
            doc = fitz.open(file_path)
            total_pages = doc.page_count

            if page < 1 or page > total_pages:
                doc.close()
                raise ValueError(
                    f"页码超出范围: {page}，文件共 {total_pages} 页"
                )

            # 页码从 0 开始
            pdf_page = doc[page - 1]
            image = pdf_page_to_image(pdf_page, dpi=200)
            doc.close()

            return image

        elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            # 图片文件
            return Image.open(file_path)

        else:
            raise ValueError(
                f"不支持的文件类型: {suffix}，"
                "仅支持 PDF 和常见图片格式"
            )

    def _parse_json(self, response: str) -> Dict[str, Any]:
        """
        从模型响应中解析 JSON

        Args:
            response: 模型返回的文本

        Returns:
            解析后的字典
        """
        if not response:
            raise ValueError("模型返回空响应")

        # 尝试直接解析
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON（处理可能的 markdown 代码块）
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试查找 JSON 对象
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # 都失败了，返回原始响应
        raise ValueError(
            f"无法解析模型返回的 JSON: {response[:200]}..."
        )


def format_output(
    data: Union[Dict, List[Dict]],
    output_format: str = "json",
) -> str:
    """
    格式化输出结果

    Args:
        data: 抽取数据
        output_format: 输出格式 (json/yaml/csv)

    Returns:
        格式化后的字符串
    """
    if output_format == "json":
        return json.dumps(data, ensure_ascii=False, indent=2)

    elif output_format == "yaml":
        import yaml
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)

    elif output_format == "csv":
        if isinstance(data, dict):
            data = [data]

        if not data:
            return ""

        # 获取所有字段名
        fieldnames = set()
        for item in data:
            if isinstance(item, dict):
                fieldnames.update(item.keys())

        fieldnames = sorted(fieldnames)

        # 生成 CSV
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()

    else:
        raise ValueError(f"不支持的输出格式: {output_format}")
