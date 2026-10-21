"""柔和草的色盤對應（gradient map）：灰階母版的每個深淺等級，由淺到深對應到色盤的一個顏色。
Usage: python -I tools/worldgen/soft_grass_palette.py [參考截圖] [--apply]
  預覽 build/previews/soft_grass_palette.png；--apply 寫入三組草的貼圖，模型改成原版 minecraft:block/cross（不染色）。

使用者選擇：原版十字＋預先上色。三組草各自一張已上色的貼圖，顏色跟著草的種類（生態域），不跟著腳下那一格：
  crimson_*      粉色色盤（取自參考截圖）
  soft_violet_*  粉色色盤的色相轉到紫晶區地面（violet_capped_dark_slate 頂面）的色相，鮮豔度與深淺不變；葉形＝母版左右鏡像
  soft_dune_*    粉色色盤的色相轉到沙丘地面（amber_sand）的色相；葉形＝鏡像後葉尖壓低 2 px

母版（tools/worldgen/art/soft_grass_src/）是使用者畫的灰階：7 個等級 160 150 138 126 119 108 92（由淺到深）。
粉色色盤取自使用者給的參考截圖（影片裡的粉紅草叢），一樣由淺到深 7 色。
"""
import sys, json, colorsys, shutil, datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

P = Path(__file__).resolve().parents[2]
SRC = P / "tools/worldgen/art/soft_grass_src"
PREVIEW = P / "build/previews/soft_grass_palette.png"
A = P / "src/main/resources/assets/pysift"
VEG = A / "textures/block/vegetation"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_soft_grass_palette")
# 每組草的色盤：("pink",) 粉色本身；("rotate", 地面) 粉色色盤轉到地面色相；("relative", 地面色, 飽和加成, 明度提升)
#   relative：把「粉色色盤 ↔ 赤紅地板 #F47D89」的亮暗、飽和關係套到這種地板上（使用者：紫色要專門符合地板的色相）
SETS = {
    "crimson": ("pink",),
    "soft_violet": ("relative", "#4F4657", 1.4, 0.22),   # 紫晶區地板很暗很灰：保持地板色相，稍微提亮才看得到
    "soft_dune": ("rotate", "amber_sand"),
    "soft_teal": ("relative", "#43B6B0", 1.0, 0.0),      # 青色地板（尖柱頂 capped_crimson_strata、abyssal / silted strata）
}
SHAPES = {"crimson": (False, 0), "soft_violet": (True, 0), "soft_dune": (True, 2), "soft_teal": (False, 1)}   # (鏡像, 葉尖壓低 px)
PINK_FLOOR = "#F47D89"   # 粉色色盤所在的赤紅地板（crimson_capped_crimson_strata_2 頂面平均色）
NAMES_ZH = {"crimson": "柔和赤紅", "soft_violet": "柔和紫晶", "soft_dune": "柔和沙丘", "soft_teal": "柔和青碧"}
NAMES_EN = {"crimson": "Soft Crimson", "soft_violet": "Soft Violet", "soft_dune": "Soft Dune", "soft_teal": "Soft Teal"}
REF = None   # 參考截圖（可選）：python ... <截圖路徑>


def hx(h):
    return tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))


# 粉色色盤（由淺到深），對應母版灰階 160 → 92
PINK = [hx(c) for c in ("#FC9CA8", "#F6909C", "#F67E8A", "#EA6C78", "#E46672", "#DE5A5E", "#CC484E")]


def levels(images):
    """所有母版用到的灰階值，由淺到深。"""
    vals = sorted({p[0] for im in images for p in im.get_flattened_data() if p[3] > 0}, reverse=True)
    return vals


def gradient_map(im, lv, pal):
    out = Image.new("RGBA", im.size)
    idx = {v: i for i, v in enumerate(lv)}
    for (x, y), p in zip(((x, y) for y in range(im.height) for x in range(im.width)), im.get_flattened_data()):
        if p[3]:
            c = pal[min(len(pal) - 1, round(idx[p[0]] * (len(pal) - 1) / max(1, len(lv) - 1)))]
            out.putpixel((x, y), c + (p[3],))
    return out


def ground_hue(block):
    """地面頂面貼圖平均色的色相（0~1）。"""
    bs = json.loads((A / f"blockstates/{block}.json").read_text(encoding="utf-8"))["variants"]
    key = next((k for k in bs if "facing=up" in k), next(iter(bs)))
    v = bs[key]
    v = v[0] if isinstance(v, list) else v

    def tex(ref):
        ns, path = ref.split(":")
        j = json.loads((A / "models" / (path + ".json")).read_text(encoding="utf-8")) if ns == "pysift" else {}
        t = tex(j["parent"]) if ns == "pysift" and "parent" in j else {}
        return {**t, **j.get("textures", {})}
    t = tex(v["model"])
    ref = next(t[k] for k in ("top", "up", "all") if k in t)
    while ref.startswith("#"):
        ref = t[ref[1:]]
    im = Image.open(A / "textures" / (ref.split(":")[1] + ".png")).convert("RGBA").crop((0, 0, 16, 16))
    px = [p for p in im.get_flattened_data() if p[3] > 0]
    avg = [sum(p[i] for p in px) / len(px) / 255 for i in range(3)]
    return colorsys.rgb_to_hsv(*avg)[0]


