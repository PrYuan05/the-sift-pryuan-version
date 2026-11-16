"""Stone upgrade plan: real-world reference stones as 16x16 pixel sketches + the per-biome table of blocks to upgrade.
Usage: python -I tools/worldgen/stone_reference_sheet.py <project>
Writes art_requests/stone_upgrade_plan.md and art_requests/stone_upgrade_references.png (it does NOT touch any game texture).

Every reference is a hand-built pixel sketch of the real stone's structure (bedding, cracks, vesicles, foliation, veins ...) in
the stone's real colours: the structure rules are the point, not a photo. Next to it the same sketch is shown tinted with the hue
of the block it will replace (the biome keeps its colour identity; the structure becomes real), and the current texture.
Palette: seven steps (skill 2.1): luminance ladder in fixed fractions of the stone's span, hue +13..-19 deg, S 0.48..1.0.
The soft pink family and the slates use a narrow span and only adjacent steps (user: the first pink set was too contrasty).
"""
import colorsys, math, random, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift"
T = A / "textures/block"
C1, C2, C3, C4, C5, C6, C7 = range(7)
G = 7        # second ramp starts here (idx G + k)

# ------------------------------------------------------------------------------------------------ palette
FRAC = [+0.44, +0.29, +0.14, 0.0, -0.14, -0.32, -0.56]
DH = [+13, +9, +4, 0, -4, -10, -19]
SF = [0.48, 0.66, 0.86, 1.0, 0.98, 0.86, 0.72]


def lum(rgb): return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255


def ramp(h, s, l0, span):
    out = []
    for dh, sf, fr in zip(DH, SF, FRAC):
        target = min(0.93, max(0.08, l0 + fr * span))
        lo, hi = 0.0, 1.0
        for _ in range(40):
            v = (lo + hi) / 2
            rgb = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(((h + dh) % 360) / 360, min(0.9, s * sf), v))
            lo, hi = (v, hi) if lum(rgb) < target else (lo, v)
        out.append(rgb)
    return out


# ------------------------------------------------------------------------------------------------ canvas + helpers
class Grid:
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
    cells = set(cells)
    for p in cells:
        c.set(*p, base)
    keys, weights = zip(*colours.items())
    for _ in range(500):
        if sum(1 for p in cells if c.get(*p) == base) <= base_max * len(cells):
            break
        x, y = rnd.choice(sorted(cells))
        col = rnd.choices(keys, weights)[0]
        for dx, dy in rnd.choice(BLOBS):
            q = ((x + dx) % 16, (y + dy) % 16)
            if q in cells and c.get(*q) == base:
                c.set(*q, col)


def sprinkle(c, rnd, n, colours):
    for _ in range(n):
        x, y = rnd.randrange(16), rnd.randrange(16)
        col = rnd.choice(colours)
        for dx, dy in rnd.choice(BLOBS[:5]):
            c.set(x + dx, y + dy, col)


