"""Split the single-"root" mob models into part bones, fix misplaced parts, and write part animations.
Usage: python -I tools/models/rig_mobs.py <project> <mob> [--install]

Every mob has a hand-written RIG spec (the converted geometry is too irregular to rig automatically):
  move    : [(cube indices, [dx, dy, dz]), ...]  fixes for misplaced parts (cube origin and pivot are moved)
  shift   : [dx, dy, dz] applied to the whole model afterwards (e.g. lift parts that were sunk into the ground)
  place   : [(cube index, [x, y, z]), ...] put a cube at an exact origin and remove its rotation (applied last)
  pose    : [(cube index, [x, y, z], [rx, ry, rz], [px, py, pz]), ...] exact origin, rotation and pivot for a cube
  reface  : [(cube index, [x, y, z], [w, h, d], {new face: old face}), ...] like place, but also give the cube a new
            size and move its per-face UVs (e.g. turn a plane that was rotated onto the side back into a front plane)
  rerotate: [(cube index, [rx, ry, rz]), ...] give a cube a new rotation about its bottom centre, keeping that point
            (e.g. an elbow joining the forearm) exactly where it was; applied after move/shift
  bones   : [(name, parent, pivot), ...] in post-fix coordinates; "root" is always the top bone (pivot 0,0,0)
  assign  : {bone: [cube indices]}; cubes not listed stay in root. Cube data (origin/size/uv/rotation) is kept as is,
            and geo cube coordinates are absolute, so regrouping alone never changes the rest pose.
  hitbox  : (width, height) in blocks, written to ModEntities when it differs
  anims   : {name: animation} replacing idle / walk and upgrading the skill animations (same names, so no code changes)
  drop_anims: [name, ...] animations to delete because the code no longer triggers them
Cube indices are the order of cubes in the current file (see rig_view.py, which labels them).
Without --install it writes build/models/rig_preview/<mob>.png (current vs rigged, bones coloured) and the would-be
files to build/models/rig_out/. With --install the geo + animation files are backed up to .texture_backups/ first.
Animation rotation convention: +x leans forward (top towards -z), +z leans the top towards +x."""
import sys, json, math, copy, re, shutil, datetime
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from rig_view import render, rot_point  # noqa: E402

P, MOB = Path(sys.argv[1]), sys.argv[2]
INSTALL = "--install" in sys.argv
ASSETS = P / "src/main/resources/assets/pysift"
GEO = ASSETS / f"geckolib/models/entity/{MOB}.geo.json"
ANIM = ASSETS / f"geckolib/animations/entity/{MOB}.animation.json"
TEX = ASSETS / f"textures/entity/{MOB}.png"
MOD_ENTITIES = P / "src/main/java/pryuan05/pysift/entity/ModEntities.java"


# ------------------------------------------------------------------------------------------------ animation helpers
def _key(t):
    return f"{t:.4f}".rstrip("0").rstrip(".") if t else "0.0"


def wave(period, amp, phase=0.0, axis=0, base=(0, 0, 0), steps=8):
    """Looping sine keyframes on one axis: base + amp*sin(2pi(t/period + phase))."""
    out = {}
    for i in range(steps + 1):
        t = period * i / steps
        v = list(base)
        v[axis] = round(base[axis] + amp * math.sin(2 * math.pi * (i / steps + phase)), 3)
        out[_key(t)] = v
    return out


def keys(*frames):
    return {_key(t): list(v) for t, v in frames}


def loop_anim(period, bones):
    return {"loop": True, "animation_length": period, "bones": bones}


def once(length, bones, hold=False):
    a = {"animation_length": length, "bones": bones}
    if hold:
        a["loop"] = "hold_on_last_frame"
    return a


Z = [0, 0, 0]
ONE = [1, 1, 1]


# ------------------------------------------------------------------------------------------------ rig specs
def singer():
    # long-necked singer: body was offset (+6, 0, +3.95) from the centre line, the arms floated off the body tilted outward,
    # and the whole model was sunk 16px
    walk_t, idle_t = 1.0, 3.0
    return {
        "move": [([13, 14], [-6, 0, -3.95])],   # body back to the centre line
        "shift": [0, 16, 0],
        # arms hang straight down beside the body (no outward tilt): upper arm flush with the shoulder, forearm below it
        "place": [(8, [-10, 10, -3.75]), (12, [-9.75, 3, -2.25]), (7, [6, 10, -3.75]), (11, [6.25, 3, -2.25])],
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 3.5, 0]),
                  ("neck", "body", [0, 19.5, 0.2]),
                  ("head", "neck", [0, 29.5, 0.2]),
                  ("left_ear", "head", [-4, 36, -1.2]),
                  ("right_ear", "head", [4, 36, -1.2]),
                  ("left_arm", "body", [-8, 20, 0]),
                  ("right_arm", "body", [8, 20, 0]),
                  ("left_leg", "root", [-3.05, 3.5, -0.05]),
                  ("right_leg", "root", [2.95, 3.5, -0.05])],
        "assign": {"body": [13, 14], "neck": [0], "head": [1, 4, 5, 6], "left_ear": [2], "right_ear": [3],
                   "left_arm": [8, 12], "right_arm": [7, 11], "left_leg": [9], "right_leg": [10]},
        "hitbox": (1.0, 2.7),
        "anims": {
            "idle": loop_anim(idle_t, {
                "neck": {"rotation": wave(idle_t, 3, 0.0)},
                "head": {"rotation": wave(idle_t, 4, 0.25)},
                "left_ear": {"rotation": wave(idle_t, 6, 0.1, axis=2)},
                "right_ear": {"rotation": wave(idle_t, -6, 0.1, axis=2)},
                "left_arm": {"rotation": wave(idle_t, 4, 0.0, axis=2)},
                "right_arm": {"rotation": wave(idle_t, -4, 0.0, axis=2)},
                "body": {"position": wave(idle_t, 0.4, 0.0, axis=1)}}),
            "walk": loop_anim(walk_t, {
                "left_leg": {"rotation": wave(walk_t, 30, 0.0)},
                "right_leg": {"rotation": wave(walk_t, 30, 0.5)},
                "left_arm": {"rotation": wave(walk_t, 20, 0.5)},
                "right_arm": {"rotation": wave(walk_t, 20, 0.0)},
                "neck": {"rotation": wave(walk_t / 2, 4, 0.0, base=(5, 0, 0))},
                "head": {"rotation": wave(walk_t / 2, -4, 0.0)},
                "body": {"position": wave(walk_t / 2, 0.6, 0.25, axis=1)}}),
            # head back, ears open, arms raised, then a bow
            "sing": once(1.5, {
                "neck": {"rotation": keys((0, Z), (0.3, [-20, 0, 0]), (1.1, [-15, 0, 0]), (1.5, Z))},
                "head": {"rotation": keys((0, Z), (0.3, [-15, 0, 0]), (0.7, [-10, 0, 0]), (1.1, [-15, 0, 0]), (1.5, Z))},
                "left_ear": {"rotation": keys((0, Z), (0.3, [0, 0, -25]), (1.1, [0, 0, -20]), (1.5, Z))},
                "right_ear": {"rotation": keys((0, Z), (0.3, [0, 0, 25]), (1.1, [0, 0, 20]), (1.5, Z))},
                "left_arm": {"rotation": keys((0, Z), (0.3, [-30, 0, -40]), (1.1, [-25, 0, -35]), (1.5, Z))},
                "right_arm": {"rotation": keys((0, Z), (0.3, [-30, 0, 40]), (1.1, [-25, 0, 35]), (1.5, Z))}}),
        },
    }


def roamroot():
    # walking tree: the big canopy block is its head (the nose sticks out of its front) and sits low over the trunk -
    # keep it there. Only fix: the legs went 9.8px into the ground.
    idle_t, walk_t = 3.0, 1.6
    return {
        "shift": [0, 9.8, 0],
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 16.8, 0.5]),
                  ("canopy", "body", [0, 20.8, -0.5]),
                  ("left_leg", "root", [-4.5, 21, 0]),
                  ("right_leg", "root", [4.5, 21, 0])],
        "assign": {"body": [0, 3, 4, 5, 6], "canopy": [10, 11, 12, 13, 14, 15, 16],
                   "left_leg": [1, 7], "right_leg": [2, 8, 9]},
        "hitbox": (1.1, 2.4),
        "anims": {
            "idle": loop_anim(idle_t, {
                "canopy": {"rotation": wave(idle_t, 3, 0.0, axis=2)},
                "body": {"rotation": wave(idle_t, 1.5, 0.25)}}),
            "walk": loop_anim(walk_t, {
                "left_leg": {"rotation": wave(walk_t, 22, 0.0)},
                "right_leg": {"rotation": wave(walk_t, 22, 0.5)},
                "body": {"rotation": wave(walk_t, 3, 0.25, axis=2), "position": wave(walk_t / 2, 0.5, 0.25, axis=1)},
                "canopy": {"rotation": wave(walk_t, -4, 0.35, axis=2)}}),
            # lift a leg high and slam it down (impact at 0.6 s)
            "stomp": once(1.1, {
                "right_leg": {"rotation": keys((0, Z), (0.4, [-45, 0, 0]), (0.6, [5, 0, 0]), (1.1, Z))},
                "body": {"rotation": keys((0, Z), (0.4, [-8, 0, -4]), (0.6, [8, 0, 0]), (1.1, Z)),
                         "position": keys((0, Z), (0.4, [0, 2, 0]), (0.6, [0, -1, 0]), (1.1, Z))},
                "canopy": {"rotation": keys((0, Z), (0.45, [-6, 0, 0]), (0.65, [12, 0, 0]), (1.1, Z))}}),
            # canopy head-butt
            "attack": once(0.5, {
                "body": {"rotation": keys((0, Z), (0.15, [12, 0, 0]), (0.5, Z))},
                "canopy": {"rotation": keys((0, Z), (0.15, [18, 0, 0]), (0.5, Z))}}),
        },
    }


