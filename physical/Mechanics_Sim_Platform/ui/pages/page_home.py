# -*- coding: utf-8 -*-
"""
主页：项目简介与后续开发步骤说明。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class HomePage(QWidget):
    """应用入口页，展示平台定位与分步实施路线。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        title = QLabel("力学仿真教学平台")
        title.setObjectName("homeTitle")
        title.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        body = QLabel(
            "<p><b>定位：</b>面向教学的桌面客户端，集成知识讲解、交互控件与物理过程动画。</p>"
            "<p><b>技术栈：</b>PyQt5 纯代码界面；NumPy / SciPy（solve_ivp RK4）；"
            "Matplotlib 嵌入画布；耗时任务使用 QThread + pyqtSignal，避免阻塞主界面线程。</p>"
            "<hr/>"
            "<p><b>实施路线：</b></p>"
            "<ol>"
            "<li>第一步（当前）：主窗口骨架、侧栏导航、全局明亮样式。</li>"
            "<li>第二步：engine/ 物理计算模块，仅返回数组，不含绘图。</li>"
            "<li>第三步：AI 助教 Worker（QThread）与流式回复集成。</li>"
            "<li>第四步：三个实验页的仿真控制与 QTimer + Matplotlib 动画。</li>"
            "</ol>"
            "<p>请从左侧导航进入各实验占位页；完整交互界面将在后续步骤替换。</p>"
        )
        body.setWordWrap(True)
        body.setTextFormat(Qt.RichText)
        body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        body.setOpenExternalLinks(False)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(16)
        inner_layout.addWidget(title)
        inner_layout.addWidget(body)
        inner_layout.addStretch()
        scroll.setWidget(inner)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.addWidget(scroll)
