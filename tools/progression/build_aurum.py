"""Aurum material line (progression/AurumGear.java): raw aurum, ingot, nugget, five tools and three foods, plus the aurum
ore's new loot (raw aurum by richness, silk touch keeps the ore and its richness).
Usage: python -I tools/progression/build_aurum.py <project>

Textures (texture skill, method C): the vanilla gold item of the same kind is the structure; its gold pixels (sweet
berries: its red berries) take the aurum ramp by luminance rank, sticks / leaves / stems keep their vanilla colours.
The ramp is the aurum ore's ochre gold (hue ~40), stretched to item contrast and hue-shifted (dark -> red-brown, light ->
pale warm), so it reads apart from vanilla's lemon gold. Textures are only ADDED (art_guard.save on files that do not exist
yet; user, 2026-10-31: existing textures are frozen). Lang is merged, tags appended.
Preview: build/previews/aurum_items.png
"""
import colorsys, io, json, sys, zipfile
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(P / "tools"))
import art_guard

A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
JAR = next((P / ".gradle/loom-cache/minecraftMaven/net/minecraft").glob("minecraft-clientOnly-*/26.3/*.jar"))
VANILLA = zipfile.ZipFile(JAR)

# dark -> light: cool red-brown shadows, ochre-gold body (the ore's own hue), pale warm highlights; no pure black / white
# (6 steps, value 24 / 48 / 68 / 79 / 89 / 97 %: >= 8 % apart so the icon stays crisp)
AURUM = [(0x3D, 0x1C, 0x1A), (0x7A, 0x3E, 0x2A), (0xAE, 0x6C, 0x38), (0xCA, 0x8E, 0x44), (0xE2, 0xB8, 0x62), (0xF8, 0xEB, 0xC0)]
TOOLS = ("sword", "pickaxe", "axe", "shovel", "hoe")
# item -> (vanilla structure, which pixels take the ramp)
# vanilla gold incl. its deep orange-brown outline (hue 15-30) and the white glints of the golden tools
GOLD = lambda h, s, v: (15 <= h <= 70 and s > 0.25) or (s < 0.16 and v > 0.85)
RED = lambda h, s, v: (h < 20 or h > 330) and s > 0.3      # sweet berries' fruit
ITEMS = {"raw_aurum": ("raw_gold", GOLD), "aurum_ingot": ("gold_ingot", GOLD), "aurum_nugget": ("gold_nugget", GOLD),
         **{f"aurum_{t}": (f"golden_{t}", GOLD) for t in TOOLS},
         "aurum_apple": ("golden_apple", GOLD), "aurum_carrot": ("golden_carrot", GOLD), "aurum_berries": ("sweet_berries", RED)}
LANG = {"raw_aurum": ("Raw Aurum", "粗金岩"), "aurum_ingot": ("Aurum Ingot", "金岩錠"), "aurum_nugget": ("Aurum Nugget", "金岩粒"),
        "aurum_sword": ("Aurum Sword", "金岩劍"), "aurum_pickaxe": ("Aurum Pickaxe", "金岩鎬"), "aurum_axe": ("Aurum Axe", "金岩斧"),
        "aurum_shovel": ("Aurum Shovel", "金岩鏟"), "aurum_hoe": ("Aurum Hoe", "金岩鋤"),
        "aurum_apple": ("Aurum Apple", "金岩蘋果"), "aurum_carrot": ("Aurum Carrot", "金岩胡蘿蔔"),
        "aurum_berries": ("Aurum Berries", "金岩莓果")}


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def recolour(src, pick):
    img = Image.open(io.BytesIO(VANILLA.read(f"assets/minecraft/textures/item/{src}.png"))).convert("RGBA")
    hsv = lambda p: (lambda h, s, v: (h * 360, s, v))(*colorsys.rgb_to_hsv(*(c / 255 for c in p[:3])))
    take = lambda p: p[3] and (pick is None or pick(*hsv(p)))
    order = sorted({p[:3] for p in img.get_flattened_data() if take(p)}, key=lum)
    to = {c: AURUM[round(i * (len(AURUM) - 1) / max(1, len(order) - 1))] for i, c in enumerate(order)}
    out = img.copy()
    out.putdata([(*to[p[:3]], p[3]) if take(p) else p for p in img.get_flattened_data()])
    return out


def add_tag(path, values):
    f = D / path
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"replace": False, "values": []}
    data["values"] += [v for v in values if v not in data["values"]]
    wj(f, data)


def recipe(name, obj):
    wj(D / f"pysift/recipe/{name}.json", obj)


def shaped(name, pattern, key, result=None, category="equipment"):
    recipe(name, {"type": "minecraft:crafting_shaped", "category": category, "key": key, "pattern": pattern,
                  "result": {"id": f"pysift:{result or name}"}})


