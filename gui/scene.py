"""
gui/scene.py
场景图元管理：优化点击式挂载交互与高亮显示。
"""
import math
from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsEllipseItem, QGraphicsRectItem,
                              QGraphicsItem, QGraphicsLineItem, QGraphicsPathItem, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt5.QtGui import QBrush, QPen, QColor, QPainterPath, QTransform
import numpy as np

from core.models import Ball, Block, Spring, StaticBlock, Groove

# ─────────────────────────────────────────────────────────
# 公共 mixin：速度箭头 + 轨迹线
# ─────────────────────────────────────────────────────────
class _TrailArrowMixin:
    def _init_trail_arrow(self):
        self.velocity_arrow = QGraphicsLineItem(self)
        self.velocity_arrow.setPen(QPen(Qt.red, 2))
        self.velocity_arrow.setZValue(8)
        self.velocity_arrow.setVisible(False)
        self.trail_path_item = QGraphicsPathItem()
        self.trail_path_item.setPen(QPen(QColor(150, 150, 150, 150), 2, Qt.DashLine))
        self.trail_path_item.setZValue(5)
        self.trail_path_item.setVisible(False)
        self.trail_points = []

    def update_velocity_arrow(self):
        vx, vy = self.obj.vel[0], self.obj.vel[1]
        speed = math.sqrt(vx * vx + vy * vy)
        if speed > 0:
            scale = min(50.0 / speed, 0.1)
            self.velocity_arrow.setLine(0, 0, vx * scale, vy * scale)
        else:
            self.velocity_arrow.setLine(0, 0, 0, 0)

    def add_trail_point(self, scene_pos):
        self.trail_points.append(QPointF(scene_pos.x(), scene_pos.y()))
        if len(self.trail_points) > 500: self.trail_points.pop(0)
        self._rebuild_trail()

    def _rebuild_trail(self):
        if not self.trail_points:
            self.trail_path_item.setPath(QPainterPath())
            return
        path = QPainterPath()
        path.moveTo(self.trail_points[0])
        for p in self.trail_points[1:]: path.lineTo(p)
        self.trail_path_item.setPath(path)

    def clear_trail(self):
        self.trail_points.clear()
        self.trail_path_item.setPath(QPainterPath())

    def set_show_velocity_arrow(self, show): self.velocity_arrow.setVisible(show)
    def set_show_trail(self, show): self.trail_path_item.setVisible(show)


class BallItem(_TrailArrowMixin, QGraphicsEllipseItem):
    def __init__(self, obj, parent=None):
        super().__init__(-obj.radius, -obj.radius, obj.radius * 2, obj.radius * 2, parent)
        self.obj = obj
        self.setBrush(QBrush(QColor(obj.color)))
        self.setPen(QPen(Qt.black, 1))
        self.setZValue(10)
        self._init_trail_arrow()
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setPos(obj.pos[0], obj.pos[1])

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.obj.pos[0], self.obj.pos[1] = self.pos().x(), self.pos().y()
            self.update_velocity_arrow()
            if self.scene():
                self.scene()._sync_springs_to_body(self.obj)
        return super().itemChange(change, value)

    def update_appearance(self):
        self.setRect(-self.obj.radius, -self.obj.radius, self.obj.radius * 2, self.obj.radius * 2)
        self.setBrush(QBrush(QColor(self.obj.color)))
        self.setPos(self.obj.pos[0], self.obj.pos[1])
        self.update_velocity_arrow()


class BlockItem(_TrailArrowMixin, QGraphicsRectItem):
    def __init__(self, obj, parent=None):
        super().__init__(-obj.width / 2, -obj.height / 2, obj.width, obj.height, parent)
        self.obj = obj
        self.setBrush(QBrush(QColor(obj.color)))
        self.setPen(QPen(Qt.black, 1))
        self.setZValue(10)
        self._init_trail_arrow()
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setPos(obj.pos[0], obj.pos[1])

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.obj.pos[0], self.obj.pos[1] = self.pos().x(), self.pos().y()
            self.update_velocity_arrow()
            if self.scene():
                self.scene()._sync_springs_to_body(self.obj)
        return super().itemChange(change, value)

    def update_appearance(self):
        self.setRect(-self.obj.width / 2, -self.obj.height / 2, self.obj.width, self.obj.height)
        self.setBrush(QBrush(QColor(self.obj.color)))
        self.setPos(self.obj.pos[0], self.obj.pos[1])
        self.update_velocity_arrow()


