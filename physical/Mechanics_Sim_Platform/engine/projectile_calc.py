# -*- coding: utf-8 -*-
"""
抛物运动数值求解（理想 vs 空气阻力），纯 NumPy / SciPy，不含任何界面代码。

阻力模型：与速率平方成正比、方向与速度相反
    F_drag = -k * |v|^2 * (v / |v|) = -k * |v| * v
对应加速度（质量 m）：a_drag = -(k/m) * |v| * [vx, vy]^T
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp

# 物理常数（标准重力加速度，贴近中学/大学教材常用取值）
G_DEFAULT = 9.81

# 发射高度微小正值，避免 θ=0 且 vy=0 时立刻处于 y<0；与 calculate_projectile 一致。
Y_LAUNCH_EPS = 1e-4

# UI 宏步内经典 RK4 微步的默认尺度（s）。
DT_MICRO_DEFAULT = 1e-3

# SciPy 的 solve_ivp 未提供固定步长的经典 RK4 接口；RK45 为同族的显式 Runge-Kutta（Dormand–Prince），
# 精度与稳定性优于低阶固定步长 RK4，适合教学仿真。
_SOLVER_METHOD = "RK45"


def _make_state_rhs_ideal(g: float) -> Callable[[float, np.ndarray], np.ndarray]:
    """构造理想情况（仅重力）的右端项：d[x,y,vx,vy]/dt。"""

    def rhs(_t: float, s: np.ndarray) -> np.ndarray:
        _x, _y, vx, vy = s
        return np.array([vx, vy, 0.0, -g], dtype=float)

    return rhs


def _make_state_rhs_drag(g: float, k: float, m: float) -> Callable[[float, np.ndarray], np.ndarray]:
    """构造含二次阻力（相对于速率平方）的右端项。"""

    def rhs(_t: float, s: np.ndarray) -> np.ndarray:
        _x, _y, vx, vy = s
        v_mag = float(np.hypot(vx, vy))
        ax = 0.0
        ay = -g
        if v_mag > 1e-12:
            factor = -(k / m) * v_mag
            ax = factor * vx
            ay = factor * vy - g
        return np.array([vx, vy, ax, ay], dtype=float)

    return rhs


def projectile_kinetic_energy(vx: float, vy: float, m: float) -> float:
    r"""平动动能 \(\frac12 m (v_x^2+v_y^2)\)。"""
    return 0.5 * float(m) * (float(vx) * float(vx) + float(vy) * float(vy))


def projectile_potential_energy(y: float, m: float, g: float) -> float:
    r"""重力势能 \(m g y\)（\(y\) 向上为正，地面 \(y=0\)）。"""
    return float(m) * float(g) * float(y)


def projectile_mechanics_from_state(s: np.ndarray, m: float, g: float) -> Dict[str, float]:
    r"""由状态 \([x,y,v_x,v_y]\) 给出动能、势能、总机械能及位置。"""
    x, y, vx, vy = (float(v) for v in np.asarray(s, dtype=float).reshape(4))
    ke = projectile_kinetic_energy(vx, vy, m)
    pe = projectile_potential_energy(y, m, g)
    return {"ke": ke, "pe": pe, "e_total": ke + pe, "x": x, "y": y, "vx": vx, "vy": vy}


def step_projectile_rk4(
    y: np.ndarray,
    *,
    g: float,
    k: float,
    m: float,
    macro_dt: float,
    dt_micro: float = DT_MICRO_DEFAULT,
) -> Tuple[np.ndarray, Dict[str, float]]:
    r"""
    将状态 \([x,y,v_x,v_y]\) 沿仿真时间推进 macro_dt：划分为若干微步，每微步手写经典 RK4。
    ``k=0`` 时使用理想（仅重力）右端项；否则使用二次阻力模型。
    返回新状态与末端时刻的力学标量（动能、势能、总机械能等）。
    """
    state = np.asarray(y, dtype=float).reshape(4).copy()
    if macro_dt <= 0.0:
        return state, projectile_mechanics_from_state(state, float(m), float(g))

    rhs: Callable[[float, np.ndarray], np.ndarray]
    if float(k) <= 0.0:
        rhs = _make_state_rhs_ideal(float(g))
    else:
        rhs = _make_state_rhs_drag(float(g), float(k), float(m))

    n = max(1, int(np.ceil(float(macro_dt) / float(dt_micro))))
    h = float(macro_dt) / float(n)

    def rk4_step(s: np.ndarray, hh: float) -> np.ndarray:
        k1 = rhs(0.0, s)
        k2 = rhs(0.0, s + 0.5 * hh * k1)
        k3 = rhs(0.0, s + 0.5 * hh * k2)
        k4 = rhs(0.0, s + hh * k3)
        return s + (hh / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    for _ in range(n):
        state = rk4_step(state, h)

    return state, projectile_mechanics_from_state(state, float(m), float(g))


def _landing_event(_t: float, s: np.ndarray) -> float:
    """落地事件：高度 y 穿过 0（仅在 vy<0 阶段触发，direction=-1）。"""
    return float(s[1])


_landing_event.terminal = True  # type: ignore[attr-defined]
_landing_event.direction = -1.0  # type: ignore[attr-defined]


def _integrate_until_ground(
    rhs: Callable[[float, np.ndarray], np.ndarray],
    y0_state: np.ndarray,
    t_max: float,
    *,
    rtol: float = 1e-9,
    atol: float = 1e-11,
    max_step: Optional[float] = None,
) -> Any:
    """
    从 t=0 积分直到落地事件（y=0 向下穿越）或到达 t_max。
    返回 scipy OdeResult（含 dense_output 时可后续重采样）。
    """
    # 赋事件属性（使用独立函数避免共享可变状态）
    events_fn = _landing_event

    kwargs = dict(
        fun=rhs,
        t_span=(0.0, float(t_max)),
        y0=y0_state.astype(float),
        method=_SOLVER_METHOD,
        rtol=rtol,
        atol=atol,
        dense_output=True,
        events=events_fn,
    )
    if max_step is not None:
        kwargs["max_step"] = max_step
    sol = solve_ivp(**kwargs)
    return sol


def _uniform_sample_solution(sol: Any, n_samples: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    在 [0, sol.t[-1]] 上均匀采样状态轨迹。
    返回 (t_arr, states) 其中 states.shape == (4, n_samples)。
    """
    t_end = float(sol.t[-1])
    if t_end <= 0.0:
        t_end = max(float(np.max(sol.t)), 1e-9)

    n = max(int(n_samples), 2)
    t_grid = np.linspace(0.0, t_end, n)

    # sol.sol 可能在部分失败解上不可用；优先 dense_output
    if sol.sol is not None:
        states = sol.sol(t_grid)
    else:
        # 退化：线性插值已有采样点
        states = np.zeros((4, n))
        for i in range(4):
            states[i, :] = np.interp(t_grid, sol.t, sol.y[i, :])

    return t_grid, np.asarray(states, dtype=float)


