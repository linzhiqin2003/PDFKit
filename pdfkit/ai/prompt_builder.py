"""Prompt 构建器 - 根据模板生成抽取提示词"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class FieldType(str, Enum):
    """字段类型"""
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class FieldTemplate:
    """字段模板"""
    name: str                           # 字段名（输出JSON的key）
    label: Optional[str] = None         # 显示名称（用于提示词）
    type: FieldType = FieldType.STRING  # 类型
    description: Optional[str] = None   # 字段描述
    required: bool = False              # 是否必填
    fields: List['FieldTemplate'] = field(default_factory=list)  # 嵌套字段
    items: List['FieldTemplate'] = field(default_factory=list)   # 数组元素定义

    def __post_init__(self):
        """后处理：默认 label 使用 name"""
        if self.label is None:
            self.label = self.name


def _format_field_desc(field: FieldTemplate, indent: int = 0) -> List[str]:
    """
    递归生成字段描述

    Args:
        field: 字段模板
        indent: 缩进层级

    Returns:
        字段描述列表
    """
    prefix = "  " * indent
    lines = []

    # 基本信息
    required_mark = "（必填）" if field.required else ""
    type_info = f"[类型: {field.type.value}]"

    if field.description:
        desc_line = f"- **{field.name}** ({field.label}): {field.description} {type_info}{required_mark}"
    else:
        desc_line = f"- **{field.name}** ({field.label}) {type_info}{required_mark}"

    lines.append(prefix + desc_line)

    # 处理嵌套字段 (object 类型)
    if field.type == FieldType.OBJECT and field.fields:
        lines.append(prefix + f"  嵌套字段:")
        for sub_field in field.fields:
            lines.extend(_format_field_desc(sub_field, indent + 2))

    # 处理数组元素 (array 类型)
    if field.type == FieldType.ARRAY and field.items:
        lines.append(prefix + f"  数组元素字段:")
        for item_field in field.items:
            lines.extend(_format_field_desc(item_field, indent + 2))

    return lines


def build_extract_prompt(template: Dict[str, Any]) -> str:
    """
    根据模板生成抽取提示词

    Args:
        template: 模板配置，可以是简单格式 {"fields": ["field1", "field2"]}
                  或完整格式（带字段描述）

    Returns:
        抽取提示词
    """
    fields_data = template.get("fields", [])

    if not fields_data:
        raise ValueError("模板必须包含 fields 字段")

    # 生成字段描述
    fields_desc = []

    for field_item in fields_data:
        # 简单格式：字符串列表
        if isinstance(field_item, str):
            fields_desc.append(f"- {field_item}")
        # 完整格式：字典
        elif isinstance(field_item, dict):
            field = _parse_field_dict(field_item)
            fields_desc.extend(_format_field_desc(field))
        else:
            raise ValueError(f"无效的字段格式: {field_item}")

    # 添加模板名称和描述（如果有）
    template_name = template.get("name", "")
    template_desc = template.get("description", "")

    header = ""
    if template_name:
        header = f"【{template_name}】"
        if template_desc:
            header += f" {template_desc}"
        header += "\n"

    # 构建完整提示词
    prompt = f"""{header}请从图片中识别并抽取以下信息：

{chr(10).join(fields_desc)}

输出要求：
1. 以 JSON 格式输出
2. 字段名使用英文（如模板定义）
3. 无法识别的字段设为 null
4. 数值类型直接输出数字（不要加引号）
5. 日期格式使用 YYYY-MM-DD
6. 布尔值使用 true/false
7. 数组使用 JSON 数组格式
8. 对象使用 JSON 对象格式

请直接输出 JSON，不要添加任何解释或标记。"""

    return prompt


def _parse_field_dict(data: Dict[str, Any]) -> FieldTemplate:
    """
    从字典解析字段模板

    Args:
        data: 字段数据字典

    Returns:
        FieldTemplate 对象
    """
    name = data.get("name")
    if not name:
        raise ValueError("字段必须包含 name 属性")

    label = data.get("label")
    type_str = data.get("type", "string")
    description = data.get("description")
    required = data.get("required", False)

    # 解析类型
    try:
        field_type = FieldType(type_str)
    except ValueError:
        field_type = FieldType.STRING

    # 解析嵌套字段
    fields = []
    if "fields" in data:
        for field_data in data["fields"]:
            fields.append(_parse_field_dict(field_data))

    # 解析数组元素
    items = []
    if "items" in data:
        for item_data in data["items"]:
            items.append(_parse_field_dict(item_data))

    return FieldTemplate(
        name=name,
        label=label,
        type=field_type,
        description=description,
        required=required,
        fields=fields,
        items=items,
    )


def validate_template(template: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    验证模板格式是否正确

    Args:
        template: 模板配置

    Returns:
        (是否有效, 错误信息)
    """
    if not isinstance(template, dict):
        return False, "模板必须是字典格式"

    if "fields" not in template:
        return False, "模板必须包含 fields 字段"

    fields = template["fields"]
    if not isinstance(fields, list):
        return False, "fields 必须是列表"

    if not fields:
        return False, "fields 不能为空"

    # 验证每个字段
    for i, field_item in enumerate(fields):
        if isinstance(field_item, str):
            if not field_item.strip():
                return False, f"第 {i+1} 个字段不能为空字符串"
        elif isinstance(field_item, dict):
            error = _validate_field_dict(field_item, f"fields[{i}]")
            if error:
                return False, error
        else:
            return False, f"第 {i+1} 个字段格式无效，必须是字符串或字典"

    return True, None


def _validate_field_dict(data: Dict[str, Any], path: str = "") -> Optional[str]:
    """
    递归验证字段字典

    Args:
        data: 字段数据
        path: 当前路径（用于错误提示）

    Returns:
        错误信息，None 表示无错误
    """
    if "name" not in data:
        return f"{path}: 缺少 name 属性"

    name = data["name"]
    current_path = f"{path}.{name}" if path else name

    # 验证类型
    if "type" in data:
        type_str = data["type"]
        try:
            field_type = FieldType(type_str)
        except ValueError:
            return f"{current_path}: 无效的类型 '{type_str}'"

        # 验证嵌套结构
        if field_type == FieldType.OBJECT:
            if "fields" not in data:
                return f"{current_path}: object 类型必须包含 fields 字段"
            if not isinstance(data["fields"], list):
                return f"{current_path}: fields 必须是列表"
            for i, sub_field in enumerate(data["fields"]):
                if not isinstance(sub_field, dict):
                    return f"{current_path}.fields[{i}]: 必须是字典"
                error = _validate_field_dict(sub_field, current_path)
                if error:
                    return error

        elif field_type == FieldType.ARRAY:
            if "items" not in data:
                return f"{current_path}: array 类型必须包含 items 字段"
            if not isinstance(data["items"], list):
                return f"{current_path}: items 必须是列表"
            for i, item_field in enumerate(data["items"]):
                if not isinstance(item_field, dict):
                    return f"{current_path}.items[{i}]: 必须是字典"
                error = _validate_field_dict(item_field, current_path)
                if error:
                    return error

    return None
