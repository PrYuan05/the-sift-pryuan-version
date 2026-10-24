"""Build the Hunter, Trapper and Sculk Cube: GeckoLib models, textures and animations, plus a preview sheet.
Usage: python -I tools/entity/build_sift_creatures.py <project>
Writes assets/pysift/geckolib/models/entity/<id>.geo.json, geckolib/animations/entity/<id>.animation.json,
textures/entity/<id>.png and build/texture_pipeline/out/sift_creatures_preview.png.

Designs follow the user's reference images:
  hunter  - a stalking quadruped: dark navy body speckled with glowing teal, a big orange shelf-fungus growth on its
            back and brow, four long thin legs fading from navy through teal to salmon tips
  trapper - the same build in indigo with a magenta growth (dark spiral marks) and teal leg tips, a little lower
  sculk_cube - a block of sculk with glowing cyan specks, two dim eyes and two stone fangs at the front bottom corners
Animation names match the Java code (HunterEntity / TrapperEntity skillAnimations, SculkCubeEntity "roll").
Textures are painted procedurally from fixed seeds, so re-running gives the same result."""
import json, math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import art_guard   # 臨時圖保護：使用者用同檔名覆蓋過的貼圖不會被重跑蓋掉
from PIL import Image, ImageDraw

P = Path(sys.argv[1])
R = P / "src/main/resources/assets/pysift"
OUT = P / "build/texture_pipeline/out"


# ------------------------------------------------------------------ model description
def cube(origin, size, role, inflate=0.0):
    return {"origin": origin, "size": size, "role": role, "inflate": inflate}


def quadruped(leg_len, cap_lumps):
    """Bones for hunter / trapper. Units are model pixels; the model faces north (-Z)."""
    y0 = leg_len                                   # underside of the body
    legs = []
    for name, x, z in (("front_left", 4.5, -4.5), ("front_right", -4.5, -4.5), ("back_left", 4.5, 5.0), ("back_right", -4.5, 5.0)):
        legs.append({"name": f"leg_{name}", "parent": "root", "pivot": [x, y0, z],
                     "cubes": [cube([x - 1.5, 0, z - 1.5], [3, leg_len, 3], "leg")]})
    bones = [
        {"name": "root", "pivot": [0, 0, 0], "cubes": []},
        {"name": "body", "parent": "root", "pivot": [0, y0 + 4, 0],
         "cubes": [cube([-6, y0, -7], [12, 9, 14], "body")]},
        {"name": "growth", "parent": "body", "pivot": [0, y0 + 9, 2],
         "cubes": [cube([-6.5, y0 + 9, -4], [13, 3, 11], "cap")] + [cube(o, s, "cap") for o, s in cap_lumps(y0)]},
        {"name": "head", "parent": "body", "pivot": [0, y0 + 5, -7],
         "cubes": [cube([-4.5, y0 + 1, -13], [9, 9, 6], "head")]},
        {"name": "brow", "parent": "head", "pivot": [0, y0 + 10, -10],
         "cubes": [cube([-5, y0 + 10, -13.5], [10, 2, 7], "cap"), cube([-2, y0 + 12, -12], [4, 2, 4], "cap")]},
        {"name": "jaw", "parent": "head", "pivot": [0, y0 + 2, -8],
         "cubes": [cube([-3.5, y0 - 1, -12.5], [7, 3, 5], "head")]},
    ] + legs
    return bones


HUNTER_BONES = quadruped(14, lambda y0: [([-5, y0 + 12, -2], [4, 2, 4]), ([1, y0 + 12, 0], [4, 3, 4]),
                                         ([-2, y0 + 12, 4], [3, 2, 3])])
TRAPPER_BONES = quadruped(11, lambda y0: [([-5.5, y0 + 12, -3], [5, 3, 5]), ([1.5, y0 + 12, 1], [4, 2, 4])])
CUBE_BONES = [
    {"name": "root", "pivot": [0, 0, 0], "cubes": []},
    {"name": "cube", "parent": "root", "pivot": [0, 6, 0], "cubes": [cube([-6, 0, -6], [12, 12, 12], "sculk")]},
    {"name": "fang_left", "parent": "cube", "pivot": [4, 2, -6],
     "cubes": [cube([2.5, -0.5, -7.5], [3, 4, 2], "fang")]},
    {"name": "fang_right", "parent": "cube", "pivot": [-4, 2, -6],
     "cubes": [cube([-5.5, -0.5, -7.5], [3, 4, 2], "fang")]},
]

