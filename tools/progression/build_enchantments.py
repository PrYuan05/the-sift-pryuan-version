"""The Sift's enchantments: data/pysift/enchantment/*.json, their item and enchantment tags, and their names.
Usage: python -I tools/progression/build_enchantments.py <project>

Two tiers (the user's decision, 2026-11-17):
  everyday - enchanting table, villager trades and random loot (in_enchanting_table, non_treasure, tradeable,
             on_random_loot), like Sharpness;
  treasure - only in the Sift's structure chests (minecraft:treasure + pysift:sift_treasure, which the chest tables
             draw from: tools/worldgen/loot_books.py), like Mending.
Vanilla weapons and tools take them by kind through the vanilla enchantable tags, and the mod's own gear is in those
tags already. Effects that vanilla enchantment data can express are written here; the rest have no "effects" block and
are read in Java through progression/SiftEnchantments.level (hammer, staff, charm, fork, horn, javelin, armor).
The JSON shapes follow the vanilla 26.3 files named next to each one."""
import json
import sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
D = P / "src/main/resources/data"
A = P / "src/main/resources/assets/pysift"


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def add_tag(path, values):
    f = D / path
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"replace": False, "values": []}
    for v in values:
        if v not in data["values"]:
            data["values"].append(v)
    wj(f, data)


def linear(base, per):
    return {"type": "minecraft:linear", "base": base, "per_level_above_first": per}


def chance(base, per):
    return {"type": "minecraft:random_chance", "chance": {"type": "minecraft:enchantment_level", "amount": linear(base, per)}}


def on_hit(effect, seconds, per_level, odds, extra=()):
    """bane_of_arthropods.json's post_attack: the victim gets a mob effect, here with a level-based chance."""
    terms = [chance(*odds), *extra]
    return {"minecraft:post_attack": [{
        "enchanted": "attacker", "affected": "victim",
        "effect": {"type": "minecraft:apply_mob_effect", "to_apply": effect,
                   "min_duration": float(seconds), "max_duration": linear(float(seconds), float(per_level)),
                   "min_amplifier": 0.0, "max_amplifier": 0.0},
        "requirements": terms[0] if len(terms) == 1 else {"type": "minecraft:all_of", "terms": terms}}]}


PROJECTILE = {"type": "minecraft:damage_source_properties", "predicate": {"tags": [{"id": "#minecraft:is_projectile", "expected": True}]}}
NOT_PLAYER = {"type": "minecraft:inverted", "term": {"type": "minecraft:entity_properties", "entity": "this",
                                                      "predicate": {"minecraft:entity_type": "minecraft:player"}}}

# soul_speed.json's location_changed, with the block test swapped for "on the ground in the Sift"
RIFT_STEP = {"minecraft:location_changed": [{
    "effect": {"type": "minecraft:attribute", "attribute": "minecraft:movement_speed", "id": "pysift:enchantment.rift_step",
               "operation": "add_value", "amount": linear(0.01, 0.01)},
    "requirements": {"type": "minecraft:all_of", "terms": [
        {"type": "minecraft:inverted", "term": {"type": "minecraft:entity_properties", "entity": "this", "predicate": {"minecraft:vehicle": {}}}},
        {"type": "minecraft:entity_properties", "entity": "this", "predicate": {
            "minecraft:flags": {"is_flying": False}, "minecraft:location": {"dimension": "pysift:the_sift"}}},
        # like soul_speed.json: switching on needs the ground; once on, it stays on in the air (the test only runs
        # when the entity steps into a new block, often mid-stride)
        {"type": "minecraft:any_of", "terms": [
            {"type": "minecraft:enchantment_active_check", "active": True},
            {"type": "minecraft:entity_properties", "entity": "this", "predicate": {"minecraft:flags": {"is_on_ground": True}}}]}]}}]}

# silk_touch.json's block_experience, adding instead of setting
SOUL_HARVEST = {"minecraft:block_experience": [{"effect": {"type": "minecraft:add", "value": linear(1.0, 1.0)}}]}

# loyalty.json: the javelin reads the return speed from this, like the trident does
HOMECOMING = {"minecraft:trident_return_acceleration": [{"effect": {"type": "minecraft:add", "value": linear(1.0, 1.0)}}]}

