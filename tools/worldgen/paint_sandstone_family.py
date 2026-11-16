"""Hand-designed sandstone textures for one sand (minecraft-texture-crafter skill: two-tier palette + Jappa topology).
Usage: python -I tools/worldgen/paint_sandstone_family.py <project> <sand colour: amber|pale> [--apply]

Without --apply only build/previews/<colour>_sandstone_paint.png is written (new vs current, tilings, a small wall).
With --apply the five textures under textures/block/<colour>_sandstone/ are written through tools/art_guard.py (the
current files are backed up to .texture_backups/<stamp>_paint_<colour>_sandstone/ first).

Material brief: aeolian sandstone of the amber dunes (cemented dune sand): matte, porous, granular; layered like Navajo
Sandstone. Vanilla anchors: sandstone / sandstone_top / cut_sandstone / chiseled_sandstone (cap band, bevel frame, carved
panel); the side and the bottom are rebuilt as rounded clastic cells (skill handbook 8.3). The chiseled panel carries the
head of the biome's creature (skill rule): the amber dunes are the Monarch's, so a crowned Monarch head in relief.

Palette: seven steps in two tiers (skill 2.1 / handbook ch. 8) - structural steps #1 #2 #6 #7 and the micro-texture
steps #3 #4 #5 around the base (Lum 0.045 apart). Hues turn warm towards the light (+4..+13 deg) and towards a cool deep
brown in the shadow (-4..-19 deg); total span Lum 0.85 -> 0.52 (matte rock, not metal).
  #1 top-edge micro highlight (cap top edge, bevel corner, relief peaks only)
  #2 lit sand (top-left rims)      #3 light grain (micro A)      #4 base      #5 dark grain (micro B)
  #6 warm shadow buffer (1 px around every deep seam / groove)   #7 deepest seam (crack valleys, carved shadow sides)
"""
import colorsys, datetime, math, random, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
COLOUR = sys.argv[2]
APPLY = "--apply" in sys.argv
A = P / "src/main/resources/assets/pysift"
OUT = A / f"textures/block/{COLOUR}_sandstone"
sys.path.insert(0, str(P / "tools"))
import art_guard

C1, C2, C3, C4, C5, C6, C7 = range(7)
# per sand: base hue / saturation of the sandstone; per step: (dH, saturation %, target luminance)
SANDS = {"amber": (37, 56), "pale": (40, 40)}
STEPS = [(+13, 0.48, 0.85), (+9, 0.66, 0.80), (+4, 0.86, 0.75), (0, 1.00, 0.705), (-4, 0.98, 0.66), (-10, 0.86, 0.60),
         (-19, 0.72, 0.52)]   # saturation as a factor of the base saturation; the dark end is desaturated to a cool deep brown


def lum(rgb):
    return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255.0


LIFT = {"amber": 0.0, "pale": 0.03}      # pale sand: the whole ladder is a little lighter, same step spacing


def palette(colour):
    """Each step: hue and saturation from the table, value solved so the luminance hits the target exactly."""
    h, s = SANDS[colour]
    out = []
    for dh, sf, target in STEPS:
        target += LIFT[colour]
        lo, hi = 0.0, 1.0
        for _ in range(40):
            v = (lo + hi) / 2
            rgb = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(((h + dh) % 360) / 360, min(0.95, s * sf / 100), v))
            lo, hi = (v, hi) if lum(rgb) < target else (lo, v)
        out.append(rgb)
    return out


class Canvas:
    def __init__(self, fill=C4):
        self.px = [[fill] * 16 for _ in range(16)]

    def set(self, x, y, c):
        self.px[y % 16][x % 16] = c

    def get(self, x, y):
        return self.px[y % 16][x % 16]

    def image(self, pal):
        img = Image.new("RGBA", (16, 16))
        img.putdata([pal[self.px[y][x]] + (255,) for y in range(16) for x in range(16)])
        return img


BLOBS = [((0, 0), (1, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)), ((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 0), (0, 1), (1, 1)),
         ((0, 0), (1, 0), (2, 0)), ((1, 0), (0, 1), (1, 1), (2, 1))]


