"""阿里百炼图像翻译模型客户端

使用 qwen-mt-image 模型进行图像翻译，保留原始排版。
"""

import os
import time
from typing import Optional, List
from enum import Enum


def _import_requests():
    """Lazy import requests for optional dependency"""
    try:
        import requests
        return requests
    except ImportError:
        raise ImportError(
            "AI Translate 功能需要安装 requests 库。\n"
            "请运行以下命令安装:\n"
            "  pip install requests\n"
            "或:\n"
            "  pip3 install requests"
        )


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    UNKNOWN = "UNKNOWN"


class LanguageCode(str, Enum):
    """支持的语言代码

    源语言或目标语言必须有一个是中文或英文。
    """

    # 可作为源语言和目标语言
    ZH = "zh"  # 中文
    EN = "en"  # 英语
    JA = "ja"  # 日语
    KO = "ko"  # 韩语
    FR = "fr"  # 法语
    ES = "es"  # 西班牙语
    RU = "ru"  # 俄语
    PT = "pt"  # 葡萄牙语
    IT = "it"  # 意大利语
    VI = "vi"  # 越南语

    # 仅可作为源语言
    DE = "de"  # 德语

    # 仅可作为目标语言
    TH = "th"  # 泰语
    AR = "ar"  # 阿拉伯语
    ID = "id"  # 印尼语
    MS = "ms"  # 马来语


class QwenImageTranslator:
    """阿里百炼图像翻译模型客户端

    使用 qwen-mt-image 模型进行图像翻译。
    """

    API_BASE = "https://dashscope.aliyuncs.com/api/v1"
    MODEL = "qwen-mt-image"

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 120,
        poll_interval: int = 5,
    ):
        """
        初始化翻译器

        Args:
            api_key: API Key，默认从环境变量 DASHSCOPE_API_KEY 读取
            timeout: 单页翻译超时时间（秒）
            poll_interval: 轮询间隔（秒）
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API Key 未配置。请设置环境变量 DASHSCOPE_API_KEY 或传入 api_key 参数\n"
                "获取 API Key: https://help.aliyun.com/zh/model-studio/get-api-key"
            )

        self.timeout = timeout
        self.poll_interval = poll_interval

    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

    def translate_image(
        self,
        image_url: str,
        target_lang: str,
        source_lang: str = "auto",
        domain_hint: Optional[str] = None,
        terminologies: Optional[List[dict]] = None,
        sensitives: Optional[List[str]] = None,
        skip_main_subject: bool = False,
    ) -> Optional[str]:
        """
        翻译单张图片（异步）

        Args:
            image_url: 图片的公网可访问URL
            target_lang: 目标语言代码
            source_lang: 源语言代码，默认auto自动检测
            domain_hint: 领域提示（英文）
            terminologies: 术语表 [{"src": "xxx", "tgt": "yyy"}, ...]
            sensitives: 敏感词列表（不翻译的词）
            skip_main_subject: 是否翻译主体（人物/商品/Logo）上的文字

        Returns:
            翻译后图片的URL，如果页面无文字则返回 None
        """
        # 步骤1: 创建任务
        task_id = self._create_task(
            image_url=image_url,
            target_lang=target_lang,
            source_lang=source_lang,
            domain_hint=domain_hint,
            terminologies=terminologies,
            sensitives=sensitives,
            skip_main_subject=skip_main_subject,
        )

        # 步骤2: 轮询结果
        return self._poll_result(task_id)

    def _create_task(
        self,
        image_url: str,
        target_lang: str,
        source_lang: str = "auto",
        domain_hint: Optional[str] = None,
        terminologies: Optional[List[dict]] = None,
        sensitives: Optional[List[str]] = None,
        skip_main_subject: bool = False,
    ) -> str:
        """创建翻译任务，返回task_id"""

        payload = {
            "model": self.MODEL,
            "input": {
                "image_url": image_url,
                "source_lang": source_lang,
                "target_lang": target_lang,
            }
        }

        # 可选扩展参数
        ext = {}
        if domain_hint:
            ext["domainHint"] = domain_hint
        if terminologies:
            ext["terminologies"] = terminologies
        if sensitives:
            ext["sensitives"] = sensitives
        if ext:
            payload["input"]["ext"] = ext

        # 配置参数
        if skip_main_subject:
            payload["input"]["config"] = {"skipImgSegment": True}

        requests = _import_requests()
        response = requests.post(
            f"{self.API_BASE}/services/aigc/image2image/image-synthesis",
            headers=self._get_headers(),
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

        if "code" in result:
            raise Exception(
                f"创建任务失败: {result.get('message', result.get('code'))}"
            )

        return result["output"]["task_id"]

    def _poll_result(self, task_id: str) -> Optional[str]:
        """轮询任务结果

        Returns:
            翻译后图片的URL，如果页面无文字则返回 None
        """
        requests = _import_requests()
        url = f"{self.API_BASE}/tasks/{task_id}"

        start_time = time.time()
        while time.time() - start_time < self.timeout:
            response = requests.get(url, headers={"Authorization": f"Bearer {self.api_key}"})
            response.raise_for_status()
            result = response.json()

            status = result["output"]["task_status"]

            if status == TaskStatus.SUCCEEDED:
                image_url = result["output"].get("image_url")
                message = result["output"].get("message", "")

                if "No text detected" in message or not image_url:
                    # 无可翻译文字，返回 None
                    return None

                return image_url

            elif status == TaskStatus.FAILED:
                raise Exception(
                    f"翻译失败: {result['output'].get('message', 'Unknown error')}"
                )

            elif status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                time.sleep(self.poll_interval)

            else:  # CANCELED, UNKNOWN
                raise Exception(f"任务状态异常: {status}")

        raise TimeoutError(f"翻译超时 (>{self.timeout}s)")


def validate_language_pair(source: str, target: str) -> tuple[bool, Optional[str]]:
    """
    验证语言对是否有效

    源语言或目标语言必须有一个是中文或英文。

    Args:
        source: 源语言代码
        target: 目标语言代码

    Returns:
        (是否有效, 错误信息)
    """
    has_zh = source == "zh" or target == "zh"
    has_en = source == "en" or target == "en"

    if not (has_zh or has_en):
        return False, "源语言或目标语言必须有一个是中文或英文"

    return True, None