#  id: (names, supported items, max level, weight, min cost, max cost, anvil, slots, tier, effects, exclusive set)
ENCH = {
    "aftershock": (("Aftershock", "餘震"), "#pysift:enchantable/sculk_hammer", 3, 5, (10, 10), (35, 10), 4, ["mainhand"], "everyday", None, None),
    "resonance": (("Resonance", "共振"), "#pysift:enchantable/sonic_staff", 3, 5, (10, 10), (35, 10), 4, ["mainhand"], "everyday", None, None),
    "hemorrhage": (("Hemorrhage", "放血"), "#pysift:enchantable/hemorrhage", 3, 2, (10, 10), (40, 10), 4, ["mainhand"], "everyday",
                   on_hit("pysift:bleeding", 3, 2, (0.15, 0.15)), None),
    "ensnare": (("Ensnare", "纏縛"), "#pysift:enchantable/ranged", 2, 2, (15, 15), (45, 15), 4, ["mainhand"], "everyday",
                on_hit("pysift:ensnared", 1, 0.75, (0.25, 0.25), [PROJECTILE]), None),
    "rift_step": (("Rift Step", "隙步"), "#minecraft:enchantable/foot_armor", 3, 2, (10, 10), (25, 10), 4, ["feet"], "everyday",
                  RIFT_STEP, "#pysift:exclusive_set/rift_step"),
    "soul_harvest": (("Soul Harvest", "靈魂收割"), "#minecraft:enchantable/mining_loot", 3, 2, (15, 9), (65, 9), 4, ["mainhand"], "everyday",
                     SOUL_HARVEST, "#pysift:exclusive_set/soul_harvest"),
    "soul_rend": (("Soul Rend", "靈魂撕裂"), "#pysift:enchantable/soul_rend", 2, 1, (20, 20), (60, 20), 8, ["mainhand"], "treasure",
                  on_hit("pysift:soul_deprivation", 4, 2, (0.10, 0.10), [NOT_PLAYER]), "#pysift:exclusive_set/soul_rend"),
    "soul_ward": (("Soul Ward", "靈魂護佑"), "#pysift:enchantable/soul_ward", 1, 1, (25, 0), (75, 0), 8, ["head", "chest"], "treasure", None, None),
    "afterimage": (("Afterimage", "殘影"), "#pysift:enchantable/dash_charm", 3, 1, (20, 15), (60, 15), 8, ["mainhand", "offhand"], "treasure", None, None),
    "harmony": (("Harmony", "和聲"), "#pysift:enchantable/tuning_fork", 3, 1, (20, 15), (60, 15), 8, ["mainhand", "offhand"], "treasure", None, None),
    "lament": (("Lament", "哀歌"), "#pysift:enchantable/mourning_horn", 3, 1, (20, 15), (60, 15), 8, ["mainhand", "offhand"], "treasure", None, None),
    "homecoming": (("Homecoming", "歸魂"), "#pysift:enchantable/javelin", 3, 1, (12, 7), (50, 0), 8, ["mainhand"], "treasure", HOMECOMING, None),
}

DESC = {
    "aftershock": ("Sculk Hammer: a wider shockwave and one more tendril per level", "幽匿重錘：每級讓蓄力震波大 0.75 格、多 1 條幽匿藤蔓"),
    "resonance": ("Sonic Staff: +3 blocks of range and +1 damage per level", "音波法杖：每級射程 +3 格、傷害 +1"),
    "hemorrhage": ("Hits may make the target bleed (15% per level)", "命中時有機率讓目標流血（每級 15%）"),
    "ensnare": ("Projectile hits may snare the target in place (25% per level)", "投射物命中時有機率把目標纏住（每級 25%）"),
    "rift_step": ("Faster on the ground in the Sift", "在隙浮的地面上移動更快"),
    "soul_harvest": ("More experience from ores and other blocks that drop it", "挖礦石等會掉經驗的方塊時，多給經驗"),
    "soul_rend": ("Hits may tear the soul out of a creature: it takes 30% more damage (10% per level; not players)", "命中時有機率撕裂生物的靈魂，讓牠多受 30% 傷害（每級 10%；對玩家無效）"),
    "soul_ward": ("Immune to Soul Deprivation", "免疫靈魂剝奪"),
    "afterimage": ("Dash Charm: dash further, a longer-lived decoy and a shorter cooldown", "衝刺護符：衝得更遠、分身留得更久、冷卻更短"),
    "harmony": ("Tuning Fork: Singers answer from further away and their Regeneration lasts longer", "調音叉：更遠的歌者也會回應，再生持續更久"),
    "lament": ("Mourning Horn: calms creatures from further away", "哀悼號角：安撫範圍更大"),
    "homecoming": ("Soul Javelin: flies back to you after it hits", "靈魂標槍：命中後飛回你手上"),
}

