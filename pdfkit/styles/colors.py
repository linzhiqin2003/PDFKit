"""颜色和主题系统"""

from rich.theme import Theme
from rich.style import Style
from typing import Dict

# ============================================================================
# 主色调定义
# ============================================================================

# 主色 - 蓝色系 (品牌色)
PRIMARY = "#3B82F6"         # 主要操作、标题
PRIMARY_LIGHT = "#60A5FA"   # 悬停、次要
PRIMARY_DARK = "#1D4ED8"    # 强调

# 成功色 - 绿色系
SUCCESS = "#10B981"         # 成功消息
SUCCESS_LIGHT = "#34D399"
SUCCESS_DARK = "#059669"

# 警告色 - 黄色系
WARNING = "#F59E0B"         # 警告消息
WARNING_LIGHT = "#FBBF24"
WARNING_DARK = "#D97706"

# 错误色 - 红色系
ERROR = "#EF4444"           # 错误消息
ERROR_LIGHT = "#F87171"
ERROR_DARK = "#DC2626"

# 信息色 - 青色系
INFO = "#06B6D4"            # 信息提示
INFO_LIGHT = "#22D3EE"
INFO_DARK = "#0891B2"

# 中性色 - 灰色系
TEXT = "#E5E7EB"            # 主文本
TEXT_MUTED = "#9CA3AF"      # 次要文本
TEXT_DIM = "#6B7280"        # 暗淡文本
BORDER = "#374151"          # 边框
BACKGROUND = "#1F2937"      # 背景

# 特殊色
HIGHLIGHT = "#A855F7"       # 高亮 (紫色)
LINK = "#3B82F6"            # 链接
CODE = "#F472B6"            # 代码 (粉色)
PATH = "#34D399"            # 文件路径 (绿色)
NUMBER = "#FBBF24"          # 数字 (黄色)
SIZE = "#60A5FA"            # 文件大小 (浅蓝)


# ============================================================================
# Rich 主题定义
# ============================================================================

PDFKIT_THEME = Theme({
    # 基础样式
    "info": f"bold {INFO}",
    "warning": f"bold {WARNING}",
    "error": f"bold {ERROR}",
    "success": f"bold {SUCCESS}",
    "text": f"{TEXT}",

    # 标题和强调
    "title": f"bold {PRIMARY}",
    "subtitle": f"{PRIMARY_LIGHT}",
    "heading": f"bold {TEXT}",
    "emphasis": f"italic {TEXT_MUTED}",

    # 命令和代码
    "command": f"bold {CODE}",
    "option": f"{INFO}",
    "argument": f"{WARNING_LIGHT}",
    "code": f"{CODE}",

    # 文件和路径
    "path": f"{PATH}",
    "filename": f"bold {PATH}",
    "url": f"underline {LINK}",

    # 数据
    "number": f"{NUMBER}",
    "size": f"{SIZE}",
    "percent": f"{SUCCESS}",
    "date": f"{TEXT_MUTED}",

    # 状态
    "status.pending": f"{TEXT_MUTED}",
    "status.running": f"bold {INFO}",
    "status.success": f"bold {SUCCESS}",
    "status.failed": f"bold {ERROR}",
    "status.skipped": f"{WARNING}",

    # 进度条
    "progress.description": f"{TEXT}",
    "progress.percentage": f"bold {PRIMARY}",
    "progress.bar.complete": f"{SUCCESS}",
    "progress.bar.incomplete": f"{BORDER}",

    # 表格
    "table.header": f"bold {PRIMARY}",
    "table.border": f"{BORDER}",
    "table.row.odd": f"{TEXT}",
    "table.row.even": f"{TEXT_MUTED}",

    # PDF 相关特殊样式
    "pdf.pages": f"bold {NUMBER}",
    "pdf.size": f"{SIZE}",
    "pdf.encrypted": f"bold {ERROR}",
    "pdf.metadata": f"{TEXT_MUTED}",
})


# ============================================================================
# 图标定义 (Nerd Font / Unicode)
# ============================================================================

