"""
templates/experiment_templates.py
预设实验模板，每个模板返回与 JSON 保存格式兼容的数据字典。
"""


def _engine_defaults(gravity=None):
    return {
        "time": 0.0,
        "gravity": gravity or [0.0, 980.0],
        "bounds": [0, 0, 800, 600]
    }


def _ball(name, x, y, vx=0.0, vy=0.0, radius=20.0, mass=1.0, restitution=0.8):
    return {
        "type": "ball",
        "name": name,
        "pos": [float(x), float(y)],
        "vel": [float(vx), float(vy)],
        "acc": [0.0, 0.0],
        "mass": float(mass),
        "radius": float(radius),
        "restitution": float(restitution)
    }


def _block(name, x, y, vx=0.0, vy=0.0, width=60.0, height=60.0, mass=1.0, restitution=0.8):
    return {
        "type": "block",
        "name": name,
        "pos": [float(x), float(y)],
        "vel": [float(vx), float(vy)],
        "acc": [0.0, 0.0],
        "mass": float(mass),
        "width": float(width),
        "height": float(height),
        "restitution": float(restitution)
    }


# ──────────────────────────────────────────────────────────
# 1. 自由落体实验
# ──────────────────────────────────────────────────────────
def free_fall():
    return {
        "name": "自由落体实验",
        "engine": _engine_defaults(),
        "ball_counter": 2,
        "scene": {"show_velocity_arrow": True, "show_trail": True},
        "objects": [
            _ball("Ball_1", x=400, y=80, vx=0, vy=0, radius=22, mass=1.0, restitution=0.6)
        ]
    }


# ──────────────────────────────────────────────────────────
# 2. 平抛运动实验
# ──────────────────────────────────────────────────────────
def projectile_motion():
    return {
        "name": "平抛运动实验",
        "engine": _engine_defaults(),
        "ball_counter": 2,
        "scene": {"show_velocity_arrow": True, "show_trail": True},
        "objects": [
            _ball("Ball_1", x=80, y=100, vx=400, vy=0, radius=18, mass=1.0, restitution=0.5)
        ]
    }


# ──────────────────────────────────────────────────────────
# 3. 双球弹性碰撞实验
# ──────────────────────────────────────────────────────────
def elastic_collision():
    return {
        "name": "双球弹性碰撞实验",
        "engine": _engine_defaults(),
        "ball_counter": 3,
        "scene": {"show_velocity_arrow": True, "show_trail": True},
        "objects": [
            _ball("Ball_1", x=180, y=300, vx=350, vy=0, radius=22, mass=1.0, restitution=1.0),
            _ball("Ball_2", x=550, y=300, vx=0,   vy=0, radius=22, mass=1.0, restitution=1.0),
        ]
    }


# ──────────────────────────────────────────────────────────
# 4. 轻重球碰撞实验
# ──────────────────────────────────────────────────────────
def mass_collision():
    return {
        "name": "轻重球碰撞实验",
        "engine": _engine_defaults(),
        "ball_counter": 3,
        "scene": {"show_velocity_arrow": True, "show_trail": True},
        "objects": [
            _ball("Light_1", x=160, y=300, vx=400,  vy=0, radius=16, mass=1.0,  restitution=1.0),
            _ball("Heavy_2", x=520, y=300, vx=-200, vy=0, radius=30, mass=10.0, restitution=1.0),
        ]
    }


# ──────────────────────────────────────────────────────────
# 5. 方块碰撞实验
# ──────────────────────────────────────────────────────────
def block_collision():
    return {
        "name": "方块碰撞实验",
        "engine": _engine_defaults(),
        "ball_counter": 3,
        "scene": {"show_velocity_arrow": True, "show_trail": False},
        "objects": [
            _block("Block_1", x=160, y=300, vx=350, vy=0, width=60, height=60, mass=2.0, restitution=0.8),
            _block("Block_2", x=580, y=300, vx=-200, vy=0, width=70, height=70, mass=3.0, restitution=0.8),
        ]
    }


# ──────────────────────────────────────────────────────────
# 6. 球撞方块实验
# ──────────────────────────────────────────────────────────
def ball_hits_block():
    return {
        "name": "球撞方块实验",
        "engine": _engine_defaults(),
        "ball_counter": 3,
        "scene": {"show_velocity_arrow": True, "show_trail": True},
        "objects": [
            _ball("Ball_1",   x=100, y=300, vx=500, vy=0, radius=20, mass=1.0, restitution=0.9),
            _block("Block_2", x=560, y=300, vx=0,   vy=0, width=80, height=80, mass=8.0, restitution=0.7),
        ]
    }


# ──────────────────────────────────────────────────────────
# 所有模板注册表（用于菜单生成）
# ──────────────────────────────────────────────────────────
ALL_TEMPLATES = [
    free_fall,
    projectile_motion,
    elastic_collision,
    mass_collision,
    block_collision,
    ball_hits_block,
]
