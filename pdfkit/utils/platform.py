"""跨平台工具 - 处理不同操作系统的兼容性问题"""

import os
import sys
from pathlib import Path
from typing import Optional
from functools import lru_cache


# ============================================================================
# 平台检测
# ============================================================================

def is_windows() -> bool:
    """检查是否为 Windows 系统"""
    return sys.platform == "win32"


def is_macos() -> bool:
    """检查是否为 macOS 系统"""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """检查是否为 Linux 系统"""
    return sys.platform.startswith("linux")


def get_platform_name() -> str:
    """获取平台名称"""
    if is_windows():
        return "Windows"
    elif is_macos():
        return "macOS"
    elif is_linux():
        return "Linux"
    return sys.platform


# ============================================================================
# 目录路径
# ============================================================================

@lru_cache(maxsize=1)
def get_app_config_dir() -> Path:
    """
    获取应用程序配置目录
    
    - Windows: %APPDATA%\\pdfkit (例如 C:\\Users\\xxx\\AppData\\Roaming\\pdfkit)
    - macOS/Linux: ~/.pdfkit
    """
    if is_windows():
        # 使用 APPDATA 环境变量
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "pdfkit"
        # 回退到用户目录
        return Path.home() / "AppData" / "Roaming" / "pdfkit"
    else:
        return Path.home() / ".pdfkit"


@lru_cache(maxsize=1)
def get_documents_dir() -> Path:
    """
    获取用户文档目录
    
    - Windows: 使用 Shell API 获取真实的 Documents 文件夹路径
    - macOS/Linux: ~/Documents
    """
    if is_windows():
        try:
            import ctypes
            from ctypes import wintypes
            
            # CSIDL_PERSONAL = 0x0005 (Documents folder)
            CSIDL_PERSONAL = 5
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            result = ctypes.windll.shell32.SHGetFolderPathW(
                None, CSIDL_PERSONAL, None, 0, buf
            )
            if result == 0:  # S_OK
                return Path(buf.value)
        except Exception:
            pass
        # 回退到默认路径
        return Path.home() / "Documents"
    else:
        return Path.home() / "Documents"


@lru_cache(maxsize=1)
def get_temp_dir() -> Path:
    """
    获取临时文件目录
    
    - Windows: %TEMP% (例如 C:\\Users\\xxx\\AppData\\Local\\Temp)
    - macOS/Linux: /tmp 或 $TMPDIR
    """
    import tempfile
    return Path(tempfile.gettempdir())


@lru_cache(maxsize=1)
def get_cache_dir() -> Path:
    """
    获取缓存目录
    
    - Windows: %LOCALAPPDATA%\\pdfkit\\cache
    - macOS: ~/Library/Caches/pdfkit
    - Linux: ~/.cache/pdfkit
    """
    if is_windows():
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / "pdfkit" / "cache"
        return Path.home() / "AppData" / "Local" / "pdfkit" / "cache"
    elif is_macos():
        return Path.home() / "Library" / "Caches" / "pdfkit"
    else:
        xdg_cache = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache:
            return Path(xdg_cache) / "pdfkit"
        return Path.home() / ".cache" / "pdfkit"


# ============================================================================
# 可执行文件路径
# ============================================================================

def get_executable_extension() -> str:
    """获取可执行文件扩展名"""
    return ".exe" if is_windows() else ""


def find_executable(name: str, search_paths: Optional[list] = None) -> Optional[Path]:
    """
    查找可执行文件
    
    Args:
        name: 可执行文件名（不含扩展名）
        search_paths: 额外的搜索路径
    
    Returns:
        可执行文件路径，未找到返回 None
    """
    import shutil
    
    # 添加平台扩展名
    if is_windows() and not name.endswith(".exe"):
        name_with_ext = f"{name}.exe"
    else:
        name_with_ext = name
    
    # 首先使用 shutil.which (搜索 PATH)
    result = shutil.which(name_with_ext)
    if result:
        return Path(result)
    
    # 搜索额外路径
    if search_paths:
        for path in search_paths:
            candidate = Path(path) / name_with_ext
            if candidate.exists() and candidate.is_file():
                return candidate
    
    # Windows 特定路径
    if is_windows():
        common_paths = [
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
        ]
        for base in common_paths:
            if base.exists():
                # 递归搜索一层
                for subdir in base.iterdir():
                    if subdir.is_dir():
                        candidate = subdir / name_with_ext
                        if candidate.exists():
                            return candidate
    
    return None


# ============================================================================
# 终端/控制台
# ============================================================================

def setup_windows_console():
    """
    设置 Windows 控制台以支持 ANSI 颜色和 UTF-8
    
    在 Windows 10+ 上启用虚拟终端处理，
    允许终端正确显示 ANSI 转义序列和彩色输出。
    """
    if not is_windows():
        return
    
    try:
        import ctypes
        
        # 启用 ANSI 转义序列支持 (Windows 10+)
        kernel32 = ctypes.windll.kernel32
        
        # STD_OUTPUT_HANDLE = -11
        # STD_ERROR_HANDLE = -12
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        
        for handle_id in (-11, -12):
            handle = kernel32.GetStdHandle(handle_id)
            if handle == -1:
                continue
            
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                # 启用虚拟终端处理
                new_mode = mode.value | 0x0004
                kernel32.SetConsoleMode(handle, new_mode)
        
        # 设置控制台代码页为 UTF-8
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
        
    except Exception:
        # 静默失败，Rich 库有后备方案
        pass