def calculate_projectile(
    v0: float,
    angle_deg: float,
    m: float,
    k: float,
    t_max: float,
    *,
    g: float = G_DEFAULT,
    n_samples: int = 1200,
) -> Dict[str, Dict[str, np.ndarray]]:
    """
    计算理想抛物与有阻力抛物，直到落地（y<=0 的向下穿越）或积分上限 t_max。

    参数
    ------
    v0 : float
        初速率 (m/s)，>0。
    angle_deg : float
        发射仰角（相对水平），度。
    m : float
        质量 (kg)，>0。
    k : float
        阻力系数 (SI 下与 F∝v² 定义一致)，>=0。
    t_max : float
        积分时间上界 (s)，防止未落地时无限积分。
    g : float
        重力加速度大小。
    n_samples : int
        输出时间序列均匀采样点数（含端点）。

    返回
    ------
    dict
        {
          "ideal": {"t","x","y","vx","vy"},
          "drag":  {"t","x","y","vx","vy"},
        }
        各字段均为 1D np.ndarray，ideal/drag 长度可不同（由各自落地时间决定）。
    """
    if v0 <= 0:
        raise ValueError("v0 必须为正。")
    if m <= 0:
        raise ValueError("质量 m 必须为正。")
    if k < 0:
        raise ValueError("阻力系数 k 不能为负。")
    if t_max <= 0:
        raise ValueError("t_max 必须为正。")

    theta = np.deg2rad(float(angle_deg))
    vx0 = v0 * np.cos(theta)
    vy0 = v0 * np.sin(theta)
    # 发射点取极小正高度，避免 θ=0 且 vy=0 时质点立刻处于 y<0 的退化情形，
    # 同时不影响教学可视化的尺度感。
    y_init = float(Y_LAUNCH_EPS)
    y0_state = np.array([0.0, y_init, vx0, vy0], dtype=float)

    rhs_ideal = _make_state_rhs_ideal(g)
    rhs_drag = _make_state_rhs_drag(g, float(k), float(m))

    sol_ideal = _integrate_until_ground(rhs_ideal, y0_state, t_max)
    sol_drag = _integrate_until_ground(rhs_drag, y0_state, t_max)

    if not sol_ideal.success:
        raise RuntimeError(f"理想轨迹积分失败：{sol_ideal.message}")
    if not sol_drag.success:
        raise RuntimeError(f"阻力轨迹积分失败：{sol_drag.message}")

    def pack(sol: Any) -> Dict[str, np.ndarray]:
        t_arr, states = _uniform_sample_solution(sol, n_samples)
        x = states[0, :].copy()
        y = states[1, :].copy()
        vx = states[2, :].copy()
        vy = states[3, :].copy()
        # 数值噪声可能导致最后一个采样点略低于地面；为可视化裁剪到 y>=0
        mask = y >= -1e-9
        if not np.all(mask):
            last_good = np.where(mask)[0]
            if last_good.size == 0:
                return {
                    "t": t_arr[:1],
                    "x": x[:1],
                    "y": np.maximum(y[:1], 0.0),
                    "vx": vx[:1],
                    "vy": vy[:1],
                }
            idx = last_good[-1]
            t_arr = t_arr[: idx + 1]
            x = x[: idx + 1]
            y = np.maximum(y[: idx + 1], 0.0)
            vx = vx[: idx + 1]
            vy = vy[: idx + 1]
        else:
            y = np.maximum(y, 0.0)
        return {"t": t_arr, "x": x, "y": y, "vx": vx, "vy": vy}

    return {"ideal": pack(sol_ideal), "drag": pack(sol_drag)}
