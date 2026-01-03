"""MCP 工具错误码和错误详情定义

提供统一的错误码体系和错误响应格式。
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class ErrorCode(str, Enum):
    """MCP 工具错误码

    格式: ERR_<模块>_<具体错误>_<数字编号>

    模块:
        FILE - 文件操作错误
        PARAM - 参数验证错误
        PAGE - 页面相关错误
        CONVERT - 格式转换错误
        OCR - OCR 识别错误
        OP - 操作执行错误
    """

    # 文件错误 (ERR_FILE_xxx)
    FILE_NOT_FOUND = "ERR_FILE_001"
    FILE_INVALID_PDF = "ERR_FILE_002"
    FILE_ENCRYPTED = "ERR_FILE_003"
    FILE_PERMISSION_DENIED = "ERR_FILE_004"
    FILE_OUTPUT_DIR_INVALID = "ERR_FILE_005"

    # 参数错误 (ERR_PARAM_xxx)
    PARAM_INVALID_VALUE = "ERR_PARAM_001"
    PARAM_OUT_OF_RANGE = "ERR_PARAM_002"
    PARAM_MISSING_REQUIRED = "ERR_PARAM_003"
    PARAM_INVALID_FORMAT = "ERR_PARAM_004"

    # 页面错误 (ERR_PAGE_xxx)
    PAGE_OUT_OF_RANGE = "ERR_PAGE_001"
    PAGE_INVALID_RANGE = "ERR_PAGE_002"
    PAGE_INVALID_NUMBER = "ERR_PAGE_003"

    # 转换错误 (ERR_CONVERT_xxx)
    CONVERT_PDF_TO_IMAGE_FAILED = "ERR_CONVERT_001"
    CONVERT_PDF_TO_WORD_FAILED = "ERR_CONVERT_002"
    CONVERT_PDF_TO_HTML_FAILED = "ERR_CONVERT_003"
    CONVERT_PDF_TO_MD_FAILED = "ERR_CONVERT_004"
    CONVERT_HTML_TO_PDF_FAILED = "ERR_CONVERT_005"
    CONVERT_URL_TO_PDF_FAILED = "ERR_CONVERT_006"
    CONVERT_IMAGES_TO_PDF_FAILED = "ERR_CONVERT_007"

    # OCR 错误 (ERR_OCR_xxx)
    OCR_API_ERROR = "ERR_OCR_001"
    OCR_TIMEOUT = "ERR_OCR_002"
    OCR_QUOTA_EXCEEDED = "ERR_OCR_003"
    OCR_INVALID_MODEL = "ERR_OCR_004"

    # 操作错误 (ERR_OP_xxx)
    OP_MERGE_FAILED = "ERR_OP_001"
    OP_SPLIT_FAILED = "ERR_OP_002"
    OP_COMPRESS_FAILED = "ERR_OP_003"
    OP_REPAIR_FAILED = "ERR_OP_004"
    OP_WATERMARK_FAILED = "ERR_OP_005"
    OP_CROP_FAILED = "ERR_OP_006"
    OP_RESIZE_FAILED = "ERR_OP_007"
    OP_HEADER_FOOTER_FAILED = "ERR_OP_008"


@dataclass
class ErrorDetail:
    """错误详情数据类"""

    code: ErrorCode
    type: str
    message: str
    suggestion: Optional[str] = None
    context: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "success": False,
            "error": True,
            "error_code": self.code.value,
            "error_type": self.type,
            "message": self.message,
        }
        if self.suggestion:
            result["suggestion"] = self.suggestion
        if self.context:
            result["context"] = self.context
        return result


# 预定义错误详情模板

def create_error_detail(
    code: ErrorCode,
    error_type: str,
    message: str,
    suggestion: str = None,
    **context
) -> ErrorDetail:
    """创建错误详情

    Args:
        code: 错误码
        error_type: 错误类型名称
        message: 错误消息
        suggestion: 建议修复方案
        **context: 额外上下文信息

    Returns:
        ErrorDetail 对象
    """
    return ErrorDetail(
        code=code,
        type=error_type,
        message=message,
        suggestion=suggestion,
        context=context if context else None
    )


# 快速创建函数

def file_not_found(path: str) -> ErrorDetail:
    """文件不存在错误"""
    return ErrorDetail(
        code=ErrorCode.FILE_NOT_FOUND,
        type="FileNotFoundError",
        message=f"文件不存在: {path}",
        suggestion="请检查文件路径是否正确，确保文件扩展名正确（.pdf）",
        context={"path": path}
    )


def invalid_pdf(path: str) -> ErrorDetail:
    """无效 PDF 文件错误"""
    return ErrorDetail(
        code=ErrorCode.FILE_INVALID_PDF,
        type="InvalidPDFError",
        message=f"不是有效的 PDF 文件: {path}",
        suggestion="请确保文件是 PDF 格式且未损坏",
        context={"path": path}
    )


def encrypted_pdf(path: str) -> ErrorDetail:
    """PDF 加密错误"""
    return ErrorDetail(
        code=ErrorCode.FILE_ENCRYPTED,
        type="EncryptedPDFError",
        message=f"PDF 文件已加密: {path}",
        suggestion="请使用 pdfkit_decrypt_pdf 解密后再操作",
        context={"path": path}
    )


def page_out_of_range(page: int, total: int) -> ErrorDetail:
    """页码超出范围错误"""
    return ErrorDetail(
        code=ErrorCode.PAGE_OUT_OF_RANGE,
        type="PageOutOfRangeError",
        message=f"页码 {page} 超出范围 (1-{total})",
        suggestion=f"请使用有效页码: 1 到 {total}",
        context={"page": page, "total_pages": total, "valid_range": f"1-{total}"}
    )


def invalid_page_range(range_str: str) -> ErrorDetail:
    """无效的页面范围格式错误"""
    return ErrorDetail(
        code=ErrorCode.PAGE_INVALID_RANGE,
        type="InvalidPageRangeError",
        message=f"页面范围格式无效: {range_str}",
        suggestion="正确格式: '1-3', '5', '1-3,5,7-9'",
        context={"range": range_str, "examples": ["1-3", "5", "1-3,5,7-9"]}
    )


def param_out_of_range(param: str, value: Any, min_val: float = None, max_val: float = None) -> ErrorDetail:
    """参数超出范围错误"""
    range_desc = []
    if min_val is not None:
        range_desc.append(f"最小值 {min_val}")
    if max_val is not None:
        range_desc.append(f"最大值 {max_val}")

    return ErrorDetail(
        code=ErrorCode.PARAM_OUT_OF_RANGE,
        type="ParameterOutOfRangeError",
        message=f"参数 '{param}' 的值 '{value}' 超出范围",
        suggestion=f"请调整参数值到有效范围 ({', '.join(range_desc)})",
        context={"param": param, "value": value, "min": min_val, "max": max_val}
    )


def param_invalid_value(param: str, value: Any, allowed: list) -> ErrorDetail:
    """参数值无效错误"""
    return ErrorDetail(
        code=ErrorCode.PARAM_INVALID_VALUE,
        type="InvalidParameterValueError",
        message=f"参数 '{param}' 的值 '{value}' 无效",
        suggestion=f"允许的值: {', '.join(str(v) for v in allowed)}",
        context={"param": param, "value": value, "allowed_values": allowed}
    )


def param_invalid_format(param: str, value: Any, expected: str) -> ErrorDetail:
    """参数格式无效错误"""
    return ErrorDetail(
        code=ErrorCode.PARAM_INVALID_FORMAT,
        type="InvalidParameterFormatError",
        message=f"参数 '{param}' 的格式无效: {value}",
        suggestion=f"期望格式: {expected}",
        context={"param": param, "value": value, "expected_format": expected}
    )


def operation_failed(op_name: str, reason: str = None) -> ErrorDetail:
    """操作执行失败错误"""
    message = f"{op_name} 失败"
    if reason:
        message += f": {reason}"

    return ErrorDetail(
        code=ErrorCode.OP_MERGE_FAILED,  # 默认，可覆盖
        type="OperationFailedError",
        message=message,
        suggestion="请检查输入文件是否有效，或尝试使用不同的参数设置",
        context={"operation": op_name, "reason": reason}
    )


# 错误码到错误类型的映射

ERROR_TYPE_MAPPING: Dict[ErrorCode, str] = {
    # 文件错误
    ErrorCode.FILE_NOT_FOUND: "FileNotFoundError",
    ErrorCode.FILE_INVALID_PDF: "InvalidPDFError",
    ErrorCode.FILE_ENCRYPTED: "EncryptedPDFError",
    ErrorCode.FILE_PERMISSION_DENIED: "PermissionDeniedError",
    ErrorCode.FILE_OUTPUT_DIR_INVALID: "InvalidOutputDirectoryError",

    # 参数错误
    ErrorCode.PARAM_INVALID_VALUE: "InvalidParameterValueError",
    ErrorCode.PARAM_OUT_OF_RANGE: "ParameterOutOfRangeError",
    ErrorCode.PARAM_MISSING_REQUIRED: "MissingRequiredParameterError",
    ErrorCode.PARAM_INVALID_FORMAT: "InvalidParameterFormatError",

    # 页面错误
    ErrorCode.PAGE_OUT_OF_RANGE: "PageOutOfRangeError",
    ErrorCode.PAGE_INVALID_RANGE: "InvalidPageRangeError",
    ErrorCode.PAGE_INVALID_NUMBER: "InvalidPageNumberError",

    # 转换错误
    ErrorCode.CONVERT_PDF_TO_IMAGE_FAILED: "PDFToImageConversionError",
    ErrorCode.CONVERT_PDF_TO_WORD_FAILED: "PDFToWordConversionError",
    ErrorCode.CONVERT_PDF_TO_HTML_FAILED: "PDFToHTMLConversionError",
    ErrorCode.CONVERT_PDF_TO_MD_FAILED: "PDFToMarkdownConversionError",
    ErrorCode.CONVERT_HTML_TO_PDF_FAILED: "HTMLToPDFConversionError",
    ErrorCode.CONVERT_URL_TO_PDF_FAILED: "URLToPDFConversionError",
    ErrorCode.CONVERT_IMAGES_TO_PDF_FAILED: "ImagesToPDFConversionError",

    # OCR 错误
    ErrorCode.OCR_API_ERROR: "OCRAPIError",
    ErrorCode.OCR_TIMEOUT: "OCRTimeoutError",
    ErrorCode.OCR_QUOTA_EXCEEDED: "OCRQuotaExceededError",
    ErrorCode.OCR_INVALID_MODEL: "InvalidOCRModelError",

    # 操作错误
    ErrorCode.OP_MERGE_FAILED: "MergeOperationError",
    ErrorCode.OP_SPLIT_FAILED: "SplitOperationError",
    ErrorCode.OP_COMPRESS_FAILED: "CompressOperationError",
    ErrorCode.OP_REPAIR_FAILED: "RepairOperationError",
    ErrorCode.OP_WATERMARK_FAILED: "WatermarkOperationError",
    ErrorCode.OP_CROP_FAILED: "CropOperationError",
    ErrorCode.OP_RESIZE_FAILED: "ResizeOperationError",
    ErrorCode.OP_HEADER_FOOTER_FAILED: "HeaderFooterOperationError",
}


def get_error_type(code: ErrorCode) -> str:
    """获取错误码对应的错误类型

    Args:
        code: 错误码

    Returns:
        错误类型字符串
    """
    return ERROR_TYPE_MAPPING.get(code, "UnknownError")


# 导出所有错误码和函数

__all__ = [
    # 错误码枚举
    "ErrorCode",
    # 错误详情类
    "ErrorDetail",
    "create_error_detail",
    # 快速创建函数
    "file_not_found",
    "invalid_pdf",
    "encrypted_pdf",
    "page_out_of_range",
    "invalid_page_range",
    "param_out_of_range",
    "param_invalid_value",
    "param_invalid_format",
    "operation_failed",
    # 工具函数
    "get_error_type",
    "ERROR_TYPE_MAPPING",
]
