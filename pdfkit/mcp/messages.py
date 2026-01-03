"""MCP 工具错误消息模板

提供友好的、本地化的错误消息模板和格式化函数。
"""

from typing import Dict, Any, Optional
from string import Formatter


# ==================== 错误消息模板 ====================

class ErrorMessages:
    """错误消息模板类

    提供各种错误场景的消息模板和建议。
    """

    # ========== 文件错误 ==========

    FILE_NOT_FOUND = "文件 '{path}' 不存在"
    FILE_NOT_FOUND_SUGGESTION = "请检查文件路径是否正确，确保文件扩展名正确（.pdf）"

    FILE_INVALID_PDF = "不是有效的 PDF 文件: '{path}'"
    FILE_INVALID_PDF_SUGGESTION = "请确保文件是 PDF 格式且未损坏。可以通过重命名方式将其他格式伪装的 PDF 转换为真正的 PDF"

    FILE_ENCRYPTED = "PDF 文件 '{path}' 已加密"
    FILE_ENCRYPTED_SUGGESTION = "请先使用 pdfkit_decrypt_pdf 工具解密，或提供密码参数"

    FILE_PERMISSION_DENIED = "没有文件 '{path}' 的访问权限"
    FILE_PERMISSION_DENIED_SUGGESTION = "请检查文件权限设置，确保有读取权限"

    OUTPUT_DIR_INVALID = "无法创建输出目录: '{path}'"
    OUTPUT_DIR_INVALID_SUGGESTION = "请检查目录路径是否有效，并确保有写入权限"

    # ========== 参数错误 ==========

    PARAM_OUT_OF_RANGE = "参数 '{param}' 的值 '{value}' 超出有效范围 [{min}, {max}]"
    PARAM_OUT_OF_RANGE_SUGGESTION = "请将参数值调整到指定范围内"

    PARAM_INVALID_VALUE = "参数 '{param}' 的值 '{value}' 无效"
    PARAM_INVALID_VALUE_SUGGESTION = "允许的值: {values}"

    PARAM_MISSING_REQUIRED = "缺少必需参数: '{param}'"
    PARAM_MISSING_REQUIRED_SUGGESTION = "请提供该参数的值"

    PARAM_INVALID_FORMAT = "参数 '{param}' 的格式无效: '{value}'"
    PARAM_INVALID_FORMAT_SUGGESTION = "期望格式: {expected}"

    # ========== 页面错误 ==========

    PAGE_OUT_OF_RANGE = "页码 '{page}' 超出范围 (1-{total})"
    PAGE_OUT_OF_RANGE_SUGGESTION = "请使用有效页码: 1 到 {total}"

    PAGE_INVALID_RANGE = "页面范围 '{range}' 格式无效"
    PAGE_INVALID_RANGE_SUGGESTION = "正确格式: '1-3' (连续页), '5' (单页), '1-3,5,7-9' (混合)"

    PAGE_INVALID_NUMBER = "页码 '{page}' 不是有效的数字"
    PAGE_INVALID_NUMBER_SUGGESTION = "请使用数字页码，从 1 开始"

    # ========== 转换错误 ==========

    CONVERT_FAILED = "{operation} 失败: {reason}"
    CONVERT_FAILED_SUGGESTION = "请检查源文件是否损坏，或尝试使用不同的参数设置（如降低 DPI、减少页数）"

    PDF_TO_IMAGE_FAILED = "PDF 转图片失败"
    PDF_TO_IMAGE_FAILED_SUGGESTION = "请检查 PDF 文件是否有效。如果文件很大，尝试处理更小的页面范围"

    PDF_TO_WORD_FAILED = "PDF 转 Word 失败"
    PDF_TO_WORD_FAILED_SUGGESTION = "某些 PDF 元素可能无法完美转换到 Word，建议检查转换结果"

    HTML_TO_PDF_FAILED = "HTML 转 PDF 失败"
    HTML_TO_PDF_FAILED_SUGGESTION = "请检查 HTML 文件是否有效，确保 CSS 和资源文件路径正确"

    URL_TO_PDF_FAILED = "网页转 PDF 失败"
    URL_TO_PDF_FAILED_SUGGESTION = "请检查 URL 是否可访问，网络连接是否正常。某些网站可能阻止抓取"

    # ========== OCR 错误 ==========

    OCR_API_ERROR = "OCR API 调用失败"
    OCR_API_ERROR_SUGGESTION = "请检查 API 密钥 (DASHSCOPE_API_KEY) 是否配置正确"

    OCR_TIMEOUT = "OCR 请求超时"
    OCR_TIMEOUT_SUGGESTION = "文件可能过大或网络不稳定。建议减小处理范围或增加超时时间"

    OCR_QUOTA_EXCEEDED = "OCR 配额已用尽"
    OCR_QUOTA_EXCEEDED_SUGGESTION = "请检查账户配额，或稍后重试"

    OCR_INVALID_MODEL = "无效的 OCR 模型: '{model}'"
    OCR_INVALID_MODEL_SUGGESTION = "可用模型: flash (快速), plus (高精度), ocr (标准)"

    # ========== 操作错误 ==========

    OP_MERGE_FAILED = "合并 PDF 失败"
    OP_MERGE_FAILED_SUGGESTION = "请检查所有输入文件是否为有效的 PDF 文件"

    OP_SPLIT_FAILED = "拆分 PDF 失败"
    OP_SPLIT_FAILED_SUGGESTION = "请检查页面范围参数是否正确"

    OP_COMPRESS_FAILED = "压缩 PDF 失败"
    OP_COMPRESS_FAILED_SUGGESTION = "某些 PDF 可能无法进一步压缩，或文件已损坏"

    OP_REPAIR_FAILED = "修复 PDF 失败"
    OP_REPAIR_FAILED_SUGGESTION = "文件损坏可能过于严重，无法自动修复"

    OP_WATERMARK_FAILED = "添加水印失败"
    OP_WATERMARK_FAILED_SUGGESTION = "请检查水印参数是否正确（角度只支持 0/90/180/270 度）"

    OP_CROP_FAILED = "裁剪页面失败"
    OP_CROP_FAILED_SUGGESTION = "请检查裁剪参数是否正确（margin 或 box）"

    OP_RESIZE_FAILED = "调整页面大小失败"
    OP_RESIZE_FAILED_SUGGESTION = "请检查页面尺寸参数是否正确"

    OP_HEADER_FOOTER_FAILED = "添加页眉/页脚失败"
    OP_HEADER_FOOTER_FAILED_SUGGESTION = "请检查文本和参数是否正确"


