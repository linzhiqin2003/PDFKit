"""进度条流光工具 - 简化版，直接可用"""

from rich.text import Text
import time


# 流光颜色渐变（金色系）
SHIMMER_STYLES = [
    "dim",                # 最暗
    "color 236",          # 暗金
    "color 178",          # 金黄
    "color 220",          # 亮金
    "bold color 228",     # 最亮
]


def shimmer_text(text: str, position: int = 0) -> Text:
    """
    为文本添加流光效果

    Args:
        text: 原始文本
        position: 流光中心位置（0 到 len(text) + width）

    Returns:
        带 Rich 样式的 Text 对象
    """
    result = Text()
    chars = list(text)
    width = 3  # 流光宽度（单边）

    for i, char in enumerate(chars):
        # 计算到流光中心的距离
        distance = abs(i - position)

        if distance <= width:
            # 在流光范围内，根据距离选择颜色
            intensity = 1 - (distance / width)
            idx = int(intensity * (len(SHIMMER_STYLES) - 1))
            style = SHIMMER_STYLES[min(idx, len(SHIMMER_STYLES) - 1)]
            result.append(char, style=style)
        else:
            result.append(char, style="dim")

    return result


def get_progress_text(text: str, frame: int) -> str:
    """
    获取带流光的进度文本（用于 progress.update）

    Args:
        text: 原始文本（如"检测第 1 页图像"）
        frame: 当前帧数

    Returns:
        带流光的文本字符串
    """
    # 只对关键词添加流光
    keywords = ["检测", "处理", "翻译", "识别", "提取", "渲染"]

    result = []
    chars = list(text)
    width = 4  # 流光宽度
    position = frame % (len(chars) + width * 2)

    for i, char in enumerate(chars):
        # 判断是否在关键词中
        in_keyword = False
        for kw in keywords:
            start = text.find(kw)
            if start != -1 and start <= i < start + len(kw):
                in_keyword = True
                # 计算在关键词中的相对位置
                kw_pos = i - start
                kw_distance = abs(kw_pos - (position - start))
                if kw_distance <= width:
                    # 应用流光颜色
                    intensity = 1 - (kw_distance / width)
                    idx = int(intensity * 4)  # 5档颜色
                    if idx == 4:
                        result.append(f"\x1b[1;38;5;228m{char}\x1b[0m")  # 最亮
                    elif idx == 3:
                        result.append(f"\x1b[38;5;220m{char}\x1b[0m")
                    elif idx == 2:
                        result.append(f"\x1b[38;5;178m{char}\x1b[0m")
                    elif idx == 1:
                        result.append(f"\x1b[38;5;236m{char}\x1b[0m")
                    else:
                        result.append(f"\x1b[2m{char}\x1b[0m")
                    break
        if not in_keyword or len(result) <= i:
            result.append(char)

    return "".join(result)


# 简化版：只对"AI 处理中"这样的固定文本添加流光
AI_KEYWORDS = {
    "检测": "🔍",
    "处理": "⚙️",
    "翻译": "🌐",
    "识别": "👁️",
    "提取": "📤",
    "渲染": "🖼️",
}


def format_with_shimmer(text: str, frame: int) -> str:
    """
    格式化文本，添加流光效果

    Args:
        text: 原始文本
        frame: 当前帧数

    Returns:
        带 ANSI 颜色的文本
    """
    # 查找关键词位置
    for kw, emoji in AI_KEYWORDS.items():
        if kw in text:
            # 替换关键词为带流光的版本
            return text.replace(kw, _shimmer_word(kw, frame))

    return text


def _shimmer_word(word: str, frame: int) -> str:
    """为单个词添加流光效果"""
    width = 2
    position = frame % (len(word) + width * 2)
    result = []

    for i, char in enumerate(word):
        distance = abs(i - position)
        if distance <= width:
            intensity = 1 - (distance / width)
            idx = int(intensity * 4)
            if idx >= 4:
                result.append(f"\x1b[1;38;5;228m{char}\x1b[0m")
            elif idx >= 3:
                result.append(f"\x1b[38;5;220m{char}\x1b[0m")
            elif idx >= 2:
                result.append(f"\x1b[38;5;178m{char}\x1b[0m")
            elif idx >= 1:
                result.append(f"\x1b[38;5;236m{char}\x1b[0m")
            else:
                result.append(f"\x1b[2m{char}\x1b[0m")
        else:
            result.append(char)

    return "".join(result)
