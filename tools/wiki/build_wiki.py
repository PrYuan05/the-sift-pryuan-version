"""隙浮 Wiki 產生器：從模組資料與 tools/wiki/content/*.md 產生 docs/wiki/（像 Minecraft Wiki 的單頁網站）。

  python -I tools/wiki/build_wiki.py            # 產生網站（會順便重畫圖示圖集）
  python -I tools/wiki/build_wiki.py --check    # 只做檢查：缺名稱、缺圖示、斷掉的站內連結

輸出（檔案很少，GitHub Pages、直接開檔、claude.ai 網頁都能用）：
  docs/wiki/index.html   殼層（導覽、搜尋）        docs/wiki/wiki.css / wiki.js
  docs/wiki/data.js      所有頁面（HTML 片段）與搜尋索引，用 <script> 載入，file:// 也能開
  docs/wiki/img/icons.png + icons.json   方塊與物品圖示圖集（render_icons.py）
  docs/wiki/img/mobs/*.png、img/shots/*.jpg       生物與場景截圖（crop_shots.py 從遊戲內截圖裁切）

資料都自動讀模組：語系（zh_tw / en_us，原版的從 Loom client jar）、配方、標籤、掉落表、生態域（溫度、生物生成、
地物）、結構與結構組、生物屬性（entity/mob/*.java 的 createAttributes）。手寫的說明在 tools/wiki/content/。"""
import html, json, math, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_icons as RI  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources"
DATA = RES / "data"
ASSETS = RES / "assets"
JAVA = ROOT / "src/main/java/pryuan05/pysift"
CONTENT = Path(__file__).resolve().parent / "content"
OUT = ROOT / "docs/wiki"
JAR = RI.JAR
JAR_NAMES = RI.JAR_NAMES


# ----------------------------------------------------------------------------------------------------------- utils
def esc(s):
    return html.escape(str(s), quote=True)


def jload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def jar_json(name):
    return json.loads(JAR.read(name)) if name in JAR_NAMES else None


def norm(i):
    i = i.strip()
    if i.startswith("#"):
        return "#" + norm(i[1:])
    return i if ":" in i else "minecraft:" + i


# ------------------------------------------------------------------------------------------------------- language
LANG = {"zh": {}, "en": {}}
for code, key in (("zh_tw", "zh"), ("en_us", "en")):
    v = jar_json(f"assets/minecraft/lang/{code}.json") or {}
    LANG[key].update(v)
    LANG[key].update(jload(ASSETS / f"pysift/lang/{code}.json"))


def tr(key, lang="zh"):
    return LANG[lang].get(key) or LANG["en"].get(key)


def name(i, lang="zh"):
    i = norm(i)
    if i.startswith("#"):
        ns, p = i[1:].split(":")
        return tr(f"tag.item.{ns}.{p.replace('/', '.')}", lang) or f"#{p}"
    ns, p = i.split(":")
    if p == "sift_codex":
        return tr("book.pysift.sift_codex.name", lang) or "隙浮手記"
    for k in (f"item.{ns}.{p}", f"block.{ns}.{p}", f"entity.{ns}.{p}", f"biome.{ns}.{p}"):
        v = tr(k, lang)
        if v:
            return v
    return p.replace("_", " ")


# ------------------------------------------------------------------------------------------------------------ tags
TAGS = {}


def _load_tags():
    for d in DATA.iterdir():
        for kind in ("item", "block"):
            base = d / "tags" / kind
            if base.exists():
                for f in base.rglob("*.json"):
                    key = f"{kind}:{d.name}:{f.relative_to(base).with_suffix('').as_posix()}"
                    TAGS.setdefault(key, []).extend(jload(f).get("values", []))
    for n in JAR_NAMES:
        m = re.match(r"data/(\w+)/tags/(item|block)/(.+)\.json$", n)
        if m:
            key = f"{m.group(2)}:{m.group(1)}:{m.group(3)}"
            TAGS.setdefault(key, []).extend(json.loads(JAR.read(n)).get("values", []))


_load_tags()


def expand(tag, kind="item", seen=None):
    seen = seen or set()
    tag = norm(tag).lstrip("#")
    if tag in seen:
        return []
    seen.add(tag)
    out = []
    for v in TAGS.get(f"{kind}:{tag}", []):
        v = v["id"] if isinstance(v, dict) else v
        out += expand(v[1:], kind, seen) if v.startswith("#") else [norm(v)]
    return out


# --------------------------------------------------------------------------------------------------------- recipes
def ing(x):
    """An ingredient -> list of item ids (tags expanded, tag kept as first marker)."""
    if x is None:
        return []
    if isinstance(x, list):
        return [i for e in x for i in ing(e)]
    if isinstance(x, dict):
        x = x.get("item") or x.get("id") or ("#" + x["tag"] if "tag" in x else None)
        if x is None:
            return []
    x = norm(x)
    if x.startswith("#"):
        return expand(x) or [x]
    return [x]


def result(r):
    res = r.get("result") or r.get("output")
    if isinstance(res, str):
        return norm(res), 1, None
    comps = res.get("components", {})
    return norm(res["id"]), res.get("count", 1), comps


KIND_NAME = {"crafting_shaped": "工作台", "crafting_shapeless": "工作台（無序）", "smelting": "熔爐", "blasting": "高爐",
             "smoking": "煙燻爐", "campfire_cooking": "營火", "stonecutting": "切石機", "smithing_transform": "鍛造台",
             "brewing": "釀造台", "crafting_transmute": "工作台（轉換）"}


def load_recipes():
    out = []
    for f in sorted((DATA / "pysift/recipe").glob("*.json")):
        r = jload(f)
        t = r.get("type", "").split(":")[-1]
        if t not in KIND_NAME:
            continue
        try:
            rid, cnt, comps = result(r)
        except (KeyError, TypeError):
            continue
        rec = {"file": f.stem, "kind": t, "out": rid, "count": cnt, "comps": comps or {}}
        if t == "crafting_shaped":
            pat = r["pattern"]
            key = {k: ing(v) for k, v in r["key"].items()}
            rec["grid"] = [[key.get(ch, []) if ch != " " else [] for ch in row.ljust(3)] for row in pat]
        elif t == "crafting_shapeless":
            rec["inputs"] = [ing(i) for i in r["ingredients"]]
        elif t in ("smelting", "blasting", "smoking", "campfire_cooking", "stonecutting"):
            rec["inputs"] = [ing(r["ingredient"])]
            rec["time"] = r.get("cookingtime")
            rec["xp"] = r.get("experience")
        elif t == "smithing_transform":
            rec["inputs"] = [ing(r.get("template")), ing(r.get("base")), ing(r.get("addition"))]
        elif t == "crafting_transmute":
            rec["inputs"] = [ing(r["input"]), ing(r["material"])]
        elif t == "brewing":
            src = r["input"]
            pot = (src.get("potion_contents") or {}).get("potions") or (src.get("potion_contents") or {}).get("potion")
            rec["inputs"] = [[norm(src["item"])], ing(r["reagent"])]
            rec["potion_in"] = pot
            rec["potion_out"] = ((rec["comps"].get("minecraft:potion_contents") or {}).get("potion"))
        out.append(rec)
    return out


