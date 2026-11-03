"""Sculk Maw (SculkMawEntity, the Sculk Hammer's ground tendril): GeckoLib model, texture and animations.
Usage: python -I tools/entity/build_sculk_maw.py <project>

A ring of six sculk fangs around a glowing soul core, growing out of a patch of sculk:
  emerge - shoots up out of the ground and the fangs fan open
  idle   - the fangs twitch, the core pulses
  bite   - the fangs open wide, then snap shut over the core (tick 5 = SculkMawEntity.SNAP_TICK), the core bursts and the
           maw sinks back into the ground (0.6 s = BITE_TICKS)
The texture goes through tools/art_guard.py (a hand-painted replacement is kept)."""
import json, math, random, sys
from pathlib import Path

from PIL import Image

P = Path(sys.argv[1])
sys.path.insert(0, str(P / "tools"))
import art_guard

R = P / "src/main/resources/assets/pysift"
FANGS = 6
RING = 3.5          # fang distance from the centre (model pixels)


def cube(origin, size, role):
    return {"origin": origin, "size": size, "role": role}


BONES = [{"name": "root", "pivot": [0, 0, 0], "cubes": []},
         {"name": "base", "parent": "root", "pivot": [0, 0, 0],
          "cubes": [cube([-5, 0, -5], [10, 1, 10], "sculk"), cube([-3, 1, -6], [6, 1, 2], "sculk"),
                    cube([-6, 1, -2], [2, 1, 5], "sculk"), cube([3, 1, 3], [3, 1, 2], "sculk")]},
         {"name": "core", "parent": "root", "pivot": [0, 2.5, 0], "cubes": [cube([-1.5, 1, -1.5], [3, 3, 3], "core")]}]
for i in range(FANGS):
    BONES.append({"name": f"fang_{i}", "parent": "root", "pivot": [0, 0, 0], "rotation": [0, 360 / FANGS * i, 0], "cubes": []})
    BONES.append({"name": f"tilt_{i}", "parent": f"fang_{i}", "pivot": [0, 1, -RING],
                  "cubes": [cube([-1, 1, -RING - 1], [2, 5, 2], "fang"), cube([-0.5, 6, -RING - 0.5], [1, 3, 1], "tip")]})

PALETTE = {"sculk": [(6, 24, 36), (12, 40, 55), (18, 56, 72), (40, 130, 150)],
           "fang": [(10, 30, 44), (22, 58, 74), (34, 86, 100), (70, 150, 160)],
           "tip": [(120, 200, 205), (170, 235, 238), (215, 250, 250)],
           "core": [(40, 190, 210), (110, 225, 240), (190, 250, 255)]}


def paint(img, role, face, rect, rnd):
    x0, y0, w, h = rect
    pal = PALETTE[role]
    px = img.load()
    for j in range(h):
        for i in range(w):
            r = rnd.random()
            if role == "fang":       # darker at the root, lighter toward the tip, a glowing vein up the middle
                t = 1 - (j + 0.5) / h
                c = pal[min(3, int(t * 3 + r * 0.6))]
                if face in ("north", "south") and i == w // 2 and r > 0.5:
                    c = PALETTE["core"][0]
            elif role == "sculk":
                c = pal[0 if r < 0.35 else 1 if r < 0.8 else 2]
                if r > 0.95:
                    c = pal[3]
            else:
                c = pal[0 if r < 0.3 else 1 if r < 0.75 else 2]
            px[x0 + i, y0 + j] = c + (255,)


def face_size(face, size):
    x, y, z = (max(1, math.ceil(v)) for v in size)
    return {"north": (x, y), "south": (x, y), "east": (z, y), "west": (z, y), "up": (x, z), "down": (x, z)}[face]