# ------------------------------------------------------------------ palettes
PALETTES = {
    "hunter": {"body": [(16, 34, 52), (22, 44, 66), (28, 56, 80)], "spot": (40, 112, 128), "glow": (110, 220, 235),
               "cap": [(196, 84, 40), (232, 120, 58), (246, 160, 96)], "cap_mark": (34, 52, 72),
               "leg": [(18, 38, 58), (30, 92, 108), (64, 160, 160), (236, 150, 128)], "eye": (140, 235, 245)},
    "trapper": {"body": [(24, 20, 50), (36, 30, 72), (50, 42, 92)], "spot": (78, 64, 132), "glow": (90, 220, 200),
                "cap": [(158, 46, 108), (214, 88, 154), (242, 134, 192)], "cap_mark": (86, 26, 70),
                "leg": [(26, 22, 54), (44, 52, 96), (52, 140, 140), (88, 214, 190)], "eye": (120, 240, 215)},
    "sculk_cube": {"sculk": [(6, 24, 36), (12, 40, 55), (18, 56, 72)], "spot": (40, 130, 150), "glow": (110, 225, 240),
                   "eye": (170, 245, 250), "fang": [(78, 82, 96), (108, 110, 122), (140, 142, 152)]},
}


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def paint(img, role, face, rect, pal, rnd):
    """Fill one cube face. rect = (x, y, w, h) in texture pixels."""
    x0, y0, w, h = rect
    px = img.load()
    for j in range(h):
        for i in range(w):
            r = rnd.random()
            if role in ("body", "head"):
                c = pal["body"][0 if r < 0.25 else 1 if r < 0.8 else 2]
                if r > 0.93:
                    c = pal["spot"]
                if r > 0.985:
                    c = pal["glow"]
            elif role == "cap":
                if face in ("up",):
                    c = pal["cap"][1 if r < 0.6 else 2]
                    if r > 0.94:
                        c = pal["cap_mark"]
                else:                                   # sides: light lip on top, darker underneath
                    c = pal["cap"][2] if j == 0 else pal["cap"][1] if j < h - 1 else pal["cap"][0]
                    if r > 0.9:
                        c = pal["cap"][0]
            elif role == "leg":
                if face == "up":
                    c = pal["leg"][0]
                elif face == "down":
                    c = pal["leg"][3]
                else:                                   # navy -> teal -> tip colour, slightly dithered
                    t = (j + 0.5) / h + (r - 0.5) * 0.12
                    stops = pal["leg"]
                    seg = min(len(stops) - 2, max(0, int(t * (len(stops) - 1))))
                    c = mix(stops[seg], stops[seg + 1], min(1, max(0, t * (len(stops) - 1) - seg)))
            elif role == "sculk":
                c = pal["sculk"][0 if r < 0.3 else 1 if r < 0.8 else 2]
                if r > 0.9:
                    c = pal["spot"]
                if r > 0.975:
                    c = pal["glow"]
            elif role == "fang":
                c = pal["fang"][0 if r < 0.3 else 1 if r < 0.8 else 2]
            px[x0 + i, y0 + j] = c + (255,)
    # details
    if role == "cap" and face == "up" and "cap_mark" in pal and w >= 8:
        d = ImageDraw.Draw(img)                          # spiral / ring marks on the big growths
        for k in range(max(1, w * h // 60)):
            cx, cy = x0 + rnd.randint(1, w - 3), y0 + rnd.randint(1, h - 3)
            d.rectangle([cx, cy, cx + 1, cy + 1], fill=pal["cap_mark"] + (255,))
    if role == "head" and face == "north" and h >= 8:   # two glowing eyes under the brow
        for ex in (x0 + 1, x0 + w - 3):
            for (dx, dy) in ((0, 0), (1, 0)):
                px[ex + dx, y0 + 2 + dy] = pal["eye"] + (255,)
    if role == "sculk" and face == "north":              # dim eyes on the front face
        for ex in (x0 + 3, x0 + w - 5):
            for dx in (0, 1):
                px[ex + dx, y0 + 4] = pal["eye"] + (255,)
                px[ex + dx, y0 + 5] = pal["glow"] + (255,)
    if role == "fang" and face == "north":
        px[x0 + w // 2, y0 + 1] = pal["glow"] + (255,)


# ------------------------------------------------------------------ UV packing + geo json
FACES = ("north", "south", "east", "west", "up", "down")


def face_size(face, size):
    x, y, z = (max(1, math.ceil(v)) for v in size)
    return {"north": (x, y), "south": (x, y), "east": (z, y), "west": (z, y), "up": (x, z), "down": (x, z)}[face]


def build(entity_id, bones, tex_w, tex_h, seed):
    pal = PALETTES[entity_id]
    rnd = random.Random(seed)
    img = Image.new("RGBA", (tex_w, tex_h), (0, 0, 0, 0))
    cx = cy = row_h = 0
    geo_bones = []
    placed = []                                          # for the preview: (bone, cube, {face: rect})
    for b in bones:
        out = {k: v for k, v in b.items() if k != "cubes"}
        out["cubes"] = []
        for c in b["cubes"]:
            uv = {}
            rects = {}
            for f in FACES:
                w, h = face_size(f, c["size"])
                if cx + w > tex_w:
                    cx, cy, row_h = 0, cy + row_h, 0
                assert cy + h <= tex_h, f"{entity_id}: texture {tex_w}x{tex_h} too small"
                rects[f] = (cx, cy, w, h)
                paint(img, c["role"], f, rects[f], pal, rnd)
                uv[f] = {"uv": [cx, cy], "uv_size": [w, h]}
                cx += w
                row_h = max(row_h, h)
            cj = {"origin": c["origin"], "size": c["size"], "uv": uv}
            if c["inflate"]:
                cj["inflate"] = c["inflate"]
            out["cubes"].append(cj)
            placed.append((b["name"], c, rects))
        if not out["cubes"]:
            del out["cubes"]
        geo_bones.append(out)
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.{entity_id}", "texture_width": tex_w, "texture_height": tex_h,
                        "visible_bounds_width": 3, "visible_bounds_height": 3, "visible_bounds_offset": [0, 1.5, 0]},
        "bones": geo_bones}]}
    return geo, img, placed


