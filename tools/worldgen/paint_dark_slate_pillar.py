"""dark_slate_pillar in dark_slate's current colours (user). Usage: python -I tools/worldgen/paint_dark_slate_pillar.py <project> [--apply]

The pillar (built by build_corrupted_slate_pillar.py: concentric square rings on the ends, vertical flutes on the side) was
purple (avg #534A5C) while dark_slate is now grey-green (dark_slate_k avg #666D68). The structure is kept exactly: every
pixel keeps its rank in the pillar's own luminance distribution (one shared mapping for top, side and bottom, so the ends
and the side stay consistent) and is put on the 7-step ladder built from dark_slate_k's grey-green; the ladder's dark
steps turn towards blue (skill 2.2), which brings back the faint violet the dark slate has in its shadows.
"""
import colorsys, datetime, shutil, sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
T = P / "src/main/resources/assets/pysift/textures/block"
sys.path.insert(0, str(P / "tools")); sys.path.insert(0, str(P / "tools/worldgen"))
import art_guard
from paint_pink_strata import ramp, lum
from paint_violet_slate import slate_family

SPAN = 0.22
FILES = [T / "dark_slate_pillar" / f"dark_slate_pillar_{k}.png" for k in ("top", "side", "bottom")]
ORIG = P / ".texture_backups/20261030-pillar_original/src/main/resources/assets/pysift/textures/block/dark_slate_pillar"


def main():
    src = ORIG if ORIG.exists() else FILES[0].parent                    # always repaint from the original purple textures
    ims = {f.name: Image.open(src / f.name).convert("RGB") for f in FILES}
    allpx = sorted(lum(c) for im in ims.values() for c in im.get_flattened_data())
    cuts = [allpx[int(len(allpx) * q)] for q in (0.04, 0.14, 0.34, 0.62, 0.84, 0.96)]     # 7 ranks: dark ... light
    k = [c[:3] for c in Image.open(T / "dark_slate/dark_slate_k.png").convert("RGBA").get_flattened_data() if slate_family(c[:3]) == "grey"]
    pal = ramp(k, SPAN)[::-1]                                             # ramp(): index 0 = lightest -> reversed: dark first
    # user: the dark steps take dark_slate's own purple (hue / saturation of its purple patches, pooled over the fades),
    # solved to the same luminance as the grey step they replace; the 4th step is the half-way mix, the lights stay grey-green
    pur = [c[:3] for x in "koprstuv" for c in Image.open(T / f"dark_slate/dark_slate_{x}.png").convert("RGBA").get_flattened_data()
           if slate_family(c[:3]) == "purple"]
    pr, pg, pb = (sum(c[i] for c in pur) / len(pur) / 255 for i in range(3))
    ph, ps, _ = colorsys.rgb_to_hsv(pr, pg, pb)
    def purple_at(target):
        lo, hi = 0.0, 1.0
        for _ in range(40):
            v = (lo + hi) / 2
            rgb = tuple(round(x * 255) for x in colorsys.hsv_to_rgb(ph, min(0.9, ps * 1.05), v))
            lo, hi = (v, hi) if lum(rgb) < target else (lo, v)
        return rgb
    for i in range(3):
        pal[i] = purple_at(lum(pal[i]))
    pal[3] = tuple((a_ + b_) // 2 for a_, b_ in zip(pal[3], purple_at(lum(pal[3]))))
    out = {}
    for name, im in ims.items():
        new = Image.new("RGB", (16, 16))
        new.putdata([pal[sum(lum(c) > t for t in cuts)] for c in im.get_flattened_data()])
        out[name] = new
    s = Image.new("RGB", (3 * 100 + 8, 2 * 100 + 8), (30, 30, 36))
    for i, (name, new) in enumerate(out.items()):
        s.paste(ims[name].resize((96, 96), Image.NEAREST), (4 + i * 100, 4))
        s.paste(new.resize((96, 96), Image.NEAREST), (4 + i * 100, 104))
    s.save(P / "build/previews/dark_slate_pillar_paint.png")
    col = Image.new("RGB", (16 * 4, 16 * 6))                                  # pillar column next to dark slate, 3 layers
    ds = [Image.open(T / f"dark_slate/dark_slate_{x}.png").convert("RGB") for x in "kopr"]
    for y in range(6):
        for x in range(4):
            col.paste(out["dark_slate_pillar_side.png"] if x in (1, 2) and 0 < y < 5 else
                      out["dark_slate_pillar_top.png"] if x in (1, 2) else ds[(x + y) % 4], (x * 16, y * 16))
    col.resize((col.width * 4, col.height * 4), Image.NEAREST).save(P / "build/previews/dark_slate_pillar_wall.png")
    print("preview: build/previews/dark_slate_pillar_paint.png, dark_slate_pillar_wall.png")
    if not APPLY:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_dark_slate_pillar")
    for f in FILES:
        (bk / f.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, bk / f.relative_to(P))
        f.unlink()                                                          # another session's file: replaced on request
        art_guard.save(out[f.name], f)
    print("applied; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