class StaticBlockItem(QGraphicsRectItem):
    def __init__(self, obj, parent=None):
        super().__init__(-obj.width / 2, -obj.height / 2, obj.width, obj.height, parent)
        self.obj = obj
        self.setBrush(QBrush(QColor(obj.color)))
        self.setPen(QPen(Qt.black, 1))
        self.setZValue(12)
        self.setRotation(obj.angle)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setPos(obj.pos[0], obj.pos[1])

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.obj.pos[0], self.obj.pos[1] = self.pos().x(), self.pos().y()
        return super().itemChange(change, value)

    def update_appearance(self):
        self.setRect(-self.obj.width / 2, -self.obj.height / 2, self.obj.width, self.obj.height)
        self.setBrush(QBrush(QColor(self.obj.color)))
        self.setPos(self.obj.pos[0], self.obj.pos[1])
        self.setRotation(self.obj.angle)

class GrooveItem(QGraphicsPathItem):
    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.setBrush(QBrush(QColor(obj.color)))
        self.setPen(QPen(Qt.black, 1))
        self.setZValue(12)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.update_appearance()
        self.setPos(obj.pos[0], obj.pos[1])

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.obj.pos[0], self.obj.pos[1] = self.pos().x(), self.pos().y()
        return super().itemChange(change, value)

    def update_appearance(self):
        self.setBrush(QBrush(QColor(self.obj.color)))
        path = QPainterPath()
        
        r_in = self.obj.radius
        r_out = self.obj.radius + self.obj.thickness
        
        path.moveTo(-r_out, 0)
        path.lineTo(-r_in, 0)
        # 从左到右画内半圆 (下半圆)
        path.arcTo(QRectF(-r_in, -r_in, 2*r_in, 2*r_in), 180, 180)
        
        path.lineTo(r_out, 0)
        path.lineTo(r_out, r_out)
        path.lineTo(-r_out, r_out)
        path.closeSubpath()
        
        self.setPath(path)
        self.setPos(self.obj.pos[0], self.obj.pos[1])



# ─────────────────────────────────────────────────────────
# 端点手柄 (用于 Spring, Rod, Rope)
# ─────────────────────────────────────────────────────────
class EndpointHandle(QGraphicsEllipseItem):
    def __init__(self, owner_item, is_start=True):
        super().__init__(-8, -8, 16, 16)
        self.owner_item = owner_item
        self.is_start = is_start
        self._is_internal_updating = False
        
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 1))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges | QGraphicsItem.ItemIsSelectable)
        self.setZValue(40)
        self.setVisible(False)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and not self._is_internal_updating:
            bound_id = self.owner_item.obj.start_body_id if self.is_start else self.owner_item.obj.end_body_id
            if not bound_id:
                new_pos = self.pos()
                if self.is_start:
                    self.owner_item.obj.start_pos = np.array([new_pos.x(), new_pos.y()])
                else:
                    self.owner_item.obj.end_pos = np.array([new_pos.x(), new_pos.y()])
                self.owner_item.rebuild_path()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        scene = self.scene()
        if not scene: return
        
        my_id = (self.owner_item, self.is_start)
        current_mounting = getattr(scene, 'mounting_endpoint', None)
        
        if current_mounting == my_id:
            scene.cancel_mounting()
        else:
            scene.start_mounting(self.owner_item, self.is_start)
        
        bound_id = self.owner_item.obj.start_body_id if self.is_start else self.owner_item.obj.end_body_id
        if bound_id:
            event.accept()
            return
            
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.is_start: self.owner_item.obj.start_body_id = None
        else: self.owner_item.obj.end_body_id = None
        self.owner_item.rebuild_path()
        event.accept()

    def update_status(self, is_mounting_this):
        bound_id = self.owner_item.obj.start_body_id if self.is_start else self.owner_item.obj.end_body_id
        if is_mounting_this:
            self.setBrush(QBrush(Qt.yellow))
        elif bound_id:
            self.setBrush(QBrush(Qt.red))
        else:
            self.setBrush(QBrush(Qt.white))


