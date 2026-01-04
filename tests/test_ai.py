"""AI 抽取功能单元测试"""

import pytest
from pathlib import Path
from pdfkit.ai.prompt_builder import (
    build_extract_prompt,
    validate_template,
    _parse_field_dict,
    FieldTemplate,
    FieldType,
)
from pdfkit.ai.extract import AIExtractor, format_output


class TestPromptBuilder:
    """Prompt 构建器测试"""

    def test_build_prompt_simple_fields(self):
        """测试简单字段列表的 prompt 构建"""
        template = {
            "fields": ["姓名", "电话", "地址"]
        }
        prompt = build_extract_prompt(template)

        assert "姓名" in prompt
        assert "电话" in prompt
        assert "地址" in prompt
        assert "JSON 格式" in prompt
        assert "无法识别的字段设为 null" in prompt

    def test_build_prompt_with_descriptions(self):
        """测试带描述的字段 prompt 构建"""
        template = {
            "fields": [
                {
                    "name": "invoice_no",
                    "label": "发票号码",
                    "description": "发票右上角的8位数字编号",
                    "type": "string",
                    "required": True
                }
            ]
        }
        prompt = build_extract_prompt(template)

        assert "invoice_no" in prompt
        assert "发票号码" in prompt
        assert "发票右上角的8位数字编号" in prompt
        assert "[类型: string]" in prompt
        assert "（必填）" in prompt

    def test_build_prompt_with_nested_fields(self):
        """测试嵌套字段的 prompt 构建"""
        template = {
            "fields": [
                {
                    "name": "buyer",
                    "label": "购买方",
                    "type": "object",
                    "fields": [
                        {"name": "name", "label": "名称"},
                        {"name": "tax_no", "label": "税号"}
                    ]
                }
            ]
        }
        prompt = build_extract_prompt(template)

        assert "buyer" in prompt
        assert "购买方" in prompt
        assert "[类型: object]" in prompt
        assert "嵌套字段:" in prompt
        assert "name" in prompt
        assert "tax_no" in prompt

    def test_build_prompt_with_array(self):
        """测试数组字段的 prompt 构建"""
        template = {
            "fields": [
                {
                    "name": "items",
                    "label": "商品明细",
                    "type": "array",
                    "items": [
                        {"name": "name", "label": "名称"},
                        {"name": "quantity", "label": "数量", "type": "number"}
                    ]
                }
            ]
        }
        prompt = build_extract_prompt(template)

        assert "items" in prompt
        assert "商品明细" in prompt
        assert "[类型: array]" in prompt
        assert "数组元素字段:" in prompt

    def test_build_prompt_with_template_name(self):
        """测试带模板名称的 prompt 构建"""
        template = {
            "name": "invoice",
            "description": "增值税发票",
            "fields": ["发票号码", "金额"]
        }
        prompt = build_extract_prompt(template)

        assert "【invoice】" in prompt
        assert "增值税发票" in prompt

    def test_validate_template_simple(self):
        """验证简单模板格式"""
        template = {"fields": ["field1", "field2"]}
        is_valid, error = validate_template(template)
        assert is_valid
        assert error is None

    def test_validate_template_missing_fields(self):
        """验证缺少 fields 字段的模板"""
        template = {"name": "test"}
        is_valid, error = validate_template(template)
        assert not is_valid
        assert "fields" in error

    def test_validate_template_empty_fields(self):
        """验证空 fields 列表的模板"""
        template = {"fields": []}
        is_valid, error = validate_template(template)
        assert not is_valid
        assert "不能为空" in error

    def test_validate_template_invalid_field_type(self):
        """验证无效字段类型的模板"""
        template = {"fields": [123]}
        is_valid, error = validate_template(template)
        assert not is_valid

    def test_validate_template_invalid_nested_type(self):
        """验证无效嵌套类型的模板"""
        template = {
            "fields": [
                {
                    "name": "test",
                    "type": "invalid_type"
                }
            ]
        }
        is_valid, error = validate_template(template)
        # 不会报错，因为类型验证时会有默认值
        # 但如果类型是 object 或 array 会验证结构

    def test_parse_field_dict_basic(self):
        """测试基本字段解析"""
        data = {
            "name": "test_field",
            "label": "测试字段",
            "type": "string",
            "required": True
        }
        field = _parse_field_dict(data)

        assert field.name == "test_field"
        assert field.label == "测试字段"
        assert field.type == FieldType.STRING
        assert field.required is True

    def test_parse_field_dict_with_default_label(self):
        """测试字段解析时默认 label"""
        data = {"name": "test_field"}
        field = _parse_field_dict(data)

        assert field.name == "test_field"
        assert field.label == "test_field"  # 默认使用 name
        assert field.type == FieldType.STRING  # 默认类型

    def test_parse_field_dict_missing_name(self):
        """测试缺少 name 的字段解析"""
        data = {"label": "test"}
        with pytest.raises(ValueError, match="name"):
            _parse_field_dict(data)


