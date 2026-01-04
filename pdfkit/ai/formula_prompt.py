"""公式提示词构建器

为 AI 公式识别功能构建专门的提示词。
"""

from typing import Optional


def build_formula_prompt(
    explain: bool = False,
    inline: bool = False,
    output_format: str = "latex",
) -> str:
    """
    构建公式识别提示词

    Args:
        explain: 是否添加公式解释
        inline: 是否使用行内公式格式
        output_format: 输出格式 (latex/mathml/json)

    Returns:
        提示词字符串
    """
    if output_format == "latex":
        return _build_latex_prompt(explain, inline)
    elif output_format == "mathml":
        return _build_mathml_prompt(explain)
    elif output_format == "json":
        return _build_json_prompt(explain)
    else:
        return _build_latex_prompt(explain, inline)


def _build_latex_prompt(explain: bool, inline: bool) -> str:
    """构建 LaTeX 格式提示词"""
    style = "行内公式 ($...$)" if inline else "独立公式 ($$...$$)"

    prompt = f"""请识别图片中的所有数学公式、物理公式或化学方程式。

输出要求：
1. 使用标准 LaTeX 语法
2. 使用{style}格式
3. 每个公式单独一行
4. 按出现顺序编号
5. 复杂公式保持完整，不要拆分
6. 只输出公式，不要输出其他文字内容"""

    if explain:
        prompt += """
7. 在每个公式前添加注释说明（使用 % 符号）：
   - 公式类型（数学/物理/化学）
   - 公式名称（如果是常见公式）
   - 简要解释公式含义"""

    prompt += """

输出格式示例：
```
% 公式 1
$$E = mc^2$$

% 公式 2
$$F = ma$$
```

请直接输出公式列表，不要添加其他内容。"""

    return prompt


def _build_mathml_prompt(explain: bool) -> str:
    """构建 MathML 格式提示词"""
    prompt = """请识别图片中的所有数学公式、物理公式或化学方程式。

输出要求：
1. 使用 MathML 格式
2. 每个公式用 <math> 标签包裹
3. 按出现顺序编号
4. 只输出公式代码，不要输出其他内容"""

    if explain:
        prompt += """
5. 在每个公式前添加注释说明（使用 <!-- -->）：
   - 公式类型（数学/物理/化学）
   - 公式名称（如果是常见公式）
   - 简要解释公式含义"""

    prompt += """

输出格式示例：
```
<!-- 公式 1: 质能方程 -->
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mi>E</mi>
  <mo>=</mo>
  <mi>m</mi>
  <msup>
    <mi>c</mi>
    <mn>2</mn>
  </msup>
</math>

<!-- 公式 2: 牛顿第二定律 -->
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mi>F</mi>
  <mo>=</mo>
  <mi>m</mi>
  <mi>a</mi>
</math>
```

请直接输出公式列表，不要添加其他内容。"""

    return prompt


def _build_json_prompt(explain: bool) -> str:
    """构建 JSON 格式提示词"""
    prompt = """请识别图片中的所有数学公式、物理公式或化学方程式。

输出要求：
1. 输出 JSON 格式
2. 包含公式数组，每个公式有以下字段：
   - id: 公式编号（从1开始）
   - latex: LaTeX 格式的公式
   - type: 公式类型（可选：math/physics/chemistry）
   - name: 公式名称（可选，如 "质能方程"）
   - explanation: 公式解释（可选）
3. 按出现顺序排列"""

    if explain:
        prompt += """
4. 对于常见公式，请尽可能提供：
   - 公式类型
   - 公式名称
   - 简要解释"""

    prompt += """

输出格式示例：
```json
{
  "formulas": [
    {
      "id": 1,
      "latex": "E = mc^2",
      "type": "physics",
      "name": "质能方程",
      "explanation": "爱因斯坦质能等价公式"
    },
    {
      "id": 2,
      "latex": "F = ma",
      "type": "physics",
      "name": "牛顿第二定律",
      "explanation": "力等于质量乘以加速度"
    }
  ]
}
```

请直接输出 JSON，不要添加其他内容。"""

    return prompt


