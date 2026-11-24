"""Split the shared Dungeons 2 sheet into the five mobs' own textures, plus their climate variants (user 2026-11-24).

nester, pollinator, seedling, sprout and sentinel were converted from one Dungeons 2 sheet
(.texture_backups/20261124_mob_originals/files/textures/entity/nester_pollinator_seedling_sentinel_sprout.png) and all
five got a full copy of it. Each mob's uv rectangles point at its own part of that sheet, so:

  <mob>.png           only the sheet's pixels under the mob's own face rectangles (everything else transparent; the
                      original art and colours, no new pattern). The nester's and the pollinator's mouth faces now use
                      the sheet's unused mouth squares (tools/models/build_placeholder_variants.py fix_base_uvs).
  <mob>_tropical.png  the same, more saturated and a little brighter; 3D flowers (petals from the sheet's mouth pink,
                      centres from its tan; the second kind the other way round)
  <mob>_cold.png      cooler (30% towards a pale blue-grey of the same value); 3D fur parts (ruff, leg cuffs, round tail) painted from the mob's own
                      coat colours with soft in-between steps and frosted tips

The variant models come from tools/models/build_placeholder_variants.py (run it first). Eyes (faces of 4 px or less)
keep their colours in every variant.
Usage: python -I tools/texture_pipeline/paint_placeholder_mobs.py [--split] [mob ...]
  default   rebuilds <mob>_tropical / _cold from the live <mob>.png (the upgraded split)
  --split   first rewrites <mob>.png as the plain split (then run upgrade_placeholder_mobs.py again)
"""
import colorsys
import importlib.util
import json
import random
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import art_guard  # noqa: E402

RES = ROOT / "src/main/resources/assets/pysift"
GEO = RES / "geckolib/models/entity"
BACKUP = ROOT / ".texture_backups/20261124_mob_originals"
SHEET = BACKUP / "files/textures/entity/nester_pollinator_seedling_sentinel_sprout.png"
MOBS = ("nester", "pollinator", "seedling", "sprout", "sentinel")

# where each mob's coat is on the sheet (x, y, w, h): its colours make the cold fur
COAT = {"nester": (39, 91, 14, 15), "pollinator": (66, 90, 48, 14), "seedling": (97, 53, 30, 4),
        "sprout": (89, 5, 16, 12), "sentinel": (36, 15, 17, 17)}
PINK = (11, 95, 11, 12)      # the sheet's mouth pink
TAN = (66, 92, 48, 12)       # the sheet's tan

_spec = importlib.util.spec_from_file_location("placeholder_variants", ROOT / "tools/models/build_placeholder_variants.py")
PV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PV)


def hsv(c):
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c[:3]))
    return h * 360, s, v


def rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, max(0, min(1, s)), max(0, min(1, v)))
    return tuple(max(8, min(247, round(x * 255))) for x in (r, g, b))


def lum(c):
    return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255


def hue_lerp(a, b, t):
    d = ((b - a + 180) % 360) - 180
    return a + d * t


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def colours(img, rect):
    x0, y0, w, h = rect
    p = img.load()
    cs = {}
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if p[x, y][3]:
                cs[p[x, y][:3]] = cs.get(p[x, y][:3], 0) + 1
    total = sum(cs.values())
    main = [c for c, n in cs.items() if n >= max(3, 0.1 * total)] or list(cs)
    return sorted(main, key=lum)


def soft_ramp(cols, steps=6):
    """The sheet's own colours, dark -> light, with soft in-between steps (no new hues)."""
    lo, hi = cols[0], cols[-1]
    return [lerp(lo, hi, i / (steps - 1)) for i in range(steps)]


def faces(mob, suffix=""):
    g = json.loads((GEO / f"{mob}{suffix}.geo.json").read_text(encoding="utf-8"))["minecraft:geometry"][0]
    for b in g["bones"]:
        for c in b.get("cubes", []):
            for name, f in c["uv"].items():
                (u, v), (w, h) = f["uv"], f["uv_size"]
                yield name, int(min(u, u + w)), int(min(v, v + h)), int(abs(w)), int(abs(h))


# ------------------------------------------------------------------------------------------------------------ split
def split(mob, sheet):
    out = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    sp, op = sheet.load(), out.load()
    eyes = set()
    for _, x0, y0, w, h in faces(mob):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                op[x, y] = sp[x, y]
                if w * h <= 4:
                    eyes.add((x, y))
    return out, eyes


