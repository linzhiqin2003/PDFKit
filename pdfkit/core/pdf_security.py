"""PDF 安全服务 - 核心业务逻辑

此模块包含与 PDF 安全相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, Union, List
from dataclasses import dataclass

import pikepdf


# ==================== 数据模型 ====================

@dataclass
class EncryptResult:
    """加密结果"""
    output_path: str
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "success": self.success,
        }


@dataclass
class DecryptResult:
    """解密结果"""
    output_path: str
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "success": self.success,
        }


@dataclass
class ProtectResult:
    """权限设置结果"""
    output_path: str
    restrictions: List[str]
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "restrictions": self.restrictions,
            "success": self.success,
        }


@dataclass
class CleanMetadataResult:
    """清除元数据结果"""
    output_path: str
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "output_path": str(self.output_path),
            "success": self.success,
        }


# ==================== 自定义异常 ====================

class PDFSecurityError(Exception):
    """PDF 安全错误"""
    pass


class PasswordError(PDFSecurityError):
    """密码错误"""
    pass


class EncryptedPDFError(PDFSecurityError):
    """PDF 加密错误"""
    pass


# ==================== 核心函数 ====================

def encrypt_pdf(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    password: str,
) -> EncryptResult:
    """
    加密 PDF 文件

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        password: 设置密码

    Returns:
        EncryptResult: 加密结果
    """
    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        # 检查是否覆盖输入文件
        overwrite_input = (file_path == output_path)

        # 使用 pikepdf 进行加密
        pdf = pikepdf.open(file_path, allow_overwriting_input=overwrite_input)

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存并加密
        pdf.save(output_path, encryption=pikepdf.Encryption(owner=password, user=password))
        pdf.close()

        return EncryptResult(
            output_path=str(output_path),
            success=True,
        )

    except Exception as e:
        raise PDFSecurityError(f"加密失败: {e}")


def decrypt_pdf(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    password: str,
) -> DecryptResult:
    """
    解密 PDF 文件

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        password: PDF 密码

    Returns:
        DecryptResult: 解密结果
    """
    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        # 检查是否覆盖输入文件
        overwrite_input = (file_path == output_path)

        # 使用 pikepdf 打开并解密
        pdf = pikepdf.open(file_path, password=password, allow_overwriting_input=overwrite_input)

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存不加密
        pdf.save(output_path, encryption=pikepdf.Encryption(owner='', user=''))
        pdf.close()

        return DecryptResult(
            output_path=str(output_path),
            success=True,
        )

    except pikepdf.PasswordError:
        raise PasswordError("密码错误")
    except Exception as e:
        raise PDFSecurityError(f"解密失败: {e}")


def protect_pdf(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
    owner_password: str,
    user_password: str = "",
    no_print: bool = False,
    no_copy: bool = False,
    no_modify: bool = False,
) -> ProtectResult:
    """
    设置 PDF 权限

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径
        owner_password: 所有者密码
        user_password: 用户密码（可选）
        no_print: 禁止打印
        no_copy: 禁止复制
        no_modify: 禁止修改

    Returns:
        ProtectResult: 设置结果
    """
    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        # 检查是否覆盖输入文件
        overwrite_input = (file_path == output_path)

        # 使用 pikepdf 设置权限
        pdf = pikepdf.open(file_path, allow_overwriting_input=overwrite_input)

        # 设置权限 (使用新版 pikepdf API)
        permissions = pikepdf.Permissions(
            accessibility=True,
            extract=not no_copy,           # 禁止复制 = 禁止提取
            modify_annotation=not no_modify,
            modify_assembly=not no_modify,
            modify_form=not no_modify,
            modify_other=not no_modify,
            print_lowres=not no_print,
            print_highres=not no_print,
        )

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存
        pdf.save(
            output_path,
            encryption=pikepdf.Encryption(
                owner=owner_password,
                user=user_password if user_password else "",
                allow=permissions
            )
        )
        pdf.close()

        # 收集限制列表
        restrictions = []
        if no_print:
            restrictions.append("禁止打印")
        if no_copy:
            restrictions.append("禁止复制")
        if no_modify:
            restrictions.append("禁止修改")

        return ProtectResult(
            output_path=str(output_path),
            restrictions=restrictions,
            success=True,
        )

    except Exception as e:
        raise PDFSecurityError(f"设置权限失败: {e}")


def clean_metadata(
    file_path: Union[str, Path],
    output_path: Union[str, Path],
) -> CleanMetadataResult:
    """
    清除 PDF 元数据

    删除可能包含敏感信息的元数据，如：
    - 作者
    - 创建程序
    - 创建/修改日期
    - 标题、主题、关键词

    Args:
        file_path: PDF 文件路径
        output_path: 输出文件路径

    Returns:
        CleanMetadataResult: 清除结果
    """
    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        # 检查是否覆盖输入文件
        overwrite_input = (file_path == output_path)

        # 使用 pikepdf
        try:
            pdf = pikepdf.open(file_path, allow_overwriting_input=overwrite_input)
        except pikepdf.PasswordError:
            raise EncryptedPDFError("PDF 文件已加密，需要密码才能清除元数据")

        # 清除文档信息字典 (Document Info Dictionary)
        # 使用 del_info() 方法或逐个删除
        try:
            with pdf.open_metadata() as meta:
                # 清除 XMP 元数据
                meta.clear()
        except Exception:
            pass  # 有些 PDF 可能没有 XMP 元数据

        # 清除 docinfo
        keys_to_delete = list(pdf.docinfo.keys())
        for key in keys_to_delete:
            try:
                del pdf.docinfo[key]
            except Exception:
                pass

        # 尝试删除 /Metadata 对象
        try:
            if hasattr(pdf, 'Root') and pdf.Root is not None:
                if '/Metadata' in pdf.Root:
                    del pdf.Root['/Metadata']
        except Exception:
            pass

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存
        pdf.save(output_path)
        pdf.close()

        return CleanMetadataResult(
            output_path=str(output_path),
            success=True,
        )

    except EncryptedPDFError:
        raise
    except Exception as e:
        raise PDFSecurityError(f"清除元数据失败: {e}")
