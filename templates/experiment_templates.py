"""
templates/experiment_templates.py
预设实验模板，每个模板返回与 JSON 保存格式兼容的数据字典。
"""
import math

def _engine_defaults(gravity=None):
    return {
        "time": 0.0,
        "gravity": gravity or [0.0, 980.0],
        "bounds": [0, 0, 800, 600]
    }

def _ball(id, name, x, y, vx=0.0, vy=0.0, radius=20.0, mass=1.0, restitution=0.8):
    return {
        "id": id,
        "type": "ball",
        "name": name,
        "pos": [float(x), float(y)],
        "vel": [float(vx), float(vy)],
        "acc": [0.0, 0.0],
        "mass": float(mass),
        "radius": float(radius),
        "restitution": float(restitution)
    }

def _block(id, name, x, y, vx=0.0, vy=0.0, angle=0.0, width=60.0, height=60.0, mass=1.0, restitution=0.8, friction=0.1):
    return {
        "id": id,
        "type": "block",
        "name": name,
        "pos": [float(x), float(y)],
        "vel": [float(vx), float(vy)],
        "acc": [0.0, 0.0],
        "mass": float(mass),
        "angle": float(angle),
        "width": float(width),
        "height": float(height),
        "restitution": float(restitution),
        "friction": float(friction)
    }

def _spring(id, name, start_pos, end_pos, rest_length, stiffness=30.0, damping=0.5, start_id=None, end_id=None):
    return {
        "id": id,
        "type": "spring",
        "name": name,
        "start_pos": start_pos,
        "end_pos": end_pos,
        "start_local_offset": [0.0, 0.0],
        "end_local_offset": [0.0, 0.0],
        "start_body_id": start_id,
        "end_body_id": end_id,
        "rest_length": float(rest_length),
        "stiffness": float(stiffness),
        "damping": float(damping)
    }

def _static_block(id, name, x, y, width, height, angle=0.0, restitution=0.8, friction=0.1):
    return {
        "id": id,
        "type": "static_block",
        "name": name,
        "pos": [float(x), float(y)],
        "width": float(width),
        "height": float(height),
        "angle": float(angle),
        "restitution": float(restitution),
        "friction": float(friction)
    }

def _groove(id, name, x, y, radius, thickness, restitution=0.8, friction=0.1, fixed=True):
    return {
        "id": id,
        "type": "groove",
        "name": name,
        "center_pos": [float(x), float(y)],
        "radius": float(radius),
        "thickness": float(thickness),
        "start_angle": 0.0,
        "end_angle": 180.0,
        "restitution": float(restitution),
        "friction": float(friction),
        "fixed": fixed,
        "static": fixed,
        "mass": 10.0,
        "vel": [0.0, 0.0],
        "acc": [0.0, 0.0]
    }

def _rod(id, name, start_pos, end_pos, thickness=6, mass=1.0, start_id=None, end_id=None):
    return {
        "id": id,
        "type": "rod",
        "name": name,
        "start_pos": start_pos,
        "end_pos": end_pos,
        "thickness": float(thickness),
        "mass": float(mass),
        "color": "#a0a0a0",
        "fixed_start": start_id is None,
        "fixed_end": end_id is None,
        "start_body_id": start_id,
        "end_body_id": end_id,
        "start_local_offset": [0.0, 0.0],
        "end_local_offset": [0.0, 0.0],
        "friction": 0.0,
        "damping": 0.0,
        "length": float(math.sqrt((end_pos[0]-start_pos[0])**2 + (end_pos[1]-start_pos[1])**2))
    }

def _rope(id, name, start_pos, end_pos, length=None, damping=0.2, start_id=None, end_id=None):
    if length is None:
        length = math.sqrt((end_pos[0]-start_pos[0])**2 + (end_pos[1]-start_pos[1])**2)
    return {
        "id": id,
        "type": "rope",
        "name": name,
        "start_pos": start_pos,
        "end_pos": end_pos,
        "length": float(length),
        "damping": float(damping),
        "color": "#333333",
        "thickness": 3.0,
        "fixed_start": start_id is None,
        "fixed_end": end_id is None,
        "start_body_id": start_id,
        "end_body_id": end_id,
        "start_local_offset": [0.0, 0.0],
        "end_local_offset": [0.0, 0.0]
    }

def tpl_free_fall():
    return {
        "name": "自由落体实验",
        "description": "观察小球在重力作用下的位移、速度变化。图表单位已按 100 px = 1 m 换算为 SI 单位。",
        "engine": _engine_defaults([0.0, 980.0]),
        "counters": {"ball": 2, "platform": 2},
        "scene": {
            "experiment_mode": "vertical",
            "show_velocity_arrow": True,
            "show_trail": True
        },
        "objects": [
            _ball("tpl_ff_ball1", "ball1", 400, 120, 0, 0, 20, 1.0, 0.6),
            _static_block("tpl_ff_plat1", "platform1", 400, 570, 800, 30, 0.0, 0.6)
        ],
        "preferred_observe_object": "ball1",
        "preferred_curves": ["y", "vy", "kinetic_energy", "potential_energy"]
    }

