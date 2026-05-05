# -*- coding: utf-8 -*-
"""
实验三：双摆混沌模型 — 教学视图 + 仿真实验室（RK4 微步实时积分、相空间与能量监控）。
"""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
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
from ui.scalable_textbook_image import ScalableTextbookImage
from engine.pendulum_calc import G_DEFAULT, state_cartesian, state_mechanics, step_double_pendulum_rk4
from ui.mpl_setup import configure_matplotlib_chinese_font
from ui.teaching_chat_helper import TeachingChatHelper

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEXTBOOK_PATH = _PROJECT_ROOT / "assets" / "long_images" / "双摆与混沌.png"

_TRAIL_MAXLEN = 100
_PHASE_MAXLEN = 2500
_ENERGY_MAXLEN = 3500

TIMER_MS = 16

_LAB_FORMULA_STYLE = (
    "background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;"
    "padding:16px;color:#334155;font-size:13pt;line-height:165%;"
)
_LAB_SECTION_TITLE_STYLE = "font-weight:600;font-size:13pt;color:#0f172a;padding-bottom:4px;"


def _card_shadow(widget: QWidget, blur: int = 22, dy: int = 3) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, dy)
    effect.setColor(QColor(15, 23, 42, 38))
    widget.setGraphicsEffect(effect)


