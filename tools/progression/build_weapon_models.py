"""3D in-hand models for the three boss weapons (sonic_staff, dash_charm, sculk_hammer), like the vanilla spyglass:
the item definition picks the 2D icon in the inventory, on the ground, in item frames and on shelves, and the 3D model
everywhere else (in hand, on the head).
Usage: python -I tools/progression/build_weapon_models.py <project>

Each weapon is built upright from boxes (1 model unit = 1 icon pixel, lengths match the 2D icon) and every box is turned
-45 degrees about z, so it lies on the icon's diagonal and the vanilla handheld display transforms hold it exactly like
the 2D icon. Textures: textures/item/<name>_model.png, 32 x 32, one 8 x 16 px strip per material (1 px per model unit),
painted from the 2D icon's own colours; glowing parts set light_emission.
Hand-painted replacements of the _model textures are kept (tools/art_guard.py). In-hand models re-made by hand
(Blockbench, or the pixel-by-pixel sonic staff; their JSON has "credit") are kept too; their use stages come from
HAND_STAGES."""
import json, random, sys
from pathlib import Path

from PIL import Image

P = Path(sys.argv[1])
sys.path.insert(0, str(P / "tools"))
import art_guard

A = P / "src/main/resources/assets/pysift"


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def hexes(*codes):
    return [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in codes]


# ---- materials: ramp dark -> light (taken from each 2D icon), glow = light_emission
MATERIALS = {
    "staff_wood": (hexes("#18121f", "#413452", "#59486e", "#77638f"), 0),        # purple shaft
    "staff_gold": (hexes("#3d2614", "#734e29", "#a67341", "#d99e62", "#f5c291"), 0),
    "staff_crystal": (hexes("#0b3f78", "#0284c7", "#29dfeb", "#cffafe"), 13),
    "charm_grip": (hexes("#262030", "#4a3f5c", "#7e7294", "#a69bb8"), 0),
    "charm_blade": (hexes("#ded7c3", "#f3eedf", "#fffef7", "#fffef7"), 0),
    "charm_edge": (hexes("#2b5957", "#458a82", "#68b3a8", "#ace6ce"), 0),
    "charm_guard": (hexes("#1c2928", "#2b3d3c", "#458a82", "#68b3a8"), 0),
    "hammer_handle": (hexes("#1c2630", "#40576c", "#6e757b", "#8a9399"), 0),
    "hammer_head": (hexes("#0d1217", "#111b21", "#052a32", "#034150"), 0),
    "hammer_core": (hexes("#0a5060", "#009295", "#29dfeb", "#b8fbff"), 11),
    "hammer_bone": (hexes("#6b7a5e", "#819988", "#a2af86", "#d1d6b6"), 0),
}


def paint_strip(ramp, seed, glow):
    """8 x 16 px: lit from the top-left, darker toward the bottom-right, 2-3 px clusters (no single-pixel noise)."""
    rnd = random.Random(seed)
    img = Image.new("RGBA", (8, 16))
    n = len(ramp)
    for y in range(16):
        for x in range(8):
            t = 1.0 - (x / 7 * 0.35 + y / 15 * 0.25)          # 1 at the top-left, ~0.4 at the bottom-right
            idx = min(n - 1, max(0, int(t * (n - 1) + 0.5)))
            img.putpixel((x, y), ramp[idx] + (255,))
    for _ in range(6 if glow else 8):                          # clusters of the neighbouring tone
        cx, cy = rnd.randrange(8), rnd.randrange(16)
        base = img.getpixel((cx, cy))[:3]
        i = ramp.index(base)
        tone = ramp[max(0, min(n - 1, i + rnd.choice((-1, 1))))]
        for dx, dy in ((0, 0), (1, 0), (0, 1))[:rnd.randint(2, 3)]:
            img.putpixel(((cx + dx) % 8, (cy + dy) % 16), tone + (255,))
    if glow:                                                   # bright core in the middle of a glowing strip
        for y in range(5, 11):
            for x in range(2, 6):
                if (x + y) % 3:
                    img.putpixel((x, y), ramp[-1] + (255,))
    return img


