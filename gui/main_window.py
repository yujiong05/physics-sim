from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QGraphicsView, QToolBar, QAction, 
                             QActionGroup, QFileDialog, QMessageBox, QLabel, QDialog)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
import pyqtgraph as pg
import numpy as np
import math

from gui.scene import PhysicsScene
from core.engine import PhysicsEngine
from core.models import Ball, Block, Spring, StaticBlock, Groove
from gui.property_panel import PropertyPanel
from gui.object_create_panel import ObjectCreatePanel
from gui.data_panel import DataPanel
from core.data_recorder import DataRecorder
from gui.force_dialog import ForceDialog

from storage.project_io import save_project, load_project
from templates.experiment_templates import ALL_TEMPLATES

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("二维物理仿真实验室")
        self.resize(1300, 800)
        
        self.engine = PhysicsEngine()
        self.recorder = DataRecorder()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        
        self.ball_counter = 1
        self.block_counter = 1
        self.spring_counter = 1
        self.platform_counter = 1
        self.wall_counter = 1
        self.ramp_counter = 1
        self.groove_counter = 1
        self.initial_state_snapshot = None
        self.current_file_path = None

        
        self.create_menus()
        self.create_template_menu()
        self.init_ui()
        self.clear_scene()
        
    def update_name_counters_from_scene(self):
        import re
        max_c = {"ball":0, "block":0, "spring":0, "platform":0, "wall":0, "ramp":0, "groove":0}
        for obj in self.engine.objects:
            m = re.match(r'(ball|block|spring|platform|wall|ramp|groove)(\d+)', obj.name.lower())
            if m:
                typ, num = m.groups()
                num = int(num)
                if typ in max_c and num > max_c[typ]: max_c[typ] = num
        self.ball_counter = max(self.ball_counter, max_c["ball"] + 1)
        self.block_counter = max(self.block_counter, max_c["block"] + 1)
        self.spring_counter = max(self.spring_counter, max_c["spring"] + 1)
        self.platform_counter = max(self.platform_counter, max_c["platform"] + 1)
        self.wall_counter = max(self.wall_counter, max_c["wall"] + 1)
        self.ramp_counter = max(self.ramp_counter, max_c["ramp"] + 1)
        self.groove_counter = max(self.groove_counter, max_c["groove"] + 1)
        
    def get_next_default_name(self, object_type):
        if object_type == "ball":
            name = f"ball{self.ball_counter}"
            self.ball_counter += 1
        elif object_type == "block":
            name = f"block{self.block_counter}"
            self.block_counter += 1
        elif object_type == "spring":
            name = f"spring{self.spring_counter}"
            self.spring_counter += 1
        elif object_type == "platform":
            name = f"platform{self.platform_counter}"
            self.platform_counter += 1
        elif object_type == "wall":
            name = f"wall{self.wall_counter}"
            self.wall_counter += 1
        elif object_type == "ramp":
            name = f"ramp{self.ramp_counter}"
            self.ramp_counter += 1
        elif object_type == "groove":
            name = f"groove{self.groove_counter}"
            self.groove_counter += 1
        else:
            name = f"{object_type}_1"
        return name
        
    def capture_initial_state(self):
        if self.is_playing: return
        objects = [obj.get_state() for obj in self.engine.objects]
        self.initial_state_snapshot = {
            "engine": {
                "gravity": self.engine.gravity.tolist(),
                "bounds": self.engine.bounds
            },
            "objects": objects
        }
        
    def restore_initial_state(self):
        self.pause_simulation()
        if not self.initial_state_snapshot: return
        
        self.scene.clear_items()
        self.engine.clear()
        
        engine_data = self.initial_state_snapshot["engine"]
        self.engine.gravity = np.array(engine_data["gravity"], dtype=np.float64)
        self.engine.bounds = tuple(engine_data["bounds"])
        
        objects = []
        for obj_data in self.initial_state_snapshot["objects"]:
            t = obj_data.get("type")
            if t == "ball": objects.append(Ball.from_state(obj_data))
            elif t == "block": objects.append(Block.from_state(obj_data))
            elif t == "spring": objects.append(Spring.from_state(obj_data))
            elif t == "static_block": objects.append(StaticBlock.from_state(obj_data))
            elif t == "groove": objects.append(Groove.from_state(obj_data))
            
        for obj in objects:
            self.engine.add_object(obj)
            self.scene.add_physics_object(obj)
            
        self.engine.clear_forces()
        self.engine.time = 0.0
        self.scene.clear_all_trails()
        self.recorder.clear_all()
        self.scene.update_items(playing=False)
        self.data_panel.refresh_objects(self.engine.objects)
        
        if self.property_panel.current_obj:
            cid = self.property_panel.current_obj.id
            for obj in self.engine.objects:
                if obj.id == cid:
                    self.property_panel.set_object(obj)
                    self.data_panel.select_object(obj)
                    break


    def create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件(&F)")
        
        action_new = QAction("新建(&N)", self)
        action_new.setShortcut("Ctrl+N")
        action_new.triggered.connect(self.new_project)
        
        action_open = QAction("打开(&O)...", self)
        action_open.setShortcut("Ctrl+O")
        action_open.triggered.connect(self.open_project)
        
        action_save = QAction("保存(&S)", self)
        action_save.setShortcut("Ctrl+S")
        action_save.triggered.connect(self.save_project)
        
        action_save_as = QAction("另存为(&A)...", self)
        action_save_as.setShortcut("Ctrl+Shift+S")
        action_save_as.triggered.connect(self.save_as_project)
        
        file_menu.addAction(action_new)
        file_menu.addAction(action_open)
        file_menu.addAction(action_save)
        file_menu.addAction(action_save_as)

    def create_template_menu(self):
        menubar = self.menuBar()
        tmpl_menu = menubar.addMenu("实验模板(&T)")
        for template_fn in ALL_TEMPLATES:
            data = template_fn()
            action = QAction(data["name"], self)
            action.triggered.connect(lambda checked, fn=template_fn: self.load_template(fn()))
            tmpl_menu.addAction(action)

    def load_template(self, template_data):
        self.pause_simulation()
        engine_data = template_data.get("engine", {})
        counters = template_data.get("counters", {"ball": template_data.get("ball_counter", 1), "block": 1, "spring": 1})
        scene_data   = template_data.get("scene", {})

        objects = []
        for obj_data in template_data.get("objects", []):
            t = obj_data.get("type")
            if t == "ball":
                objects.append(Ball.from_state(obj_data))
            elif t == "block":
                objects.append(Block.from_state(obj_data))
            elif t == "spring":
                objects.append(Spring.from_state(obj_data))

        self.apply_project_data(engine_data, objects, counters, scene_data)
        self.current_file_path = None
        self.setWindowTitle(f"二维物理仿真实验室 - [{template_data.get('name', '实验模板')}]")

    def new_project(self):
        self.pause_simulation()
        self.clear_scene()
        self.current_file_path = None
        self.setWindowTitle("二维物理仿真实验室")

    def open_project(self):
        self.pause_simulation()
        path, _ = QFileDialog.getOpenFileName(self, "打开项目", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            engine_data, objects, counters, scene_data = load_project(path)
            self.apply_project_data(engine_data, objects, counters, scene_data)
            self.current_file_path = path
            self.setWindowTitle(f"二维物理仿真实验室 - {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开项目: {str(e)}")

    def apply_project_data(self, engine_data, objects, counters, scene_data):
        self.clear_scene()
        self.engine.clear_forces()
        self.engine.time = engine_data.get("time", 0.0)
        if "gravity" in engine_data:
            self.engine.gravity = np.array(engine_data["gravity"], dtype=np.float64)
        if "bounds" in engine_data:
            self.engine.bounds = tuple(engine_data["bounds"])

        self.ball_counter = counters.get("ball", 1)
        self.block_counter = counters.get("block", 1)
        self.spring_counter = counters.get("spring", 1)
        self.platform_counter = counters.get("platform", 1)
        self.wall_counter = counters.get("wall", 1)
        self.ramp_counter = counters.get("ramp", 1)
        self.groove_counter = counters.get("groove", 1)

        # 实验模式同步
        mode = scene_data.get("experiment_mode", "vertical")
        if mode == "horizontal":
            self.create_panel.rb_horizontal.setChecked(True)
        else:
            self.create_panel.rb_vertical.setChecked(True)

        show_arrow = scene_data.get("show_velocity_arrow", False)
        show_trail = scene_data.get("show_trail", False)
        self.action_show_arrow.setChecked(show_arrow)
        self.action_show_trail.setChecked(show_trail)
        self.scene.set_show_velocity_arrow(show_arrow)
        self.scene.set_show_trail(show_trail)

        for obj in objects:
            self.engine.add_object(obj)
            self.scene.add_physics_object(obj)

        self.scene.update_items(playing=False)
        self.update_name_counters_from_scene()
        self.data_panel.refresh_objects(self.engine.objects)
        self.capture_initial_state()

    def save_project(self):
        if not self.current_file_path:
            self.save_as_project()
        else:
            try:
                scene_data = {
                    "show_velocity_arrow": self.scene.show_velocity_arrow,
                    "show_trail": self.scene.show_trail,
                    "experiment_mode": "horizontal" if self.create_panel.rb_horizontal.isChecked() else "vertical"
                }
                counters = {"ball": self.ball_counter, "block": self.block_counter, "spring": self.spring_counter,
                            "platform": self.platform_counter, "wall": self.wall_counter, "ramp": self.ramp_counter,
                            "groove": self.groove_counter}
                save_project(self.current_file_path, self.engine, counters, scene_data)
                self.setWindowTitle(f"二维物理仿真实验室 - {self.current_file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存项目: {str(e)}")

    def save_as_project(self):
        self.pause_simulation()
        path, _ = QFileDialog.getSaveFileName(self, "另存为项目", "", "JSON Files (*.json)")
        if path:
            self.current_file_path = path
            self.save_project()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 1. 左侧：对象创建控制面板
        self.create_panel = ObjectCreatePanel()
        self.create_panel.mode_changed.connect(self.set_experiment_mode)
        self.create_panel.create_requested.connect(self.start_create_object)
        main_layout.addWidget(self.create_panel)

        # 2. 中间：画布和播放控制
        mid_layout = QVBoxLayout()
        
        # 工具栏
        self.toolbar = QToolBar("编辑工具")
        self.action_select = QAction("选择模式", self)
        self.action_select.setCheckable(True)
        self.action_select.setChecked(True)
        self.action_select.triggered.connect(lambda: self.scene.set_mode('select'))
        
        self.action_delete = QAction("删除选中物体", self)
        self.action_delete.triggered.connect(self.delete_selected)
        
        self.action_clear = QAction("清空场景", self)
        self.action_clear.triggered.connect(self.clear_scene)
        
        self.action_show_arrow = QAction("显示速度箭头", self)
        self.action_show_arrow.setCheckable(True)
        self.action_show_arrow.triggered.connect(lambda checked: self.scene.set_show_velocity_arrow(checked))
        
        self.action_show_trail = QAction("显示运动轨迹", self)
        self.action_show_trail.setCheckable(True)
        self.action_show_trail.triggered.connect(lambda checked: self.scene.set_show_trail(checked))
        
        self.toolbar.addAction(self.action_select)
        self.toolbar.addAction(self.action_delete)
        self.toolbar.addAction(self.action_clear)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_show_arrow)
        self.toolbar.addAction(self.action_show_trail)
        
        mid_layout.addWidget(self.toolbar)
        
        # 画布
        self.scene = PhysicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(1)
        mid_layout.addWidget(self.view)
        
        # 播放控制
        controls_layout = QHBoxLayout()
        self.btn_play = QPushButton("播放")
        self.btn_pause = QPushButton("暂停")
        self.btn_reset = QPushButton("重置")
        self.btn_play.clicked.connect(self.play_simulation)
        self.btn_pause.clicked.connect(self.pause_simulation)
        self.btn_reset.clicked.connect(self.reset_simulation)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_pause)
        controls_layout.addWidget(self.btn_reset)
        mid_layout.addLayout(controls_layout)
        
        main_layout.addLayout(mid_layout, stretch=2)
        
        # 右侧面板
        right_layout = QVBoxLayout()
        self.property_panel = PropertyPanel()
        self.property_panel.property_changed.connect(self.on_property_changed)
        right_layout.addWidget(self.property_panel)
        
        self.scene.object_selected.connect(self.on_object_selected)
        self.scene.request_create_object.connect(self.create_object_at)
        self.scene.request_apply_force.connect(self.show_apply_force_dialog)
        self.scene.request_delete_object.connect(self.delete_object)
        
        self.data_panel = DataPanel(self.recorder)
        right_layout.addWidget(self.data_panel)
        
        main_layout.addLayout(right_layout, stretch=1)

        self.is_playing = False
        self.statusBar().showMessage("准备就绪")

    def set_experiment_mode(self, mode):
        if mode == "horizontal":
            self.engine.gravity = np.array([0.0, 0.0], dtype=np.float64)
            self.statusBar().showMessage("切换到水平模式 (无重力)")
        else:
            self.engine.gravity = np.array([0.0, 980.0], dtype=np.float64)
            self.statusBar().showMessage("切换到垂直模式 (重力: 9.8)")
        if not self.is_playing: self.capture_initial_state()

    def start_create_object(self, object_type, params):
        self.scene.set_pending_create(object_type, params)
        self.action_select.setChecked(False)
        self.statusBar().showMessage(f"等待在画布上放置: {object_type}")

    def create_object_at(self, object_type, x, y, params):
        import time
        if not hasattr(self, '_last_create_signature'):
            self._last_create_signature = None
        sig = (object_type, round(x, 1), round(y, 1), time.monotonic())
        if self._last_create_signature:
            last_sig = self._last_create_signature
            if last_sig[0] == sig[0] and last_sig[1] == sig[1] and last_sig[2] == sig[2]:
                if sig[3] - last_sig[3] < 0.1:
                    print(f"Warning: Ignored duplicate create_object_at for {object_type} at {x}, {y}")
                    return
        self._last_create_signature = sig
        
        objects_to_add = []
        name = params.get("name", "").strip()
        if not name or name.lower() in ["ball", "block", "spring", "未命名"]:
            name = self.get_next_default_name(object_type)
        
        if object_type == "ball":
            obj = Ball(x=x, y=y, radius=params["radius"], mass=params["mass"], name=name)
            obj.vel = np.array([params["vx"], params["vy"]], dtype=np.float64)
            obj.restitution = params["restitution"]
            obj.color = params["color"]
            objects_to_add.append(obj)
        elif object_type == "block":
            obj = Block(x=x, y=y, width=params["width"], height=params["height"], mass=params["mass"], name=name)
            obj.vel = np.array([params["vx"], params["vy"]], dtype=np.float64)
            obj.restitution = params["restitution"]
            obj.color = params["color"]
            objects_to_add.append(obj)
        elif object_type == "spring":
            length = params["length"]
            angle_rad = math.radians(params["angle"])
            end_x = x + length * math.cos(angle_rad)
            end_y = y + length * math.sin(angle_rad)
            obj = Spring(start_pos=[x, y], end_pos=[end_x, end_y], 
                         stiffness=params["stiffness"], damping=params["damping"], 
                         rest_length=params["rest_length"], name=name, color=params["color"])
            objects_to_add.append(obj)
        elif object_type in ["platform", "wall", "ramp"]:
            obj = StaticBlock(x=x, y=y, width=params["width"], height=params["height"], 
                              angle=params["angle"], name=name)
            obj.restitution = params["restitution"]
            obj.friction = params["friction"]
            obj.color = params["color"]
            objects_to_add.append(obj)
        elif object_type == "groove":
            obj = Groove(x=x, y=y, radius=params["radius"], thickness=params["thickness"], name=name)
            obj.restitution = params["restitution"]
            obj.friction = params["friction"]
            obj.color = params["color"]
            objects_to_add.append(obj)
        
        if objects_to_add:
            for obj in objects_to_add:
                self.engine.add_object(obj)
                self.scene.add_physics_object(obj)
            self.data_panel.refresh_objects(self.engine.objects)
            if not self.is_playing: self.capture_initial_state()
            self.statusBar().showMessage(f"已创建: {name}")
        
        self.action_select.setChecked(True)

    def delete_selected(self):
        selected = self.scene.selectedItems()
        objs_to_delete = []
        for item in selected:
            owner, obj = self.scene.find_owner_item(item)
            if obj and obj not in objs_to_delete:
                objs_to_delete.append(obj)
        for obj in objs_to_delete:
            self.delete_object(obj)
        self.scene.clearSelection()

    def delete_object(self, obj):
        if obj not in self.engine.objects:
            return
            
        # 如果删除的是 Ball 或 Block，解除关联的弹簧绑定
        if isinstance(obj, (Ball, Block)):
            for other in self.engine.objects:
                if isinstance(other, Spring):
                    if other.start_body_id == obj.id:
                        other.start_body_id = None
                        other.start_pos = other.start_pos.copy() # preserve pos
                    if other.end_body_id == obj.id:
                        other.end_body_id = None
                        other.end_pos = other.end_pos.copy() # preserve pos
                        
        self.engine.remove_object(obj)
        self.engine.remove_forces_for_object(obj.id)
        self.scene.remove_physics_object(obj)
        self.recorder.remove_object(obj.id)
        
        if self.property_panel.current_obj == obj:
            self.property_panel.set_object(None)
            
        self.data_panel.refresh_objects(self.engine.objects)
        if not self.is_playing: self.capture_initial_state()

    def show_apply_force_dialog(self, obj):
        if not isinstance(obj, (Ball, Block)):
            QMessageBox.information(self, "提示", "该对象不能施加力")
            return
            
        dialog = ForceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            magnitude, angle_deg, duration = dialog.get_values()
            self.engine.add_force(obj.id, magnitude, angle_deg, duration)
            self.statusBar().showMessage(f"已对 {obj.name} 施加 {magnitude}N，方向 {angle_deg}°，持续 {duration}s")

    def clear_scene(self):
        self.engine.clear()
        self.scene.clear_items()
        self.recorder.clear_all()
        self.property_panel.set_object(None)
        self.data_panel.refresh_objects(self.engine.objects)
        self.ball_counter = 1
        self.block_counter = 1
        self.spring_counter = 1
        self.platform_counter = 1
        self.wall_counter = 1
        self.ramp_counter = 1
        self.groove_counter = 1
        if not self.is_playing: self.capture_initial_state()

    def on_object_selected(self, obj):
        self.property_panel.set_object(obj)
        self.data_panel.select_object(obj)
        
    def on_property_changed(self):
        self.scene.update_items(playing=False)
        self.data_panel.refresh_objects(self.engine.objects)
        if not self.is_playing: self.capture_initial_state()
        obj = self.property_panel.current_obj
        if obj and obj in self.scene.items_dict:
            item = self.scene.items_dict[obj]
            if hasattr(item, 'update_appearance'):
                item.update_appearance()

    def play_simulation(self):
        if not self.is_playing: self.capture_initial_state()
        self.is_playing = True
        self.timer.start(16)
        self.statusBar().showMessage("仿真运行中...")
        
    def pause_simulation(self):
        self.is_playing = False
        self.timer.stop()
        self.statusBar().showMessage("仿真已暂停")
        
    def reset_simulation(self):
        self.restore_initial_state()
        self.statusBar().showMessage("重置完成")
        
    def update_simulation(self):
        dt = 0.016
        self.engine.step(dt)
        self.scene.update_items(record_trail=True, playing=True)
        self.recorder.record(self.engine.time, self.engine.objects, self.engine)
        self.data_panel.update_plot()
