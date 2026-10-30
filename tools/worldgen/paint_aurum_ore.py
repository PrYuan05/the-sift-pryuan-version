"""aurum_ore (Lullaby Hills river bed) - oxidised pyrite in white sandstone (user: candidate F, white-sandstone ground).
Usage: python -I tools/worldgen/paint_aurum_ore.py <project> [--apply]

The ground IS bleached_sandstone bleach 0 (the block it borders and dithers into on the canyon floor), so the river bed
blends into the land layer without a seam. On it: small bright pyrite cubes (2 x 2: #1 corner, #2 / #3 faces, #5 shadow
face) inside rusty limonite halos in the current texture's own orange-gold, and a 1 px darker sandstone shadow under
each halo (skill: ore clusters sit IN the rock). richness 0 = a few cubes on the bank, richness 1 = many, halos merging.
Candidates and their comparison: tools/worldgen/aurum_candidates.py.
"""
import colorsys, datetime, random, shutil, sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
T = P / "src/main/resources/assets/pysift/textures/block"
sys.path.insert(0, str(P / "tools"))
sys.path.insert(0, str(P / "tools/worldgen"))
import art_guard
from aurum_candidates import colours, shade
from paint_void_stone import Canvas
from paint_pink_strata import ramp

# pyrite's brass yellow (H ~45): glint, lit face, side face, shadow face - its own ramp, so it never turns olive
BRASS = [(246, 228, 150), (226, 192, 84), (196, 158, 62), (146, 108, 48)]
SRC = P / ".texture_backups/20261030-171615_paint_aurum_ore/src/main/resources/assets/pysift/textures/block/aurum_ore"   # the original ore


def paint(rich):
    ground = Image.open(T / "bleached_sandstone/bleached_sandstone_bleach0.png").convert("RGB")
    sand = ramp(list(ground.get_flattened_data()), 0.16)
    _, gold = colours(SRC)                                     # gold from the ORIGINAL ore texture, not our output
    # the original ochre (~#AF893A) is darker than the white sandstone it now sits on: lift the whole ramp so the mass
    # reads as gold instead of a brown stain (value x1.18, saturation x1.05, same hue)
    gold = [tuple(round(v * 255) for v in colorsys.hsv_to_rgb(h, min(0.9, s_ * 1.05), min(0.97, v_ * 1.18)))
            for h, s_, v_ in (colorsys.rgb_to_hsv(*(c / 255 for c in g)) for g in gold)]
    # user: exactly candidate F's shapes (aurum_candidates.pyrite_rust, same seed), filled with the chosen colours
    rnd = random.Random(f"Oxidised pyrite{rich}")
    m, cubes = set(), []
    for _ in range(6 if rich == 0 else 16):                    # same random sequence as pyrite_rust
        x, y = rnd.randrange(16), rnd.randrange(16)
        cubes.append((x, y))
        for dx in range(-1, 3):
            for dy in range(-1, 3):
                if rnd.random() < 0.75:
                    m.add(((x + dx) % 16, (y + dy) % 16))
    g = Canvas()
    shade(g, m, rnd)
    img = ground.copy()
    for yy in range(16):
        for xx in range(16):
            k = g.get(xx, yy)
            if (xx, yy) in m:
                img.putpixel((xx, yy), gold[k])                 # lit edge #2, grain #3-#5 (lifted gold)
            elif k == 6:
                img.putpixel((xx, yy), sand[5])                 # shadow on the sandstone
    for x, y in cubes:                                          # pyrite cube
        for (dx, dy), col in (((0, 0), BRASS[0]), ((1, 0), BRASS[1]), ((0, 1), BRASS[2]), ((1, 1), BRASS[3])):
            img.putpixel(((x + dx) % 16, (y + dy) % 16), col)
    return img


def main():
    imgs = {r: paint(r) for r in (0, 1)}
    sheet = Image.new("RGB", (3 * 112 + 8, 2 * 112 + 8), (30, 30, 36))
    ground = Image.open(T / "bleached_sandstone/bleached_sandstone_bleach0.png").convert("RGB")
    for r, img in imgs.items():
        field = Image.new("RGB", (48, 16))                     # bank: sandstone | richness r | sandstone
        field.paste(ground, (0, 0)); field.paste(img, (16, 0)); field.paste(ground, (32, 0))
        sheet.paste(img.resize((96, 96), Image.NEAREST), (8, 8 + r * 112))
        t = Image.new("RGB", (48, 48))
        for a in range(3):
            for b in range(3):
                t.paste(img, (a * 16, b * 16))
        sheet.paste(t.resize((96, 96), Image.NEAREST), (120, 8 + r * 112))
        sheet.paste(field.resize((96, 32), Image.NEAREST), (232, 40 + r * 112))
    sheet.save(P / "build/previews/aurum_ore_paint.png")
    tmp = P / "build/previews/aurum_ore_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    for r, img in imgs.items():
        img.save(tmp / f"aurum_ore_richness{r}.png")
    print("preview: build/previews/aurum_ore_paint.png")
    if not APPLY:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_aurum_ore")
    for r, img in imgs.items():
        dst = T / f"aurum_ore/aurum_ore_richness{r}.png"
        (bk / dst.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dst, bk / dst.relative_to(P))
        if not art_guard.is_ours(dst) and "--force" in sys.argv:
            dst.unlink()
        art_guard.save(img, dst)
    print("applied; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
