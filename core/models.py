import numpy as np
import math
import uuid

class PhysicalObject:
    def __init__(self, x, y, mass=1.0, name="Object"):
        self.id = uuid.uuid4().hex
        self.name = name
        self.pos = np.array([x, y], dtype=np.float64)
        self.vel = np.array([0.0, 0.0], dtype=np.float64)
        self.acc = np.array([0.0, 0.0], dtype=np.float64)
        self.mass = max(0.1, mass)
        self.restitution = 0.8
        self.friction = 0.0
        self.color = "#6496ff"

class Ball(PhysicalObject):
    def __init__(self, x, y, radius=20, mass=1.0, name="Ball"):
        super().__init__(x, y, mass, name)
        self.radius = radius

    def get_state(self):
        return {
            "type": "ball",
            "id": self.id,
            "name": self.name,
            "pos": self.pos.tolist(),
            "vel": self.vel.tolist(),
            "acc": self.acc.tolist(),
            "mass": float(self.mass),
            "radius": float(self.radius),
            "restitution": float(self.restitution),
            "friction": float(self.friction),
            "color": self.color,
        }

    @classmethod
    def from_state(cls, data):
        pos = data.get("pos", [0.0, 0.0])
        ball = cls(x=pos[0], y=pos[1], radius=data.get("radius", 20.0),
                   mass=data.get("mass", 1.0), name=data.get("name", "Ball"))
        ball.id = data.get("id", uuid.uuid4().hex)
        ball.vel = np.array(data.get("vel", [0.0, 0.0]), dtype=np.float64)
        ball.acc = np.array(data.get("acc", [0.0, 0.0]), dtype=np.float64)
        ball.restitution = data.get("restitution", 0.8)
        ball.friction = data.get("friction", 0.0)
        ball.color = data.get("color", "#6496ff")
        return ball

class Block(PhysicalObject):
    def __init__(self, x, y, width=40.0, height=40.0, mass=1.0, name="Block"):
        super().__init__(x, y, mass, name)
        self.width = width
        self.height = height

    def get_state(self):
        return {
            "type": "block",
            "id": self.id,
            "name": self.name,
            "pos": self.pos.tolist(),
            "vel": self.vel.tolist(),
            "acc": self.acc.tolist(),
            "mass": float(self.mass),
            "width": float(self.width),
            "height": float(self.height),
            "restitution": float(self.restitution),
            "friction": float(self.friction),
            "color": self.color,
        }

    @classmethod
    def from_state(cls, data):
        pos = data.get("pos", [0.0, 0.0])
        block = cls(x=pos[0], y=pos[1], width=data.get("width", 40.0),
                    height=data.get("height", 40.0), mass=data.get("mass", 1.0),
                    name=data.get("name", "Block"))
        block.id = data.get("id", uuid.uuid4().hex)
        block.vel = np.array(data.get("vel", [0.0, 0.0]), dtype=np.float64)
        block.acc = np.array(data.get("acc", [0.0, 0.0]), dtype=np.float64)
        block.restitution = data.get("restitution", 0.8)
        block.friction = data.get("friction", 0.0)
        block.color = data.get("color", "#64c896")
        return block

class Spring:
    def __init__(self, start_pos, end_pos, stiffness=200.0, damping=5.0,
                 rest_length=None, name="Spring", color="#ffa040"):
        self.id = uuid.uuid4().hex
        self.name = name
        self.start_pos = np.array(start_pos, dtype=np.float64)
        self.end_pos   = np.array(end_pos,   dtype=np.float64)
        self.stiffness = stiffness
        self.damping   = damping
        if rest_length is None:
            rest_length = float(np.linalg.norm(self.end_pos - self.start_pos))
        self.rest_length = rest_length
        self.color = color
        
        # 绑定属性
        self.start_body_id = None
        self.end_body_id = None
        self.start_local_offset = np.array([0.0, 0.0], dtype=np.float64)
        self.end_local_offset = np.array([0.0, 0.0], dtype=np.float64)

    def get_state(self):
        return {
            "type": "spring",
            "id": self.id,
            "name": self.name,
            "start_pos": self.start_pos.tolist(),
            "end_pos":   self.end_pos.tolist(),
            "stiffness": float(self.stiffness),
            "damping":   float(self.damping),
            "rest_length": float(self.rest_length),
            "color": self.color,
            "start_body_id": self.start_body_id,
            "end_body_id": self.end_body_id,
            "start_local_offset": self.start_local_offset.tolist(),
            "end_local_offset": self.end_local_offset.tolist(),
        }

    @classmethod
    def from_state(cls, data):
        spring = cls(
            start_pos   = data.get("start_pos", [0.0, 0.0]),
            end_pos     = data.get("end_pos",   [100.0, 0.0]),
            stiffness   = data.get("stiffness", 200.0),
            damping     = data.get("damping",   5.0),
            rest_length = data.get("rest_length", None),
            name        = data.get("name", "Spring"),
            color       = data.get("color", "#ffa040")
        )
        spring.id = data.get("id", uuid.uuid4().hex)
        spring.start_body_id = data.get("start_body_id")
        spring.end_body_id = data.get("end_body_id")
        spring.start_local_offset = np.array(data.get("start_local_offset", [0.0, 0.0]), dtype=np.float64)
        spring.end_local_offset = np.array(data.get("end_local_offset", [0.0, 0.0]), dtype=np.float64)
        return spring

