"""植被總表與 AI 產生貼圖的待畫清單 → art_requests/vegetation_todo.md（附兩張總覽圖）。
Usage: python -I tools/build_art_requests.py [--seed]

A. 植被總表：從 ModVegetation.java / SiftFlora.java 讀出所有植被 ID，順著 blockstate → 模型（含 parent）→ 貼圖，
   列出模型類型、貼圖與尺寸、物品圖示、材質來源、狀態。總覽圖 art_requests/vegetation_todo_overview.png。
B. 全專案 AI／腳本產生的貼圖（AI_CATALOG），加上 build_progression.py 還沒被替換的臨時圖。
   總覽圖 art_requests/ai_textures_overview.png。
--seed：把 AI_CATALOG 裡「AI 產生／由圖轉出」而且還沒登記的檔案，登記到 tools/ai_texture_hashes.json
（art_guard.py 的臨時圖紀錄），之後使用者用同檔名覆蓋就不會被腳本蓋回去。
"""
import json, re, sys, hashlib, fnmatch
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parents[1]
A = P / "src/main/resources/assets/pysift"
T = A / "textures"
OUT_MD = P / "art_requests/vegetation_todo.md"
OUT_VEG_PNG = P / "art_requests/vegetation_todo_overview.png"
OUT_AI_PNG = P / "art_requests/ai_textures_overview.png"
sys.path.insert(0, str(P / "tools"))
import art_guard

# 植被：ID → 備註（合併、新匯入）
MERGED = {
    "rift_orange_short_grass": "原 orange_rift_grass，併入 sift_orange_short_grass 的新材質",
    "rift_orange_tall_grass": "原 orange_tall_rift_grass，併入 sift_orange_tall_grass 的新材質",
    "rift_red_short_grass": "原 crimson_short_sprouts，併入 sift_red_short_grass 的新材質",
    "rift_mint_short_grass": "原 mint_rift_grass，併入 sift_short_grass 的新材質",
    "rift_mint_tall_grass": "原 sift_tallgrass，成為薄荷短草的高草版",
    "glowshade_short_grass": "原 glowshade_grass，草葉改用 sculk_grass（幽匿草）貼圖，發光層重新對齊",
}
IMPORTED_NEW = {"carapace_flower", "carapace_short_grass", "carapace_vine", "white_flower_patch", "yellow_flower_patch",
                "soul_bubble_flower", "green_sift_vine", "orange_sift_vine", "soul_vine", "sift_wall_leaves", "cleaver_plant",
                "soul_cleaver_plant", "sift_wheat_sprout", "sift_wheat_plant", "sift_wheat", "yellow_leaf_litter"}