# ------------------------------------------------------------------ animations
Z = [0, 0, 0]


def kf(*frames):
    return {f"{t:.2f}".rstrip("0").rstrip(".") if t % 1 else f"{t:.1f}": v for t, v in frames}


def loop_cycle(length, n, fn):
    """n+1 evenly spaced keyframes of fn(phase in radians) over one loop."""
    return kf(*[(length * i / n, fn(2 * math.pi * i / n)) for i in range(n + 1)])


def quadruped_anims(eid, swing, extra):
    a = {}
    a["idle"] = {"loop": True, "animation_length": 3.0, "bones": {
        "body": {"position": loop_cycle(3.0, 6, lambda p: [0, round(0.4 * math.sin(p), 2), 0])},
        "head": {"rotation": kf((0, Z), (1.0, [3, 10, 0]), (2.0, [3, -10, 0]), (3.0, Z))},
        "growth": {"scale": loop_cycle(3.0, 6, lambda p: [round(1 + 0.03 * math.sin(p), 3)] * 3)},
        "jaw": {"rotation": kf((0, Z), (1.4, [8, 0, 0]), (1.8, Z), (3.0, Z))},
    }}
    walk = {"body": {"position": loop_cycle(1.0, 8, lambda p: [0, round(0.6 * abs(math.sin(p)), 2), 0]),
                     "rotation": loop_cycle(1.0, 8, lambda p: [0, 0, round(2 * math.sin(p), 2)])},
            "head": {"rotation": loop_cycle(1.0, 8, lambda p: [round(3 * math.sin(2 * p), 2), 0, 0])}}
    for leg, ph in (("front_left", 0), ("back_right", 0), ("front_right", math.pi), ("back_left", math.pi)):
        walk[f"leg_{leg}"] = {"rotation": loop_cycle(1.0, 8, lambda p, ph=ph: [round(swing * math.sin(p + ph), 2), 0, 0])}
    a["walk"] = {"loop": True, "animation_length": 1.0, "bones": walk}
    # bite / lunge
    a["attack"] = {"animation_length": 0.6, "bones": {
        "body": {"rotation": kf((0, Z), (0.15, [-8, 0, 0]), (0.3, [12, 0, 0]), (0.6, Z)),
                 "position": kf((0, Z), (0.15, [0, 0, 1.5]), (0.3, [0, -1, -2.5]), (0.6, Z))},
        "head": {"rotation": kf((0, Z), (0.15, [-20, 0, 0]), (0.3, [18, 0, 0]), (0.6, Z))},
        "jaw": {"rotation": kf((0, Z), (0.15, [35, 0, 0]), (0.3, [-5, 0, 0]), (0.6, Z))},
        "leg_front_left": {"rotation": kf((0, Z), (0.3, [-25, 0, 0]), (0.6, Z))},
        "leg_front_right": {"rotation": kf((0, Z), (0.3, [-25, 0, 0]), (0.6, Z))},
    }}
    a.update(extra)
    return {f"animation.{eid}.{k}": v for k, v in a.items()}