RECIPES = load_recipes()
MADE_BY = defaultdict(list)
USED_IN = defaultdict(list)
for i, r in enumerate(RECIPES):
    MADE_BY[r["out"]].append(i)
    ids = set()
    for row in r.get("grid", []):
        for c in row:
            ids.update(c)
    for c in r.get("inputs", []):
        ids.update(c)
    for x in ids:
        if not x.startswith("#"):
            USED_IN[x].append(i)

# resonance core recipes live in Java (ResonanceCoreBlockEntity), not JSON
EXTRA_RECIPES = [
    ("共鳴靈陣", ["minecraft:amethyst_shard"] + ["minecraft:sculk"] * 4 + ["pysift:soul_essence"] * 4, "minecraft:echo_shard", 2),
    ("共鳴靈陣", ["minecraft:amethyst_cluster"] + ["pysift:soul_essence"] * 4, "pysift:charoite", 4),
    ("共鳴靈陣", ["minecraft:deepslate"] + ["minecraft:bone_block"] * 4 + ["pysift:soul_crystal_block"] * 4,
     "minecraft:reinforced_deepslate", 1),
]


# ------------------------------------------------------------------------------------------------------ loot tables
def count_of(entry):
    lo = hi = 1
    fns = []
    for k in ("functions", "modifier", "modifiers"):
        v = entry.get(k, [])
        fns += v if isinstance(v, list) else [v]
    for fn in fns:
        if isinstance(fn, dict) and fn.get("function", fn.get("type", "")).endswith("set_count"):
            c = fn["count"]
            if isinstance(c, (int, float)):
                lo = hi = c
            elif isinstance(c, dict):
                lo, hi = c.get("min", c.get("value", 1)), c.get("max", c.get("value", 1))
    return lo, hi


def loot_items(table):
    """[(item, lo, hi, chance or None, note)] from a loot table (one level of nesting, alternatives flattened)."""
    out = []
    for pool in table.get("pools", []):
        entries = pool.get("entries", [])
        total = sum(e.get("weight", 1) for e in entries if e.get("type", "").endswith(("item", "empty", "tag")))
        rolls = pool.get("rolls", 1)
        rolls_txt = rolls if isinstance(rolls, (int, float)) else f"{rolls.get('min', '?')}–{rolls.get('max', '?')}"
        pool_cond = [c.get("condition", "") for c in pool.get("conditions", [])]
        for e in entries:
            stack = [e]
            while stack:
                e = stack.pop()
                t = e.get("type", "").split(":")[-1]
                if t in ("alternatives", "group", "sequence"):
                    stack += e.get("children", [])
                    continue
                if t != "item":
                    continue
                lo, hi = count_of(e)
                chance = None
                for c in e.get("conditions", []) + pool.get("conditions", []):
                    if c.get("condition", "").endswith("random_chance"):
                        chance = c.get("chance")
                    if c.get("condition", "").endswith("random_chance_with_enchanted_bonus"):
                        chance = c.get("unenchanted_chance")
                w = e.get("weight", 1)
                share = (w / total) if total and len(entries) > 1 else None
                player = any(x.endswith("killed_by_player") for x in pool_cond) or \
                    any(c.get("condition", "").endswith("killed_by_player") for c in e.get("conditions", []))
                out.append({"id": norm(e["name"]), "lo": lo, "hi": hi, "chance": chance, "share": share,
                            "rolls": rolls_txt, "player": player})
    return out


def load_loot(kind):
    out = {}
    for base in (DATA / "pysift/loot_table" / kind,):
        if base.exists():
            for f in base.rglob("*.json"):
                out[f.relative_to(base).with_suffix("").as_posix()] = loot_items(jload(f))
    return out


ENTITY_LOOT = load_loot("entities")
CHEST_LOOT = load_loot("chests")
BLOCK_LOOT = load_loot("blocks")
DROPPED_BY = defaultdict(list)       # item -> [mob]
FOUND_IN = defaultdict(list)         # item -> [chest table]
for mob, items in ENTITY_LOOT.items():
    for it in items:
        DROPPED_BY[it["id"]].append(mob)
for t, items in CHEST_LOOT.items():
    for it in items:
        FOUND_IN[it["id"]].append(t)


# ----------------------------------------------------------------------------------------------------------- biomes
BIOMES = {}
for f in sorted((DATA / "pysift/worldgen/biome").glob("*.json")):
    b = jload(f)
    spawns = (b.get("attributes", {}).get("minecraft:gameplay/natural_mob_spawns", {}).get("argument", {})
              .get("spawns_by_category", {}))
    BIOMES[f.stem] = {"temp": b.get("temperature"), "rain": b.get("has_precipitation"), "spawns": spawns,
                      "features": [x for step in b.get("features", []) for x in step]}

FEATURE_BLOCKS = {}


def feature_blocks(pf):
    """Block ids a placed feature (and its configured feature) puts in the world."""
    if pf in FEATURE_BLOCKS:
        return FEATURE_BLOCKS[pf]
    ns, p = pf.split(":")
    found = set()
    for kind in ("placed_feature", "configured_feature"):
        f = DATA / ns / "worldgen" / kind / f"{p}.json"
        if f.exists():
            txt = f.read_text(encoding="utf-8")
            found.update(re.findall(r'"(pysift:[a-z0-9_]+)"', txt))
            m = re.search(r'"feature"\s*:\s*"([^"]+)"', txt)
            if m and kind == "placed_feature":
                cf = DATA / m.group(1).split(":")[0] / "worldgen/configured_feature" / (m.group(1).split(":")[1] + ".json")
                if cf.exists():
                    found.update(re.findall(r'"(pysift:[a-z0-9_]+)"', cf.read_text(encoding="utf-8")))
    FEATURE_BLOCKS[pf] = {x for x in found if (ASSETS / "pysift/items" / (x.split(":")[1] + ".json")).exists()}
    return FEATURE_BLOCKS[pf]


GENERATES_IN = defaultdict(set)      # block -> biomes
for bid, b in BIOMES.items():
    for pf in b["features"]:
        for blk in feature_blocks(pf):
            GENERATES_IN[blk].add(bid)

# ------------------------------------------------------------------------------------------------------- structures
STRUCTURES = {}
for f in sorted((DATA / "pysift/worldgen/structure").glob("*.json")):
    s = jload(f)
    tag = s.get("biomes", "")
    biomes = []
    if isinstance(tag, str) and tag.startswith("#"):
        ns, p = tag[1:].split(":")
        tf = DATA / ns / "tags/worldgen/biome" / f"{p}.json"
        if tf.exists():
            biomes = [norm(v).split(":")[1] for v in jload(tf).get("values", [])]
    sset = DATA / "pysift/worldgen/structure_set" / f"{f.stem}.json"
    place = jload(sset)["placement"] if sset.exists() else {}
    STRUCTURES[f.stem] = {"biomes": biomes, "spacing": place.get("spacing"), "separation": place.get("separation"),
                          "step": s.get("step"), "type": s.get("type")}

