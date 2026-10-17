#!/usr/bin/env python3
"""cover_styles.py：封面风格参数表 —— v4 兼容垫片。

v3.3.0 的 cover_styles.py 已迁入 gzhkit.visual.styles（干净重写）。
本文件仅做重导出，保持 `from cover_styles import DESIGNER_STYLES` 等
旧 import 写法可用；`python3 cover_styles.py` 仍打印风格一览。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit.visual.styles import (  # noqa: F401,E402
    DESIGNER_STYLES,
    TONE_TO_STYLE,
    list_styles,
)

if __name__ == '__main__':
    list_styles()
