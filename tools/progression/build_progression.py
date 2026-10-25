"""Resources for the phase 1 progression content (ModProgression.java): models, item definitions, placeholder
textures, loot tables, recipes, tags and lang. Usage: python -I tools/progression/build_progression.py <project>

Placeholder textures are painted procedurally from fixed seeds (the user replaces them with hand-drawn art later;
the list of what to draw is written to art_requests/progression.md). A texture that already exists and is NOT one of
our placeholders (its PNG differs from what we would paint) is never overwritten, so hand-drawn art is safe."""
import json, random, sys, hashlib
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1])
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
STATE = P / "tools/progression/placeholder_hashes.json"     # sha1 of every placeholder we painted
placeholder_hashes = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
ART_REQUESTS = []                                            # (texture path, what to draw)


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha1(path):
    return hashlib.sha1(path.read_bytes()).hexdigest()


def save_placeholder(img, rel, request):
    """Write a placeholder texture unless hand-drawn art is already there."""
    path = A / "textures" / f"{rel}.png"
    ART_REQUESTS.append((f"textures/{rel}.png", request))
    if path.exists() and placeholder_hashes.get(rel) != sha1(path):
        return                                               # replaced by the user: keep it
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    placeholder_hashes[rel] = sha1(path)


# ------------------------------------------------------------------ placeholder painting
def speckle(base_path, colours, density, seed):
    """Copy of a 16x16 texture with clusters of ore specks in the given colours."""
    rnd = random.Random(seed)
    img = Image.open(base_path).convert("RGBA").crop((0, 0, 16, 16))
    px = img.load()
    for _ in range(int(density)):
        cx, cy = rnd.randint(1, 14), rnd.randint(1, 14)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0)):
            if rnd.random() < 0.75:
                c = colours[rnd.randrange(len(colours))]
                px[min(15, max(0, cx + dx)), min(15, max(0, cy + dy))] = c + (255,)
    return img