# ------------------------------------------------------------------------------------------------------------- mobs
MOBS = {}
_reg = (JAVA / "entity/ModEntities.java").read_text(encoding="utf-8")
for m in re.finditer(r'"([a-z_]+)",\s*(\w+)::new,\s*MobCategory\.(\w+),\s*([\d.]+)f,\s*([\d.]+)f', _reg):
    mid, cls, cat, w, h = m.groups()
    if cat == "MISC":
        continue
    attrs = {}
    c = cls
    for _depth in range(3):
        src = next(JAVA.rglob(f"{c}.java"), None)
        if not src:
            break
        t = src.read_text(encoding="utf-8")
        for a, v in re.findall(r"Attributes\.([A-Z_]+),\s*([\d.]+)", t):
            attrs.setdefault(a, float(v))
        sm = re.search(r"SCALE\s*=\s*([\d.]+)", t)
        if sm and "SCALE" not in attrs:
            attrs["SCALE"] = float(sm.group(1))
        ext = re.search(r"class\s+\w+\s+extends\s+(\w+)", t)
        if not ext or "MAX_HEALTH" in attrs:
            break
        c = ext.group(1)
    MOBS[mid] = {"cat": cat, "w": float(w), "h": float(h), "attrs": attrs, "cls": cls}
MOBS.setdefault("sift_warden", {"cat": "CREATURE", "w": 0.9, "h": 2.9, "attrs": {}, "cls": "SiftWardenEntity"})
for _k, _v in {"MAX_HEALTH": 500.0, "ATTACK_DAMAGE": 15.0, "MOVEMENT_SPEED": 0.3, "KNOCKBACK_RESISTANCE": 1.0}.items():
    MOBS["sift_warden"]["attrs"].setdefault(_k, _v)     # vanilla warden values, attack lowered to 15
BOSSES = ["harmonizer", "monarch", "sculk_monstrosity"]
SPAWNS_OF = defaultdict(list)        # mob -> [(biome, weight, min, max, category)]
for bid, b in BIOMES.items():
    for cat, lst in b["spawns"].items():
        for s in lst:
            c = s.get("count", {})
            lo = c.get("min_inclusive", s.get("minCount", 1)) if isinstance(c, dict) else c
            hi = c.get("max_inclusive", s.get("maxCount", 1)) if isinstance(c, dict) else c
            SPAWNS_OF[norm(s["type"]).split(":")[1]].append((bid, s.get("weight"), lo, hi, cat))

# --------------------------------------------------------------------------------------------------- hand content
SECTIONS = {}


def load_content():
    for f in sorted(CONTENT.glob("*.md")):
        cur, buf = None, []
        for line in f.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^=== (\S+)(?:\s*\|\s*(.*))?$", line)
            if m:
                if cur:
                    SECTIONS[cur[0]] = (cur[1], "\n".join(buf).strip())
                cur, buf = (m.group(1), (m.group(2) or "").strip()), []
            else:
                buf.append(line)
        if cur:
            SECTIONS[cur[0]] = (cur[1], "\n".join(buf).strip())


load_content()

# -------------------------------------------------------------------------------------------------------- icons
ICON = {}


def icon_index():
    ids = set(ITEMS)
    for r in RECIPES:
        ids.add(r["out"])
        for row in r.get("grid", []):
            for c in row:
                ids.update(x for x in c if not x.startswith("#"))
        for c in r.get("inputs", []):
            ids.update(x for x in c if not x.startswith("#"))
    for items in list(ENTITY_LOOT.values()) + list(CHEST_LOOT.values()):
        ids.update(i["id"] for i in items)
    ids.update(SECTION_ITEM_REFS)
    ICON.update(RI.build(sorted(ids)))


SECTION_ITEM_REFS = set()
for _t, body in SECTIONS.values():
    for ref in re.findall(r"\[\[((?:pysift|minecraft):[a-z0-9_/]+)", body):
        SECTION_ITEM_REFS.add(ref)

COLS = 32


def ic(i, size=32, title=True):
    i = norm(i)
    n = ICON.get(i, 0)
    t = f' title="{esc(name(i))}"' if title else ""
    return (f'<span class="ic s{size}" style="--x:{n % COLS};--y:{n // COLS}"{t}></span>')


def is_page_item(i):
    return i.startswith("pysift:") and i in ITEMS


def item_link(i, label=None, size=32):
    i = norm(i)
    lab = esc(label or name(i))
    if is_page_item(i):
        return f'<a class="il" href="#/item/{i[7:]}">{ic(i, size)}{lab}</a>'
    return f'<span class="il">{ic(i, size)}{lab}</span>'


# ------------------------------------------------------------------------------------------------------- markdown
def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)

    def link(m):
        ref, _, label = m.group(1).partition("|")
        label = label or None
        if ref.startswith(("pysift:", "minecraft:")):
            return item_link(ref, label, 24)
        kind, _, key = ref.partition(":")
        target = {"mob": f"#/mob/{key}", "biome": f"#/biome/{key}", "structure": f"#/structure/{key}",
                  "page": f"#/page/{key}", "go": f"#/{key}"}.get(kind, f"#/page/{ref}")
        if not label:
            label = {"mob": name(f"pysift:{key}"), "biome": name(f"pysift:{key}"),
                     "structure": STRUCT_NAMES.get(key, key)}.get(kind) or PAGE_TITLES.get(key, key)
        return f'<a href="{target}">{label}</a>'
    s = re.sub(r"\[\[(.+?)\]\]", link, s)
    return s


def md(text):
    out, para, lst, table = [], [], None, []

    def flush():
        nonlocal para, lst, table
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para = []
        if lst:
            out.append(f"<{lst[0]}>" + "".join(f"<li>{inline(x)}</li>" for x in lst[1]) + f"</{lst[0]}>")
            lst = None
        if table:
            rows = [r for r in table if not re.match(r"^\|?\s*:?-+", r.strip().strip("|").strip() or "-")]
            cells = [[c.strip().replace("\u2063", "|") for c in
                      re.sub(r"\[\[[^\]]*\]\]", lambda m: m.group(0).replace("|", "\u2063"), r.strip().strip("|")).split("|")]
                     for r in rows]
            h = "".join(f"<th>{inline(c)}</th>" for c in cells[0])
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in cells[1:])
            out.append(f'<table class="wt"><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table>')
            table = []
    for line in text.splitlines():
        st = line.strip()
        if not st:
            flush()
            continue
        if st.startswith("<!--"):
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", st)
        if m:
            flush()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            continue
        if st.startswith("|"):
            if para or lst:
                t = table
                table = []
                flush()
                table = t
            table.append(st)
            continue
        m = re.match(r"^([-*]|\d+\.)\s+(.*)", st)
        if m:
            if para or table:
                flush()
            kind = "ol" if m.group(1)[0].isdigit() else "ul"
            if lst and lst[0] != kind:
                flush()
            lst = lst or (kind, [])
            lst[1].append(m.group(2))
            continue
        if st.startswith("> "):
            flush()
            out.append(f'<div class="note">{inline(st[2:])}</div>')
            continue
        if lst and line.startswith("  "):
            lst[1][-1] += " " + st
            continue
        if lst or table:
            flush()
        para.append(st)
    flush()
    return "\n".join(out)