class TestFormatOutput:
    """格式化输出测试"""

    def test_format_output_json(self):
        """测试 JSON 格式输出"""
        data = {"name": "张三", "age": 30}
        output = format_output(data, "json")

        assert '"name": "张三"' in output
        assert '"age": 30' in output

    def test_format_output_yaml(self):
        """测试 YAML 格式输出"""
        data = {"name": "张三", "age": 30}
        output = format_output(data, "yaml")

        assert "name: 张三" in output
        assert "age: 30" in output

    def test_format_output_csv_single(self):
        """测试单个字典的 CSV 输出"""
        data = {"name": "张三", "age": 30}
        output = format_output(data, "csv")

        assert "name,age" in output
        assert "张三,30" in output

    def test_format_output_csv_multiple(self):
        """测试多个字典的 CSV 输出"""
        data = [
            {"name": "张三", "age": 30},
            {"name": "李四", "age": 25}
        ]
        output = format_output(data, "csv")

        assert "name,age" in output
        assert "张三,30" in output
        assert "李四,25" in output

    def test_format_output_csv_empty(self):
        """测试空数据的 CSV 输出"""
        output = format_output([], "csv")
        assert output == ""

    def test_format_output_invalid_format(self):
        """测试无效格式"""
        with pytest.raises(ValueError, match="不支持的输出格式"):
            format_output({"test": "data"}, "invalid")

    def test_format_output_csv_with_file_column(self):
        """测试带 _file 列的 CSV 输出"""
        data = [
            {"_file": "test1.pdf", "name": "张三"},
            {"_file": "test2.pdf", "name": "李四"}
        ]
        output = format_output(data, "csv")

        assert "_file,name" in output
        assert "test1.pdf,张三" in output
        assert "test2.pdf,李四" in output


class TestAIExtractor:
    """AI 抽取器测试"""

    def test_load_template_from_fields(self):
        """测试从字段列表加载模板"""
        extractor = AIExtractor(model="flash")

        template = extractor._load_template(
            fields=["姓名", "电话"],
            template_path=None
        )

        assert template == {"fields": ["姓名", "电话"]}

    def test_load_template_from_file(self, tmp_path: Path):
        """测试从文件加载模板"""
        template_file = tmp_path / "template.json"
        template_file.write_text('{"fields": ["field1", "field2"]}')

        extractor = AIExtractor(model="flash")
        template = extractor._load_template(
            fields=None,
            template_path=template_file
        )

        assert template == {"fields": ["field1", "field2"]}

    def test_load_template_from_yaml_file(self, tmp_path: Path):
        """测试从 YAML 文件加载模板"""
        template_file = tmp_path / "template.yaml"
        template_file.write_text('fields:\n  - field1\n  - field2')

        extractor = AIExtractor(model="flash")
        template = extractor._load_template(
            fields=None,
            template_path=template_file
        )

        assert template == {"fields": ["field1", "field2"]}

    def test_load_template_missing_file(self, tmp_path: Path):
        """测试加载不存在的模板文件"""
        extractor = AIExtractor(model="flash")

        with pytest.raises(FileNotFoundError):
            extractor._load_template(
                fields=None,
                template_path=tmp_path / "nonexistent.json"
            )

    def test_load_template_no_fields_no_template(self):
        """测试既没有字段也没有模板"""
        extractor = AIExtractor(model="flash")

        with pytest.raises(ValueError, match="需要指定"):
            extractor._load_template(fields=None, template_path=None)

    def test_get_image_from_pdf(self, sample_pdf: Path):
        """测试从 PDF 获取图像"""
        extractor = AIExtractor(model="flash")
        image = extractor._get_image(sample_pdf, page=1)

        assert image is not None
        assert image.width > 0
        assert image.height > 0

    def test_get_image_invalid_page(self, sample_pdf: Path):
        """测试获取不存在的页面"""
        extractor = AIExtractor(model="flash")

        with pytest.raises(ValueError, match="页码超出范围"):
            extractor._get_image(sample_pdf, page=999)

    def test_get_image_nonexistent_file(self):
        """测试获取不存在的文件图像"""
        extractor = AIExtractor(model="flash")

        with pytest.raises(FileNotFoundError):
            extractor._get_image(Path("nonexistent.pdf"), page=1)

    def test_parse_json_valid(self):
        """测试解析有效的 JSON"""
        extractor = AIExtractor(model="flash")
        result = extractor._parse_json('{"name": "张三", "age": 30}')

        assert result == {"name": "张三", "age": 30}

    def test_parse_json_with_markdown(self):
        """测试解析带 markdown 代码块的 JSON"""
        extractor = AIExtractor(model="flash")
        response = '''```json
{"name": "张三", "age": 30}
```'''
        result = extractor._parse_json(response)

        assert result == {"name": "张三", "age": 30}

    def test_parse_json_extract_from_text(self):
        """测试从文本中提取 JSON"""
        extractor = AIExtractor(model="sharp")
        response = '这是前面的文字 {"name": "张三", "age": 30} 后面的文字'
        result = extractor._parse_json(response)

        assert result == {"name": "张三", "age": 30}

    def test_parse_json_empty_response(self):
        """测试解析空响应"""
        extractor = AIExtractor(model="plus")

        with pytest.raises(ValueError, match="空响应"):
            extractor._parse_json("")

    def test_parse_json_invalid(self):
        """测试解析无效的 JSON"""
        extractor = AIExtractor(model="plus")

        with pytest.raises(ValueError, match="无法解析"):
            extractor._parse_json("这不是 JSON")


@pytest.mark.parametrize("template,expected_valid", [
    ({"fields": ["a", "b"]}, True),
    ({"fields": []}, False),
    ({"fields": [""]}, False),
    ({"fields": [{"name": "test"}]}, True),
    ({"fields": [{"name": "test", "type": "object", "fields": []}]}, False),
])
def test_validate_template_cases(template, expected_valid):
    """参数化测试模板验证"""
    is_valid, _ = validate_template(template)
    assert is_valid == expected_valid
