"""
core/collision.py
碰撞检测与响应模块：处理 Ball-Ball、Block-Block、Ball-Block 碰撞。
所有碰撞均为轴对齐 AABB，不考虑旋转和角动量。
"""
import numpy as np
from core.models import Ball, Block


def _apply_impulse(a, b, normal, penetration):
    """
    在 normal 方向上对 a, b 施加冲量，并做位置修正。
    normal: 单位法向量（从 b 指向 a）
    penetration: 穿透深度（正值）
    """
    restitution = min(a.restitution, b.restitution)

    rel_vel = a.vel - b.vel
    vel_along_normal = np.dot(rel_vel, normal)

    # 如果两物体正在分离，不需要处理
    if vel_along_normal > 0:
        return

    inv_mass_a = 1.0 / a.mass if a.mass > 0 else 0.0
    inv_mass_b = 1.0 / b.mass if b.mass > 0 else 0.0
    inv_mass_sum = inv_mass_a + inv_mass_b

    if inv_mass_sum == 0:
        return

    # 冲量大小
    j = -(1 + restitution) * vel_along_normal / inv_mass_sum

    impulse = j * normal
    a.vel += impulse * inv_mass_a
    b.vel -= impulse * inv_mass_b

    # 位置修正：按质量倒数分配穿透深度，留 20% 缓冲防抖动
    slop = 0.5        # 允许的最小穿透量（像素），低于此不修正
    percent = 0.8     # 修正比例
    correction_mag = max(penetration - slop, 0.0) * percent / inv_mass_sum
    correction = correction_mag * normal
    a.pos += correction * inv_mass_a
    b.pos -= correction * inv_mass_b


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


# ──────────────────────────────────────────────
# 入口：对所有对象对进行碰撞检测
# ──────────────────────────────────────────────
def detect_and_resolve(objects):
    """遍历所有物体对，执行碰撞检测与响应。"""
    n = len(objects)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = objects[i], objects[j]
            if isinstance(a, Ball) and isinstance(b, Ball):
                collide_ball_ball(a, b)
            elif isinstance(a, Block) and isinstance(b, Block):
                collide_block_block(a, b)
            elif isinstance(a, Ball) and isinstance(b, Block):
                collide_ball_block(a, b)
            elif isinstance(a, Block) and isinstance(b, Ball):
                collide_ball_block(b, a)   # 保持 ball 在前
