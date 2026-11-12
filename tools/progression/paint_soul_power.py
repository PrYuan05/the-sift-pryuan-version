"""Paint the soul power textures (assets/pysift/textures/block/soul_power/). Usage:
    python -I tools/progression/paint_soul_power.py <project>

Every texture is drawn here, pixel by pixel, from the mod's own palettes; nothing is a recoloured vanilla block. The
only borrowed pixels are vanilla *particle* sprites (soul_fire_flame, sculk_soul_*) used as the flames and souls inside
the machines. UVs in the models follow the element positions (like vanilla), so every texture is drawn centred on the
16x16 block grid: discs around (7.5, 7.5), shafts in columns 6..9, the dial window in the middle of the face.

Material brief (minecraft-texture-crafter, step 0)
  identity    Create-style soul machines built by the ancients, shaped like the vanilla sculk family (shrieker claw
              corners, catalyst ribs, glowing pores) in our own colours: patina-bronze frames, dark deepslate plates,
              siftite (pink gold) gears and wheels, soul-crystal light. Deep, cool ambient light (The Sift); shared dark = blue-black.
  surfaces    patina bronze: metal, high contrast, sheen along the long axis, rivets; deepslate plate: matte, narrow
              value span, 2-4 px clusters; stained willow: soft grain along the fibre, end-grain rings on discs;
              soul glow / charoite: 80 % muted base, 20 % saturated focus.
  real world  verdigris-crusted bronze machinery (ship winches, mill gearing), slate-and-iron furnace doors,
              wooden mill cogwheels with iron teeth, Siberian charoite (fibrous violet swirls).
  anchors     structure only: block/blast_furnace_front (firebox grate proportions), block/grindstone (stone wheel),
              Create's andesite casing (2 px bevelled frame around a plate); colours and pixels are all new.
Writes through tools/art_guard.py, so a texture the user repaints keeps their version."""
import io, json, math, random, sys, zipfile
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(P / "tools"))
import art_guard  # noqa: E402

