"""Resources for the soul power blocks (src/main/java/pryuan05/pysift/soulpower/, first stage).
Usage: python -I tools/progression/build_soul_power.py <project>

Writes blockstates, block / item models, item definitions, loot tables, recipes (crafting + pysift:soul_grinding),
mineable / blocks_motion_no_leaves tags, lang and the two GUI backgrounds (cut from vanilla's furnace GUI).
Textures are vanilla placeholders until the art lands (art_requests/soul_power_todo.md); POWERED=true uses
animated vanilla textures so a running network is visible."""
import io, json, sys, zipfile
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1])
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
CLIENT = zipfile.ZipFile(Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client-only.jar")


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# name: (English, 繁中, solid full cube)
BLOCKS = {
    "spirit_engine": ("Spirit Engine", "靈液引擎", True),
    "soul_shaft": ("Soul Shaft", "靈魂傳動軸", False),
    "soul_wave_emitter": ("Soul Wave Emitter", "靈魂振波發送器", True),
    "soul_wave_receiver": ("Soul Wave Receiver", "靈魂振波接收器", True),
    "soul_grinder": ("Soul Grinder", "靈魂研磨機", True),
}
SIDE = "minecraft:block/polished_deepslate"
# orientable machines: textures for (unpowered, powered)
MACHINES = {
    "spirit_engine": {"top": SIDE, "side": "minecraft:block/deepslate_tiles",
                      "front": ("minecraft:block/blast_furnace_front", "minecraft:block/blast_furnace_front_on")},
    "soul_grinder": {"top": ("minecraft:block/smithing_table_top", "minecraft:block/sculk"), "side": "minecraft:block/deepslate_tiles",
                     "front": "minecraft:block/smithing_table_front"},
    "soul_wave_emitter": {"top": SIDE, "side": SIDE,
                          "front": ("minecraft:block/sculk_catalyst_top", "minecraft:block/sculk_catalyst_top_bloom")},
    "soul_wave_receiver": {"top": SIDE, "side": SIDE,
                           "front": ("minecraft:block/sculk_shrieker_inner_top", "minecraft:block/sculk_shrieker_can_summon_inner_top")},
}
# FACING -> rotation of minecraft:block/orientable (front faces north)
ROT = {"north": {}, "east": {"y": 90}, "south": {"y": 180}, "west": {"y": 270}, "up": {"x": 270}, "down": {"x": 90}}

for name, tex in MACHINES.items():
    for powered in (False, True):
        t = {k: (v[powered] if isinstance(v, tuple) else v) for k, v in tex.items()}
        suffix = "_on" if powered else ""
        wj(A / f"models/block/{name}{suffix}.json", {"parent": "minecraft:block/orientable",
                                                     "textures": {"top": t["top"], "side": t["side"], "front": t["front"],
                                                                  "particle": t["side"]}})
    variants = {}
    for facing, rot in ROT.items():
        for powered in ("false", "true"):
            variants[f"facing={facing},powered={powered}"] = {"model": f"pysift:block/{name}{'_on' if powered == 'true' else ''}", **rot}
    wj(A / f"blockstates/{name}.json", {"variants": variants})

# shaft: a 6x6 rod along Y, rotated for the other axes
for powered in (False, True):
    side = "minecraft:block/sculk" if powered else "minecraft:block/polished_basalt_side"
    end = "minecraft:block/polished_basalt_top"
    faces = {d: {"uv": [5, 0, 11, 16], "texture": "#side"} for d in ("north", "south", "east", "west")}
    faces["up"] = {"uv": [5, 5, 11, 11], "texture": "#end", "cullface": "up"}
    faces["down"] = {"uv": [5, 5, 11, 11], "texture": "#end", "cullface": "down"}
    wj(A / f"models/block/soul_shaft{'_on' if powered else ''}.json", {
        "parent": "minecraft:block/block",
        "textures": {"side": side, "end": end, "particle": "minecraft:block/polished_basalt_side"},
        "elements": [{"from": [5, 0, 5], "to": [11, 16, 11], "faces": faces}]})
shaft = {}
for axis, rot in (("y", {}), ("x", {"x": 90, "y": 90}), ("z", {"x": 90})):
    for powered in ("false", "true"):
        shaft[f"axis={axis},powered={powered}"] = {"model": f"pysift:block/soul_shaft/soul_shaft{'_on' if powered == 'true' else ''}", **rot}
wj(A / "blockstates/soul_shaft.json", {"variants": shaft})

for name in BLOCKS:
    wj(A / f"models/item/{name}.json", {"parent": f"pysift:block/{name}"})
    wj(A / f"items/{name}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{name}"}})
    loot = {"type": "minecraft:block", "pools": [{"rolls": 1, "condition": {"type": "minecraft:survives_explosion"},
                                                   "entries": [{"type": "minecraft:item", "name": f"pysift:{name}"}]}],
            "random_sequence": f"pysift:blocks/{name}"}
    for folder in ("loot_table", "loot_tables"):
        wj(D / f"pysift/{folder}/blocks/{name}.json", loot)


def add_tag(path, values):
    f = D / path
    cur = json.loads(f.read_text(encoding="utf-8-sig")) if f.exists() else {"replace": False, "values": []}
    cur["values"] += [v for v in values if v not in cur["values"]]
    wj(f, cur)