def section(key, default=""):
    return md(SECTIONS[key][1]) if key in SECTIONS else default


PAGE_TITLES = {k.split(":", 1)[1]: v[0] for k, v in SECTIONS.items() if k.startswith("page:")}
STRUCT_NAMES = {k.split(":", 1)[1]: v[0] for k, v in SECTIONS.items() if k.startswith("structure:")}


# --------------------------------------------------------------------------------------------------------- recipes
# Recipes are shipped once as compact data (RJS) and drawn by wiki.js; pages only hold <div class="rcp" data-i=..>.
RJS = []
RJS_INDEX = {}
USED_IDS = set()


def _slots(lists):
    out = []
    for c in lists:
        ids = [x for x in c if not x.startswith("#")][:8] or [x for x in c][:1]
        USED_IDS.update(ids)
        out.append(ids)
    return out


def _export(r):
    k = r["kind"]
    if k == "crafting_shaped":
        g = [row + [[]] * (3 - len(row)) for row in r["grid"]] + [[[], [], []]] * (3 - len(r["grid"]))
        lay, slots, lab = "g", _slots([c for row in g for c in row[:3]]), ""
    elif k in ("crafting_shapeless", "crafting_transmute", "resonance"):
        lay, slots, lab = "g", _slots(r["inputs"] + [[]] * (9 - len(r["inputs"]))), ""
    elif k == "smithing_transform":
        lay, slots, lab = "r", _slots(r["inputs"]), ""
    elif k == "brewing":
        lay, slots = "b", _slots(r["inputs"])
        lab = potion_name((r.get("potion_in") or "").split(":")[-1])
    else:
        lay, slots = "f", _slots(r["inputs"])
        lab = f'{r["time"] / 20:g} 秒' if r.get("time") else ""
    out_name = name(r["out"])
    if k == "brewing" and r.get("potion_out"):
        out_name = potion_name(r["potion_out"].split(":")[-1]) + "（" + name(r["out"]) + "）"
    if r["comps"].get("pysift:awakened"):
        out_name += "（覺醒）"
    USED_IDS.add(r["out"])
    return [KIND_NAME[k], r["out"], r["count"], lay, slots, out_name, lab]


def recipe_html(r):
    key = id(r)
    if key not in RJS_INDEX:
        RJS_INDEX[key] = len(RJS)
        RJS.append(_export(r))
    return f'<div class="rcp" data-i="{RJS_INDEX[key]}"></div>'


def potion_name(p):
    for k in (f"item.minecraft.potion.effect.{p}", f"potion.pysift.{p}", f"effect.pysift.{p}", f"effect.minecraft.{p}"):
        if tr(k):
            return tr(k)
    return {"awkward": "粗製的藥水"}.get(p, p)


KIND_NAME["resonance"] = "共鳴靈陣"
for _w, _ins, _o, _n in EXTRA_RECIPES:
    RECIPES.append({"file": "", "kind": "resonance", "out": _o, "count": _n, "comps": {}, "inputs": [[x] for x in _ins]})
    MADE_BY[_o].append(len(RECIPES) - 1)
    for _x in set(_ins):
        USED_IN[_x].append(len(RECIPES) - 1)
EXTRA_RECIPES = []


def extra_recipe_html(*_a):
    return ""


# ------------------------------------------------------------------------------------------- what players can get
# tools/wiki/data/creative_tabs.txt is dumped from the running game (the temporary client game test writes
# wiki_tabs.txt: "<tab> <item id>" per line). Items that are only in the "unused blocks" tab are blocks the world no
# longer generates; they are left out of the wiki unless a player can still get them (drop, chest, crafting from things
# that are obtainable). Items in no tab at all (the kinetic add-on when it is off) stay in.
TABS = defaultdict(set)
_tabs_file = Path(__file__).resolve().parent / "data/creative_tabs.txt"
if _tabs_file.exists():
    for _line in _tabs_file.read_text(encoding="utf-8").splitlines():
        if _line.strip():
            _t, _i = _line.split()
            TABS[_i].add(_t)
UNUSED_ONLY = {i for i, t in TABS.items() if t == {"pysift_unused_blocks"}}


def _obtainable():
    ok = {f"pysift:{p.stem}" for p in (ASSETS / "pysift/items").glob("*.json")} - UNUSED_ONLY
    ok |= set(GENERATES_IN) | set(DROPPED_BY) | set(FOUND_IN)
    changed = True
    while changed:
        changed = False
        for r in RECIPES:
            if r["out"] in ok:
                continue
            slots = [c for row in r.get("grid", []) for c in row] + list(r.get("inputs", []))
            if all(not c or any((x in ok) or x.startswith(("minecraft:", "#")) for x in c) for c in slots):
                ok.add(r["out"])
                changed = True
    return ok


OBTAINABLE = _obtainable()
HIDDEN = UNUSED_ONLY - OBTAINABLE
RECIPES[:] = [r for r in RECIPES if r["out"] not in HIDDEN and all(
    any(x not in HIDDEN for x in c) for c in [c for row in r.get("grid", []) for c in row] + list(r.get("inputs", [])) if c)]
MADE_BY.clear()
USED_IN.clear()
for _k, _r in enumerate(RECIPES):
    MADE_BY[_r["out"]].append(_k)
    _ids = {x for row in _r.get("grid", []) for c in row for x in c} | {x for c in _r.get("inputs", []) for x in c}
    for _x in _ids:
        if not _x.startswith("#"):
            USED_IN[_x].append(_k)
for _d in (DROPPED_BY, FOUND_IN, GENERATES_IN):
    for _h in HIDDEN:
        _d.pop(_h, None)


# ------------------------------------------------------------------------------------------------------ item data
ITEMS = sorted(f"pysift:{p.stem}" for p in (ASSETS / "pysift/items").glob("*.json"))
ITEMS = [i for i in ITEMS if i not in HIDDEN and i != "pysift:sift_codex"]
IS_BLOCK = {i for i in ITEMS if (ASSETS / "pysift/blockstates" / (i[7:] + ".json")).exists()}

TOOL_TAGS = {}
for tool in ("pickaxe", "axe", "shovel", "hoe"):
    for v in expand(f"#minecraft:mineable/{tool}", "block"):
        TOOL_TAGS.setdefault(v, tool)
