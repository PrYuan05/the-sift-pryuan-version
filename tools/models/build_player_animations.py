"""Player animations for item use, played by Player Animation Library (client/PlayerAnims.java).
Usage: python -I tools/models/build_player_animations.py <project>

Writes assets/pysift/player_animations/weapons.json (GeckoLib / Bedrock animation format, one file, one animation per
state). Bones: body (the whole player), torso, head, right_arm, left_arm, right_leg, left_leg.

Conventions used here (degrees; the same signs as the vanilla player model):
  arm x  : negative raises the arm forward, -180 points it straight up, positive swings it back
  arm z  : right arm positive / left arm negative opens the arm away from the body
  body x : positive leans forward, negative leans back;  body y: turns;  body position y: negative sinks (crouch)
  leg x  : negative kicks forward, positive back

Every pose is written as a dict of bones; a clip is a list of (time, pose, easing). The principles are the usual ones
for readable, exaggerated motion: anticipation (wind up the other way first), overshoot (easeOutBack / elastic),
squash on impact (sink the body, bend the legs) and a slow settle."""
import json
import sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
OUT = P / "src/main/resources/assets/pysift/player_animations/weapons.json"

REST = {"body": [0, 0, 0], "body_pos": [0, 0, 0], "torso": [0, 0, 0], "head": [0, 0, 0],
        "right_arm": [0, 0, 0], "left_arm": [0, 0, 0], "right_leg": [0, 0, 0], "left_leg": [0, 0, 0]}


def pose(**bones):
    out = dict(REST)
    out.update(bones)
    return out


def settle(frames, overshoot=0.18, extra=0.22):
    """Follow-through for a one-shot action (後搖): instead of stopping dead at the rest pose, the body swings a little
    past it the other way and eases back. The last frame must be the rest pose; the pose before it sets the direction."""
    *body, (t_end, last, _) = frames
    before = body[-1][1]
    past = {k: [-v * overshoot for v in before[k]] for k in REST}
    return body + [(t_end, past, "easeOutQuad"), (t_end + extra, REST, "easeInOutSine")]


def clip(name, frames, loop=None, length=None):
    """frames: [(time, pose, easing)] -> one animation; channels that never leave the rest pose are left out.
    One-shot clips (no loop) that end at rest get a follow-through (settle)."""
    if loop is None and frames[-1][1] == REST and len(frames) >= 3:
        frames = settle(frames)
    bones = {}
    for key in REST:
        values = [(t, p[key], e) for t, p, e in frames]
        if all(v == [0, 0, 0] for _, v, _ in values):
            continue
        bone, channel = (key[:-4], "position") if key.endswith("_pos") else (key, "rotation")
        track = {}
        for t, v, e in values:
            frame = {"vector": v}
            if e != "linear":
                frame["easing"] = e
            track[f"{t:.4f}".rstrip("0").rstrip(".") if t else "0.0"] = frame
        bones.setdefault(bone, {})[channel] = track
    anim = {"animation_length": length if length is not None else frames[-1][0], "bones": bones}
    if loop is not None:
        anim["loop"] = loop
    return name, anim


def mirror(p):
    """The same pose for the other hand: swap left and right, flip the y and z rotations."""
    flip = lambda v: [v[0], -v[1], -v[2]]
    return {"body": flip(p["body"]), "body_pos": [-p["body_pos"][0], p["body_pos"][1], p["body_pos"][2]],
            "torso": flip(p["torso"]), "head": flip(p["head"]),
            "right_arm": flip(p["left_arm"]), "left_arm": flip(p["right_arm"]),
            "right_leg": flip(p["left_leg"]), "left_leg": flip(p["right_leg"])}


ANIMS = []

# ------------------------------------------------------------------ sculk hammer
# charge: a dip first (anticipation), then both arms haul the hammer up and behind the head while the back arches
H_DIP = pose(body=[14, 0, 0], body_pos=[0, -1.5, 0], right_arm=[-35, -20, 0], left_arm=[-35, 20, 0],
             right_leg=[-12, 0, 0], left_leg=[10, 0, 0], head=[-8, 0, 0])
