"""PDFKit 入口点"""

import sys

from .cli import run


def main():
    """主入口"""
    try:
        run()
    except KeyboardInterrupt:
        # 处理 Ctrl+C
        print("\n操作已取消")
        sys.exit(130)
    except Exception as e:
        # 处理其他异常
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