def rear_and_fling(length, release):
    """Rear up on the hind legs, then snap forward at `release` (throwing something from the head)."""
    return {"animation_length": length, "bones": {
        "body": {"rotation": kf((0, Z), (release * 0.8, [-28, 0, 0]), (release, [-30, 0, 0]), (release + 0.15, [14, 0, 0]),
                                (length, Z)),
                 "position": kf((0, Z), (release, [0, 2, 1]), (release + 0.15, [0, -1, -1.5]), (length, Z))},
        "head": {"rotation": kf((0, Z), (release, [-25, 0, 0]), (release + 0.15, [30, 0, 0]), (length, Z))},
        "jaw": {"rotation": kf((0, Z), (release, [30, 0, 0]), (release + 0.1, [40, 0, 0]), (release + 0.3, Z), (length, Z))},
        "leg_front_left": {"rotation": kf((0, Z), (release, [-60, 0, -8]), (release + 0.15, [10, 0, 0]), (length, Z))},
        "leg_front_right": {"rotation": kf((0, Z), (release, [-55, 0, 8]), (release + 0.15, [10, 0, 0]), (length, Z))},
        "leg_back_left": {"rotation": kf((0, Z), (release, [20, 0, 0]), (length, Z))},
        "leg_back_right": {"rotation": kf((0, Z), (release, [20, 0, 0]), (length, Z))},
    }}


