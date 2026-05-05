# -*- coding: utf-8 -*-
"""
力学仿真教学平台 — 程序入口与主窗口。
左侧 QListWidget 导航 + 右侧 QStackedWidget 多页切换；全局明亮学术风 QSS。
"""

import os
import sys

# 将项目根目录添加到 sys.path，以便导入 physics_sim 模块
platform_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(platform_dir, "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from PyQt5.QtCore import Qt, QCoreApplication
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
    QPushButton,
    QShortcut,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui.page_collision import PageCollision
from ui.page_pendulum import PagePendulum
from ui.page_projectile import PageProjectile
from ui.pages.page_menu import PageMenu
from ui.teaching_chat_helper import TeachingChatHelper
from gui.main_window import MainWindow as PhysicsSimWindow


def get_platform_qss() -> str:
    """
    获取平台专属的 QSS 样式。
    """
    return """
        #PlatformWindow {
            background-color: #f5f7fb;
        }

        /* 返回主菜单按钮样式 */
        QPushButton#backToMenuBtn {
            background-color: #ffffff;
            color: #3b82f6;
            border: 1px solid #dbeafe;
            border-radius: 10px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 10.5pt;
            margin-top: 10px;
        }
        QPushButton#backToMenuBtn:hover {
            background-color: #eff6ff;
            border: 1px solid #3b82f6;
        }

        QStackedWidget {
            background-color: transparent;
        }

        /* 平台专属按钮样式 - 仅作用于平台页面 */
        .PageMenu QPushButton, .PageProjectile QPushButton, .PageCollision QPushButton, .PagePendulum QPushButton {
            background-color: #3b82f6;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: 600;
        }
        .PageMenu QPushButton:hover, .PageProjectile QPushButton:hover, .PageCollision QPushButton:hover, .PagePendulum QPushButton:hover {
            background-color: #2563eb;
        }
    """


class MainWindow(QMainWindow):
    """
    主窗口：左侧固定宽度导航 + 右侧页面栈。
    导航项与 stack 索引一一对应，后续新增页面只需同步扩展两处列表。
    """

    NAV_ITEMS = (
        "主菜单",
        "抛体运动",
        "碰撞模型",
        "双摆模型",
        "仿真实验室",
    )

    def __init__(self):
        super().__init__()
        self.setObjectName("PlatformWindow")
        self.setWindowTitle("力学仿真平台")
        self.resize(1120, 720)
        self.setMinimumSize(880, 560)

        self._apply_platform_style()

        self._stack = QStackedWidget()
        self.page_menu = PageMenu()
        self.page_menu.module_selected.connect(self._on_nav_changed)
        
        self._stack.addWidget(self.page_menu)
        self._stack.addWidget(PageProjectile())
        self._stack.addWidget(PageCollision())
        self._stack.addWidget(PagePendulum())
        
        # 仿真实验室界面
        self.physics_sim = PhysicsSimWindow()
        self.physics_sim.setPalette(QApplication.style().standardPalette())
        self.physics_sim.setStyleSheet("/* Reset Style */")
        self._stack.addWidget(self.physics_sim)

        # 顶层布局：仅包含页面栈（填满全部空间）
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0) # 填满
        main_layout.setSpacing(0)

        main_layout.addWidget(self._stack, stretch=1)

        self.setCentralWidget(central)

        # 为各个页面注入返回按钮（确保不产生全局底部空隙）
        self._inject_back_buttons()

        # 初始化显示
        self._on_nav_changed(0)
        self.setStyleSheet(get_platform_qss())

        # 设置菜单
        self._init_menu()

        # Ctrl+Tab / Ctrl+Shift+Tab 循环切换页面
        self._shortcut_next = QShortcut(QKeySequence("Ctrl+Tab"), self)
        self._shortcut_next.activated.connect(self._cycle_stack_next)
        self._shortcut_prev = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        self._shortcut_prev.activated.connect(self._cycle_stack_prev)

    def _apply_platform_style(self) -> None:
        """应用平台专属调色板。"""
        palette = self.palette()
        palette.setColor(palette.Window, QColor("#f5f7fb"))
        palette.setColor(palette.WindowText, QColor("#1f2937"))
        palette.setColor(palette.Base, QColor("#ffffff"))
        palette.setColor(palette.AlternateBase, QColor("#eef2f8"))
        palette.setColor(palette.Button, QColor("#ffffff"))
        palette.setColor(palette.ButtonText, QColor("#1f2937"))
        palette.setColor(palette.Highlight, QColor("#3b82f6"))
        palette.setColor(palette.HighlightedText, QColor("#ffffff"))
        self.setPalette(palette)

    def _init_menu(self) -> None:
        """初始化顶部菜单栏。"""
        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu("设置(&S)")
        
        api_action = QAction("DeepSeek API 密钥(&K)", self)
        api_action.setStatusTip("配置用于 AI 智能助教的 API 密钥")
        api_action.triggered.connect(self._open_deepseek_api_dialog)
        settings_menu.addAction(api_action)

    def _on_nav_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)

    def _inject_back_buttons(self) -> None:
        """
        在各实验页面的左侧控制面板底部注入“返回主菜单”按钮。
        这样可以避免全局底部布局产生的空隙，使中右部内容填满。
        """
        # 1. 仿真实验室
        btn_back_sim = self._create_back_btn()
        # 仿真实验室的左侧面板是 create_panel，其布局最后有 stretch
        self.physics_sim.create_panel.layout().addWidget(btn_back_sim)

        # 2. 其他教学实验页
        for page in [self._stack.widget(1), self._stack.widget(2), self._stack.widget(3)]:
            try:
                # 注入到教学页面 (Teaching View) 的左侧底部
                teaching_view = page._stack.widget(0)
                # teaching_view layout: [ left_card, right_inner ]
                left_card = teaching_view.layout().itemAt(0).widget()
                left_inner = left_card.layout().itemAt(0).widget()
                left_layout = left_inner.layout()
                if left_layout:
                    btn_back_teaching = self._create_back_btn()
                    left_layout.addWidget(btn_back_teaching)
            except Exception as e:
                print("Failed to inject back button to teaching view:", e)

            try:
                # 注入到实验室页面 (Lab View) 的左侧底部
                lab_view = page._stack.widget(1)
                splitter = lab_view.findChild(QSplitter)
                if splitter:
                    left_card = splitter.widget(0)
                    left_layout = left_card.layout()
                    if left_layout:
                        btn_back_lab = self._create_back_btn()
                        left_layout.addWidget(btn_back_lab)
            except Exception as e:
                print("Failed to inject back button to lab view:", e)

    def _create_back_btn(self) -> QPushButton:
        btn = QPushButton("返回主菜单")
        btn.setObjectName("backToMenuBtn")
        btn.setFixedWidth(140)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._on_nav_changed(0))
        return btn

    def _cycle_stack_next(self) -> None:
        n = self._stack.count()
        if n == 0:
            return
        idx = (self._stack.currentIndex() + 1) % n
        self._on_nav_changed(idx)

    def _open_deepseek_api_dialog(self) -> None:
        from ui.dialog_api_key import DeepSeekApiKeyDialog

        dlg = DeepSeekApiKeyDialog(self)
        dlg.exec_()

    def _cycle_stack_prev(self) -> None:
        n = self._stack.count()
        if n == 0:
            return
        idx = (self._stack.currentIndex() - 1) % n
        self._on_nav_changed(idx)


# 渲染模式配置：针对 QWebEngineView 滑动不刷新问题
# 模式A "chromium_disable_gpu_only"：默认，仅禁用 Chromium GPU
# 模式B "desktop_opengl"：强制使用桌面 OpenGL
# 模式C "software_opengl"：强制使用软件 OpenGL (某些系统可能启动崩溃)
WEBENGINE_RENDER_MODE = "chromium_disable_gpu_only"

def main() -> int:
    from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
    print(f"Qt Version: {QT_VERSION_STR}")
    print(f"PyQt Version: {PYQT_VERSION_STR}")

    # 第一优先级：修正 Chromium 启动参数，不要禁用软件光栅化
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
        "--disable-gpu "
        "--disable-gpu-compositing "
        "--disable-accelerated-2d-canvas "
        "--disable-features=CalculateNativeWinOcclusion,VizDisplayCompositor "
        "--enable-begin-frame-control"
    )

    # 第二优先级：可切换的 OpenGL 测试模式
    if WEBENGINE_RENDER_MODE == "desktop_opengl":
        QCoreApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    elif WEBENGINE_RENDER_MODE == "software_opengl":
        QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
    
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
