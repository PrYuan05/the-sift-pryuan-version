"""Harmonize the red rock of void_capped_crimson_01 with crimson_vein_stone (user request, Lullaby Hills).

  python -I tools/texture_pipeline/harmonize_crimson.py <project> review   -> build/texture_pipeline/out/crimson_harmonize_review.png
  python -I tools/texture_pipeline/harmonize_crimson.py <project> apply    -> writes the PNGs, backs up to .texture_backups/crimson_harmonize/

Only the red / peach-pink pixels move (hue 320..40 deg, saturation > 0.25, value > 0.3): the void-black cap, the dark grey
spots of crimson vein stone and transparent pixels stay. Both sides get the same hue (the circular mean of the two
measured hues); void-capped red keeps its saturation and is lifted a little towards peach-pink, crimson vein stone is
darkened and its saturation pulled towards the void side. Every pixel keeps its offset from its group's mean, so the
pattern stays. ember_stone (which used to share crimson_vein_stone_crimson_spread4's pixels) is not touched."""
import colorsys, math, shutil, sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1])
MODE = sys.argv[2] if len(sys.argv) > 2 else "review"
T = P / "src/main/resources/assets/pysift/textures/block"
VOID = ["void_capped_crimson_01/void_capped_crimson_01_side.png", "void_capped_crimson_01/void_capped_crimson_01_bottom.png"]
VEIN = [f"crimson_vein_stone/crimson_vein_stone_crimson_spread{s}.png" for s in ("1_a", "1_b", "2", "3", "4")]
EMBER = "ember_stone/ember_stone_heat0_a.png"     # shown for comparison only (it keeps its colours)
# targets (value / saturation means of the red pixels after the change)
VOID_VALUE, VOID_SAT_GAIN = 0.71, 1.05      # void red: a touch brighter, a touch more saturated -> peach-pink
VEIN_VALUE, VEIN_SAT_MIX = 0.66, 0.6        # vein: darker; saturation 60 % of the way towards the void side


def is_red(r, g, b, a):
    if a < 128:
        return False
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return s > 0.25 and v > 0.3 and (h * 360 >= 320 or h * 360 <= 40)


def red_stats(files):
    hx = hy = s_sum = v_sum = 0.0
    n = 0
    for f in files:
        for px in Image.open(T / f).convert("RGBA").get_flattened_data():
            if is_red(*px):
                h, s, v = colorsys.rgb_to_hsv(px[0] / 255, px[1] / 255, px[2] / 255)
                hx += math.cos(h * 2 * math.pi)
                hy += math.sin(h * 2 * math.pi)
                s_sum += s
                v_sum += v
                n += 1
    return (math.atan2(hy, hx) / (2 * math.pi)) % 1.0, s_sum / n, v_sum / n


def shift(files, mean_h, mean_s, mean_v, hue, sat, val):
    out = {}
    for f in files:
        im = Image.open(T / f).convert("RGBA")
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                if not is_red(r, g, b, a):
                    continue
                h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                dh = ((h - mean_h + 0.5) % 1.0) - 0.5                 # keep each pixel's offset from the mean
                nh = (hue + dh) % 1.0
                ns = min(1.0, max(0.0, s * sat / mean_s))
                nv = min(1.0, max(0.0, v * val / mean_v))
                nr, ng, nb = colorsys.hsv_to_rgb(nh, ns, nv)
                px[x, y] = (round(nr * 255), round(ng * 255), round(nb * 255), a)
        out[f] = im
    return out


vh, vs, vv = red_stats(VOID)
nh, ns, nv = red_stats(VEIN)
hue = (math.atan2(math.sin(vh * 2 * math.pi) + math.sin(nh * 2 * math.pi),
                  math.cos(vh * 2 * math.pi) + math.cos(nh * 2 * math.pi)) / (2 * math.pi)) % 1.0
void_sat = min(0.95, vs * VOID_SAT_GAIN)
vein_sat = ns + (vs - ns) * VEIN_SAT_MIX
new = {**shift(VOID, vh, vs, vv, hue, void_sat, VOID_VALUE), **shift(VEIN, nh, ns, nv, hue, vein_sat, VEIN_VALUE)}
print(f"void red: hue {vh * 360:.1f} sat {vs:.2f} val {vv:.2f} -> hue {hue * 360:.1f} sat {void_sat:.2f} val {VOID_VALUE:.2f}")
print(f"vein pink: hue {nh * 360:.1f} sat {ns:.2f} val {nv:.2f} -> hue {hue * 360:.1f} sat {vein_sat:.2f} val {VEIN_VALUE:.2f}")

if MODE == "review":
    S = 8
    names = VOID + VEIN + [EMBER]

    def wall(side_img, vein_img):
        """3 x 3 blocks: a capped top row (side texture) over two rows of crimson vein stone - how a cliff will look."""
        w = Image.new("RGBA", (48 * S // 2, 48 * S // 2))
        for i in range(3):
            w.paste(side_img.crop((0, 0, 16, 16)).resize((8 * S, 8 * S), Image.NEAREST), (i * 8 * S, 0))
            for j in (1, 2):
                w.paste(vein_img.crop((0, 0, 16, 16)).resize((8 * S, 8 * S), Image.NEAREST), (i * 8 * S, j * 8 * S))
        return w

    cols = len(names)
    sheet = Image.new("RGBA", (cols * (16 * S + 8) + 2 * (24 * S + 16) + 40, 2 * (16 * S + 30) + 40), (32, 30, 36, 255))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    original = {f: Image.open(T / f).convert("RGBA") for f in names}
    for row, (label, imgs) in enumerate((("before", original), ("after", {**original, **new}))):
        y = 20 + row * (16 * S + 30)
        d.text((4, y - 14), label, fill=(240, 240, 240))
        for i, f in enumerate(names):
            sheet.paste(imgs[f].crop((0, 0, 16, 16)).resize((16 * S, 16 * S), Image.NEAREST), (i * (16 * S + 8), y))
        x = cols * (16 * S + 8) + 20
        sheet.paste(wall(imgs[VOID[0]], imgs[VEIN[-1]]), (x, y))
        sheet.paste(wall(imgs[VOID[0]], imgs[VEIN[-2]]), (x + 24 * S + 16, y))
    out = P / "build/texture_pipeline/out/crimson_harmonize_review.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print("review:", out)
elif MODE == "apply":
    backup = P / ".texture_backups/crimson_harmonize"
    for f, im in new.items():
        dst = backup / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(T / f, dst)
        im.save(T / f)
        print("wrote", f)
else:
    sys.exit(__doc__)
