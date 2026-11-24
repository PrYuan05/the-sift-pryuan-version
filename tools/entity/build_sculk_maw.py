"""Sculk Maw (SculkMawEntity, the Sculk Hammer's ground tendril): Razor-Fanged GeckoLib model, vibrant Warden-bone texture,
emissive glowmask, and animations.
Usage: python -I tools/entity/build_sculk_maw.py <project>

A ring of six curved multi-tiered hooked bone fangs + 12 curved flanking side fangs + 6 serrated inner throat tooth rows
erupting from a cracked abyssal sculk crater around a blazing cyan soul core!
Preserves all bone names (root, base, core, fang_0..5, tilt_0..5) and animations 100% intact.
"""
import json, math, random, sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
R = P / "src/main/resources/assets/pysift"
FANGS = 6
RING = 3.5

# ------------------------------------------------------------------ 1:1 UV Packer (64x64)
TEX_W, TEX_H = 64, 64


class Packer:
    def __init__(self, w=64, h=64):
        self.w, self.h = w, h
        self.used = [[False] * w for _ in range(h)]
        self.rects = []
        self.cache = {}

    def alloc(self, w, h, role, face="side"):
        w, h = max(1, int(round(w))), max(1, int(round(h)))
        for y in range(self.h - h + 1):
            for x in range(self.w - w + 1):
                if all(not self.used[yy][xx] for yy in range(y, y + h) for xx in range(x, x + w)):
                    for yy in range(y, y + h):
                        for xx in range(x, x + w):
                            self.used[yy][xx] = True
                    self.rects.append((role, face, x, y, w, h))
                    return x, y, w, h
        raise RuntimeError(f"Out of UV space for {role}.{face} ({w}x{h}) on {self.w}x{self.h}")

    def box(self, origin, size, role, pivot=None, rotation=None, share=True):
        sx, sy, sz = (max(1, int(round(v))) for v in size)
        dims = {"north": (sx, sy), "south": (sx, sy), "east": (sz, sy), "west": (sz, sy), "up": (sx, sz), "down": (sx, sz)}
        uv = {}
        for f, (fw, fh) in dims.items():
            group = "side" if f in ("north", "south", "east", "west") else f
            key = (role, group, fw, fh) if share else None
            if key and key in self.cache:
                u, v, rw, rh = self.cache[key]
            else:
                u, v, rw, rh = self.alloc(fw, fh, role, face=f)
                if key:
                    self.cache[key] = (u, v, rw, rh)
            uv[f] = {"uv": [u, v], "uv_size": [rw, rh]}
        c = {"origin": [round(x, 3) for x in origin], "size": [round(x, 3) for x in size], "uv": uv}
        if pivot is not None:
            c["pivot"] = [round(x, 3) for x in pivot]
        if rotation is not None:
            c["rotation"] = [round(x, 3) for x in rotation]
        return c

    def plane(self, origin, size, role, pivot=None, rotation=None, share=True):
        """0.05-thick 2-sided alpha-cutout razor plane with exact 1:1 integer UV."""
        sx, sy, sz = size
        if sz <= 0.1:
            faces, uw, vh = ("north", "south"), max(1, int(round(sx))), max(1, int(round(sy)))
        elif sx <= 0.1:
            faces, uw, vh = ("east", "west"), max(1, int(round(sz))), max(1, int(round(sy)))
        else:
            faces, uw, vh = ("up", "down"), max(1, int(round(sx))), max(1, int(round(sz)))
        key = (role, "plane", uw, vh) if share else None
        if key and key in self.cache:
            u, v, rw, rh = self.cache[key]
        else:
            u, v, rw, rh = self.alloc(uw, vh, role, face="plane")
            if key:
                self.cache[key] = (u, v, rw, rh)
        uv = {faces[0]: {"uv": [u, v], "uv_size": [rw, rh]}, faces[1]: {"uv": [u, v], "uv_size": [rw, rh]}}
        c = {"origin": [round(x, 3) for x in origin], "size": [round(x, 3) for x in size], "uv": uv}
        if pivot is not None:
            c["pivot"] = [round(x, 3) for x in pivot]
        if rotation is not None:
            c["rotation"] = [round(x, 3) for x in rotation]
        return c


pk = Packer(TEX_W, TEX_H)

# ------------------------------------------------------------------ Build Razor-Fanged Geometry (100% 1:1 UV)
bones = [
    {"name": "root", "pivot": [0, 0, 0]},
    {
        "name": "base",
        "parent": "root",
        "pivot": [0, 0, 0],
        "cubes": [
            # Cracked abyssal sculk crater slab
            pk.box([-5.5, 0, -5.5], [11, 1, 11], "sculk", share=False),
            # Irregular jagged sculk rim ridges around the crater
            pk.box([-3.5, 1, -6.2], [7, 1, 2], "sculk_rim"),
            pk.box([-6.2, 1, -2.5], [2, 1, 6], "sculk_rim"),
            pk.box([3.5, 1, -3.5], [3, 1, 5], "sculk_rim"),
            pk.box([-2.5, 1, 4.2], [6, 1, 2], "sculk_rim"),
            # Inner dark abyssal throat pit
            pk.box([-3.0, 0.8, -3.0], [6, 1, 6], "throat", share=False),
        ],
    },
    {
        "name": "core",
        "parent": "root",
        "pivot": [0, 2.5, 0],
        "cubes": [
            # Blazing soul-cyan inner core + diamond-rotated crystalline spark!
            pk.box([-1.5, 1.0, -1.5], [3, 3, 3], "core"),
            pk.box([-1.0, 1.5, -1.0], [2, 2, 2], "core_spark", pivot=[0, 2.5, 0], rotation=[45, 45, 0]),
        ],
    },
]