class StaticBlock:
    def __init__(self, x, y, width=100.0, height=20.0, angle=0.0, name="StaticBlock"):
        self.id = uuid.uuid4().hex
        self.type = "static_block"
        self.name = name
        self.pos = np.array([x, y], dtype=np.float64)
        self.width = width
        self.height = height
        self.angle = angle
        self.restitution = 0.8
        self.friction = 0.2
        self.color = "#808080"
        self.static = True

    def get_state(self):
        return {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "pos": self.pos.tolist(),
            "width": float(self.width),
            "height": float(self.height),
            "angle": float(self.angle),
            "restitution": float(self.restitution),
            "friction": float(self.friction),
            "color": self.color,
            "static": self.static
        }

    @classmethod
    def from_state(cls, data):
        pos = data.get("pos", [0.0, 0.0])
        block = cls(x=pos[0], y=pos[1], width=data.get("width", 100.0),
                    height=data.get("height", 20.0), angle=data.get("angle", 0.0),
                    name=data.get("name", "StaticBlock"))
        block.id = data.get("id", uuid.uuid4().hex)
        block.restitution = data.get("restitution", 0.8)
        block.friction = data.get("friction", 0.2)
        block.color = data.get("color", "#808080")
        return block

class Groove:
    def __init__(self, x, y, radius=150.0, thickness=20.0, name="Groove", fixed=True):
        self.id = uuid.uuid4().hex
        self.type = "groove"
        self.name = name
        self.center_pos = np.array([x, y], dtype=np.float64)
        self.radius = radius
        self.thickness = thickness
        self.start_angle = 0.0
        self.end_angle = 180.0
        self.restitution = 0.8
        self.friction = 0.2
        self.color = "#808080"
        
        self.fixed = fixed
        self.static = fixed
        self.mass = 10.0
        self.vel = np.array([0.0, 0.0], dtype=np.float64)
        self.acc = np.array([0.0, 0.0], dtype=np.float64)

    @property
    def pos(self):
        # Alias for compatibility with scene placement/selection logic
        return self.center_pos

    @pos.setter
    def pos(self, value):
        self.center_pos = np.array(value, dtype=np.float64)

    def get_state(self):
        return {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "center_pos": self.center_pos.tolist(),
            "radius": float(self.radius),
            "thickness": float(self.thickness),
            "start_angle": float(self.start_angle),
            "end_angle": float(self.end_angle),
            "restitution": float(self.restitution),
            "friction": float(self.friction),
            "color": self.color,
            "static": self.static,
            "fixed": self.fixed,
            "mass": float(self.mass),
            "vel": self.vel.tolist(),
            "acc": self.acc.tolist()
        }

    @classmethod
    def from_state(cls, data):
        c_pos = data.get("center_pos", [0.0, 0.0])
        fixed = data.get("fixed", data.get("static", True))
        groove = cls(x=c_pos[0], y=c_pos[1], radius=data.get("radius", 150.0),
                     thickness=data.get("thickness", 20.0), name=data.get("name", "Groove"),
                     fixed=fixed)
        groove.id = data.get("id", uuid.uuid4().hex)
        groove.start_angle = data.get("start_angle", 0.0)
        groove.end_angle = data.get("end_angle", 180.0)
        groove.restitution = data.get("restitution", 0.8)
        groove.friction = data.get("friction", 0.2)
        groove.color = data.get("color", "#808080")
        groove.mass = data.get("mass", 10.0)
        groove.vel = np.array(data.get("vel", [0.0, 0.0]), dtype=np.float64)
        groove.acc = np.array(data.get("acc", [0.0, 0.0]), dtype=np.float64)
        groove.static = groove.fixed
        return groove