def blob_item(colours, seed, shape="lump"):
    """A simple 16x16 item sprite: a shaded lump / pile / orb in the given dark->light colours."""
    rnd = random.Random(seed)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    cx, cy = 7.5, 8.5
    for y in range(16):
        for x in range(16):
            dx, dy = (x - cx) / 6.0, (y - cy) / (5.0 if shape == "pile" else 6.0)
            if shape == "pile":
                dy = (y - 11) / 4.5
            r = dx * dx + dy * dy + rnd.uniform(-0.12, 0.12)
            if r < 1.0 and (shape != "pile" or y >= 6):
                light = 1 - (x + y) / 30 + rnd.uniform(-0.1, 0.1)      # lit from the top-left
                k = min(len(colours) - 1, max(0, int(light * len(colours))))
                px[x, y] = colours[k] + (255,)
    for y in range(16):                                      # dark outline
        for x in range(16):
            if px[x, y][3] == 0 and any(0 <= x + a < 16 and 0 <= y + b < 16 and px[x + a, y + b][3] and
                                        px[x + a, y + b][:3] != colours[0] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = colours[0] + (255,)
    return img


def crystal_cluster(colours, seed):
    """Amethyst-cluster style sprite (drawn on a cross model): a few upward crystal spikes."""
    rnd = random.Random(seed)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for base_x, height, width in ((7, 13, 2), (3, 8, 2), (11, 9, 2), (5, 5, 1), (10, 6, 1)):
        for y in range(16 - height, 16):
            t = (y - (16 - height)) / height
            half = max(0, round(width * t + 0.3))
            for x in range(base_x - half, base_x + half + 1):
                if 0 <= x < 16:
                    k = 3 if x == base_x - half else 2 if x < base_x else 1
                    if y < 16 - height + 2:
                        k = 3
                    px[x, y] = colours[min(k, len(colours) - 1)] + (255,)
    return img


# palettes taken from the existing item art (siftite_ingot, charoite)
SIFTITE = [(45, 55, 65), (80, 95, 105), (120, 135, 145), (230, 205, 120)]
CHAROITE = [(70, 24, 120), (110, 40, 175), (160, 70, 225), (200, 120, 255), (240, 200, 255)]
SOUL = [(20, 70, 90), (40, 150, 170), (110, 225, 235), (200, 250, 250)]
FUSE = [(70, 50, 40), (150, 110, 60), (220, 170, 80), (250, 230, 150)]

VOID_STONE = A / "textures/block/void_stone/void_stone_c.png"
save_placeholder(speckle(VOID_STONE, [SIFTITE[2], SIFTITE[3], SIFTITE[3]], 7, 11), "block/progression/siftite_ore",
                 "篩金石礦：虛黑岩底，帶淡金色與灰銀色的礦點（16x16）")
save_placeholder(crystal_cluster(CHAROITE[1:], 12), "block/progression/charoite_cluster",
                 "紫龍晶簇：像紫水晶簇的紫色晶刺，畫在十字模型上（16x16，透明背景）")
save_placeholder(blob_item(SIFTITE, 13), "item/raw_siftite", "粗篩金石：灰銀色礦塊帶金色斑點（物品 16x16）")
save_placeholder(blob_item(FUSE, 14, "pile"), "item/fuse_powder", "引信粉：一小堆金黃色火藥粉（物品 16x16）")
save_placeholder(blob_item(SOUL, 15), "item/soul_essence", "靈魂精華：發光的青藍色靈魂團（物品 16x16）")


# ------------------------------------------------------------------ models / blockstates / items
def item_def(name, model=None):
    wj(A / f"items/{name}.json", {"model": {"type": "minecraft:model", "model": model or f"pysift:item/{name}"}})


def generated_item(name, texture=None):
    wj(A / f"models/item/{name}.json", {"parent": "minecraft:item/generated",
                                        "textures": {"layer0": texture or f"pysift:item/{name}"}})
    item_def(name)


# siftite ore: plain cube
wj(A / "blockstates/siftite_ore.json", {"variants": {"": {"model": "pysift:block/progression/siftite_ore"}}})
wj(A / "models/block/progression/siftite_ore.json", {"parent": "minecraft:block/cube_all",
                                                     "textures": {"all": "pysift:block/progression/siftite_ore"}})
item_def("siftite_ore", "pysift:block/progression/siftite_ore")

# charoite cluster: cross model, rotated by facing like the vanilla amethyst cluster
FACING_ROT = {"up": {}, "down": {"x": 180}, "north": {"x": 90}, "south": {"x": 90, "y": 180},
              "east": {"x": 90, "y": 90}, "west": {"x": 90, "y": 270}}
wj(A / "blockstates/charoite_cluster.json", {"variants": {
    f"facing={f},waterlogged={w}": {"model": "pysift:block/progression/charoite_cluster", **rot}
    for f, rot in FACING_ROT.items() for w in ("false", "true")}})
wj(A / "models/block/progression/charoite_cluster.json", {"parent": "minecraft:block/cross", "render_type": "cutout",
                                                          "textures": {"cross": "pysift:block/progression/charoite_cluster"}})
generated_item("charoite_cluster", "pysift:block/progression/charoite_cluster")

for name in ("raw_siftite", "fuse_powder", "soul_essence"):
    generated_item(name)


# ------------------------------------------------------------------ loot tables
def loot(path, pools):
    for folder in ("loot_table", "loot_tables"):             # plural kept for older tooling (CLAUDE.md)
        wj(D / f"pysift/{folder}/{path}.json", {"type": "minecraft:block" if path.startswith("blocks/") else "minecraft:entity",
                                                "pools": pools, "random_sequence": f"pysift:{path}"})


def ore_loot(block, drop, count=None):
    child = {"type": "minecraft:item", "name": drop, "modifier": (
        ([{"type": "minecraft:set_count", "count": count}] if count else []) +
        [{"type": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
         {"type": "minecraft:explosion_decay"}])}
    loot(f"blocks/{block}", [{"rolls": 1, "entries": [{"type": "minecraft:alternatives", "children": [
        {"type": "minecraft:item", "condition": "minecraft:tool/can_silk_touch", "name": f"pysift:{block}"}, child]}]}])


ore_loot("siftite_ore", "pysift:raw_siftite")
ore_loot("charoite_cluster", "pysift:charoite", {"type": "minecraft:uniform", "min": 2, "max": 4})


def drop(item, lo, hi, chance=None, looting=1.0):
    entry = {"type": "minecraft:item", "name": item, "modifier": [
        {"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}},
        {"type": "minecraft:enchanted_count_increase", "count": {"type": "minecraft:uniform", "min": 0.0, "max": looting},
         "enchantment": "minecraft:looting"}]}
    pool = {"rolls": 1, "entries": [entry]}
    if chance is not None:
        pool["condition"] = {"type": "minecraft:all_of", "terms": [   # 26.3: one "condition" per pool
            {"type": "minecraft:killed_by_player"},
            {"type": "minecraft:random_chance_with_enchanted_bonus", "enchantment": "minecraft:looting",
             "unenchanted_chance": chance, "enchanted_chance": {"type": "minecraft:linear",
                                                               "base": chance + 0.05, "per_level_above_first": 0.05}}]}
    return pool


ESSENCE = lambda chance: drop("pysift:soul_essence", 1, 1, chance)   # hostile Sift mobs: material for the summoning sigil
MOB_DROPS = {   # entity: pools (bosses get their loot in a later step; lootkin keeps its hand-made table)
    "fusefly": [drop("pysift:fuse_powder", 1, 2), ESSENCE(0.25)],
    "dartback": [drop("minecraft:arrow", 0, 3), ESSENCE(0.3)],
    "hurler": [drop("minecraft:cobblestone", 1, 3), ESSENCE(0.3)],
    "hunter": [drop("minecraft:bone", 0, 2), ESSENCE(0.4)],
    "trapper": [drop("minecraft:string", 1, 3), ESSENCE(0.4)],
    "stalker": [drop("minecraft:bone", 0, 2), ESSENCE(0.35)],
    "sentinel": [drop("pysift:raw_siftite", 0, 1), ESSENCE(0.5)],
    "scavenger": [drop("minecraft:bone", 0, 1), drop("minecraft:gold_nugget", 0, 3), ESSENCE(0.3)],
    "prickle": [drop("minecraft:stick", 0, 2), ESSENCE(0.25)],
    "roamroot": [drop("minecraft:stick", 1, 3), drop("pysift:soul_willow_sapling", 0, 1), ESSENCE(0.35)],
    "bloombud": [drop("pysift:soul_berries", 0, 2), ESSENCE(0.25)],
    "tuner": [drop("minecraft:amethyst_shard", 0, 2), ESSENCE(0.4)],
    "wobble": [drop("minecraft:slime_ball", 0, 2), ESSENCE(0.25)],
    "nester": [drop("minecraft:feather", 1, 3), ESSENCE(0.35)],
    "seedling": [drop("minecraft:wheat_seeds", 0, 2)],
    "sprout": [drop("minecraft:wheat_seeds", 0, 2)],
    "singer": [drop("minecraft:echo_shard", 0, 1, 0.1)],
    "echo_golem": [drop("pysift:charoite", 0, 2)],
    "blub": [drop("minecraft:slime_ball", 0, 1)],
    "nuzzle": [drop("minecraft:leather", 0, 2)],
    "pollinator": [drop("minecraft:honeycomb", 0, 1)],
    "slabber": [drop("minecraft:leather", 0, 2)],
}
for mob, pools in MOB_DROPS.items():
    loot(f"entities/{mob}", pools)


# ------------------------------------------------------------------ recipes
def cooking(name, kind, ingredient, result, xp, time):
    wj(D / f"pysift/recipe/{name}.json", {"type": f"minecraft:{kind}", "category": "misc", "cookingtime": time,
                                          "experience": xp, "group": result.split(":")[1], "ingredient": ingredient,
                                          "result": {"id": result}})


cooking("siftite_ingot_from_smelting_raw_siftite", "smelting", "pysift:raw_siftite", "pysift:siftite_ingot", 0.8, 200)
cooking("siftite_ingot_from_blasting_raw_siftite", "blasting", "pysift:raw_siftite", "pysift:siftite_ingot", 0.8, 100)
cooking("siftite_ingot_from_smelting_siftite_ore", "smelting", "pysift:siftite_ore", "pysift:siftite_ingot", 0.8, 200)
cooking("siftite_ingot_from_blasting_siftite_ore", "blasting", "pysift:siftite_ore", "pysift:siftite_ingot", 0.8, 100)


# ------------------------------------------------------------------ tags (merged into the existing files)
def add_tag(path, values):
    f = D / path
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"replace": False, "values": []}
    for v in values:
        if v not in data["values"]:
            data["values"].append(v)
    wj(f, data)


add_tag("minecraft/tags/block/mineable/pickaxe.json", ["pysift:siftite_ore", "pysift:charoite_cluster"])
add_tag("minecraft/tags/block/needs_iron_tool.json", ["pysift:siftite_ore"])
add_tag("minecraft/tags/block/blocks_motion_no_leaves.json", ["pysift:siftite_ore"])   # build_vegetation.py keeps it too


# ------------------------------------------------------------------ lang (merged)
LANG = {
    "siftite_ore": ("Siftite Ore", "篩金石礦"), "charoite_cluster": ("Charoite Cluster", "紫龍晶簇"),
    "raw_siftite": ("Raw Siftite", "粗篩金石"), "fuse_powder": ("Fuse Powder", "引信粉"),
    "soul_essence": ("Soul Essence", "靈魂精華"),
}
BLOCKS = {"siftite_ore", "charoite_cluster"}
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in LANG.items():
        if key in BLOCKS:
            data[f"block.pysift.{key}"] = names[i]
        data[f"item.pysift.{key}"] = names[i]
    wj(f, data)

# ------------------------------------------------------------------ siftite gear (SiftiteGear.java)
# Placeholder sprites from hand-made pixel masks: h/H handle, l highlight, m metal, d shadow, g gold trim; outline added.
GEAR_COLOURS = {"h": (96, 64, 36), "H": (128, 88, 52), "l": (190, 200, 205), "m": (130, 145, 155), "d": (82, 96, 106),
                "g": (230, 205, 120)}
OUTLINE = (40, 48, 56)
BLANK = "................"
MASKS = {
    "siftite_sword": ["..............ll", ".............lmd", "............lmd.", "...........lmd..", "..........lmd...",
                      ".........lmd....", "........lmd.....", ".......lmd......", "..g...lmd.......", "..gg.lmd........",
                      "...ggmd.........", "....Hg..........", "...hHgg.........", "..hh..g.........", ".hh.............", BLANK],
    "siftite_pickaxe": [BLANK, ".....lllmmmg....", "....lmmmmmmmd...", "...lmd....Hgdd..", "..lmd....hH..dd.",
                        "..md....hH....d.", "..md...hH.......", "......hH........", ".....hH.........", "....hH..........",
                        "...hH...........", "..hH............", ".hH.............", BLANK, BLANK, BLANK],
    "siftite_axe": [BLANK, "........lmm.....", ".......lmmmd....", "......lmmmmd....", "......mmmgHd....",
                    ".......ddhHd....", "........hH......", ".......hH.......", "......hH........", ".....hH.........",
                    "....hH..........", "...hH...........", "..hH............", ".hH.............", BLANK, BLANK],
    "siftite_shovel": [BLANK, "............lm..", "...........lmmd.", "..........lmmmd.", ".........gmmmd..",
                       "........hHdd....", ".......hH.......", "......hH........", ".....hH.........", "....hH..........",
                       "...hH...........", "..hH............", ".hH.............", BLANK, BLANK, BLANK],
    "siftite_hoe": [BLANK, ".......lmmmmd...", "......lmdgHd....", ".........hH.....", "........hH......",
                    ".......hH.......", "......hH........", ".....hH.........", "....hH..........", "...hH...........",
                    "..hH............", ".hH.............", BLANK, BLANK, BLANK, BLANK],
    "siftite_helmet": [BLANK, BLANK, BLANK, "....lllmmmmd....", "...lmmmmmmmmd...", "...mmgmmmmgmd...", "...mmd....mmd...",
                       "...md......md...", "...dd......dd...", BLANK, BLANK, BLANK, BLANK, BLANK, BLANK, BLANK],
    "siftite_chestplate": [BLANK, BLANK, "..lmm......mmd..", ".lmmmmlllllmmmd.", ".mmmmmmgmmmmmmd.", ".mmd.mmmmmm.dmd.",
                           "..d..mmgmmm..d..", ".....mmmmmmd....", ".....mmgmmmd....", ".....mmmmmmd....", ".....ddddddd....",
                           BLANK, BLANK, BLANK, BLANK, BLANK],
    "siftite_leggings": [BLANK, BLANK, "....lmmgmmmd....", "....mmmmmmmd....", "....mmmddmmd....", "....mmd..mmd....",
                         "....mmd..mmd....", "....mmd..mmd....", "....mmd..mmd....", "....mmd..mmd....", "....dd....dd....",
                         BLANK, BLANK, BLANK, BLANK, BLANK],
    "siftite_boots": [BLANK, BLANK, BLANK, BLANK, BLANK, "...lmd....lmd...", "...mmd....mmd...", "...mmd....mmd...",
                      "..gmmd...gmmd...", "..mmmd...mmmd...", "..dddd...dddd...", BLANK, BLANK, BLANK, BLANK, BLANK],
}


def mask_sprite(rows):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in GEAR_COLOURS:
                px[x, y] = GEAR_COLOURS[ch] + (255,)
    filled = {(x, y) for y in range(16) for x in range(16) if px[x, y][3]}
    for (x, y) in filled:                                    # 1px dark outline around the shape
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + a < 16 and 0 <= y + b < 16 and (x + a, y + b) not in filled:
                px[x + a, y + b] = OUTLINE + (255,)
    return img


GEAR_NAMES = {"siftite_sword": ("Siftite Sword", "篩金石劍"), "siftite_pickaxe": ("Siftite Pickaxe", "篩金石鎬"),
              "siftite_axe": ("Siftite Axe", "篩金石斧"), "siftite_shovel": ("Siftite Shovel", "篩金石鏟"),
              "siftite_hoe": ("Siftite Hoe", "篩金石鋤"), "siftite_helmet": ("Siftite Helmet", "篩金石頭盔"),
              "siftite_chestplate": ("Siftite Chestplate", "篩金石胸甲"), "siftite_leggings": ("Siftite Leggings", "篩金石護腿"),
              "siftite_boots": ("Siftite Boots", "篩金石靴子")}
TOOLS = ("siftite_sword", "siftite_pickaxe", "siftite_axe", "siftite_shovel", "siftite_hoe")
for name, rows in MASKS.items():
    save_placeholder(mask_sprite(rows), f"item/{name}", f"{GEAR_NAMES[name][1]}：銀灰金屬、金色點綴（物品 16x16）")
    wj(A / f"models/item/{name}.json", {"parent": "minecraft:item/handheld" if name in TOOLS else "minecraft:item/generated",
                                        "textures": {"layer0": f"pysift:item/{name}"}})
    item_def(name)


def armor_layer(leggings, seed):
    """64x32 humanoid armour layer painted on the vanilla box-UV layout (head, body, arms, legs)."""
    rnd = random.Random(seed)
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    px = img.load()

    def box(u, v, w, h, d, rows=None):
        """Fill every face of a box-UV cube; rows limits the side faces to those rows (from the top)."""
        faces = [(u + d, v, w, d), (u + d + w, v, w, d),                       # top, bottom
                 (u, v + d, d, h), (u + d, v + d, w, h), (u + d + w, v + d, d, h), (u + 2 * d + w, v + d, w, h)]
        for i, (x0, y0, fw, fh) in enumerate(faces):
            for y in range(fh):
                if i >= 2 and rows and not (rows[0] <= y < rows[1]):
                    continue
                for x in range(fw):
                    edge = y in (0, fh - 1) or x in (0, fw - 1)
                    if edge:
                        c = GEAR_COLOURS["g"] if rnd.random() < 0.5 else GEAR_COLOURS["d"]
                    else:
                        c = GEAR_COLOURS[rnd.choice("lmmmd")]
                    px[x0 + x, y0 + y] = c + (255,)

    if not leggings:
        box(0, 0, 8, 8, 8)                       # helmet
        for x in range(10, 14):                  # eye slit on the front face (u 8..16, v 8..16)
            px[x, 12] = (0, 0, 0, 0)
        box(16, 16, 8, 12, 4, rows=(0, 9))       # chestplate body
        box(40, 16, 4, 12, 4, rows=(0, 6))       # chestplate arms
        box(0, 16, 4, 12, 4, rows=(8, 12))       # boots
    else:
        box(16, 16, 8, 12, 4, rows=(7, 12))      # leggings waist
        box(0, 16, 4, 12, 4, rows=(0, 9))        # leggings legs
    return img


save_placeholder(armor_layer(False, 21), "entity/equipment/humanoid/siftite", "篩金石盔甲穿著外觀（頭盔、胸甲、靴子；原版 64x32 版型）")
save_placeholder(armor_layer(True, 22), "entity/equipment/humanoid_leggings/siftite", "篩金石護腿穿著外觀（原版 64x32 版型）")
wj(A / "equipment/siftite.json", {"layers": {"humanoid": [{"texture": "pysift:siftite"}],
                                             "humanoid_leggings": [{"texture": "pysift:siftite"}]}})


def shaped(name, pattern, key, category="equipment"):
    wj(D / f"pysift/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": category, "key": key,
                                          "pattern": pattern, "result": {"id": f"pysift:{name}"}})


I_S = {"I": "#pysift:siftite_tool_materials", "S": "minecraft:stick"}
I_ = {"I": "#pysift:repairs_siftite_armor"}
shaped("siftite_sword", [" I ", " I ", " S "], I_S)
shaped("siftite_pickaxe", ["III", " S ", " S "], I_S)
shaped("siftite_axe", ["II", "IS", " S"], I_S)
shaped("siftite_shovel", ["I", "S", "S"], I_S)
shaped("siftite_hoe", ["II", " S", " S"], I_S)
shaped("siftite_helmet", ["III", "I I"], I_)
shaped("siftite_chestplate", ["I I", "III", "III"], I_)
shaped("siftite_leggings", ["III", "I I", "I I"], I_)
shaped("siftite_boots", ["I I", "I I"], I_)

add_tag("pysift/tags/item/siftite_tool_materials.json", ["pysift:siftite_ingot"])
add_tag("pysift/tags/item/repairs_siftite_armor.json", ["pysift:siftite_ingot"])
for tag, item in (("swords", "sword"), ("pickaxes", "pickaxe"), ("axes", "axe"), ("shovels", "shovel"), ("hoes", "hoe"),
                  ("head_armor", "helmet"), ("chest_armor", "chestplate"), ("leg_armor", "leggings"), ("foot_armor", "boots")):
    add_tag(f"minecraft/tags/item/{tag}.json", [f"pysift:siftite_{item}"])
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in GEAR_NAMES.items():
        data[f"item.pysift.{key}"] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ boss rewards (BossRewards.java)
HARMONIZER_PAL = [(30, 40, 80), (60, 90, 170), (120, 170, 240), (220, 240, 255)]
CROWN_PAL = [(90, 60, 20), (170, 120, 40), (230, 190, 80), (255, 240, 170)]
SCULK_PAL = [(10, 30, 40), (20, 80, 100), (50, 170, 190), (160, 245, 250)]
save_placeholder(blob_item(HARMONIZER_PAL, 31), "item/harmonizer_core", "調和者核心：發出音波光暈的藍色核心（物品 16x16）")
save_placeholder(mask_sprite([BLANK, BLANK, BLANK, BLANK, "..g...g...g.....", "..gg.ggg.gg.....", "..gggggggggg....",
                              "..glgglgglgg....", "..gggggggggg....", "..dddddddddd....", BLANK, BLANK, BLANK, BLANK, BLANK, BLANK]),
                 "item/monarch_crown", "君王王冠：金色的尖頂王冠（物品 16x16）")
save_placeholder(blob_item(SCULK_PAL, 32), "item/sculk_monstrosity_heart", "幽匿巨怪之心：跳動的深青色幽匿心臟（物品 16x16）")
save_placeholder(crystal_cluster(HARMONIZER_PAL[1:], 33), "item/resonant_crystal", "共鳴音晶：藍色的小晶體（物品 16x16）")
save_placeholder(blob_item(SCULK_PAL[:3], 34, "pile"), "item/sculk_scale", "幽匿鱗片：幾片深青色鱗片（物品 16x16）")
save_placeholder(blob_item([(40, 20, 60), (90, 50, 140), (170, 110, 230), (240, 210, 255)], 35), "item/summoning_sigil",
                 "召喚印記：刻著符文的紫色圓形印記（物品 16x16）")
ALTAR_SIDE = speckle(A / "textures/block/dark_slate_bricks/dark_slate_bricks.png", [CHAROITE[2], SOUL[2]], 4, 36)
ALTAR_TOP = speckle(A / "textures/block/dark_slate_bricks/dark_slate_bricks.png", [SOUL[2], SOUL[3]], 10, 37)
save_placeholder(ALTAR_SIDE, "block/progression/sift_altar_side", "篩靈祭壇側面：深色板岩磚、紫與青色符文（16x16）")
save_placeholder(ALTAR_TOP, "block/progression/sift_altar_top", "篩靈祭壇頂面：發光的召喚陣（16x16）")
wj(A / "blockstates/sift_altar.json", {"variants": {"": {"model": "pysift:block/progression/sift_altar"}}})
wj(A / "models/block/progression/sift_altar.json", {"parent": "minecraft:block/cube_bottom_top", "textures": {
    "top": "pysift:block/progression/sift_altar_top", "side": "pysift:block/progression/sift_altar_side",
    "bottom": "pysift:block/dark_slate_bricks/dark_slate_bricks"}})
item_def("sift_altar", "pysift:block/progression/sift_altar")
loot("blocks/sift_altar", [{"rolls": 1, "condition": {"type": "minecraft:survives_explosion"},
                             "entries": [{"type": "minecraft:item", "name": "pysift:sift_altar"}]}])
add_tag("minecraft/tags/block/mineable/pickaxe.json", ["pysift:sift_altar"])
add_tag("minecraft/tags/block/blocks_motion_no_leaves.json", ["pysift:sift_altar"])
for name in ("harmonizer_core", "monarch_crown", "sculk_monstrosity_heart", "resonant_crystal", "sculk_scale", "summoning_sigil"):
    generated_item(name)


def boss_loot(boss, core, shard):
    loot(f"entities/{boss}", [
        {"rolls": 1, "entries": [{"type": "minecraft:item", "name": core}]},
        {"rolls": 1, "entries": [{"type": "minecraft:item", "name": shard, "modifier": [
            {"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 2, "max": 4}},
            {"type": "minecraft:enchanted_count_increase", "count": {"type": "minecraft:uniform", "min": 0.0, "max": 1.0},
             "enchantment": "minecraft:looting"}]}]},
        drop("pysift:soul_essence", 3, 6),
        drop("pysift:siftite_ingot", 2, 4)])


boss_loot("harmonizer", "pysift:harmonizer_core", "pysift:resonant_crystal")
boss_loot("monarch", "pysift:monarch_crown", "pysift:monarch_feather")
boss_loot("sculk_monstrosity", "pysift:sculk_monstrosity_heart", "pysift:sculk_scale")

shaped("summoning_sigil", ["ECE", "CIC", "ECE"], {"E": "pysift:soul_essence", "C": "pysift:charoite", "I": "pysift:siftite_ingot"}, "misc")
shaped("sift_altar", ["CEC", "EIE", "BBB"], {"C": "pysift:charoite", "E": "pysift:soul_essence", "I": "pysift:siftite_ingot",
                                             "B": "pysift:dark_slate_bricks"}, "building")

BOSS_LANG = {
    "item.pysift.harmonizer_core": ("Harmonizer Core", "調和者核心"),
    "item.pysift.monarch_crown": ("Monarch Crown", "君王王冠"),
    "item.pysift.sculk_monstrosity_heart": ("Sculk Monstrosity Heart", "幽匿巨怪之心"),
    "item.pysift.resonant_crystal": ("Resonant Crystal", "共鳴音晶"),
    "item.pysift.sculk_scale": ("Sculk Scale", "幽匿鱗片"),
    "item.pysift.summoning_sigil": ("Summoning Sigil", "召喚印記"),
    "block.pysift.sift_altar": ("Sift Altar", "篩靈祭壇"),
    "item.pysift.sift_altar": ("Sift Altar", "篩靈祭壇"),
    "message.pysift.altar.no_arena": ("The altar must stand within 48 blocks of a boss arena", "祭壇必須放在 Boss 競技場 48 格內"),
    "message.pysift.altar.boss_alive": ("The arena's boss is still alive", "這座競技場的 Boss 還活著"),
    "message.pysift.altar.summoned": ("%s answers the summons!", "%s 回應了召喚！"),
}
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in BOSS_LANG.items():
        data[key] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ boss weapons (BossWeapons.java)
GEAR_COLOURS.update({"b": HARMONIZER_PAL[1], "B": HARMONIZER_PAL[2], "c": CROWN_PAL[2], "s": SCULK_PAL[1], "S": SCULK_PAL[2]})
WEAPON_MASKS = {
    "sonic_staff": ["...........BBB..", "..........BbbbB.", "..........BbBbB.", "..........BbbbB.", "...........gBB..",
                    "..........hg....", ".........hH.....", "........hH......", ".......hH.......", "......hH........",
                    ".....hH.........", "....hH..........", "...hH...........", "..hH............", ".hH.............", BLANK],
    "dash_charm": [BLANK, BLANK, "......gggg......", ".....g....g.....", "....g......g....", ".....gccccg.....",
                   "....gcllcccg....", "....gcclccdg....", "....gcccccdg....", ".....gccdddg....", "......gdddg.....",
                   ".......ggg......", BLANK, BLANK, BLANK, BLANK],
    "sculk_hammer": [BLANK, ".......sSSs.....", "......sSSSSs....", "......sSllSs....", "......sSSSSs....", ".......sHHs.....",
                     "........hH......", ".......hH.......", "......hH........", ".....hH.........", "....hH..........",
                     "...hH...........", "..hH............", ".hH.............", BLANK, BLANK],
}
WEAPON_NAMES = {"sonic_staff": ("Sonic Staff", "音波法杖", "音波法杖：頂端鑲著藍色音晶的長杖"),
                "dash_charm": ("Dash Charm", "衝刺護符", "衝刺護符：金框鑲著王冠紋章的護符"),
                "sculk_hammer": ("Sculk Hammer", "重錘", "重錘：深青色幽匿錘頭的大錘")}
for name, rows in WEAPON_MASKS.items():
    save_placeholder(mask_sprite(rows), f"item/{name}", WEAPON_NAMES[name][2] + "（物品 16x16）")
    wj(A / f"models/item/{name}.json", {"parent": "minecraft:item/handheld" if name != "dash_charm" else "minecraft:item/generated",
                                        "textures": {"layer0": f"pysift:item/{name}"}})
    item_def(name)

shaped("sonic_staff", [" RH", " IR", "I  "], {"H": "pysift:harmonizer_core", "R": "pysift:resonant_crystal", "I": "pysift:siftite_ingot"})
shaped("dash_charm", ["F F", " C ", "FIF"], {"F": "pysift:monarch_feather", "C": "pysift:monarch_crown", "I": "pysift:siftite_ingot"})
shaped("sculk_hammer", ["SHS", "SIS", " I "], {"S": "pysift:sculk_scale", "H": "pysift:sculk_monstrosity_heart", "I": "pysift:siftite_ingot"})


def awaken(weapon, template, addition):
    """Smithing table: weapon + the OTHER two bosses' shards -> the same weapon, awakened (keeps enchantments)."""
    wj(D / f"pysift/recipe/{weapon}_awakening.json", {
        "type": "minecraft:smithing_transform", "template": template, "base": f"pysift:{weapon}", "addition": addition,
        "result": {"id": f"pysift:{weapon}", "components": {"pysift:awakened": True}}})


awaken("sonic_staff", "pysift:monarch_feather", "pysift:sculk_scale")
awaken("dash_charm", "pysift:resonant_crystal", "pysift:sculk_scale")
awaken("sculk_hammer", "pysift:resonant_crystal", "pysift:monarch_feather")

WEAPON_LANG = {
    "item.pysift.sonic_staff": ("Sonic Staff", "音波法杖"),
    "item.pysift.dash_charm": ("Dash Charm", "衝刺護符"),
    "item.pysift.sculk_hammer": ("Sculk Hammer", "重錘"),
    "tooltip.pysift.awakened": ("✦ Awakened", "✦ 已覺醒"),
    "tooltip.pysift.sonic_staff.use": ("Right-click: sonic boom (8 damage, 15 blocks, 3 s cooldown)", "右鍵：發射音爆（8 點傷害，15 格，冷卻 3 秒）"),
    "tooltip.pysift.sonic_staff.use_awakened": ("Right-click: wide sonic boom (12 damage, 15 blocks, 2 s cooldown)", "右鍵：寬幅音爆（12 點傷害，15 格，冷卻 2 秒）"),
    "tooltip.pysift.sonic_staff.hit": ("Hits chain to 3 nearby foes (3 damage) and inflict Soul Deprivation", "命中時連鎖 3 個敵人（各 3 點）並附加靈魂剝奪"),
    "tooltip.pysift.sonic_staff.hit_awakened": ("Hits chain to 5 nearby foes (4 damage) and inflict Soul Deprivation", "命中時連鎖 5 個敵人（各 4 點）並附加靈魂剝奪"),
    "tooltip.pysift.dash_charm.use": ("Right-click: dash, up to 2 times in a row", "右鍵：衝刺，最多連續 2 次"),
    "tooltip.pysift.dash_charm.use_awakened": ("Right-click: dash up to 3 times, cutting through foes", "右鍵：衝刺最多 3 次，穿過的敵人受到傷害"),
    "tooltip.pysift.dash_charm.decoy": ("Leaves a decoy of you for 10 seconds", "原地留下你的分身 10 秒，吸引怪物"),
    "tooltip.pysift.sculk_hammer.use": ("Hold right-click, release to slam the ground (4 blocks)", "按住右鍵蓄力，放開砸地（半徑 4 格）"),
    "tooltip.pysift.sculk_hammer.use_awakened": ("Hold right-click, release to slam the ground (6 blocks)", "按住右鍵蓄力，放開砸地（半徑 6 格）"),
    "tooltip.pysift.sculk_hammer.tendrils": ("Leaves sculk tendrils that explode with Soul Deprivation", "留下幽匿藤蔓，2 秒後爆炸並造成靈魂剝奪"),
}
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in WEAPON_LANG.items():
        data[key] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ sift beacon (SiftBeacon.java)
save_placeholder(crystal_cluster([(120, 240, 230), (180, 250, 245), (240, 255, 255), (255, 255, 255)], 41), "item/sift_beacon_gem",
                 "篩靈信標寶石：發出青白色光芒的寶石（物品 16x16）")
generated_item("sift_beacon_gem")
shaped("sift_beacon_gem", ["CCC", "HMS", "CCC"], {"C": "pysift:charoite", "H": "pysift:harmonizer_core",
                                                   "M": "pysift:monarch_crown", "S": "pysift:sculk_monstrosity_heart"}, "misc")
CHESTPLATES = ["minecraft:leather_chestplate", "minecraft:chainmail_chestplate", "minecraft:copper_chestplate",
               "minecraft:iron_chestplate", "minecraft:golden_chestplate", "minecraft:diamond_chestplate",
               "minecraft:netherite_chestplate", "pysift:siftite_chestplate"]
for chest in CHESTPLATES:     # smithing: gem (template) + chestplate + charoite -> same chestplate with the beacon inlaid
    wj(D / f"pysift/recipe/sift_beacon_inlay_{chest.split(':')[1]}.json", {
        "type": "minecraft:smithing_transform", "template": "pysift:sift_beacon_gem", "base": chest,
        "addition": "pysift:charoite", "result": {"id": chest, "components": {"pysift:sift_beacon": True}}})

# ------------------------------------------------------------------ advancements (progression line)
ADV = D / "pysift/advancement/progression"


def adv(name, parent, icon, title, desc, criteria, frame="task", hidden=False, show=True, background=None, xp=0):
    display = {"icon": {"id": icon}, "title": {"translate": f"advancements.pysift.{name}.title"},
               "description": {"translate": f"advancements.pysift.{name}.description"}, "frame": frame,
               "show_toast": show, "announce_to_chat": show and frame != "task", "hidden": hidden}
    if background:
        display["background"] = background
    data = {"criteria": criteria, "display": display, "requirements": [list(criteria)]}
    if parent:
        data["parent"] = f"pysift:progression/{parent}"
    if xp:
        data["rewards"] = {"experience": xp}
    wj(ADV / f"{name}.json", data)
    ADV_LANG[f"advancements.pysift.{name}.title"] = title[0], title[1]
    ADV_LANG[f"advancements.pysift.{name}.description"] = desc[0], desc[1]


ADV_LANG = {}
has = lambda items, **extra: {"trigger": "minecraft:inventory_changed", "conditions": {"items": [{"items": items, **extra}]}}
killed = lambda entity: {"trigger": "minecraft:player_killed_entity", "conditions": {"entity": {
    "type": "minecraft:entity_properties", "entity": "this", "predicate": {"minecraft:entity_type": entity}}}}
adv("root", None, "pysift:sift_beacon_gem", ("The Sift", "篩靈界"), ("Step through the portal into The Sift", "穿過傳送門，進入篩靈界"),
    {"entered": {"trigger": "minecraft:changed_dimension", "conditions": {"to": "pysift:the_sift"}}},
    show=False, background="minecraft:gui/advancements/backgrounds/end")
adv("spirit_touch", "root", "pysift:spirit_liquid_bucket", ("Soul Drain", "靈魂抽離"),
    ("Touch Spirit Liquid and suffer Soul Deprivation", "碰到靈液，陷入靈魂剝奪"),
    {"deprived": {"trigger": "minecraft:effects_changed", "conditions": {"effects": {"pysift:soul_deprivation": {}}}}})
adv("antidote", "spirit_touch", "pysift:soul_antidote", ("Second Wind", "失而復得"),
    ("Drink a Soul Antidote", "喝下靈魂解藥"),
    {"drank": {"trigger": "minecraft:consume_item", "conditions": {"item": {"items": "pysift:soul_antidote"}}}})
adv("siftite", "root", "pysift:raw_siftite", ("Sifted Metal", "篩出金屬"), ("Mine Siftite Ore", "挖到篩金石礦"),
    {"raw": has("pysift:raw_siftite")})
adv("siftite_armor", "siftite", "pysift:siftite_chestplate", ("Sift-Forged", "篩金鍛甲"),
    ("Craft any piece of Siftite armor", "製作任一件篩金石盔甲"),
    {"armor": has(["pysift:siftite_helmet", "pysift:siftite_chestplate", "pysift:siftite_leggings", "pysift:siftite_boots"])})
adv("kill_harmonizer", "root", "pysift:harmonizer_core", ("Silenced", "曲終人散"), ("Defeat the Harmonizer", "擊敗調和者"),
    {"kill": killed("pysift:harmonizer")}, frame="goal", xp=100)
adv("kill_monarch", "root", "pysift:monarch_crown", ("Uncrowned", "王冠落地"), ("Defeat the Monarch", "擊敗君王"),
    {"kill": killed("pysift:monarch")}, frame="goal", xp=100)
adv("kill_sculk_monstrosity", "root", "pysift:sculk_monstrosity_heart", ("Heart of the Deep", "深淵之心"),
    ("Defeat the Sculk Monstrosity", "擊敗幽匿巨怪"), {"kill": killed("pysift:sculk_monstrosity")}, frame="goal", xp=100)
adv("awakened", "kill_harmonizer", "pysift:sonic_staff", ("Awakening", "覺醒"),
    ("Awaken a boss weapon at a smithing table", "在鍛造台讓 Boss 武器覺醒"),
    {w: has(f"pysift:{w}", components={"pysift:awakened": True}) for w in ("sonic_staff", "dash_charm", "sculk_hammer")},
    frame="challenge", xp=200)
# any one of the three awakened weapons is enough: all criteria in ONE requirement group
data = json.loads((ADV / "awakened.json").read_text(encoding="utf-8"))
data["requirements"] = [["sonic_staff", "dash_charm", "sculk_hammer"]]
wj(ADV / "awakened.json", data)
adv("sift_beacon", "awakened", "pysift:sift_beacon_gem", ("Beacon of The Sift", "篩靈信標"),
    ("Inlay a Sift Beacon Gem into a chestplate", "把篩靈信標寶石鑲嵌到胸甲上"),
    {"beacon": has("#minecraft:chest_armor", components={"pysift:sift_beacon": True})}, frame="challenge", xp=500)

BEACON_LANG = {
    "item.pysift.sift_beacon_gem": ("Sift Beacon Gem", "篩靈信標寶石"),
    "tooltip.pysift.sift_beacon.inlaid": ("✦ Sift Beacon inlaid", "✦ 已鑲嵌篩靈信標"),
    "tag.item.pysift.siftite_tool_materials": ("Siftite Tool Materials", "篩金石工具材料"),
    "tag.item.pysift.repairs_siftite_armor": ("Repairs Siftite Armor", "可修理篩金石盔甲"),
    "tooltip.pysift.sift_beacon.aura": ("Players within 8 blocks are immune to Soul Deprivation",
                                        "半徑 8 格內的玩家免疫靈魂剝奪，靈液不再傷人"),
    **ADV_LANG,
}
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in BEACON_LANG.items():
        data[key] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ usage hints (tooltips)
HINT_LANG = {
    "tooltip.pysift.summoning_sigil.0": ("Use on a Sift Altar placed within 48 blocks of a boss arena",
                                         "對放在 Boss 競技場 48 格內的篩靈祭壇右鍵使用"),
    "tooltip.pysift.summoning_sigil.1": ("The arena's boss is summoned again at its center",
                                         "該競技場的 Boss 會在中央再次出現"),
    "tooltip.pysift.summoning_sigil.2": ("Find arenas with /locate boss <monarch|harmonizer|sculk_monstrosity>",
                                         "用 /locate boss <monarch|harmonizer|sculk_monstrosity> 找競技場"),
    "tooltip.pysift.sift_beacon_gem.0": ("Smithing Table: this gem (template) + any chestplate + Charoite",
                                         "鍛造台：模板欄放此寶石、裝備欄放任一胸甲、材料欄放紫龍晶"),
    "tooltip.pysift.sift_beacon_gem.1": ("Inlays the beacon; enchantments and trims are kept",
                                         "鑲嵌後保留胸甲原本的附魔與紋飾"),
    "tooltip.pysift.sonic_staff.how_to_awaken": ("Awaken: Smithing Table — Monarch Feather + this + Sculk Scale",
                                                 "覺醒：鍛造台，模板欄放君王羽刃、裝備欄放此武器、材料欄放幽匿鱗片"),
    "tooltip.pysift.dash_charm.how_to_awaken": ("Awaken: Smithing Table — Resonant Crystal + this + Sculk Scale",
                                                "覺醒：鍛造台，模板欄放共鳴音晶、裝備欄放此武器、材料欄放幽匿鱗片"),
    "tooltip.pysift.sculk_hammer.how_to_awaken": ("Awaken: Smithing Table — Resonant Crystal + this + Monarch Feather",
                                                  "覺醒：鍛造台，模板欄放共鳴音晶、裝備欄放此武器、材料欄放君王羽刃"),
}
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in HINT_LANG.items():
        data[key] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ soulite (SouliteGear.java): stronger than netherite
SOULITE_COLOURS = {"h": (40, 30, 60), "H": (70, 55, 100), "l": (150, 240, 230), "m": (90, 80, 160), "d": (50, 42, 100),
                   "g": (200, 140, 255)}


def soulite_sprite(rows):
    saved = dict(GEAR_COLOURS)
    GEAR_COLOURS.update(SOULITE_COLOURS)
    try:
        return mask_sprite(rows)
    finally:
        GEAR_COLOURS.clear()
        GEAR_COLOURS.update(saved)


SOULITE_NAMES = {"sword": ("Soulite Sword", "靈髓劍"), "pickaxe": ("Soulite Pickaxe", "靈髓鎬"), "axe": ("Soulite Axe", "靈髓斧"),
                 "shovel": ("Soulite Shovel", "靈髓鏟"), "hoe": ("Soulite Hoe", "靈髓鋤"), "helmet": ("Soulite Helmet", "靈髓頭盔"),
                 "chestplate": ("Soulite Chestplate", "靈髓胸甲"), "leggings": ("Soulite Leggings", "靈髓護腿"),
                 "boots": ("Soulite Boots", "靈髓靴子")}
for piece, names in SOULITE_NAMES.items():
    name = f"soulite_{piece}"
    save_placeholder(soulite_sprite(MASKS[f"siftite_{piece}"]), f"item/{name}", f"{names[1]}：深紫金屬、青色靈光點綴（物品 16x16）")
    wj(A / f"models/item/{name}.json", {"parent": "minecraft:item/handheld" if piece in ("sword", "pickaxe", "axe", "shovel", "hoe")
                                        else "minecraft:item/generated", "textures": {"layer0": f"pysift:item/{name}"}})
    item_def(name)
    # smithing: soulite upgrade template + netherite piece + soulite ingot -> soulite piece (enchantments kept)
    wj(D / f"pysift/recipe/soulite_{piece}_smithing.json", {
        "type": "minecraft:smithing_transform", "template": "pysift:soulite_upgrade_smithing_template",
        "base": f"minecraft:netherite_{piece}", "addition": "#pysift:soulite_tool_materials", "result": {"id": f"pysift:{name}"}})

save_placeholder(blob_item([(40, 30, 70), (90, 80, 160), (150, 240, 230), (220, 255, 250)], 51), "item/soulite_ingot",
                 "靈髓錠：深紫色金屬錠，表面有青色靈光紋（物品 16x16）")
save_placeholder(soulite_sprite([BLANK, "...dddddddddd...", "...dmmmmmmmmd...", "...dmllgglmmd...", "...dmlgggglmd...",
                                 "...dmmgllgmmd...", "...dmmmggmmmd...", "...dmmmmmmmmd...", "...dmlmmmmlmd...",
                                 "...dmmmmmmmmd...", "...dddddddddd...", BLANK, BLANK, BLANK, BLANK, BLANK]),
                 "item/soulite_upgrade_smithing_template", "靈髓升級模板：深紫色鍛造模板，中央有青色靈魂紋（物品 16x16）")
generated_item("soulite_ingot")
generated_item("soulite_upgrade_smithing_template")


def soulite_layer(leggings, seed):
    saved = dict(GEAR_COLOURS)
    GEAR_COLOURS.update(SOULITE_COLOURS)
    try:
        return armor_layer(leggings, seed)
    finally:
        GEAR_COLOURS.clear()
        GEAR_COLOURS.update(saved)


save_placeholder(soulite_layer(False, 52), "entity/equipment/humanoid/soulite", "靈髓盔甲穿著外觀（頭盔、胸甲、靴子；原版 64x32 版型）")
save_placeholder(soulite_layer(True, 53), "entity/equipment/humanoid_leggings/soulite", "靈髓護腿穿著外觀（原版 64x32 版型）")
wj(A / "equipment/soulite.json", {"layers": {"humanoid": [{"texture": "pysift:soulite"}],
                                             "humanoid_leggings": [{"texture": "pysift:soulite"}]}})

wj(D / "pysift/recipe/soulite_ingot.json", {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": [
    "minecraft:netherite_ingot", "pysift:resonant_crystal", "pysift:monarch_feather", "pysift:sculk_scale",
    "pysift:charoite", "pysift:charoite", "pysift:charoite", "pysift:charoite"], "result": {"id": "pysift:soulite_ingot"}})
wj(D / "pysift/recipe/soulite_upgrade_smithing_template.json", {   # duplicate like the netherite template
    "type": "minecraft:crafting_shaped", "category": "misc",
    "key": {"C": "pysift:charoite", "T": "pysift:soulite_upgrade_smithing_template", "S": "pysift:soul_essence"},
    "pattern": ["CTC", "CSC", "CCC"], "result": {"id": "pysift:soulite_upgrade_smithing_template", "count": 2}})

add_tag("pysift/tags/item/soulite_tool_materials.json", ["pysift:soulite_ingot"])
add_tag("pysift/tags/item/repairs_soulite_armor.json", ["pysift:soulite_ingot"])
for tag, piece in (("swords", "sword"), ("pickaxes", "pickaxe"), ("axes", "axe"), ("shovels", "shovel"), ("hoes", "hoe"),
                   ("head_armor", "helmet"), ("chest_armor", "chestplate"), ("leg_armor", "leggings"), ("foot_armor", "boots")):
    add_tag(f"minecraft/tags/item/{tag}.json", [f"pysift:soulite_{piece}"])

# the template drops from bosses (25 %)
for boss in ("harmonizer", "monarch", "sculk_monstrosity"):
    for folder in ("loot_table", "loot_tables"):
        f = D / f"pysift/{folder}/entities/{boss}.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        if not any("soulite_upgrade" in json.dumps(pool) for pool in data["pools"]):
            data["pools"].append({"rolls": 1, "condition": {"type": "minecraft:random_chance", "chance": 0.25},
                                  "entries": [{"type": "minecraft:item", "name": "pysift:soulite_upgrade_smithing_template"}]})
        wj(f, data)

adv("soulite", "awakened", "pysift:soulite_ingot", ("Beyond Netherite", "超越獄髓"), ("Forge a Soulite Ingot", "鍛造出靈髓錠"),
    {"ingot": has("pysift:soulite_ingot")}, frame="goal", xp=200)
adv("soulite_set", "soulite", "pysift:soulite_chestplate", ("Soulbound", "靈髓加身"),
    ("Wear a full set of Soulite armor", "穿上整套靈髓盔甲"),
    {piece: has(f"pysift:soulite_{piece}") for piece in ("helmet", "chestplate", "leggings", "boots")}, frame="challenge", xp=500)

SOULITE_LANG = {f"item.pysift.soulite_{k}": v for k, v in SOULITE_NAMES.items()}
SOULITE_LANG.update({
    "item.pysift.soulite_ingot": ("Soulite Ingot", "靈髓錠"),
    "item.pysift.soulite_upgrade_smithing_template": ("Soulite Upgrade", "靈髓升級模板"),
    "tag.item.pysift.soulite_tool_materials": ("Soulite Tool Materials", "靈髓工具材料"),
    "tag.item.pysift.repairs_soulite_armor": ("Repairs Soulite Armor", "可修理靈髓盔甲"),
    "tooltip.pysift.soulite_upgrade.0": ("Smithing Table: this + Netherite gear + Soulite Ingot", "鍛造台：模板欄放此模板、裝備欄放獄髓裝備、材料欄放靈髓錠"),
    "tooltip.pysift.soulite_upgrade.1": ("Upgrades it to Soulite, keeping enchantments", "升級成靈髓裝備，附魔保留"),
    "tooltip.pysift.soulite_sword": ("Every 3rd hit: sonic chain to 2 foes + Soul Deprivation", "每第 3 下命中：音波連鎖 2 個敵人並附加靈魂剝奪"),
    "tooltip.pysift.soulite_axe": ("Fully charged hits grow an exploding sculk tendril", "蓄滿力的攻擊會在目標腳下長出會爆炸的幽匿藤蔓"),
    "tooltip.pysift.soulite_digger": ("Ores have a 15% chance to drop Soul Essence", "挖礦石時 15% 額外掉落靈魂精華"),
    "tooltip.pysift.soulite_helmet": ("Enemies within 16 blocks glow", "16 格內的敵人會發光"),
    "tooltip.pysift.soulite_chestplate": ("Below 30% health: leave a decoy and gain Speed II (60 s cooldown)", "血量低於 30%：留下分身並獲得速度 II（冷卻 60 秒）"),
    "tooltip.pysift.soulite_leggings": ("Less knockback; melee attackers take 3 sculk thorn damage", "受到的擊退減少；近戰攻擊你的敵人受到 3 點幽匿荊棘傷害"),
    "tooltip.pysift.soulite_boots": ("No fall damage; walk on Spirit Liquid (sneak to sink)", "免疫摔落傷害；可在靈液上行走（蹲下會沉下去）"),
    "tooltip.pysift.soulite_set": ("Full set: immune to Soul Deprivation", "整套：免疫靈魂剝奪"),
})
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in {**SOULITE_LANG, **{k: v for k, v in ADV_LANG.items() if "soulite" in k}}.items():
        data[key] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ onboarding (SiftGuidance.java)
import re, zipfile
VANILLA_JAR = Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client.jar"

# soul compass: the vanilla compass definition, but the "no target yet" model is our own sprite
save_placeholder(blob_item([(30, 25, 55), (70, 60, 130), (120, 200, 210), (200, 250, 245)], 61, "orb"), "item/soul_compass",
                 "靈魂羅盤（未鎖定時）：深紫外框、青色靈光錶面的羅盤（物品 16x16；鎖定後暫用原版羅盤指針圖）")
wj(A / "models/item/soul_compass.json", {"parent": "minecraft:item/generated", "textures": {"layer0": "pysift:item/soul_compass"}})
compass = None
if VANILLA_JAR.exists():
    with zipfile.ZipFile(VANILLA_JAR) as jar:
        compass = json.loads(jar.read("assets/minecraft/items/compass.json"))
if compass:
    compass["model"]["on_false"] = {"type": "minecraft:model", "model": "pysift:item/soul_compass"}
    # 使用者畫好的 32 張指針圖（textures/item/soul_compass_00..31.png）存在時，鎖定後的指針也改用自己的圖
    if all((A / f"textures/item/soul_compass_{i:02d}.png").exists() for i in range(32)):
        for i in range(32):
            wj(A / f"models/item/soul_compass_{i:02d}.json",
               {"parent": "minecraft:item/generated", "textures": {"layer0": f"pysift:item/soul_compass_{i:02d}"}})
        compass = json.loads(re.sub(r'"minecraft:item/compass_(\d\d)"', r'"pysift:item/soul_compass_\1"', json.dumps(compass)))
    wj(A / "items/soul_compass.json", compass)
elif not (A / "items/soul_compass.json").exists():
    item_def("soul_compass")

save_placeholder(blob_item([(25, 20, 45), (60, 50, 110), (110, 90, 190), (150, 240, 230)], 62), "item/homeward_stone",
                 "回程符石：深紫色圓潤石頭，刻著青色的回家符文（物品 16x16）")
generated_item("homeward_stone")

shaped("soul_compass", [" C ", "CMC", " S "], {"C": "pysift:charoite", "M": "minecraft:compass", "S": "pysift:soul_essence"},
       category="misc")
wj(D / "pysift/recipe/homeward_stone.json", {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": [
    "pysift:soul_essence", "pysift:charoite", "minecraft:ender_pearl"], "result": {"id": "pysift:homeward_stone", "count": 2}})