class SpringItem(QGraphicsPathItem):
    COILS = 10

    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.setPos(0, 0)
        self.setPen(QPen(QColor(obj.color), 2))
        self.setBrush(QBrush(Qt.NoBrush))
        self.setZValue(30)
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        
        self.start_handle = EndpointHandle(self, is_start=True)
        self.end_handle = EndpointHandle(self, is_start=False)

    def update_handle_states(self):
        scene = self.scene()
        mounting = getattr(scene, 'mounting_endpoint', None)
        self.start_handle.update_status(mounting == (self, True))
        self.end_handle.update_status(mounting == (self, False))

    def rebuild_path(self):
        p1 = QPointF(self.obj.start_pos[0], self.obj.start_pos[1])
        p2 = QPointF(self.obj.end_pos[0], self.obj.end_pos[1])
        
        self.start_handle._is_internal_updating = True
        self.start_handle.setPos(p1)
        self.start_handle._is_internal_updating = False
        
        self.end_handle._is_internal_updating = True
        self.end_handle.setPos(p2)
        self.end_handle._is_internal_updating = False
        
        self.update_handle_states()
        
        dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
        length = math.sqrt(dx*dx + dy*dy) or 1.0
        tx, ty = dx/length, dy/length
        nx, ny = -ty, tx
        
        coils = self.COILS
        amp = min(12.0, length / (coils * 1.5))
        seg_len = length / (coils * 2 + 2)
        
        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p1.x() + tx * seg_len, p1.y() + ty * seg_len)
        for i in range(coils * 2):
            side = 1 if i % 2 == 0 else -1
            along = seg_len * (i + 1.5)
            path.lineTo(p1.x() + tx * along + nx * amp * side,
                        p1.y() + ty * along + ny * amp * side)
        path.lineTo(p2)
        self.setPath(path)
        
        self.update_handle_states()

    def update_handle_states(self):
        scene = self.scene()
        mounting = getattr(scene, 'mounting_endpoint', None) if scene else None
        
        # 决定手柄是否应该可见：被选中，或者正在挂载模式
        is_selected = self.isSelected()
        
        for h in [self.start_handle, self.end_handle]:
            h._is_internal_updating = True
            pos = QPointF(self.obj.start_pos[0], self.obj.start_pos[1]) if h.is_start else QPointF(self.obj.end_pos[0], self.obj.end_pos[1])
            h.setPos(pos)
            
            bound_id = self.obj.start_body_id if h.is_start else self.obj.end_body_id
            is_mounting = (mounting == (self, h.is_start))
            
            # 高亮逻辑
            if is_mounting: h.setBrush(QBrush(QColor(255, 255, 0))) # 黄色
            elif bound_id: h.setBrush(QBrush(QColor(255, 80, 80)))  # 红色
            else: h.setBrush(QBrush(QColor(255, 255, 255)))       # 白色
            
            # 只有选中弹簧或者正在挂载时才显示手柄
            h.setVisible(is_selected or is_mounting or h.isSelected())
            
            # 锁定已绑定的拖拽
            h.setFlag(QGraphicsItem.ItemIsMovable, not bound_id)
            h._is_internal_updating = False

    def update_appearance(self, playing=False):
        if playing:
            self.sync_bound_endpoints(playing=True)
        self.rebuild_path()

    def sync_bound_endpoints(self, playing=False):
        scene = self.scene()
        if not scene: return
        id_map = scene.get_id_map()
        
        if self.obj.start_body_id in id_map:
            body = id_map[self.obj.start_body_id]
            self.obj.start_pos = body.pos + self.obj.start_local_offset
        if self.obj.end_body_id in id_map:
            body = id_map[self.obj.end_body_id]
            self.obj.end_pos = body.pos + self.obj.end_local_offset

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.update_handle_states()
        return super().itemChange(change, value)


