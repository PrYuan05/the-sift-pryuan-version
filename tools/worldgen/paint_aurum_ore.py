"""aurum_ore (Lullaby Hills river bed) - oxidised pyrite, exactly candidate F of art_requests/aurum_ore_candidates.png
(user): small bright pyrite cubes inside rusty limonite halos in a grey host rock, in the original ore's own grey and gold.
Usage: python -I tools/worldgen/paint_aurum_ore.py <project> [--apply [--force]]

richness 0 / 1 are the candidate sheet's tiles (same function, same seeds); 2 / 3 add more cubes until the halos merge;
4 is solid ore (user): no host rock left, a limonite mass with pyrite cubes, each with a 1 px shadow under it.
Candidates and their comparison: tools/worldgen/aurum_candidates.py.
"""
import datetime, random, shutil, sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
T = P / "src/main/resources/assets/pysift/textures/block"
sys.path.insert(0, str(P / "tools"))
sys.path.insert(0, str(P / "tools/worldgen"))
import art_guard
from aurum_candidates import colours, pyrite_rust, render, C1, C2, C3, C4, C5, C6
from paint_void_stone import Canvas, mottle, ALL

SRC = P / ".texture_backups/20261030-171615_paint_aurum_ore/src/main/resources/assets/pysift/textures/block/aurum_ore"   # the original ore
LEVELS = range(5)


def solid(gold):
    """richness 4: limonite grain over the whole tile, pyrite cubes on a jittered grid so they never overlap."""
    rnd = random.Random("Oxidised pyrite4")
    g = Canvas()
    mottle(g, rnd, ALL, {C3: 2, C5: 5}, base_max=0.4)   # darker grain: the cubes read on it
    for gy in range(4):
        for gx in range(4):
            if rnd.random() < 0.2:
                continue
            x, y = gx * 4 + rnd.randrange(2) + (gy % 2) * 2, gy * 4 + rnd.randrange(2)
            for (dx, dy), c in (((0, 0), C1), ((1, 0), C2), ((0, 1), C3), ((1, 1), C5)):
                g.set(x + dx, y + dy, c)
            g.set(x, y + 2, C6)
            g.set(x + 1, y + 2, C6)
    return g.image(gold)


def paint(rich, grey, gold):
    return solid(gold) if rich == 4 else render(pyrite_rust, rich, grey, gold, f"Oxidised pyrite{rich}")


def main():
    grey, gold = colours(SRC)                                  # colours from the ORIGINAL ore texture, not our output
    imgs = {r: paint(r, grey, gold) for r in LEVELS}
    sheet = Image.new("RGB", (2 * 112 + 8, len(imgs) * 112 + 8), (30, 30, 36))
    for r, img in imgs.items():
        sheet.paste(img.resize((96, 96), Image.NEAREST), (8, 8 + r * 112))
        t = Image.new("RGB", (48, 48))
        for a in range(3):
            for b in range(3):
                t.paste(img, (a * 16, b * 16))
        sheet.paste(t.resize((96, 96), Image.NEAREST), (120, 8 + r * 112))
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
        if dst.exists():
            (bk / dst.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, bk / dst.relative_to(P))
            if not art_guard.is_ours(dst) and "--force" in sys.argv:
                dst.unlink()
        art_guard.save(img, dst)
    print("applied; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
