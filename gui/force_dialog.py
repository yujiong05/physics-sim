from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QDialogButtonBox, QLabel

class ForceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("施加外力")
        self.resize(300, 150)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.sp_magnitude = QDoubleSpinBox()
        self.sp_magnitude.setRange(0, 1000000)
        self.sp_magnitude.setValue(1000)
        self.sp_magnitude.setSuffix(" N")
        
        self.sp_angle = QDoubleSpinBox()
        self.sp_angle.setRange(-360, 360)
        self.sp_angle.setValue(-90)
        self.sp_angle.setSuffix(" °")
        self.sp_angle.setToolTip("0=向右，90=向下，-90=向上")
        
        self.sp_duration = QDoubleSpinBox()
        self.sp_duration.setRange(0.01, 60)
        self.sp_duration.setValue(1.0)
        self.sp_duration.setSuffix(" s")
        self.sp_duration.setSingleStep(0.1)
        
        form_layout.addRow("力的大小:", self.sp_magnitude)
        form_layout.addRow("力的方向:", self.sp_angle)
        form_layout.addRow("", QLabel("<small>0=向右，90=向下，-90=向上</small>"))
        form_layout.addRow("持续时间:", self.sp_duration)
        
        layout.addLayout(form_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
    def get_values(self):
        return (
            self.sp_magnitude.value(),
            self.sp_angle.value(),
            self.sp_duration.value()
        )
