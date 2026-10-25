"""植被整理：合併重複的植物、統一方塊 ID 與名稱（一次性；已套用後再跑會直接停止）。
Usage:
  python -I tools/worldgen/rename_vegetation.py            # 只列出會改到的地方（dry run）
  python -I tools/worldgen/rename_vegetation.py --apply    # 實際執行

1. MERGES：保留舊方塊（世界生成、掉落、物品定義都不動），改用 sift_vegetation_assets 新方塊的模型與貼圖，
   新方塊的方塊狀態／模型／名稱／標籤移除。保留方塊原本的模型與貼圖移到備份。
2. RENAMES：舊 ID → 新 ID。src/main/resources（assets/pysift、data）與 tools/ 底下的檔名和文字內容一起改，
   用 token 邊界比對（前後不是英數字），所以 patch_<id>、<id>_top、<id>_glow 這類衍生名稱會一起改。
   Java（ModVegetation、SiftFlora）手動改好，不在這裡處理。
3. NAMES：所有植被的中英文名稱統一成「家族＋顏色＋形態」。
所有改到的檔案先備份到 .texture_backups/<stamp>_rename_vegetation/（保留原路徑）。
"""
import json, re, shutil, sys, datetime
from pathlib import Path

P = Path(__file__).resolve().parents[2]
RES = P / "src/main/resources"
A = RES / "assets/pysift"
D = RES / "data"
APPLY = "--apply" in sys.argv
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_rename_vegetation")

# 保留的舊方塊 → 併入的新方塊（用新方塊的模型；新方塊本身刪除）
MERGES = {
    "orange_rift_grass": "sift_orange_short_grass",
    "orange_tall_rift_grass": "sift_orange_tall_grass",
    "crimson_short_sprouts": "sift_red_short_grass",
    "mint_rift_grass": "sift_short_grass",
}
# 夜光短草改用幽匿草貼圖：由 tools/progression/build_progression.py 產生（模型、發光層），這裡只刪幽匿草方塊
DROPPED = ["sculk_grass"]
# 匯入時多出來、沒有任何模型引用的重複檔（改名後會和 custom/cleaver_plant、custom/soul_cleaver_plant 撞名）
CLEANUP = ["models/custom/sift_cleaver_plant.json", "models/custom/sift_soul_cleaver_plant.json"]

RENAMES = {
    "orange_rift_grass": "rift_orange_short_grass",
    "orange_tall_rift_grass": "rift_orange_tall_grass",
    "crimson_short_sprouts": "rift_red_short_grass",
    "mint_rift_grass": "rift_mint_short_grass",
    "sift_tallgrass": "rift_mint_tall_grass",
    "yellow_short_grass": "rift_yellow_short_grass",
    "glowshade_grass": "glowshade_short_grass",
    "tall_glow_grass": "glowshade_tall_grass",
    "crimson_short_grass": "soft_crimson_short_grass",
    "crimson_tall_grass": "soft_crimson_tall_grass",
    "curled_fern_blue": "blue_curled_fern",
    "curled_fern_pink": "pink_curled_fern",
    "curled_fern_white": "white_curled_fern",
    "giant_canopy_green": "green_giant_canopy",
    "giant_canopy_blue": "blue_giant_canopy",
    "giant_canopy_white": "white_giant_canopy",
    "agave_rosette": "yellow_agave",
    "sift_small_flowers": "white_flower_patch",
    "sift_small_flowers_yellow": "yellow_flower_patch",
    "weat_small_plant": "sift_wheat_sprout",
    "weat_plant": "sift_wheat_plant",
    "weat": "sift_wheat",
    "green_tree_vine": "green_sift_vine",
    "orange_tree_vine": "orange_sift_vine",
    "sift_wall_leaf": "sift_wall_leaves",
    "sift_cleaver_plant": "cleaver_plant",
    "sift_soul_cleaver_plant": "soul_cleaver_plant",
    "yellow_leaf": "yellow_leaf_litter",
}

