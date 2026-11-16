"""Animations for the bosses' new abilities (Sculk Monstrosity, Harmonizer, Monarch).
Usage: python -I tools/models/add_boss_animations.py <project> [--write]

Each animation's timing matches the skill goal in code (impact tick / total ticks; 20 ticks = 1 s), noted per entry.
Existing animations with the same name are replaced; everything else in the file is left alone. Without --write it
only checks that every animated bone exists in the model and prints what would change.
Conventions (match the existing animations): arms raised forward / up = negative x; +z leans a bone's top towards +x,
so a left arm (on -x) swings outward with +z and a right arm with -z; +x leans the top forward (-z)."""
import sys, json
from pathlib import Path

P = Path(sys.argv[1])
WRITE = "--write" in sys.argv
ASSETS = P / "src/main/resources/assets/pysift/geckolib"


def _key(t):
    return f"{t:.4f}".rstrip("0").rstrip(".") if t else "0.0"


def keys(*frames):
    return {_key(t): list(v) for t, v in frames}


def once(length, bones, hold=False):
    a = {"animation_length": length, "bones": bones}
    if hold:
        a["loop"] = "hold_on_last_frame"
    return a


def spin(t0, t1, turns, axis=1, steps=8, base=(0, 0, 0)):
    """Keyframes for a full spin (turns * 360 degrees) between t0 and t1 on one axis."""
    out = []
    for i in range(steps + 1):
        v = list(base)
        v[axis] = base[axis] + 360.0 * turns * i / steps
        out.append((t0 + (t1 - t0) * i / steps, v))
    return out


Z = [0, 0, 0]
ONE = [1, 1, 1]


