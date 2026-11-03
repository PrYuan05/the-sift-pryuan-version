"""aurum_ore candidates: real minerals that look like the current texture (grey host rock + orange-gold patches), each
drawn at richness 0 and 1 in the current texture's own two colours (grey from richness0, gold from richness1), so only
the structure is compared. Writes art_requests/aurum_ore_candidates.png (no game texture is touched).
Usage: python -I tools/worldgen/aurum_candidates.py <project>
"""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
T = P / "src/main/resources/assets/pysift/textures/block/aurum_ore"
sys.path.insert(0, str(P / "tools/worldgen"))
from paint_void_stone import Canvas, mottle, ALL, BLOBS, lum
from paint_pink_strata import ramp

C1, C2, C3, C4, C5, C6, C7 = range(7)


def colours(folder=T):
    import colorsys
    def fam(c):
        h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
        return "gold" if s > 0.35 and 20 / 360 <= h <= 55 / 360 else "grey"
    pools = {"gold": [], "grey": []}
    for n in ("aurum_ore_richness0.png", "aurum_ore_richness1.png"):
        for c in Image.open(folder / n).convert("RGB").get_flattened_data():
            pools[fam(c)].append(c)
    return ramp(pools["grey"], 0.20), ramp(pools["gold"], 0.26)


def blob_mask(rnd, frac, size=(2, 4)):
    m = set()
    while len(m) < frac * 256:
        x, y, r = rnd.randrange(16), rnd.randrange(16), rnd.uniform(*size) / 2
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx * dx + dy * dy <= r * r + rnd.uniform(-0.6, 0.6):
                    m.add(((x + dx) % 16, (y + dy) % 16))
    return m


def shade(c, m, rnd):
    """Gold areas: #3/#4/#5 grain, lit top-left edge (#2), #6 shadow cast on the host below-right."""
    for (x, y) in ALL:
        if (x, y) in m:
            up, lf = ((x, (y - 1) % 16) in m), (((x - 1) % 16, y) in m)
            c.set(x, y, C2 if not up or not lf else rnd.choice((C3, C4, C4, C5)))
    for (x, y) in list(m):
        for q in ((x + 1, y + 1), (x, y + 1)):
            q = (q[0] % 16, q[1] % 16)
            if q not in m:
                c.set(*q, C6)


def host(rnd):
    c = Canvas()
    mottle(c, rnd, ALL, {C3: 4, C5: 4}, base_max=0.4)
    return c


# each: (rnd, richness) -> (host grid, gold grid, gold mask)
def ochre_clouds(rnd, rich):                       # yellow ochre / earthy goethite: soft clouds (closest to today)
    m = blob_mask(rnd, 0.35 if rich == 0 else 0.8, (3, 6))
    g = Canvas(); shade(g, m, rnd)
    return host(rnd), g, m


def gossan(rnd, rich):                             # gossan boxwork: ochre walls around leached cavities
    pts = [(rnd.uniform(0, 16), rnd.uniform(0, 16)) for _ in range(9)]
    def own(x, y):
        return min(range(len(pts)), key=lambda i: math.hypot(min(abs(x - pts[i][0]), 16 - abs(x - pts[i][0])),
                                                              min(abs(y - pts[i][1]), 16 - abs(y - pts[i][1]))))
    o = {(x, y): own(x, y) for x, y in ALL}
    walls = {(x, y) for x, y in ALL if o[((x + 1) % 16, y)] != o[(x, y)] or o[(x, (y + 1) % 16)] != o[(x, y)]}
    if rich:
        walls |= {(x, y) for x, y in ALL if rnd.random() < 0.55}
    g = Canvas(); shade(g, walls, rnd)
    for (x, y) in ALL:
        if (x, y) not in walls and rich == 0 and o[(x, y)] % 3 == 0:
            g.set(x, y, C6)
    return host(rnd), g, walls


def orpiment(rnd, rich):                           # orpiment / realgar: golden bladed crystals, resinous streaks
    m = set()
    for _ in range(9 if rich == 0 else 26):
        x, y, n = rnd.randrange(16), rnd.randrange(16), rnd.randint(3, 5)
        for k in range(n):
            m.add(((x + k) % 16, (y - k) % 16))
            m.add(((x + k + 1) % 16, (y - k) % 16))
    g = Canvas(); shade(g, m, rnd)
    return host(rnd), g, m


