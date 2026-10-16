"""Build the SculkMonstrosity GeckoLib model + matching texture from code.
Usage: python -I tools/models/build_sculk_monstrosity.py <project> [--preview-only]

Design (reference: hulking sculk brute): hunched heavy torso with a back hump, a small head set low and forward
with glowing eyes, huge rocky shoulder pads crowned with glowing cyan sculk crystals, long arms whose big fists
nearly touch the ground, short thick legs. Bone names stay root / head / right_arm / left_arm / right_leg /
left_leg so the existing animations and skills keep working (extra bones: body, right_hand, left_hand, back).
Coordinates are Bedrock/GeckoLib pixels: feet at y=0, centred on x/z, front is -Z. Every face gets its own UV
rectangle (shelf-packed) and is painted procedurally with the palette of the original texture.
Writes the geo, the texture and preview renders (front / side / three-quarter) to build/models/."""
import sys, json, math, random, shutil, datetime
from pathlib import Path
from PIL import Image, ImageDraw

P = Path(sys.argv[1])
PREVIEW_ONLY = "--preview-only" in sys.argv
GEO = P / "src/main/resources/assets/pysift/geckolib/models/entity/sculk_monstrosity.geo.json"
TEX = P / "src/main/resources/assets/pysift/textures/entity/sculk_monstrosity.png"
OUT = P / "build/models/sculk_monstrosity"
TEX_SIZE = 256

# palette sampled from the original texture
NAVY, NAVY_D = (0, 24, 43), (6, 17, 24)
TEAL1, TEAL2, TEAL3, TEAL4 = (0, 44, 63), (0, 52, 63), (3, 68, 80), (2, 83, 99)
TEAL_HI = (0, 116, 145)
GLOW, GLOW2 = (56, 225, 253), (2, 140, 175)
STONE_D, STONE, STONE_L, STONE_H = (58, 55, 58), (75, 76, 82), (105, 109, 103), (118, 122, 112)
BONE, BONE_D = (219, 204, 162), (191, 183, 126)
MOSS, MOSS_D = (128, 142, 99), (80, 123, 97)

# ---------------- geometry ----------------
# (bone, origin[x,y,z], size[w,h,d], material, extra)  -- origin = min corner
CUBES = []


def cube(bone, o, s, mat, rot=None, pivot=None, face=None):
    CUBES.append({"bone": bone, "origin": list(o), "size": list(s), "mat": mat, "rot": rot, "pivot": pivot, "face": face})


def mirror(bone_from, bone_to):
    for c in [c for c in CUBES if c["bone"] == bone_from]:
        o, s = c["origin"], c["size"]
        rot = None if c["rot"] is None else [c["rot"][0], -c["rot"][1], -c["rot"][2]]
        piv = None if c["pivot"] is None else [-c["pivot"][0], c["pivot"][1], c["pivot"][2]]
        CUBES.append({**c, "bone": bone_to, "origin": [-(o[0] + s[0]), o[1], o[2]], "rot": rot, "pivot": piv})


# legs: short and thick
cube("right_leg", (-17, 0, -7), (13, 16, 14), "flesh")
cube("right_leg", (-18, 0, -9), (15, 4, 4), "stone")            # toe plate
# hips / lower torso
cube("body", (-15, 14, -10), (30, 16, 20), "flesh")
# chest: hunched forward
cube("body", (-21, 28, -17), (42, 26, 28), "flesh")
cube("body", (-12, 30, -19), (24, 14, 2), "bone")               # rib plate on the chest
# back hump
cube("back", (-17, 50, -10), (34, 12, 22), "flesh")
cube("back", (-7, 62, 0), (4, 12, 4), "crystal", rot=[-12, 0, 8], pivot=[-5, 62, 2])
cube("back", (2, 61, 2), (4, 10, 4), "crystal", rot=[-8, 0, -10], pivot=[4, 61, 4])
cube("back", (-2, 62, 6), (3, 16, 3), "crystal", rot=[-15, 0, 0], pivot=[0, 62, 7])
cube("back", (8, 58, -4), (3, 8, 3), "crystal", rot=[0, 0, -20], pivot=[9, 58, -3])
# head: small, low and forward, glowing face
cube("head", (-9, 38, -29), (18, 15, 15), "flesh", face="face")
cube("head", (-8, 34, -27), (16, 5, 12), "bone", face="jaw")    # jaw / teeth
cube("head", (-11, 49, -26), (4, 7, 4), "bone", rot=[0, 0, 20], pivot=[-9, 49, -24])   # small horns
cube("head", (7, 49, -26), (4, 7, 4), "bone", rot=[0, 0, -20], pivot=[9, 49, -24])
# right arm: rocky shoulder pad with crystals, upper arm, forearm (hand bone) with a huge fist
cube("right_arm", (-37, 45, -13), (19, 15, 22), "stone")
cube("right_arm", (-34, 27, -8), (12, 20, 13), "flesh")
cube("right_arm", (-33, 60, -7), (4, 12, 4), "crystal", rot=[-10, 0, 12], pivot=[-31, 60, -5])
cube("right_arm", (-27, 59, -2), (4, 15, 4), "crystal", rot=[8, 0, -6], pivot=[-25, 59, 0])
cube("right_arm", (-36, 59, 2), (3, 9, 3), "crystal", rot=[12, 0, 22], pivot=[-35, 59, 3])
cube("right_arm", (-24, 59, -10), (3, 8, 3), "crystal", rot=[-18, 0, -14], pivot=[-23, 59, -9])
cube("right_hand", (-36, 12, -10), (16, 17, 16), "flesh")
cube("right_hand", (-37, 2, -12), (18, 12, 19), "stone", face="fist")
mirror("right_leg", "left_leg")
mirror("right_arm", "left_arm")
mirror("right_hand", "left_hand")

