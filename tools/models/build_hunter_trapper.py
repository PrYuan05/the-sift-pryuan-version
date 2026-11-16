"""Rebuild GeckoLib models, textures, and animations for Hunter, Sculk Cube, and Trapper
matching the original artist textures and reference renders, and directly replace existing assets.

Usage:
  python -I tools/models/build_hunter_trapper.py [--write]
"""
import json
import math
import shutil
import datetime
import sys
from pathlib import Path
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift"
BK = P / ".texture_backups/entity_redesign_20261018"


def box_uv(u, v, w, h, d):
    """Standard Blockbench per-face box UV."""
    return {
        "north": {"uv": [u + d, v + d], "uv_size": [w, h]},
        "east": {"uv": [u, v + d], "uv_size": [d, h]},
        "south": {"uv": [u + 2 * d + w, v + d], "uv_size": [w, h]},
        "west": {"uv": [u + d + w, v + d], "uv_size": [d, h]},
        "up": {"uv": [u + d + w, v + d], "uv_size": [-w, -d]},
        "down": {"uv": [u + d + 2 * w, v], "uv_size": [-w, d]},
    }


def diamond_head_uv(u, v, w, h, d):
    """Head UV for 45-degree diamond orientation (ry=+45 puts (+X, -Z) corner straight forward -Z):
    - east (+X) is front-left face -> uses x=8..16 reversed so x=8 meets the front corner
    - north (-Z) is front-right face -> uses x=16..24 so x=16 meets the front corner
    - up (+Y) uses [16, 8], size [-8, -8] so (8,7) is at front corner (+X, -Z)
    """
    return {
        "east": {"uv": [u + d + w, v + d], "uv_size": [-w, h]},
        "north": {"uv": [u + d + w, v + d], "uv_size": [w, h]},
        "west": {"uv": [u + d + 2 * w, v + d], "uv_size": [d, h]},
        "south": {"uv": [u, v + d], "uv_size": [w, h]},
        "up": {"uv": [u + d + w, v + d], "uv_size": [-w, -d]},
        "down": {"uv": [u + d + 2 * w, v], "uv_size": [-w, d]},
    }


def body_uv(u, v, w, h, d):
    """Body UV layout: up (u,v), down (u+w,v); sides at v+d."""
    return {
        "east": {"uv": [u + w, v + d], "uv_size": [-w, h]},
        "north": {"uv": [u + d, v + d], "uv_size": [w, h]},
        "west": {"uv": [u + d + w, v + d], "uv_size": [d, h]},
        "south": {"uv": [u + 2 * d + w, v + d], "uv_size": [w, h]},
        "up": {"uv": [u + w, v + d], "uv_size": [-w, -d]},
        "down": {"uv": [u + d + 2 * w, v], "uv_size": [-w, d]},
    }


def plane_z_uv(u, v, su, sv, flip_x=False):
    """Flat plane facing north/south."""
    if flip_x:
        f = {"uv": [u + su, v], "uv_size": [-su, sv]}
        b = {"uv": [u, v], "uv_size": [su, sv]}
    else:
        f = {"uv": [u, v], "uv_size": [su, sv]}
        b = {"uv": [u + su, v], "uv_size": [-su, sv]}
    return {"north": f, "south": b, "east": f, "west": f, "up": f, "down": f}


def cube(origin, size, uv, rotation=None, pivot=None, inflate=None):
    c = {"origin": [round(x, 3) for x in origin], "size": [round(x, 3) for x in size], "uv": uv}
    if rotation:
        c["rotation"] = [round(x, 3) for x in rotation]
        c["pivot"] = [round(x, 3) for x in pivot]
    if inflate is not None:
        c["inflate"] = inflate
    return c


def bone(name, parent, pivot, cubes=None):
    b = {"name": name, "pivot": [round(x, 3) for x in pivot]}
    if parent:
        b["parent"] = parent
    if cubes:
        b["cubes"] = cubes
    return b


def geo(name, bones, tex_w=64, tex_h=64):
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": f"geometry.{name}",
                    "texture_width": tex_w,
                    "texture_height": tex_h,
                    "visible_bounds_width": 3,
                    "visible_bounds_height": 3.5,
                    "visible_bounds_offset": [0, 1.5, 0],
                },
                "bones": bones,
            }
        ],
    }


