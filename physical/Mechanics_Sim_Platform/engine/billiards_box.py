# -*- coding: utf-8 -*-
"""
二维矩形边界内两圆盘运动：匀速积分 + 完全弹性碰壁 + 可选恢复系数的对心碰撞冲量模型。
纯 NumPy，无 UI 依赖。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class BilliardsState:
    """两球状态：位置 (m)、速度 (m/s)、质量 (kg)、半径 (m)。"""

    pos: np.ndarray  # shape (2, 2)  (x,y) per ball
    vel: np.ndarray  # shape (2, 2)
    m: np.ndarray  # shape (2,)
    r: np.ndarray  # shape (2,)


def radii_from_masses(m1: float, m2: float, m_ref: float = 1.0, r_ref: float = 0.055) -> Tuple[float, float]:
    """质量越大半径越大（按体积 ∝ 质量估算 r ∝ m^{1/3}），并钳制范围避免溢出箱体。"""
    r1 = float(r_ref * (max(m1, 1e-6) / m_ref) ** (1.0 / 3.0))
    r2 = float(r_ref * (max(m2, 1e-6) / m_ref) ** (1.0 / 3.0))
    return float(np.clip(r1, 0.018, 0.13)), float(np.clip(r2, 0.018, 0.13))


def spawn_centers(box_w: float, box_h: float, r1: float, r2: float) -> Tuple[np.ndarray, np.ndarray]:
    """左右分居放置，避免初始重叠。"""
    margin = 0.06
    y = box_h * 0.5
    x1 = r1 + margin
    x2 = box_w - r2 - margin
    if x2 - x1 < r1 + r2 + 0.02:
        mid = 0.5 * box_w
        x1 = mid - (r1 + r2 + 0.04) * 0.5
        x2 = mid + (r1 + r2 + 0.04) * 0.5
        x1 = float(np.clip(x1, r1 + 1e-3, box_w * 0.5 - r1))
        x2 = float(np.clip(x2, box_w * 0.5 + r2, box_w - r2 - 1e-3))
    return np.array([x1, y], dtype=float), np.array([x2, y], dtype=float)


def polar_to_velocity(speed: float, angle_deg: float) -> np.ndarray:
    """方向角相对 +x 轴逆时针（数学惯例），单位度。"""
    th = np.deg2rad(angle_deg)
    return np.array([speed * np.cos(th), speed * np.sin(th)], dtype=float)


def resolve_walls(state: BilliardsState, box_w: float, box_h: float) -> None:
    """刚性碰壁：位置钳制并镜面反射速度。"""
    for i in range(2):
        x, y = state.pos[i]
        r = float(state.r[i])
        vx, vy = state.vel[i]

        if x < r:
            x = r
            vx *= -1.0
        elif x > box_w - r:
            x = box_w - r
            vx *= -1.0

        if y < r:
            y = r
            vy *= -1.0
        elif y > box_h - r:
            y = box_h - r
            vy *= -1.0

        state.pos[i, 0] = x
        state.pos[i, 1] = y
        state.vel[i, 0] = vx
        state.vel[i, 1] = vy


def resolve_ball_collision(state: BilliardsState, e: float) -> None:
    """两球重叠时先分离，再沿连心线施加冲量（恢复系数 e）。"""
    d = state.pos[1] - state.pos[0]
    dist = float(np.linalg.norm(d))
    min_dist = float(state.r[0] + state.r[1])
    if dist < 1e-12 or dist >= min_dist:
        return

    n = d / dist
    overlap = min_dist - dist

    m1 = float(state.m[0])
    m2 = float(state.m[1])
    inv_mt = 1.0 / (m1 + m2)

    state.pos[0] -= n * overlap * (m2 * inv_mt)
    state.pos[1] += n * overlap * (m1 * inv_mt)

    v_rel = state.vel[1] - state.vel[0]
    vn = float(np.dot(v_rel, n))
    if vn >= 0.0:
        return

    j = -(1.0 + float(np.clip(e, 0.0, 1.0))) * vn / (1.0 / m1 + 1.0 / m2)
    state.vel[0] -= (j / m1) * n
    state.vel[1] += (j / m2) * n


def kinetic_energy(state: BilliardsState) -> float:
    ke = 0.0
    for i in range(2):
        v2 = float(np.dot(state.vel[i], state.vel[i]))
        ke += 0.5 * float(state.m[i]) * v2
    return float(ke)


def step_state(state: BilliardsState, dt: float, box_w: float, box_h: float, e_ball: float, substeps: int = 10) -> None:
    """半隐式：多子步减小穿墙/穿透。"""
    h = float(dt / max(int(substeps), 1))
    for _ in range(int(substeps)):
        state.pos += state.vel * h
        resolve_walls(state, box_w, box_h)
        resolve_ball_collision(state, e_ball)


def make_state(m1: float, m2: float, speed1: float, ang1_deg: float, speed2: float, ang2_deg: float, box_w: float, box_h: float) -> BilliardsState:
    r1, r2 = radii_from_masses(m1, m2)
    p1, p2 = spawn_centers(box_w, box_h, r1, r2)
    v1 = polar_to_velocity(speed1, ang1_deg)
    v2 = polar_to_velocity(speed2, ang2_deg)
    return BilliardsState(
        pos=np.stack([p1, p2]),
        vel=np.stack([v1, v2]),
        m=np.array([m1, m2], dtype=float),
        r=np.array([r1, r2], dtype=float),
    )


def clamp_positions(state: BilliardsState, box_w: float, box_h: float) -> None:
    """将球心限制在箱体内且不与边界相交。"""
    for i in range(2):
        r = float(state.r[i])
        state.pos[i, 0] = float(np.clip(state.pos[i, 0], r, box_w - r))
        state.pos[i, 1] = float(np.clip(state.pos[i, 1], r, box_h - r))


def update_radii_keep_centers(state: BilliardsState, m1: float, m2: float) -> None:
    """质量改变时更新半径；轻微推开以免重叠。"""
    r1, r2 = radii_from_masses(m1, m2)
    state.m[:] = [m1, m2]
    state.r[:] = [r1, r2]
    d = state.pos[1] - state.pos[0]
    dist = float(np.linalg.norm(d))
    min_dist = float(r1 + r2 + 1e-4)
    if dist < min_dist and dist > 1e-12:
        n = d / dist
        overlap = min_dist - dist
        m1f, m2f = float(state.m[0]), float(state.m[1])
        inv = 1.0 / (m1f + m2f)
        state.pos[0] -= n * overlap * (m2f * inv)
        state.pos[1] += n * overlap * (m1f * inv)

