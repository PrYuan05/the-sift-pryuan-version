"""Top-down map of a saved test-server area in texture colours (highest block per column, brighter = higher).
Usage: python -I tools/worldgen/topmap.py x z [half] [out]   (reads run-server/<level>, run devserver.py gen first)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import devserver as d
from PIL import Image

x, z = int(sys.argv[1]), int(sys.argv[2])
h = int(sys.argv[3]) if len(sys.argv) > 3 else 80
out = sys.argv[4] if len(sys.argv) > 4 else f"build/texture_pipeline/out/topmap_{x}_{z}.png"
box = d.blocks_in_box(x - h, 40, z - h, x + h - 1, 160, z + h - 1, with_props=True)
top = {}
for (bx, by, bz), name in box.items():
    if (bx, bz) not in top or by > top[(bx, bz)][0]:
        top[(bx, bz)] = (by, name)
ys = [v[0] for v in top.values()]
lo, hi = min(ys), max(ys)
img = Image.new("RGB", (2 * h, 2 * h), (0, 0, 0))
for (bx, bz), (by, name) in top.items():
    c = d.texture_color(name, "top")
    # height tint plus hillshade (light from the north-west) so slopes, steps and dune crests read clearly
    nw = top.get((bx - 1, bz - 1), (by, None))[0]
    k = (0.55 + 0.45 * (by - lo) / max(1, hi - lo)) * max(0.45, min(1.6, 1.0 + 0.18 * (by - nw)))
    img.putpixel((bx - x + h, bz - z + h), tuple(min(255, int(v * k)) for v in c))
img = img.resize((4 * h, 4 * h), Image.Resampling.NEAREST)
Path(d.ROOT / out).parent.mkdir(parents=True, exist_ok=True)
img.save(d.ROOT / out)
print(out, "y range", lo, hi)
