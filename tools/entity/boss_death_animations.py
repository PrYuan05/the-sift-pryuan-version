"""Write the 3-second boss death animations (animation.<id>.death) into the GeckoLib animation files.
Usage: python -I tools/entity/boss_death_animations.py <project>
Length must match BossMechanics.DEATH_TICKS (60 ticks = 3.0 s); the server keeps the body until it ends.
Only the "death" entry of each file is replaced; every other animation is left untouched.
Keyframes: {bone: {channel: [(time, [x, y, z]), ...]}}, rotation in degrees, position in model pixels."""
import json, sys
from pathlib import Path

P = Path(sys.argv[1])
A = P / "src/main/resources/assets/pysift/geckolib/animations/entity"
LENGTH = 3.0
Z = [0, 0, 0]
ONE = [1, 1, 1]

# ---- Sculk Monstrosity: roars to the sky, staggers, drops to its knees bracing on one arm, then topples sideways.
#      Impact at 2.2 s (SculkMonstrosityEntity impact tick 44). Eyes and shoulder flames fade out.
SCULK = {
    "root": {"rotation": [(0, Z), (0.25, [-10, 0, 0]), (0.6, [4, 0, -3]), (0.9, [10, 0, 4]), (1.2, [14, 0, 0]),
                          (1.8, [16, 0, -6]), (2.2, [0, 0, 85]), (2.35, [0, 0, 80]), (2.5, [0, 0, 85]), (3.0, [0, 0, 85])],
             "position": [(0, Z), (0.9, Z), (1.2, [0, -9, 0]), (1.8, [0, -9, 0]), (2.2, [8, -6, 0]), (3.0, [8, -6, 0])]},
    "right_leg": {"rotation": [(0, Z), (0.9, Z), (1.2, [-70, 0, 0]), (1.8, [-70, 0, 0]), (2.2, [-30, 0, 0]), (3.0, [-30, 0, 0])]},
    "left_leg": {"rotation": [(0, Z), (0.9, Z), (1.2, [-60, 0, 0]), (1.8, [-60, 0, 0]), (2.2, [-15, 0, 0]), (3.0, [-15, 0, 0])]},
    "head": {"rotation": [(0, Z), (0.25, [-40, 0, 0]), (0.6, [-35, 0, 0]), (0.9, [10, 0, 8]), (1.8, [15, 0, -5]),
                          (2.2, [20, 0, 0]), (3.0, [20, 0, 0])]},
    "jaw": {"rotation": [(0, Z), (0.25, [35, 0, 0]), (0.7, [35, 0, 0]), (1.0, [10, 0, 0]), (2.2, [30, 0, 0]), (3.0, [30, 0, 0])]},
    "right_arm": {"rotation": [(0, Z), (0.25, [-70, 0, 25]), (0.6, [-60, 0, 20]), (0.9, [10, 0, 10]), (1.2, [-30, 0, 5]),
                               (1.8, [-30, 0, 5]), (2.2, [-40, 0, 20]), (3.0, [-40, 0, 20])]},
    "left_arm": {"rotation": [(0, Z), (0.25, [-70, 0, -25]), (0.6, [-60, 0, -20]), (0.9, [20, 0, -15]), (1.2, [25, 0, -20]),
                              (2.2, [-20, 0, -30]), (3.0, [-20, 0, -30])]},
    "eye_glow": {"scale": [(0, ONE), (1.8, ONE), (2.8, [0.01, 0.01, 0.01]), (3.0, [0.01, 0.01, 0.01])]},
    "shoulder_flame_right": {"scale": [(0, ONE), (1.0, ONE), (2.6, [0.05, 0.05, 0.05]), (3.0, [0.05, 0.05, 0.05])]},
    "shoulder_flame_left": {"scale": [(0, ONE), (1.0, ONE), (2.6, [0.05, 0.05, 0.05]), (3.0, [0.05, 0.05, 0.05])]},
}

