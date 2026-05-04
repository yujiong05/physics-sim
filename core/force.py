import math
import numpy as np

class AppliedForce:
    def __init__(self, target_id, magnitude, angle_deg, duration):
        self.target_id = target_id
        self.magnitude = magnitude
        self.angle_deg = angle_deg
        self.duration = duration
        self.elapsed = 0.0
        
        angle_rad = math.radians(angle_deg)
        self.force_vector = np.array([
            magnitude * math.cos(angle_rad),
            magnitude * math.sin(angle_rad)
        ], dtype=np.float64)
