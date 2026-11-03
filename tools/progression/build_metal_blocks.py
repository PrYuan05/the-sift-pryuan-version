"""Metal storage blocks and the patina metal (ModProgression: SIFTITE_BLOCK, RAW_SIFTITE_BLOCK, PATINA_BLOCK,
RAW_PATINA_BLOCK, RAW_PATINA, PATINA_INGOT).
Usage: python -I tools/progression/build_metal_blocks.py <project>

Textures reuse the vanilla structure of the matching raw ore / ingot / storage block (pixel layout and shading) and
replace its colours by rank with our ramps (texture skill, method C):
  raw_siftite_block <- block/raw_iron_block     siftite_block <- block/gold_block (bevelled metal, diagonal sheen)
  raw_patina        <- item/raw_copper          patina_ingot  <- item/copper_ingot
  raw_patina_block  <- block/raw_copper_block   patina_block  <- block/copper_block
Raw copper already carries verdigris: its copper pixels take the ochre cement ramp of patina ore's breccia, its green
pixels the verdigris ramp. Patina ore itself (user, 2026-10-31): oxidation 0 is the hydrothermal breccia that used to
be argent ore, oxidation 1 the same breccia with its cement turned to verdigris from the clast contacts outward.
New PNGs go through tools/art_guard.py, so hand-drawn replacements are never overwritten."""
import colorsys, io, json, random, sys, zipfile
from pathlib import Path

from PIL import Image

P = Path(sys.argv[1])
sys.path.insert(0, str(P / "tools"))
import art_guard

A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
T = A / "textures"
JAR = next((P / ".gradle/loom-cache/minecraftMaven/net/minecraft").glob("minecraft-clientOnly-*/26.3/*.jar"))
VANILLA = zipfile.ZipFile(JAR)


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def vanilla(name):
    return Image.open(io.BytesIO(VANILLA.read(f"assets/minecraft/textures/{name}.png"))).convert("RGBA")


def hexes(*codes):
    return [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in codes]


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


# ramps dark -> light; shadows lean cold, highlights warm and less saturated, no pure black / white
SIFTITE = hexes("#2e1032", "#6e1a4e", "#b02c66", "#dc3e85", "#f0629c", "#fa86ae", "#ffb0bd", "#ffd6d6")   # siftite_ingot, hue-shifted
RAW_SIFTITE = hexes("#24263a", "#464a5e", "#9e245c", "#cc3a74", "#eb5296", "#ff88b0", "#ffc8cf")         # raw_siftite
CEMENT = hexes("#7c3f30", "#ad5d3e", "#d67a52", "#e48f55", "#eca556", "#f0b360", "#f5ca84")             # breccia cement
VERDIGRIS = hexes("#1d3b47", "#28585f", "#367674", "#479185", "#64ab95", "#94c9a6", "#c6e2b6")          # copper patina


def by_rank(img, ramp, pick=None):
    """Replace every opaque colour by the ramp colour at its luminance rank (within its group, see pick)."""
    groups = {}
    for p in img.get_flattened_data():
        if p[3]:
            groups.setdefault(pick(p) if pick else 0, set()).add(p[:3])
    mapping = {}
    for g, colours in groups.items():
        r = ramp[g] if isinstance(ramp, dict) else ramp
        order = sorted(colours, key=lum)
        for i, c in enumerate(order):
            mapping[c] = r[round(i * (len(r) - 1) / max(1, len(order) - 1))]
    out = img.copy()
    out.putdata([mapping[p[:3]] + (p[3],) if p[3] else p for p in img.get_flattened_data()])
    return out


def is_green(p):
    """raw copper's verdigris pixels"""
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))
    return "green" if 0.3 < h < 0.6 and s > 0.15 else "copper"


COPPER_RAMPS = {"copper": CEMENT, "green": VERDIGRIS}
textures = {
    "item/raw_patina": by_rank(vanilla("item/raw_copper"), COPPER_RAMPS, is_green),
    "item/patina_ingot": by_rank(vanilla("item/copper_ingot"), VERDIGRIS),
    "block/raw_patina_block/raw_patina_block": by_rank(vanilla("block/raw_copper_block"), COPPER_RAMPS, is_green),
    "block/patina_block/patina_block": by_rank(vanilla("block/copper_block"), VERDIGRIS),
    "block/siftite_block/siftite_block": by_rank(vanilla("block/gold_block"), SIFTITE),
    "block/raw_siftite_block/raw_siftite_block": by_rank(vanilla("block/raw_iron_block"), RAW_SIFTITE),
}
for name, img in textures.items():
    art_guard.save(img, T / f"{name}.png")