class RodItem(QGraphicsPathItem):
    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.setPen(QPen(Qt.black, 1))
        self.setBrush(QBrush(QColor(obj.color)))
        self.setZValue(25)
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        
        self.start_handle = EndpointHandle(self, is_start=True)
        self.end_handle = EndpointHandle(self, is_start=False)
        self.rebuild_path()

    def update_handle_states(self):
        scene = self.scene()
        mounting = getattr(scene, 'mounting_endpoint', None) if scene else None
        is_selected = self.isSelected()
        for h in [self.start_handle, self.end_handle]:
            h.update_status(mounting == (self, h.is_start))
            h.setVisible(is_selected or (mounting == (self, h.is_start)) or h.isSelected())

    def rebuild_path(self):
        p1 = QPointF(self.obj.start_pos[0], self.obj.start_pos[1])
        p2 = QPointF(self.obj.end_pos[0], self.obj.end_pos[1])
        
        self.start_handle._is_internal_updating = True
        self.start_handle.setPos(p1)
        self.start_handle._is_internal_updating = False
        
        self.end_handle._is_internal_updating = True
        self.end_handle.setPos(p2)
        self.end_handle._is_internal_updating = False
        
        dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
        dist = math.sqrt(dx*dx + dy*dy) or 1.0
        
        path = QPainterPath()
        t = self.obj.thickness / 2
        nx, ny = -dy/dist * t, dx/dist * t
        path.moveTo(p1.x() + nx, p1.y() + ny)
        path.lineTo(p2.x() + nx, p2.y() + ny)
        path.lineTo(p2.x() - nx, p2.y() - ny)
        path.lineTo(p1.x() - nx, p1.y() - ny)
        path.closeSubpath()
        self.setPath(path)
        self.update_handle_states()

    def update_appearance(self, playing=False):
        if playing: self.sync_bound_endpoints()
        self.rebuild_path()

    def sync_bound_endpoints(self):
        scene = self.scene()
        if not scene: return
        id_map = scene.get_id_map()
        if self.obj.start_body_id in id_map:
            self.obj.start_pos = id_map[self.obj.start_body_id].pos + self.obj.start_local_offset
        if self.obj.end_body_id in id_map:
            self.obj.end_pos = id_map[self.obj.end_body_id].pos + self.obj.end_local_offset

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.update_handle_states()
        return super().itemChange(change, value)

class RopeItem(QGraphicsPathItem):
    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.setPen(QPen(QColor(obj.color), obj.thickness))
        self.setZValue(28)
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        
        self.start_handle = EndpointHandle(self, is_start=True)
        self.end_handle = EndpointHandle(self, is_start=False)
        self.rebuild_path()

    def update_handle_states(self):
        scene = self.scene()
        mounting = getattr(scene, 'mounting_endpoint', None) if scene else None
        is_selected = self.isSelected()
        for h in [self.start_handle, self.end_handle]:
            h.update_status(mounting == (self, h.is_start))
            h.setVisible(is_selected or (mounting == (self, h.is_start)) or h.isSelected())

    def rebuild_path(self):
        p1 = QPointF(self.obj.start_pos[0], self.obj.start_pos[1])
        p2 = QPointF(self.obj.end_pos[0], self.obj.end_pos[1])
        
        self.start_handle._is_internal_updating = True
        self.start_handle.setPos(p1)
        self.start_handle._is_internal_updating = False
        
        self.end_handle._is_internal_updating = True
        self.end_handle.setPos(p2)
        self.end_handle._is_internal_updating = False
        
        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        self.setPath(path)
        self.update_handle_states()

    def update_appearance(self, playing=False):
        if playing: self.sync_bound_endpoints()
        self.rebuild_path()

    def sync_bound_endpoints(self):
        scene = self.scene()
        if not scene: return
        id_map = scene.get_id_map()
        if self.obj.start_body_id in id_map:
            self.obj.start_pos = id_map[self.obj.start_body_id].pos + self.obj.start_local_offset
        if self.obj.end_body_id in id_map:
            self.obj.end_pos = id_map[self.obj.end_body_id].pos + self.obj.end_local_offset

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.update_handle_states()
        return super().itemChange(change, value)