BONES = [
    {"name": "root", "pivot": [0, 0, 0]},
    {"name": "body", "parent": "root", "pivot": [0, 14, 0]},
    {"name": "back", "parent": "body", "pivot": [0, 50, 0]},
    {"name": "head", "parent": "body", "pivot": [0, 44, -16]},
    {"name": "right_arm", "parent": "body", "pivot": [-26, 54, -2]},
    {"name": "right_hand", "parent": "right_arm", "pivot": [-28, 28, -2]},
    {"name": "left_arm", "parent": "body", "pivot": [26, 54, -2]},
    {"name": "left_hand", "parent": "left_arm", "pivot": [28, 28, -2]},
    {"name": "right_leg", "parent": "root", "pivot": [-10, 16, 0]},
    {"name": "left_leg", "parent": "root", "pivot": [10, 16, 0]},
]

# ---------------- UV packing ----------------
FACES = {"north": ("w", "h"), "south": ("w", "h"), "east": ("d", "h"), "west": ("d", "h"), "up": ("w", "d"), "down": ("w", "d")}


def face_size(c, f):
    w, h, d = c["size"]
    dims = {"w": w, "h": h, "d": d}
    a, b = FACES[f]
    return max(1, round(dims[a])), max(1, round(dims[b]))


rects = []   # (cube index, face, w, h)
for i, c in enumerate(CUBES):
    for f in FACES:
        rects.append((i, f) + face_size(c, f))
rects.sort(key=lambda r: -r[3])
x = y = shelf = 0
uv = {}
for i, f, w, h in rects:
    if x + w > TEX_SIZE:
        x, y, shelf = 0, y + shelf, 0
    uv[(i, f)] = (x, y, w, h)
    x += w
    shelf = max(shelf, h)
assert y + shelf <= TEX_SIZE, f"texture overflow: {y + shelf}"


# ---------------- painting ----------------
def noise(rng, w, h, cell=2):
    """blocky value noise in [0,1): 2x2 cells, lightly smoothed."""
    cw, ch = w // cell + 2, h // cell + 2
    g = [[rng.random() for _ in range(cw)] for _ in range(ch)]
    out = [[0.0] * w for _ in range(h)]
    for yy in range(h):
        for xx in range(w):
            gx, gy = xx // cell, yy // cell
            out[yy][xx] = (g[gy][gx] * 2 + g[gy + 1][gx] + g[gy][gx + 1]) / 4
    return out


