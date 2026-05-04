# -*- coding: utf-8 -*-
"""
主菜单页面：提供四个模块的选择入口。
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
)

class MenuCard(QFrame):
    """自定义菜单卡片组件"""
    clicked = pyqtSignal(int)

    def __init__(self, title, description, icon_text, index, color="#3b82f6"):
        super().__init__()
        self.index = index
        self.setObjectName("MenuCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(240, 300)
        
        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(15)

        # 图标/文字
        icon_label = QLabel(icon_text)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"font-size: 50pt; color: {color}; background: transparent;")
        
        # 标题
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #1f2937; background: transparent;")
        
        # 描述
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 10pt; color: #6b7280; background: transparent;")

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()

        self.setStyleSheet(f"""
            QFrame#MenuCard {{
                background-color: white;
                border: 2px solid #f3f4f6;
                border-radius: 20px;
            }}
            QFrame#MenuCard:hover {{
                border: 2px solid {color};
                background-color: #f9fafb;
            }}
        """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.index)
        super().mousePressEvent(event)


class PageMenu(QWidget):
    """主菜单页面"""
    module_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # 标题栏
        header = QVBoxLayout()
        title = QLabel("力学仿真教学平台")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32pt; font-weight: 800; color: #0f172a; margin-bottom: 5px;")
        
        subtitle = QLabel("探索物理之美，从这里开始")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14pt; color: #64748b;")
        
        header.addWidget(title)
        header.addWidget(subtitle)
        main_layout.addLayout(header)

        # 模块网格
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(30)
        grid_layout.setAlignment(Qt.AlignCenter)

        modules = [
            ("抛体运动", "研究在重力作用下的抛体轨迹与参数影响。", "🚀", 1, "#3b82f6"),
            ("碰撞模型", "模拟不同恢复系数下的动量守恒与能量耗散。", "💥", 2, "#ef4444"),
            ("双摆模型", "探索多自由度非线性系统的混沌之美。", "⛓️", 3, "#8b5cf6"),
            ("仿真实验室", "全功能二维物理引擎，自由搭建实验场景。", "🔬", 4, "#10b981"),
        ]

        for i, (name, desc, icon, idx, color) in enumerate(modules):
            card = MenuCard(name, desc, icon, idx, color)
            card.clicked.connect(self.module_selected.emit)
            grid_layout.addWidget(card, i // 4, i % 4)

        main_layout.addStretch(1)
        main_layout.addWidget(grid_container)
        main_layout.addStretch(1)

        # 页脚
        footer = QLabel("© 2026 力学仿真教学团队")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("font-size: 9pt; color: #94a3b8;")
        main_layout.addWidget(footer)