def element(frm, to, mat, slot):
    """A box on material strip `slot` (0..7). Faces take the strip's top-left w x h pixels (stretched past 8 x 16)."""
    u0, v0 = (slot % 4) * 4, (slot // 4) * 8                  # strip origin in UV units (32 px texture: 2 px per unit)
    size = [t - f for f, t in zip(frm, to)]
    dims = {"north": (0, 1), "south": (0, 1), "east": (2, 1), "west": (2, 1), "up": (0, 2), "down": (0, 2)}
    faces = {}
    for face, (a, b) in dims.items():
        w, h = min(size[a], 8) / 2, min(size[b], 16) / 2
        faces[face] = {"uv": [u0, v0, u0 + max(w, 0.5), v0 + max(h, 0.5)], "texture": "#model"}
    e = {"from": frm, "to": to, "rotation": {"angle": -45, "axis": "z", "origin": [8, 8, 8]}, "faces": faces}
    if MATERIALS[mat][1]:
        e["light_emission"] = MATERIALS[mat][1]
    return e


def box(cx, cz, w, d, y0, y1):
    return [cx - w / 2, y0, cz - d / 2], [cx + w / 2, y1, cz + d / 2]


# ---- the three weapons, upright; y runs from the butt (-3) to the tip (19) like the icon's diagonal
WEAPONS = {
    "sonic_staff": [
        ("staff_gold", *box(8, 8, 2, 2, -3, -1)),                 # butt cap
        ("staff_wood", *box(8, 8, 1.5, 1.5, -1, 13)),             # shaft
        ("staff_gold", *box(8, 8, 1.8, 1.8, 2, 3)),               # grip bands
        ("staff_gold", *box(8, 8, 1.8, 1.8, 5, 6)),
        ("staff_gold", *box(8, 8, 4, 4, 12.5, 13.5)),             # collar under the crystal
        ("staff_crystal", *box(8, 8, 3, 3, 13.5, 17.5)),          # the crystal
        ("staff_gold", *box(5.5, 8, 1, 1, 13, 18)),               # four prongs holding it
        ("staff_gold", *box(10.5, 8, 1, 1, 13, 18)),
        ("staff_gold", *box(8, 5.5, 1, 1, 13, 18)),
        ("staff_gold", *box(8, 10.5, 1, 1, 13, 18)),
        ("staff_crystal", *box(8, 8, 1, 1, 17.5, 19.5)),          # spark on top
    ],
    "dash_charm": [
        ("charm_grip", *box(8, 8, 1.5, 1.5, -3, 2)),              # grip
        ("charm_guard", *box(8, 8, 5, 1.5, 2, 3)),                # guard
        ("charm_blade", *box(7.5, 8, 3, 1, 3, 9)),                # feather blade, tapering: cream spine...
        ("charm_edge", *box(9.5, 8, 1, 1, 3, 9)),                 # ...teal edge
        ("charm_blade", *box(7.75, 8, 2.5, 1, 9, 14)),
        ("charm_edge", *box(9.5, 8, 1, 1, 9, 13)),
        ("charm_blade", *box(8, 8, 2, 1, 14, 17)),
        ("charm_edge", *box(8, 8, 1, 1, 17, 19)),                 # tip
    ],
    "sculk_hammer": [
        ("hammer_bone", *box(8, 8, 2, 2, -3, -1.5)),              # pommel
        ("hammer_handle", *box(8, 8, 1.5, 1.5, -1.5, 10)),        # handle
        ("hammer_bone", *box(8, 8, 2.2, 2.2, 9, 10.5)),           # collar
        ("hammer_head", *box(8, 8, 8, 5, 10.5, 15.5)),            # head
        ("hammer_core", *box(8, 8, 3, 5.4, 11.5, 14.5)),          # glowing core through the head (front and back)
        ("hammer_bone", *box(3.25, 8, 1.5, 4, 11, 15)),           # bone flanges on both ends
        ("hammer_bone", *box(12.75, 8, 1.5, 4, 11, 15)),
        ("hammer_bone", *box(2, 8, 1, 2, 12, 14)),                # spikes
        ("hammer_bone", *box(14, 8, 1, 2, 12, 14)),
        ("hammer_bone", *box(8, 8, 1, 1, 15.5, 17)),
    ],
}

# the vanilla minecraft:item/handheld display transforms (26.3), so the 3D model is held exactly like the 2D icon
HANDHELD = {
    "thirdperson_righthand": {"rotation": [0, -90, 55], "translation": [0, 4.0, 0.5], "scale": [0.85, 0.85, 0.85]},
    "thirdperson_lefthand": {"rotation": [0, 90, -55], "translation": [0, 4.0, 0.5], "scale": [0.85, 0.85, 0.85]},
    "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
    "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
}

# ---- use animations: while the item is being used, the in-hand model steps through stages (like the vanilla bow).
# Each stage adds boxes to the base model. Thresholds are seconds of use (minecraft:use_duration x 0.05) and match the
# Java timings: SonicStaffItem.CAST_TICKS = 12 (0.6 s); SculkHammerItem.MIN_CHARGE = 15 (0.75 s), FULL_CHARGE = 40 (2 s).
STAGES = {
    "sonic_staff": ("casting", [
        (0.0, [("staff_crystal", *box(8, 8, 3.6, 3.6, 13.2, 17.8))]),                 # the crystal swells and glows
        (0.2, [("staff_crystal", *box(8, 8, 3.6, 3.6, 13.2, 17.8)),                   # + four shards orbiting it
               ("staff_crystal", *box(4.5, 8, 1, 1, 15, 16)), ("staff_crystal", *box(11.5, 8, 1, 1, 15, 16)),
               ("staff_crystal", *box(8, 4.5, 1, 1, 16, 17)), ("staff_crystal", *box(8, 11.5, 1, 1, 16, 17))]),
        (0.4, [("staff_crystal", *box(8, 8, 4.2, 4.2, 12.9, 18.1)),                   # + the shards fly out, a spark on top
               ("staff_crystal", *box(3.5, 8, 1, 1, 16, 17)), ("staff_crystal", *box(12.5, 8, 1, 1, 16, 17)),
               ("staff_crystal", *box(8, 3.5, 1, 1, 17, 18)), ("staff_crystal", *box(8, 12.5, 1, 1, 17, 18)),
               ("staff_crystal", *box(8, 8, 1.4, 1.4, 18.1, 20.5))]),
    ]),
    "sculk_hammer": ("charging", [
        (0.0, [("hammer_core", *box(8, 8, 3.6, 5.8, 11.2, 14.8))]),                   # the core wakes up
        (0.75, [("hammer_core", *box(8, 8, 4.2, 6.0, 11, 15)),                         # ready: sculk spines rise from the head
                ("hammer_core", *box(5, 8, 1, 1, 15.5, 17)), ("hammer_core", *box(11, 8, 1, 1, 15.5, 17)),
                ("hammer_bone", *box(8, 8, 1, 1, 15.5, 18))]),
        (2.0, [("hammer_core", *box(8, 8, 5, 6.2, 10.8, 15.2)),                        # full: blazing core, long spines
               ("hammer_core", *box(5, 8, 1, 1, 15.5, 18.5)), ("hammer_core", *box(11, 8, 1, 1, 15.5, 18.5)),
               ("hammer_core", *box(3.25, 8, 1, 1, 15, 17)), ("hammer_core", *box(12.75, 8, 1, 1, 15, 17)),
               ("hammer_bone", *box(8, 8, 1, 1, 15.5, 19.5))]),
    ]),
}


def model_json(name, parts, mats):
    return {"display": HANDHELD,   # no parent: item/generated would build a flat sprite instead of these boxes
            "textures": {"model": f"pysift:item/{name}_model", "particle": f"pysift:item/{name}"},
            "elements": [element(frm, to, m, mats.index(m)) for m, frm, to in parts]}


def ref(model):
    return {"type": "minecraft:model", "model": f"pysift:item/{model}"}


# ---- hand-made in-hand models (Blockbench, "credit" set): kept as they are. Their use stages are the hand-made model
# plus the boxes below, in the same frame as the hand-made boxes (upright, turned -45 degrees about z around 8, 8, 8).
# Texturing matches the hand-made model: 1 texel per model unit (a face w x h units takes w/2 x h/2 UV units) out of a
# region of the hand-painted _model texture, or the exact faces of one of its elements ("copy").
HAMMER_UV = {                          # region in UV units (0..16): u0, v0, u1, v1
    "glow": [12, 0, 16, 3.5],          # brightest cyan of the core
    "core": [12, 3.5, 16, 8],          # cyan core with teal flecks
}
FACE_DIMS = {"north": (0, 1), "south": (0, 1), "east": (2, 1), "west": (2, 1), "up": (0, 2), "down": (0, 2)}


def hand_box(frm, to, src, light, shift=0.0):
    e = {"from": frm, "to": to, "rotation": {"angle": -45, "axis": "z", "origin": [8, 8, 8]}, "light_emission": light}
    if isinstance(src, int):           # copy the faces of hand-made element `src` (resolved in stage_model)
        e["copy"] = src
        return e
    u0, v0, u1, v1 = HAMMER_UV[src]
    size = [t - f for f, t in zip(frm, to)]
    faces = {}
    for k, (face, (a, b)) in enumerate(FACE_DIMS.items()):
        w, h = min(size[a] / 2, u1 - u0), min(size[b] / 2, v1 - v0)
        su = u0 + ((shift + k * 0.5) % max(0.001, u1 - u0 - w))      # different texels on each face and box
        faces[face] = {"uv": [round(su, 3), v0, round(su + w, 3), v0 + h], "texture": "#model"}
    e["faces"] = faces
    return e


# crystals: the echo cradle's fully grown sprite (the crystal cluster that grows echo golems) on two crossed planes
def crystal(cx, cz, y0, size, light):
    """Two crossed planes (one along x, one along z) carrying the crystal sprite; the sprite's bottom sits at y0."""
    def plane(frm, to, faces):
        return {"from": frm, "to": to, "rotation": {"angle": -45, "axis": "z", "origin": [8, 8, 8]}, "shade": False,
                "light_emission": light, "faces": {f: {"uv": [0, 0, 16, 16], "texture": "#crystal"} for f in faces}}
    h = size / 2
    return [plane([cx - h, y0, cz], [cx + h, y0 + size, cz], ("north", "south")),
            plane([cx, y0, cz - h], [cx, y0 + size, cz + h], ("east", "west"))]


def halo(cx, cz, half, y, thick, light, shift=0.0):
    """A floating square ring of sculk energy around the handle."""
    x0, x1, z0, z1 = cx - half, cx + half, cz - half, cz + half
    return [hand_box([x0, y, z0], [x1, y + thick, z0 + thick], "glow", light, shift),
            hand_box([x0, y, z1 - thick], [x1, y + thick, z1], "glow", light, shift + 1),
            hand_box([x0, y, z0 + thick], [x0 + thick, y + thick, z1 - thick], "glow", light, shift + 2),
            hand_box([x1 - thick, y, z0 + thick], [x1, y + thick, z1 - thick], "glow", light, shift + 3)]


# head x 5..11, y 10.5..15.5, z 5.5..10.5; core = element 4 (x 6.5..9.5, y 11.5..14.5, z 5.3..10.7);
# top cube = element 5 (about x 6.6..8.6, y 15.7..17.2 in this frame); handle x 7.75..9.25, z 7.25..8.75
HAND_STAGES = {
    "sculk_hammer": ("charging", [
        (0.0, [hand_box([6.2, 11.2, 5.0], [9.8, 14.8, 11.0], 4, 10),                             # the core wakes up
               *crystal(7.6, 8, 16.9, 3.0, 10)]),                                                 # a crystal sprouts
        (0.75, [hand_box([5.9, 10.9, 4.8], [10.1, 15.1, 11.2], 4, 13),                            # ready: core swells,
                *crystal(7.6, 8, 16.7, 5.0, 12),                                                  # a crown of crystals,
                *crystal(5.6, 8, 15.2, 3.5, 11), *crystal(9.8, 8, 15.2, 3.5, 11),
                *halo(8.5, 8, 2.0, 7.5, 0.5, 12)]),                                               # an energy ring
        (2.0, [hand_box([5.6, 10.6, 4.5], [10.4, 15.4, 11.5], 4, 15),                             # full: blazing core,
               *crystal(7.6, 8, 16.5, 7.0, 15),                                                   # a tall crown
               *crystal(5.4, 8, 15.2, 5.0, 14), *crystal(10.0, 8, 15.2, 5.0, 14),
               *crystal(7.6, 6.0, 15.2, 3.5, 13), *crystal(7.6, 10.0, 15.2, 3.5, 13),
               *halo(8.5, 8, 2.2, 8.0, 0.5, 15), *halo(8.5, 8, 2.8, 5.0, 0.5, 14, 1),             # two rings
               hand_box([8.25, 0.0, 7.1], [8.75, 9.0, 7.25], "core", 12),                         # veins down the handle
               hand_box([8.25, 0.0, 8.75], [8.75, 9.0, 8.9], "core", 12, 1)]),
    ]),
}

# ---- sonic staff: sonic_staff_in_hand.json and sonic_staff_model.png are hand-made pixel by pixel ("credit" set; the
# texture differs from the hash in tools/ai_texture_hashes.json, so art_guard keeps it). The casting stages add glow
# shells round the core and sound rings that close in on it, cut from these regions of the 32 x 32 texture
# (texels: x, y, w, h; 1 texel per model unit, 2 texels per UV unit).
STAFF_UV = {
    "core1": (24, 0, 4, 4), "padend1": (28, 0, 2, 2), "captop1": (30, 0, 2, 2), "capside1": (30, 2, 2, 1), "padlong1": (22, 4, 6, 2),
    "core2": (16, 6, 4, 4), "padend2": (20, 6, 2, 2), "captop2": (22, 6, 2, 2), "capside2": (22, 8, 2, 1), "padlong2": (16, 10, 6, 2),
    "core3": (24, 6, 4, 4), "padend3": (28, 6, 2, 2), "captop3": (30, 6, 2, 2), "capside3": (30, 8, 2, 1), "padlong3": (22, 10, 6, 2),
    "ring_1": (0, 29, 12, 1), "ring_2": (0, 30, 12, 1), "ring_3": (0, 31, 12, 1),   # dim / mid / bright cyan strips
}
STAFF_ROT = {"angle": -45, "axis": "z", "origin": [8, 8, 8]}


def staff_uv(name, w=None, h=None, rot=0, center=False):
    x, y, rw, rh = STAFF_UV[name]
    w, h = rw if w is None else w, rh if h is None else h
    if center:
        x += (rw - w) // 2
    face = {"uv": [x / 2, y / 2, (x + w) / 2, (y + h) / 2], "texture": "#model"}
    return face | ({"rotation": rot} if rot else {})


def staff_box(frm, to, faces, light, name):
    return {"from": frm, "to": to, "rotation": STAFF_ROT, "faces": faces, "light_emission": light, "name": name}


def staff_ring(r, y0, strip, light, w=1.0):
    """A square sound ring round the staff axis, outer half-width r: four flat w-wide strips with no thickness
    (user: 1 x 1 x 0 planes, not cubes), lying level at the middle of y0..y0+w and seen from above and below."""
    long_, short = int(2 * r), int(2 * r - 2 * w)
    a, b = 8 - r, 8 + r
    y = y0 + w / 2
    lb = {f: staff_uv(strip, long_, 1, center=True) for f in ("up", "down")}
    sb = {f: staff_uv(strip, short, 1, rot=90, center=True) for f in ("up", "down")}
    return [staff_box([a, y, a], [b, y, a + w], lb, light, "sound ring"),
            staff_box([a, y, b - w], [b, y, b], lb, light, "sound ring"),
            staff_box([a, y, a + w], [a + w, y, b - w], sb, light, "sound ring"),
            staff_box([b - w, y, a + w], [b, y, b - w], sb, light, "sound ring")]


def staff_glow(level, light, g):
    """A glow shell g units outside the core (4-cube + side pads + cap of the hand-made model)."""
    c, pe, pl, ct, cs = (f"{k}{level}" for k in ("core", "padend", "padlong", "captop", "capside"))
    every = ("north", "east", "south", "west", "up", "down")
    pad_x = {f: staff_uv(pe) for f in ("east", "west")} | {f: staff_uv(pl) for f in ("north", "south", "up", "down")}
    pad_z = {f: staff_uv(pe) for f in ("north", "south")} | {f: staff_uv(pl) for f in ("east", "west")} | \
            {f: staff_uv(pl, rot=90) for f in ("up", "down")}
    cap = {f: staff_uv(cs) for f in ("north", "east", "south", "west")} | {f: staff_uv(ct) for f in ("up", "down")}
    name = f"glow shell {level}"
    return [staff_box([6 - g, 12 - g, 6 - g], [10 + g, 16 + g, 10 + g], {f: staff_uv(c) for f in every}, light, name),
            staff_box([5 - g, 13 - g, 7 - g], [11 + g, 15 + g, 9 + g], pad_x, light, name),
            staff_box([7 - g, 13 - g, 5 - g], [9 + g, 15 + g, 11 + g], pad_z, light, name),
            staff_box([7 - g, 16, 7 - g], [9 + g, 17 + g, 9 + g], cap, light, name)]


# hand-made model: core x 6..10, y 12..17 (pads out to 5..11 at y 13..15), cradle plate y 11..12, collar y 10..11,
# idle lavender halo r 3.5 at y 17.5..18.5. Thresholds match SonicStaffItem.CAST_TICKS = 12 (0.6 s).
HAND_STAGES["sonic_staff"] = ("casting", [
    (0.0, [*staff_glow(1, 14, 0.2), *staff_ring(6, 13.5, "ring_1", 10)]),                 # a wide wave arrives
    (0.2, [*staff_glow(2, 15, 0.25),                                                      # two waves close in
           *staff_ring(5.5, 10.5, "ring_2", 12), *staff_ring(5.5, 15.5, "ring_2", 12)]),
    (0.4, [*staff_glow(3, 15, 0.3), *staff_ring(4.5, 13.5, "ring_3", 15),                 # they hit the core: white-hot
           *staff_ring(3.5, 9.5, "ring_3", 15), *staff_ring(3.6, 17.4, "ring_3", 15, 1.2),  # core, tight rings, the halo
           staff_box([7.5, 19, 7.5], [8.5, 20, 8.5], {f: staff_uv("core3", 1, 1) for f in    # lit up, a spark on top
                     ("north", "east", "south", "west", "up", "down")}, 15, "spark")]),
])
# extra texture slots. Item models only see the item atlas (textures/item/), so a block texture is mirrored there:
# slot -> (item texture written here, block texture it copies)
HAND_TEXTURES = {"sculk_hammer": {"crystal": ("echo_cradle_crystal", "block/echo_cradle/echo_cradle_3")}}


def stage_model(hand, name, extra):
    elements = list(hand["elements"])
    for e in extra:
        if "copy" in e:
            e = {k: v for k, v in e.items() if k != "copy"} | {"faces": hand["elements"][e["copy"]]["faces"]}
        elements.append(e)
    return {"display": hand.get("display", HANDHELD),
            "textures": {**hand["textures"], **{k: f"pysift:item/{f}" for k, (f, _) in HAND_TEXTURES.get(name, {}).items()}, "particle": f"pysift:item/{name}"}, "elements": elements}


def hand_made(name):
    path = A / f"models/item/{name}_in_hand.json"
    if not path.exists():
        return None
    model = json.loads(path.read_text(encoding="utf-8"))
    return model if "credit" in model else None


for name, parts in WEAPONS.items():
    mats = list(dict.fromkeys(m for m, _, _ in parts))
    hand = hand_made(name)
    if hand is None:
        tex = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        for i, m in enumerate(mats):
            ramp, glow = MATERIALS[m]
            tex.paste(paint_strip(ramp, f"{name}/{m}", glow), ((i % 4) * 8, (i // 4) * 16))
        art_guard.save(tex, A / f"textures/item/{name}_model.png")
        wj(A / f"models/item/{name}_in_hand.json", model_json(name, parts, mats))
    elif name in STAGES and name not in HAND_STAGES:
        sys.exit(f"{name}_in_hand.json is hand-made: add its use stages to HAND_STAGES")
    for file, source in HAND_TEXTURES.get(name, {}).values():
        src, dst = A / f"textures/{source}.png", A / f"textures/item/{file}.png"
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            dst.write_bytes(src.read_bytes())
    in_hand = ref(f"{name}_in_hand")
    if name in STAGES:
        verb, stages = HAND_STAGES[name] if hand else STAGES[name]
        entries = []
        for i, (threshold, extra) in enumerate(stages):
            if hand:
                model = stage_model(hand, name, extra)
            else:
                model = model_json(name, parts + extra, mats)
            wj(A / f"models/item/{name}_{verb}_{i}.json", model)
            entries.append({"threshold": threshold, "model": ref(f"{name}_{verb}_{i}")})
        in_hand = {"type": "minecraft:condition", "property": "minecraft:using_item", "on_false": in_hand,
                   "on_true": {"type": "minecraft:range_dispatch", "property": "minecraft:use_duration", "scale": 0.05,
                               "entries": entries[1:], "fallback": entries[0]["model"]}}
    wj(A / f"items/{name}.json", {"model": {
        "type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": ["gui", "ground", "fixed", "on_shelf"], "model": ref(name)}],
        "fallback": in_hand}})
    print(f"{name}: {len(parts)} boxes, {len(mats)} materials" + (f", {len(STAGES[name][1])} use stages" if name in STAGES else ""))