def cells_voronoi(c, rnd, rows, per_row, jitter, shallow=0.5, rim=C2, deep=C7, inner=None, mot_max=0.38):
    """Torus Voronoi cells: mottled interior, lit top-left rim, #6 buffer then #7 crack bottom-right (half the joints shallow)."""
    pts = [((k * 16 / per_row + (8 / per_row if r % 2 else 0) + rnd.uniform(-jitter, jitter)) % 16, cy + rnd.uniform(-jitter, jitter))
           for r, cy in enumerate(rows) for k in range(per_row)]
    n = len(pts)
    wob = {(bx, by): rnd.uniform(-0.6, 0.6) for bx in range(8) for by in range(8)}

    def owner(x, y):
        best, who = 1e9, 0
        for i, (sx, sy) in enumerate(pts):
            dx = min(abs(x + 0.5 - sx), 16 - abs(x + 0.5 - sx))
            dy = min(abs(y + 0.5 - sy), 16 - abs(y + 0.5 - sy))
            d = math.hypot(dx, dy * 1.2) + wob[(x // 2, y // 2)] * (1 if i % 2 else -1)
            if d < best:
                best, who = d, i
        return who

    own = {p: owner(*p) for p in ALL}
    sh = {(i, j) for i in range(n) for j in range(i + 1, n) if rnd.random() < shallow}
    crack = {}
    for (x, y), o in own.items():
        for dx, dy in ((1, 0), (0, 1)):
            q = ((x + dx) % 16, (y + dy) % 16)
            if own[q] != o:
                crack[(x, y)] = C6 if tuple(sorted((o, own[q]))) in sh else deep
    body = [p for p in own if p not in crack]
    mottle(c, rnd, body, inner or {C3: 5, C5: 5}, base_max=mot_max)
    for p, col in crack.items():
        c.set(*p, col)
    for x, y in body:
        o = own[(x, y)]
        dn, rt, up, lf = own[(x, (y + 1) % 16)], own[((x + 1) % 16, y)], own[(x, (y - 1) % 16)], own[((x - 1) % 16, y)]
        if dn != o or rt != o or crack.get((x, (y + 1) % 16)) == deep or crack.get(((x + 1) % 16, y)) == deep:
            c.set(x, y, C6)
        elif up != o or lf != o or (x, (y - 1) % 16) in crack or ((x - 1) % 16, y) in crack:
            c.set(x, y, rim if (x + y) % 3 else C3)


def vein(c, rnd, y0, slope, core, buf, phase=0, amp=1.2, buf_p=0.5, thin=False):
    """Diagonal vein, slope +-1 so it wraps seamlessly on the torus, gently wobbling."""
    for x in range(16):
        y = (y0 + slope * x + round(amp * math.sin(2 * math.pi * (x + phase) / 8))) % 16
        c.set(x, y, core)
        if not thin:
            if rnd.random() < buf_p:
                c.set(x, y + 1, buf)
            if rnd.random() < buf_p:
                c.set(x, y - 1, buf)


# ------------------------------------------------------------------------------------------------ patterns
def p_ripples(rnd):
    c = Grid()
    wave = [0, 1, 0, -1]
    for y in range(16):
        for x in range(16):
            c.set(x, y, [C2, C3, C4, C4, C5, C5, C4, C3][(y + wave[(x // 4) % 4]) % 8])
    sprinkle(c, rnd, 9, [C3, C5])
    for x in range(16):
        if rnd.random() < 0.3:
            c.set(x, (0 - wave[(x // 4) % 4]) % 8 + 8 * rnd.randrange(2), C1)
    return c


def p_crossbed(rnd, tilt=(0, 1, 2, 1), thick=(2, 1, 3, 2, 1, 2, 3, 2), parting=True):
    c = Grid()
    lam = []
    for k, t in enumerate(thick):
        lam += [[C3, C4, C5, C4][k % 4]] * t
    for y in range(16):
        for x in range(16):
            c.set(x, y, lam[(y + tilt[(x // 4) % len(tilt)]) % 16])
    if parting:
        for x in range(16):
            y = (7 + tilt[(x // 4) % len(tilt)]) % 16
            if x % 8 not in (5, 6):
                c.set(x, y, C6)
    sprinkle(c, rnd, 12 if parting else 6, [C3, C5])
    return c


def p_mudcrack(rnd):
    c = Grid()
    cells_voronoi(c, rnd, rows=(3.5, 11.5), per_row=3, jitter=2.0, shallow=0.45)
    return c


def p_bands(rnd, thick=(3, 2, 1, 2, 3, 2, 1, 2), cols=(C4, C6, G + C3, C3, C5, G + C2, C4, C6)):
    c = Grid()
    rows = []
    for t, col in zip(thick, cols):
        rows += [col] * t
    wave = [0, 1, 2, 1]
    for y in range(16):
        for x in range(16):
            c.set(x, y, rows[(y + wave[(x // 4) % 4]) % 16])
    sprinkle(c, rnd, 10, [C3, C5])
    return c


def p_foliated(rnd, wavy=False, seg=(4, 9), cols=(C4, C4, C5, C3, C5, C6), n_lines=4, line=(C7, C6)):
    g = Grid()
    for y in range(16):
        x = rnd.randrange(16)
        covered = 0
        while covered < 16:
            n = rnd.randint(*seg)
            col = rnd.choice(cols)
            for k in range(n):
                if covered + k < 16:
                    g.set(x + covered + k, y, col)
            covered += n
    for _ in range(n_lines):                # cleavage lines: buffer above, line
        x, y, n = rnd.randrange(16), rnd.randrange(16), rnd.randint(6, 10)
        for k in range(n):
            g.set(x + k, y, line[0])
            g.set(x + k, y - 1, line[1])
    if not wavy:
        return g
    c = Grid()
    off = [round(1.7 * math.sin(2 * math.pi * x / 16)) for x in range(16)]
    for y in range(16):
        for x in range(16):
            c.set(x, y, g.get(x, y + off[x]))
    return c


def p_marble(rnd):
    c = Grid()
    mottle(c, rnd, ALL, {C2: 4, C3: 3, C5: 1}, base_max=0.4)
    for k, (y0, sl) in enumerate(((2, 1), (11, -1))):
        vein(c, rnd, y0, sl, C6, C5, phase=k * 3)
    vein(c, rnd, 9, -1, C5, C5, phase=5, amp=0.8, thin=True)
    return c


def p_basalt(rnd):
    c = Grid()
    mottle(c, rnd, ALL, {C3: 3, C5: 5, C2: 1}, base_max=0.36)
    for x, y in ((3, 2), (11, 6), (6, 12), (14, 13)):
        c.set(x, y, C7)
        c.set(x + 1, y, C6)
    for x, y, n in ((5, 1, 3), (12, 8, 3)):
        for k in range(n):
            c.set(x + (k // 2), y + k, C6)
    return c


def p_serp(rnd):
    c = Grid()
    mottle(c, rnd, ALL, {C3: 5, C5: 5, C2: 1}, base_max=0.3)
    for k, (y0, sl) in enumerate(((3, 1), (12, -1))):
        vein(c, rnd, y0, sl, C2, C6, phase=k * 4, amp=1.5, buf_p=0.7)
    return c


# --- soft pink family: only adjacent steps, no deep cracks, no bright lips
def p_tuff(rnd):
    c = Grid()
    mottle(c, rnd, ALL, {C3: 5, C5: 4}, base_max=0.45)
    for _ in range(6):                       # tiny pits: one shadow pixel, a lit pixel below-right
        x, y = rnd.randrange(16), rnd.randrange(16)
        c.set(x, y, C5)
        c.set(x + 1, y + 1, C3)
    return c


def p_rhyolite_flow(rnd):
    c = Grid()
    wob = [0, 1, 0, -1]
    for y in range(16):
        for x in range(16):
            c.set(x, y, [C4, C3, C4, C5][((x + 2 * y + wob[(x // 4) % 4]) % 16) // 4])
    sprinkle(c, rnd, 6, [C3, C5])
    for _ in range(3):
        x, y = rnd.randrange(16), rnd.randrange(16)
        c.set(x, y, C6)
        c.set(x + 1, y + 1, C3)
    return c


def p_clay(rnd):
    c = Grid()
    mottle(c, rnd, ALL, {C3: 4, C5: 4, C2: 1}, base_max=0.4)
    sprinkle(c, rnd, 4, [C5])
    return c


def p_rosa_marble(rnd):
    c = Grid()
    mottle(c, rnd, ALL, {C3: 4, C5: 3, C2: 2}, base_max=0.4)
    vein(c, rnd, 3, 1, C2, C3, phase=0, amp=1.4, buf_p=0.6)
    vein(c, rnd, 11, -1, C2, C3, phase=4, amp=1.0, buf_p=0.5)
    vein(c, rnd, 7, 1, C3, C3, phase=2, amp=0.8, thin=True)
    return c


# --- ore veins that fill the whole block (like aurum_ore: mottled vein material, almost no host rock left)
def p_tigers_eye(rnd):
    c = Grid()
    rows, k = [], 0
    while len(rows) < 16:
        rows += [[C4, C5, C3, C4, C6, C3, C5][k % 7]] * rnd.choice((1, 2, 2))
        k += 1
    rows = rows[:16]
    wave = [0, 1, 1, 0, 0, -1, -1, 0]
    for y in range(16):
        for x in range(16):
            c.set(x, y, rows[(y + wave[(x // 2) % 8]) % 16])
    for _ in range(7):                       # chatoyant silky streaks along the fibres
        x, y, n = rnd.randrange(16), rnd.randrange(16), rnd.randint(3, 6)
        for q in range(n):
            c.set(x + q, y, C1 if q == n // 2 else C2)
            if rnd.random() < 0.6:
                c.set(x + q, y + 1, C5)
    return c


def p_limonite(rnd):
    c = Grid()
    cells_voronoi(c, rnd, rows=(2, 6, 10, 14), per_row=4, jitter=0.8, shallow=0.85, rim=C2, inner={C3: 4, C5: 4}, mot_max=0.5)
    return c


def p_chalcopyrite(rnd):
    c = Grid()
    mottle(c, rnd, ALL, {C3: 4, C5: 4, C2: 2, C6: 1}, base_max=0.3)
    for gx, gy in ((1, 2), (9, 8), (4, 11)):  # iridescent blue-purple tarnish films
        for dx, dy in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (1, 2)):
            c.set(gx + dx, gy + dy, G + (C3 if (dx + dy) % 2 else C4))
        c.set(gx + 2, gy + 1, G + C6)
    return c


def p_native_copper(rnd):
    c = Grid()
    mottle(c, rnd, ALL, {C3: 3, C5: 5, C6: 2}, base_max=0.3)
    for _ in range(3):                       # dendritic copper sheets
        x, y = rnd.randrange(16), rnd.randrange(16)
        for _ in range(9):
            c.set(x, y, C2)
            c.set(x, y + 1, C5)
            x += rnd.choice((1, 1, 0))
            y += rnd.choice((-1, 0, 1))
    for gx, gy in ((12, 2), (3, 12)):         # verdigris patina
        for dx, dy in BLOBS[4]:
            c.set(gx + dx, gy + dy, G + C3)
        c.set(gx + 1, gy + 2, G + C4)
    return c


# ------------------------------------------------------------------------------------------------ the reference stones
# key: (zh, en, site / formation, (H, S, L0, span), pattern, kwargs, second ramp (H, S, L0, span) or None, structure notes)
REFS = {
    "sand": ("風紋沙", "Wind-rippled dune sand", "納米布沙漠、撒哈拉", (28, .55, .66, .24), p_ripples, {}, None,
             "沙丘表面的風成漣漪：背風面較陡較暗、迎風面長而緩，漣漪線微微起伏；沙粒細，只有零星的亮暗顆粒"),
    "coconino": ("科科尼諾白砂岩", "Coconino sandstone", "美國亞利桑那 大峽谷", (42, .20, .80, .20), p_crossbed,
                 {"tilt": (0, 1, 2, 1)}, None, "風成交錯層理：細白的石英砂，層理線斜著穿過；顏色最淡、顆粒最細"),
    "mudcrack": ("龜裂泥岩", "Mud-cracked playa mudstone", "死亡谷 Badwater、乾涸湖床", (30, .30, .62, .22), p_mudcrack, {}, None,
                 "乾縮龜裂：多邊形泥片，邊緣翹起（左上亮緣）、裂縫右下較深，一半是淺裂"),
    # --- soft pink family (replaces the first, too contrasty set)
    "tuff": ("粉紅凝灰岩", "Pink rhyolitic tuff", "土耳其 卡帕多奇亞、匈牙利 Eger", (350, .34, .62, .15), p_tuff, {}, None,
             "柔軟細緻的火山灰固結岩：幾乎平滑，只有細小的孔點與團粒，色階只用相鄰 3~4 階，跨度很窄"),
    "pink_sandstone": ("粉紅砂岩", "Coral pink sandstone", "美國猶他 Coral Pink Sand Dunes", (8, .42, .60, .16), p_crossbed,
                       {"tilt": (0, 1, 1, 0), "thick": (3, 2, 3, 2, 3, 3), "parting": False}, None,
                       "細粒風成砂岩，只有很淡的寬層理（2~3 px 一層、相鄰色階），沒有深色夾層線"),
    "rhyolite": ("粉紅流紋岩", "Pink flow-banded rhyolite", "美國黃石、墨西哥", (5, .38, .55, .16), p_rhyolite_flow, {}, None,
                 "火山熔岩流動形成的斜向細條帶（4 px 一條、相鄰色階），偶有極小的氣孔；整體平順"),
    "pink_clay": ("粉紅黏土", "Pink kaolin clay", "澳洲 Pilbara、法國 Provence", (350, .30, .64, .12), p_clay, {}, None,
                  "細膩的黏土團粒：2~4 px 的柔和團塊交織，色階只差一階，沒有礫石也沒有裂縫"),
    "rosa_marble": ("玫瑰大理石", "Rosa Portogallo marble", "葡萄牙 Estremoz、義大利 Rosa Aurora", (355, .30, .60, .20), p_rosa_marble, {}, None,
                    "粉紅基底，幾條很淡的亮色斜脈（只比底色亮兩階），脈兩側有柔和暈邊；沒有高對比的白脈"),
    # --- other biomes
    "siltstone": ("層紋粉砂岩", "Laminated siltstone", "美國 Moenkopi／Chinle 地層", (150, .16, .52, .22), p_crossbed,
                  {"tilt": (0, 0, 1, 0), "thick": (1, 2, 1, 1, 2, 1, 3, 2, 1, 2), "parting": True}, None,
                  "細密的薄層紋理（1~2 px 一層），層面平整略起伏，偶有較暗的泥質夾層；綠灰色（含海綠石／綠泥石）"),
    "banded_mud": ("條帶泥岩", "Banded bentonite mudstone (Chinle)", "彩繪沙漠（Painted Desert）", (15, .28, .50, .30), p_bands,
                   {"thick": (4, 2, 3, 1, 3, 2, 1), "cols": (C4, G + C3, C5, C6, C3, G + C2, C5)}, (310, .12, .62, .22),
                   "寬而平的灰、紅、淡紫色帶，色帶之間界線清楚"),
    "slate": ("紫色板岩", "Purple slate", "威爾斯 Penrhyn", (282, .20, .36, .15), p_foliated,
              {"seg": (7, 13), "cols": (C4, C4, C4, C5, C3, C3), "n_lines": 2, "line": (C6, C5)}, None,
              "板狀劈理：長而細的 1 px 薄片（7~13 px）整齊疊放，相鄰色階接近、劈理線只用次暗色，整體平順"),
    "phyllite": ("紫色千枚岩", "Purple phyllite", "阿帕拉契山脈", (290, .24, .42, .18), p_foliated,
                 {"wavy": True, "seg": (5, 9), "cols": (C4, C4, C5, C3, C3, C5), "n_lines": 2, "line": (C6, C5)}, None,
                 "比板岩更細膩、有絲絹光澤的波浪狀劈理，起伏一個週期、對比同樣收窄"),
    "marble": ("卡拉拉大理石", "Carrara marble", "義大利 托斯卡尼", (40, .06, .78, .30), p_marble, {}, None,
               "白到淺灰的細粒基底，1 px 的灰色斜向脈紋蜿蜒穿過，脈兩側有淡淡的暗暈"),
    "chlorite": ("綠泥片岩", "Chlorite schist", "阿爾卑斯、格陵蘭", (150, .30, .38, .26), p_foliated,
                 {"wavy": True, "seg": (5, 11), "n_lines": 3}, None, "波浪狀葉理的暗綠色片岩，帶絲絹光澤的亮脊，葉理起伏明顯"),
    # --- ore veins that fill the whole block (aurum_ore): pick one
    "tigers_eye": ("虎眼石", "Tiger's eye", "南非 Northern Cape、西澳", (36, .78, .36, .34), p_tigers_eye, {}, None,
                   "金棕色平行纖維（1~2 px 一條、微微起伏），纖維上有 3~6 px 的絲絹亮條（貓眼光），整塊都是礦"),
    "limonite": ("褐鐵礦（葡萄狀）", "Botryoidal limonite / goethite", "德國、英國 Cumbria", (28, .72, .40, .30), p_limonite, {}, None,
                 "棕橘色圓球狀結核連成一片（4 px 左右的小圓丘），左上受光、縫淺，整塊都是礦"),
    "chalcopyrite": ("黃銅礦（虹彩）", "Iridescent chalcopyrite", "秘魯、美國 Bisbee", (48, .80, .52, .30), p_chalcopyrite, {}, (265, .42, .42, .24),
                     "黃銅色團塊，局部氧化出藍紫色虹彩膜；金黃主體加少量藍紫斑，整塊都是礦"),
    "native_copper": ("自然銅", "Native copper (with verdigris)", "美國密西根 Keweenaw", (22, .70, .46, .30), p_native_copper, {}, (165, .40, .50, .20),
                      "橘棕色的銅片與樹枝狀結構，夾少量綠色銅鏽；整塊都是礦"),
    # --- underground
    "basalt": ("玄武岩", "Basalt", "冰島、愛爾蘭 巨人堤道", (215, .08, .27, .17), p_basalt, {}, None,
               "細粒暗灰，結構緻密：幾個 1~2 px 小氣孔，加上稀疏的垂直節理（短、錯開）"),
    "rusty_basalt": ("鐵染玄武岩", "Oxidized (iron-stained) basalt", "夏威夷、澳洲玄武岩紅土", (18, .38, .34, .22), p_basalt, {}, None,
                     "同玄武岩的緻密結構，表面鐵氧化成紅褐，氣孔邊緣鏽色更深"),
    "peridotite": ("橄欖岩／蛇紋岩", "Peridotite / serpentinite", "阿曼、加州 Coast Range", (95, .32, .36, .24), p_serp, {}, None,
                   "橄欖綠顆粒基底，白綠色的蛇紋石細脈（1 px）蜿蜒穿過，脈旁有暗暈"),
}
ORDER = list(REFS)
RID = {k: f"R{i + 1:02d}" for i, k in enumerate(ORDER)}      # R01.. follows the table order
ORE = ["tigers_eye", "limonite", "chalcopyrite", "native_copper"]

# biome tables: (biome id, zh, [(layer, [(block, current default texture)], ref keys, has building set, note)])
BIOMES = [
    ("amber_dunes", "琥珀沙丘", [
        ("地表（0~3 格）", [("amber_sand", "amber_sand/amber_sand"), ("pale_sand", "pale_sand/pale_sand")], ["sand"], False,
         "兩種沙都畫成風紋沙；色階相同、色相不同"),
        ("地下（3~6 格）", [("bleached_sandstone", "bleached_sandstone/bleached_sandstone_bleach0")], ["coconino"], True,
         "bleach 0~4 五階：越白越接近最淡階（琥珀／淺砂岩建材組上一輪已完成，不列入）"),
        ("深層（6~9 格）", [("cracked_sandstone", "cracked_sandstone/cracked_sandstone_crack0")], ["mudcrack"], False,
         "crack 0~3：裂得越多多邊形越小；也是柳絮林地的路徑"),
    ]),
    ("crimson_strata_canyon", "赤紅沉積峽谷", [
        ("地表", [("canyon_capped_crimson_strata", "sift_ground/canyon_top_a")], ["tuff", "pink_sandstone"], False,
         "頂面（canyon_top_a~d）→ 粉紅凝灰岩；側面 crimson_strata_i → 粉紅砂岩；底面沿用地下的 silted_strata"),
        ("地下（0~4 格）", [("silted_strata", "silted_strata/silted_strata_silt0_a")], ["siltstone"], True,
         "silt 0~2：越深層紋越密、含更多暗色泥質夾層"),
        ("路徑", [("banded_mudstone", "banded_mudstone/banded_mudstone_banding0")], ["banded_mud"], True, "banding 0~3：色帶由窄到寬"),
        ("桌山頂", [("capped_crimson_strata", "capped_crimson_strata/capped_crimson_strata_rose_top")], ["tuff", "pink_sandstone"], False,
         "tone teal／rose／mottled／deep_teal 四種：頂面凝灰岩、側面粉紅砂岩"),
        ("桌山身", [("ember_stone", "ember_stone/ember_stone_heat0_a")], ["rhyolite"], True, "heat 0~4：粉紅流紋岩由淺到深（越熱越偏赭紅）"),
        ("岩壁與層", [("crimson_strata", "crimson_strata/crimson_strata_a")], ["pink_sandstone"], True, "14 張側面貼圖：tone rose／mottled／crimson／plum"),
    ]),
    ("violet_slate_abyss", "紫晶深板岩區", [
        ("地表", [("violet_capped_dark_slate", "violet_strata/violet_strata_e")], ["phyllite", "slate"], False,
         "頂面（violet_strata_e）→ 千枚岩；側面（dark_slate_q）→ 板岩"),
        ("地下（0~5 格）", [("dark_slate", "dark_slate/dark_slate_a")], ["slate"], True, "fade 0~4、共 20 張：由暗紫板岩漸變，要保留每個階段的辨識度"),
        ("路徑", [("ash_marble", "ash_marble/ash_marble_veining0")], ["marble"], True, "veining 0~3：脈紋由少到多（也用在搖籃曲山丘的台地）"),
        ("結構（Boss 神殿、方尖碑）", [("dark_slate_pillar", "dark_slate_pillar/dark_slate_pillar_side")], ["slate"], False,
         "柱身（top／side／bottom）：切割過的板岩柱，劈理沿柱軸方向"),
        ("岩壁與紫層", [("violet_strata", "violet_strata/violet_strata_e")], ["phyllite"], True, "紫色地層本體"),
    ]),
    ("willow_grove", "柳絮林地", [
        ("地表", [("grove_capped_crimson_strata", "sift_ground/grove_top")], ["pink_clay", "pink_sandstone"], False,
         "頂面（grove_top、grove_top_b）→ 粉紅黏土；側面 crimson_strata_c → 粉紅砂岩；底面 teal_strata_a"),
        ("地下（0~6 格）", [("abyssal_strata", "abyssal_strata/abyssal_strata_depth0_a")], ["chlorite"], True,
         "depth 0~3、共 7 張：越深葉理越密越暗（Boss 神殿的磚用這個）"),
        ("路徑", [("cracked_sandstone", "cracked_sandstone/cracked_sandstone_crack0")], ["mudcrack"], False, "與琥珀沙丘共用，不重畫"),
        ("底面與層", [("teal_strata", "teal_strata/teal_strata_a")], ["siltstone"], True, "tone pale／cyan"),
    ]),
    ("lullaby_hills", "搖籃曲山丘", [
        ("台地地表", [("capped_crimson_vein_stone", "capped_crimson_vein_stone/capped_crimson_vein_stone_top")], ["rusty_basalt", "basalt"], False,
         "頂面鐵染玄武岩、底面玄武岩、側面兩者交界"),
        ("岩壁", [("crimson_vein_stone", "crimson_vein_stone/crimson_vein_stone_crimson_spread0")], ["rosa_marble"], True,
         "crimson_spread 0~4：灰紫底 → 粉紅（spread 4 整塊玫瑰大理石；spread 3、4 是牆面）"),
        ("谷地", [("ash_marble", "ash_marble/ash_marble_veining0")], ["marble"], False, "與紫晶區共用，不重畫"),
        ("河岸與河床", [("aurum_ore", "aurum_ore/aurum_ore_richness1")], ORE, False,
         "richness 0~1；**四種礦脈材質擇一**，礦脈佈滿整個方塊（richness 0 留較多灰色圍岩、1 幾乎全滿）；谷底砂岩層用 bleached_sandstone"),
    ]),
    ("red_zone_caves", "紅區洞穴", [
        ("洞穴地面與天花板", [("canyon_capped_crimson_strata", "sift_ground/canyon_top_a"), ("silted_strata", "silted_strata/silted_strata_silt0_a")],
         ["tuff", "pink_sandstone", "siltstone"], False, "與赤紅沉積峽谷共用同一組方塊，不重畫（洞穴的光照會改變觀感，進遊戲再看一次）"),
    ]),
    ("(所有生態域)", "地底 void_stone", [
        ("底岩（深度 5~8 格起）", [("void_stone", "void_stone/void_stone_c")], ["basalt"], True,
         "只保留 tone dark → 玄武岩（施工中）；rusty、olive 之後刪除或改成別的方塊，見待辦"),
    ]),
]


def sets_in_java():
    java = (P / "src/main/java/pryuan05/pysift/block/ModBlocks.java").read_text(encoding="utf-8")
    m = re.search(r"BUILDING_SETS = List\.of\((.*?)\);", java, re.S)
    return re.findall(r'"([a-z0-9_]+)"', m[1])


def derived(base):
    return [f"{base}_bricks", f"chiseled_{base}_bricks", f"{base}_slab", f"{base}_stairs", f"{base}_wall",
            f"{base}_brick_slab", f"{base}_brick_stairs", f"{base}_brick_wall"]


def png_count(folder):
    d = T / folder
    return len(list(d.rglob("*.png"))) if d.is_dir() else 0


def avg_hs(path):
    px = [c[:3] for c in Image.open(T / f"{path}.png").convert("RGBA").get_flattened_data() if c[3] > 0]
    r, g, b = (sum(c[i] for c in px) / len(px) / 255 for i in range(3))
    h, s, _ = colorsys.rgb_to_hsv(r, g, b)
    return h * 360, s


def render(key, tint=None):
    zh, en, site, (h, s, l0, span), fn, kw, second, notes = REFS[key]
    c = fn(random.Random(key), **kw)
    base = ramp(h, s, l0, span)
    if tint:
        base = ramp(tint[0], min(0.75, max(0.12, tint[1])), l0, span)
    pal = base + (ramp(*second) if second else [(255, 0, 255)] * 7)
    return c.image(pal), base


def main():
    sets = set(sets_in_java())
    cur_for = {}
    for _, _, rows in BIOMES:
        for layer, blocks, refs, der, note in rows:
            for k in refs:
                cur_for.setdefault(k, []).append(blocks[0])
    cur_for["basalt"] = [("void_stone", "void_stone/void_stone_c")]          # tone dark
    cur_for["rusty_basalt"] = [("void_stone", "void_stone/void_stone_f")]    # tone rusty
    cur_for["peridotite"] = [("void_stone", "void_stone/void_stone_e")]      # tone olive
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 12)
    fb = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 13)
    S, cw, ch, cols = 88, 300, 168, 4
    rows_n = (len(ORDER) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw + 10, rows_n * ch + 44), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "現實石材 16×16 參考樣式：左＝現實色｜中＝套上被取代方塊的色相（生態域色系）｜右＝目前的貼圖", fill=(235, 235, 235), font=fb)
    palettes = {}
    for i, key in enumerate(ORDER):
        x0, y0 = 10 + (i % cols) * cw, 34 + (i // cols) * ch
        real, base = render(key)
        palettes[key] = base
        cur = cur_for.get(key, [])
        tint, curim = None, None
        if cur:
            tint = avg_hs(cur[0][1])
            curim = Image.open(T / f"{cur[0][1]}.png").convert("RGB").crop((0, 0, 16, 16))
        tinted, _ = render(key, tint) if tint and key != "rusty_basalt" else (real, base)   # rusty: today's tone is blue-grey, keep the real rust
        if key in ORE:
            tinted = real                                   # the vein colour is the point of the ore candidates
        for k, im in enumerate([real, tinted, curim]):
            if im is not None:
                sheet.paste(im.resize((S, S), Image.NEAREST), (x0 + k * (S + 6), y0 + 20))
        d.text((x0, y0), f"{RID[key]} {REFS[key][0]}", fill=(255, 235, 170), font=fb)
        d.text((x0, y0 + 20 + S + 3), REFS[key][1][:40], fill=(190, 200, 215), font=f)
        for k, rgb in enumerate(base):
            d.rectangle([x0 + k * 14, y0 + 20 + S + 20, x0 + k * 14 + 12, y0 + 20 + S + 32], fill=rgb)
    out = P / "art_requests/stone_upgrade_references.png"
    sheet.save(out)

    L = ["# 石材升級對印表（現實石材 → 生態域方塊）", "",
         "由 `tools/worldgen/stone_reference_sheet.py` 產生（不會改任何遊戲貼圖）。總覽圖：`art_requests/stone_upgrade_references.png`"
         "（每種現實石材三張 16×16：現實色／套上生態域色相／目前貼圖）。", "",
         "**做法**：紋理結構（層理、裂紋、氣孔、劈理、脈紋）取自現實石材；色相保留各生態域原本的色系（青碧、粉紅、紫、金…），"
         "亮暗階與色相偏移照 skill 的 7 色雙層色階。參考樣式是照現實石材的結構手繪的像素草圖，不是照片。", "",
         "**這一版的修改**：粉紅系方塊改用更柔和的石材（凝灰岩、粉紅砂岩、流紋岩、黏土、玫瑰大理石），色階跨度壓窄到 0.12~0.20；"
         "紫色板岩、千枚岩也磨平；`aurum_ore` 改成四種「礦脈佈滿整個方塊」的候選；已完成的琥珀／淺砂岩不再列出。", "",
         f"## 一、現實參考石材（{len(ORDER)} 種）", "",
         "| 編號 | 現實石材 | 英文／產地 | 要畫出的結構 | 現實色 7 階（亮→暗） |", "| :-- | :-- | :-- | :-- | :-- |"]
    for key in ORDER:
        zh, en, site, _, _, _, _, notes = REFS[key]
        L.append(f"| {RID[key]} | {zh} | {en}（{site}） | {notes} | " + " ".join("`#%02X%02X%02X`" % c for c in palettes[key]) + " |")
    total_base = total_der = total_tex = 0
    seen = set()
    for bid, zh, rows in BIOMES:
        L += ["", f"## {zh}" + (f"（`{bid}`）" if not bid.startswith("(") else ""), "",
              "| 層位 | 現有方塊 | 貼圖數* | 參考石材 | 升級的方塊（含衍生） | 備註 |", "| :-- | :-- | :-- | :-- | :-- | :-- |"]
        for layer, blocks, refs, der, note in rows:
            names = "、".join(f"`{b}`" for b, _ in blocks)
            tex = sum(png_count(b) + (png_count(f"{b}_bricks") + png_count(f"chiseled_{b}_bricks") if b in sets else 0) for b, _ in blocks)
            refs_s = ("四選一：" if refs == ORE else "") + "、".join(f"{RID[k]} {REFS[k][0]}" for k in refs)
            if der and blocks[0][0] in sets:
                up = "本體＋8 個衍生：" + "、".join(f"`{m}`" for m in derived(blocks[0][0]))
            elif der:
                up = "本體（沒有建材組）"
            else:
                up = "本體（單一方塊，無衍生）"
            if "共用" not in note:
                for b, _ in blocks:
                    if b not in seen:
                        seen.add(b)
                        total_base += 1
                        if b in sets:
                            total_der += 8
                        total_tex += png_count(b) + (png_count(f"{b}_bricks") + png_count(f"chiseled_{b}_bricks") if b in sets else 0)
            L.append(f"| {layer} | {names} | {tex if tex else '見備註'} | {refs_s} | {up} | {note} |")
    L += ["", "\\* 貼圖數 = 本體資料夾的 PNG ＋（有建材組時）石磚、浮雕石磚資料夾的 PNG；半磚、階梯、牆直接用本體或石磚的貼圖，不另外畫。", "",
          "## 二、工作量", "",
          f"- 要重畫的本體方塊：**{total_base} 種**（已排除共用與已完成的）。",
          f"- 連動升級的衍生方塊：**約 {total_der} 個**（半磚、階梯、牆等只改模型引用，不另畫貼圖）。",
          f"- 要重畫的 PNG：**約 {total_tex} 張**（本體、石磚、浮雕石磚）；另外地表複合方塊的頂面在 `sift_ground/`（canyon_top_a~d、grove_top、grove_top_b 共 6 張）、側面沿用 `crimson_strata`，不重複計算。",
          "- 浮雕石磚（`chiseled_*`）依 skill 規則要換成該生態域的生物頭像：柳絮林地 Harmonizer、紫晶深板岩區 Sculk Monstrosity、赤紅峽谷 Dartback、搖籃曲山丘 Echo Golem、紅區洞穴 Stalker；琥珀沙丘的 `chiseled_bleached_sandstone_bricks` 用 Monarch。", "",
          "## 三、建議的施工順序", "",
          "1. **地底 void_stone**（玄武岩、鐵染玄武岩、橄欖岩，9 張＋建材組）：全世界都會看到，先做。",
          "2. **地表複合方塊**：赤紅峽谷、柳絮林地、紫晶區、搖籃曲山丘的地表（頂面 ＋ 側面）。",
          "3. **地下層與路徑**：silted／abyssal／dark_slate、bleached／cracked sandstone、banded_mudstone、ash_marble。",
          "4. **建材組**：每種石頭的石磚與浮雕石磚（浮雕換生物頭像）。", "",
          "## 四、待辦", "",
          "- [ ] **void_stone 只留第一種變體**：`void_stone` 之後只保留 tone `dark`（玄武岩）；`rusty`（`void_stone_f`）和 `olive`（`void_stone_e`）"
          "兩個 tone 會刪除或改成別的方塊，等使用者決定。注意 `void_stone_f` 也被 `gray_capped_void_stone`、`crimson_capped_violet_strata` 用到，刪之前要換掉。"
          "R20 鐵染玄武岩、R21 橄欖岩因此暫不畫。",
          "- [ ] **R17 黃銅礦、R18 自然銅先不要套用**（使用者 2026-10-30）；`aurum_ore` 的礦脈材質還沒選定（剩 R15 虎眼石／R16 褐鐵礦）。",
          "- [x] **地底 void_stone（玄武岩）**：本體 `void_stone_c`、石磚 `void_stone_b`／`void_stone_d`、雕紋 `chiseled_void_stone_bricks`（Stalker 頭像）、柱 `void_stone_h`＋六角柱頂面。", "",
          "## 五、需要你確認", "",
          "1. 色相保留生態域色系（預設）？還是改成更接近現實石材的顏色？（對照圖中間那張就是「保留色系」的樣子）",
          f"2. `aurum_ore` 的礦脈材質四選一：{RID['tigers_eye']} 虎眼石／{RID['limonite']} 褐鐵礦／{RID['chalcopyrite']} 黃銅礦／{RID['native_copper']} 自然銅。",
          "3. 先做哪一批？",
          "4. `bleached_sandstone`、`cracked_sandstone` 是否也算「砂岩不需要修改」？如果是，我會把它們和琥珀沙丘的地表一起拿掉。"]
    (P / "art_requests/stone_upgrade_plan.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(out.relative_to(P), len(ORDER), "refs;", total_base, "bases,", total_der, "derived,", total_tex, "textures")


if __name__ == "__main__":
    main()
