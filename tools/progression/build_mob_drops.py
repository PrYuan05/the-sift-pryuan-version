"""Resources for the mob drops (progression/MobDrops.java, v2.2): item models / definitions, names, cooking and crafting
recipes, brewing recipes and tags. Usage: python -I tools/progression/build_mob_drops.py <project>

The loot tables themselves are written by build_progression.py (MOB_DROPS), so re-running either script keeps them in
sync. Textures are hand-drawn (minecraft-texture-crafter) at textures/item/<id>.png; this script never paints any.
Brewing files use the prefix mob_brewing_ because build_progression.py deletes every brewing_*.json it finds.
"""
import json, sys, zipfile
from pathlib import Path

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
R = D / "pysift/recipe"
VANILLA_JAR = next((P / ".gradle/loom-cache/minecraftMaven/net/minecraft").glob("minecraft-common-*/26.3/*.jar"), None)


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_tag(path, values):
    f = D / path
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"replace": False, "values": []}
    data["values"] += [v for v in values if v not in data["values"]]
    wj(f, data)


# id: (English, 中文, model parent)
ITEMS = {
    "blub_gel": ("Blub Gel", "布魯布凝膠", "generated"),
    "blub_jelly": ("Blub Jelly", "布魯布果凍", "generated"),
    "raw_slabber_steak": ("Raw Slabber Steak", "生泥板獸排", "generated"),
    "cooked_slabber_steak": ("Cooked Slabber Steak", "熟泥板獸排", "generated"),
    "raw_dartback_meat": ("Raw Dartback Meat", "生飛鏢背殼肉", "generated"),
    "cooked_dartback_meat": ("Cooked Dartback Meat", "熟飛鏢背殼肉", "generated"),
    "nester_egg": ("Nester Egg", "築巢者蛋", "generated"),
    "fried_nester_egg": ("Fried Nester Egg", "煎築巢者蛋", "generated"),
    "roamroot_tuber": ("Roamroot Tuber", "漫遊根塊莖", "generated"),
    "baked_roamroot_tuber": ("Baked Roamroot Tuber", "烤漫遊根塊莖", "generated"),
    "soul_nectar": ("Soul Nectar", "靈魂花蜜", "generated"),
    "wobble_jelly": ("Wobble Jelly", "搖晃凍", "generated"),
    "sift_stew": ("Sift Stew", "隙浮燉菜", "generated"),
    "nuzzle_fluff": ("Nuzzle Fluff", "蹭蹭軟毛", "generated"),
    "bloombud_petal": ("Bloombud Petal", "花苞花瓣", "generated"),
    "dartback_spine": ("Dartback Spine", "飛鏢背棘刺", "generated"),
    "prickle_quill": ("Prickle Quill", "刺球棘", "generated"),
    "scavenger_fang": ("Scavenger Fang", "清道夫獠牙", "generated"),
    "shadow_hide": ("Shadow Hide", "暗影皮", "generated"),
    "hunter_spearhead": ("Hunter Spearhead", "標槍頭", "generated"),
    "spine_arrow": ("Spine Arrow", "棘刺箭", "generated"),
    "bleeding_arrow": ("Bleeding Arrow", "放血箭", "generated"),
    "soul_javelin": ("Soul Javelin", "靈魂標槍", "handheld"),
    "tuning_fork": ("Tuning Fork", "調音叉", "handheld"),
}
for name, (_, _, parent) in ITEMS.items():
    wj(A / f"models/item/{name}.json", {"parent": f"minecraft:item/{parent}", "textures": {"layer0": f"pysift:item/{name}"}})
    wj(A / f"items/{name}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{name}"}})

LANG = {f"item.pysift.{k}": (en, zh) for k, (en, zh, _) in ITEMS.items()}
LANG.update({
    "effect.pysift.bleeding": ("Bleeding", "流血"),
    "tooltip.pysift.soul_javelin": ("Use to throw; pick it back up where it lands", "右鍵擲出，插在哪裡就去撿回來"),
    "tooltip.pysift.tuning_fork": ("Sneak + use on a note block: remember its pitch. Use on another: tune it to that pitch",
                                   "潛行＋右鍵音符盒：記住音高；右鍵別的音符盒：調成同一個音"),
    "message.pysift.tuning_fork.stored": ("Pitch remembered: %s", "記住音高：%s"),
    "message.pysift.tuning_fork.tuned": ("Tuned to pitch %s", "已調成音高 %s"),
    "message.pysift.tuning_fork.empty": ("Sneak + use on a note block first to remember a pitch", "先潛行＋右鍵一個音符盒，記住要調的音"),
})


# ------------------------------------------------------------------ recipes
def shapeless(name, ingredients, result, count=1, category="misc"):
    wj(R / f"{name}.json", {"type": "minecraft:crafting_shapeless", "category": category, "ingredients": ingredients,
                            "result": {"count": count, "id": result} if count > 1 else {"id": result}})


def shaped(name, pattern, key, result, count=1, category="misc"):
    wj(R / f"{name}.json", {"type": "minecraft:crafting_shaped", "category": category, "key": key, "pattern": pattern,
                            "result": {"count": count, "id": result} if count > 1 else {"id": result}})


def cook(raw, cooked, xp=0.35):
    """Furnace / smoker / campfire, with vanilla's times for meat."""
    for kind, time, suffix in (("smelting", 200, ""), ("smoking", 100, "_from_smoking"), ("campfire_cooking", 600, "_from_campfire_cooking")):
        wj(R / f"{cooked}{suffix}.json", {"type": f"minecraft:{kind}", "category": "food", "cookingtime": time,
                                          "experience": xp, "ingredient": f"pysift:{raw}", "result": {"id": f"pysift:{cooked}"}})


