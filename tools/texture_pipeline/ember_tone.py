"""Every ember-stone-type block takes ember_stone_heat4's exact colours for its orange-brown earth (user).
Usage: python -I tools/texture_pipeline/ember_tone.py <project> [--groups=a,b] [--apply]

Per group (one block family, so all its faces share one mapping), the orange-brown pixels (hue 6-50 deg, saturation
>= 0.3) are ranked by lightness together; the rank quantiles are cut in the proportions the colours have in
ember_stone_heat4 and each pixel takes the palette colour of its quantile. Everything else (the pink ember stone, grey
void stone, teal caps, dark grout) is left alone and shapes never change, so the heat stages keep their difference.
Read-only unless --apply (backups in .texture_backups/). Review: build/texture_pipeline/out/ember_tone_review.png
"""
import colorsys, datetime, shutil, sys
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
T = P / "src/main/resources/assets/pysift/textures/block"
sys.path.insert(0, str(P / "tools"))
import art_guard

REF = T / "ember_stone/ember_stone_heat4.png"
GROUPS = {
    "ember_stone": [f"ember_stone/ember_stone_heat{s}" for s in ("1_a", "2_a", "2_b", "3_a")],
    "ember_basalt": ["ember_basalt/ember_basalt", "ember_basalt/ember_basalt_speckled", "ember_basalt_bricks/ember_basalt_bricks",
                     "ember_basalt_bricks/chiseled_ember_basalt_bricks"],
    # the smooth chiseled top is all one dark brown: ranked with the family it would all fall on heat4's darkest salmon
    "ember_basalt_top": ["ember_basalt_bricks/chiseled_ember_basalt_bricks_top"],
    "crimson_capped": ["crimson_capped_ember_stone/crimson_capped_ember_stone_side", "crimson_capped_ember_stone/crimson_capped_ember_stone_top",
                       "crimson_capped_void_stone/crimson_capped_ember_stone_side", "crimson_capped_void_stone/crimson_capped_ember_stone_top"],
    "gray_capped": ["gray_capped_void_stone/gray_capped_ember_stone_side", "gray_capped_void_stone/gray_capped_ember_stone_top_a",
                    "gray_capped_void_stone/gray_capped_ember_stone_top_b"],
    "warm_capped": ["warm_capped_ember_stone/warm_capped_ember_stone_side", "warm_capped_ember_stone/warm_capped_ember_stone_top"],
}
lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def in_tone(c):
    if c[3] == 0:
        return False
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c[:3]))
    return 6 <= h * 360 <= 50 and s >= 0.3 and v >= 0.3


def palette():
    """ember_stone_heat4's colours, darkest first, with the share of the tile each covers."""
    n = Counter(Image.open(REF).convert("RGB").get_flattened_data())
    cols = sorted(n, key=lum)
    return cols, [n[c] / 256 for c in cols]


def remap(names):
    cols, shares = palette()
    imgs = {n: Image.open(T / f"{n}.png").convert("RGBA") for n in names}
    weight = Counter(c[:3] for im in imgs.values() for c in im.get_flattened_data() if in_tone(c))
    total, acc, edges = sum(weight.values()), 0.0, []
    for s in shares:
        acc += s
        edges.append(acc)
    to, seen = {}, 0
    for c in sorted(weight, key=lum):                   # quantile of the colour's middle pixel -> palette colour
        q = (seen + weight[c] / 2) / total
        to[c] = cols[next(i for i, e in enumerate(edges) if q <= e + 1e-9)]
        seen += weight[c]
    out = {}
    for n, im in imgs.items():
        o = im.copy()
        o.putdata([(*to[c[:3]], c[3]) if in_tone(c) else c for c in im.get_flattened_data()])
        out[n] = o
    return imgs, out


def tile(im):
    t = Image.new("RGBA", (48, 48))
    for a in range(3):
        for b in range(3):
            t.paste(im, (a * 16, b * 16))
    return t


def review(results):
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 12)
    fb = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 14)
    S = 64
    rows = [(g, n, before[n], after[n]) for g, (before, after) in results.items() for n in before]
    sheet = Image.new("RGB", (40 + 4 * (S + 8) + 320, 64 + len(rows) * (S + 10)), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    d.text((50, 14), "ember_stone_heat4 色票套用對照：原圖｜套用後｜原圖 3×3｜套用後 3×3", fill=(240, 232, 205), font=fb)
    sheet.paste(Image.open(REF).convert("RGB").resize((32, 32), Image.NEAREST), (10, 8))
    y = 64
    for g, n, a, b in rows:
        x = 10
        for im in (a, b, tile(a), tile(b)):
            bg = Image.new("RGBA", im.size, (30, 30, 36, 255))
            bg.alpha_composite(im)
            sheet.paste(bg.convert("RGB").resize((S, S), Image.NEAREST), (x, y))
            x += S + 8
        d.text((x + 6, y + 4), f"[{g}]", fill=(255, 210, 140), font=fb)
        d.text((x + 6, y + 24), n, fill=(210, 220, 235), font=f)
        y += S + 10
    out = P / "build/texture_pipeline/out/ember_tone_review.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def main():
    sel = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--groups=")), list(GROUPS))
    results = {g: remap(GROUPS[g]) for g in sel}
    print("review:", review(results).relative_to(P))
    if "--apply" not in sys.argv:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_ember_tone")
    for g, (_, after) in results.items():
        for n, im in after.items():
            dst = T / f"{n}.png"
            (bk / dst.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, bk / dst.relative_to(P))
            if not art_guard.is_ours(dst):
                dst.unlink()                            # the user asked for these faces to be refilled
            art_guard.save(im, dst)
    print("applied; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