add_tag("minecraft/tags/block/mineable/pickaxe.json", [f"pysift:{n}" for n in BLOCKS])
add_tag("minecraft/tags/block/blocks_motion_no_leaves.json", [f"pysift:{n}" for n, v in BLOCKS.items() if v[2]])

# ------------------------------------------------------------------ recipes
SHAPED = {
    "spirit_engine": (["PIP", "IBI", "PEP"], {"P": "minecraft:polished_deepslate", "I": "pysift:siftite_ingot",
                                              "B": "minecraft:blast_furnace", "E": "pysift:soul_essence"}, 1),
    "soul_shaft": (["I", "S", "I"], {"I": "pysift:siftite_ingot", "S": "minecraft:polished_basalt"}, 4),
    "soul_wave_emitter": (["PAP", "ESE", "PIP"], {"P": "minecraft:polished_deepslate", "A": "minecraft:amethyst_shard",
                                                  "E": "pysift:soul_essence", "S": "minecraft:sculk_sensor",
                                                  "I": "pysift:siftite_ingot"}, 1),
    "soul_wave_receiver": (["PIP", "ESE", "PAP"], {"P": "minecraft:polished_deepslate", "A": "minecraft:amethyst_shard",
                                                   "E": "pysift:soul_essence", "S": "minecraft:sculk_sensor",
                                                   "I": "pysift:siftite_ingot"}, 1),
    "soul_grinder": (["PSP", "IGI", "PEP"], {"P": "minecraft:polished_deepslate", "S": "minecraft:stonecutter",
                                             "I": "pysift:siftite_ingot", "G": "minecraft:grindstone",
                                             "E": "pysift:soul_essence"}, 1),
}
for name, (pattern, key, count) in SHAPED.items():
    result = {"id": f"pysift:{name}"}
    if count > 1:
        result["count"] = count
    wj(D / f"pysift/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": "redstone",
                                          "key": key, "pattern": pattern, "result": result})
# soul grinding: ores double, stone breaks down (like a mill)
GRINDING = {
    "siftite_ore": ("pysift:siftite_ore", "pysift:raw_siftite", 2),
    "iron_ores": ("#minecraft:iron_ores", "minecraft:raw_iron", 2),
    "gold_ores": ("#minecraft:gold_ores", "minecraft:raw_gold", 2),
    "copper_ores": ("#minecraft:copper_ores", "minecraft:raw_copper", 6),
    "cobblestone": ("minecraft:cobblestone", "minecraft:gravel", 1),
    "gravel": ("minecraft:gravel", "minecraft:sand", 1),
    "bone": ("minecraft:bone", "minecraft:bone_meal", 6),
    "soul_soil": ("minecraft:soul_soil", "minecraft:soul_sand", 1),
}
for name, (ingredient, item, count) in GRINDING.items():
    wj(D / f"pysift/recipe/soul_grinding/{name}.json",
       {"type": "pysift:soul_grinding", "ingredient": ingredient, "result": {"id": item, "count": count}})

# ------------------------------------------------------------------ GUI backgrounds from vanilla's furnace
furnace = Image.open(io.BytesIO(CLIENT.read("assets/minecraft/textures/gui/container/furnace.png"))).convert("RGBA")
BG = furnace.getpixel((60, 70))           # the panel grey
slot = furnace.crop((55, 16, 73, 34))     # an 18x18 slot


def clear(im, box):
    im.paste(Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), BG), box[:2])


engine = furnace.copy()                    # keep the fuel slot and the flame; no input, arrow or result
clear(engine, (55, 16, 73, 34))
clear(engine, (78, 32, 140, 60))
grinder = furnace.copy()                   # input in the middle, arrow, result, essence slot under it
clear(grinder, (55, 16, 73, 71))
grinder.paste(slot, (55, 34))
grinder.paste(slot, (115, 59))
for name, im in (("spirit_engine", engine), ("soul_grinder", grinder)):
    out = A / f"textures/gui/container/{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)

# ------------------------------------------------------------------ lang (merge, keep line endings)
LANG = {f"block.pysift.{n}": (v[0], v[1]) for n, v in BLOCKS.items()}
LANG.update({
    "gui.pysift.soul_power.speed": ("Speed: %s RPM", "轉速：%s RPM"),
    "gui.pysift.soul_power.capacity": ("Capacity: %s SP", "靈壓容量：%s SP"),
    "gui.pysift.soul_power.stress": ("Load: %s SP", "需求：%s SP"),
    "gui.pysift.soul_power.overloaded": ("Overloaded!", "過載！"),
    "gui.pysift.soul_power.running": ("Running at %s RPM", "運轉中：%s RPM"),
    "gui.pysift.soul_power.idle": ("No soul power", "沒有靈魂動力"),
    "message.pysift.soul_wave.frequency": ("Tuned to %s", "頻率：%s"),
    "message.pysift.soul_wave.empty": ("Tune it with a resonant music disc", "放入一張共鳴唱片來設定頻率"),
})
for code, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{code}.json"
    raw = f.read_bytes().decode("utf-8-sig")
    data = json.loads(raw)
    for k, v in LANG.items():
        data[k] = v[i]
    out = json.dumps(data, ensure_ascii=False, indent=2)
    if "\r\n" in raw:
        out = out.replace("\n", "\r\n")
    f.write_bytes((out + ("\r\n" if raw.endswith("\n") else "")).encode("utf-8"))
print(f"{len(BLOCKS)} soul power blocks, {len(GRINDING)} grinding recipes")