H_UP = pose(body=[-10, 0, 0], body_pos=[0, 0.5, 0], right_arm=[-165, -18, 0], left_arm=[-165, 18, 0],
            right_leg=[8, 0, 0], left_leg=[-6, 0, 0], head=[14, 0, 0])
H_FULL = pose(body=[-22, 0, 0], body_pos=[0, 1.0, 0], right_arm=[-205, -14, 0], left_arm=[-205, 14, 0],
              right_leg=[14, 0, 0], left_leg=[-10, 0, 0], head=[24, 0, 0])
ANIMS.append(clip("hammer_charge", [
    (0.0, REST, "linear"), (0.18, H_DIP, "easeOutQuad"), (0.75, H_UP, "easeOutBack"), (2.0, H_FULL, "easeInOutSine"),
], loop="hold_on_last_frame"))

# fully charged: the whole body trembles under the weight
shake = []
for i in range(9):
    s = 1 if i % 2 == 0 else -1
    p = pose(body=[-22 + s * 1.5, s * 2.0, 0], body_pos=[s * 0.25, 1.0, 0], right_arm=[-205 + s * 3, -14, s * 2],
             left_arm=[-205 - s * 3, 14, s * 2], right_leg=[14, 0, 0], left_leg=[-10, 0, 0], head=[24 - s * 2, 0, 0])
    shake.append((i * 0.05, p, "easeInOutSine"))
ANIMS.append(clip("hammer_charged", shake, loop=True))

# slam: a last stretch up, then everything comes down at once - the body folds, the knees give, a bounce, a slow rise
H_HIT = pose(body=[58, 0, 0], body_pos=[0, -5.0, -1.0], right_arm=[-28, -12, 0], left_arm=[-28, 12, 0],
             right_leg=[-52, 0, 0], left_leg=[38, 0, 0], head=[-30, 0, 0])
H_BOUNCE = pose(body=[44, 0, 0], body_pos=[0, -3.2, -0.6], right_arm=[-46, -12, 0], left_arm=[-46, 12, 0],
                right_leg=[-40, 0, 0], left_leg=[28, 0, 0], head=[-18, 0, 0])
ANIMS.append(clip("hammer_slam", [
    (0.0, H_FULL, "linear"), (0.07, pose(body=[-30, 0, 0], body_pos=[0, 2.0, 0], right_arm=[-215, -14, 0],
                                         left_arm=[-215, 14, 0], right_leg=[18, 0, 0], left_leg=[-12, 0, 0], head=[30, 0, 0]), "easeOutQuad"),
    (0.17, H_HIT, "easeInCubic"), (0.27, H_BOUNCE, "easeOutQuad"), (0.36, H_HIT, "easeInQuad"),
    (0.62, pose(body=[26, 0, 0], body_pos=[0, -2.0, 0], right_arm=[-30, -8, 0], left_arm=[-30, 8, 0],
                right_leg=[-22, 0, 0], left_leg=[14, 0, 0], head=[-8, 0, 0]), "easeInOutSine"),
    (0.95, REST, "easeInOutSine"),
]))

# left-click swings: a diagonal chop from one shoulder to the opposite hip, with the whole body turning through it
SW_UP = pose(body=[-12, -34, 0], body_pos=[0, 0.5, 0], right_arm=[-170, -30, 12], left_arm=[-150, 40, -6],
             right_leg=[10, 0, 0], left_leg=[-12, 0, 0], head=[8, 26, 0])
SW_DOWN = pose(body=[34, 42, 0], body_pos=[0, -2.5, 0], right_arm=[-22, 38, 0], left_arm=[-34, 62, 0],
               right_leg=[-34, 0, 0], left_leg=[24, 0, 0], head=[-14, -30, 0])
swing = [(0.0, REST, "linear"), (0.12, SW_UP, "easeOutCubic"), (0.26, SW_DOWN, "easeInCubic"),
         (0.34, pose(**{k: [x * 0.82 for x in v] for k, v in SW_DOWN.items()}), "easeOutQuad"), (0.6, REST, "easeInOutSine")]
