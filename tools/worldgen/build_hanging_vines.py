"""Resources for the hanging vines (block/HangingVines.java): vines that hang from cave ceilings, after the user's three
wall vines (green / orange Sift vine, carapace vine).
Usage: python -I tools/worldgen/build_hanging_vines.py <project>

Each vine is drawn on vanilla's cross model; bottom=false is the strand, bottom=true the tip (its own texture).
Textures: textures/block/vegetation/hanging_vines/<id>.png and <id>_tip.png.
"""
import json, sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"

VINES = {   # id -> (English, Chinese)
    "hanging_green_sift_vine": ("Hanging Green Sift Vine", "垂吊綠隙浮藤"),
    "hanging_orange_sift_vine": ("Hanging Orange Sift Vine", "垂吊橙隙浮藤"),
    "hanging_carapace_vine": ("Hanging Carapace Vine", "垂吊甲殼藤"),
}


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_tag(path, values):
    f = D / path
    tag = json.loads(f.read_text(encoding="utf-8-sig")) if f.exists() else {"replace": False, "values": []}
    tag["values"] += [v for v in values if v not in tag["values"]]
    wj(f, tag)


names = {}
for vid, (en, zh) in VINES.items():
    tex = f"pysift:block/vegetation/hanging_vines/{vid}"
    wj(A / f"models/block/vegetation/hanging_vines/{vid}.json", {"parent": "minecraft:block/cross", "textures": {"cross": tex}})
    wj(A / f"models/block/vegetation/hanging_vines/{vid}_tip.json", {"parent": "minecraft:block/cross", "textures": {"cross": tex + "_tip"}})
    wj(A / f"blockstates/{vid}.json", {"variants": {
        "bottom=false": {"model": f"pysift:block/vegetation/hanging_vines/{vid}"},
        "bottom=true": {"model": f"pysift:block/vegetation/hanging_vines/{vid}_tip"}}})
    wj(A / f"models/item/{vid}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": tex + "_tip"}})
    wj(A / f"items/{vid}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{vid}"}})
    loot = {"type": "minecraft:block", "pools": [{"condition": {"type": "minecraft:survives_explosion"},
                                                  "entries": [{"type": "minecraft:item", "name": f"pysift:{vid}"}], "rolls": 1}],
            "random_sequence": f"pysift:blocks/{vid}"}
    wj(D / f"pysift/loot_table/blocks/{vid}.json", loot)
    wj(D / f"pysift/loot_tables/blocks/{vid}.json", loot)
    names[f"block.pysift.{vid}"] = (en, zh)
    names[f"item.pysift.{vid}"] = (en, zh)

ids = [f"pysift:{v}" for v in VINES]
add_tag("minecraft/tags/block/climbable.json", ids)
add_tag("minecraft/tags/block/washed_away_by_fluids.json", ids)

for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_bytes().decode("utf-8-sig"))
    for k, v in names.items():
        data[k] = v[i]
    f.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))   # the lang files use LF
print("hanging vines:", ", ".join(VINES))