def tpl_projectile_motion():
    return {
        "name": "平抛运动实验",
        "description": "观察水平速度不变、竖直方向受重力影响的抛物线轨迹。图表单位已按 100 px = 1 m 换算为 SI 单位。",
        "engine": _engine_defaults([0.0, 980.0]),
        "counters": {"ball": 2, "platform": 2},
        "scene": {
            "experiment_mode": "vertical",
            "show_velocity_arrow": True,
            "show_trail": True
        },
        "objects": [
            _ball("tpl_pm_ball1", "ball1", 120, 180, 450, 0, 16, 1.0, 0.4),
            _static_block("tpl_pm_plat1", "platform1", 400, 570, 800, 30)
        ],
        "preferred_observe_object": "ball1",
        "preferred_curves": ["x", "y", "vx", "vy"]
    }

def tpl_elastic_collision():
    return {
        "name": "双球弹性碰撞实验",
        "description": "观察等质量小球弹性碰撞中的速度交换。",
        "engine": _engine_defaults([0.0, 0.0]),
        "counters": {"ball": 3},
        "scene": {
            "experiment_mode": "horizontal",
            "show_velocity_arrow": True,
            "show_trail": True
        },
        "objects": [
            _ball("tpl_ec_ball1", "ball1", 260, 360, 300, 0, 25, 1.0, 1.0),
            _ball("tpl_ec_ball2", "ball2", 520, 360, 0, 0, 25, 1.0, 1.0)
        ],
        "preferred_observe_object": "ball1",
        "preferred_curves": ["vx", "speed", "kinetic_energy"]
    }

def tpl_mass_collision():
    return {
        "name": "轻重球碰撞实验",
        "description": "观察不同质量物体碰撞后速度变化。",
        "engine": _engine_defaults([0.0, 0.0]),
        "counters": {"ball": 3},
        "scene": {
            "experiment_mode": "horizontal",
            "show_velocity_arrow": True,
            "show_trail": True
        },
        "objects": [
            _ball("tpl_mc_ball1", "ball1", 240, 360, 400, 0, 18, 1.0, 1.0),
            _ball("tpl_mc_ball2", "ball2", 540, 360, -80, 0, 32, 8.0, 1.0)
        ],
        "preferred_observe_object": "ball1",
        "preferred_curves": ["vx", "vy"]
    }

def tpl_inelastic_collision():
    return {
        "name": "非弹性碰撞实验",
        "description": "观察非弹性碰撞中动能损失和速度变化。",
        "engine": _engine_defaults([0.0, 0.0]),
        "counters": {"ball": 3},
        "scene": {
            "experiment_mode": "horizontal",
            "show_velocity_arrow": True,
            "show_trail": True
        },
        "objects": [
            _ball("tpl_ic_ball1", "ball1", 260, 360, 350, 0, 25, 1.0, 0.0),
            _ball("tpl_ic_ball2", "ball2", 520, 360, 0, 0, 25, 1.0, 0.0)
        ],
        "preferred_observe_object": "ball1",
        "preferred_curves": ["vx", "speed", "kinetic_energy"]
    }

def tpl_spring_oscillator():
    return {
        "name": "弹簧振子实验",
        "description": "观察弹簧连接小球后产生的周期性振动。",
        "engine": _engine_defaults([0.0, 0.0]),
        "counters": {"ball": 2, "spring": 2},
        "scene": {
            "experiment_mode": "horizontal",
            "show_velocity_arrow": True,
            "show_trail": True
        },
        "objects": [
            _ball("tpl_so_ball1", "ball1", 520, 360, 0, 0, 22, 1.0, 0.8),
            _spring("tpl_so_spring1", "spring1", [300, 360], [520, 360], 140, 30, 0.5, None, "tpl_so_ball1")
        ],
        "preferred_observe_object": "spring1",
        "preferred_curves": ["extension", "spring_energy"]
    }

def tpl_spring_coupled():
    return {
        "name": "弹簧连接双球实验",
        "description": "观察两个小球通过弹簧耦合振动。",
        "engine": _engine_defaults([0.0, 0.0]),
        "counters": {"ball": 3, "spring": 2},
        "scene": {
            "experiment_mode": "horizontal",
            "show_velocity_arrow": True,
            "show_trail": True
        },
        "objects": [
            _ball("tpl_sc_ball1", "ball1", 330, 360, 100, 0, 20, 1.0, 0.8),
            _ball("tpl_sc_ball2", "ball2", 560, 360, -100, 0, 20, 1.0, 0.8),
            _spring("tpl_sc_spring1", "spring1", [330, 360], [560, 360], 160, 25, 0.5, "tpl_sc_ball1", "tpl_sc_ball2")
        ],
        "preferred_observe_object": "spring1",
        "preferred_curves": ["extension", "spring_energy"]
    }

