"""Chiseled blocks get top / bottom faces like vanilla (chiseled sandstone = smooth sandstone on the ends): a cube_column
model, side = the chiseled texture, end = the stone's smooth texture.
Usage: python -I tools/texture_pipeline/chiseled_tops.py <project> [--apply]

  - the stone has a smooth block (SMOOTH below)  -> end = that texture
  - otherwise -> end = <chiseled texture>_top.png, painted here in the smooth style (flat panel, very soft mottling,
    1 px bevel frame lit top / left, shaded bottom / right) in the stone's own colours (quantiles of its bricks texture,
    or of the chiseled texture when there are no bricks)
Models that are already a cube_column are left alone. New PNGs go through tools/art_guard.py.
building_sets.py calls smooth_top() / column_model() for new sets, so they are born with the right ends.
"""
import colorsys, json, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

VSCALE = [1.16, 1.09, 1.035, 1.0, 0.965, 0.88, 0.78]      # #1 .. #7 as value factors of the stone's median colour
HSHIFT = [+6, +4, +2, 0, -2, -5, -8]                       # light steps a touch warmer, dark ones cooler (skill 2.2)
SMOOTH = {"chiseled_void_stone_bricks": "pysift:block/void_stone/smooth_void_stone"}


def lum(c): return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def stone_palette(img):
    """Seven steps around the median-luminance colour of the stone, fixed value ratios: every end gets the same soft but
    visible bevel even when the source texture has only a few colours."""
    px = sorted((c[:3] for c in img.convert("RGBA").get_flattened_data() if c[3] > 0), key=lum)
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in px[len(px) // 2]))
    return [tuple(round(x * 255) for x in colorsys.hsv_to_rgb((h * 360 + dh) % 360 / 360, s * (0.85 if k < 2 else 1.0),
                                                              min(1.0, v * vs)))
            for k, (vs, dh) in enumerate(zip(VSCALE, HSHIFT))]


def smooth_top(img, seed):
    """16 x 16 smooth-stone end in the colours of img (the stone's bricks or chiseled texture)."""
    pal = stone_palette(img)                 # pal[0] = #1 (lightest) ... pal[6] = #7
    rnd = random.Random(seed)
    g = [[3] * 16 for _ in range(16)]        # #4 base
    for _ in range(18):                      # very soft 2-3 px mottles of the neighbouring steps
        x, y, col = rnd.randrange(1, 14), rnd.randrange(1, 14), rnd.choice((2, 2, 4))
        for dx, dy in rnd.choice((((0, 0), (1, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)), ((0, 0), (1, 0), (1, 1)))):
            g[y + dy][x + dx] = col
    for i in range(16):                      # bevel frame
        g[0][i], g[i][0] = 2, 2
        g[15][i], g[i][15] = 5, 5
    g[0][0], g[15][15], g[0][15], g[15][0] = 1, 6, 3, 3
    out = Image.new("RGB", (16, 16))
    out.putdata([pal[g[y][x]] for y in range(16) for x in range(16)])
    return out


def column_model(side, end):
    return {"parent": "minecraft:block/cube_column", "textures": {"end": end, "side": side}}


def main():
    P = Path(sys.argv[1]).resolve()
    A = P / "src/main/resources/assets/pysift"
    sys.path.insert(0, str(P / "tools"))
    import art_guard
    apply = "--apply" in sys.argv
    done, previews = [], []
    for bs in sorted((A / "blockstates").glob("chiseled_*.json")):
        var = json.loads(bs.read_text(encoding="utf-8"))["variants"]
        entry = next(iter(var.values()))
        entry = entry[0] if isinstance(entry, list) else entry
        mpath = A / "models" / (entry["model"].split(":", 1)[1] + ".json")
        model = json.loads(mpath.read_text(encoding="utf-8"))
        if model.get("parent") != "minecraft:block/cube_all":
            continue
        side = model["textures"]["all"]
        side_png = A / "textures" / (side.split(":", 1)[1] + ".png")
        if bs.stem in SMOOTH:
            end = SMOOTH[bs.stem]
            top_img = Image.open(A / "textures" / (end.split(":", 1)[1] + ".png")).convert("RGB")
        else:
            bricks = side_png.with_name(side_png.name.replace("chiseled_", "", 1))
            top_img = smooth_top(Image.open(bricks if bricks.exists() else side_png), bs.stem)
            end = side + "_top"
            if apply:
                art_guard.save(top_img, side_png.with_name(side_png.stem + "_top.png"))
        if apply:
            mpath.write_text(json.dumps(column_model(side, end), indent=2) + "\n", encoding="utf-8")
        done.append(bs.stem)
        previews.append((bs.stem, Image.open(side_png).convert("RGB").crop((0, 0, 16, 16)), top_img))
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 10)
    S, per = 48, 10
    sheet = Image.new("RGB", (per * (2 * S + 14) + 10, ((len(previews) + per - 1) // per) * (S + 20) + 8), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    for i, (name, side_img, top_img) in enumerate(previews):
        x, y = 6 + (i % per) * (2 * S + 14), 4 + (i // per) * (S + 20)
        sheet.paste(side_img.resize((S, S), Image.NEAREST), (x, y))
        sheet.paste(top_img.resize((S, S), Image.NEAREST), (x + S + 2, y))
        d.text((x, y + S + 2), name.replace("chiseled_", "")[:20], fill=(200, 205, 215), font=f)
    sheet.save(P / "build/previews/chiseled_tops.png")
    print(("applied: " if apply else "would change: ") + str(len(done)), "chiseled blocks; preview build/previews/chiseled_tops.png")


if __name__ == "__main__":
    main()