for i in range(FANGS):
    bones.append({"name": f"fang_{i}", "parent": "root", "pivot": [0, 0, 0], "rotation": [0, 360 / FANGS * i, 0]})
    jaw_cubes = [
        # 1. Muscular dark sculk jaw gum base (flares slightly outward from crater)
        pk.box([-1.5, 0.8, -RING - 1.5], [3, 3, 2], "jaw_gum", pivot=[0, 1.0, -RING], rotation=[8, 0, 0]),
        # 2. Primary Hooked Bone Fang — Root segment (curving INWARD toward core!)
        pk.box([-1.0, 3.4, -RING - 1.2], [2, 3, 2], "fang_root", pivot=[0, 3.6, -RING - 0.2], rotation=[-16, 0, 0]),
        # 3. Primary Hooked Bone Fang — Sleek 1x3x1 tapered bone blade curving further inward!
        pk.box([-0.5, 6.0, -RING - 0.3], [1, 3, 1], "fang_mid", pivot=[0, 6.2, -RING + 0.2], rotation=[-32, 0, 0]),
        # 4. Primary Razor Needle Tip — ODD 3x5 crossed alpha-cutout razor fang tapering to a TRUE 1px needle tip!
        pk.plane([-1.5, 7.6, -RING + 1.05], [3.0, 5.0, 0.05], "fang_needle", pivot=[0, 7.8, -RING + 1.05], rotation=[-46, 0, 0]),
        pk.plane([-0.025, 7.6, -RING - 0.45], [0.05, 5.0, 3.0], "fang_needle", pivot=[0, 7.8, -RING + 1.05], rotation=[-46, 0, 0]),
        # 5. Curved Flanking Razor Side Fangs (3x6 mirrored hooked bone teeth on left & right of each jaw!)
        pk.plane([-3.2, 2.4, -RING - 0.5], [3.0, 6.0, 0.05], "side_fang_l", pivot=[-1.5, 2.6, -RING - 0.5], rotation=[-20, 26, -12]),
        pk.plane([0.2, 2.4, -RING - 0.5], [3.0, 6.0, 0.05], "side_fang_r", pivot=[1.5, 2.6, -RING - 0.5], rotation=[-20, -26, 12]),
        # 6. Inner Serrated Throat Barbs (5x5 double needle-point bone teeth lining the inner mouth!)
        pk.plane([-2.5, 2.0, -RING + 0.80], [5.0, 5.0, 0.05], "inner_teeth", pivot=[0, 2.2, -RING + 0.80], rotation=[-24, 0, 0]),
    ]
    bones.append({"name": f"tilt_{i}", "parent": f"fang_{i}", "pivot": [0, 1, -RING], "cubes": jaw_cubes})

geo = {
    "format_version": "1.12.0",
    "minecraft:geometry": [
        {
            "description": {
                "identifier": "geometry.sculk_maw",
                "texture_width": TEX_W,
                "texture_height": TEX_H,
                "visible_bounds_width": 2.4,
                "visible_bounds_height": 2.4,
                "visible_bounds_offset": [0, 0.6, 0],
            },
            "bones": bones,
        }
    ],
}

# ------------------------------------------------------------------ Paint Crisp Pixel-Art Razor Fangs + Emissive Glowmask
img = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 0))
glow = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 0))
px = img.load()
gpx = glow.load()
rnd = random.Random(20261124)

SCULK_DARK = [(4, 18, 28), (8, 30, 44), (13, 46, 62), (20, 68, 86)]
SCULK_VEIN = [(26, 184, 204), (66, 224, 240), (144, 246, 252)]
BONE_RAMP = [(56, 58, 52), (96, 98, 86), (148, 148, 130), (198, 196, 174), (232, 228, 206), (250, 248, 234)]
CORE_RAMP = [(28, 176, 202), (76, 222, 240), (154, 244, 252), (218, 252, 255)]


def sample(ramp, t):
    t = max(0.0, min(1.0, t))
    f = t * (len(ramp) - 1)
    k = min(len(ramp) - 2, int(f))
    a, b = ramp[k], ramp[k + 1]
    u = f - k
    return tuple(int(round(a[i] + (b[i] - a[i]) * u)) for i in range(3))


# Hand-crafted razor-sharp pixel masks ('.'=transparent, 'S'=sculk root, 'b'=bone shadow, 'B'=bone bright, 'W'=ivory edge, 'C'=cyan glowing razor tip!)
NEEDLE_3x5 = [
    ".C.",  # y=0: TRUE 1px glowing razor needle point!
    ".C.",  # y=1: slender 1px razor tip!
    ".W.",  # y=2: ivory razor blade!
    "bWB",  # y=3: tapered bone shoulder
    "bBB",  # y=4: grips seamlessly onto fang_mid
]

