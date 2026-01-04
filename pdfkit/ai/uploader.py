"""图片上传模块

将本地图片上传到公网可访问的位置，供图像翻译 API 使用。
"""

import os
import base64
from pathlib import Path
from typing import Optional
from datetime import datetime
from enum import Enum
import tempfile


class UploadMethod(str, Enum):
    """上传方法"""
    OSS = "oss"           # 阿里云OSS
    LOCAL = "local"       # 本地HTTP服务器（仅测试用）
    BASE64 = "base64"     # Base64 Data URL（部分API支持）


class ImageUploader:
    """图片上传器基类"""

    def upload(self, img_bytes: bytes, filename: str) -> str:
        """
        上传图片，返回公网可访问的URL

        Args:
            img_bytes: 图片字节
            filename: 文件名

        Returns:
            图片URL
        """
        raise NotImplementedError


class Base64Uploader(ImageUploader):
    """Base64 Data URL 上传器

    注意：这是一种特殊格式，某些 API 可能不支持。
    """

    def upload(self, img_bytes: bytes, filename: str) -> str:
        """转换为 Base64 Data URL"""
        b64 = base64.b64encode(img_bytes).decode()
        return f"data:image/png;base64,{b64}"


class LocalUploader(ImageUploader):
    """本地HTTP服务器上传器（仅用于测试）

    启动一个临时HTTP服务器，将图片保存到临时目录。
    注意：这种方法不适用于生产环境，因为需要服务器正在运行。
    """

    def __init__(self, port: int = 8000):
        self.port = port
        self.temp_dir = Path(tempfile.gettempdir()) / "pdfkit-translate"
        self.temp_dir.mkdir(exist_ok=True)
        self.server_running = False

    def upload(self, img_bytes: bytes, filename: str) -> str:
        """
        保存图片到本地临时目录

        注意：实际使用时需要先启动HTTP服务器：
        python -m http.server 8000 -d {temp_dir}
        """
        file_path = self.temp_dir / filename
        file_path.write_bytes(img_bytes)
        return f"http://localhost:{self.port}/{filename}"


def create_uploader(
    method: str = "base64",
    **kwargs
) -> ImageUploader:
    """
    创建图片上传器

    Args:
        method: 上传方法 (oss/local/base64)
        **kwargs: 上传器特定参数

    Returns:
        ImageUploader 实例
    """
    method = method.lower()

    if method == UploadMethod.BASE64:
        return Base64Uploader()

    elif method == UploadMethod.LOCAL:
        port = kwargs.get("port", 8000)
        return LocalUploader(port=port)

    elif method == UploadMethod.OSS:
        # OSS 上传器需要 oss2 库
        try:
            from .oss_uploader import OSSUploader
            return OSSUploader(
                access_key_id=kwargs.get("access_key_id"),
                access_key_secret=kwargs.get("access_key_secret"),
                endpoint=kwargs.get("endpoint"),
                bucket_name=kwargs.get("bucket_name"),
            )
        except ImportError:
            raise ImportError(
                "OSS 上传需要安装 oss2: pip install oss2"
            )

    else:
        raise ValueError(f"不支持的上传方法: {method}")


# 便捷函数
def upload_image(
    img_bytes: bytes,
    filename: str,
    method: str = "base64",
    **kwargs
) -> str:
    """
    上传图片的便捷函数

    Args:
        img_bytes: 图片字节
        filename: 文件名
        method: 上传方法
        **kwargs: 上传器参数

    Returns:
        图片URL
    """
    uploader = create_uploader(method, **kwargs)
    return uploader.upload(img_bytes, filename)