ANIMS.append(clip("hammer_swing_right", swing))
ANIMS.append(clip("hammer_swing_left", [(t, mirror(p), e) for t, p, e in swing]))

# ------------------------------------------------------------------ sonic staff
# cast: the staff arm climbs to the sky, the other hand reaches out, the caster rises on the toes and leans back
C_UP = pose(body=[-8, 0, 0], body_pos=[0, 0.8, 0], right_arm=[-190, 0, 16], left_arm=[-82, 24, 0],
            right_leg=[4, 0, 0], left_leg=[-10, 0, 0], head=[18, 0, 0])
ANIMS.append(clip("staff_cast", [
    (0.0, REST, "linear"),
    (0.12, pose(body=[10, 0, 0], body_pos=[0, -1.0, 0], right_arm=[-30, 0, 10], left_arm=[-10, 0, -8], head=[-6, 0, 0]), "easeOutQuad"),
    (0.6, C_UP, "easeOutBack"),
], loop="hold_on_last_frame"))
# blast: the staff whips down and forward, the body is thrown back by the recoil, then recovers
ANIMS.append(clip("staff_blast", [
    (0.0, C_UP, "linear"),
    (0.09, pose(body=[22, 0, 0], body_pos=[0, -1.5, -1.0], right_arm=[-86, 0, 6], left_arm=[-60, 30, 0],
                right_leg=[-26, 0, 0], left_leg=[22, 0, 0], head=[-12, 0, 0]), "easeInCubic"),
    (0.22, pose(body=[-16, 0, 0], body_pos=[0, -0.5, 2.0], right_arm=[-104, 0, 10], left_arm=[30, 20, -20],
                right_leg=[16, 0, 0], left_leg=[-24, 0, 0], head=[10, 0, 0]), "easeOutBack"),
    (0.7, REST, "easeInOutSine"),
]))
# thrust (left click): pull back, lunge, recover
ANIMS.append(clip("staff_thrust", [
    (0.0, REST, "linear"),
    (0.14, pose(body=[-8, -28, 0], right_arm=[-40, -30, 14], left_arm=[-50, 20, 0], right_leg=[12, 0, 0], left_leg=[-8, 0, 0], head=[0, 22, 0]), "easeOutQuad"),
    (0.26, pose(body=[26, 24, 0], body_pos=[0, -1.8, -2.5], right_arm=[-96, 22, 0], left_arm=[38, 10, -16],
                right_leg=[-40, 0, 0], left_leg=[30, 0, 0], head=[-16, -18, 0]), "easeInCubic"),
    (0.6, REST, "easeInOutSine"),
]))

# ------------------------------------------------------------------ tuning fork
# strike: flick the fork up beside the ear, snap it down against the other palm, then hold it out while it rings
# (a fast tremble that dies away), head tilted to listen
F_UP = pose(body=[-6, -14, 0], right_arm=[-150, -10, 18], left_arm=[-58, 30, 0], head=[6, 18, -10], left_leg=[-6, 0, 0])
F_HIT = pose(body=[14, 12, 0], body_pos=[0, -1.0, 0], right_arm=[-72, 34, 0], left_arm=[-64, -30, 0], head=[-8, -10, 6],
             right_leg=[-14, 0, 0], left_leg=[10, 0, 0])
F_HOLD = pose(body=[-4, 0, 0], right_arm=[-112, -8, 10], left_arm=[-20, 0, -10], head=[10, 14, -14])
fork = [(0.0, REST, "linear"), (0.14, F_UP, "easeOutBack"), (0.24, F_HIT, "easeInCubic"), (0.42, F_HOLD, "easeOutBack")]
for i in range(1, 9):                                        # the ringing: +-4 degrees fading to nothing over 0.8 s
    amp = 4.0 * (1 - i / 9) * (1 if i % 2 else -1)
    ring = pose(**{k: list(v) for k, v in F_HOLD.items()})
    ring["right_arm"] = [-112 + amp, -8, 10 + amp * 0.6]
    ring["head"] = [10, 14, -14 + amp * 0.5]
    fork.append((0.42 + i * 0.1, ring, "easeInOutSine"))