def bloombud():
    # flower-headed ambusher: legs sunk 6px; arm cube 6 was 0.8px lower / further out than its mirror (cube 7)
    idle_t, walk_t = 3.0, 1.2
    return {
        "shift": [0, 6, 0],
        "place": [(6, [-10, 5, -0.8])],   # mirror of cube 7 (origin [7, 5, -0.8] after the lift, size 3 x 15 x 4)
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 10, 0]),
                  ("head", "body", [0, 17, 0]),
                  ("jaw", "head", [0, 23, -4.5]),
                  ("crown", "head", [0, 28, 0]),
                  ("left_petals", "crown", [-0.5, 28, 0]),
                  ("right_petals", "crown", [0.5, 28, 0]),
                  ("left_arm", "body", [-8.5, 19, 1.2]),
                  ("right_arm", "body", [8.5, 19, 1.2]),
                  ("left_leg", "root", [-2.5, 13, 0]),
                  ("right_leg", "root", [2.5, 13, 0])],
        "assign": {"body": [0], "head": [1, 2, 3, 4, 5], "jaw": [10, 11], "crown": [12, 13, 14, 18],
                   "left_petals": [17, 19], "right_petals": [15, 16],
                   "left_arm": [6], "right_arm": [7], "left_leg": [8], "right_leg": [9]},
        "hitbox": (0.9, 2.4),
        "anims": {
            "idle": loop_anim(idle_t, {
                "left_petals": {"rotation": wave(idle_t, 6, 0.0, axis=2)},
                "right_petals": {"rotation": wave(idle_t, -6, 0.0, axis=2)},
                "crown": {"rotation": wave(idle_t, 3, 0.25)},
                "head": {"rotation": wave(idle_t, 2, 0.5)},
                "left_arm": {"rotation": wave(idle_t, 3, 0.0, axis=2)},
                "right_arm": {"rotation": wave(idle_t, -3, 0.0, axis=2)}}),
            "walk": loop_anim(walk_t, {
                "left_leg": {"rotation": wave(walk_t, 25, 0.0)},
                "right_leg": {"rotation": wave(walk_t, 25, 0.5)},
                "left_arm": {"rotation": wave(walk_t, 20, 0.5)},
                "right_arm": {"rotation": wave(walk_t, 20, 0.0)},
                "body": {"position": wave(walk_t / 2, 0.5, 0.25, axis=1)},
                "crown": {"rotation": wave(walk_t / 2, 4, 0.0)}}),
            # jaw snaps open, petals flare, arms grab forward, head lunges (bite lands at 0.2 s)
            "bite": once(0.6, {
                "jaw": {"rotation": keys((0, Z), (0.08, [-55, 0, 0]), (0.2, [5, 0, 0]), (0.6, Z))},
                "head": {"rotation": keys((0, Z), (0.08, [-8, 0, 0]), (0.2, [15, 0, 0]), (0.6, Z))},
                "left_petals": {"rotation": keys((0, Z), (0.08, [0, 0, -25]), (0.3, [0, 0, -10]), (0.6, Z))},
                "right_petals": {"rotation": keys((0, Z), (0.08, [0, 0, 25]), (0.3, [0, 0, 10]), (0.6, Z))},
                "left_arm": {"rotation": keys((0, Z), (0.1, [-70, 0, 0]), (0.2, [-50, 0, 15]), (0.6, Z))},
                "right_arm": {"rotation": keys((0, Z), (0.1, [-70, 0, 0]), (0.2, [-50, 0, -15]), (0.6, Z))}}),
        },
    }


def slabber():
    # armoured quadruped with mushrooms on its back; only fix: the legs were sunk 4px
    idle_t, walk_t = 3.0, 1.2
    return {
        "shift": [0, 4, 0],
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 9, 0]),
                  ("head", "body", [0, 17, -5]),
                  ("tongue", "head", [0, 13, -14]),
                  ("mushrooms", "body", [0, 26, 0]),
                  ("front_left_leg", "root", [-5.5, 11, -5.5]),
                  ("front_right_leg", "root", [5.5, 11, -5.5]),
                  ("back_right_leg", "root", [5.5, 11, 8.5]),
                  ("back_left_leg", "root", [-5.5, 11, 8.5])],
        "assign": {"body": [0], "head": [1, 2, 3, 4, 5], "tongue": [6],
                   "mushrooms": [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
                   "front_left_leg": [19], "front_right_leg": [20], "back_right_leg": [21], "back_left_leg": [22]},
        "hitbox": (1.4, 1.7),
        "anims": {
            "idle": loop_anim(idle_t, {
                "body": {"position": wave(idle_t, 0.3, 0.0, axis=1)},
                "head": {"rotation": wave(idle_t, 2, 0.25)},
                "tongue": {"rotation": wave(idle_t, 6, 0.4)},
                "mushrooms": {"rotation": wave(idle_t, 3, 0.1, axis=2)}}),
            # diagonal gait
            "walk": loop_anim(walk_t, {
                "front_left_leg": {"rotation": wave(walk_t, 20, 0.0)},
                "back_right_leg": {"rotation": wave(walk_t, 20, 0.0)},
                "front_right_leg": {"rotation": wave(walk_t, 20, 0.5)},
                "back_left_leg": {"rotation": wave(walk_t, 20, 0.5)},
                "body": {"rotation": wave(walk_t, 2, 0.25, axis=2), "position": wave(walk_t / 2, 0.4, 0.25, axis=1)},
                "head": {"rotation": wave(walk_t / 2, 3, 0.0)},
                "tongue": {"rotation": wave(walk_t / 2, 10, 0.3)},
                "mushrooms": {"rotation": wave(walk_t, -4, 0.35, axis=2)}}),
            # head lunge with a tongue flick
            "attack": once(0.5, {
                "head": {"rotation": keys((0, Z), (0.15, [15, 0, 0]), (0.5, Z))},
                "tongue": {"rotation": keys((0, Z), (0.1, [-45, 0, 0]), (0.25, [10, 0, 0]), (0.5, Z))},
                "body": {"rotation": keys((0, Z), (0.15, [4, 0, 0]), (0.5, Z))}}),
            # recoil when an arrow bounces off the front
            "deflect": once(0.4, {
                "body": {"rotation": keys((0, Z), (0.1, [-6, 0, 0]), (0.4, Z))},
                "head": {"rotation": keys((0, Z), (0.1, [-10, 0, 0]), (0.4, Z))},
                "mushrooms": {"rotation": keys((0, Z), (0.1, [0, 0, 8]), (0.2, [0, 0, -6]), (0.4, Z))}}),
        },
    }


def scavenger():
    # legless predator: right ear / arm / claw (cubes 5, 7, 9) had drifted behind the body - placed as mirrors of 4, 6, 8;
    # the body floated 5px above the ground with nothing under it - lowered onto the ground
    idle_t, walk_t = 3.0, 1.0
    return {
        "shift": [0, -5, 0],
        # place uses final coordinates (after the -5 lift): mirrors of ear 4 (-7.5, 22, -4.5), arm 6 (-14, 11, -4.5), claw 8
        "place": [(5, [4.5, 22, -4.5]), (7, [8, 11, -4.5]), (9, [13.7, 11.2, -10.8])],
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 0, 0]),
                  ("head", "body", [0, 17, 0]),
                  ("left_arm", "body", [-8, 13.5, -3]),
                  ("right_arm", "body", [8, 13.5, -3])],
        "assign": {"body": [0], "head": [1, 2, 3, 4, 5], "left_arm": [6, 8], "right_arm": [7, 9]},
        "hitbox": (1.0, 1.6),
        "anims": {
            "idle": loop_anim(idle_t, {
                "body": {"position": wave(idle_t, 0.3, 0.0, axis=1)},
                "head": {"rotation": wave(idle_t, 8, 0.0, axis=1)},
                "left_arm": {"rotation": wave(idle_t, 4, 0.0)},
                "right_arm": {"rotation": wave(idle_t, 4, 0.5)}}),
            # no legs: waddles side to side with a little hop, arms pumping
            "walk": loop_anim(walk_t, {
                "body": {"rotation": wave(walk_t, 6, 0.0, axis=2), "position": wave(walk_t / 2, 0.8, 0.25, axis=1)},
                "head": {"rotation": wave(walk_t, -4, 0.0, axis=2)},
                "left_arm": {"rotation": wave(walk_t, 25, 0.0)},
                "right_arm": {"rotation": wave(walk_t, 25, 0.5)}}),
            # double claw swipe
            "attack": once(0.5, {
                "left_arm": {"rotation": keys((0, Z), (0.12, [-50, 0, 0]), (0.25, [30, 0, 0]), (0.5, Z))},
                "right_arm": {"rotation": keys((0, Z), (0.12, [-50, 0, 0]), (0.25, [30, 0, 0]), (0.5, Z))},
                "body": {"rotation": keys((0, Z), (0.25, [10, 0, 0]), (0.5, Z))},
                "head": {"rotation": keys((0, Z), (0.25, [10, 0, 0]), (0.5, Z))}}),
        },
    }