# ------------------------------------------------------------------------------------------------ Sculk Monstrosity
def sculk():
    return {
        # left hand of the melee combo (mirror of "attack")
        "attack_left": once(0.5, {
            "left_arm": {"rotation": keys((0, Z), (0.15, [-130, 0, 15]), (0.3, [-25, 0, -5]), (0.5, Z))},
            "left_forearm": {"rotation": keys((0, Z), (0.15, [-45, 0, 0]), (0.3, [-5, 0, 0]), (0.5, Z))},
            "root": {"rotation": keys((0, Z), (0.3, [8, 10, 0]), (0.5, Z))},
            "head": {"rotation": keys((0, Z), (0.3, [10, 0, 0]), (0.5, Z))}}),
        # SoulChargeGoal: starts 2 ticks after the charge stops, punch lands 14 ticks later (0.7 s)
        "mega_punch": once(1.3, {
            "right_arm": {"rotation": keys((0, Z), (0.35, [35, 0, 25]), (0.6, [40, 0, 25]), (0.7, [-95, 0, -5]), (1.0, [-90, 0, -5]),
                                           (1.3, Z))},
            "right_forearm": {"rotation": keys((0, Z), (0.35, [-80, 0, 0]), (0.6, [-85, 0, 0]), (0.7, [-5, 0, 0]), (1.3, Z))},
            "root": {"rotation": keys((0, Z), (0.35, [-4, -25, 0]), (0.6, [-4, -28, 0]), (0.7, [10, 30, 0]), (1.0, [8, 25, 0]), (1.3, Z))},
            "shoulder_flame_right": {"scale": keys((0, ONE), (0.3, [1.6, 1.8, 1.6]), (0.7, [2.0, 2.2, 2.0]), (1.0, [1.3, 1.4, 1.3]), (1.3, ONE))},
            "head": {"rotation": keys((0, Z), (0.35, [-8, -15, 0]), (0.7, [12, 10, 0]), (1.3, Z))}}),
        # swipe: impact 16 ticks (0.8 s), total 26 (1.3 s) - twist back, left arm out, then sweep across the front
        "swipe": once(1.3, {
            "root": {"rotation": keys((0, Z), (0.6, [-5, 35, 0]), (0.8, [8, -40, 0]), (1.0, [6, -35, 0]), (1.3, Z))},
            "left_arm": {"rotation": keys((0, Z), (0.6, [-20, 0, 85]), (0.8, [-75, 0, 65]), (1.0, [-70, 0, 55]), (1.3, Z))},
            "left_forearm": {"rotation": keys((0, Z), (0.6, [-25, 0, 0]), (0.8, [-5, 0, 0]), (1.3, Z))},
            "right_arm": {"rotation": keys((0, Z), (0.6, [15, 0, -10]), (0.8, [-10, 0, -20]), (1.3, Z))},
            "head": {"rotation": keys((0, Z), (0.6, [0, -25, 0]), (0.8, [5, 20, 0]), (1.3, Z))}}),
        # cube barrage: impact 30 ticks (1.5 s), total 50 (2.5 s) - crouch, throw the arms open and roar
        "cube_barrage": once(2.5, {
            "root": {"position": keys((0, Z), (0.9, [0, -2, 0]), (1.5, [0, 1, 0]), (2.1, [0, 0.5, 0]), (2.5, Z)),
                     "rotation": keys((0, Z), (0.9, [8, 0, 0]), (1.5, [-10, 0, 0]), (2.1, [-8, 0, 0]), (2.5, Z))},
            "right_arm": {"rotation": keys((0, Z), (0.9, [-20, 0, -15]), (1.5, [-70, 0, -75]), (2.1, [-65, 0, -70]), (2.5, Z))},
            "left_arm": {"rotation": keys((0, Z), (0.9, [-20, 0, 15]), (1.5, [-70, 0, 75]), (2.1, [-65, 0, 70]), (2.5, Z))},
            "head": {"rotation": keys((0, Z), (0.9, [10, 0, 0]), (1.5, [-25, 0, 0]), (2.1, [-22, 0, 0]), (2.5, Z))},
            "jaw": {"rotation": keys((0, Z), (1.3, Z), (1.5, [32, 0, 0]), (2.1, [28, 0, 0]), (2.4, Z))},
            "back_spines": {"scale": keys((0, ONE), (1.5, [1.25, 1.3, 1.25]), (2.1, [1.2, 1.25, 1.2]), (2.5, ONE))}}),
        # catalyst summon: impact 24 ticks (1.2 s), total 40 (2 s) - flex both arms, palms glowing, core pulses
        "catalyst": once(2.0, {
            "right_arm": {"rotation": keys((0, Z), (0.8, [-40, 0, -45]), (1.2, [-45, 0, -50]), (1.6, [-40, 0, -45]), (2.0, Z))},
            "right_forearm": {"rotation": keys((0, Z), (0.8, [-110, 0, 0]), (1.2, [-115, 0, 0]), (1.6, [-110, 0, 0]), (2.0, Z))},
            "left_arm": {"rotation": keys((0, Z), (0.8, [-40, 0, 45]), (1.2, [-45, 0, 50]), (1.6, [-40, 0, 45]), (2.0, Z))},
            "left_forearm": {"rotation": keys((0, Z), (0.8, [-110, 0, 0]), (1.2, [-115, 0, 0]), (1.6, [-110, 0, 0]), (2.0, Z))},
            "root": {"position": keys((0, Z), (0.8, [0, -1.5, 0]), (1.2, [0, -2, 0]), (1.6, [0, -1.5, 0]), (2.0, Z))},
            "core": {"scale": keys((0, ONE), (0.8, [1.15, 1.15, 1.15]), (1.0, [1.0, 1.0, 1.0]), (1.2, [1.3, 1.3, 1.3]), (1.6, [1.1, 1.1, 1.1]), (2.0, ONE))},
            "head": {"rotation": keys((0, Z), (0.8, [-12, 0, 0]), (1.6, [-12, 0, 0]), (2.0, Z))}}),
    }


# ------------------------------------------------------------------------------------------------ Harmonizer
# outward tilt for each tentacle (where it hangs around the body): front = -x, back = +x, left = +z, right = -z
FLARE = {1: [-30, 0, 30], 2: [-30, 0, -30], 3: [-35, 0, 0], 4: [-35, 0, 0], 5: [35, 0, 0], 6: [35, 0, 0], 7: [30, 0, 30], 8: [30, 0, -30]}


def scaled(v, f):
    return [round(x * f, 2) for x in v]