def paint(img, rect, mat, face, cube_face, rng):
    x0, y0, w, h = rect
    n = noise(rng, w, h)
    px = img.load()
    for yy in range(h):
        for xx in range(w):
            v = n[yy][xx]
            top = 1 - yy / max(1, h - 1)         # lighter towards the top of side faces
            edge = xx in (0, w - 1) or yy in (0, h - 1)
            if mat == "flesh":
                ramp = [NAVY_D, NAVY, TEAL1, TEAL2, TEAL3, TEAL4]
                k = min(5, max(0, int(v * 4.2 + (top * 1.3 if cube_face in ("north", "south", "east", "west") else 1.0))))
                c = ramp[k]
                if rng.random() < 0.025 and not edge:
                    c = GLOW if rng.random() < 0.5 else GLOW2          # sculk soul specks
                if edge:
                    c = NAVY_D if cube_face != "up" else c
            elif mat == "stone":
                ramp = [STONE_D, STONE, STONE_L, STONE_H]
                k = min(3, max(0, int(v * 3.0 + top * 1.0)))
                c = ramp[k]
                if rng.random() < 0.05:
                    c = MOSS_D if rng.random() < 0.6 else MOSS
                if edge:
                    c = STONE_D
            elif mat == "bone":
                c = BONE if v + top * 0.3 > 0.55 else BONE_D
                if edge:
                    c = BONE_D
            elif mat == "crystal":
                t = yy / max(1, h - 1)               # 0 = tip (top of side face)
                c = (190, 250, 255) if t < 0.15 else GLOW if t < 0.55 else GLOW2
                if xx == 0 or xx == w - 1:
                    c = GLOW2 if t < 0.55 else TEAL_HI
                if cube_face in ("up",):
                    c = (190, 250, 255)
                if cube_face == "down":
                    c = TEAL_HI
            px[x0 + xx, y0 + yy] = (*c, 255)
    # details on the front face
    if cube_face == "north" and face == "face":
        for ex in (w // 2 - 6, w // 2 + 3):          # glowing eyes, 3x2 with a bright core
            for dx in range(3):
                for dy in range(2):
                    px[x0 + ex + dx, y0 + h // 2 - 1 + dy] = (*GLOW, 255)
            px[x0 + ex + 1, y0 + h // 2 - 1] = (220, 255, 255, 255)
        for bx in range(2, w - 2):                   # heavy brow
            px[x0 + bx, y0 + h // 2 - 3] = (*NAVY_D, 255)
    if cube_face == "north" and face == "jaw":
        for tx in range(1, w - 1, 2):                 # teeth
            px[x0 + tx, y0] = (*BONE, 255)
            px[x0 + tx, y0 + 1] = (*BONE, 255)
            px[x0 + tx + 1, y0] = (*NAVY_D, 255)
    if cube_face == "north" and face == "fist":
        for kx in range(2, w - 2, 4):                 # knuckles
            for dx in range(3):
                px[x0 + kx + dx, y0 + 2] = (*STONE_H, 255)
                px[x0 + kx + dx, y0 + 3] = (*STONE_L, 255)


tex = Image.new("RGBA", (TEX_SIZE, TEX_SIZE), (0, 0, 0, 0))
for (i, f), rect in uv.items():
    c = CUBES[i]
    paint(tex, rect, c["mat"], c["face"], f, random.Random(f"{i}-{f}"))

# ---------------- geo json ----------------
bones = []
for b in BONES:
    cubes = []
    for i, c in enumerate(CUBES):
        if c["bone"] != b["name"]:
            continue
        entry = {"origin": c["origin"], "size": c["size"],
                 "uv": {f: {"uv": list(uv[(i, f)][:2]), "uv_size": list(uv[(i, f)][2:])} for f in FACES}}
        if c["rot"]:
            entry["pivot"], entry["rotation"] = c["pivot"], c["rot"]
        cubes.append(entry)
    bones.append({**b, **({"cubes": cubes} if cubes else {})})
geo = {"format_version": "1.12.0", "minecraft:geometry": [{
    "description": {"identifier": "geometry.sculk_monstrosity", "texture_width": TEX_SIZE, "texture_height": TEX_SIZE,
                    "visible_bounds_width": 7, "visible_bounds_height": 6, "visible_bounds_offset": [0, 3, 0]},
    "bones": bones}]}


# ---------------- preview (orthographic, cube rotations ignored) ----------------
def render(view, scale=4):
    """view: 'front' (looking at -Z faces), 'side' (looking at -X / west faces), 'top'."""
    W, H = 96, 90
    canvas = Image.new("RGBA", (W * scale, H * scale), (40, 44, 52, 255))
    order = []
    for i, c in enumerate(CUBES):
        (x, y, z), (w, h, d) = c["origin"], c["size"]
        if view == "front":
            order.append((z, i, "north", x + 48, H - (y + h) - 4, w, h))
        else:
            order.append((x, i, "west", z + 48, H - (y + h) - 4, d, h))
    for depth, i, f, sx, sy, w, h in sorted(order, key=lambda o: -o[0]):
        u, v, uw, uh = uv[(i, f)]
        patch = tex.crop((u, v, u + uw, v + uh)).resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.Resampling.NEAREST)
        canvas.alpha_composite(patch, (round(sx * scale), round(sy * scale)))
    return canvas


OUT.mkdir(parents=True, exist_ok=True)
front, side = render("front"), render("side")
sheet = Image.new("RGBA", (front.width + side.width + 20, front.height), (28, 28, 32, 255))
sheet.alpha_composite(front, (0, 0))
sheet.alpha_composite(side, (front.width + 20, 0))
sheet.save(OUT / "preview.png")
tex.save(OUT / "sculk_monstrosity.png")
(OUT / "sculk_monstrosity.geo.json").write_text(json.dumps(geo, indent=2) + "\n", encoding="utf-8")
ys = [c["origin"][1] + c["size"][1] for c in CUBES]
xs = [v for c in CUBES for v in (c["origin"][0], c["origin"][0] + c["size"][0])]
zs = [v for c in CUBES for v in (c["origin"][2], c["origin"][2] + c["size"][2])]
print(f"cubes {len(CUBES)}, bones {len(BONES)}, height {max(ys) / 16:.2f} blocks, width {(max(xs) - min(xs)) / 16:.2f}, "
      f"depth {(max(zs) - min(zs)) / 16:.2f}, texture rows used {y + shelf}/{TEX_SIZE}")

if not PREVIEW_ONLY:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = P / ".texture_backups" / f"{stamp}_sculk_monstrosity_model"
    bdir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GEO, bdir / GEO.name)
    shutil.copy2(TEX, bdir / TEX.name)
    shutil.copyfile(OUT / "sculk_monstrosity.geo.json", GEO)
    shutil.copyfile(OUT / "sculk_monstrosity.png", TEX)
    print("installed; previous model and texture backed up to", bdir.relative_to(P))