# 新 ID → (中文, English)
NAMES = {
    "rift_orange_short_grass": ("裂隙橙短草", "Rift Orange Short Grass"),
    "rift_orange_tall_grass": ("裂隙橙高草", "Rift Orange Tall Grass"),
    "rift_red_short_grass": ("裂隙紅短草", "Rift Red Short Grass"),
    "rift_mint_short_grass": ("裂隙薄荷短草", "Rift Mint Short Grass"),
    "rift_mint_tall_grass": ("裂隙薄荷高草", "Rift Mint Tall Grass"),
    "rift_yellow_short_grass": ("裂隙黃短草", "Rift Yellow Short Grass"),
    "olive_forked_stalk": ("橄欖叉莖", "Olive Forked Stalk"),
    "blue_curled_fern": ("藍捲蕨", "Blue Curled Fern"),
    "pink_curled_fern": ("粉捲蕨", "Pink Curled Fern"),
    "white_curled_fern": ("白捲蕨", "White Curled Fern"),
    "yellow_agave": ("黃龍舌蘭", "Yellow Agave"),
    "green_giant_canopy": ("綠巨傘草", "Green Giant Canopy"),
    "blue_giant_canopy": ("藍巨傘草", "Blue Giant Canopy"),
    "white_giant_canopy": ("白巨傘草", "White Giant Canopy"),
    "clustered_yellow_flowers": ("簇生黃花", "Clustered Yellow Flowers"),
    "glowshade_short_grass": ("夜光短草", "Glowshade Short Grass"),
    "glowshade_tall_grass": ("夜光高草", "Glowshade Tall Grass"),
    "glowshade_tuft": ("夜光草叢", "Glowshade Tuft"),
    "soft_crimson_short_grass": ("柔和赤紅短草", "Soft Crimson Short Grass"),
    "soft_crimson_tall_grass": ("柔和赤紅高草", "Soft Crimson Tall Grass"),
    "carapace_flower": ("甲殼花", "Carapace Flower"),
    "carapace_short_grass": ("甲殼短草", "Carapace Short Grass"),
    "carapace_vine": ("甲殼藤", "Carapace Vine"),
    "white_flower_patch": ("白色小花叢", "White Flower Patch"),
    "yellow_flower_patch": ("黃色小花叢", "Yellow Flower Patch"),
    "soul_bubble_flower": ("靈魂氣泡花", "Soul Bubble Flower"),
    "green_sift_vine": ("綠隙浮藤", "Green Sift Vine"),
    "orange_sift_vine": ("橙隙浮藤", "Orange Sift Vine"),
    "soul_vine": ("靈魂藤", "Soul Vine"),
    "sift_wall_leaves": ("隙浮攀牆葉", "Sift Wall Leaves"),
    "cleaver_plant": ("劈裂草", "Cleaver Plant"),
    "soul_cleaver_plant": ("靈魂劈裂草", "Soul Cleaver Plant"),
    "sift_wheat_sprout": ("隙浮小麥幼苗", "Sift Wheat Sprout"),
    "sift_wheat_plant": ("隙浮小麥植株", "Sift Wheat Plant"),
    "sift_wheat": ("隙浮小麥", "Sift Wheat"),
    "yellow_leaf_litter": ("黃色落葉", "Yellow Leaf Litter"),
}

TOKEN = re.compile(r"(?<![a-z0-9])(" + "|".join(sorted(map(re.escape, RENAMES), key=len, reverse=True)) + r")(?![a-z0-9])")
TEXT = {".json", ".py", ".md", ".mcmeta", ".txt"}
ROOTS = [A, D, P / "tools"]   # 另加 art_requests/*.md（art_requests/models、textures 是快照，不改）
SKIP = {Path(__file__).resolve()}


def backup(p):
    dst = BK / p.relative_to(P)
    if APPLY and p.exists() and not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)


def remove(p):
    """移到備份（不直接刪除）。"""
    if p.exists():
        backup(p)
        if APPLY:
            p.unlink()
        print("  remove", p.relative_to(P))


def lj(p): return json.loads(p.read_text(encoding="utf-8"))


def wj(p, obj, indent=2):
    backup(p)
    if APPLY:
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def strip_refs(obj, ids):
    """從標籤或清單移除 pysift:<id>。"""
    if isinstance(obj, dict):
        return {k: strip_refs(v, ids) for k, v in obj.items()}
    if isinstance(obj, list):
        return [strip_refs(v, ids) for v in obj if not (isinstance(v, str) and v in ids)]
    return obj