def harmonizer():
    roar_t = {f"tentacle_{n}": {"rotation": keys((0, Z), (0.7, scaled(FLARE[n], -0.3)), (1.0, FLARE[n]), (1.5, scaled(FLARE[n], 0.8)), (2.0, Z))}
              for n in FLARE}
    vortex_t = {}
    for n in FLARE:
        swirl = [(0, Z)]
        for i in range(1, 7):
            t = i * 0.5
            swirl.append((t, [FLARE[n][0] * 0.5, 25 * (1 if i % 2 else -1), FLARE[n][2] * 0.5]))
        swirl += [(3.3, scaled(FLARE[n], 0.3)), (3.5, FLARE[n]), (3.9, scaled(FLARE[n], 0.5)), (4.2, Z)]
        vortex_t[f"tentacle_{n}"] = {"rotation": keys(*swirl)}
    return {
        # roar: impact 20 ticks (1 s), total 40 (2 s) - draws in, then bursts out with every tentacle flared
        "roar": once(2.0, {
            **roar_t,
            "body": {"scale": keys((0, ONE), (0.7, [0.92, 0.95, 0.92]), (1.0, [1.15, 1.12, 1.15]), (1.5, [1.08, 1.05, 1.08]), (2.0, ONE))},
            "head": {"rotation": keys((0, Z), (0.7, [10, 0, 0]), (1.0, [-20, 0, 0]), (1.5, [-15, 0, 0]), (2.0, Z))}}),
        # tentacle grab: impact 14 ticks (0.7 s), total 30 (1.5 s) - front-left tentacle rises, lashes out, hauls back
        "tentacle_grab": once(1.5, {
            "tentacle_1": {"rotation": keys((0, Z), (0.55, [-110, 0, 10]), (0.7, [-65, 0, 5]), (1.1, [20, 0, 0]), (1.5, Z))},
            "tentacle_1_seg1": {"rotation": keys((0, Z), (0.55, [-20, 0, 0]), (0.7, [-5, 0, 0]), (1.1, [25, 0, 0]), (1.5, Z))},
            "tentacle_1_seg2": {"rotation": keys((0, Z), (0.55, [-20, 0, 0]), (0.7, [-5, 0, 0]), (1.1, [30, 0, 0]), (1.5, Z))},
            "tentacle_1_seg3": {"rotation": keys((0, Z), (0.55, [-15, 0, 0]), (0.7, [10, 0, 0]), (1.1, [40, 0, 0]), (1.5, Z))},
            "body": {"rotation": keys((0, Z), (0.55, [-6, 0, 0]), (0.7, [8, 0, 0]), (1.1, [-4, 0, 0]), (1.5, Z))}}),
        # vortex: impact 70 ticks (3.5 s), total 84 (4.2 s) - rises and spins while the orb pulls, then slams down
        "vortex": once(4.2, {
            **vortex_t,
            "root": {"position": keys((0, Z), (1.0, [0, 8, 0]), (3.2, [0, 9, 0]), (3.5, [0, -2, 0]), (3.8, [0, -1, 0]), (4.2, Z)),
                     "rotation": keys(*spin(0.3, 3.2, 2), (3.5, [10, 720, 0]), (4.2, [0, 720, 0]))},
            "body": {"scale": keys((0, ONE), (3.2, [1.05, 1.1, 1.05]), (3.5, [1.2, 0.85, 1.2]), (3.9, [1.05, 0.98, 1.05]), (4.2, ONE))}}),
    }


