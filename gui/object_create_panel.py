from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton, 
                             QComboBox, QFormLayout, QLineEdit, QDoubleSpinBox, QPushButton, 
                             QLabel, QColorDialog, QStackedWidget)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor

class ObjectCreatePanel(QWidget):
    mode_changed = pyqtSignal(str)  # "horizontal", "vertical"
    create_requested = pyqtSignal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. 实验模式
        mode_group = QGroupBox("实验模式")
        mode_layout = QHBoxLayout()
        self.rb_vertical = QRadioButton("垂直 (有重力)")
        self.rb_horizontal = QRadioButton("水平 (无重力)")
        self.rb_vertical.setChecked(True)
        mode_layout.addWidget(self.rb_vertical)
        mode_layout.addWidget(self.rb_horizontal)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        self.rb_vertical.toggled.connect(lambda: self.mode_changed.emit("vertical") if self.rb_vertical.isChecked() else None)
        self.rb_horizontal.toggled.connect(lambda: self.mode_changed.emit("horizontal") if self.rb_horizontal.isChecked() else None)

        # 2. 创建对象
        create_group = QGroupBox("创建对象")
        create_layout = QVBoxLayout()

        self.cb_type = QComboBox()
        self.cb_type.addItems(["小球", "方块", "弹簧"])
        create_layout.addWidget(QLabel("对象类型:"))
        create_layout.addWidget(self.cb_type)

        # 参数区域 - 使用 StackedWidget 切换不同对象的参数
        self.param_stack = QStackedWidget()
        
        # 小球/方块共用或独立？为了简单，先独立
        self.ball_params = self.create_ball_form()
        self.block_params = self.create_block_form()
        self.spring_params = self.create_spring_form()

        self.param_stack.addWidget(self.ball_params)
        self.param_stack.addWidget(self.block_params)
        self.param_stack.addWidget(self.spring_params)

        create_layout.addWidget(self.param_stack)
        self.cb_type.currentIndexChanged.connect(self.param_stack.setCurrentIndex)

        self.btn_create = QPushButton("创建对象")
        self.btn_create.setStyleSheet("height: 40px; font-weight: bold;")
        self.btn_create.clicked.connect(self.on_create_clicked)
        create_layout.addWidget(self.btn_create)

        create_group.setLayout(create_layout)
        layout.addWidget(create_group)
        layout.addStretch()

    def create_ball_form(self):
        w = QWidget()
        l = QFormLayout(w)
        self.ball_name = QLineEdit("Ball")
        self.ball_mass = QDoubleSpinBox(); self.ball_mass.setRange(0.1, 1000); self.ball_mass.setValue(1.0)
        self.ball_radius = QDoubleSpinBox(); self.ball_radius.setRange(1, 200); self.ball_radius.setValue(20.0)
        self.ball_restitution = QDoubleSpinBox(); self.ball_restitution.setRange(0, 1.1); self.ball_restitution.setValue(0.8)
        self.ball_vx = QDoubleSpinBox(); self.ball_vx.setRange(-2000, 2000); self.ball_vx.setValue(0.0)
        self.ball_vy = QDoubleSpinBox(); self.ball_vy.setRange(-2000, 2000); self.ball_vy.setValue(0.0)
        l.addRow("名称:", self.ball_name)
        l.addRow("质量:", self.ball_mass)
        l.addRow("半径:", self.ball_radius)
        l.addRow("弹性:", self.ball_restitution)
        l.addRow("初速 X:", self.ball_vx)
        l.addRow("初速 Y:", self.ball_vy)
        return w

    def create_block_form(self):
        w = QWidget()
        l = QFormLayout(w)
        self.block_name = QLineEdit("Block")
        self.block_mass = QDoubleSpinBox(); self.block_mass.setRange(0.1, 1000); self.block_mass.setValue(1.0)
        self.block_width = QDoubleSpinBox(); self.block_width.setRange(1, 500); self.block_width.setValue(60.0)
        self.block_height = QDoubleSpinBox(); self.block_height.setRange(1, 500); self.block_height.setValue(60.0)
        self.block_restitution = QDoubleSpinBox(); self.block_restitution.setRange(0, 1.1); self.block_restitution.setValue(0.8)
        self.block_vx = QDoubleSpinBox(); self.block_vx.setRange(-2000, 2000); self.block_vx.setValue(0.0)
        self.block_vy = QDoubleSpinBox(); self.block_vy.setRange(-2000, 2000); self.block_vy.setValue(0.0)
        l.addRow("名称:", self.block_name)
        l.addRow("质量:", self.block_mass)
        l.addRow("宽度:", self.block_width)
        l.addRow("高度:", self.block_height)
        l.addRow("弹性:", self.block_restitution)
        l.addRow("初速 X:", self.block_vx)
        l.addRow("初速 Y:", self.block_vy)
        return w

    def create_spring_form(self):
        w = QWidget()
        l = QFormLayout(w)
        self.spring_name = QLineEdit("Spring")
        self.spring_k = QDoubleSpinBox(); self.spring_k.setRange(1, 5000); self.spring_k.setValue(200.0)
        self.spring_d = QDoubleSpinBox(); self.spring_d.setRange(0, 100); self.spring_d.setValue(5.0)
        self.spring_len = QDoubleSpinBox(); self.spring_len.setRange(1, 1000); self.spring_len.setValue(100.0)
        self.spring_angle = QDoubleSpinBox(); self.spring_angle.setRange(0, 360); self.spring_angle.setValue(0.0)
        l.addRow("名称:", self.spring_name)
        l.addRow("劲度系数:", self.spring_k)
        l.addRow("阻尼系数:", self.spring_d)
        l.addRow("静止长度:", self.spring_len)
        l.addRow("初始长度:", self.spring_len) # 简化：静止长度即初始长度
        l.addRow("偏转角度:", self.spring_angle)
        return w

    def on_create_clicked(self):
        idx = self.cb_type.currentIndex()
        params = {}
        if idx == 0: # Ball
            obj_type = "ball"
            params = {
                "name": self.ball_name.text(),
                "mass": self.ball_mass.value(),
                "radius": self.ball_radius.value(),
                "restitution": self.ball_restitution.value(),
                "vx": self.ball_vx.value(),
                "vy": self.ball_vy.value(),
                "color": "#6496ff"
            }
        elif idx == 1: # Block
            obj_type = "block"
            params = {
                "name": self.block_name.text(),
                "mass": self.block_mass.value(),
                "width": self.block_width.value(),
                "height": self.block_height.value(),
                "restitution": self.block_restitution.value(),
                "vx": self.block_vx.value(),
                "vy": self.block_vy.value(),
                "color": "#64c896"
            }
        else: # Spring
            obj_type = "spring"
            params = {
                "name": self.spring_name.text(),
                "stiffness": self.spring_k.value(),
                "damping": self.spring_d.value(),
                "rest_length": self.spring_len.value(),
                "length": self.spring_len.value(),
                "angle": self.spring_angle.value(),
                "color": "#ffa040"
            }
        self.create_requested.emit(obj_type, params)
