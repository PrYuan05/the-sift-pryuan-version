"""Soul Caldera textures (minecraft-texture-crafter skill), from the user's spec "soul_caldera 材質規格書".
Usage: python -I tools/worldgen/paint_soul_caldera.py <project> [--apply]

One biome palette for every block (no colour jumps between blocks): basalt grey ~70 %, scorched crimson ~20 %, soul-teal moss
~10 %, the warm embers only at the crater rim. Every rock starts from the SAME basalt grain (the upgraded void stone's ladder and
paint_void_stone.basalt structure), so the blocks meet softly; the crusts, veins, rust and ores are laid on top of it.

  block (states)                 real world                              vanilla skeleton    structure
  mossy_void_stone (moss 0-3)    Icelandic basalt + Eldhraun woolly moss  void stone + grass   top moss 0/22/50/84 %, cushions, fringe,
                                 (glow: luminous moss)                    _block_side          glowing tips; side moss hangs 1-2/2-4/4-7
  red_sculk_vein_bottom          oxidised lava-tube wall                 deepslate grain     curved crimson veinlets + soot halo
  rusted_dark_cobble (rust 0-3)  iron-rich scoria                        cobblestone         cobbles + dark joints, 0/3/7/12 rusty ones
  warm_capped_ember_stone        ropy pahoehoe crust + ash               magma_block         ash crust, ropes every ~4 px, glowing cracks
  crimson_capped_ember_stone     scorched pahoehoe crust                 magma_block         same, crust in scorched crimson
  magma_vein_slate (vein 0-2)    slate cut by dykes                      deepslate           1-3 px cleavage; 1/3/5 crimson seams, vein 2
                                                                                             seams glow at the core
  argent_ore                     dendritic native silver                 iron_ore            4 branching wires, bright tips, 1 px shadow
  patina_ore (oxidation 0-1)     native copper -> malachite              copper_ore          5 copper clusters, 35 % / 80 % green, the
                                                                                             green seeping into the rock
Glow: the moss tips, the ember cracks / crust undersides and the vein-2 seam cores go on a second, cutout layer with
light_emission 15 (templates cube_bottom_top_glow / cube_all_glow), so only those pixels are full-bright.
Shared textures of other biomes (ember_stone, void_stone) are not touched: the two capped ember stones get their own top /
side / bottom files. The building set of mossy_void_stone (bricks, chiseled) is painted by the same script after
building_sets.py --only=mossy_void_stone has created its resources.
"""
import colorsys, datetime, json, math, random, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
A = P / "src/main/resources/assets/pysift"
T = A / "textures/block"
M = A / "models/block"
sys.path.insert(0, str(P / "tools"))
sys.path.insert(0, str(P / "tools/worldgen"))
sys.path.insert(0, str(P / "tools/texture_pipeline"))
import art_guard
from paint_void_stone import basalt, bricks as basalt_bricks, chiseled as stalker_chiseled, mottle, ALL, BLOBS


def hx(s): return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