for eid, (names, items, top, weight, mn, mx, anvil, slots, tier, effects, exclusive) in ENCH.items():
    data = {"description": {"translate": f"enchantment.pysift.{eid}"}, "supported_items": items, "weight": weight, "max_level": top,
            "min_cost": {"base": mn[0], "per_level_above_first": mn[1]}, "max_cost": {"base": mx[0], "per_level_above_first": mx[1]},
            "anvil_cost": anvil, "slots": slots}
    if exclusive:
        data["exclusive_set"] = exclusive
    if effects:
        data["effects"] = effects
    wj(D / f"pysift/enchantment/{eid}.json", data)

# ---- item tags: which items take which enchantment (vanilla kinds through vanilla tags, the mod's items by name)
add_tag("pysift/tags/item/enchantable/hemorrhage.json", ["#minecraft:enchantable/weapon", "#minecraft:enchantable/bow",
                                                         "#minecraft:enchantable/crossbow", "pysift:soul_javelin",
                                                         "pysift:sculk_hammer", "pysift:sonic_staff"])
add_tag("pysift/tags/item/enchantable/ranged.json", ["#minecraft:enchantable/bow", "#minecraft:enchantable/crossbow",
                                                     "#minecraft:enchantable/trident", "pysift:soul_javelin"])
add_tag("pysift/tags/item/enchantable/soul_rend.json", ["#minecraft:enchantable/weapon", "pysift:sculk_hammer", "pysift:sonic_staff"])
add_tag("pysift/tags/item/enchantable/soul_ward.json", ["#minecraft:enchantable/chest_armor", "#minecraft:enchantable/head_armor"])
add_tag("pysift/tags/item/enchantable/javelin.json", ["pysift:soul_javelin"])
add_tag("pysift/tags/item/enchantable/dash_charm.json", ["pysift:dash_charm"])
add_tag("pysift/tags/item/enchantable/tuning_fork.json", ["pysift:tuning_fork"])
add_tag("pysift/tags/item/enchantable/mourning_horn.json", ["pysift:mourning_horn"])
add_tag("pysift/tags/item/enchantable/sculk_hammer.json", ["pysift:sculk_hammer"])
add_tag("pysift/tags/item/enchantable/sonic_staff.json", ["pysift:sonic_staff"])
# Unbreaking and Mending for the mod's items that wear out
add_tag("minecraft/tags/item/enchantable/durability.json", ["pysift:sculk_hammer", "pysift:sonic_staff", "pysift:dash_charm",
                                                            "pysift:mourning_horn", "pysift:tuning_fork"])

# ---- enchantment tags: the two tiers and the exclusive sets (one side is enough: vanilla checks both sets)
everyday = [f"pysift:{e}" for e, v in ENCH.items() if v[8] == "everyday"]
treasure = [f"pysift:{e}" for e, v in ENCH.items() if v[8] == "treasure"]
for tag in ("in_enchanting_table", "non_treasure", "tradeable", "on_random_loot"):
    add_tag(f"minecraft/tags/enchantment/{tag}.json", everyday)
add_tag("minecraft/tags/enchantment/treasure.json", treasure)
add_tag("pysift/tags/enchantment/sift_treasure.json", treasure)
add_tag("pysift/tags/enchantment/exclusive_set/soul_rend.json", ["minecraft:fire_aspect", "pysift:hemorrhage"])
add_tag("pysift/tags/enchantment/exclusive_set/rift_step.json", ["minecraft:soul_speed", "minecraft:depth_strider", "minecraft:frost_walker"])
add_tag("pysift/tags/enchantment/exclusive_set/soul_harvest.json", ["minecraft:silk_touch"])

# ---- names (the lang files keep LF line endings)
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for eid, v in ENCH.items():
        data[f"enchantment.pysift.{eid}"] = v[0][i]
        data[f"enchantment.pysift.{eid}.desc"] = DESC[eid][i]
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

print(f"{len(ENCH)} enchantments: everyday {', '.join(everyday)}; treasure {', '.join(treasure)}")