def prepare_textures():
    """Restore original artist textures with transparent background and extract sculk_cube.png."""
    # 1. Hunter
    hunter_im = Image.open(BK / "hunter.png").convert("RGBA")
    hpx = hunter_im.load()
    for y in range(64):
        for x in range(64):
            if hpx[x, y][:3] == (199, 199, 199):
                hpx[x, y] = (0, 0, 0, 0)

    # 2. Trapper
    trapper_im = Image.open(BK / "trapper.png").convert("RGBA")
    tpx = trapper_im.load()
    for y in range(64):
        for x in range(64):
            if tpx[x, y][:3] == (199, 199, 199):
                tpx[x, y] = (0, 0, 0, 0)
    # Copy the 3x10 vertical shield-arm top/bottom strips (x=48..53, y=12..21 and y=34..43)
    # into 10x3 horizontal strips at (x=41..60, y=19..21 and y=41..43) so unrotated [10, 3] up/down UVs work cleanly
    for v_src, v_dst in ((12, 19), (34, 41)):
        for dy in range(3):
            for dx in range(10):
                tpx[41 + dx, v_dst + dy] = tpx[48 + dy, v_src + dx]
                tpx[51 + dx, v_dst + dy] = tpx[51 + dy, v_src + dx]

    # 3. Sculk Cube (extracted from sculk_monstrosity.png at (1, 223, 65, 255))
    mon_im = Image.open(A / "textures/entity/sculk_monstrosity.png").convert("RGBA")
    cube_im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    cube_im.paste(mon_im.crop((1, 223, 65, 255)), (0, 0))

    return {"hunter": hunter_im, "trapper": trapper_im, "sculk_cube": cube_im}


