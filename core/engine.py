import numpy as np
from core.models import Ball, Spring
from core.collision import detect_and_resolve
from core.force import AppliedForce

class PhysicsEngine:
    def __init__(self):
        self.objects = []
        self.applied_forces = []
        self.gravity = np.array([0.0, 980.0], dtype=np.float64) 
        self.time = 0.0
        self.bounds = (0, 0, 800, 600)
        
    def add_force(self, target_id, magnitude, angle_deg, duration):
        if duration > 0:
            self.applied_forces.append(AppliedForce(target_id, magnitude, angle_deg, duration))
            
    def clear_forces(self):
        self.applied_forces.clear()
        
    def remove_forces_for_object(self, object_id):
        self.applied_forces = [f for f in self.applied_forces if f.target_id != object_id]
        
    def add_object(self, obj):
        self.objects.append(obj)
        
    def remove_object(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)
        
    def clear(self):
        self.objects.clear()
        self.applied_forces.clear()
        self.time = 0.0
        
    def step(self, dt):
        """执行单步物理计算"""
        self.time += dt
        
        # 1. 建立 ID 映射
        id_map = {obj.id: obj for obj in self.objects}
        
        # 2. 初始化刚体加速度为重力
        for obj in self.objects:
            if not isinstance(obj, Spring) and not getattr(obj, "static", False):
                obj.acc = np.copy(self.gravity)
        
        # 3. 处理弹簧力 (更新端点坐标并施加力)
        for obj in self.objects:
            if isinstance(obj, Spring):
                self._apply_spring_physics(obj, id_map)
                
        # 处理临时外力
        active_forces = []
        for f in self.applied_forces:
            target = id_map.get(f.target_id)
            if target and not getattr(target, "static", False) and not isinstance(target, Spring):
                target.acc += f.force_vector / target.mass
                f.elapsed += dt
                if f.elapsed < f.duration:
                    active_forces.append(f)
        self.applied_forces = active_forces
        
        # 4. 积分更新速度和位置
        for obj in self.objects:
            if isinstance(obj, Spring) or getattr(obj, "static", False):
                continue
            obj.vel += obj.acc * dt
            obj.pos += obj.vel * dt
            
            # 5. 边界碰撞检测
            self._handle_boundary_collision(obj)

        # 6. 物体间碰撞检测与响应
        rigid_bodies = [o for o in self.objects if not isinstance(o, Spring)]
        detect_and_resolve(rigid_bodies)

    def _apply_spring_physics(self, spring, id_map):
        # 根据绑定更新端点坐标
        p1 = spring.start_pos
        if spring.start_body_id in id_map:
            body1 = id_map[spring.start_body_id]
            p1 = body1.pos + spring.start_local_offset
            spring.start_pos = np.copy(p1)
            
        p2 = spring.end_pos
        if spring.end_body_id in id_map:
            body2 = id_map[spring.end_body_id]
            p2 = body2.pos + spring.end_local_offset
            spring.end_pos = np.copy(p2)
            
        # 计算力向量
        delta = p2 - p1
        dist = np.linalg.norm(delta)
        if dist < 0.1: return # 避免除以零或太近产生的数值抖动
        
        unit_dir = delta / dist
        extension = dist - spring.rest_length
        
        # 1. 弹性力 (Hooke's Law)
        f_spring = spring.stiffness * extension
        
        # 2. 阻尼力
        v1 = np.array([0.0, 0.0])
        if spring.start_body_id in id_map:
            v1 = id_map[spring.start_body_id].vel
        v2 = np.array([0.0, 0.0])
        if spring.end_body_id in id_map:
            v2 = id_map[spring.end_body_id].vel
            
        rel_vel = v2 - v1
        f_damping = spring.damping * np.dot(rel_vel, unit_dir)
        
        total_f_mag = f_spring + f_damping
        force_vec = total_f_mag * unit_dir
        
        # 施加加速度 (a = F/m)
        if spring.start_body_id in id_map:
            body1 = id_map[spring.start_body_id]
            body1.acc += force_vec / body1.mass
        if spring.end_body_id in id_map:
            body2 = id_map[spring.end_body_id]
            body2.acc -= force_vec / body2.mass

    def _handle_boundary_collision(self, obj):
        if isinstance(obj, Ball):
            if obj.pos[1] + obj.radius > self.bounds[3]:
                obj.pos[1] = self.bounds[3] - obj.radius
                obj.vel[1] = -obj.vel[1] * obj.restitution
            if obj.pos[0] - obj.radius < self.bounds[0]:
                obj.pos[0] = self.bounds[0] + obj.radius
                obj.vel[0] = -obj.vel[0] * obj.restitution
            if obj.pos[0] + obj.radius > self.bounds[2]:
                obj.pos[0] = self.bounds[2] - obj.radius
                obj.vel[0] = -obj.vel[0] * obj.restitution
        else:
            from core.models import Block
            if isinstance(obj, Block):
                half_w = obj.width / 2.0
                half_h = obj.height / 2.0
                if obj.pos[1] + half_h > self.bounds[3]:
                    obj.pos[1] = self.bounds[3] - half_h
                    obj.vel[1] = -obj.vel[1] * obj.restitution
                if obj.pos[1] - half_h < self.bounds[1]:
                    obj.pos[1] = self.bounds[1] + half_h
                    obj.vel[1] = -obj.vel[1] * obj.restitution
                if obj.pos[0] - half_w < self.bounds[0]:
                    obj.pos[0] = self.bounds[0] + half_w
                    obj.vel[0] = -obj.vel[0] * obj.restitution
                if obj.pos[0] + half_w > self.bounds[2]:
                    obj.pos[0] = self.bounds[2] - half_w
                    obj.vel[0] = -obj.vel[0] * obj.restitution
            
            from core.models import Groove
            if isinstance(obj, Groove):
                half_w = obj.radius + obj.thickness
                # 底部边缘是圆心 y + 半径 + 厚度
                h = obj.radius + obj.thickness
                if obj.pos[1] + h > self.bounds[3]:
                    obj.pos[1] = self.bounds[3] - h
                    obj.vel[1] = -obj.vel[1] * obj.restitution
                if obj.pos[1] - h < self.bounds[1]:
                    obj.pos[1] = self.bounds[1] + h
                    obj.vel[1] = -obj.vel[1] * obj.restitution
                if obj.pos[0] - half_w < self.bounds[0]:
                    obj.pos[0] = self.bounds[0] + half_w
                    obj.vel[0] = -obj.vel[0] * obj.restitution
                if obj.pos[0] + half_w > self.bounds[2]:
                    obj.pos[0] = self.bounds[2] - half_w
                    obj.vel[0] = -obj.vel[0] * obj.restitution