cook("raw_slabber_steak", "cooked_slabber_steak")
cook("raw_dartback_meat", "cooked_dartback_meat")
cook("nester_egg", "fried_nester_egg")
cook("roamroot_tuber", "baked_roamroot_tuber")

shapeless("slime_ball_from_blub_gel", ["pysift:blub_gel"], "minecraft:slime_ball")
shapeless("slime_ball_from_wobble_jelly", ["pysift:wobble_jelly"], "minecraft:slime_ball")
shapeless("blub_jelly", ["pysift:blub_gel", "pysift:blub_gel", "pysift:blub_gel", "minecraft:sugar"], "pysift:blub_jelly")
shapeless("sift_stew", ["minecraft:bowl", "pysift:cooked_slabber_steak", "pysift:baked_roamroot_tuber", "pysift:gloomcap"], "pysift:sift_stew")
shaped("white_wool_from_nuzzle_fluff", ["FF", "FF"], {"F": "pysift:nuzzle_fluff"}, "minecraft:white_wool", category="building")
shaped("leather_from_shadow_hide", ["HH", "HH"], {"H": "pysift:shadow_hide"}, "minecraft:leather")
shapeless("yellow_dye_from_bloombud_petal", ["pysift:bloombud_petal"], "minecraft:yellow_dye", 2)
shaped("spine_arrow", ["X", "#", "Y"], {"X": "#pysift:arrow_spines", "#": "minecraft:stick", "Y": "minecraft:feather"},
       "pysift:spine_arrow", 4, "equipment")
shapeless("bleeding_arrow", ["pysift:scavenger_fang"] + ["minecraft:arrow"] * 4, "pysift:bleeding_arrow", 4, "equipment")
shaped("soul_javelin", ["X", "#", "#"], {"X": "pysift:hunter_spearhead", "#": "minecraft:stick"}, "pysift:soul_javelin", 1, "equipment")
shapeless("string_from_trapper_net", ["pysift:trapper_net"], "minecraft:string", 3)
# fuse powder works like gunpowder
shaped("tnt_from_fuse_powder", ["X#X", "#X#", "X#X"], {"#": ["minecraft:sand", "minecraft:red_sand"], "X": "pysift:fuse_powder"},
       "minecraft:tnt", 1, "redstone")
shapeless("firework_rocket_from_fuse_powder", ["pysift:fuse_powder", "minecraft:paper"], "minecraft:firework_rocket", 3)

# ------------------------------------------------------------------ brewing (26.3 brewing recipes are data)
for f in R.glob("mob_brewing_*.json"):
    f.unlink()


def brew(name, container, base, reagent, out_id, out_potion):
    wj(R / f"mob_brewing_{name}.json", {"type": "minecraft:brewing",
        "input": {"item": f"minecraft:{container}", "potion_contents": {"potions": base}},
        "reagent": {"item": reagent},
        "output": {"id": out_id, "components": {"minecraft:potion_contents": {"potion": out_potion}}}})


for container in ("potion", "splash_potion", "lingering_potion"):
    brew(f"{container}_regeneration_from_nuzzle_fluff", container, "minecraft:awkward", "pysift:nuzzle_fluff",
         f"minecraft:{container}", "minecraft:regeneration")
    brew(f"{container}_invisibility_from_shadow_hide", container, "minecraft:awkward", "pysift:shadow_hide",
         f"minecraft:{container}", "minecraft:invisibility")

# every "potion + gunpowder = splash potion" recipe also works with fuse powder
splash = []
if VANILLA_JAR:
    with zipfile.ZipFile(VANILLA_JAR) as jar:
        for n in jar.namelist():
            if n.startswith("data/minecraft/recipe/brewing/potion_") and n.endswith("_gunpowder.json"):
                splash.append(json.loads(jar.read(n))["input"]["potion_contents"]["potions"])
else:
    print("warning: vanilla jar not found, fuse powder splash recipes skipped for vanilla potions")
for potion in ("soul_ward", "long_soul_ward", "echo_sight", "long_echo_sight"):
    splash.append(f"pysift:{potion}")
for potion in sorted(set(splash)):
    brew(f"splash_{potion.replace(':', '_')}_from_fuse_powder", "potion", potion, "pysift:fuse_powder", "minecraft:splash_potion", potion)

# ------------------------------------------------------------------ tags
add_tag("pysift/tags/item/arrow_spines.json", ["pysift:dartback_spine", "pysift:prickle_quill"])
add_tag("minecraft/tags/item/arrows.json", ["pysift:spine_arrow", "pysift:bleeding_arrow"])   # bows and crossbows accept them
add_tag("minecraft/tags/item/eggs.json", ["pysift:nester_egg"])                              # cake
add_tag("minecraft/tags/item/meat.json", ["pysift:raw_slabber_steak", "pysift:cooked_slabber_steak",
                                          "pysift:raw_dartback_meat", "pysift:cooked_dartback_meat"])   # wolves eat it

# ------------------------------------------------------------------ lang
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_bytes().decode("utf-8-sig"))
    for k, v in LANG.items():
        data[k] = v[i]
    f.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))   # LF
print(f"mob drops: {len(ITEMS)} items, {len(splash)} fuse powder splash recipes")
