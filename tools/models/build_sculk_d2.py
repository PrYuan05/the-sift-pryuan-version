"""SculkMonstrosity: Redstone Monstrosity skeleton, repainted with the user's Dungeons II sculk texture.
Usage: python -I tools/models/build_sculk_d2.py <project> <bbmodel> <sculk_texture> [--install]

- Geometry: the .bbmodel is converted to GeckoLib geo exactly like build_sculk_from_redstone.py (same bone names, so the
  existing animations keep working), then Dungeons II features are added under existing bones: shoulder blocks with
  soul flames (new child bones left_flame / right_flame), bone tusks beside the head, and fists around the forearm ends.
- Texture: a fresh 256x256 box-UV layout. Every face is cut 1:1 (tiled when larger) from a named region of the user's
  sculk texture chosen by body part, so all pixels come from that texture; nothing is recoloured or rescaled.
- Glowmask: bright cyan pixels (eyes, sculk dots, flames) go to sculk_monstrosity_glowmask.png for AutoGlowingGeoLayer.
Without --install it only writes build/models/sculk_d2/ (geo, texture, glowmask, preview)."""
import sys, json, shutil, datetime, zlib
from pathlib import Path
from PIL import Image

P, BB, SRC = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
INSTALL = "--install" in sys.argv
OUT = P / "build/models/sculk_d2"
GEO = P / "src/main/resources/assets/pysift/geckolib/models/entity/sculk_monstrosity.geo.json"
TEX = P / "src/main/resources/assets/pysift/textures/entity/sculk_monstrosity.png"
GLOW = TEX.with_name("sculk_monstrosity_glowmask.png")
ANIM = P / "src/main/resources/assets/pysift/geckolib/animations/entity/sculk_monstrosity.animation.json"

RENAME = {
    "redstone_golem": "root", "redstone_golem_leg_right": "right_leg", "redstone_golem_leg_left": "left_leg",
    "redstone_golem_hip": "hip", "redstone_golem_torso": "body", "redstone_golem_core": "core",
    "redstone_golem_head": "head", "redstone_golem_arm_left": "left_arm", "redstone_golem_arm_right": "right_arm",
    "redstone_golem_forearm_left": "left_forearm", "redstone_golem_forearm_right": "right_forearm",
}
for side in ("left", "right"):
    for i in (1, 2, 3):
        RENAME[f"redstone_golem_finger_{side}_{i}"] = f"{side}_finger_{i}"

src = Image.open(SRC).convert("RGBA")

# source regions in the user's sculk texture (u, v, w, h)
R = {
    "body": (0, 108, 128, 50),     # navy + cyan dots, a few grey stone patches
    "leg": (16, 150, 112, 24),      # navy fading into the grey stone band (towards the feet)
    "armstone": (176, 160, 48, 64),  # navy with large grey stone patches
    "dots": (160, 132, 64, 26),    # navy + cyan dots with pale teal seams
    "teal": (176, 4, 40, 22),      # lighter teal sculk
    "stone": (0, 172, 24, 48),     # grey deepslate block
    "brick": (90, 0, 36, 75),      # deepslate bricks
    "bone": (0, 64, 88, 40),       # bone white
    "fist": (176, 68, 32, 32),     # knuckle rings
    "claw": (176, 96, 80, 32),     # navy with bone claws
    "flame": (61, 24, 22, 13),     # soul-flame cyan
}
# the original 16x16x16 head cube of the sculk texture (box UV at [1, 223])
HEAD_UV = (1, 223, 16)

# ---------------------------------------------------------------- geometry (same conversion as build_sculk_from_redstone)
bb = json.loads(BB.read_text(encoding="utf-8-sig"))
groups = {g["uuid"]: g for g in bb.get("groups", [])}
elems = {e["uuid"]: e for e in bb["elements"]}
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
            cube = {"origin": [-t[0], f[1], f[2]], "size": [round(b - a, 4) for a, b in zip(f, t)]}
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
old_names = [b["name"] for b in bones]
B = {b["name"]: b for b in bones}


