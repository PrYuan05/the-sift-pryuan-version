"""Soul Caldera ground, redone from scratch (minecraft-texture-crafter skill): earth-ember caps, a warm caldera basalt,
an ochre breccia ore and a plum slate cut by one magma dyke.
Usage: python -I tools/worldgen/paint_caldera_earth.py <project> [--apply]

Without --apply only build/previews/caldera_earth_paint.png (tiles, 3x3 tilings, a ground and a cliff patchwork, greyscale)
and the single tiles in build/previews/caldera_earth/ are written. With --apply the textures go in through tools/art_guard.py,
the models / blockstates / glow template are rewritten and the replaced files are deleted (backed up first).

Every colour is sampled from the ORIGINAL textures, copied once to .texture_backups/caldera_earth_originals/ so a rerun never
samples its own output.

Material briefs
  ember_basalt - the caldera's own basalt: dense, matte, calm. Real: weathered Icelandic basalt stained by iron-rich
    volcanic soil. Sampled from the original umber void stone, pulled ~18 % towards the warm orange earth of the crimson
    capped ember stone's side. Vanilla anchor: deepslate / smooth_basalt (calm grain, few vesicles).
  warm_capped_ember_stone - warm volcanic earth (heat 4 of ember stone) lying over that basalt. Real: oxidised tephra soil
    over a lava field. Top: organic flowing cover on ~60 %; side: a 4-5 px earth layer hanging over the basalt (like the
    capped strata). Vanilla anchor: grass_block_side / podzol_side (a cap over the base).
  patina_ore (oxidation 0, was argent_ore) - hydrothermal breccia: ochre / amber mineral cement (most of the tile) holding rounded void stone clasts, a
    little malachite green against the clasts. Real: gossan-cemented breccia. Vanilla anchor: gravel / suspicious_gravel
    (rounded clasts in a matrix), not a stone with ore dots.
  magma_vein_slate (vein 0-3) - thick plum slate with faint bedding, cut by a single branching dyke: a hot
    white-yellow core, orange to orange-red flanks, a 1 px baked dark-rose rim on the slate. Real: a basaltic dyke through
    slate. Vanilla anchor: deepslate (calm plain face), magma_block (hot colours).
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
from paint_void_stone import Canvas, mottle, ALL, lum, palette as void_palette
import paint_void_stone as pvs
sys.path.insert(0, str(P / "tools/texture_pipeline"))
from chiseled_tops import smooth_top

C1, C2, C3, C4, C5, C6, C7 = range(7)
ORIG = P / ".texture_backups/caldera_earth_originals"
SOURCES = ["ember_stone/ember_stone_heat2_a.png", "warm_capped_ember_stone/warm_capped_ember_stone_top.png", "ember_stone/ember_stone_heat4.png", "crimson_capped_ember_stone/ember_stone_heat3_b.png",
           "ember_basalt/void_stone_a.png", "magma_vein_slate/magma_vein_slate_vein0_a.png",
           "magma_vein_slate/magma_vein_slate_vein2_a.png", "patina_ore/patina_ore_oxidation1.png"]


REFS = {"teal": "build/previews/teal_row2.png", "vcc": "build/previews/_vcc_wall.png"}   # user-chosen colour references


def originals():
    for k, r in REFS.items():                              # copied once with the originals: build/ can be cleaned
        if not (ORIG / "refs" / f"{k}.png").exists():
            (ORIG / "refs").mkdir(parents=True, exist_ok=True)
            shutil.copy2(P / r, ORIG / "refs" / f"{k}.png")
    if not (ORIG / SOURCES[0]).exists():
        for s in SOURCES:
            (ORIG / s).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(T / s, ORIG / s)
    out = {s: list(Image.open(ORIG / s).convert("RGB").get_flattened_data()) for s in SOURCES}
    for k in REFS:
        out[k] = list(Image.open(ORIG / "refs" / f"{k}.png").convert("RGB").get_flattened_data())
    return out


def hsv(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    return h * 360, s, v


def mean(rgbs):
    return tuple(sum(c[i] for c in rgbs) / len(rgbs) for i in range(3))


def at_lum(h, s, target):
    lo, hi = 0.0, 1.0
    for _ in range(40):
        v = (lo + hi) / 2
        rgb = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h % 360 / 360, min(0.9, s), v))
        lo, hi = (v, hi) if lum(rgb) < target else (lo, v)
    return rgb


def ladder(base, steps):
    """7 steps around a sampled base colour: (hue shift, saturation factor, luminance offset) each."""
    h, s, _ = hsv(base)
    l0 = lum(base)
    return [at_lum(h + dh, s * sf, l0 + dl) for dh, sf, dl in steps]


# ------------------------------------------------------------------------------------------------------------ palettes
def spirit_colours():
    from collections import Counter
    px = [c[:3] for c in Image.open(T / "fluid/spirit_liquid_still.png").convert("RGBA").get_flattened_data() if c[3]]
    px += [c[:3] for c in Image.open(T / "fluid/spirit_liquid_flow.png").convert("RGBA").get_flattened_data() if c[3]]
    common = [c for c, _ in Counter(px).most_common(60)]
    pick = lambda lo, hi: max((c for c in common if lo <= hsv(c)[0] <= hi and hsv(c)[1] > 0.3), key=lambda c: Counter(px)[c])
    pink, magenta, blue, cyan = pick(320, 340), pick(300, 315), pick(245, 265), pick(175, 190)
    return [at_lum(hsv(pink)[0], 0.16, 0.88), pink, magenta, blue, cyan]


def palettes():
    o = originals()
    heat4 = mean(o["ember_stone/ember_stone_heat4.png"])                          # warm earth, H~30
    side = o["crimson_capped_ember_stone/ember_stone_heat3_b.png"]
    orange = mean([c for c in side if 20 <= hsv(c)[0] <= 40])                     # the side's lower warm orange earth
    umber = mean([c for c in o["ember_basalt/void_stone_a.png"] if hsv(c)[1] > 0.05])   # its warm brown, not its grey
    burnt = tuple(u * 0.82 + r * 0.18 for u, r in zip(umber, orange))              # caldera basalt: umber pulled to the earth
    plum = mean(o["magma_vein_slate/magma_vein_slate_vein0_a.png"])
    vtop = [c for c in o["vcc"] if 250 <= hsv(c)[0] <= 300]                       # vcc wall upper band #64586d #5d5266 ...
    mauve = at_lum(hsv(mean(vtop))[0] + 8, hsv(mean(vtop))[1] * 1.55, lum(mean(vtop)) + 0.05)
    hot = o["magma_vein_slate/magma_vein_slate_vein2_a.png"]
    green = mean([c for c in o["patina_ore/patina_ore_oxidation1.png"] if 150 <= hsv(c)[0] <= 210])
    pal = {
        # lights warm (towards yellow), darks cool (towards plum-brown); span ~0.22 (matte basalt)
        "BASALT": ladder(burnt, [(16, 0.76, 0.150), (9, 0.90, 0.075), (4, 1.0, 0.034), (0, 1.0, 0.0), (-6, 1.04, -0.034),
                                 (-22, 1.10, -0.080), (-44, 1.18, -0.135)]),
        # earth: span ~0.24, darks to red-brown
        "EARTH": ladder(heat4, [(16, 0.66, 0.105), (10, 0.82, 0.060), (3, 0.96, 0.028), (0, 1.0, 0.0), (-6, 1.02, -0.032),
                                (-14, 1.0, -0.080), (-24, 1.0, -0.135)]),
        # plum slate: span ~0.22, lights towards rose, darks towards violet
        "SLATE": ladder(mauve, [(24, 0.70, 0.150), (14, 0.84, 0.070), (6, 0.95, 0.034), (0, 1.0, 0.0), (-6, 1.03, -0.034),
                               (-14, 1.08, -0.075), (-24, 1.14, -0.135)]),
        "GREEN": ladder(green, [(-12, 0.70, 0.13), (-6, 0.85, 0.07), (0, 1.0, 0.0), (6, 1.08, -0.06)]),
        # magma: sampled hot red of vein 2, a white-yellow and orange core above it, baked dark-rose rim below
        # user: not lava but spirit liquid (pink and blue): the fluid's own colours (its texture is not ours to repaint,
        # so it is read straight from the game folder) - a pale pink-white heart, pink, magenta, blue-violet, cyan glints
        "MAGMA": spirit_colours(),
        "COOLED": [],                                                              # filled below from MAGMA
    }
    h4 = sorted(set(o["ember_stone/ember_stone_heat4.png"]), key=lum, reverse=True)
    tan = [c for c in h4 if hsv(c)[0] >= 24]                                       # #b59763 #b58d55 #b3834e #b0784d
    salmon = [c for c in h4 if hsv(c)[0] < 24]                                     # #be7b60 #bc7159 #b86757 #aa6c4f
    # user: the earth is ember_stone_heat4 itself (its own 8 colours); only a lit step and two structural darks are added
    pal["HEAT4"] = [at_lum(40, 0.40, lum(tan[0]) + 0.045), *tan[:4], at_lum(16, 0.55, 0.455), at_lum(4, 0.52, 0.385),
                    salmon[0], salmon[1]]                                           # 7 / 8: heat4's salmon accents
    top = o["warm_capped_ember_stone/warm_capped_ember_stone_top.png"]
    teal = mean([c for c in top if 150 <= hsv(c)[0] <= 200])                       # the original top's teal (#42787b #417f6c)
    olive = mean([c for c in top if 50 <= hsv(c)[0] <= 90])                        # its olive (#7b7f61): the bridge to the earth
    from collections import Counter
    tr = [c for c, _ in Counter(o["teal"]).most_common(10)]                     # teal_row2: #54d2c4 #4acdc5 #48c4c7 ...
    tr = sorted(tr, key=lum, reverse=True)
    t_mid = tr[len(tr) // 2]
    bridge = tuple(round(a * 0.55 + b * 0.45) for a, b in zip(at_lum(hsv(t_mid)[0], 0.30, lum(t_mid) - 0.02), pal["HEAT4"][3]))
    pal["TEAL"] = [tr[0], tr[1], tr[3], tr[5], tr[7], tr[-1], at_lum(hsv(tr[-1])[0] + 8, 0.66, lum(tr[-1]) - 0.08), bridge]
    vcc = [c for c, _ in Counter(o["vcc"]).most_common(10) if hsv(c)[0] > 330 or hsv(c)[0] < 15]   # the rose lower part
    vcc = sorted(vcc, key=lum, reverse=True)                                        # #ad6e6e #ad6368 #a85b65 #9e5565
    pal["ROSEWALL"] = [at_lum(8, 0.30, lum(vcc[0]) + 0.045), *vcc[:4], at_lum(340, 0.46, lum(vcc[3]) - 0.05),
                       at_lum(328, 0.42, lum(vcc[3]) - 0.10)]
    # warm ash (gray-capped void stone) and the scorched crust (crimson-capped void stone, from the rift bed's reds)
    pal["ASH"] = ladder(at_lum(30, 0.16, 0.47), [(14, 0.7, 0.10), (8, 0.85, 0.055), (3, 0.95, 0.025), (0, 1, 0),
                                                 (-6, 1.05, -0.03), (-16, 1.1, -0.075), (-30, 1.15, -0.12)])
    reds = sorted(set(c for c in hot if hsv(c)[0] > 330 or hsv(c)[0] < 15), key=lum, reverse=True)
    sc = [at_lum(10, 0.42, lum(reds[0]) + 0.05)] + reds[:5] + [at_lum(330, 0.36, 0.22)]
    pal["SCORCH"] = pal["ROSEWALL"]
    rose = [c for c in hot if 335 <= hsv(c)[0] <= 352]
    pal["ROSE"] = sorted(set(rose), key=lum, reverse=True)                         # #994e58 #874f59 #77495a
    pal["VOID"] = void_palette()
    mg = hsv(pal["MAGMA"][2])[0]                                                   # vein 1: spirit that has set - faded
    pal["RIM"] = at_lum(hsv(pal["MAGMA"][3])[0] + 20, 0.42, 0.27)                   # baked deep violet rim of the spirit
    pal["COOLED"] = [at_lum(mg, 0.36, 0.50), at_lum(mg - 12, 0.34, 0.44), at_lum(mg - 26, 0.32, 0.38)]
    pal["BASALT"] = pal["HEAT4"][:7]                                                # user: one main colour, heat4
    return pal


PAL = palettes()


# ------------------------------------------------------------------------------------------------------------ helpers
def wrap(x, y): return x % 16, y % 16


def periodic_noise(seed, cells=(4, 8), weights=(1.0, 0.45)):
    """Tileable value noise on the 16 px torus (cosine-interpolated lattices of 4 and 8 cells)."""
    rnd = random.Random(seed)
    out = {p: 0.0 for p in ALL}
    for n, w in zip(cells, weights):
        g = [[rnd.random() for _ in range(n)] for _ in range(n)]
        step = 16 / n
        for x, y in ALL:
            fx, fy = x / step, y / step
            x0, y0 = int(fx), int(fy)
            tx, ty = (1 - math.cos(math.pi * (fx - x0))) / 2, (1 - math.cos(math.pi * (fy - y0))) / 2
            a, b = g[y0 % n][x0 % n], g[y0 % n][(x0 + 1) % n]
            c, d = g[(y0 + 1) % n][x0 % n], g[(y0 + 1) % n][(x0 + 1) % n]
            out[(x, y)] += w * ((a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty)
    return out


def threshold_mask(noise, frac):
    cut = sorted(noise.values(), reverse=True)[int(frac * 256) - 1]
    return {p for p, v in noise.items() if v >= cut}


def tidy(mask, passes=2):
    """No orphans: a cell with <= 1 same-kind 4-neighbours flips."""
    for _ in range(passes):
        flip = set()
        for x, y in ALL:
            inside = (x, y) in mask
            same = sum(((wrap(x + dx, y + dy) in mask) == inside) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if same <= 1:
                flip.add((x, y))
        mask ^= flip
    return mask


def render(layers):
    """layers: list of (canvas, palette, cells) - later layers win."""
    img = Image.new("RGB", (16, 16))
    for x, y in ALL:
        for c, pal, cells in layers:
            if cells is None or (x, y) in cells:
                img.putpixel((x, y), pal[c.get(x, y)])
    return img


# ------------------------------------------------------------------------------------------------------------ basalt
def basalt(seed, vesicles=2):
    """Calm warm basalt (like the calm dark slate): three micro steps woven in 2-4 px clusters, two soft curved shadow
    strokes (#5 / #6, lit #3 above) and a couple of small vesicles (#6 pit, #3 lower lip). Nothing louder than #2 / #6,
    no glyph-like marks."""
    rnd = random.Random(seed)
    c = Canvas()
    mottle(c, rnd, ALL, {C3: 4, C5: 5, C2: 1, C6: 1}, base_max=0.36)
    for _ in range(2):
        x, y = rnd.randrange(16), rnd.randrange(16)
        bend = rnd.choice((-1, 1))
        for i, (dx, dy) in enumerate(((0, 0), (1, 0), (2, bend), (3, bend))):
            c.set(x + dx, y + dy, C6 if i in (1, 2) else C5)
            c.set(x + dx, y + dy - 1, C3)
    for _ in range(vesicles):
        x, y = rnd.randrange(16), rnd.randrange(16)
        c.set(x, y, C6); c.set(x + 1, y, C6); c.set(x + 1, y + 1, C3)
    return c


def umber():
    return earth_rock("caldera earth rock").image(PAL["HEAT4"])


def earth_rock(seed):
    """ember_basalt (user): heat4's own colours with a calm, slightly earthy basalt grain so the earth and the rock
    under it read as one ground: woven tan micro steps, heat4's salmon in 2-3 px clusters, two soft curved shadow strokes
    and one small pit (#6 / #7) - no hard vesicles."""
    rnd = random.Random(seed)
    c = Canvas()
    mottle(c, rnd, ALL, {C3: 4, C5: 4, C2: 1, 7: 2, 8: 1}, base_max=0.34)
    for _ in range(2):
        x, y = rnd.randrange(16), rnd.randrange(16)
        bend = rnd.choice((-1, 1))
        for i, (dx, dy) in enumerate(((0, 0), (1, 0), (2, bend), (3, bend))):
            c.set(x + dx, y + dy, C6 if i in (1, 2) else 8)
            c.set(x + dx, y + dy - 1, C2)
    x, y = rnd.randrange(16), rnd.randrange(16)
    c.set(x, y, C7); c.set(x + 1, y, C6); c.set(x + 1, y + 1, C2)
    return c


def brick_family(stone, flecks=False, pal=None):
    """The ember stones' bricks (user: their derived blocks in the new earth colour): the void stone family's skeleton -
    four 4 px courses of 8 px bricks staggered by 4, the Stalker head on the chiseled bricks (skill rule for void stone) -
    painted in heat4's own colours; the speckled stone's bricks carry its pale 2 px flecks (never on the mortar), the
    chiseled ends are the smooth-style top in the same colours (chiseled_tops.smooth_top)."""
    rnd = random.Random(stone + " bricks")
    b = pvs.bricks(rnd)
    if flecks:
        for _ in range(7):
            x, y = rnd.randrange(16), rnd.randrange(16)
            if all(b.get(x + d, y) not in (C6, C7) for d in (0, 1)) and y % 4 not in (0, 3):
                b.set(x, y, C1); b.set(x + 1, y, C2)
    pal = pal or PAL["HEAT4"][:7]
    bricks = b.image(pal)
    chis = pvs.chiseled(random.Random(stone + " chiseled")).image(pal)
    d = f"{stone}_bricks"
    return {f"{d}/{d}": (bricks, None), f"{d}/chiseled_{d}": (chis, None),
            f"{d}/chiseled_{d}_top": (smooth_top(bricks, stone + " top"), None)}


def speckled():
    """ember_basalt's speckled texture: the same calm basalt, darker warm brown, with pale feldspar flecks (2 px)."""
    rnd = random.Random("caldera speckled")
    c = basalt("caldera speckled")
    for _ in range(6):
        x, y = rnd.randrange(16), rnd.randrange(16)
        c.set(x, y, C1); c.set(x + 1, y, C2)
    return c


# ------------------------------------------------------------------------------------------------------------ earth caps
def earth_grain(seed):
    c = Canvas()
    mottle(c, random.Random(seed), ALL, {C3: 5, C5: 4, C2: 1}, base_max=0.38)
    return c


def edge_shade(cover, under, c_cover, c_under, lit=C2, dim=C5, cast=C6, soft=C3):
    """Cover cells with nothing above get the lit step, with nothing left the softer lit step, with nothing below / right
    the dim step; uncovered cells right under the cover get a soft cast shadow (right of it only one step down)."""
    for x, y in ALL:
        if (x, y) in cover:
            if wrap(x, y - 1) not in cover:
                c_cover.set(x, y, lit)
            elif wrap(x - 1, y) not in cover:
                c_cover.set(x, y, soft)
            elif wrap(x, y + 1) not in cover or wrap(x + 1, y) not in cover:
                c_cover.set(x, y, dim)
        elif wrap(x, y - 1) in cover:
            c_under.set(x, y, cast)
        elif wrap(x - 1, y) in cover:
            c_under.set(x, y, C5)


def cap_top(seed, cover_pal, base, base_pal, frac, bridge=None):
    """A cover in organic patches on ~frac of a top (light lean to the rim so it wraps over the edge into the side's
    layer, but no picture frame), lit top edges, a softer left edge, the bottom / right edge in `bridge` (or dim), a soft
    cast shadow on the rock below."""
    noise = periodic_noise(seed, (2, 4, 8), (1.0, 0.7, 0.3))
    for (x, y) in ALL:
        rim = min(x, 15 - x, y, 15 - y)
        noise[(x, y)] += 0.12 if rim == 0 else 0.06 if rim == 1 else 0.0
    cover = tidy(threshold_mask(noise, frac))
    e = earth_grain(seed + " grain")
    edge_shade(cover, None, e, base, cast=C6)
    if bridge is not None:
        for x, y in ALL:
            if (x, y) in cover and (wrap(x, y + 1) not in cover or wrap(x + 1, y) not in cover) and wrap(x, y - 1) in cover:
                e.set(x, y, bridge)
    return render([(base, base_pal, None), (e, cover_pal, cover)])


def cap_side(seed, cover_pal, base, base_pal, depths=(4, 5), bridge=None):
    """A layer hanging over the rock: depths[0]-depths[1] px in lumps plus two drips 1-2 px lower, its lower edge in
    `bridge` (or dim), a 1 px soft shadow on the rock, lit 2 px clusters on the top rim. Painted upright (no vflip)."""
    rnd = random.Random(seed)
    lo, hi = depths
    depth = [lo + (hi > lo and x % 8 in (1, 2, 3, 5)) for x in range(16)]
    for x0 in (2, 10):
        depth[x0] += 1
        depth[x0 + 1] += rnd.choice((1, 2))
    rot = rnd.randrange(16)
    depth = depth[rot:] + depth[:rot]
    cover = {(x, y) for x in range(16) for y in range(depth[x])}
    e = earth_grain(seed + " grain")
    for x in range(16):
        e.set(x, depth[x] - 1, bridge if bridge is not None else C5 if depth[x] <= depth[(x + 1) % 16] else C6)
        base.set(x, depth[x], C6)
        if depth[(x - 1) % 16] < depth[x]:
            e.set(x, depth[(x - 1) % 16], C3)
    for x in range(0, 16, 5):
        e.set(x + rnd.randrange(2), 0, C2)
        e.set(x + 2, 0, C2)
    return render([(base, base_pal, None), (e, cover_pal, cover)])


def moss_top(): return cap_top("moss top", PAL["TEAL"], earth_rock("moss top rock"), PAL["HEAT4"], 0.60, bridge=7)
def moss_side(): return cap_side("moss side", PAL["TEAL"], earth_rock("moss side rock"), PAL["HEAT4"], bridge=7)
def ash_top(seed): return cap_top(seed, PAL["ASH"], speckled(), PAL["BASALT"], 0.70)
def ash_side(): return cap_side("ash side", PAL["ASH"], speckled(), PAL["BASALT"], depths=(3, 4))
def scorch_top(): return cap_top("scorch top c", PAL["SCORCH"], speckled(), PAL["BASALT"], 0.72)
def scorch_side(): return cap_side("scorch side", PAL["SCORCH"], speckled(), PAL["BASALT"], depths=(4, 5))


# ------------------------------------------------------------------------------------------------------------ ochre breccia
def breccia():
    rnd = random.Random("ochre breccia")
    clasts, tries = [], 0
    sizes = [(5, 4), (4, 4), (4, 3), (3, 3), (3, 2), (2, 2)]
    while len(clasts) < len(sizes) and tries < 500:            # rounded clasts, never touching (1 px of cement at least)
        tries += 1
        w, h = sizes[len(clasts)]
        x, y = rnd.randrange(16), rnd.randrange(16)
        cells = {wrap(x + i, y + j) for i in range(w) for j in range(h)
                 if not ((i in (0, w - 1)) and (j in (0, h - 1)) and w > 2 and h > 2)}   # cut the corners round
        halo = {wrap(a + dx, b + dy) for a, b in cells for dx in (-1, 0, 1, 2) for dy in (-1, 0, 1, 2)}
        if all(not (halo & c) for c in clasts):
            clasts.append(cells)
    rock = set().union(*clasts)
    m = Canvas()
    mottle(m, rnd, ALL, {C3: 4, C5: 5}, base_max=0.36)          # porous hot-mud cement
    for _ in range(9):                                          # pores: a dark 2 px pit with a lit lower-right lip
        x, y = rnd.randrange(16), rnd.randrange(16)
        if not ({wrap(x, y), wrap(x + 1, y), wrap(x + 1, y + 1)} & rock):
            m.set(x, y, C6); m.set(x + 1, y, C6); m.set(x + 1, y + 1, C3)
    v = Canvas()
    mottle(v, rnd, rock, {C3: 4, C5: 4}, base_max=0.4)
    edge_shade(rock, None, v, m, lit=C2, dim=C5, cast=C6)       # clasts: lit top-left, dim lower-right; settling shadow
    for x, y in ALL:                                            # cement lit where it wraps over a clast's top-left
        if (x, y) not in rock and (wrap(x + 1, y) in rock or wrap(x, y + 1) in rock) and m.get(x, y) != C6:
            m.set(x, y, C2)
    g = Canvas(C3)
    green = set()
    for cl in clasts[:4]:                                       # malachite crust against the clasts' lower edge
        edge = sorted(p for p in cl if wrap(p[0], p[1] + 1) not in rock)
        x, y = edge[len(edge) // 2]
        for i, (dx, dy) in enumerate(((0, 1), (1, 1), (-1, 1), (2, 1))[:rnd.randint(2, 4)]):   # a thin crust under it
            q = wrap(x + dx, y + dy)
            if q not in rock:
                green.add(q)
                g.set(*q, (C2, C3, C3, C4)[i])
    return render([(m, PAL["HEAT4"], None), (v, PAL["VOID"], rock), (g, PAL["GREEN"], green)]), rock, green


# ------------------------------------------------------------------------------------------------------------ plum slate
def slate(seed):
    """Thick plum slate: woven micro steps and 2-3 faint bedding planes (3-5 px flat clusters, lit above, dim below)."""
    rnd = random.Random(seed)
    c = Canvas()
    mottle(c, rnd, ALL, {C3: 4, C5: 5, C2: 1, C6: 1}, base_max=0.4)
    for k in range(3):                                         # inside the tile: variants meet without cut-off planes
        y = 2 + k * 5 + rnd.randrange(2)
        x = 1 + rnd.randrange(3)
        for seg in range(2):
            n = rnd.randint(3, 5)
            for i in range(n):
                if x + i <= 14:
                    c.set(x + i, y, C7 if i not in (0, n - 1) else C6)
                    c.set(x + i, y - 1, C2 if i not in (0, n - 1) else C3)
            x += n + rnd.randint(2, 4)
            y += rnd.choice((-1, 1))
    return c


DYKE_X = 7                                                     # every dyke enters / leaves at columns 6..9
SILL_Y = 7                                                     # every sill leaves the left / right edge at rows 7..8


def dyke(seed, branches=1):
    """One thick dyke through the whole tile (wraps top to bottom): a centre line, 3 px wide, plus branches 2 px wide.
    Returns (centre cells, flank cells, right flank cells)."""
    rnd = random.Random(seed)
    steps = [0] * 6 + [1] * 5 + [-1] * 5
    while True:                                                # a walk that stays within +-3 px of the entry column
        rnd.shuffle(steps)
        walk = [sum(steps[:i]) for i in range(17)]
        if max(map(abs, walk)) <= 3:
            break
    x = DYKE_X
    centre, flank, right = set(), set(), set()
    for y in range(16):
        centre.add(wrap(x, y)); centre.add(wrap(x + 1, y))
        flank.add(wrap(x - 1, y)); right.add(wrap(x + 2, y))
        if steps[y]:                                           # keep the walk connected on jogs
            centre.add(wrap(x + steps[y], y)); centre.add(wrap(x + 1 + steps[y], y))
        x += steps[y]
    # the branch (user: the left / right sides must join too) is a sill across the whole tile: it leaves the left and
    # right edges at rows SILL_Y..SILL_Y+1 in every variant, so dykes beside each other join into one network; in between
    # it bows up or down by a pixel or two (each variant its own way)
    bow = [0] * 16
    for x0, x1, d in ((rnd.randrange(1, 3), rnd.randrange(13, 15), rnd.choice((-1, 1))),):
        for xx in range(x0, x1 + 1):
            bow[xx] = d * (2 if x0 + 2 <= xx <= x1 - 2 else 1)
    for xx in range(16):
        y = SILL_Y + bow[xx]
        if (xx, y) in centre or (xx, y + 1) in centre:
            continue
        flank.add((xx, y))                                     # lit upper row
        right.add((xx, y + 1))                                 # darker lower row
        if bow[xx] != bow[xx - 1] and xx:                      # keep the steps connected
            right.add((xx, SILL_Y + bow[xx - 1] + 1))
    flank -= centre
    right -= centre | flank
    right -= {p for p in right if p[1] in (0, 15)}             # 1 px narrower at the edges: under plain slate it tapers
    return centre, flank, right


def magma_slate(level, seed, branches=1):
    s = slate(seed + " slate")
    img = s.image(PAL["SLATE"])
    glow = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    if level == 0:
        return img, None
    centre, flank, right = dyke(seed, branches)
    crack = centre | flank | right
    hot, rose = PAL["MAGMA"], PAL["ROSE"]
    for x, y in ALL:                                           # 1 px baked dark-rose rim on the slate
        if (x, y) not in crack and any(wrap(x + dx, y + dy) in crack for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            img.putpixel((x, y), PAL["RIM"] if level == 2 else PAL["SLATE"][C6])
    for p in crack:
        if level == 2:
            col = hot[2] if p in flank else hot[3]
            if p in centre:                                    # white-yellow heart, yellow-orange where it touches the walls
                col = hot[0] if wrap(p[0] - 1, p[1]) in centre or wrap(p[0] + 1, p[1]) not in centre and                     wrap(p[0], p[1] - 1) in centre else hot[1]
        else:
            col = PAL["COOLED"][0] if p in centre else PAL["COOLED"][1] if p in flank else PAL["COOLED"][2]
        img.putpixel(p, col)
        if level == 2:
            glow.putpixel(p, (*col, 255))
    return img, (glow if level == 2 else None)


def intruded(seed="rift"):
    """magma vein slate vein 3 (user): fully intruded - the face is magma (orange-red ground, orange, yellow and white-yellow
    channels by a tileable noise) with a few rounded plum slate remnants, each with a 1 px baked dark-rose rim."""
    hot, rose = PAL["MAGMA"], PAL["ROSE"]
    n = periodic_noise(seed + " magma", (4, 8), (1.0, 0.5))
    lean = {(x, y): -v - 0.55 * (1 - min(x, 15 - x) / 7.5) ** 2 * -1 for (x, y), v in
            periodic_noise(seed + " islands", (4, 8), (1.0, 0.4)).items()}       # slate leans to the side edges
    islands = tidy(threshold_mask(lean, 0.14))                    # user: the full state fuller - few remnants
    islands -= {(x, y) for x in range(DYKE_X - 2, DYKE_X + 4) for y in range(16)}   # the river's middle stays molten
    islands -= {(x, y) for x in range(16) for y in range(SILL_Y - 1, SILL_Y + 3)}     # and the sill rows: left / right join
    heat = lambda x, y: n[(x, y)] + (0.35 if DYKE_X - 1 <= x <= DYKE_X + 2 else 0.12 if SILL_Y <= y <= SILL_Y + 1 else 0.0)
    order = sorted((heat(x, y) for (x, y) in n), reverse=True)
    cut = lambda f: order[int(f * 256) - 1]
    s_ = slate("rift remnants").image(PAL["SLATE"])
    img, glow = Image.new("RGB", (16, 16)), Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for x, y in ALL:
        if (x, y) in islands:
            img.putpixel((x, y), s_.getpixel((x, y)))
            continue
        if any(wrap(x + dx, y + dy) in islands for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            img.putpixel((x, y), PAL["RIM"])
            continue
        v = heat(x, y)                                         # hottest along the dyke columns and the sill rows
        col = (hot[0] if v >= cut(0.08) else hot[4] if v >= cut(0.12) else hot[1] if v >= cut(0.36) else hot[2]
               if v >= cut(0.64) else hot[3])                  # pale heart, cyan glints round it, pink, magenta, blue
        img.putpixel((x, y), col)
        glow.putpixel((x, y), (*col, 255))
    return img, glow


def rose_swap(pixels, keep=lambda c: False):
    """Same picture, its pink pixels re-coloured by luminance rank onto the vcc rose (5 lightest steps)."""
    pinks = sorted({c for c in pixels if not keep(c) and (hsv(c)[0] > 320 or hsv(c)[0] < 10)}, key=lum, reverse=True)
    rose = PAL["ROSEWALL"]
    m = {c: rose[min(len(rose) - 1, round(i * 5 / max(1, len(pinks) - 1)))] for i, c in enumerate(pinks)}
    img = Image.new("RGB", (16, 16))
    img.putdata([m.get(c, c) for c in pixels])
    return img


def crimson_cap_top(): return rose_swap(originals()["ember_stone/ember_stone_heat2_a.png"])
def crimson_cap_side(): return rose_swap(originals()["crimson_capped_ember_stone/ember_stone_heat3_b.png"])


# new names: the old magma_vein_slate_vein*_x pictures stay for the blocks that share them (violet strata caps, slabs)
MAGMA_VARIANTS = {lv: [f"magma_vein_slate_dyke{lv}_{v}" for v in "abc"] for lv in range(4)}


def textures():
    out = {}
    out["ember_basalt/ember_basalt"] = (umber(), None)
    out["warm_capped_ember_stone/warm_capped_ember_stone_top"] = (moss_top(), None)
    out["warm_capped_ember_stone/warm_capped_ember_stone_side"] = (moss_side(), None)
    out["crimson_capped_ember_stone/crimson_capped_ember_stone_top"] = (crimson_cap_top(), None)
    out["crimson_capped_ember_stone/crimson_capped_ember_stone_side"] = (crimson_cap_side(), None)
    out["ember_basalt/ember_basalt_speckled"] = (speckled().image(PAL["BASALT"]), None)
    out.update(brick_family("ember_basalt"))
    out.update(brick_family("magma_vein_slate", pal=PAL["SLATE"]))   # user: the slate's bricks in its new grape-mauve
    out["gray_capped_void_stone/gray_capped_ember_stone_top_a"] = (ash_top("ash top a"), None)
    out["gray_capped_void_stone/gray_capped_ember_stone_top_b"] = (ash_top("ash top b"), None)
    out["gray_capped_void_stone/gray_capped_ember_stone_side"] = (ash_side(), None)
    out["crimson_capped_void_stone/crimson_capped_ember_stone_top"] = (scorch_top(), None)
    out["crimson_capped_void_stone/crimson_capped_ember_stone_side"] = (scorch_side(), None)
    out["patina_ore/patina_ore_oxidation0"] = (breccia()[0], None)
    for lv, names in MAGMA_VARIANTS.items():
        for n in names:
            out[f"magma_vein_slate/{n}"] = intruded(n) if lv == 3 else magma_slate(lv, n)
    return out


# ------------------------------------------------------------------------------------------------------------ preview
def tile3(img):
    t = Image.new("RGB", (48, 48))
    for a in range(3):
        for b in range(3):
            t.paste(img, (a * 16, b * 16))
    return t


def preview(tex):
    o = {k: Image.open(ORIG / k).convert("RGB") for k in SOURCES}
    crimson_top = tex["crimson_capped_ember_stone/crimson_capped_ember_stone_top"][0]
    crimson_side = tex["crimson_capped_ember_stone/crimson_capped_ember_stone_side"][0].transpose(Image.FLIP_TOP_BOTTOM)
    g = lambda k: tex[k][0]
    U, ET, ES, ORE = (g("ember_basalt/ember_basalt"), g("warm_capped_ember_stone/warm_capped_ember_stone_top"),
                      g("warm_capped_ember_stone/warm_capped_ember_stone_side"), g("patina_ore/patina_ore_oxidation0"))
    # ground patchwork seen from above: basalt, earth caps, crimson caps, a little ore
    rnd = random.Random("field")
    field = Image.new("RGB", (16 * 10, 16 * 6))
    for i in range(10):
        for j in range(6):
            r = rnd.random()
            field.paste(ET if r < 0.45 else U if r < 0.75 else crimson_top if r < 0.94 else ORE, (i * 16, j * 16))
    # cliff: caps on top, basalt, then the rift wall (slate vein 0 -> 2), the rift bed, ore pockets
    cliff = Image.new("RGB", (16 * 10, 16 * 7))
    for i in range(10):
        cliff.paste(ES if i % 3 else crimson_side, (i * 16, 0))
        cliff.paste(U, (i * 16, 16))
        for j, lv in enumerate((0, 0, 1, 2)):
            cliff.paste(g(f"magma_vein_slate/{MAGMA_VARIANTS[lv][(i + j) % 3]}"), (i * 16, (2 + j) * 16))
        cliff.paste(ORE if i in (2, 7) else U, (i * 16, 96 if i % 2 else 16 * 6))
        cliff.paste(g(f"magma_vein_slate/{MAGMA_VARIANTS[3][i % 3]}"), (i * 16, 96))   # the rift bed: vein 3
    for i in (2, 7):
        cliff.paste(ORE, (i * 16, 48))
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 12)
    keys = list(tex)
    cols, S = 5, 64
    rows = (len(keys) + cols - 1) // cols
    W = 12 + cols * (S + 4 + 3 * 48 // 1 + 16)
    W = max(W, 12 + 2 * (160 * 3 + 20))
    H = 30 + rows * (S + 34) + 7 * 16 * 3 + 60
    sheet = Image.new("RGB", (W, H), (28, 27, 32))
    d = ImageDraw.Draw(sheet)
    d.text((10, 6), "靈魂火山口重製：每格 單張｜3×3 平鋪；下方：地表拼貼（俯視）、崖壁拼貼、崖壁灰階", fill=(240, 230, 205), font=f)
    for i, k in enumerate(keys):
        x, y = 10 + (i % cols) * (S + 164), 30 + (i // cols) * (S + 34)
        sheet.paste(tex[k][0].resize((S, S), Image.NEAREST), (x, y))
        sheet.paste(tile3(tex[k][0]).resize((144, 144), Image.NEAREST).crop((0, 0, 144, S)), (x + S + 4, y))
        d.text((x, y + S + 2), k.split("/")[1], fill=(200, 205, 215), font=f)
    y0 = 30 + rows * (S + 34) + 6
    sheet.paste(field.resize((field.width * 3, field.height * 3), Image.NEAREST), (10, y0))
    sheet.paste(cliff.resize((cliff.width * 3, cliff.height * 3), Image.NEAREST), (10 + 480 + 20, y0))
    gray = cliff.convert("L").convert("RGB")
    sheet.paste(gray.resize((gray.width * 2, gray.height * 2), Image.NEAREST), (10, y0 + 6 * 48 + 10))
    out = P / "build/previews/caldera_earth_paint.png"
    sheet.save(out)
    tmp = P / "build/previews/caldera_earth"                  # <block folder>/<texture>.png, as in the game (two blocks
    if tmp.exists():                                           # have a crimson_capped_ember_stone_top of their own)
        shutil.rmtree(tmp)
    for k, (img, glow) in tex.items():
        (tmp / k).parent.mkdir(parents=True, exist_ok=True)
        img.save(tmp / f"{k}.png")
        if glow:
            glow.save(tmp / f"{k}_glow.png")
    print("preview:", out.relative_to(P))


# ------------------------------------------------------------------------------------------------------------ apply
def wj(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def glow_template():
    faces = lambda tex, cull: {f: {"uv": [0, 0, 16, 16], "texture": tex, **({"cullface": f} if cull else {})}
                               for f in ("down", "up", "north", "south", "west", "east")}
    return {"parent": "minecraft:block/block", "render_type": "cutout", "textures": {"particle": "#all"},
            "elements": [{"from": [0, 0, 0], "to": [16, 16, 16], "faces": faces("#all", True)},
                         {"from": [0, 0, 0], "to": [16, 16, 16], "shade": False, "light_emission": 15,
                          "faces": faces("#glow", True)}]}


def apply(tex):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bk = P / ".texture_backups" / f"{stamp}_paint_caldera_earth"
    old = [T / "warm_capped_ember_stone/ember_stone_heat3_c.png", T / "crimson_capped_ember_stone/ember_stone_heat3_b.png", T / "gray_capped_void_stone/void_stone_i.png",
           T / "crimson_capped_void_stone/crimson_capped_void_stone_bottom.png",
           # user: the earth-coloured void stone textures are named *_ember_stone now; the old files go
           T / "ember_basalt/void_stone_a.png", T / "crimson_capped_void_stone/crimson_capped_void_stone_top.png",
           T / "crimson_capped_void_stone/crimson_capped_void_stone_side.png"]
    speckled_models = [p for d in ("speckled_ember_stone", "speckled_ember_stone_slab", "speckled_ember_stone_stairs",
                                   "speckled_ember_stone_wall") for p in (A / "models/block" / d).glob("*.json")]
    # umber void stone and its slab / stairs / wall / item point at the renamed texture
    speckled_models += [p for d in ("ember_basalt", "ember_basalt_slab", "ember_basalt_stairs",
                                    "ember_basalt_wall") for p in (A / "models/block" / d).glob("*.json")]
    speckled_models += [A / "models/item/ember_basalt.json"]
    # the old magma vein slate pictures go only when nothing else uses them: crimson_capped_violet_strata (violet slate
    # abyss) and the slate's own slab / stairs / wall keep theirs
    others = " ".join(q.read_text(encoding="utf-8") for q in (A / "models").rglob("*.json")
                      if q.parent.name != "magma_vein_slate")
    old += [p for p in (T / "magma_vein_slate").glob("magma_vein_slate_vein*.png")
            if f'"pysift:block/magma_vein_slate/{p.stem}"' not in others]
    # the same for the old models: the slab's double-slab state uses the slate's own vein 0 models
    users = others + " ".join(q.read_text(encoding="utf-8") for q in (A / "blockstates").glob("*.json")
                              if q.name != "magma_vein_slate.json")
    old += [p for p in (A / "models/block/magma_vein_slate").glob("magma_vein_slate_vein*.json")
            if f'"pysift:block/magma_vein_slate/{p.stem}"' not in users]
    for p in [T / f"{k}.png" for k in tex] + old + speckled_models + [A / "blockstates/magma_vein_slate.json",
                                                    A / "blockstates/warm_capped_ember_stone.json",
                                                    A / "models/block/crimson_capped_ember_stone/crimson_capped_ember_stone_1.json",
                                                    A / "models/block/gray_capped_void_stone/gray_capped_void_stone_1.json",
                                                    A / "models/block/gray_capped_void_stone/gray_capped_void_stone_2.json",
                                                    A / "models/block/crimson_capped_void_stone/crimson_capped_void_stone.json",
                                                    A / "models/block/warm_capped_ember_stone/warm_capped_ember_stone_1.json"]:
        if p.exists():
            dst = bk / p.relative_to(P)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
    # user (2026-10-31): the textures as they are now are final - nothing that exists is rewritten or deleted any more;
    # only missing files are added. --unfreeze lifts this for a deliberate repaint.
    if "--unfreeze" not in sys.argv:
        for k, (img, glow) in tex.items():
            for dst, im in ((T / f"{k}.png", img), (T / f"{k}_glow.png", glow)):
                if im is not None and not dst.exists():
                    art_guard.save(im, dst)
                    print("  added (was missing):", dst.relative_to(P))
        print("textures frozen: existing pictures kept as they are (models / blockstates below are still written)")
        old = [p for p in old if p.suffix != ".png"]
        tex = {}
    for p in old:
        if p.exists():
            p.unlink()
    for k, (img, glow) in tex.items():
        dst = T / f"{k}.png"
        # a texture the user repainted by hand is kept (art_guard); --force replaces it anyway. Its glow layer is then
        # the user's own hot pixels, not this script's, so the glow stays aligned with the painting.
        if dst.exists() and not art_guard.is_ours(dst) and "--force" not in sys.argv:
            print("  kept (edited by the user):", dst.relative_to(P))
            if glow:
                own = Image.open(dst).convert("RGBA")
                glow = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
                for x, y in ALL:
                    c = own.getpixel((x, y))
                    if colorsys.rgb_to_hsv(*(t / 255 for t in c[:3]))[2] >= 0.65:
                        glow.putpixel((x, y), (*c[:3], 255))
        else:
            if dst.exists() and not art_guard.is_ours(dst):
                dst.unlink()
            art_guard.save(img, dst)
        if glow:
            g = T / f"{k}_glow.png"
            if g.exists() and not art_guard.is_ours(g):
                g.unlink()
            art_guard.save(glow, g)
    M = A / "models/block"
    wj(M / "templates/cube_all_glow.json", glow_template())
    for lv, names in MAGMA_VARIANTS.items():
        for n in names:
            wj(M / f"magma_vein_slate/{n}.json",
               {"parent": "pysift:block/templates/cube_all_glow",
                "textures": {"all": f"pysift:block/magma_vein_slate/{n}", "glow": f"pysift:block/magma_vein_slate/{n}_glow"}}
               if lv >= 2 else {"parent": "minecraft:block/cube_all", "textures": {"all": f"pysift:block/magma_vein_slate/{n}"}})
    wj(A / "blockstates/magma_vein_slate.json", {"variants": {
        f"vein={lv}": [{"model": f"pysift:block/magma_vein_slate/{n}", "weight": 1} for n in names]
        for lv, names in MAGMA_VARIANTS.items()}})
    it = A / "items/magma_vein_slate.json"                         # the item shows the first variant of each vein level
    data = json.loads(it.read_text(encoding="utf-8"))
    data["model"]["cases"] = [{"model": {"type": "minecraft:model", "model": f"pysift:block/magma_vein_slate/{names[0]}"},
                               "when": str(lv)} for lv, names in MAGMA_VARIANTS.items()]
    wj(it, data)
    # the new side is painted upright (earth layer at the top of the png), so no vflip template
    wj(M / "warm_capped_ember_stone/warm_capped_ember_stone_1.json",
       {"parent": "minecraft:block/cube_bottom_top",
        "textures": {"top": "pysift:block/warm_capped_ember_stone/warm_capped_ember_stone_top",
                     "bottom": "pysift:block/ember_basalt/ember_basalt",
                     "side": "pysift:block/warm_capped_ember_stone/warm_capped_ember_stone_side"}})
    # speckled void stone and its slab / stairs / wall: its own texture now (void_stone_g is shared with the violet strata)
    for p in speckled_models:
        p.write_text(p.read_text(encoding="utf-8")
                     .replace("pysift:block/void_stone/void_stone_g", "pysift:block/speckled_ember_stone/speckled_ember_stone")
                     .replace("pysift:block/ember_basalt/void_stone_a", "pysift:block/ember_basalt/ember_basalt"),
                     encoding="utf-8")
    SPECK = "pysift:block/ember_basalt/ember_basalt_speckled"
    # ember_basalt (user: umber + speckled merged): two random textures, plain and speckled; the item shows the plain one
    for n in ("ember_basalt", "ember_basalt_speckled"):
        wj(M / f"ember_basalt/{n}.json", {"parent": "minecraft:block/cube_all", "textures": {"all": f"pysift:block/ember_basalt/{n}"}})
    wj(A / "blockstates/ember_basalt.json", {"variants": {"": [{"model": "pysift:block/ember_basalt/ember_basalt", "weight": 3},
                                                              {"model": "pysift:block/ember_basalt/ember_basalt_speckled", "weight": 2}]}})
    old_model = M / "ember_basalt/void_stone_a.json"
    if old_model.exists():
        old_model.unlink()
    for q in [*(A / "models").rglob("*.json"), *(A / "items").glob("*.json"), *(A / "blockstates").glob("*.json")]:   # everything that used it
        t = q.read_text(encoding="utf-8")
        if "pysift:block/ember_basalt/void_stone_a" in t:
            q.write_text(t.replace("pysift:block/ember_basalt/void_stone_a", "pysift:block/ember_basalt/ember_basalt"), encoding="utf-8")
    for i, v in ((1, "a"), (2, "b")):
        wj(M / f"gray_capped_void_stone/gray_capped_void_stone_{i}.json",
           {"parent": "minecraft:block/cube_bottom_top",
            "textures": {"top": f"pysift:block/gray_capped_void_stone/gray_capped_ember_stone_top_{v}", "bottom": SPECK,
                         "side": "pysift:block/gray_capped_void_stone/gray_capped_ember_stone_side"}})
    wj(M / "crimson_capped_void_stone/crimson_capped_void_stone.json",
       {"parent": "minecraft:block/cube_bottom_top",
        "textures": {"top": "pysift:block/crimson_capped_void_stone/crimson_capped_ember_stone_top", "bottom": SPECK,
                     "side": "pysift:block/crimson_capped_void_stone/crimson_capped_ember_stone_side"}})
    cm = M / "crimson_capped_ember_stone/crimson_capped_ember_stone_1.json"        # still v-flipped like the original side
    data = json.loads(cm.read_text(encoding="utf-8"))
    data["textures"]["top"] = "pysift:block/crimson_capped_ember_stone/crimson_capped_ember_stone_top"
    data["textures"]["side"] = "pysift:block/crimson_capped_ember_stone/crimson_capped_ember_stone_side"
    wj(cm, data)
    bs = A / "blockstates/warm_capped_ember_stone.json"            # facing=up: the top in four turns
    data = json.loads(bs.read_text(encoding="utf-8"))
    m = data["variants"]["facing=up"][0]["model"]
    data["variants"]["facing=up"] = [{"model": m, "weight": 1, **({"y": r} if r else {})} for r in (0, 90, 180, 270)]
    wj(bs, data)
    man = P / "tools/texture_pipeline/recolor_manifest.json"          # hand-painted now: not the recolor pipeline's
    if man.exists():
        data = json.loads(man.read_text(encoding="utf-8"))
        gone = {f"textures/block/{t}.png" for t in tex} | {p.relative_to(A).as_posix() for p in old if p.suffix == ".png"}
        data["entries"] = [e for e in data["entries"] if e.get("file") not in gone]
        man.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("applied; backups in", bk.relative_to(P))


def iso(tex, k=4):
    """Isometric 3D view of a small caldera slope: every face where the game puts it (top faces on top, sides below
    their top edge; the crimson cap's side is shown v-flipped like its cube_bottom_top_vflip model)."""
    g = lambda key: tex[key][0]
    U = g("ember_basalt/ember_basalt")
    blocks = {
        "warm": (g("warm_capped_ember_stone/warm_capped_ember_stone_top"), g("warm_capped_ember_stone/warm_capped_ember_stone_side")),
        "crim": (g("crimson_capped_ember_stone/crimson_capped_ember_stone_top"),
                 g("crimson_capped_ember_stone/crimson_capped_ember_stone_side").transpose(Image.FLIP_TOP_BOTTOM)),
        "umber": (U, U), "ore": (g("patina_ore/patina_ore_oxidation0"),) * 2,
        "speck": (g("ember_basalt/ember_basalt_speckled"),) * 2,
        "ash": (g("gray_capped_void_stone/gray_capped_ember_stone_top_a"), g("gray_capped_void_stone/gray_capped_ember_stone_side")),
        "scorch": (g("crimson_capped_void_stone/crimson_capped_ember_stone_top"),
                   g("crimson_capped_void_stone/crimson_capped_ember_stone_side")),
        "s0": (g("magma_vein_slate/magma_vein_slate_dyke0_a"),) * 2, "s1": (g("magma_vein_slate/magma_vein_slate_dyke1_b"),) * 2,
        "s2": (g("magma_vein_slate/magma_vein_slate_dyke2_c"),) * 2,
        "bed": (g("magma_vein_slate/magma_vein_slate_dyke3_a"),) * 2}
    bed_turns = [g(f"magma_vein_slate/{n}") for n in MAGMA_VARIANTS[3]] * 2   # the rift bed is magma vein slate vein 3
    H = [[5, 5, 5, 4, 4, 1, 1], [5, 5, 4, 4, 3, 1, 1], [5, 4, 4, 3, 3, 1, 1], [4, 4, 3, 3, 3, 1, 1], [4, 3, 3, 3, 2, 1, 1]]
    rnd = random.Random("iso")
    cells = []
    for z, row in enumerate(H):
        for x, h in enumerate(row):
            for y in range(h):
                if h == 1:
                    kind = "bed"
                elif y == h - 1:
                    kind = rnd.choice(("warm", "warm", "warm", "umber", "crim", "ash", "scorch", "speck"))
                elif x >= 3 and y < h - 2:
                    kind = rnd.choice(("s0", "s1", "s2", "s0", "ore"))
                else:
                    kind = rnd.choice(("umber", "umber", "speck"))
                cells.append((x, y, z, kind))
    W, Hh = 900, 620
    img = Image.new("RGB", (W, Hh), (28, 27, 32))
    d = ImageDraw.Draw(img)
    ox, oy = W // 2 - 60, 220
    pt = lambda X, Y, Z: (ox + (X - Z) * k * 1.0, oy + (X + Z) * k * 0.5 - Y * k)
    shade = lambda c, f: tuple(int(v * f) for v in c)
    filled = {(x, y, z) for x, y, z, _ in cells}
    for x, y, z, kind in sorted(cells, key=lambda c: (c[0] + c[2], c[1])):
        top, side = blocks[kind]
        if kind == "bed":
            top = bed_turns[(x * 7 + z * 3) % 4]
        if kind == "warm":
            top = top.rotate(90 * ((x * 5 + z * 3 + y) % 4))
        X, Y, Z = x * 16, (y + 1) * 16, z * 16
        if (x, y + 1, z) not in filled:
            for u in range(16):
                for v in range(16):
                    d.polygon([pt(X + u, Y, Z + v), pt(X + u + 1, Y, Z + v), pt(X + u + 1, Y, Z + v + 1), pt(X + u, Y, Z + v + 1)],
                              fill=top.getpixel((u, v)))
        if (x, y, z + 1) not in filled:                       # south face (towards the viewer, left)
            for u in range(16):
                for t in range(16):
                    d.polygon([pt(X + u, Y - t, Z + 16), pt(X + u + 1, Y - t, Z + 16), pt(X + u + 1, Y - t - 1, Z + 16),
                               pt(X + u, Y - t - 1, Z + 16)], fill=shade(side.getpixel((u, t)), 0.8))
        if (x + 1, y, z) not in filled:                       # east face (right)
            for u in range(16):
                for t in range(16):
                    d.polygon([pt(X + 16, Y - t, Z + 16 - u), pt(X + 16, Y - t, Z + 15 - u), pt(X + 16, Y - t - 1, Z + 15 - u),
                               pt(X + 16, Y - t - 1, Z + 16 - u)], fill=shade(side.getpixel((u, t)), 0.6))
    out = P / "build/previews/caldera_earth_3d.png"
    img.save(out)
    print("3d preview:", out.relative_to(P))


def magma_tests(tex):
    """Seam tests (user: every magma variant must join its neighbours): per vein level a 3x3 of its variants picked at
    random; every pair of levels side by side and stacked; a 10 x 8 wall mixed the way the worldgen mixes it."""
    g = lambda lv, v: tex[f"magma_vein_slate/{MAGMA_VARIANTS[lv][v]}"][0]
    rnd = random.Random("seams")
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 12)
    Z = 5
    sheet = Image.new("RGB", (1180, 900), (28, 27, 32))
    d = ImageDraw.Draw(sheet)
    d.text((10, 6), "熔脈板岩接縫測試：上排 = 各 vein 等級的三種變體隨機 3×3；中排 = 兩個等級上下、左右相鄰；下排 = 照生成規則混合的崖壁", fill=(240, 230, 205), font=f)
    for lv in range(4):
        t = Image.new("RGB", (48, 48))
        for a in range(3):
            for b in range(3):
                t.paste(g(lv, rnd.randrange(3)), (a * 16, b * 16))
        sheet.paste(t.resize((48 * Z, 48 * Z), Image.NEAREST), (10 + lv * (48 * Z + 50), 28))
        d.text((10 + lv * (48 * Z + 50), 28 + 48 * Z + 2), f"vein {lv}", fill=(220, 225, 235), font=f)
    pairs = [(0, 1), (1, 2), (2, 3), (1, 3)]
    for i, (a, b) in enumerate(pairs):                       # a column of a over b, beside a row of a | b
        t = Image.new("RGB", (48, 32))
        for k in range(3):
            t.paste(g(a, k), (k * 16, 0))
            t.paste(g(b, (k + 1) % 3), (k * 16, 16))
        sheet.paste(t.resize((48 * 4, 32 * 4), Image.NEAREST), (10 + i * 290, 300))
        u = Image.new("RGB", (32, 32))
        u.paste(g(a, 0), (0, 0)); u.paste(g(b, 1), (16, 0)); u.paste(g(b, 2), (0, 16)); u.paste(g(a, 2), (16, 16))
        sheet.paste(u.resize((32 * 2, 32 * 2), Image.NEAREST), (10 + i * 290 + 200, 300))
        d.text((10 + i * 290, 300 + 130), f"vein {a} / vein {b}", fill=(220, 225, 235), font=f)
    wall = Image.new("RGB", (16 * 18, 16 * 9))
    for x in range(18):                                      # like SOUL_WALL: deep 1/2 mix, shallow 0/1 mix, rift bed 3
        for y in range(9):
            lv = 3 if y == 8 else (rnd.choice((0, 0, 1)) if y < 4 else rnd.choice((1, 2, 2)))
            wall.paste(g(lv, rnd.randrange(3)), (x * 16, y * 16))
    sheet.paste(wall.resize((wall.width * 2, wall.height * 2), Image.NEAREST), (10, 450))
    sheet = sheet.crop((0, 0, 1180, 450 + wall.height * 2 + 10))
    out = P / "build/previews/magma_seams.png"
    sheet.save(out)
    print("seam test:", out.relative_to(P))


def main():
    tex = textures()
    preview(tex)
    iso(tex)
    magma_tests(tex)
    if APPLY:
        apply(tex)


if __name__ == "__main__":
    main()
