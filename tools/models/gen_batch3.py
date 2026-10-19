"""批次 3：影片裡有、模組還沒有的兩種植物。
  tall_glow_grass   高發光草：兩格高的青色粗葉草（gen_blade_models 的葉片），葉間有不染色的黃色發光小方塊；顏色依地板（FloorTint）。
  coral_leaf_carpet 珊瑚落葉地毯：像原版粉紅花瓣（FlowerBedBlock），1~4 層，用原版 flowerbed_1..4 模型，只換貼圖。
Usage (from the project root):
  python -I tools/models/gen_batch3.py            預覽 build/previews/sift_batch_3.png
  python -I tools/models/gen_batch3.py --apply    寫入貼圖、模型、blockstate、物品、掉落表、名稱、標籤（先備份）
Java 註冊在 ModVegetation（TALL_GLOW_GRASS、CORAL_LEAF_CARPET）。
"""
import sys, json, math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_blade_models as g

P, A = g.P, g.A
D = P / "src/main/resources/data"
VEG = A / "textures/block/vegetation"
PREVIEW = P / "build/previews/sift_batch_3.png"
VANILLA = P / "build/vanilla_ref/assets/minecraft"


def hx(h):
    return tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))


# ------------------------------------------------------------------ tall glow grass
def glow_models():
    bottom, top = g.tall_tuft(131, 13)
    rnd = random.Random(17)
    for _ in range(3):   # 上半格的發光點
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(2, 4.5)
        top.append(g.speck(8 + math.cos(a) * r, rnd.uniform(0, 9), 8 + math.sin(a) * r))
    a = rnd.uniform(0, math.tau)
    bottom.append(g.speck(8 + math.cos(a) * 3.5, 12, 8 + math.sin(a) * 3.5))
    return bottom, top


# ------------------------------------------------------------------ coral leaf carpet
LEAF = [hx(c) for c in ("#C9584A", "#DD6E56", "#E8825E", "#F29A6E", "#F6B488")]
OUTLINE = hx("#A8443C")
PETAL, CENTRE = hx("#FFD34A"), hx("#E8962E")