SIDE_FANG_L_3x6 = [
    "..C",  # y=0: curved 1px hooked razor tip leaning inward toward center!
    "..W",  # y=1: slender 1px curved blade!
    ".WB",  # y=2: curved mid-fang!
    ".Bb",  # y=3: widening downward!
    "BBb",  # y=4: broad bone base!
    "SbS",  # y=5: sculk gum socket!
]
SIDE_FANG_R_3x6 = [row[::-1] for row in SIDE_FANG_L_3x6]

INNER_TEETH_5x5 = [
    "..W..",  # y=0: tall central inner needle tooth!
    ".bW..",  # y=1
    "W.B.W",  # y=2: flanking sharp inner teeth!
    "BbBbB",  # y=3: serrated bone ridge!
    "SSbSS",  # y=4: dark sculk inner gum!
]

MASK_COLOR = {
    "S": ((10, 36, 52), False),
    "b": ((124, 124, 108), False),
    "B": ((206, 204, 182), False),
    "W": ((248, 246, 232), False),
    "C": ((120, 242, 252), True),
}


def paint_mask(mask, x0, y0):
    for yy, row in enumerate(mask):
        for xx, ch in enumerate(row):
            if ch in MASK_COLOR:
                col, emit = MASK_COLOR[ch]
                px[x0 + xx, y0 + yy] = (*col, 255)
                if emit:
                    gpx[x0 + xx, y0 + yy] = (*col, 255)


for role, face, x0, y0, w, h in pk.rects:
    if role == "fang_needle":
        paint_mask(NEEDLE_3x5, x0, y0)
        continue
    if role == "side_fang_l":
        paint_mask(SIDE_FANG_L_3x6, x0, y0)
        continue
    if role == "side_fang_r":
        paint_mask(SIDE_FANG_R_3x6, x0, y0)
        continue
    if role == "inner_teeth":
        paint_mask(INNER_TEETH_5x5, x0, y0)
        continue

    for yy in range(h):
        lv = (yy + 0.5) / h
        for xx in range(w):
            lu = (xx + 0.5) / w
            n = rnd.random()
            col = None
            emit = False

            if role in ("sculk", "sculk_rim"):
                edge_hi = 0.25 if (face == "up" and (xx == 0 or yy == 0 or xx == w - 1 or yy == h - 1)) else 0.0
                if (xx * 7 + yy * 13) % 19 == 0 or (face == "up" and n > 0.91):
                    col = sample(SCULK_VEIN, 0.3 + 0.6 * n)
                    emit = True
                else:
                    col = sample(SCULK_DARK, 0.18 + 0.55 * n + edge_hi)

            elif role == "throat":
                dist = math.hypot((lu - 0.5) * 2.0, (lv - 0.5) * 2.0)
                if dist < 0.55:
                    col = sample(SCULK_VEIN, 0.85 - dist)
                    emit = True
                else:
                    col = sample(SCULK_DARK, max(0.0, 0.35 - dist * 0.25))

            elif role in ("core", "core_spark"):
                d = math.hypot((lu - 0.5) * 2.0, (lv - 0.5) * 2.0)
                col = sample(CORE_RAMP, 0.95 - d * 0.55 + 0.12 * n)
                emit = True

            elif role == "jaw_gum":
                if face in ("north", "south", "east", "west") and abs(lu - 0.5) < 0.24 and lv > 0.25 and ((yy + xx) % 2 == 0):
                    col = sample(SCULK_VEIN, 0.4 + 0.5 * (1.0 - lv))
                    emit = True
                else:
                    col = sample(SCULK_DARK, 0.15 + 0.65 * (1.0 - lv) + 0.15 * n)

            elif role == "fang_root":
                if lv > 0.72:
                    col = sample(SCULK_DARK, 0.55 + 0.3 * (1.0 - lv))
                else:
                    shade = 0.30 + 0.56 * (1.0 - lv) + (0.14 if lu < 0.5 else -0.10)
                    col = sample(BONE_RAMP, shade)

            elif role == "fang_mid":
                shade = 0.62 + 0.36 * (1.0 - lv) + (0.10 if face in ("north", "east", "up") else -0.08)
                col = sample(BONE_RAMP, shade)

            if col is not None:
                px[x0 + xx, y0 + yy] = (*col, 255)
                if emit:
                    gpx[x0 + xx, y0 + yy] = (*col, 255)

(R / "geckolib/models/entity/sculk_maw.geo.json").write_text(json.dumps(geo, indent=2) + "\n", encoding="utf-8")
img.save(R / "textures/entity/sculk_maw.png")
glow.save(R / "textures/entity/sculk_maw_glowmask.png")
print(f"sculk_maw razor-fang v2 complete: {len(bones)} bones, {len(pk.rects)} UV tiles, glow pixels={sum(1 for y in range(TEX_H) for x in range(TEX_W) if gpx[x,y][3]>0)}")