# 全專案 AI／腳本產生的貼圖：(textures/ 底下的 glob, 用途, 產生腳本, 類別)
# 類別：AI = 腳本從零畫的；轉出 = 由使用者的圖或原版貼圖重新上色／裁切；待確認 = 腳本畫過，但可能已被換成使用者的圖
AI_CATALOG = [
    ("block/vegetation/humus_fern.png", "腐殖蕨 葉片", "tools/models/gen_blade_models.py", "AI"),
    ("block/vegetation/humus_bush.png", "腐殖灌木 葉片", "tools/models/gen_blade_models.py", "AI"),
    ("block/vegetation/bone_spire.png", "骨刺", "tools/worldgen/make_decor_textures.py", "AI"),
    ("block/vegetation/puff_grass_*.png", "蓬鬆草（上／下半）", "tools/worldgen/make_decor_textures.py", "AI"),
    ("block/vegetation/glowshade_tall_grass.png", "夜光高草 葉片", "tools/models/gen_batch3.py", "AI"),
    ("item/glowshade_tall_grass.png", "夜光高草 物品圖示", "tools/models/gen_batch3.py", "AI"),
    ("block/vegetation/coral_leaf_carpet*.png", "珊瑚落葉（葉、枝）", "tools/models/gen_batch3.py", "AI"),
    ("item/coral_leaf_carpet.png", "珊瑚落葉 物品圖示", "tools/models/gen_batch3.py", "AI"),
    ("block/vegetation/abyss_grass.png", "深淵草", "tools/worldgen/make_abyss_grass.py", "AI"),
    ("block/vegetation/tall_ember_grass_*.png", "高餘燼草", "tools/worldgen/make_abyss_grass.py", "AI"),
    ("block/vegetation/sift_pink_loam.png", "粉壤土（由帶狀泥岩重新上色）", "tools/worldgen/make_pink_loam.py", "轉出"),
    ("item/*_spawn_egg.png", "生怪蛋（臉取自生物貼圖）", "tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py", "AI"),
    ("mob_effect/ensnared.png", "定身效果圖示", "tools/models/hunter_trapper_assets.py", "AI"),
    ("mob_effect/soul_deprivation.png", "靈魂剝奪效果圖示（只在缺檔時寫）", "tools/worldgen/build_vegetation.py", "待確認"),
    ("item/soul_antidote.png", "靈魂解藥", "tools/items/make_soul_burn_textures.py", "AI"),
    ("particle/soul_wisp.png", "靈魂幽火粒子", "tools/worldgen/make_soul_wisp_textures.py", "AI"),
    ("particle/soul_trail.png", "靈魂拖尾粒子", "tools/worldgen/make_soul_wisp_textures.py", "AI"),
    ("gui/sprites/hud/heart/soul_*.png", "靈魂剝奪的愛心（原版愛心重新上色）", "tools/items/make_soul_hearts.py", "轉出"),
    ("block/soul_willow/*.png", "靈柳木建材組（原版橡木重新上色）", "tools/worldgen/build_soul_willow_wood.py", "轉出"),
    ("item/soul_willow_*.png", "靈柳木物品（原版橡木重新上色）", "tools/worldgen/build_soul_willow_wood.py", "轉出"),
    ("entity/boat/soul_willow.png", "靈柳木船", "tools/worldgen/build_soul_willow_wood.py", "轉出"),
    ("entity/chest_boat/soul_willow.png", "靈柳木運輸船", "tools/worldgen/build_soul_willow_wood.py", "轉出"),
    ("block/soul_crystal_block.png", "靈魂晶塊（取自 echo_golem 貼圖）", "tools/worldgen/build_soul_crystal.py", "轉出"),
    ("entity/hunter.png", "Hunter（可能已換成使用者的合併貼圖）", "tools/entity/build_sift_creatures.py", "待確認"),
    ("entity/trapper.png", "Trapper（可能已換成使用者的合併貼圖）", "tools/entity/build_sift_creatures.py", "待確認"),
    ("entity/sculk_cube.png", "幽匿方塊", "tools/entity/build_sift_creatures.py", "待確認"),
]
RIFT_FLORA_TEX = {"blue_curled_fern", "pink_curled_fern", "white_curled_fern", "olive_forked_stalk", "rift_yellow_short_grass",
                  "canopy_leaf_blue", "canopy_leaf_green", "canopy_leaf_white", "canopy_stem_blue", "canopy_stem_green",
                  "canopy_stem_white", "yellow_agave_leaf", "yellow_flower_head", "yellow_flower_stem"}
# sift_vegetation_assets 自帶的物品圖示；其他植被的 textures/item 圖示是 veg_models.py icon 從方塊模型算繪的
IMPORTED_ICONS = {"carapace_vine", "soul_bubble_flower", "green_sift_vine", "orange_sift_vine", "souls_vine", "cleaver_plant",
                  "soul_cleaver_plant", "yellow_leaf_litter"}
BLOOMS = {"golden_bloom", "sun_bloom", "rose_bloom", "dusk_bloom"}

FONT = "C:/Windows/Fonts/msjh.ttc"


def lj(p): return json.loads(Path(p).read_text(encoding="utf-8"))


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def veg_ids():
    ids = []
    for f in ("src/main/java/pryuan05/pysift/block/ModVegetation.java", "src/main/java/pryuan05/pysift/progression/SiftFlora.java"):
        ids += re.findall(r'register(?:Block)?\("([a-z0-9_]+)"', (P / f).read_text(encoding="utf-8"))
    return [i for i in ids if i != "sift_pink_loam"] + ["sift_pink_loam"]


def split(ref):
    ns, path = ref.split(":", 1) if ":" in ref else ("minecraft", ref)
    return ns, path


def model_chain(ref):
    """模型和它的 parent 鏈：[(ref, json or None)]。"""
    out = []
    while ref:
        ns, path = split(ref)
        j = lj(A / f"models/{path}.json") if ns == "pysift" and (A / f"models/{path}.json").exists() else None
        out.append((f"{ns}:{path}", j))
        ref = j.get("parent") if j else None
    return out