OUT = P / "src/main/resources/assets/pysift/textures/block/soul_power"
JAR = zipfile.ZipFile(Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client-only.jar")

# ------------------------------------------------------------------ palettes (dark -> light, hue-shifted)
PATINA = [(24, 44, 58), (34, 70, 80), (48, 100, 104), (66, 132, 124), (94, 164, 144), (142, 198, 164), (192, 224, 180)]
SLATE = [(22, 24, 34), (32, 34, 46), (42, 45, 58), (52, 56, 70), (63, 67, 82), (78, 82, 96), (96, 100, 112)]
WOOD = [(30, 38, 54), (42, 54, 72), (56, 72, 90), (72, 92, 108), (92, 114, 126), (118, 140, 148), (150, 168, 170)]
SOUL = [(14, 60, 74), (22, 104, 116), (36, 150, 156), (78, 204, 202), (148, 238, 226), (206, 250, 238)]
SIFTITE = [(61, 16, 36), (125, 28, 71), (184, 46, 106), (220, 62, 133), (240, 98, 156), (250, 130, 181), (252, 196, 214)]   # the siftite ingot: gear teeth and rims
CHAROITE = [(40, 22, 62), (64, 36, 96), (94, 56, 134), (126, 84, 172), (164, 124, 204), (204, 172, 228), (230, 214, 238)]
IRON = [(40, 42, 52), (62, 66, 76), (90, 94, 102), (122, 124, 130), (158, 158, 160), (196, 194, 188), (226, 222, 210)]
STONE = [(52, 52, 58), (70, 70, 76), (88, 88, 92), (106, 106, 108), (126, 124, 122), (150, 146, 140)]
RED = [(52, 16, 30), (86, 24, 40), (128, 38, 54), (170, 62, 72), (210, 104, 104)]
CREAM = [(120, 104, 84), (168, 152, 124), (206, 192, 160), (228, 218, 190)]
LAMP_OFF = [(54, 38, 34), (82, 56, 44), (112, 76, 54)]
# soul conduit: living red sculk (the mod's red_sculk colours), dead blue sculk (vanilla sculk's), and a dry husk
LIVE_SCULK = [(116, 46, 99), (138, 58, 94), (168, 74, 102), (189, 86, 110), (204, 98, 118), (230, 119, 136), (251, 176, 168)]
DEAD_SCULK = [(13, 18, 23), (17, 27, 33), (5, 42, 50), (3, 65, 80), (5, 98, 93), (0, 146, 149), (41, 223, 235)]
HUSK = [(24, 25, 32), (33, 35, 43), (44, 46, 55), (57, 59, 68), (72, 74, 83), (90, 92, 100)]
LAMP_ON = [(150, 72, 30), (220, 132, 52), (246, 196, 104), (252, 234, 170)]


class Tex:
    def __init__(self, seed, w=16, h=16):
        self.w, self.h = w, h
        self.px = [[None] * w for _ in range(h)]
        self.rng = random.Random(seed)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def get(self, x, y):
        return self.px[y][x] if 0 <= x < self.w and 0 <= y < self.h else None

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def image(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y][x]
                if c is not None:
                    im.putpixel((x, y), (*c[:3], c[3] if len(c) > 3 else 255))
        return im


def grain(t, x0, y0, x1, y1, pal, base, rng_clusters=None, horizontal=True):
    """Fill a rectangle with a three-tone micro texture: the base tone, 2-5 px clusters one step lighter (lit on their
    top/left end) and one step darker, and a few two-step dark pits. Cluster count scales with the area so no tone
    covers more than about half the rectangle (anti-flatness, rule 18)."""
    t.rect(x0, y0, x1, y1, pal[base])
    area = (x1 - x0 + 1) * (y1 - y0 + 1)
    n = rng_clusters if rng_clusters is not None else max(4, area // 7)
    top = len(pal) - 1
    for k in range(n):
        d = 1 if k % 2 == 0 else -1
        cx, cy = t.rng.randint(x0, x1), t.rng.randint(y0, y1)
        length = t.rng.randint(2, 5)
        for i in range(length):
            x, y = (cx + i, cy) if horizontal else (cx, cy + i)
            if x0 <= x <= x1 and y0 <= y <= y1:
                tone = base + d
                if d > 0 and i == 0:
                    tone = base + 2           # the lit end of a raised cluster
                if d < 0 and i == length - 1:
                    tone = base - 2           # the shadowed end of a dent
                t.set(x, y, pal[max(0, min(top, tone))])


def bevel(t, x0, y0, x1, y1, pal, hi, lo):
    """1 px bevel: top/left lit, bottom/right in shadow."""
    for x in range(x0, x1 + 1):
        t.set(x, y0, pal[hi])
        t.set(x, y1, pal[lo])
    for y in range(y0, y1 + 1):
        t.set(x0, y, pal[hi])
        t.set(x1, y, pal[lo])
    t.set(x1, y0, pal[(hi + lo) // 2])
    t.set(x0, y1, pal[(hi + lo) // 2])


def rivet(t, x, y):
    """A raised rivet: lit top-left, shadow under it."""
    t.set(x, y, PATINA[6])
    t.set(x + 1, y, PATINA[4])
    t.set(x, y + 1, PATINA[4])
    t.set(x + 1, y + 1, PATINA[1])


VERDIGRIS = [(70, 150, 128), (104, 184, 150), (150, 214, 172)]


def crust(t, cells, n):
    """Verdigris crust on bronze: small pale-green blooms (2-3 px) with a darker pit beside some of them."""
    for _ in range(n):
        x, y = t.rng.choice(cells)
        t.set(x, y, VERDIGRIS[1])
        nx, ny = x + t.rng.choice((-1, 1)), y
        if (nx, ny) in cells:
            t.set(nx, ny, VERDIGRIS[0])
        if t.rng.random() < 0.4 and (x, y + 1) in cells:
            t.set(x, y + 1, PATINA[1])


CLAW = [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (0, 3), (2, 2)]


def claw(t, cx, cy, sx, sy):
    """A bone-claw corner piece (the sculk shrieker's top corners), drawn in bronze: a thick L that tapers to a point
    along both edges, lit on its outer top/left side, a dark notch where it bites into the plate."""
    for (dx, dy) in CLAW:
        x, y = cx + dx * sx, cy + dy * sy
        lit = (sx > 0 and sy > 0)
        tone = 6 if (dx, dy) in ((0, 0), (1, 0), (0, 1)) and lit else 5 if dx + dy <= 1 else 4 if dx + dy <= 2 else 3
        if not lit:
            tone -= 1
        t.set(x, y, PATINA[tone])
    t.set(cx + 2 * sx, cy + 2 * sy, PATINA[1])           # the notch


def frame(t, width=2):
    """The casing frame in the sculk family's shape language: a 2 px bronze border (outer edge lit top-left, inner
    edge shadowed so the plate sits inside it), heavy claw pieces at the four corners like the shrieker's bones, and
    a little dark growth creeping over the bars (sculk spreading on bone)."""
    cells = [(x, y) for y in range(16) for x in range(16) if x < width or y < width or x > 15 - width or y > 15 - width]
    for (x, y) in cells:
        outer = min(x, y, 15 - x, 15 - y) == 0
        lit = x + y < 15
        t.set(x, y, PATINA[(5 if outer else 4) if lit else (2 if outer else 3)])
    for _ in range(5):                                    # creeping growth: 2-3 px dark clumps on the bars
        x, y = t.rng.choice(cells)
        if 4 <= x <= 11 or 4 <= y <= 11:
            t.set(x, y, SLATE[1])
            t.set(x + (1 if x < 8 else -1), y, SLATE[2]) if (x + (1 if x < 8 else -1), y) in cells else None
    claw(t, 0, 0, 1, 1)
    claw(t, 15, 0, -1, 1)
    claw(t, 0, 15, 1, -1)
    claw(t, 15, 15, -1, -1)


def pores(t, x0, y0, x1, y1, n):
    """Sculk's glowing pores: a bright soul pixel with one or two dimmer pixels beside it, scattered over the plate,
    and a few darker clumps between them (the vanilla sculk block's pattern, in our soul-cyan palette)."""
    for k in range(n):
        x, y = t.rng.randint(x0 + 1, x1 - 1), t.rng.randint(y0 + 1, y1 - 1)
        t.set(x, y, SOUL[4] if k % 3 == 0 else SOUL[3])
        for dx, dy in t.rng.sample([(1, 0), (0, 1), (-1, 0), (0, -1)], t.rng.randint(1, 2)):
            if x0 < x + dx < x1 and y0 < y + dy < y1:
                t.set(x + dx, y + dy, SOUL[1] if dx + dy > 0 else SOUL[2])
    for _ in range(n // 2 + 1):
        x, y = t.rng.randint(x0 + 1, x1 - 2), t.rng.randint(y0 + 1, y1 - 1)
        t.set(x, y, SLATE[0])
        t.set(x + 1, y, SLATE[1])


def plate(t, x0=2, y0=2, x1=13, y1=13, base=3, glow=4):
    """The deepslate plate set INTO the casing (the frame shades its top/left edge, its bottom/right edge catches the
    light), grown over with sculk: glowing pores and dark clumps instead of seams and bolts."""
    grain(t, x0, y0, x1, y1, SLATE, base)
    for x in range(x0, x1 + 1):
        t.set(x, y0, SLATE[base - 2])
        t.set(x, y0 + 1, SLATE[base - 1]) if t.get(x, y0 + 1) == SLATE[base] else None
        t.set(x, y1, SLATE[base + 2])
    for y in range(y0, y1 + 1):
        t.set(x0, y, SLATE[base - 2])
        t.set(x1, y, SLATE[base + 2])
    pores(t, x0, y0, x1, y1, glow)


def ribs(t):
    """The sculk catalyst's side: bone ribs arching up from the bottom edge toward the middle (in bronze), a glowing
    pore cradled between them."""
    for side in (-1, 1):
        for i, (dx, y) in enumerate(((5, 13), (5, 12), (4, 11), (4, 10), (3, 9), (3, 8), (2, 7))):
            x = int(7.5 + side * dx + (0.5 if side > 0 else -0.5))
            t.set(x, y, PATINA[5 if side < 0 else 4])
            t.set(x - side, y, PATINA[3 if side < 0 else 2])
        t.set(int(7.5 + side * 2.5 + (0.5 if side > 0 else -0.5)), 6, PATINA[4])
    t.rect(7, 9, 8, 10, SOUL[3])
    t.set(7, 9, SOUL[4])


def casing(seed, base=3, rib=False, glow=4):
    t = Tex(seed)
    plate(t, base=base, glow=glow)
    if rib:
        ribs(t)
    frame(t)
    return t


def disc(t, cx, cy, r, pal, ring_every=2.0, hub=None, hub_r=0):
    """End-grain disc: concentric growth rings, lit from the top left; a rim one step darker."""
    for y in range(t.h):
        for x in range(t.w):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            light = -(dx + dy) / (r * 2.2)
            ring = int(d / ring_every) % 2
            idx = 3 + round(light * 2) - ring
            if d > r - 1:
                idx = 1 if dx + dy > 0 else 2
            t.set(x, y, pal[max(0, min(len(pal) - 1, idx))])
            if hub and d <= hub_r:
                hi = 4 + round(light * 2)
                t.set(x, y, hub[max(0, min(len(hub) - 1, hi))] if d < hub_r - 0.6 else hub[1])


def particle(name, frame_px=None):
    im = Image.open(io.BytesIO(JAR.read(f"assets/minecraft/textures/particle/{name}.png"))).convert("RGBA")
    return im


def stamp(t, sprite, ox, oy, remap=None, scale=1):
    """Paste a particle sprite onto the texture (opaque pixels only); pure white is toned down."""
    for y in range(sprite.height * scale):
        for x in range(sprite.width * scale):
            c = sprite.getpixel((x // scale, y // scale))
            if c[3] < 128:
                continue
            c = c[:3]
            if remap:
                c = remap.get(c, c)
            if c == (255, 255, 255):
                c = (220, 252, 244)
            t.set(ox + x, oy + y, c)


# ================================================================== textures
TEX = {}


def solid(t):
    """Machine models render as solid blocks: a transparent pixel would show as a hole (the side wheels looked cut).
    Fill every unpainted pixel from its nearest painted neighbour, one ring at a time."""
    while any(c is None for row in t.px for c in row):
        filled = []
        for y in range(t.h):
            for x in range(t.w):
                if t.px[y][x] is None:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                        c = t.get(x + dx, y + dy)
                        if c is not None:
                            filled.append((x, y, c))
                            break
        if not filled:
            break
        for x, y, c in filled:
            t.px[y][x] = c
    return t


def save(name, t):
    TEX[name] = solid(t).image() if isinstance(t, Tex) else t


# casing (shared look of the soul machines)
save("casing", casing(1, rib=True, glow=2))   # the catalyst look on every plain casing side
t = casing(2, base=2)
for y in range(5, 11):                      # top: a recessed square for whatever sits on it
    for x in range(5, 11):
        t.set(x, y, SLATE[1] if (x in (5, 10) or y in (5, 10)) else SLATE[2])
save("casing_top", t)

# ---------------------------------------------------------------- spirit engine
def engine_front(flame_frame=None, lit=False):
    t = casing(3)
    # firebox door: patina frame 4..11 x 6..12, grate bars, glow behind
    bevel(t, 3, 5, 12, 12, PATINA, 4, 1)
    t.rect(4, 6, 11, 11, SLATE[0])
    if lit and flame_frame is not None:
        stamp(t, flame_frame, 4, 4)
        for x in range(4, 12):
            t.set(x, 11, SOUL[2])
    for x in (5, 7, 9, 11):                 # grate bars
        for y in range(6, 12):
            t.set(x, y, PATINA[2] if y < 11 else PATINA[1])
    for x in range(4, 12):
        t.set(x, 6, PATINA[3])
    # nameplate slot above
    t.rect(5, 3, 10, 3, PATINA[2])
    t.set(5, 3, PATINA[4])
    return t


save("engine_front", engine_front())
flame = particle("soul_fire_flame")
frames = []
for i, (dx, dy) in enumerate(((0, 0), (0, -1), (1, 0), (0, 1))):
    f = engine_front(flame, lit=True)
    # flicker: shift the flame and lift the tip on alternate frames
    t2 = engine_front(None, lit=True)
    stamp(t2, flame, 4 + dx, 4 + dy)
    for x in (5, 7, 9, 11):
        for y in range(6, 12):
            t2.set(x, y, PATINA[2] if y < 11 else PATINA[1])
    for x in range(4, 12):
        t2.set(x, 6, PATINA[3])
    frames.append(t2.image())
sheet = Image.new("RGBA", (16, 64))
for i, f in enumerate(frames):
    sheet.paste(f, (0, i * 16))
save("engine_front_on", sheet)

t = casing(4)
for y in (4, 6, 8, 10):                     # louvre vents on the sides
    for x in range(4, 12):
        t.set(x, y, SLATE[0])
        t.set(x, y + 1, SLATE[5] if x < 11 else SLATE[4])
save("engine_side", t)
t = casing(5, base=2)
for y in range(4, 8):                       # exhaust grate where the chimney sits (back left)
    for x in range(3, 7):
        t.set(x, y + 6, SLATE[0] if (x + y) % 2 else SLATE[1])
save("engine_top", t)

# flywheel face: rim, four spokes, hub, a soul-crystal counterweight
t = Tex(6)
for y in range(16):
    for x in range(16):
        dx, dy = x - 7.5, y - 7.5
        d = math.hypot(dx, dy)
        light = -(dx + dy) / 12
        if 4.6 < d <= 6.2:
            t.set(x, y, SIFTITE[3 + round(light * 2)] if d < 5.9 else SIFTITE[1])
        elif d <= 4.6 and (abs(dx) < 1 or abs(dy) < 1):
            t.set(x, y, SIFTITE[4 + round(light * 2)])
        elif d <= 1.8:
            t.set(x, y, SIFTITE[5])
        elif d <= 4.6:
            t.set(x, y, SIFTITE[0])         # the deep web between the spokes
        else:
            t.set(x, y, SIFTITE[1] if dx + dy > 0 else SIFTITE[2])   # octagon corners outside the rim
for (x, y) in ((7, 2), (8, 2), (7, 3), (8, 3)):
    t.set(x, y, SOUL[3] if y == 2 else SOUL[2])
save("flywheel", t)
t = Tex(7)
grain(t, 0, 0, 15, 15, SIFTITE, 2)
for x in range(0, 16, 4):
    t.set(x, 7, SIFTITE[5])
    t.set(x, 8, SIFTITE[1])
save("flywheel_edge", t)

# ---------------------------------------------------------------- shaft and cogs
t = Tex(8)
grain(t, 0, 0, 15, 15, WOOD, 3, horizontal=False)
for x in range(16):
    t.set(x, 6, WOOD[4]); t.set(x, 9, WOOD[2])
for y in (0, 1, 14, 15):                    # patina bands at both ends
    for x in range(16):
        t.set(x, y, PATINA[3] if y in (0, 14) else PATINA[2])
for y in range(3, 13):                      # the soul groove that shows the turning
    t.set(7, y, SOUL[2] if y % 3 else SOUL[3])
save("shaft", t)
t = Tex(9)
grain(t, 0, 0, 15, 15, WOOD, 2)
for y in range(16):
    for x in range(16):
        d = math.hypot(x - 7.5, y - 7.5)
        if 1.2 < d < 2.2:
            t.set(x, y, PATINA[4] if x + y < 15 else PATINA[2])
        elif d <= 1.2:
            t.set(x, y, WOOD[1])
save("shaft_end", t)

t = Tex(10)
disc(t, 7.5, 7.5, 6.0, SIFTITE[:4], ring_every=1.6, hub=SIFTITE, hub_r=2.2)
save("cog_face", t)
t = Tex(11)
disc(t, 7.5, 7.5, 7.6, SIFTITE[:4], ring_every=1.8, hub=SIFTITE, hub_r=2.6)
save("large_cog_face", t)
t = Tex(12)
grain(t, 0, 0, 15, 15, SIFTITE, 2)
for x in range(16):
    t.set(x, 6, SIFTITE[4]); t.set(x, 9, SIFTITE[1])
save("cog_edge", t)
t = Tex(13)                                 # teeth: siftite bars one step brighter than the wheel, tips brightest
grain(t, 0, 0, 15, 15, SIFTITE, 4)
for i in range(16):
    t.set(i, 6, SIFTITE[5]); t.set(i, 9, SIFTITE[1])
    t.set(6, i, SIFTITE[5]); t.set(9, i, SIFTITE[1])
for i in (0, 1, 14, 15):
    for j in range(6, 10):
        t.set(i, j, SIFTITE[6] if i < 8 else SIFTITE[3])
        t.set(j, i, SIFTITE[6] if i < 8 else SIFTITE[3])
save("cog_tooth", t)

# ---------------------------------------------------------------- gauge
t = casing(14)
# a small round dial set in the casing plate (Create's gauge): bronze bezel, dark face, a thin coloured scale arc
# from the lower left (no load) over the top to the lower right (full); the red needle part turns over it
for y in range(16):
    for x in range(16):
        dx, dy = x - 7.5, y - 7.5
        d = math.hypot(dx, dy)
        lit = dx + dy < 0
        if d <= 4.4:
            t.set(x, y, SLATE[1] if d > 3.4 else SLATE[2] if lit else SLATE[1])
            phi = math.degrees(math.atan2(dx, -dy))       # clockwise from up
            if 3.2 < d <= 4.4 and -135 <= phi <= 135:
                load = (phi + 135) / 270
                t.set(x, y, (70, 142, 86) if load < 0.55 else (200, 166, 64) if load < 0.8 else (176, 58, 50))
        elif d <= 5.5:
            t.set(x, y, IRON[5] if d < 5.0 and lit else IRON[3] if d < 5.0 else IRON[1])
for (x, y) in ((4, 10), (11, 10)):          # end stops of the scale
    t.set(x, y, CREAM[3])
save("gauge_side", t)
t = Tex(15)                                 # needle: red with a lighter edge, brass hub
t.rect(0, 0, 15, 15, (150, 40, 36))
for i in range(16):
    t.set(i, 0, (204, 84, 70)); t.set(0, i, (204, 84, 70))
save("needle", t)

# ---------------------------------------------------------------- grinder and millstone
t = casing(16)
t.rect(5, 9, 10, 13, SLATE[0])              # the chute the ground stuff falls out of
bevel(t, 4, 8, 11, 13, PATINA, 4, 1)
for x in range(5, 11):
    t.set(x, 12, STONE[2] if x % 2 else STONE[1])
save("grinder_side", t)
t = Tex(17)
for y in range(16):
    for x in range(16):
        dx, dy = x - 7.5, y - 7.5
        d, a = math.hypot(dx, dy), math.degrees(math.atan2(dy, dx)) % 60
        light = -(dx + dy) / 14
        idx = 3 + round(light * 2)
        if a < 6 and d > 2.2:
            idx -= 2                        # six radial grooves (a real millstone's furrows)
        if d < 1.6:
            idx = 0                         # the eye
        t.set(x, y, STONE[max(0, min(5, idx))])
save("millstone_top", t)
t = Tex(18)
grain(t, 0, 0, 15, 15, STONE, 3)
for x in range(16):
    t.set(x, 10, STONE[1]); t.set(x, 11, STONE[4])
save("millstone_side", t)

# ---------------------------------------------------------------- soul sifter
t = Tex(19)
grain(t, 0, 0, 15, 15, WOOD, 3, horizontal=False)
for i in range(16):                         # a cross brace
    t.set(i, i, WOOD[1]); t.set(i, 15 - i, WOOD[1])
bevel(t, 0, 0, 15, 15, WOOD, 5, 1)
save("sifter_frame", t)
t = Tex(20)                                 # tray of red sculk granules in a bronze pan
for y in range(16):
    for x in range(16):
        t.set(x, y, RED[1])
for _ in range(24):
    x, y = t.rng.randint(1, 13), t.rng.randint(1, 13)
    t.set(x, y, RED[3]); t.set(x + 1, y, RED[2]); t.set(x, y + 1, RED[2])
    if t.rng.random() < 0.3:
        t.set(x, y, RED[4])
bevel(t, 0, 0, 15, 15, PATINA, 4, 1)
save("sifter_tray", t)
t = Tex(21)                                 # the sieve: a woven mesh in a willow frame
for y in range(16):
    for x in range(16):
        t.set(x, y, SLATE[1] if (x % 3 and y % 3) else WOOD[3 if (x + y) % 2 else 2])
bevel(t, 0, 0, 15, 15, WOOD, 5, 1)
save("sieve", t)

# ---------------------------------------------------------------- soul wave dishes, ring and core
def dish(seed, petal_pal, vein):
    t = Tex(seed)
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            d = math.hypot(dx, dy)
            if d > 7.2:
                continue
            a = math.degrees(math.atan2(dy, dx)) % 90
            light = -(dx + dy) / 14
            idx = 3 + round(light * 2)
            if abs(a - 45) < 8 and d > 2.5:
                idx -= 2                    # gaps between the four petals
            if d > 6.4:
                idx = 1
            t.set(x, y, petal_pal[max(0, min(len(petal_pal) - 1, idx))])
            if vein and d > 3 and (abs(dx) < 0.6 or abs(dy) < 0.6):
                t.set(x, y, SOUL[3])
            if d < 2.4:
                t.set(x, y, PATINA[2] if d > 1.4 else PATINA[1])
    return t


save("dish_emitter", dish(22, CHAROITE, False))
save("dish_receiver", dish(23, [(10, 30, 38), (16, 48, 58), (22, 70, 80), (34, 96, 104), (58, 130, 132), (100, 170, 160)], True))
t = Tex(24)
grain(t, 0, 0, 15, 15, PATINA, 3)
for i in range(16):
    t.set(i, 0, PATINA[5]); t.set(0, i, PATINA[5]); t.set(i, 15, PATINA[1]); t.set(15, i, PATINA[1])
save("ring", t)
t = Tex(25)                                 # soul crystal core: a sculk soul (particle) floating in crystal
for y in range(16):
    for x in range(16):
        t.set(x, y, SOUL[1] if (x + y) % 5 else SOUL[0])
stamp(t, particle("sculk_soul_5"), 0, 0, remap={(6, 14, 16): SOUL[0], (13, 18, 23): SOUL[0], (17, 27, 33): SOUL[1], (5, 42, 50): SOUL[1]})
for i in range(4, 12):
    t.set(i, 4 if i < 8 else 5, SOUL[4])
save("core", t)
t = casing(26, base=2)
save("wave_base_top", t)
t = casing(27)
for x in range(3, 13):                      # a band of sensor tendril slots
    t.set(x, 7, SOUL[1] if x % 2 else SLATE[0])
    t.set(x, 8, SLATE[0])
save("wave_base_side", t)

# ---------------------------------------------------------------- charoite: lens, beam housing, prism
def charoite(seed, facets=True):
    t = Tex(seed)
    for y in range(16):
        for x in range(16):
            swirl = math.sin((x * 0.7 + y * 0.35) + math.sin(y * 0.5) * 1.6)
            idx = 3 + round(swirl * 1.4) + (1 if x + y < 12 else 0) - (1 if x + y > 20 else 0)
            t.set(x, y, CHAROITE[max(0, min(6, idx))])
    if facets:
        for i in range(4):
            t.set(3 + i, 3, CHAROITE[6]); t.set(3, 3 + i, CHAROITE[5])
        t.set(11, 11, CHAROITE[5]); t.set(12, 11, CHAROITE[4])
    return t


save("lens", charoite(28))
t = charoite(29)
for x in range(16):                         # bronze band round the prism
    t.set(x, 7, PATINA[4]); t.set(x, 8, PATINA[2])
save("prism", t)
t = casing(30)
t.rect(6, 4, 9, 11, SLATE[0])               # a violet slit
for y in range(5, 11):
    t.set(7, y, CHAROITE[4]); t.set(8, y, CHAROITE[3])
save("beam_housing", t)
t = casing(31, base=2)
for y in range(16):
    for x in range(16):
        if 2.2 < math.hypot(x - 7.5, y - 7.5) < 3.4:
            t.set(x, y, CHAROITE[3])
save("beam_top", t)

# ---------------------------------------------------------------- soul vein node and soul-veined stone
def stone(seed):
    """Deepslate-like layered stone of our own: horizontal 3-4 px slabs with darker partings."""
    t = Tex(seed)
    for y in range(16):
        for x in range(16):
            t.set(x, y, SLATE[3])
    for y in (3, 7, 12):
        for x in range(16):
            if t.rng.random() < 0.8:
                t.set(x, y, SLATE[1])
    for _ in range(14):
        x, y = t.rng.randint(0, 15), t.rng.randint(0, 15)
        for i in range(t.rng.randint(2, 4)):
            if t.get((x + i) % 16, y) == SLATE[3]:
                t.set((x + i) % 16, y, SLATE[t.rng.choice((2, 4, 5))])
    return t


def vein(t, path, glow=True):
    for i, (x, y) in enumerate(path):
        t.set(x % 16, y % 16, SOUL[4] if i % 3 == 0 else SOUL[3])
    if glow:
        cs = {(x % 16, y % 16) for x, y in path}
        for x, y in cs:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = ((x + dx) % 16, (y + dy) % 16)
                if q not in cs and t.get(*q) in (SLATE[1], SLATE[2], SLATE[3], SLATE[4], SLATE[5]):
                    t.set(*q, SOUL[1])


VEIN = [(0, 5), (1, 5), (2, 6), (3, 6), (4, 6), (5, 7), (6, 7), (7, 8), (8, 8), (9, 8), (10, 7), (11, 6), (12, 6), (13, 5),
        (14, 5), (15, 5), (8, 9), (8, 10), (9, 11), (9, 12), (10, 13), (10, 14), (10, 15), (10, 0), (10, 1), (9, 2), (9, 3),
        (8, 4), (4, 7), (3, 8), (3, 9), (2, 10)]
t = stone(32)
vein(t, VEIN)
save("soul_veined_stone", t)
t = casing(33)
vein(t, [(4, 8), (5, 8), (6, 7), (7, 7), (8, 8), (9, 8), (10, 9), (11, 9), (7, 6), (7, 5), (8, 9), (8, 10)], glow=False)
save("vein_node_side", t)
t = casing(34, base=2)
for y in range(16):
    for x in range(16):
        if math.hypot(x - 7.5, y - 7.5) < 3:
            t.set(x, y, SOUL[1] if math.hypot(x - 7.5, y - 7.5) > 2 else SOUL[2])
save("vein_node_top", t)

# ---------------------------------------------------------------- pump and pipe
t = casing(35)
for y in range(4, 12):                      # a sight glass showing the spirit liquid level
    t.set(7, y, SOUL[2] if y > 6 else SLATE[0]); t.set(8, y, SOUL[1] if y > 6 else SLATE[0])
bevel(t, 6, 3, 9, 12, PATINA, 4, 1)
save("pump_side", t)
t = Tex(36)
for y in range(16):
    for x in range(16):
        d = math.hypot(x - 7.5, y - 7.5)
        t.set(x, y, SLATE[0] if d < 2.5 else PATINA[4 if x + y < 15 else 2] if d < 4 else PATINA[3])
save("pump_front", t)
t = Tex(37)
grain(t, 0, 0, 15, 15, PATINA, 3)
for x in range(16):                         # sheen along the pipe, two clamp bands
    t.set(x, 6, PATINA[5]); t.set(x, 10, PATINA[1])
for y in range(16):
    t.set(3, y, PATINA[1]); t.set(12, y, PATINA[1])
save("pipe", t)
t = Tex(38)
for y in range(16):
    for x in range(16):
        d = math.hypot(x - 7.5, y - 7.5)
        t.set(x, y, SOUL[1] if d < 1.8 else PATINA[2] if d < 2.8 else PATINA[3])
save("pipe_end", t)

# ---------------------------------------------------------------- hand crank
t = Tex(39)
grain(t, 0, 0, 15, 15, WOOD, 4, horizontal=False)
for y in range(16):
    t.set(0, y, WOOD[5]); t.set(15, y, WOOD[1])
save("crank", t)

# ---------------------------------------------------------------- clutch and gearshift
def shift(seed, on, arrows):
    t = casing(seed)
    lamp = LAMP_ON if on else LAMP_OFF
    t.rect(6, 3, 9, 5, lamp[1])
    t.set(6, 3, lamp[-1]); t.set(7, 3, lamp[-1] if on else lamp[2])
    bevel(t, 5, 2, 10, 6, PATINA, 4, 1)
    if arrows:                              # gearshift: two arrows pointing opposite ways
        for i in range(3):
            t.set(4 + i, 9 + i, PATINA[4]); t.set(4 + i, 11 - i + 2, PATINA[4])
            t.set(11 - i, 9 + i, PATINA[2]); t.set(11 - i, 11 - i + 2, PATINA[2])
    else:                                   # clutch: two plates with a gap
        t.rect(4, 9, 6, 12, PATINA[3]); t.rect(9, 9, 11, 12, PATINA[3])
        t.rect(4, 9, 6, 9, PATINA[5]); t.rect(9, 9, 11, 9, PATINA[5])
    return t


for n, arrows in (("clutch", False), ("gearshift", True)):
    save(n, shift(40 + arrows, False, arrows))
    save(n + "_on", shift(40 + arrows, True, arrows))
t = casing(42, base=2)
for y in range(16):
    for x in range(16):
        if math.hypot(x - 7.5, y - 7.5) < 2.6:
            t.set(x, y, SLATE[0])
save("shift_end", t)

# ---------------------------------------------------------------- fan
t = Tex(43)                                 # propeller blade
grain(t, 0, 0, 15, 15, PATINA, 4)
for i in range(16):
    t.set(i, 6, PATINA[6]); t.set(i, 9, PATINA[1])
save("fan_blade", t)
t = casing(44)
for y in range(3, 13):                      # a grille seen on the side walls
    if y % 2:
        for x in range(3, 13):
            t.set(x, y, SLATE[0])
save("fan_side", t)

# ---------------------------------------------------------------- drill
t = Tex(45)                                 # iron bit: broad spiral flutes, each with a lit edge and a shadowed groove
for y in range(16):
    for x in range(16):
        band = (x + y) % 8
        idx = 5 if band == 0 else 4 if band < 3 else 3 if band < 5 else 2 if band < 7 else 1
        t.set(x, y, IRON[idx])
save("drill_bit", t)
t = casing(46)
for x in range(4, 12):
    t.set(x, 4, IRON[4]); t.set(x, 5, IRON[2])
save("drill_side", t)

# ---------------------------------------------------------------- resonance core and pedestal
t = Tex(47)
grain(t, 0, 0, 15, 15, PATINA, 3)
bevel(t, 0, 0, 15, 15, PATINA, 5, 1)
for (x, y) in ((7, 3), (8, 3), (6, 5), (9, 5), (7, 7), (8, 7), (5, 9), (10, 9), (7, 11), (8, 11), (7, 12), (8, 12)):
    t.set(x, y, SOUL[3])                    # a rune of the eight notes
save("res_core_side", t)
t = Tex(48)
for y in range(16):
    for x in range(16):
        d = math.hypot(x - 7.5, y - 7.5)
        t.set(x, y, SOUL[2] if d < 3 else CHAROITE[2] if d < 4 else PATINA[3 if x + y > 14 else 4])
bevel(t, 0, 0, 15, 15, PATINA, 5, 1)
save("res_core_top", t)
t = Tex(49)
grain(t, 0, 0, 15, 15, SLATE, 3, horizontal=False)
for y in range(16):
    t.set(0, y, SLATE[5]); t.set(15, y, SLATE[1])
for y in (3, 12):
    for x in range(16):
        t.set(x, y, PATINA[4]); t.set(x, y + 1, PATINA[2])
save("pedestal_side", t)
t = Tex(50)
for y in range(16):
    for x in range(16):
        d = math.hypot(x - 7.5, y - 7.5)
        t.set(x, y, CHAROITE[3 if (x + y) % 3 else 4] if d < 4.5 else PATINA[3])
bevel(t, 0, 0, 15, 15, PATINA, 5, 1)
save("pedestal_top", t)

# soul conduit (three looks). The model's arms are 4 px thick and take their UVs from where they sit, so only the cross
# through the middle of the sheet is ever seen: rows 6..9 on arms that run sideways, columns 6..9 on upright ones, the
# 5 px knot in the centre on the core. Each band is a round vein (light on the upper / left edge, shadow on the other)
# with a brighter strand wandering along it and a pore every few pixels.
def conduit(seed, pal, pores):
    t = Tex(seed)
    n = len(pal)
    body, lit, shade, deep = pal[min(2, n - 1)], pal[min(3, n - 1)], pal[1], pal[0]
    t.rect(0, 0, 15, 15, deep)
    for i in range(16):
        strand = 7 if (i // 3 + seed) % 2 == 0 else 8             # the strand shifts one pixel every three
        for k, c in ((6, lit), (7, body), (8, body), (9, shade)):
            t.set(i, k, c)                                          # sideways band
            t.set(k, i, c)                                          # upright band
        t.set(i, strand, pal[min(4, n - 1)] if pores else lit)
        t.set(strand, i, pal[min(4, n - 1)] if pores else lit)
    for y in range(5, 11):                                          # the knot where arms meet
        for x in range(5, 11):
            edge = x in (5, 10) or y in (5, 10)
            t.set(x, y, shade if edge and (x + y) >= 16 else lit if edge else body)
    t.rect(7, 7, 8, 8, pal[min(4, n - 1)])
    if pores:
        for i in (1, 4, 11, 14):                                    # glowing pores along both bands
            t.set(i, 7 if i % 2 else 8, pal[-2])
            t.set(7 if i % 2 else 8, i, pal[-2])
        t.set(7, 7, pal[-1])
        t.set(8, 8, pal[-2])
    return t


save("conduit_soul", conduit(301, LIVE_SCULK, True))
save("conduit_plain", conduit(302, DEAD_SCULK, True))
save("conduit_off", conduit(303, HUSK, False))

# ---------------------------------------------------------------- soul redstone, stage two: note block, repeater, filter
# Material brief (minecraft-texture-crafter, step 0)
#   soul note block
#     identity    a Singer's instrument: a resonator box of stained soul willow in the machines' patina frame; the comb of
#                 siftite reeds on its sides is the octave (longest reed = lowest note), the top is a sound hole ringed by
#                 eight tuning pegs. Deep cool ambient light, shared dark = blue-black (SLATE[0]).
#     surfaces    willow panel: organic, soft, horizontal grain in 1x3..1x5 clusters; reeds and pegs: siftite, metal, high
#                 contrast with a bright top pixel; sound hole: 80 % dark, a small soul-light focus.
#     real world  a music box comb (steel reeds of stepped length), the sound hole and pegs of a lute.
#     anchor      block/note_block: a dark frame round a warm panel (frame 1 px there, our casing frame 2 px), panel
#                 detail in a regular rhythm. Only the proportions; palette, reeds and pegs are new.
#   soul repeater
#     identity    a check valve on a conduit: a patina sleeve clamped round the vein, two siftite chevrons showing the
#                 way the song flows. The vein is a dry husk when idle, living red sculk when a signal passes.
#     surfaces    sleeve: bronze, sheen along the axis; vein: organic, glowing pores (80/20); chevrons: bright metal.
#     real world  a brass check valve / pipe union with its cast flow arrow.
#     anchor      block/repeater: reads its direction at a glance. Structure is ours (a sleeve, not a slab).
#   soul filter
#     identity    a sight glass on a conduit: a patina cage round a charoite lens; the core behind the lens shows which
#                 signal it lets through - living red (soul) or dead blue (plain).
#     surfaces    lens: crystal, high contrast, a facet lit top-left and a reflection bottom-right; cage: bronze.
#     real world  an inline sight glass / strainer; Siberian charoite.
#     anchor      block/observer's framed aperture, our own casing frame.
def note_side():
    t = casing(310, base=2, glow=0)
    grain(t, 3, 3, 12, 12, WOOD, 3)
    for x in range(3, 13):                      # the panel sits in the frame: shadow under the top bar, light on the sill
        t.set(x, 3, WOOD[1])
        t.set(x, 12, WOOD[4])
    for y in range(3, 13):
        t.set(3, y, WOOD[1])
    # the comb: a bar across the top, four siftite reeds of stepped length hanging from it (lowest note on the left)
    t.rect(4, 4, 11, 4, SIFTITE[5])
    t.rect(4, 5, 11, 5, SIFTITE[2])
    t.set(11, 4, SIFTITE[3])
    for x, length in ((4, 6), (6, 5), (8, 3), (10, 2)):
        for y in range(6, 6 + length):
            t.set(x, y, SIFTITE[4])             # the reed's lit face
            t.set(x + 1, y, SIFTITE[1])         # and its shadowed edge
        t.set(x, 6, SIFTITE[6])
        t.set(x, 5 + length, SIFTITE[3])
    return t


def note_top():
    t = casing(311, base=2, glow=0)
    grain(t, 3, 3, 12, 12, WOOD, 3)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d < 2.9:                         # the sound hole, a soul light deep inside
                t.set(x, y, SLATE[0] if d > 1.2 else SOUL[2])
            elif d < 3.9:                       # its rim: lit on the far (bottom right) side, where light falls into it
                t.set(x, y, WOOD[5] if (x - 7.5) + (y - 7.5) > 1 else WOOD[1])
    t.set(7, 7, SOUL[4])
    for k in range(8):                          # eight tuning pegs round the hole: the eight notes
        a = math.radians(22.5 + 45 * k)
        x, y = round(7.5 + 5.0 * math.cos(a)), round(7.5 + 5.0 * math.sin(a))
        t.set(x, y, SIFTITE[5] if x + y < 15 else SIFTITE[3])
    return t


def repeater_side(vein):
    """Flow runs up the sheet (the model is built along +Y). Columns 4..11 are seen: sleeve, vein, chevrons."""
    t = Tex(320 + len(vein))
    grain(t, 0, 0, 15, 15, PATINA, 3, horizontal=False)
    for y in range(16):
        t.set(5, y, PATINA[5])                  # sheen along the sleeve's lit edge, shadow on the other
        t.set(10, y, PATINA[1])
        for x, c in ((7, vein[min(3, len(vein) - 1)]), (8, vein[1])):
            t.set(x, y, c)                      # the vein seen through the slot in the sleeve
    lit = len(vein) > 6
    for y in (2, 6, 10, 14):                    # pores of the vein (they only glow when it is alive)
        t.set(7, y, vein[-2] if lit else vein[min(4, len(vein) - 1)])
    for y0 in (4, 10):                          # two chevrons pointing with the flow
        for dx, dy in ((0, 0), (1, 1), (2, 2)):
            t.set(7 - dx - 0, y0 + dy, SIFTITE[5])
            t.set(8 + dx, y0 + dy, SIFTITE[3])
            t.set(7 - dx, y0 + dy + 1, SIFTITE[1])
            t.set(8 + dx, y0 + dy + 1, SIFTITE[1])
    for y, c in ((0, PATINA[6]), (1, PATINA[2]), (14, PATINA[5]), (15, PATINA[1])):   # the two clamps
        for x in range(4, 12):
            t.set(x, y, c)
    return t


def repeater_end():
    t = Tex(325)
    grain(t, 0, 0, 15, 15, PATINA, 3)
    bevel(t, 4, 4, 11, 11, PATINA, 5, 1)
    for y in range(6, 10):
        for x in range(6, 10):
            t.set(x, y, SLATE[1] if x + y > 15 else SLATE[0])
    t.rect(7, 7, 8, 8, LIVE_SCULK[2])
    t.set(7, 7, LIVE_SCULK[5])
    return t


def filter_face(core):
    """Seen from 3..12: a bronze cage (2 px), a charoite lens, and the core behind it (soul red / dead blue)."""
    t = Tex(330 + len(core) + core[0][0])
    grain(t, 0, 0, 15, 15, SLATE, 2)
    for i in (3, 4):
        bevel(t, i, i, 15 - i, 15 - i, PATINA, 5 if i == 3 else 3, 1 if i == 3 else 2)
    for y in range(5, 11):
        for x in range(5, 11):                  # the lens: a facet lit top-left, deep in the middle, a reflection bottom-right
            d = (x - 5) + (y - 5)
            t.set(x, y, CHAROITE[5] if d < 2 else CHAROITE[4] if d < 4 else CHAROITE[2] if d < 8 else CHAROITE[3])
    t.set(5, 5, CHAROITE[6])
    t.set(10, 10, CHAROITE[4])
    t.rect(6, 6, 9, 9, core[1])                 # the core that tells the mode: a 4 px bead of sculk behind the lens
    t.rect(6, 6, 8, 8, core[3])
    t.rect(7, 7, 8, 8, core[2])
    t.set(6, 6, core[-2])
    t.set(7, 6, core[-2])
    t.set(6, 7, core[4])
    return t


save("note_side", note_side())
save("note_top", note_top())
save("repeater_side", repeater_side(HUSK))
save("repeater_side_on", repeater_side(LIVE_SCULK))
save("repeater_end", repeater_end())
save("filter_soul", filter_face(LIVE_SCULK))
save("filter_plain", filter_face(DEAD_SCULK))

# ------------------------------------------------------------------ write
OUT.mkdir(parents=True, exist_ok=True)
for name, im in TEX.items():
    art_guard.save(im, OUT / f"{name}.png")
(OUT / "engine_front_on.png.mcmeta").write_text(json.dumps({"animation": {"frametime": 3, "interpolate": False}}, indent=2) + "\n",
                                                 encoding="utf-8")
# contact sheet for review (build/, not shipped)
names = list(TEX)
cols = 8
sheet = Image.new("RGBA", (cols * 80, ((len(names) + cols - 1) // cols) * 80), (36, 38, 46, 255))
for i, n in enumerate(names):
    im = TEX[n].crop((0, 0, 16, 16)).resize((64, 64), Image.NEAREST)
    sheet.alpha_composite(im, ((i % cols) * 80 + 8, (i // cols) * 80 + 8))
prev = P / "build/soul_power_preview"
prev.mkdir(parents=True, exist_ok=True)
sheet.save(prev / "textures.png")
print(f"{len(TEX)} soul power textures")


# ------------------------------------------------------------------ LabPBR maps (for Iris + a LabPBR shader pack)
# Vanilla ignores these. Every pixel's material is known from the palette its colour came from, so the maps follow the
# painting exactly: <name>_n.png (R,G normal in DirectX order, B ambient occlusion, A height) and <name>_s.png
# (R perceptual smoothness, G F0 or a predefined metal 230..254, B porosity 0..64 / subsurface 65..255, A emission
# 0..254, 255 = none). LabPBR 1.3.
MATERIALS = [   # (palette, smoothness, F0 or metal id, porosity/SSS, emissive?)
    (PATINA, 150, 234, 0, False),          # bronze: predefined copper
    (SIFTITE, 185, 231, 0, False),         # siftite: a bright metal (gold slot)
    (VERDIGRIS, 40, 12, 45, False),        # crusty verdigris
    (SLATE, 70, 10, 20, False),
    (WOOD, 80, 10, 35, False),
    (STONE, 35, 10, 55, False),
    (IRON, 175, 230, 0, False),            # predefined iron
    (CHAROITE, 215, 14, 0, False),
    (CREAM, 200, 11, 0, False),            # the gauge glass
    (RED, 100, 10, 140, True),             # red sculk: subsurface, faint glow
    (SOUL, 210, 20, 0, True),
    (LAMP_ON, 180, 12, 0, True),
    (LAMP_OFF, 120, 12, 0, False),
    (LIVE_SCULK, 110, 10, 150, True),      # living sculk vein: subsurface, glows
    (DEAD_SCULK, 90, 10, 90, True),        # dead sculk carrying a plain signal: only its pores glow
    (HUSK, 40, 10, 40, False),
]
LOOKUP = {}
for pal, smooth, f0, poro, glow in MATERIALS:
    for k, c in enumerate(pal):
        LOOKUP.setdefault(tuple(c[:3]), (smooth, f0, poro, glow, k / max(1, len(pal) - 1)))


def material(c):
    if c in LOOKUP:
        return LOOKUP[c]
    r, g, b = c                            # particle pixels and blends: bright cyan = soul light, else a plain surface
    if g > 120 and b > 120 and r < 160:
        return (210, 20, 0, True, min(1.0, (g + b) / 500))
    return (90, 10, 20, False, (r + g + b) / 765)


def pbr(im):
    w, h = im.size
    px = im.load()
    lum = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            lum[y][x] = (0.299 * r + 0.587 * g + 0.114 * b) / 255 if a else 0.0
    n = Image.new("RGBA", (w, h))
    sp = Image.new("RGBA", (w, h))
    tile = w                                # animated sheets: each frame wraps on its own
    for y in range(h):
        y0 = (y // tile) * tile
        for x in range(w):
            r, g, b, a = px[x, y]
            if not a:
                n.putpixel((x, y), (128, 128, 255, 0))
                sp.putpixel((x, y), (0, 0, 0, 255))
                continue
            ht = lum[y][x]
            hl = lum[y][(x - 1) % w]
            hr = lum[y][(x + 1) % w]
            hu = lum[y0 + (y - y0 - 1) % tile][x]
            hd = lum[y0 + (y - y0 + 1) % tile][x]
            dx, dy = (hl - hr) * 2.2, (hu - hd) * 2.2
            nz = 1.0
            ln = math.sqrt(dx * dx + dy * dy + nz * nz)
            nx, ny = dx / ln, -dy / ln      # DirectX: green points down
            ao = 255 - int(max(0.0, (sum((hl, hr, hu, hd)) / 4 - ht)) * 300)
            n.putpixel((x, y), (int((nx * 0.5 + 0.5) * 255), int((ny * 0.5 + 0.5) * 255), max(150, min(255, ao)),
                               max(1, min(255, int(40 + ht * 215)))))
            smooth, f0, poro, glow, rank = material((r, g, b))
            emit = 255
            if glow and rank > 0.45:
                emit = int(60 + rank * 180)
            sp.putpixel((x, y), (smooth, f0, poro, min(254, emit) if emit != 255 else 255))
    return n, sp


for name, im in TEX.items():
    nm, sm = pbr(im.convert("RGBA"))
    art_guard.save(nm, OUT / f"{name}_n.png")
    art_guard.save(sm, OUT / f"{name}_s.png")
for suffix in ("_n", "_s"):
    (OUT / f"engine_front_on{suffix}.png.mcmeta").write_text(
        json.dumps({"animation": {"frametime": 3, "interpolate": False}}, indent=2) + "\n", encoding="utf-8")
print(f"{len(TEX) * 2} LabPBR maps")
