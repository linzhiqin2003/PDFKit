"""AI 图像提取功能单元测试"""

import pytest
from pathlib import Path

from pdfkit.ai.image_detection_prompt import (
    build_image_detection_prompt,
    parse_detection_result,
    filter_images_by_type,
    normalize_bbox_to_pixels,
    IMAGE_TYPES,
)
from pdfkit.ai.image_extractor import AIImageExtractor


class TestBuildImageDetectionPrompt:
    """图像检测提示词构建测试"""

    def test_build_default_prompt(self):
        """测试默认提示词"""
        prompt = build_image_detection_prompt()

        assert "图像" in prompt
        assert "图表" in prompt
        assert "照片" in prompt
        assert "JSON" in prompt
        assert "bbox" in prompt
        assert "0-1000" in prompt

    def test_build_prompt_with_types(self):
        """测试带类型过滤的提示词"""
        prompt = build_image_detection_prompt(include_types=["photo", "chart"])

        assert "照片" in prompt or "photo" in prompt
        assert "图表" in prompt or "chart" in prompt
        assert "只关注以下类型" in prompt

    def test_build_prompt_with_exclude(self):
        """测试带排除类型的提示词"""
        prompt = build_image_detection_prompt(exclude_types=["logo", "screenshot"])

        assert "排除" in prompt
        assert "Logo" in prompt or "logo" in prompt

    def test_build_prompt_with_both_filters(self):
        """测试同时使用包含和排除类型"""
        prompt = build_image_detection_prompt(
            include_types=["photo", "chart"],
            exclude_types=["logo"]
        )

        assert "只关注以下类型" in prompt
        assert "排除以下类型" in prompt

    def test_build_prompt_with_all(self):
        """测试 all 类型"""
        prompt = build_image_detection_prompt(include_types=["all"])

        # "all" 应该不显示具体的类型过滤
        # 因为检测所有类型
        assert len(prompt) > 0


class TestParseDetectionResult:
    """检测结果解析测试"""

    def test_parse_simple_json(self):
        """测试解析简单 JSON"""
        response = '''{
  "images": [
    {
      "type": "photo",
      "description": "一张风景照片",
      "bbox": [100, 100, 500, 400]
    }
  ]
}'''

        result = parse_detection_result(response)

        assert len(result) == 1
        assert result[0]["type"] == "photo"
        assert result[0]["description"] == "一张风景照片"
        assert result[0]["bbox"] == [100, 100, 500, 400]

    def test_parse_multiple_images(self):
        """测试解析多个图像"""
        response = '''```json
{
  "images": [
    {
      "type": "chart",
      "description": "柱状图",
      "bbox": [50, 50, 400, 300]
    },
    {
      "type": "photo",
      "description": "产品照片",
      "bbox": [450, 50, 950, 300]
    }
  ]
}
```'''

        result = parse_detection_result(response)

        assert len(result) == 2
        assert result[0]["type"] == "chart"
        assert result[1]["type"] == "photo"

    def test_parse_empty_result(self):
        """测试解析空结果"""
        response = '{"images": []}'
        result = parse_detection_result(response)

        assert len(result) == 0

    def test_parse_markdown_code_block(self):
        """测试解析 Markdown 代码块"""
        response = '''检测到以下图像：

```json
{
  "images": [
    {
      "type": "diagram",
      "description": "流程图",
      "bbox": [100, 100, 600, 400]
    }
  ]
}
```

检测完成。'''

        result = parse_detection_result(response)

        assert len(result) == 1
        assert result[0]["type"] == "diagram"

    def test_parse_invalid_json(self):
        """测试解析无效 JSON"""
        response = "这不是有效的 JSON"
        result = parse_detection_result(response)

        assert len(result) == 0

    def test_parse_malformed_json(self):
        """测试解析格式错误的 JSON"""
        response = '{"images": [}'
        result = parse_detection_result(response)

        assert len(result) == 0


class TestFilterImagesByType:
    """图像类型过滤测试"""

    def test_filter_by_include_types(self):
        """测试按包含类型过滤"""
        images = [
            {"type": "photo", "bbox": [0, 0, 100, 100]},
            {"type": "chart", "bbox": [100, 0, 200, 100]},
            {"type": "logo", "bbox": [200, 0, 300, 100]},
        ]

        filtered = filter_images_by_type(images, include_types=["photo", "chart"])

        assert len(filtered) == 2
        assert filtered[0]["type"] == "photo"
        assert filtered[1]["type"] == "chart"

    def test_filter_by_exclude_types(self):
        """测试按排除类型过滤"""
        images = [
            {"type": "photo", "bbox": [0, 0, 100, 100]},
            {"type": "chart", "bbox": [100, 0, 200, 100]},
            {"type": "logo", "bbox": [200, 0, 300, 100]},
        ]

        filtered = filter_images_by_type(images, exclude_types=["logo"])

        assert len(filtered) == 2
        assert all(img["type"] != "logo" for img in filtered)

    def test_filter_with_all(self):
        """测试 all 类型不过滤"""
        images = [
            {"type": "photo", "bbox": [0, 0, 100, 100]},
            {"type": "chart", "bbox": [100, 0, 200, 100]},
        ]

        filtered = filter_images_by_type(images, include_types=["all"])

        assert len(filtered) == 2

    def test_filter_no_filters(self):
        """测试无过滤条件"""
        images = [
            {"type": "photo", "bbox": [0, 0, 100, 100]},
            {"type": "chart", "bbox": [100, 0, 200, 100]},
        ]

        filtered = filter_images_by_type(images)

        assert len(filtered) == 2

    def test_filter_combined(self):
        """测试组合过滤（包含+排除）"""
        images = [
            {"type": "photo", "bbox": [0, 0, 100, 100]},
            {"type": "chart", "bbox": [100, 0, 200, 100]},
            {"type": "logo", "bbox": [200, 0, 300, 100]},
            {"type": "illustration", "bbox": [300, 0, 400, 100]},
        ]

        filtered = filter_images_by_type(
            images,
            include_types=["photo", "chart", "logo", "illustration"],
            exclude_types=["logo"]
        )

        assert len(filtered) == 3
        assert all(img["type"] != "logo" for img in filtered)


