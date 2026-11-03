"""3D in-hand models for the three boss weapons (sonic_staff, dash_charm, sculk_hammer), like the vanilla spyglass:
the item definition picks the 2D icon in the inventory, on the ground, in item frames and on shelves, and the 3D model
everywhere else (in hand, on the head).
Usage: python -I tools/progression/build_weapon_models.py <project>

Each weapon is built upright from boxes (1 model unit = 1 icon pixel, lengths match the 2D icon) and every box is turned
-45 degrees about z, so it lies on the icon's diagonal and the vanilla handheld display transforms hold it exactly like
the 2D icon. Textures: textures/item/<name>_model.png, 32 x 32, one 8 x 16 px strip per material (1 px per model unit),
painted from the 2D icon's own colours; glowing parts set light_emission.
Hand-painted replacements of the _model textures are kept (tools/art_guard.py)."""
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


for name, parts in WEAPONS.items():
    mats = list(dict.fromkeys(m for m, _, _ in parts))
    tex = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for i, m in enumerate(mats):
        ramp, glow = MATERIALS[m]
        tex.paste(paint_strip(ramp, f"{name}/{m}", glow), ((i % 4) * 8, (i // 4) * 16))
    art_guard.save(tex, A / f"textures/item/{name}_model.png")
    wj(A / f"models/item/{name}_in_hand.json", model_json(name, parts, mats))
    in_hand = ref(f"{name}_in_hand")
    if name in STAGES:
        verb, stages = STAGES[name]
        entries = []
        for i, (threshold, extra) in enumerate(stages):
            wj(A / f"models/item/{name}_{verb}_{i}.json", model_json(name, parts + extra, mats))
            entries.append({"threshold": threshold, "model": ref(f"{name}_{verb}_{i}")})
        in_hand = {"type": "minecraft:condition", "property": "minecraft:using_item", "on_false": in_hand,
                   "on_true": {"type": "minecraft:range_dispatch", "property": "minecraft:use_duration", "scale": 0.05,
                               "entries": entries[1:], "fallback": entries[0]["model"]}}
    wj(A / f"items/{name}.json", {"model": {
        "type": "minecraft:select", "property": "minecraft:display_context",
        "cases": [{"when": ["gui", "ground", "fixed", "on_shelf"], "model": ref(name)}],
        "fallback": in_hand}})
    print(f"{name}: {len(parts)} boxes, {len(mats)} materials" + (f", {len(STAGES[name][1])} use stages" if name in STAGES else ""))