PALETTES = {
    # the user's spec (v1)
    "spec": {"MOSS": "#77c0b3 #4e9c9a #397d81 #2f5e68 #27414d", "CRIM": "#90535b #7b3d4d #612e43 #462438 #301c2c",
             "EMB": "#dabd6d #cb883d #b85929 #943829", "GREEN": "#7db8a0 #569485 #3d756f"},
    # A "soul fire": the glow is soul-fire cyan (vanilla soul fire), lichen-like desaturated moss, hematite red-brown scorch,
    #   chrysocolla blue-green instead of malachite (echoes the soul cyan)
    "A": {"MOSS": "#7fa89d #5d8780 #466b69 #34514f #263b3d", "CRIM": "#85565a #6b3f45 #533039 #3c2430 #2a1a24",
          "EMB": "#d4fbf7 #8eeae6 #3ec2cf #1f7f96", "GREEN": "#79bdbf #4f9aa3 #387680"},
    # B "muted embers": warm embers kept but darker and smaller, sage moss, burgundy-brown scorch
    "B": {"MOSS": "#84a597 #61857b #496a65 #36504f #283b3d", "CRIM": "#8a5651 #704044 #573139 #3e2430 #2b1b24",
          "EMB": "#d9b77a #c08446 #9c5534 #6e3627", "GREEN": "#7db8a0 #569485 #3d756f"},
    # mix (user's choice): A's scorch and chrysocolla, B's muted warm embers, and the moss in soul_willow_planks' teal-blue
    #   (#95C5C9 #6DABBE #5297AF #4D90A4 + a deeper step) - the same family as the soul crystal and the willow wood
    "mix": {"MOSS": "#95c5c9 #6dabbe #5297af #4d90a4 #36677a", "CRIM": "#85565a #6b3f45 #533039 #3c2430 #2a1a24",
            "EMB": "#d9b77a #c08446 #9c5534 #6e3627", "GREEN": "#79bdbf #4f9aa3 #387680"},
}
PAL = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--palette=")), "spec")
BAS = [hx(c) for c in "#696764 #585d5f #4c5156 #42464d #393c45 #2e2f3a #22212d".split()]
MOSS = [hx(c) for c in PALETTES[PAL]["MOSS"].split()]
CRIM = [hx(c) for c in PALETTES[PAL]["CRIM"].split()]
EMB = [hx(c) for c in PALETTES[PAL]["EMB"].split()]
RUST = [hx(c) for c in "#725642 #644034 #53312b #3d2325".split()]
ASH = [hx(c) for c in "#7a7874 #66696d".split()]
SILV = [hx(c) for c in "#dedcd1 #b0bac0 #8a939d #686e7f".split()]
GREEN = [hx(c) for c in PALETTES[PAL]["GREEN"].split()]
COPPER = [hx(c) for c in "#b68657 #9e5f3f #774032".split()]
CLEAR = (0, 0, 0, 0)


def lum(c): return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255


def rock(seed):
    """The shared basalt grain (paint_void_stone.basalt) as a 16 x 16 RGB image."""
    return basalt(random.Random(seed)).image(BAS).convert("RGBA")


def wrap(x, y): return (x % 16, y % 16)