def stalker():
    # shadow assassin: right horn pieces / eye / claws had been turned 90 degrees around the head or body, and the two
    # blade arms were asymmetric (one in front of the chest, one floating 3px off the side). Rebuilt symmetrically:
    # horns and eye mirrored, both blade arms flush with the body sides, three claws hanging under each arm.
    idle_t, walk_t = 3.0, 0.8
    claws_y = 5
    return {
        "place": [(2, [2, 17.2, -1.5]), (4, [3, 17.4, -1.2]),
                  (10, [-7.25, 10, -2.5]), (11, [2.75, 10, -2.5]),
                  (12, [-6.75, claws_y, -2.9]), (13, [-5.5, claws_y, -2.9]), (14, [-4.25, claws_y, -2.9]),
                  (15, [3.25, claws_y, -2.9]), (16, [4.5, claws_y, -2.9]), (17, [5.75, claws_y, -2.9])],
        "reface": [(6, [-1.5, 17.5, -2.5], [1.5, 0.5, 0], {"north": "east", "south": "west"})],
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 9, 0]),
                  ("head", "body", [0, 15, 0]),
                  ("left_arm", "body", [-5, 15, -1.25]),
                  ("right_arm", "body", [5, 15, -1.25]),
                  ("left_leg", "root", [-0.7, 9, 0]),
                  ("right_leg", "root", [0.3, 9, 1])],
        "assign": {"body": [7], "head": [0, 1, 2, 3, 4, 5, 6], "left_arm": [10, 12, 13, 14], "right_arm": [11, 15, 16, 17],
                   "left_leg": [8], "right_leg": [9]},
        "hitbox": (0.8, 1.3),
        "anims": {
            "idle": loop_anim(idle_t, {
                "head": {"rotation": wave(idle_t, 10, 0.0, axis=1)},
                "body": {"position": wave(idle_t, 0.3, 0.0, axis=1)},
                "left_arm": {"rotation": wave(idle_t, 5, 0.0, base=(-10, 0, 0))},
                "right_arm": {"rotation": wave(idle_t, 5, 0.5, base=(-10, 0, 0))}}),
            # low, quick skulk
            "walk": loop_anim(walk_t, {
                "left_leg": {"rotation": wave(walk_t, 30, 0.0)},
                "right_leg": {"rotation": wave(walk_t, 30, 0.5)},
                "body": {"rotation": wave(walk_t / 2, 2, 0.0, base=(10, 0, 0))},
                "head": {"rotation": wave(walk_t / 2, -2, 0.0, base=(-8, 0, 0))},
                "left_arm": {"rotation": wave(walk_t, 15, 0.5, base=(-20, 0, 0))},
                "right_arm": {"rotation": wave(walk_t, 15, 0.0, base=(-20, 0, 0))}}),
            # crossing double slash
            "attack": once(0.5, {
                "left_arm": {"rotation": keys((0, Z), (0.12, [-80, 0, -20]), (0.25, [20, 0, 25]), (0.5, Z))},
                "right_arm": {"rotation": keys((0, Z), (0.12, [-80, 0, 20]), (0.25, [20, 0, -25]), (0.5, Z))},
                "body": {"rotation": keys((0, Z), (0.25, [15, 0, 0]), (0.5, Z))}}),
        },
    }


def quad_walk(period, legs, amp):
    """Diagonal gait: legs = (front_left, front_right, back_right, back_left)."""
    fl, fr, br, bl = legs
    return {fl: {"rotation": wave(period, amp, 0.0)}, br: {"rotation": wave(period, amp, 0.0)},
            fr: {"rotation": wave(period, amp, 0.5)}, bl: {"rotation": wave(period, amp, 0.5)}}


LEGS4 = ("front_left_leg", "front_right_leg", "back_right_leg", "back_left_leg")


def blub():
    idle_t, hop_t = 2.5, 0.45
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 2, 0]),
                  ("left_ear", "body", [-2.5, 9, -3.5]),
                  ("right_ear", "body", [2.5, 9, -3.5]),
                  ("front_left_leg", "root", [-4, 2, -4]), ("front_right_leg", "root", [4, 2, -4]),
                  ("back_right_leg", "root", [4, 2, 4]), ("back_left_leg", "root", [-4, 2, 4])],
        "assign": {"body": [0, 3, 4, 5], "left_ear": [1], "right_ear": [2],
                   "front_left_leg": [6], "front_right_leg": [7], "back_left_leg": [8], "back_right_leg": [9]},
        "hitbox": (0.8, 0.8),
        "anims": {
            # every few seconds a little bounce on the spot (squash - pop up - squash)
            "idle": loop_anim(idle_t, {
                "root": {"position": keys((0, Z), (1.7, Z), (1.85, [0, 1.5, 0]), (2.0, Z), (idle_t, Z))},
                "body": {"scale": keys((0, ONE), (1.6, ONE), (1.68, [1.12, 0.85, 1.12]), (1.82, [0.94, 1.1, 0.94]),
                                       (2.0, [1.1, 0.88, 1.1]), (2.15, ONE), (idle_t, ONE))},
                "left_ear": {"rotation": keys((0, Z), (1.85, [-15, 0, -10]), (2.05, [10, 0, 5]), (2.3, Z), (idle_t, Z))},
                "right_ear": {"rotation": keys((0, Z), (1.85, [-15, 0, 10]), (2.05, [10, 0, -5]), (2.3, Z), (idle_t, Z))}}),
            # bouncy hopping: squash on the ground, stretch in the air, legs tuck, ears flop behind
            "walk": loop_anim(hop_t, {
                "root": {"position": keys((0, Z), (0.08, Z), (0.22, [0, 3.5, 0]), (0.36, Z), (hop_t, Z))},
                "body": {"scale": keys((0, [1.15, 0.82, 1.15]), (0.1, [0.9, 1.15, 0.9]), (0.22, [0.95, 1.08, 0.95]),
                                       (0.36, [1.18, 0.8, 1.18]), (hop_t, [1.15, 0.82, 1.15]))},
                "left_ear": {"rotation": keys((0, [10, 0, -5]), (0.15, [-25, 0, -10]), (0.3, [15, 0, -15]), (hop_t, [10, 0, -5]))},
                "right_ear": {"rotation": keys((0, [10, 0, 5]), (0.15, [-25, 0, 10]), (0.3, [15, 0, 15]), (hop_t, [10, 0, 5]))},
                "front_left_leg": {"rotation": keys((0, Z), (0.22, [-35, 0, 0]), (0.36, Z), (hop_t, Z))},
                "front_right_leg": {"rotation": keys((0, Z), (0.22, [-35, 0, 0]), (0.36, Z), (hop_t, Z))},
                "back_left_leg": {"rotation": keys((0, Z), (0.22, [35, 0, 0]), (0.36, Z), (hop_t, Z))},
                "back_right_leg": {"rotation": keys((0, Z), (0.22, [35, 0, 0]), (0.36, Z), (hop_t, Z))}}),
            # low health (mood controller): ears droop, body slumps
            "sad": loop_anim(2.0, {
                "left_ear": {"rotation": wave(2.0, 4, 0.0, base=(-20, 0, -55))},
                "right_ear": {"rotation": wave(2.0, -4, 0.0, base=(-20, 0, 55))},
                "body": {"position": keys((0, [0, -0.4, 0]), (1.0, [0, -0.6, 0]), (2.0, [0, -0.4, 0])),
                         "scale": keys((0, [1.04, 0.93, 1.04]), (1.0, [1.06, 0.9, 1.06]), (2.0, [1.04, 0.93, 1.04]))}}),
        },
    }


