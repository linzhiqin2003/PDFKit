"""PDF 安全服务 - 核心业务逻辑

此模块包含与 PDF 安全相关的核心功能，
可被 CLI 命令和 MCP 工具共同调用。
"""

from pathlib import Path
from typing import Optional, Union, List
from dataclasses import dataclass

import pikepdf


# ==================== 密码验证辅助函数 ====================

def _validate_password(password: str, param_name: str = "password") -> None:
    """
    验证密码参数

    Args:
        password: 密码字符串
        param_name: 参数名（用于错误消息）

    Raises:
        PasswordError: 密码无效时
    """
    if not password or password.strip() == "":
        raise PasswordError(
            f"{param_name} 不能为空。"
            f"空密码无法提供安全保护。请提供至少 4 个字符的密码。"
        )

    if len(password) < 4:
        raise PasswordError(
            f"{param_name} 长度必须至少为 4 个字符。"
            f"当前长度: {len(password)}"
        )


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
        password: 设置密码（至少 4 个字符）

    Returns:
        EncryptResult: 加密结果

    Raises:
        PasswordError: 密码无效时
        PDFSecurityError: 加密失败时
    """
    # ========== 密码验证 ==========
    _validate_password(password, "password")

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
        password: PDF 密码（必须正确）

    Returns:
        DecryptResult: 解密结果

    Raises:
        PasswordError: 密码为空或错误时
        PDFSecurityError: 解密失败时
    """
    # ========== 密码验证 ==========
    # 注意：解密时允许空密码（有些 PDF 可能没有密码），但需要明确处理
    # 如果用户明确传入空字符串，给出提示
    if password == "":
        # 尝试不使用密码打开
        pass  # 在下面尝试时处理

    file_path = Path(file_path)
    output_path = Path(output_path)

    try:
        # 检查是否覆盖输入文件
        overwrite_input = (file_path == output_path)

        # 首先检查文件是否加密
        try:
            # 尝试不使用密码打开
            test_pdf = pikepdf.open(file_path, allow_overwriting_input=overwrite_input)
            is_encrypted = test_pdf.is_encrypted
            test_pdf.close()
        except pikepdf.PasswordError:
            # 需要密码才能打开，说明文件已加密
            is_encrypted = True

        # 如果文件已加密但未提供密码
        if is_encrypted and not password:
            raise PasswordError(
                "PDF 文件已加密，需要提供正确的密码才能解密。"
            )

        # 使用 pikepdf 打开并解密
        # 注意：如果密码错误，pikepdf 会抛出 PasswordError
        pdf = pikepdf.open(file_path, password=password if password else None, allow_overwriting_input=overwrite_input)

        # 检查解密后的文件是否真的加密了
        if not pdf.is_encrypted:
            pdf.close()
            raise PasswordError(
                "PDF 文件未加密，无需解密。"
                "如果这是预期行为，请直接复制文件即可。"
            )

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
        raise PasswordError(
            "密码错误或 PDF 文件已加密。"
            "请提供正确的密码。"
        )
    except PasswordError:
        raise
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
        owner_password: 所有者密码（至少 4 个字符）
        user_password: 用户密码（可选）
        no_print: 禁止打印
        no_copy: 禁止复制
        no_modify: 禁止修改

    Returns:
        ProtectResult: 设置结果

    Raises:
        PasswordError: 密码无效时
        PDFSecurityError: 设置权限失败时
    """
    # ========== 密码验证 ==========
    # owner_password 是必需的且不能为空
    _validate_password(owner_password, "owner_password")

    # user_password 如果提供，也必须验证
    if user_password and user_password.strip():
        if len(user_password) < 4:
            raise PasswordError(
                f"user_password 长度必须至少为 4 个字符。"
                f"当前长度: {len(user_password)}"
            )

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
