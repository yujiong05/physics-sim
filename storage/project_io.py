import json
import numpy as np
from core.models import Ball, Block, Spring


def save_project(path, engine, counters, scene_data):
    data = {
        "engine": {
            "time": float(engine.time),
            "gravity": engine.gravity.tolist(),
            "bounds": list(engine.bounds),
            "experiment_mode": scene_data.get("experiment_mode", "vertical"),
        },
        "scene": scene_data,
        "counters": counters,
        "objects": []
    }

    for obj in engine.objects:
        if hasattr(obj, 'get_state'):
            data["objects"].append(obj.get_state())

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_project(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    engine_data = data.get("engine", {})
    scene_data  = data.get("scene", {"show_velocity_arrow": False, "show_trail": False})
    
    counters = data.get("counters", {"ball": data.get("ball_counter", 1), "block": 1, "spring": 1})

    # 若旧文件 scene 里没有 experiment_mode，根据 gravity 推断
    if "experiment_mode" not in scene_data:
        grav = engine_data.get("gravity", [0.0, 980.0])
        scene_data["experiment_mode"] = "horizontal" if grav[1] == 0.0 else "vertical"

    objects = []
    for obj_data in data.get("objects", []):
        t = obj_data.get("type")
        if t == "ball":
            objects.append(Ball.from_state(obj_data))
        elif t == "block":
            objects.append(Block.from_state(obj_data))
        elif t == "spring":
            objects.append(Spring.from_state(obj_data))

    return engine_data, objects, counters, scene_data
