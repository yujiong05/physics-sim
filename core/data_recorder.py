import math
from core.models import Ball, Block, Spring

class DataRecorder:
    def __init__(self, max_records=5000):
        self.max_records = max_records
        self.records = {}  # {object_id: [dict, ...]}

    def clear_all(self):
        self.records.clear()

    def clear_object(self, obj_id):
        if obj_id in self.records:
            self.records[obj_id].clear()

    def remove_object(self, obj_id):
        if obj_id in self.records:
            del self.records[obj_id]

    def record(self, current_time, objects, engine):
        scene_height = engine.bounds[3]

        for obj in objects:
            if obj.id not in self.records:
                self.records[obj.id] = []

            data = {"time": current_time}

            if isinstance(obj, (Ball, Block)):
                data["x"] = obj.pos[0]
                data["y"] = obj.pos[1]
                data["vx"] = obj.vel[0]
                data["vy"] = obj.vel[1]
                data["speed"] = math.hypot(obj.vel[0], obj.vel[1])
                data["ax"] = obj.acc[0]
                data["ay"] = obj.acc[1]
                data["mass"] = obj.mass
                data["kinetic_energy"] = 0.5 * obj.mass * data["speed"]**2
                
                h = scene_height - obj.pos[1]
                g_y = engine.gravity[1] if engine.gravity[1] > 0 else 0.0
                data["potential_energy"] = obj.mass * g_y * h

            elif isinstance(obj, Spring):
                dx = obj.end_pos[0] - obj.start_pos[0]
                dy = obj.end_pos[1] - obj.start_pos[1]
                curr_len = math.hypot(dx, dy)
                ext = curr_len - obj.rest_length
                
                data["current_length"] = curr_len
                data["rest_length"] = obj.rest_length
                data["extension"] = ext
                data["spring_energy"] = 0.5 * obj.stiffness * (ext ** 2)

            self.records[obj.id].append(data)
            if len(self.records[obj.id]) > self.max_records:
                self.records[obj.id].pop(0)

    def get_data(self, obj_id):
        return self.records.get(obj_id, [])