def rotate_palette(pal, hue):
    """色盤整組轉到 hue，每一色的飽和度與明度不變（鮮豔度、深淺層次和粉色一樣）。"""
    out = []
    for c in pal:
        _, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
        out.append(tuple(round(x * 255) for x in colorsys.hsv_to_rgb(hue, s, v)))
    return out


def relative_palette(floor_hex, sat_boost, v_lift):
    def hsv(c):
        return colorsys.rgb_to_hsv(*(x / 255 for x in c))
    hf, sf, vf = hsv(hx(floor_hex))
    _, sp, vp = hsv(hx(PINK_FLOOR))
    out = []
    for c in PINK:
        _, s, v = hsv(c)
        out.append(tuple(round(x * 255) for x in colorsys.hsv_to_rgb(hf, min(1, sf * s / sp * sat_boost), min(1, vf * v / vp + v_lift))))
    return out


def palette_for(spec):
    if spec[0] == "pink":
        return PINK
    if spec[0] == "rotate":
        return rotate_palette(PINK, ground_hue(spec[1]))
    return relative_palette(*spec[1:])


def shift_down(im, dy):
    out = Image.new("RGBA", im.size)
    out.paste(im.crop((0, 0, im.width, im.height - dy)), (0, dy))
    return out


def build():
    """回傳 {貼圖名: 上色後 Image}, {set: palette}。"""
    names = ("short_grass", "tall_grass_bottom", "tall_grass_top")
    m = {n: Image.open(SRC / f"crimson_{n}.png").convert("RGBA") for n in names}
    lv = levels(m.values())
    pals, tex = {}, {}
    for prefix, spec in SETS.items():
        pal = palette_for(spec)
        pals[prefix] = pal
        mirror, dy = SHAPES[prefix]
        for n in names:
            im = ImageOps.mirror(m[n]) if mirror else m[n]
            if dy and n != "tall_grass_bottom":
                im = shift_down(im, dy)
            tex[f"{prefix}_{n}"] = gradient_map(im, lv, pal)
    return tex, pals, lv


def apply(tex):
    def backup(p):
        if p.exists():
            dst = BK / p.relative_to(P)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
    for n, im in tex.items():
        p = VEG / f"{n}.png"
        backup(p)
        im.save(p)
        mp = A / f"models/block/vegetation/{n}.json"
        backup(mp)
        mp.write_text(json.dumps({"parent": "minecraft:block/cross", "textures": {"cross": f"pysift:block/vegetation/{n}"}},
                                 indent="\t") + "\n", encoding="utf-8")
    D = P / "src/main/resources/data"

    def wj(path, obj, indent=2):
        backup(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")
    lang = {"zh_tw": {}, "en_us": {}}
    shears = {"type": "minecraft:any_of", "terms": ["minecraft:tool/can_shear", "minecraft:tool/can_silk_touch"]}
    for prefix in SETS:
        short, tall = f"{prefix}_short_grass", f"{prefix}_tall_grass"
        wj(A / f"blockstates/{short}.json", {"variants": {"": [dict({"model": f"pysift:block/vegetation/{short}"}, **({"y": y} if y else {}))
                                                               for y in (0, 90, 180, 270)]}})
        wj(A / f"blockstates/{tall}.json", {"variants": {"half=lower": {"model": f"pysift:block/vegetation/{tall}_bottom"},
                                                         "half=upper": {"model": f"pysift:block/vegetation/{tall}_top"}}})
        for item, layer in ((short, short), (tall, f"{tall}_top")):
            wj(A / f"items/{item}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{item}"}})   # 貼圖已上色，不染色
            wj(A / f"models/item/{item}.json", {"parent": "minecraft:item/generated",
                                                "textures": {"layer0": f"pysift:block/vegetation/{layer}"}}, "\t")
        for item, is_tall in ((short, False), (tall, True)):
            cond = shears if not is_tall else {"type": "minecraft:all_of", "terms": [
                {"type": "minecraft:match_block", "blocks": f"pysift:{item}", "state": {"half": "lower"}}, shears]}
            loot = {"type": "minecraft:block", "pools": [{"condition": cond, "entries": [{"type": "minecraft:item", "name": f"pysift:{item}"}],
                                                          "rolls": 1}], "random_sequence": f"pysift:blocks/{item}"}
            for folder in ("loot_table", "loot_tables"):
                wj(D / f"pysift/{folder}/blocks/{item}.json", loot)
        for key in ("block", "item"):
            lang["zh_tw"][f"{key}.pysift.{short}"] = NAMES_ZH[prefix] + "短草"
            lang["en_us"][f"{key}.pysift.{short}"] = NAMES_EN[prefix] + " Short Grass"
            lang["zh_tw"][f"{key}.pysift.{tall}"] = NAMES_ZH[prefix] + "高草"
            lang["en_us"][f"{key}.pysift.{tall}"] = NAMES_EN[prefix] + " Tall Grass"
    for l, entries in lang.items():
        lp = A / f"lang/{l}.json"
        backup(lp)
        j = json.loads(lp.read_text(encoding="utf-8"))
        j.update(entries)
        lp.write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tp = D / "minecraft/tags/block/replaceable_by_trees.json"
    j = json.loads(tp.read_text(encoding="utf-8"))
    for prefix in SETS:
        for n in (f"pysift:{prefix}_short_grass", f"pysift:{prefix}_tall_grass"):
            if n not in j["values"]:
                j["values"].append(n)
    wj(tp, j)
    print("applied; backups in", BK)


