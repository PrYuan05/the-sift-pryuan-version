"""Second merge into capped_crimson_strata[facing, tone]:
  rose_capped_crimson_strata -> tone=mottled   (top moved byte-for-byte to capped_crimson_strata_mottled_top.png)
  teal_capped_dark_slate     -> tone=deep_teal (side repainted: its red rock now uses the coral palette of the
                                                capped_crimson_strata side crimson_strata_h; bottoms are the same as
                                                the other tones)
  teal_capped_dark_slate_2   -> deleted (user), with its only texture dark_slate_c.
Usage: python -I tools/texture_pipeline/history/merge_capped_crimson_2.py <project>
Old IDs are removed directly. Every removed or rewritten file is backed up to .texture_backups/<stamp>_merge_capped_crimson_2/.
ModBlocks.java is edited by hand (.tones("teal", "rose", "mottled", "deep_teal"), three facing(...) lines removed).
Run afterwards: verify.py."""
import colorsys, datetime, json, re, shutil, sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
RES = P / "src/main/resources"; A = RES / "assets/pysift"; D = RES / "data"
TP = P / "tools/texture_pipeline"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_merge_capped_crimson_2")
NEW = "capped_crimson_strata"
MOTTLED, DEEP, GONE = "rose_capped_crimson_strata", "teal_capped_dark_slate", "teal_capped_dark_slate_2"
OLD = [MOTTLED, DEEP, GONE]
BOTTOMS = ["pysift:block/crimson_vein_stone/crimson_vein_stone_crimson_spread4", "pysift:block/ember_stone/ember_stone_heat0_a"]


def lj(p): return json.loads(p.read_text(encoding="utf-8-sig"))


def wj(p, obj):
    backup(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def backup(p):
    dst = BK / p.relative_to(P)
    if p.exists() and not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)


def remove(p):
    if p.is_dir():
        for f in p.rglob("*"):
            if f.is_file():
                backup(f)
        shutil.rmtree(p)
    elif p.exists():
        backup(p)
        p.unlink()


def entries(v): return v if isinstance(v, list) else [v]


def is_teal(c):
    h, s, _ = colorsys.rgb_to_hsv(*(x / 255 for x in c[:3]))
    return 0.40 <= h <= 0.56 and s > 0.25


def lum(c): return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def coral_side():
    """dark_slate_b with every non-teal (red rock) pixel mapped by brightness onto the rock palette of crimson_strata_h."""
    src = Image.open(A / "textures/block/dark_slate/dark_slate_b.png").convert("RGBA")
    ref = Image.open(A / "textures/block/crimson_strata/crimson_strata_h.png").convert("RGBA")
    pal = sorted({p[:3] for p in ref.get_flattened_data() if p[3] and not is_teal(p)}, key=lum)
    rock = [p for p in src.get_flattened_data() if p[3] and not is_teal(p)]
    lo, hi = min(map(lum, rock)), max(map(lum, rock))
    rlo, rhi = lum(pal[0]), lum(pal[-1])
    px = src.load()
    for y in range(src.height):
        for x in range(src.width):
            c = px[x, y]
            if c[3] and not is_teal(c):
                target = rlo + ((lum(c) - lo) / (hi - lo) if hi > lo else 0.5) * (rhi - rlo)
                px[x, y] = min(pal, key=lambda r: abs(lum(r) - target)) + (c[3],)
    return src


assert not any(t in json.dumps(lj(A / f"blockstates/{NEW}.json")) for t in ("tone=mottled", "tone=deep_teal")), "already merged"
TEX = A / "textures/block" / NEW
bs = lj(A / f"blockstates/{NEW}.json")

# ---- mottled: the rose_capped_crimson_strata models with the top moved into the capped_crimson_strata folder ----
backup(A / f"textures/block/{MOTTLED}/{MOTTLED}_top.png")
shutil.move(A / f"textures/block/{MOTTLED}/{MOTTLED}_top.png", TEX / f"{NEW}_mottled_top.png")
for i, m in enumerate(sorted((A / f"models/block/{MOTTLED}").glob("*.json")), 1):
    j = lj(m)
    j["textures"] = {k: (f"pysift:block/{NEW}/{NEW}_mottled_top" if v.endswith(f"/{MOTTLED}_top") else v) for k, v in j["textures"].items()}
    wj(A / f"models/block/{NEW}/{NEW}_mottled_{i}.json", j)