class TestNormalizeBboxToPixels:
    """边界框坐标转换测试"""

    def test_normalize_basic(self):
        """测试基本转换"""
        bbox = [500, 500, 1000, 1000]
        width = 2000
        height = 2000

        result = normalize_bbox_to_pixels(bbox, width, height)

        # 500/1000 * 2000 = 1000
        # 1000/1000 * 2000 = 2000
        assert result == (1000, 1000, 2000, 2000)

    def test_normalize_with_padding(self):
        """测试带边距的转换"""
        bbox = [200, 200, 800, 800]
        width = 1000
        height = 1000
        padding = 10

        result = normalize_bbox_to_pixels(bbox, width, height, padding)

        # 200/1000 * 1000 = 200, 800/1000 * 1000 = 800
        # with padding: (190, 190, 810, 810)
        assert result == (190, 190, 810, 810)

    def test_normalize_bounds_checking(self):
        """测试边界检查"""
        bbox = [0, 0, 1000, 1000]
        width = 500
        height = 500
        padding = 50

        result = normalize_bbox_to_pixels(bbox, width, height, padding)

        # 应该限制在图像边界内
        assert result[0] >= 0  # px1
        assert result[1] >= 0  # py1
        assert result[2] <= width  # px2
        assert result[3] <= height  # py2

    def test_normalize_small_bbox(self):
        """测试小边界框"""
        bbox = [100, 100, 200, 200]
        width = 1000
        height = 1000

        result = normalize_bbox_to_pixels(bbox, width, height)

        # 100/1000 * 1000 = 100, 200/1000 * 1000 = 200
        assert result == (100, 100, 200, 200)

    def test_normalize_padding_overflow(self):
        """测试边距溢出"""
        bbox = [0, 0, 100, 100]
        width = 1000
        height = 1000
        padding = 200

        result = normalize_bbox_to_pixels(bbox, width, height, padding)

        # 应该限制在 0 边界
        assert result[0] == 0  # px1 不会小于 0
        assert result[1] == 0  # py1 不会小于 0


class TestAIImageExtractor:
    """AI 图像提取器测试"""

    def test_init_default(self):
        """测试默认初始化"""
        extractor = AIImageExtractor()
        assert extractor.model == "plus"

    def test_init_with_model(self):
        """测试指定模型初始化"""
        extractor = AIImageExtractor(model="flash")
        assert extractor.model == "flash"

    def test_init_with_api_key(self):
        """测试指定 API Key 初始化"""
        extractor = AIImageExtractor(api_key="test_key")
        assert extractor.ocr.api_key == "test_key"


class TestImageTypes:
    """图像类型常量测试"""

    def test_image_types_defined(self):
        """测试图像类型已定义"""
        expected_types = ["photo", "chart", "diagram", "illustration", "table", "logo", "screenshot"]

        for t in expected_types:
            assert t in IMAGE_TYPES
            assert isinstance(IMAGE_TYPES[t], str)
            assert len(IMAGE_TYPES[t]) > 0


@pytest.mark.parametrize("include_types,exclude_types", [
    (None, None),
    (["photo", "chart"], None),
    (None, ["logo"]),
    (["photo"], ["logo"]),
    (["all"], None),
])
def test_build_image_detection_prompt_cases(include_types, exclude_types):
    """参数化测试提示词构建"""
    prompt = build_image_detection_prompt(include_types, exclude_types)

    # 检查基本内容
    assert len(prompt) > 0
    assert "图像" in prompt
    assert "JSON" in prompt

    # 根据参数检查特定内容
    if include_types and "all" not in include_types:
        assert "只关注以下类型" in prompt

    if exclude_types:
        assert "排除以下类型" in prompt


@pytest.mark.parametrize("bbox,width,height,expected", [
    ([0, 0, 1000, 1000], 1000, 1000, (0, 0, 1000, 1000)),
    ([500, 500, 1000, 1000], 2000, 2000, (1000, 1000, 2000, 2000)),
    ([100, 100, 900, 900], 1000, 1000, (100, 100, 900, 900)),
])
def test_normalize_bbox_cases(bbox, width, height, expected):
    """参数化测试坐标转换"""
    result = normalize_bbox_to_pixels(bbox, width, height)
    assert result == expected