GUIDE = [
    ("Welcome to The Sift. The violet pools are Spirit Liquid: touching it drains your health and gives Soul Deprivation. "
     "Cure it with a Soul Antidote (crafting table).",
     "歡迎來到篩靈界。紫色的池子是靈液：碰到會抽走血量並造成「靈魂剝奪」。用靈魂解藥（工作台合成）可以解除。"),
    ("Siftite Ore hides underground (y -40 to 40). Smelt Raw Siftite into ingots for Siftite gear: "
     "the full set halves the health drained by Spirit Liquid.",
     "篩金石礦藏在地底（y -40 到 40）。粗篩金石燒成錠就能做篩金石裝備：整套穿上時，靈液抽走的血量減半。"),
    ("Charoite grows in the Violet Slate Abyss and in soul geodes deep below. It is used for compasses, "
     "homeward stones, sigils and Soulite.",
     "紫龍晶長在紫晶深板岩區，以及地底深處的靈魂晶洞。羅盤、回程符石、召喚符印與靈髓都會用到。"),
    ("Three bosses guard their arenas: the Harmonizer (Willow Grove), the Monarch (Amber Dunes) and the "
     "Sculk Monstrosity (Violet Slate Abyss). Each drops a core and a shard.",
     "三隻 Boss 守在自己的競技場：調和者（柳絮林地）、君王（琥珀沙丘）與幽匿巨怪（紫晶深板岩區）。每隻都會掉落核心與碎片。"),
    ("Want a rematch? Craft a Summoning Sigil, place a Sift Altar near an arena and use the sigil on it. "
     "The boss returns if it is not already alive.",
     "想再打一次？合成召喚符印，把篩靈祭壇放在競技場附近，拿符印對祭壇右鍵。Boss 不在場時就會重新出現。"),
    ("Cores become weapons: Sonic Staff, Dash Charm and Sculk Hammer. At a smithing table, a boss shard "
     "awakens a weapon and makes it stronger.",
     "核心可以做成武器：音波法杖、衝刺護符、幽匿重錘。在鍛造台用 Boss 碎片可以「覺醒」武器，讓它變得更強。"),
    ("Inlay a Sift Beacon gem into a chestplate at the smithing table. While worn, players within 8 blocks "
     "are immune to Soul Deprivation.",
     "在鍛造台把篩靈信標寶石鑲進胸甲。穿著時，8 格內的玩家都會免疫靈魂剝奪。"),
    ("Soulite is stronger than netherite. Forge a Soulite Ingot, then upgrade netherite gear with the Soulite "
     "Upgrade template (dropped by bosses and found in ruins).",
     "靈髓比獄髓更強。先合成靈髓錠，再用靈髓升級模板（Boss 掉落、遺跡箱子）把獄髓裝備升級。"),
    ("Each Soulite piece carries a boss ability, and the full set makes you immune to Soul Deprivation. "
     "Soulite boots let you walk on Spirit Liquid.",
     "每件靈髓裝備都帶有 Boss 的能力，整套穿上會免疫靈魂剝奪。靈髓靴子可以在靈液上行走。"),
    ("Lost? The Soul Compass points to arenas and ruins (sneak + use to switch). Hold a Homeward Stone for "
     "3 seconds to return to your overworld spawn.",
     "迷路了？靈魂羅盤會指向競技場與遺跡（蹲下右鍵切換）。按住回程符石 3 秒，就能回到主世界的重生點。"),
    ("Soul Berries grow beside Spirit Liquid; Gloomcaps glow in caves. Brew them in Awkward Potions for Soul Ward and "
     "Echo Sight. Tame a Blub with a Soul Crystal Block: it fights and fetches.",
     "靈莓長在靈液旁，幽光菇長在洞穴。把它們加進粗製藥水，可以釀出靈魂守護與回音視界。拿靈魂晶塊餵布魯布就有機會馴服牠，馴服後牠會幫你打架、撿東西。"),
    ("The eight jukeboxes at the Ancient City are the key: break one and that portal closes. To open a portal from here, "
     "build a closed frame of Soul Crystal blocks and use an Echo Shard on it.",
     "遠古城市那 8 個共鳴唱片盒就是門的鑰匙：打破任一個，那道門就會關閉。想從這裡開一道回去的門，用靈魂晶塊蓋一個封閉框架，再拿迴音碎片右鍵框架。"),
]
GUIDE_LANG = {f"book.pysift.guide.page{i + 1}": page for i, page in enumerate(GUIDE)}
GUIDE_LANG.update({
    "book.pysift.guide.title": ("Sift Guidebook", "篩靈指南書"),
    "message.pysift.guide.received": ("You received the Sift Guidebook. Read it to survive The Sift!",
                                      "你獲得了《篩靈指南書》，讀一讀，才能在篩靈界活下去！"),
    "item.pysift.soul_compass": ("Soul Compass", "靈魂羅盤"),
    "item.pysift.homeward_stone": ("Homeward Stone", "回程符石"),
    "tooltip.pysift.soul_compass.0": ("Use in The Sift to point at the target", "在篩靈界右鍵：指針指向目標"),
    "tooltip.pysift.soul_compass.1": ("Sneak + use: switch target (Harmonizer → Monarch → Sculk Monstrosity → Ruins) and lock on", "蹲下右鍵：切換目標（調和者 → 君王 → 幽匿巨怪 → 遺跡）並立刻鎖定"),
    "tooltip.pysift.homeward_stone": ("Hold use for 3 s in The Sift: return to your overworld spawn",
                                      "在篩靈界按住右鍵 3 秒：傳送回主世界的重生點"),
    "message.pysift.compass.mode": ("Target: %s", "目標：%s"),
    "message.pysift.compass.ruins": ("Nearest ruins", "最近的遺跡"),
    "message.pysift.compass.found": ("%s: %s blocks away", "%s：距離 %s 格"),
    "message.pysift.compass.biome": ("%s: arena not found yet, pointing at its biome (%s blocks)",
                                     "%s：還沒發現競技場，先指向它所在的生態域（%s 格）"),
    "message.pysift.compass.not_found": ("%s: nothing found nearby", "%s：附近找不到"),
    "message.pysift.compass.wrong_dimension": ("The needle only stirs in The Sift", "指針只會在篩靈界轉動"),
    "message.pysift.homeward.wrong_dimension": ("The stone only works in The Sift", "符石只在篩靈界有效"),
})
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in GUIDE_LANG.items():
        data[key] = names[i]
    wj(f, data)

