"""PDF 页眉页脚服务 - 核心业务逻辑

此模块包含与 PDF 页眉页脚相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, List, Union
from dataclasses import dataclass
from datetime import datetime

import fitz  # PyMuPDF


# ==================== 数据模型 ====================

@dataclass
class HeaderResult:
    """页眉添加结果"""
    output_path: str
    page_count: int
    text: str
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "page_count": self.page_count,
            "text": self.text,
            "success": self.success,
        }


@dataclass
class FooterResult:
    """页脚添加结果"""
    output_path: str
    page_count: int
    text: str
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "page_count": self.page_count,
            "text": self.text,
            "success": self.success,
        }


# ==================== 自定义异常 ====================

class PDFHeaderError(Exception):
    """PDF 页眉页脚错误"""
    pass


class EncryptedPDFError(PDFHeaderError):
    """PDF 加密错误"""
    pass


class InvalidParameterError(PDFHeaderError):
    """无效参数"""
    pass


# ==================== 核心函数 ====================

def add_header(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    text: str,
    font_size: int = 12,
    align: str = "center",
    margin_top: float = 18,
    pages: Optional[List[int]] = None,
) -> HeaderResult:
    """
    添加页眉到 PDF

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        text: 页眉文字
        font_size: 字体大小
        align: 对齐方式 (left/center/right)
        margin_top: 顶部边距（点）
        pages: 页码列表 (0-indexed)，None 表示全部页面

    Returns:
        HeaderResult: 添加结果
    """
    if align not in ("left", "center", "right"):
        raise InvalidParameterError("对齐方式必须是 left, center 或 right")

    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        total_pages = doc.page_count

        # 确定要添加页眉的页面
        if pages is None:
            pages = list(range(total_pages))

        # 获取页面尺寸
        if pages:
            page_width = doc[pages[0]].rect.width

        for page_num in pages:
            page = doc[page_num]
            rect = page.rect

            # y 坐标：从页面顶部 + 边距
            y = rect.y0 + margin_top

            # textbox 高度需要足够大
            tb_height = font_size * 2

            # 计算 textbox 区域
            if align == "left":
                tb_rect = fitz.Rect(rect.x0 + 36, y, rect.x1 - 36, y + tb_height)
            elif align == "center":
                margin = 36
                tb_rect = fitz.Rect(rect.x0 + margin, y, rect.x1 - margin, y + tb_height)
            else:  # right
                tb_rect = fitz.Rect(rect.x0 + 36, y, rect.x1 - 36, y + tb_height)

            # 设置对齐方式
            align_flag = fitz.TEXT_ALIGN_LEFT
            if align == "center":
                align_flag = fitz.TEXT_ALIGN_CENTER
            elif align == "right":
                align_flag = fitz.TEXT_ALIGN_RIGHT

            # 插入文本
            rc = page.insert_textbox(
                tb_rect,
                text,
                fontsize=font_size,
                fontname="helv",  # 使用内置字体
                color=(0, 0, 0),
                align=align_flag,
            )

            # rc < 0 表示文本不适合 textbox
            if rc < 0:
                # 如果文本太长，尝试更大的区域
                tb_rect = fitz.Rect(rect.x0 + 18, y, rect.x1 - 18, y + tb_height * 2)
                page.insert_textbox(
                    tb_rect,
                    text,
                    fontsize=font_size,
                    fontname="helv",
                    color=(0, 0, 0),
                    align=align_flag,
                )

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存 (使用 deflate 压缩)
        doc.save(output_path, deflate=True)
        doc.close()

        return HeaderResult(
            output_path=str(output_path),
            page_count=len(pages),
            text=text,
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFHeaderError(f"添加页眉失败: {e}")


def add_footer(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    text: str,
    font_size: int = 10,
    align: str = "center",
    margin_bottom: float = 18,
    pages: Optional[List[int]] = None,
) -> FooterResult:
    """
    添加页脚到 PDF

    支持的变量:
        {page}  - 当前页码
        {total} - 总页数
        {date}  - 当前日期
        {time}  - 当前时间

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        text: 页脚文字（支持变量）
        font_size: 字体大小
        align: 对齐方式 (left/center/right)
        margin_bottom: 底部边距（点）
        pages: 页码列表 (0-indexed)，None 表示全部页面

    Returns:
        FooterResult: 添加结果
    """
    if align not in ("left", "center", "right"):
        raise InvalidParameterError("对齐方式必须是 left, center 或 right")

    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        doc = fitz.open(file_path)

        if doc.is_encrypted and doc.needs_pass:
            doc.close()
            raise EncryptedPDFError(f"PDF 文件已加密: {file_path}")

        total_pages = doc.page_count

        # 确定要添加页脚的页面
        if pages is None:
            pages = list(range(total_pages))

        # 准备变量
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        for page_num in pages:
            page = doc[page_num]
            rect = page.rect

            # 替换变量
            page_text = text.format(
                page=page_num + 1,
                total=total_pages,
                date=date_str,
                time=time_str
            )

            # textbox 高度
            tb_height = font_size * 2

            # y 坐标：从页面底部往上
            y = rect.y1 - margin_bottom - tb_height

            # 计算 textbox 区域（页脚在底部，横跨页面宽度）
            if align == "left":
                tb_rect = fitz.Rect(rect.x0 + 36, y, rect.x1 - 36, y + tb_height)
            elif align == "center":
                tb_rect = fitz.Rect(rect.x0 + 36, y, rect.x1 - 36, y + tb_height)
            else:  # right
                tb_rect = fitz.Rect(rect.x0 + 36, y, rect.x1 - 36, y + tb_height)

            # 设置对齐方式
            align_flag = fitz.TEXT_ALIGN_LEFT
            if align == "center":
                align_flag = fitz.TEXT_ALIGN_CENTER
            elif align == "right":
                align_flag = fitz.TEXT_ALIGN_RIGHT

            # 插入文本
            rc = page.insert_textbox(
                tb_rect,
                page_text,
                fontsize=font_size,
                fontname="helv",  # 使用内置字体
                color=(0.3, 0.3, 0.3),
                align=align_flag,
            )

            # rc < 0 表示文本不适合 textbox
            if rc < 0:
                tb_rect = fitz.Rect(rect.x0 + 18, y, rect.x1 - 18, y + tb_height * 2)
                page.insert_textbox(
                    tb_rect,
                    page_text,
                    fontsize=font_size,
                    fontname="helv",
                    color=(0.3, 0.3, 0.3),
                    align=align_flag,
                )

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存
        doc.save(output_path, deflate=True)
        doc.close()

        return FooterResult(
            output_path=str(output_path),
            page_count=len(pages),
            text=text,
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFHeaderError(f"添加页脚失败: {e}")
