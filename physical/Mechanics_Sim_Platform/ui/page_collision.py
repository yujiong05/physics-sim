# -*- coding: utf-8 -*-
"""
实验二：二维装箱内两球实时碰撞仿真。
弹性 / 非弹性模式；质量决定半径；速率 + 方向控制初速度；碰壁与球-球碰撞；
实验室含「开始仿真 / 暂停 / 重置」与回放倍速。
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (
    QButtonGroup,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ui.markdown_viewer import MarkdownFormulaViewer
from engine.billiards_box import (
    BilliardsState,
    clamp_positions,
    kinetic_energy,
    make_state,
    polar_to_velocity,
    step_state,
    update_radii_keep_centers,
)
from ui.mpl_setup import configure_matplotlib_chinese_font
from ui.teaching_chat_helper import TeachingChatHelper

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEXTBOOK_PATH = _PROJECT_ROOT / "assets" / "long_images" / "碰撞模型.png"

BOX_W = 1.0
BOX_H = 0.65
LINE_Y = BOX_H * 0.5

_HIST_CAP = 1400
_TIME_WINDOW = 20.0


def _card_shadow(widget: QWidget, blur: int = 22, dy: int = 3) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, dy)
    effect.setColor(QColor(15, 23, 42, 38))
    widget.setGraphicsEffect(effect)


class PageCollision(QWidget):
    """实验二页面：教材 / AI / 装箱碰撞实验室。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._on_tick)

        self._state: Optional[BilliardsState] = None
        self._paused = False
        self._sim_running = False
        self._sim_time = 0.0
        self._ke_baseline = 0.0

        self._hist_t: List[float] = []
        self._hist_ke: List[float] = []
        self._hist_loss: List[float] = []

        self._circ1: Optional[Circle] = None
        self._circ2: Optional[Circle] = None
        self._arena_rect = None
        self._txt_ball1 = None
        self._txt_ball2 = None
        self._line_ke_tot = None
        self._line_ke_loss = None

        self._saved_e = 0.82

        configure_matplotlib_chinese_font()
        self._chat_ai = TeachingChatHelper(self, "collision")
        self._build_ui()
        self._stack.currentChanged.connect(self._on_stack_changed)
        self._refresh_transport_buttons()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._refresh_chat_webview)
        QTimer.singleShot(100, self._refresh_chat_webview)
        QTimer.singleShot(300, self._refresh_chat_webview)

    def _refresh_chat_webview(self):
        if hasattr(self, "_chat_log") and hasattr(self._chat_log, "force_refresh"):
            self._chat_log.force_refresh()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_teaching_view())
        self._stack.addWidget(self._build_lab_view())
        outer.addWidget(self._stack, stretch=1)

        self.setStyleSheet(
            """
            QFrame.CardPanel {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }
            QPushButton.SecondaryBtn {
                background-color: #e2e8f0;
                color: #1e293b;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: 600;
            }
            QPushButton.SecondaryBtn:hover { background-color: #cbd5e1; }
            QPushButton.PrimaryXL {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 14px;
                padding: 18px 24px;
                font-weight: 700;
                font-size: 13pt;
            }
            QPushButton.PrimaryXL:hover { background-color: #2563eb; }
            QPushButton.ToolBtn {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 600;
            }
            QPushButton.ToolBtn:hover { background-color: #2563eb; }
            QPushButton.ToolBtn:disabled {
                background-color: #cbd5e1;
                color: #64748b;
            }
            QLineEdit.ChatInput {
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 10px 12px;
                background: #ffffff;
            }
            QLineEdit.ParamEdit {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 6px 8px;
                background: #ffffff;
                min-width: 88px;
                max-width: 160px;
            }
            QTextBrowser.ChatLog {
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                background: #f8fafc;
                padding: 12px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #e2e8f0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3b82f6;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QRadioButton { spacing: 8px; color: #334155; }
            """
        )

    def _wrap_card(self, inner: QWidget, margins: Tuple[int, int, int, int] = (16, 16, 16, 16)) -> QFrame:
        card = QFrame()
        card.setObjectName("CardPanel")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(*margins)
        lay.addWidget(inner)
        _card_shadow(card)
        return card

    def _build_teaching_view(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setSpacing(18)

        left_inner = QWidget()
        left_lay = QVBoxLayout(left_inner)
        title_l = QLabel("教材讲解")
        title_l.setStyleSheet("font-weight:600;font-size:12pt;color:#0f172a;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setAlignment(Qt.AlignTop)

        pic = QLabel()
        pic.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        if _TEXTBOOK_PATH.is_file():
            pix = QPixmap(str(_TEXTBOOK_PATH))
            if not pix.isNull():
                pic.setPixmap(pix.scaledToWidth(760, Qt.SmoothTransformation))
            else:
                pic.setText("无法解码 collision_textbook.png。")
        else:
            pic.setText(
                "未找到 assets/collision_textbook.png。\n"
                "放入教材插图后可在此展示；当前为占位提示。"
            )
            pic.setWordWrap(True)

        scroll.setWidget(pic)
        left_lay.addWidget(title_l)
        left_lay.addWidget(scroll, stretch=1)

        right_inner = QWidget()
        rl = QVBoxLayout(right_inner)
        rl.setSpacing(14)

        title_r = QLabel("智能助教")
        title_r.setStyleSheet("font-weight:600;font-size:12pt;color:#0f172a;")

        self._chat_log = MarkdownFormulaViewer()
        self._chat_log.set_markdown(
            "可提问动量守恒、恢复系数或碰撞分类。请先在主窗口「设置 → DeepSeek API 密钥」保存密钥。"
        )

        row = QHBoxLayout()
        self._chat_input = QLineEdit()
        self._chat_input.setPlaceholderText("输入问题…")
        self._chat_input.setObjectName("ChatInput")
        self._btn_chat_send = QPushButton("发送")
        self._btn_chat_send.setObjectName("ToolBtn")
        self._chat_ai.attach(self._chat_log, self._chat_input, self._btn_chat_send)
        self._btn_chat_send.clicked.connect(self._chat_ai.on_send)
        self._chat_input.returnPressed.connect(self._chat_ai.on_send)
        row.addWidget(self._chat_input, stretch=1)
        row.addWidget(self._btn_chat_send)

        btn_lab = QPushButton("进入仿真实验室")
        btn_lab.setObjectName("PrimaryXL")
        btn_lab.setMinimumHeight(56)
        btn_lab.setCursor(Qt.PointingHandCursor)
        btn_lab.clicked.connect(lambda: self._stack.setCurrentIndex(1))

        rl.addWidget(title_r)
        rl.addWidget(self._chat_log, stretch=1)
        rl.addLayout(row)
        rl.addWidget(btn_lab)

        layout.addWidget(self._wrap_card(left_inner), stretch=6)
        # 第三优先级：去除外层复杂包装，裸布局测试是否实时刷新
        layout.addWidget(right_inner, stretch=4)
        return page

    def _build_lab_view(self) -> QWidget:
        page = QWidget()
        root = QHBoxLayout(page)
        root.setSpacing(16)

        ctrl = QWidget()
        ctrl.setMinimumWidth(360)
        ctrl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        cv = QVBoxLayout(ctrl)
        cv.setSpacing(12)

        btn_back = QPushButton("← 返回教学页面")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._on_back_teaching)

        mode_row = QHBoxLayout()
        self._radio_elastic = QRadioButton("弹性碰撞（e = 1）")
        self._radio_inelastic = QRadioButton("非弹性碰撞（e < 1，可调）")
        self._radio_inelastic.setChecked(True)
        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self._radio_elastic, 0)
        self._mode_group.addButton(self._radio_inelastic, 1)
        self._mode_group.buttonClicked.connect(lambda _b: self._on_collision_mode_changed())
        mode_row.addWidget(self._radio_elastic)
        mode_row.addWidget(self._radio_inelastic)
        mode_row.addStretch()

        geo = QLabel(
            f"<b>装箱场地</b>：矩形区域宽 {BOX_W:g} m × 高 {BOX_H:g} m；"
            f"边界为刚性墙壁（镜面反弹）。本实验两球<strong>限制在水平中线 y = {LINE_Y:g} m 上运动</strong>，"
            f"为沿 x 轴的一维对碰；<strong>质量越大半径越大</strong>（∝ m<sup>1/3</sup>）。"
        )
        geo.setWordWrap(True)
        geo.setStyleSheet(
            "background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:10px;color:#334155;"
        )

        self._formula_lab = QLabel()
        self._formula_lab.setWordWrap(True)
        self._formula_lab.setStyleSheet(
            "background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:10px;color:#334155;"
        )
        self._update_formula_text()

        form = QFormLayout()
        form.setSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setHorizontalSpacing(14)

        self._spin_m1 = QDoubleSpinBox()
        self._spin_m1.setRange(0.1, 50.0)
        self._spin_m1.setDecimals(2)
        self._spin_m1.setSingleStep(0.1)
        self._spin_m1.setValue(1.0)
        self._spin_m1.setSuffix(" kg")

        self._spin_m2 = QDoubleSpinBox()
        self._spin_m2.setRange(0.1, 50.0)
        self._spin_m2.setDecimals(2)
        self._spin_m2.setSingleStep(0.1)
        self._spin_m2.setValue(2.0)
        self._spin_m2.setSuffix(" kg")

        self._spin_speed1 = QDoubleSpinBox()
        self._spin_speed1.setRange(0.0, 14.0)
        self._spin_speed1.setDecimals(2)
        self._spin_speed1.setSingleStep(0.15)
        self._spin_speed1.setValue(1.05)
        self._spin_speed1.setSuffix(" m/s")

        self._spin_angle1 = QDoubleSpinBox()
        self._spin_angle1.setRange(-180.0, 180.0)
        self._spin_angle1.setDecimals(1)
        self._spin_angle1.setSingleStep(5.0)
        self._spin_angle1.setValue(0.0)
        self._spin_angle1.setSuffix(" °")
        self._spin_angle1.setToolTip(
            "相对 +x 轴逆时针（数学角）；运动约束在水平中线，仅水平分量参与运动。"
        )

        self._spin_speed2 = QDoubleSpinBox()
        self._spin_speed2.setRange(0.0, 14.0)
        self._spin_speed2.setDecimals(2)
        self._spin_speed2.setSingleStep(0.15)
        self._spin_speed2.setValue(0.85)
        self._spin_speed2.setSuffix(" m/s")

        self._spin_angle2 = QDoubleSpinBox()
        self._spin_angle2.setRange(-180.0, 180.0)
        self._spin_angle2.setDecimals(1)
        self._spin_angle2.setSingleStep(5.0)
        self._spin_angle2.setValue(180.0)
        self._spin_angle2.setSuffix(" °")
        self._spin_angle2.setToolTip(
            "相对 +x 轴逆时针（数学角）；运动约束在水平中线，仅水平分量参与运动。"
        )

        self._slider_e = QSlider(Qt.Horizontal)
        self._slider_e.setRange(0, 100)
        self._slider_e.setValue(82)
        self._spin_e = QDoubleSpinBox()
        self._spin_e.setRange(0.0, 1.0)
        self._spin_e.setDecimals(2)
        self._spin_e.setSingleStep(0.05)
        self._spin_e.setValue(0.82)
        self._slider_e.valueChanged.connect(self._on_slider_e_changed)
        self._spin_e.valueChanged.connect(self._on_spin_e_changed)

        self._spin_playback = QDoubleSpinBox()
        self._spin_playback.setRange(0.2, 8.0)
        self._spin_playback.setDecimals(2)
        self._spin_playback.setSingleStep(0.1)
        self._spin_playback.setValue(0.55)
        self._spin_playback.setToolTip(
            "回放倍速：相对默认定时步的仿真快慢；默认略慢于 1.00，便于观察碰撞。"
        )

        self._edit_m1 = QLineEdit()
        self._edit_m1.setObjectName("ParamEdit")
        self._edit_m1.editingFinished.connect(self._apply_m1_edit)
        self._edit_m2 = QLineEdit()
        self._edit_m2.setObjectName("ParamEdit")
        self._edit_m2.editingFinished.connect(self._apply_m2_edit)
        self._edit_e = QLineEdit()
        self._edit_e.setObjectName("ParamEdit")
        self._edit_e.editingFinished.connect(self._apply_e_edit)

        self._spin_m1.valueChanged.connect(self._sync_m1_edit)
        self._spin_m2.valueChanged.connect(self._sync_m2_edit)
        self._spin_e.valueChanged.connect(self._sync_e_edit)
        self._spin_m1.valueChanged.connect(self._on_mass_update)
        self._spin_m2.valueChanged.connect(self._on_mass_update)
        self._spin_speed1.valueChanged.connect(self._on_velocity_update)
        self._spin_angle1.valueChanged.connect(self._on_velocity_update)
        self._spin_speed2.valueChanged.connect(self._on_velocity_update)
        self._spin_angle2.valueChanged.connect(self._on_velocity_update)

        form.addRow("质量 m₁：", self._spin_edit_row(self._spin_m1, self._edit_m1))
        form.addRow("质量 m₂：", self._spin_edit_row(self._spin_m2, self._edit_m2))
        form.addRow("球1 速率：", self._spin_speed1)
        form.addRow("球1 方向角：", self._spin_angle1)
        form.addRow("球2 速率：", self._spin_speed2)
        form.addRow("球2 方向角：", self._spin_angle2)

        row_e = QHBoxLayout()
        row_e.addWidget(self._slider_e, stretch=1)
        row_e.addWidget(self._spin_e)
        row_e.addWidget(self._edit_e)
        self._e_widget = QWidget()
        self._e_widget.setLayout(row_e)
        form.addRow("恢复系数 e：", self._e_widget)

        self._refresh_param_edits()

        playback_row = QHBoxLayout()
        playback_row.setSpacing(10)
        lbl_pb = QLabel("回放倍速：")
        lbl_pb.setStyleSheet("color:#334155;font-weight:600;")
        playback_row.addWidget(lbl_pb)
        playback_row.addWidget(self._spin_playback, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self._btn_start = QPushButton("开始仿真")
        self._btn_start.setObjectName("PrimaryXL")
        self._btn_start.setMinimumHeight(48)
        self._btn_start.setCursor(Qt.PointingHandCursor)
        self._btn_start.clicked.connect(self._on_start_simulation)

        self._btn_pause = QPushButton("暂停")
        self._btn_pause.setObjectName("SecondaryBtn")
        self._btn_pause.setMinimumHeight(48)
        self._btn_pause.setCursor(Qt.PointingHandCursor)
        self._btn_pause.clicked.connect(self._on_pause_toggle)

        self._btn_reset = QPushButton("重置")
        self._btn_reset.setObjectName("ToolBtn")
        self._btn_reset.setMinimumHeight(48)
        self._btn_reset.setCursor(Qt.PointingHandCursor)
        self._btn_reset.clicked.connect(self._full_reset)

        btn_row.addWidget(self._btn_start, stretch=2)
        btn_row.addWidget(self._btn_pause, stretch=1)
        btn_row.addWidget(self._btn_reset, stretch=2)

        hint = QLabel(
            "提示：先点「开始仿真」启动计时；可调回放倍速加快或减慢。"
            "两球始终在场地水平中线对碰（一维沿 x）；方向角仅决定水平速度分量的符号与大小。"
            "暂停时可改参数；重置会回到初始位置并停止。质量改变半径。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#64748b;font-size:10pt;")

        cv.addWidget(btn_back)
        cv.addLayout(mode_row)
        cv.addWidget(geo)
        cv.addWidget(self._formula_lab)
        title_params = QLabel("参数")
        title_params.setStyleSheet("font-weight:700;font-size:11pt;color:#0f172a;")
        cv.addWidget(title_params)
        cv.addLayout(form)
        cv.addLayout(playback_row)
        cv.addLayout(btn_row)
        cv.addWidget(hint)
        cv.addStretch()

        plot = QWidget()
        pv = QVBoxLayout(plot)
        pv.setContentsMargins(4, 4, 4, 4)

        self._fig = Figure(figsize=(10.8, 6.9), dpi=100, layout="constrained")
        self._fig.patch.set_facecolor("#f8fafc")
        gs = self._fig.add_gridspec(2, 1, height_ratios=[2.55, 1.0], hspace=0.34)

        self._ax_track = self._fig.add_subplot(gs[0, 0])
        self._ax_track.set_facecolor("#ffffff")
        self._ax_track.set_title("二维装箱：两球实物模型", color="#0f172a", pad=10)
        self._ax_track.set_xlabel("x / m")
        self._ax_track.set_ylabel("y / m")
        self._ax_track.set_xlim(-0.01, BOX_W + 0.01)
        self._ax_track.set_ylim(-0.01, BOX_H + 0.01)
        self._ax_track.set_aspect("equal", adjustable="box")

        self._arena_rect = Rectangle(
            (0.0, 0.0),
            BOX_W,
            BOX_H,
            linewidth=2.2,
            edgecolor="#1e293b",
            facecolor="#f8fafc",
            zorder=0,
        )
        self._ax_track.add_patch(self._arena_rect)
        self._ax_track.axhline(
            LINE_Y,
            color="#94a3b8",
            linestyle="--",
            linewidth=1.0,
            alpha=0.75,
            zorder=1,
        )

        self._circ1 = Circle((0.22, LINE_Y), 0.05, facecolor="#3b82f6", edgecolor="#ffffff", linewidth=1.8, zorder=5)
        self._circ2 = Circle((0.78, LINE_Y), 0.05, facecolor="#ef4444", edgecolor="#ffffff", linewidth=1.8, zorder=5)
        self._ax_track.add_patch(self._circ1)
        self._ax_track.add_patch(self._circ2)

        self._txt_ball1 = self._ax_track.text(0, 0, "", ha="center", va="bottom", fontsize=8.5, color="#1e3a8a", zorder=6)
        self._txt_ball2 = self._ax_track.text(0, 0, "", ha="center", va="bottom", fontsize=8.5, color="#991b1b", zorder=6)

        self._ax_energy = self._fig.add_subplot(gs[1, 0])
        self._ax_energy.set_facecolor("#ffffff")
        self._ax_energy.set_title("能量随时间变化", color="#0f172a")
        self._ax_energy.set_xlabel("t / s")
        self._ax_energy.set_ylabel("E / J")
        self._ax_energy.grid(True, linestyle="--", linewidth=0.5, alpha=0.35)

        (self._line_ke_tot,) = self._ax_energy.plot([], [], drawstyle="default", color="#16a34a", linewidth=1.7, label="总动能")
        (self._line_ke_loss,) = self._ax_energy.plot([], [], drawstyle="default", color="#ef4444", linewidth=1.5, label="动能损失（相对基准）")
        self._ax_energy.legend(loc="upper right", fontsize=8, framealpha=0.92)

        self._canvas = FigureCanvas(self._fig)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pv.addWidget(self._canvas)

        sp = QSplitter(Qt.Horizontal)
        sp.addWidget(self._wrap_card(ctrl))
        sp.addWidget(self._wrap_card(plot, margins=(12, 12, 12, 12)))
        sp.setStretchFactor(0, 30)
        sp.setStretchFactor(1, 70)
        sp.setSizes([380, 920])

        root.addWidget(sp)
        return page

    # ------------------------------------------------------------------
    def _on_stack_changed(self, idx: int) -> None:
        if idx == 1:
            if self._state is None:
                self._full_reset()
            self._refresh_transport_buttons()
        else:
            self._timer.stop()
            self._sim_running = False
            self._refresh_transport_buttons()

    def _is_elastic_mode(self) -> bool:
        return self._radio_elastic.isChecked()

    def _on_collision_mode_changed(self) -> None:
        elastic = self._is_elastic_mode()
        if elastic:
            self._saved_e = float(self._spin_e.value())
            self._spin_e.blockSignals(True)
            self._spin_e.setValue(1.0)
            self._spin_e.blockSignals(False)
            self._slider_e.blockSignals(True)
            self._slider_e.setValue(100)
            self._slider_e.blockSignals(False)
            self._sync_e_edit()
        else:
            self._spin_e.blockSignals(True)
            self._spin_e.setValue(self._saved_e)
            self._spin_e.blockSignals(False)
            self._slider_e.blockSignals(True)
            self._slider_e.setValue(int(round(self._saved_e * 100.0)))
            self._slider_e.blockSignals(False)
            self._sync_e_edit()

        self._slider_e.setEnabled(not elastic)
        self._spin_e.setEnabled(not elastic)
        self._edit_e.setEnabled(not elastic)
        self._update_formula_text()

    def _update_formula_text(self) -> None:
        if self._is_elastic_mode():
            self._formula_lab.setText(
                "<b>弹性碰撞（球-球）</b>：<i>e = 1</i>，沿连心线相对分离速率等于接近速率。"
                "碰壁为完全弹性反射。<br/>"
                "<b>动量守恒</b>（碰撞瞬时）：<i>m₁v⃗₁ + m₂v⃗₂</i> 在连心线冲量下更新。"
            )
        else:
            self._formula_lab.setText(
                "<b>非弹性碰撞（球-球）</b>：<i>0 ≤ e < 1</i>，可调恢复系数。"
                "<i>e → 0</i> 趋向完全非弹性极限。<br/>"
                "当 <i>e < 1</i> 时，碰撞前后系统总动能不守恒：有一部分转化为热、声等耗散，"
                "故碰撞后总动能一般<strong>低于</strong>碰撞前（可在下方能量曲线中观察跃降）。"
                "碰壁仍为弹性反射；能量损失主要体现在两球相互碰撞。"
            )

    def _spin_edit_row(self, spin: QDoubleSpinBox, edit: QLineEdit) -> QWidget:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(spin, stretch=1)
        row.addWidget(edit)
        w = QWidget()
        w.setLayout(row)
        return w

    def _on_slider_e_changed(self, val: int) -> None:
        self._spin_e.blockSignals(True)
        self._spin_e.setValue(val / 100.0)
        self._spin_e.blockSignals(False)
        self._saved_e = float(self._spin_e.value())
        self._sync_e_edit()

    def _on_spin_e_changed(self, val: float) -> None:
        self._slider_e.blockSignals(True)
        self._slider_e.setValue(int(round(float(val) * 100.0)))
        self._slider_e.blockSignals(False)
        self._saved_e = float(self._spin_e.value())
        self._sync_e_edit()

    def _refresh_param_edits(self) -> None:
        self._edit_m1.setText(f"{self._spin_m1.value():.2f}")
        self._edit_m2.setText(f"{self._spin_m2.value():.2f}")
        self._edit_e.setText(f"{self._spin_e.value():.2f}")

    def _sync_m1_edit(self, *_a: object) -> None:
        self._edit_m1.blockSignals(True)
        self._edit_m1.setText(f"{self._spin_m1.value():.2f}")
        self._edit_m1.blockSignals(False)

    def _sync_m2_edit(self, *_a: object) -> None:
        self._edit_m2.blockSignals(True)
        self._edit_m2.setText(f"{self._spin_m2.value():.2f}")
        self._edit_m2.blockSignals(False)

    def _sync_e_edit(self, *_a: object) -> None:
        self._edit_e.blockSignals(True)
        self._edit_e.setText(f"{self._spin_e.value():.2f}")
        self._edit_e.blockSignals(False)

    def _parse_edit(self, edit: QLineEdit, fallback: float) -> Optional[float]:
        t = edit.text().strip().replace(",", ".")
        if not t:
            return None
        try:
            return float(t)
        except ValueError:
            QMessageBox.warning(self, "输入无效", "请输入数值。")
            return fallback

    def _apply_m1_edit(self) -> None:
        v = self._parse_edit(self._edit_m1, self._spin_m1.value())
        if v is None:
            self._sync_m1_edit()
            return
        self._spin_m1.setValue(max(0.1, min(50.0, v)))

    def _apply_m2_edit(self) -> None:
        v = self._parse_edit(self._edit_m2, self._spin_m2.value())
        if v is None:
            self._sync_m2_edit()
            return
        self._spin_m2.setValue(max(0.1, min(50.0, v)))

    def _apply_e_edit(self) -> None:
        if self._is_elastic_mode():
            self._sync_e_edit()
            return
        v = self._parse_edit(self._edit_e, self._spin_e.value())
        if v is None:
            self._sync_e_edit()
            return
        self._spin_e.setValue(max(0.0, min(1.0, v)))

    def _ball_e(self) -> float:
        return 1.0 if self._is_elastic_mode() else float(self._spin_e.value())

    def _constrain_to_horizontal_line(self) -> None:
        """两球限制在场地水平中线：y 钳制、vy=0（一维沿 x 对碰）。"""
        if self._state is None:
            return
        s = self._state
        for i in range(2):
            r = float(s.r[i])
            y = float(np.clip(LINE_Y, r + 1e-9, BOX_H - r - 1e-9))
            s.pos[i, 1] = y
            s.vel[i, 1] = 0.0

    def _clear_history(self) -> None:
        self._hist_t.clear()
        self._hist_ke.clear()
        self._hist_loss.clear()

    def _full_reset(self) -> None:
        """重置位置与历史；用于首次进入或按钮。"""
        self._timer.stop()
        self._sim_running = False
        self._sim_time = 0.0
        self._paused = False
        self._btn_pause.setText("暂停")
        self._clear_history()
        try:
            self._state = make_state(
                float(self._spin_m1.value()),
                float(self._spin_m2.value()),
                float(self._spin_speed1.value()),
                float(self._spin_angle1.value()),
                float(self._spin_speed2.value()),
                float(self._spin_angle2.value()),
                BOX_W,
                BOX_H,
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "初始化失败", str(exc))
            self._state = None
            self._refresh_transport_buttons()
            return

        clamp_positions(self._state, BOX_W, BOX_H)
        self._constrain_to_horizontal_line()
        self._ke_baseline = kinetic_energy(self._state)
        self._sync_graphics()
        self._update_plot_lines()
        self._canvas.draw_idle()
        self._refresh_transport_buttons()

    def _refresh_transport_buttons(self) -> None:
        if not hasattr(self, "_btn_start"):
            return
        self._btn_start.setEnabled(not self._sim_running)
        self._btn_pause.setEnabled(self._sim_running)

    def _on_start_simulation(self) -> None:
        if self._state is None:
            self._full_reset()
        if self._state is None:
            return
        self._paused = False
        self._btn_pause.setText("暂停")
        self._sim_running = True
        self._refresh_transport_buttons()
        self._timer.start()

    def _on_mass_update(self, *_args: object) -> None:
        if self._state is None:
            return
        update_radii_keep_centers(self._state, float(self._spin_m1.value()), float(self._spin_m2.value()))
        clamp_positions(self._state, BOX_W, BOX_H)
        self._constrain_to_horizontal_line()
        self._ke_baseline = kinetic_energy(self._state)
        self._sync_graphics()
        self._canvas.draw_idle()

    def _on_velocity_update(self, *_args: object) -> None:
        if self._state is None:
            return
        self._state.vel[0] = polar_to_velocity(float(self._spin_speed1.value()), float(self._spin_angle1.value()))
        self._state.vel[1] = polar_to_velocity(float(self._spin_speed2.value()), float(self._spin_angle2.value()))
        self._state.vel[0, 1] = 0.0
        self._state.vel[1, 1] = 0.0
        self._constrain_to_horizontal_line()
        self._ke_baseline = kinetic_energy(self._state)
        self._sync_graphics()
        self._canvas.draw_idle()

    def _append_history(self, ke: float, loss: float) -> None:
        self._hist_t.append(self._sim_time)
        self._hist_ke.append(ke)
        self._hist_loss.append(loss)
        if len(self._hist_t) > _HIST_CAP:
            self._hist_t.pop(0)
            self._hist_ke.pop(0)
            self._hist_loss.pop(0)

    def _update_plot_lines(self) -> None:
        if not self._hist_t:
            self._line_ke_tot.set_data([], [])
            self._line_ke_loss.set_data([], [])
            self._ax_energy.set_xlim(0.0, _TIME_WINDOW)
            return

        tt = np.asarray(self._hist_t, dtype=float)
        self._line_ke_tot.set_data(tt, np.asarray(self._hist_ke, dtype=float))
        self._line_ke_loss.set_data(tt, np.asarray(self._hist_loss, dtype=float))

        t_end = float(tt[-1])
        if t_end < _TIME_WINDOW:
            self._ax_energy.set_xlim(0.0, _TIME_WINDOW)
        else:
            t1 = max(0.0, t_end - _TIME_WINDOW)
            self._ax_energy.set_xlim(t1, t_end + 1e-6)

        self._ax_energy.relim()
        self._ax_energy.autoscale_view(scalex=False, scaley=True)

    def _sync_graphics(self) -> None:
        if self._state is None:
            return
        s = self._state
        self._circ1.set_center((float(s.pos[0, 0]), float(s.pos[0, 1])))
        self._circ2.set_center((float(s.pos[1, 0]), float(s.pos[1, 1])))
        self._circ1.set_radius(float(s.r[0]))
        self._circ2.set_radius(float(s.r[1]))

        v1m = float(np.linalg.norm(s.vel[0]))
        v2m = float(np.linalg.norm(s.vel[1]))
        off = 0.042
        self._txt_ball1.set_position((float(s.pos[0, 0]), float(s.pos[0, 1]) + float(s.r[0]) + off))
        self._txt_ball2.set_position((float(s.pos[1, 0]), float(s.pos[1, 1]) + float(s.r[1]) + off))
        self._txt_ball1.set_text(f"|v|={v1m:.2f} m/s\n球1\nm={float(s.m[0]):.2f} kg")
        self._txt_ball2.set_text(f"|v|={v2m:.2f} m/s\n球2\nm={float(s.m[1]):.2f} kg")

    def _on_tick(self) -> None:
        if self._state is None:
            return

        if not self._paused:
            dt = (float(self._timer.interval()) / 1000.0) * float(self._spin_playback.value())
            step_state(self._state, dt, BOX_W, BOX_H, self._ball_e(), substeps=18)
            self._sim_time += dt

            ke = kinetic_energy(self._state)
            loss = max(0.0, float(self._ke_baseline) - ke)
            self._append_history(ke, loss)

        self._constrain_to_horizontal_line()
        self._sync_graphics()
        self._update_plot_lines()
        self._canvas.draw_idle()

    def _on_pause_toggle(self) -> None:
        if not self._sim_running:
            return
        self._paused = not self._paused
        self._btn_pause.setText("继续" if self._paused else "暂停")

    def _on_back_teaching(self) -> None:
        self._paused = False
        self._btn_pause.setText("暂停")
        self._stack.setCurrentIndex(0)