# ------------------------------------------------------------------------------------------------ Monarch (no arm bones)
def monarch():
    return {
        # dash strike: impact 12 ticks (0.6 s), dash until 1.1 s, total 34 (1.7 s) - reel back, twirling lunge
        "dash_strike": once(1.7, {
            "body": {"rotation": keys((0, Z), (0.6, [-10, -50, 0]), (0.7, [25, 0, 0]), (1.1, [25, 0, 0]), (1.4, [10, 0, 0]), (1.7, Z))},
            "root": {"rotation": keys((0, Z), (0.6, Z), *spin(0.6, 1.1, 1)[1:], (1.7, [0, 360, 0]))},
            "cape": {"rotation": keys((0, Z), (0.6, [20, 0, 0]), (0.75, [65, 0, 0]), (1.1, [60, 0, 0]), (1.7, Z))},
            "crown": {"rotation": keys((0, Z), (0.6, [0, 0, -10]), (1.1, [0, 0, 10]), (1.7, Z))}}),
        # hover loop: impact 10 ticks (0.5 s), spin until 1.2 s, total 40 (2 s) - reels the other way, rises and spins twice
        "hover_loop": once(2.0, {
            "body": {"rotation": keys((0, Z), (0.5, [-8, 50, 0]), (0.6, [15, 0, 0]), (1.2, [15, 0, 0]), (2.0, Z))},
            "root": {"rotation": keys((0, Z), (0.5, Z), *spin(0.5, 1.2, 2)[1:], (2.0, [0, 720, 0])),
                     "position": keys((0, Z), (0.5, Z), (0.7, [0, 2.5, 0]), (1.1, [0, 2.5, 0]), (1.3, Z), (2.0, Z))},
            "cape": {"rotation": keys((0, Z), (0.5, [15, 0, 0]), (0.7, [70, 0, 15]), (1.2, [70, 0, -15]), (2.0, Z))}}),
        # calamity combo: total 60 ticks (3 s) - slash at 0.7 s, twirling dash 1.0-1.5 s, final slash at 2.1 s
        "calamity": once(3.0, {
            "body": {"rotation": keys((0, Z), (0.5, [-12, -60, 0]), (0.7, [15, 45, 0]), (0.95, [10, 35, 0]), (1.0, [20, 0, 0]),
                                      (1.5, [20, 0, 0]), (1.9, [-12, -55, 0]), (2.1, [18, 60, 0]), (2.5, [10, 40, 0]), (3.0, Z))},
            "root": {"rotation": keys((0, Z), (1.0, Z), *spin(1.0, 1.5, 1)[1:], (3.0, [0, 360, 0]))},
            "cape": {"rotation": keys((0, Z), (0.5, [20, 0, 0]), (0.7, [50, 0, 0]), (1.0, [65, 0, 0]), (1.5, [60, 0, 0]),
                                      (1.9, [20, 0, 0]), (2.1, [55, 0, 0]), (3.0, Z))},
            "head": {"rotation": keys((0, Z), (0.5, [0, 25, 0]), (0.7, [5, -20, 0]), (1.9, [0, 25, 0]), (2.1, [5, -25, 0]), (3.0, Z))}}),
        # heel stomp: impact 8 ticks (0.4 s), total 18 (0.9 s) - quick twirl with a heel kick
        "heel_stomp": once(0.9, {
            "root": {"rotation": keys((0, Z), *spin(0.05, 0.45, 1, steps=6)[1:], (0.9, [0, 360, 0])),
                     "position": keys((0, Z), (0.2, [0, 1, 0]), (0.4, Z), (0.9, Z))},
            "right_leg": {"rotation": keys((0, Z), (0.25, [-55, 0, 0]), (0.4, [10, 0, 0]), (0.9, Z))},
            "cape": {"rotation": keys((0, Z), (0.3, [50, 0, 0]), (0.9, Z))}}),
        # summon: impact 20 ticks (1 s), total 36 (1.8 s) - throws its head back and roars, cape and crown flaring
        "summon": once(1.8, {
            "head": {"rotation": keys((0, Z), (0.8, [-32, 0, 0]), (1.4, [-28, 0, 0]), (1.8, Z))},
            "body": {"rotation": keys((0, Z), (0.8, [-10, 0, 0]), (1.4, [-8, 0, 0]), (1.8, Z)),
                     "scale": keys((0, ONE), (1.0, [1.08, 1.08, 1.08]), (1.8, ONE))},
            "cape": {"rotation": keys((0, Z), (1.0, [40, 0, 0]), (1.4, [35, 0, 0]), (1.8, Z))},
            "crown": {"scale": keys((0, ONE), (1.0, [1.25, 1.25, 1.25]), (1.8, ONE))}}),
    }


BOSSES = {"sculk_monstrosity": sculk, "harmonizer": harmonizer, "monarch": monarch}

problems = 0
for mob, fn in BOSSES.items():
    geo = json.loads((ASSETS / f"models/entity/{mob}.geo.json").read_text(encoding="utf-8"))
    bones = {b["name"] for b in geo["minecraft:geometry"][0]["bones"]}
    f = ASSETS / f"animations/entity/{mob}.animation.json"
    doc = json.loads(f.read_text(encoding="utf-8"))
    new = fn()
    for name, a in new.items():
        missing = sorted(set(a["bones"]) - bones)
        if missing:
            problems += 1
            print(f"  {mob}.{name}: missing bones {missing}")
        key = f"animation.{mob}.{name}"
        state = "replace" if key in doc["animations"] else "add"
        doc["animations"][key] = a
        print(f"{mob:18s} {state:7s} {name} ({a['animation_length']} s)")
    if WRITE and not problems:
        f.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
print("problems:", problems, "- written" if WRITE and not problems else "")