HUNTER_EXTRA = {
    "throw": rear_and_fling(1.0, 0.5),
    # mark the prey: raises its head, the growth swells and pulses twice
    "mark": {"animation_length": 1.0, "bones": {
        "head": {"rotation": kf((0, Z), (0.25, [-30, 0, 0]), (0.75, [-30, 0, 0]), (1.0, Z))},
        "jaw": {"rotation": kf((0, Z), (0.25, [25, 0, 0]), (0.75, [25, 0, 0]), (1.0, Z))},
        "growth": {"scale": kf((0, [1, 1, 1]), (0.3, [1.15, 1.2, 1.15]), (0.45, [1.05, 1.05, 1.05]), (0.6, [1.15, 1.2, 1.15]),
                               (1.0, [1, 1, 1]))},
        "brow": {"scale": kf((0, [1, 1, 1]), (0.3, [1.1, 1.3, 1.1]), (0.6, [1.1, 1.3, 1.1]), (1.0, [1, 1, 1]))},
        "body": {"rotation": kf((0, Z), (0.1, [0, 0, 2]), (0.2, [0, 0, -2]), (0.3, [0, 0, 1]), (0.4, Z), (1.0, Z))},
    }},
    # pounce: crouch, then spring forward with the legs stretched
    "leap": {"animation_length": 0.7, "bones": {
        "body": {"position": kf((0, Z), (0.2, [0, -3, 1]), (0.35, [0, 3, -2]), (0.7, Z)),
                 "rotation": kf((0, Z), (0.2, [6, 0, 0]), (0.35, [-12, 0, 0]), (0.7, Z))},
        "head": {"rotation": kf((0, Z), (0.2, [15, 0, 0]), (0.35, [-10, 0, 0]), (0.7, Z))},
        "leg_front_left": {"rotation": kf((0, Z), (0.2, [25, 0, 0]), (0.35, [-55, 0, 0]), (0.7, Z))},
        "leg_front_right": {"rotation": kf((0, Z), (0.2, [25, 0, 0]), (0.35, [-55, 0, 0]), (0.7, Z))},
        "leg_back_left": {"rotation": kf((0, Z), (0.2, [-25, 0, 0]), (0.35, [50, 0, 0]), (0.7, Z))},
        "leg_back_right": {"rotation": kf((0, Z), (0.2, [-25, 0, 0]), (0.35, [50, 0, 0]), (0.7, Z))},
    }},
}
TRAPPER_EXTRA = {
    "throw_net": rear_and_fling(0.9, 0.45),
    # set a trap: crouch low and scratch at the ground with the front legs, head down
    "set_trap": {"animation_length": 1.2, "bones": {
        "body": {"position": kf((0, Z), (0.25, [0, -4, 0]), (0.95, [0, -4, 0]), (1.2, Z)),
                 "rotation": kf((0, Z), (0.25, [10, 0, 0]), (0.95, [10, 0, 0]), (1.2, Z))},
        "head": {"rotation": kf((0, Z), (0.25, [30, 0, 0]), (0.95, [30, 0, 0]), (1.2, Z))},
        "jaw": {"rotation": kf((0, Z), (0.4, [20, 0, 0]), (0.6, Z), (0.8, [20, 0, 0]), (1.0, Z))},
        "leg_front_left": {"rotation": kf((0, Z), (0.25, [-20, 0, 0]), (0.4, [-50, 0, 0]), (0.55, [-15, 0, 0]),
                                          (0.7, [-50, 0, 0]), (0.85, [-15, 0, 0]), (1.2, Z))},
        "leg_front_right": {"rotation": kf((0, Z), (0.25, [-20, 0, 0]), (0.47, [-15, 0, 0]), (0.62, [-50, 0, 0]),
                                           (0.77, [-15, 0, 0]), (0.92, [-50, 0, 0]), (1.2, Z))},
        "leg_back_left": {"rotation": kf((0, Z), (0.25, [25, 0, 0]), (0.95, [25, 0, 0]), (1.2, Z))},
        "leg_back_right": {"rotation": kf((0, Z), (0.25, [25, 0, 0]), (0.95, [25, 0, 0]), (1.2, Z))},
    }},
}
CUBE_ANIMS = {
    # tumbling forward while it rolls at the player; the fangs chatter
    "animation.sculk_cube.roll": {"loop": True, "animation_length": 0.8, "bones": {
        "cube": {"rotation": kf((0, Z), (0.8, [-360, 0, 0]))},
        "fang_left": {"rotation": loop_cycle(0.8, 4, lambda p: [round(15 * max(0, math.sin(2 * p)), 2), 0, 0])},
        "fang_right": {"rotation": loop_cycle(0.8, 4, lambda p: [round(15 * max(0, math.sin(2 * p + 1)), 2), 0, 0])},
    }},
    "animation.sculk_cube.idle": {"loop": True, "animation_length": 2.0, "bones": {
        "cube": {"scale": loop_cycle(2.0, 4, lambda p: [round(1 + 0.04 * math.sin(p), 3)] * 3)},
    }},
}