def nuzzle():
    idle_t, walk_t = 3.0, 0.8
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 4, 0]),
                  ("left_antenna", "body", [-4, 20, -5]),
                  ("right_antenna", "body", [4, 20, -5]),
                  ("front_left_leg", "root", [-5, 6, -4]), ("front_right_leg", "root", [5, 6, -4]),
                  ("back_right_leg", "root", [5, 6, 5]), ("back_left_leg", "root", [-5, 6, 5])],
        "assign": {"body": [0, 1, 2, 3, 4], "left_antenna": [5], "right_antenna": [6],
                   "front_left_leg": [7], "front_right_leg": [8], "back_right_leg": [9], "back_left_leg": [10]},
        "hitbox": (1.0, 1.3),
        "anims": {
            "idle": loop_anim(idle_t, {
                "body": {"position": wave(idle_t, 0.3, 0.0, axis=1)},
                "left_antenna": {"rotation": wave(idle_t, 8, 0.0, axis=2)},
                "right_antenna": {"rotation": wave(idle_t, -8, 0.15, axis=2)}}),
            "walk": loop_anim(walk_t, {**quad_walk(walk_t, LEGS4, 30),
                                       "body": {"position": wave(walk_t / 2, 0.6, 0.25, axis=1)},
                                       "left_antenna": {"rotation": wave(walk_t / 2, 12, 0.0)},
                                       "right_antenna": {"rotation": wave(walk_t / 2, 12, 0.1)}}),
            # rubs its face side to side against the player
            "nuzzle": once(1.0, {
                "body": {"rotation": keys((0, Z), (0.2, [10, 0, 10]), (0.4, [10, 0, -10]), (0.6, [10, 0, 10]),
                                          (0.8, [10, 0, -10]), (1.0, Z))},
                "left_antenna": {"rotation": keys((0, Z), (0.2, [0, 0, -20]), (0.6, [0, 0, -20]), (1.0, Z))},
                "right_antenna": {"rotation": keys((0, Z), (0.2, [0, 0, 20]), (0.6, [0, 0, 20]), (1.0, Z))}}),
        },
    }


def lootkin():
    # six-legged runner with a sack on its back and a tall flat crest in front
    idle_t, walk_t = 2.0, 0.45
    tri_a, tri_b = wave(walk_t, 30, 0.0), wave(walk_t, 30, 0.5)
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 3, -3]),
                  ("sack", "body", [0, 5.5, 1]),
                  ("crest", "body", [0, 10, -7]),
                  ("left_front_leg", "root", [-2, 3, -2]), ("right_front_leg", "root", [2, 3, -2]),
                  ("left_middle_leg", "root", [-2, 3, 1]), ("right_middle_leg", "root", [2, 3, 1]),
                  ("right_back_leg", "root", [2, 3, 4]), ("left_back_leg", "root", [-2, 3, 4])],
        "assign": {"body": [0, 8, 9, 10, 11, 12, 13, 14], "sack": [1],
                   "crest": [15, 16, 17, 18, 19, 20, 21, 22, 23],
                   "left_front_leg": [2], "right_front_leg": [3], "left_middle_leg": [4], "right_middle_leg": [5],
                   "right_back_leg": [6], "left_back_leg": [7]},
        "hitbox": (0.6, 0.8),
        "anims": {
            "idle": loop_anim(idle_t, {
                "crest": {"rotation": wave(idle_t, 4, 0.0, axis=2)},
                "sack": {"position": wave(idle_t, 0.2, 0.25, axis=1)},
                "body": {"rotation": wave(idle_t, 3, 0.0, axis=1)}}),
            # tripod gait, scurrying
            "walk": loop_anim(walk_t, {
                "left_front_leg": {"rotation": tri_a}, "right_middle_leg": {"rotation": tri_a},
                "left_back_leg": {"rotation": tri_a},
                "right_front_leg": {"rotation": tri_b}, "left_middle_leg": {"rotation": tri_b},
                "right_back_leg": {"rotation": tri_b},
                "body": {"position": wave(walk_t / 2, 0.4, 0.25, axis=1)},
                "sack": {"rotation": wave(walk_t / 2, 8, 0.3)},
                "crest": {"rotation": wave(walk_t, 10, 0.0, axis=2)}}),
        },
    }


def fusefly():
    # flying bug: no wings, two dangling legs - it bobs in the air; it explodes when it dies
    idle_t, walk_t = 1.6, 0.8
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 3.5, 0]),
                  ("head", "body", [0, 11.5, 0]),
                  ("left_leg", "body", [-1.7, 5, 0]),
                  ("right_leg", "body", [1.7, 5, 0])],
        "assign": {"body": [0], "head": [1, 2, 3, 4, 5, 6, 7], "left_leg": [8], "right_leg": [9]},
        "hitbox": (0.6, 1.0),
        "drop_anims": ["fuse"],   # no more proximity fuse: it explodes when it dies
        "anims": {
            "idle": loop_anim(idle_t, {
                "body": {"position": wave(idle_t, 1.0, 0.0, axis=1)},
                "head": {"rotation": wave(idle_t * 2, 6, 0.0, axis=2)},
                "left_leg": {"rotation": wave(idle_t, 12, 0.0)},
                "right_leg": {"rotation": wave(idle_t, 12, 0.3)}}),
            "walk": loop_anim(walk_t, {
                "body": {"rotation": keys((0, [15, 0, 0]), (walk_t, [15, 0, 0])),
                         "position": wave(walk_t, 1.0, 0.0, axis=1)},
                "left_leg": {"rotation": wave(walk_t, 20, 0.0, base=(-20, 0, 0))},
                "right_leg": {"rotation": wave(walk_t, 20, 0.3, base=(-20, 0, 0))}}),
            # death: the body balloons into a ~0.9-block cube in faster and faster pulses and holds; FuseflyEntity
            # bursts on death tick 18 (0.9 s). Head and legs get the inverse scale so they keep their size.
            "death": once(1.0, {
                "body": {"scale": keys((0.0, [1.0, 1.0, 1.0]), (0.12, [1.35, 1.2, 1.35]), (0.22, [1.168, 1.096, 1.168]), (0.32, [1.63, 1.36, 1.63]), (0.4, [1.42, 1.24, 1.42]), (0.48, [1.868, 1.496, 1.868]), (0.55, [1.7, 1.4, 1.7]), (0.62, [2.092, 1.624, 2.092]), (0.68, [1.952, 1.544, 1.952]), (0.74, [2.26, 1.72, 2.26]), (0.8, [2.19, 1.68, 2.19]), (0.86, [2.4, 1.8, 2.4]), (1.0, [2.4, 1.8, 2.4])),
                         "rotation": keys((0, Z), (0.2, [0, 0, 6]), (0.35, [0, 0, -6]), (0.5, [0, 0, 8]),
                                          (0.6, [0, 0, -8]), (0.7, [0, 0, 6]), (0.8, [0, 0, -6]), (0.86, Z))},
                "head": {"scale": keys((0.0, [1.0, 1.0, 1.0]), (0.12, [0.741, 0.833, 0.741]), (0.22, [0.856, 0.912, 0.856]), (0.32, [0.613, 0.735, 0.613]), (0.4, [0.704, 0.806, 0.704]), (0.48, [0.535, 0.668, 0.535]), (0.55, [0.588, 0.714, 0.588]), (0.62, [0.478, 0.616, 0.478]), (0.68, [0.512, 0.648, 0.512]), (0.74, [0.442, 0.581, 0.442]), (0.8, [0.457, 0.595, 0.457]), (0.86, [0.417, 0.556, 0.417]), (1.0, [0.417, 0.556, 0.417]))},
                "left_leg": {"scale": keys((0.0, [1.0, 1.0, 1.0]), (0.12, [0.741, 0.833, 0.741]), (0.22, [0.856, 0.912, 0.856]), (0.32, [0.613, 0.735, 0.613]), (0.4, [0.704, 0.806, 0.704]), (0.48, [0.535, 0.668, 0.535]), (0.55, [0.588, 0.714, 0.588]), (0.62, [0.478, 0.616, 0.478]), (0.68, [0.512, 0.648, 0.512]), (0.74, [0.442, 0.581, 0.442]), (0.8, [0.457, 0.595, 0.457]), (0.86, [0.417, 0.556, 0.417]), (1.0, [0.417, 0.556, 0.417])), "rotation": keys((0, Z), (0.86, [0, 0, -40]))},
                "right_leg": {"scale": keys((0.0, [1.0, 1.0, 1.0]), (0.12, [0.741, 0.833, 0.741]), (0.22, [0.856, 0.912, 0.856]), (0.32, [0.613, 0.735, 0.613]), (0.4, [0.704, 0.806, 0.704]), (0.48, [0.535, 0.668, 0.535]), (0.55, [0.588, 0.714, 0.588]), (0.62, [0.478, 0.616, 0.478]), (0.68, [0.512, 0.648, 0.512]), (0.74, [0.442, 0.581, 0.442]), (0.8, [0.457, 0.595, 0.457]), (0.86, [0.417, 0.556, 0.417]), (1.0, [0.417, 0.556, 0.417])), "rotation": keys((0, Z), (0.86, [0, 0, 40]))}}, hold=True),
            # bite
            "attack": once(0.4, {
                "body": {"rotation": keys((0, Z), (0.12, [25, 0, 0]), (0.4, Z))},
                "head": {"rotation": keys((0, Z), (0.12, [15, 0, 0]), (0.4, Z))}}),
        },
    }


