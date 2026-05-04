from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton, 
                             QComboBox, QFormLayout, QLineEdit, QDoubleSpinBox, QPushButton, 
                             QLabel, QColorDialog, QStackedWidget, QCheckBox)
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
        self.cb_type.addItems(["小球", "方块", "弹簧", "平台", "挡板", "斜面", "凹槽", "细棒", "绳子"])
        create_layout.addWidget(QLabel("对象类型:"))
        create_layout.addWidget(self.cb_type)

        # 参数区域 - 使用 StackedWidget 切换不同对象的参数
        self.param_stack = QStackedWidget()
        
        self.ball_params = self.create_ball_form()
        self.block_params = self.create_block_form()
        self.spring_params = self.create_spring_form()
        self.static_params = self.create_static_form()
        self.groove_params = self.create_groove_form()
        self.rod_params = self.create_rod_form()
        self.rope_params = self.create_rope_form()

        self.param_stack.addWidget(self.ball_params)
        self.param_stack.addWidget(self.block_params)
        self.param_stack.addWidget(self.spring_params)
        self.param_stack.addWidget(self.static_params)
        self.param_stack.addWidget(self.static_params) # 挡板
        self.param_stack.addWidget(self.static_params) # 斜面
        self.param_stack.addWidget(self.groove_params) # 凹槽
        self.param_stack.addWidget(self.rod_params)    # 细棒
        self.param_stack.addWidget(self.rope_params)   # 绳子

        create_layout.addWidget(self.param_stack)
        
        def on_type_changed(idx):
            if idx == 6: # 凹槽
                self.param_stack.setCurrentIndex(6)
                self.groove_name.setText("")
            elif idx == 7: # 细棒
                self.param_stack.setCurrentIndex(7)
                self.rod_name.setText("")
            elif idx == 8: # 绳子
                self.param_stack.setCurrentIndex(8)
                self.rope_name.setText("")
            else:
                self.param_stack.setCurrentIndex(min(idx, 3))
            # 自动调整静态物体表单提示
            if idx == 3: # 平台
                self.static_name.setText("")
                self.static_width.setValue(300.0)
                self.static_height.setValue(30.0)
                self.static_angle.setValue(0.0)
            elif idx == 4: # 挡板
                self.static_name.setText("")
                self.static_width.setValue(30.0)
                self.static_height.setValue(200.0)
                self.static_angle.setValue(0.0)
            elif idx == 5: # 斜面
                self.static_name.setText("")
                self.static_width.setValue(300.0)
                self.static_height.setValue(30.0)
                self.static_angle.setValue(20.0)

        self.cb_type.currentIndexChanged.connect(on_type_changed)

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
        self.ball_name = QLineEdit("")
        self.ball_name.setPlaceholderText("留空自动生成")
        self.ball_mass = QDoubleSpinBox(); self.ball_mass.setRange(0.1, 1000); self.ball_mass.setValue(1.0)
        self.ball_radius = QDoubleSpinBox(); self.ball_radius.setRange(1, 200); self.ball_radius.setValue(20.0)
        self.ball_restitution = QDoubleSpinBox(); self.ball_restitution.setRange(0, 1.1); self.ball_restitution.setValue(0.8)
        self.ball_vx = QDoubleSpinBox(); self.ball_vx.setRange(-2000, 2000); self.ball_vx.setValue(0.0)
        self.ball_vy = QDoubleSpinBox(); self.ball_vy.setRange(-2000, 2000); self.ball_vy.setValue(0.0)
        l.addRow("名称:", self.ball_name)
        l.addRow("质量 (kg):", self.ball_mass)
        l.addRow("半径 (px):", self.ball_radius)
        l.addRow("弹性:", self.ball_restitution)
        l.addRow("初速 X (px/s):", self.ball_vx)
        l.addRow("初速 Y (px/s):", self.ball_vy)
        return w

    def create_block_form(self):
        w = QWidget()
        l = QFormLayout(w)
        self.block_name = QLineEdit("")
        self.block_name.setPlaceholderText("留空自动生成")
        self.block_mass = QDoubleSpinBox(); self.block_mass.setRange(0.1, 1000); self.block_mass.setValue(1.0)
        self.block_width = QDoubleSpinBox(); self.block_width.setRange(1, 500); self.block_width.setValue(60.0)
        self.block_height = QDoubleSpinBox(); self.block_height.setRange(1, 500); self.block_height.setValue(60.0)
        self.block_restitution = QDoubleSpinBox(); self.block_restitution.setRange(0, 1.1); self.block_restitution.setValue(0.8)
        self.block_vx = QDoubleSpinBox(); self.block_vx.setRange(-2000, 2000); self.block_vx.setValue(0.0)
        self.block_vy = QDoubleSpinBox(); self.block_vy.setRange(-2000, 2000); self.block_vy.setValue(0.0)
        l.addRow("名称:", self.block_name)
        l.addRow("质量 (kg):", self.block_mass)
        l.addRow("宽度 (px):", self.block_width)
        l.addRow("高度 (px):", self.block_height)
        l.addRow("弹性:", self.block_restitution)
        l.addRow("初速 X (px/s):", self.block_vx)
        l.addRow("初速 Y (px/s):", self.block_vy)
        return w

    def create_spring_form(self):
        w = QWidget()
        l = QFormLayout(w)
        self.spring_name = QLineEdit("")
        self.spring_name.setPlaceholderText("留空自动生成")
        self.spring_k = QDoubleSpinBox(); self.spring_k.setRange(1, 5000); self.spring_k.setValue(200.0)
        self.spring_d = QDoubleSpinBox(); self.spring_d.setRange(0, 100); self.spring_d.setValue(5.0)
        self.spring_len = QDoubleSpinBox(); self.spring_len.setRange(1, 1000); self.spring_len.setValue(100.0)
        self.spring_angle = QDoubleSpinBox(); self.spring_angle.setRange(0, 360); self.spring_angle.setValue(0.0)
        l.addRow("名称:", self.spring_name)
        l.addRow("刚度 (k):", self.spring_k)
        l.addRow("阻尼 (d):", self.spring_d)
        l.addRow("静止长度 (px):", self.spring_len)
        l.addRow("当前角度 (°):", self.spring_angle)
        return w
        
    def create_static_form(self):
        w = QWidget()
        l = QFormLayout(w)
        self.static_name = QLineEdit("")
        self.static_name.setPlaceholderText("留空自动生成")
        self.static_width = QDoubleSpinBox(); self.static_width.setRange(1, 1000); self.static_width.setValue(300.0)
        self.static_height = QDoubleSpinBox(); self.static_height.setRange(1, 1000); self.static_height.setValue(30.0)
        self.static_angle = QDoubleSpinBox(); self.static_angle.setRange(-360, 360); self.static_angle.setValue(0.0)
        self.static_restitution = QDoubleSpinBox(); self.static_restitution.setRange(0, 1.1); self.static_restitution.setValue(0.8)
        self.static_friction = QDoubleSpinBox(); self.static_friction.setRange(0, 1.0); self.static_friction.setValue(0.2)
        l.addRow("名称:", self.static_name)
        l.addRow("宽度 (px):", self.static_width)
        l.addRow("高度 (px):", self.static_height)
        l.addRow("角度 (°):", self.static_angle)
        l.addRow("弹性系数:", self.static_restitution)
        l.addRow("摩擦系数:", self.static_friction)
        return w

    def create_groove_form(self):
        w = QWidget()
        l = QFormLayout(w)
        self.groove_name = QLineEdit("")
        self.groove_name.setPlaceholderText("留空自动生成")
        self.groove_radius = QDoubleSpinBox(); self.groove_radius.setRange(10, 1000); self.groove_radius.setValue(150.0)
        self.groove_thickness = QDoubleSpinBox(); self.groove_thickness.setRange(1, 200); self.groove_thickness.setValue(20.0)
        
        self.groove_fixed = QCheckBox("固定"); self.groove_fixed.setChecked(True)
        self.groove_mass = QDoubleSpinBox(); self.groove_mass.setRange(0.1, 1000); self.groove_mass.setValue(10.0)
        self.groove_vx = QDoubleSpinBox(); self.groove_vx.setRange(-2000, 2000); self.groove_vx.setValue(0.0)
        self.groove_vy = QDoubleSpinBox(); self.groove_vy.setRange(-2000, 2000); self.groove_vy.setValue(0.0)
        
        self.groove_restitution = QDoubleSpinBox(); self.groove_restitution.setRange(0, 1.1); self.groove_restitution.setValue(0.8)
        self.groove_friction = QDoubleSpinBox(); self.groove_friction.setRange(0, 1.0); self.groove_friction.setValue(0.2)
        
        l.addRow("名称:", self.groove_name)
        l.addRow("半径 (px):", self.groove_radius)
        l.addRow("厚度 (px):", self.groove_thickness)
        l.addRow("是否固定:", self.groove_fixed)
        l.addRow("质量 (kg):", self.groove_mass)
        l.addRow("初速 X (px/s):", self.groove_vx)
        l.addRow("初速 Y (px/s):", self.groove_vy)
        l.addRow("弹性系数:", self.groove_restitution)
        l.addRow("摩擦系数:", self.groove_friction)
        
        # 联动控制
        def toggle_fixed():
            fixed = self.groove_fixed.isChecked()
            self.groove_mass.setEnabled(not fixed)
            self.groove_vx.setEnabled(not fixed)
            self.groove_vy.setEnabled(not fixed)
        self.groove_fixed.toggled.connect(toggle_fixed)
        toggle_fixed() # 初始化
        
        return w

    def create_rod_form(self):
        w = QWidget()
        l = QFormLayout(w)
        self.rod_name = QLineEdit("")
        self.rod_name.setPlaceholderText("留空自动生成")
        self.rod_len = QDoubleSpinBox(); self.rod_len.setRange(1, 2000); self.rod_len.setValue(160.0)
        self.rod_angle = QDoubleSpinBox(); self.rod_angle.setRange(-360, 360); self.rod_angle.setValue(90.0)
        self.rod_thickness = QDoubleSpinBox(); self.rod_thickness.setRange(1, 100); self.rod_thickness.setValue(6.0)
        self.rod_mass = QDoubleSpinBox(); self.rod_mass.setRange(0.1, 1000); self.rod_mass.setValue(1.0)
        self.rod_friction = QDoubleSpinBox(); self.rod_friction.setRange(0, 1); self.rod_friction.setValue(0.0)
        
        l.addRow("名称:", self.rod_name)
        l.addRow("长度 (px):", self.rod_len)
        l.addRow("角度 (°):", self.rod_angle)
        l.addRow("厚度 (px):", self.rod_thickness)
        l.addRow("质量 (kg):", self.rod_mass)
        l.addRow("摩擦系数:", self.rod_friction)
        return w

    def create_rope_form(self):
        w = QWidget()
        l = QFormLayout(w)
        self.rope_name = QLineEdit("")
        self.rope_name.setPlaceholderText("留空自动生成")
        self.rope_len = QDoubleSpinBox(); self.rope_len.setRange(1, 2000); self.rope_len.setValue(180.0)
        self.rope_angle = QDoubleSpinBox(); self.rope_angle.setRange(-360, 360); self.rope_angle.setValue(90.0)
        self.rope_damping = QDoubleSpinBox(); self.rope_damping.setRange(0, 10); self.rope_damping.setValue(0.2)
        self.rope_thickness = QDoubleSpinBox(); self.rope_thickness.setRange(1, 20); self.rope_thickness.setValue(3.0)
        self.rope_color = QLineEdit("#333333")
        
        l.addRow("名称:", self.rope_name)
        l.addRow("长度 (px):", self.rope_len)
        l.addRow("角度 (°):", self.rope_angle)
        l.addRow("阻尼 (d):", self.rope_damping)
        l.addRow("线宽 (px):", self.rope_thickness)
        l.addRow("颜色:", self.rope_color)
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
        elif idx == 2: # Spring
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
        elif idx in [3, 4, 5]: # StaticBlock objects
            type_map = {3: "platform", 4: "wall", 5: "ramp"}
            obj_type = type_map[idx]
            params = {
                "name": self.static_name.text(),
                "width": self.static_width.value(),
                "height": self.static_height.value(),
                "angle": self.static_angle.value(),
                "restitution": self.static_restitution.value(),
                "friction": self.static_friction.value(),
                "color": "#808080"
            }
        elif idx == 6: # Groove
            obj_type = "groove"
            params = {
                "name": self.groove_name.text(),
                "radius": self.groove_radius.value(),
                "thickness": self.groove_thickness.value(),
                "fixed": self.groove_fixed.isChecked(),
                "mass": self.groove_mass.value(),
                "vx": self.groove_vx.value(),
                "vy": self.groove_vy.value(),
                "restitution": self.groove_restitution.value(),
                "friction": self.groove_friction.value(),
                "color": "#808080"
            }
        elif idx == 7: # Rod
            obj_type = "rod"
            params = {
                "name": self.rod_name.text(),
                "length": self.rod_len.value(),
                "angle": self.rod_angle.value(),
                "thickness": self.rod_thickness.value(),
                "mass": self.rod_mass.value(),
                "friction": self.rod_friction.value(),
                "color": "#333333"
            }
        elif idx == 8: # Rope
            obj_type = "rope"
            params = {
                "name": self.rope_name.text(),
                "length": self.rope_len.value(),
                "angle": self.rope_angle.value(),
                "damping": self.rope_damping.value(),
                "thickness": self.rope_thickness.value(),
                "color": self.rope_color.text()
            }
        self.create_requested.emit(obj_type, params)