def add_cube(bone, origin, size, role, **kw):
    B[bone].setdefault("cubes", []).append({"origin": origin, "size": size, "role": role, **kw})


# role of every converted cube, by bone
ROLE = {"head": "head", "body": "body", "core": "core", "hip": "hip", "right_leg": "leg", "left_leg": "leg",
        "right_arm": "arm", "left_arm": "arm", "right_forearm": "forearm", "left_forearm": "forearm"}
for b in bones:
    for c in b.get("cubes", []):
        c["role"] = "finger" if "finger" in b["name"] else ROLE.get(b["name"], "body")

# Dungeons II features
for side, sx in (("left", -1), ("right", 1)):
    arm = B[f"{side}_arm"]["cubes"][0]
    ax0, ax1 = arm["origin"][0], arm["origin"][0] + arm["size"][0]
    cx = (ax0 + ax1) / 2 + sx * 1                                   # a little outward
    az = arm["origin"][2] + arm["size"][2] / 2
    # shoulder block, top flush with the body top (y = 60)
    add_cube(f"{side}_arm", [cx - 9, 50, az - 8], [18, 10, 16], "shoulder")
    # soul flames: three staggered layers
    bones.append({"name": f"{side}_flame", "parent": f"{side}_arm", "pivot": [cx, 60, az], "cubes": [
        {"origin": [cx - 6, 60, az - 6], "size": [12, 3, 12], "role": "flame"},
        {"origin": [cx - 4 + sx, 63, az - 4], "size": [8, 3, 8], "role": "flame"},
        {"origin": [cx - 2 - sx, 66, az - 2 + 1], "size": [4, 2, 4], "role": "flame"},
    ]})
    B[f"{side}_flame"] = bones[-1]
    # bone tusk beside the head: three tapering segments, each bending further outward and forward
    # (GeckoLib negates bone x rotation and mirrors x: +x rot leans the tip forward (-z), +z rot leans it towards +x)
    tx, tz = sx * 12, -15
    segs = [(f"{side}_tusk", "body", 44, [6, 8, 6], [15, 0, sx * 15]),
            (f"{side}_tusk_mid", f"{side}_tusk", 52, [5, 7, 5], [20, 0, sx * 18]),
            (f"{side}_tusk_tip", f"{side}_tusk_mid", 59, [3, 6, 3], [25, 0, sx * 20])]
    for name, parent, y0, (w, h, d), rot in segs:
        bones.append({"name": name, "parent": parent, "pivot": [tx, y0, tz], "rotation": rot,
                      "cubes": [{"origin": [tx - w / 2, y0, tz - d / 2], "size": [w, h, d], "role": "bone"}]})
        B[name] = bones[-1]
    # fist around the forearm end
    fa = B[f"{side}_forearm"]["cubes"][0]
    fx = fa["origin"][0] + fa["size"][0] / 2
    fz = fa["origin"][2] + fa["size"][2] / 2
    add_cube(f"{side}_forearm", [fx - 6.5, 10, fz - 6.5], [13, 8, 13], "fist")

# ---------------------------------------------------------------- texture: pack box UVs and paint faces from the source
FACE_ROLES = {   # role -> (sides, up, down)
    "body": ("body", "dots", "body"), "core": ("teal", "teal", "teal"), "hip": ("stone", "stone", "stone"),
    "leg": ("leg", "dots", "stone"), "arm": ("armstone", "dots", "armstone"), "forearm": ("dots", "dots", "bone"),
    "finger": ("bone", "bone", "bone"), "shoulder": ("dots", "teal", "armstone"), "flame": ("flame", "flame", "flame"),
    "bone": ("bone", "bone", "bone"), "fist": ("claw", "dots", "claw"), "head": (None, None, None),
}
TW = TH = 256
tex = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
occupied = [[False] * TW for _ in range(TH)]
face_rects = []