def gold_quartz(rnd, rich):                        # native gold in quartz: branching veinlets with blebs
    m = set()
    for _ in range(3 if rich == 0 else 6):
        x, y = rnd.randrange(16), rnd.randrange(16)
        for _ in range(12):
            m.add((x % 16, y % 16))
            if rnd.random() < 0.25:
                m.update({((x + 1) % 16, y % 16), (x % 16, (y + 1) % 16)})
            x += rnd.choice((1, 1, 0)); y += rnd.choice((-1, 0, 1))
    if rich:
        m |= blob_mask(rnd, 0.45, (3, 5))
    g = Canvas(); shade(g, m, rnd)
    return host(rnd), g, m


def siderite(rnd, rich):                           # siderite: little tan-orange rhomb crystals in clusters
    m = set()
    for _ in range(10 if rich == 0 else 30):
        x, y = rnd.randrange(16), rnd.randrange(16)
        for dx, dy in ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
            m.add(((x + dx) % 16, (y + dy) % 16))
    g = Canvas(); shade(g, m, rnd)
    return host(rnd), g, m


PYRITE_CUBES = {0: 6, 1: 16, 2: 26, 3: 40}          # cubes per richness (0 / 1 are the candidate sheet's)


def pyrite_rust(rnd, rich):                        # oxidised pyrite: 2x2 cubes inside rusty halos
    m, cubes = set(), []
    for _ in range(PYRITE_CUBES[rich]):
        x, y = rnd.randrange(16), rnd.randrange(16)
        cubes.append((x, y))
        for dx in range(-1, 3):
            for dy in range(-1, 3):
                if rnd.random() < 0.75:
                    m.add(((x + dx) % 16, (y + dy) % 16))
    g = Canvas(); shade(g, m, rnd)
    for x, y in cubes:
        g.set(x, y, C1); g.set(x + 1, y, C2); g.set(x, y + 1, C3); g.set(x + 1, y + 1, C5)
    return host(rnd), g, m


CANDIDATES = [
    ("A 黃赭石（土狀針鐵礦）", "Yellow ochre", "柔和的雲團狀礦斑，最接近現在的樣子", ochre_clouds),
    ("B 褐鐵礦鐵帽", "Gossan boxwork", "礦物沿著裂隙長成網格牆，中間是被淋濾掉的灰色空腔", gossan),
    ("C 雌黃", "Orpiment", "金黃色的斜向刀片狀晶體，帶樹脂光澤的條紋", orpiment),
    ("D 含金石英脈", "Gold in quartz", "分岔的細礦脈加上小金粒；富礦版脈旁長出礦團", gold_quartz),
    ("E 菱鐵礦", "Siderite", "一小顆一小顆的菱形晶體成群聚集", siderite),
    ("F 氧化黃鐵礦", "Oxidised pyrite", "亮色的小立方晶體，外圍一圈鐵鏽暈", pyrite_rust),
]


def render(fn, rich, grey, gold, seed):
    rnd = random.Random(seed)
    h, g, m = fn(rnd, rich)
    img = Image.new("RGB", (16, 16))
    img.putdata([(gold[g.get(x, y)] if (x, y) in m else grey[h.get(x, y)]) if g.get(x, y) != C6 or (x, y) in m
                 else grey[C6] for y in range(16) for x in range(16)])
    return img


def main():
    grey, gold = colours()
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 12)
    fb = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 13)
    S, cw = 88, 470
    sheet = Image.new("RGB", (2 * cw + 20, 40 + (len(CANDIDATES) // 2 + 1) * 160), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "aurum_ore 礦脈候選：每種左＝richness 0、中＝richness 1、右＝3×3 平鋪（richness 1）｜顏色都取自現在的貼圖", fill=(235, 235, 235), font=fb)
    cur = [Image.open(T / f"aurum_ore_richness{k}.png").convert("RGB") for k in (0, 1)]
    items = [("現在的貼圖", "", "", None)] + CANDIDATES
    for i, (zh, en, note, fn) in enumerate(items):
        x0, y0 = 10 + (i % 2) * cw, 34 + (i // 2) * 160
        ims = cur if fn is None else [render(fn, k, grey, gold, f"{en}{k}") for k in (0, 1)]
        tile = Image.new("RGB", (48, 48))
        for a in range(3):
            for b in range(3):
                tile.paste(ims[1], (a * 16, b * 16))
        for k, im in enumerate(ims + [tile]):
            sheet.paste(im.resize((S, S), Image.NEAREST), (x0 + k * (S + 8), y0 + 20))
        d.text((x0, y0), f"{zh}  {en}", fill=(255, 225, 150), font=fb)
        d.text((x0, y0 + 20 + S + 4), note, fill=(200, 210, 225), font=f)
    out = P / "art_requests/aurum_ore_candidates.png"
    sheet.save(out)
    print(out.relative_to(P))


if __name__ == "__main__":
    main()