def parse_formulas_from_response(response: str, output_format: str = "latex") -> list:
    """
    从模型响应中解析公式列表

    Args:
        response: 模型返回的文本
        output_format: 输出格式

    Returns:
        公式列表，每项包含 (id, latex, type, name, explanation)
    """
    import re
    import json

    if output_format == "json":
        # 解析 JSON 格式
        try:
            # 提取 JSON（处理可能的 markdown 代码块）
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            else:
                # 尝试直接查找 JSON 对象
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    response = json_match.group(0)

            data = json.loads(response)
            formulas = data.get("formulas", [])

            result = []
            for f in formulas:
                result.append({
                    "id": f.get("id", 0),
                    "latex": f.get("latex", ""),
                    "type": f.get("type", ""),
                    "name": f.get("name", ""),
                    "explanation": f.get("explanation", ""),
                })
            return result
        except (json.JSONDecodeError, KeyError):
            # JSON 解析失败，回退到 LaTeX 解析
            pass

    # LaTeX/MathML 格式解析
    formulas = []
    lines = response.strip().split("\n")

    current_formula = []
    formula_id = 0
    current_comment = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 解析注释行
        if line.startswith("%"):
            # LaTeX 注释
            comment_text = line[1:].strip()
            _parse_comment(comment_text, current_comment)
            continue
        elif line.startswith("<!--"):
            # MathML 注释
            comment_text = line[4:-3].strip()
            _parse_comment(comment_text, current_comment)
            continue

        # 解析公式行
        if "$$" in line or "$" in line:
            if current_formula:
                # 保存上一个公式
                formulas.append({
                    "id": formula_id,
                    "latex": "\n".join(current_formula),
                    "type": current_comment.get("type", ""),
                    "name": current_comment.get("name", ""),
                    "explanation": current_comment.get("explanation", ""),
                })
                formula_id += 1
                current_formula = []
                current_comment = {}

            current_formula.append(line)

        elif "<math" in line:
            # MathML 公式（可能多行）
            current_formula.append(line)
        elif current_formula and ("<" in line or ">" in line):
            # MathML 内容的一部分
            current_formula.append(line)

    # 保存最后一个公式
    if current_formula:
        formulas.append({
            "id": formula_id,
            "latex": "\n".join(current_formula),
            "type": current_comment.get("type", ""),
            "name": current_comment.get("name", ""),
            "explanation": current_comment.get("explanation", ""),
        })

    return formulas


def _parse_comment(text: str, comment_dict: dict):
    """解析注释内容"""
    text = text.strip()

    # 尝试解析结构化注释
    # 格式: "公式 1: 质能方程"
    if "公式" in text and ":" in text:
        parts = text.split(":", 1)
        if len(parts) == 2:
            key_part = parts[0].strip()
            value_part = parts[1].strip()
            if "类型" in key_part:
                comment_dict["type"] = value_part
            elif "名称" in key_part or "说明" in key_part:
                if "name" not in comment_dict:
                    comment_dict["name"] = value_part
                else:
                    comment_dict["explanation"] = value_part
            return

    # 检查常见公式类型
    if any(word in text for word in ["物理", "力学", "电磁", "光学", "热学"]):
        comment_dict["type"] = "physics"
    elif any(word in text for word in ["数学", "代数", "几何", "微积分"]):
        comment_dict["type"] = "math"
    elif any(word in text for word in ["化学", "反应", "方程"]):
        comment_dict["type"] = "chemistry"

    # 检查常见公式名称
    common_formulas = {
        "质能方程": "E = mc^2",
        "牛顿第二定律": "F = ma",
        "万有引力": "F = G",
        "动能": "E_k =",
        "势能": "E_p =",
        "勾股定理": "a^2 + b^2 = c^2",
        "二次公式": "x = \\frac{-b",
    }

    for name, pattern in common_formulas.items():
        if name in text:
            comment_dict["name"] = name
            break

    # 如果没有名称但有解释，存为解释
    if "explanation" not in comment_dict and text:
        if "name" not in comment_dict:
            comment_dict["name"] = text[:50]  # 取前50字作为名称
        else:
            comment_dict["explanation"] = text