def tpl_groove_ball():
    return {
        "name": "小球落入半圆凹槽实验",
        "description": "观察小球从半圆槽一端落入后在槽内受约束运动。",
        "engine": _engine_defaults([0.0, 980.0]),
        "counters": {"ball": 2, "groove": 2},
        "scene": {
            "experiment_mode": "vertical",
            "show_velocity_arrow": True,
            "show_trail": True
        },
        "objects": [
            _groove("tpl_gb_groove1", "groove1", 430, 420, 150, 30, 0.8, 0.03, fixed=False),
            _ball("tpl_gb_ball1", "ball1", 310, 170, 0, 0, 18, 1.0, 0.0)
        ],
        "preferred_observe_object": "ball1"
    }

def tpl_double_pendulum():
    b1_pos = [440, 300]
    b2_pos = [510, 430]
    return {
        "name": "双摆实验",
        "description": "观察由两根细棒连接的双摆耦合运动。",
        "engine": _engine_defaults([0.0, 980.0]),
        "counters": {"ball": 2, "rod": 2},
        "scene": {
            "experiment_mode": "vertical",
            "show_velocity_arrow": True,
            "show_trail": True
        },
        "objects": [
            _ball("tpl_double_pendulum_ball1", "ball1", b1_pos[0], b1_pos[1], 120, 0, 18, 1.0, 0.8),
            _ball("tpl_double_pendulum_ball2", "ball2", b2_pos[0], b2_pos[1], 0, 0, 18, 1.0, 0.8),
            # rod1 连接固定点 [400, 150] 到 ball1
            _rod("tpl_double_pendulum_rod1", "rod1", [400, 150], b1_pos, 4, 1.0, None, "tpl_double_pendulum_ball1"),
            # rod2 连接 ball1 到 ball2
            _rod("tpl_double_pendulum_rod2", "rod2", b1_pos, b2_pos, 4, 1.0, "tpl_double_pendulum_ball1", "tpl_double_pendulum_ball2")
        ],
        "preferred_observe_object": "ball2",
        "preferred_curves": ["x", "y", "speed"]
    }

def tpl_newtons_cradle():
    objs = []
    anchor_y = 120
    rope_length = 240
    ball_radius = 18
    rest_y = anchor_y + rope_length
    
    # 静止的小球 (ball2 - ball5)
    x_static = [360, 396, 432, 468]
    for i, x in enumerate(x_static):
        bid = f"tpl_nc_ball{i+2}"
        objs.append(_ball(bid, f"ball{i+2}", x, rest_y, 0, 0, ball_radius, 1.0, 0.98))
        objs.append(_rope(f"tpl_nc_rope{i+2}", f"rope{i+2}", [x, anchor_y], [x, rest_y], rope_length, 0.05, None, bid))
    
    # 倾斜拉起的小球 (ball1)
    anchor1_x = 324
    angle_deg = -25
    angle_rad = math.radians(angle_deg)
    b1_x = anchor1_x + rope_length * math.sin(angle_rad)
    b1_y = anchor_y + rope_length * math.cos(angle_rad)
    
    objs.append(_ball("tpl_nc_ball1", "ball1", b1_x, b1_y, 0, 0, ball_radius, 1.0, 0.98))
    objs.append(_rope("tpl_nc_rope1", "rope1", [anchor1_x, anchor_y], [b1_x, b1_y], rope_length, 0.05, None, "tpl_nc_ball1"))
    
    return {
        "name": "牛顿摆实验",
        "description": "观察第一个小球从倾斜位置释放后，动量在等质量小球间传递。",
        "engine": _engine_defaults([0.0, 980.0]),
        "counters": {"ball": 6, "rope": 6},
        "scene": {
            "experiment_mode": "vertical",
            "show_velocity_arrow": True,
            "show_trail": True
        },
        "objects": objs,
        "preferred_observe_object": "ball1",
        "preferred_curves": ["vx", "speed", "kinetic_energy"]
    }

ALL_TEMPLATES = [
    tpl_free_fall,
    tpl_projectile_motion,
    tpl_elastic_collision,
    tpl_mass_collision,
    tpl_inelastic_collision,
    tpl_spring_oscillator,
    tpl_spring_coupled,
    tpl_groove_ball,
    tpl_double_pendulum,
    tpl_newtons_cradle
]