# ---- patina ore, oxidation 1: the breccia's cement turns to verdigris, first where it touches the clasts ----
def oxidised(breccia):
    px = breccia.load()
    cement = {(x, y) for x in range(16) for y in range(16) if colorsys.rgb_to_hsv(*(c / 255 for c in px[x, y][:3]))[1] > 0.45
              and lum(px[x, y]) > 140}
    rnd = random.Random("patina")
    seeds = [(rnd.randrange(16), rnd.randrange(16)) for _ in range(5)]
    def wrap(a, b):
        d = abs(a - b)
        return min(d, 16 - d)
    def score(x, y):          # distance to the nearest clast (non-cement) pixel, minus a few random patina blooms
        near = min(max(wrap(x, a), wrap(y, b)) for a in range(16) for b in range(16) if (a, b) not in cement)
        bloom = min(wrap(x, sx) + wrap(y, sy) for sx, sy in seeds)
        return near + 0.35 * bloom
    turned = sorted(cement, key=lambda p: score(*p))[:round(len(cement) * 0.62)]
    order = sorted({px[p][:3] for p in turned}, key=lum)
    mapping = {c: VERDIGRIS[1 + round(i * (len(VERDIGRIS) - 2) / max(1, len(order) - 1))] for i, c in enumerate(order)}
    out = breccia.copy()
    for p in turned:
        out.putpixel(p, mapping[px[p][:3]] + (255,))
    return out


ORE = T / "block/patina_ore"
ARGENT = T / "block/argent_ore/argent_ore.png"
if ARGENT.exists():                       # one-time move (the old patina textures were backed up in .texture_backups/)
    breccia = Image.open(ARGENT).convert("RGBA")
    breccia.save(ORE / "patina_ore_oxidation0.png")
    oxidised(breccia).save(ORE / "patina_ore_oxidation1.png")
    art_guard.record(ORE / "patina_ore_oxidation0.png", ORE / "patina_ore_oxidation1.png")


# ---- block / item resources ----
def cube(name):
    wj(A / f"blockstates/{name}.json", {"variants": {"": {"model": f"pysift:block/{name}/{name}"}}})
    wj(A / f"models/block/{name}/{name}.json", {"parent": "minecraft:block/cube_all",
                                                "textures": {"all": f"pysift:block/{name}/{name}"}})
    wj(A / f"models/item/{name}.json", {"parent": f"pysift:block/{name}/{name}"})
    wj(A / f"items/{name}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{name}"}})
    loot = {"type": "minecraft:block", "pools": [{"rolls": 1, "condition": {"type": "minecraft:survives_explosion"},
                                                  "entries": [{"type": "minecraft:item", "name": f"pysift:{name}"}]}],
            "random_sequence": f"pysift:blocks/{name}"}
    for folder in ("loot_table", "loot_tables"):
        wj(D / f"pysift/{folder}/blocks/{name}.json", loot)


def flat_item(name):
    wj(A / f"models/item/{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"pysift:item/{name}"}})
    wj(A / f"items/{name}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{name}"}})


BLOCKS = ["siftite_block", "raw_siftite_block", "patina_block", "raw_patina_block"]
for b in BLOCKS:
    cube(b)
for i in ("raw_patina", "patina_ingot"):
    flat_item(i)

