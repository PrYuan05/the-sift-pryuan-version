"""Paint the block textures of the 9 new Sift colours from the user's dye drawings (minecraft-texture-crafter, method C:
rank remapping). The tinted vanilla white textures had too little contrast; this keeps vanilla's structure (the order of
its brightness levels) and maps every level onto the colour ramp of the user's dye.

  python -I tools/progression/paint_sift_colors.py <project> [--preview] [--only bed_,item_cushion,entity_cushion]

--only: paint just the kinds starting with one of these prefixes (the others keep their current files).

- Ramp: the pigment pixels of textures/item/<colour>_dye.png, without the brown dish (the colours every dye shares, plus
  the two dish shadows) and without accents whose hue is far from the dye's main hue (coral's yellow highlight,
  lavender's pink, void's cyan glow, dusk gold's orange heart). Sorted dark -> light; near-identical colours merged.
- Each kind uses its own window of that ramp (WINDOWS): concrete is narrow and flat like vanilla concrete, terracotta
  dark and muted like fired clay, glass light and keeps vanilla's alpha.
- Writes textures/block/sift_colors/<colour>_<kind>.png; tools/progression/build_sift_colors.py then uses them instead
  of the tint. Glazed terracotta and the dyes are the user's drawings and are never written here."""
import colorsys, io, math, sys, zipfile
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw

