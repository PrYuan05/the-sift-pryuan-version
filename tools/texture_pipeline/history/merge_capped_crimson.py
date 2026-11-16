"""Merge teal_capped_crimson_strata + rose_capped_crimson_strata_2 into capped_crimson_strata[facing, tone=teal|rose].
Usage: python -I tools/texture_pipeline/history/merge_capped_crimson.py <project>
Old IDs are removed directly. Textures are moved (byte-for-byte) into textures/block/capped_crimson_strata/;
recolor_manifest.json follows the move. The merged block is facing+tone, so refit_faces.py skips it (like edged_stone).
Run afterwards: changes_report.py, build_vegetation.py (blocks_motion_no_leaves), verify.py."""
import json, sys, shutil
from pathlib import Path

P = Path(sys.argv[1])
RES = P / "src/main/resources"; A = RES / "assets/pysift"; D = RES / "data"
TP = P / "tools/texture_pipeline"
NEW = "capped_crimson_strata"
OLD = {"teal": "teal_capped_crimson_strata", "rose": "rose_capped_crimson_strata_2"}   # tone -> old id (order = tone order)


def lj(p): return json.loads(p.read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def entries(v): return v if isinstance(v, list) else [v]


assert not (A / "blockstates" / f"{NEW}.json").exists(), "already merged"
variants, item_cases = {}, []
moved = {}
for tone, oid in OLD.items():
    old_tex = f"pysift:block/{oid}/{oid}_top"
    new_tex = f"pysift:block/{NEW}/{NEW}_{tone}_top"
    src_png = A / f"textures/block/{oid}/{oid}_top.png"
    dst_png = A / f"textures/block/{NEW}/{NEW}_{tone}_top.png"
    dst_png.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(src_png, dst_png)
    src_png.parent.rmdir()
    moved[f"textures/block/{oid}/{oid}_top.png"] = (f"textures/block/{NEW}/{NEW}_{tone}_top.png", f"{NEW}:{tone}_top")
    # models: same parents / sides / bottoms, new top path
    old_bs = lj(A / "blockstates" / f"{oid}.json")["variants"]
    rename = {}
    for i, e in enumerate(entries(old_bs["facing=up"]), 1):
        m = lj(A / "models/block" / oid / f"{oid}_{i}.json")
        m["textures"] = {k: (new_tex if v == old_tex else v) for k, v in m["textures"].items()}
        wj(A / "models/block" / NEW / f"{NEW}_{tone}_{i}.json", m)
        rename[e["model"]] = f"pysift:block/{NEW}/{NEW}_{tone}_{i}"
    for key, v in old_bs.items():                     # key = "facing=<dir>"
        variants[f"{key},tone={tone}"] = [{**e, "model": rename[e["model"]]} for e in entries(v)]
    item_cases.append({"when": tone, "model": {"type": "minecraft:model", "model": rename[entries(old_bs["facing=up"])[0]["model"]]}})
    # remove old files
    shutil.rmtree(A / "models/block" / oid)
    for f in (A / "blockstates" / f"{oid}.json", A / "items" / f"{oid}.json", A / "models/item" / f"{oid}.json",
              D / "pysift/loot_table/blocks" / f"{oid}.json", D / "pysift/loot_tables/blocks" / f"{oid}.json"):
        f.unlink()

wj(A / "blockstates" / f"{NEW}.json", {"variants": variants})
first = item_cases[0]["model"]["model"]
wj(A / "models/item" / f"{NEW}.json", {"parent": first})
wj(A / "items" / f"{NEW}.json", {"model": {"type": "minecraft:select", "block_state_property": "tone",
                                          "property": "minecraft:block_state", "cases": item_cases,
                                          "fallback": {"type": "minecraft:model", "model": f"pysift:item/{NEW}"}}})
loot = {"type": "minecraft:block", "pools": [{"condition": {"type": "minecraft:survives_explosion"},
        "entries": [{"type": "minecraft:item", "name": f"pysift:{NEW}",
                     "modifier": [{"type": "minecraft:copy_state", "block": f"pysift:{NEW}", "properties": ["tone"]}]}],
        "rolls": 1}], "random_sequence": f"pysift:blocks/{NEW}"}
for d in ("loot_table", "loot_tables"):
    wj(D / f"pysift/{d}/blocks/{NEW}.json", loot)

# tags: swap the old ids for the new one
for tf in (D / "minecraft/tags/block").rglob("*.json"):
    t = lj(tf)
    vals = t.get("values", [])
    if any(v in (f"pysift:{o}" for o in OLD.values()) for v in vals):
        out = []
        for v in vals:
            nv = f"pysift:{NEW}" if v in (f"pysift:{o}" for o in OLD.values()) else v
            if nv not in out:
                out.append(nv)
        t["values"] = out
        wj(tf, t)

# lang
NAMES = {"en_us": "Capped Crimson Strata", "zh_tw": "覆蓋赤紅地層岩"}
for lang, name in NAMES.items():
    lf = A / f"lang/{lang}.json"
    lang_d, out = lj(lf), {}
    for k, v in lang_d.items():
        if any(k.endswith(f".pysift.{o}") for o in OLD.values()):
            if k.startswith("block."):
                out[f"block.pysift.{NEW}"] = name
                out[f"item.pysift.{NEW}"] = name
            continue
        out[k] = v
    wj(lf, out)

# texture pipeline bookkeeping
rules = lj(TP / "face_rules.json")
for oid in OLD.values():
    rules["generated_faces"].pop(oid, None)
rules["skip_blocks"].append(NEW)
wj(TP / "face_rules.json", rules)
man = lj(TP / "recolor_manifest.json")
for e in man["entries"]:
    if e["file"] in moved:
        e["file"], e["pool"] = moved[e["file"]]
wj(TP / "recolor_manifest.json", man)
print("merged", list(OLD.values()), "->", NEW, f"({len(variants)} variants)")
