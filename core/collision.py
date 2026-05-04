"""
core/collision.py
碰撞检测与响应模块：处理 Ball-Ball、Block-Block、Ball-Block 碰撞。
所有碰撞均为轴对齐 AABB，不考虑旋转和角动量。
"""
import numpy as np
from core.models import Ball, Block, StaticBlock, Groove


def _apply_impulse(a, b, normal, penetration):
    """
    在 normal 方向上对 a, b 施加冲量，并做位置修正。
    normal: 单位法向量（从 b 指向 a）
    penetration: 穿透深度（正值）
    """
    if getattr(a, "static", False) and getattr(b, "static", False):
        return

    restitution = min(a.restitution, b.restitution)

    vel_a = getattr(a, "vel", np.zeros(2))
    vel_b = getattr(b, "vel", np.zeros(2))
    rel_vel = vel_a - vel_b
    vel_along_normal = np.dot(rel_vel, normal)

    # 如果两物体正在分离，不需要处理
    if vel_along_normal > 0:
        return

    if abs(vel_along_normal) < 5:
        restitution = 0.0

    inv_mass_a = 0.0 if getattr(a, "static", False) else (1.0 / a.mass if a.mass > 0 else 0.0)
    inv_mass_b = 0.0 if getattr(b, "static", False) else (1.0 / b.mass if b.mass > 0 else 0.0)
    inv_mass_sum = inv_mass_a + inv_mass_b

    if inv_mass_sum == 0:
        return

    # 冲量大小
    j = -(1 + restitution) * vel_along_normal / inv_mass_sum

    impulse = j * normal
    friction = min(getattr(a, "friction", 0.2), getattr(b, "friction", 0.2))

    if not getattr(a, "static", False):
        tangent = a.vel - np.dot(a.vel, normal) * normal
        a.vel = a.vel - friction * tangent * 0.02
        a.vel = a.vel + impulse * inv_mass_a
    if not getattr(b, "static", False):
        tangent = b.vel - np.dot(b.vel, normal) * normal
        b.vel = b.vel - friction * tangent * 0.02
        b.vel = b.vel - impulse * inv_mass_b

    # 位置修正：按质量倒数分配穿透深度，留 20% 缓冲防抖动
    slop = 0.5        # 允许的最小穿透量（像素），低于此不修正
    percent = 0.8     # 修正比例
    correction_mag = max(penetration - slop, 0.0) * percent / inv_mass_sum
    correction = correction_mag * normal
    if not getattr(a, "static", False):
        a.pos = a.pos + correction * inv_mass_a
    if not getattr(b, "static", False):
        b.pos = b.pos - correction * inv_mass_b


# ──────────────────────────────────────────────
# Ball - Ball
# ──────────────────────────────────────────────
def collide_ball_ball(a: Ball, b: Ball):
    delta = a.pos - b.pos
    dist = np.linalg.norm(delta)
    min_dist = a.radius + b.radius

    if dist >= min_dist:
        return

    # 避免两圆完全重叠时除零
    if dist < 1e-6:
        normal = np.array([1.0, 0.0])
        penetration = min_dist
    else:
        normal = delta / dist
        penetration = min_dist - dist

    _apply_impulse(a, b, normal, penetration)


# ──────────────────────────────────────────────
# Block - Block  (AABB)
# ──────────────────────────────────────────────
def collide_block_block(a: Block, b: Block):
    ax0 = a.pos[0] - a.width  / 2; ax1 = a.pos[0] + a.width  / 2
    ay0 = a.pos[1] - a.height / 2; ay1 = a.pos[1] + a.height / 2
    bx0 = b.pos[0] - b.width  / 2; bx1 = b.pos[0] + b.width  / 2
    by0 = b.pos[1] - b.height / 2; by1 = b.pos[1] + b.height / 2

    overlap_x = min(ax1, bx1) - max(ax0, bx0)
    overlap_y = min(ay1, by1) - max(ay0, by0)

    if overlap_x <= 0 or overlap_y <= 0:
        return

    # 选较小轴作为分离轴
    if overlap_x < overlap_y:
        # X 轴分离
        normal = np.array([1.0, 0.0]) if a.pos[0] > b.pos[0] else np.array([-1.0, 0.0])
        penetration = overlap_x
    else:
        # Y 轴分离
        normal = np.array([0.0, 1.0]) if a.pos[1] > b.pos[1] else np.array([0.0, -1.0])
        penetration = overlap_y

    _apply_impulse(a, b, normal, penetration)


