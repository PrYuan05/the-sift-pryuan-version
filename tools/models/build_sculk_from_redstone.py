"""SculkMonstrosity from the Redstone Monstrosity Blockbench model (its prototype).
Usage: python -I tools/models/build_sculk_from_redstone.py <project> <bbmodel> [--install]

- Geometry: the .bbmodel (Blockbench free format, box UV) is converted to GeckoLib geo 1.12 the way Blockbench's
  Bedrock/GeckoLib exporter does it (x mirrored: origin.x = -to.x, pivot.x = -origin.x). Bones are renamed so the
  existing SculkMonstrosity animations keep working: root / right_leg / left_leg / hip / body / core / head /
  right_arm / left_arm / *_forearm / *_finger_1..3. Feet stay at y=0, the model is centred on x/z.
- Texture: the model's own redstone texture (its UVs match it exactly) recoloured into the sculk palette with an
  exact per-colour map: stone greys -> sculk navy/teal (brightest stone -> grey accents), redstone reds -> sculk cyan glow.
Without --install it only writes build/models/sculk_from_redstone/ (geo, texture, preview)."""
import sys, json, io, base64, shutil, datetime, colorsys
from pathlib import Path
from PIL import Image

P, BB = Path(sys.argv[1]), Path(sys.argv[2])
INSTALL = "--install" in sys.argv
OUT = P / "build/models/sculk_from_redstone"
GEO = P / "src/main/resources/assets/pysift/geckolib/models/entity/sculk_monstrosity.geo.json"
TEX = P / "src/main/resources/assets/pysift/textures/entity/sculk_monstrosity.png"

RENAME = {
    "redstone_golem": "root", "redstone_golem_leg_right": "right_leg", "redstone_golem_leg_left": "left_leg",
    "redstone_golem_hip": "hip", "redstone_golem_torso": "body", "redstone_golem_core": "core",
    "redstone_golem_head": "head", "redstone_golem_arm_left": "left_arm", "redstone_golem_arm_right": "right_arm",
    "redstone_golem_forearm_left": "left_forearm", "redstone_golem_forearm_right": "right_forearm",
}
for side in ("left", "right"):
    for i in (1, 2, 3):
        RENAME[f"redstone_golem_finger_{side}_{i}"] = f"{side}_finger_{i}"

# exact colour map: redstone palette -> sculk palette (sampled from the original sculk texture)
COLOR_MAP = {
    # stone body: greys -> sculk navy / teal (brightest stone stays as grey accents)
    (20, 21, 23): (6, 17, 24), (47, 49, 55): (4, 18, 30), (63, 63, 67): (0, 24, 43), (86, 86, 92): (0, 32, 50),
    (100, 99, 105): (0, 40, 58), (116, 116, 116): (0, 46, 62), (127, 127, 127): (0, 52, 63),
    (143, 137, 131): (3, 62, 76), (154, 148, 142): (3, 72, 86), (174, 170, 166): (105, 109, 103),
    # redstone glow -> sculk cyan glow (by brightness)
    (115, 12, 0): (0, 116, 145), (148, 20, 0): (2, 140, 175), (164, 24, 8): (15, 170, 205),
    (189, 32, 8): (40, 205, 240), (230, 32, 8): (56, 225, 253),
    (232, 93, 10): (120, 238, 255), (255, 143, 0): (150, 245, 255), (255, 216, 0): (190, 250, 255),
    (255, 255, 151): (225, 255, 255),
}


def recolor(c):
    rgb = c[:3]
    if rgb in COLOR_MAP:
        return (*COLOR_MAP[rgb], c[3])
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in rgb))          # fallback for unexpected colours
    if s > 0.5:
        return (int(40 * l * 2), int(225 * min(1, l * 2)), int(253 * min(1, l * 2)), c[3])
    return (0, int(24 + 60 * l), int(43 + 60 * l), c[3])


bb = json.loads(BB.read_text(encoding="utf-8-sig"))
groups = {g["uuid"]: g for g in bb.get("groups", [])}
elems = {e["uuid"]: e for e in bb["elements"]}
tex_index = 0   # every face of this model uses texture 0 (the redstone texture)
src = bb["textures"][tex_index]["source"]
redstone = Image.open(io.BytesIO(base64.b64decode(src.split(",", 1)[1]))).convert("RGBA")
unknown = {c[:3] for c in redstone.getdata() if c[3] > 0 and c[:3] not in COLOR_MAP}
sculk = Image.new("RGBA", redstone.size)
sculk.putdata([recolor(c) if c[3] > 0 else c for c in redstone.getdata()])

bones = []


