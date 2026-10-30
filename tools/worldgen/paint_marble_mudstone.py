"""The last stones of art_requests/stone_upgrade_plan.md (minecraft-texture-crafter skill).
Usage: python -I tools/worldgen/paint_marble_mudstone.py <project> [--apply] [--only=a,b]

  ash_marble (veining 0-3)          Carrara marble: warm grey-white grain, veins two steps darker in a cool grey (never
                                    black-brown); the four levels share veining0's palette, only the vein count grows.
  crimson_vein_stone (spread 0-4)   Rosa Portogallo marble: keeps the grey-violet -> rose layout of every spread level;
                                    both colours get one palette shared by all levels (no step between blocks), the rose
                                    the canyon's hue a little less saturated, veins only two steps lighter than the ground.
  banded_mudstone (banding 0-3)     Chinle banded mudstone: wide flat bands with clear edges instead of diagonal streaks;
                                    violet-brown ground, cream bands (a touch warmer) - level = number of cream bands.
  bleached_sandstone (bleach 0-4)   Coconino sandstone: cross-bedded laminae; one ladder that gets paler and less
                                    saturated per level, the lightest step capped at V 0.92 (no near-white).
  void_capped_crimson_01            basalt plateau: top = void_stone's basalt (same palette, the ground below), bottom =
                                    iron-stained basalt in a brick red-brown, side = both, keeping its layout.
Bricks (vanilla_building_patterns.md): marbles on quartz_bricks (top course one 16 px block, bottom course 8 px bricks
staggered 4), mudstone on mud_bricks (light joints), white sandstone on end_stone_bricks. Chiseled heads: ash marble =
Echo Golem, crimson vein stone = Singer (Lullaby Hills), banded mudstone = Nester (crimson canyon), bleached sandstone =
Hurler (amber dunes). Chiseled ends from the new bricks.
"""
import colorsys, datetime, json, math, random, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
A = P / "src/main/resources/assets/pysift"
T = A / "textures/block"
sys.path.insert(0, str(P / "tools"))
sys.path.insert(0, str(P / "tools/worldgen"))
sys.path.insert(0, str(P / "tools/texture_pipeline"))
import art_guard
from paint_void_stone import Canvas, mottle, ALL, BLOBS, basalt, palette as void_palette
from paint_pink_strata import repaint, ramp, chiseled
from paint_teal_strata import small_bricks
from chiseled_tops import smooth_top

C1, C2, C3, C4, C5, C6, C7 = range(7)
ORIG = P / ".texture_backups/20261030-165719_paint_marble_mudstone"     # textures before this script's first apply


def px(path):
    return [c[:3] for c in Image.open(path).convert("RGBA").get_flattened_data() if c[3]]


def lum(c): return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255


def adjust(rgbs, s_mul=1.0, l_add=0.0, v_cap=1.0):
    h, s, v = colorsys.rgb_to_hsv(*(sum(c[i] for c in rgbs) / len(rgbs) / 255 for i in range(3)))
    v = min(v_cap, v + l_add)
    return [tuple(round(x * 255) for x in colorsys.hsv_to_rgb(h, s * s_mul, v))]


def cap(pal, v_cap=0.92):
    out = []
    for c in pal:
        h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
        out.append(tuple(round(x * 255) for x in colorsys.hsv_to_rgb(h, s, min(v, v_cap))))
    return out


def paint(grid, pal):
    img = Image.new("RGB", (16, 16))
    img.putdata([pal[grid.get(x, y)] for y in range(16) for x in range(16)])
    return img


def vein(c, rnd, y0, slope, core, halo, amp, phase, halo_p=0.6, period=8):
    for x in range(16):
        y = y0 + slope * x + round(amp * math.sin(2 * math.pi * (x + phase) / period))
        c.set(x, y, core)
        if rnd.random() < halo_p:
            c.set(x, y + 1, halo)


# ------------------------------------------------------------------------------------------------ structures
def carrara(rnd, level):
    c = Canvas(C3)
    mottle(c, rnd, ALL, {C2: 4, C4: 4, C1: 1}, base_max=0.42, base=C3)
    for k in range(level + 1):                 # veins: #6 core with a #5 halo, two steps under the ground
        if k == 0:                             # one diagonal vein, the others meander across (no diamond lattice)
            vein(c, rnd, rnd.randrange(16), rnd.choice((1, -1)), C6, C5, 1.0, rnd.uniform(0, 8))
        else:
            vein(c, rnd, rnd.randrange(16), 0, C6, C5, rnd.uniform(1.8, 2.6), rnd.uniform(0, 16), period=16)
    return c