def dartback():
    # six-legged spiky lizard; scaled up x3.15 in game (Attributes.SCALE) so it stands ~2 blocks tall
    idle_t, walk_t = 2.5, 0.5
    tri_a, tri_b = wave(walk_t, 30, 0.0), wave(walk_t, 30, 0.5)
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 2, 0.7]),
                  ("head", "body", [0, 5, -2.8]),
                  ("back_spikes", "body", [0, 8, 1]),
                  ("tail", "body", [0, 3.4, 4.2]),
                  ("tail_tip", "tail", [0, 3.4, 7]),
                  ("left_front_leg", "root", [-2, 2.2, -4.1]), ("right_front_leg", "root", [2, 2.2, -4.1]),
                  ("left_middle_leg", "root", [-1.8, 2.2, -0.7]), ("right_middle_leg", "root", [1.8, 2.2, -0.7]),
                  ("left_back_leg", "root", [-1.8, 2.2, 2.9]), ("right_back_leg", "root", [1.8, 2.2, 2.9])],
        "assign": {"body": [6], "head": [0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 27, 28, 29, 30, 31],
                   "back_spikes": [32, 33, 34, 35], "tail": [7, 36, 37], "tail_tip": [8],
                   "left_front_leg": [22], "right_front_leg": [21], "left_middle_leg": [23], "right_middle_leg": [24],
                   "left_back_leg": [25], "right_back_leg": [26]},
        "hitbox": (0.6, 0.53),   # base size up to the body top (not the thin spikes); x3.15 scale -> about 1.9 x 1.67
        "anims": {
            "idle": loop_anim(idle_t, {
                "tail": {"rotation": wave(idle_t, 10, 0.0, axis=1)},
                "tail_tip": {"rotation": wave(idle_t, 14, 0.15, axis=1)},
                "head": {"rotation": wave(idle_t, 3, 0.25)},
                "back_spikes": {"rotation": wave(idle_t, 2, 0.5)}}),
            "walk": loop_anim(walk_t, {
                "left_front_leg": {"rotation": tri_a}, "right_middle_leg": {"rotation": tri_a},
                "left_back_leg": {"rotation": tri_a},
                "right_front_leg": {"rotation": tri_b}, "left_middle_leg": {"rotation": tri_b},
                "right_back_leg": {"rotation": tri_b},
                "body": {"rotation": wave(walk_t, 4, 0.0, axis=1), "position": wave(walk_t / 2, 0.2, 0.25, axis=1)},
                "head": {"rotation": wave(walk_t, -4, 0.0, axis=1)},
                "tail": {"rotation": wave(walk_t, 12, 0.1, axis=1)},
                "tail_tip": {"rotation": wave(walk_t, 16, 0.25, axis=1)}}),
            # spikes bristle back, then flick forward as the dart flies (impact at 0.4 s)
            "shoot": once(0.8, {
                "back_spikes": {"rotation": keys((0, Z), (0.3, [-25, 0, 0]), (0.4, [20, 0, 0]), (0.8, Z))},
                "body": {"rotation": keys((0, Z), (0.3, [-6, 0, 0]), (0.4, [4, 0, 0]), (0.8, Z))},
                "head": {"rotation": keys((0, Z), (0.3, [8, 0, 0]), (0.8, Z))},
                "tail": {"rotation": keys((0, Z), (0.3, [-15, 0, 0]), (0.4, [10, 0, 0]), (0.8, Z))}}),
        },
    }


def hurler():
    # armless heavy thrower: the whole body heaves the rock; ears and back hump wobble
    idle_t, walk_t = 3.0, 1.0
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 6, 0]),
                  ("left_ear", "body", [-6.5, 12, 2.8]),
                  ("right_ear", "body", [6.5, 12, 2.8]),
                  ("hump", "body", [0, 10.5, 5.5]),
                  ("left_leg", "root", [-5.5, 6, 1]),
                  ("right_leg", "root", [5.5, 6, 1])],
        "assign": {"body": [0, 1, 2], "left_ear": [5], "right_ear": [6], "hump": [7, 8, 9],
                   "left_leg": [3], "right_leg": [4]},
        "hitbox": (1.0, 1.0),
        "anims": {
            "idle": loop_anim(idle_t, {
                "body": {"position": wave(idle_t, 0.3, 0.0, axis=1)},
                "left_ear": {"rotation": wave(idle_t, 8, 0.0, axis=2)},
                "right_ear": {"rotation": wave(idle_t, -8, 0.1, axis=2)},
                "hump": {"rotation": wave(idle_t, 3, 0.3)}}),
            # heavy waddle
            "walk": loop_anim(walk_t, {
                "left_leg": {"rotation": wave(walk_t, 25, 0.0)},
                "right_leg": {"rotation": wave(walk_t, 25, 0.5)},
                "body": {"rotation": wave(walk_t, 5, 0.25, axis=2), "position": wave(walk_t / 2, 0.5, 0.25, axis=1)},
                "left_ear": {"rotation": wave(walk_t / 2, 10, 0.0, axis=2)},
                "right_ear": {"rotation": wave(walk_t / 2, -10, 0.0, axis=2)},
                "hump": {"rotation": wave(walk_t / 2, 5, 0.3)}}),
            # rear back, then heave forward (rock released at 0.7 s)
            "throw": once(1.2, {
                "body": {"rotation": keys((0, Z), (0.5, [-25, 0, 0]), (0.75, [30, 0, 0]), (1.2, Z)),
                         "position": keys((0, Z), (0.5, [0, -1, 0]), (0.75, [0, 0.5, 0]), (1.2, Z))},
                "left_ear": {"rotation": keys((0, Z), (0.5, [0, 0, 25]), (0.75, [0, 0, -20]), (1.2, Z))},
                "right_ear": {"rotation": keys((0, Z), (0.5, [0, 0, -25]), (0.75, [0, 0, 20]), (1.2, Z))},
                "hump": {"rotation": keys((0, Z), (0.55, [10, 0, 0]), (0.8, [-15, 0, 0]), (1.2, Z))},
                "left_leg": {"rotation": keys((0, Z), (0.5, [20, 0, 0]), (0.75, [-15, 0, 0]), (1.2, Z))},
                "right_leg": {"rotation": keys((0, Z), (0.5, [20, 0, 0]), (0.75, [-15, 0, 0]), (1.2, Z))}}),
            # body slam
            "attack": once(0.5, {
                "body": {"rotation": keys((0, Z), (0.15, [-10, 0, 0]), (0.3, [20, 0, 0]), (0.5, Z))}}),
        },
    }


def pollinator():
    # ground bug (it does not fly): the top layer (eyes + the big sail-wing) is an upper jaw hinged at the back;
    # the mouth line stays on the body
    idle_t, walk_t = 2.5, 0.7
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 4, 0]),
                  ("head", "body", [0, 18, 6]),
                  ("wing", "head", [0, 23, 4.5]),
                  ("front_left_leg", "root", [-3, 5, -2.5]), ("front_right_leg", "root", [3, 5, -2.5]),
                  ("back_left_leg", "root", [-3, 5, 2.5]), ("back_right_leg", "root", [3, 5, 2.5])],
        "assign": {"body": [0, 8], "head": [1, 2, 3, 4, 5, 6, 7], "wing": [9],
                   "front_left_leg": [10], "front_right_leg": [11], "back_left_leg": [12], "back_right_leg": [13]},
        "hitbox": (0.8, 1.5),
        "anims": {
            "idle": loop_anim(idle_t, {
                "body": {"position": wave(idle_t, 0.3, 0.0, axis=1)},
                "head": {"rotation": keys((0, Z), (1.4, Z), (1.55, [-18, 0, 0]), (1.75, Z), (idle_t, Z))},
                "wing": {"rotation": wave(idle_t, 6, 0.0, axis=2)}}),
            "walk": loop_anim(walk_t, {**quad_walk(walk_t, ("front_left_leg", "front_right_leg", "back_right_leg",
                                                             "back_left_leg"), 28),
                                       "body": {"position": wave(walk_t / 2, 0.5, 0.25, axis=1),
                                                "rotation": wave(walk_t, 3, 0.25, axis=2)},
                                       "head": {"rotation": wave(walk_t, 5, 0.0, base=(-4, 0, 0))},
                                       "wing": {"rotation": wave(walk_t / 2, 10, 0.0, axis=2)}}),
            # lunging bite (the sting): mouth gapes, then snaps shut
            "sting": once(0.5, {
                "body": {"rotation": keys((0, Z), (0.2, [20, 0, 0]), (0.5, Z))},
                "head": {"rotation": keys((0, Z), (0.12, [-40, 0, 0]), (0.22, [3, 0, 0]), (0.5, Z))},
                "wing": {"rotation": keys((0, Z), (0.12, [0, 0, 20]), (0.22, [0, 0, -15]), (0.5, Z))}}),
            # bends over the plant and breathes on it, wing fluttering
            "pollinate": once(1.0, {
                "body": {"rotation": keys((0, Z), (0.3, [18, 0, 0]), (0.8, [18, 0, 0]), (1.0, Z))},
                "head": {"rotation": keys((0, Z), (0.3, [-25, 0, 0]), (0.8, [-25, 0, 0]), (1.0, Z))},
                "wing": {"rotation": keys((0, Z), (0.2, [0, 0, 20]), (0.35, [0, 0, -20]), (0.5, [0, 0, 20]),
                                          (0.65, [0, 0, -20]), (0.8, [0, 0, 20]), (1.0, Z))}}),
        },
    }


