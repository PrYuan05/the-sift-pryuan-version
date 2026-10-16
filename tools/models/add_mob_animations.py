"""Add the triggerable animations the non-boss mobs' code uses (attack, bite, slash, ...) to their GeckoLib animation files.
Usage: python -I tools/models/add_mob_animations.py <project> [--write]

These models only have a single "root" bone, so every animation is a whole-body move (rotation / position / scale of
root). Existing animations with the same name are never touched - a proper Blockbench animation exported under the same
name replaces these placeholders. Without --write it only reports what would be added.
Rotation convention (GeckoLib negates bone x rotation): +x leans the model forward, -x leans it back."""
import sys, json
from pathlib import Path

P = Path(sys.argv[1])
WRITE = "--write" in sys.argv
ANIM_DIR = P / "src/main/resources/assets/pysift/geckolib/animations/entity"


def kf(*frames):
    """frames: (time, [x, y, z]) -> GeckoLib keyframe dict."""
    return {f"{t:.2f}".rstrip("0").rstrip(".") if t else "0.0": list(v) for t, v in frames}


def anim(length, loop=False, rotation=None, position=None, scale=None):
    bone = {}
    if rotation:
        bone["rotation"] = kf(*rotation)
    if position:
        bone["position"] = kf(*position)
    if scale:
        bone["scale"] = kf(*scale)
    a = {"animation_length": length, "bones": {"root": bone}}
    if loop:
        a["loop"] = loop
    return a


Z = [0, 0, 0]
ONE = [1, 1, 1]
# generic lunge: lean forward and dip, back to rest
ATTACK = anim(0.5, rotation=[(0, Z), (0.15, [20, 0, 0]), (0.5, Z)], position=[(0, Z), (0.15, [0, -1, 0]), (0.5, Z)])

ANIMS = {
    "blub": {"sad": anim(2.0, loop=True, rotation=[(0, [8, 0, -3]), (1.0, [12, 0, 3]), (2.0, [8, 0, -3])],
                         position=[(0, [0, -1.5, 0]), (1.0, [0, -2, 0]), (2.0, [0, -1.5, 0])],
                         scale=[(0, [1.08, 0.86, 1.08]), (1.0, [1.1, 0.82, 1.1]), (2.0, [1.08, 0.86, 1.08])])},
    "singer": {"sing": anim(1.5, rotation=[(0, Z), (0.3, [-15, 0, 0]), (1.1, [-12, 0, 0]), (1.5, Z)],
                            scale=[(0, ONE), (0.4, [1.1, 1.1, 1.1]), (0.8, [1.05, 1.05, 1.05]), (1.2, [1.1, 1.1, 1.1]), (1.5, ONE)])},
    "nuzzle": {"nuzzle": anim(1.0, rotation=[(0, Z), (0.2, [10, 0, 10]), (0.4, [10, 0, -10]), (0.6, [10, 0, 10]),
                                             (0.8, [10, 0, -10]), (1.0, Z)])},
    "dartback": {"shoot": anim(0.8, rotation=[(0, Z), (0.3, [-12, 0, 0]), (0.4, [8, 0, 0]), (0.8, Z)])},
    "hurler": {"throw": anim(1.2, rotation=[(0, Z), (0.5, [-25, 0, 0]), (0.75, [30, 0, 0]), (1.2, Z)],
                             position=[(0, Z), (0.5, [0, -1, 0]), (0.75, [0, 0.5, 0]), (1.2, Z)]),
               "attack": ATTACK},
    "pollinator": {"sting": anim(0.5, rotation=[(0, Z), (0.2, [35, 0, 0]), (0.5, Z)]),
                   "pollinate": anim(1.0, position=[(0, Z), (0.5, [0, -2, 0]), (1.0, Z)],
                                     rotation=[(0, Z), (0.5, [10, 0, 0]), (1.0, Z)])},
    "nester": {"summon": anim(1.0, scale=[(0, ONE), (0.4, [1.2, 0.85, 1.2]), (0.6, [0.95, 1.1, 0.95]), (1.0, ONE)],
                              rotation=[(0, Z), (0.4, [-10, 0, 0]), (1.0, Z)]),
               "attack": ATTACK},
    "seedling": {"attack": ATTACK},
    "sprout": {"attack": ATTACK},
    "bloombud": {"bite": anim(0.6, rotation=[(0, Z), (0.08, [-15, 0, 0]), (0.2, [25, 0, 0]), (0.6, Z)],
                              scale=[(0, ONE), (0.08, [1.3, 1.4, 1.3]), (0.2, [1.1, 0.9, 1.1]), (0.6, ONE)])},
    "stalker": {"attack": ATTACK},
    "scavenger": {"attack": ATTACK},
    "prickle": {"bristle": anim(0.5, scale=[(0, ONE), (0.1, [1.35, 1.35, 1.35]), (0.5, ONE)])},
    "sentinel": {"slash": anim(1.3, rotation=[(0, Z), (0.6, [-10, -40, 0]), (0.85, [20, 50, 0]), (1.3, Z)]),
                 "attack": ATTACK},
    "tuner": {"aura": anim(1.0, rotation=[(0, Z), (0.5, [0, 180, 0]), (1.0, [0, 360, 0])],
                           scale=[(0, ONE), (0.3, [1.15, 1.15, 1.15]), (1.0, ONE)])},
    "roamroot": {"stomp": anim(1.1, rotation=[(0, Z), (0.4, [-8, 0, 0]), (0.6, [10, 0, 0]), (1.1, Z)],
                               position=[(0, Z), (0.4, [0, 4, 0]), (0.6, [0, -1, 0]), (1.1, Z)]),
                 "attack": ATTACK},
    "slabber": {"deflect": anim(0.4, rotation=[(0, Z), (0.1, [-12, 0, 0]), (0.4, Z)]),
                "attack": ATTACK},
    "wobble": {"attack": ATTACK,
               "death": anim(1.0, loop="hold_on_last_frame",
                             position=[(0, Z), (0.3, [0, 8, 0]), (0.6, Z)],
                             scale=[(0, ONE), (0.3, [0.85, 1.2, 0.85]), (0.7, [1.3, 0.6, 1.3]), (1.0, [1.2, 0.7, 1.2])],
                             rotation=[(0, Z), (0.7, Z), (1.0, [0, 0, 90])])},
}

total = 0
for mob, new in ANIMS.items():
    f = ANIM_DIR / f"{mob}.animation.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    anims = data["animations"]
    added = []
    for name, a in new.items():
        key = f"animation.{mob}.{name}"
        if key not in anims:
            anims[key] = a
            added.append(name)
    total += len(added)
    print(f"{mob:11s} +{added}")
    if WRITE and added:
        f.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{'wrote' if WRITE else 'would add'} {total} animations")