# ──────────────────────────────────────────────
# Ball - Block  (Circle vs AABB)
# ──────────────────────────────────────────────
def collide_ball_block(ball: Ball, block: Block):
    bx0 = block.pos[0] - block.width  / 2
    bx1 = block.pos[0] + block.width  / 2
    by0 = block.pos[1] - block.height / 2
    by1 = block.pos[1] + block.height / 2

    # 圆心最近点（夹在矩形范围内）
    closest_x = np.clip(ball.pos[0], bx0, bx1)
    closest_y = np.clip(ball.pos[1], by0, by1)

    inside = (ball.pos[0] == closest_x and ball.pos[1] == closest_y)

    delta = ball.pos - np.array([closest_x, closest_y])
    dist = np.linalg.norm(delta)

    if not inside and dist >= ball.radius:
        return

    if inside:
        # 圆心在矩形内：找最近边推出
        dx0 = ball.pos[0] - bx0; dx1 = bx1 - ball.pos[0]
        dy0 = ball.pos[1] - by0; dy1 = by1 - ball.pos[1]
        min_d = min(dx0, dx1, dy0, dy1)
        if min_d == dx0:
            normal = np.array([-1.0, 0.0]); penetration = ball.radius + dx0
        elif min_d == dx1:
            normal = np.array([1.0, 0.0]);  penetration = ball.radius + dx1
        elif min_d == dy0:
            normal = np.array([0.0, -1.0]); penetration = ball.radius + dy0
        else:
            normal = np.array([0.0, 1.0]);  penetration = ball.radius + dy1
    else:
        if dist < 1e-6:
            normal = np.array([0.0, -1.0])
            penetration = ball.radius
        else:
            normal = delta / dist
            penetration = ball.radius - dist

# normal 方向从 block 指向 ball，对应 _apply_impulse 的 a=ball, b=block
    _apply_impulse(ball, block, normal, penetration)

def collide_ball_static_block(ball: Ball, block: StaticBlock):
    import math
    angle_rad = math.radians(block.angle)
    cos_a = math.cos(-angle_rad)
    sin_a = math.sin(-angle_rad)
    
    dx = ball.pos[0] - block.pos[0]
    dy = ball.pos[1] - block.pos[1]
    lx = dx * cos_a - dy * sin_a
    ly = dx * sin_a + dy * cos_a
    
    bx0 = -block.width / 2; bx1 = block.width / 2
    by0 = -block.height / 2; by1 = block.height / 2
    
    closest_x = np.clip(lx, bx0, bx1)
    closest_y = np.clip(ly, by0, by1)
    inside = (lx == closest_x and ly == closest_y)
    
    delta_x = lx - closest_x
    delta_y = ly - closest_y
    dist = math.hypot(delta_x, delta_y)
    
    if not inside and dist >= ball.radius:
        return
        
    if inside:
        d0 = lx - bx0; d1 = bx1 - lx
        d2 = ly - by0; d3 = by1 - ly
        min_d = min(d0, d1, d2, d3)
        if min_d == d0: normal_local = np.array([-1.0, 0.0]); penetration = ball.radius + d0
        elif min_d == d1: normal_local = np.array([1.0, 0.0]); penetration = ball.radius + d1
        elif min_d == d2: normal_local = np.array([0.0, -1.0]); penetration = ball.radius + d2
        else: normal_local = np.array([0.0, 1.0]); penetration = ball.radius + d3
    else:
        if dist < 1e-6:
            normal_local = np.array([0.0, -1.0])
            penetration = ball.radius
        else:
            normal_local = np.array([delta_x / dist, delta_y / dist])
            penetration = ball.radius - dist
            
    cos_pos = math.cos(angle_rad)
    sin_pos = math.sin(angle_rad)
    nx = normal_local[0] * cos_pos - normal_local[1] * sin_pos
    ny = normal_local[0] * sin_pos + normal_local[1] * cos_pos
    normal = np.array([nx, ny])
    
    _apply_impulse(ball, block, normal, penetration)