# patina ore drops raw patina like copper ore (2-5, fortune); silk touch keeps the ore and its oxidation
ore_loot = {"type": "minecraft:block", "random_sequence": "pysift:blocks/patina_ore", "pools": [{"rolls": 1, "entries": [{
    "type": "minecraft:alternatives", "children": [
        {"type": "minecraft:item", "name": "pysift:patina_ore", "condition": "minecraft:tool/can_silk_touch",
         "modifier": [{"type": "minecraft:copy_state", "block": "pysift:patina_ore", "properties": ["oxidation"]}]},
        {"type": "minecraft:item", "name": "pysift:raw_patina", "modifier": [
            {"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 2, "max": 5}},
            {"type": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
            {"type": "minecraft:explosion_decay"}]}]}]}]}
for folder in ("loot_table", "loot_tables"):
    wj(D / f"pysift/{folder}/blocks/patina_ore.json", ore_loot)


# ---- recipes: 9 <-> 1 storage, smelting ----
def shaped(name, pattern, key, result, count=1, category="building"):
    wj(D / f"pysift/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": category, "pattern": pattern,
                                         "key": key, "result": {"id": result, "count": count}})


def shapeless(name, ingredient, result, count):
    wj(D / f"pysift/recipe/{name}.json", {"type": "minecraft:crafting_shapeless", "category": "misc",
                                         "ingredients": [ingredient], "result": {"id": result, "count": count}})


def cooking(name, kind, ingredient, result, xp, time):
    wj(D / f"pysift/recipe/{name}.json", {"type": f"minecraft:{kind}", "category": "misc", "ingredient": ingredient,
                                         "result": {"id": result}, "experience": xp, "cookingtime": time})


for block, item in (("siftite_block", "siftite_ingot"), ("raw_siftite_block", "raw_siftite"),
                    ("patina_block", "patina_ingot"), ("raw_patina_block", "raw_patina")):
    shaped(block, ["###", "###", "###"], {"#": f"pysift:{item}"}, f"pysift:{block}")
    shapeless(f"{item}_from_{block}", f"pysift:{block}", f"pysift:{item}", 9)
for src in ("raw_patina", "patina_ore"):
    cooking(f"patina_ingot_from_smelting_{src}", "smelting", f"pysift:{src}", "pysift:patina_ingot", 0.7, 200)
    cooking(f"patina_ingot_from_blasting_{src}", "blasting", f"pysift:{src}", "pysift:patina_ingot", 0.7, 100)


# ---- tags ----
def add_tag(path, values):
    f = D / path
    tag = json.loads(f.read_text(encoding="utf-8-sig")) if f.exists() else {"replace": False, "values": []}
    tag["values"] += [v for v in values if v not in tag["values"]]
    wj(f, tag)


ids = [f"pysift:{b}" for b in BLOCKS]
add_tag("minecraft/tags/block/mineable/pickaxe.json", ids)
add_tag("minecraft/tags/block/needs_stone_tool.json", ids)
add_tag("minecraft/tags/block/blocks_motion_no_leaves.json", ids)
add_tag("minecraft/tags/block/beacon_base_blocks.json", ["pysift:siftite_block", "pysift:patina_block"])
add_tag("minecraft/tags/item/beacon_payment_items.json", ["pysift:siftite_ingot", "pysift:patina_ingot"])

# ---- names ----
NAMES = {
    "block.pysift.siftite_block": ("Block of Siftite", "隙浮金錠塊"),
    "block.pysift.raw_siftite_block": ("Block of Raw Siftite", "粗隙浮金塊"),
    "block.pysift.patina_block": ("Block of Patina", "銅綠錠塊"),
    "block.pysift.raw_patina_block": ("Block of Raw Patina", "粗銅綠塊"),
    "item.pysift.raw_patina": ("Raw Patina", "粗銅綠"),
    "item.pysift.patina_ingot": ("Patina Ingot", "銅綠錠"),
    "tooltip.pysift.patina_ingot": ("Soul power material", "靈魂動力的材料"),
    "tooltip.pysift.soul_essence.use": ("Use on a block: change its variant (uses 1)",
                                        "對方塊右鍵：換成下一種型態（消耗 1 個）"),
    "tooltip.pysift.soul_essence.select": ("Sneak + use: choose which variant to change", "潛行＋右鍵：選擇要換的型態"),
    "message.pysift.soul_essence.no_variants": ("The souls find nothing to reshape here", "靈魂在這裡找不到可以重塑的型態"),
    "message.pysift.soul_essence.selected": ("Reshaping: %s (now %s)", "要重塑的型態：%s（目前是 %s）"),
    "message.pysift.soul_essence.changed": ("%s → %s", "%s → %s"),
}
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8-sig"))
    for k, v in NAMES.items():
        data[k] = v[i]
    for k in ("block.pysift.siftite_block", "block.pysift.raw_siftite_block", "block.pysift.patina_block",
              "block.pysift.raw_patina_block"):
        data["item" + k[len("block"):]] = data[k]
    wj(f, data)
print("metal blocks:", ", ".join(BLOCKS + ["raw_patina", "patina_ingot"]))