class Icons:
    # 状态图标
    SUCCESS = "✓"           # ✓ or
    ERROR = "✗"             # ✗ or
    WARNING = "⚠"           # ⚠ or
    INFO = "ℹ"              # ℹ or
    PENDING = "○"           # ○ or
    RUNNING = "◐"           # ◐ or

    # 文件图标
    PDF = "📄"              # or
    IMAGE = "🖼"            # or
    FOLDER = "📁"           # or
    FILE = "📄"             # or

    # 操作图标
    SPLIT = "✂"             # or 󰗈
    MERGE = "🔗"            # or
    CONVERT = "🔄"          # or
    COMPRESS = "📦"         # or
    ENCRYPT = "🔒"          # or
    DECRYPT = "🔓"          # or
    EXTRACT = "📤"          # or
    CROP = "✂"             # or
    RESIZE = "📐"           # or
    BOOKMARK = "🔖"         # or
    TABLE = "📊"            # or
    DROP = "💧"             # or

    # 箭头
    ARROW_RIGHT = "→"
    ARROW_LEFT = "←"
    ARROW_DOWN = "↓"
    ARROW_UP = "↑"

    # 其他
    CHECK = "✓"
    CROSS = "✗"
    DOT = "•"
    STAR = "★"
    CLOCK = "⏱"
    SEARCH = "🔍"
    MAGIC = "✨"


# ============================================================================
# 从配置加载颜色（支持用户自定义）
# ============================================================================

def load_theme_from_config(config_colors: Dict[str, str]) -> Theme:
    """
    从配置文件加载自定义颜色主题

    Args:
        config_colors: 配置文件中的 colors 字典

    Returns:
        Rich Theme 对象
    """
    # 获取自定义颜色，如果没有则使用默认值
    primary = config_colors.get("primary", PRIMARY)
    success = config_colors.get("success", SUCCESS)
    warning = config_colors.get("warning", WARNING)
    error = config_colors.get("error", ERROR)
    info = config_colors.get("info", INFO)

    return Theme({
        "info": f"bold {info}",
        "warning": f"bold {warning}",
        "error": f"bold {error}",
        "success": f"bold {success}",
        "text": f"{TEXT}",
        "title": f"bold {primary}",
        "subtitle": f"{primary}",
        "heading": "bold",
        "command": f"bold {CODE}",
        "option": f"{info}",
        "argument": f"{warning}",
        "code": f"{CODE}",
        "path": f"{PATH}",
        "filename": f"bold {PATH}",
        "url": f"underline {primary}",
        "number": f"{NUMBER}",
        "size": f"{SIZE}",
        "percent": f"{success}",
        "date": f"{TEXT_MUTED}",
        "status.pending": f"{TEXT_MUTED}",
        "status.running": f"bold {info}",
        "status.success": f"bold {success}",
        "status.failed": f"bold {error}",
        "status.skipped": f"{warning}",
        "progress.description": f"{TEXT}",
        "progress.percentage": f"bold {primary}",
        "progress.bar.complete": f"{success}",
        "progress.bar.incomplete": f"{BORDER}",
        "table.header": f"bold {primary}",
        "table.border": f"{BORDER}",
        "table.row.odd": f"{TEXT}",
        "table.row.even": f"{TEXT_MUTED}",
        "pdf.pages": f"bold {NUMBER}",
        "pdf.size": f"{SIZE}",
        "pdf.encrypted": f"bold {error}",
        "pdf.metadata": f"{TEXT_MUTED}",
    })


def get_theme(use_config: bool = True) -> Theme:
    """
    获取当前主题

    Args:
        use_config: 是否使用配置文件中的颜色

    Returns:
        Rich Theme 对象
    """
    if use_config:
        try:
            from ..utils.config import load_config
            config = load_config()
            config_colors = config.get("ui", {}).get("colors", {})
            if config_colors:
                return load_theme_from_config(config_colors)
        except Exception:
            pass

    return PDFKIT_THEME
