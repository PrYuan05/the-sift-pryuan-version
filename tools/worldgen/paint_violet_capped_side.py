"""violet_capped_dark_slate side: the violet cap draped over dark slate, made to join the blocks around it (user).
Usage: python -I tools/worldgen/paint_violet_capped_side.py <project> [--apply]

On the violet slate abyss surface this block's top face is violet_strata_e and the block under it is dark_slate fade 0
(dark_slate_k). Like a vanilla grass block side (it replaces the old dark_slate_q side, user): a cap draped 3-7 px over the
top that takes the TOP face's own pixels, so it continues the top; everything
under the cap is dark_slate_k's own pixels, so the bottom edge tiles into the block below without a seam. The cap's lowest
pixel in every column is one step darker, and the slate pixel right under it gets a shadow step.
"""
import shutil, sys, datetime
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
T = P / "src/main/resources/assets/pysift/textures/block"
sys.path.insert(0, str(P / "tools")); sys.path.insert(0, str(P / "tools/worldgen"))
import art_guard
from paint_pink_strata import lum

OUT = T / "violet_capped_dark_slate/violet_capped_dark_slate_side.png"


def main():
    top = Image.open(T / "violet_strata/violet_strata_e.png").convert("RGB")
    k = Image.open(T / "dark_slate/dark_slate_k.png").convert("RGB")
    # the cap drapes 3-7 px, wavering column by column like the original's ragged edge (ends match, so it tiles sideways)
    DEPTH = [4, 5, 5, 6, 5, 3, 4, 5, 7, 6, 5, 4, 3, 4, 5, 4]
    cap = [[y < DEPTH[x] for x in range(16)] for y in range(16)]
    t_px = sorted(top.get_flattened_data(), key=lum)
    top_dark = t_px[len(t_px) // 5]                          # one step under the cap's middle, not its darkest
    k_px = sorted(k.get_flattened_data(), key=lum)
    k_shadow = k_px[len(k_px) // 4]                          # a soft shadow under the cap
    out = Image.new("RGB", (16, 16))
    for y in range(16):
        for x in range(16):
            if cap[y][x]:
                edge = y == 15 or not cap[y + 1][x]
                out.putpixel((x, y), top_dark if edge else top.getpixel((x, y)))
            else:
                under_cap = y > 0 and cap[y - 1][x]
                out.putpixel((x, y), k_shadow if under_cap else k.getpixel((x, y)))
    W = 6
    s = Image.new("RGB", (16 * W, 16 * 5))
    for x in range(W):
        s.paste(top, (x * 16, 0)); s.paste(out, (x * 16, 16))
        for r in range(2, 5):
            s.paste(k, (x * 16, r * 16))
    s.resize((s.width * 5, s.height * 5), Image.NEAREST).save(P / "build/previews/violet_surface_stack.png")
    print("preview: build/previews/violet_surface_stack.png")
    if APPLY:
        bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_violet_capped_side")
        (bk / OUT.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OUT, bk / OUT.relative_to(P))
        art_guard.save(out, OUT)
        print("applied; backup in", bk.relative_to(P))


if __name__ == "__main__":
    main()