def collide_block_static_block(block_a: Block, block_b: StaticBlock):
    if getattr(block_b, "angle", 0) != 0:
        import math
        angle_rad = math.radians(block_b.angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        hw_a = block_a.width / 2
        hh_a = block_a.height / 2
        axes = [
            np.array([1.0, 0.0]),
            np.array([0.0, 1.0]),
            np.array([cos_a, sin_a]),
            np.array([-sin_a, cos_a])
        ]
        
        cx_a, cy_a = block_a.pos
        pts_a = [
            np.array([cx_a - hw_a, cy_a - hh_a]),
            np.array([cx_a + hw_a, cy_a - hh_a]),
            np.array([cx_a + hw_a, cy_a + hh_a]),
            np.array([cx_a - hw_a, cy_a + hh_a])
        ]
        
        cx_b, cy_b = block_b.pos
        hw_b = block_b.width / 2
        hh_b = block_b.height / 2
        local_pts = [
            np.array([-hw_b, -hh_b]),
            np.array([hw_b, -hh_b]),
            np.array([hw_b, hh_b]),
            np.array([-hw_b, hh_b])
        ]
        pts_b = []
        for lx, ly in local_pts:
            px = cx_b + lx * cos_a - ly * sin_a
            py = cy_b + lx * sin_a + ly * cos_a
            pts_b.append(np.array([px, py]))
            
        min_overlap = float('inf')
        best_axis = None
        
        for axis in axes:
            min_a = min(np.dot(p, axis) for p in pts_a)
            max_a = max(np.dot(p, axis) for p in pts_a)
            min_b = min(np.dot(p, axis) for p in pts_b)
            max_b = max(np.dot(p, axis) for p in pts_b)
                
            overlap = min(max_a, max_b) - max(min_a, min_b)
            if overlap <= 0:
                return
                
            if overlap < min_overlap:
                min_overlap = overlap
                best_axis = axis
                
        center_delta = block_a.pos - block_b.pos
        if np.dot(center_delta, best_axis) < 0:
            best_axis = -best_axis
            
        _apply_impulse(block_a, block_b, best_axis, min_overlap)
    else:
        bx0 = block_b.pos[0] - block_b.width/2; bx1 = block_b.pos[0] + block_b.width/2
        by0 = block_b.pos[1] - block_b.height/2; by1 = block_b.pos[1] + block_b.height/2
        
        ax0 = block_a.pos[0] - block_a.width/2; ax1 = block_a.pos[0] + block_a.width/2
        ay0 = block_a.pos[1] - block_a.height/2; ay1 = block_a.pos[1] + block_a.height/2
        
        overlap_x = min(ax1, bx1) - max(ax0, bx0)
        overlap_y = min(ay1, by1) - max(ay0, by0)
        
        if overlap_x <= 0 or overlap_y <= 0:
            return
            
        if overlap_x < overlap_y:
            normal = np.array([1.0, 0.0]) if block_a.pos[0] > block_b.pos[0] else np.array([-1.0, 0.0])
            penetration = overlap_x
        else:
            normal = np.array([0.0, 1.0]) if block_a.pos[1] > block_b.pos[1] else np.array([0.0, -1.0])
            penetration = overlap_y
            
        _apply_impulse(block_a, block_b, normal, penetration)

def collide_ball_groove(ball: Ball, groove: Groove):
    import math
    dx = ball.pos[0] - groove.pos[0]
    dy = ball.pos[1] - groove.pos[1]
    
    # |dx| <= radius 范围内处理半圆约束
    if dy < 0 or abs(dx) > groove.radius:
        return
        
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
        
    max_dist = groove.radius - ball.radius
    if dist > max_dist:
        penetration = dist - max_dist
        # normal 应该从 Groove 指向 Ball (推回圆心的法线)
        # 槽壁碰撞，法向是从圆弧向圆心，即 -(ball.pos - groove.pos)
        normal = np.array([-dx / dist, -dy / dist])
        _apply_impulse(ball, groove, normal, penetration)

def collide_block_groove(block: Block, groove: Groove):
    import math
    hw = block.width / 2
    hh = block.height / 2
    cx, cy = block.pos
    
    pts = [
        np.array([cx - hw, cy - hh]),
        np.array([cx + hw, cy - hh]),
        np.array([cx + hw, cy + hh]),
        np.array([cx - hw, cy + hh]),
        np.array([cx, cy - hh]),
        np.array([cx, cy + hh]),
        np.array([cx - hw, cy]),
        np.array([cx + hw, cy]),
        np.array([cx, cy])
    ]
    
    max_penetration = -1
    best_normal = None
    
    for p in pts:
        dx = p[0] - groove.pos[0]
        dy = p[1] - groove.pos[1]
        
        # 内半圆检测 (只在 y >= 0 或 |dx| <= radius 处理，这里选 dy >= 0)
        if dy >= 0:
            dist = math.hypot(dx, dy)
            if dist > groove.radius:
                penetration = dist - groove.radius
                if penetration > max_penetration:
                    max_penetration = penetration
                    # normal 应该从 Groove 指向 Block (由于向内推，应为向圆心的方向)
                    best_normal = np.array([-dx / dist, -dy / dist])
                    
    if max_penetration > 0 and best_normal is not None:
        _apply_impulse(block, groove, best_normal, max_penetration)

# ──────────────────────────────────────────────
# 入口：对所有对象对进行碰撞检测
# ──────────────────────────────────────────────
def detect_and_resolve(objects):
    """遍历所有物体对，执行碰撞检测与响应。"""
    n = len(objects)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = objects[i], objects[j]
            
            if getattr(a, "static", False) and getattr(b, "static", False):
                continue
                
            if isinstance(a, Ball) and isinstance(b, Ball):
                collide_ball_ball(a, b)
            elif isinstance(a, Block) and isinstance(b, Block):
                collide_block_block(a, b)
            elif isinstance(a, Ball) and isinstance(b, Block):
                collide_ball_block(a, b)
            elif isinstance(a, Block) and isinstance(b, Ball):
                collide_ball_block(b, a)
            elif isinstance(a, Ball) and isinstance(b, StaticBlock):
                collide_ball_static_block(a, b)
            elif isinstance(a, StaticBlock) and isinstance(b, Ball):
                collide_ball_static_block(b, a)
            elif isinstance(a, Block) and isinstance(b, StaticBlock):
                collide_block_static_block(a, b)
            elif isinstance(a, StaticBlock) and isinstance(b, Block):
                collide_block_static_block(b, a)
            elif isinstance(a, Ball) and isinstance(b, Groove):
                collide_ball_groove(a, b)
            elif isinstance(a, Groove) and isinstance(b, Ball):
                collide_ball_groove(b, a)
            elif isinstance(a, Block) and isinstance(b, Groove):
                collide_block_groove(a, b)
            elif isinstance(a, Groove) and isinstance(b, Block):
                collide_block_groove(b, a)