# ─────────────────────────────────────────────────────────
# PhysicsScene
# ─────────────────────────────────────────────────────────
class PhysicsScene(QGraphicsScene):
    object_selected = pyqtSignal(object)
    request_create_object = pyqtSignal(str, float, float, dict)
    request_apply_force = pyqtSignal(object)
    request_delete_object = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 800, 600)
        self.items_dict = {}
        self.mode = 'select'
        self.show_velocity_arrow = False
        self.show_trail = False
        self._pending_type = None
        self._pending_params = {}
        self.mounting_endpoint = None 
        self.selectionChanged.connect(self._on_selection_changed)

    def get_id_map(self):
        id_map = {}
        for obj, item in self.items_dict.items():
            if hasattr(obj, 'id'): id_map[obj.id] = obj
        return id_map

    def start_mounting(self, spring_item, is_start):
        self.cancel_mounting() 
        self.mounting_endpoint = (spring_item, is_start)
        spring_item.update_handle_states()

    def cancel_mounting(self):
        if self.mounting_endpoint:
            item, _ = self.mounting_endpoint
            self.mounting_endpoint = None
            item.update_handle_states()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel_mounting()
        super().keyPressEvent(event)

    def _on_selection_changed(self):
        selected = self.selectedItems()
        if selected:
            item = selected[0]
            if isinstance(item, EndpointHandle): 
                self.object_selected.emit(item.owner_item.obj)
                item.owner_item.update_handle_states()
            elif hasattr(item, 'obj'): self.object_selected.emit(item.obj)
        else: self.object_selected.emit(None)

    def find_owner_item(self, item):
        current = item
        while current:
            if hasattr(current, 'obj') and current.obj is not None:
                return current, current.obj
            if hasattr(current, 'owner_item'):
                return current.owner_item, current.owner_item.obj
            current = current.parentItem()
        return None, None

    def contextMenuEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())
        if not item:
            super().contextMenuEvent(event)
            return
            
        owner_item, obj = self.find_owner_item(item)

        if not obj:
            super().contextMenuEvent(event)
            return

        # 选中主图元
        self.clearSelection()
        if owner_item:
            owner_item.setSelected(True)
            
        self.object_selected.emit(obj)

        menu = QMenu()
        apply_action = menu.addAction("施加力")
        delete_action = menu.addAction("删除对象")

        if isinstance(obj, (Ball, Block)):
            apply_action.setEnabled(True)
        else:
            apply_action.setEnabled(False)

        action = menu.exec_(event.screenPos())
        if action == apply_action:
            self.request_apply_force.emit(obj)
        elif action == delete_action:
            self.request_delete_object.emit(obj)
        
        event.accept()

    def mousePressEvent(self, event):
        # 1. 检查挂载交互
        if self.mounting_endpoint:
            sp = event.scenePos()
            # 获取点击位置的所有图元
            items = self.items(sp)
            target_obj = None
            hit_handle = False
            for item in items:
                if isinstance(item, (BallItem, BlockItem, StaticBlockItem, GrooveItem)):
                    target_obj = item.obj
                    break
                if isinstance(item, EndpointHandle):
                    hit_handle = True
            
            if target_obj:
                owner_item, is_start = self.mounting_endpoint
                if is_start:
                    owner_item.obj.start_body_id = target_obj.id
                    owner_item.obj.start_local_offset = np.array([0.0, 0.0])
                    owner_item.obj.start_pos = target_obj.pos.copy()
                else:
                    owner_item.obj.end_body_id = target_obj.id
                    owner_item.obj.end_local_offset = np.array([0.0, 0.0])
                    owner_item.obj.end_pos = target_obj.pos.copy()
                
                self.cancel_mounting()
                owner_item.rebuild_path()
                event.accept()
                return
            elif not hit_handle:
                # 只有在没点到手柄时，点击空白才取消（防止点击手柄本身启动挂载又瞬间被取消）
                self.cancel_mounting()

        # 2. 正常逻辑
        if event.button() == Qt.LeftButton:
            sp = event.scenePos()
            if self.mode == 'pending_create' and self._pending_type:
                object_type = self._pending_type
                params = dict(self._pending_params)
                self._pending_type = None
                self._pending_params = None
                self.mode = 'select'
                self.request_create_object.emit(object_type, sp.x(), sp.y(), params)
                event.accept()
                return
        super().mousePressEvent(event)

    def set_mode(self, mode):
        self.mode = mode
        if mode == 'select': self._pending_type = None

    def set_pending_create(self, object_type, params):
        self._pending_type = object_type
        self._pending_params = params
        self.mode = 'pending_create'

    def add_physics_object(self, obj):
        if obj in self.items_dict:
            print(f"Warning: Object {getattr(obj, 'name', obj)} already in scene!")
            return
        if isinstance(obj, Ball): item = BallItem(obj)
        elif isinstance(obj, Block): item = BlockItem(obj)
        elif isinstance(obj, Spring):
            item = SpringItem(obj)
            self.addItem(item)
            self.addItem(item.start_handle)
            self.addItem(item.end_handle)
            self.items_dict[obj] = item
            item.rebuild_path()
            return
        elif isinstance(obj, StaticBlock):
            item = StaticBlockItem(obj)
            self.addItem(item)
            self.items_dict[obj] = item
            return
        elif isinstance(obj, Groove):
            item = GrooveItem(obj)
            self.addItem(item)
            self.items_dict[obj] = item
            return
        elif getattr(obj, "type", "") == "rod":
            item = RodItem(obj)
            self.addItem(item)
            self.addItem(item.start_handle)
            self.addItem(item.end_handle)
            self.items_dict[obj] = item
            item.rebuild_path()
            return
        elif getattr(obj, "type", "") == "rope":
            item = RopeItem(obj)
            self.addItem(item)
            self.addItem(item.start_handle)
            self.addItem(item.end_handle)
            self.items_dict[obj] = item
            item.rebuild_path()
            return
        else: return
        item.set_show_velocity_arrow(self.show_velocity_arrow)
        item.set_show_trail(self.show_trail)
        self.addItem(item)
        self.addItem(item.trail_path_item)
        self.items_dict[obj] = item

    def remove_physics_object(self, obj):
        if obj not in self.items_dict: 
            return
        item = self.items_dict.pop(obj)
        if isinstance(item, (SpringItem, RodItem, RopeItem)):
            if item.start_handle.scene() == self:
                self.removeItem(item.start_handle)
            if item.end_handle.scene() == self:
                self.removeItem(item.end_handle)
        if hasattr(item, 'trail_path_item') and item.trail_path_item.scene() == self: 
            self.removeItem(item.trail_path_item)
        if item.scene() == self:
            self.removeItem(item)

    def update_items(self, record_trail=False, playing=False):
        for obj, item in self.items_dict.items():
            if isinstance(item, (SpringItem, RodItem, RopeItem)):
                item.update_appearance(playing=playing)
                continue
            elif isinstance(item, StaticBlockItem):
                # StaticBlock doesn't move or have trails
                item.setPos(obj.pos[0], obj.pos[1])
                item.setRotation(obj.angle)
                continue
            elif isinstance(item, GrooveItem):
                item.setPos(obj.pos[0], obj.pos[1])
                continue
            item.setPos(obj.pos[0], obj.pos[1])
            item.update_velocity_arrow()
            if record_trail: item.add_trail_point(item.pos())

    def clear_items(self):
        self.clear()
        self.items_dict.clear()
        self.addRect(self.sceneRect(), QPen(Qt.black))

    def set_show_velocity_arrow(self, show):
        self.show_velocity_arrow = show
        for obj, item in self.items_dict.items():
            if not isinstance(obj, Spring) and hasattr(item, 'set_show_velocity_arrow'):
                item.set_show_velocity_arrow(show)

    def set_show_trail(self, show):
        self.show_trail = show
        for obj, item in self.items_dict.items():
            if not isinstance(obj, Spring) and hasattr(item, 'set_show_trail'):
                item.set_show_trail(show)

    def clear_all_trails(self):
        from core.models import Spring as SpringModel
        for obj, item in self.items_dict.items():
            if not isinstance(obj, SpringModel) and hasattr(item, 'clear_trail'):
                item.clear_trail()

    def _sync_springs_to_body(self, body_obj):
        for obj, item in self.items_dict.items():
            if isinstance(item, SpringItem):
                item.sync_bound_endpoints(playing=False)
                item.rebuild_path()