def carpet_texture():
    """四個 8x8 象限各是一團交疊的珊瑚色落葉（透明底），兩個象限有黃色四瓣小花。"""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()
    shapes = [((0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (1, 2)), ((1, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
              ((0, 0), (1, 0), (2, 0), (1, 1), (2, 1), (3, 1)), ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2))]
    rnd = random.Random(23)
    for qx, qy, flower in ((0, 0, True), (8, 0, False), (0, 8, False), (8, 8, True)):
        for _ in range(13):
            x, y = qx + rnd.randint(0, 5), qy + rnd.randint(0, 5)
            c = rnd.choice(LEAF[1:])
            sh = rnd.choice(shapes)
            for dx, dy in sh:
                if x + dx < qx + 8 and y + dy < qy + 8:
                    px[x + dx, y + dy] = c + (255,)
            dx, dy = sh[-1]
            if x + dx < qx + 8 and y + dy + 1 < qy + 8:
                px[x + dx, y + dy + 1] = OUTLINE + (255,)
        if flower:
            fx, fy = qx + rnd.randint(2, 5), qy + rnd.randint(2, 5)
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                px[fx + dx, fy + dy] = PETAL + (255,)
            px[fx, fy] = CENTRE + (255,)
    return im


def stem_texture():
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        im.putpixel((0, y), (hx("#B8584A") if y % 3 else hx("#9C4A40")) + (255,))
    return im


def item_icon(carpet):
    """物品圖示：四個象限往中間靠成一團。"""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for (sx, sy), (dx, dy) in (((0, 0), (1, 2)), ((8, 0), (7, 1)), ((0, 8), (2, 7)), ((8, 8), (7, 7))):
        q = carpet.crop((sx, sy, sx + 8, sy + 8))
        im.alpha_composite(q, (dx, dy))
    return im


# ------------------------------------------------------------------ preview
def flowerbed_elements(n):
    j = json.loads((VANILLA / f"models/block/flowerbed_{n}.json").read_text(encoding="utf-8"))
    out = []
    for e in j["elements"]:
        e = json.loads(json.dumps(e))
        r = e.get("rotation")
        e["rotation"] = {"origin": r["origin"], r["axis"]: r["angle"]} if r else {"origin": [8, 8, 8]}
        out.append(e)
    return out


def preview(glow, tex):
    font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 15)
    W = 300
    sheet = Image.new("RGB", (W * 3 + 40, 2 * (W + 30) + 120), (34, 33, 40))
    d = ImageDraw.Draw(sheet)
    # 高發光草：青地單株、3x3、紫地單株
    d.text((10, 10), "高發光草 tall_glow_grass（顏色依地板：青地 / 紫地；黃點不染色、發光）", fill=(235, 235, 235), font=font)
    for k, (tint, floor, grid) in enumerate(((("#7BE0D0"), "#2E7F7A", False), ("#7BE0D0", "#2E7F7A", True), ("#B995E0", "#6E5A8C", False))):
        c = g.Canvas(W, W, 4.2 if grid else 7.5)
        cells = [(gx, gz) for gx in range(3) for gz in range(3)] if grid else [(1, 1)]
        for gx, gz in cells:
            c.ground(((gx - 1) * 16, 0, (gz - 1) * 16), g.hexrgb(floor))
        for gx, gz in cells:
            for half, els in enumerate(glow):
                for e in els:
                    e2 = g.rotate_y_model(e, ((gx * 3 + gz) * 90) % 360)
                    c.element(e2, {"#0": tex["tall_glow_grass"]}, g.hexrgb(tint), ((gx - 1) * 16, 16 * half, (gz - 1) * 16))
        sheet.paste(c.img, (10 + k * (W + 10), 32))
    # 珊瑚落葉地毯：1~4 層 + 貼圖
    y0 = W + 50
    d.text((10, y0), "珊瑚落葉地毯 coral_leaf_carpet（1~4 層，像原版粉紅花瓣）", fill=(235, 235, 235), font=font)
    for n in range(1, 5):
        c = g.Canvas(W * 3 // 4 - 10, W * 3 // 4 - 10, 9, pitch=40)
        c.ground((0, 0, 0), g.hexrgb("#9C8C78"))
        for m in range(1, n + 1):
            for e in flowerbed_elements(m):
                c.element(e, {"#flowerbed": tex["coral_leaf_carpet"], "#stem": tex["coral_leaf_carpet_stem"]}, (255, 255, 255))
        sheet.paste(c.img, (10 + (n - 1) * (W * 3 // 4), y0 + 22))
    sheet.paste(tex["coral_leaf_carpet"].resize((96, 96), Image.NEAREST), (10, y0 + W * 3 // 4 + 20), tex["coral_leaf_carpet"].resize((96, 96), Image.NEAREST))
    sheet.paste(tex["tall_glow_grass"].resize((96, 96), Image.NEAREST), (116, y0 + W * 3 // 4 + 20))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)


# ------------------------------------------------------------------ apply
def wj(p, obj, indent=2):
    g.backup(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def apply(glow, tex):
    for n, im in tex.items():
        p = VEG / f"{n}.png"
        g.backup(p)
        im.save(p)
    icon = A / "textures/item/coral_leaf_carpet.png"
    g.backup(icon)
    item_icon(tex["coral_leaf_carpet"]).save(icon)
    # 高發光草
    for half, els in (("bottom", glow[0]), ("top", glow[1])):
        wj(A / g.MODEL_DIR / f"tall_glow_grass_{half}.json", g.model("tall_glow_grass", els), indent="\t")
    wj(A / "blockstates/tall_glow_grass.json", {"variants": {"half=lower": {"model": "pysift:block/vegetation/tall_glow_grass_bottom"},
                                                             "half=upper": {"model": "pysift:block/vegetation/tall_glow_grass_top"}}})
    # 珊瑚落葉地毯：原版 flowerbed 模型 + 自己的貼圖
    for n in range(1, 5):
        wj(A / g.MODEL_DIR / f"coral_leaf_carpet_{n}.json", {"parent": f"minecraft:block/flowerbed_{n}", "textures": {
            "flowerbed": "pysift:block/vegetation/coral_leaf_carpet", "stem": "pysift:block/vegetation/coral_leaf_carpet_stem"}})
    parts = []
    for n in range(1, 5):
        amount = "|".join(str(k) for k in range(n, 5))
        for facing, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
            apply_ = {"model": f"pysift:block/vegetation/coral_leaf_carpet_{n}"}
            if y:
                apply_["y"] = y
            when = {"facing": facing} if n == 1 else {"facing": facing, "flower_amount": amount}
            parts.append({"apply": apply_, "when": when})
    wj(A / "blockstates/coral_leaf_carpet.json", {"multipart": parts})
    # 物品
    wj(A / "items/tall_glow_grass.json", {"model": {"type": "minecraft:model", "model": "pysift:item/tall_glow_grass"}})
    wj(A / "items/coral_leaf_carpet.json", {"model": {"type": "minecraft:model", "model": "pysift:item/coral_leaf_carpet"}})
    wj(A / "models/item/coral_leaf_carpet.json", {"parent": "minecraft:item/generated", "textures": {"layer0": "pysift:item/coral_leaf_carpet"}}, indent="\t")
    # 掉落表
    glow_loot = {"type": "minecraft:block", "pools": [{"condition": {"type": "minecraft:all_of", "terms": [
        {"type": "minecraft:match_block", "blocks": "pysift:tall_glow_grass", "state": {"half": "lower"}},
        {"type": "minecraft:any_of", "terms": ["minecraft:tool/can_shear", "minecraft:tool/can_silk_touch"]}]},
        "entries": [{"type": "minecraft:item", "name": "pysift:tall_glow_grass"}], "rolls": 1}], "random_sequence": "pysift:blocks/tall_glow_grass"}
    carpet_loot = {"type": "minecraft:block", "pools": [{"entries": [{"type": "minecraft:item", "name": "pysift:coral_leaf_carpet", "modifier": [
        *[{"type": "minecraft:set_count", "condition": {"type": "minecraft:match_block", "blocks": "pysift:coral_leaf_carpet",
                                                         "state": {"flower_amount": str(k)}}, "count": k} for k in range(1, 5)],
        {"type": "minecraft:explosion_decay"}]}], "rolls": 1}], "random_sequence": "pysift:blocks/coral_leaf_carpet"}
    for folder in ("loot_table", "loot_tables"):
        wj(D / "pysift" / folder / "blocks/tall_glow_grass.json", glow_loot)
        wj(D / "pysift" / folder / "blocks/coral_leaf_carpet.json", carpet_loot)
    # 名稱
    names = {"tall_glow_grass": ("高發光草", "Tall Glow Grass"), "coral_leaf_carpet": ("珊瑚落葉", "Coral Leaf Carpet")}
    for lang, i in (("zh_tw", 0), ("en_us", 1)):
        p = A / f"lang/{lang}.json"
        g.backup(p)
        j = json.loads(p.read_text(encoding="utf-8"))
        for n, v in names.items():
            j[f"block.pysift.{n}"] = j[f"item.pysift.{n}"] = v[i]
        p.write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 標籤：和其他植被一樣瞬間破壞、樹可長穿
    p = D / "minecraft/tags/block/replaceable_by_trees.json"
    g.backup(p)
    j = json.loads(p.read_text(encoding="utf-8"))
    for n in names:
        if f"pysift:{n}" not in j["values"]:
            j["values"].append(f"pysift:{n}")
    p.write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("applied; backups in", g.BK)


def main():
    glow = glow_models()
    tex = {"tall_glow_grass": g.blade_texture("grass"), "coral_leaf_carpet": carpet_texture(), "coral_leaf_carpet_stem": stem_texture()}
    preview(glow, tex)
    print("preview:", PREVIEW)
    if "--apply" in sys.argv:
        apply(glow, tex)


if __name__ == "__main__":
    main()
