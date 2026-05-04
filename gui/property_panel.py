from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox, QGroupBox, QLabel, QPushButton, QHBoxLayout, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np
from core.models import Ball, Block, Spring, StaticBlock, Groove, Rod, Rope

class PropertyPanel(QWidget):
    property_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_obj = None
        self._updating = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.group_box = QGroupBox("属性面板")
        self.form_layout = QFormLayout(self.group_box)
        
        # 基础属性
        self.le_name = QLineEdit()
        self.lb_id = QLabel("N/A")
        self.sp_mass = QDoubleSpinBox(); self.sp_mass.setRange(0.1, 10000)
        self.sp_x = QDoubleSpinBox(); self.sp_x.setRange(-10000, 10000)
        self.sp_y = QDoubleSpinBox(); self.sp_y.setRange(-10000, 10000)
        self.sp_vx = QDoubleSpinBox(); self.sp_vx.setRange(-10000, 10000)
        self.sp_vy = QDoubleSpinBox(); self.sp_vy.setRange(-10000, 10000)
        self.sp_restitution = QDoubleSpinBox(); self.sp_restitution.setRange(0, 1.5); self.sp_restitution.setSingleStep(0.1)
        self.sp_friction = QDoubleSpinBox(); self.sp_friction.setRange(0, 1.0); self.sp_friction.setSingleStep(0.1)
        self.sp_angle = QDoubleSpinBox(); self.sp_angle.setRange(-360, 360)
        
        self.cb_fixed = QCheckBox("固定")
        self.cb_fixed.toggled.connect(self._on_fixed_toggled)
        
        # 小球属性
        self.sp_radius = QDoubleSpinBox(); self.sp_radius.setRange(1, 1000)
        self.sp_thickness = QDoubleSpinBox(); self.sp_thickness.setRange(1, 1000)
        
        # 方块属性
        self.sp_width = QDoubleSpinBox(); self.sp_width.setRange(1, 1000)
        self.sp_height = QDoubleSpinBox(); self.sp_height.setRange(1, 1000)

        # 弹簧属性
        self.sp_stiffness = QDoubleSpinBox(); self.sp_stiffness.setRange(1, 10000)
        self.sp_damping = QDoubleSpinBox(); self.sp_damping.setRange(0, 1000)
        self.sp_rest_length = QDoubleSpinBox(); self.sp_rest_length.setRange(1, 2000)
        self.sp_start_x = QDoubleSpinBox(); self.sp_start_x.setRange(-2000, 2000)
        self.sp_start_y = QDoubleSpinBox(); self.sp_start_y.setRange(-2000, 2000)
        self.sp_end_x = QDoubleSpinBox(); self.sp_end_x.setRange(-2000, 2000)
        self.sp_end_y = QDoubleSpinBox(); self.sp_end_y.setRange(-2000, 2000)
        
        # 挂载属性
        self.lbl_start_title = QLabel("挂载起点:")
        self.lb_start_mount = QLabel("无")
        self.btn_unbind_start = QPushButton("解除")
        self.btn_unbind_start.setFixedWidth(50)
        self.btn_unbind_start.clicked.connect(self.unbind_start)
        self.start_mount_container = QWidget()
        l_start = QHBoxLayout(self.start_mount_container)
        l_start.setContentsMargins(0, 0, 0, 0)
        l_start.addWidget(self.lb_start_mount); l_start.addWidget(self.btn_unbind_start)
        
        self.lbl_end_title = QLabel("挂载终点:")
        self.lb_end_mount = QLabel("无")
        self.btn_unbind_end = QPushButton("解除")
        self.btn_unbind_end.setFixedWidth(50)
        self.btn_unbind_end.clicked.connect(self.unbind_end)
        self.end_mount_container = QWidget()
        l_end = QHBoxLayout(self.end_mount_container)
        l_end.setContentsMargins(0, 0, 0, 0)
        l_end.addWidget(self.lb_end_mount); l_end.addWidget(self.btn_unbind_end)
        
        self.form_layout.addRow("ID:", self.lb_id)
        self.form_layout.addRow("名称:", self.le_name)
        self.form_layout.addRow("是否固定:", self.cb_fixed)
        self.form_layout.addRow("质量 (kg):", self.sp_mass)
        self.form_layout.addRow("坐标 X (px):", self.sp_x)
        self.form_layout.addRow("坐标 Y (px):", self.sp_y)
        self.form_layout.addRow("速度 X (px/s):", self.sp_vx)
        self.form_layout.addRow("速度 Y (px/s):", self.sp_vy)
        self.form_layout.addRow("旋转角度 (°):", self.sp_angle)
        self.form_layout.addRow("弹性系数:", self.sp_restitution)
        self.form_layout.addRow("摩擦系数:", self.sp_friction)
        self.form_layout.addRow("半径 (px):", self.sp_radius)
        self.form_layout.addRow("厚度 (px):", self.sp_thickness)
        self.form_layout.addRow("宽度 (px):", self.sp_width)
        self.form_layout.addRow("高度 (px):", self.sp_height)
        self.form_layout.addRow("刚度 (k):", self.sp_stiffness)
        self.form_layout.addRow("阻尼 (d):", self.sp_damping)
        self.form_layout.addRow("静止长度 (px):", self.sp_rest_length)
        self.form_layout.addRow("起点 X (px):", self.sp_start_x)
        self.form_layout.addRow("起点 Y (px):", self.sp_start_y)
        self.form_layout.addRow("终点 X (px):", self.sp_end_x)
        self.form_layout.addRow("终点 Y (px):", self.sp_end_y)
        self.form_layout.addRow(self.lbl_start_title, self.start_mount_container)
        self.form_layout.addRow(self.lbl_end_title, self.end_mount_container)
        
        layout.addWidget(self.group_box)
        layout.addStretch()
        
        # 绑定信号
        self.le_name.textChanged.connect(self._on_value_changed)
        for w in [self.sp_mass, self.sp_x, self.sp_y, self.sp_vx, self.sp_vy, self.sp_restitution, self.sp_friction, self.sp_angle,
                  self.sp_radius, self.sp_thickness, self.sp_width, self.sp_height,
                  self.sp_stiffness, self.sp_damping, self.sp_rest_length,
                  self.sp_start_x, self.sp_start_y, self.sp_end_x, self.sp_end_y]:
            w.valueChanged.connect(self._on_value_changed)
        
        self.set_object(None)
        
    def set_object(self, obj):
        self.current_obj = obj
        if obj is None:
            self.group_box.setEnabled(False)
        else:
            self.group_box.setEnabled(True)
            self.update_from_object()
            
    def _on_fixed_toggled(self, fixed):
        if self._updating or self.current_obj is None: return
        if isinstance(self.current_obj, Groove):
            self.current_obj.fixed = fixed
            self.current_obj.static = fixed
            if fixed:
                self.current_obj.vel = np.array([0.0, 0.0], dtype=np.float64)
            self.update_from_object()
            self.property_changed.emit()
            
    def update_from_object(self):
        if self.current_obj is None: return
        self._updating = True
        
        self.lb_id.setText(str(self.current_obj.id)[:12])
        self.le_name.setText(self.current_obj.name)
        
        is_ball = isinstance(self.current_obj, Ball)
        is_block = isinstance(self.current_obj, Block)
        is_spring = isinstance(self.current_obj, Spring)
        is_static = isinstance(self.current_obj, StaticBlock)
        is_groove = isinstance(self.current_obj, Groove)
        is_rod = isinstance(self.current_obj, Rod)
        is_rope = isinstance(self.current_obj, Rope)

        # 刚体属性
        rigid_visible = is_ball or is_block or is_rod
        
        for w in [self.sp_x, self.sp_y]:
            w.setVisible(rigid_visible or is_static or is_groove)
            self.form_layout.labelForField(w).setVisible(rigid_visible or is_static or is_groove)
            
        for w in [self.sp_mass, self.sp_vx, self.sp_vy]:
            w.setVisible(rigid_visible)
            self.form_layout.labelForField(w).setVisible(rigid_visible)
            
        for w in [self.sp_restitution, self.sp_friction]:
            w.setVisible(rigid_visible or is_static or is_groove or is_rod)
            self.form_layout.labelForField(w).setVisible(rigid_visible or is_static or is_groove or is_rod)

        self.sp_angle.setVisible(is_static); self.form_layout.labelForField(self.sp_angle).setVisible(is_static)
        self.sp_radius.setVisible(is_ball or is_groove); self.form_layout.labelForField(self.sp_radius).setVisible(is_ball or is_groove)
        self.sp_thickness.setVisible(is_groove or is_rod or is_rope); self.form_layout.labelForField(self.sp_thickness).setVisible(is_groove or is_rod or is_rope)
        self.sp_width.setVisible(is_block or is_static); self.form_layout.labelForField(self.sp_width).setVisible(is_block or is_static)
        self.sp_height.setVisible(is_block or is_static); self.form_layout.labelForField(self.sp_height).setVisible(is_block or is_static)

        # 固定/质量/速度控制
        self.cb_fixed.setVisible(is_groove)
        if self.form_layout.labelForField(self.cb_fixed):
            self.form_layout.labelForField(self.cb_fixed).setVisible(is_groove)
            
        is_dynamic_groove = is_groove and not self.current_obj.fixed
        rigid_visible = is_ball or is_block or is_dynamic_groove
        
        for w in [self.sp_mass, self.sp_vx, self.sp_vy]:
            if is_groove:
                w.setVisible(True)
                self.form_layout.labelForField(w).setVisible(True)
                w.setEnabled(not self.current_obj.fixed if w != self.sp_mass else True)
            else:
                w.setVisible(rigid_visible)
                self.form_layout.labelForField(w).setVisible(rigid_visible)
                w.setEnabled(True)

        # 连动/挂载属性
        is_link = is_spring or is_rod or is_rope
        for w in [self.sp_start_x, self.sp_start_y, self.sp_end_x, self.sp_end_y]:
            w.setVisible(is_link)
            self.form_layout.labelForField(w).setVisible(is_link)
        
        self.sp_stiffness.setVisible(is_spring)
        self.form_layout.labelForField(self.sp_stiffness).setVisible(is_spring)
        self.sp_damping.setVisible(is_spring or is_rope)
        self.form_layout.labelForField(self.sp_damping).setVisible(is_spring or is_rope)
        self.sp_rest_length.setVisible(is_link)
        self.form_layout.labelForField(self.sp_rest_length).setVisible(is_link)
        
        if is_rod or is_rope:
            self.form_layout.labelForField(self.sp_rest_length).setText("长度:")
        else:
            self.form_layout.labelForField(self.sp_rest_length).setText("静止长度:")

        self.lbl_start_title.setVisible(is_link)
        self.start_mount_container.setVisible(is_link)
        self.lbl_end_title.setVisible(is_link)
        self.end_mount_container.setVisible(is_link)

        # 填充数值
        if rigid_visible or is_static or is_groove:
            self.sp_x.setValue(self.current_obj.pos[0])
            self.sp_y.setValue(self.current_obj.pos[1])
            self.sp_restitution.setValue(self.current_obj.restitution)
            self.sp_friction.setValue(self.current_obj.friction)
            
        if rigid_visible:
            self.sp_mass.setValue(self.current_obj.mass)
            self.sp_vx.setValue(self.current_obj.vel[0]); self.sp_vy.setValue(self.current_obj.vel[1])
            if is_ball: self.sp_radius.setValue(self.current_obj.radius)
            elif is_block: self.sp_width.setValue(self.current_obj.width); self.sp_height.setValue(self.current_obj.height)
        elif is_static:
            self.sp_angle.setValue(self.current_obj.angle)
            self.sp_width.setValue(self.current_obj.width)
            self.sp_height.setValue(self.current_obj.height)
        elif is_groove:
            self.cb_fixed.setChecked(self.current_obj.fixed)
            self.sp_mass.setValue(self.current_obj.mass)
            self.sp_vx.setValue(self.current_obj.vel[0]); self.sp_vy.setValue(self.current_obj.vel[1])
            self.sp_radius.setValue(self.current_obj.radius)
            self.sp_thickness.setValue(self.current_obj.thickness)
        elif is_spring:
            self.sp_stiffness.setValue(self.current_obj.stiffness)
            self.sp_damping.setValue(self.current_obj.damping)
            self.sp_rest_length.setValue(self.current_obj.rest_length)
            self.sp_start_x.setValue(self.current_obj.start_pos[0]); self.sp_start_y.setValue(self.current_obj.start_pos[1])
            self.sp_end_x.setValue(self.current_obj.end_pos[0]); self.sp_end_y.setValue(self.current_obj.end_pos[1])
            self.lb_start_mount.setText(self.current_obj.start_body_id[:8] if self.current_obj.start_body_id else "无")
            self.lb_end_mount.setText(self.current_obj.end_body_id[:8] if self.current_obj.end_body_id else "无")
        elif is_rod:
            self.sp_mass.setValue(self.current_obj.mass)
            self.sp_thickness.setValue(self.current_obj.thickness)
            self.sp_rest_length.setValue(self.current_obj.length)
            self.sp_start_x.setValue(self.current_obj.start_pos[0]); self.sp_start_y.setValue(self.current_obj.start_pos[1])
            self.sp_end_x.setValue(self.current_obj.end_pos[0]); self.sp_end_y.setValue(self.current_obj.end_pos[1])
            self.lb_start_mount.setText(self.current_obj.start_body_id[:8] if self.current_obj.start_body_id else "无")
            self.lb_end_mount.setText(self.current_obj.end_body_id[:8] if self.current_obj.end_body_id else "无")
        elif is_rope:
            self.sp_damping.setValue(self.current_obj.damping)
            self.sp_rest_length.setValue(self.current_obj.length)
            self.sp_start_x.setValue(self.current_obj.start_pos[0]); self.sp_start_y.setValue(self.current_obj.start_pos[1])
            self.sp_end_x.setValue(self.current_obj.end_pos[0]); self.sp_end_y.setValue(self.current_obj.end_pos[1])
            self.lb_start_mount.setText(self.current_obj.start_body_id[:8] if self.current_obj.start_body_id else "无")
            self.lb_end_mount.setText(self.current_obj.end_body_id[:8] if self.current_obj.end_body_id else "无")

        self._updating = False
        
    def _on_value_changed(self):
        if self._updating or self.current_obj is None: return
        self.current_obj.name = self.le_name.text()
        if isinstance(self.current_obj, (Ball, Block, StaticBlock, Groove)):
            self.current_obj.pos[0] = self.sp_x.value()
            self.current_obj.pos[1] = self.sp_y.value()
            self.current_obj.restitution = self.sp_restitution.value()
            self.current_obj.friction = self.sp_friction.value()
            
        if isinstance(self.current_obj, (Ball, Block)):
            self.current_obj.mass = self.sp_mass.value()
            self.current_obj.vel[0], self.current_obj.vel[1] = self.sp_vx.value(), self.sp_vy.value()
            if isinstance(self.current_obj, Ball): self.current_obj.radius = self.sp_radius.value()
            else: self.current_obj.width, self.current_obj.height = self.sp_width.value(), self.sp_height.value()
        elif isinstance(self.current_obj, StaticBlock):
            self.current_obj.angle = self.sp_angle.value()
            self.current_obj.width = self.sp_width.value()
            self.current_obj.height = self.sp_height.value()
        elif isinstance(self.current_obj, Groove):
            self.current_obj.fixed = self.cb_fixed.isChecked()
            self.current_obj.static = self.current_obj.fixed
            self.current_obj.mass = self.sp_mass.value()
            self.current_obj.vel[0], self.current_obj.vel[1] = self.sp_vx.value(), self.sp_vy.value()
            self.current_obj.radius = self.sp_radius.value()
            self.current_obj.thickness = self.sp_thickness.value()
        elif isinstance(self.current_obj, Spring):
            self.current_obj.stiffness = self.sp_stiffness.value()
            self.current_obj.damping = self.sp_damping.value()
            self.current_obj.rest_length = self.sp_rest_length.value()
            self._apply_link_endpoint_edits()
        elif isinstance(self.current_obj, Rod):
            self.current_obj.mass = self.sp_mass.value()
            self.current_obj.thickness = self.sp_thickness.value()
            self.current_obj.length = self.sp_rest_length.value()
            self._apply_link_endpoint_edits()
        elif isinstance(self.current_obj, Rope):
            self.current_obj.damping = self.sp_damping.value()
            self.current_obj.length = self.sp_rest_length.value()
            self._apply_link_endpoint_edits()

        self.property_changed.emit()

    def _apply_link_endpoint_edits(self):
        # 坐标编辑：如果坐标改变，自动解除挂载
        new_sx, new_sy = self.sp_start_x.value(), self.sp_start_y.value()
        if abs(new_sx - self.current_obj.start_pos[0]) > 0.01 or abs(new_sy - self.current_obj.start_pos[1]) > 0.01:
            self.current_obj.start_body_id = None
            self.current_obj.start_pos[0], self.current_obj.start_pos[1] = new_sx, new_sy
            
        new_ex, new_ey = self.sp_end_x.value(), self.sp_end_y.value()
        if abs(new_ex - self.current_obj.end_pos[0]) > 0.01 or abs(new_ey - self.current_obj.end_pos[1]) > 0.01:
            self.current_obj.end_body_id = None
            self.current_obj.end_pos[0], self.current_obj.end_pos[1] = new_ex, new_ey
        # 重新刷新显示（以防解除挂载后 UI 需要更新文本）
        if isinstance(self.current_obj, Spring):
            self.update_from_object()

    def unbind_start(self):
        if isinstance(self.current_obj, Spring):
            self.current_obj.start_body_id = None
            self.update_from_object()
            self.property_changed.emit()

    def unbind_end(self):
        if isinstance(self.current_obj, Spring):
            self.current_obj.end_body_id = None
            self.update_from_object()
            self.property_changed.emit()
