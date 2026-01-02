"""配置管理 - 从配置文件加载所有可配置项"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache

# 配置文件路径
CONFIG_DIR = Path.home() / ".pdfkit"
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
            "output_dir": str(Path.home() / "Documents" / "pdfkit_output"),
            "quality": "medium",
            "overwrite": False,
            "verbose": False,
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
                "text": "请识别并提取图片中的所有文字内容，保持原有的格式和布局。只输出识别到的文字，不要添加任何解释。",
                "markdown": "请识别图片中的所有文字内容，并以 Markdown 格式输出。保持标题、列表、表格等结构。",
                "json": "请识别图片中的所有文字内容，以 JSON 格式输出。",
                "table": "请识别图片中的表格数据，并以 Markdown 表格格式输出。",
                "layout": "请分析文档图片的版面结构，以 JSON 格式输出。",
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
