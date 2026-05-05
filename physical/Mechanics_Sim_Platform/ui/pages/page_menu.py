# -*- coding: utf-8 -*-
"""
优化后的主菜单界面：动态 GIF 背景、高级磨砂质感遮罩、响应式卡片布局与顺序入场动画。
"""

import os
import sys
from PyQt5.QtCore import (
    Qt, 
    pyqtSignal, 
    QPropertyAnimation, 
    QEasingCurve, 
    QPoint, 
    QSize,
    QTimer,
    QParallelAnimationGroup,
    QSequentialAnimationGroup
)
from PyQt5.QtGui import (
    QColor, 
    QFont, 
    QPixmap, 
    QPainter, 
    QBrush, 
    QLinearGradient, 
    QRadialGradient,
    QMovie,
    QPalette
)
from PyQt5.QtWidgets import (
    QWidget, 
    QLabel, 
    QVBoxLayout, 
    QHBoxLayout, 
    QFrame, 
    QGraphicsDropShadowEffect, 
    QLayout, 
    QSpacerItem, 
    QSizePolicy,
    QGraphicsOpacityEffect,
    QGridLayout
)

def resource_path(relative_path: str) -> str:
    """获取资源的绝对路径，兼容 PyInstaller 打包后的路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境下，相对于当前文件所在目录的父目录的父目录（Mechanics_Sim_Platform/assets）
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 尝试多种可能的路径前缀
    paths_to_try = [
        os.path.join(base_path, relative_path),
        os.path.join(os.path.abspath("."), relative_path),
        os.path.join(os.path.dirname(base_path), relative_path)
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            return p
    return os.path.join(base_path, relative_path)

class AnimatedBackgroundWidget(QWidget):
    """
    动态背景组件：使用 QMovie 播放 GIF，支持比例缩放填充、高级遮罩叠加与渐变兜底。
    """
    def __init__(self, gif_path: str, parent=None):
        super().__init__(parent)
        self.gif_path = gif_path
        self.movie = None
        self.fallback_active = False
        self._init_movie()

    def _init_movie(self):
        if self.gif_path and os.path.exists(self.gif_path):
            self.movie = QMovie(self.gif_path)
            if self.movie.isValid():
                self.movie.setCacheMode(QMovie.CacheAll)
                self.movie.frameChanged.connect(self.update)
                self.movie.start()
            else:
                print(f"Warning: GIF is invalid: {self.gif_path}")
                self.fallback_active = True
        else:
            print(f"Warning: GIF path not found: {self.gif_path}")
            self.fallback_active = True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 1. 绘制底图 (GIF 或 渐变)
        if not self.fallback_active and self.movie and self.movie.state() == QMovie.Running:
            current_frame = self.movie.currentPixmap()
            if not current_frame.isNull():
                scaled = current_frame.scaled(
                    self.size(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                x = (self.width() - scaled.width()) // 2
                y = (self.height() - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
            else:
                self._draw_fallback(painter)
        else:
            self._draw_fallback(painter)

        # 2. 叠加多层遮罩
        # 第一层：整体半透明浅色遮罩
        painter.fillRect(self.rect(), QColor(241, 245, 249, 160))

        # 第二层：顶部线性渐变（增强标题可读性）
        top_gradient = QLinearGradient(0, 0, 0, self.height() * 0.4)
        top_gradient.setColorAt(0, QColor(255, 255, 255, 120))
        top_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillRect(self.rect(), QBrush(top_gradient))

        # 第三层：中心区域径向高亮（聚焦卡片）
        radial_gradient = QRadialGradient(self.rect().center(), self.width() * 0.6)
        radial_gradient.setColorAt(0, QColor(255, 255, 255, 80))
        radial_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillRect(self.rect(), QBrush(radial_gradient))

    def _draw_fallback(self, painter):
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#f1f5f9"))
        gradient.setColorAt(1, QColor("#e2e8f0"))
        painter.fillRect(self.rect(), QBrush(gradient))

class HomeMenuCard(QFrame):
    """
    高级实验入口卡片：支持 Accent 风格、图标容器、上浮动画与状态反馈。
    """
    clicked = pyqtSignal(str)

    def __init__(self, title, subtitle, icon, accent, route, parent=None):
        super().__init__(parent)
        self.route = route
        self.accent = QColor(accent)
        self.setFixedSize(240, 310)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("HomeMenuCard")
        
        # 基础样式
        self._update_style(False)

        # 阴影效果
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(10)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(self.shadow)

        # 内部布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(10)

        # 1. 图标区域 (彩色圆形背景)
        self.icon_container = QWidget()
        self.icon_container.setFixedSize(70, 70)
        self.icon_container.setStyleSheet(f"""
            background-color: {self.accent.name()}15;
            border-radius: 35px;
        """)
        icon_layout = QVBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        self.icon_label = QLabel(icon)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 32pt; background: transparent;")
        icon_layout.addWidget(self.icon_label)
        
        layout.addWidget(self.icon_container, 0, Qt.AlignCenter)
        layout.addSpacing(10)
        
        # 2. 标题
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"""
            font-family: 'Microsoft YaHei', 'PingFang SC';
            font-size: 22px;
            font-weight: bold;
            color: #0f172a;
            background: transparent;
        """)
        layout.addWidget(self.title_label)
        
        # 3. 描述
        self.desc_label = QLabel(subtitle)
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("""
            font-family: 'Microsoft YaHei', 'PingFang SC';
            font-size: 13px;
            color: #475569;
            background: transparent;
            line-height: 1.3;
        """)
        layout.addWidget(self.desc_label)
        
        layout.addStretch()
        
        # 4. 底部引导文字
        self.action_label = QLabel("开始探索 →")
        self.action_label.setAlignment(Qt.AlignCenter)
        self.action_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: #64748b;
            background: transparent;
        """)
        layout.addWidget(self.action_label)

        # 动画对象
        self.offset_anim = QPropertyAnimation(self, b"pos")
        self.offset_anim.setDuration(300)
        self.offset_anim.setEasingCurve(QEasingCurve.OutQuint)
        self.base_pos = None

    def _update_style(self, is_hover: bool):
        # 使用更稳健的样式设置
        bg_color = "rgba(255, 255, 255, 200)" if not is_hover else "rgba(255, 255, 255, 240)"
        border_color = self.accent.name() if is_hover else "#ffffff"
        border_width = "2px" if is_hover else "1px"
        
        self.setStyleSheet(f"""
            QFrame#HomeMenuCard {{
                background-color: {bg_color};
                border: {border_width} solid {border_color};
                border-radius: 24px;
            }}
        """)
        if hasattr(self, 'action_label'):
            color = self.accent.name() if is_hover else "#64748b"
            self.action_label.setStyleSheet(f"color: {color}; font-weight: 600; background: transparent;")

    def enterEvent(self, event):
        if self.base_pos is None:
            self.base_pos = self.pos()
        
        self.offset_anim.stop()
        self.offset_anim.setEndValue(self.base_pos + QPoint(0, -10))
        self.offset_anim.start()
        
        self.shadow.setBlurRadius(35)
        self.shadow.setColor(QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 50))
        self._update_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.base_pos is not None:
            self.offset_anim.stop()
            self.offset_anim.setEndValue(self.base_pos)
            self.offset_anim.start()
        
        self.shadow.setBlurRadius(25)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self._update_style(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.offset_anim.stop()
        self.offset_anim.setEndValue(self.base_pos + QPoint(0, -2))
        self.offset_anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.rect().contains(event.pos()):
            self.clicked.emit(self.route)
        super().mouseReleaseEvent(event)

class HomePage(QWidget):
    """
    主菜单首页：负责 Hero 区域绘制、响应式网格布局以及顺序淡入动画。
    """
    module_selected = pyqtSignal(int)
    route_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.route_map = {
            "projectile": 1,
            "collision": 2,
            "double_pendulum": 3,
            "lab": 4
        }
        self._setup_ui()
        # 延迟执行入场动画
        QTimer.singleShot(100, self._start_entrance_animation)

    def _setup_ui(self):
        # 1. 动态背景
        gif_path = resource_path("assets/background.gif")
        self.background = AnimatedBackgroundWidget(gif_path, self)
        
        # 2. 内容层
        self.content_container = QWidget(self)
        self.layout_main = QVBoxLayout(self.content_container)
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(0)
        
        # 顶层弹性空间 (让内容重心稍偏上)
        self.layout_main.addStretch(1)

        # --- Hero 区域 ---
        hero_widget = QWidget()
        hero_layout = QVBoxLayout(hero_widget)
        hero_layout.setSpacing(12)
        
        # 胶囊标签
        tags_layout = QHBoxLayout()
        tags_layout.setAlignment(Qt.AlignCenter)
        tag_text = "Projectile · Collision · Double Pendulum · Virtual Lab"
        self.tag_label = QLabel(tag_text)
        self.tag_label.setStyleSheet("""
            color: #64748b;
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 1px;
            background-color: rgba(255, 255, 255, 120);
            border-radius: 12px;
            padding: 4px 15px;
        """)
        tags_layout.addWidget(self.tag_label)
        hero_layout.addLayout(tags_layout)

        # 主标题
        self.title_label = QLabel("力学仿真教学平台")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            font-size: 52px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: 1px;
            background: transparent;
        """)
        hero_layout.addWidget(self.title_label)
        
        # 副标题
        self.subtitle_label = QLabel("以可视化实验理解力学规律")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("""
            font-family: 'Microsoft YaHei', 'PingFang SC';
            font-size: 20px;
            color: #475569;
            background: transparent;
        """)
        hero_layout.addWidget(self.subtitle_label)
        
        self.layout_main.addWidget(hero_widget)
        self.layout_main.addSpacing(65)
        
        # --- 卡片区域 ---
        self.grid_container = QWidget()
        self.grid_container.setMaximumWidth(1200)
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(32)
        self.grid_layout.setAlignment(Qt.AlignCenter)
        
        card_data = [
            {
                "title": "抛体运动",
                "subtitle": "分析重力场中的轨迹、速度与射程变化。",
                "icon": "🚀",
                "accent": "#ef4444",
                "route": "projectile"
            },
            {
                "title": "碰撞模型",
                "subtitle": "观察动量守恒、能量损失与恢复系数影响。",
                "icon": "💥",
                "accent": "#f97316",
                "route": "collision"
            },
            {
                "title": "双摆模型",
                "subtitle": "体验非线性系统的敏感依赖与混沌行为。",
                "icon": "⛓️",
                "accent": "#6366f1",
                "route": "double_pendulum"
            },
            {
                "title": "仿真实验室",
                "subtitle": "自由搭建实验条件，验证你的物理猜想。",
                "icon": "🔬",
                "accent": "#2563eb",
                "route": "lab"
            }
        ]
        
        self.cards = []
        for i, data in enumerate(card_data):
            card = HomeMenuCard(
                data["title"], 
                data["subtitle"], 
                data["icon"], 
                data["accent"],
                data["route"]
            )
            card.clicked.connect(self._handle_card_click)
            # 初始设置为透明以支持动画
            op = QGraphicsOpacityEffect(card)
            op.setOpacity(0)
            card.setGraphicsEffect(op)
            
            self.cards.append(card)
            # 默认布局将由 _update_grid_layout 处理

        centered_layout = QHBoxLayout()
        centered_layout.addStretch(1)
        centered_layout.addWidget(self.grid_container)
        centered_layout.addStretch(1)
        self.layout_main.addLayout(centered_layout)
        
        self.layout_main.addStretch(2)

        # 初始透明度 (用于 Hero 区域)
        self.hero_opacity = QGraphicsOpacityEffect(hero_widget)
        self.hero_opacity.setOpacity(0)
        hero_widget.setGraphicsEffect(self.hero_opacity)

    def _start_entrance_animation(self):
        # 1. 标题淡入
        self.hero_anim = QPropertyAnimation(self.hero_opacity, b"opacity")
        self.hero_anim.setDuration(800)
        self.hero_anim.setStartValue(0)
        self.hero_anim.setEndValue(1)
        self.hero_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.hero_anim.start()

        # 2. 卡片顺序淡入并轻微上弹
        self.card_anims = QSequentialAnimationGroup()
        for card in self.cards:
            op_effect = card.graphicsEffect()
            
            # 淡入
            anim = QPropertyAnimation(op_effect, b"opacity")
            anim.setDuration(400)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            
            self.card_anims.addAnimation(anim)
            self.card_anims.addPause(50) # 短暂间隔
            
        self.card_anims.start()

    def _handle_card_click(self, route):
        self.route_selected.emit(route)
        if route in self.route_map:
            self.module_selected.emit(self.route_map[route])

    def resizeEvent(self, event):
        self.background.setGeometry(0, 0, self.width(), self.height())
        self.content_container.setGeometry(0, 0, self.width(), self.height())
        self._update_grid_layout()
        # 窗口缩放时重置卡片的基准位置
        for card in self.cards:
            card.base_pos = None 
        super().resizeEvent(event)

    def _update_grid_layout(self):
        # 简单的响应式逻辑
        w = self.width()
        # 清空当前网格内容，但不销毁卡片
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
            
        if w > 1150:
            # 4 列
            for i, card in enumerate(self.cards):
                card.show()
                self.grid_layout.addWidget(card, 0, i)
        elif w > 650:
            # 2 列
            for i, card in enumerate(self.cards):
                card.show()
                self.grid_layout.addWidget(card, i // 2, i % 2)
        else:
            # 1 列
            for i, card in enumerate(self.cards):
                card.show()
                self.grid_layout.addWidget(card, i, 0)

# 别名保持兼容
class PageMenu(HomePage):
    pass
