"""把使用者給的 rift_dimension_flora_assets.zip（解壓到 build/flora_import/）裝進 pysift。
Usage: python -I tools/worldgen/install_rift_flora.py

- 模型、貼圖的命名空間 modid → pysift，放到 models/block/vegetation/、textures/block/vegetation/。
- 產生 blockstate（短草類 4 個 y 旋轉隨機）、物品定義、物品模型、掉落表、中英文名稱。
- 物品圖示：平面交叉草用方塊貼圖（item/generated，和原版草一樣）；立體的（龍舌蘭、巨傘草、簇生黃花）之後用
  tools/worldgen/veg_models.py icon 畫。
- 世界生成寫在 build_the_sift.py 的 VEGETATION 表。
- 注意：重跑會把模型蓋回交叉平面；之後要再跑 tools/models/gen_rift_blades.py --apply 換回 3D 葉片。
已存在的檔案會先備份到 .texture_backups/<stamp>_rift_flora/。
"""
import json, shutil, sys, datetime
from pathlib import Path

P = Path(__file__).resolve().parents[2]
SRC = P / "build/flora_import"
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_rift_flora")

# name: (kind, zh, en, item icon texture or None = 3D icon)
PLANTS = {
    "rift_red_short_grass": ("grass", "赤紅短芽", "Crimson Short Sprouts", "rift_red_short_grass"),
    "blue_curled_fern": ("grass", "藍捲蕨", "Blue Curled Fern", "blue_curled_fern"),
    "pink_curled_fern": ("grass", "粉捲蕨", "Pink Curled Fern", "pink_curled_fern"),
    "white_curled_fern": ("grass", "白捲蕨", "White Curled Fern", "white_curled_fern"),
    "rift_mint_short_grass": ("grass", "薄荷裂隙草", "Mint Rift Grass", "rift_mint_short_grass"),
    "rift_orange_short_grass": ("grass", "橙裂隙草", "Orange Rift Grass", "rift_orange_short_grass"),
    "rift_yellow_short_grass": ("grass", "黃短草", "Yellow Short Grass", "rift_yellow_short_grass"),
    "olive_forked_stalk": ("grass", "橄欖叉莖", "Olive Forked Stalk", "olive_forked_stalk"),
    "rift_orange_tall_grass": ("tall", "高橙裂隙草", "Tall Orange Rift Grass", "rift_orange_tall_grass_top"),
    "yellow_agave": ("bush", "黃龍舌蘭", "Yellow Agave Rosette", None),
    "green_giant_canopy": ("bush", "綠巨傘草", "Green Giant Canopy", None),
    "blue_giant_canopy": ("bush", "藍巨傘草", "Blue Giant Canopy", None),
    "white_giant_canopy": ("bush", "白巨傘草", "White Giant Canopy", None),
    "clustered_yellow_flowers": ("flower", "簇生黃花", "Clustered Yellow Flowers", None),
}


def backup(p):
    if p.exists():
        dst = BK / p.relative_to(P)
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)


def wj(p, obj, indent=2):
    backup(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def rename_refs(obj):
    """modid:block/x → pysift:block/vegetation/x（模型與貼圖參照）。"""
    if isinstance(obj, dict):
        return {k: rename_refs(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rename_refs(v) for v in obj]
    if isinstance(obj, str) and obj.startswith("modid:block/"):
        return "pysift:block/vegetation/" + obj[len("modid:block/"):]
    return obj


def shears_loot(name, tall=False):
    cond = {"type": "minecraft:any_of", "terms": ["minecraft:tool/can_shear", "minecraft:tool/can_silk_touch"]}
    if tall:
        cond = {"type": "minecraft:all_of", "terms": [
            {"type": "minecraft:match_block", "blocks": f"pysift:{name}", "state": {"half": "lower"}}, cond]}
    return {"type": "minecraft:block", "pools": [{"condition": cond, "entries": [{"type": "minecraft:item", "name": f"pysift:{name}"}],
                                                   "rolls": 1}], "random_sequence": f"pysift:blocks/{name}"}


def self_loot(name):
    return {"type": "minecraft:block", "pools": [{"condition": {"type": "minecraft:survives_explosion"},
                                                   "entries": [{"type": "minecraft:item", "name": f"pysift:{name}"}], "rolls": 1}],
            "random_sequence": f"pysift:blocks/{name}"}


def add_tag(path, values):
    j = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"replace": False, "values": []}
    for v in values:
        if v not in j["values"]:
            j["values"].append(v)
    j["values"] = sorted(j["values"]) if path.name == "not_in_worldgen.json" else j["values"]
    wj(path, j)


def add_lang(path, entries):
    backup(path)
    j = json.loads(path.read_text(encoding="utf-8"))
    j.update(entries)
    path.write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    if "--force" not in sys.argv:
        sys.exit("已整合：這批植物之後經過 tools/worldgen/rename_vegetation.py 合併與改名，重跑會把舊 ID 和舊模型寫回來。"
                 "真的要重新匯入請加 --force，之後再跑一次 rename_vegetation.py。")
    # 貼圖
    for png in (SRC / "textures/block").glob("*.png"):
        dst = A / "textures/block/vegetation" / png.name
        backup(dst)
        shutil.copy2(png, dst)
    # 模型（含模板）
    for js in (SRC / "models/block").glob("*.json"):
        j = rename_refs(json.loads(js.read_text(encoding="utf-8")))
        wj(A / "models/block/vegetation" / js.name, j, indent="\t")
    zh, en = {}, {}
    for name, (kind, zname, ename, icon) in PLANTS.items():
        model = f"pysift:block/vegetation/{name}"
        if kind == "tall":
            bs = {"variants": {"half=lower": {"model": model + "_bottom"}, "half=upper": {"model": model + "_top"}}}
        else:
            bs = {"variants": {"": [{"model": model, "y": y} if y else {"model": model} for y in (0, 90, 180, 270)]}}
        wj(A / "blockstates" / f"{name}.json", bs)
        wj(A / "items" / f"{name}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{name}"}})
        if icon:
            wj(A / "models/item" / f"{name}.json",
               {"parent": "minecraft:item/generated", "textures": {"layer0": f"pysift:block/vegetation/{icon}"}}, indent="\t")
        loot = self_loot(name) if kind in ("flower", "bush") else shears_loot(name, kind == "tall")
        for folder in ("loot_table", "loot_tables"):   # 專案兩個資料夾都有一份
            wj(D / "pysift" / folder / "blocks" / f"{name}.json", loot)
        for key in ("block", "item"):
            zh[f"{key}.pysift.{name}"] = zname
            en[f"{key}.pysift.{name}"] = ename
    add_lang(A / "lang/zh_tw.json", zh)
    add_lang(A / "lang/en_us.json", en)
    ids = [f"pysift:{n}" for n in PLANTS]
    add_tag(D / "minecraft/tags/block/replaceable_by_trees.json", ids)   # 和既有植被一樣：瞬間破壞、樹可以長穿
    for t in ("block", "item"):
        add_tag(D / f"minecraft/tags/{t}/small_flowers.json", ["pysift:clustered_yellow_flowers"])
    print("installed", len(PLANTS), "plants; backups (if any) in", BK)


if __name__ == "__main__":
    main()