TOOL_ZH = {"pickaxe": "鎬", "axe": "斧", "shovel": "鏟", "hoe": "鋤"}

COLORS = ["amber", "coral", "dusk_gold", "lavender", "mint", "rose", "soul_blue", "teal", "void"]
SHAPES = ("_slab", "_stairs", "_wall", "_pillar", "_fence_gate", "_fence", "_door", "_trapdoor", "_pressure_plate",
          "_button", "_hanging_sign", "_wall_hanging_sign", "_wall_sign", "_sign", "_shelf")
PREFIXES = ("chiseled_", "polished_", "cracked_", "smooth_", "cut_", "stripped_")


def family_of(i):
    p = i[7:]
    if p.endswith("_spawn_egg"):
        return "spawn_eggs"
    for c in COLORS:
        if p.startswith(c + "_") and (p.endswith(("_wool", "_carpet", "_concrete", "_concrete_powder", "_terracotta",
                                                   "_glazed_terracotta", "_stained_glass", "_stained_glass_pane",
                                                   "_candle", "_candle_cake", "_bed", "_banner", "_shulker_box",
                                                   "_dye", "_paper_lantern", "_wool_slab", "_wool_stairs",
                                                   "_concrete_slab", "_concrete_stairs", "_cushion"))):
            return "colors"
    if p.startswith("soul_willow") or p.startswith("stripped_soul_willow") or p.startswith("glowing_soul_willow") \
            or p.startswith("pale_soul_willow"):
        return "soul_willow"
    if i not in IS_BLOCK:
        return None
    base = p
    for s in SHAPES:
        if base.endswith(s):
            base = base[: -len(s)]
            break
    for pre in PREFIXES:
        if base.startswith(pre):
            base = base[len(pre):]
    for suf in ("_bricks", "_brick", "_tiles", "_tile"):
        if base.endswith(suf):
            base = base[: -len(suf)]
    return "stone:" + base


FAMILIES = defaultdict(list)
for i in ITEMS:
    f = family_of(i)
    if f:
        FAMILIES[f].append(i)
# stone families with a single member that is not a building block belong to "misc blocks"
for f in list(FAMILIES):
    if f.startswith("stone:") and len(FAMILIES[f]) < 3:
        FAMILIES["misc_blocks"].extend(FAMILIES.pop(f))

CATEGORY = {}
for k, v in SECTIONS.items():
    if k.startswith("cat:"):
        for line in v[1].splitlines():
            for x in re.findall(r"[a-z0-9_]+", line.split("#")[0]):
                CATEGORY.setdefault(f"pysift:{x}", k[4:])


def item_category(i):
    if i in CATEGORY:
        return CATEGORY[i]
    f = family_of(i)
    if f == "spawn_eggs":
        return "spawn_eggs"
    if f == "colors":
        return "colors"
    if f == "soul_willow":
        return "wood"
    if f and f.startswith("stone:") or f == "misc_blocks":
        return "building"
    return "blocks_other" if i in IS_BLOCK else "items_other"


CAT_TITLES = {"building": "建材與石材", "wood": "靈魂柳木", "plants": "植物與作物", "nature": "天然方塊與礦石",
              "colors": "隙浮九色", "decor": "裝飾方塊", "soulpower": "靈魂動力", "story_blocks": "故事方塊",
              "materials": "材料", "tools": "工具與盔甲", "weapons": "Boss 武器與戰鬥", "boss": "Boss 掉落",
              "story": "故事物品", "food": "食物", "drops": "生物掉落物", "misc": "其他物品", "spawn_eggs": "生怪蛋",
              "blocks_other": "其他方塊", "items_other": "其他物品（未分類）"}


# ------------------------------------------------------------------------------------------------------------ pages
PAGES = {}            # route -> {"t": title, "h": html, "s": search text}


def page(route, title, body, search="", side=""):
    PAGES[route] = {"t": title, "h": body, "s": search, "k": side}


def infobox(title, img, rows, sub=""):
    trs = "".join(f"<tr><th>{esc(k)}</th><td>{v}</td></tr>" for k, v in rows if v not in (None, ""))
    return (f'<aside class="infobox"><div class="ib-t">{esc(title)}</div>'
            f'{f"<div class=ib-s>{esc(sub)}</div>" if sub else ""}<div class="ib-i">{img}</div>'
            f"<table>{trs}</table></aside>")


def tooltip_lines(i):
    p = i[7:]
    keys = sorted(k for k in LANG["zh"] if k.startswith(f"tooltip.pysift.{p}") or k == f"item.pysift.{p}.desc"
                  or k.startswith(f"item.pysift.{p}.tooltip") or k.startswith(f"block.pysift.{p}.tooltip"))
    return [LANG["zh"][k] for k in keys]


def build_item_pages():
    for i in ITEMS:
        p = i[7:]
        rows = [("英文名", esc(name(i, "en"))), ("ID", f"<code>{esc(i)}</code>"),
                ("種類", "方塊" if i in IS_BLOCK else "物品")]
        if i in IS_BLOCK:
            t = TOOL_TAGS.get(i)
            rows.append(("適用工具", TOOL_ZH.get(t, "任何") if t else "任何／不需工具"))
        if GENERATES_IN.get(i):
            rows.append(("自然生成", "、".join(f'<a href="#/biome/{b}">{esc(name("pysift:" + b))}</a>'
                                           for b in sorted(GENERATES_IN[i]))))
        fam = family_of(i)
        body = [infobox(name(i), f'<div class="ib-icon">{ic(i, 64, False)}</div>', rows, name(i, "en"))]
        body.append(f"<h1>{esc(name(i))}</h1>")
        note = section(f"item:{p}")
        tips = tooltip_lines(i)
        if tips:
            body.append('<div class="tip">' + "".join(f"<div>{inline(t)}</div>" for t in tips) + "</div>")
        if note:
            body.append(note)
        elif not tips:
            body.append(f"<p>{esc(name(i))}是隙浮的{'方塊' if i in IS_BLOCK else '物品'}。</p>")
        # obtaining
        get = []
        if GENERATES_IN.get(i):
            get.append("<li>自然生成於：" + "、".join(f'<a href="#/biome/{b}">{esc(name("pysift:" + b))}</a>'
                                                  for b in sorted(GENERATES_IN[i])) + "</li>")
        if DROPPED_BY.get(i):
            get.append("<li>生物掉落：" + "、".join(f'<a href="#/mob/{m}">{esc(name("pysift:" + m))}</a>'
                                                for m in sorted(set(DROPPED_BY[i]))) + "</li>")
        if FOUND_IN.get(i):
            get.append("<li>箱子戰利品：" + "、".join(esc(chest_name(t)) for t in sorted(set(FOUND_IN[i]))) + "</li>")
        if get:
            body.append("<h2>取得方式</h2><ul>" + "".join(get) + "</ul>")
        made = [RECIPES[k] for k in MADE_BY.get(i, [])]
        extra = [e for e in EXTRA_RECIPES if e[2] == i]
        if made or extra:
            body.append("<h2>合成</h2><div class=recipes>" + "".join(recipe_html(r) for r in made[:24])
                        + "".join(extra_recipe_html(*e) for e in extra) + "</div>")
            if len(made) > 24:
                body.append(f"<p class=muted>另有 {len(made) - 24} 種做法未列出。</p>")
        used = [RECIPES[k] for k in USED_IN.get(i, []) if RECIPES[k]["out"] != i]
        if used:
            body.append("<h2>用途</h2><div class=recipes>" + "".join(recipe_html(r) for r in used[:30]) + "</div>")
            if len(used) > 30:
                more = "、".join(item_link(r["out"], size=24) for r in used[30:])
                body.append(f"<p>其他用途：{more}</p>")
        if fam and fam.startswith("stone:") and len(FAMILIES.get(fam, [])) > 1:
            body.append("<h2>同系列方塊</h2><div class=fam>" + "".join(item_link(x) for x in FAMILIES[fam]) + "</div>")
        page(f"item/{p}", name(i), "\n".join(body), f"{name(i)} {name(i, 'en')} {p}", "item")