def build_hunter_geo():
    """Hunter model matching Image 1 (ref_1_zoom.png):
    - 2 legs (3x12x3)
    - 45-degree diamond body (9x14x9)
    - 45-degree diamond head (8x9x8) with two 3x1 eyes on the two front-angled faces
    - 2 swept-upward curled horns (inner 5x4x3 + outer curled hook 5x6x3) attached to the upper outer sides of the head
    - 2 angled shield-arms (11x8x5) with 3 hanging tendrils (2x12) under each arm
    """
    leg_h = 12
    body_h = 14
    head_y = leg_h + body_h - 1.5
    head_h = 9
    center_pivot = [0, head_y, 0]

    # Head + Eyes
    head_cubes = [
        cube([-4, head_y, -4], [8, head_h, 8], diamond_head_uv(0, 0, 8, head_h, 8), [5, 45, 0], center_pivot),
        # Left Eye (on east +X front-left face, near +X,-Z front corner)
        cube([4.02, head_y + 3.2, -3.2], [0.05, 1, 3], {
            "east": {"uv": [7, 6], "uv_size": [-3, 1]},
            "west": {"uv": [4, 6], "uv_size": [3, 1]},
        }, [5, 45, 0], center_pivot),
        # Right Eye (on north -Z front-right face, near +X,-Z front corner)
        cube([0.2, head_y + 3.2, -4.07], [3, 1, 0.05], {
            "north": {"uv": [4, 6], "uv_size": [3, 1]},
            "south": {"uv": [7, 6], "uv_size": [-3, 1]},
        }, [5, 45, 0], center_pivot),
    ]

    # Horns:
    # Continuous 10px UV strip x=61->56 (inner 5x4x3) and x=56->51 (outer 5x6x3) with y=4 at top, y=8/10 at bottom!
    hy = head_y + head_h - 0.5
    r_horn_pivot = [-2.3, hy - 1.5, -3.4]
    r_inner_uv = {
        "north": {"uv": [61, 4], "uv_size": [-5, 4]},
        "south": {"uv": [38, 4], "uv_size": [5, 4]},
        "east": {"uv": [38, 4], "uv_size": [3, 4]},
        "west": {"uv": [38, 4], "uv_size": [3, 4]},
        "up": {"uv": [61, 13], "uv_size": [-5, -3]},
        "down": {"uv": [43, 8], "uv_size": [-5, 3]},
    }
    r_outer_uv = {
        "north": {"uv": [56, 4], "uv_size": [-5, 6]},
        "south": {"uv": [43, 4], "uv_size": [5, 6]},
        "west": {"uv": [48, 4], "uv_size": [3, 6]},
        "east": {"uv": [48, 10], "uv_size": [3, 2]},
        "up": {"uv": [56, 13], "uv_size": [-5, -3]},
        "down": {"uv": [48, 10], "uv_size": [-5, 3]},
    }
    right_horn_cubes = [
        cube([-7.3, hy - 3.5, -5.4], [5, 4, 3], r_inner_uv, [0, 45, 22], r_horn_pivot),
        cube([-12.3, hy - 5.5, -5.4], [5, 6, 3], r_outer_uv, [0, 45, 22], r_horn_pivot),
    ]

    l_horn_pivot = [2.3, hy - 1.5, -3.4]
    l_inner_uv = {
        "north": {"uv": [56, 4], "uv_size": [5, 4]},
        "south": {"uv": [43, 4], "uv_size": [-5, 4]},
        "east": {"uv": [38, 4], "uv_size": [3, 4]},
        "west": {"uv": [38, 4], "uv_size": [3, 4]},
        "up": {"uv": [56, 13], "uv_size": [5, -3]},
        "down": {"uv": [38, 8], "uv_size": [5, 3]},
    }
    l_outer_uv = {
        "north": {"uv": [51, 4], "uv_size": [5, 6]},
        "south": {"uv": [48, 4], "uv_size": [-5, 6]},
        "east": {"uv": [48, 4], "uv_size": [3, 6]},
        "west": {"uv": [48, 10], "uv_size": [3, 2]},
        "up": {"uv": [51, 13], "uv_size": [5, -3]},
        "down": {"uv": [43, 10], "uv_size": [5, 3]},
    }
    left_horn_cubes = [
        cube([2.3, hy - 3.5, -5.4], [5, 4, 3], l_inner_uv, [0, -45, -22], l_horn_pivot),
        cube([7.3, hy - 5.5, -5.4], [5, 6, 3], l_outer_uv, [0, -45, -22], l_horn_pivot),
    ]

    # Shield-Arms (11x8x5) + 3 hanging tendrils (2x12) under each arm
    arm_y = leg_h + 4.2
    tendril_uv = plane_z_uv(34, 9, 2, 12)

    def arm_uv(v, mirror=False):
        if not mirror:
            return {
                "north": {"uv": [36, v + 5], "uv_size": [11, 8]},
                "east": {"uv": [31, v + 5], "uv_size": [5, 8]},
                "south": {"uv": [52, v + 5], "uv_size": [11, 8]},
                "west": {"uv": [47, v + 5], "uv_size": [5, 8]},
                "up": {"uv": [52, v + 5], "uv_size": [-11, -5]},
                "down": {"uv": [63, v], "uv_size": [-11, 5]},
            }
        return {
            "north": {"uv": [47, v + 5], "uv_size": [-11, 8]},
            "west": {"uv": [31, v + 5], "uv_size": [5, 8]},
            "south": {"uv": [63, v + 5], "uv_size": [-11, 8]},
            "east": {"uv": [47, v + 5], "uv_size": [5, 8]},
            "up": {"uv": [41, v + 5], "uv_size": [11, -5]},
            "down": {"uv": [52, v], "uv_size": [11, 5]},
        }

    # Left arm (screen-left, ry=-45 around inner shoulder point [1.1, arm_y + 7, -5.3])
    l_arm_pivot = [1.1, arm_y + 7.0, -5.3]
    left_arm_cubes = [
        cube([1.1, arm_y, -10.3], [11, 8, 5], arm_uv(19, mirror=True), [-5, -45, 0], l_arm_pivot),
        cube([2.1, arm_y - 11.8, -9.5], [2, 12, 0.05], tendril_uv, [-5, -45, 0], l_arm_pivot),
        cube([5.6, arm_y - 11.8, -9.5], [2, 12, 0.05], tendril_uv, [-5, -45, 0], l_arm_pivot),
        cube([9.1, arm_y - 11.8, -9.5], [2, 12, 0.05], tendril_uv, [-5, -45, 0], l_arm_pivot),
    ]

    # Right arm (screen-right, ry=+45 around inner shoulder point [-1.1, arm_y + 7, -5.3])
    r_arm_pivot = [-1.1, arm_y + 7.0, -5.3]
    right_arm_cubes = [
        cube([-12.1, arm_y, -10.3], [11, 8, 5], arm_uv(49, mirror=False), [-5, 45, 0], r_arm_pivot),
        cube([-4.1, arm_y - 11.8, -9.5], [2, 12, 0.05], tendril_uv, [-5, 45, 0], r_arm_pivot),
        cube([-7.6, arm_y - 11.8, -9.5], [2, 12, 0.05], tendril_uv, [-5, 45, 0], r_arm_pivot),
        cube([-11.1, arm_y - 11.8, -9.5], [2, 12, 0.05], tendril_uv, [-5, 45, 0], r_arm_pivot),
    ]

    bones = [
        bone("root", None, [0, 0, 0]),
        bone("body", "root", [0, leg_h, 0], [
            cube([-4.5, leg_h, -4.5], [9, body_h, 9], body_uv(1, 24, 9, body_h, 9), [5, 45, 0], [0, leg_h, 0]),
        ]),
        bone("head", "body", center_pivot, head_cubes),
        bone("left_horn", "head", l_horn_pivot, left_horn_cubes),
        bone("right_horn", "head", r_horn_pivot, right_horn_cubes),
        bone("left_arm", "body", l_arm_pivot, left_arm_cubes),
        bone("right_arm", "body", r_arm_pivot, right_arm_cubes),
        bone("left_leg", "root", [1.5, leg_h, 0], [
            cube([0.0, 0, -1.5], [3, leg_h, 3], box_uv(2, 48, 3, leg_h, 3)),
        ]),
        bone("right_leg", "root", [-1.5, leg_h, 0], [
            cube([-3.0, 0, -1.5], [3, leg_h, 3], box_uv(15, 48, 3, leg_h, 3)),
        ]),
    ]
    return geo("hunter", bones)


