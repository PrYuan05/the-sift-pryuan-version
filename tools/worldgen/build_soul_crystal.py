"""Resources for pysift:soul_crystal_block (SoulCrystal.java).
Usage: python -I tools/worldgen/build_soul_crystal.py <project>
The texture is the face of the light-blue block on the Echo Golem's head (textures/entity/echo_golem.png, uv 111,48,
16x16), so the block the golem hands over looks exactly like what it carried. Written only if missing."""
import json, sys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1])
A, D = P / "src/main/resources/assets/pysift", P / "src/main/resources/data"
NAME = "soul_crystal_block"


def lj(p): return json.loads(p.read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


tex = A / f"textures/block/{NAME}.png"
if not tex.exists():
    Image.open(A / "textures/entity/echo_golem.png").convert("RGBA").crop((111, 48, 127, 64)).save(tex)
wj(A / f"models/block/{NAME}.json", {"parent": "minecraft:block/cube_all", "textures": {"all": f"pysift:block/{NAME}"}})
wj(A / f"blockstates/{NAME}.json", {"variants": {"": {"model": f"pysift:block/{NAME}"}}})
wj(A / f"models/item/{NAME}.json", {"parent": f"pysift:block/{NAME}"})
wj(A / f"items/{NAME}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{NAME}"}})
loot = {"type": "minecraft:block", "pools": [{"condition": {"type": "minecraft:survives_explosion"},
        "entries": [{"type": "minecraft:item", "name": f"pysift:{NAME}"}], "rolls": 1}], "random_sequence": f"pysift:blocks/{NAME}"}
for d in ("loot_table", "loot_tables"):
    wj(D / f"pysift/{d}/blocks/{NAME}.json", loot)
tag = D / "minecraft/tags/block/mineable/pickaxe.json"
t = lj(tag)
if f"pysift:{NAME}" not in t["values"]:
    t["values"].append(f"pysift:{NAME}")
    wj(tag, t)
for lang, name in (("en_us", "Soul Crystal Block"), ("zh_tw", "靈魂晶塊")):
    lf = A / f"lang/{lang}.json"
    d = lj(lf)
    d[f"block.pysift.{NAME}"] = name
    d[f"item.pysift.{NAME}"] = name
    wj(lf, d)
print("soul crystal block resources written")