def textures_of(ref):
    tex = {}
    for _, j in reversed(model_chain(ref)):
        if j:
            tex.update(j.get("textures", {}))
    vals = []
    for v in tex.values():
        while isinstance(v, str) and v.startswith("#"):
            v = tex.get(v[1:])
        if isinstance(v, str) and v not in vals:
            vals.append(v)
    return vals


def blockstate_models(bid):
    bs = lj(A / f"blockstates/{bid}.json")
    refs = []

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("model"), str) and o["model"] not in refs:
                refs.append(o["model"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(bs)
    return refs, "half=" in json.dumps(bs)


def model_kind(refs, tall):
    chain = [(r, j) for ref in refs for r, j in model_chain(ref)]
    s = " ".join(r for r, _ in chain)
    tex = " ".join(json.dumps(j.get("textures", {})) for _, j in chain if j)
    if "custom/" in s:
        k = "自訂立體模型（models/custom）"
    elif "flowerbed" in s:
        k = "原版花床（1~4 層）"
    elif "_glow" in tex:
        k = "十字＋發光層"
    elif "tinted_cross" in s:
        k = "原版十字（可染色）"
    elif "block/cross" in s or '"cross"' in tex:
        k = "原版十字" if "block/cross" in s else "十字（自訂元素）"
    elif "cube_column" in s:
        k = "柱狀方塊（cube_column）"
    elif "vine" in s:
        k = "藤（貼牆面）"
    elif "leaves" in s or "cube_all" in s:
        k = "方塊（cube_all）"
    else:
        k = "3D 模型（Blockbench／腳本）"
    return ("兩格高（上／下半）・" if tall else "") + k


def png_size(ref):
    ns, path = split(ref)
    if ns != "pysift":
        return None
    p = T / f"{path}.png"
    return Image.open(p).size if p.exists() else None


def tex_source(ref, progression):
    ns, path = split(ref)
    if ns != "pysift":
        return "原版貼圖（暫借）"
    name = path.rsplit("/", 1)[-1]
    rel = f"{path}.png"
    for pat, _, script, kind in AI_CATALOG:
        if fnmatch.fnmatch(rel, pat):
            return {"AI": "AI 產生", "轉出": "由圖轉出", "待確認": "待確認"}[kind] + f"（{Path(script.split('、')[0]).name}）"
    if path.startswith("block/progression/"):
        h = hashlib.sha1((T / rel).read_bytes()).hexdigest() if (T / rel).exists() else None
        return "AI 產生（build_progression.py 臨時圖）" if progression.get(path) == h else "使用者繪製"
    if name.startswith("soft_"):
        return "由使用者的圖轉出（灰色母版＋色盤）"
    if name.startswith("soul_willow_") and name != "soul_willow_sapling":
        return "由使用者的圖轉出（soul_willow_sheet.png）"
    if name in BLOOMS:
        return "使用者的 Blockbench 模型（待確認）"
    if name in RIFT_FLORA_TEX:
        return "匯入素材 rift_dimension_flora（待確認）"
    if path.startswith("block/") and "/" not in path[len("block/"):]:
        return "匯入素材 sift_vegetation_assets（待確認）"
    if path.startswith("item/") and name in IMPORTED_ICONS:
        return "匯入素材 sift_vegetation_assets（待確認）"
    if path.startswith("item/"):
        return "由模型算繪（veg_models.py icon）"
    return "待確認"


def status(bid, sources, sizes=()):
    odd = [f"{w}x{h}" for w, h in sizes if w != h]
    if odd:
        return "尺寸異常（" + "、".join(odd) + "，十字模型會被拉伸）"
    if bid in MERGED:
        return "合併後換新材質（待確認）"
    if any(s.startswith("AI") for s in sources):
        return "暫用（待補畫）"
    if any(s.startswith("原版") for s in sources):
        return "缺圖（借用原版）"
    if any("待確認" in s for s in sources):
        return "已完成（來源待確認）"
    return "已完成"


def vegetation_rows(zh, progression):
    rows = []
    for bid in veg_ids():
        refs, tall = blockstate_models(bid)
        texs = []
        for r in refs:
            for t in textures_of(r):
                if t not in texs:
                    texs.append(t)
        item = lj(A / f"models/item/{bid}.json")
        icon = item.get("textures", {}).get("layer0") or ("（用方塊模型）" if "parent" in item else "")
        srcs = [tex_source(t, progression) for t in texs]
        if icon and not icon.startswith("（"):
            srcs_icon = tex_source(icon, progression)
        else:
            srcs_icon = ""
        rows.append(dict(id=bid, zh=zh.get(f"block.pysift.{bid}", "?"), models=refs, kind=model_kind(refs, tall),
                         texs=texs, icon=icon, src=list(dict.fromkeys(srcs + ([srcs_icon] if srcs_icon else []))),
                         status=status(bid, srcs + [srcs_icon], [png_size(t) for t in texs if png_size(t)]), note=MERGED.get(bid, "新匯入" if bid in IMPORTED_NEW else "")))
    return rows


def ai_rows(progression):
    rows = []
    for pat, use, script, kind in AI_CATALOG:
        for p in sorted(T.glob(pat)):
            rows.append(dict(path=p.relative_to(T).as_posix(), use=use, script=script, kind=kind, size=Image.open(p).size))
    for key, h in sorted(progression.items()):
        p = T / f"{key}.png"
        if p.exists() and hashlib.sha1(p.read_bytes()).hexdigest() == h:
            rows.append(dict(path=f"{key}.png", use="進度內容臨時圖（詳見 texture_todo.md）", script="tools/progression/build_progression.py",
                             kind="AI", size=Image.open(p).size))
    return rows


def thumb(path, size):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    s = max(1, min(size // w, size // h))
    im = im.resize((w * s, h * s), Image.NEAREST) if s > 1 else im.copy()
    im.thumbnail((size, size), Image.NEAREST)
    return im


def checker(w, h, c=8):
    bg = Image.new("RGBA", (w, h), (58, 58, 64, 255))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, c):
        for x in range(0, w, c):
            if (x // c + y // c) % 2:
                d.rectangle([x, y, x + c - 1, y + c - 1], fill=(70, 70, 78, 255))
    return bg


def sheet(items, out, title, cols=6, cell=64, label_h=46, per=3):
    """items: [(label lines, [png paths])]"""
    cw = max(cell * per + 4 * (per - 1), 150) + 12
    rows = (len(items) + cols - 1) // cols
    img = Image.new("RGBA", (cols * cw + 20, rows * (cell + label_h + 14) + 60), (32, 32, 38, 255))
    d = ImageDraw.Draw(img)
    d.text((14, 12), title, fill=(240, 240, 240), font=font(22))
    for i, (labels, pngs) in enumerate(items):
        x0 = 14 + (i % cols) * cw
        y0 = 52 + (i // cols) * (cell + label_h + 14)
        for k, pth in enumerate(pngs[:3]):
            bx = x0 + k * (cell + 4)
            img.alpha_composite(checker(cell, cell), (bx, y0))
            if pth and Path(pth).exists():
                t = thumb(pth, cell)
                img.alpha_composite(t, (bx + (cell - t.width) // 2, y0 + (cell - t.height) // 2))
        for k, line in enumerate(labels[:3]):
            d.text((x0, y0 + cell + 3 + k * 15), line, fill=(225, 225, 225) if k == 0 else (170, 200, 255), font=font(12))
    img.save(out)


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(":--" for _ in header) + " |"]
    out += ["| " + " | ".join(str(c).replace("|", "／") for c in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    zh = lj(A / "lang/zh_tw.json")
    progression = lj(P / "tools/progression/placeholder_hashes.json")
    vrows = vegetation_rows(zh, progression)
    arows = ai_rows(progression)
    # 植被總表裡來源「待確認」的貼圖（匯入素材、Blockbench 模型、來源不明）也全部列進待畫清單
    seen = {r["path"] for r in arows}
    for r in vrows:
        for ref, what in [(t, "貼圖") for t in r["texs"]] + ([(r["icon"], "物品圖示")] if r["icon"] and not r["icon"].startswith("（") else []):
            ns, path = split(ref)
            src = tex_source(ref, progression)
            if ns != "pysift" or "待確認" not in src or f"{path}.png" in seen or not (T / f"{path}.png").exists():
                continue
            seen.add(f"{path}.png")
            arows.append(dict(path=f"{path}.png", use=f"{r['zh']} {what}", script=src.replace("（待確認）", ""), kind="待確認",
                              size=Image.open(T / f"{path}.png").size))

    if "--seed" in sys.argv:
        state = art_guard._load()
        new = [T / r["path"] for r in arows if r["kind"] in ("AI", "轉出") and "build_progression" not in r["script"]
               and art_guard.key(T / r["path"]) not in state]
        if new:
            art_guard.record(*new)
        print("seeded", len(new), "textures into", art_guard.STATE.relative_to(P))

    def short(ref):
        ns, path = split(ref)
        sz = png_size(ref)
        return f"`{path if ns == 'pysift' else ref}`" + (f" {sz[0]}x{sz[1]}" if sz else "")

    lines = [f"# 植被總表與 AI 產生貼圖待畫清單",
             "",
             "由 `tools/build_art_requests.py` 產生，重跑會更新（不要手動改這份）。",
             "",
             "**怎麼替換**：畫好後用同樣的檔名覆蓋 `src/main/resources/assets/pysift/textures/` 底下的檔案即可，路徑以下都省略這段。",
             "產生這些圖的腳本已加上臨時圖保護（`tools/art_guard.py`），只要檔案和腳本上次畫的不同，重跑就不會蓋掉你的圖。",
             "",
             f"## A. 植被總表（{len(vrows)} 種）",
             "",
             "總覽圖：`art_requests/vegetation_todo_overview.png`（每格最多 3 張貼圖，第二行是狀態）。",
             "",
             "- **使用者繪製**：你給的圖。**由使用者的圖轉出**：用你的圖套色盤、裁切或重新上色。",
             "- **AI 產生**：腳本從零畫的臨時圖，列在下面 B 表，等你重畫。",
             "- **匯入素材**：`sift_vegetation_assets.zip`、`rift_dimension_flora_assets.zip`，來源不確定，標成「待確認」。",
             "",
             md_table(["#", "ID", "中文名", "方塊模型", "模型類型", "貼圖（尺寸）", "物品圖示", "材質來源", "狀態", "備註"],
                      [(i + 1, f"`{r['id']}`", r["zh"], "<br>".join(f"`{m.split(':')[1]}`" for m in r["models"]), r["kind"],
                        "<br>".join(short(t) for t in r["texs"]), short(r["icon"]) if r["icon"] and not r["icon"].startswith("（") else r["icon"],
                        "<br>".join(r["src"]), r["status"], r["note"]) for i, r in enumerate(vrows)]),
             "",
             f"## B. AI 產生與待確認的貼圖（{len(arows)} 張，全專案）",
             "",
             "總覽圖：`art_requests/ai_textures_overview.png`。類別：**AI** = 腳本從零畫的；**轉出** = 由你的圖或原版貼圖重新上色／裁切，"
             "可以沿用也可以重畫；**待確認** = 腳本畫過但可能已換成你的圖，或是匯入素材、來源不明的圖：是你畫的就保留，不是就重畫。",
             "",
             md_table(["#", "檔案", "用途", "尺寸", "產生腳本／來源", "類別"],
                      [(i + 1, f"`{r['path']}`", r["use"], f"{r['size'][0]}x{r['size'][1]}", (f"`{r['script']}`" if r["script"].startswith("tools/") else r["script"]), r["kind"])
                       for i, r in enumerate(arows)]),
             ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    def tex_path(ref):
        ns, path = split(ref)
        return T / f"{path}.png" if ns == "pysift" else None
    sheet([([r["id"], r["status"], r["zh"]], [tex_path(t) for t in r["texs"]]) for r in vrows], OUT_VEG_PNG,
          f"植被總表（{len(vrows)} 種）：ID／狀態／中文名")
    sheet([([r["path"].rsplit("/", 1)[-1], r["kind"] + "・" + (Path(r["script"].split("、")[0]).name if r["script"].startswith("tools/") else r["script"][:10]), r["use"][:14]], [T / r["path"]])
           for r in arows], OUT_AI_PNG, f"AI 產生與待確認的貼圖（{len(arows)} 張）：檔名／類別・來源／用途", cols=9, cell=56, per=1)
    print(f"wrote {OUT_MD.relative_to(P)} ({len(vrows)} vegetation, {len(arows)} AI textures) and 2 overview sheets")


if __name__ == "__main__":
    main()
