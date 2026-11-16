"""Colour table for plants tinted by the block under them (ember_grass, tall_ember_grass, abyss_grass, puff_grass).
Usage: python -I tools/worldgen/make_floor_tints.py <project>

For every block in #minecraft:supports_vegetation the average colour of its TOP face texture is taken (the auto colour)
and its family is read from that colour's hue (what the plant actually stands on, not the block name):
  red / crimson top -> pale peach pink           purple top -> two colours, lilac and pale yellow (FloorTint mixes them
  pale pink top -> pink                          in patches by position, so a purple field is part purple, part yellow)
  yellow / sand top -> yellow-orange             teal top -> teal
Greyish tops (saturation < GREY_SAT) fall back to the block name (violet / slate / void -> purple, crimson -> peach).
Each family colour is mixed with FAMILY_WEIGHT of the family and the rest auto colour, then kept light (MIN_VALUE) so
the grey blade textures (made light on purpose) end up pastel rather than muddy.
Writes src/client/java/pryuan05/pysift/client/FloorTints.java and a swatch preview."""
import sys, json, colorsys
from pathlib import Path
from PIL import Image, ImageDraw

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift"
TAG = P / "src/main/resources/data/minecraft/tags/block/supports_vegetation.json"
OUT = P / "src/client/java/pryuan05/pysift/client/FloorTints.java"
PREVIEW = P / "build/texture_pipeline/out/floor_tints.png"
PEACH = [(248, 176, 164)]                       # 淡桃紅 (user: crimson ground)
PURPLE_YELLOW = [(200, 160, 244), (246, 224, 128)]   # user: violet ground part purple, part yellow
TEAL = [(110, 222, 204)]
PINK = [(204, 86, 86)]
SAND = [(240, 200, 110)]
GREY_SAT = 0.15
NAME_FALLBACK = [(("violet", "slate", "void", "abyssal"), PURPLE_YELLOW), (("crimson", "ember"), PEACH)]
FAMILY_WEIGHT = 0.85
MIN_VALUE = 0.88
MAX_SAT = 0.45
TOP_KEYS = ("up", "top", "end", "all", "particle")


def lj(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def model_textures(ref):
    ns, path = ref.split(":")
    j = lj(A / "models" / (path + ".json")) if ns == "pysift" else {}
    tex = model_textures(j["parent"]) if ns == "pysift" and "parent" in j else {}
    return {**tex, **j.get("textures", {})}


def top_texture(block):
    bs = lj(A / f"blockstates/{block}.json")
    variants = bs.get("variants", {})
    key = next((k for k in variants if "facing=up" in k), next(iter(variants)))
    v = variants[key]
    v = v[0] if isinstance(v, list) else v
    tex = model_textures(v["model"])
    for k in TOP_KEYS:
        t = tex.get(k)
        while t and t.startswith("#"):
            t = tex.get(t[1:])
        if t:
            return t
    raise SystemExit(f"no top texture for {block}")


def average(ref):
    ns, path = ref.split(":")
    im = Image.open(A / "textures" / (path + ".png")).convert("RGBA")
    im = im.crop((0, 0, im.width, im.width))
    px = [p for p in im.get_flattened_data() if p[3] > 0]
    return tuple(sum(p[i] for p in px) / len(px) for i in range(3))


def family(block, auto):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in auto))
    h *= 360
    if s < GREY_SAT:
        return next((c for keys, c in NAME_FALLBACK if any(k in block for k in keys)), None)
    if (h >= 330 or h < 20) and v > 0.8 and s < 0.45:
        return PINK                       # pale pink (pink loam)
    if h >= 330 or h < 35:
        return PEACH                      # red / crimson / brown earth
    if h < 70:
        return SAND
    if 240 <= h < 330:
        return PURPLE_YELLOW              # purple rock
    if 150 <= h < 240:
        return TEAL                       # teal caps
    return None


def light(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    return tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, min(s, MAX_SAT), max(v, MIN_VALUE)))


def stylise(block, auto):
    fam = family(block, auto)
    if fam is None:
        return [light(auto)], False
    return [light(tuple(f[i] * FAMILY_WEIGHT + auto[i] * (1 - FAMILY_WEIGHT) for i in range(3))) for f in fam], True


def main():
    blocks = [v.split(":")[1] for v in lj(TAG)["values"] if v.startswith("pysift:")]
    rows = []
    for b in blocks:
        auto = average(top_texture(b))
        cols, fam = stylise(b, auto)
        rows.append((b, auto, cols, fam))
    hexes = lambda cols: ", ".join(f"0xFF{c[0]:02X}{c[1]:02X}{c[2]:02X}" for c in cols)
    entries = ",\n".join(f'            Map.entry("pysift:{b}", new int[]{{{hexes(c)}}})' for b, _, c, _ in rows)
    OUT.write_text(f"""package pryuan05.pysift.client;

import java.util.Map;

/**
 * 地板方塊 → 草色（ARGB）。由 tools/worldgen/make_floor_tints.py 產生，請改腳本後重跑，不要手改。
 * 每個地板取頂面貼圖平均色，依色相分家族：赤紅→淡桃紅、紫岩→紫／淡黃兩色（FloorTint 依位置分區混色）、
 * 青色頂面→青、粉壤→粉紅、沙→黃橙；顏色都偏淡，配合淺灰的草葉貼圖。
 */
public final class FloorTints {{
    public static final Map<String, int[]> COLORS = Map.ofEntries(
{entries}
    );

    private FloorTints() {{
    }}
}}
""", encoding="utf-8")
    S = 28
    img = Image.new("RGB", (560, S * len(rows) + 4), (30, 30, 34))
    d = ImageDraw.Draw(img)
    for i, (b, auto, cols, fam) in enumerate(rows):
        y = 2 + i * S
        d.rectangle([4, y, 4 + S - 4, y + S - 4], fill=tuple(round(c) for c in auto))
        for j, c in enumerate(cols):
            d.rectangle([36 + j * S, y, 36 + j * S + S - 4, y + S - 4], fill=c)
        d.text((100, y + 6), f"{b}{'' if fam else '  (auto)'}", fill=(230, 230, 230))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    img.save(PREVIEW)
    print(f"{len(rows)} floors -> {OUT.relative_to(P)}")


if __name__ == "__main__":
    main()