# the guidebook can also be crafted (book + charoite)
wj(D / "pysift/recipe/sift_guidebook.json", {"type": "minecraft:crafting_shapeless", "category": "misc",
    "ingredients": ["minecraft:book", "pysift:charoite"], "result": {"id": "minecraft:written_book", "components": {
        "minecraft:custom_name": {"translate": "book.pysift.guide.title", "color": "light_purple"},
        "minecraft:written_book_content": {"title": "Sift Guide", "author": "PrYuan05", "resolved": True,
                                           "pages": [{"translate": k} for k in GUIDE_LANG if ".page" in k]}}}})

wj(D / "pysift/tags/worldgen/structure/soul_compass_targets.json", {"values": [
    "pysift:strata_shrine", "pysift:abyss_obelisk", "pysift:willow_hut", "pysift:dune_tomb"]})

adv("soul_compass", "root", "pysift:soul_compass", ("Needle of Souls", "靈魂指針"),
    ("Craft a Soul Compass", "合成靈魂羅盤"), {"compass": has("pysift:soul_compass")})
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in ADV_LANG.items():
        if "soul_compass" in key:
            data[key] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ farming & brewing (SiftFarming.java)
BERRY = [(30, 60, 70), (60, 140, 150), (130, 235, 225), (220, 255, 250)]
LEAF = [(25, 45, 40), (45, 85, 70), (75, 130, 105)]
GLOOM = [(30, 30, 60), (60, 70, 140), (90, 200, 220), (200, 255, 250)]


