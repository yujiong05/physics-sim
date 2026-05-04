from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox, QGroupBox, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from core.models import Ball, Block, Spring

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
        self.sp_vx = QDoubleSpinBox(); self.sp_vx.setRange(-10000, 10000)
        self.sp_vy = QDoubleSpinBox(); self.sp_vy.setRange(-10000, 10000)
        self.sp_restitution = QDoubleSpinBox(); self.sp_restitution.setRange(0, 1.5); self.sp_restitution.setSingleStep(0.1)
        
        # 小球属性
        self.sp_radius = QDoubleSpinBox(); self.sp_radius.setRange(1, 1000)
        
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
        self.form_layout.addRow("质量:", self.sp_mass)
        self.form_layout.addRow("速度 X:", self.sp_vx)
        self.form_layout.addRow("速度 Y:", self.sp_vy)
        self.form_layout.addRow("弹性系数:", self.sp_restitution)
        self.form_layout.addRow("半径:", self.sp_radius)
        self.form_layout.addRow("宽度:", self.sp_width)
        self.form_layout.addRow("高度:", self.sp_height)
        self.form_layout.addRow("劲度系数:", self.sp_stiffness)
        self.form_layout.addRow("阻尼系数:", self.sp_damping)
        self.form_layout.addRow("静止长度:", self.sp_rest_length)
        self.form_layout.addRow("起点 X:", self.sp_start_x)
        self.form_layout.addRow("起点 Y:", self.sp_start_y)
        self.form_layout.addRow("终点 X:", self.sp_end_x)
        self.form_layout.addRow("终点 Y:", self.sp_end_y)
        self.form_layout.addRow(self.lbl_start_title, self.start_mount_container)
        self.form_layout.addRow(self.lbl_end_title, self.end_mount_container)
        
        layout.addWidget(self.group_box)
        layout.addStretch()
        
        # 绑定信号
        self.le_name.textChanged.connect(self._on_value_changed)
        for w in [self.sp_mass, self.sp_vx, self.sp_vy, self.sp_restitution, 
                  self.sp_radius, self.sp_width, self.sp_height,
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
            
    def update_from_object(self):
        if self.current_obj is None: return
        self._updating = True
        
        self.lb_id.setText(str(self.current_obj.id)[:12])
        self.le_name.setText(self.current_obj.name)
        
        is_ball = isinstance(self.current_obj, Ball)
        is_block = isinstance(self.current_obj, Block)
        is_spring = isinstance(self.current_obj, Spring)

        # 刚体属性
        rigid_visible = is_ball or is_block
        for w in [self.sp_mass, self.sp_vx, self.sp_vy, self.sp_restitution]:
            w.setVisible(rigid_visible)
            self.form_layout.labelForField(w).setVisible(rigid_visible)

        self.sp_radius.setVisible(is_ball); self.form_layout.labelForField(self.sp_radius).setVisible(is_ball)
        self.sp_width.setVisible(is_block); self.form_layout.labelForField(self.sp_width).setVisible(is_block)
        self.sp_height.setVisible(is_block); self.form_layout.labelForField(self.sp_height).setVisible(is_block)

        # 弹簧属性
        for w in [self.sp_stiffness, self.sp_damping, self.sp_rest_length, self.sp_start_x, self.sp_start_y, self.sp_end_x, self.sp_end_y]:
            w.setVisible(is_spring)
            self.form_layout.labelForField(w).setVisible(is_spring)
        
        self.lbl_start_title.setVisible(is_spring)
        self.start_mount_container.setVisible(is_spring)
        self.lbl_end_title.setVisible(is_spring)
        self.end_mount_container.setVisible(is_spring)

        # 填充数值
        if rigid_visible:
            self.sp_mass.setValue(self.current_obj.mass)
            self.sp_vx.setValue(self.current_obj.vel[0]); self.sp_vy.setValue(self.current_obj.vel[1])
            self.sp_restitution.setValue(self.current_obj.restitution)
            if is_ball: self.sp_radius.setValue(self.current_obj.radius)
            elif is_block: self.sp_width.setValue(self.current_obj.width); self.sp_height.setValue(self.current_obj.height)
        elif is_spring:
            self.sp_stiffness.setValue(self.current_obj.stiffness)
            self.sp_damping.setValue(self.current_obj.damping)
            self.sp_rest_length.setValue(self.current_obj.rest_length)
            self.sp_start_x.setValue(self.current_obj.start_pos[0]); self.sp_start_y.setValue(self.current_obj.start_pos[1])
            self.sp_end_x.setValue(self.current_obj.end_pos[0]); self.sp_end_y.setValue(self.current_obj.end_pos[1])
            self.lb_start_mount.setText(self.current_obj.start_body_id[:8] if self.current_obj.start_body_id else "无")
            self.lb_end_mount.setText(self.current_obj.end_body_id[:8] if self.current_obj.end_body_id else "无")

        self._updating = False
        
    def _on_value_changed(self):
        if self._updating or self.current_obj is None: return
        self.current_obj.name = self.le_name.text()
        if isinstance(self.current_obj, (Ball, Block)):
            self.current_obj.mass = self.sp_mass.value()
            self.current_obj.vel[0], self.current_obj.vel[1] = self.sp_vx.value(), self.sp_vy.value()
            self.current_obj.restitution = self.sp_restitution.value()
            if isinstance(self.current_obj, Ball): self.current_obj.radius = self.sp_radius.value()
            else: self.current_obj.width, self.current_obj.height = self.sp_width.value(), self.sp_height.value()
        elif isinstance(self.current_obj, Spring):
            self.current_obj.stiffness = self.sp_stiffness.value()
            self.current_obj.damping = self.sp_damping.value()
            self.current_obj.rest_length = self.sp_rest_length.value()
            
            # 坐标编辑：如果坐标改变，自动解除挂载
            new_sx, new_sy = self.sp_start_x.value(), self.sp_start_y.value()
            if abs(new_sx - self.current_obj.start_pos[0]) > 0.01 or abs(new_sy - self.current_obj.start_pos[1]) > 0.01:
                self.current_obj.start_body_id = None
                self.current_obj.start_pos[0], self.current_obj.start_pos[1] = new_sx, new_sy
                
            new_ex, new_ey = self.sp_end_x.value(), self.sp_end_y.value()
            if abs(new_ex - self.current_obj.end_pos[0]) > 0.01 or abs(new_ey - self.current_obj.end_pos[1]) > 0.01:
                self.current_obj.end_body_id = None
                self.current_obj.end_pos[0], self.current_obj.end_pos[1] = new_ex, new_ey

        self.property_changed.emit()
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