def build_trapper_geo():
    """Trapper model matching Image 3 (ref_3_zoom.png):
    - 2 legs (2x8x2) with 1px gap
    - 45-degree diamond body (9x12x9)
    - 45-degree diamond head (8x8x8) with two 3x1 pink-pupiled eyes
    - 2 blocky pink spiral horns (4x6x4) on the outer upper sides of the head (beside the eyes)
    - 2 angled shield-arms (10x8x3) with 3 cyan-tipped claws (2x5) under each arm
    """
    leg_h = 8
    body_h = 12
    head_y = leg_h + body_h - 1.5
    head_h = 8
    center_pivot = [0, head_y, 0]

    head_cubes = [
        cube([-4, head_y, -4], [8, head_h, 8], diamond_head_uv(0, 0, 8, head_h, 8), [5, 45, 0], center_pivot),
        # Left Eye (on east +X front-left face)
        cube([4.02, head_y + 3.0, -3.2], [0.05, 1, 3], {
            "east": {"uv": [7, 6], "uv_size": [-3, 1]},
            "west": {"uv": [4, 6], "uv_size": [3, 1]},
        }, [5, 45, 0], center_pivot),
        # Right Eye (on north -Z front-right face)
        cube([0.2, head_y + 3.0, -4.07], [3, 1, 0.05], {
            "north": {"uv": [4, 6], "uv_size": [3, 1]},
            "south": {"uv": [7, 6], "uv_size": [-3, 1]},
        }, [5, 45, 0], center_pivot),
    ]

    # Left & Right Horns (4x6x4) defined in the SAME [5, 45, 0] frame as the head cube!
    r_horn_pivot = [-2.5, head_y + 6.0, -3.5]
    r_horn_uv = {
        "north": {"uv": [52, 4], "uv_size": [4, 6]},
        "east": {"uv": [56, 4], "uv_size": [4, 6]},
        "south": {"uv": [60, 4], "uv_size": [4, 6]},
        "west": {"uv": [48, 4], "uv_size": [4, 6]},
        "up": {"uv": [56, 4], "uv_size": [-4, -4]},
        "down": {"uv": [60, 0], "uv_size": [-4, 4]},
    }
    right_horn_cubes = [
        cube([-4.5, head_y + 3.8, -5.8], [4, 6, 4], r_horn_uv, [5, 45, 0], center_pivot),
    ]

    l_horn_pivot = [2.5, head_y + 6.0, -3.5]
    l_horn_uv = {
        "east": {"uv": [36, 4], "uv_size": [4, 6]},
        "north": {"uv": [40, 4], "uv_size": [4, 6]},
        "west": {"uv": [44, 4], "uv_size": [4, 6]},
        "south": {"uv": [32, 4], "uv_size": [4, 6]},
        "up": {"uv": [36, 4], "uv_size": [4, -4]},
        "down": {"uv": [40, 0], "uv_size": [4, 4]},
    }
    left_horn_cubes = [
        cube([1.8, head_y + 3.8, 0.5], [4, 6, 4], l_horn_uv, [5, 45, 0], center_pivot),
    ]

    # Shield-Arms (10x8x3) + 3 claws (2x5) under each arm
    arm_y = leg_h + 2.5
    claw1_uv = plane_z_uv(40, 56, 2, 5)
    claw2_uv = plane_z_uv(42, 56, 2, 5)
    claw3_uv = plane_z_uv(44, 56, 2, 5)

    def trapper_arm_uv(v_side, v_top, mirror=False):
        if not mirror:
            return {
                "north": {"uv": [41, v_side], "uv_size": [10, 8]},
                "east": {"uv": [38, v_side], "uv_size": [3, 8]},
                "south": {"uv": [54, v_side], "uv_size": [10, 8]},
                "west": {"uv": [51, v_side], "uv_size": [3, 8]},
                "up": {"uv": [51, v_top + 3], "uv_size": [-10, -3]},
                "down": {"uv": [61, v_top], "uv_size": [-10, 3]},
            }
        return {
            "north": {"uv": [51, v_side], "uv_size": [-10, 8]},
            "west": {"uv": [38, v_side], "uv_size": [3, 8]},
            "south": {"uv": [64, v_side], "uv_size": [-10, 8]},
            "east": {"uv": [51, v_side], "uv_size": [3, 8]},
            "up": {"uv": [41, v_top + 3], "uv_size": [10, -3]},
            "down": {"uv": [51, v_top], "uv_size": [10, 3]},
        }

    l_arm_pivot = [1.1, arm_y + 7.0, -5.3]
    left_arm_cubes = [
        cube([1.1, arm_y, -8.3], [10, 8, 3], trapper_arm_uv(22, 19, mirror=True), [-5, -45, 0], l_arm_pivot),
        cube([1.6, arm_y - 4.8, -7.8], [2, 5, 0.05], claw1_uv, [-5, -45, 0], l_arm_pivot),
        cube([5.1, arm_y - 4.8, -7.8], [2, 5, 0.05], claw2_uv, [-5, -45, 0], l_arm_pivot),
        cube([8.6, arm_y - 4.8, -7.8], [2, 5, 0.05], claw3_uv, [-5, -45, 0], l_arm_pivot),
    ]

    r_arm_pivot = [-1.1, arm_y + 7.0, -5.3]
    right_arm_cubes = [
        cube([-11.1, arm_y, -8.3], [10, 8, 3], trapper_arm_uv(44, 41, mirror=False), [-5, 45, 0], r_arm_pivot),
        cube([-3.6, arm_y - 4.8, -7.8], [2, 5, 0.05], claw1_uv, [-5, 45, 0], r_arm_pivot),
        cube([-7.1, arm_y - 4.8, -7.8], [2, 5, 0.05], claw2_uv, [-5, 45, 0], r_arm_pivot),
        cube([-10.6, arm_y - 4.8, -7.8], [2, 5, 0.05], claw3_uv, [-5, 45, 0], r_arm_pivot),
    ]

    def leg_uv(u):
        return {
            "east": {"uv": [u, 38], "uv_size": [2, 8]},
            "north": {"uv": [u + 2, 38], "uv_size": [2, 8]},
            "west": {"uv": [u + 4, 38], "uv_size": [2, 8]},
            "south": {"uv": [u + 6, 38], "uv_size": [2, 8]},
            "up": {"uv": [8, 38], "uv_size": [2, 2]},
            "down": {"uv": [8, 45], "uv_size": [2, 2]},
        }

    bones = [
        bone("root", None, [0, 0, 0]),
        bone("body", "root", [0, leg_h, 0], [
            cube([-4.5, leg_h, -4.5], [9, body_h, 9], body_uv(0, 16, 9, body_h, 9), [5, 45, 0], [0, leg_h, 0]),
        ]),
        bone("head", "body", center_pivot, head_cubes),
        bone("left_horn", "head", l_horn_pivot, left_horn_cubes),
        bone("right_horn", "head", r_horn_pivot, right_horn_cubes),
        bone("left_arm", "body", l_arm_pivot, left_arm_cubes),
        bone("right_arm", "body", r_arm_pivot, right_arm_cubes),
        bone("left_leg", "root", [1.5, leg_h, 0], [
            cube([0.5, 0, -1.0], [2, leg_h, 2], leg_uv(0)),
        ]),
        bone("right_leg", "root", [-1.5, leg_h, 0], [
            cube([-2.5, 0, -1.0], [2, leg_h, 2], leg_uv(10)),
        ]),
    ]
    return geo("trapper", bones)


