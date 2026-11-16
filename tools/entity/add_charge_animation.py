"""Add an "animation.<entity>.charge" to entities that use ChargeGoal (Dartback, Sculk Monstrosity).
Usage: python -I tools/entity/add_charge_animation.py <project>

The animation matches the goal's timing (wind-up, dash, recover in ticks, see the entity class):
  wind-up : the lean bone tips back and the head drops (bracing to charge)
  dash    : the walk cycle played at DASH_SPEED x, repeated, with the lean bone tipped forward
  recover : back to neutral
The lean bone is the first of LEAN_BONES that the walk animation does not already animate (so the two do not fight).
Re-running replaces the charge animation."""
import json, sys
from pathlib import Path

P = Path(sys.argv[1])
GL = P / "src/main/resources/assets/pysift/geckolib"
# entity: (wind-up ticks, dash ticks, recover ticks) — keep in sync with the ChargeGoal in the entity class
TIMING = {"dartback": (15, 20, 15), "sculk_monstrosity": (20, 24, 25)}
LEAN_BONES = ["root", "hip", "body"]
DASH_SPEED = 2.0
LEAN_BACK, LEAN_FORWARD = 12.0, -18.0


def lj(p): return json.loads(p.read_text(encoding="utf-8"))


def frames_value(spec, t):
    """Value of a keyframed channel at time t (linear between keys); spec is a dict time -> vec or a constant."""
    if isinstance(spec, list):
        return spec
    keys = sorted((float(k), v["post"] if isinstance(v, dict) else v) for k, v in spec.items())
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            return [a + (b - a) * f if isinstance(a, (int, float)) and isinstance(b, (int, float)) else b
                    for a, b in zip(v0, v1)]
    return keys[-1][1]


for entity, (wind, dash, recover) in TIMING.items():
    path = GL / f"animations/entity/{entity}.animation.json"
    anims = lj(path)
    walk = anims["animations"][f"animation.{entity}.walk"]
    walk_len = float(walk["animation_length"])
    t_dash, t_rec, t_end = wind / 20, (wind + dash) / 20, (wind + dash + recover) / 20
    bones = {}
    # walk cycle at DASH_SPEED during the dash, sampled every 0.05 s
    step = 0.05
    for bone, channels in walk["bones"].items():
        out = {}
        for channel, spec in channels.items():
            keys = {}
            t = t_dash
            while t <= t_rec + 1e-6:
                local = ((t - t_dash) * DASH_SPEED) % walk_len
                keys[f"{round(t, 3)}"] = [round(v, 3) for v in frames_value(spec, local)]
                t += step
            zero = [0, 0, 0] if channel != "scale" else [1, 1, 1]
            keys.setdefault("0.0", zero)
            keys[f"{round(t_dash - step, 3)}"] = zero
            keys[f"{round(t_end, 3)}"] = zero
            out[channel] = dict(sorted(keys.items(), key=lambda kv: float(kv[0])))
        bones[bone] = out
    lean = next(b for b in LEAN_BONES if b not in walk["bones"])
    bones[lean] = {"rotation": {"0.0": [0, 0, 0], f"{round(t_dash * 0.8, 3)}": [LEAN_BACK, 0, 0],
                                f"{round(t_dash + 0.1, 3)}": [LEAN_FORWARD, 0, 0], f"{round(t_rec, 3)}": [LEAN_FORWARD, 0, 0],
                                f"{round(t_end, 3)}": [0, 0, 0]}}
    anims["animations"][f"animation.{entity}.charge"] = {"animation_length": round(t_end, 3), "bones": bones}
    path.write_text(json.dumps(anims, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{entity}: charge {t_end}s, lean bone {lean}, {len(bones)} bones")
