import pyqtgraph as pg
import csv
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QPushButton, QCheckBox, QFileDialog, QMessageBox, QScrollArea, QGridLayout, QLabel)
from PyQt5.QtCore import Qt
from core.models import Ball, Block, Spring

FIELD_UNITS = {
    "x": "x (m)",
    "y": "y (m)",
    "vx": "vx (m/s)",
    "vy": "vy (m/s)",
    "speed": "speed (m/s)",
    "ax": "ax eff. (m/s²)",
    "ay": "ay eff. (m/s²)",
    "kinetic_energy": "kinetic energy (J)",
    "potential_energy": "potential energy (J)",
    "current_length": "length (m)",
    "rest_length": "rest length (m)",
    "extension": "extension (m)",
    "spring_energy": "spring energy (J)",
    "time": "time (s)"
}

class DataPanel(QWidget):
    def __init__(self, recorder, parent=None):
        super().__init__(parent)
        self.recorder = recorder
        self.current_obj = None
        self.objects_list = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部提示
        tip = QLabel("显示单位：100 px = 1 m；图表已自动换算为 SI 单位。")
        tip.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(tip)

        # 1. 观测对象选择
        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(QLabel("观测对象:"))
        self.cb_objects = QComboBox()
        self.cb_objects.currentIndexChanged.connect(self._on_object_selected)
        h_layout1.addWidget(self.cb_objects)
        layout.addLayout(h_layout1)
        
        # 2. 曲线选择
        self.checkbox_container = QWidget()
        self.checkbox_layout = QGridLayout(self.checkbox_container)
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.checkbox_container)
        scroll.setMaximumHeight(100)
        layout.addWidget(scroll)
        
        self.checkboxes = {}
        
        # 3. 图表
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('bottom', 'Time (s)')
        layout.addWidget(self.plot_widget)
        
        # 4. 按钮
        h_layout2 = QHBoxLayout()
        self.btn_clear = QPushButton("清空数据")
        self.btn_clear.clicked.connect(self._on_clear_clicked)
        self.btn_export = QPushButton("导出 CSV")
        self.btn_export.clicked.connect(self._on_export_clicked)
        h_layout2.addWidget(self.btn_clear)
        h_layout2.addWidget(self.btn_export)
        layout.addLayout(h_layout2)

    def refresh_objects(self, objects):
        self.objects_list = objects
        current_id = self.current_obj.id if self.current_obj else None
        
        self.cb_objects.blockSignals(True)
        self.cb_objects.clear()
        
        new_idx = -1
        # 过滤静态物体
        filtered_objects = [obj for obj in objects if getattr(obj, "type", "") not in ["static_block", "wall", "ramp", "platform"]]
        for i, obj in enumerate(filtered_objects):
            name = obj.name
            self.cb_objects.addItem(name, obj)
            if current_id == obj.id:
                new_idx = i
                
        if new_idx >= 0:
            self.cb_objects.setCurrentIndex(new_idx)
        elif self.cb_objects.count() > 0:
            self.cb_objects.setCurrentIndex(0)
            self.current_obj = self.cb_objects.itemData(0)
            self._update_checkboxes()
        else:
            self.current_obj = None
            self._update_checkboxes()
            
        self.cb_objects.blockSignals(False)
        self.update_plot()

    def select_object(self, obj):
        if obj is None: return
        for i in range(self.cb_objects.count()):
            if self.cb_objects.itemData(i).id == obj.id:
                self.cb_objects.setCurrentIndex(i)
                break

    def _on_object_selected(self, index):
        if index >= 0:
            new_obj = self.cb_objects.itemData(index)
            if self.current_obj is None or new_obj.id != self.current_obj.id:
                self.current_obj = new_obj
                self._update_checkboxes()
                self.update_plot()

    def _update_checkboxes(self):
        for i in reversed(range(self.checkbox_layout.count())): 
            self.checkbox_layout.itemAt(i).widget().setParent(None)
        self.checkboxes.clear()
        
        if self.current_obj is None:
            return
            
        if isinstance(self.current_obj, (Ball, Block)):
            fields = ["x", "y", "vx", "vy", "speed", "ax", "ay", "kinetic_energy", "potential_energy"]
            default_fields = ["vy"]
        elif isinstance(self.current_obj, Spring):
            fields = ["current_length", "rest_length", "extension", "spring_energy"]
            default_fields = ["extension"]
        else:
            fields = []
            default_fields = []
            
        row, col = 0, 0
        for field in fields:
            display_name = FIELD_UNITS.get(field, field)
            cb = QCheckBox(display_name)
            cb.setChecked(field in default_fields)
            cb.stateChanged.connect(self.update_plot)
            self.checkbox_layout.addWidget(cb, row, col)
            self.checkboxes[field] = cb
            
            col += 1
            if col > 2:
                col = 0
                row += 1

    def _on_clear_clicked(self):
        if self.current_obj:
            self.recorder.clear_object(self.current_obj.id)
            self.update_plot()

    def _on_export_clicked(self):
        if not self.current_obj:
            return
            
        data = self.recorder.get_data(self.current_obj.id)
        if not data:
            QMessageBox.information(self, "提示", "暂无数据可导出")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", f"{self.current_obj.name}_data.csv", "CSV Files (*.csv)")
        if not path:
            return
            
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                raw_fieldnames = list(data[0].keys())
                # 带单位的表头
                display_headers = [FIELD_UNITS.get(fn, fn) for fn in raw_fieldnames]
                
                writer = csv.DictWriter(f, fieldnames=raw_fieldnames)
                # 手动写入带单位的表头
                f.write(",".join(display_headers) + "\n")
                
                for row in data:
                    # 保留 4 位小数
                    formatted_row = {k: round(v, 4) if isinstance(v, (float, int)) else v for k, v in row.items()}
                    writer.writerow(formatted_row)
                    
            QMessageBox.information(self, "提示", "导出成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def update_plot(self):
        self.plot_widget.clear()
        if not self.current_obj: return
        
        data = self.recorder.get_data(self.current_obj.id)
        if not data: return
        
        # 只保留最近 1500 个点，防止性能下降并使曲线更聚焦
        if len(data) > 1500:
            data = data[-1500:]
            
        times = [d["time"] for d in data]
        
        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        color_idx = 0
        
        active_fields = []
        for field, cb in self.checkboxes.items():
            if cb.isChecked():
                active_fields.append(field)
                values = [d[field] for d in data]
                display_name = FIELD_UNITS.get(field, field)
                pen = pg.mkPen(color=colors[color_idx % len(colors)], width=2)
                # 开启抗锯齿
                self.plot_widget.plot(times, values, name=display_name, pen=pen, antialias=True)
                color_idx += 1
                
        # 设置 Y 轴标签
        if len(active_fields) == 1:
            self.plot_widget.setLabel('left', FIELD_UNITS.get(active_fields[0], "Value"))
        elif len(active_fields) > 1:
            self.plot_widget.setLabel('left', "Value (mixed units)")
        else:
            self.plot_widget.setLabel('left', "Value")