# ==================== 成功消息模板 ====================

class SuccessMessages:
    """成功消息模板类"""

    GET_INFO = "成功获取 PDF 信息"
    GET_PAGE_COUNT = "成功获取页数"
    GET_METADATA = "成功获取元数据"

    EXTRACT_TEXT = "成功提取文本"
    EXTRACT_PAGES = "成功提取页面"
    EXTRACT_IMAGES = "成功提取图片"

    MERGE_FILES = "成功合并 {count} 个文件"
    SPLIT_PAGES = "成功拆分 PDF"
    DELETE_PAGES = "成功删除页面"

    PDF_TO_IMAGES = "成功转换 PDF 为图片"
    PDF_TO_WORD = "成功转换 PDF 为 Word"
    PDF_TO_HTML = "成功转换 PDF 为 HTML"
    PDF_TO_MD = "成功转换 PDF 为 Markdown"
    HTML_TO_PDF = "成功转换 HTML 为 PDF"
    URL_TO_PDF = "成功转换网页为 PDF"

    ADD_WATERMARK = "成功添加水印"
    CROP_PAGES = "成功裁剪页面"
    RESIZE_PAGES = "成功调整页面大小"
    ADD_HEADER = "成功添加页眉"
    ADD_FOOTER = "成功添加页脚"

    ENCRYPT_PDF = "成功加密 PDF"
    DECRYPT_PDF = "成功解密 PDF"
    PROTECT_PDF = "成功设置 PDF 权限"
    CLEAN_METADATA = "成功清除元数据"

    COMPRESS_PDF = "成功压缩 PDF"
    OPTIMIZE_IMAGES = "成功优化图片"
    REPAIR_PDF = "成功修复 PDF"

    OCR_RECOGNIZE = "成功识别文本"
    OCR_EXTRACT_TABLES = "成功提取表格"
    OCR_ANALYZE_LAYOUT = "成功分析版面"


# ==================== 消息格式化函数 ====================

