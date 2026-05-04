# -*- coding: utf-8 -*-
"""
实验一：考虑空气阻力的抛物运动 — 教学视图 + 仿真实验室（内嵌 Matplotlib 动画）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPixmap
from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from engine.projectile_calc import (
    G_DEFAULT,
    Y_LAUNCH_EPS,
    calculate_projectile,
    projectile_mechanics_from_state,
    step_projectile_rk4,
)
from ui.mpl_setup import configure_matplotlib_chinese_font
from ui.teaching_chat_helper import TeachingChatHelper

# 教材插图路径（相对于本文件：ui/ → 项目根）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

TIMER_MS = 16
_TEXTBOOK_PATH = _PROJECT_ROOT / "assets" / "projectile_textbook.png"


def _card_shadow(widget: QWidget, blur: int = 22, dy: int = 3) -> None:
    """为卡片控件添加柔和阴影（补充全局 QSS 无法实现的层次感）。"""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, dy)
    effect.setColor(QColor(15, 23, 42, 38))
    widget.setGraphicsEffect(effect)


class PageProjectile(QWidget):
    """抛物运动实验页：默认教学视图，可切换至仿真实验室。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_MS)  # 约 60 Hz，宏观仿真步长 = TIMER_MS/1000 × 倍速
        self._timer.timeout.connect(self._on_animation_tick)

        self._paused = False
        self._y_drag_state: Optional[np.ndarray] = None
        self._t_drag_sim = 0.0
        self._drag_finished = False
        self._hist_t: list[float] = []
        self._hist_x: list[float] = []
        self._hist_y: list[float] = []
        self._hist_vx: list[float] = []
        self._hist_vy: list[float] = []
        self._hist_ke: list[float] = []
        self._hist_pe: list[float] = []
        self._hist_e: list[float] = []

        self._line_ideal = None
        self._line_drag = None
        self._scatter_pt = None

        self._line_v_ideal = None
        self._line_v_drag = None
        self._line_y_macro_ideal = None
        self._line_y_macro_drag = None
        self._vline_speed = None
        self._vline_height = None
        self._line_e_ke = None
        self._line_e_pe = None
        self._line_e_tot = None
        self._pack_ideal: Optional[Dict[str, Any]] = None
        self._pack_drag: Optional[Dict[str, Any]] = None

        configure_matplotlib_chinese_font()
        self._chat_ai = TeachingChatHelper(self, "projectile")
        self._build_ui()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(10)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_teaching_view())
        self._stack.addWidget(self._build_lab_view())
        outer.addWidget(self._stack, stretch=1)

        self._apply_local_styles()

    def _apply_local_styles(self) -> None:
        """页面级 QSS：卡片留白、次要按钮、强调按钮 hover。"""
        self.setStyleSheet(
            """
            QFrame.CardPanel {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }
            QLabel.SectionTitle {
                font-weight: 600;
                font-size: 12pt;
                color: #0f172a;
                padding-bottom: 6px;
            }
            QPushButton.SecondaryBtn {
                background-color: #e2e8f0;
                color: #1e293b;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: 600;
            }
            QPushButton.SecondaryBtn:hover {
                background-color: #cbd5e1;
            }
            QPushButton.PrimaryXL {
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 14px;
                padding: 18px 24px;
                font-weight: 700;
                font-size: 13pt;
            }
            QPushButton.PrimaryXL:hover {
                background-color: #2563eb;
            }
            QPushButton.PrimaryXL:pressed {
                background-color: #1d4ed8;
            }
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
                min-width: 72px;
                max-width: 110px;
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

        # 左侧：教材（约 60%）
        left_inner = QWidget()
        left_lay = QVBoxLayout(left_inner)
        left_lay.setSpacing(10)
        title_l = QLabel("教材讲解")
        title_l.setProperty("class", "SectionTitle")
        title_l.setStyleSheet("font-weight:600;font-size:12pt;color:#0f172a;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        pic_holder = QLabel()
        pic_holder.setAlignment(Qt.AlignCenter)
        pic_holder.setMinimumHeight(280)
        pic_holder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if _TEXTBOOK_PATH.is_file():
            pix = QPixmap(str(_TEXTBOOK_PATH))
            if not pix.isNull():
                pic_holder.setPixmap(pix.scaledToWidth(780, Qt.SmoothTransformation))
                pic_holder.setScaledContents(False)
            else:
                pic_holder.setText("无法解码教材图片，请检查 assets/projectile_textbook.png 格式。")
        else:
            pic_holder.setText(
                "未找到 assets/projectile_textbook.png。\n"
                "请将教材长图放入该路径后重启应用；当前为占位提示。"
            )
            pic_holder.setWordWrap(True)

        scroll.setWidget(pic_holder)
        left_lay.addWidget(title_l)
        left_lay.addWidget(scroll, stretch=1)

        # 右侧：AI + 入口（约 40%）
        right_inner = QWidget()
        right_lay = QVBoxLayout(right_inner)
        right_lay.setSpacing(14)

        title_r = QLabel("AI 智能助教")
        title_r.setStyleSheet("font-weight:600;font-size:12pt;color:#0f172a;")

        self._chat_log = QTextBrowser()
        self._chat_log.setObjectName("ChatLog")
        self._chat_log.setOpenExternalLinks(False)
        self._chat_log.setHtml(
            "<p style='color:#64748b;'>您好！可提问抛物运动、空气阻力模型或仿真现象。"
            "请先通过主窗口菜单「设置 → DeepSeek API 密钥」保存密钥；回复由 DeepSeek 生成。</p>"
        )

        input_row = QHBoxLayout()
        self._chat_input = QLineEdit()
        self._chat_input.setPlaceholderText("输入问题后点击发送…")
        self._chat_input.setObjectName("ChatInput")
        self._btn_chat_send = QPushButton("发送")
        self._btn_chat_send.setObjectName("ToolBtn")
        self._chat_ai.attach(self._chat_log, self._chat_input, self._btn_chat_send)
        self._btn_chat_send.clicked.connect(self._chat_ai.on_send)
        self._chat_input.returnPressed.connect(self._chat_ai.on_send)
        input_row.addWidget(self._chat_input, stretch=1)
        input_row.addWidget(self._btn_chat_send)

        btn_lab = QPushButton("进入仿真实验室")
        btn_lab.setObjectName("PrimaryXL")
        btn_lab.setMinimumHeight(58)
        btn_lab.setCursor(Qt.PointingHandCursor)
        btn_lab.clicked.connect(lambda: self._stack.setCurrentIndex(1))

        right_lay.addWidget(title_r)
        right_lay.addWidget(self._chat_log, stretch=1)
        right_lay.addLayout(input_row)
        right_lay.addWidget(btn_lab)

        layout.addWidget(self._wrap_card(left_inner), stretch=6)
        layout.addWidget(self._wrap_card(right_inner), stretch=4)
        return page

    def _build_lab_view(self) -> QWidget:
        page = QWidget()
        root = QHBoxLayout(page)
        root.setSpacing(16)

        # 左侧控制（约 30%）
        ctrl_inner = QWidget()
        cv = QVBoxLayout(ctrl_inner)
        cv.setSpacing(14)

        btn_back = QPushButton("← 返回教学页面")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._on_back_to_teaching)

        formula = QLabel(
            "<b>状态</b>：<i>s</i> = [<i>x</i>, <i>y</i>, <i>v<sub>x</sub></i>, <i>v<sub>y</sub></i>]<sup>T</sup><br/>"
            "<b>重力加速度</b>：<i>g</i> = 9.81 m/s²（与 <code>engine/projectile_calc.py</code> 中常量一致）<br/>"
            "<b>理想（无阻力）</b>：<br/>"
            "d<i>x</i>/d<i>t</i> = <i>v<sub>x</sub></i>,  d<i>y</i>/d<i>t</i> = <i>v<sub>y</sub></i><br/>"
            "d<i>v<sub>x</sub></i>/d<i>t</i> = 0,  d<i>v<sub>y</sub></i>/d<i>t</i> = −<i>g</i><br/>"
            "<b>有阻力（与速率平方成正比，方向与速度相反）</b>：<br/>"
            "d<i>v<sub>x</sub></i>/d<i>t</i> = −(<i>k</i>/<i>m</i>)|<i><b>v</b></i>|<i>v<sub>x</sub></i>,  "
            "d<i>v<sub>y</sub></i>/d<i>t</i> = −<i>g</i> − (<i>k</i>/<i>m</i>)|<i><b>v</b></i>|<i>v<sub>y</sub></i><br/>"
            "<b>仿真实验室</b>：理想轨迹仍由 SciPy 一次性积分给出作对照；"
            "<b>有阻力</b>轨迹与能量曲线由固定 "
            f"{TIMER_MS} ms UI 节拍 × 回放倍速 作为宏观步长，在引擎内对同一方程做经典 RK4 微步递推得到。"
        )
        formula.setWordWrap(True)
        formula.setStyleSheet(
            "background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:12px;color:#334155;"
        )

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self._slider_v0 = QSlider(Qt.Horizontal)
        self._slider_v0.setRange(10, 100)
        self._slider_v0.setValue(40)
        self._spin_v0 = QSpinBox()
        self._spin_v0.setRange(10, 100)
        self._spin_v0.setSuffix(" m/s")
        self._spin_v0.setValue(self._slider_v0.value())
        self._slider_v0.valueChanged.connect(self._sync_v0_from_slider)
        self._spin_v0.valueChanged.connect(self._sync_v0_from_spin)

        self._slider_deg = QSlider(Qt.Horizontal)
        self._slider_deg.setRange(0, 90)
        self._slider_deg.setValue(45)
        self._spin_deg = QSpinBox()
        self._spin_deg.setRange(0, 90)
        self._spin_deg.setSuffix(" °")
        self._spin_deg.setValue(self._slider_deg.value())
        self._slider_deg.valueChanged.connect(self._sync_deg_from_slider)
        self._spin_deg.valueChanged.connect(self._sync_deg_from_spin)

        self._spin_k = QDoubleSpinBox()
        self._spin_k.setRange(0.0, 0.5)
        self._spin_k.setDecimals(3)
        self._spin_k.setSingleStep(0.005)
        self._spin_k.setValue(0.05)

        self._spin_m = QDoubleSpinBox()
        self._spin_m.setRange(0.1, 10.0)
        self._spin_m.setDecimals(2)
        self._spin_m.setSingleStep(0.1)
        self._spin_m.setValue(1.0)
        self._spin_m.setSuffix(" kg")

        # 直接键盘输入（回车或失去焦点时写入合法范围并同步滑块）
        self._edit_v0 = QLineEdit()
        self._edit_v0.setObjectName("ParamEdit")
        self._edit_v0.setPlaceholderText("输入")
        self._edit_v0.setToolTip("直接输入初速度，单位 m/s，范围 10–100")
        self._edit_v0.editingFinished.connect(self._apply_v0_from_edit)

        self._edit_deg = QLineEdit()
        self._edit_deg.setObjectName("ParamEdit")
        self._edit_deg.setPlaceholderText("输入")
        self._edit_deg.setToolTip("直接输入发射角，单位 °，范围 0–90")
        self._edit_deg.editingFinished.connect(self._apply_deg_from_edit)

        self._edit_k = QLineEdit()
        self._edit_k.setObjectName("ParamEdit")
        self._edit_k.setPlaceholderText("输入")
        self._edit_k.setToolTip("直接输入阻力系数 k，范围 0–0.5")
        self._edit_k.editingFinished.connect(self._apply_k_from_edit)

        self._edit_m = QLineEdit()
        self._edit_m.setObjectName("ParamEdit")
        self._edit_m.setPlaceholderText("输入")
        self._edit_m.setToolTip("直接输入质量，单位 kg，范围 0.1–10")
        self._edit_m.editingFinished.connect(self._apply_m_from_edit)

        self._spin_k.valueChanged.connect(self._sync_k_edit)
        self._spin_m.valueChanged.connect(self._sync_m_edit)

        row_v0 = QHBoxLayout()
        row_v0.addWidget(self._slider_v0, stretch=1)
        row_v0.addWidget(self._spin_v0)
        row_v0.addWidget(self._edit_v0)
        w_v0 = QWidget()
        w_v0.setLayout(row_v0)

        row_deg = QHBoxLayout()
        row_deg.addWidget(self._slider_deg, stretch=1)
        row_deg.addWidget(self._spin_deg)
        row_deg.addWidget(self._edit_deg)
        w_deg = QWidget()
        w_deg.setLayout(row_deg)

        row_k = QHBoxLayout()
        row_k.addWidget(self._spin_k, stretch=1)
        row_k.addWidget(self._edit_k)
        w_k = QWidget()
        w_k.setLayout(row_k)

        row_m = QHBoxLayout()
        row_m.addWidget(self._spin_m, stretch=1)
        row_m.addWidget(self._edit_m)
        w_m = QWidget()
        w_m.setLayout(row_m)

        form.addRow("初速度 v₀：", w_v0)
        form.addRow("发射角 θ：", w_deg)
        form.addRow("阻力系数 k：", w_k)
        form.addRow("质量 m：", w_m)

        self._spin_playback = QDoubleSpinBox()
        self._spin_playback.setRange(0.1, 5.0)
        self._spin_playback.setDecimals(2)
        self._spin_playback.setSingleStep(0.1)
        self._spin_playback.setValue(1.0)
        self._spin_playback.setToolTip(
            f"回放倍速：每 {TIMER_MS} ms 推进的仿真时间为 ("
            f"{TIMER_MS}/1000)× 倍速（秒）。1.0 时约 1 s 仿真 / 1 s 墙钟。"
        )
        form.addRow("回放倍速：", self._spin_playback)

        self._refresh_param_edits_from_spins()

        btn_row = QHBoxLayout()
        self._btn_start = QPushButton("开始仿真")
        self._btn_pause = QPushButton("暂停")
        self._btn_reset = QPushButton("重置")
        for b in (self._btn_start, self._btn_pause, self._btn_reset):
            b.setObjectName("ToolBtn")
        self._btn_pause.setEnabled(False)
        self._btn_start.clicked.connect(self._on_start_simulation)
        self._btn_pause.clicked.connect(self._on_pause_toggle)
        self._btn_reset.clicked.connect(self._on_reset_simulation)
        btn_row.addWidget(self._btn_start)
        btn_row.addWidget(self._btn_pause)
        btn_row.addWidget(self._btn_reset)

        cv.addWidget(btn_back)
        cv.addWidget(QLabel("公式与模型"))
        cv.addWidget(formula)
        cv.addWidget(QLabel("参数与控制"))
        cv.addLayout(form)
        cv.addLayout(btn_row)
        cv.addStretch()

        # 右侧画布（约 70%）
        plot_inner = QWidget()
        pv = QVBoxLayout(plot_inner)
        pv.setContentsMargins(4, 4, 4, 4)

        self._fig = Figure(figsize=(6.4, 7.9), dpi=100)
        self._fig.patch.set_facecolor("#f8fafc")
        gs = self._fig.add_gridspec(3, 2, height_ratios=[2.15, 1.0, 0.92], hspace=0.36, wspace=0.28)

        self._ax = self._fig.add_subplot(gs[0, :])
        self._ax.set_facecolor("#ffffff")
        self._ax.set_title("轨迹对比：理想（虚线）与有阻力（RK4 实时，实线 + 当前位置）", color="#0f172a", pad=10)
        self._ax.set_xlabel("x / m")
        self._ax.set_ylabel("y / m")
        self._ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.35)

        self._ax_v = self._fig.add_subplot(gs[1, 0])
        self._ax_v.set_facecolor("#ffffff")
        self._ax_v.set_title("宏观：速率随时间", fontsize=10, color="#0f172a")
        self._ax_v.set_xlabel("t / s")
        self._ax_v.set_ylabel("|v| / (m·s⁻¹)")
        self._ax_v.grid(True, linestyle="--", linewidth=0.5, alpha=0.35)

        self._ax_y = self._fig.add_subplot(gs[1, 1])
        self._ax_y.set_facecolor("#ffffff")
        self._ax_y.set_title("宏观：高度随时间", fontsize=10, color="#0f172a")
        self._ax_y.set_xlabel("t / s")
        self._ax_y.set_ylabel("y / m")
        self._ax_y.grid(True, linestyle="--", linewidth=0.5, alpha=0.35)

        self._ax_e = self._fig.add_subplot(gs[2, :])
        self._ax_e.set_facecolor("#ffffff")
        self._ax_e.set_title("有阻力：机械能分量（RK4 状态）", fontsize=10, color="#0f172a")
        self._ax_e.set_xlabel("t / s")
        self._ax_e.set_ylabel("E / J")
        self._ax_e.grid(True, linestyle="--", linewidth=0.5, alpha=0.35)

        (self._line_ideal,) = self._ax.plot([], [], linestyle="--", linewidth=2.0, color="#94a3b8", label="无阻力")
        (self._line_drag,) = self._ax.plot([], [], linestyle="-", linewidth=2.2, color="#2563eb", label="有阻力")
        self._scatter_pt = self._ax.scatter([], [], s=85, color="#f97316", edgecolors="#ffffff", linewidths=1.2, zorder=5)
        self._ax.legend(loc="upper right", framealpha=0.9, fontsize=9)

        (self._line_v_ideal,) = self._ax_v.plot([], [], linestyle="--", linewidth=1.6, color="#94a3b8", label="无阻力 |v|")
        (self._line_v_drag,) = self._ax_v.plot([], [], linestyle="-", linewidth=1.8, color="#2563eb", label="有阻力 |v|")
        self._ax_v.legend(loc="upper right", fontsize=8, framealpha=0.92)

        (self._line_y_macro_ideal,) = self._ax_y.plot([], [], linestyle="--", linewidth=1.6, color="#94a3b8", label="无阻力 y")
        (self._line_y_macro_drag,) = self._ax_y.plot([], [], linestyle="-", linewidth=1.8, color="#2563eb", label="有阻力 y")
        self._ax_y.legend(loc="upper right", fontsize=8, framealpha=0.92)

        self._vline_speed = self._ax_v.axvline(0.0, color="#64748b", linestyle=":", linewidth=1.2, alpha=0.9)
        self._vline_height = self._ax_y.axvline(0.0, color="#64748b", linestyle=":", linewidth=1.2, alpha=0.9)
        self._vline_speed.set_visible(False)
        self._vline_height.set_visible(False)

        (self._line_e_ke,) = self._ax_e.plot([], [], linestyle="-", linewidth=1.6, color="#16a34a", label="动能")
        (self._line_e_pe,) = self._ax_e.plot([], [], linestyle="-", linewidth=1.6, color="#ca8a04", label="势能")
        (self._line_e_tot,) = self._ax_e.plot([], [], linestyle="-", linewidth=2.0, color="#7c3aed", label="总机械能")
        self._ax_e.legend(loc="upper right", fontsize=8, framealpha=0.92)

        self._canvas = FigureCanvas(self._fig)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pv.addWidget(self._canvas)

        splitter = QSplitter(Qt.Horizontal)
        left_card = self._wrap_card(ctrl_inner)
        right_card = self._wrap_card(plot_inner, margins=(12, 12, 12, 12))
        splitter.addWidget(left_card)
        splitter.addWidget(right_card)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)

        root.addWidget(splitter)
        return page

    # ------------------------------------------------------------------
    # 教学页逻辑
    # ------------------------------------------------------------------
    def _on_back_to_teaching(self) -> None:
        self._timer.stop()
        self._paused = False
        self._btn_pause.setEnabled(False)
        self._btn_pause.setText("暂停")
        self._stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # 参数同步
    # ------------------------------------------------------------------
    def _refresh_param_edits_from_spins(self) -> None:
        """根据当前 SpinBox 数值刷新右侧输入框显示。"""
        self._edit_v0.blockSignals(True)
        self._edit_v0.setText(str(self._spin_v0.value()))
        self._edit_v0.blockSignals(False)
        self._edit_deg.blockSignals(True)
        self._edit_deg.setText(str(self._spin_deg.value()))
        self._edit_deg.blockSignals(False)
        self._sync_k_edit()
        self._sync_m_edit()

    def _sync_k_edit(self, *_args: object) -> None:
        self._edit_k.blockSignals(True)
        self._edit_k.setText(f"{self._spin_k.value():.3f}")
        self._edit_k.blockSignals(False)

    def _sync_m_edit(self, *_args: object) -> None:
        self._edit_m.blockSignals(True)
        self._edit_m.setText(f"{self._spin_m.value():.2f}")
        self._edit_m.blockSignals(False)

    def _sync_v0_from_slider(self, val: int) -> None:
        self._spin_v0.blockSignals(True)
        self._spin_v0.setValue(val)
        self._spin_v0.blockSignals(False)
        self._edit_v0.blockSignals(True)
        self._edit_v0.setText(str(val))
        self._edit_v0.blockSignals(False)

    def _sync_v0_from_spin(self, val: int) -> None:
        self._slider_v0.blockSignals(True)
        self._slider_v0.setValue(val)
        self._slider_v0.blockSignals(False)
        self._edit_v0.blockSignals(True)
        self._edit_v0.setText(str(val))
        self._edit_v0.blockSignals(False)

    def _sync_deg_from_slider(self, val: int) -> None:
        self._spin_deg.blockSignals(True)
        self._spin_deg.setValue(val)
        self._spin_deg.blockSignals(False)
        self._edit_deg.blockSignals(True)
        self._edit_deg.setText(str(val))
        self._edit_deg.blockSignals(False)

    def _sync_deg_from_spin(self, val: int) -> None:
        self._slider_deg.blockSignals(True)
        self._slider_deg.setValue(val)
        self._slider_deg.blockSignals(False)
        self._edit_deg.blockSignals(True)
        self._edit_deg.setText(str(val))
        self._edit_deg.blockSignals(False)

    def _apply_v0_from_edit(self) -> None:
        text = self._edit_v0.text().strip().replace(",", ".")
        if not text:
            self._edit_v0.blockSignals(True)
            self._edit_v0.setText(str(self._spin_v0.value()))
            self._edit_v0.blockSignals(False)
            return
        try:
            v = float(text)
        except ValueError:
            QMessageBox.warning(self, "输入无效", "初速度请输入数值（单位 m/s）。")
            self._refresh_param_edits_from_spins()
            return
        iv = int(round(max(10.0, min(100.0, v))))
        self._slider_v0.setValue(iv)

    def _apply_deg_from_edit(self) -> None:
        text = self._edit_deg.text().strip().replace(",", ".")
        if not text:
            self._edit_deg.blockSignals(True)
            self._edit_deg.setText(str(self._spin_deg.value()))
            self._edit_deg.blockSignals(False)
            return
        try:
            v = float(text)
        except ValueError:
            QMessageBox.warning(self, "输入无效", "发射角请输入数值（单位 °）。")
            self._refresh_param_edits_from_spins()
            return
        iv = int(round(max(0.0, min(90.0, v))))
        self._slider_deg.setValue(iv)

    def _apply_k_from_edit(self) -> None:
        text = self._edit_k.text().strip().replace(",", ".")
        if not text:
            self._sync_k_edit()
            return
        try:
            v = float(text)
        except ValueError:
            QMessageBox.warning(self, "输入无效", "阻力系数 k 请输入数值。")
            self._sync_k_edit()
            return
        v = max(0.0, min(0.5, v))
        self._spin_k.blockSignals(True)
        self._spin_k.setValue(v)
        self._spin_k.blockSignals(False)
        self._sync_k_edit()

    def _apply_m_from_edit(self) -> None:
        text = self._edit_m.text().strip().replace(",", ".")
        if not text:
            self._sync_m_edit()
            return
        try:
            v = float(text)
        except ValueError:
            QMessageBox.warning(self, "输入无效", "质量 m 请输入数值（单位 kg）。")
            self._sync_m_edit()
            return
        v = max(0.1, min(10.0, v))
        self._spin_m.blockSignals(True)
        self._spin_m.setValue(v)
        self._spin_m.blockSignals(False)
        self._sync_m_edit()

    # ------------------------------------------------------------------
    # 仿真与动画
    # ------------------------------------------------------------------
    def _estimate_t_max(self) -> float:
        v0 = float(self._spin_v0.value())
        theta = np.deg2rad(float(self._spin_deg.value()))
        vy0 = v0 * np.sin(theta)
        g = float(G_DEFAULT)
        if vy0 <= 1e-9:
            t_simple = 10.0
        else:
            t_simple = 2.0 * vy0 / g
        return float(max(80.0, t_simple * 6.0))

    def _on_start_simulation(self) -> None:
        self._timer.stop()
        self._paused = False
        self._btn_pause.setEnabled(True)
        self._btn_pause.setText("暂停")

        v0 = float(self._spin_v0.value())
        angle = float(self._spin_deg.value())
        m = float(self._spin_m.value())
        k = float(self._spin_k.value())
        t_max = self._estimate_t_max()

        try:
            packs = calculate_projectile(v0, angle, m, k, t_max, n_samples=1600)
        except Exception as exc:  # noqa: BLE001 — 教学软件：向用户展示可读错误
            QMessageBox.warning(self, "仿真失败", str(exc))
            return

        ideal = packs["ideal"]
        drag = packs["drag"]
        self._pack_ideal = ideal
        self._pack_drag = drag

        xi, yi = ideal["x"], ideal["y"]
        xd, yd = drag["x"], drag["y"]

        # 坐标范围：理想 + SciPy 阻力参考轨迹（与本实验 RK4 实时轨迹尺度一致）
        xs = np.concatenate([xi, xd])
        ys = np.concatenate([yi, yd])
        xmin, xmax = float(np.min(xs)), float(np.max(xs))
        ymin, ymax = 0.0, float(np.max(ys)) * 1.08 + 1e-6
        xr = xmax - xmin
        yr = ymax - ymin
        pad_x = max(xr * 0.05, 1.0)
        pad_y = max(yr * 0.08, 1.0)
        self._ax.set_xlim(xmin - pad_x, xmax + pad_x)
        self._ax.set_ylim(ymin - pad_y * 0.2, ymax + pad_y)

        ti = ideal["t"]
        vi = np.hypot(ideal["vx"], ideal["vy"])
        self._line_v_ideal.set_data(ti, vi)
        self._line_y_macro_ideal.set_data(ti, yi)

        self._line_ideal.set_data(xi, yi)

        theta = np.deg2rad(angle)
        vx0 = v0 * np.cos(theta)
        vy0 = v0 * np.sin(theta)
        y0 = float(Y_LAUNCH_EPS)
        self._y_drag_state = np.array([0.0, y0, vx0, vy0], dtype=float)
        self._t_drag_sim = 0.0
        self._drag_finished = False
        self._hist_t = []
        self._hist_x = []
        self._hist_y = []
        self._hist_vx = []
        self._hist_vy = []
        self._hist_ke = []
        self._hist_pe = []
        self._hist_e = []
        mech0 = projectile_mechanics_from_state(self._y_drag_state, m, float(G_DEFAULT))
        self._append_hist_point(0.0, self._y_drag_state, mech0)

        self._line_v_drag.set_data([], [])
        self._line_y_macro_drag.set_data([], [])
        self._line_drag.set_data([], [])
        self._line_e_ke.set_data([], [])
        self._line_e_pe.set_data([], [])
        self._line_e_tot.set_data([], [])
        self._ax_v.relim()
        self._ax_v.autoscale_view()
        self._ax_y.relim()
        self._ax_y.autoscale_view()
        self._ax_e.relim()
        self._ax_e.autoscale_view()

        self._vline_speed.set_visible(True)
        self._vline_height.set_visible(True)

        self._sync_live_plot_lines()
        self._canvas.draw_idle()
        self._timer.start()

    def _on_pause_toggle(self) -> None:
        if self._y_drag_state is None:
            return
        if self._paused:
            self._paused = False
            self._btn_pause.setText("暂停")
            self._timer.start()
        else:
            self._paused = True
            self._btn_pause.setText("继续")
            self._timer.stop()

    def _on_reset_simulation(self) -> None:
        self._timer.stop()
        self._paused = False
        self._btn_pause.setEnabled(False)
        self._btn_pause.setText("暂停")
        self._y_drag_state = None
        self._t_drag_sim = 0.0
        self._drag_finished = False
        self._hist_t.clear()
        self._hist_x.clear()
        self._hist_y.clear()
        self._hist_vx.clear()
        self._hist_vy.clear()
        self._hist_ke.clear()
        self._hist_pe.clear()
        self._hist_e.clear()
        self._pack_ideal = None
        self._pack_drag = None

        self._line_ideal.set_data([], [])
        self._line_drag.set_data([], [])
        self._scatter_pt.set_offsets(np.zeros((0, 2)))

        self._line_v_ideal.set_data([], [])
        self._line_v_drag.set_data([], [])
        self._line_y_macro_ideal.set_data([], [])
        self._line_y_macro_drag.set_data([], [])
        self._line_e_ke.set_data([], [])
        self._line_e_pe.set_data([], [])
        self._line_e_tot.set_data([], [])
        self._vline_speed.set_visible(False)
        self._vline_height.set_visible(False)

        self._ax.relim()
        self._ax.autoscale_view()
        self._ax_v.relim()
        self._ax_v.autoscale_view()
        self._ax_y.relim()
        self._ax_y.autoscale_view()
        self._ax_e.relim()
        self._ax_e.autoscale_view()
        self._canvas.draw_idle()

    def _append_hist_point(self, t: float, state: np.ndarray, mech: Dict[str, float]) -> None:
        self._hist_t.append(float(t))
        self._hist_x.append(float(state[0]))
        self._hist_y.append(float(state[1]))
        self._hist_vx.append(float(state[2]))
        self._hist_vy.append(float(state[3]))
        self._hist_ke.append(float(mech["ke"]))
        self._hist_pe.append(float(mech["pe"]))
        self._hist_e.append(float(mech["e_total"]))

    def _sync_live_plot_lines(self) -> None:
        """根据 `_hist_*` 刷新有阻力轨迹、宏观图与能量曲线（不清除坐标轴）。"""
        if not self._hist_t:
            return
        t = np.asarray(self._hist_t, dtype=float)
        x = np.asarray(self._hist_x, dtype=float)
        y = np.asarray(self._hist_y, dtype=float)
        vx = np.asarray(self._hist_vx, dtype=float)
        vy = np.asarray(self._hist_vy, dtype=float)
        vmag = np.hypot(vx, vy)

        self._line_drag.set_data(x, y)
        self._scatter_pt.set_offsets(np.array([[float(x[-1]), float(y[-1])]]))
        t_cur = float(t[-1])
        self._vline_speed.set_xdata([t_cur, t_cur])
        self._vline_height.set_xdata([t_cur, t_cur])

        self._line_v_drag.set_data(t, vmag)
        self._line_y_macro_drag.set_data(t, y)

        self._line_e_ke.set_data(t, np.asarray(self._hist_ke, dtype=float))
        self._line_e_pe.set_data(t, np.asarray(self._hist_pe, dtype=float))
        self._line_e_tot.set_data(t, np.asarray(self._hist_e, dtype=float))

        self._ax_v.relim()
        self._ax_v.autoscale_view()
        self._ax_y.relim()
        self._ax_y.autoscale_view()
        self._ax_e.relim()
        self._ax_e.autoscale_view()

    def _on_animation_tick(self) -> None:
        if self._y_drag_state is None or self._drag_finished:
            return

        m = float(self._spin_m.value())
        k = float(self._spin_k.value())
        g = float(G_DEFAULT)
        macro_dt = (TIMER_MS / 1000.0) * float(self._spin_playback.value())

        y_prev = np.asarray(self._y_drag_state, dtype=float).copy()
        y_new, mech = step_projectile_rk4(y_prev, g=g, k=k, m=m, macro_dt=macro_dt)

        yp = float(y_prev[1])
        yn = float(y_new[1])

        if yn <= 0.0 and yp > 0.0:
            denom = yp - yn
            alpha = yp / denom if denom > 1e-18 else 1.0
            alpha = float(min(1.0, max(0.0, alpha)))
            y_land = y_prev + alpha * (y_new - y_prev)
            y_land[1] = 0.0
            t_land = self._t_drag_sim + alpha * macro_dt
            mech_land = projectile_mechanics_from_state(y_land, m, g)
            self._append_hist_point(t_land, y_land, mech_land)
            self._y_drag_state = y_land
            self._t_drag_sim = t_land
            self._drag_finished = True
        elif yn <= 0.0:
            y_end = y_new.copy()
            y_end[1] = max(0.0, float(y_end[1]))
            self._t_drag_sim += macro_dt
            mech_end = projectile_mechanics_from_state(y_end, m, g)
            self._append_hist_point(self._t_drag_sim, y_end, mech_end)
            self._y_drag_state = y_end
            self._drag_finished = True
        else:
            self._y_drag_state = y_new
            self._t_drag_sim += macro_dt
            self._append_hist_point(self._t_drag_sim, y_new, mech)

        self._sync_live_plot_lines()
        self._canvas.draw_idle()

        if self._drag_finished:
            self._timer.stop()
            self._btn_pause.setEnabled(False)
            self._btn_pause.setText("暂停")
