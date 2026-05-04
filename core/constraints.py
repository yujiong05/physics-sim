import numpy as np
from core.models import Rope, Rod

def apply_rod_constraints(objects, id_map, iterations=4):
    """
    遍历 Rod 对象并应用刚性长度约束（即不可伸长也不可压缩）。
    """
    for _ in range(iterations):
        for obj in objects:
            if getattr(obj, "type", "") != "rod":
                continue
                
            p1 = obj.start_pos
            body1 = id_map.get(obj.start_body_id)
            if body1: p1 = body1.pos + obj.start_local_offset
                
            p2 = obj.end_pos
            body2 = id_map.get(obj.end_body_id)
            if body2: p2 = body2.pos + obj.end_local_offset
                
            delta = p2 - p1
            dist = np.linalg.norm(delta)
            if dist < 1e-6: continue
            normal = delta / dist
            
            inv_m1 = 0.0 if (not body1 or getattr(body1, "static", False)) else 1.0 / body1.mass
            inv_m2 = 0.0 if (not body2 or getattr(body2, "static", False)) else 1.0 / body2.mass
            sum_inv_m = inv_m1 + inv_m2
            
            # 1. 位置修正
            diff = dist - obj.length
            if abs(diff) > 1e-4 and sum_inv_m > 0:
                correction = (diff / sum_inv_m) * normal
                if inv_m1 > 0: body1.pos += correction * inv_m1
                if inv_m2 > 0: body2.pos -= correction * inv_m2
                # 更新缓存位置用于绘制
                if body1: obj.start_pos = body1.pos + obj.start_local_offset
                if body2: obj.end_pos = body2.pos + obj.end_local_offset

            # 2. 速度投影 (仅最后一次迭代)
            if _ == iterations - 1:
                v1 = body1.vel if (body1 and not getattr(body1, "static", False)) else np.zeros(2)
                v2 = body2.vel if (body2 and not getattr(body2, "static", False)) else np.zeros(2)
                v_rel = v2 - v1
                v_rel_normal = np.dot(v_rel, normal)
                
                if abs(v_rel_normal) > 1e-6 and sum_inv_m > 0:
                    j = v_rel_normal / sum_inv_m
                    if inv_m1 > 0: body1.vel += j * inv_m1 * normal
                    if inv_m2 > 0: body2.vel -= j * inv_m2 * normal
                
                # 能量损耗 (如果设置了 damping)
                d_val = getattr(obj, "damping", 0.0)
                if d_val > 0:
                    dt = 0.016
                    if body1 and not getattr(body1, "static", False): body1.vel *= (1.0 - d_val * dt)
                    if body2 and not getattr(body2, "static", False): body2.vel *= (1.0 - d_val * dt)



def apply_rope_constraints(objects, id_map, iterations=4):
    """
    遍历 Rope 对象并应用长度约束。
    通过位置修正和速度投影保持绳子长度不超过限制。
    """
    for _ in range(iterations):
        for obj in objects:
            if not isinstance(obj, Rope):
                continue
                
            # 1. 确定两端的世界坐标和关联物体
            p1 = obj.start_pos
            body1 = id_map.get(obj.start_body_id)
            if body1:
                p1 = body1.pos + obj.start_local_offset
                obj.start_pos = np.copy(p1)
                
            p2 = obj.end_pos
            body2 = id_map.get(obj.end_body_id)
            if body2:
                p2 = body2.pos + obj.end_local_offset
                obj.end_pos = np.copy(p2)
                
            # 2. 计算当前长度和偏差
            delta = p2 - p1
            dist = np.linalg.norm(delta)
            if dist <= obj.length or dist < 1e-6:
                continue
                
            # 3. 位置修正 (Position Correction)
            diff = dist - obj.length
            normal = delta / dist
            
            inv_m1 = 0.0 if (not body1 or getattr(body1, "static", False)) else 1.0 / body1.mass
            inv_m2 = 0.0 if (not body2 or getattr(body2, "static", False)) else 1.0 / body2.mass
            sum_inv_m = inv_m1 + inv_m2
            
            if sum_inv_m > 0:
                correction = (diff / sum_inv_m) * normal
                if inv_m1 > 0:
                    body1.pos += correction * inv_m1
                if inv_m2 > 0:
                    body2.pos -= correction * inv_m2

            # 4. 速度投影 (Velocity Constraint) - 只在最后一次迭代执行或单次迭代执行
            if _ == iterations - 1:
                v1 = body1.vel if (body1 and not getattr(body1, "static", False)) else np.zeros(2)
                v2 = body2.vel if (body2 and not getattr(body2, "static", False)) else np.zeros(2)
                
                v_rel = v2 - v1
                v_rel_normal = np.dot(v_rel, normal)
                
                if v_rel_normal > 0: # 正在伸长
                    # 消除伸长方向的速度，并应用阻尼
                    impulse = v_rel_normal * (1.0 + obj.damping)
                    if sum_inv_m > 0:
                        j = impulse / sum_inv_m
                        if inv_m1 > 0:
                            body1.vel += j * inv_m1 * normal
                        if inv_m2 > 0:
                            body2.vel -= j * inv_m2 * normal
