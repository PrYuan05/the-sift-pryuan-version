"""Hand-designed basalt textures for void_stone, the bedrock under every Sift biome (minecraft-texture-crafter skill).
Usage: python -I tools/worldgen/paint_void_stone.py <project> [--apply]

Without --apply only build/previews/void_stone_paint.png is written (current vs new, tilings).
With --apply the textures are backed up to .texture_backups/<stamp>_paint_void_stone/ and written through tools/art_guard.py;
files the recolor pipeline made are taken out of tools/texture_pipeline/recolor_manifest.json (they are hand-painted now).

Material brief (stone_upgrade_plan.md R19):
  1. Identity: void_stone tone dark, the world's deep bedrock (5-8 blocks under every biome), plus its bricks, chiseled bricks
     and pillar. Only tone dark stays; rusty / olive will be removed (see the plan's to-do list).
  2. Physical: basalt - dense, fine-grained, matte; soft narrow contrast, 2-4 px grain clusters, a few small gas vesicles,
     sparse short cooling joints, scattered pale plagioclase laths (porphyritic basalt).
  3. Real-world analogue: Icelandic / Giant's Causeway basalt; the pillar is a columnar-jointed basalt colonnade and its end
     the hexagonal cross-section of the columns.
  4. Vanilla anchors: deepslate / deepslate_bricks (4 px courses, 8 px bricks, staggered) / chiseled_deepslate (bevel frame),
     basalt_side / basalt_top (vertical column faces, polygon end).
Chiseled bricks carry a creature head (skill rule): void_stone has no biome of its own, so the head of the Stalker, the
creature of the deep caves (red zone caves, violet slate abyss): square head, two ear nubs, a carved visor with two eyes.

Palette: seven steps, grey basalt from the current void_stone_c (H221 S0.15 Lum 0.25); low-saturation material, so the
light steps lean to a warm grey and the dark steps to a cool blue-grey (skill 2.2). #1 only on peaks, never next to #7.
"""
import colorsys, datetime, json, math, random, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
A = P / "src/main/resources/assets/pysift"
T = A / "textures/block"
sys.path.insert(0, str(P / "tools"))
import art_guard

C1, C2, C3, C4, C5, C6, C7 = range(7)
# (hue, saturation, target luminance) per step
STEPS = [(40, 0.04, 0.405), (200, 0.07, 0.358), (212, 0.11, 0.312), (221, 0.15, 0.272), (227, 0.17, 0.234),
         (238, 0.21, 0.186), (248, 0.26, 0.136)]


def lum(rgb): return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255


def palette():
    out = []
    for h, s, target in STEPS:
        lo, hi = 0.0, 1.0
        for _ in range(40):
            v = (lo + hi) / 2
            rgb = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h / 360, s, v))
            lo, hi = (v, hi) if lum(rgb) < target else (lo, v)
        out.append(rgb)
    return out


class Canvas:
    def __init__(self, fill=C4):
        self.px = [[fill] * 16 for _ in range(16)]

    def set(self, x, y, c): self.px[y % 16][x % 16] = c
    def get(self, x, y): return self.px[y % 16][x % 16]

    def image(self, pal):
        img = Image.new("RGB", (16, 16))
        img.putdata([pal[self.px[y][x]] for y in range(16) for x in range(16)])
        return img


BLOBS = [((0, 0), (1, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)), ((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 0), (0, 1), (1, 1)),
         ((0, 0), (1, 0), (2, 0)), ((1, 0), (0, 1), (1, 1), (2, 1))]
ALL = [(x, y) for x in range(16) for y in range(16)]


def mottle(c, rnd, cells, colours, base_max=0.4, base=C4):
    """2-4 px grain clusters of the micro steps until the base colour covers at most base_max of the cells."""
    cells = set(cells)
    for p in cells:
        c.set(*p, base)
    keys, weights = zip(*colours.items())
    for _ in range(600):
        if sum(1 for p in cells if c.get(*p) == base) <= base_max * len(cells):
            break
        x, y = rnd.choice(sorted(cells))
        col = rnd.choices(keys, weights)[0]
        for dx, dy in rnd.choice(BLOBS):
            q = ((x + dx) % 16, (y + dy) % 16)
            if q in cells and c.get(*q) == base:
                c.set(*q, col)