fork.append((1.6, REST, "easeInOutSine"))
ANIMS.append(clip("fork_strike", fork))

# ------------------------------------------------------------------ soul javelin
# charge: the throwing arm goes far back and up, the body twists away and leans back, the front arm points at the target
J_BACK = pose(body=[-14, -42, 0], body_pos=[0, -0.8, 1.0], right_arm=[-200, -30, 26], left_arm=[-88, 34, 0],
              right_leg=[20, 0, 0], left_leg=[-26, 0, 0], head=[6, 38, 0])
J_FULL = dict(J_BACK)
J_FULL.update(body=[-18, -48, 0], right_arm=[-208, -34, 30])
ANIMS.append(clip("javelin_charge", [
    (0.0, REST, "linear"),
    (0.12, pose(body=[8, 10, 0], right_arm=[-50, 10, 0], left_arm=[-20, 0, 0], head=[-4, -8, 0]), "easeOutQuad"),
    (0.55, J_BACK, "easeOutBack"),
    (1.4, J_FULL, "easeInOutSine"),
], loop="hold_on_last_frame"))
# throw: the whole body whips round and forward, the arm follows through past the hip, one step to catch the balance
ANIMS.append(clip("javelin_throw", [
    (0.0, J_BACK, "linear"),
    (0.1, pose(body=[36, 40, 0], body_pos=[0, -2.2, -2.5], right_arm=[-70, 30, 0], left_arm=[40, 20, -24],
               right_leg=[-46, 0, 0], left_leg=[34, 0, 0], head=[-20, -30, 0]), "easeInCubic"),
    (0.2, pose(body=[48, 52, 0], body_pos=[0, -3.0, -3.0], right_arm=[24, 44, 0], left_arm=[58, 20, -30],
               right_leg=[-54, 0, 0], left_leg=[40, 0, 0], head=[-26, -40, 0]), "easeOutQuad"),
    (0.34, pose(body=[30, 34, 0], body_pos=[0, -1.8, -1.5], right_arm=[10, 30, 0], left_arm=[30, 10, -16],
                right_leg=[-30, 0, 0], left_leg=[22, 0, 0], head=[-12, -24, 0]), "easeOutBack"),
    (0.7, REST, "easeInOutSine"),
]))

# ------------------------------------------------------------------ dash charm
# dash: a short crouch, then the body is thrown flat forward with both arms stabbing ahead and the legs trailing,
# and a skidding stop that leans back before standing up
ANIMS.append(clip("charm_dash", [
    (0.0, REST, "linear"),
    (0.05, pose(body=[20, 0, 0], body_pos=[0, -2.5, 0], right_arm=[40, 0, 10], left_arm=[40, 0, -10],
                right_leg=[-30, 0, 0], left_leg=[-30, 0, 0], head=[-14, 0, 0]), "easeOutQuad"),
    (0.14, pose(body=[72, 0, 0], body_pos=[0, -3.5, -2.0], right_arm=[-168, 14, 0], left_arm=[-168, -14, 0],
                right_leg=[44, 0, 6], left_leg=[58, 0, -6], head=[-58, 0, 0]), "easeOutBack"),
    (0.36, pose(body=[66, 0, 0], body_pos=[0, -3.2, -1.5], right_arm=[-160, 10, 0], left_arm=[-160, -10, 0],
                right_leg=[52, 0, 6], left_leg=[40, 0, -6], head=[-52, 0, 0]), "easeInOutSine"),
    (0.5, pose(body=[-16, 0, 0], body_pos=[0, -1.5, 1.5], right_arm=[-40, 0, 26], left_arm=[-40, 0, -26],
               right_leg=[-36, 0, 0], left_leg=[18, 0, 0], head=[12, 0, 0]), "easeOutBack"),
    (0.85, REST, "easeInOutSine"),
]))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"format_version": "1.8.0", "animations": dict(ANIMS)}, indent=1) + "\n", encoding="utf-8", newline="\n")
print(f"wrote {OUT.relative_to(P)}: {', '.join(name for name, _ in ANIMS)}")