def nester():
    # brood mother: head with a lower jaw and two antennae on a thin neck-body, four thin legs (back legs splayed back);
    # scaled x1.67 in game (Attributes.SCALE) so the body (without antennae) is 1.8 blocks tall
    idle_t, walk_t = 3.0, 0.8
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 7.2, 0]),
                  ("head", "body", [0, 12.2, 0]),
                  ("jaw", "head", [0, 14.7, 3.7]),
                  ("front_left_leg", "root", [-1.5, 8.5, -1.75]), ("front_right_leg", "root", [1.5, 8.5, -1.75]),
                  ("back_left_leg", "root", [-1.5, 8, 3.75]), ("back_right_leg", "root", [1.5, 8, 3.75])],
        "assign": {"body": [10], "head": [1, 2, 3, 4, 5, 6, 7, 8, 9], "jaw": [0],
                   "front_left_leg": [11], "front_right_leg": [12], "back_left_leg": [13], "back_right_leg": [14]},
        "hitbox": (0.6, 1.08),   # base size; x1.67 scale -> 1.0 x 1.8
        "anims": {
            # looks around and works its jaw
            "idle": loop_anim(idle_t, {
                "head": {"rotation": wave(idle_t, 8, 0.0, axis=1)},
                "jaw": {"rotation": keys((0, Z), (0.5, [25, 0, 0]), (0.8, Z), (1.1, [15, 0, 0]), (1.3, Z),
                                         (2.2, Z), (2.5, [30, 0, 0]), (2.8, Z), (idle_t, Z))},
                "body": {"position": wave(idle_t, 0.3, 0.0, axis=1)}}),
            "walk": loop_anim(walk_t, {**quad_walk(walk_t, LEGS4, 25),
                                       "head": {"rotation": wave(walk_t / 2, 4, 0.0)},
                                       "jaw": {"rotation": wave(walk_t / 2, 10, 0.0, base=(10, 0, 0))},
                                       "body": {"position": wave(walk_t / 2, 0.4, 0.25, axis=1)}}),
            # rears its head back, jaw wide open, then calls the brood
            "summon": once(1.0, {
                "head": {"rotation": keys((0, Z), (0.3, [-25, 0, 0]), (0.7, [-20, 0, 0]), (1.0, Z))},
                "jaw": {"rotation": keys((0, Z), (0.3, [45, 0, 0]), (0.7, [40, 0, 0]), (1.0, Z))},
                "body": {"scale": keys((0, ONE), (0.4, [1.15, 1.05, 1.15]), (0.7, [1.1, 1.05, 1.1]), (1.0, ONE))}}),
            # peck with a big jaw snap
            "attack": once(0.5, {
                "head": {"rotation": keys((0, Z), (0.15, [25, 0, 0]), (0.5, Z))},
                "jaw": {"rotation": keys((0, Z), (0.1, [45, 0, 0]), (0.2, Z), (0.5, Z))}}),
        },
    }


def seedling():
    # small swarmling: the green top layer (eyes, leaf tufts) is an upper jaw hinged at the back - the mouth opens
    # between it and the lower body
    idle_t, walk_t = 2.0, 0.5
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 4, 0]),
                  ("upper_jaw", "body", [0, 8, 5]),
                  ("left_leaf", "upper_jaw", [-5, 12, 4]),
                  ("right_leaf", "upper_jaw", [5, 12, 4]),
                  ("front_left_leg", "root", [-2.5, 5, -1.7]), ("front_right_leg", "root", [2.5, 5, -1.7]),
                  ("back_left_leg", "root", [-2.5, 5, 3.3]), ("back_right_leg", "root", [2.5, 5, 3.3])],
        "assign": {"body": [0], "upper_jaw": [1, 2, 3, 4, 5, 6, 7], "left_leaf": [8, 9], "right_leaf": [10, 11],
                   "front_left_leg": [12], "front_right_leg": [13], "back_left_leg": [14], "back_right_leg": [15]},
        "hitbox": (0.6, 0.8),
        "anims": {
            "idle": loop_anim(idle_t, {
                "body": {"position": wave(idle_t, 0.3, 0.0, axis=1)},
                "upper_jaw": {"rotation": keys((0, Z), (0.9, Z), (1.05, [-20, 0, 0]), (1.2, Z), (1.3, [-12, 0, 0]),
                                               (1.45, Z), (idle_t, Z))},
                "left_leaf": {"rotation": wave(idle_t, 10, 0.0, axis=2)},
                "right_leaf": {"rotation": wave(idle_t, -10, 0.1, axis=2)}}),
            "walk": loop_anim(walk_t, {**quad_walk(walk_t, LEGS4, 35),
                                       "body": {"position": wave(walk_t / 2, 0.5, 0.25, axis=1)},
                                       "upper_jaw": {"rotation": wave(walk_t, 6, 0.0, base=(-6, 0, 0))},
                                       "left_leaf": {"rotation": wave(walk_t / 2, 15, 0.0, axis=2)},
                                       "right_leaf": {"rotation": wave(walk_t / 2, -15, 0.0, axis=2)}}),
            # pounce: mouth gapes on the way in and snaps shut on the bite
            "attack": once(0.4, {
                "body": {"rotation": keys((0, Z), (0.1, [-12, 0, 0]), (0.2, [22, 0, 0]), (0.4, Z))},
                "upper_jaw": {"rotation": keys((0, Z), (0.12, [-45, 0, 0]), (0.2, [3, 0, 0]), (0.4, Z))},
                "left_leaf": {"rotation": keys((0, Z), (0.2, [0, 0, -25]), (0.4, Z))},
                "right_leaf": {"rotation": keys((0, Z), (0.2, [0, 0, 25]), (0.4, Z))},
                "front_left_leg": {"rotation": keys((0, Z), (0.2, [-40, 0, 0]), (0.4, Z))},
                "front_right_leg": {"rotation": keys((0, Z), (0.2, [-40, 0, 0]), (0.4, Z))}}),
        },
    }


def sprout():
    # a head carried on five long root legs (four corners + one in the middle)
    idle_t, walk_t = 2.5, 0.6
    a, b = wave(walk_t, 20, 0.0), wave(walk_t, 20, 0.5)
    return {
        "shift": [0, -1.05, 0],   # the root feet floated 1px above the ground
        "bones": [("root", None, [0, 0, 0]),
                  ("head", "root", [0, 16.45, 0]),
                  ("front_left_leg", "root", [-4, 16.45, -2]), ("front_right_leg", "root", [3, 16.45, -2]),
                  ("back_left_leg", "root", [-4, 16.45, 2]), ("back_right_leg", "root", [3, 16.45, 2]),
                  ("middle_leg", "root", [-1, 16.45, -0.5])],
        "assign": {"head": [0, 1, 2], "front_left_leg": [3, 4, 5, 6], "front_right_leg": [7, 8, 9, 10],
                   "back_left_leg": [11, 12, 13, 14], "back_right_leg": [15, 16, 17, 18], "middle_leg": [19, 20, 21, 22]},
        "hitbox": (0.7, 1.6),
        "anims": {
            "idle": loop_anim(idle_t, {
                "head": {"position": wave(idle_t, 0.5, 0.0, axis=1), "rotation": wave(idle_t, 3, 0.25, axis=2)},
                "front_left_leg": {"rotation": wave(idle_t, 3, 0.0, axis=2)},
                "front_right_leg": {"rotation": wave(idle_t, -3, 0.0, axis=2)},
                "back_left_leg": {"rotation": wave(idle_t, 3, 0.5, axis=2)},
                "back_right_leg": {"rotation": wave(idle_t, -3, 0.5, axis=2)}}),
            # spidery stride
            "walk": loop_anim(walk_t, {
                "front_left_leg": {"rotation": a}, "back_right_leg": {"rotation": a}, "middle_leg": {"rotation": a},
                "front_right_leg": {"rotation": b}, "back_left_leg": {"rotation": b},
                "head": {"position": wave(walk_t / 2, 0.8, 0.25, axis=1), "rotation": wave(walk_t, 4, 0.0, axis=2)}}),
            # head lunges down, front legs rear up
            "attack": once(0.4, {
                "head": {"rotation": keys((0, Z), (0.15, [20, 0, 0]), (0.4, Z)),
                         "position": keys((0, Z), (0.15, [0, -2, 0]), (0.4, Z))},
                "front_left_leg": {"rotation": keys((0, Z), (0.15, [-30, 0, 0]), (0.4, Z))},
                "front_right_leg": {"rotation": keys((0, Z), (0.15, [-30, 0, 0]), (0.4, Z))}}),
        },
    }