def walk(node, parent):
    g = groups[node["uuid"]]
    name = RENAME.get(g["name"], g["name"])
    o = g.get("origin", [0, 0, 0])
    bone = {"name": name, "pivot": [-o[0], o[1], o[2]]}
    if parent:
        bone["parent"] = parent
    r = g.get("rotation", [0, 0, 0])
    if any(r):
        bone["rotation"] = [-r[0], -r[1], r[2]]
    cubes = []
    for child in node.get("children", []):
        if isinstance(child, str):
            e = elems[child]
            f, t = e["from"], e["to"]
            cube = {"origin": [-t[0], f[1], f[2]], "size": [round(b - a, 4) for a, b in zip(f, t)],
                    "uv": list(e.get("uv_offset") or [0, 0])}
            if e.get("mirror_uv"):
                cube["mirror"] = True
            if e.get("inflate"):
                cube["inflate"] = e["inflate"]
            er = e.get("rotation")
            if er and any(er):
                eo = e.get("origin", [0, 0, 0])
                cube["pivot"], cube["rotation"] = [-eo[0], eo[1], eo[2]], [-er[0], -er[1], er[2]]
            cubes.append(cube)
    if cubes:
        bone["cubes"] = cubes
    bones.append(bone)
    for child in node.get("children", []):
        if isinstance(child, dict):
            walk(child, name)


for top in bb["outliner"]:
    walk(top, None)

xs = [v for b in bones for c in b.get("cubes", []) for v in (c["origin"][0], c["origin"][0] + c["size"][0])]
ys = [v for b in bones for c in b.get("cubes", []) for v in (c["origin"][1], c["origin"][1] + c["size"][1])]
zs = [v for b in bones for c in b.get("cubes", []) for v in (c["origin"][2], c["origin"][2] + c["size"][2])]
geo = {"format_version": "1.12.0", "minecraft:geometry": [{
    "description": {"identifier": "geometry.sculk_monstrosity", "texture_width": redstone.width, "texture_height": redstone.height,
                    "visible_bounds_width": 6, "visible_bounds_height": 5, "visible_bounds_offset": [0, 2.5, 0]},
    "bones": bones}]}


def box_rects(c):
    w, h, d = [round(v) for v in c["size"]]
    u, v = c["uv"]
    return {"up": (u + d, v, w, d), "down": (u + d + w, v, w, d), "east": (u, v + d, d, h), "north": (u + d, v + d, w, h),
            "west": (u + d + w, v + d, d, h), "south": (u + 2 * d + w, v + d, w, h)}


def render(view, scale=4):
    W, H = 90, 70
    canvas = Image.new("RGBA", (W * scale, H * scale), (40, 44, 52, 255))
    items = []
    for b in bones:
        for c in b.get("cubes", []):
            (x, y, z), (w, h, d) = c["origin"], c["size"]
            rects = box_rects(c)
            if view == "front":
                items.append((z, rects["north"], x + W / 2, H - (y + h) - 2, w, h, c.get("mirror")))
            else:
                items.append((-x - w, rects["east"], z + W / 2, H - (y + h) - 2, d, h, c.get("mirror")))
    for depth, (u, v, uw, uh), sx, sy, w, h, mir in sorted(items, key=lambda i: -i[0]):
        patch = sculk.crop((u, v, u + uw, v + uh))
        if mir:
            patch = patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        patch = patch.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.Resampling.NEAREST)
        canvas.alpha_composite(patch, (round(sx * scale), round(sy * scale)))
    return canvas


OUT.mkdir(parents=True, exist_ok=True)
front, side = render("front"), render("side")
sheet = Image.new("RGBA", (front.width + side.width + 20 + 256 * 2 + 20, max(front.height, 256 * 2)), (28, 28, 32, 255))
sheet.alpha_composite(front, (0, 0))
sheet.alpha_composite(side, (front.width + 20, 0))
sheet.alpha_composite(sculk.resize((512, 512), Image.Resampling.NEAREST), (front.width + side.width + 40, 0))
sheet.save(OUT / "preview.png")
sculk.save(OUT / "sculk_monstrosity.png")
(OUT / "sculk_monstrosity.geo.json").write_text(json.dumps(geo, indent=2) + "\n", encoding="utf-8")
print(f"bones {len(bones)} ({[b['name'] for b in bones]})")
print(f"size: width {(max(xs) - min(xs)) / 16:.2f} (centre x {(max(xs) + min(xs)) / 2}), height {max(ys) / 16:.2f} "
      f"(min y {min(ys)}), depth {(max(zs) - min(zs)) / 16:.2f} (centre z {(max(zs) + min(zs)) / 2}); unmapped colours {sorted(unknown)}")
if INSTALL:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = P / ".texture_backups" / f"{stamp}_sculk_monstrosity_before_redstone_base"
    bdir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GEO, bdir / GEO.name)
    shutil.copy2(TEX, bdir / TEX.name)
    shutil.copyfile(OUT / "sculk_monstrosity.geo.json", GEO)
    shutil.copyfile(OUT / "sculk_monstrosity.png", TEX)
    print("installed; previous files backed up to", bdir.relative_to(P))
