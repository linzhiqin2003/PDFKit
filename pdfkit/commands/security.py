"""PDF 安全命令"""

from pathlib import Path
from typing import Optional
import typer
import fitz  # PyMuPDF
import pikepdf

from ..utils.console import (
    console, print_success, print_error, print_info, Icons,
    print_security_warning, print_structured_error, confirm
)
from ..utils.validators import validate_pdf_file
from ..utils.file_utils import resolve_path

# 创建 security 子应用
app = typer.Typer(help="安全操作")


# ============================================================================
# 加密 PDF
# ============================================================================

@app.command("encrypt")
def encrypt_pdf(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        help="设置密码",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
):
    """
    加密 PDF 文件

    示例:
        pdfkit security encrypt document.pdf -p mypassword
        pdfkit security encrypt document.pdf -p mypassword -o encrypted.pdf
    """
    if not validate_pdf_file(file):
        print_structured_error(
            title="无效的 PDF 文件",
            error_message=f"文件不存在或不是有效的 PDF: {file}",
            causes=[
                "文件路径拼写错误",
                "文件已损坏",
                "文件格式不是 PDF"
            ],
            suggestions=[
                "检查文件路径是否正确",
                "使用 pdfkit info 命令检查文件状态"
            ]
        )
        raise typer.Exit(1)

    # 显示安全警告
    print_security_warning(
        operation="PDF 加密",
        risk_level="medium",
        details="您即将对 PDF 文件进行加密。加密后的文件需要密码才能打开。",
        risks=[
            "忘记密码将无法打开 PDF",
            "某些 PDF 查看器可能不支持加密",
            "密码应妥善保管，避免泄露"
        ],
        confirmation_required=False
    )

    try:
        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}_encrypted{file.suffix}")
        else:
            output = resolve_path(output)

        # 检查是否覆盖输入文件
        overwrite_input = (resolve_path(file) == output)

        # 使用 pikepdf 进行加密
        pdf = pikepdf.open(file, allow_overwriting_input=overwrite_input)

        # 保存并加密
        pdf.save(output, encryption=pikepdf.Encryption(owner=password, user=password))
        pdf.close()

        print_success(f"PDF 已加密: [path]{output}[/]")
        print_info("请记住您设置的密码，它不会再次显示")

    except Exception as e:
        print_error(f"加密失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# 解密 PDF
# ============================================================================

@app.command("decrypt")
def decrypt_pdf(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        help="PDF 密码",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
):
    """
    解密 PDF 文件

    示例:
        pdfkit security decrypt encrypted.pdf -p mypassword
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}_decrypted{file.suffix}")
        else:
            output = resolve_path(output)

        # 检查是否覆盖输入文件
        overwrite_input = (resolve_path(file) == output)

        # 使用 pikepdf 打开并解密
        pdf = pikepdf.open(file, password=password, allow_overwriting_input=overwrite_input)

        # 保存不加密
        pdf.save(output, encryption=pikepdf.Encryption(owner='', user=''))
        pdf.close()

        print_success(f"PDF 已解密: [path]{output}[/]")

    except pikepdf.PasswordError:
        print_structured_error(
            title="密码错误",
            error_message="无法使用提供的密码打开 PDF",
            causes=[
                "密码大小写不正确",
                "使用了所有者密码而非用户密码",
                "密码中包含特殊字符（如空格、引号）",
                "文件可能已损坏"
            ],
            suggestions=[
                "检查密码大小写是否正确",
                "确认使用的是打开密码（用户密码）",
                "尝试复制粘贴密码，避免手动输入错误",
                "使用 pdfkit info 命令检查文件状态"
            ]
        )
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"解密失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# 设置权限
# ============================================================================

@app.command("protect")
def protect_pdf(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    owner_password: str = typer.Option(
        ...,
        "--owner-password",
        "-O",
        help="所有者密码",
    ),
    user_password: str = typer.Option(
        "",
        "--user-password",
        "-U",
        help="用户密码（可选）",
    ),
    no_print: bool = typer.Option(
        False,
        "--no-print",
        help="禁止打印",
    ),
    no_copy: bool = typer.Option(
        False,
        "--no-copy",
        help="禁止复制",
    ),
    no_modify: bool = typer.Option(
        False,
        "--no-modify",
        help="禁止修改",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
):
    """
    设置 PDF 权限

    示例:
        # 禁止打印
        pdfkit security protect document.pdf -O ownerpass --no-print

        # 禁止打印和复制
        pdfkit security protect document.pdf -O ownerpass --no-print --no-copy

        # 同时设置用户密码
        pdfkit security protect document.pdf -O ownerpass -U userpass --no-modify
    """
    if not validate_pdf_file(file):
        print_structured_error(
            title="无效的 PDF 文件",
            error_message=f"文件不存在或不是有效的 PDF: {file}",
            causes=[
                "文件路径拼写错误",
                "文件已损坏",
                "文件格式不是 PDF"
            ],
            suggestions=[
                "检查文件路径是否正确",
                "使用 pdfkit info 命令检查文件状态"
            ]
        )
        raise typer.Exit(1)

    # 显示安全警告
    restrictions = []
    if no_print:
        restrictions.append("禁止打印")
    if no_copy:
        restrictions.append("禁止复制")
    if no_modify:
        restrictions.append("禁止修改")

    if restrictions:
        print_security_warning(
            operation="PDF 权限修改",
            risk_level="medium",
            details=f"您正在修改 PDF 的访问权限，将限制: {', '.join(restrictions)}",
            risks=[
                "某些 PDF 查看器可能不遵守权限设置",
                "权限设置可能导致文件在某些设备上无法正常打开",
                "权限保护并非绝对，专业工具可能绕过限制",
                "无法撤销权限（除非有原始备份或所有者密码）"
            ],
            confirmation_required=False
        )

    try:
        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}_protected{file.suffix}")
        else:
            output = resolve_path(output)

        # 检查是否覆盖输入文件
        overwrite_input = (resolve_path(file) == output)

        # 使用 pikepdf 设置权限
        pdf = pikepdf.open(file, allow_overwriting_input=overwrite_input)

        # 设置权限 (使用新版 pikepdf API)
        # 新版参数: accessibility, extract, modify_annotation, modify_assembly,
        #          modify_form, modify_other, print_lowres, print_highres
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

        # 保存
        pdf.save(
            output,
            encryption=pikepdf.Encryption(
                owner=owner_password,
                user=user_password if user_password else "",
                allow=permissions
            )
        )
        pdf.close()

        print_success(f"权限设置完成: [path]{output}[/]")

        restrictions = []
        if no_print:
            restrictions.append("禁止打印")
        if no_copy:
            restrictions.append("禁止复制")
        if no_modify:
            restrictions.append("禁止修改")

        if restrictions:
            print_info(f"限制: [warning]{', '.join(restrictions)}[/]")
        else:
            print_info("已设置密码保护（无其他限制）")

    except Exception as e:
        print_error(f"设置权限失败: {e}")
        raise typer.Exit(1)


# ============================================================================
# 清除元数据
# ============================================================================

@app.command("clean-meta")
def clean_metadata(
    file: Path = typer.Argument(
        ...,
        help="PDF 文件路径",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
):
    """
    清除 PDF 元数据

    删除可能包含敏感信息的元数据，如：
    - 作者
    - 创建程序
    - 创建/修改日期
    - 标题、主题、关键词

    示例:
        pdfkit security clean-meta document.pdf
    """
    if not validate_pdf_file(file):
        print_error(f"文件不存在或不是有效的 PDF: {file}")
        raise typer.Exit(1)

    try:
        # 确定输出路径
        if output is None:
            output = resolve_path(file.parent / f"{file.stem}_cleaned{file.suffix}")
        else:
            output = resolve_path(output)

        # 检查是否覆盖输入文件
        overwrite_input = (resolve_path(file) == output)

        # 使用 pikepdf
        try:
            pdf = pikepdf.open(file, allow_overwriting_input=overwrite_input)
        except pikepdf.PasswordError:
            print_error(f"PDF 文件已加密，需要密码才能清除元数据")
            print_info("提示: 使用 pdfkit security decrypt <文件> -p <密码> 解密后再操作")
            raise typer.Exit(1)

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

        # 保存
        pdf.save(output)
        pdf.close()

        print_success(f"元数据已清除: [path]{output}[/]")

    except Exception as e:
        print_error(f"清除元数据失败: {e}")
        raise typer.Exit(1)