def bush_sprite(stage, seed):
    """A small round bush; berries appear from stage 2 (soul berries glow cyan)."""
    rnd = random.Random(seed)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    radius = (3.5, 5.5, 7.0, 7.5)[stage]
    cy = 16 - radius
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) / radius) ** 2 + ((y - cy) / radius) ** 2 + rnd.uniform(-0.15, 0.15)
            if d < 1.0:
                px[x, y] = LEAF[min(2, int((1 - d) * 3 + rnd.uniform(-0.6, 0.6)) % 3)] + (255,)
    if stage >= 2:
        for _ in range(4 if stage == 2 else 9):
            x, y = rnd.randint(3, 12), rnd.randint(int(cy - radius + 3), 14)
            if px[x, y][3]:
                px[x, y] = BERRY[2 if stage == 2 else 3] + (255,)
                if x + 1 < 16 and px[x + 1, y][3]:
                    px[x + 1, y] = BERRY[1] + (255,)
    return img


def mushroom_sprite(colours, seed):
    rnd = random.Random(seed)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for y in range(11, 16):                                  # stem
        for x in (7, 8):
            px[x, y] = (170, 175, 190, 255)
    for y in range(5, 11):                                   # cap
        half = 2 + (y - 5)
        for x in range(8 - half, 8 + half):
            if 0 <= x < 16:
                k = 0 if y == 10 else 1 if y > 7 else 2
                if rnd.random() < 0.15:
                    k = 3                                    # glowing spots
                px[x, y] = colours[k] + (255,)
    return img


