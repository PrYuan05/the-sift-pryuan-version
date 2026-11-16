"""Hand-designed amber and pale sand (minecraft-texture-crafter skill; stone_upgrade_plan.md R01 wind-rippled sand).
Usage: python -I tools/worldgen/paint_sand.py <project> [--apply]

Without --apply only build/previews/sand_paint.png is written (current vs new, a 4 x 4 field with the random rotations,
the sand lying on its sandstone). With --apply the two textures are backed up to .texture_backups/<stamp>_paint_sand/ and
written through tools/art_guard.py, and both blockstates get vanilla sand's four random y rotations.

Material brief:
  1. Identity: the amber dunes' surface (0-3 blocks), falling blocks; amber ~70 %, pale ~30 % patches; lies on the
     amber / pale sandstone painted by paint_sandstone_family.py, so the hues follow that sandstone, a little lighter.
  2. Physical: fine, loose, matte grains - narrow value span (skill: fine sand 0.10-0.20), no hard edges, wind ripples.
  3. Real world: amber = Namib red dune sand (quartz coated with iron oxide, a few black magnetite grains);
     pale = pale interdune quartz sand of the Sahara (little iron, fewer dark grains, fainter ripples).
  4. Vanilla anchor: block/sand.png (4 colours, span 0.17, fine 1-2 px grain) and its blockstate (4 random y rotations).
Structure: four wavy ripple crests per tile (period 3-5 px, wobbling, wrapping in x): a lit crest row (#2, a few #1 glints),
the lee slope just under it one step darker (#5), the troughs mottled #3 / #4; 2 px dark mineral grains (#6) and pale
quartz grains (#2) scattered on top.
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

C1, C2, C3, C4, C5, C6 = range(6)
# (dH, saturation factor, target luminance): a fine-sand ladder, span 0.175 like vanilla sand
STEPS = [(+16, 0.50, 0.845), (+11, 0.70, 0.810), (+5, 0.88, 0.775), (0, 1.00, 0.740), (-6, 0.95, 0.705), (-14, 0.80, 0.668)]
SANDS = {  # colour -> (hue, saturation, luminance lift, ripple strength, dark grains, seed)
    "amber": (36, 0.52, 0.00, 0.7, 5, "amber"),
    "pale": (40, 0.36, 0.045, 0.5, 3, "pale"),
}
ALL = [(x, y) for x in range(16) for y in range(16)]


def lum(rgb): return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255


def palette(colour):
    h, s, lift = SANDS[colour][:3]
    out = []
    for dh, sf, target in STEPS:
        lo, hi = 0.0, 1.0
        for _ in range(40):
            v = (lo + hi) / 2
            rgb = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(((h + dh) % 360) / 360, min(0.9, s * sf), v))
            lo, hi = (v, hi) if lum(rgb) < target + lift else (lo, v)
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


BLOBS = [((0, 0), (1, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)), ((0, 0), (1, 0), (1, 1)), ((0, 0), (1, 0), (0, 1), (1, 1))]


def mottle(c, rnd, colours, base_max):
    keys, weights = zip(*colours.items())
    for _ in range(600):
        if sum(1 for p in ALL if c.get(*p) == C4) <= base_max * 256:
            break
        x, y = rnd.randrange(16), rnd.randrange(16)
        col = rnd.choices(keys, weights)[0]
        for dx, dy in rnd.choice(BLOBS):
            if c.get(x + dx, y + dy) == C4:
                c.set(x + dx, y + dy, col)


def sand(colour):
    _, _, _, strength, dark, seed = SANDS[colour]
    rnd = random.Random(seed)
    c = Canvas()
    mottle(c, rnd, {C3: 5, C5: 4}, base_max=0.42)                      # trough grain
    y0 = rnd.randrange(16)
    crests, y = [], y0
    while len(crests) < 4:                                              # 4 crests, spacing 3-5, summing to 16
        crests.append(y)
        y += (4, 3, 5, 4)[len(crests) - 1]
    for k, cy in enumerate(crests):
        amp, phase, per = rnd.choice((1.0, 1.3)), rnd.uniform(0, 16), rnd.choice((8, 16))
        for x in range(16):
            yy = cy + round(amp * math.sin(2 * math.pi * (x + phase) / per))
            if rnd.random() < strength:
                c.set(x, yy, C2)                                        # lit crest
                if (x + k) % 3:
                    c.set(x, yy + 1, C5)                                # lee slope one step darker (broken)
            else:
                c.set(x, yy, C3)                                        # faint crest
        for _ in range(2 if strength >= 1 else 1):                      # glints on the crest, never alone
            x = rnd.randrange(16)
            yy = cy + round(amp * math.sin(2 * math.pi * (x + phase) / per))
            if c.get(x, yy) == C2 and c.get(x + 1, yy) == C2:
                c.set(x, yy, C1)
    for _ in range(dark):                                               # dark mineral grains, 2 px
        x, y = rnd.randrange(16), rnd.randrange(16)
        if c.get(x, y) not in (C1, C2) and c.get(x + 1, y) not in (C1, C2):
            c.set(x, y, C6)
            c.set(x + 1, y, C5)
    for _ in range(4):                                                  # pale quartz grains, 2 px
        x, y = rnd.randrange(16), rnd.randrange(16)
        if c.get(x, y) in (C4, C5) and c.get(x, y + 1) in (C4, C5):
            c.set(x, y, C2)
            c.set(x, y + 1, C3)
    return c


def blockstate(colour):
    model = f"pysift:block/{colour}_sand/{colour}_sand"
    return {"variants": {"": [{"model": model}] + [{"model": model, "y": r} for r in (90, 180, 270)]}}


def preview(images, pals):
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
    S, z = 8, 3
    sheet = Image.new("RGB", (40 + 2 * (2 * 16 * S + 40) + 2 * 64 * z + 40, 16 * S + 64 * z + 120), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    x = 20
    for colour, img in images.items():
        old = Image.open(T / f"{colour}_sand/{colour}_sand.png").convert("RGB")
        d.text((x, 4), f"{colour}_sand：舊 → 新", fill=(230, 230, 230), font=f)
        sheet.paste(old.resize((16 * S, 16 * S), Image.NEAREST), (x, 24))
        sheet.paste(img.resize((16 * S, 16 * S), Image.NEAREST), (x + 16 * S + 8, 24))
        rnd = random.Random(colour)
        field = Image.new("RGB", (64, 64))                              # top view with the 4 random rotations
        for bx in range(4):
            for by in range(4):
                field.paste(img.rotate(90 * rnd.randrange(4)), (bx * 16, by * 16))
        y0 = 24 + 16 * S + 30
        d.text((x, y0 - 22), "地面（隨機旋轉）", fill=(200, 200, 200), font=f)
        sheet.paste(field.resize((64 * z, 64 * z), Image.NEAREST), (x, y0))
        wall = Image.new("RGB", (64, 64))                               # side view: sand on its sandstone
        stone = Image.open(T / f"{colour}_sandstone/{colour}_sandstone.png").convert("RGB")
        for bx in range(4):
            for by in range(4):
                wall.paste(img if by < 2 else stone, (bx * 16, by * 16))
        d.text((x + 64 * z + 12, y0 - 22), "側面：沙疊在砂岩上", fill=(200, 200, 200), font=f)
        sheet.paste(wall.resize((64 * z, 64 * z), Image.NEAREST), (x + 64 * z + 12, y0))
        for k, rgb in enumerate(pals[colour]):
            d.rectangle([x + k * 30, sheet.height - 26, x + k * 30 + 26, sheet.height - 6], fill=rgb)
        x += 2 * 64 * z + 60
    out = P / "build/previews/sand_paint.png"
    sheet.save(out)
    return out


def main():
    pals = {c: palette(c) for c in SANDS}
    images = {c: sand(c).image(pals[c]) for c in SANDS}
    for c in SANDS:
        print(c, " ".join("#%02X%02X%02X(%.3f)" % (*p, lum(p)) for p in pals[c]))
    print("preview:", preview(images, pals).relative_to(P))
    tmp = P / "build/previews/sand_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    for c, img in images.items():
        img.save(tmp / f"{c}_sand.png")
    if not APPLY:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_sand")
    for c, img in images.items():
        for dst in (T / f"{c}_sand/{c}_sand.png", A / f"blockstates/{c}_sand.json"):
            (bk / dst.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, bk / dst.relative_to(P))
        dst = T / f"{c}_sand/{c}_sand.png"
        if not art_guard.is_ours(dst) and "--force" in sys.argv:
            dst.unlink()                                                # repainting the old draft on request
        art_guard.save(img, dst)
        (A / f"blockstates/{c}_sand.json").write_text(json.dumps(blockstate(c), indent=2) + "\n", encoding="utf-8")
    print("applied; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
