# -*- coding: utf-8 -*-
"""
一维光滑导轨上的对心碰撞模型（无外力分段匀速）。
动量守恒 + 恢复系数 e：v₂′ − v₁′ = e (u₁ − u₂)。

本模块不含界面代码；轨迹采用闭式分段拼接（无需数值积分）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np


def post_collision_velocities(m1: float, m2: float, u1: float, u2: float, e: float) -> Tuple[float, float]:
    """
    计算碰后速度 v₁′, v₂′。
    e ∈ [0, 1]，e=1 为弹性，e=0 为完全非弹性极限（但本模型仍为瞬时碰撞公式，非粘连）。
    """
    mt = m1 + m2
    v1p = ((m1 - e * m2) * u1 + (1.0 + e) * m2 * u2) / mt
    v2p = ((1.0 + e) * m1 * u1 + (m2 - e * m1) * u2) / mt
    return float(v1p), float(v2p)


def _collision_time(
    x1_0: float,
    x2_0: float,
    u1: float,
    u2: float,
    r1: float,
    r2: float,
    eps: float = 1e-9,
) -> Tuple[bool, float]:
    """
    判断是否在 t≥0 发生碰撞，并给出碰撞时刻（相对运动匀速）。
    约定：球 2 在球 1 右侧（x₂ > x₁），接触条件：x₂ − x₁ = r₁ + r₂。
    """
    R = float(r1 + r2)
    gap_surface = float(x2_0 - x1_0) - R

    if gap_surface <= eps:
        return True, 0.0

    du = float(u1 - u2)
    if abs(du) <= eps:
        return False, float("inf")

    # gap_surface(t) = gap_surface + (u₂ − u₁) t = gap_surface − du · t
    t_c = gap_surface / du
    if t_c > eps and du > 0:
        return True, float(t_c)

    return False, float("inf")


def simulate_collision_1d(
    m1: float,
    m2: float,
    u1: float,
    u2: float,
    x1_0: float,
    x2_0: float,
    r1: float,
    r2: float,
    e: float,
    *,
    t_tail: float = 4.0,
    n_samples: int = 720,
) -> Dict[str, Any]:
    """
    生成统一时间轴上的位置、速度、动能序列。

    参数
    ------
    m1, m2 : 质量 (kg)，必须为正。
    u1, u2 : 碰前速度 (m/s)，沿轨正向。
    x1_0, x2_0 : 初始球心坐标 (m)，需满足 x2_0 > x1_0（球 2 在右侧）。
    r1, r2 : 半径 (m)，非负。
    e : 恢复系数 [0, 1]。
    t_tail : 碰撞结束后额外展示的仿真时长 (s)。
    n_samples : 输出采样点数（含端点）。

    返回
    ------
    dict 包含 t, x1, x2, v1, v2, ke1, ke2, ke_total，
    以及 t_collision（无碰撞则为 None）、v1_after, v2_after、has_collision、ke 对标量（碰前/碰后）。
    """
    if m1 <= 0 or m2 <= 0:
        raise ValueError("质量必须为正。")
    if r1 < 0 or r2 < 0:
        raise ValueError("半径不能为负。")
    if not (0.0 <= e <= 1.0):
        raise ValueError("恢复系数 e 应在 [0, 1]。")
    if x2_0 <= x1_0:
        raise ValueError("需满足 x₂₀ > x₁₀（球 2 在右侧），以保证对心碰撞几何约定。")

    has_collision, t_c = _collision_time(x1_0, x2_0, u1, u2, r1, r2)

    if has_collision:
        v1p, v2p = post_collision_velocities(m1, m2, u1, u2, e)
        u1_after, u2_after = v1p, v2p
    else:
        v1p, v2p = u1, u2
        u1_after, u2_after = u1, u2

    ke1_pre = 0.5 * m1 * u1 * u1
    ke2_pre = 0.5 * m2 * u2 * u2
    ke_pre_total = ke1_pre + ke2_pre

    ke1_post_scalar = 0.5 * m1 * u1_after * u1_after
    ke2_post_scalar = 0.5 * m2 * u2_after * u2_after
    ke_post_total = ke1_post_scalar + ke2_post_scalar

    if has_collision and np.isfinite(t_c):
        t_end = float(max(t_c + max(t_tail, 1.0), 2.5))
    else:
        t_end = float(max(5.0, t_tail, 2.5))

    n = max(int(n_samples), 3)
    t = np.linspace(0.0, t_end, n)

    x1 = np.empty_like(t)
    x2 = np.empty_like(t)
    v1 = np.empty_like(t)
    v2 = np.empty_like(t)

    if not has_collision or not np.isfinite(t_c):
        x1[:] = x1_0 + u1 * t
        x2[:] = x2_0 + u2 * t
        v1[:] = u1
        v2[:] = u2
    else:
        tc = float(t_c)
        x1_c = x1_0 + u1 * tc
        x2_c = x2_0 + u2 * tc
        mask_pre = t <= tc
        tp = t[mask_pre]
        x1[mask_pre] = x1_0 + u1 * tp
        x2[mask_pre] = x2_0 + u2 * tp
        v1[mask_pre] = u1
        v2[mask_pre] = u2

        mask_post = ~mask_pre
        if np.any(mask_post):
            dt = t[mask_post] - tc
            x1[mask_post] = x1_c + v1p * dt
            x2[mask_post] = x2_c + v2p * dt
            v1[mask_post] = v1p
            v2[mask_post] = v2p

    ke1 = 0.5 * m1 * v1 * v1
    ke2 = 0.5 * m2 * v2 * v2
    ke_total = ke1 + ke2

    return {
        "t": t,
        "x1": x1,
        "x2": x2,
        "v1": v1,
        "v2": v2,
        "ke1": ke1,
        "ke2": ke2,
        "ke_total": ke_total,
        "t_collision": float(t_c) if has_collision and np.isfinite(t_c) else None,
        "has_collision": bool(has_collision and np.isfinite(t_c)),
        "v1_after": float(u1_after),
        "v2_after": float(u2_after),
        "ke1_pre": float(ke1_pre),
        "ke2_pre": float(ke2_pre),
        "ke_pre_total": float(ke_pre_total),
        "ke1_post": float(ke1_post_scalar),
        "ke2_post": float(ke2_post_scalar),
        "ke_post_total": float(ke_post_total),
        "r1": float(r1),
        "r2": float(r2),
    }
