"""Vanilla dyes from The Sift's plants (user request: dyes through our plants; vanilla dye colours, so they work on wool,
glass, beds, leather... everything).
Usage: python -I tools/progression/build_dyes.py <project>
Writes data/pysift/recipe/<dye>_from_<plant>.json (shapeless, one plant -> 1 or 2 dyes, grouped with the vanilla dye
recipes) and data/pysift/advancement/recipes/misc/<same>.json (unlocks the recipe when the plant is in the inventory).
The plant -> dye map follows each plant's texture colour (measured: main hue of the saturated pixels) and its name;
tall / large plants give 2 like vanilla sunflowers and rose bushes. Plants matching one of the 9 new Sift colours make
that dye (pysift:<colour>_dye, see tools/progression/build_sift_colors.py); the others make vanilla dyes."""
import json, sys
from pathlib import Path

P = Path(sys.argv[1])
D = P / "src/main/resources/data/pysift"
A = P / "src/main/resources/assets/pysift"

DYES = {   # dye: [(plant, count)]; "pysift:" dyes are the new Sift colours (SiftColors.java), the rest are vanilla
    # new Sift colours: plants whose colour matches one take it
    "pysift:teal": [("soft_teal_short_grass", 1), ("soft_teal_tall_grass", 2), ("green_sift_vine", 1), ("cleaver_plant", 1)],
    "pysift:mint": [("rift_mint_short_grass", 1), ("rift_mint_tall_grass", 2), ("glowshade_short_grass", 1), ("glowshade_tuft", 1)],
    "pysift:coral": [("coral_leaf_carpet", 1), ("carapace_short_grass", 1)],
    "pysift:amber": [("rift_orange_short_grass", 1), ("rift_orange_tall_grass", 2), ("orange_sift_vine", 1)],
    "pysift:lavender": [("soft_violet_short_grass", 1), ("soft_violet_tall_grass", 2), ("pink_curled_fern", 1)],
    "pysift:rose": [("carapace_flower", 2), ("carapace_vine", 1), ("soft_crimson_short_grass", 1), ("soft_crimson_tall_grass", 2)],
    "pysift:soul_blue": [("soul_cleaver_plant", 1), ("soul_willow_leaves", 1)],
    "pysift:void": [("gloomcap", 1)],
    "pysift:dusk_gold": [("dusk_bloom", 1), ("clustered_yellow_flowers", 2), ("yellow_agave", 2)],
    # vanilla colours for the plants without a Sift colour of their own
    "yellow": [("yellow_leaf_litter", 1), ("soft_dune_short_grass", 1), ("soft_dune_tall_grass", 2)],
    "lime": [("yellow_flower_patch", 1)],
    "green": [("blue_giant_canopy", 2), ("olive_forked_stalk", 1)],
    "blue": [("blue_curled_fern", 1)],
    "light_gray": [("puff_grass", 1)],
    "white": [("bone_spire", 2)],
}


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# clean out dye recipes this script wrote before (a plant may have moved to another colour)
for folder in (D / "recipe", D / "advancement/recipes/misc"):
    for old in folder.glob("*_dye_from_*.json") if folder.exists() else []:
        old.unlink()
written = 0
for colour, plants in DYES.items():
    for plant, count in plants:
        assert (A / "items" / f"{plant}.json").exists(), f"pysift:{plant} has no item"
        ns, colour_id = colour.split(":") if ":" in colour else ("minecraft", colour)
        name = f"{colour_id}_dye_from_{plant}"
        result = {"id": f"{ns}:{colour_id}_dye"}
        if count > 1:
            result["count"] = count
        wj(D / f"recipe/{name}.json", {"type": "minecraft:crafting_shapeless", "group": f"{colour_id}_dye",
                                       "ingredients": [f"pysift:{plant}"], "result": result})
        wj(D / f"advancement/recipes/misc/{name}.json", {
            "parent": "minecraft:recipes/root",
            "criteria": {f"has_{plant}": {"conditions": {"items": [{"items": f"pysift:{plant}"}]},
                                          "trigger": "minecraft:inventory_changed"},
                         "has_the_recipe": {"conditions": {"recipes": f"pysift:{name}"}, "trigger": "minecraft:recipe_unlocked"}},
            "requirements": [["has_the_recipe", f"has_{plant}"]],
            "rewards": {"recipes": [f"pysift:{name}"]}})
        written += 1
print(f"{written} dye recipes for {len(DYES)} colours")