class PagePendulum(QWidget):
    """实验三：教材 / AI / 双摆仿真实验室。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._on_tick)

        self._y: Optional[np.ndarray] = None
        self._sim_time = 0.0
        self._running = False
        self._paused = False
        self._dirty = True

        self._trail: Deque[Tuple[float, float]] = deque(maxlen=_TRAIL_MAXLEN)
        self._phase_pts: Deque[Tuple[float, float]] = deque(maxlen=_PHASE_MAXLEN)
        self._energy_t: List[float] = []
        self._energy_ke: List[float] = []
        self._energy_pe: List[float] = []
        self._energy_et: List[float] = []

        self._line_rods = None
        self._scatter_balls = None
        self._line_trail = None
        self._line_phase = None
        self._line_ke = None
        self._line_pe = None
        self._line_etot = None
        self._ax_anim = None
        self._ax_phase = None
        self._ax_energy = None
        self._phase_frame_i = 0

        self._pendulum_run_tag = ""
        self._trail_prev: List[Tuple[float, float]] = []
        self._phase_prev: List[Tuple[float, float]] = []
        self._trail_prev_caption = ""

        self._line_trail_prev = None
        self._line_phase_prev = None

        configure_matplotlib_chinese_font()
        self._chat_ai = TeachingChatHelper(self, "pendulum")
        self._build_ui()
        self._stack.currentChanged.connect(self._on_stack_changed)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._refresh_chat_webview)
        QTimer.singleShot(100, self._refresh_chat_webview)
        QTimer.singleShot(300, self._refresh_chat_webview)

    def _refresh_chat_webview(self):
        if hasattr(self, "_chat_log") and hasattr(self._chat_log, "force_refresh"):
            self._chat_log.force_refresh()

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
            QDoubleSpinBox, QSpinBox {
                font-size: 11pt;
                min-height: 30px;
            }
            QPushButton.SecondaryBtn {
                background-color: #e2e8f0;
                color: #1e293b;
                border: none;
                border-radius: 10px;
                padding: 12px 18px;
                font-weight: 600;
                font-size: 11pt;
            }
            QPushButton.SecondaryBtn:hover { background-color: #cbd5e1; }
            QPushButton.SecondaryBtn:disabled {
                background-color: #f1f5f9;
                color: #94a3b8;
            }
            QPushButton.PrimaryXL {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 14px;
                padding: 20px 26px;
                font-weight: 700;
                font-size: 14pt;
            }
            QPushButton.PrimaryXL:hover { background-color: #2563eb; }
            QPushButton.ToolBtn {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 12px 18px;
                font-weight: 600;
                font-size: 11pt;
            }
            QPushButton.ToolBtn:hover { background-color: #2563eb; }
            QPushButton.ToolBtn:disabled {
                background-color: #cbd5e1;
                color: #64748b;
            }
            QLineEdit.ChatInput {
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 11px 13px;
                background: #ffffff;
                font-size: 11pt;
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
        title_l.setStyleSheet("font-weight:600;font-size:13.5pt;color:#0f172a;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setAlignment(Qt.AlignTop)

        pic = ScalableTextbookImage(
            _TEXTBOOK_PATH,
            decode_fail_text="无法解码 pendulum_textbook.png。",
            missing_file_text=(
                "未找到 assets/pendulum_textbook.png。\n"
                "放入教材插图后可在此展示；当前为占位提示。"
            ),
        )

        scroll.setWidget(pic)
        left_lay.addWidget(title_l)
        left_lay.addWidget(scroll, stretch=1)

        right_inner = QWidget()
        rl = QVBoxLayout(right_inner)
        rl.setSpacing(14)

        title_r = QLabel("AI 智能助教")
        title_r.setStyleSheet("font-weight:600;font-size:13.5pt;color:#0f172a;")

        self._chat_log = MarkdownFormulaViewer()
        self._chat_log.set_markdown(
            "可提问双摆方程、混沌初值敏感性或能量与阻尼。请先在主窗口「设置 → DeepSeek API 密钥」保存密钥。"
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
        btn_lab.setMinimumHeight(62)
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
        ctrl.setMinimumWidth(390)
        ctrl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        cv = QVBoxLayout(ctrl)
        cv.setSpacing(12)

        btn_back = QPushButton("← 返回教学页面")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._on_back_teaching)

        self._formula_lab = QLabel()
        self._formula_lab.setWordWrap(True)
        self._formula_lab.setStyleSheet(_LAB_FORMULA_STYLE)
        self._formula_lab.setText(
            "<b>状态</b>：<i>y = [θ₁, ω₁, θ₂, ω₂]</i>（rad）。<br/>"
            "<b>阻尼</b>：角加速度叠加 <i>−c·ω₁</i>、<i>−c·ω₂</i>（<i>c=0</i> 时机械能近似守恒）。<br/>"
            "<b>积分</b>：UI 周期 <b>16 ms</b>；每帧仿真宏步 <i>Δt = 0.016×播放倍速</i>；"
            "引擎内拆分为微步 <i>h≈10⁻³ s</i> 的 <b>RK4</b> 循环。"
        )

        form = QFormLayout()
        form.setSpacing(12)
        form.setHorizontalSpacing(12)

        self._slider_L1 = QSlider(Qt.Horizontal)
        self._slider_L1.setRange(50, 200)
        self._slider_L1.setValue(100)
        self._lbl_L1 = QLabel("1.00 m")
        self._slider_L2 = QSlider(Qt.Horizontal)
        self._slider_L2.setRange(50, 200)
        self._slider_L2.setValue(100)
        self._lbl_L2 = QLabel("1.00 m")

        self._slider_m1 = QSlider(Qt.Horizontal)
        self._slider_m1.setRange(10, 500)
        self._slider_m1.setValue(100)
        self._lbl_m1 = QLabel("1.00 kg")
        self._slider_m2 = QSlider(Qt.Horizontal)
        self._slider_m2.setRange(10, 500)
        self._slider_m2.setValue(100)
        self._lbl_m2 = QLabel("1.00 kg")

        self._slider_th1 = QSlider(Qt.Horizontal)
        self._slider_th1.setRange(-1800, 1800)
        self._slider_th1.setValue(1200)
        self._spin_th1 = QDoubleSpinBox()
        self._spin_th1.setRange(-180.0, 180.0)
        self._spin_th1.setDecimals(2)
        self._spin_th1.setSingleStep(0.1)
        self._spin_th1.setValue(120.0)
        self._spin_th1.setSuffix(" °")

        self._slider_th2 = QSlider(Qt.Horizontal)
        self._slider_th2.setRange(-1800, 1800)
        self._slider_th2.setValue(-900)
        self._spin_th2 = QDoubleSpinBox()
        self._spin_th2.setRange(-180.0, 180.0)
        self._spin_th2.setDecimals(2)
        self._spin_th2.setSingleStep(0.1)
        self._spin_th2.setValue(-90.0)
        self._spin_th2.setSuffix(" °")

        self._spin_scale = QDoubleSpinBox()
        self._spin_scale.setRange(0.1, 5.0)
        self._spin_scale.setDecimals(2)
        self._spin_scale.setSingleStep(0.1)
        self._spin_scale.setValue(5.0)
        self._spin_scale.setSuffix(" ×")

        self._spin_c_damp = QDoubleSpinBox()
        self._spin_c_damp.setRange(0.0, 2.0)
        self._spin_c_damp.setDecimals(3)
        self._spin_c_damp.setSingleStep(0.01)
        self._spin_c_damp.setValue(0.05)
        self._spin_c_damp.setSuffix(" s⁻¹")
        self._spin_c_damp.setToolTip("关节粘性阻尼：角运动方程中叠加与角速度成正比的耗散项，c 的单位为 1/s")

        self._spin_tmax = QDoubleSpinBox()
        self._spin_tmax.setRange(5.0, 120.0)
        self._spin_tmax.setDecimals(1)
        self._spin_tmax.setSingleStep(5.0)
        self._spin_tmax.setValue(60.0)
        self._spin_tmax.setSuffix(" s")
        self._spin_tmax.setToolTip("仿真时间到达该上限后自动停止")

        for sl in (
            self._slider_L1,
            self._slider_L2,
            self._slider_m1,
            self._slider_m2,
            self._slider_th1,
            self._slider_th2,
        ):
            sl.setMinimumHeight(28)

        self._slider_L1.valueChanged.connect(self._on_L1_slider)
        self._slider_L2.valueChanged.connect(self._on_L2_slider)
        self._slider_m1.valueChanged.connect(self._on_m1_slider)
        self._slider_m2.valueChanged.connect(self._on_m2_slider)
        self._slider_th1.valueChanged.connect(self._on_th1_slider)
        self._slider_th2.valueChanged.connect(self._on_th2_slider)
        self._spin_th1.valueChanged.connect(self._on_th1_spin)
        self._spin_th2.valueChanged.connect(self._on_th2_spin)
        self._spin_scale.valueChanged.connect(self._mark_dirty)
        self._spin_c_damp.valueChanged.connect(self._mark_dirty)
        self._spin_tmax.valueChanged.connect(self._mark_dirty)

        form.addRow("摆长 L₁ (m)：", self._slider_label_row(self._slider_L1, self._lbl_L1))
        form.addRow("摆长 L₂ (m)：", self._slider_label_row(self._slider_L2, self._lbl_L2))
        form.addRow("质量 m₁ (kg)：", self._slider_label_row(self._slider_m1, self._lbl_m1))
        form.addRow("质量 m₂ (kg)：", self._slider_label_row(self._slider_m2, self._lbl_m2))
        form.addRow("初始 θ₁ (°)：", self._angle_row(self._slider_th1, self._spin_th1))
        form.addRow("初始 θ₂ (°)：", self._angle_row(self._slider_th2, self._spin_th2))
        form.addRow("播放倍速：", self._spin_scale)
        form.addRow("阻尼系数 c (1/s)：", self._spin_c_damp)
        form.addRow("仿真时长上限：", self._spin_tmax)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self._btn_start = QPushButton("开始仿真")
        self._btn_start.setObjectName("ToolBtn")
        self._btn_pause = QPushButton("暂停")
        self._btn_pause.setObjectName("SecondaryBtn")
        self._btn_pause.setEnabled(False)
        self._btn_reset = QPushButton("重置")
        self._btn_reset.setObjectName("ToolBtn")
        self._btn_start.clicked.connect(self._on_start)
        self._btn_pause.clicked.connect(self._on_pause_toggle)
        self._btn_reset.clicked.connect(self._on_reset)
        btn_row.addWidget(self._btn_start)
        btn_row.addWidget(self._btn_pause)
        btn_row.addWidget(self._btn_reset)

        hint = QLabel(
            "提示：<i>c=0</i> 时总能量曲线近似水平；<i>c&gt;0</i> 时机械能逐渐减小。"
            "橙色线为 m₂ 拖尾；再次「开始仿真」或「重置」后保留<b>上次</b>拖尾与相轨（灰色虚线）作对照。"
            "每帧 RK4 微步推进。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#64748b;font-size:12pt;line-height:155%;")

        cv.addWidget(btn_back)
        cv.addWidget(self._formula_lab)
        title_params = QLabel("参数")
        title_params.setStyleSheet(_LAB_SECTION_TITLE_STYLE)
        cv.addWidget(title_params)
        cv.addLayout(form)
        cv.addLayout(btn_row)
        cv.addWidget(hint)
        cv.addStretch()

        plot = QWidget()
        pv = QVBoxLayout(plot)
        pv.setContentsMargins(4, 4, 4, 4)

        self._fig = Figure(figsize=(10.2, 6.2), dpi=100, layout="constrained")
        self._fig.patch.set_facecolor("#f8fafc")
        gs = self._fig.add_gridspec(2, 2, width_ratios=[1.18, 1.0], height_ratios=[1.0, 1.0])

        self._ax_anim = self._fig.add_subplot(gs[:, 0])
        self._ax_anim.set_facecolor("#ffffff")
        self._ax_anim.set_title("双摆动画", color="#0f172a")
        self._ax_anim.set_xlabel("x / m")
        self._ax_anim.set_ylabel("y / m")
        self._ax_anim.set_aspect("equal", adjustable="box")
        self._ax_anim.grid(True, linestyle="--", linewidth=0.5, alpha=0.35)

        self._ax_phase = self._fig.add_subplot(gs[0, 1])
        self._ax_phase.set_facecolor("#ffffff")
        self._ax_phase.set_title("下摆相空间 (θ₂ — ω₂)", color="#0f172a")
        self._ax_phase.set_xlabel("θ₂ / rad")
        self._ax_phase.set_ylabel("ω₂ / (rad·s⁻¹)")
        self._ax_phase.grid(True, linestyle="--", linewidth=0.5, alpha=0.35)

        self._ax_energy = self._fig.add_subplot(gs[1, 1])
        self._ax_energy.set_facecolor("#ffffff")
        self._ax_energy.set_title("系统机械能", color="#0f172a")
        self._ax_energy.set_xlabel("t / s")
        self._ax_energy.set_ylabel("E / J")
        self._ax_energy.grid(True, linestyle="--", linewidth=0.5, alpha=0.35)

        (self._line_rods,) = self._ax_anim.plot([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], color="#1e293b", linewidth=2.4, zorder=3)
        self._scatter_balls = self._ax_anim.scatter(
            [0.0, 0.0], [0.0, 0.0], s=[140, 140], c=["#3b82f6", "#ef4444"], zorder=5, edgecolors="#ffffff", linewidths=1.5
        )
        self._ax_anim.plot([0.0], [0.0], marker="s", color="#64748b", markersize=5, zorder=4)
        (self._line_trail,) = self._ax_anim.plot([], [], color="#f97316", linewidth=1.4, alpha=0.88, zorder=2)
        (self._line_trail_prev,) = self._ax_anim.plot(
            [], [], color="#64748b", linewidth=1.2, linestyle="--", alpha=0.65, zorder=1
        )

        (self._line_phase,) = self._ax_phase.plot([], [], color="#2563eb", linewidth=0.9, alpha=0.75)
        (self._line_phase_prev,) = self._ax_phase.plot(
            [], [], color="#94a3b8", linewidth=0.75, linestyle="--", alpha=0.55
        )

        (self._line_ke,) = self._ax_energy.plot([], [], color="#16a34a", linewidth=1.3, label="动能", alpha=0.9)
        (self._line_pe,) = self._ax_energy.plot([], [], color="#ca8a04", linewidth=1.3, label="势能", alpha=0.9)
        (self._line_etot,) = self._ax_energy.plot([], [], color="#2563eb", linewidth=1.5, label="总机械能", alpha=0.95)
        self._ax_energy.legend(loc="upper right", fontsize=8, framealpha=0.92)

        self._canvas = FigureCanvas(self._fig)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pv.addWidget(self._canvas)

        sp = QSplitter(Qt.Horizontal)
        sp.addWidget(self._wrap_card(ctrl))
        sp.addWidget(self._wrap_card(plot, margins=(12, 12, 12, 12)))
        sp.setStretchFactor(0, 30)
        sp.setStretchFactor(1, 70)
        sp.setSizes([400, 720])

        root.addWidget(sp)
        self._refresh_transport_buttons()
        return page

    def _slider_label_row(self, slider: QSlider, lbl: QLabel) -> QWidget:
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(slider, stretch=1)
        lbl.setMinimumWidth(72)
        lbl.setStyleSheet("color:#334155;font-weight:600;")
        row.addWidget(lbl)
        w = QWidget()
        w.setLayout(row)
        return w

    def _angle_row(self, slider: QSlider, spin: QDoubleSpinBox) -> QWidget:
        row = QVBoxLayout()
        row.setSpacing(6)
        top = QHBoxLayout()
        top.addWidget(slider, stretch=1)
        spin.setMinimumWidth(100)
        top.addWidget(spin)
        row.addLayout(top)
        w = QWidget()
        w.setLayout(row)
        return w

    def _L_from_slider(self, v: int) -> float:
        return 0.5 + (v - 50) / 150.0 * (2.0 - 0.5)

    def _m_from_slider(self, v: int) -> float:
        return v / 100.0

    def _on_L1_slider(self, v: int) -> None:
        self._lbl_L1.setText(f"{self._L_from_slider(v):.2f} m")
        self._mark_dirty()

    def _on_L2_slider(self, v: int) -> None:
        self._lbl_L2.setText(f"{self._L_from_slider(v):.2f} m")
        self._mark_dirty()

    def _on_m1_slider(self, v: int) -> None:
        self._lbl_m1.setText(f"{self._m_from_slider(v):.2f} kg")
        self._mark_dirty()

    def _on_m2_slider(self, v: int) -> None:
        self._lbl_m2.setText(f"{self._m_from_slider(v):.2f} kg")
        self._mark_dirty()

    def _on_th1_slider(self, v: int) -> None:
        deg = v / 10.0
        self._spin_th1.blockSignals(True)
        self._spin_th1.setValue(deg)
        self._spin_th1.blockSignals(False)
        self._mark_dirty()

    def _on_th2_slider(self, v: int) -> None:
        deg = v / 10.0
        self._spin_th2.blockSignals(True)
        self._spin_th2.setValue(deg)
        self._spin_th2.blockSignals(False)
        self._mark_dirty()

    def _on_th1_spin(self, val: float) -> None:
        iv = int(round(float(val) * 10.0))
        iv = max(-1800, min(1800, iv))
        self._slider_th1.blockSignals(True)
        self._slider_th1.setValue(iv)
        self._slider_th1.blockSignals(False)
        self._mark_dirty()

    def _on_th2_spin(self, val: float) -> None:
        iv = int(round(float(val) * 10.0))
        iv = max(-1800, min(1800, iv))
        self._slider_th2.blockSignals(True)
        self._slider_th2.setValue(iv)
        self._slider_th2.blockSignals(False)
        self._mark_dirty()

    def _mark_dirty(self, *_a: object) -> None:
        self._dirty = True

    def _physics_params(self) -> Tuple[float, float, float, float]:
        return (
            self._m_from_slider(self._slider_m1.value()),
            self._m_from_slider(self._slider_m2.value()),
            self._L_from_slider(self._slider_L1.value()),
            self._L_from_slider(self._slider_L2.value()),
        )

    def _reset_energy_buffers(self) -> None:
        self._energy_t.clear()
        self._energy_ke.clear()
        self._energy_pe.clear()
        self._energy_et.clear()

    def _pendulum_run_label(self) -> str:
        c = float(self._spin_c_damp.value())
        t1 = float(self._spin_th1.value())
        t2 = float(self._spin_th2.value())
        return f"c={c:.4g}, θ₁={t1:.1f}°, θ₂={t2:.1f}°"

    def _append_energy_point(self, t: float, ke: float, pe: float, et: float) -> None:
        self._energy_t.append(t)
        self._energy_ke.append(ke)
        self._energy_pe.append(pe)
        self._energy_et.append(et)
        if len(self._energy_t) > _ENERGY_MAXLEN:
            del self._energy_t[0]
            del self._energy_ke[0]
            del self._energy_pe[0]
            del self._energy_et[0]

    def _init_simulation(self) -> None:
        if len(self._trail) >= 2:
            self._trail_prev = list(self._trail)
            self._phase_prev = list(self._phase_pts)
            self._trail_prev_caption = self._pendulum_run_tag

        m1, m2, L1, L2 = self._physics_params()
        th1 = np.deg2rad(self._spin_th1.value())
        th2 = np.deg2rad(self._spin_th2.value())
        self._y = np.array([th1, 0.0, th2, 0.0], dtype=float)
        self._sim_time = 0.0
        self._trail.clear()
        self._phase_pts.clear()
        self._phase_frame_i = 0
        self._reset_energy_buffers()

        lim = (L1 + L2) * 1.28 + 0.12
        self._ax_anim.set_xlim(-lim, lim)
        self._ax_anim.set_ylim(-lim, lim)

        self._ax_phase.set_xlim(-3.5, 3.5)
        self._ax_phase.set_ylim(-12.0, 12.0)

        self._line_phase.set_data([], [])
        self._line_trail.set_data([], [])
        self._line_ke.set_data([], [])
        self._line_pe.set_data([], [])
        self._line_etot.set_data([], [])
        self._ax_energy.set_xlim(0.0, max(5.0, float(self._spin_tmax.value()) * 0.05))
        self._ax_energy.set_ylim(-1.0, 1.0)

        if len(self._trail_prev) >= 2:
            px, py = zip(*self._trail_prev)
            self._line_trail_prev.set_data(px, py)
        else:
            self._line_trail_prev.set_data([], [])

        if len(self._phase_prev) >= 2:
            a, b = zip(*self._phase_prev)
            self._line_phase_prev.set_data(a, b)
        else:
            self._line_phase_prev.set_data([], [])

        info0 = state_mechanics(self._y, m1, m2, L1, L2, G_DEFAULT)
        self._append_energy_point(0.0, info0["ke"], info0["pe"], info0["e_total"])
        self._draw_state(info0)

        emax = max(abs(info0["ke"]), abs(info0["pe"]), abs(info0["e_total"]), 0.5)
        self._ax_energy.set_ylim(-0.05 * emax, 1.15 * emax)

        self._pendulum_run_tag = self._pendulum_run_label()

        self._canvas.draw_idle()
        self._dirty = False

    def _draw_state(self, info: Dict[str, Any]) -> None:
        x1, y1, x2, y2 = info["x1"], info["y1"], info["x2"], info["y2"]
        self._line_rods.set_data([0.0, x1, x2], [0.0, y1, y2])
        self._scatter_balls.set_offsets(np.array([[x1, y1], [x2, y2]], dtype=float))

    def _expand_phase_limits(self, th2: float, w2: float) -> None:
        xmin, xmax = self._ax_phase.get_xlim()
        ymin, ymax = self._ax_phase.get_ylim()
        pad_x, pad_y = 0.25, 0.8
        if th2 < xmin + pad_x:
            xmin = th2 - 2.0 * pad_x
        if th2 > xmax - pad_x:
            xmax = th2 + 2.0 * pad_x
        if w2 < ymin + pad_y:
            ymin = w2 - 3.0 * pad_y
        if w2 > ymax - pad_y:
            ymax = w2 + 3.0 * pad_y
        self._ax_phase.set_xlim(xmin, xmax)
        self._ax_phase.set_ylim(ymin, ymax)

    def _update_energy_axes(self) -> None:
        if not self._energy_t:
            return
        t_arr = np.asarray(self._energy_t, dtype=float)
        self._line_ke.set_data(t_arr, np.asarray(self._energy_ke, dtype=float))
        self._line_pe.set_data(t_arr, np.asarray(self._energy_pe, dtype=float))
        self._line_etot.set_data(t_arr, np.asarray(self._energy_et, dtype=float))
        t_end = float(t_arr[-1])
        win = max(8.0, min(45.0, float(self._spin_tmax.value())))
        self._ax_energy.set_xlim(max(0.0, t_end - win), max(win * 0.1, t_end + 1e-6))
        ke_a = np.asarray(self._energy_ke, dtype=float)
        pe_a = np.asarray(self._energy_pe, dtype=float)
        et_a = np.asarray(self._energy_et, dtype=float)
        all_e = np.concatenate([ke_a, pe_a, et_a])
        lo = float(np.min(all_e))
        hi = float(np.max(all_e))
        span = max(hi - lo, 0.05)
        self._ax_energy.set_ylim(lo - 0.08 * span, hi + 0.12 * span)

    def _refresh_transport_buttons(self) -> None:
        if not hasattr(self, "_btn_start"):
            return
        self._btn_start.setEnabled(not self._running)
        self._btn_pause.setEnabled(self._running)
        self._btn_pause.setText("继续" if self._paused else "暂停")

    def _on_stack_changed(self, idx: int) -> None:
        if idx != 1:
            self._timer.stop()
            self._running = False
            self._paused = False
            self._refresh_transport_buttons()

    def _on_back_teaching(self) -> None:
        self._timer.stop()
        self._running = False
        self._paused = False
        self._refresh_transport_buttons()
        self._stack.setCurrentIndex(0)

    def _on_start(self) -> None:
        if self._dirty or self._y is None:
            self._init_simulation()
        self._paused = False
        self._running = True
        self._refresh_transport_buttons()
        self._timer.start()

    def _on_pause_toggle(self) -> None:
        if not self._running:
            return
        self._paused = not self._paused
        self._btn_pause.setText("继续" if self._paused else "暂停")

    def _on_reset(self) -> None:
        self._timer.stop()
        self._running = False
        self._paused = False
        self._dirty = True
        self._init_simulation()
        self._refresh_transport_buttons()

    def _on_tick(self) -> None:
        if not self._running or self._paused or self._y is None:
            return

        t_cap = float(self._spin_tmax.value())
        if self._sim_time >= t_cap - 1e-9:
            self._timer.stop()
            self._running = False
            self._paused = False
            self._refresh_transport_buttons()
            return

        macro_dt = (self._timer.interval() / 1000.0) * float(self._spin_scale.value())
        macro_dt = min(macro_dt, max(0.0, t_cap - self._sim_time))

        m1, m2, L1, L2 = self._physics_params()
        c_damp = float(self._spin_c_damp.value())

        self._y, info = step_double_pendulum_rk4(
            self._y,
            m1=m1,
            m2=m2,
            L1=L1,
            L2=L2,
            g=G_DEFAULT,
            c_damp=c_damp,
            macro_dt=macro_dt,
        )
        self._sim_time += macro_dt

        self._draw_state(info)
        x2, y2 = info["x2"], info["y2"]
        self._trail.append((x2, y2))
        th2 = float(self._y[2])
        w2 = float(self._y[3])
        self._phase_pts.append((th2, w2))
        if self._phase_frame_i % 3 == 0:
            self._expand_phase_limits(th2, w2)
        self._phase_frame_i += 1

        if len(self._trail) >= 2:
            xs, ys = zip(*self._trail)
            self._line_trail.set_data(xs, ys)
        else:
            self._line_trail.set_data([], [])

        if self._phase_pts:
            a, b = zip(*self._phase_pts)
            self._line_phase.set_data(a, b)

        self._append_energy_point(self._sim_time, info["ke"], info["pe"], info["e_total"])
        self._update_energy_axes()

        self._canvas.draw_idle()

        if self._sim_time >= t_cap - 1e-9:
            self._timer.stop()
            self._running = False
            self._paused = False
            self._refresh_transport_buttons()
