"""Resources for the pointed stones (block/PointedStones.java): one speleothem block per underground layer.
Usage: python -I tools/worldgen/build_pointed_stones.py <project>

Writes blockstates, block / item models, item definitions, loot tables, tags and names. Every block works like vanilla
pointed dripstone (5 thicknesses x up / down) and is drawn on the vanilla pointed-dripstone cross model. Textures are
drawn in the UP orientation only, textures/block/pointed/<id>_<part>.png; the DOWN models flip them with their UVs
(models/block/pointed/pointed_cross_vflip.json; not in templates/, which verify.py keeps for cube templates), so no flipped PNGs exist (CLAUDE.md).
"""
import json, sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"

# id -> (stone it grows on, English name, Chinese name)
STONES = {
    "pointed_dark_slate": ("dark_slate", "Pointed Dark Slate", "尖暗板岩"),
    "pointed_crimson_vein_stone": ("crimson_vein_stone", "Pointed Crimson Vein Stone", "尖赤紅脈石"),
    "pointed_void_stone": ("void_stone", "Pointed Void Stone", "尖虛空石"),
    "pointed_violet_strata": ("violet_strata", "Pointed Violet Strata", "尖紫地層"),
}
PARTS = ["tip_merge", "tip", "frustum", "middle", "base"]


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_tag(path, values):
    f = D / path
    tag = json.loads(f.read_text(encoding="utf-8-sig")) if f.exists() else {"replace": False, "values": []}
    tag["values"] += [v for v in values if v not in tag["values"]]
    wj(f, tag)


# the down template: vanilla's crossed planes with the texture flipped upside down
wj(A / "models/block/pointed/pointed_cross_vflip.json", {
    "ambientocclusion": True,
    "textures": {"particle": "#cross"},
    "elements": [
        {"from": [0.8, 0, 8], "to": [15.2, 16, 8],
         "rotation": {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True}, "shade_direction_override": "up",
         "faces": {"north": {"uv": [0, 16, 16, 0], "texture": "#cross"}, "south": {"uv": [0, 16, 16, 0], "texture": "#cross"}}},
        {"from": [8, 0, 0.8], "to": [8, 16, 15.2],
         "rotation": {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True}, "shade_direction_override": "up",
         "faces": {"west": {"uv": [0, 16, 16, 0], "texture": "#cross"}, "east": {"uv": [0, 16, 16, 0], "texture": "#cross"}}},
    ]})

names = {}
for bid, (stone, en, zh) in STONES.items():
    variants = {}
    for part in PARTS:
        tex = f"pysift:block/pointed/{bid}_{part}"
        wj(A / f"models/block/pointed/{bid}_up_{part}.json", {"parent": "minecraft:block/pointed_dripstone", "textures": {"cross": tex}})
        wj(A / f"models/block/pointed/{bid}_down_{part}.json", {"parent": "pysift:block/pointed/pointed_cross_vflip",
                                                               "textures": {"cross": tex}})
        for d in ("up", "down"):
            variants[f"thickness={part},vertical_direction={d}"] = {"model": f"pysift:block/pointed/{bid}_{d}_{part}"}
    wj(A / f"blockstates/{bid}.json", {"variants": variants})
    wj(A / f"models/item/{bid}.json", {"parent": "minecraft:item/generated",
                                       "textures": {"layer0": f"pysift:block/pointed/{bid}_frustum"}})
    wj(A / f"items/{bid}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{bid}"}})
    loot = {"type": "minecraft:block", "pools": [{"rolls": 1, "conditions": [{"condition": "minecraft:survives_explosion"}],
                                                  "entries": [{"type": "minecraft:item", "name": f"pysift:{bid}"}]}],
            "random_sequence": f"pysift:blocks/{bid}"}
    wj(D / f"pysift/loot_table/blocks/{bid}.json", loot)
    wj(D / f"pysift/loot_tables/blocks/{bid}.json", loot)
    names[f"block.pysift.{bid}"] = (en, zh)
    names[f"item.pysift.{bid}"] = (en, zh)          # 26.3 block items read the item key (verify.py item_missing_name)

ids = [f"pysift:{b}" for b in STONES]
add_tag("minecraft/tags/block/mineable/pickaxe.json", ids)
add_tag("minecraft/tags/block/speleothems.json", ids)          # vanilla's speleothem logic and features recognise them
# what the cave speleothem clusters may turn into their base stone (build_the_sift.py)
add_tag("pysift/tags/block/speleothem_replaceable.json", ["#pysift:red_sculk_replaceable", "pysift:varied_dark_slate",
                                                          "pysift:crimson_vein_stone", "pysift:violet_strata",
                                                          "pysift:dark_slate"])

for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    raw = f.read_bytes().decode("utf-8-sig")
    data = json.loads(raw)
    for k, v in names.items():
        data[k] = v[i]
    out = json.dumps(data, ensure_ascii=False, indent=2)
    f.write_bytes((out + "\n").encode("utf-8"))   # the lang files use LF
print("pointed stones:", ", ".join(STONES))
