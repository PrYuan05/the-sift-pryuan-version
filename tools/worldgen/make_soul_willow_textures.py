"""Cut the user's soul willow art sheet into block textures and derive the colour variants.
Usage: python -I tools/worldgen/make_soul_willow_textures.py <project>

Source: tools/worldgen/art/soul_willow_sheet.png (32x32, four 16x16 tiles, drawn by the user):
  top-left = leaves, top-right = vine body, bottom-left = vine end piece (tip), bottom-right = log side.
The sheet itself is never modified. Outputs go to textures/block/vegetation/:
  soul_willow_leaves / _leaves_pale / _leaves_glowing       leaves as drawn, pale-blue blend, glowing (near white) blend
  soul_willow_vine_<shade> / soul_willow_vine_tip_<shade>   shade 0 = as drawn, 1 = pale blue, 2 = white / lavender
  soul_willow_log_side                                      as drawn
  soul_willow_log_top                                       umber_log_top remapped by brightness onto the log side palette
The blocks are not tinted in game: all colour comes from these PNGs (tools/worldgen/build_vegetation.py wires them)."""
import sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1])
SHEET = P / "tools/worldgen/art/soul_willow_sheet.png"
T = P / "src/main/resources/assets/pysift/textures/block"
OUT = T / "vegetation"

PALE = (170, 206, 242)       # pale blue
GLOW = (226, 255, 248)       # glowing leaves: almost white mint
WHITE = (238, 230, 252)      # vine end: white / lavender


def tile(sheet, col, row):
    return sheet.crop((col * 16, row * 16, col * 16 + 16, row * 16 + 16))


def blend(im, target, amount):
    """Mix every visible pixel toward `target` by `amount`, keeping alpha (the pattern stays, the hue shifts)."""
    out = Image.new("RGBA", im.size)
    out.putdata([(c if c[3] == 0 else (*(round(v * (1 - amount) + t * amount) for v, t in zip(c[:3], target)), c[3]))
                 for c in im.get_flattened_data()])
    return out


def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def remap_onto(src, palette_image):
    """Brightness-rank remap of src onto the colours of palette_image (dark -> light)."""
    ramp = sorted({c[:3] for c in palette_image.get_flattened_data() if c[3] > 0}, key=lum)
    px = list(src.get_flattened_data())
    ls = [lum(c) for c in px if c[3] > 0]
    lo, hi = min(ls), max(ls)
    out = Image.new("RGBA", src.size)
    out.putdata([c if c[3] == 0 else (*ramp[min(len(ramp) - 1, int((lum(c) - lo) / (hi - lo or 1) * len(ramp)))], c[3])
                 for c in px])
    return out


sheet = Image.open(SHEET).convert("RGBA")
assert sheet.size == (32, 32), sheet.size
leaves, vine, vine_tip, log_side = tile(sheet, 0, 0), tile(sheet, 1, 0), tile(sheet, 0, 1), tile(sheet, 1, 1)
OUT.mkdir(parents=True, exist_ok=True)
files = {
    "soul_willow_leaves": leaves,
    "soul_willow_leaves_pale": blend(leaves, PALE, 0.45),
    "soul_willow_leaves_glowing": blend(leaves, GLOW, 0.55),
    "soul_willow_log_side": log_side,
    "soul_willow_log_top": remap_onto(Image.open(T / "umber_log/umber_log_top.png").convert("RGBA"), log_side),
}
for shade, (target, amount) in enumerate(((None, 0.0), (PALE, 0.5), (WHITE, 0.65))):
    files[f"soul_willow_vine_{shade}"] = vine if target is None else blend(vine, target, amount)
    files[f"soul_willow_vine_tip_{shade}"] = vine_tip if target is None else blend(vine_tip, target, amount)
for name, im in files.items():
    im.save(OUT / f"{name}.png")
print("wrote", len(files), "textures to", OUT.relative_to(P))
