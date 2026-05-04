import math
import numpy as np
from core.models import Ball, Block, Spring
from core.units import (px_to_m, px_s_to_m_s, px_s2_to_m_s2, 
                        kinetic_energy_joule, potential_energy_joule, spring_energy_joule)

class DataRecorder:
    def __init__(self, max_records=5000):
        self.max_records = max_records
        self.records = {}  # {object_id: [dict, ...]}
        self.prev_velocities = {} # {object_id: np.array([vx, vy])}
        self.prev_smoothed_acc = {} # {object_id: np.array([ax, ay])}
        self.alpha = 0.3 # 指数平滑系数

    def clear_all(self):
        self.records.clear()
        self.prev_velocities.clear()
        self.prev_smoothed_acc.clear()

    def clear_object(self, obj_id):
        if obj_id in self.records:
            self.records[obj_id].clear()
        if obj_id in self.prev_velocities:
            del self.prev_velocities[obj_id]
        if obj_id in self.prev_smoothed_acc:
            del self.prev_smoothed_acc[obj_id]

    def remove_object(self, obj_id):
        if obj_id in self.records:
            del self.records[obj_id]
        if obj_id in self.prev_velocities:
            del self.prev_velocities[obj_id]
        if obj_id in self.prev_smoothed_acc:
            del self.prev_smoothed_acc[obj_id]

    def record(self, current_time, objects, engine, dt=None):
        scene_height = engine.bounds[3]

        for obj in objects:
            if obj.id not in self.records:
                self.records[obj.id] = []

            data = {"time": current_time}

            if isinstance(obj, (Ball, Block)):
                # 记录位置和速度
                data["x"] = px_to_m(obj.pos[0])
                data["y"] = px_to_m(obj.pos[1])
                data["vx"] = px_s_to_m_s(obj.vel[0])
                data["vy"] = px_s_to_m_s(obj.vel[1])
                speed_px = math.hypot(obj.vel[0], obj.vel[1])
                data["speed"] = px_s_to_m_s(speed_px)
                
                # 计算有效加速度 (基于速度变化)
                eff_acc_px = obj.acc.copy()
                if dt is not None and dt > 0 and obj.id in self.prev_velocities:
                    eff_acc_px = (obj.vel - self.prev_velocities[obj.id]) / dt
                
                # EMA 平滑加速度
                if obj.id in self.prev_smoothed_acc:
                    smoothed_acc_px = self.alpha * eff_acc_px + (1 - self.alpha) * self.prev_smoothed_acc[obj.id]
                else:
                    smoothed_acc_px = eff_acc_px
                
                self.prev_smoothed_acc[obj.id] = smoothed_acc_px.copy()
                
                data["ax"] = px_s2_to_m_s2(smoothed_acc_px[0])
                data["ay"] = px_s2_to_m_s2(smoothed_acc_px[1])
                
                # 能量计算
                data["mass"] = obj.mass
                data["kinetic_energy"] = kinetic_energy_joule(obj.mass, speed_px)
                h_px = scene_height - obj.pos[1]
                data["potential_energy"] = potential_energy_joule(obj.mass, engine.gravity[1], h_px)
                
                # 更新速度缓存
                self.prev_velocities[obj.id] = obj.vel.copy()

            elif isinstance(obj, Spring):
                dx = obj.end_pos[0] - obj.start_pos[0]
                dy = obj.end_pos[1] - obj.start_pos[1]
                curr_len_px = math.hypot(dx, dy)
                ext_px = curr_len_px - obj.rest_length
                
                data["current_length"] = px_to_m(curr_len_px)
                data["rest_length"] = px_to_m(obj.rest_length)
                data["extension"] = px_to_m(ext_px)
                
                # 内部能量计算并换算
                internal_energy = 0.5 * obj.stiffness * (ext_px ** 2)
                data["spring_energy"] = spring_energy_joule(internal_energy)

            self.records[obj.id].append(data)
            if len(self.records[obj.id]) > self.max_records:
                self.records[obj.id].pop(0)

    def get_data(self, obj_id):
        return self.records.get(obj_id, [])