def place(wb, hb):
    for v in range(0, TH - hb + 1):
        for u in range(0, TW - wb + 1):
            if not occupied[v][u] and all(not occupied[y][x] for y in range(v, v + hb) for x in range(u, u + wb)):
                for y in range(v, v + hb):
                    for x in range(u, u + wb):
                        occupied[y][x] = True
                return u, v
    raise SystemExit(f"texture full ({wb}x{hb})")


def filled(region):
    """The region cut out of the source with its transparent gaps filled from neighbouring pixels (no holes in faces)."""
    ru, rv, rw, rh = R[region]
    img = src.crop((ru, rv, ru + rw, rv + rh))
    px = img.load()
    while True:
        holes = [(x, y) for y in range(rh) for x in range(rw) if px[x, y][3] == 0]
        if not holes:
            return img
        fills = {}
        for x, y in holes:
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < rw and 0 <= ny < rh and px[nx, ny][3] > 0:
                    fills[(x, y)] = px[nx, ny]
                    break
        for k, c in fills.items():
            px[k] = c


FILLED = {k: filled(k) for k in R}


def cut(region, w, h, key):
    """w x h patch cut 1:1 from region, tiled when larger; offset varies per face so repeats don't line up."""
    ru, rv, rw, rh = R[region]
    srcimg = FILLED[region]
    seed = zlib.crc32(key.encode())
    ox, oy = seed % max(1, rw - min(w, rw) + 1), (seed >> 8) % max(1, rh - min(h, rh) + 1)
    patch = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            patch.putpixel((x, y), srcimg.getpixel(((ox + x) % rw, (oy + y) % rh)))
    return patch


def head_face(face, w, h):
    u, v, s = HEAD_UV
    rect = {"up": (u + s, v), "down": (u + 2 * s, v), "east": (u, v + s), "north": (u + s, v + s),
            "west": (u + 2 * s, v + s), "south": (u + 3 * s, v + s)}[face]
    return src.crop((rect[0], rect[1], rect[0] + s, rect[1] + s)).crop((0, s - h if face in ("north", "south", "east", "west") else 0, w, s if face in ("north", "south", "east", "west") else h))


for b in bones:
    for i, c in enumerate(b.get("cubes", [])):
        w, h, d = [max(1, round(v)) for v in c["size"]]
        u, v = place(2 * d + 2 * w, d + h)
        c["uv"] = [u, v]
        role = c.pop("role")
        rects = {"up": (u + d, v, w, d), "down": (u + d + w, v, w, d), "east": (u, v + d, d, h),
                 "north": (u + d, v + d, w, h), "west": (u + d + w, v + d, d, h), "south": (u + 2 * d + w, v + d, w, h)}
        sides, up, down = FACE_ROLES[role]
        for face, (fu, fv, fw, fh) in rects.items():
            key = f"{b['name']}/{i}/{face}"
            if role == "head":
                patch = head_face(face, fw, fh)
            elif role == "fist" and face == "north":
                patch = cut("fist", fw, fh, key)
            else:
                patch = cut(up if face == "up" else down if face == "down" else sides, fw, fh, key)
            tex.alpha_composite(patch, (fu, fv))
            face_rects.append((fu, fv, fw, fh))

holes = sum(1 for fu, fv, fw, fh in face_rects for y in range(fv, fv + fh) for x in range(fu, fu + fw) if tex.getpixel((x, y))[3] == 0)

# glowmask: bright cyan pixels only
glow = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
for y in range(TH):
    for x in range(TW):
        r, g, bl, a = tex.getpixel((x, y))
        if a and bl >= 170 and g >= 150 and r <= 140:
            glow.putpixel((x, y), (r, g, bl, a))