def preview_sets(tex, pals, lv, sheet_path):
    font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 16)
    S = 10
    grounds = {"crimson": hx("#F47D89"), "soft_violet": hx("#4F4657"), "soft_dune": hx("#E1B66E"), "soft_teal": hx("#43B6B0")}
    sheet = Image.new("RGB", (len(pals) * 420 + 20, 600), (34, 33, 40))
    d = ImageDraw.Draw(sheet)
    for k, (prefix, pal) in enumerate(pals.items()):
        x = 10 + k * 420
        d.text((x, 8), prefix, fill=(235, 235, 235), font=font)
        for i, c in enumerate(pal):
            d.rectangle([x + i * 56, 34, x + i * 56 + 50, 70], fill=c)
        bg = Image.new("RGBA", (16 * S, 32 * S), grounds[prefix] + (255,))
        tall = Image.new("RGBA", (16, 32))
        tall.paste(tex[f"{prefix}_tall_grass_top"], (0, 0))
        tall.paste(tex[f"{prefix}_tall_grass_bottom"], (0, 16))
        bg.alpha_composite(tall.resize((16 * S, 32 * S), Image.NEAREST))
        sheet.paste(bg.convert("RGB"), (x, 90))
        bg2 = Image.new("RGBA", (16 * S, 16 * S), grounds[prefix] + (255,))
        bg2.alpha_composite(tex[f"{prefix}_short_grass"].resize((16 * S, 16 * S), Image.NEAREST))
        sheet.paste(bg2.convert("RGB"), (x + 16 * S + 20, 90 + 16 * S))
    sheet.save(sheet_path)


def main(ref_path=None):
    names = ("crimson_short_grass", "crimson_tall_grass_bottom", "crimson_tall_grass_top")
    m = {n: Image.open(SRC / f"{n}.png").convert("RGBA") for n in names}
    lv = levels(m.values())
    print("gray levels (light→dark):", lv)
    col = {n: gradient_map(im, lv, PINK) for n, im in m.items()}
    font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 16)
    S = 12
    ground = hx("#F07E86")
    sheet = Image.new("RGB", (1400, 560), (34, 33, 40))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "色盤（淺→深）＝母版灰階 " + " ".join(map(str, lv)), fill=(235, 235, 235), font=font)
    for i, (g, c) in enumerate(zip(lv, PINK)):
        d.rectangle([10 + i * 80, 34, 80 + i * 80, 74], fill=(g, g, g))
        d.rectangle([10 + i * 80, 78, 80 + i * 80, 118], fill=c)
        d.text((10 + i * 80, 122), "#%02X%02X%02X" % c, fill=(220, 220, 220), font=font)
    x = 10
    for label, ims in (("母版（灰階）", m), ("粉色色盤對應", col)):
        d.text((x, 160), label, fill=(235, 235, 235), font=font)
        bg = Image.new("RGBA", (16 * S, 32 * S), ground + (255,))
        tall = Image.new("RGBA", (16, 32))
        tall.paste(ims["crimson_tall_grass_top"], (0, 0))
        tall.paste(ims["crimson_tall_grass_bottom"], (0, 16))
        bg.alpha_composite(tall.resize((16 * S, 32 * S), Image.NEAREST))
        sheet.paste(bg.convert("RGB"), (x, 186))
        bg2 = Image.new("RGBA", (16 * S, 16 * S), ground + (255,))
        bg2.alpha_composite(ims["crimson_short_grass"].resize((16 * S, 16 * S), Image.NEAREST))
        sheet.paste(bg2.convert("RGB"), (x + 16 * S + 10, 186 + 16 * S))
        x += 2 * 16 * S + 40
    if ref_path:
        ref = Image.open(ref_path).convert("RGB")
        ref.thumbnail((560, 380))
        d.text((x, 160), "參考截圖", fill=(235, 235, 235), font=font)
        sheet.paste(ref, (x, 186))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)
    print("preview:", PREVIEW)


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(args[0] if args else None)
    tex, pals, lv = build()
    preview_sets(tex, pals, lv, PREVIEW.with_name("soft_grass_palette_sets.png"))
    print("sets preview:", PREVIEW.with_name("soft_grass_palette_sets.png"))
    if "--apply" in sys.argv:
        apply(tex)
