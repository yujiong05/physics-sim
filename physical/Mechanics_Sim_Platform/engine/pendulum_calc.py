# -*- coding: utf-8 -*-
"""
平面双摆动力学：拉格朗日方程导出的耦合非线性 ODE + 可选粘性阻尼（−c·ω₁、−c·ω₂）。

实时仿真推荐使用「宏步 + 微步 RK4」接口 step_double_pendulum_rk4；
离线整条轨迹仍可用 calculate_double_pendulum（solve_ivp RK45）。

状态向量 y = [θ₁, ω₁, θ₂, ω₂]（弧度），ωᵢ = dθᵢ/dt。

坐标约定（y 轴向上，悬挂点为原点）：
  θ = 0 铅垂向下，逆时针为正。
  x₁ = L₁ sin θ₁, y₁ = −L₁ cos θ₁
  x₂ = x₁ + L₂ sin θ₂, y₂ = y₁ − L₂ cos θ₂

阻尼（关节粘性）：在角加速度上叠加 −c·ω₁、−c·ω₂（c≥0，单位 s⁻¹）。
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, Tuple

import numpy as np
from scipy.integrate import solve_ivp

G_DEFAULT = 9.8
_SOLVER_METHOD = "RK45"
DT_MICRO_DEFAULT = 1e-3


def _double_pendulum_rhs(
    _t: float,
    y: np.ndarray,
    m1: float,
    m2: float,
    L1: float,
    L2: float,
    g: float,
    c_damp: float,
) -> np.ndarray:
    th1, w1, th2, w2 = y
    delta = th1 - th2
    denom = 2.0 * m1 + m2 - m2 * np.cos(2.0 * th1 - 2.0 * th2)
    if abs(denom) < 1e-14:
        denom = np.copysign(1e-14, denom) if denom != 0.0 else 1e-14

    num1 = (
        -g * (2.0 * m1 + m2) * np.sin(th1)
        - m2 * g * np.sin(th1 - 2.0 * th2)
        - 2.0 * np.sin(delta) * m2 * (w2 * w2 * L2 + w1 * w1 * L1 * np.cos(delta))
    )
    th1dd = num1 / (L1 * denom)

    num2 = 2.0 * np.sin(delta) * (
        w1 * w1 * L1 * (m1 + m2)
        + g * (m1 + m2) * np.cos(th1)
        + w2 * w2 * L2 * m2 * np.cos(delta)
    )
    th2dd = num2 / (L2 * denom)

    c = float(max(c_damp, 0.0))
    th1dd -= c * w1
    th2dd -= c * w2

    return np.array([w1, th1dd, w2, th2dd], dtype=float)


def kinetic_energy(
    theta1: np.ndarray,
    omega1: np.ndarray,
    theta2: np.ndarray,
    omega2: np.ndarray,
    m1: float,
    m2: float,
    L1: float,
    L2: float,
) -> np.ndarray:
    """动能 T₁+T₂（向量化或标量）。"""
    t1 = np.asarray(theta1, dtype=float)
    t2 = np.asarray(theta2, dtype=float)
    w1 = np.asarray(omega1, dtype=float)
    w2 = np.asarray(omega2, dtype=float)
    vx1 = L1 * w1 * np.cos(t1)
    vy1 = L1 * w1 * np.sin(t1)
    vx2 = vx1 + L2 * w2 * np.cos(t2)
    vy2 = vy1 + L2 * w2 * np.sin(t2)
    return 0.5 * m1 * (vx1 * vx1 + vy1 * vy1) + 0.5 * m2 * (vx2 * vx2 + vy2 * vy2)


def potential_energy(
    theta1: np.ndarray,
    theta2: np.ndarray,
    m1: float,
    m2: float,
    L1: float,
    L2: float,
    g: float,
) -> np.ndarray:
    """势能 V = m₁ g y₁ + m₂ g y₂。"""
    t1 = np.asarray(theta1, dtype=float)
    t2 = np.asarray(theta2, dtype=float)
    y1 = -L1 * np.cos(t1)
    y2 = y1 - L2 * np.cos(t2)
    return m1 * g * y1 + m2 * g * y2


def total_energy(
    theta1: np.ndarray,
    omega1: np.ndarray,
    theta2: np.ndarray,
    omega2: np.ndarray,
    m1: float,
    m2: float,
    L1: float,
    L2: float,
    g: float,
) -> np.ndarray:
    return kinetic_energy(theta1, omega1, theta2, omega2, m1, m2, L1, L2) + potential_energy(
        theta1, theta2, m1, m2, L1, L2, g
    )


def state_cartesian(y: np.ndarray, L1: float, L2: float) -> Tuple[float, float, float, float]:
    """单时刻笛卡尔坐标。"""
    th1, _w1, th2, _w2 = y
    x1 = float(L1 * np.sin(th1))
    y1 = float(-L1 * np.cos(th1))
    x2 = float(x1 + L2 * np.sin(th2))
    y2 = float(y1 - L2 * np.cos(th2))
    return x1, y1, x2, y2


def state_mechanics(
    y: np.ndarray,
    m1: float,
    m2: float,
    L1: float,
    L2: float,
    g: float,
) -> Dict[str, float]:
    """单时刻 KE、PE、E 与位置。"""
    th1, w1, th2, w2 = y
    ke = float(kinetic_energy(th1, w1, th2, w2, m1, m2, L1, L2))
    pe = float(potential_energy(th1, th2, m1, m2, L1, L2, g))
    x1, y1, x2, y2 = state_cartesian(y, L1, L2)
    return {"ke": ke, "pe": pe, "e_total": ke + pe, "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def _rk4_step(y: np.ndarray, h: float, rhs: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    k1 = rhs(y)
    k2 = rhs(y + 0.5 * h * k1)
    k3 = rhs(y + 0.5 * h * k2)
    k4 = rhs(y + h * k3)
    return y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def step_double_pendulum_rk4(
    y: np.ndarray,
    *,
    m1: float,
    m2: float,
    L1: float,
    L2: float,
    g: float = G_DEFAULT,
    c_damp: float,
    macro_dt: float,
    dt_micro: float = DT_MICRO_DEFAULT,
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    在一个 UI 宏步 macro_dt 内，用 N 个微步 RK4 推进（微步长 h = macro_dt / N，严格铺满宏步）。

    返回 (y_new, mechanics_dict)，mechanics_dict 含 ke, pe, e_total, x1, y1, x2, y2。
    """
    y = np.asarray(y, dtype=float).copy()
    macro_dt = float(macro_dt)
    dt_micro = float(max(dt_micro, 1e-12))
    n_sub = max(1, int(math.ceil(macro_dt / dt_micro)))
    h = macro_dt / n_sub

    def rhs(state: np.ndarray) -> np.ndarray:
        return _double_pendulum_rhs(0.0, state, m1, m2, L1, L2, g, c_damp)

    for _ in range(n_sub):
        y = _rk4_step(y, h, rhs)

    info = state_mechanics(y, m1, m2, L1, L2, g)
    return y, info