def main():
    imgs = {n: recolour(src, pick) for n, (src, pick) in ITEMS.items()}
    sheet = Image.new("RGBA", (len(imgs) * 72 + 8, 80), (30, 30, 36, 255))
    for i, img in enumerate(imgs.values()):
        sheet.alpha_composite(img.resize((64, 64), Image.NEAREST), (8 + i * 72, 8))
    sheet.convert("RGB").save(P / "build/previews/aurum_items.png")
    tmp = P / "build/previews/aurum_items"
    tmp.mkdir(parents=True, exist_ok=True)
    for n, img in imgs.items():
        img.save(tmp / f"{n}.png")
    print("preview: build/previews/aurum_items.png")
    if "--apply" not in sys.argv:
        return

    for n, img in imgs.items():
        dst = A / f"textures/item/{n}.png"
        if dst.exists() and not art_guard.is_ours(dst):        # someone drew it by hand: keep theirs
            print("  kept (edited by hand):", dst.relative_to(P))
        else:
            art_guard.save(img, dst)
        parent = "minecraft:item/handheld" if n.split("_")[-1] in TOOLS else "minecraft:item/generated"
        wj(A / f"models/item/{n}.json", {"parent": parent, "textures": {"layer0": f"pysift:item/{n}"}})
        wj(A / f"items/{n}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{n}"}})

    # aurum ore: raw aurum, more the richer the ore (richness 4 is solid ore); silk touch keeps the ore and its richness
    counts = {0: (1, 2), 1: (1, 3), 2: (2, 4), 3: (3, 5), 4: (4, 7)}
    # 26.3 loot syntax (vanilla gold_ore / beetroots): "condition" / "modifier" objects with a "type"
    raw = [{"type": "minecraft:item", "name": "pysift:raw_aurum",
            "condition": {"type": "minecraft:match_block", "blocks": "pysift:aurum_ore", "state": {"richness": str(r)}},
            "modifier": [{"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}},
                         {"type": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
                         {"type": "minecraft:explosion_decay"}]} for r, (lo, hi) in counts.items()]
    loot = {"type": "minecraft:block", "random_sequence": "pysift:blocks/aurum_ore", "pools": [{"rolls": 1, "entries": [{
        "type": "minecraft:alternatives", "children": [
            {"type": "minecraft:item", "name": "pysift:aurum_ore", "condition": "minecraft:tool/can_silk_touch",
             "modifier": [{"type": "minecraft:copy_state", "block": "pysift:aurum_ore", "properties": ["richness"]}]},
            *raw]}]}]}
    for folder in ("loot_table", "loot_tables"):
        wj(D / f"pysift/{folder}/blocks/aurum_ore.json", loot)

    # smelting, 9 nuggets <-> 1 ingot
    for src in ("raw_aurum", "aurum_ore"):
        for kind, time in (("smelting", 200), ("blasting", 100)):
            recipe(f"aurum_ingot_from_{kind}_{src}", {"type": f"minecraft:{kind}", "category": "misc",
                                                      "ingredient": f"pysift:{src}", "result": {"id": "pysift:aurum_ingot"},
                                                      "experience": 0.7, "cookingtime": time})
    recipe("aurum_ingot_from_nuggets", {"type": "minecraft:crafting_shaped", "category": "misc", "key": {"#": "pysift:aurum_nugget"},
                                        "pattern": ["###", "###", "###"], "result": {"id": "pysift:aurum_ingot"}})
    recipe("aurum_nugget", {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": ["pysift:aurum_ingot"],
                            "result": {"id": "pysift:aurum_nugget", "count": 9}})

    # tools
    I_S = {"I": "#pysift:aurum_tool_materials", "S": "minecraft:stick"}
    for t, pattern in (("sword", [" I ", " I ", " S "]), ("pickaxe", ["III", " S ", " S "]), ("axe", ["II", "IS", " S"]),
                       ("shovel", ["I", "S", "S"]), ("hoe", ["II", " S", " S"])):
        shaped(f"aurum_{t}", pattern, I_S)
        add_tag(f"minecraft/tags/item/{t}s.json", [f"pysift:aurum_{t}"])
    add_tag("pysift/tags/item/aurum_tool_materials.json", ["pysift:aurum_ingot"])

    # foods, like vanilla's golden apple / golden carrot; berries take 4 nuggets round them
    shaped("aurum_apple", ["III", "IAI", "III"], {"I": "pysift:aurum_ingot", "A": "minecraft:apple"}, category="misc")
    shaped("aurum_carrot", ["NNN", "NCN", "NNN"], {"N": "pysift:aurum_nugget", "C": "minecraft:carrot"}, category="misc")
    shaped("aurum_berries", [" N ", "NBN", " N "], {"N": "pysift:aurum_nugget", "B": "minecraft:sweet_berries"}, category="misc")

    for lang, i in (("en_us", 0), ("zh_tw", 1)):
        f = A / f"lang/{lang}.json"
        data = json.loads(f.read_text(encoding="utf-8"))
        for key, names in LANG.items():
            data[f"item.pysift.{key}"] = names[i]
        wj(f, data)
    print("applied")


if __name__ == "__main__":
    main()