def build_sculk_cube_geo():
    """Sculk Cube model matching Image 2 (ref_2_zoom.png):
    Pure 16x16x16 cube using the embedded sculk_monstrosity UV region (no protruding fangs).
    """
    bones = [
        bone("root", None, [0, 0, 0]),
        bone("cube", "root", [0, 8, 0], [
            cube([-8, 0, -8], [16, 16, 16], box_uv(0, 0, 16, 16, 16)),
        ]),
    ]
    return geo("sculk_cube", bones)


def k(d):
    return {str(t): v for t, v in d.items()}


def build_animations():
    hunter_anims = {
        "idle": {
            "animation_length": 3.0,
            "loop": True,
            "bones": {
                "body": {"position": k({0.0: [0, 0, 0], 1.5: [0, 0.4, 0], 3.0: [0, 0, 0]})},
                "head": {"rotation": k({0.0: [0, 0, 0], 1.0: [2, 8, 0], 2.0: [2, -8, 0], 3.0: [0, 0, 0]})},
                "left_horn": {"rotation": k({0.0: [0, 0, 0], 1.5: [0, 0, -4], 3.0: [0, 0, 0]})},
                "right_horn": {"rotation": k({0.0: [0, 0, 0], 1.5: [0, 0, 4], 3.0: [0, 0, 0]})},
                "left_arm": {"rotation": k({0.0: [0, 0, 0], 1.5: [-4, 0, -3], 3.0: [0, 0, 0]})},
                "right_arm": {"rotation": k({0.0: [0, 0, 0], 1.5: [-4, 0, 3], 3.0: [0, 0, 0]})},
            },
        },
        "walk": {
            "animation_length": 0.9,
            "loop": True,
            "bones": {
                "left_leg": {"rotation": k({0.0: [28, 0, 0], 0.45: [-28, 0, 0], 0.9: [28, 0, 0]})},
                "right_leg": {"rotation": k({0.0: [-28, 0, 0], 0.45: [28, 0, 0], 0.9: [-28, 0, 0]})},
                "left_arm": {"rotation": k({0.0: [-14, -8, 0], 0.45: [12, 8, 0], 0.9: [-14, -8, 0]})},
                "right_arm": {"rotation": k({0.0: [12, -8, 0], 0.45: [-14, 8, 0], 0.9: [12, -8, 0]})},
                "body": {
                    "rotation": k({0.0: [6, 0, 0], 0.45: [6, 0, 0], 0.9: [6, 0, 0]}),
                    "position": k({0.0: [0, 0, 0], 0.225: [0, 0.6, 0], 0.45: [0, 0, 0], 0.675: [0, 0.6, 0], 0.9: [0, 0, 0]}),
                },
                "head": {"rotation": k({0.0: [-4, 0, 0], 0.45: [-2, 0, 0], 0.9: [-4, 0, 0]})},
            },
        },
        # Double shield-arm tendril slash (melee attack)
        "attack": {
            "animation_length": 0.55,
            "bones": {
                "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.18: [-35, 30, -20], 0.32: [22, -22, 10], 0.55: [0, 0, 0]})},
                "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.18: [-35, -30, 20], 0.32: [22, 22, -10], 0.55: [0, 0, 0]})},
                "body": {"rotation": k({0.0: [0, 0, 0], 0.18: [-8, 0, 0], 0.32: [16, 0, 0], 0.55: [0, 0, 0]})},
                "head": {"rotation": k({0.0: [0, 0, 0], 0.18: [-6, 0, 0], 0.32: [10, 0, 0], 0.55: [0, 0, 0]})},
            },
        },
        # Soul javelin throw (releases projectile at 0.55s / tick 11)
        "throw": {
            "animation_length": 1.0,
            "bones": {
                "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.35: [-45, -35, 25], 0.5: [-40, -30, 20], 0.6: [28, 25, -12], 1.0: [0, 0, 0]})},
                "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.35: [-20, 20, -10], 0.6: [15, -12, 6], 1.0: [0, 0, 0]})},
                "body": {"rotation": k({0.0: [0, 0, 0], 0.35: [-12, 20, 0], 0.6: [16, -15, 0], 1.0: [0, 0, 0]})},
                "head": {"rotation": k({0.0: [0, 0, 0], 0.35: [-8, -16, 0], 0.6: [10, 12, 0], 1.0: [0, 0, 0]})},
                "left_horn": {"rotation": k({0.0: [0, 0, 0], 0.35: [0, 0, -10], 0.6: [0, 0, 6], 1.0: [0, 0, 0]})},
                "right_horn": {"rotation": k({0.0: [0, 0, 0], 0.35: [0, 0, 10], 0.6: [0, 0, -6], 1.0: [0, 0, 0]})},
            },
        },
        # Hunter's mark (channels glowing mark at 0.5s / tick 10)
        "mark": {
            "animation_length": 1.0,
            "bones": {
                "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.3: [-35, 35, -20], 0.75: [-35, 35, -20], 1.0: [0, 0, 0]})},
                "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.3: [-35, -35, 20], 0.75: [-35, -35, 20], 1.0: [0, 0, 0]})},
                "head": {"rotation": k({0.0: [0, 0, 0], 0.3: [-12, 0, 0], 0.75: [-12, 0, 0], 1.0: [0, 0, 0]})},
                "left_horn": {"rotation": k({0.0: [0, 0, 0], 0.3: [0, 0, -14], 0.75: [0, 0, -14], 1.0: [0, 0, 0]})},
                "right_horn": {"rotation": k({0.0: [0, 0, 0], 0.3: [0, 0, 14], 0.75: [0, 0, 14], 1.0: [0, 0, 0]})},
                "body": {"rotation": k({0.0: [0, 0, 0], 0.3: [-6, 0, 0], 0.75: [-6, 0, 0], 1.0: [0, 0, 0]})},
            },
        },
        # Evasive back-leap (fires at 0.2s / tick 4)
        "leap": {
            "animation_length": 0.7,
            "bones": {
                "body": {
                    "rotation": k({0.0: [0, 0, 0], 0.15: [16, 0, 0], 0.32: [-18, 0, 0], 0.7: [0, 0, 0]}),
                    "position": k({0.0: [0, 0, 0], 0.15: [0, -2.0, 0], 0.32: [0, 1.5, 0], 0.7: [0, 0, 0]}),
                },
                "left_leg": {"rotation": k({0.0: [0, 0, 0], 0.15: [-20, 0, 0], 0.32: [32, 0, 0], 0.7: [0, 0, 0]})},
                "right_leg": {"rotation": k({0.0: [0, 0, 0], 0.15: [-20, 0, 0], 0.32: [32, 0, 0], 0.7: [0, 0, 0]})},
                "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.32: [-25, 25, -15], 0.7: [0, 0, 0]})},
                "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.32: [-25, -25, 15], 0.7: [0, 0, 0]})},
            },
        },
    }

    trapper_anims = {
        "idle": {
            "animation_length": 3.0,
            "loop": True,
            "bones": {
                "body": {"position": k({0.0: [0, 0, 0], 1.5: [0, 0.35, 0], 3.0: [0, 0, 0]})},
                "head": {"rotation": k({0.0: [0, 0, 0], 1.0: [3, 10, 0], 2.0: [3, -10, 0], 3.0: [0, 0, 0]})},
                "left_horn": {"rotation": k({0.0: [0, 0, 0], 1.5: [0, 0, -3], 3.0: [0, 0, 0]})},
                "right_horn": {"rotation": k({0.0: [0, 0, 0], 1.5: [0, 0, 3], 3.0: [0, 0, 0]})},
                "left_arm": {"rotation": k({0.0: [0, 0, 0], 1.5: [-3, 0, -2], 3.0: [0, 0, 0]})},
                "right_arm": {"rotation": k({0.0: [0, 0, 0], 1.5: [-3, 0, 2], 3.0: [0, 0, 0]})},
            },
        },
        "walk": {
            "animation_length": 0.9,
            "loop": True,
            "bones": {
                "left_leg": {"rotation": k({0.0: [24, 0, 0], 0.45: [-24, 0, 0], 0.9: [24, 0, 0]})},
                "right_leg": {"rotation": k({0.0: [-24, 0, 0], 0.45: [24, 0, 0], 0.9: [-24, 0, 0]})},
                "left_arm": {"rotation": k({0.0: [-12, -6, 0], 0.45: [10, 6, 0], 0.9: [-12, -6, 0]})},
                "right_arm": {"rotation": k({0.0: [10, -6, 0], 0.45: [-12, 6, 0], 0.9: [10, -6, 0]})},
                "body": {
                    "rotation": k({0.0: [5, 0, 0], 0.45: [5, 0, 0], 0.9: [5, 0, 0]}),
                    "position": k({0.0: [0, 0, 0], 0.225: [0, 0.5, 0], 0.45: [0, 0, 0], 0.675: [0, 0.5, 0], 0.9: [0, 0, 0]}),
                },
            },
        },
        # Double claw swipe
        "attack": {
            "animation_length": 0.6,
            "bones": {
                "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.2: [-35, 28, -15], 0.38: [22, -20, 8], 0.6: [0, 0, 0]})},
                "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.22: [-35, -28, 15], 0.4: [22, 20, -8], 0.6: [0, 0, 0]})},
                "body": {"rotation": k({0.0: [0, 0, 0], 0.2: [-6, 0, 0], 0.38: [14, 0, 0], 0.6: [0, 0, 0]})},
                "head": {"rotation": k({0.0: [0, 0, 0], 0.2: [-4, 0, 0], 0.38: [10, 0, 0], 0.6: [0, 0, 0]})},
            },
        },
        # Bury soul snare in ground (activates at 0.6s / tick 12)
        "set_trap": {
            "animation_length": 1.2,
            "bones": {
                "body": {
                    "rotation": k({0.0: [0, 0, 0], 0.4: [28, 0, 0], 0.8: [28, 0, 0], 1.2: [0, 0, 0]}),
                    "position": k({0.0: [0, 0, 0], 0.4: [0, -1.8, 0], 0.8: [0, -1.8, 0], 1.2: [0, 0, 0]}),
                },
                "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.4: [25, -15, 0], 0.6: [40, -5, 0], 0.8: [25, -15, 0], 1.2: [0, 0, 0]})},
                "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.4: [25, 15, 0], 0.6: [40, 5, 0], 0.8: [25, 15, 0], 1.2: [0, 0, 0]})},
                "head": {"rotation": k({0.0: [0, 0, 0], 0.4: [-15, 0, 0], 0.8: [-15, 0, 0], 1.2: [0, 0, 0]})},
            },
        },
        # Cast trapper net (releases at 0.5s / tick 10)
        "throw_net": {
            "animation_length": 0.9,
            "bones": {
                "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.3: [25, -25, 12], 0.5: [-45, 25, -15], 0.9: [0, 0, 0]})},
                "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.3: [20, 20, -10], 0.5: [-40, -20, 12], 0.9: [0, 0, 0]})},
                "body": {"rotation": k({0.0: [0, 0, 0], 0.3: [-10, 18, 0], 0.5: [14, -12, 0], 0.9: [0, 0, 0]})},
                "head": {"rotation": k({0.0: [0, 0, 0], 0.3: [-6, -12, 0], 0.5: [8, 8, 0], 0.9: [0, 0, 0]})},
            },
        },
    }

    sculk_cube_anims = {
        "idle": {
            "animation_length": 1.2,
            "loop": True,
            "bones": {
                "cube": {
                    "scale": k({
                        0.0: [1.0, 1.0, 1.0],
                        0.4: [1.05, 0.95, 1.05],
                        0.8: [0.97, 1.04, 0.97],
                        1.2: [1.0, 1.0, 1.0],
                    }),
                    "rotation": k({
                        0.0: [0, 0, 0],
                        0.4: [3, 0, -3],
                        0.8: [-3, 0, 3],
                        1.2: [0, 0, 0],
                    }),
                }
            },
        },
        "roll": {
            "animation_length": 0.6,
            "loop": True,
            "bones": {
                "cube": {
                    "rotation": k({
                        0.0: [0, 0, 0],
                        0.15: [90, 0, 0],
                        0.3: [180, 0, 0],
                        0.45: [270, 0, 0],
                        0.6: [360, 0, 0],
                    }),
                    "position": k({
                        0.0: [0, 0, 0],
                        0.075: [0, 1.4, 0],
                        0.15: [0, 0, 0],
                        0.225: [0, 1.4, 0],
                        0.3: [0, 0, 0],
                        0.375: [0, 1.4, 0],
                        0.45: [0, 0, 0],
                        0.525: [0, 1.4, 0],
                        0.6: [0, 0, 0],
                    }),
                }
            },
        },
    }

    return {
        "hunter": {"format_version": "1.8.0", "animations": {f"animation.hunter.{n}": a for n, a in hunter_anims.items()}},
        "trapper": {"format_version": "1.8.0", "animations": {f"animation.trapper.{n}": a for n, a in trapper_anims.items()}},
        "sculk_cube": {"format_version": "1.8.0", "animations": {f"animation.sculk_cube.{n}": a for n, a in sculk_cube_anims.items()}},
    }


