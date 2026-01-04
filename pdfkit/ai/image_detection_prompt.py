"""图像检测提示词构建器

为 AI 图像检测功能构建专门的提示词，用于识别 PDF 页面中的图像位置。
"""

from typing import List, Optional


# 支持的图像类型
IMAGE_TYPES = {
    "photo": "照片、图片",
    "chart": "图表",
    "diagram": "示意图、流程图",
    "illustration": "插图、手绘图",
    "table": "表格（作为图像）",
    "logo": "Logo、图标",
    "screenshot": "截图",
}


def build_image_detection_prompt(
    include_types: Optional[List[str]] = None,
    exclude_types: Optional[List[str]] = None,
) -> str:
    """
    构建图像检测提示词

    Args:
        include_types: 要检测的图像类型
        exclude_types: 要排除的图像类型

    Returns:
        检测提示词
    """
    type_filters = []

    if include_types and "all" not in include_types:
        type_names = [IMAGE_TYPES.get(t, t) for t in include_types]
        type_filters.append(f"只关注以下类型：{', '.join(type_names)}")

    if exclude_types:
        exclude_names = [IMAGE_TYPES.get(t, t) for t in exclude_types]
        type_filters.append(f"排除以下类型：{', '.join(exclude_names)}")

    filter_desc = "\n".join(type_filters) if type_filters else "检测所有类型的图像"

    prompt = f"""检测图中所有的图像、图表、照片、插图，并返回每个图像的边界框坐标。

{filter_desc}

要求：
1. 识别所有视觉内容（照片、图表、示意图、插图、截图等）
2. 不要包含纯文字区域、页眉页脚、页码、水印
3. 只检测有实际视觉内容的区域
4. 以 JSON 格式返回结果

返回格式：
```json
{{
  "images": [
    {{
      "type": "photo|chart|diagram|illustration|table|logo|screenshot",
      "description": "简短描述这个图像的内容",
      "bbox": [x1, y1, x2, y2]
    }}
  ]
}}
```

bbox 坐标格式：[左上角x, 左上角y, 右下角x, 右下角y]
坐标值范围是 0-1000，表示相对于图像宽高的千分比位置。

如果没有检测到任何图像，返回空数组：{{"images": []}}

请直接输出 JSON，不要添加任何解释。"""

    return prompt


def parse_detection_result(text: str) -> List[dict]:
    """
    解析模型返回的检测结果

    Args:
        text: 模型返回的文本

    Returns:
        图像列表，每项包含 type, description, bbox
    """
    import json
    import re

    try:
        # 尝试直接解析 JSON
        result = json.loads(text)
        return result.get("images", [])
    except json.JSONDecodeError:
        pass

    # 尝试提取 JSON 部分（处理可能的 markdown 代码块）
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            return result.get("images", [])
        except json.JSONDecodeError:
            pass

    # 尝试查找 JSON 对象
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            result = json.loads(json_match.group(0))
            return result.get("images", [])
        except json.JSONDecodeError:
            pass

    return []


def filter_images_by_type(
    images: List[dict],
    include_types: Optional[List[str]] = None,
    exclude_types: Optional[List[str]] = None,
) -> List[dict]:
    """
    根据类型过滤图像

    Args:
        images: 图像列表
        include_types: 要包含的类型
        exclude_types: 要排除的类型

    Returns:
        过滤后的图像列表
    """
    filtered = images

    if include_types and "all" not in include_types:
        filtered = [img for img in filtered if img.get("type") in include_types]

    if exclude_types:
        filtered = [img for img in filtered if img.get("type") not in exclude_types]

    return filtered


def normalize_bbox_to_pixels(
    bbox: list,
    image_width: int,
    image_height: int,
    padding: int = 0,
) -> tuple:
    """
    将归一化坐标 (0-1000) 转换为像素坐标

    Args:
        bbox: 归一化边界框 [x1, y1, x2, y2]
        image_width: 图像宽度（像素）
        image_height: 图像高度（像素）
        padding: 边界扩展（像素）

    Returns:
        像素坐标 (px1, py1, px2, py2)
    """
    x1, y1, x2, y2 = bbox

    # 归一化坐标 → 像素坐标
    px1 = int(x1 / 1000 * image_width)
    py1 = int(y1 / 1000 * image_height)
    px2 = int(x2 / 1000 * image_width)
    py2 = int(y2 / 1000 * image_height)

    # 应用 padding 并限制边界
    px1 = max(0, px1 - padding)
    py1 = max(0, py1 - padding)
    px2 = min(image_width, px2 + padding)
    py2 = min(image_height, py2 + padding)

    return (px1, py1, px2, py2)
