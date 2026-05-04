from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QGraphicsView, QToolBar, QAction, 
                             QActionGroup, QFileDialog, QMessageBox, QLabel)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
import pyqtgraph as pg
import numpy as np
import math

from gui.scene import PhysicsScene
from core.engine import PhysicsEngine
from core.models import Ball, Block, Spring
from gui.property_panel import PropertyPanel
from gui.object_create_panel import ObjectCreatePanel
from storage.project_io import save_project, load_project
from templates.experiment_templates import ALL_TEMPLATES

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("二维物理仿真实验室")
        self.resize(1300, 800)
        
        self.engine = PhysicsEngine()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        
        # 绘图数据
        self.time_data = []
        self.vel_data = []
        self.tracked_ball = None 
        self.ball_counter = 1
        self.current_file_path = None
        
        self.create_menus()
        self.create_template_menu()
        self.init_ui()
        self.reset_simulation()

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
        ball_counter = template_data.get("ball_counter", 1)
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

        self.apply_project_data(engine_data, objects, ball_counter, scene_data)
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
            engine_data, objects, ball_counter, scene_data = load_project(path)
            self.apply_project_data(engine_data, objects, ball_counter, scene_data)
            self.current_file_path = path
            self.setWindowTitle(f"二维物理仿真实验室 - {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开项目: {str(e)}")

    def apply_project_data(self, engine_data, objects, ball_counter, scene_data):
        self.clear_scene()
        self.engine.time = engine_data.get("time", 0.0)
        if "gravity" in engine_data:
            self.engine.gravity = np.array(engine_data["gravity"], dtype=np.float64)
        if "bounds" in engine_data:
            self.engine.bounds = tuple(engine_data["bounds"])

        self.ball_counter = ball_counter

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

        if objects:
            self.tracked_ball = objects[0]
            self.scene.update_items(playing=False)

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
                save_project(self.current_file_path, self.engine, self.ball_counter, scene_data)
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
        self.scene.request_create_object.connect(self.create_object_at)
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
        
        # 3. 右侧：属性面板和图表
        right_layout = QVBoxLayout()
        self.property_panel = PropertyPanel()
        self.property_panel.property_changed.connect(self.on_property_changed)
        self.scene.object_selected.connect(self.on_object_selected)
        right_layout.addWidget(self.property_panel)
        
        self.plot_widget = pg.PlotWidget(title="速度-时间曲线 (Y轴)")
        self.plot_widget.setLabel('left', 'Velocity Y', units='px/s')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_curve = self.plot_widget.plot(pen='r')
        right_layout.addWidget(self.plot_widget)
        
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

    def start_create_object(self, object_type, params):
        self.scene.set_pending_create(object_type, params)
        self.action_select.setChecked(False)
        self.statusBar().showMessage(f"等待在画布上放置: {object_type}")

    def create_object_at(self, object_type, x, y, params):
        obj = None
        name = params.get("name", f"{object_type}_{self.ball_counter}")
        self.ball_counter += 1
        
        if object_type == "ball":
            obj = Ball(x=x, y=y, radius=params["radius"], mass=params["mass"], name=name)
            obj.vel = np.array([params["vx"], params["vy"]], dtype=np.float64)
            obj.restitution = params["restitution"]
            obj.color = params["color"]
        elif object_type == "block":
            obj = Block(x=x, y=y, width=params["width"], height=params["height"], mass=params["mass"], name=name)
            obj.vel = np.array([params["vx"], params["vy"]], dtype=np.float64)
            obj.restitution = params["restitution"]
            obj.color = params["color"]
        elif object_type == "spring":
            length = params["length"]
            angle_rad = math.radians(params["angle"])
            end_x = x + length * math.cos(angle_rad)
            end_y = y + length * math.sin(angle_rad)
            obj = Spring(start_pos=[x, y], end_pos=[end_x, end_y], 
                         stiffness=params["stiffness"], damping=params["damping"], 
                         rest_length=params["rest_length"], name=name, color=params["color"])
        
        if obj:
            self.engine.add_object(obj)
            self.scene.add_physics_object(obj)
            if self.tracked_ball is None:
                self.tracked_ball = obj
            self.statusBar().showMessage(f"已创建: {name}")
        
        self.action_select.setChecked(True)

    def delete_selected(self):
        selected = self.scene.selectedItems()
        for item in selected:
            if hasattr(item, 'obj'):
                obj = item.obj
                self.engine.remove_object(obj)
                self.scene.remove_physics_object(obj)
                if self.tracked_ball == obj:
                    self.tracked_ball = None
                    self.time_data = []
                    self.vel_data = []
                    self.plot_curve.setData(self.time_data, self.vel_data)
        self.property_panel.set_object(None)

    def clear_scene(self):
        self.engine.clear()
        self.scene.clear_items()
        self.property_panel.set_object(None)
        self.tracked_ball = None
        self.time_data = []
        self.vel_data = []
        self.plot_curve.setData(self.time_data, self.vel_data)
        self.ball_counter = 1

    def on_object_selected(self, obj):
        self.property_panel.set_object(obj)
        self.tracked_ball = obj

    def on_property_changed(self):
        obj = self.property_panel.current_obj
        if obj and obj in self.scene.items_dict:
            item = self.scene.items_dict[obj]
            if hasattr(item, 'update_appearance'):
                item.update_appearance()

    def play_simulation(self):
        self.is_playing = True
        self.timer.start(16)
        self.statusBar().showMessage("仿真运行中...")
        
    def pause_simulation(self):
        self.is_playing = False
        self.timer.stop()
        self.statusBar().showMessage("仿真已暂停")
        
    def reset_simulation(self):
        self.pause_simulation()
        self.clear_scene()
        self.time_data = []
        self.vel_data = []
        self.plot_curve.setData([], [])
        self.statusBar().showMessage("重置完成")
        
    def update_simulation(self):
        dt = 0.016
        self.engine.step(dt)
        self.scene.update_items(record_trail=True, playing=True)
        
        if self.tracked_ball and not isinstance(self.tracked_ball, Spring):
            self.time_data.append(self.engine.time)
            self.vel_data.append(self.tracked_ball.vel[1])
            if len(self.time_data) > 500:
                self.time_data.pop(0)
                self.vel_data.pop(0)
            self.plot_curve.setData(self.time_data, self.vel_data)