def render_comparison(textures, geos):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from geo_preview3d import render as render3d, render_views

    renders = [
        ("Hunter", Image.open(P / "build/previews/ref_1_zoom.png").convert("RGBA"),
         render3d(geos["hunter"]["minecraft:geometry"][0], textures["hunter"], scale=8, yaw=16, pitch=24)),
        ("Sculk Cube", Image.open(P / "build/previews/ref_2_zoom.png").convert("RGBA"),
         render3d(geos["sculk_cube"]["minecraft:geometry"][0], textures["sculk_cube"], scale=10, yaw=45, pitch=30)),
        ("Trapper", Image.open(P / "build/previews/ref_3_zoom.png").convert("RGBA"),
         render3d(geos["trapper"]["minecraft:geometry"][0], textures["trapper"], scale=8, yaw=16, pitch=24)),
    ]

    cols = []
    for label, ref_im, gen_im in renders:
        h = 320
        rw = int(ref_im.width * (h / ref_im.height))
        gw = int(gen_im.width * (h / gen_im.height))
        ref_r = ref_im.resize((rw, h), Image.Resampling.NEAREST)
        gen_r = gen_im.resize((gw, h), Image.Resampling.NEAREST)
        panel = Image.new("RGB", (rw + gw + 20, h + 30), (30, 32, 40))
        d = ImageDraw.Draw(panel)
        d.text((8, 6), f"{label} (Left: Ref | Right: Rebuilt)", fill=(230, 230, 230))
        panel.paste(ref_r, (5, 25), ref_r if ref_r.mode == "RGBA" else None)
        panel.paste(gen_r, (rw + 15, 25))
        cols.append(panel)

    total_w = max(c.width for c in cols)
    total_h = sum(c.height for c in cols) + 20
    sheet = Image.new("RGB", (total_w, total_h), (24, 24, 30))
    y = 0
    for c in cols:
        sheet.paste(c, (0, y))
        y += c.height + 10
    out_path = P / "build/previews/comparison_all3.png"
    sheet.save(out_path)
    print("Saved comparison:", out_path)

    # Also render 3-view + action pose previews
    pose_sheets = [
        render_views(geos["hunter"], textures["hunter"], scale=6, title="hunter (rest: front / side / back)"),
        render_views(geos["hunter"], textures["hunter"], scale=6,
                     pose={"right_arm": {"rotation": [-45, -35, 25]}, "left_arm": {"rotation": [-20, 20, -10]},
                           "body": {"rotation": [-12, 20, 0]}, "head": {"rotation": [-8, -16, 0]}},
                     title="hunter (throw windup)"),
        render_views(geos["sculk_cube"], textures["sculk_cube"], scale=6, title="sculk_cube (rest: front / side / back)"),
        render_views(geos["trapper"], textures["trapper"], scale=6, title="trapper (rest: front / side / back)"),
        render_views(geos["trapper"], textures["trapper"], scale=6,
                     pose={"body": {"rotation": [28, 0, 0], "position": [0, -1.8, 0]},
                           "left_arm": {"rotation": [40, -5, 0]}, "right_arm": {"rotation": [40, 5, 0]},
                           "head": {"rotation": [-15, 0, 0]}},
                     title="trapper (set_trap)"),
    ]
    pw = max(p.width for p in pose_sheets)
    ph = sum(p.height for p in pose_sheets) + 10 * len(pose_sheets)
    psheet = Image.new("RGB", (pw, ph), (24, 24, 30))
    py = 0
    for p in pose_sheets:
        psheet.paste(p, (0, py))
        py += p.height + 10
    pose_out = P / "build/previews/hunter_trapper_sculk_cube_poses.png"
    psheet.save(pose_out)
    print("Saved poses:", pose_out)


def main():
    textures = prepare_textures()
    geos = {
        "hunter": build_hunter_geo(),
        "trapper": build_trapper_geo(),
        "sculk_cube": build_sculk_cube_geo(),
    }
    anims = build_animations()
    render_comparison(textures, geos)

    if "--write" in sys.argv:
        bk_dir = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_rebuilt_3mobs")
        for mob in ("hunter", "trapper", "sculk_cube"):
            tex_p = A / f"textures/entity/{mob}.png"
            geo_p = A / f"geckolib/models/entity/{mob}.geo.json"
            anim_p = A / f"geckolib/animations/entity/{mob}.animation.json"
            for p in (tex_p, geo_p, anim_p):
                if p.exists():
                    dst = bk_dir / p.relative_to(P)
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, dst)
            textures[mob].save(tex_p)
            geo_p.write_text(json.dumps(geos[mob], indent="\t") + "\n", encoding="utf-8")
            anim_p.write_text(json.dumps(anims[mob], indent="\t") + "\n", encoding="utf-8")
            print(f"Wrote {mob}: {tex_p.name}, {geo_p.name}, {anim_p.name}")


if __name__ == "__main__":
    main()