def get_terminal_size() -> tuple:
    """
    获取终端尺寸
    
    Returns:
        (columns, rows) 元组
    """
    import shutil
    size = shutil.get_terminal_size(fallback=(80, 24))
    return (size.columns, size.lines)


# ============================================================================
# 文件系统
# ============================================================================

def get_long_path_prefix() -> str:
    """
    获取 Windows 长路径前缀
    
    Windows 默认路径限制为 260 字符，使用 \\\\?\\ 前缀可支持更长路径
    """
    return "\\\\?\\" if is_windows() else ""


def normalize_path(path: Path) -> Path:
    """
    规范化路径
    
    - Windows: 转换为正斜杠或反斜杠，处理长路径
    - Unix: 展开 ~ 和解析符号链接
    """
    path = path.expanduser()
    
    if is_windows():
        # 解析为绝对路径
        path = path.resolve()
        # 对于超长路径，添加前缀
        path_str = str(path)
        if len(path_str) > 240 and not path_str.startswith("\\\\?\\"):
            path = Path(f"\\\\?\\{path_str}")
    else:
        path = path.resolve()
    
    return path


def get_path_separator() -> str:
    """获取路径分隔符"""
    return "\\" if is_windows() else "/"


# ============================================================================
# 进程管理
# ============================================================================

def get_process_priority_class():
    """
    获取当前进程的优先级类
    
    Returns:
        Windows: 优先级类常量
        Unix: nice 值
    """
    if is_windows():
        try:
            import ctypes
            
            PROCESS_QUERY_INFORMATION = 0x0400
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetCurrentProcess()
            return kernel32.GetPriorityClass(handle)
        except Exception:
            return None
    else:
        return os.nice(0)  # 获取当前 nice 值


# ============================================================================
# 系统信息
# ============================================================================

@lru_cache(maxsize=1)
def get_system_info() -> dict:
    """
    获取系统信息
    
    Returns:
        包含系统信息的字典
    """
    import platform
    
    info = {
        "platform": get_platform_name(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
    }
    
    if is_windows():
        info["windows_edition"] = platform.win32_edition() if hasattr(platform, 'win32_edition') else "Unknown"
        info["is_64bit"] = sys.maxsize > 2**32
    elif is_macos():
        info["macos_version"] = platform.mac_ver()[0]
    
    return info


def check_dependencies() -> dict:
    """
    检查可选依赖的安装状态
    
    Returns:
        {依赖名: (是否安装, 版本或错误信息)}
    """
    dependencies = {}
    
    # 检查 WeasyPrint
    try:
        import weasyprint
        dependencies["weasyprint"] = (True, weasyprint.__version__)
    except ImportError as e:
        dependencies["weasyprint"] = (False, str(e))
    
    # 检查 pdf2image (需要 Poppler)
    try:
        from pdf2image import convert_from_path
        # 尝试找到 Poppler
        poppler_path = find_poppler_path()
        if poppler_path:
            dependencies["pdf2image"] = (True, f"Poppler at {poppler_path}")
        else:
            dependencies["pdf2image"] = (False, "Poppler not found in PATH")
    except ImportError as e:
        dependencies["pdf2image"] = (False, str(e))
    
    # 检查 Playwright
    try:
        from playwright.sync_api import sync_playwright
        import importlib.metadata
        try:
            version = importlib.metadata.version("playwright")
        except Exception:
            version = "installed"
        dependencies["playwright"] = (True, version)
    except ImportError as e:
        dependencies["playwright"] = (False, str(e))
    
    return dependencies


def find_poppler_path() -> Optional[Path]:
    """
    查找 Poppler 安装路径
    
    Returns:
        Poppler bin 目录路径，未找到返回 None
    """
    # 首先检查 PATH
    pdftoppm = find_executable("pdftoppm")
    if pdftoppm:
        return pdftoppm.parent
    
    if is_windows():
        # Windows 常见安装路径
        common_paths = [
            Path("C:\\Program Files\\poppler\\Library\\bin"),
            Path("C:\\Program Files\\poppler-24.08.0\\Library\\bin"),
            Path("C:\\poppler\\bin"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "poppler" / "Library" / "bin",
        ]
        for path in common_paths:
            if (path / "pdftoppm.exe").exists():
                return path
    elif is_macos():
        # Homebrew 安装路径
        homebrew_paths = [
            Path("/opt/homebrew/bin"),  # Apple Silicon
            Path("/usr/local/bin"),      # Intel
        ]
        for path in homebrew_paths:
            if (path / "pdftoppm").exists():
                return path
    
    return None


# ============================================================================
# 初始化
# ============================================================================

def init_platform():
    """
    初始化平台特定设置
    
    应在程序启动时调用
    """
    if is_windows():
        setup_windows_console()
    
    # 确保配置目录存在
    config_dir = get_app_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)


# 在模块加载时自动初始化
if is_windows():
    setup_windows_console()
