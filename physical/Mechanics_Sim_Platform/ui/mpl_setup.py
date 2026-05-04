# -*- coding: utf-8 -*-
"""Matplotlib 中文与全局显示配置（多页面复用）。"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib
from matplotlib import font_manager

_MPL_FONT_CONFIGURED = False


def configure_matplotlib_chinese_font() -> None:
    """
    修复中文标题/图例显示为方框：注册 Windows 微软雅黑等，并关闭 Unicode 负号乱码。
    """
    global _MPL_FONT_CONFIGURED
    if _MPL_FONT_CONFIGURED:
        return
    matplotlib.rcParams["axes.unicode_minus"] = False

    windir = os.environ.get("WINDIR", r"C:\Windows")
    for name in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf"):
        fp = Path(windir) / "Fonts" / name
        if fp.is_file():
            try:
                font_manager.fontManager.addfont(str(fp))
            except (OSError, ValueError):
                continue

    matplotlib.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "Microsoft YaHei UI",
        "SimHei",
        "DengXian",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    matplotlib.rcParams["font.family"] = "sans-serif"
    _MPL_FONT_CONFIGURED = True