def effect_icon(colours, seed):
    img = blob_item(colours, seed, "orb").resize((18, 18), Image.NEAREST)
    return img


for stage in range(4):
    save_placeholder(bush_sprite(stage, 70 + stage), f"block/vegetation/soul_berry_bush/soul_berry_bush_stage{stage}",
                     f"靈莓叢第 {stage} 階：深綠色小灌木{'，掛著發光的青色莓果' if stage >= 2 else ''}（十字模型 16x16，透明背景）")
    wj(A / f"models/block/vegetation/soul_berry_bush/soul_berry_bush_stage{stage}.json", {
        "parent": "minecraft:block/cross", "render_type": "cutout",
        "textures": {"cross": f"pysift:block/vegetation/soul_berry_bush/soul_berry_bush_stage{stage}"}})
wj(A / "blockstates/soul_berry_bush.json", {"variants": {
    f"age={a}": {"model": f"pysift:block/vegetation/soul_berry_bush/soul_berry_bush_stage{a}"} for a in range(4)}})
save_placeholder(blob_item(BERRY, 74), "item/soul_berries", "靈莓：一小串發光的青色莓果（物品 16x16）")
generated_item("soul_berries")

save_placeholder(mushroom_sprite(GLOOM, 75), "block/vegetation/gloomcap/gloomcap", "幽光菇：深藍紫色菇傘、帶青色發光斑點的小菇（十字模型 16x16）")
wj(A / "blockstates/gloomcap.json", {"variants": {"": {"model": "pysift:block/vegetation/gloomcap/gloomcap"}}})
wj(A / "models/block/vegetation/gloomcap/gloomcap.json", {"parent": "minecraft:block/cross", "render_type": "cutout",
                                                  "textures": {"cross": "pysift:block/vegetation/gloomcap/gloomcap"}})