# ------------------------------------------------------------------ preview
def render(placed, tex, scale=10, yaw=-35, pitch=28):
    """Isometric-ish preview of the rest pose (bone rotations are all zero)."""
    ya, pa = math.radians(yaw), math.radians(pitch)

    def proj(x, y, z):
        xr = x * math.cos(ya) + z * math.sin(ya)
        zr = -x * math.sin(ya) + z * math.cos(ya)
        return (xr * scale, -(y * math.cos(pa) + zr * math.sin(pa)) * scale, zr * math.cos(pa) - y * math.sin(pa))

    quads = []
    for _, c, rects in placed:
        (ox, oy, oz), (sx, sy, sz) = c["origin"], c["size"]
        X0, X1, Y0, Y1, Z0, Z1 = ox, ox + sx, oy, oy + sy, oz, oz + sz
        corners = {  # face: corners (top-left, top-right, bottom-right, bottom-left) as seen from outside
            "north": [(X1, Y1, Z0), (X0, Y1, Z0), (X0, Y0, Z0), (X1, Y0, Z0)],
            "south": [(X0, Y1, Z1), (X1, Y1, Z1), (X1, Y0, Z1), (X0, Y0, Z1)],
            "east": [(X1, Y1, Z1), (X1, Y1, Z0), (X1, Y0, Z0), (X1, Y0, Z1)],
            "west": [(X0, Y1, Z0), (X0, Y1, Z1), (X0, Y0, Z1), (X0, Y0, Z0)],
            "up": [(X0, Y1, Z0), (X1, Y1, Z0), (X1, Y1, Z1), (X0, Y1, Z1)],
            "down": [(X0, Y0, Z1), (X1, Y0, Z1), (X1, Y0, Z0), (X0, Y0, Z0)],
        }
        shade = {"up": 1.0, "north": 0.85, "south": 0.85, "east": 0.7, "west": 0.7, "down": 0.5}
        for f, pts in corners.items():
            p2 = [proj(*q) for q in pts]
            # back-face cull with the projected winding
            area = sum(p2[i][0] * p2[(i + 1) % 4][1] - p2[(i + 1) % 4][0] * p2[i][1] for i in range(4))
            if area <= 0:
                continue
            quads.append((sum(p[2] for p in p2) / 4, p2, rects[f], shade[f]))
    xs = [p[0] for q in quads for p in q[1]]
    ys = [p[1] for q in quads for p in q[1]]
    W, H = int(max(xs) - min(xs)) + 20, int(max(ys) - min(ys)) + 20
    dx, dy = -min(xs) + 10, -min(ys) + 10
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for _, p2, (rx, ry, rw, rh), sh in sorted(quads, key=lambda q: -q[0]):
        face = tex.crop((rx, ry, rx + rw, ry + rh)).resize((rw * 8, rh * 8), Image.Resampling.NEAREST)
        face = Image.eval(face.convert("RGB"), lambda v: int(v * sh)).convert("RGBA")
        dst = [(p[0] + dx, p[1] + dy) for p in p2]
        src = [(0, 0), (face.width, 0), (face.width, face.height), (0, face.height)]
        coeffs = perspective_coeffs(dst, src)
        warped = face.transform((W, H), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.NEAREST)
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).polygon(dst, fill=255)
        img.paste(warped, (0, 0), mask)
    return img


def perspective_coeffs(dst, src):
    """Coefficients mapping output (dst) points to input (src) points for Image.transform(PERSPECTIVE)."""
    A = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, v])
    n = 8                                               # Gauss-Jordan elimination with partial pivoting
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(A[r][col]))
        A[col], A[piv] = A[piv], A[col]
        for r in range(n):
            if r != col and A[col][col]:
                f = A[r][col] / A[col][col]
                A[r] = [a - f * b for a, b in zip(A[r], A[col])]
    return [A[i][n] / A[i][i] for i in range(n)]


# ------------------------------------------------------------------ write everything
SPECS = [("hunter", HUNTER_BONES, 128, 64, 11, quadruped_anims("hunter", 28, HUNTER_EXTRA)),
         ("trapper", TRAPPER_BONES, 128, 64, 23, quadruped_anims("trapper", 24, TRAPPER_EXTRA)),
         ("sculk_cube", CUBE_BONES, 64, 64, 37, CUBE_ANIMS)]
previews = []
for eid, bones, tw, th, seed, anims in SPECS:
    geo, tex, placed = build(eid, bones, tw, th, seed)
    (R / "geckolib/models/entity").mkdir(parents=True, exist_ok=True)
    (R / f"geckolib/models/entity/{eid}.geo.json").write_text(json.dumps(geo, indent=2) + "\n", encoding="utf-8")
    art_guard.save(tex, R / f"textures/entity/{eid}.png")
    (R / f"geckolib/animations/entity/{eid}.animation.json").write_text(
        json.dumps({"format_version": "1.8.0", "animations": anims}, indent=2) + "\n", encoding="utf-8")
    previews.append((eid, render(placed, tex)))
    print(f"{eid}: {len(geo['minecraft:geometry'][0]['bones'])} bones, texture {tw}x{th}, animations {sorted(k.split('.')[-1] for k in anims)}")

OUT.mkdir(parents=True, exist_ok=True)
W = sum(p.width for _, p in previews) + 40 * len(previews)
H = max(p.height for _, p in previews) + 40
sheet = Image.new("RGBA", (W, H), (40, 38, 48, 255))
x = 20
for eid, p in previews:
    sheet.alpha_composite(p, (x, 30))
    ImageDraw.Draw(sheet).text((x, 8), eid, fill=(240, 240, 240, 255))
    x += p.width + 40
sheet.save(OUT / "sift_creatures_preview.png")
print("preview:", OUT / "sift_creatures_preview.png")
