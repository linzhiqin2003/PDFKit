"""PDF 信息服务 - 核心业务逻辑

此模块包含与 PDF 信息获取相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass
import fitz  # PyMuPDF

from ..utils.file_utils import format_size


@dataclass
class PDFInfo:
    """PDF 文件信息"""
    filename: str
    path: str
    size_bytes: int
    size_human: str
    page_count: int
    version: str
    is_encrypted: bool
    # 元数据（可选）
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "filename": self.filename,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "size_human": self.size_human,
            "page_count": self.page_count,
            "version": self.version,
            "is_encrypted": self.is_encrypted,
            "title": self.title,
            "author": self.author,
            "subject": self.subject,
            "keywords": self.keywords,
            "creator": self.creator,
            "producer": self.producer,
            "created": self.created,
            "modified": self.modified,
        }


class PDFInfoError(Exception):
    """PDF 信息获取错误"""
    pass


class PDFEncryptedError(PDFInfoError):
    """PDF 加密错误"""
    pass


class PDFNotFoundError(PDFInfoError):
    """PDF 文件不存在"""
    pass


def get_pdf_info(
    file_path: Union[str, Path],
    detailed: bool = False,
) -> PDFInfo:
    """
    获取 PDF 文件的基本信息
    
    Args:
        file_path: PDF 文件路径
        detailed: 是否获取详细元数据
        
    Returns:
        PDFInfo: PDF 文件信息对象
        
    Raises:
        PDFNotFoundError: 文件不存在
        PDFEncryptedError: 文件加密且无法读取
        PDFInfoError: 其他读取错误
    """
    path = Path(file_path)
    
    # 验证文件存在
    if not path.exists():
        raise PDFNotFoundError(f"文件不存在: {file_path}")
    
    if not path.suffix.lower() == '.pdf':
        raise PDFInfoError(f"不是 PDF 文件: {file_path}")
    
    try:
        doc = fitz.open(path)
        
        # 检查加密
        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise PDFEncryptedError(
                f"PDF 文件已加密，需要密码才能读取: {file_path}"
            )
        
        # 基础信息
        info = PDFInfo(
            filename=path.name,
            path=str(path.absolute()),
            size_bytes=path.stat().st_size,
            size_human=format_size(path.stat().st_size),
            page_count=doc.page_count,
            version="PDF",
            is_encrypted=doc.is_encrypted,
        )
        
        # 元数据
        metadata = doc.metadata or {}
        if metadata:
            info.version = f"PDF {metadata.get('format', 'Unknown')}"
            
            if detailed:
                info.title = metadata.get("title") or None
                info.author = metadata.get("author") or None
                info.subject = metadata.get("subject") or None
                info.keywords = metadata.get("keywords") or None
                info.creator = metadata.get("creator") or None
                info.producer = metadata.get("producer") or None
                info.created = metadata.get("creationDate") or None
                info.modified = metadata.get("modDate") or None
        
        doc.close()
        return info
        
    except PDFInfoError:
        raise
    except Exception as e:
        raise PDFInfoError(f"读取 PDF 失败: {e}")


def get_page_count(file_path: Union[str, Path]) -> int:
    """
    快速获取 PDF 页数
    
    Args:
        file_path: PDF 文件路径
        
    Returns:
        int: 页数
    """
    info = get_pdf_info(file_path, detailed=False)
    return info.page_count


def get_metadata(file_path: Union[str, Path]) -> dict:
    """
    获取 PDF 元数据
    
    Args:
        file_path: PDF 文件路径
        
    Returns:
        dict: 元数据字典
    """
    path = Path(file_path)
    
    if not path.exists():
        raise PDFNotFoundError(f"文件不存在: {file_path}")
    
    try:
        doc = fitz.open(path)
        
        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise PDFEncryptedError("PDF 已加密")
        
        metadata = doc.metadata or {}
        doc.close()
        
        return metadata
        
    except PDFInfoError:
        raise
    except Exception as e:
        raise PDFInfoError(f"读取元数据失败: {e}")