# ---------------------------------------------------------------------------------------------------- variant parts
def paint_parts(img, mob, variant, sheet, rnd):
    p = img.load()
    regions = PV.regions(mob)[variant]
    coat = soft_ramp(colours(sheet, COAT[mob]))
    pink, tan = colours(sheet, PINK), colours(sheet, TAN)
    flowers = {"a": (pink, tan), "b": (tan, pink)}     # (petal colours, centre colours)
    n = len(coat)
    for name, (x0, y0, w, h) in regions.items():
        role, _, key = name.partition(".")
        if role in ("fluff", "ball"):
            strands = [rnd.choice((-0.5, 0, 0.5)) + (0.6 if c % 2 == 0 else -0.6) for c in range(w)]
            short = {c for c in range(w) if h >= 4 and rnd.random() < 0.4}
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    v, u = (y - y0 + 0.5) / h, (x - x0 + 0.5) / w
                    if role == "ball":
                        i = n - 2 + 0.8 * (0.5 - v) - 1.2 * abs(u - 0.5)
                        c = coat[max(0, min(n - 1, round(i)))]
                    else:
                        tip = y == y0 + h - 1 or (y == y0 + h - 2 and (x - x0) in short)
                        i = n / 2 + 1.6 * (0.5 - v) + strands[x - x0]
                        c = coat[max(0, min(n - 1, round(i)))]
                        if tip and h > 1:                       # frosted lighter hair tips
                            hh, ss, vv = hsv(c)
                            c = rgb(hh, ss * 0.7, min(0.95, vv * 1.12))
                    p[x, y] = c + (255,)
        elif role in ("petal", "petal_edge", "centre", "centre_side"):
            pet, cen = flowers[key.split("_")[0]]
            light, deep = pet[-1], pet[0]
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    ring = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
                    corner = x in (x0, x0 + w - 1) and y in (y0, y0 + h - 1)
                    if role == "petal":
                        # rounded petals with colour, not transparency (a cut-out corner shows a gap in the
                        # petal's thickness from the side): the corners a step deeper than the petal's throat
                        c = lerp(deep, (0, 0, 0), 0.15) if corner and w >= 3 else light if ring else deep
                    elif role == "petal_edge":
                        c = deep
                    elif role == "centre":
                        c = cen[-1] if (x - x0) + (y - y0) < max(w, h) / 2 else cen[0]
                    else:
                        c = cen[0]
                    p[x, y] = c + (255,)


def recolour(img, variant, keep):
    p = img.load()
    for y in range(img.height):
        for x in range(img.width):
            c = p[x, y]
            if not c[3] or (x, y) in keep:
                continue
            h, s, v = hsv(c)
            if variant == "tropical":
                s, v = min(0.92, s * 1.18 + 0.03), min(0.97, v * 1.03)
                p[x, y] = rgb(h, s, v) + (c[3],)
            else:
                # cooler without sliding warm hues through yellow: mix towards a pale blue-grey of the same value
                p[x, y] = lerp(c[:3], rgb(205, 0.22, v), 0.3) + (c[3],)


def save(img, mob, suffix):
    out = RES / f"textures/entity/{mob}{suffix}.png"
    if out.exists() and not art_guard.is_ours(out):
        man = json.loads((BACKUP / "manifest.json").read_text(encoding="utf-8"))["textures"]
        if man.get(f"textures/entity/{mob}{suffix}.png", {}).get("sha1") == art_guard.sha1(out):
            art_guard.record(out)                       # still the copied placeholder sheet: ours to replace
    art_guard.save(img, out)
    return out


def build(mob, resplit=False):
    """Variants from the live <mob>.png (the upgraded split, see upgrade_placeholder_mobs.py); resplit=True first
    rewrites <mob>.png as the plain split of the sheet."""
    sheet = Image.open(SHEET).convert("RGBA")
    split_img, eyes = split(mob, sheet)
    written = []
    if resplit:
        written.append(save(split_img, mob, ""))
    base = Image.open(RES / f"textures/entity/{mob}.png").convert("RGBA")
    for variant in ("tropical", "cold"):
        img = base.copy()
        paint_parts(img, mob, variant, sheet, random.Random(f"{mob}:{variant}"))
        recolour(img, variant, eyes)
        written.append(save(img, mob, f"_{variant}"))
    return written


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for m in args or MOBS:
        for w in build(m, "--split" in sys.argv):
            print("wrote", w.relative_to(ROOT))
