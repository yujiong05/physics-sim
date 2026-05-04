# -*- coding: utf-8 -*-
"""
实验占位页：第一步用于导航联调，第四步将替换为完整实验视图。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderExperimentPage(QWidget):
    """
    通用占位：显示实验名称与后续实现提示。
    后续可迁移为 page_projectile / page_collision / page_pendulum 专用模块。
    """

    def __init__(self, experiment_title: str, parent=None):
        super().__init__(parent)
        self._experiment_title = experiment_title
        self._build_ui()

    def _build_ui(self) -> None:
        title = QLabel(self._experiment_title)
        title.setObjectName("placeholderTitle")
        title.setAlignment(Qt.AlignCenter)

        hint = QLabel(
            "此实验的教学讲解、AI 助教、参数面板与 Matplotlib 动画\n"
            "将在第二至第四步逐步实现。\n\n"
            "当前页面仅用于验证侧栏与 QStackedWidget 切换是否正常。"
        )
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 48, 32, 48)
        layout.setSpacing(20)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addStretch()