def files():
    yield from (P / "art_requests").glob("*.md")
    for root in ROOTS:
        for p in root.rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.resolve() not in SKIP:
                yield p


def merge():
    print("== merge")
    gone = {f"pysift:{s}" for s in list(MERGES.values()) + DROPPED}
    for keep, src in MERGES.items():
        # 保留方塊原本的模型與只給它用的貼圖 → 備份
        for p in list((A / "models/block/vegetation").glob(f"{keep}*.json")) + list((A / "textures/block/vegetation").glob(f"{keep}*.png")):
            if re.fullmatch(re.escape(keep) + r"(_top|_bottom|_blades)?\.(json|png)", p.name):
                remove(p)
        # 新方塊的模型改名成保留方塊的；方塊狀態與物品模型改指過去
        for m in (A / "models/block").glob(f"{src}*.json"):
            dst = m.with_name(keep + m.name[len(src):])
            print("  model", m.name, "->", dst.name)
            backup(m)
            if APPLY:
                m.rename(dst)
        bs = lj(A / f"blockstates/{src}.json")
        bs = json.loads(json.dumps(bs).replace(f"pysift:block/{src}", f"pysift:block/{keep}"))
        wj(A / f"blockstates/{keep}.json", bs)
        wj(A / f"models/item/{keep}.json", lj(A / f"models/item/{src}.json"))
    for src in list(MERGES.values()) + DROPPED:
        for p in (A / f"blockstates/{src}.json", A / f"models/item/{src}.json", A / f"items/{src}.json",
                  D / f"pysift/loot_table/blocks/{src}.json", D / f"pysift/loot_tables/blocks/{src}.json"):
            remove(p)
        for m in (A / "models/block").glob(f"{src}*.json"):
            if re.fullmatch(re.escape(src) + r"(_bottom)?\.json", m.name):
                remove(m)
    for n in CLEANUP:
        remove(A / n)
    for p in (D / "minecraft/tags").rglob("*.json"):
        j = lj(p)
        j2 = strip_refs(j, gone)
        if j2 != j:
            print("  tag", p.relative_to(D))
            wj(p, j2)
    for lang in ("zh_tw", "en_us"):
        p = A / f"lang/{lang}.json"
        j = lj(p)
        j2 = {k: v for k, v in j.items() if not any(k.endswith(f".pysift.{s}") for s in list(MERGES.values()) + DROPPED)}
        if j2 != j:
            wj(p, j2)


def rename():
    print("== rename")
    hits = {}
    moves = []
    for p in list(files()):
        if p.suffix in TEXT:
            s = p.read_text(encoding="utf-8")
            n = TOKEN.sub(lambda m: RENAMES[m.group(1)], s)
            if n != s:
                for m in TOKEN.finditer(s):
                    a, b = max(0, m.start() - 12), min(len(s), m.end() + 12)
                    hits.setdefault(s[a:b].replace("\n", " "), set()).add(p.relative_to(P).as_posix())
                backup(p)
                if APPLY:
                    p.write_text(n, encoding="utf-8")
        name = TOKEN.sub(lambda m: RENAMES[m.group(1)], p.name)
        if name != p.name:
            moves.append((p, p.with_name(name)))
    for p, dst in moves:
        if dst.exists():
            sys.exit(f"target already exists: {dst.relative_to(P)}")
        print("  mv", p.relative_to(P).as_posix(), "->", dst.name)
        backup(p)
        if APPLY:
            p.rename(dst)
    print(f"  {len(hits)} distinct contexts, {len(moves)} files renamed")
    if "--contexts" in sys.argv:
        for ctx in sorted(hits):
            print("   ", repr(ctx))


def names():
    print("== names")
    for lang, i in (("zh_tw", 0), ("en_us", 1)):
        p = A / f"lang/{lang}.json"
        j = lj(p) if APPLY else {}
        for bid, n in NAMES.items():
            for key in ("block", "item"):
                j[f"{key}.pysift.{bid}"] = n[i]
        wj(p, j)


def main():
    if (A / "blockstates/sift_wheat.json").exists() or (A / "blockstates/rift_mint_tall_grass.json").exists():
        sys.exit("already applied (new IDs exist)")
    merge()
    rename()
    names()
    print("applied; backups in" if APPLY else "dry run; backups would go to", BK.relative_to(P))


if __name__ == "__main__":
    main()
