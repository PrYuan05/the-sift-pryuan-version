"""Oblique 3D view of a saved test-server area in texture colours (painter's algorithm, looking north).
Usage: python -I tools/worldgen/oblique.py x z [half] [out]   (reads run-server/<level>; run devserver.py gen first)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import devserver as d
from PIL import Image

x, z = int(sys.argv[1]), int(sys.argv[2])
h = int(sys.argv[3]) if len(sys.argv) > 3 else 100
out = sys.argv[4] if len(sys.argv) > 4 else f"build/texture_pipeline/out/oblique_{x}_{z}.png"
box = d.blocks_in_box(x - h, 30, z - h, x + h - 1, 170, z + h - 1, with_props=True)
top = {}
for (bx, by, bz), name in box.items():
    if (bx, bz) not in top or by > top[(bx, bz)][0]:
        top[(bx, bz)] = (by, name)
S, YK = 3, 3                                  # pixels per block horizontally, per block of height
YTOP = 170
img = Image.new("RGB", (2 * h * S + 40, h * S + (YTOP - 30) * YK + 20), (205, 170, 160))
px_ = img.load()


def rect(x0, y0, w, hgt, col):
    for py in range(max(0, y0), min(img.height, y0 + hgt)):
        for px in range(max(0, x0), min(img.width, x0 + w)):
            px_[px, py] = col


for depth in range(2 * h):                    # north (far) rows first, viewer looks north from the south
    for i in range(2 * h):
        bx, bz = x - h + i, z - h + depth
        if (bx, bz) not in top:
            continue
        by, name = top[(bx, bz)]
        sx, sy = 20 + i * S, depth * S // 2 + (YTOP - by) * YK
        south = top.get((bx, bz + 1), (30,))[0]
        drop = max(0, by - south)
        rect(sx, sy + S // 2, S, drop * YK + S, tuple(int(v * 0.6) for v in d.texture_color(name, "side")))
        rect(sx, sy, S, S // 2 + 1, d.texture_color(name, "top"))
Path(d.ROOT / out).parent.mkdir(parents=True, exist_ok=True)
img.save(d.ROOT / out)
print(out)