def basalt(rnd):
    """Natural basalt: fine grain, four vesicles (dark top-left wall, lit bottom-right lip), two short stepped cooling
    joints with a #6 buffer, a few pale plagioclase laths. Everything wraps around the tile edges."""
    c = Canvas()
    mottle(c, rnd, ALL, {C3: 4, C5: 5, C6: 1}, base_max=0.36)
    for x, y in ((2, 2), (12, 5), (6, 10), (14, 13)):           # laths: 2 px #2 with a #3 tail
        c.set(x, y, C2)
        c.set(x + 1, y, C2)
        c.set(x + 2, y, C3)
    for x, y in ((9, 1), (3, 6), (11, 9), (1, 13)):            # vesicles
        c.set(x, y, C7)
        c.set(x + 1, y, C6)
        c.set(x, y + 1, C6)
        c.set(x + 1, y + 1, C3)
    for x, y, steps in ((6, 3, ((0, 1), (1, 1), (0, 1), (1, 1))), (13, 10, ((1, 1), (0, 1), (1, 1)))):   # cooling joints
        for dx, dy in steps:
            c.set(x, y, C7)
            c.set(x + 1, y, C6)
            c.set(x - 1, y, C5)
            x, y = x + dx, y + dy
        c.set(x, y, C6)
    return c


def bricks(rnd, offsets=(0, 4, 0, 4), cracked=None):
    """Basalt bricks: four 4 px courses of 8 px bricks, staggered by 4; mortar (bottom row and right column of every brick)
    is #7, every brick has a lit #2 top row, a #3 left column, #3/#4/#5 grain and a #6 buffer along its bottom and right."""
    c = Canvas()
    for course, off in enumerate(offsets):
        y0 = course * 4
        for b in range(2):
            x0 = off + b * 8
            cells = [(x0 + i, y0 + j) for i in range(7) for j in range(3)]
            mottle(c, rnd, [((x % 16), y) for x, y in cells], {C3: 4, C5: 4}, base_max=0.4)
            for i in range(7):
                c.set(x0 + i, y0, C3 if (i + course) % 4 == 3 else C2)        # lit top row
                c.set(x0 + i, y0 + 2, C5 if c.get(x0 + i, y0 + 2) != C3 else C4)
            c.set(x0, y0 + 1, C3)                                              # lit left column
            c.set(x0, y0 + 2, C4)
            c.set(x0 + 6, y0 + 1, C6)                                          # shadow buffer on the right
            c.set(x0 + 6, y0 + 2, C6)
            c.set(x0 + 6, y0, C4)
            c.set(x0 + 5, y0 + 2, C6)
            for j in range(4):                                                 # mortar column
                c.set(x0 + 7, y0 + j, C7)
            for i in range(8):                                                 # mortar row
                c.set(x0 + i, y0 + 3, C7)
    if cracked:                                                                # a weathered brick: a short stepped crack
        x, y = cracked
        for dx, dy in ((1, 0), (0, 1), (1, 0)):
            c.set(x, y, C6)
            x, y = x + dx, y + dy
        c.set(x, y, C6)
    return c


STALKER = [  # 12 x 8 head (x 2..13, y 4..11), mirror symmetric; # relief, E carved visor, O eye glinting in the visor
    ".#........#.",
    ".##......##.",
    "..########..",
    "..########..",
    "..#EOEEOE#..",
    "..########..",
    "...######...",
    ".##########.",
]


