# -*- coding: utf-8 -*-
"""
力学仿真教学平台 — 程序入口与主窗口。
左侧 QListWidget 导航 + 右侧 QStackedWidget 多页切换；全局明亮学术风 QSS。
"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QShortcut,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.page_collision import PageCollision
from ui.page_pendulum import PagePendulum
from ui.page_projectile import PageProjectile
from ui.pages.page_home import HomePage


def apply_global_style(app: QApplication) -> None:
    """
    应用全局 Qt Style Sheets（浅色、扁平、圆角控件）。
    说明：QSS 不支持 CSS 的 box-shadow；层次感通过边框与背景色差模拟，
    若需真实阴影可在后续自定义卡片组件上使用 QGraphicsDropShadowEffect。
    """
    app.setStyle("Fusion")

    palette = app.palette()
    palette.setColor(palette.Window, QColor("#f5f7fb"))
    palette.setColor(palette.WindowText, QColor("#1f2937"))
    palette.setColor(palette.Base, QColor("#ffffff"))
    palette.setColor(palette.AlternateBase, QColor("#eef2f8"))
    palette.setColor(palette.Button, QColor("#ffffff"))
    palette.setColor(palette.ButtonText, QColor("#1f2937"))
    palette.setColor(palette.Highlight, QColor("#3b82f6"))
    palette.setColor(palette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    app.setStyleSheet(
        """
        QWidget {
            font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
            font-size: 11pt;
            color: #1f2937;
            background-color: #f5f7fb;
        }
        QMainWindow {
            background-color: #f5f7fb;
        }
        /* 侧栏容器：白底 + 细边框模拟轻微层次（非阴影） */
        QFrame#sidebar {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
        }
        QLabel#sidebarBrand {
            font-size: 13pt;
            font-weight: 600;
            color: #0f172a;
            padding: 8px 4px 12px 4px;
            background-color: transparent;
        }
        QLabel#homeTitle {
            font-size: 18pt;
            font-weight: 600;
            color: #0f172a;
            background-color: transparent;
        }
        QLabel#placeholderTitle {
            font-size: 16pt;
            font-weight: 600;
            color: #0f172a;
            background-color: transparent;
        }
        QListWidget {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 8px;
            outline: 0;
        }
        QListWidget::item {
            padding: 12px 14px;
            margin: 4px 0;
            border-radius: 8px;
            color: #334155;
            background-color: transparent;
        }
        QListWidget::item:hover {
            background-color: #e8f0fe;
            color: #1e3a8a;
        }
        QListWidget::item:selected {
            background-color: #dbeafe;
            color: #1e40af;
            font-weight: 600;
        }
        QStackedWidget {
            background-color: transparent;
        }
        QScrollArea {
            background-color: transparent;
            border: none;
        }
        QPushButton {
            background-color: #3b82f6;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #2563eb;
        }
        QPushButton:pressed {
            background-color: #1d4ed8;
        }
        QPushButton:disabled {
            background-color: #cbd5e1;
            color: #64748b;
        }
        """
    )


class MainWindow(QMainWindow):
    """
    主窗口：左侧固定宽度导航 + 右侧页面栈。
    导航项与 stack 索引一一对应，后续新增页面只需同步扩展两处列表。
    """

    NAV_ITEMS = (
        "主页",
        "抛体运动",
        "碰撞模型",
        "双摆模型",
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("力学仿真平台")
        self.resize(1120, 720)
        self.setMinimumSize(880, 560)

        self._nav = QListWidget()
        self._nav.setObjectName("mainNav")
        self._nav.setSpacing(2)
        self._nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for text in self.NAV_ITEMS:
            self._nav.addItem(QListWidgetItem(text))

        self._stack = QStackedWidget()
        self._stack.addWidget(HomePage())
        self._stack.addWidget(PageProjectile())
        self._stack.addWidget(PageCollision())
        self._stack.addWidget(PagePendulum())

        # 侧栏：品牌标题 + 列表，便于 QSS 统一圆角与留白
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)
        brand = QLabel("力学仿真")
        brand.setObjectName("sidebarBrand")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 18, 16, 18)
        side_layout.setSpacing(8)
        side_layout.addWidget(brand)
        side_layout.addWidget(self._nav, stretch=1)

        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)
        main_layout.addWidget(sidebar, stretch=0)
        main_layout.addWidget(self._stack, stretch=1)

        self.setCentralWidget(central)

        menu_bar = self.menuBar()
        menu_settings = menu_bar.addMenu("设置")
        act_api_key = QAction("DeepSeek API 密钥…", self)
        act_api_key.triggered.connect(self._open_deepseek_api_dialog)
        menu_settings.addAction(act_api_key)

        # 键盘/鼠标切换导航时同步页面
        self._nav.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._nav.setCurrentRow(0)

        # Ctrl+Tab / Ctrl+Shift+Tab 循环切换页面（与侧栏选中状态同步）
        self._shortcut_next = QShortcut(QKeySequence("Ctrl+Tab"), self)
        self._shortcut_next.activated.connect(self._cycle_stack_next)
        self._shortcut_prev = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        self._shortcut_prev.activated.connect(self._cycle_stack_prev)

    def _cycle_stack_next(self) -> None:
        n = self._stack.count()
        if n == 0:
            return
        idx = (self._stack.currentIndex() + 1) % n
        self._stack.setCurrentIndex(idx)
        self._nav.setCurrentRow(idx)

    def _open_deepseek_api_dialog(self) -> None:
        from ui.dialog_api_key import DeepSeekApiKeyDialog

        dlg = DeepSeekApiKeyDialog(self)
        dlg.exec_()

    def _cycle_stack_prev(self) -> None:
        n = self._stack.count()
        if n == 0:
            return
        idx = (self._stack.currentIndex() - 1) % n
        self._stack.setCurrentIndex(idx)
        self._nav.setCurrentRow(idx)


def main() -> int:
    app = QApplication(sys.argv)
    apply_global_style(app)
    win = MainWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
