"""Echo cradle (回音晶簇): the crystal in the Echo Den's grotto that condenses Singer song into echo golems.

Writes the 4 resonance-stage textures (only when missing: textures are frozen, never overwritten), blockstate, block and
item models, item definition, loot tables and the pickaxe tag entry.
The texture takes the charoite cluster's shape and shading and recolours it to echo teal; each stage is brighter and
has more glowing tips.
Usage: python -I tools/worldgen/build_echo_cradle.py <project>"""
import json
import sys
from pathlib import Path

from PIL import Image

P = Path(sys.argv[1])
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data/pysift"
NAME = "echo_cradle"
STAGES = 4
# dark -> bright: deep sculk teal, echo teal, soul cyan, white-cyan glow
RAMP = [(6, 34, 44), (10, 70, 84), (18, 118, 128), (40, 178, 182), (98, 232, 222), (196, 255, 246)]


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ramp(t):
    t = max(0.0, min(1.0, t)) * (len(RAMP) - 1)
    i = min(int(t), len(RAMP) - 2)
    f = t - i
    return tuple(round(a + (b - a) * f) for a, b in zip(RAMP[i], RAMP[i + 1]))


src = Image.open(A / "textures/block/progression/charoite_cluster.png").convert("RGBA")
lum = {}
for y in range(16):
    for x in range(16):
        r, g, b, a = src.getpixel((x, y))
        if a:
            lum[(x, y)] = (0.3 * r + 0.59 * g + 0.11 * b) / 255
lo, hi = min(lum.values()), max(lum.values())
for stage in range(STAGES):
    out = A / f"textures/block/{NAME}/{NAME}_{stage}.png"
    if out.exists():
        print("kept", out.name)
        continue
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    lift = 0.12 * stage                                  # brighter overall with each stage
    for (x, y), l in lum.items():
        t = (l - lo) / (hi - lo or 1)
        t = t * 0.82 + lift
        if t > 0.9 - 0.08 * stage:                       # more of the bright tips glow
            t = 1.0
        img.putpixel((x, y), ramp(t) + (255,))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print("wrote", out.relative_to(P))

for stage in range(STAGES):
    wj(A / f"models/block/{NAME}/{NAME}_{stage}.json",
       {"parent": "minecraft:block/cross", "render_type": "cutout", "textures": {"cross": f"pysift:block/{NAME}/{NAME}_{stage}"}})
wj(A / f"blockstates/{NAME}.json", {"variants": {f"resonance={s}": {"model": f"pysift:block/{NAME}/{NAME}_{s}"} for s in range(STAGES)}})
wj(A / f"models/item/{NAME}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"pysift:block/{NAME}/{NAME}_2"}})
wj(A / f"items/{NAME}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{NAME}"}})
loot = {"type": "minecraft:block", "random_sequence": f"pysift:blocks/{NAME}", "pools": [
    {"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"pysift:{NAME}"}], "conditions": [{"condition": "minecraft:survives_explosion"}]}]}
for folder in ("loot_table", "loot_tables"):
    wj(D / f"{folder}/blocks/{NAME}.json", loot)
tag = P / "src/main/resources/data/minecraft/tags/block/mineable/pickaxe.json"
data = json.loads(tag.read_text(encoding="utf-8"))
if f"pysift:{NAME}" not in data["values"]:
    data["values"].append(f"pysift:{NAME}")
    wj(tag, data)
print("done")
