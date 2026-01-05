"""配置管理 - 从配置文件加载所有可配置项"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache

from .platform import get_app_config_dir, get_documents_dir

# 配置文件路径 (跨平台兼容)
CONFIG_DIR = get_app_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.yaml"
DEFAULT_CONFIG_FILE = Path(__file__).parent.parent / "templates" / "default_config.yaml"


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Any]:
    """
    加载配置文件

    优先级:
    1. 用户配置 (~/.pdfkit/config.yaml)
    2. 默认配置 (内置)

    Returns:
        配置字典
    """
    config = _get_default_config()

    # 加载用户配置
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            # 深度合并配置
            config = _deep_merge(config, user_config)
        except Exception as e:
            print(f"警告: 加载配置文件失败: {e}")

    # 处理环境变量引用
    config = _expand_env_vars(config)

    return config


def _get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        "defaults": {
            "output_dir": str(get_documents_dir() / "pdfkit_output"),
            "quality": "medium",
            "overwrite": False,
            "verbose": False,
        },
        "ai": {
            "translate": {
                "default_dpi": 200,
                "poll_interval": 5,
                "timeout": 120,
                "upload_method": "base64",
                "upload": {
                    "base64": {},
                    "local": {
                        "port": 8000,
                    },
                    "oss": {
                        "access_key_id": os.getenv("ALIYUN_ACCESS_KEY_ID", ""),
                        "access_key_secret": os.getenv("ALIYUN_ACCESS_KEY_SECRET", ""),
                        "endpoint": os.getenv("ALIYUN_OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com"),
                        "bucket_name": os.getenv("ALIYUN_OSS_BUCKET", "pdfkit-temp"),
                    },
                },
            },
        },
        "ocr": {
            "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
            "models": {
                "flash": "qwen3-vl-flash",
                "plus": "qwen3-vl-plus",
                "ocr": "qwen-vl-ocr-latest",
            },
            "regions": {
                "beijing": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "singapore": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            },
            "default_model": "flash",
            "default_region": "beijing",
            "default_dpi": 300,
            "default_format": "text",
            "timeout": 60,
            "max_retries": 3,
            "concurrency": 10,  # 异步模式最大并发数
            "prompts": {
                # 通用提示词（所有模型共用）
                "text": "请识别并提取图片中的所有文字内容，保持原有的格式和布局。只输出识别到的文字，不要添加任何解释。",

                "markdown": (
                    "请识别图片中的所有文字内容，直接以 Markdown 格式输出。\n"
                    "\n"
                    "输出要求：\n"
                    "1. 直接输出纯 Markdown 内容，不要用代码块(```)包装\n"
                    "2. 标题处理：\n"
                    "   - 文章/论文标题用 # (包括副标题，合并为一行)\n"
                    "   - 章节标题(1, 2, 3...)用 ##\n"
                    "   - 子节标题(2.1, 2.2...)用 ###\n"
                    "   - 更深层次(2.1.1, 2.1.2...)用 ####\n"
                    "   - 小标题/粗体标题用 **文本**\n"
                    "3. 表格必须使用 Markdown 表格语法（不要用 LaTeX tabular 环境）\n"
                    "4. 数学公式用 LaTeX，行内 $...$，独立块 $$...$$\n"
                    "5. 图片/图表无法识别时，使用占位符格式：\n"
                    "   ![Figure X: 图表描述]()\n"
                    "6. 脚注使用上标格式，如 ²、³ 或 ${}^{n}$\n"
                    "7. 忽略单独的页码数字\n"
                    "8. 只输出识别的内容，不要添加任何解释"
                ),

                "markdown_with_images": (
                    "请识别图片中的所有文字内容，直接以 Markdown 格式输出。\n"
                    "\n"
                    "输出要求：\n"
                    "1. 直接输出纯 Markdown 内容，不要用代码块(```)包装\n"
                    "2. 标题处理：\n"
                    "   - 文章/论文标题用 # (包括副标题，合并为一行)\n"
                    "   - 章节标题(1, 2, 3...)用 ##\n"
                    "   - 子节标题(2.1, 2.2...)用 ###\n"
                    "   - 更深层次(2.1.1, 2.1.2...)用 ####\n"
                    "   - 小标题/粗体标题用 **文本**\n"
                    "3. 表格必须使用 Markdown 表格语法（不要用 LaTeX tabular 环境）\n"
                    "4. 数学公式用 LaTeX，行内 $...$，独立块 $$...$$\n"
                    "5. 脚注使用上标格式，如 ²、³ 或 ${}^{n}$\n"
                    "6. 忽略单独的页码数字\n"
                    "7. 只输出识别的内容，不要添加任何解释\n"
                    "\n"
                    "【关键规则 - 图像处理】：\n"
                    "- 我会提供本页已提取的图像列表和路径\n"
                    "- 当遇到图片/图表/表格图像时，必须使用我提供的路径\n"
                    "- 格式：![Figure X: 描述](images/page_X_img_Y.png)\n"
                    "- 严禁使用 <!-- 图片无法识别 --> 或空路径\n"
                    "- 如果没有提供图像路径，直接省略该图像引用"
                ),

                "json": "请识别图片中的所有文字内容，以 JSON 格式输出。",

                "table": "请识别图片中的表格数据，并以 Markdown 表格格式输出。如果有多个表格，请依次输出。只输出 Markdown 表格，不要添加其他解释。",

                "layout": "请分析这张文档图片的版面结构，识别出标题、正文、表格等，以 JSON 格式输出结构化的版面分析结果。",

                # 模型特定提示词（可选，覆盖通用提示词）
                "models": {
                    "flash": {
                        # flash 模型使用通用提示词（无需覆盖）
                    },
                    "plus": {
                        # plus 模型可以使用更详细的提示词（可选）
                        # 取消注释以下内容以覆盖通用提示词：
                        # "markdown": "..."
                    },
                    "ocr": {
                        # ocr 模型可以使用结构化文本专用提示词（可选）
                    },
                },
            },
        },
        "compress": {
            "quality": "medium",
            "image_quality": 85,
            "downscale_images": True,
            "max_image_size": 1920,
        },
        "watermark": {
            "font": "Helvetica",
            "font_size": 48,
            "color": "#00000033",
            "rotation": 45,
            "position": "center",
            "opacity": 0.3,
        },
        "ui": {
            "colors": {
                "primary": "#3B82F6",
                "success": "#10B981",
                "warning": "#F59E0B",
                "error": "#EF4444",
                "info": "#06B6D4",
            },
            "show_progress": True,
            "use_emoji": True,
        },
        "convert": {
            "to_image": {
                "format": "png",
                "dpi": 150,
                "quality": 90,
            },
            "from_image": {
                "page_size": "A4",
                "margin": 10,
            },
            "to_word": {
                "preserve_layout": True,
                "extract_images": True,
            },
            "from_url": {
                "wait_time": 3,
                "viewport_width": 1920,
                "viewport_height": 1080,
                "full_page": True,
            },
        },
        "batch": {
            "parallel": 4,
            "continue_on_error": True,
            "log_file": str(CONFIG_DIR / "batch.log"),
        },
        "logging": {
            "level": "INFO",
            "file": str(CONFIG_DIR / "pdfkit.log"),
            "max_size": "10M",
            "backup_count": 5,
        },
    }


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """深度合并两个字典"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _expand_env_vars(config: Any) -> Any:
    """递归展开环境变量引用 (${VAR_NAME})"""
    if isinstance(config, dict):
        return {k: _expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_expand_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        env_var = config[2:-1]
        return os.getenv(env_var, "")
    return config


def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    获取配置值

    Args:
        key_path: 配置路径，如 "ocr.models.flash"
        default: 默认值

    Returns:
        配置值
    """
    config = load_config()
    keys = key_path.split(".")

    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value


def init_config():
    """初始化配置文件（如果不存在）"""
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True)

    if not CONFIG_FILE.exists():
        default_config = _get_default_config()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
        print(f"已创建配置文件: {CONFIG_FILE}")


def reload_config() -> Dict[str, Any]:
    """重新加载配置（清除缓存）"""
    load_config.cache_clear()
    return load_config()