def mottle(c, rnd, cells, colours, base_max=0.40, wrap=True):
    """Two/three-tone sand grain: over the base #4, rounded 2~4 px blobs of the other micro colours until the base covers
    at most base_max of the area. cells: the pixels to fill; colours: {colour: weight} for the blobs."""
    cells = set(cells)
    for p in cells:
        c.set(*p, C4)
    keys, weights = zip(*colours.items())
    for _ in range(400):
        if sum(1 for p in cells if c.get(*p) == C4) <= base_max * len(cells):
            break
        x, y = rnd.choice(sorted(cells))
        col = rnd.choices(keys, weights)[0]
        for dx, dy in rnd.choice(BLOBS):
            q = ((x + dx) % 16, (y + dy) % 16) if wrap else (x + dx, y + dy)
            if q in cells and c.get(*q) == C4:
                c.set(*q, col)


def cobbles(c, rnd, region, rows, wrap_y, palette_rim=C2, deep=C7, jitter=1.2):
    """Rounded clastic cells (torus Voronoi): every cell gets a lit top-left rim (#2/#3), a mottled #3/#4/#5 interior,
    a #6 buffer on its bottom-right and a #7 crack beyond it; half of the joints are shallow (#6 only), so the cells read
    as semi-closed. rows: the y centre of each row of cells; three cells per row, every other row shifted half a cell
    (like laid stone), each seed jittered a little - even sizes, rounded outlines, no long straight cracks."""
    pts = [((k * 16 / 3 + (8 / 3 if r % 2 else 0) + rnd.uniform(-jitter, jitter)) % 16, cy + rnd.uniform(-jitter, jitter))
           for r, cy in enumerate(rows) for k in range(3)]
    seeds = len(pts)
    wobble = {(bx, by): rnd.uniform(-0.7, 0.7) for bx in range(8) for by in range(8)}   # 2x2-block noise: ragged joints

    def owner(x, y):
        best, who = 1e9, 0
        for i, (sx, sy) in enumerate(pts):
            dx = min(abs(x + 0.5 - sx), 16 - abs(x + 0.5 - sx))
            dy = abs(y + 0.5 - sy)
            if wrap_y:
                dy = min(dy, 16 - dy)
            d = math.hypot(dx, dy * 1.25) + wobble[(x // 2, (y % 16) // 2)] * (1 if i % 2 else -1)   # wider than tall
            if d < best:
                best, who = d, i
        return who

    own = {(x, y): owner(x, y) for x, y in region}
    inside = lambda q: q in own
    nb = lambda x, y, dx, dy: ((x + dx) % 16, (y + dy) % 16 if wrap_y else y + dy)
    shallow = {tuple(sorted(pair)) for pair in [(i, j) for i in range(seeds) for j in range(seeds) if i < j] if rnd.random() < 0.50}
    crack = {}
    for (x, y), o in own.items():
        for dx, dy in ((1, 0), (0, 1)):
            q = nb(x, y, dx, dy)
            if inside(q) and own[q] != o:
                crack[(x, y)] = C6 if tuple(sorted((o, own[q]))) in shallow else deep
    body = [p for p in own if p not in crack]
    mottle(c, rnd, body, {C3: 5, C5: 5}, base_max=0.38, wrap=True)
    for (x, y), col in crack.items():
        c.set(x, y, col)
    for x, y in body:
        o = own[(x, y)]
        up, left = nb(x, y, 0, -1), nb(x, y, -1, 0)
        down, right = nb(x, y, 0, 1), nb(x, y, 1, 0)
        if (down in crack and crack[down] == deep) or (right in crack and crack[right] == deep) \
                or (inside(down) and own[down] != o) or (inside(right) and own[right] != o):
            c.set(x, y, C6)                                         # buffer before the deep crack
        elif up in crack or left in crack or (inside(up) and own[up] != o) or (inside(left) and own[left] != o):
            c.set(x, y, palette_rim if (x + y) % 3 else C3)         # lit top-left rim, softened every third pixel
    return own


WAVE = [0, 1, 1, 0]          # cap seam offset per 4 px segment (repeats every 16 px)


def top(rnd):
    c = Canvas()
    mottle(c, rnd, [(x, y) for x in range(16) for y in range(16)], {C3: 5, C5: 4, C2: 2}, base_max=0.38)
    return c


def side(rnd):
    c = Canvas()
    cobbles(c, rnd, [(x, y) for x in range(16) for y in range(4, 16)], rows=(6.5, 12.5), wrap_y=False)
    # compacted cap band y = 0..3
    for x in range(16):
        c.set(x, 0, C2)
        c.set(x, 1, C3 if (x // 3) % 2 else C2)
    for x in (2, 3, 9, 10, 11):
        c.set(x, 0, C1)                                             # top-edge micro highlight
    for x in range(16):
        w = WAVE[(x // 4) % 4]
        if w:
            c.set(x, 2, C3)
        c.set(x, 2 + w, C7)                                         # wavy compaction seam
        c.set(x, 3 + w, C6)                                         # #6 buffer under it
    return c


def bottom(rnd):
    c = Canvas()
    cobbles(c, rnd, [(x, y) for x in range(16) for y in range(16)], rows=(3.5, 11.5), wrap_y=True, palette_rim=C3,
            jitter=2.2)   # rougher, less regular than the side: unweathered underside
    return c


def bevel(c):
    """1 px bevel frame lit from the top-left; #1 only at the lit corner, #7 only at the shadow corner."""
    for i in range(16):
        c.set(i, 0, C2)
        c.set(0, i, C2)
        c.set(i, 15, C6)
        c.set(15, i, C6)
    c.set(0, 0, C1)
    c.set(1, 0, C1)
    c.set(0, 1, C1)
    c.set(15, 15, C7)
    c.set(15, 0, C4)
    c.set(0, 15, C4)


def cut(rnd):
    c = Canvas()
    for panel in (range(1, 7), range(9, 15)):
        mottle(c, rnd, [(x, y) for x in range(1, 15) for y in panel], {C3: 5, C5: 5}, base_max=0.45, wrap=False)
    for x in range(1, 15):                 # middle seam: #6 buffer, #7 groove, lit lower lip
        c.set(x, 7, C7 if 2 <= x <= 13 else C6)
        c.set(x, 8, C3)
        if x % 4 == 1:
            c.set(x, 6, C5)
    bevel(c)
    for x, y, col in ((6, 0, C5), (0, 11, C5), (10, 15, C5)):   # weathered nicks in the frame
        c.set(x, y, col)
    return c


MONARCH = [  # 12 x 8 crowned head (x 2..13, y 4..11), mirror symmetric; # = relief, E = carved eye slit
    "..#..##..#..",
    "..##.##.##..",
    "..########..",
    ".##########.",
    ".##EE##EE##.",
    ".##########.",
    "..########..",
    "...######...",
]


def draw_monarch(c):
    """Amber dunes: the Monarch's crowned head in relief (boss of the biome)."""
    head = {(2 + i, 4 + j): ch for j, row in enumerate(MONARCH) for i, ch in enumerate(row) if ch != "."}
    solid = lambda x, y: head.get((x, y)) == "#"
    for (x, y), ch in head.items():
        if ch == "E":
            c.set(x, y, C7)                                         # eye slit, carved
            continue
        if not solid(x, y - 1) and not solid(x - 1, y):
            col = C2                                                # lit top-left edge
        elif not solid(x, y + 1) or not solid(x + 1, y):
            col = C5                                                # shaded bottom-right edge of the relief
        else:
            col = C3                                                # face
        c.set(x, y, col)
    for (x, y), ch in head.items():        # crown tips are the relief's peaks
        if ch == "#" and (x, y - 1) not in head and y == 4:
            c.set(x, y, C1)
    for (x, y), ch in head.items():        # eye slits: #6 buffer above (shaded top wall), #3 already below
        if ch == "E" and head.get((x, y - 1)) == "#":
            c.set(x, y - 1, C6)
    for (x, y) in list(head):              # cast shadow on the panel: #6 under / right of the relief, #7 at the corner
        for dx, dy in ((1, 0), (0, 1)):
            q = (x + dx, y + dy)
            if q not in head and 3 <= q[1] <= 12 and 1 <= q[0] <= 14:
                c.set(*q, C6)
        q = (x + 1, y + 1)
        if q not in head and (x + 1, y) not in head and (x, y + 1) not in head and 3 <= q[1] <= 12 and q[0] <= 14:
            c.set(*q, C7)


SCAVENGER = [  # 12 x 8 hooded head with swept horns (x 2..13, y 4..11), mirror symmetric
    "H...####...H",     # H = horn, # = hood, D = shadowed hollow of the hood, E = an eye glinting in it
    "HH.######.HH",
    ".H########H.",
    "..##DDDD##..",
    "..#DEDDED#..",
    "..#DDDDDD#..",
    "...#DDDD#...",
    "....####....",
]


def draw_scavenger(c):
    """Pale dunes (the amber dunes' other sand): the Scavenger - the commonest creature of the biome. Relief hood with two
    horns swept out and up, the face a deep hollow (top and left walls in shadow #7, floor #6, lit lower lip #5) and two
    eyes (#2) glinting out of it."""
    head = {(2 + i, 4 + j): ch for j, row in enumerate(SCAVENGER) for i, ch in enumerate(row) if ch != "."}
    relief = lambda x, y: head.get((x, y)) in ("#", "H")
    hollow = lambda x, y: head.get((x, y)) in ("D", "E")
    for (x, y), ch in head.items():
        if ch in "DE":
            if ch == "E":
                col = C2                                            # eye: the lit pixel in the dark
            elif not hollow(x, y - 1) or not hollow(x - 1, y):
                col = C7                                            # top / left wall of the recess: deepest shadow
            elif not hollow(x, y + 1) or not hollow(x + 1, y):
                col = C5                                            # bottom / right lip catches the light
            else:
                col = C6
            c.set(x, y, col)
            continue
        if y == 4:
            col = C1                                                # horn tips and the hood's top are the peaks
        elif not relief(x, y - 1) and not relief(x - 1, y):
            col = C2                                                # lit top-left edge
        elif not relief(x, y + 1) or not relief(x + 1, y):
            col = C5                                                # shaded bottom-right edge of the relief
        else:
            col = C3
        c.set(x, y, col)
    for (x, y), ch in head.items():        # the hood's edge above the hollow gets the #6 buffer, never #1 next to #7
        if ch in "#H" and hollow(x, y + 1):
            c.set(x, y, C6)
    for (x, y), ch in list(head.items()):  # cast shadow on the panel: #6 under / right of the relief, #7 at the corner
        if ch not in "#H":
            continue
        for dx, dy in ((1, 0), (0, 1)):
            q = (x + dx, y + dy)
            if q not in head and 3 <= q[1] <= 12 and 1 <= q[0] <= 14:
                c.set(*q, C6)
        q = (x + 1, y + 1)
        if q not in head and (x + 1, y) not in head and (x, y + 1) not in head and 3 <= q[1] <= 12 and q[0] <= 14:
            c.set(*q, C7)


def chiseled(rnd):
    c = Canvas()
    mottle(c, rnd, [(x, y) for x in range(1, 15) for y in range(3, 13)], {C5: 6, C3: 2}, base_max=0.45, wrap=False)
    for x in range(1, 15):                 # thin bands: lit band + groove (top), groove + lit band (bottom)
        c.set(x, 1, C3 if x % 4 == 0 else C2)
        c.set(x, 2, C7 if 2 <= x <= 13 else C6)
        c.set(x, 13, C6 if x in (1, 14) else C7)
        c.set(x, 14, C3)
    (draw_scavenger if COLOUR == "pale" else draw_monarch)(c)
    bevel(c)
    return c


TEXTURES = {  # file -> painter
    f"{COLOUR}_sandstone_top": top, f"{COLOUR}_sandstone": side, f"{COLOUR}_sandstone_bottom": bottom,
    f"cut_{COLOUR}_sandstone": cut, f"chiseled_{COLOUR}_sandstone": chiseled,
}


def preview(images, pal):
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
    S = 6
    names = list(images)
    sheet = Image.new("RGB", (40 + len(names) * (16 * S + 20), 2 * (16 * S + 30) + 3 * 16 * 4 + 90), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        x = 20 + i * (16 * S + 20)
        old = OUT / f"{n}.png"
        d.text((x, 4), n.replace(f"{COLOUR}_", ""), fill=(230, 230, 230), font=f)
        if old.exists():
            sheet.paste(Image.open(old).convert("RGB").resize((16 * S, 16 * S), Image.NEAREST), (x, 22))
        sheet.paste(images[n].convert("RGB").resize((16 * S, 16 * S), Image.NEAREST), (x, 22 + 16 * S + 20))
    d.text((2, 22 + 16 * S // 2), "舊", fill=(200, 200, 200), font=f)
    d.text((2, 42 + 16 * S + 16 * S // 2), "新", fill=(200, 200, 200), font=f)
    y0 = 2 * (16 * S + 30) + 10
    d.text((20, y0 - 2), "平鋪：側面 4x3（上方一排頂面）｜頂面 3x3｜雕紋與切製", fill=(230, 230, 230), font=f)
    z = 3
    wall = Image.new("RGB", (16 * 4, 16 * 4))
    for bx in range(4):
        wall.paste(images[f"{COLOUR}_sandstone_top"].convert("RGB"), (bx * 16, 0))
        for by in range(1, 4):
            wall.paste(images[f"{COLOUR}_sandstone"].convert("RGB"), (bx * 16, by * 16))
    sheet.paste(wall.resize((64 * z, 64 * z), Image.NEAREST), (20, y0 + 18))
    tiles = Image.new("RGB", (48, 48))
    for bx in range(3):
        for by in range(3):
            tiles.paste(images[f"{COLOUR}_sandstone_top"].convert("RGB"), (bx * 16, by * 16))
    sheet.paste(tiles.resize((48 * z, 48 * z), Image.NEAREST), (40 + 64 * z, y0 + 18))
    mix = Image.new("RGB", (48, 32))
    for bx, n in enumerate([f"chiseled_{COLOUR}_sandstone", f"cut_{COLOUR}_sandstone", f"chiseled_{COLOUR}_sandstone"]):
        mix.paste(images[n].convert("RGB"), (bx * 16, 0))
        mix.paste(images[f"cut_{COLOUR}_sandstone"].convert("RGB"), (bx * 16, 16))
    sheet.paste(mix.resize((48 * z, 32 * z), Image.NEAREST), (60 + 112 * z, y0 + 18))
    for k, rgb in enumerate(pal):
        d.rectangle([20 + k * 34, sheet.height - 30, 50 + k * 34, sheet.height - 8], fill=rgb)
        d.text((24 + k * 34, sheet.height - 46), f"#{k + 1}", fill=(220, 220, 220), font=f)
    out = P / f"build/previews/{COLOUR}_sandstone_paint.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def main():
    pal = palette(COLOUR)
    images = {}
    for n, painter in TEXTURES.items():
        images[n] = painter(random.Random(f"{COLOUR}:{n}")).image(pal)
    print("palette:", " ".join("#%02X%02X%02X(%.3f)" % (*c, lum(c)) for c in pal))
    print("preview:", preview(images, pal).relative_to(P))
    tmp = P / "build/previews/sandstone_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    for n, img in images.items():
        img.save(tmp / f"{n}.png")                     # for the texture audit script
    if APPLY:
        bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + f"_paint_{COLOUR}_sandstone")
        for n, img in images.items():
            dst = OUT / f"{n}.png"
            if dst.exists():
                (bk / dst.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, bk / dst.relative_to(P))
            art_guard.save(img, dst)
        print("applied; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
