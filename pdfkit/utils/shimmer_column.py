"""进度条流光效果 - 集成到 Rich Progress"""

from rich.text import Text
from rich.progress import ProgressColumn
from rich.style import Style


class ShimmerColumn(ProgressColumn):
    """显示带流光效果的文本"""

    def __init__(self, text: str = "AI 处理中"):
        self.text = text
        self.frame = 0
        super().__init__()

    def render(self, task):
        """渲染带流光的文本"""
        # 使用内置图标
        text = Text()
        text.append("✨ ", style="bold yellow")
        text.append(self._get_shimmer_text(task.description if task.description else self.text))
        return text

    def _get_shimmer_text(self, text: str) -> Text:
        """创建带流光效果的文本"""
        result = Text()
        chars = list(text)

        # 简化的流光：只高亮几个字符
        highlight_start = self.frame % len(chars)
        highlight_end = (highlight_start + 4) % len(chars)

        for i, char in enumerate(chars):
            # 判断是否在高亮区
            is_highlighted = False
            if highlight_start < highlight_end:
                is_highlighted = highlight_start <= i < highlight_end
            else:  # 跨越字符串边界
                is_highlighted = i >= highlight_start or i < highlight_end

            if is_highlighted:
                # 根据距离中心的距离选择颜色
                if highlight_start == i or (highlight_end - 1) % len(chars) == i:
                    result.append(char, style="color 236")  # 边缘暗
                else:
                    result.append(char, style="bold color 228")  # 中心亮
            else:
                result.append(char, style="dim")  # 默认暗色

        self.frame += 1
        return result


def get_shimmer_style(text: str, position: int = 0) -> Text:
    """
    为文本添加流光效果（Rich Text 格式）

    Args:
        text: 原始文本
        position: 流光位置（0 到 len(text)）

    Returns:
        带 Rich 样式的 Text 对象
    """
    result = Text()
    chars = list(text)
    width = 4  # 流光宽度

    for i, char in enumerate(chars):
        # 计算到流光中心的距离
        distance = abs(i - position)

        if distance < width:
            # 在流光范围内，根据距离选择颜色
            intensity = 1 - (distance / width)
            if intensity > 0.7:
                result.append(char, style="bold color 228")  # 最亮
            elif intensity > 0.4:
                result.append(char, style="color 220")     # 中等
            else:
                result.append(char, style="color 236")     # 较暗
        else:
            result.append(char, style="dim")              # 默认暗色

    return result