generated_item("gloomcap", "pysift:block/vegetation/gloomcap/gloomcap")
save_placeholder(blob_item([(60, 40, 30), (110, 80, 60), (80, 90, 170), (120, 220, 230)], 76), "item/gloomcap_stew",
                 "幽光菇燉湯：木碗裝著藍紫色、帶青色光點的湯（物品 16x16）")
generated_item("gloomcap_stew")

save_placeholder(effect_icon([(20, 70, 80), (60, 170, 170), (130, 235, 225), (230, 255, 250)], 77), "mob_effect/soul_ward",
                 "靈魂守護效果圖示：青色護盾形的靈魂（18x18）")
save_placeholder(effect_icon([(10, 50, 60), (30, 130, 150), (40, 220, 235), (200, 255, 255)], 78), "mob_effect/echo_sight",
                 "回音視界效果圖示：青色的伏聆感測波紋（18x18）")

# loot: the bush drops 1 berry (+1~2 when ripe), the gloomcap drops itself
loot("blocks/soul_berry_bush", [
    {"rolls": 1, "entries": [{"type": "minecraft:item", "name": "pysift:soul_berries"}]},
    {"rolls": 1, "condition": {"type": "minecraft:match_block", "blocks": "pysift:soul_berry_bush", "state": {"age": "3"}},
     "entries": [{"type": "minecraft:item", "name": "pysift:soul_berries", "modifier": {
         "type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 1, "max": 2}}}]}])
loot("blocks/gloomcap", [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": "pysift:gloomcap"}]}])

wj(D / "pysift/recipe/gloomcap_stew.json", {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": [
    "minecraft:bowl", "pysift:gloomcap", "pysift:gloomcap", "pysift:soul_berries"], "result": {"id": "pysift:gloomcap_stew"}})

# brewing (26.3 brewing recipes are data): awkward + reagent, redstone = long, gunpowder = splash, dragon's breath = lingering
for f in (D / "pysift/recipe").glob("brewing_*.json"):
    f.unlink()


def brew(container, base, reagent, result, out_container=None):
    out_container = out_container or container
    name = f"brewing_{out_container}_{result.split(':')[1]}_from_{base.split(':')[1]}_{reagent.split(':')[1]}"
    wj(D / f"pysift/recipe/{name}.json", {"type": "minecraft:brewing",
        "input": {"item": f"minecraft:{container}", "potion_contents": {"potions": base}},
        "reagent": {"item": reagent},
        "output": {"id": f"minecraft:{out_container}", "components": {"minecraft:potion_contents": {"potion": result}}}})


for potion, reagent in (("soul_ward", "pysift:soul_berries"), ("echo_sight", "pysift:gloomcap")):
    for container in ("potion", "splash_potion", "lingering_potion"):
        brew(container, "minecraft:awkward", reagent, f"pysift:{potion}")
        brew(container, f"pysift:{potion}", "minecraft:redstone", f"pysift:long_{potion}")
    for variant in (potion, f"long_{potion}"):
        brew("potion", f"pysift:{variant}", "minecraft:gunpowder", f"pysift:{variant}", "splash_potion")
        brew("splash_potion", f"pysift:{variant}", "minecraft:dragon_breath", f"pysift:{variant}", "lingering_potion")


FARM_LANG = {
    "block.pysift.soul_berry_bush": ("Soul Berry Bush", "靈莓叢"),
    "item.pysift.soul_berries": ("Soul Berries", "靈莓"),
    "block.pysift.gloomcap": ("Gloomcap", "幽光菇"),
    "item.pysift.gloomcap": ("Gloomcap", "幽光菇"),
    "item.pysift.gloomcap_stew": ("Gloomcap Stew", "幽光菇燉湯"),
    "effect.pysift.soul_ward": ("Soul Ward", "靈魂守護"),
    "effect.pysift.echo_sight": ("Echo Sight", "回音視界"),
}
for potion, (en, zh) in (("soul_ward", ("Soul Ward", "靈魂守護")), ("echo_sight", ("Echo Sight", "回音視界"))):
    FARM_LANG[f"item.minecraft.potion.effect.pysift.{potion}"] = (f"Potion of {en}", f"{zh}藥水")
    FARM_LANG[f"item.minecraft.splash_potion.effect.pysift.{potion}"] = (f"Splash Potion of {en}", f"飛濺型{zh}藥水")
    FARM_LANG[f"item.minecraft.lingering_potion.effect.pysift.{potion}"] = (f"Lingering Potion of {en}", f"滯留型{zh}藥水")
    FARM_LANG[f"item.minecraft.tipped_arrow.effect.pysift.{potion}"] = (f"Arrow of {en}", f"{zh}之箭")
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in FARM_LANG.items():
        data[key] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ altar feedback (SiftAltarBlock.java)
ALTAR_LANG = {
    "message.pysift.altar.no_arena": ("The altar must stand within 48 blocks of a boss arena", "祭壇必須放在 Boss 競技場中心 48 格內"),
    "message.pysift.altar.boss_alive": ("%s is still alive near this arena - defeat it first",
                                        "%s 還活在這座競技場附近，先打倒牠才能再召喚"),
    "message.pysift.altar.linked": ("The altar resonates with the arena of %s. Use a Summoning Sigil on it.",
                                    "祭壇與 %s 的競技場產生共鳴。手持召喚印記對祭壇右鍵即可召喚。"),
    "message.pysift.altar.too_far": ("No arena in range. The nearest is %s's arena, %s. Place the altar within %s blocks of its centre.",
                                     "附近沒有競技場。最近的是 %s 的競技場，%s。請把祭壇放在競技場中心 %s 格內。"),
    "message.pysift.altar.no_arena_found": ("No boss arena has been discovered in The Sift yet. Explore to find one first.",
                                            "篩靈界還沒有發現任何 Boss 競技場，先去探索找到一座吧。"),
    "message.pysift.altar.dir.north": ("%s blocks north", "往北 %s 格"),
    "message.pysift.altar.dir.south": ("%s blocks south", "往南 %s 格"),
    "message.pysift.altar.dir.east": ("%s blocks east", "往東 %s 格"),
    "message.pysift.altar.dir.west": ("%s blocks west", "往西 %s 格"),
    "message.pysift.altar.dir.northeast": ("%s blocks north-east", "往東北 %s 格"),
    "message.pysift.altar.dir.northwest": ("%s blocks north-west", "往西北 %s 格"),
    "message.pysift.altar.dir.southeast": ("%s blocks south-east", "往東南 %s 格"),
    "message.pysift.altar.dir.southwest": ("%s blocks south-west", "往西南 %s 格"),
    "message.pysift.altar.dir.here": ("%s blocks above or below", "就在正上方或正下方 %s 格"),
}
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in ALTAR_LANG.items():
        data[key] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ eight-song portal ritual (SiftPortalRitual.java)
wj(A / "blockstates/resonant_jukebox.json", {"variants": {"": {"model": "pysift:block/ritual/resonant_jukebox"}}})
# the block itself is drawn by ResonantJukeboxRenderer; this model only gives the break particles
wj(A / "models/block/ritual/resonant_jukebox.json", {"textures": {"particle": "minecraft:block/jukebox_side"}})
loot("blocks/resonant_jukebox", [])                                                                 # only the disc drops
add_tag("minecraft/tags/block/mineable/axe.json", ["pysift:resonant_jukebox"])
adv("eight_songs", None, "minecraft:music_disc_5", ("Eight Songs", "八音共鳴"),
    ("Fill the eight Resonant Jukeboxes and open the way to The Sift", "放滿 8 個共鳴唱片盒，開啟通往篩靈界的門"),
    {"opened": {"trigger": "minecraft:impossible"}}, frame="goal", background="minecraft:gui/advancements/backgrounds/end")
# the progression tree starts here now: "The Sift" (entering) hangs under it
data = json.loads((ADV / "root.json").read_text(encoding="utf-8"))
data["parent"] = "pysift:progression/eight_songs"
data["display"].pop("background", None)
wj(ADV / "root.json", data)

RITUAL_LANG = {
    "block.pysift.resonant_jukebox": ("Resonant Jukebox", "共鳴唱片盒"),
    "message.pysift.ritual.wrong_disc": ("This jukebox is waiting for another song...", "這個唱片盒在等待另一首歌……"),
    "message.pysift.ritual.wants": ("This jukebox is waiting for %s", "這個唱片盒在等待「%s」"),
    "message.pysift.ritual.disc_used": ("Another jukebox is already playing that song", "另一個唱片盒已經在放這首歌了"),
    "message.pysift.ritual.progress": ("%s / %s songs resonate", "%s / %s 首歌產生共鳴"),
    "message.pysift.ritual.already": ("The jukeboxes are already in place - fill them with the eight songs",
                                      "唱片盒都已經擺好了，把 8 首歌放進去吧"),
    "message.pysift.ritual.busy": ("The Echo Golems are still at work", "迴音傀儡還在忙"),
    "message.pysift.ritual.opened": ("The eight songs resonate - the way to The Sift is open!", "八首歌共鳴，通往篩靈界的門開啟了！"),
    "message.pysift.ritual.closed": ("A jukebox fell silent - the portal to The Sift closes", "一個唱片盒靜了下來，通往篩靈界的門關閉了"),
    "message.pysift.ritual.no_crystal_frame": ("Build a closed frame of Soul Crystal blocks first", "先用靈魂晶塊蓋一個封閉的框架"),
}
for key, names in ADV_LANG.items():
    if "eight_songs" in key:
        RITUAL_LANG[key] = names
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in RITUAL_LANG.items():
        data[key] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ night-glow flora (SiftFlora.java)
def blades(colours, seed, height, count):
    """Grass blades on a cross texture (transparent background), dark at the root, light at the tip."""
    rnd = random.Random(seed)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for _ in range(count):
        x = rnd.randint(1, 14)
        h = rnd.randint(height - 4, height)
        lean = rnd.choice((-1, 0, 0, 1))
        for i in range(h):
            y = 15 - i
            xx = min(15, max(0, x + (lean if i > h * 0.6 else 0)))
            k = min(len(colours) - 1, i * len(colours) // max(1, h))
            px[xx, y] = colours[k] + (255,)
    return img


def glow_dots(base, colour, seed, count):
    """Only the glowing points (on top of the blade tips of `base`) -> drawn with light_emission 15."""
    rnd = random.Random(seed)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    bp, px = base.load(), img.load()
    spots = [(x, y) for x in range(16) for y in range(16) if bp[x, y][3] and (y == 0 or not bp[x, y - 1][3])]
    for x, y in rnd.sample(spots, min(count, len(spots))):
        px[x, y] = colour + (255,)
    return img


def shrub(colours, seed):
    rnd = random.Random(seed)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for y in range(3, 16):
        for x in range(16):
            r = ((x - 7.5) / 7.0) ** 2 + ((y - 9.5) / 6.5) ** 2 + rnd.uniform(-0.2, 0.2)
            if r < 1.0:
                px[x, y] = colours[min(len(colours) - 1, int((1 - r) * len(colours)))] + (255,)
    return img


def glow_cross_model(name, cross=None):
    """Cross model with a second, emissive cross for the glowing dots (no z-fighting: the glow planes sit 0.01 in front)."""
    def plane(texture, z_or_x, emissive, axis):
        if axis == "z":
            el = {"from": [0.8, 0, z_or_x], "to": [15.2, 16, z_or_x], "rotation": {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True},
                  "shade": False, "faces": {"north": {"uv": [0, 0, 16, 16], "texture": texture}, "south": {"uv": [0, 0, 16, 16], "texture": texture}}}
        else:
            el = {"from": [z_or_x, 0, 0.8], "to": [z_or_x, 16, 15.2], "rotation": {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True},
                  "shade": False, "faces": {"east": {"uv": [0, 0, 16, 16], "texture": texture}, "west": {"uv": [0, 0, 16, 16], "texture": texture}}}
        if emissive:
            el["light_emission"] = 15
        return el
    wj(A / f"models/block/vegetation/{name}/{name}.json", {
        "ambientocclusion": False, "render_type": "cutout",
        "textures": {"particle": cross or f"pysift:block/vegetation/{name}/{name}", "cross": cross or f"pysift:block/vegetation/{name}/{name}",
                     "glow": f"pysift:block/vegetation/{name}/{name}_glow"},
        "elements": [plane("#cross", 8, False, "z"), plane("#cross", 8, False, "x"),
                     plane("#glow", 8.01, True, "z"), plane("#glow", 8.01, True, "x")]})
    wj(A / f"blockstates/{name}.json", {"variants": {"": {"model": f"pysift:block/vegetation/{name}/{name}"}}})
    generated_item(name, cross or f"pysift:block/vegetation/{name}/{name}")


GLOW_TEAL = [(20, 60, 60), (30, 100, 95), (50, 150, 135), (90, 200, 180)]
FLORA = {
    "glowshade_short_grass": (blades(GLOW_TEAL, 81, 9, 7), (150, 255, 245), 6,
                        "夜光短草（草葉用幽匿草貼圖）：青綠色短草葉，葉尖有青白色的發光點（十字模型；另一張 _glow 只畫發光點）"),
    "glowshade_tuft": (blades(GLOW_TEAL, 82, 15, 9), (150, 255, 245), 9,
                       "夜光草叢：較高的青綠色草叢，葉尖發光（十字模型；_glow 只畫發光點）"),
}
# 夜光短草：草葉沿用幽匿草（sift_vegetation_assets 的 sculk_grass.png，使用者決定合併），只產生對齊它的發光層
FLORA_CROSS = {"glowshade_short_grass": "block/vegetation/glowshade_short_grass/sculk_grass"}
for name, (base, dot, n, desc) in FLORA.items():
    cross = FLORA_CROSS.get(name)
    if cross:
        base = Image.open(A / f"textures/{cross}.png").convert("RGBA")
    else:
        save_placeholder(base, f"block/vegetation/{name}/{name}", desc)
    save_placeholder(glow_dots(base, dot, sum(map(ord, name)), n), f"block/vegetation/{name}/{name}_glow", desc + "（發光層）")
    glow_cross_model(name, cross and f"pysift:{cross}")
    loot(f"blocks/{name}", [{"rolls": 1, "condition": {"type": "minecraft:match_tool", "predicate": {"items": "minecraft:shears"}},
                              "entries": [{"type": "minecraft:item", "name": f"pysift:{name}"}]}])

FLORA_LANG = {
    "block.pysift.glowshade_short_grass": ("Glowshade Short Grass", "夜光短草"),
    "block.pysift.glowshade_tuft": ("Glowshade Tuft", "夜光草叢"),
}
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in FLORA_LANG.items():
        data[key] = names[i]
        data[key.replace("block.", "item.", 1)] = names[i]
    wj(f, data)


# ------------------------------------------------------------------ bookkeeping
STATE.write_text(json.dumps(placeholder_hashes, indent=1, sort_keys=True) + "\n", encoding="utf-8")
req = ["# 第 1 階段待繪製的貼圖", "",
       "目前是 tools/progression/build_progression.py 畫的臨時圖；直接用同名檔案覆蓋即可，腳本重跑不會蓋掉你的圖。", "",
       "| 檔案 | 內容 |", "| :-- | :-- |"] + [f"| `assets/pysift/{p}` | {d} |" for p, d in ART_REQUESTS]
(P / "art_requests").mkdir(exist_ok=True)
(P / "art_requests/progression.md").write_text("\n".join(req) + "\n", encoding="utf-8")
print(f"progression resources: {len(ART_REQUESTS)} textures, {len(MOB_DROPS)} mob loot tables")