for key, v in lj(A / f"blockstates/{MOTTLED}.json")["variants"].items():
    bs["variants"][f"{key},tone=mottled"] = [dict(e, model=re.sub(rf"block/{MOTTLED}/{MOTTLED}_(\d)", rf"block/{NEW}/{NEW}_mottled_\1", e["model"]))
                                             for e in entries(v)]

# ---- deep_teal: teal top, coral side (repainted), the same two bottoms as the other tones ----
coral_side().save(TEX / f"{NEW}_deep_teal_side.png")
old_model = lj(A / f"models/block/{DEEP}/{DEEP}_1.json")
for i, bottom in enumerate(BOTTOMS, 1):
    wj(A / f"models/block/{NEW}/{NEW}_deep_teal_{i}.json", {
        "parent": old_model["parent"],
        "textures": {"top": old_model["textures"]["top"], "bottom": bottom, "side": f"pysift:block/{NEW}/{NEW}_deep_teal_side",
                     "particle": f"pysift:block/{NEW}/{NEW}_deep_teal_side"}})
for key, v in lj(A / f"blockstates/{DEEP}.json")["variants"].items():
    rot = {k: e for k, e in entries(v)[0].items() if k in ("x", "y")}
    bs["variants"][f"{key},tone=deep_teal"] = [dict(model=f"pysift:block/{NEW}/{NEW}_deep_teal_{i}", weight=1, **rot) for i in (1, 2)]
wj(A / f"blockstates/{NEW}.json", bs)

# item: one case per tone
item = lj(A / f"items/{NEW}.json")
for tone in ("mottled", "deep_teal"):
    item["model"]["cases"].append({"when": tone, "model": {"type": "minecraft:model", "model": f"pysift:block/{NEW}/{NEW}_{tone}_1"}})
wj(A / f"items/{NEW}.json", item)

# ---- remove the old blocks ----
for oid in OLD:
    for p in (A / f"blockstates/{oid}.json", A / f"items/{oid}.json", A / f"models/item/{oid}.json", A / f"models/block/{oid}",
              A / f"textures/block/{oid}", D / f"pysift/loot_table/blocks/{oid}.json", D / f"pysift/loot_tables/blocks/{oid}.json"):
        remove(p)
for png in ("dark_slate_b", "dark_slate_c"):   # only these two blocks used them (dark_slate_b is repainted into deep_teal_side)
    remove(A / f"textures/block/dark_slate/{png}.png")
ids = {f"pysift:{oid}" for oid in OLD}
for tag in (t for t in D.rglob("*.json") if "tags" in t.parts):
    j = lj(tag)
    if any(v in ids for v in j.get("values", [])):
        j["values"] = [v for v in j["values"] if v not in ids]
        wj(tag, j)
for lang in ("zh_tw", "en_us"):
    p = A / f"lang/{lang}.json"
    j = lj(p)
    wj(p, {k: v for k, v in j.items() if not any(k == f"{t}.pysift.{oid}" for t in ("block", "item") for oid in OLD)})

# ---- texture pipeline records ----
mp = TP / "recolor_manifest.json"
man = lj(mp)
gone = {"textures/block/dark_slate/dark_slate_b.png", "textures/block/dark_slate/dark_slate_c.png"}
man["entries"] = [dict(e, file=f"textures/block/{NEW}/{NEW}_mottled_top.png", pool=f"{NEW}:mottled_top")
                  if e["file"] == f"textures/block/{MOTTLED}/{MOTTLED}_top.png" else e
                  for e in man["entries"] if e["file"] not in gone]
wj(mp, man)
fr = TP / "face_rules.json"
rules = lj(fr)
for section in rules.values():
    if isinstance(section, dict):
        for oid in OLD:
            section.pop(oid, None)
wj(fr, rules)
sc = P / "tools/worldgen/surface_candidates.py"
backup(sc)
sc.write_text(re.sub(rf'"{MOTTLED}", ', "", sc.read_text(encoding="utf-8")), encoding="utf-8")
print("merged into", NEW, "; backups in", BK.relative_to(P))