# ---- Harmonizer: shudders with flailing tentacles, rises a little, then sinks limply to the ground.
#      Impact at 2.6 s (HarmonizerEntity impact tick 52).
HARMONIZER = {
    "body": {"position": [(0, Z), (0.3, [0, 2, 0]), (0.8, [0, 4, 0]), (1.4, [0, 3, 0]), (2.6, [0, -14, 0]),
                          (2.75, [0, -12.5, 0]), (3.0, [0, -14, 0])],
             "rotation": [(0, Z), (0.1, [0, 0, 6]), (0.2, [0, 0, -6]), (0.3, [0, 0, 5]), (0.4, [0, 0, -4]), (0.6, [0, 0, 3]),
                          (0.8, [-10, 0, 0]), (1.4, [-5, 0, -8]), (2.6, [20, 0, 15]), (3.0, [20, 0, 15])]},
    "head": {"rotation": [(0, Z), (0.3, [-25, 0, 0]), (0.8, [-35, 0, 0]), (1.4, [-10, 0, 0]), (2.6, [30, 0, 0]), (3.0, [30, 0, 0])]},
}
for i in range(1, 9):
    s = 1 if i % 2 else -1
    HARMONIZER[f"tentacle_{i}"] = {"rotation": [(0, Z), (0.15, [0, 0, 25 * s]), (0.3, [0, 0, -25 * s]), (0.45, [0, 0, 20 * s]),
                                                (0.6, [0, 0, -15 * s]), (0.8, [0, 0, 30]), (1.4, [0, 0, 20]),
                                                (2.6, [0, 0, 40]), (3.0, [0, 0, 40])]}
    HARMONIZER[f"tentacle_{i}_seg1"] = {"rotation": [(0, Z), (0.8, [-20, 0, 0]), (1.4, [-10, 0, 0]), (2.6, [15, 0, 0]),
                                                     (3.0, [15, 0, 0])]}

# ---- Monarch: recoils, staggers, sinks to one knee with the head bowed, the crown slips off, then falls backwards.
#      Impact at 2.5 s (MonarchEntity impact tick 50).
MONARCH = {
    "root": {"rotation": [(0, Z), (0.2, [8, 0, 0]), (0.5, [-12, 0, 5]), (0.8, [6, 0, -4]), (1.1, [20, 0, 0]),
                          (1.8, [22, 0, 0]), (2.1, [15, 0, 0]), (2.5, [-85, 0, 0]), (2.65, [-80, 0, 0]),
                          (2.8, [-85, 0, 0]), (3.0, [-85, 0, 0])],
             "position": [(0, Z), (0.8, Z), (1.1, [0, -8, 0]), (2.1, [0, -8, 0]), (2.5, [0, 1, 8]), (3.0, [0, 1, 8])]},
    "body": {"rotation": [(0, Z), (0.8, Z), (1.1, [10, 0, 0]), (2.1, [15, 0, 0]), (2.5, Z), (3.0, Z)]},
    "right_leg": {"rotation": [(0, Z), (0.8, Z), (1.1, [-70, 0, 5]), (2.1, [-70, 0, 5]), (2.5, [-20, 0, 0]), (3.0, [-20, 0, 0])]},
    "left_leg": {"rotation": [(0, Z), (0.8, Z), (1.1, [-15, 0, -5]), (2.1, [-15, 0, -5]), (2.5, [-10, 0, 0]), (3.0, [-10, 0, 0])]},
    "head": {"rotation": [(0, Z), (0.2, [15, 0, 0]), (0.5, [-25, 0, 0]), (1.1, [25, 0, 0]), (2.1, [30, 0, 0]),
                          (2.5, [-20, 0, 0]), (3.0, [-20, 0, 0])]},
    "crown": {"rotation": [(0, Z), (1.6, Z), (2.0, [-20, 0, 25]), (2.5, [-30, 0, 40]), (3.0, [-30, 0, 40])],
              "position": [(0, Z), (1.6, Z), (2.0, [-2, -1, -2]), (2.5, [-4, -3, -4]), (3.0, [-4, -3, -4])]},
    "cape": {"rotation": [(0, Z), (0.5, [10, 0, 0]), (1.1, [15, 0, 0]), (2.1, [15, 0, 0]), (2.5, [-30, 0, 0]), (3.0, [-30, 0, 0])]},
}


def bones_of(entity_id):
    geo = json.loads((P / f"src/main/resources/assets/pysift/geckolib/models/entity/{entity_id}.geo.json").read_text(encoding="utf-8"))
    return {b["name"] for b in geo["minecraft:geometry"][0]["bones"]}


for entity_id, keys in (("sculk_monstrosity", SCULK), ("harmonizer", HARMONIZER), ("monarch", MONARCH)):
    missing = set(keys) - bones_of(entity_id)
    assert not missing, f"{entity_id}: bones not in model: {sorted(missing)}"
    f = A / f"{entity_id}.animation.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    name = f"animation.{entity_id}.death"
    assert name in data["animations"], name
    data["animations"][name] = {"loop": "hold_on_last_frame", "animation_length": LENGTH, "bones": {
        bone: {ch: {f"{t:g}" if t % 1 else f"{t:.1f}": v for t, v in frames} for ch, frames in chans.items()}
        for bone, chans in keys.items()}}
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{entity_id}: death {LENGTH}s, {len(keys)} bones")
