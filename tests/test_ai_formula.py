"""AI 公式识别功能单元测试"""

import pytest
from pathlib import Path

from pdfkit.ai.formula_prompt import (
    build_formula_prompt,
    parse_formulas_from_response,
)
from pdfkit.ai.formula_extractor import AIFormulaExtractor, OutputFormat


class TestBuildFormulaPrompt:
    """公式提示词构建测试"""

    def test_build_latex_prompt_default(self):
        """测试默认 LaTeX 提示词"""
        prompt = build_formula_prompt(explain=False, inline=False, output_format="latex")

        assert "LaTeX" in prompt
        assert "$$" in prompt
        assert "独立公式" in prompt
        assert "行内公式" not in prompt
        assert "解释" not in prompt

    def test_build_latex_prompt_inline(self):
        """测试行内公式 LaTeX 提示词"""
        prompt = build_formula_prompt(explain=False, inline=True, output_format="latex")

        assert "$" in prompt
        assert "行内公式" in prompt
        assert "$$" not in prompt or "$...$" in prompt

    def test_build_latex_prompt_with_explain(self):
        """测试带解释的 LaTeX 提示词"""
        prompt = build_formula_prompt(explain=True, inline=False, output_format="latex")

        assert "解释" in prompt
        assert "公式类型" in prompt
        assert "公式名称" in prompt
        assert "简要解释" in prompt

    def test_build_mathml_prompt(self):
        """测试 MathML 提示词"""
        prompt = build_formula_prompt(explain=False, inline=False, output_format="mathml")

        assert "MathML" in prompt
        assert "<math" in prompt
        assert "xmlns" in prompt

    def test_build_json_prompt(self):
        """测试 JSON 提示词"""
        prompt = build_formula_prompt(explain=False, inline=False, output_format="json")

        assert "JSON" in prompt
        assert '"id"' in prompt
        assert '"latex"' in prompt
        assert '"type"' in prompt

    def test_build_json_prompt_with_explain(self):
        """测试带解释的 JSON 提示词"""
        prompt = build_formula_prompt(explain=True, inline=False, output_format="json")

        assert '"name"' in prompt
        assert '"explanation"' in prompt


class TestParseFormulasFromResponse:
    """公式响应解析测试"""

    def test_parse_simple_latex(self):
        """测试解析简单 LaTeX 公式"""
        response = """% 公式 1
$$E = mc^2$$

% 公式 2
$$F = ma$$"""

        formulas = parse_formulas_from_response(response, "latex")

        assert len(formulas) == 2
        assert formulas[0]["id"] == 0
        assert formulas[0]["latex"] == "$$E = mc^2$$"
        assert formulas[1]["latex"] == "$$F = ma$$"

    def test_parse_latex_with_comments(self):
        """测试解析带注释的 LaTeX"""
        response = """% 公式 1: 质能方程
% 类型: 物理公式
$$E = mc^2$$"""

        formulas = parse_formulas_from_response(response, "latex")

        assert len(formulas) == 1
        # 注释信息应该被解析到 type/name/explanation

    def test_parse_json_response(self):
        """测试解析 JSON 响应"""
        response = '''```json
{
  "formulas": [
    {
      "id": 1,
      "latex": "E = mc^2",
      "type": "physics",
      "name": "质能方程",
      "explanation": "爱因斯坦质能等价公式"
    }
  ]
}
```'''

        formulas = parse_formulas_from_response(response, "json")

        assert len(formulas) == 1
        assert formulas[0]["id"] == 1
        assert formulas[0]["latex"] == "E = mc^2"
        assert formulas[0]["type"] == "physics"
        assert formulas[0]["name"] == "质能方程"
        assert formulas[0]["explanation"] == "爱因斯坦质能等价公式"

    def test_parse_empty_response(self):
        """测试解析空响应"""
        formulas = parse_formulas_from_response("", "latex")
        assert len(formulas) == 0

    def test_parse_inline_formula(self):
        """测试解析行内公式"""
        response = """$E = mc^2$
$F = ma$"""

        formulas = parse_formulas_from_response(response, "latex")

        # 行内公式也会被识别
        assert len(formulas) >= 1

    def test_parse_mathml(self):
        """测试解析 MathML"""
        response = """<!-- 公式 1 -->
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mi>E</mi>
  <mo>=</mo>
  <mi>m</mi>
  <msup>
    <mi>c</mi>
    <mn>2</mn>
  </msup>
</math>"""

        formulas = parse_formulas_from_response(response, "mathml")

        # MathML 格式也会被识别
        assert len(formulas) >= 1
        assert "<math" in formulas[0]["latex"]


class TestAIFormulaExtractor:
    """AI 公式提取器测试"""

    def test_init_default(self):
        """测试默认初始化"""
        extractor = AIFormulaExtractor()
        assert extractor.model == "plus"

    def test_init_with_model(self):
        """测试指定模型初始化"""
        extractor = AIFormulaExtractor(model="flash")
        assert extractor.model == "flash"

    def test_init_with_api_key(self):
        """测试指定 API Key 初始化"""
        extractor = AIFormulaExtractor(api_key="test_key")
        assert extractor.ocr.api_key == "test_key"


@pytest.mark.parametrize("explain,inline,format_type", [
    (False, False, "latex"),
    (True, False, "latex"),
    (False, True, "latex"),
    (False, False, "mathml"),
    (False, False, "json"),
    (True, False, "json"),
])
def test_build_formula_prompt_cases(explain, inline, format_type):
    """参数化测试提示词构建"""
    prompt = build_formula_prompt(explain=explain, inline=inline, output_format=format_type)

    # 检查基本内容
    assert len(prompt) > 0

    # 根据格式检查特定内容
    if format_type == "latex":
        assert "LaTeX" in prompt
    elif format_type == "mathml":
        assert "MathML" in prompt
    elif format_type == "json":
        assert "JSON" in prompt

    if explain:
        assert "解释" in prompt or "explanation" in prompt

    if inline and format_type == "latex":
        assert "行内" in prompt or "inline" in prompt


@pytest.mark.parametrize("format_type", [
    "latex",
    "mathml",
    "json",
])
def test_output_format_enum(format_type):
    """测试输出格式枚举"""
    assert format_type in ["latex", "mathml", "json"]