def grow(rnd, frac, seeds, wrapy=True):
    """Organic torus mask covering about frac of the tile: `seeds` separate cushions of uneven size, each grown compactly
    (new cells where most neighbours are already moss), so a thin moss is several small pads, not one dot per block."""
    if frac > 0.6:                                        # thick moss: full cover with a few irregular holes of bare rock
        return set(ALL) - grow(rnd, 1 - frac, max(2, seeds // 2), wrapy)
    m = set()
    target = int(frac * 256)
    shares = [rnd.uniform(0.6, 1.4) for _ in range(seeds)]
    for share in shares:
        pad = {(rnd.randrange(16), rnd.randrange(16))}
        goal = max(2, int(target * share / sum(shares)))
        while len(pad) < goal:
            border = {wrap(x + dx, y + dy) for (x, y) in pad for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - pad
            score = lambda q: sum(wrap(q[0] + dx, q[1] + dy) in pad for dx in (-1, 0, 1) for dy in (-1, 0, 1)) + rnd.random() * 2.5
            pad.add(max(border, key=score))
        m |= pad
    while len(m) < target:                                # pads overlap: keep growing the union up to the target cover
        border = {wrap(x + dx, y + dy) for (x, y) in m for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - m
        score = lambda q: sum(wrap(q[0] + dx, q[1] + dy) in m for dx in (-1, 0, 1) for dy in (-1, 0, 1)) + rnd.random() * 2.5
        m.add(max(border, key=score))
    return m


# ------------------------------------------------------------------------------------------------ mossy void stone
def moss_top(level):
    """Top: moss cushions over the basalt (0 / 22 / 50 / 84 %), lit top-left rims, shaded bottom-right, a shadow on the rock,
    fringe spurs and glowing tips in the cushion cores. Returns (texture, glow layer)."""
    img = rock(f"mossy_top_rock")
    glow = Image.new("RGBA", (16, 16), CLEAR)
    if level == 0:
        return img, glow
    rnd = random.Random(f"moss_top{level}")
    m = grow(rnd, (0.22, 0.50, 0.84)[level - 1], (3, 5, 7)[level - 1])
    for (x, y) in m:
        up, lf, dn, rt = wrap(x, y - 1) in m, wrap(x - 1, y) in m, wrap(x, y + 1) in m, wrap(x + 1, y) in m
        if not up or not lf:
            col = MOSS[1]
        elif not dn or not rt:
            col = MOSS[3]
        else:
            col = MOSS[2]
        img.putpixel((x, y), (*col, 255))
    tuft = random.Random(f"moss_tuft{level}")             # woolly texture: 2-3 px tufts, a step lighter or darker
    inner = sorted(p for p in m if all(wrap(p[0] + dx, p[1] + dy) in m for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
    for _ in range(len(inner) // 6):
        x, y = tuft.choice(inner)
        col = MOSS[1] if tuft.random() < 0.4 else MOSS[3]
        for dx, dy in tuft.choice(BLOBS[:5]):
            q = wrap(x + dx, y + dy)
            if q in inner:
                img.putpixel(q, (*col, 255))
    for (x, y) in m:                                      # shadow of the cushion on the rock, and woolly fringe spurs
        for q in (wrap(x + 1, y + 1), wrap(x, y + 1)):
            if q not in m:
                img.putpixel(q, (*BAS[5], 255))
    for _ in range(4 + 3 * level):
        x, y = rnd.choice(sorted(m))
        q = wrap(x + rnd.choice((-1, 1)), y + rnd.choice((-1, 1)))
        if q not in m:
            img.putpixel(q, (*MOSS[3], 255))
    cores = [p for p in m if all(wrap(p[0] + dx, p[1] + dy) in m for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
    rnd.shuffle(cores)
    for (x, y) in cores[: (2, 4, 7)[level - 1]]:          # glowing tips: the pale soul-teal, full bright
        img.putpixel((x, y), (*MOSS[0], 255))
        glow.putpixel((x, y), (*MOSS[0], 255))
    return img, glow


def moss_side(level):
    """Side: basalt with the moss hanging from the top edge (1-2 / 2-4 / 4-7 px), a lit top row, a shaded lower edge, a
    darker rock shadow under it and a few longer strands whose tips glow."""
    img = rock("mossy_side_rock")
    glow = Image.new("RGBA", (16, 16), CLEAR)
    rnd = random.Random(f"moss_side{level}")
    lo, hi = ((1, 2), (2, 4), (4, 7))[level - 1]
    depth, d = [], rnd.randint(lo, hi)
    for x in range(16):                                   # a gentle random walk, wrapping in x
        d = max(lo, min(hi, d + rnd.choice((-1, 0, 0, 1))))
        depth.append(d)
    depth[15] = max(lo, min(hi, round((depth[14] + depth[0]) / 2)))
    strands = rnd.sample(range(16), 2 + level)
    for x in range(16):
        dd = depth[x] + (rnd.randint(1, 2) if x in strands else 0)
        for y in range(dd):
            col = MOSS[1] if y == 0 else MOSS[3] if y == dd - 1 else MOSS[2]
            img.putpixel((x, y), (*col, 255))
        img.putpixel((x, dd), (*BAS[5], 255))             # shadow on the rock
        if x in strands:
            img.putpixel((x, dd - 1), (*MOSS[0], 255))
            glow.putpixel((x, dd - 1), (*MOSS[0], 255))
    return img, glow


# ------------------------------------------------------------------------------------------------ red sculk vein bottom
def sculk_vein():
    img = rock("sculk_vein_rock")
    rnd = random.Random("sculk_vein")
    vein = set()
    for k, (y0, amp, per) in enumerate(((3, 2.2, 16), (10, 1.8, 8))):
        ph = rnd.uniform(0, 16)
        for x in range(16):
            y = y0 + round(amp * math.sin(2 * math.pi * (x + ph) / per))
            vein.add(wrap(x, y))
    for _ in range(3):                                    # short branches between the two veins
        x = rnd.randrange(16)
        y = next(yy for (xx, yy) in sorted(vein) if xx == x)
        for k in range(1, rnd.randint(3, 5)):
            vein.add(wrap(x + (k // 2), y + k))
    for (x, y) in vein:                                   # soot halo first, then the vein: lit upper edge, darker lower edge
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = wrap(x + dx, y + dy)
                if q not in vein and rnd.random() < 0.55:
                    img.putpixel(q, (*BAS[5 if (dx + dy) % 2 else 6], 255))
    for (x, y) in vein:
        up, dn = wrap(x, y - 1) in vein, wrap(x, y + 1) in vein
        col = CRIM[0] if not up else CRIM[2] if not dn else CRIM[1]
        img.putpixel((x, y), (*col, 255))
        if wrap(x, y + 1) not in vein:
            img.putpixel(wrap(x, y + 1), (*CRIM[3], 255))
    return img


# ------------------------------------------------------------------------------------------------ rusted dark cobble
def cobble_cells():
    rnd = random.Random("caldera_cobble")
    pts = [((k * 16 / 4 + (2 if r % 2 else 0) + rnd.uniform(-1.2, 1.2)) % 16, (r * 4 + 2 + rnd.uniform(-1, 1)) % 16)
           for r in range(4) for k in range(4)]
    own = {}
    for (x, y) in ALL:
        own[(x, y)] = min(range(len(pts)), key=lambda i: math.hypot(min(abs(x + .5 - pts[i][0]), 16 - abs(x + .5 - pts[i][0])),
                                                                    min(abs(y + .5 - pts[i][1]), 16 - abs(y + .5 - pts[i][1]))))
    return own, len(pts)


def cobble(rust_count):
    """Cobbles of the shared basalt with dark joints; rust_count of them (0 / 3 / 7 / 12, always the same cells growing)
    turn rusty, the grey ones carry small rust spots once the block is rusting."""
    own, n = cobble_cells()
    rnd = random.Random("caldera_cobble_rust")
    order = list(range(n))
    rnd.shuffle(order)
    rusty = set(order[:rust_count])
    grain = basalt(random.Random("caldera_cobble_grain")).image(BAS)
    img = Image.new("RGBA", (16, 16))
    for (x, y) in ALL:
        o = own[(x, y)]
        joint = own[wrap(x + 1, y)] != o or own[wrap(x, y + 1)] != o
        lit = own[wrap(x - 1, y)] != o or own[wrap(x, y - 1)] != o
        if joint:
            col = BAS[6]
        elif o in rusty:
            col = RUST[0] if lit else RUST[(x * 3 + y) % 2 + 1]
        else:
            col = BAS[1] if lit else grain.getpixel((x, y))[:3]
        img.putpixel((x, y), (*col, 255))
    for (x, y) in ALL:                                    # buffer: the pixel above / left of a joint one step darker
        if img.getpixel((x, y))[:3] != BAS[6] and (img.getpixel(wrap(x + 1, y))[:3] == BAS[6] or img.getpixel(wrap(x, y + 1))[:3] == BAS[6]):
            c = img.getpixel((x, y))[:3]
            img.putpixel((x, y), (*(RUST[3] if c in RUST else BAS[5]), 255))
    if rust_count:
        spots = random.Random(f"spots{rust_count}")
        for _ in range(rust_count // 2 + 1):
            x, y = spots.randrange(16), spots.randrange(16)
            if own[(x, y)] not in rusty and img.getpixel((x, y))[:3] not in (BAS[6], BAS[5]):
                img.putpixel((x, y), (*RUST[1], 255))
                if img.getpixel(wrap(x + 1, y))[:3] not in (BAS[6], BAS[5]):
                    img.putpixel(wrap(x + 1, y), (*RUST[2], 255))
    return img


# ------------------------------------------------------------------------------------------------ capped ember stones
def crust_top(crust, seed):
    """Top of a capped ember stone: a crust (two tones + the basalt for its troughs) with ropy pahoehoe folds every ~4 px
    and glowing cracks through it. Returns (texture, glow)."""
    rnd = random.Random(seed)
    img = Image.new("RGBA", (16, 16))
    glow = Image.new("RGBA", (16, 16), CLEAR)
    ph = rnd.uniform(0, 16)
    for y in range(16):
        for x in range(16):
            r = (y + round(1.3 * math.sin(2 * math.pi * (x + ph) / 16) + 0.6 * math.sin(2 * math.pi * (x + ph) / 8))) % 4
            col = crust[0] if r == 0 else crust[1] if r in (1, 2) else BAS[3]          # rope crest, body, trough
            img.putpixel((x, y), (*col, 255))
    for _ in range(10):                                   # grain on the crust
        x, y = rnd.randrange(16), rnd.randrange(16)
        if img.getpixel((x, y))[:3] == crust[1]:
            img.putpixel((x, y), (*(crust[0] if rnd.random() < 0.4 else BAS[2]), 255))
    x, y = rnd.randrange(16), rnd.randrange(16)           # glowing cracks: a branching line across the ropes
    crack = []
    for _ in range(14):
        crack.append(wrap(x, y))
        x, y = x + rnd.choice((1, 1, 0)), y + rnd.choice((-1, 1, 1, 0))
    x, y = crack[len(crack) // 2]
    for _ in range(6):
        crack.append(wrap(x, y))
        x, y = x - 1, y + rnd.choice((0, 1))
    for i, q in enumerate(crack):
        core = 3 < i < 11
        img.putpixel(q, (*(EMB[1] if core else EMB[2]), 255))
        glow.putpixel(q, (*(EMB[1] if core else EMB[2]), 255))
        e = wrap(q[0], q[1] + 1)
        if e not in crack:
            img.putpixel(e, (*EMB[3], 255))               # the cooler edge of the crack
    q = crack[len(crack) // 2]
    img.putpixel(q, (*EMB[0], 255))
    glow.putpixel(q, (*EMB[0], 255))
    return img, glow


def crust_side(crust, seed):
    """Side: the crust band (4-5 px) on top of the basalt, its underside glowing where the molten rock shows through."""
    rnd = random.Random(seed)
    img = rock(seed + "_rock")
    glow = Image.new("RGBA", (16, 16), CLEAR)
    d = 4
    for x in range(16):
        d = max(3, min(5, d + rnd.choice((-1, 0, 0, 1))))
        for y in range(d):
            col = crust[0] if y == 0 else crust[1] if y < d - 1 else BAS[3]
            img.putpixel((x, y), (*col, 255))
        if rnd.random() < 0.55:                           # the lit underside of the crust
            c = EMB[2] if rnd.random() < 0.7 else EMB[1]
            img.putpixel((x, d), (*c, 255))
            glow.putpixel((x, d), (*c, 255))
        else:
            img.putpixel((x, d), (*BAS[5], 255))
    return img, glow


# ------------------------------------------------------------------------------------------------ magma vein slate
def vein_slate(level, seed):
    """Slate: 1-3 px horizontal cleavage layers of the basalt ladder, cut by 1 / 3 / 5 crimson seams; vein 2's seams glow
    at their core. Returns (texture, glow)."""
    rnd = random.Random(seed)
    img = Image.new("RGBA", (16, 16))
    glow = Image.new("RGBA", (16, 16), CLEAR)
    rows, k = [], 0
    while len(rows) < 16:
        rows += [[BAS[2], BAS[3], BAS[4], BAS[3], BAS[2], BAS[4]][k % 6]] * rnd.choice((1, 2, 2, 3))
        k += 1
    ph = rnd.uniform(0, 16)
    wave = [round(0.8 * math.sin(2 * math.pi * (x + ph) / 16)) for x in range(16)]
    for y in range(16):
        for x in range(16):
            img.putpixel((x, y), (*rows[(y + wave[x]) % 16], 255))
    for _ in range(6):                                    # flake highlights
        x, y, n = rnd.randrange(16), rnd.randrange(16), rnd.randint(3, 5)
        for q in range(n):
            img.putpixel(wrap(x + q, y - wave[(x + q) % 16]), (*BAS[1], 255))
    seams = (1, 3, 5)[level]
    ys = sorted(rnd.sample(range(16), seams))
    for y0 in ys:
        for x in range(16):
            y = (y0 - wave[x]) % 16
            img.putpixel((x, y), (*CRIM[1], 255))
            img.putpixel(wrap(x, y - 1), (*(CRIM[0] if x % 3 else BAS[1]), 255))     # lit upper edge
            img.putpixel(wrap(x, y + 1), (*CRIM[3], 255))
            if level == 2 and x % 5 not in (0, 4):
                img.putpixel((x, y), (*EMB[1], 255))
                glow.putpixel((x, y), (*EMB[1], 255))
    return img, glow


# ------------------------------------------------------------------------------------------------ ores
def argent():
    img = rock("mossy_top_rock")                         # the same bare basalt as mossy_void_stone: seamless next to it
    rnd = random.Random("argent")
    wires = set()
    tips = []
    for sx, sy in ((5, 4), (10, 6), (4, 10), (10, 11)):
        x, y = sx, sy
        for k in range(5):
            wires.add((x, y))
            if k == 2:
                wires.add((x + 1, y - 1))                  # a fork
                tips.append((x + 1, y - 1))
            x += rnd.choice((1, 0, 1))
            y += rnd.choice((-1, 0, 1))
            x, y = max(2, min(13, x)), max(2, min(13, y))
        tips.append((x, y))
    for (x, y) in wires:
        if (x, y + 1) not in wires:
            img.putpixel((x, y + 1), (*BAS[6], 255))        # 1 px shadow under the silver
    for (x, y) in wires:
        img.putpixel((x, y), (*(SILV[1] if (x + y) % 2 else SILV[2]), 255))
    for (x, y) in tips:
        img.putpixel((x, y), (*SILV[0], 255))
    for (x, y) in wires:
        if (x + 1, y + 1) not in wires and (x, y + 1) in wires:
            img.putpixel((x, y + 1), (*SILV[3], 255))
    return img


def patina(oxidation):
    img = rock("mossy_top_rock")
    rnd = random.Random("patina")
    clusters = [(4, 4), (10, 4), (7, 8), (4, 11), (11, 11)]
    pix = []
    for cx, cy in clusters:
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1), (2, 1), (1, 2)):
            if rnd.random() < 0.8 or (dx, dy) == (0, 0):
                pix.append((cx + dx, cy + dy))
    pix = list(dict.fromkeys(pix))
    order = pix[:]
    random.Random("patina_green").shuffle(order)
    green = set(order[: round(len(order) * (0.35, 0.80)[oxidation])])
    for (x, y) in pix:
        lit = (x - 1, y) not in pix or (x, y - 1) not in pix
        if (x, y) in green:
            col = GREEN[0] if lit else GREEN[1]
        else:
            col = COPPER[0] if lit else COPPER[1]
        img.putpixel((x, y), (*col, 255))
    seep = random.Random(f"seep{oxidation}")             # the green leaks into the rock around the clusters
    for (x, y) in green:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in pix and 1 <= q[0] <= 14 and 1 <= q[1] <= 14 and seep.random() < (0.25, 0.5)[oxidation]:
                img.putpixel(q, (*GREEN[2], 255))
    for (x, y) in pix:                                    # last: the 1 px shadow under every cluster
        if (x, y + 1) not in pix:
            img.putpixel((x, y + 1), (*BAS[6], 255))
    return img


# ------------------------------------------------------------------------------------------------ mossy void stone bricks
def mossy_bricks():
    """Basalt bricks (void stone's deepslate-style courses) with moss creeping out of the joints."""
    img = basalt_bricks(random.Random("mossy_bricks"), (0, 4, 0, 4)).image(BAS).convert("RGBA")
    rnd = random.Random("mossy_brick_moss")
    for _ in range(9):
        x, y = rnd.randrange(16), rnd.choice((3, 7, 11, 15))
        for k in range(rnd.randint(2, 4)):
            img.putpixel(wrap(x + k, y), (*MOSS[2], 255))
            if rnd.random() < 0.5:
                img.putpixel(wrap(x + k, y - 1), (*MOSS[1], 255))
    return img


def mossy_chiseled():
    """Chiseled: the Stalker (the caldera's commonest creature) in relief, the moss draped over its head band."""
    img = stalker_chiseled(random.Random("mossy_chiseled")).image(BAS).convert("RGBA")
    rnd = random.Random("mossy_chiseled_moss")
    for x in range(1, 15):
        n = rnd.choice((0, 1, 1, 2))
        for y in range(1, 1 + n):
            img.putpixel((x, y), (*(MOSS[1] if y == 1 else MOSS[2]), 255))
    for x in (2, 6, 9, 13):
        img.putpixel((x, 3), (*MOSS[3], 255))
    return img


# ------------------------------------------------------------------------------------------------ models
def template_models():
    def el(faces, tex, glow=False, flip=False):
        out = {"from": [0, 0, 0], "to": [16, 16, 16], "faces": {}}
        if glow:
            out["light_emission"] = 15
        for d in faces:
            out["faces"][d] = {"uv": [0, 0, 16, 16], "texture": tex[d], "cullface": d}
        return out
    sides = ("north", "south", "west", "east")
    btg = {"parent": "minecraft:block/block", "render_type": "minecraft:cutout", "textures": {"particle": "#side"},
           "elements": [el(("down", "up") + sides, {"down": "#bottom", "up": "#top", **{s: "#side" for s in sides}}),
                        el(("up",) + sides, {"up": "#top_glow", **{s: "#side_glow" for s in sides}}, glow=True)]}
    allg = {"parent": "minecraft:block/block", "render_type": "minecraft:cutout", "textures": {"particle": "#all"},
            "elements": [el(("down", "up") + sides, {d: "#all" for d in ("down", "up") + sides}),
                         el(("down", "up") + sides, {d: "#glow" for d in ("down", "up") + sides}, glow=True)]}
    return {"templates/cube_bottom_top_glow": btg, "templates/cube_all_glow": allg}


def build():
    tex, glows, models, states = {}, {}, {}, {}
    mv = "mossy_void_stone/mossy_void_stone"
    tex[mv] = moss_top(0)[0]
    for k in (1, 2, 3):
        tex[f"{mv}_top_{k}"], glows[f"{mv}_top_{k}_glow"] = moss_top(k)
        tex[f"{mv}_side_{k}"], glows[f"{mv}_side_{k}_glow"] = moss_side(k)
    tex["red_sculk_vein_bottom/red_sculk_vein_bottom"] = sculk_vein()
    for k, n in enumerate((0, 3, 7, 12)):
        tex[f"rusted_dark_cobble/rusted_dark_cobble_rust{k}"] = cobble(n)
    for name, crust in (("warm_capped_ember_stone", ASH + [BAS[2]]), ("crimson_capped_ember_stone", [CRIM[0], CRIM[1], CRIM[3]])):
        tex[f"{name}/{name}_top"], glows[f"{name}/{name}_top_glow"] = crust_top(crust, name)
        tex[f"{name}/{name}_side"], glows[f"{name}/{name}_side_glow"] = crust_side(crust, name)
        tex[f"{name}/{name}_bottom"] = rock(name + "_bottom")
    for f in sorted((T / "magma_vein_slate").glob("magma_vein_slate_vein*.png")):
        lv = int(f.stem.split("vein")[-1][0])
        img, g = vein_slate(lv, f.stem)
        tex[f"magma_vein_slate/{f.stem}"] = img
        if lv == 2:
            glows[f"magma_vein_slate/{f.stem}_glow"] = g
    tex["argent_ore/argent_ore"] = argent()
    for k in (0, 1):
        tex[f"patina_ore/patina_ore_oxidation{k}"] = patina(k)
    if (T / "mossy_void_stone_bricks").exists():
        tex["mossy_void_stone_bricks/mossy_void_stone_bricks"] = mossy_bricks()
        tex["mossy_void_stone_bricks/chiseled_mossy_void_stone_bricks"] = mossy_chiseled()
    # models: mossy void stone (moss 0 bare, 1-3 top / side / bottom + glow), the capped ember stones, the vein-2 slates
    models.update(template_models())
    models[f"{mv}_0"] = {"parent": "minecraft:block/cube_all", "textures": {"all": f"pysift:block/{mv}"}}
    for k in (1, 2, 3):
        models[f"{mv}_{k}"] = {"parent": "pysift:block/templates/cube_bottom_top_glow", "textures": {
            "top": f"pysift:block/{mv}_top_{k}", "side": f"pysift:block/{mv}_side_{k}", "bottom": f"pysift:block/{mv}",
            "top_glow": f"pysift:block/{mv}_top_{k}_glow", "side_glow": f"pysift:block/{mv}_side_{k}_glow"}}
    variants = {"moss=0": {"model": f"pysift:block/{mv}_0"}}
    for k in (1, 2, 3):
        variants[f"moss={k}"] = [{"model": f"pysift:block/{mv}_{k}", "y": r} for r in (0, 90, 180, 270)]
    states["mossy_void_stone"] = {"variants": variants}
    for name in ("warm_capped_ember_stone", "crimson_capped_ember_stone"):
        b = f"pysift:block/{name}/{name}"
        models[f"{name}/{name}_1"] = {"parent": "pysift:block/templates/cube_bottom_top_glow", "textures": {
            "top": f"{b}_top", "side": f"{b}_side", "bottom": f"{b}_bottom", "top_glow": f"{b}_top_glow", "side_glow": f"{b}_side_glow"}}
    for key in glows:
        if key.startswith("magma_vein_slate/"):
            stem = key.split("/")[1][: -len("_glow")]
            models[f"magma_vein_slate/{stem}"] = {"parent": "pysift:block/templates/cube_all_glow", "textures": {
                "all": f"pysift:block/magma_vein_slate/{stem}", "glow": f"pysift:block/{key}"}}
    return tex, glows, models, states


def preview(tex, glows):
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 11)
    names = list(tex)
    S, per = 64, 10
    rows = (len(names) + per - 1) // per
    sheet = Image.new("RGB", (per * (S + 6) + 10, rows * (2 * S + 30) + 10), (24, 24, 30))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        x, y = 6 + (i % per) * (S + 6), 4 + (i // per) * (2 * S + 30)
        old = T / f"{n}.png"
        if old.exists():
            sheet.paste(Image.open(old).convert("RGB").crop((0, 0, 16, 16)).resize((S, S), Image.NEAREST), (x, y))
        sheet.paste(tex[n].convert("RGB").resize((S, S), Image.NEAREST), (x, y + S + 2))
        d.text((x, y + 2 * S + 4), n.split("/")[-1].replace("mossy_void_stone", "mvs").replace("magma_vein_slate", "mvsl")
               .replace("capped_ember_stone", "cap").replace("rusted_dark_cobble", "rdc")[:12], fill=(205, 210, 220), font=f)
    sheet.save(P / f"build/previews/soul_caldera_paint_{PAL}.png")
    # the biome as one surface: a 12 x 8 field of the blocks next to each other (top faces) and a cliff (side faces)
    rnd = random.Random("field")
    field_tops = ["mossy_void_stone/mossy_void_stone"] + [f"mossy_void_stone/mossy_void_stone_top_{k}" for k in (1, 2, 3)] * 3 \
        + [f"rusted_dark_cobble/rusted_dark_cobble_rust{k}" for k in range(4)] + ["red_sculk_vein_bottom/red_sculk_vein_bottom"]
    field = Image.new("RGB", (16 * 12, 16 * 8))
    for by in range(8):
        for bx in range(12):
            n = "warm_capped_ember_stone/warm_capped_ember_stone_top" if (bx - 9) ** 2 + (by - 2) ** 2 < 4 else \
                "crimson_capped_ember_stone/crimson_capped_ember_stone_top" if (bx - 9) ** 2 + (by - 2) ** 2 < 8 else rnd.choice(field_tops)
            field.paste(tex[n].convert("RGB").rotate(90 * rnd.randrange(4)), (bx * 16, by * 16))
    field.resize((field.width * 3, field.height * 3), Image.NEAREST).save(P / f"build/previews/soul_caldera_field_{PAL}.png")
    cliff = Image.new("RGB", (16 * 8, 16 * 6))
    slates = [n for n in tex if n.startswith("magma_vein_slate/")]
    for bx in range(8):
        top = f"mossy_void_stone/mossy_void_stone_side_{1 + bx % 3}" if bx < 6 else "warm_capped_ember_stone/warm_capped_ember_stone_side"
        cliff.paste(tex[top].convert("RGB"), (bx * 16, 0))
        for by in range(1, 6):
            n = rnd.choice(slates) if by > 2 else rnd.choice(["mossy_void_stone/mossy_void_stone"] + slates[:3] +
                                                              ["patina_ore/patina_ore_oxidation0", "argent_ore/argent_ore"] if by == 2 else
                                                              ["mossy_void_stone/mossy_void_stone", "rusted_dark_cobble/rusted_dark_cobble_rust1"])
            cliff.paste(tex[n].convert("RGB"), (bx * 16, by * 16))
    cliff.resize((cliff.width * 3, cliff.height * 3), Image.NEAREST).save(P / f"build/previews/soul_caldera_cliff_{PAL}.png")


def main():
    tex, glows, models, states = build()
    preview(tex, glows)
    tmp = P / "build/previews/soul_caldera_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    for n, im in {**tex, **glows}.items():
        im.save(tmp / f"{n.split('/')[-1]}.png")
    print("preview: build/previews/soul_caldera_paint.png, soul_caldera_field.png, soul_caldera_cliff.png;",
          len(tex), "textures,", len(glows), "glow layers")
    if not APPLY:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_soul_caldera")
    for n, im in {**tex, **glows}.items():
        dst = T / f"{n}.png"
        if dst.exists():
            (bk / dst.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, bk / dst.relative_to(P))
            if not art_guard.is_ours(dst) and "--force" in sys.argv:
                dst.unlink()
        dst.parent.mkdir(parents=True, exist_ok=True)
        art_guard.save(im, dst)
    for n, mj in models.items():
        dst = M / f"{n}.json"
        if dst.exists():
            (bk / dst.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, bk / dst.relative_to(P))
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(mj, indent=2) + "\n", encoding="utf-8")
    for n, sj in states.items():
        (A / f"blockstates/{n}.json").write_text(json.dumps(sj, indent=2) + "\n", encoding="utf-8")
    man = P / "tools/texture_pipeline/recolor_manifest.json"
    doc = json.loads(man.read_text(encoding="utf-8"))
    written = {f"textures/block/{n}.png" for n in {**tex, **glows}}
    doc["entries"] = [e for e in doc["entries"] if e["file"] not in written]
    man.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("applied; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