geo = {"format_version": "1.12.0", "minecraft:geometry": [{
    "description": {"identifier": "geometry.sculk_monstrosity", "texture_width": TW, "texture_height": TH,
                    "visible_bounds_width": 7, "visible_bounds_height": 6, "visible_bounds_offset": [0, 3, 0]},
    "bones": bones}]}

# ---------------------------------------------------------------- checks
names = [b["name"] for b in bones]
missing_old = [n for n in old_names if n not in names]
anim_bones = set()
for a in json.loads(ANIM.read_text(encoding="utf-8"))["animations"].values():
    anim_bones |= set(a.get("bones", {}))
missing_anim = sorted(anim_bones - set(names))
ys = [v for b in bones for c in b.get("cubes", []) for v in (c["origin"][1], c["origin"][1] + c["size"][1])]
xs = [v for b in bones for c in b.get("cubes", []) for v in (c["origin"][0], c["origin"][0] + c["size"][0])]
print(f"bones {len(bones)}: {names}")
print(f"height {max(ys) / 16:.2f} blocks (min y {min(ys)}), width {(max(xs) - min(xs)) / 16:.2f}")
print(f"old bones missing: {missing_old}; animation bones missing: {missing_anim}; glow px {sum(1 for p in glow.get_flattened_data() if p[3])}")
print(f"transparent pixels inside faces: {holes}")
assert not missing_old and not missing_anim and min(ys) == 0 and holes == 0


# ---------------------------------------------------------------- preview (orthographic front / side)
def render(view, scale=4):
    Wv, Hv = 100, 76
    canvas = Image.new("RGBA", (Wv * scale, Hv * scale), (40, 44, 52, 255))
    items = []
    for b in bones:
        for c in b.get("cubes", []):
            (x, y, z), (w, h, d) = c["origin"], c["size"]
            w, h, d = [max(1, round(q)) for q in (w, h, d)]
            u, v = c["uv"]
            if view == "front":
                items.append((z, (u + d, v + d, w, h), x + Wv / 2, Hv - (y + h) - 2, w, h))
            else:
                items.append((-x - w, (u, v + d, d, h), z + Wv / 2, Hv - (y + h) - 2, d, h))
    for _, (u, v, uw, uh), sx, sy, w, h in sorted(items, key=lambda i: -i[0]):
        patch = tex.crop((u, v, u + uw, v + uh)).resize((w * scale, h * scale), Image.Resampling.NEAREST)
        canvas.alpha_composite(patch, (round(sx * scale), round(sy * scale)))
    return canvas


OUT.mkdir(parents=True, exist_ok=True)
front, side = render("front"), render("side")
sheet = Image.new("RGBA", (front.width + side.width + 20 + 512 + 20, max(front.height, 512)), (28, 28, 32, 255))
sheet.alpha_composite(front, (0, 0))
sheet.alpha_composite(side, (front.width + 20, 0))
sheet.alpha_composite(tex.resize((512, 512), Image.Resampling.NEAREST), (front.width + side.width + 40, 0))
sheet.save(OUT / "preview.png")
tex.save(OUT / "sculk_monstrosity.png")
glow.save(OUT / "sculk_monstrosity_glowmask.png")
(OUT / "sculk_monstrosity.geo.json").write_text(json.dumps(geo, indent=2) + "\n", encoding="utf-8")

if INSTALL:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = P / ".texture_backups" / f"{stamp}_sculk_monstrosity_before_d2"
    bdir.mkdir(parents=True, exist_ok=True)
    for f in (GEO, TEX, GLOW):
        if f.exists():
            shutil.copy2(f, bdir / f.name)
    shutil.copyfile(OUT / "sculk_monstrosity.geo.json", GEO)
    shutil.copyfile(OUT / "sculk_monstrosity.png", TEX)
    shutil.copyfile(OUT / "sculk_monstrosity_glowmask.png", GLOW)
    print("installed; previous files backed up to", bdir.relative_to(P))