def chiseled(rnd):
    c = Canvas()
    mottle(c, rnd, [(x, y) for x in range(1, 15) for y in range(3, 13)], {C5: 6, C3: 2}, base_max=0.45)
    for x in range(1, 15):                 # thin bands: lit band + groove (top), groove + lit band (bottom)
        c.set(x, 1, C3 if x % 4 == 0 else C2)
        c.set(x, 2, C7 if 2 <= x <= 13 else C6)
        c.set(x, 13, C6 if x in (1, 14) else C7)
        c.set(x, 14, C3)
    head = {(2 + i, 4 + j): ch for j, row in enumerate(STALKER) for i, ch in enumerate(row) if ch != "."}
    relief = lambda x, y: head.get((x, y)) == "#"
    for (x, y), ch in head.items():
        if ch == "E":
            col = C7                                                # carved visor
        elif ch == "O":
            col = C2                                                # the eyes catch the light inside it
        elif y == 4:
            col = C1                                                # ear tips are the relief's peaks
        elif not relief(x, y - 1) and not relief(x - 1, y):
            col = C2                                                # lit top-left edge
        elif not relief(x, y + 1) or not relief(x + 1, y):
            col = C5                                                # shaded bottom-right edge
        else:
            col = C3
        c.set(x, y, col)
    for (x, y), ch in head.items():        # #6 buffer on the wall above the visor
        if ch == "#" and head.get((x, y + 1)) in ("E", "O"):
            c.set(x, y, C6)
    for (x, y), ch in list(head.items()):  # cast shadow on the panel: #6 under / right of the relief, #7 at the corner
        for dx, dy in ((1, 0), (0, 1)):
            q = (x + dx, y + dy)
            if q not in head and 3 <= q[1] <= 12 and 1 <= q[0] <= 14:
                c.set(*q, C6)
        q = (x + 1, y + 1)
        if q not in head and (x + 1, y) not in head and (x, y + 1) not in head and 3 <= q[1] <= 12 and q[0] <= 14:
            c.set(*q, C7)
    for x in range(16):                    # 1 px bevel frame
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


def column_side(rnd):
    """Columnar basalt seen from the side: three prism columns (5 / 5 / 6 px) - lit left facet, darker right facet, #7 joint
    with a #6 buffer - each broken by staggered short cross fractures, like a real colonnade."""
    c = Canvas()
    edges = [(0, 5), (5, 10), (10, 16)]
    for k, (a, b) in enumerate(edges):
        w = b - a
        for y in range(16):
            for i in range(w):
                col = C7 if i == w - 1 else C6 if i == w - 2 else C2 if i == 0 else C3 if i == 1 else C4 if i < w - 2 else C5
                c.set(a + i, y, col)
        y = 0
        while y < 16:                      # grain on the facets: 2-3 px vertical streaks
            n = rnd.choice((2, 3))
            if rnd.random() < 0.5:
                i, col = rnd.randrange(1, w - 2), rnd.choice((C3, C5))
                for q in range(n):
                    c.set(a + i, y + q, col)
            y += n
        y = (4 + 6 * k) % 16               # one cross fracture per column, staggered, not across the whole width
        for i in range(1, w - 1):
            c.set(a + i, y, C6)
            c.set(a + i, y + 1, C3)
        c.set(a + 1, y + 1, C2)
    return c


def column_end(rnd):
    """Columnar basalt from above: one hexagonal column in the middle, its neighbours at the corners (tiles seamlessly);
    every face slightly domed - #3 centre, #4 body, lit top-left rim, #6 bottom-right rim, #7 joints."""
    c = Canvas()
    seeds = [(8.0, 8.0), (0.0, 0.0)]

    def owner(x, y):
        best, who = 1e9, 0
        for i, (sx, sy) in enumerate(seeds):
            dx = min(abs(x + 0.5 - sx), 16 - abs(x + 0.5 - sx))
            dy = min(abs(y + 0.5 - sy), 16 - abs(y + 0.5 - sy))
            d = max(abs(dx) * 0.866 + abs(dy) * 0.5, abs(dy))   # hexagon metric (flat top)
            if d < best:
                best, who = d, i
        return who, best

    own = {p: owner(*p) for p in ALL}
    mottle(c, rnd, ALL, {C3: 3, C5: 4}, base_max=0.45)
    for (x, y), (o, d) in own.items():
        if d < 2.2:
            c.set(x, y, C3 if (x + y) % 3 else C2)
    for (x, y), (o, d) in own.items():
        dn, rt = own[(x, (y + 1) % 16)][0], own[((x + 1) % 16, y)][0]
        up, lf = own[(x, (y - 1) % 16)][0], own[((x - 1) % 16, y)][0]
        if dn != o or rt != o:
            c.set(x, y, C7)
        elif own[(x, (y + 2) % 16)][0] != o or own[((x + 2) % 16, y)][0] != o:
            c.set(x, y, C6)
        elif up != o or lf != o:
            c.set(x, y, C2)
    return c