def prickle():
    # hedgehog: snout + ears on the head, five flat feet on each side
    idle_t, walk_t = 2.5, 0.6
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 0, 0]),
                  ("head", "body", [0, 3.5, -5.2]),
                  ("left_ear", "head", [-2.5, 7, -5.2]),
                  ("right_ear", "head", [2.5, 7, -5.2]),
                  ("left_feet", "root", [-3.5, 0, 0]),
                  ("right_feet", "root", [3.5, 0, 0])],
        "assign": {"body": [1], "head": [0, 2, 3, 4], "left_ear": [5], "right_ear": [6],
                   "left_feet": [7, 9, 11, 13, 15], "right_feet": [8, 10, 12, 14, 16]},
        "hitbox": (0.6, 0.8),
        "anims": {
            "idle": loop_anim(idle_t, {
                "body": {"scale": keys((0, ONE), (1.25, [1.02, 1.04, 1.02]), (idle_t, ONE))},
                "head": {"rotation": wave(idle_t, 5, 0.0, axis=1)},
                "left_ear": {"rotation": keys((0, Z), (1.9, Z), (2.0, [0, 0, -15]), (2.1, Z), (idle_t, Z))},
                "right_ear": {"rotation": keys((0, Z), (1.95, Z), (2.05, [0, 0, 15]), (2.15, Z), (idle_t, Z))}}),
            # waddle with paddling feet
            "walk": loop_anim(walk_t, {
                "body": {"rotation": wave(walk_t, 4, 0.0, axis=2), "position": wave(walk_t / 2, 0.4, 0.25, axis=1)},
                "head": {"rotation": wave(walk_t, -3, 0.0, axis=2)},
                "left_feet": {"rotation": wave(walk_t, 12, 0.0, axis=2)},
                "right_feet": {"rotation": wave(walk_t, -12, 0.5, axis=2)}}),
            # puffs its spines out
            "bristle": once(0.5, {
                "body": {"scale": keys((0, ONE), (0.1, [1.3, 1.35, 1.3]), (0.5, ONE))},
                "left_ear": {"rotation": keys((0, Z), (0.1, [0, 0, -25]), (0.5, Z))},
                "right_ear": {"rotation": keys((0, Z), (0.1, [0, 0, 25]), (0.5, Z))}}),
        },
    }


def sentinel():
    # crested sentinel: a wide disc-shaped helmet head with a feather fringe on a short neck, four legs.
    # The "heavy blade" is the disc itself: the slash spins it around.
    idle_t, walk_t = 3.0, 0.8
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 7, 0]),
                  ("head", "body", [0, 11, 0]),
                  ("crest", "head", [0, 11, 0]),
                  ("front_left_leg", "root", [-1.5, 7, -1.5]), ("front_right_leg", "root", [1.5, 7, -1.5]),
                  ("back_left_leg", "root", [-1.5, 7, 2.5]), ("back_right_leg", "root", [1.5, 7, 2.5])],
        "assign": {"body": [10], "head": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                   "crest": [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26],
                   "front_left_leg": [14], "front_right_leg": [13], "back_left_leg": [11], "back_right_leg": [12]},
        "hitbox": (0.6, 0.9),
        "anims": {
            "idle": loop_anim(idle_t, {
                "head": {"rotation": wave(idle_t, 15, 0.0, axis=1)},
                "crest": {"scale": keys((0, ONE), (1.5, [1.05, 1, 1.05]), (idle_t, ONE))},
                "body": {"position": wave(idle_t, 0.2, 0.0, axis=1)}}),
            "walk": loop_anim(walk_t, {**quad_walk(walk_t, LEGS4, 25),
                                       "body": {"position": wave(walk_t / 2, 0.4, 0.25, axis=1)},
                                       "head": {"rotation": wave(walk_t / 2, 3, 0.0)}}),
            # wind the disc back, then spin it through (hit at 0.8 s)
            "slash": once(1.3, {
                "head": {"rotation": keys((0, Z), (0.6, [-10, -70, 0]), (0.85, [15, 120, 0]), (1.0, [5, 160, 0]), (1.3, [0, 360, 0]))},
                "crest": {"scale": keys((0, ONE), (0.6, [1.15, 1, 1.15]), (0.85, [1.3, 1, 1.3]), (1.3, ONE))},
                "body": {"rotation": keys((0, Z), (0.6, [-8, -20, 0]), (0.85, [10, 25, 0]), (1.3, Z))}}),
            # quick disc jab
            "attack": once(0.5, {
                "head": {"rotation": keys((0, Z), (0.15, [20, 45, 0]), (0.5, Z))},
                "body": {"rotation": keys((0, Z), (0.15, [10, 0, 0]), (0.5, Z))}}),
        },
    }


def tuner():
    # legless resonator: a tall body with a fin on top and four petals hanging from the bottom edges of the body,
    # flared down and outward like an upside-down flower; it glides on the petal tips (model lifted 5.6px)
    idle_t, walk_t = 3.0, 0.8
    h = 5.6
    return {
        "shift": [0, h, 0],
        # each petal is first laid out pointing up from its hinge on the body's bottom edge, then turned 142.5 deg
        # so it hangs down and 37.5 deg outward with the petal tip (texture top) at the free end
        "pose": [(2, [-5, h, -5], [142.5, 0, 0], [0, h, -5]),
                 (3, [-5, h, 5], [-142.5, 0, 0], [0, h, 5]),
                 (4, [5, h, -5], [0, 0, 142.5], [5, h, 0]),
                 (5, [-5, h, -5], [0, 0, -142.5], [-5, h, 0])],
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, h, 0]),
                  ("fin", "body", [0, 15 + h, 1]),
                  ("front_flap", "body", [0, h, -5]),
                  ("back_flap", "body", [0, h, 5]),
                  ("right_flap", "body", [5, h, 0]),
                  ("left_flap", "body", [-5, h, 0])],
        "assign": {"body": [0], "fin": [1], "front_flap": [2], "back_flap": [3], "right_flap": [4], "left_flap": [5]},
        "hitbox": (0.7, 1.3),
        "anims": {
            "idle": loop_anim(idle_t, {
                "body": {"position": wave(idle_t, 0.4, 0.0, axis=1)},
                "fin": {"rotation": wave(idle_t, 8, 0.0, axis=2)},
                "front_flap": {"rotation": wave(idle_t, 5, 0.0)},
                "back_flap": {"rotation": wave(idle_t, -5, 0.0)},
                "right_flap": {"rotation": wave(idle_t, 5, 0.0, axis=2)},
                "left_flap": {"rotation": wave(idle_t, -5, 0.0, axis=2)}}),
            # glides with a gentle bob, flaps rippling
            "walk": loop_anim(walk_t, {
                "body": {"position": wave(walk_t, 0.8, 0.0, axis=1), "rotation": wave(walk_t, 4, 0.25)},
                "fin": {"rotation": wave(walk_t, 10, 0.1)},
                "front_flap": {"rotation": wave(walk_t, 10, 0.0)},
                "back_flap": {"rotation": wave(walk_t, -10, 0.25)},
                "right_flap": {"rotation": wave(walk_t, 10, 0.5, axis=2)},
                "left_flap": {"rotation": wave(walk_t, -10, 0.75, axis=2)}}),
            # spins once, flaps fanning open and closed, fin ringing
            "aura": once(1.0, {
                "body": {"rotation": keys((0, Z), (0.5, [0, 180, 0]), (1.0, [0, 360, 0])),
                         "scale": keys((0, ONE), (0.3, [1.12, 1.12, 1.12]), (1.0, ONE))},
                "fin": {"rotation": keys((0, Z), (0.15, [0, 0, 20]), (0.3, [0, 0, -20]), (0.45, [0, 0, 15]),
                                         (0.6, [0, 0, -15]), (1.0, Z))},
                "front_flap": {"rotation": keys((0, Z), (0.3, [25, 0, 0]), (0.6, [-10, 0, 0]), (1.0, Z))},
                "back_flap": {"rotation": keys((0, Z), (0.3, [-25, 0, 0]), (0.6, [10, 0, 0]), (1.0, Z))},
                "right_flap": {"rotation": keys((0, Z), (0.3, [0, 0, 25]), (0.6, [0, 0, -10]), (1.0, Z))},
                "left_flap": {"rotation": keys((0, Z), (0.3, [0, 0, -25]), (0.6, [0, 0, 10]), (1.0, Z))}}),
        },
    }