TEX_W, TEX_H = 64, 64
img = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 0))
rnd = random.Random("sculk_maw")
cx = cy = row_h = 0
geo_bones = []
for b in BONES:
    out = {k: v for k, v in b.items() if k != "cubes"}
    cubes = []
    for c in b["cubes"]:
        uv = {}
        for f in ("north", "south", "east", "west", "up", "down"):
            w, h = face_size(f, c["size"])
            if cx + w > TEX_W:
                cx, cy, row_h = 0, cy + row_h, 0
            assert cy + h <= TEX_H
            paint(img, c["role"], f, (cx, cy, w, h), rnd)
            uv[f] = {"uv": [cx, cy], "uv_size": [w, h]}
            cx += w
            row_h = max(row_h, h)
        cubes.append({"origin": c["origin"], "size": c["size"], "uv": uv})
    if cubes:
        out["cubes"] = cubes
    geo_bones.append(out)

geo = {"format_version": "1.12.0", "minecraft:geometry": [{
    "description": {"identifier": "geometry.sculk_maw", "texture_width": TEX_W, "texture_height": TEX_H,
                    "visible_bounds_width": 2, "visible_bounds_height": 2, "visible_bounds_offset": [0, 0.5, 0]},
    "bones": geo_bones}]}


def kf(*frames):
    return {f"{t:.2f}".rstrip("0").rstrip(".") if t % 1 else f"{t:.1f}": v for t, v in frames}


# fang tilt: +x tips the fang outward (open), -x folds it over the core (closed)
anims = {
    "animation.sculk_maw.emerge": {"animation_length": 0.4, "bones": {
        "root": {"position": kf((0, [0, -8, 0]), (0.25, [0, 0.6, 0]), (0.4, [0, 0, 0]))},
        "core": {"scale": kf((0, [0.2, 0.2, 0.2]), (0.4, [1, 1, 1]))},
        **{f"tilt_{i}": {"rotation": kf((0, [-30, 0, 0]), (0.3, [30, 0, 0]), (0.4, [22, 0, 0]))} for i in range(FANGS)}}},
    "animation.sculk_maw.idle": {"loop": True, "animation_length": 1.0, "bones": {
        "core": {"scale": kf((0, [1, 1, 1]), (0.5, [1.2, 1.2, 1.2]), (1.0, [1, 1, 1]))},
        **{f"tilt_{i}": {"rotation": kf(*[(k / 4, [round(22 + 6 * math.sin(2 * math.pi * k / 4 + i * 1.3), 2), 0, 0])
                                           for k in range(5)])} for i in range(FANGS)}}},
    "animation.sculk_maw.bite": {"animation_length": 0.6, "bones": {
        "root": {"position": kf((0, [0, 0, 0]), (0.35, [0, 0.5, 0]), (0.6, [0, -9, 0]))},
        "core": {"scale": kf((0, [1.2, 1.2, 1.2]), (0.2, [1.6, 1.6, 1.6]), (0.25, [2.4, 2.4, 2.4]), (0.32, [0, 0, 0]),
                             (0.6, [0, 0, 0]))},
        **{f"tilt_{i}": {"rotation": kf((0, [22, 0, 0]), (0.15, [48, 0, 0]), (0.25, [-42, 0, 0]), (0.35, [-34, 0, 0]),
                                        (0.6, [-38, 0, 0]))} for i in range(FANGS)}}},
}

(R / "geckolib/models/entity").mkdir(parents=True, exist_ok=True)
(R / "geckolib/animations/entity").mkdir(parents=True, exist_ok=True)
(R / "geckolib/models/entity/sculk_maw.geo.json").write_text(json.dumps(geo, indent=2) + "\n", encoding="utf-8")
(R / "geckolib/animations/entity/sculk_maw.animation.json").write_text(
    json.dumps({"format_version": "1.8.0", "animations": anims}, indent=2) + "\n", encoding="utf-8")
art_guard.save(img, R / "textures/entity/sculk_maw.png")
print(f"sculk_maw: {len(geo_bones)} bones, animations {sorted(a.split('.')[-1] for a in anims)}")