def polished(rnd):
    """Polished basalt (vanilla polished_deepslate): ground flat, so only long soft horizontal streaks of the micro steps
    (3-4 px, never longer, so no grid lines when tiled) and a few dark polishing scratches with a lit pixel below."""
    c = Canvas()
    for y in range(16):
        x = rnd.randrange(16)
        covered = 0
        while covered < 16:
            n = rnd.randint(2, 4)
            col = rnd.choice((C4, C4, C3, C5))
            for k in range(n):
                c.set(x + covered + k, y, col)
            covered += n
    for x, y in ((2, 3), (10, 6), (5, 11), (13, 14)):
        for k in range(3):
            c.set(x + k, y, C6)
            c.set(x + k, y + 1, C3)
        c.set(x + 3, y, C5)
    return c


def tile_grid(rnd, broken=()):
    """Basalt flagstone tiles (user: the 4 px vanilla-style grid was too dense): 2 x 2 square tiles of 7 px with a 1 px
    #7 grout on their bottom / right; each tile has a lit top row and left column (#2, #3 every third pixel), #3 / #4 / #5
    grain, a #6 buffer along its bottom and right, and its own base tone so the four read as separate slabs. Broken tiles
    get a stepped crack and a chipped corner."""
    c = Canvas()
    for ty in range(2):
        for tx in range(2):
            x0, y0 = tx * 8, ty * 8
            base = (C4, C3, C5, C4)[ty * 2 + tx]
            other = {C3: 4, C5: 4} if base == C4 else {C4: 5, (C5 if base == C3 else C3): 2}
            mottle(c, rnd, [(x0 + i, y0 + j) for i in range(7) for j in range(7)], other, base_max=0.45, base=base)
            for k in range(7):
                c.set(x0 + k, y0, C3 if k % 3 == 2 else C2)
                c.set(x0, y0 + k, C3 if k % 3 == 2 else C2)
                c.set(x0 + k, y0 + 6, C6)
                c.set(x0 + 6, y0 + k, C6)
            c.set(x0 + 6, y0, C4)
            c.set(x0, y0 + 6, C4)
            for k in range(8):
                c.set(x0 + 7, y0 + k, C7)
                c.set(x0 + k, y0 + 7, C7)
            if (tx, ty) in broken:
                x, y = x0 + 2, y0 + 1
                for step in "drddrd":
                    c.set(x, y, C7)
                    c.set(x + 1, y, C6)
                    x, y = (x + 1, y) if step == "r" else (x, y + 1)
                c.set(x0 + 5, y0 + 5, C7)
                c.set(x0 + 4, y0 + 5, C6)
                c.set(x0 + 5, y0 + 4, C6)
    return c


def cracked_bricks(rnd):
    """Cracked basalt bricks (vanilla cracked_deepslate_bricks): the bricks of void_stone_b with two long stepped cracks
    running across several bricks (#7 core, #6 beside it) and two chipped corners."""
    c = bricks(rnd, (0, 4, 0, 4))
    for x, y, path in ((2, 0, "rdrddrdd"), (9, 6, "drrdrddr")):
        for step in path:
            c.set(x, y, C7)
            c.set(x + 1, y, C6) if c.get(x + 1, y) != C7 else None
            x, y = (x + 1, y) if step == "r" else (x, y + 1)
        c.set(x, y, C6)
    for x, y in ((5, 8), (14, 12)):       # chipped brick corners
        c.set(x, y, C6)
        c.set(x + 1, y, C6)
        c.set(x, y + 1, C6)
    return c


