"""Make the salmon-pink willow grove soil texture from banded_mudstone banding=0 (the source is left untouched).
Usage: python -I tools/worldgen/make_pink_loam.py <project>
Brightness remap (as recolor.py palette mode) onto a salmon ramp with deep pink patches, like the reference art.
Other source options were compared in build/texture_pipeline/out/pink_loam_options.png."""
import sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1])
T = P / "src/main/resources/assets/pysift/textures/block"
SOURCE = T / "banded_mudstone/banded_mudstone_banding0.png"
SALMON = [(0xC0, 0x6A, 0x7C), (0xD4, 0x82, 0x86), (0xE2, 0x96, 0x8E),     # dark -> light: deep pink patches ...
          (0xEB, 0xA6, 0x98), (0xF2, 0xB6, 0xA6), (0xF6, 0xC5, 0xB4)]     # ... into salmon / peach


def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


src = Image.open(SOURCE).convert("RGBA")
px = list(src.getdata())
ls = [lum(c) for c in px if c[3] > 0]
lo, hi = min(ls), max(ls)
out = []
for c in px:
    if c[3] == 0:
        out.append(c)
        continue
    t = (lum(c) - lo) / (hi - lo) if hi > lo else 0.5
    out.append((*SALMON[min(len(SALMON) - 1, int(t * len(SALMON)))], c[3]))
img = Image.new("RGBA", src.size)
img.putdata(out)
dst = T / "vegetation/sift_pink_loam.png"
dst.parent.mkdir(parents=True, exist_ok=True)
img.save(dst)
print("wrote", dst.relative_to(P))