def format_message(template: str, **kwargs) -> str:
    """
    格式化消息模板

    Args:
        template: 消息模板
        **kwargs: 模板变量

    Returns:
        格式化后的消息

    Examples:
        >>> format_message("文件 '{path}' 不存在", path="test.pdf")
        "文件 'test.pdf' 不存在"
        >>> format_message("页码 {page} 超出范围 (1-{total})", page=10, total=5)
        "页码 10 超出范围 (1-5)"
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        # 缺少模板变量，返回原始模板
        missing = str(e).strip("'")
        return template.replace(f"{{{missing}}}", str(kwargs.get(missing, f"<{missing}>")))
    except (ValueError, TypeError):
        # 格式化错误，返回原始模板
        return template


def build_error_response(
    message: str,
    suggestion: str = None,
    error_code: str = None,
    error_type: str = None,
    **context
) -> Dict[str, Any]:
    """
    构建标准错误响应

    Args:
        message: 错误消息
        suggestion: 修复建议 (可选)
        error_code: 错误码 (可选)
        error_type: 错误类型 (可选)
        **context: 额外上下文信息

    Returns:
        标准错误响应字典
    """
    response = {
        "success": False,
        "error": True,
        "message": message,
    }

    if suggestion:
        response["suggestion"] = suggestion
    if error_code:
        response["error_code"] = error_code
    if error_type:
        response["error_type"] = error_type
    if context:
        response["context"] = context

    return response


def build_success_response(
    data: Dict[str, Any],
    message: str = "操作成功"
) -> Dict[str, Any]:
    """
    构建标准成功响应

    Args:
        data: 返回数据
        message: 成功消息

    Returns:
        标准成功响应字典
    """
    return {
        "success": True,
        "error": False,
        "message": message,
        "data": data,
    }


# ==================== 快捷消息构建函数 ====================

def file_not_found_msg(path: str) -> Dict[str, Any]:
    """文件不存在错误消息"""
    return build_error_response(
        message=format_message(ErrorMessages.FILE_NOT_FOUND, path=path),
        suggestion=ErrorMessages.FILE_NOT_FOUND_SUGGESTION,
        error_type="FileNotFoundError",
        path=path
    )


def invalid_pdf_msg(path: str) -> Dict[str, Any]:
    """无效 PDF 错误消息"""
    return build_error_response(
        message=format_message(ErrorMessages.FILE_INVALID_PDF, path=path),
        suggestion=ErrorMessages.FILE_INVALID_PDF_SUGGESTION,
        error_type="InvalidPDFError",
        path=path
    )


def encrypted_pdf_msg(path: str) -> Dict[str, Any]:
    """加密 PDF 错误消息"""
    return build_error_response(
        message=format_message(ErrorMessages.FILE_ENCRYPTED, path=path),
        suggestion=ErrorMessages.FILE_ENCRYPTED_SUGGESTION,
        error_type="EncryptedPDFError",
        path=path
    )


def page_out_of_range_msg(page: int, total: int) -> Dict[str, Any]:
    """页码超出范围错误消息"""
    return build_error_response(
        message=format_message(ErrorMessages.PAGE_OUT_OF_RANGE, page=page, total=total),
        suggestion=format_message(ErrorMessages.PAGE_OUT_OF_RANGE_SUGGESTION, total=total),
        error_type="PageOutOfRangeError",
        page=page,
        total_pages=total,
        valid_range=f"1-{total}"
    )


def param_out_of_range_msg(param: str, value: Any, min_val: float = None, max_val: float = None) -> Dict[str, Any]:
    """参数超出范围错误消息"""
    range_parts = []
    if min_val is not None:
        range_parts.append(str(min_val))
    if max_val is not None:
        range_parts.append(str(max_val))
    range_str = ",".join(range_parts)

    return build_error_response(
        message=format_message(ErrorMessages.PARAM_OUT_OF_RANGE, param=param, value=value, min=min_val or "", max=max_val or ""),
        suggestion=ErrorMessages.PARAM_OUT_OF_RANGE_SUGGESTION,
        error_type="ParameterOutOfRangeError",
        param=param,
        value=value,
        min=min_val,
        max=max_val
    )


def param_invalid_value_msg(param: str, value: Any, allowed: list) -> Dict[str, Any]:
    """参数值无效错误消息"""
    return build_error_response(
        message=format_message(ErrorMessages.PARAM_INVALID_VALUE, param=param, value=value),
        suggestion=format_message(ErrorMessages.PARAM_INVALID_VALUE_SUGGESTION, values=", ".join(str(v) for v in allowed)),
        error_type="InvalidParameterValueError",
        param=param,
        value=value,
        allowed_values=allowed
    )


# ==================== 导出 ====================

__all__ = [
    # 错误消息模板
    "ErrorMessages",
    # 成功消息模板
    "SuccessMessages",
    # 格式化函数
    "format_message",
    "build_error_response",
    "build_success_response",
    # 快捷消息构建函数
    "file_not_found_msg",
    "invalid_pdf_msg",
    "encrypted_pdf_msg",
    "page_out_of_range_msg",
    "param_out_of_range_msg",
    "param_invalid_value_msg",
]