def smooth(rnd, rows=((0, 16),)):
    """Smooth basalt (vanilla smooth_stone / smooth_stone_slab_side): flat, very soft #3 / #4 mottling and a 1 px bevel
    frame around every panel (lit top / left, #6 bottom / right). rows = the panels' (top, bottom) rows."""
    c = Canvas()
    mottle(c, rnd, ALL, {C3: 5, C5: 2}, base_max=0.5)
    for y0, y1 in rows:
        for x in range(16):
            c.set(x, y0, C3)
            c.set(x, y1 - 1, C6)
        for y in range(y0, y1):
            c.set(0, y, C3)
            c.set(15, y, C6)
        c.set(0, y0, C2)
        c.set(15, y1 - 1, C7)
        c.set(15, y0, C4)
        c.set(0, y1 - 1, C4)
    return c


VS = "void_stone/void_stone_"
TEXTURES = {   # published path -> painter
    f"{VS}c": basalt,
    f"{VS}b": lambda r: bricks(r, (0, 4, 0, 4)),
    f"{VS}d": lambda r: bricks(r, (2, 6, 2, 6), cracked=(3, 5)),
    "void_stone_bricks/chiseled_void_stone_bricks": chiseled,
    "void_stone_pillar/void_stone_h": column_side,
    "void_stone_pillar/void_stone_pillar_top": column_end,
    # VoidStoneFamily (build_void_stone_family.py): vanilla deepslate's polished / tiles / cracked forms and smooth stone
    "void_stone/polished_void_stone": polished,
    "void_stone/void_stone_tiles": lambda r: tile_grid(r),
    "void_stone/cracked_void_stone_tiles": lambda r: tile_grid(r, broken=((1, 0), (0, 1))),
    "void_stone/cracked_void_stone_bricks": cracked_bricks,
    "void_stone/smooth_void_stone": smooth,
    "void_stone/smooth_void_stone_slab_side": lambda r: smooth(r, rows=((0, 8), (8, 16))),
}
PILLAR_MODEL = A / "models/block/void_stone_pillar/void_stone_pillar_1.json"


