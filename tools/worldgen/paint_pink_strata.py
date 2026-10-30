"""R03-R07 of art_requests/stone_upgrade_plan.md: the crimson canyon / willow grove pinks and the cracked sandstone, re-textured
from real stones while keeping every texture's layout and its bright pink (minecraft-texture-crafter skill).
Usage: python -I tools/worldgen/paint_pink_strata.py <project> [--apply]

Mask-preserving: each existing texture is split into colour families by HSV - pink (H 330-15), olive (H 18-75, the heated
part of ember stone), everything else (teal / grey / dark slate layers belong to other stones and stay as they are).
The pink (and olive) pixels get the new structure, painted over the whole 16 x 16 (so it still tiles) and shown only
inside the family's mask, in a 7-step ladder built around THAT texture's own average pink: the pink stays the original
bright pink (user), only the structure becomes real.

  R03 cracked_sandstone (crack 0-3)      mud-cracked playa mudstone: polygons, smaller and more of them per crack level
  R04 canyon tops, capped strata tops     pink rhyolitic tuff: almost smooth, fine pits and grains
  R05 crimson_strata, capped strata side  coral pink sandstone: soft wavy laminae 2-3 px, no dark partings
  R06 ember_stone (heat 0-4)              pink flow-banded rhyolite: diagonal flow bands, small vesicles and crystals
  R07 willow grove tops                   pink kaolin clay: soft 2-4 px clods, one step apart
Building sets (vanilla_building_patterns.md): crimson_strata_bricks = tuff_bricks skeleton (2 courses, 16 px bricks
staggered 8, bevelled joints) with sandstone faces; ember_stone_bricks = cinnabar_bricks skeleton (2 courses, 16 px
bricks staggered 8, 2-row joints) with rhyolite faces. Chiseled bricks carry the canyon's creatures: Dartback (the
commonest: wide spined body, two small eyes) on crimson strata, Fusefly (second: capsule head, fuse tuft, two big eyes)
on ember stone.
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
import art_guard
from paint_void_stone import Canvas, mottle, ALL, BLOBS, lum

C1, C2, C3, C4, C5, C6, C7 = range(7)
FRAC = [+0.44, +0.29, +0.14, 0.0, -0.14, -0.32, -0.56]     # step luminance = base + FRAC * span
DH = [+10, +7, +3, 0, -5, -12, -20]                        # lights towards salmon / orange, darks towards magenta
SF = [0.64, 0.80, 0.94, 1.0, 1.0, 0.95, 0.85]


def family(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    h *= 360
    if s >= 0.22 and v >= 0.55 and (h >= 330 or h <= 15):
        return "pink"
    if s >= 0.25 and 18 <= h <= 75:
        return "olive"
    return None


def ramp(rgbs, span):
    r, g, b = (sum(c[i] for c in rgbs) / len(rgbs) / 255 for i in range(3))
    h, s, _ = colorsys.rgb_to_hsv(r, g, b)
    l0 = 0.299 * r + 0.587 * g + 0.114 * b
    out = []
    def toward(goal):                        # +1 / -1: the shorter way round the hue circle from this stone's hue to goal
        d = (goal - h * 360) % 360
        return 1 if d < 180 else -1
    for dh, sf, fr in zip(DH, SF, FRAC):
        dh = abs(dh) * (toward(50) if dh > 0 else toward(240))   # lights towards yellow, darks towards blue (skill 2.2)
        target = l0 + fr * span
        lo, hi = 0.0, 1.0
        for _ in range(40):
            v = (lo + hi) / 2
            rgb = tuple(round(c * 255) for c in colorsys.hsv_to_rgb((h * 360 + dh) % 360 / 360, min(0.9, s * sf), v))
            lo, hi = (v, hi) if lum(rgb) < target else (lo, v)
        out.append(rgb)
    return out


# ------------------------------------------------------------------------------------------------ structures (index grids)
def tuff(rnd):
    c = Canvas()
    mottle(c, rnd, ALL, {C3: 5, C5: 4}, base_max=0.42)
    for _ in range(7):                       # fine pits: a shadow pixel, a lit pixel below-right
        x, y = rnd.randrange(16), rnd.randrange(16)
        c.set(x, y, C6 if rnd.random() < 0.3 else C5)
        c.set(x + 1, y + 1, C3)
    for _ in range(2):                       # a few small pale lapilli
        x, y = rnd.randrange(16), rnd.randrange(16)
        c.set(x, y, C2)
        c.set(x + 1, y, C3)
        c.set(x, y + 1, C3)
    return c


def sandstone(rnd):
    c = Canvas()
    lam, k = [], 0
    while len(lam) < 16:
        lam += [[C3, C4, C5, C4][k % 4]] * rnd.choice((2, 2, 3))
        k += 1
    lam = lam[:16]
    ph = rnd.uniform(0, 16)                  # laminae undulate (one wave per tile, +-1.6 px) so no long straight edges
    wave = [round(1.6 * math.sin(2 * math.pi * (x + ph) / 16) + 0.6 * math.sin(2 * math.pi * (x + ph) / 8)) for x in range(16)]
    for y in range(16):
        for x in range(16):
            c.set(x, y, lam[(y + wave[x]) % 16])
    for _ in range(12):                      # grain clusters across the laminae
        x, y = rnd.randrange(16), rnd.randrange(16)
        col = rnd.choice((C3, C5, C2))
        for dx, dy in rnd.choice(BLOBS[:5]):
            c.set(x + dx, y + dy, col)
    for _ in range(2):                       # faint broken parting (#5 only, 3-4 px)
        x, y = rnd.randrange(16), rnd.randrange(16)
        for q in range(rnd.choice((3, 4))):
            c.set(x + q, y - wave[(x + q) % 16], C5)
    return c


def rhyolite(rnd):
    c = Canvas()
    wob = [0, 1, 1, 0, -1, -1, 0, 0]
    shift = rnd.randrange(16)
    for y in range(16):
        for x in range(16):
            c.set(x, y, [C4, C3, C4, C5][((x + 2 * y + shift + wob[(x // 2) % 8]) % 16) // 4])
    for _ in range(5):
        x, y = rnd.randrange(16), rnd.randrange(16)
        for dx, dy in rnd.choice(BLOBS[:5]):
            c.set(x + dx, y + dy, rnd.choice((C3, C5)))
    for _ in range(3):                       # small vesicles
        x, y = rnd.randrange(16), rnd.randrange(16)
        c.set(x, y, C6)
        c.set(x + 1, y, C5)
        c.set(x + 1, y + 1, C3)
    for _ in range(2):                       # feldspar crystals
        x, y = rnd.randrange(16), rnd.randrange(16)
        c.set(x, y, C2)
        c.set(x + 1, y, C2)
        c.set(x + 2, y, C3)
    return c


def clay(rnd):
    c = Canvas()
    mottle(c, rnd, ALL, {C3: 4, C5: 4, C2: 1}, base_max=0.4)
    for _ in range(3):                       # soft clods: lit top-left, one step darker bottom-right
        x, y = rnd.randrange(16), rnd.randrange(16)
        for dx, dy, col in ((0, 0, C3), (1, 0, C3), (0, 1, C3), (1, 1, C4), (2, 1, C5), (1, 2, C5), (2, 2, C5)):
            c.set(x + dx, y + dy, col)
    return c


def mudcrack(rnd, level):
    """Torus Voronoi polygons; crack level 0-3 -> more, smaller plates; curled-up lit rims, #6 / #7 cracks."""
    rows, per = [((4, 12), 2), ((4, 12), 3), ((3, 8.5, 13.5), 3), ((2, 6, 10, 14), 4)][level]
    c = Canvas()
    pts = [((k * 16 / per + (8 / per if r % 2 else 0) + rnd.uniform(-1.6, 1.6)) % 16, cy + rnd.uniform(-1.2, 1.2))
           for r, cy in enumerate(rows) for k in range(per)]
    wob = {(bx, by): rnd.uniform(-0.6, 0.6) for bx in range(8) for by in range(8)}

    def owner(x, y):
        best, who = 1e9, 0
        for i, (sx, sy) in enumerate(pts):
            dx = min(abs(x + 0.5 - sx), 16 - abs(x + 0.5 - sx))
            dy = min(abs(y + 0.5 - sy), 16 - abs(y + 0.5 - sy))
            d = math.hypot(dx, dy) + wob[(x // 2, y // 2)] * (1 if i % 2 else -1)
            if d < best:
                best, who = d, i
        return who

    own = {p: owner(*p) for p in ALL}
    shallow = {(i, j) for i in range(len(pts)) for j in range(i + 1, len(pts)) if rnd.random() < 0.55 - 0.1 * level}
    crack = {}
    for (x, y), o in own.items():
        for dx, dy in ((1, 0), (0, 1)):
            q = ((x + dx) % 16, (y + dy) % 16)
            if own[q] != o:
                crack[(x, y)] = C6 if tuple(sorted((o, own[q]))) in shallow else C7
    body = [p for p in ALL if p not in crack]
    mottle(c, rnd, body, {C3: 5, C5: 4}, base_max=0.4)
    for p, col in crack.items():
        c.set(*p, col)
    for x, y in body:
        o = own[(x, y)]
        if own[(x, (y + 1) % 16)] != o or own[((x + 1) % 16, y)] != o or crack.get((x, (y + 1) % 16)) == C7:
            c.set(x, y, C5 if c.get(x, y) != C7 else C7)
        elif own[(x, (y - 1) % 16)] != o or own[((x - 1) % 16, y)] != o:
            c.set(x, y, C2 if (x + y) % 3 else C3)
    return c


# ------------------------------------------------------------------------------------------------ bricks + chiseled
def ashlar(rnd, face, bevel):
    """2 courses of 16 px bricks staggered 8 (tuff_bricks with bevel=True, cinnabar_bricks with bevel=False)."""
    c = face(rnd)
    for course, off in ((0, 0), (1, 8)):
        y0 = course * 8
        for x in range(16):
            c.set(x, y0, C2 if x % 5 else C3)                                # lit top edge
            c.set(x, y0 + 6, C6 if bevel else c.get(x, y0 + 6))              # bevel shadow
            c.set(x, y0 + 7, C7 if bevel else C6)
        if not bevel:
            for x in range(16):
                c.set(x, y0 + 6, C6 if x % 4 else C5)
                c.set(x, y0 + 7, C7)
        jx = (off + 15) % 16
        for y in range(y0, y0 + 8):
            c.set(jx, y, C7)
            c.set(jx - 1, y, C6 if y < y0 + 6 else c.get(jx - 1, y))
            c.set(jx + 1, y, C3 if y0 < y < y0 + 6 else c.get(jx + 1, y))   # lit left edge of the next brick
    return c


DARTBACK = [  # 12 x 8, mirror symmetric: spines on the back, wide body, two small eyes
    "#.#..##..#.#",
    "#.#.#..#.#.#",
    "############",
    "############",
    "##EE####EE##",
    "############",
    ".##########.",
    "..########..",
]
FUSEFLY = [   # capsule head, fuse tuft, two big eyes
    ".....##.....",
    "....#..#....",
    "...######...",
    "..########..",
    "..#EE##EE#..",
    "..#EE##EE#..",
    "..########..",
    "...######...",
]


def chiseled(rnd, face, head):
    c = face(rnd)
    for x in range(1, 15):                   # bands: lit band + groove at the top, groove + lit band at the bottom
        c.set(x, 1, C3 if x % 4 == 0 else C2)
        c.set(x, 2, C7 if 2 <= x <= 13 else C6)
        c.set(x, 13, C6 if x in (1, 14) else C7)
        c.set(x, 14, C3)
    cells = {(2 + i, 4 + j): ch for j, row in enumerate(head) for i, ch in enumerate(row) if ch != "."}
    relief = lambda x, y: cells.get((x, y)) == "#"
    for (x, y), ch in cells.items():
        if ch == "E":
            col = C7
        elif y == 4:
            col = C1
        elif not relief(x, y - 1) and not relief(x - 1, y):
            col = C2
        elif not relief(x, y + 1) or not relief(x + 1, y):
            col = C5
        else:
            col = C3
        c.set(x, y, col)
    for (x, y), ch in cells.items():         # #6 buffer above every carved eye
        if ch == "#" and cells.get((x, y + 1)) == "E":
            c.set(x, y, C6)
    for (x, y) in list(cells):               # cast shadow on the panel
        for dx, dy in ((1, 0), (0, 1)):
            q = (x + dx, y + dy)
            if q not in cells and 3 <= q[1] <= 12 and 1 <= q[0] <= 14:
                c.set(*q, C6)
    for x in range(16):
        c.set(x, 0, C2)
        c.set(x, 15, C6)
    for y in range(16):
        c.set(0, y, C2)
        c.set(15, y, C6)
    c.set(0, 0, C1)
    c.set(15, 15, C7)
    c.set(15, 0, C4)
    c.set(0, 15, C4)
    return c


# ------------------------------------------------------------------------------------------------ jobs
def jobs():
    out = []   # (texture, structure fn, families to repaint, span) ; families None = the whole texture
    for p in sorted((T / "cracked_sandstone").glob("*.png")):
        out.append((p, lambda r, lv=int(p.stem[-1]): mudcrack(r, lv), None, 0.24))
    for p in sorted((T / "sift_ground").glob("canyon_top_*.png")):
        out.append((p, tuff, ("pink",), 0.20))
    for p in sorted((T / "sift_ground").glob("grove_top*.png")):
        out.append((p, clay, ("pink",), 0.18))
    for p in sorted((T / "capped_crimson_strata").glob("*.png")):
        out.append((p, tuff if p.stem.endswith("_top") else sandstone, ("pink",), 0.20))
    for p in sorted((T / "crimson_strata").glob("*.png")):
        out.append((p, sandstone, ("pink",), 0.20))
    for p in sorted((T / "ember_stone").glob("*.png")):
        out.append((p, rhyolite, ("pink", "olive"), 0.20))
    out.append((T / "crimson_strata_bricks/crimson_strata_bricks.png", lambda r: ashlar(r, sandstone, True), None, 0.22))
    out.append((T / "crimson_strata_bricks/chiseled_crimson_strata_bricks.png", lambda r: chiseled(r, sandstone, DARTBACK), None, 0.24))
    out.append((T / "ember_stone_bricks/ember_stone_bricks.png", lambda r: ashlar(r, rhyolite, False), None, 0.22))
    out.append((T / "ember_stone_bricks/chiseled_ember_stone_bricks.png", lambda r: chiseled(r, rhyolite, FUSEFLY), None, 0.24))
    return out


def repaint(path, fn, fams, span, classify=None, macro=False, base=None):
    """macro=True keeps the old texture's large-scale light / dark (bands, darker corners): every pixel's ladder index is
    shifted by its 5 x 5 neighbourhood's luminance offset from the family average, in ladder steps."""
    classify = classify or family
    old = Image.open(path).convert("RGBA")
    w, h = old.size
    px = old.load()
    new = old.copy()
    npx = new.load()
    groups = {}
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            f = "all" if fams is None else classify(px[x, y][:3])
            if f is not None and (fams is None or f in fams):
                groups.setdefault(f, []).append((x, y))
    if fams is None and "all" in groups:                    # full repaint: brick textures keep their pink from the
        cand = [px[x, y][:3] for x, y in groups["all"] if classify(px[x, y][:3]) is not None]  # the stone's own colour, if any
        base_rgbs = {"all": cand or [px[x, y][:3] for x, y in groups["all"]]}
    else:
        base_rgbs = {f: [px[x, y][:3] for x, y in pts] for f, pts in groups.items()}
    for f, pts in groups.items():
        pal = ramp(base or base_rgbs[f], span)                  # base: calibrate to another texture's colour
        shift = {}
        if macro:
            fam = set(pts)
            avg = sum(lum(px[x, y][:3]) for x, y in pts) / len(pts)
            for x, y in pts:
                near = [lum(px[(x + dx) % w, (y // 16) * 16 + (y + dy) % 16][:3]) for dx in range(-2, 3) for dy in range(-2, 3)
                        if ((x + dx) % w, (y // 16) * 16 + (y + dy) % 16) in fam]
                shift[(x, y)] = max(-1, min(1, round((sum(near) / len(near) - avg) / (0.15 * span))))
        for frame in range(h // 16):                        # animated textures: every frame gets its own seed
            grid = fn(random.Random(f"{path.stem}:{f}:{frame}"))
            for x, y in pts:
                if y // 16 == frame:
                    npx[x, y] = pal[max(0, min(6, grid.get(x, y % 16) - shift.get((x, y), 0)))] + (px[x, y][3],)
    return new, {f: len(p) for f, p in groups.items()}


def preview(results):
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 11)
    S, per = 56, 14
    n = len(results)
    rows = (n + per - 1) // per
    sheet = Image.new("RGB", (per * (S + 6) + 12, rows * (2 * S + 30) + 8), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    for i, (path, new) in enumerate(results):
        x, y = 6 + (i % per) * (S + 6), 4 + (i // per) * (2 * S + 30)
        sheet.paste(Image.open(path).convert("RGB").crop((0, 0, 16, 16)).resize((S, S), Image.NEAREST), (x, y))
        sheet.paste(new.convert("RGB").crop((0, 0, 16, 16)).resize((S, S), Image.NEAREST), (x, y + S + 2))
        d.text((x, y + 2 * S + 4), path.stem.replace("crimson_strata", "cs").replace("ember_stone", "es")
               .replace("cracked_sandstone", "crk").replace("capped_", "cap_")[:10], fill=(200, 205, 215), font=f)
    out = P / "build/previews/pink_strata_paint.png"
    sheet.save(out)
    tiles = Image.new("RGB", (per * 54 + 12, rows * 60 + 8), (30, 30, 36))      # 3 x 3 of each new texture at 1x
    for i, (path, new) in enumerate(results):
        t = Image.new("RGB", (48, 48))
        for a in range(3):
            for b in range(3):
                t.paste(new.convert("RGB").crop((0, 0, 16, 16)), (a * 16, b * 16))
        tiles.paste(t, (6 + (i % per) * 54, 4 + (i // per) * 60))
    tiles.resize((tiles.width * 2, tiles.height * 2), Image.NEAREST).save(P / "build/previews/pink_strata_tiles.png")
    return out


def main():
    results = []
    tmp = P / "build/previews/pink_strata_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    for path, fn, fams, span in jobs():
        new, counts = repaint(path, fn, fams, span)
        results.append((path, new))
        new.save(tmp / path.name)
    print("preview:", preview(results).relative_to(P), "-", len(results), "textures")
    if not APPLY:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_pink_strata")
    written = []
    for path, new in results:
        (bk / path.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, bk / path.relative_to(P))
        if not art_guard.is_ours(path) and "--force" in sys.argv:
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