P = Path(sys.argv[1])
T = P / "src/main/resources/assets/pysift/textures"
JAR = zipfile.ZipFile(Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client-only.jar")
COLOURS = ["teal", "mint", "coral", "amber", "lavender", "rose", "soul_blue", "void", "dusk_gold"]
DISH_SHADOWS = {(0x57, 0x2B, 0x23), (0x6E, 0x4A, 0x3B)}
# kind: (vanilla white texture, ramp window low, high, saturation factor, levels)
# levels None = snap every vanilla level to the dye's own colours (wool, powder, glass: lively, a handful of levels);
# levels N = matte materials: N close shades blended between the window's two ends (narrow value span, no stray dots)
WINDOWS = {   # narrow windows: contrast close to vanilla's own variation (user: lower contrast, same hues)
    "wool": ("white_wool", 0.48, 0.74, 1.0, 5),
    "concrete": ("white_concrete", 0.54, 0.56, 1.0, 2),
    "concrete_powder": ("white_concrete_powder", 0.50, 0.70, 1.0, 4),
    "terracotta": ("white_terracotta", 0.30, 0.40, 0.70, 4),
    "stained_glass": ("white_stained_glass", 0.52, 0.72, 1.0, 3),
    "stained_glass_pane_top": ("white_stained_glass_pane_top", 0.52, 0.72, 1.0, 3),
    "candle": ("white_candle", 0.40, 0.80, 1.0, 4),
    "candle_lit": ("white_candle_lit", 0.40, 0.80, 1.0, 4),          # the flame keeps vanilla's own colours (see below)
    "item_candle": ("item:white_candle", 0.40, 0.80, 1.0, 4),
    # beds and cushions: only the cloth is dyed (the pixels that differ between vanilla's white and red versions);
    # the wooden frame and the white pillow keep vanilla's colours
    **{f"bed_{part}": (f"white_bed_{part}", 0.48, 0.74, 1.0, 5)
       for part in ("foot_east", "foot_south", "foot_up", "foot_west", "head_east", "head_up", "head_west")},
    "item_cushion": ("item:white_cushion", 0.48, 0.74, 1.0, 5),
    "entity_cushion": ("entity/cushion:white_cushion", 0.48, 0.74, 1.0, 5),
}
# kinds written somewhere else than textures/block/sift_colors/<colour>_<kind>.png
OUT_PATH = {"entity_cushion": "entity/cushion/{colour}_cushion.png"}


KEEP_FLAME = {"candle_lit", "item_candle"}


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def dye_pixels(colour):
    im = Image.open(T / f"item/{colour}_dye.png").convert("RGBA")
    return [p[:3] for p in im.get_flattened_data() if p[3] > 0]


# the dish: colours every dye shares
DISH = set.intersection(*[set(dye_pixels(c)) for c in COLOURS]) | DISH_SHADOWS


def ramp_of(colour):
    count = Counter(p for p in dye_pixels(colour) if p not in DISH)
    # main hue: circular mean of the saturated pixels, weighted by count
    x = y = 0.0
    for c, n in count.items():
        h, s, v = colorsys.rgb_to_hsv(*(k / 255 for k in c))
        if s > 0.2:
            x += n * s * math.cos(h * 2 * math.pi)
            y += n * s * math.sin(h * 2 * math.pi)
    main = (math.atan2(y, x) / (2 * math.pi)) % 1.0
    keep = []
    for c in count:
        h, s, v = colorsys.rgb_to_hsv(*(k / 255 for k in c))
        dh = abs(((h - main + 0.5) % 1.0) - 0.5) * 360
        if s < 0.2 or dh <= 40:                       # accents of another hue stay on the dye only
            keep.append(c)
    keep.sort(key=lum)
    merged = []
    for c in keep:                                    # merge near-identical colours (soul blue has many)
        if merged and abs(lum(c) - lum(merged[-1])) < 6:
            continue
        merged.append(c)
    return merged


def sample(ramp, t):
    """The ramp colour closest to brightness position t (0 = the ramp's darkest, 1 = its lightest).
    By brightness, not by index: a ramp with many light colours (soul blue) would otherwise come out pale everywhere.
    No in-between colours: every block uses only the colours drawn on its dye, a handful of levels per texture like
    vanilla, instead of dozens of blended shades."""
    lo, hi = lum(ramp[0]), lum(ramp[-1])
    target = lo + (hi - lo) * min(1.0, max(0.0, t))
    return min(ramp, key=lambda c: abs(lum(c) - target))


def blend(ramp, t):
    """Colour at brightness position t, blended between the two ramp colours around it (for the matte materials)."""
    lo, hi = lum(ramp[0]), lum(ramp[-1])
    target = lo + (hi - lo) * min(1.0, max(0.0, t))
    for a, b in zip(ramp, ramp[1:]):
        if lum(a) <= target <= lum(b):
            f = (target - lum(a)) / max(1e-6, lum(b) - lum(a))
            return tuple(round(a[k] * (1 - f) + b[k] * f) for k in range(3))
    return ramp[-1]


def desaturate(c, factor):
    h, l, s = colorsys.rgb_to_hls(*(k / 255 for k in c))
    return tuple(round(k * 255) for k in colorsys.hls_to_rgb(h, l, s * factor))


def paint(colour, kind):
    src_name, lo, hi, sat, steps = WINDOWS[kind]
    folder, name = src_name.split(":") if ":" in src_name else ("block", src_name)
    src = Image.open(io.BytesIO(JAR.read(f"assets/minecraft/textures/{folder}/{name}.png"))).convert("RGBA")
    ramp = ramp_of(colour)
    dyed = None
    if kind.startswith(("bed_", "item_cushion", "entity_cushion")):    # cloth mask: white vs red vanilla texture
        red = Image.open(io.BytesIO(JAR.read(f"assets/minecraft/textures/{folder}/{name.replace('white', 'red', 1)}.png"))).convert("RGBA")
        dyed = red.load()
    cloth = [p for i, p in enumerate(src.get_flattened_data())
             if p[3] > 0 and (dyed is None or dyed[i % src.width, i // src.width] != p)]
    levels = sorted({round(lum(p[:3])) for p in cloth})
    rank = {v: (i / (len(levels) - 1) if len(levels) > 1 else 0.5) for i, v in enumerate(levels)}
    out = Image.new("RGBA", src.size)
    po, ps = out.load(), src.load()
    for yy in range(src.height):
        for xx in range(src.width):
            r, g, b, a = ps[xx, yy]
            if a == 0:
                continue
            if dyed is not None and dyed[xx, yy] == (r, g, b, a):
                po[xx, yy] = (r, g, b, a)               # frame / pillow: not part of the cloth
                continue
            if kind in KEEP_FLAME and colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[1] > 0.35:
                po[xx, yy] = (r, g, b, a)               # the candle flame keeps vanilla's colours; only the wax is dyed
                continue
            t = rank[round(lum((r, g, b)))]
            if steps:                                  # matte: quantise to a few close shades
                q = min(steps - 1, int(t * steps))
                c = blend(ramp, lo + (hi - lo) * q / (steps - 1))
            else:
                c = sample(ramp, lo + (hi - lo) * t)
            if sat != 1.0:
                c = desaturate(c, sat)
            po[xx, yy] = (*c, a)
    return out


ONLY = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
written = []
for colour in COLOURS:
    for kind in WINDOWS:
        if ONLY and not kind.startswith(tuple(ONLY)):
            continue
        f = T / (OUT_PATH[kind].format(colour=colour) if kind in OUT_PATH else f"block/sift_colors/{colour}_{kind}.png")
        f.parent.mkdir(parents=True, exist_ok=True)
        paint(colour, kind).save(f)
        written.append(f)
print(f"painted {len(written)} textures for {len(COLOURS)} colours")

if "--preview" in sys.argv:
    # one row per colour: dye, ramp, then each kind as a 3x3 tile (glazed terracotta too, for comparison)
    S, TILE = 4, 48
    kinds = list(WINDOWS) + ["glazed_terracotta"]
    W = 16 * S + 8 + 9 * 10 + 8 + len(kinds) * (TILE * S // 4 * 1 + 0) + 0
    cell = TILE * 2 + 8
    sheet = Image.new("RGBA", (16 * S + 110 + len(kinds) * cell, len(COLOURS) * (cell + 6) + 20), (52, 52, 60, 255))
    d = ImageDraw.Draw(sheet)
    for i, kind in enumerate(kinds):
        d.text((16 * S + 110 + i * cell, 4), kind.replace("stained_glass", "glass")[:14], fill=(230, 230, 230))
    for r, colour in enumerate(COLOURS):
        y0 = 20 + r * (cell + 6)
        dye = Image.open(T / f"item/{colour}_dye.png").convert("RGBA").resize((16 * S, 16 * S), Image.NEAREST)
        sheet.paste(dye, (0, y0), dye)
        for j, c in enumerate(ramp_of(colour)):
            d.rectangle([16 * S + 8 + (j % 9) * 10, y0 + (j // 9) * 10, 16 * S + 16 + (j % 9) * 10, y0 + 8 + (j // 9) * 10], fill=c)
        for i, kind in enumerate(kinds):
            tex = Image.open(T / (OUT_PATH[kind].format(colour=colour) if kind in OUT_PATH
                                  else f"block/sift_colors/{colour}_{kind}.png")).convert("RGBA")
            tiled = Image.new("RGBA", (48, 48))
            for a in range(3):
                for b in range(3):
                    tiled.paste(tex.crop((0, 0, 16, 16)), (a * 16, b * 16))
            tiled = tiled.resize((TILE * 2, TILE * 2), Image.NEAREST)
            sheet.paste(tiled, (16 * S + 110 + i * cell, y0), tiled)
    out = P / "build/previews/sift_colors_painted.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print("preview:", out)