def smooth_marble(rnd):
    """Smooth ash marble (smooth_basalt style, user: no frame): sawn flat - very soft #3 / #4 / #5 clouds and two ghost
    veins one step under the ground, nothing darker."""
    c = Canvas(C3)
    mottle(c, rnd, ALL, {C2: 3, C4: 4}, base_max=0.5, base=C3)
    for _ in range(2):
        vein(c, rnd, rnd.randrange(16), 0, C4, C4, rnd.uniform(1.6, 2.4), rnd.uniform(0, 16), halo_p=0.0, period=16)
    return c


def rosa(rnd):
    c = Canvas()
    mottle(c, rnd, ALL, {C3: 4, C5: 4}, base_max=0.4)
    vein(c, rnd, rnd.randrange(16), 1, C2, C3, 1.3, rnd.uniform(0, 8))
    vein(c, rnd, rnd.randrange(16), -1, C3, C3, 0.9, rnd.uniform(0, 8), 0.4)
    return c


def crossbed(rnd):
    c = Canvas()
    lam, k = [], 0
    while len(lam) < 16:
        lam += [[C3, C4, C5, C4, C2, C4][k % 6]] * rnd.choice((1, 2, 2, 3))
        k += 1
    lam = lam[:16]
    tilt = [0, 1, 2, 2, 1, 0, -1, -1] if rnd.random() < 0.5 else [0, 0, 1, 2, 2, 1, 1, 0]
    for y in range(16):
        for x in range(16):
            c.set(x, y, lam[(y + tilt[(x // 2) % 8]) % 16])
    for _ in range(6):
        x, y = rnd.randrange(16), rnd.randrange(16)
        for dx, dy in rnd.choice(BLOBS[:5]):
            c.set(x + dx, y + dy, rnd.choice((C3, C5)))
    return c


def mud_grain(rnd):
    c = Canvas()
    mottle(c, rnd, ALL, {C3: 4, C5: 4}, base_max=0.4)
    return c


def banded(rnd, level, brown, cream):
    """Wide bands at 45 degrees (user: like the original), wobbling +-1; cream bands get a #2 top edge, the brown under a cream
    band a #6 shadow row. Returns an image (two palettes)."""
    thick = [3, 2, 4, 3, 2, 2] if level else [3, 3, 3, 3, 4]
    order = ["b"] * len(thick)
    for k in range(min(level, 3)):
        order[[1, 3, 5][k] % len(order)] = "c"
    rows = []
    for t, kind in zip(thick, order):
        rows += [kind] * t
    rows = (rows * 2)[:16]
    ph = rnd.uniform(0, 16)
    wave = [round(1.1 * math.sin(2 * math.pi * (t + ph) / 16)) for t in range(16)]
    g = mud_grain(rnd)
    img = Image.new("RGB", (16, 16))
    for y in range(16):
        for x in range(16):
            # bands at 45 degrees (lower left -> upper right, like the original): constant along x + y, period 16 so
            # it still tiles; a gentle wobble along the band
            yy = (y + x + wave[(x - y) % 16]) % 16
            kind, above, below = rows[yy], rows[(yy - 1) % 16], rows[(yy + 1) % 16]
            idx = g.get(x, y)
            if kind == "c" and above == "b":
                idx = C2
            if kind == "b" and above == "c":
                idx = C6
            elif kind == "b" and level == 0 and yy in (5, 11) and x % 7 < 4:
                idx = C6                      # faint darker partings in the plain level
            img.putpixel((x, y), (cream if kind == "c" else brown)[idx])
    return img


# ------------------------------------------------------------------------------------------------ bricks
def quartz_bricks(rnd, face):
    c = face(rnd)
    for course, joints in ((0, (15,)), (1, (3, 11))):
        y0 = course * 8
        for x in range(16):
            c.set(x, y0, C2 if x not in joints else C3)
            c.set(x, y0 + 7, C6)
        for jx in joints:
            for y in range(y0, y0 + 7):
                c.set(jx, y, C6)
                c.set(jx + 1, y, C2 if y > y0 else C2)
    return c


def mud_bricks(rnd, face):
    """mud_bricks: 2 courses 7 + 1, 8 px bricks staggered 4, joints LIGHTER than the bricks (#2), #5 shadow under the brick."""
    c = face(rnd)
    for course, off in ((0, 0), (1, 4)):
        y0 = course * 8
        for x in range(16):
            c.set(x, y0 + 6, C5)
            c.set(x, y0 + 7, C2)
            c.set(x, y0, C3 if c.get(x, y0) == C4 else c.get(x, y0))
        for b in range(2):
            jx = off + 8 * b + 7
            for y in range(y0, y0 + 7):
                c.set(jx, y, C2)
                c.set(jx - 1, y, C5)
    return c


ECHO_GOLEM = ["..########..", ".#.######.#.", ".#.######.#.", "..########..", "...#E##E#...", "...######...",
              "...##EE##...", "....####...."]
SINGER = ["#.#......#.#", ".#.#....#.#.", "..#.####.#..", "...######...", "...#E##E#...", "....####....",
          "....####....", "...######..."]
NESTER = ["...#....#...", "...#....#...", "...######...", "..########..", "..EEEEEEEE..", "..########..",
          "...######...", "....#..#...."]
HURLER = ["...######...", "..########..", ".##########.", ".##E####E##.", ".##########.", ".#EEEEEEEE#.",
          ".##########.", "..##....##.."]


def red(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in rgb))
    return "red" if s >= 0.3 and v >= 0.35 and (h * 360 >= 330 or h * 360 <= 25) else "ground"


# ------------------------------------------------------------------------------------------------ jobs
def build():
    out = {}                                   # path -> image
    # ash marble: veining0's palette for all four levels
    am = ramp(px(T / "ash_marble/ash_marble_veining0.png"), 0.28)
    for lv in range(4):
        out[T / f"ash_marble/ash_marble_veining{lv}.png"] = paint(carrara(random.Random(f"am{lv}"), lv), am)
    face_am = lambda r: carrara(r, 1)
    out[T / "ash_marble/smooth_ash_marble.png"] = paint(smooth_marble(random.Random("ams")), am)
    out[T / "ash_marble_bricks/ash_marble_bricks.png"] = paint(quartz_bricks(random.Random("amb"), face_am), am)
    out[T / "ash_marble_bricks/chiseled_ash_marble_bricks.png"] = paint(chiseled(random.Random("amc"), face_am, ECHO_GOLEM), am)
    # crimson vein stone: shared palettes per colour over all spread levels, mask-preserving
    cv = sorted((T / "crimson_vein_stone").glob("*.png"))
    pool = {"red": [], "ground": []}
    for p in cv:
        for c in px(ORIG / p.relative_to(P) if (ORIG / p.relative_to(P)).exists() else p):
            pool[red(c)].append(c)
    base = {"red": adjust(pool["red"], s_mul=0.85), "ground": pool["ground"]}
    for p in cv:
        img, _ = repaint(p, rosa, ("red", "ground"), 0.18, classify=red, base=base)
        out[p] = img.convert("RGB")
    gp = ramp(base["ground"], 0.20)
    out[T / "crimson_vein_stone_bricks/crimson_vein_stone_bricks.png"] = paint(quartz_bricks(random.Random("cvb"), rosa), gp)
    out[T / "crimson_vein_stone_bricks/chiseled_crimson_vein_stone_bricks.png"] = paint(chiseled(random.Random("cvc"), rosa, SINGER), gp)
    # banded mudstone
    b0 = px(T / "banded_mudstone/banded_mudstone_banding0.png")
    cream_src = [c for c in px(T / "banded_mudstone/banded_mudstone_banding2.png") if lum(c) > 0.68]
    brown, cream = ramp(b0, 0.18), ramp(adjust(cream_src, s_mul=1.15), 0.12)
    for lv in range(4):
        out[T / f"banded_mudstone/banded_mudstone_banding{lv}.png"] = banded(random.Random(f"bm{lv}"), lv, brown, cream)
    out[T / "banded_mudstone_bricks/banded_mudstone_bricks.png"] = paint(mud_bricks(random.Random("bmb"), mud_grain), brown)
    out[T / "banded_mudstone_bricks/chiseled_banded_mudstone_bricks.png"] = paint(chiseled(random.Random("bmc"), mud_grain, NESTER), brown)
    # bleached sandstone: one ladder, paler and less saturated per level
    s0 = px(T / "bleached_sandstone/bleached_sandstone_bleach0.png")
    for lv in range(5):
        pal = cap(ramp(adjust(s0, s_mul=0.8 ** lv, l_add=0.035 * lv, v_cap=0.9), 0.16))
        out[T / f"bleached_sandstone/bleached_sandstone_bleach{lv}.png"] = paint(crossbed(random.Random(f"bs{lv}")), pal)
    sp = cap(ramp(s0, 0.18))
    out[T / "bleached_sandstone_bricks/bleached_sandstone_bricks.png"] = paint(small_bricks(random.Random("bsb"), crossbed), sp)
    out[T / "bleached_sandstone_bricks/chiseled_bleached_sandstone_bricks.png"] = paint(chiseled(random.Random("bsc"), crossbed, HURLER), sp)
    # void_capped_crimson_01 caps crimson_vein_stone (Lullaby Hills): its red and grey-violet are that stone's,
    # so the same rose-marble structure and the same shared palettes replace them directly (layout kept)
    vc = T / "void_capped_crimson_01"
    for p in sorted(vc.glob("*.png")):
        src = ORIG / p.relative_to(P) if (ORIG / p.relative_to(P)).exists() else p
        img, _ = repaint(src, rosa, ("red", "ground"), 0.18, classify=red, base=base)
        out[p] = img.convert("RGB")
    for base_id in ("crimson_vein_stone", "banded_mudstone", "bleached_sandstone"):   # ash marble: ends = its smooth form
        out[T / f"{base_id}_bricks" / f"chiseled_{base_id}_bricks_top.png"] = smooth_top(out[T / f"{base_id}_bricks" / f"{base_id}_bricks.png"],
                                                                                          f"chiseled_{base_id}_bricks")
    return out


def main():
    only = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), None)
    out = {p: img for p, img in build().items() if not only or any(o in p.stem for o in only)}
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 11)
    S, per = 60, 11
    items = list(out.items())
    rows = (len(items) + per - 1) // per
    sheet = Image.new("RGB", (per * (S + 6) + 12, rows * (2 * S + 30) + 8), (30, 30, 36))
    tiles = Image.new("RGB", (per * 54 + 12, rows * 60 + 8), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    for i, (path, new) in enumerate(items):
        x, y = 6 + (i % per) * (S + 6), 4 + (i // per) * (2 * S + 30)
        if path.exists():
            sheet.paste(Image.open(path).convert("RGB").crop((0, 0, 16, 16)).resize((S, S), Image.NEAREST), (x, y))
        sheet.paste(new.resize((S, S), Image.NEAREST), (x, y + S + 2))
        d.text((x, y + 2 * S + 4), path.stem.replace("chiseled_", "ch_").replace("crimson_vein_stone", "cvs")
               .replace("banded_mudstone", "bm").replace("bleached_sandstone", "bs").replace("void_capped_crimson_01", "vcc")[:11],
               fill=(200, 205, 215), font=f)
        t = Image.new("RGB", (48, 48))
        for a in range(3):
            for b in range(3):
                t.paste(new, (a * 16, b * 16))
        tiles.paste(t, (6 + (i % per) * 54, 4 + (i // per) * 60))
    sheet.save(P / "build/previews/marble_mudstone_paint.png")
    tiles.resize((tiles.width * 2, tiles.height * 2), Image.NEAREST).save(P / "build/previews/marble_mudstone_tiles.png")
    tmp = P / "build/previews/marble_mudstone_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    for path, new in items:
        new.save(tmp / path.name)
    print("preview: build/previews/marble_mudstone_paint.png -", len(items), "textures")
    if not APPLY:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_marble_mudstone")
    written = []
    for path, new in items:
        (bk / path.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            shutil.copy2(path, bk / path.relative_to(P))
        if path.exists() and not art_guard.is_ours(path) and "--force" in sys.argv:
            path.unlink()
        if art_guard.save(new, path):
            written.append(path.relative_to(A).as_posix())
    man = P / "tools/texture_pipeline/recolor_manifest.json"
    doc = json.loads(man.read_text(encoding="utf-8"))
    keep = [e for e in doc["entries"] if e["file"] not in written]
    if len(keep) != len(doc["entries"]):
        doc["entries"] = keep
        man.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("written:", len(written), "; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