def wobble():
    # wobbly blob: body with a snout, two stubby feet at the sides; sways as it walks and bounces when it dies
    idle_t, walk_t = 2.5, 0.9
    return {
        "bones": [("root", None, [0, 0, 0]),
                  ("body", "root", [0, 0, 0]),
                  ("snout", "body", [0, 9, -2]),
                  ("left_foot", "root", [-8, 2, 0]),
                  ("right_foot", "root", [8, 2, 0])],
        "assign": {"body": [0, 2, 3, 4, 5, 6], "snout": [1], "left_foot": [7], "right_foot": [8]},
        "hitbox": (0.8, 0.85),
        "anims": {
            "idle": loop_anim(idle_t, {
                "body": {"rotation": wave(idle_t, 4, 0.0, axis=2),
                         "scale": keys((0, ONE), (1.25, [1.04, 0.96, 1.04]), (idle_t, ONE))},
                "snout": {"rotation": wave(idle_t, 5, 0.25)}}),
            # big side-to-side wobble, feet stepping in turn
            "walk": loop_anim(walk_t, {
                "body": {"rotation": wave(walk_t, 12, 0.0, axis=2), "position": wave(walk_t / 2, 0.6, 0.25, axis=1)},
                "snout": {"rotation": wave(walk_t, -6, 0.0, axis=2)},
                "left_foot": {"rotation": wave(walk_t, 25, 0.0)},
                "right_foot": {"rotation": wave(walk_t, 25, 0.5)}}),
            # headbutt with the snout
            "attack": once(0.5, {
                "body": {"rotation": keys((0, Z), (0.15, [-8, 0, 0]), (0.28, [18, 0, 0]), (0.5, Z))},
                "snout": {"rotation": keys((0, Z), (0.28, [15, 0, 0]), (0.5, Z))}}),
            # slime-like bounce, squash, then flops over (held)
            "death": once(1.0, {
                "root": {"position": keys((0, Z), (0.3, [0, 8, 0]), (0.6, Z))},
                "body": {"scale": keys((0, ONE), (0.3, [0.85, 1.2, 0.85]), (0.7, [1.3, 0.6, 1.3]), (1.0, [1.2, 0.7, 1.2])),
                         "rotation": keys((0, Z), (0.7, Z), (1.0, [0, 0, 90]))},
                "left_foot": {"rotation": keys((0, Z), (0.3, [0, 0, -30]), (1.0, [0, 0, -60]))},
                "right_foot": {"rotation": keys((0, Z), (0.3, [0, 0, 30]), (1.0, [0, 0, 60]))}}, hold=True),
        },
    }


RIGS = {"singer": singer, "roamroot": roamroot, "bloombud": bloombud, "slabber": slabber, "scavenger": scavenger,
        "stalker": stalker, "blub": blub, "nuzzle": nuzzle, "lootkin": lootkin, "fusefly": fusefly,
        "dartback": dartback, "hurler": hurler, "pollinator": pollinator, "nester": nester, "seedling": seedling,
        "sprout": sprout, "prickle": prickle, "sentinel": sentinel, "tuner": tuner, "wobble": wobble}


# ------------------------------------------------------------------------------------------------ build
def all_cubes(geo):
    return [c for b in geo["bones"] for c in b.get("cubes", [])]


def move_cube(c, d):
    c["origin"] = [round(c["origin"][i] + d[i], 4) for i in range(3)]
    if "pivot" in c:
        c["pivot"] = [round(c["pivot"][i] + d[i], 4) for i in range(3)]


def build(spec, geo_doc):
    doc = copy.deepcopy(geo_doc)
    geo = doc["minecraft:geometry"][0]
    cubes = all_cubes(geo)
    for idx, d in spec.get("move", []):
        for i in idx:
            move_cube(cubes[i], d)
    if spec.get("shift"):
        for c in cubes:
            move_cube(c, spec["shift"])
    for i, new_rot in spec.get("rerotate", []):
        c = cubes[i]
        (x, y, z), (w, h, d) = c["origin"], c["size"]
        bottom = (x + w / 2, y, z + d / 2)
        joint = rot_point(bottom, c.get("pivot", [0, 0, 0]), c.get("rotation", [0, 0, 0])) if c.get("rotation") else bottom
        move_cube(c, [joint[k] - bottom[k] for k in range(3)])
        c["pivot"] = [round(v, 4) for v in joint]
        c["rotation"] = list(new_rot)
        (x, y, z), (w, h, d) = c["origin"], c["size"]
        top = rot_point((x + w / 2, y + h, z + d / 2), c["pivot"], c["rotation"])
        print(f"  cube {i}: rotation {new_rot} about {c['pivot']}; top centre now {[round(v, 2) for v in top]}")
    for i, origin, size, faces in spec.get("reface", []):
        c = cubes[i]
        c["origin"], c["size"] = list(origin), list(size)
        c.pop("rotation", None)
        c.pop("pivot", None)
        c["uv"] = {new: c["uv"][old] for new, old in faces.items() if old in c["uv"]}
    for i, origin, rotation, pivot in spec.get("pose", []):
        c = cubes[i]
        c["origin"], c["rotation"], c["pivot"] = list(origin), list(rotation), list(pivot)
    for i, origin in spec.get("place", []):
        c = cubes[i]
        c["origin"] = list(origin)
        c.pop("rotation", None)
        c.pop("pivot", None)
    owner = {}
    for bone, idx in spec["assign"].items():
        for i in idx:
            if i in owner:
                raise SystemExit(f"cube {i} assigned to both {owner[i]} and {bone}")
            owner[i] = bone
    bones = []
    for name, parent, pivot in spec["bones"]:
        b = {"name": name, "pivot": pivot}
        if parent:
            b["parent"] = parent
        b["cubes"] = [c for i, c in enumerate(cubes) if owner.get(i, "root") == name]
        if not b["cubes"]:
            del b["cubes"]
        bones.append(b)
    geo["bones"] = bones
    return doc, len(cubes)


def main():
    if MOB not in RIGS:
        raise SystemExit(f"no rig spec for {MOB}; have {sorted(RIGS)}")
    spec = RIGS[MOB]()
    geo_doc = json.loads(GEO.read_text(encoding="utf-8"))
    anim_doc = json.loads(ANIM.read_text(encoding="utf-8"))
    tex = Image.open(TEX).convert("RGBA")
    if any(b.get("parent") for b in geo_doc["minecraft:geometry"][0]["bones"]):
        raise SystemExit(f"{MOB} is already rigged (has child bones); restore the backup to re-run")

    new_doc, n_before = build(spec, geo_doc)
    geo = new_doc["minecraft:geometry"][0]
    n_after = len(all_cubes(geo))
    ys = [c["origin"][1] for c in all_cubes(geo)]
    tops = [c["origin"][1] + c["size"][1] for c in all_cubes(geo)]
    names = {b["name"] for b in geo["bones"]}
    for key in list(anim_doc["animations"]):
        if not key.startswith("animation."):
            del anim_doc["animations"][key]   # drop the duplicated short-name copies left by the old converter
    for name in spec.get("drop_anims", []):
        anim_doc["animations"].pop(f"animation.{MOB}.{name}", None)   # animations the code no longer triggers
    for name, a in spec["anims"].items():
        anim_doc["animations"][f"animation.{MOB}.{name}"] = a
    anim_bones = {bn for a in anim_doc["animations"].values() for bn in a.get("bones", {})}
    missing = sorted(anim_bones - names)
    print(f"cubes {n_before} -> {n_after}; bones {[b['name'] for b in geo['bones']]}")
    print(f"min y {min(ys)} (rotated cubes may dip slightly), height {max(tops) / 16:.2f} blocks; "
          f"animations {sorted(k.split('.')[-1] for k in anim_doc['animations'])}; missing anim bones {missing}")
    assert n_before == n_after and not missing

    out = P / "build/models/rig_out"
    prev = P / "build/models/rig_preview"
    out.mkdir(parents=True, exist_ok=True)
    prev.mkdir(parents=True, exist_ok=True)
    a = render(geo_doc["minecraft:geometry"][0], tex, f"{MOB}: current")
    b = render(geo, tex, f"{MOB}: rigged + fixed, hitbox {spec['hitbox'][0]} x {spec['hitbox'][1]}")
    sheet = Image.new("RGB", (a.width + b.width + 20, max(a.height, b.height)), (20, 20, 24))
    sheet.paste(a, (0, 0))
    sheet.paste(b, (a.width + 20, 0))
    sheet.save(prev / f"{MOB}.png")
    (out / GEO.name).write_text(json.dumps(new_doc, indent=2) + "\n", encoding="utf-8")
    (out / ANIM.name).write_text(json.dumps(anim_doc, indent=2) + "\n", encoding="utf-8")
    print("preview:", prev / f"{MOB}.png")

    if INSTALL:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        bdir = P / ".texture_backups" / f"{stamp}_rig_{MOB}"
        bdir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(GEO, bdir / GEO.name)
        shutil.copy2(ANIM, bdir / ANIM.name)
        shutil.copyfile(out / GEO.name, GEO)
        shutil.copyfile(out / ANIM.name, ANIM)
        src = MOD_ENTITIES.read_text(encoding="utf-8")
        pat = re.compile(r'("' + MOB + r'", \w+::new, MobCategory\.\w+, )([\d.]+f), ([\d.]+f)')
        w, h = spec["hitbox"]
        new_src, n = pat.subn(lambda m: f"{m.group(1)}{w}f, {h}f", src)
        if n != 1:
            raise SystemExit("could not find the ModEntities registration to update the hitbox")
        if new_src != src:
            shutil.copy2(MOD_ENTITIES, bdir / MOD_ENTITIES.name)
            MOD_ENTITIES.write_text(new_src, encoding="utf-8")
        print("installed; backup in", bdir.relative_to(P))


main()
