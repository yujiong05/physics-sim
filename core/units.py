import numpy as np

# 物理单位换算比例：100 px = 1 m
PIXELS_PER_METER = 100.0

def px_to_m(px):
    if isinstance(px, (list, np.ndarray)):
        return np.array(px) / PIXELS_PER_METER
    return px / PIXELS_PER_METER

def m_to_px(m):
    if isinstance(m, (list, np.ndarray)):
        return np.array(m) * PIXELS_PER_METER
    return m * PIXELS_PER_METER

def px_s_to_m_s(v):
    return px_to_m(v)

def m_s_to_px_s(v):
    return m_to_px(v)

def px_s2_to_m_s2(a):
    return px_to_m(a)

def m_s2_to_px_s2(a):
    return m_to_px(a)

def internal_force_to_newton(f):
    # Newton = kg * m/s^2 = kg * (px/s^2 / 100)
    return px_to_m(f)

def newton_to_internal_force(f):
    return m_to_px(f)

def kinetic_energy_joule(mass, speed_px_s):
    # J = 0.5 * m * (v_m/s)^2
    v_m_s = px_s_to_m_s(speed_px_s)
    return 0.5 * mass * (v_m_s ** 2)

def potential_energy_joule(mass, gravity_px_s2, height_px):
    # J = m * g_m/s^2 * h_m
    g_m_s2 = abs(px_s2_to_m_s2(gravity_px_s2))
    h_m = px_to_m(height_px)
    return mass * g_m_s2 * h_m

def spring_energy_joule(internal_energy):
    # 内部能量 = 0.5 * k * dx_px^2
    # SI 能量 = 0.5 * k_si * dx_m^2
    # 1 px = 0.01 m, 所以 px^2 = 0.0001 m^2
    # 简单换算：J = internal / 10000.0
    return internal_energy / (PIXELS_PER_METER ** 2)