def angles_to_cartesian(
    theta1: np.ndarray,
    theta2: np.ndarray,
    L1: float,
    L2: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    t1 = np.asarray(theta1, dtype=float)
    t2 = np.asarray(theta2, dtype=float)
    x1 = L1 * np.sin(t1)
    y1 = -L1 * np.cos(t1)
    x2 = x1 + L2 * np.sin(t2)
    y2 = y1 - L2 * np.cos(t2)
    return x1, y1, x2, y2


def calculate_double_pendulum(
    m1: float,
    m2: float,
    L1: float,
    L2: float,
    theta1_init: float,
    theta2_init: float,
    t_max: float,
    *,
    g: float = G_DEFAULT,
    c_damp: float = 0.0,
    n_points: int = 4500,
) -> Dict[str, Any]:
    """
    离线积分 [0, t_max]，便于校验或与实时 RK4 对比。c_damp 为阻尼系数。
    """
    m1 = float(m1)
    m2 = float(m2)
    L1 = float(L1)
    L2 = float(L2)
    t_max = float(t_max)
    n_points = max(10, int(n_points))

    y0 = np.array([theta1_init, 0.0, theta2_init, 0.0], dtype=float)
    t_eval = np.linspace(0.0, t_max, n_points)

    def fun(_t: float, y: np.ndarray) -> np.ndarray:
        return _double_pendulum_rhs(_t, y, m1, m2, L1, L2, g, c_damp)

    sol = solve_ivp(
        fun,
        (0.0, t_max),
        y0,
        method=_SOLVER_METHOD,
        t_eval=t_eval,
        rtol=1e-9,
        atol=1e-11,
    )

    if not sol.success or sol.y.size == 0:
        raise RuntimeError(sol.message if hasattr(sol, "message") else "solve_ivp failed")

    t = sol.t
    theta1 = sol.y[0]
    omega1 = sol.y[1]
    theta2 = sol.y[2]
    omega2 = sol.y[3]

    x1, y1, x2, y2 = angles_to_cartesian(theta1, theta2, L1, L2)
    ke = kinetic_energy(theta1, omega1, theta2, omega2, m1, m2, L1, L2)
    pe = potential_energy(theta1, theta2, m1, m2, L1, L2, g)
    energy = ke + pe

    return {
        "t": t,
        "theta1": theta1,
        "theta2": theta2,
        "omega1": omega1,
        "omega2": omega2,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "ke": ke,
        "pe": pe,
        "energy": energy,
    }