def chest_name(t):
    return STRUCT_NAMES.get(t.split("/")[0], None) or {"echo_den_vault": "回音窟寶庫"}.get(t, t)


def build_item_index():
    cats = defaultdict(list)
    for i in ITEMS:
        cats[item_category(i)].append(i)
    order = ["building", "nature", "plants", "wood", "colors", "decor", "soulpower", "story_blocks", "blocks_other",
             "materials", "tools", "weapons", "boss", "story", "food", "drops", "misc", "items_other", "spawn_eggs"]
    blocks, items = [], []
    for c in order:
        if c not in cats:
            continue
        grid = "".join(f'<a class="cell" href="#/item/{i[7:]}" title="{esc(name(i))}">{ic(i, 32, False)}'
                       f'<span>{esc(name(i))}</span></a>' for i in cats[c])
        html_ = f'<h2 id="cat-{c}">{esc(CAT_TITLES.get(c, c))}<small>{len(cats[c])}</small></h2><div class="cells">{grid}</div>'
        (blocks if c in ("building", "nature", "plants", "wood", "colors", "decor", "soulpower", "story_blocks",
                         "blocks_other") else items).append(html_)
    page("blocks", "方塊", "<h1>方塊</h1>" + section("page:blocks_intro") + "".join(blocks), "方塊 blocks")
    page("items", "物品", "<h1>物品</h1>" + section("page:items_intro") + "".join(items), "物品 items")
    # building families
    fam_html = []
    for f in sorted(k for k in FAMILIES if k.startswith("stone:")):
        mem = FAMILIES[f]
        head = min(mem, key=len)
        fam_html.append(f'<tr><td>{item_link(head)}</td><td class="fam">'
                        + "".join(f'<a href="#/item/{m[7:]}" title="{esc(name(m))}">{ic(m, 32, False)}</a>' for m in mem)
                        + f"</td><td>{len(mem)}</td></tr>")
    page("building_sets", "建材家族", "<h1>建材家族</h1>" + section("page:building_sets")
         + '<table class="wt"><thead><tr><th>石材</th><th>全部方塊</th><th>數量</th></tr></thead><tbody>'
         + "".join(fam_html) + "</tbody></table>", "建材 石磚 半磚 階梯 牆")


def mob_img(mid, variant=""):
    p = f"img/mobs/{mid}{variant}.png"
    return f'<img class="mobimg" src="{p}" alt="{esc(name("pysift:" + mid))}" loading="lazy">' \
        if (OUT / p).exists() else ""


CAT_ZH = {"CREATURE": "被動／中立", "MONSTER": "敵對"}


def attr(a, k, fmt="{:g}"):
    v = a.get(k)
    return fmt.format(v) if v is not None else None


def hearts(v):
    return f"{v:g}（{v / 2:g} ♥）" if v is not None else None


def build_mob_pages():
    for mid, m in MOBS.items():
        a = m["attrs"]
        kind = "Boss" if mid in BOSSES else CAT_ZH.get(m["cat"], m["cat"])
        if mid in ("sift_warden", "echo_golem", "pollinator", "mourner", "roamroot"):
            kind = {"sift_warden": "可馴服", "echo_golem": "中立", "pollinator": "中立", "mourner": "中立",
                    "roamroot": "中立（被打才反擊）"}[mid]
        rows = [("英文名", esc(name("pysift:" + mid, "en"))), ("ID", f"<code>pysift:{mid}</code>"), ("類型", kind),
                ("生命", hearts(a.get("MAX_HEALTH"))), ("攻擊力", attr(a, "ATTACK_DAMAGE")),
                ("移動速度", attr(a, "MOVEMENT_SPEED")), ("飛行速度", attr(a, "FLYING_SPEED")),
                ("護甲", attr(a, "ARMOR")), ("擊退抗性", attr(a, "KNOCKBACK_RESISTANCE")),
                ("體型倍率", attr(a, "SCALE", "{:g}×")), ("碰撞箱", f'{m["w"]:g} × {m["h"]:g} 格')]
        img = mob_img(mid) or f'<div class="ib-icon">{ic("pysift:" + mid + "_spawn_egg", 64, False)}</div>'
        body = [infobox(name("pysift:" + mid), img, rows, name("pysift:" + mid, "en")), f"<h1>{esc(name('pysift:' + mid))}</h1>"]
        body.append(section(f"mob:{mid}"))
        if mid in BOSSES:
            body.append("<h2>Boss 共通規則</h2>" + section("page:boss_common"))
        codex = codex_text("bestiary", mid) or codex_text("bosses", mid)
        if codex:
            body.append('<h2>隙浮手記</h2><blockquote class="codex">' + codex + "</blockquote>")
        variants = ""
        if (OUT / f"img/mobs/{mid}_tropical.png").exists():
            variants = "".join(f'<figure>{mob_img(mid, v)}<figcaption>{c}</figcaption></figure>'
                               for v, c in (("", "一般"), ("_tropical", "熱帶"), ("_cold", "寒帶")))
            body.append('<h2>氣候變體</h2>' + section("page:climate_short")
                        + f'<div class="gallery">{variants}</div>')
        if mid == "blub":
            gal = "".join(f'<figure>{mob_img("blub", "_" + v)}<figcaption>{esc(tr(f"entity.pysift.blub.variant.{v}") or v)}'
                          f"</figcaption></figure>" for v in ("soul_engorged", "carapace", "meadows", "ravines", "fungal"))
            body.append(f'<h2>變種</h2><div class="gallery">{gal}</div>')
        sp = SPAWNS_OF.get(mid)
        if sp:
            rows_ = "".join(f'<tr><td><a href="#/biome/{b}">{esc(name("pysift:" + b))}</a></td><td>{w}</td>'
                            f"<td>{lo}–{hi}</td><td>{'怪物' if c == 'monster' else '生物'}</td></tr>"
                            for b, w, lo, hi, c in sorted(sp, key=lambda t: -(t[1] or 0)))
            body.append('<h2>生成</h2><table class="wt"><thead><tr><th>生態域</th><th>權重</th><th>每群數量</th>'
                        f"<th>類別</th></tr></thead><tbody>{rows_}</tbody></table>")
        drops = ENTITY_LOOT.get(mid)
        if drops:
            body.append("<h2>掉落物</h2>" + loot_table_html(drops))
        page(f"mob/{mid}", name("pysift:" + mid), "\n".join(body), f"{name('pysift:' + mid)} {name('pysift:' + mid, 'en')} {mid}", "mob")
    # index
    groups = [("Boss", [m for m in MOBS if m in BOSSES]),
              ("被動與中立生物", [m for m in MOBS if MOBS[m]["cat"] == "CREATURE" and m not in BOSSES]),
              ("敵對生物", [m for m in MOBS if MOBS[m]["cat"] == "MONSTER" and m not in BOSSES])]
    h = ["<h1>生物</h1>", section("page:mobs_intro")]
    for title, lst in groups:
        cards = "".join(f'<a class="card" href="#/mob/{m}">{mob_img(m) or ic("pysift:" + m + "_spawn_egg", 64, False)}'
                        f'<b>{esc(name("pysift:" + m))}</b><small>{esc(name("pysift:" + m, "en"))}</small></a>'
                        for m in sorted(lst, key=lambda x: name("pysift:" + x)))
        h.append(f"<h2>{title}</h2><div class=cards>{cards}</div>")
    page("mobs", "生物", "\n".join(h), "生物 mobs")