def preview(images, pal):
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
    S, names = 6, list(images)
    W = 40 + len(names) * (16 * S + 16)
    sheet = Image.new("RGB", (W, 2 * (16 * S + 30) + 64 * 3 + 100), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        x = 24 + i * (16 * S + 16)
        d.text((x, 4), n.split("/")[-1], fill=(230, 230, 230), font=f)
        old = T / f"{n}.png"
        if old.exists():
            sheet.paste(Image.open(old).convert("RGB").crop((0, 0, 16, 16)).resize((16 * S, 16 * S), Image.NEAREST), (x, 22))
        sheet.paste(images[n].resize((16 * S, 16 * S), Image.NEAREST), (x, 42 + 16 * S))
    d.text((2, 22 + 16 * S // 2), "舊", fill=(200, 200, 200), font=f)
    d.text((2, 42 + 16 * S + 16 * S // 2), "新", fill=(200, 200, 200), font=f)
    y0 = 2 * (16 * S + 30) + 14
    d.text((24, y0 - 4), "平鋪：玄武岩 4x4｜石磚（兩種隨機）4x4｜雕紋與石磚｜玄武岩柱（側面＋頂面）", fill=(230, 230, 230), font=f)
    z, rnd, x = 3, random.Random(1), 24
    t = Image.new("RGB", (64, 64))
    for bx in range(4):
        for by in range(4):
            t.paste(images[f"{VS}c"], (bx * 16, by * 16))
    sheet.paste(t.resize((64 * z, 64 * z), Image.NEAREST), (x, y0 + 16)); x += 64 * z + 16
    t = Image.new("RGB", (64, 64))
    for bx in range(4):
        for by in range(4):
            t.paste(images[rnd.choice((f"{VS}b", f"{VS}d"))], (bx * 16, by * 16))
    sheet.paste(t.resize((64 * z, 64 * z), Image.NEAREST), (x, y0 + 16)); x += 64 * z + 16
    t = Image.new("RGB", (48, 48))
    for bx in range(3):
        for by in range(3):
            t.paste(images["void_stone_bricks/chiseled_void_stone_bricks" if by == 1 and bx != 1 else f"{VS}b"], (bx * 16, by * 16))
    sheet.paste(t.resize((48 * z, 48 * z), Image.NEAREST), (x, y0 + 16)); x += 48 * z + 16
    t = Image.new("RGB", (48, 64))
    for bx in range(3):
        t.paste(images["void_stone_pillar/void_stone_pillar_top"], (bx * 16, 0))
        for by in range(1, 4):
            t.paste(images["void_stone_pillar/void_stone_h"], (bx * 16, by * 16))
    sheet.paste(t.resize((48 * z, 64 * z), Image.NEAREST), (x, y0 + 16))
    for k, rgb in enumerate(pal):
        d.rectangle([24 + k * 34, sheet.height - 30, 54 + k * 34, sheet.height - 8], fill=rgb)
        d.text((28 + k * 34, sheet.height - 46), f"#{k + 1}", fill=(220, 220, 220), font=f)
    out = P / "build/previews/void_stone_paint.png"
    sheet.save(out)
    return out


def main():
    pal = palette()
    images = {n: fn(random.Random(f"void:{n}")).image(pal) for n, fn in TEXTURES.items()}
    print("palette:", " ".join("#%02X%02X%02X(%.3f)" % (*c, lum(c)) for c in pal))
    print("preview:", preview(images, pal).relative_to(P))
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
    fam = [n for n in TEXTURES if "/void_stone_" not in n or n.endswith("tiles")] + [f"{VS}c", f"{VS}b"]
    fam = list(dict.fromkeys(fam))
    sheet = Image.new("RGB", (len(fam) * 160 + 20, 200), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(fam):                            # every texture tiled 3 x 3 at 3x
        t = Image.new("RGB", (48, 48))
        for bx in range(3):
            for by in range(3):
                t.paste(images[n], (bx * 16, by * 16))
        sheet.paste(t.resize((144, 144), Image.NEAREST), (16 + i * 160, 30))
        d.text((16 + i * 160, 8), n.split("/")[-1], fill=(230, 230, 230), font=f)
    sheet.save(P / "build/previews/void_stone_family_tiles.png")
    tmp = P / "build/previews/void_stone_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    for n, img in images.items():
        img.save(tmp / f"{n.split('/')[-1]}.png")          # for the texture audit script
    if not APPLY:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_void_stone")
    written = []
    for n, img in images.items():
        dst = T / f"{n}.png"
        if dst.exists():
            (bk / dst.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, bk / dst.relative_to(P))
            if not art_guard.is_ours(dst) and "--force" in sys.argv:
                dst.unlink()                                 # pipeline / imported texture being repainted on request
        if art_guard.save(img, dst):
            written.append(dst.relative_to(A).as_posix())
    man = P / "tools/texture_pipeline/recolor_manifest.json"
    doc = json.loads(man.read_text(encoding="utf-8"))
    keep = [e for e in doc["entries"] if e["file"] not in written]
    if len(keep) != len(doc["entries"]):
        doc["entries"] = keep
        man.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    model = json.loads(PILLAR_MODEL.read_text(encoding="utf-8"))
    if model["textures"]["end"] != "pysift:block/void_stone_pillar/void_stone_pillar_top":
        (bk / PILLAR_MODEL.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PILLAR_MODEL, bk / PILLAR_MODEL.relative_to(P))
        model["textures"]["end"] = "pysift:block/void_stone_pillar/void_stone_pillar_top"
        PILLAR_MODEL.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    print("written:", len(written), "; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