def codex_text(cat, key):
    parts = []
    for n in range(0, 8):
        t = tr(f"book.pysift.sift_codex.{cat}.{key}.p{n}.text")
        if t:
            ttl = tr(f"book.pysift.sift_codex.{cat}.{key}.p{n}.title")
            parts.append((f"<b>{esc(ttl)}</b><br>" if ttl else "") + codex_inline(t))
    return "<br><br>".join(parts)


def codex_inline(t):
    t = esc(t).replace("\\n", "\n")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\$\(br2?\)", "<br>", t)
    t = re.sub(r"\$\([^)]*\)", "", t)
    return t.replace("\n", "<br>")


def loot_table_html(items):
    rows = []
    for it in items:
        cnt = f'{it["lo"]:g}' if it["lo"] == it["hi"] else f'{it["lo"]:g}–{it["hi"]:g}'
        ch = []
        if it["chance"] is not None:
            ch.append(f'{it["chance"] * 100:g}%')
        if it["share"] is not None:
            ch.append(f'{it["share"] * 100:.0f}%／抽')
        if it["player"]:
            ch.append("需玩家擊殺")
        rows.append(f"<tr><td>{item_link(it['id'], size=24)}</td><td>{cnt}</td><td>{esc(' '.join(ch)) or '—'}</td></tr>")
    return ('<table class="wt"><thead><tr><th>物品</th><th>數量</th><th>機率／條件</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table>")


def build_biome_pages():
    cards = []
    for bid, b in BIOMES.items():
        shot = f"img/shots/biome_{bid}.jpg"
        img = f'<img src="{shot}" alt="" loading="lazy">' if (OUT / shot).exists() else ""
        rows = [("英文名", esc(name("pysift:" + bid, "en"))), ("ID", f"<code>pysift:{bid}</code>"),
                ("溫度", f'{b["temp"]:g}'), ("降雨", "有" if b["rain"] else "無"),
                ("氣候變體", "熱帶" if b["temp"] >= 1.4 else "寒帶" if b["temp"] <= 0.7 else "一般")]
        body = [infobox(name("pysift:" + bid), img, rows, name("pysift:" + bid, "en")), f"<h1>{esc(name('pysift:' + bid))}</h1>"]
        body.append(section(f"biome:{bid}"))
        codex = codex_text("sift", bid)
        if codex:
            body.append('<h2>隙浮手記</h2><blockquote class="codex">' + codex + "</blockquote>")
        blocks = sorted({x for pf in b["features"] for x in feature_blocks(pf)} - HIDDEN, key=name)
        if blocks:
            body.append("<h2>生成的方塊與植物</h2><div class=fam>" + "".join(item_link(x, size=24) for x in blocks) + "</div>")
        sts = [s for s, v in STRUCTURES.items() if bid in v["biomes"]]
        if sts:
            body.append("<h2>結構</h2><ul>" + "".join(f'<li><a href="#/structure/{s}">{esc(STRUCT_NAMES.get(s, s))}</a></li>'
                                                    for s in sts) + "</ul>")
        for cat, lst in b["spawns"].items():
            if not lst:
                continue
            rows_ = "".join(f'<tr><td><a href="#/mob/{norm(s["type"]).split(":")[1]}">{esc(name(s["type"]))}</a></td>'
                            f'<td>{s.get("weight")}</td><td>{s.get("count", {}).get("min_inclusive", "")}–'
                            f'{s.get("count", {}).get("max_inclusive", "")}</td></tr>'
                            for s in sorted(lst, key=lambda s: -s.get("weight", 0)))
            body.append(f'<h3>{"怪物" if cat == "monster" else "生物" if cat == "creature" else cat}</h3>'
                        '<table class="wt"><thead><tr><th>生物</th><th>權重</th><th>每群</th></tr></thead>'
                        f"<tbody>{rows_}</tbody></table>")
        page(f"biome/{bid}", name("pysift:" + bid), "\n".join(body), f"{name('pysift:' + bid)} {bid}", "biome")
        cards.append(f'<a class="card wide" href="#/biome/{bid}">{img}<b>{esc(name("pysift:" + bid))}</b>'
                     f'<small>溫度 {b["temp"]:g}</small></a>')
    page("biomes", "生態域", "<h1>隙浮維度與生態域</h1>" + section("page:dimension")
         + f'<div class="cards">{"".join(cards)}</div>', "生態域 biomes 維度")


def build_structure_pages():
    cards = []
    keys = list(STRUCTURES) + [k.split(":", 1)[1] for k in SECTIONS if k.startswith("structure:")
                               and k.split(":", 1)[1] not in STRUCTURES]
    for sid in keys:
        s = STRUCTURES.get(sid, {})
        title = STRUCT_NAMES.get(sid, sid)
        shot = f"img/shots/{'arena_' + sid[6:] if sid.startswith('arena_') else 'structure_' + sid}.jpg"
        img = f'<img src="{shot}" alt="" loading="lazy">' if (OUT / shot).exists() else ""
        rows = [("ID", f"<code>pysift:{sid}</code>" if s else None),
                ("生態域", "、".join(f'<a href="#/biome/{b}">{esc(name("pysift:" + b))}</a>' for b in s.get("biomes", []))),
                ("間距", f'{s["spacing"]} 區塊（最少隔 {s["separation"]}）' if s.get("spacing") else None)]
        body = [infobox(title, img, rows), f"<h1>{esc(title)}</h1>", section(f"structure:{sid}")]
        loot = CHEST_LOOT.get(sid)
        if loot:
            body.append("<h2>箱子戰利品</h2>" + loot_table_html(loot))
        if sid == "echo_den" and CHEST_LOOT.get("echo_den_vault"):
            body.append("<h2>寶庫戰利品</h2>" + loot_table_html(CHEST_LOOT["echo_den_vault"]))
        page(f"structure/{sid}", title, "\n".join(body), f"{title} {sid}", "structure")
        cards.append(f'<a class="card wide" href="#/structure/{sid}">{img}<b>{esc(title)}</b></a>')
    page("structures", "建築與地形", "<h1>建築與地形</h1>" + section("page:structures_intro")
         + f'<div class="cards">{"".join(cards)}</div>', "結構 建築 structures")


def build_text_pages():
    for k, (title, body) in SECTIONS.items():
        if k.startswith("page:") and not k.endswith(("_intro", "_short")) and k[5:] not in ("blocks_intro", "items_intro",
                                                                                          "dimension", "building_sets",
                                                                                          "home"):
            page(f"page/{k[5:]}", title, f"<h1>{esc(title)}</h1>" + md(body), title)


def build_recipe_index():
    by = defaultdict(list)
    for r in RECIPES:
        by[r["kind"]].append(r)
    h = ["<h1>合成索引</h1><p>模組全部配方，依工作站分類。點圖示可以開啟物品頁。</p>"]
    for k in ("crafting_shaped", "crafting_shapeless", "smithing_transform", "brewing", "resonance", "smelting",
              "blasting", "smoking", "campfire_cooking", "crafting_transmute"):
        if by.get(k):
            h.append(f"<h2>{KIND_NAME[k]}<small>{len(by[k])}</small></h2><div class=recipes>"
                     + "".join(recipe_html(r) for r in by[k]) + "</div>")
    h.append(f"<h2>切石機<small>{len(by['stonecutting'])}</small></h2><p>切石機的配方在各方塊頁的「合成」中。"
             "每種石材的原石、石磚、磨製等形式都能用切石機一次切出半磚、階梯、牆。</p>")
    page("recipes", "合成索引", "\n".join(h), "合成 配方 recipes")


def build_home():
    stats = (f"{len(ITEMS)} 個物品與方塊（其中 {len(IS_BLOCK)} 個方塊）、{len(MOBS)} 種生物、{len(BIOMES)} 個生態域、"
             f"{len(RECIPES)} 個配方")
    hero = ('<div class="home-hero"><img src="img/shots/biome_willow_grove.jpg" alt="柳絮林地的薄荷色黃昏">'
            '<div class="ht"><h1>隙浮</h1><p>Minecraft 26.3 的 Fabric 維度模組。從遠古城市那道走調的門出發，走進永遠停在'
            '薄荷色黃昏的世界：發光的靈液河、赤紅色的幽匿、會唱歌的生物，還有三位守護者。</p></div></div>')
    page("home", "首頁", hero + section("page:home").replace("{{STATS}}", esc(stats)), "首頁")


NAV = [("首頁", "home"), ("故事", "page/story"), ("新手攻略", "page/guide"), ("八音儀式與傳送門", "page/portal"),
       ("靈魂剝奪與靈液", "page/soul"), ("腐爛與封印", "page/rot"), ("靈魂動力", "page/soul_power"),
       ("附魔與釀造", "page/enchantments"), ("氣候變體", "page/climate"), ("指令與設定", "page/commands"),
       ("—", ""), ("生態域", "biomes"), ("生物", "mobs"), ("建築與地形", "structures"), ("方塊", "blocks"),
       ("建材家族", "building_sets"), ("物品", "items"), ("合成索引", "recipes")]


def write_site():
    OUT.mkdir(parents=True, exist_ok=True)
    search = [[r, p["t"], p["s"], p["k"]] for r, p in PAGES.items()]
    items = {i: [ICON.get(i, 0), name(i), 1 if is_page_item(i) else 0] for i in sorted(USED_IDS)}
    data = {"pages": {r: [p["t"], p["h"]] for r, p in PAGES.items()}, "search": search,
            "nav": NAV, "cols": COLS, "items": items, "recipes": RJS}
    (OUT / "data.js").write_text("window.WIKI=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
                                 encoding="utf-8")
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tpl = Path(__file__).resolve().parent / "site"
    for f in ("index.html", "wiki.css", "wiki.js"):
        (OUT / f).write_text((tpl / f).read_text(encoding="utf-8"), encoding="utf-8")
    # claude.ai page: the publisher adds the document skeleton, so the page is the head/body content with the CSS and
    # JS inlined; the data is fetched from data.json beside it
    idx = (tpl / "index.html").read_text(encoding="utf-8")
    head = idx.split("<head>", 1)[1].split("</head>", 1)[0]
    body = idx.split("<body>", 1)[1].split("</body>", 1)[0]
    head = re.sub(r'<meta charset[^>]*>\s*<meta name="viewport"[^>]*>\s*', "", head)
    css = (tpl / "wiki.css").read_text(encoding="utf-8")
    js = (tpl / "wiki.js").read_text(encoding="utf-8")
    nl = chr(10)
    head = head.replace('<link rel="stylesheet" href="wiki.css">', "<style>" + nl + css + nl + "</style>")
    body = body.replace('<script src="data.js"></script>', "").replace(
        '<script src="wiki.js"></script>', "<script>" + nl + js + nl + "</script>")
    (OUT / "claude_page.html").write_text(head.strip() + nl + body.strip() + nl, encoding="utf-8")
    print(f"wiki: {len(PAGES)} pages, data.js {(OUT / 'data.js').stat().st_size // 1024} KB -> {OUT}")


def check():
    bad = []
    routes = set(PAGES)
    for r, p in PAGES.items():
        for link in re.findall(r'href="#/([^"]+)"', p["h"]):
            if link not in routes:
                bad.append((r, link))
    missing_names = [i for i in ITEMS if name(i) == i[7:].replace("_", " ")]
    no_icon = [i for i in ITEMS if ICON.get(i, 0) == 0]
    print(f"check: {len(bad)} broken links, {len(missing_names)} items without a Chinese name, {len(no_icon)} without icon")
    for b in sorted(set(bad))[:40]:
        print("  broken", b)
    for i in missing_names[:40]:
        print("  no name", i)
    return not bad


def main():
    icon_index()
    build_item_pages()
    build_item_index()
    build_mob_pages()
    build_biome_pages()
    build_structure_pages()
    build_text_pages()
    build_recipe_index()
    build_home()
    ok = check()
    if "--check" not in sys.argv:
        write_site()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
