"""Generate The Sift dimension datapack files (Minecraft 26.3 formats).
Usage: python -I tools/worldgen/build_the_sift.py <project> <vanilla_overworld_noise_settings.json>
Writes data/pysift/{dimension_type,dimension,worldgen/{biome,noise_settings,material_rule}}.
Block ids are checked against the registered blockstates before anything is written."""
import json, re, sys
from pathlib import Path

P = Path(sys.argv[1]); VANILLA_NOISE = Path(sys.argv[2])
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data/pysift"


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def state(block, **props):
    bid = f"pysift:{block}"
    assert (A / "blockstates" / f"{block}.json").exists(), f"unknown block {bid}"
    return {"id": bid, "properties": {k: str(v) for k, v in props.items()}} if props else bid


# ---- blocks used by the surface rules (verified against registered blockstates) ----
BASE = state("void_stone", tone="dark")                                   # cleanest dark stone (surface_candidates.py)
CRIMSON_TOP = state("canyon_capped_crimson_strata", facing="up")     # user choice; facing block, top face up
CRIMSON_UNDER = state("silted_strata", silt=0)                           # user choice: only silt=0 under the cap
VIOLET_TOP, VIOLET_UNDER = state("violet_capped_dark_slate", facing="up"), state("dark_slate", fade=0)   # user choice
GROVE_TOP = state("grove_capped_crimson_strata", facing="up")         # user choice (no more pink loam)
GROVE_UNDER = state("abyssal_strata", depth=0)
DUNE_SAND, DUNE_ACCENT = state("amber_sand"), state("pale_sand")          # ~70 / 30 by surface noise
DUNE_STONE, DUNE_DEEP = state("bleached_sandstone", bleach=0), state("cracked_sandstone", crack=0)

# start from a clean slate so removed biomes / features leave no orphan JSON behind.
# This also removes the landmark features written by tools/worldgen/build_landmarks.py: run that one after this script.
for sub in ("biome", "feature", "placed_feature"):
    for old in (D / "worldgen" / sub).glob("*.json"):
        old.unlink()

# ---- fog (user: less fog, paler colours) ----
FOG_START, FOG_END = 48.0, 224.0   # blocks; was 10 / 96 (thick)
FOG_PALE = (0xE8, 0xDE, 0xE4)      # biome fog colours are blended this far towards a pale rose-white ...
FOG_PALE_MIX = 0.55                # ... (0 = biome colour as written, 1 = all pale)


# ---- sky (user: mint-teal sky like the reference video); every biome uses the same sky and horizon fog ----
SKY_COLOR = "#5cd6c6"     # main sky dome
SKY_FOG = "#8fe2cc"       # horizon / distance fog: a lighter, slightly greener mint


def pale_fog(hex_colour):
    c = [int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a + (b - a) * FOG_PALE_MIX):02x}" for a, b in zip(c, FOG_PALE))


# ---- dimension type: open sky, permanent dusk, nether-style fog and shading, no beds ----
wj(D / "dimension_type/the_sift.json", {
    "ambient_light": 0.25,
    "attributes": {
        "minecraft:gameplay/bed_rule": {"can_set_spawn": "never", "can_sleep": "never", "destroy_on_use": True},
        "minecraft:gameplay/straw_bed_rule": {"can_set_spawn": "never", "can_sleep": "never", "destroy_on_use": True},
        "minecraft:gameplay/respawn_anchor_works": True,
        "minecraft:gameplay/sky_light_level": 8.0,
        "minecraft:visual/sky_light_factor": 0.85,     # user: brighter sunlight (was 0.55)
        "minecraft:visual/sky_light_color": "#f2e4dc",   # near-white warm light (was #c79a8a, dim rose)
        "minecraft:visual/ambient_light_color": "#2a1f24",
        "minecraft:visual/star_brightness": 0.0,          # the day timeline raises it at night
        "minecraft:visual/cloud_color": "#cc6a4a5a",
        "minecraft:visual/fog_start_distance": FOG_START,
        "minecraft:visual/fog_end_distance": FOG_END,
    },
    "cardinal_light": "nether",
    "coordinate_scale": 1.0,
    "has_ceiling": False,
    "has_ender_dragon_fight": False,
    "default_clock": "minecraft:overworld",           # day / night shared with the overworld (user)
    "has_skylight": True,
    "height": 384,
    "infiniburn": "#minecraft:infiniburn_overworld",
    "logical_height": 384,
    "min_y": -64,
    "monster_spawn_block_light_limit": 0,
    "monster_spawn_light_level": {"type": "minecraft:uniform", "max_inclusive": 7, "min_inclusive": 0},
    "timelines": "#pysift:in_sift",
})


# ---- day cycle: three phases (user, reference video "New Sift footage"): morning / day / night ----
# Multipliers on top of the biome colours (the mint sky stays the daytime look). Tick 0 = 6:00, 6000 = noon,
# 12000 = 18:00 (dusk), 18000 = midnight. Morning 23000-3000 is warm gold-pink, day 3500-11000 unchanged,
# dusk turns pink-violet, night 13500-22000 deep blue with bright stars and dim sky light.
def track(points, modifier="multiply"):
    return {"modifier": modifier, "keyframes": [{"ticks": t, "value": v} for t, v in points]}


SIFT_DAY = {
    "minecraft:visual/sky_color": track([(0, "#ffcf9c"), (2000, "#ffe6c8"), (3500, "#ffffff"), (11000, "#ffffff"),
                                         (12200, "#e3a3d6"), (13500, "#2c3466"), (22000, "#2c3466"), (23300, "#cc96bc")]),
    "minecraft:visual/fog_color": track([(0, "#ffd6b0"), (2000, "#ffeedd"), (3500, "#ffffff"), (11000, "#ffffff"),
                                         (12200, "#e8b2dc"), (13500, "#2a325c"), (22000, "#2a325c"), (23300, "#d2a2c2")]),
    "minecraft:visual/sky_light_color": track([(0, "#ffd8b0"), (3500, "#ffffff"), (11000, "#ffffff"), (12500, "#e8b0d0"),
                                               (13500, "#98a4ff"), (22000, "#98a4ff"), (23300, "#e2b2c8")]),
    "minecraft:visual/sky_light_factor": track([(0, 0.85), (3500, 1.0), (11000, 1.0), (13500, 0.3), (22000, 0.3), (23300, 0.6)]),
    "minecraft:gameplay/sky_light_level": track([(0, 0.85), (3500, 1.0), (11000, 1.0), (13500, 0.35), (22000, 0.35), (23300, 0.6)]),
    # clouds thin out after dusk (alpha ~12 %) so the stars and the aurora stay visible
    "minecraft:visual/cloud_color": track([(0, "#ffffeedd"), (3500, "#ffffffff"), (11000, "#ffffffff"), (12200, "#c0e0b0e0"),
                                           (13500, "#1e2a2a4a"), (22000, "#1e2a2a4a"), (23300, "#a0d0a8c0")]),
    "minecraft:visual/star_brightness": track([(0, 0.05), (1000, 0.0), (11500, 0.0), (13500, 0.9), (22000, 0.9), (23500, 0.2)],
                                              "maximum"),
}
# sun, moon and star movement + the sunrise/sunset glow come straight from the vanilla day timeline
try:
    import zipfile
    _jar = Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-common.jar"
    with zipfile.ZipFile(_jar) as _z:
        _vanilla_day = json.loads(_z.read("data/minecraft/timeline/day.json"))
    for _k in ("minecraft:visual/sun_angle", "minecraft:visual/moon_angle", "minecraft:visual/star_angle",
               "minecraft:visual/sunrise_sunset_color"):
        if _k in _vanilla_day["tracks"]:
            SIFT_DAY[_k] = _vanilla_day["tracks"][_k]
except (OSError, KeyError) as _e:
    print("warning: vanilla day timeline not found, sun and moon will not move:", _e)
wj(D / "timeline/sift_day.json", {"clock": "minecraft:overworld", "period_ticks": 24000,
                                  "time_markers": {"pysift:morning": {"show_in_commands": True, "ticks": 0},
                                                   "pysift:day": {"show_in_commands": True, "ticks": 3500},
                                                   "pysift:night": {"show_in_commands": True, "ticks": 13500}},
                                  "tracks": SIFT_DAY})
wj(D / "tags/timeline/in_sift.json", {"values": ["#minecraft:universal", "pysift:sift_day", "minecraft:moon"]})


# ---- vegetation and willow features (worldgen/feature + worldgen/placed_feature) ----
SPREAD = {"type": "minecraft:offset", "x": {"type": "minecraft:trapezoid", "max": 7, "min": -7, "plateau": 0},
          "y": {"type": "minecraft:trapezoid", "max": 3, "min": -3, "plateau": 0},
          "z": {"type": "minecraft:trapezoid", "max": 7, "min": -7, "plateau": 0}}


def uniform(lo, hi):
    return {"type": "minecraft:uniform", "min_inclusive": lo, "max_inclusive": hi}


def provider(block, **props):
    """Inline block state provider. A bare string here would be read as a worldgen/block_state_provider reference."""
    s = state(block, **props)
    return s if isinstance(s, dict) else {"id": s}


# 青色地面：柔和青碧草只長在這些方塊上，其他柔和草不長在這些方塊上（使用者：草的顏色要符合地板）
TEAL_FLOORS = ["pysift:capped_crimson_strata", "pysift:abyssal_strata", "pysift:silted_strata"]
SOFT_GRASS = {"soft_crimson_short_grass", "soft_crimson_tall_grass", "soft_violet_short_grass", "soft_violet_tall_grass",
              "soft_dune_short_grass", "soft_dune_tall_grass"}


def patch(name, plant, patches, tries, noisy=True, floor_in=None, **props):
    """A plant patch: `patches` centres per chunk, `tries` placements around each centre ((lo, hi) = random per centre).
    noisy=True (default) clusters the patches like vanilla plains grass: `patches` centres where the noise is high,
    a third of that where it is low, so every area looks a little different.
    floor_in: only place on these blocks (the block below). Soft grasses (SOFT_GRASS) automatically skip TEAL_FLOORS."""
    st = state(plant, **props)
    centres = ({"type": "minecraft:noise_threshold_count", "above_noise": patches, "below_noise": max(1, patches // 3),
                "noise_level": -0.6} if noisy else {"type": "minecraft:count", "count": patches})
    tries = uniform(*tries) if isinstance(tries, tuple) else tries
    wj(D / f"worldgen/feature/{name}.json", {"type": "minecraft:simple_block", "to_place": provider(plant, **props)})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        centres, {"type": "minecraft:in_square"},
        {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, {"type": "minecraft:biome"},
        {"type": "minecraft:count", "count": tries}, SPREAD,
        {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [
            {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"},
            {"type": "minecraft:would_survive", "state": st}] + floor_predicates(plant, floor_in)}}]})
    return f"pysift:{name}"


def floor_predicates(plant, floor_in):
    below = lambda blocks: {"type": "minecraft:matching_blocks", "offset": [0, -1, 0], "blocks": blocks}
    if floor_in:
        return [below(floor_in)]
    if plant in SOFT_GRASS:
        return [{"type": "minecraft:not", "predicate": below(TEAL_FLOORS)}]
    return []


def carpet_patch(name, patches, tries):
    """珊瑚落葉地毯：像原版 flower_cherry，四個方向 x 2~4 層隨機。"""
    pid = patch(name, "coral_leaf_carpet", patches, tries, facing="north", flower_amount=4)
    wj(D / f"worldgen/feature/{name}.json", {"type": "minecraft:simple_block", "to_place": {"type": "minecraft:weighted", "entries": [
        {"data": state("coral_leaf_carpet", facing=f, flower_amount=a), "weight": 1} for a in (2, 3, 4) for f in ("north", "east", "south", "west")]}})
    return pid


# ---- soul willow (SoulWillowTrunkPlacer / FoliagePlacer / VineDecorator) ----
# Two configured features from the same code, only the JSON differs:
#   soul_willow       : the common tree. 2x2 trunk, 8-10 tall, crown 3-5 thick, few short buttress roots
#   soul_willow_giant : the giant weeping willow (crown ~24-34 wide). 2x2 saplings grow it; rare in the willow grove
LEAF = lambda block: state(block, distance=7, persistent="false", waterlogged="false")


def soul_willow_tree(name, trunk, foliage, vine_max_length):
    wj(D / f"worldgen/feature/{name}.json", {
        "type": "minecraft:tree",
        "below_trunk_provider": provider("abyssal_strata", depth=0),
        "trunk_provider": provider("soul_willow_log", axis="y"),
        "trunk_placer": {"type": "pysift:soul_willow_trunk_placer", **trunk},
        # 70% teal, 22% pale blue, 8% glowing leaves
        "foliage_provider": {"type": "minecraft:weighted", "entries": [
            {"data": LEAF("soul_willow_leaves"), "weight": 70}, {"data": LEAF("soul_willow_leaves_pale"), "weight": 22},
            {"data": LEAF("glowing_soul_willow_leaves"), "weight": 8}]},
        "foliage_placer": {"type": "pysift:soul_willow_foliage_placer", "offset": 0, **foliage},
        # side_chance: second outward face at corners; full_chance: whole strand gets all four faces
        "decorators": [{"type": "pysift:soul_willow_vines", "vine_chance": 0.75, "vine_min_length": 3,
                        "vine_max_length": vine_max_length, "glow_chance": 0.15, "vine": "pysift:soul_willow_vine",
                        "glowing_vine": "pysift:glowing_soul_willow_vine", "side_chance": 0.5,
                        "full_chance": 0.05}],
        "ignore_vines": True,
        "minimum_size": {"type": "minecraft:two_layers_feature_size", "limit": 1, "lower_size": 0, "upper_size": 2},
    })
    return f"pysift:{name}"


SOUL_WILLOW = soul_willow_tree("soul_willow", vine_max_length=9, trunk={
    "base_height": 5, "height_rand_a": 1, "height_rand_b": 1, "trunk_width": 2, "branch_count": uniform(3, 4),
    "branch_length": uniform(2, 3), "twig_count": uniform(0, 1), "root_count": uniform(0, 3), "root_length": uniform(1, 2)},
    foliage={"radius": uniform(1, 2), "clump_count": uniform(1, 2), "clump_radius": 3, "flatness": 0.45,
             "clump_y_spread": 1})
SOUL_WILLOW_GIANT = soul_willow_tree("soul_willow_giant", vine_max_length=16, trunk={
    "base_height": 13, "height_rand_a": 3, "height_rand_b": 2, "trunk_width": uniform(2, 3), "branch_count": uniform(4, 6),
    "branch_length": uniform(5, 8), "twig_count": uniform(1, 2), "root_count": uniform(4, 8), "root_length": uniform(3, 6)},
    foliage={"radius": uniform(2, 3), "clump_count": uniform(1, 3), "clump_radius": uniform(3, 6)})


def trees(name, feature, frequency):
    # origin near the chunk centre (+-4) instead of in_square: the crown reaches ~19 blocks out, and a feature
    # may only write into the 3x3 chunks around its origin chunk
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": feature, "placement": [
        frequency, {"type": "minecraft:offset", "x": uniform(4, 11), "y": 0, "z": uniform(4, 11)},
        {"type": "minecraft:surface_water_depth_filter", "max_water_depth": 0},
        {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR"},
        {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:would_survive",
                                                                   "state": "minecraft:oak_sapling"}},
        {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


def cliff_vines(name, tries=48, min_len=3, max_len=7, glow_chance=0.15, count=6, min_y=40, max_y=120):
    wj(D / f"worldgen/feature/{name}.json", {
        "type": "pysift:cliff_vines",
        "tries": tries,
        "min_length": min_len,
        "max_length": max_len,
        "glow_chance": glow_chance,
        "xz_spread": 8,
        "y_spread": 16,
    })
    wj(D / f"worldgen/placed_feature/{name}.json", {
        "feature": f"pysift:{name}",
        "placement": [
            {"type": "minecraft:count", "count": count},
            {"type": "minecraft:in_square"},
            {"type": "minecraft:height_range", "height": {
                "type": "minecraft:uniform",
                "min_inclusive": {"absolute": min_y},
                "max_inclusive": {"absolute": max_y}
            }},
            {"type": "minecraft:biome"}
        ]
    })
    return f"pysift:{name}"


def wall_plant(name, block, count, tries=24, min_len=1, max_len=1, min_y=40, max_y=120):
    """貼牆植物（SiftWallPlantBlock，pysift:wall_plant 特徵）：在峭壁側面的空氣格貼著實心面放，藤蔓再往下延伸。"""
    wj(D / f"worldgen/feature/{name}.json", {"type": "pysift:wall_plant", "block": f"pysift:{block}", "tries": tries,
                                             "min_length": min_len, "max_length": max_len, "xz_spread": 8, "y_spread": 16})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": min_y},
                                                      "max_inclusive": {"absolute": max_y}}},
        {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


VEGETATION = {
    # ember_grass / abyss_grass / puff_grass are coloured by the floor under them (client FloorTint), so the same plant
    # is orange on crimson rock, teal on violet rock, pink on pink loam (reference video, The Sift 6:34 on).
    # (lo, hi) tries are random per patch centre; every patch is noise-clustered (patch() default).
    # Colour plan (user, 2026-10-25): every biome's plants follow its ground colours.
    #   crimson canyon: reds and pinks with a few teal accents on teal floors
    #   violet abyss:   purple and yellow only (no teal / cyan plants, no soul-willow vines on its cliffs)
    #   willow grove:   mint and teal with soft pink accents (matches the soul willows)
    #   amber dunes:    yellow and orange
    "crimson_strata_canyon": [patch("patch_ember_grass", "soft_crimson_short_grass", 12, (48, 80)),
                              patch("patch_tall_ember_grass", "soft_crimson_tall_grass", 5, (16, 32), half="lower"),
                              patch("patch_carapace_short_grass", "carapace_short_grass", 6, (16, 32)),
                              patch("patch_carapace_flower", "carapace_flower", 2, (4, 8)),
                              carpet_patch("patch_canyon_coral_leaf_carpet", 3, (8, 16)),
                              patch("patch_rift_orange_short_grass", "rift_orange_short_grass", 3, (10, 20)),
                              patch("patch_rift_orange_tall_grass", "rift_orange_tall_grass", 2, (6, 12), half="lower"),
                              patch("patch_canyon_puff_grass", "puff_grass", 2, (6, 14), half="lower"),
                              patch("patch_canyon_teal_grass", "soft_teal_short_grass", 4, (16, 32), floor_in=TEAL_FLOORS),
                              patch("patch_canyon_tall_teal_grass", "soft_teal_tall_grass", 2, (6, 12), half="lower", floor_in=TEAL_FLOORS),
                              wall_plant("wall_carapace_vine", "carapace_vine", 5, max_len=4),
                              wall_plant("wall_orange_sift_vine", "orange_sift_vine", 2, max_len=3),
                              cliff_vines("cliff_vines_crimson_canyon", tries=40, min_len=3, max_len=7, glow_chance=0.10, count=6)],
    "violet_slate_abyss": [patch("patch_abyss_grass", "soft_violet_short_grass", 14, (48, 80)),
                           patch("patch_violet_ember_grass", "soft_violet_tall_grass", 6, (16, 32), half="lower"),
                           patch("patch_violet_pink_curled_fern", "pink_curled_fern", 3, (8, 16)),
                           patch("patch_violet_puff_grass", "puff_grass", 3, (8, 16), half="lower"),
                           # the yellow half of the palette
                           patch("patch_dusk_bloom", "dusk_bloom", 8, (16, 28)),
                           patch("patch_violet_clustered_yellow_flowers", "clustered_yellow_flowers", 6, (10, 20)),
                           patch("patch_violet_yellow_leaf_litter", "yellow_leaf_litter", 4, (8, 14)),
                           patch("patch_violet_yellow_agave", "yellow_agave", 1, (2, 4)),
                           patch("patch_bone_spire", "bone_spire", 2, (4, 10)),
                           patch("patch_glowcap", "gloomcap", 2, (4, 10))],
    "willow_grove": [trees("soul_willows_giant", SOUL_WILLOW_GIANT, {"type": "minecraft:rarity_filter", "chance": 16}),
                     trees("soul_willows", SOUL_WILLOW, {"type": "minecraft:count", "count": uniform(1, 2)}),
                     patch("patch_rift_mint_short_grass", "rift_mint_short_grass", 10, (40, 64)),
                     patch("patch_rift_mint_tall_grass", "rift_mint_tall_grass", 4, (12, 24), half="lower"),
                     patch("patch_grove_teal_grass", "soft_teal_short_grass", 6, (24, 40), floor_in=TEAL_FLOORS),
                     patch("patch_grove_tall_teal_grass", "soft_teal_tall_grass", 3, (8, 16), half="lower", floor_in=TEAL_FLOORS),
                     patch("patch_blue_curled_fern", "blue_curled_fern", 3, (8, 16)),
                     patch("patch_olive_forked_stalk", "olive_forked_stalk", 2, (4, 10)),
                     patch("patch_cleaver_plant", "cleaver_plant", 2, (3, 6)),
                     patch("patch_soul_cleaver_plant", "soul_cleaver_plant", 1, (2, 4)),
                     patch("patch_blue_giant_canopy", "blue_giant_canopy", 1, (2, 5)),
                     patch("patch_grove_puff_grass", "puff_grass", 2, (6, 12), half="lower"),
                     patch("patch_grove_glowcap", "gloomcap", 1, (3, 8)),
                     # soft pink accents
                     patch("patch_grove_ember_grass", "soft_crimson_short_grass", 3, (12, 24)),
                     carpet_patch("patch_coral_leaf_carpet", 2, (6, 12)),
                     patch("patch_grove_yellow_flower_patch", "yellow_flower_patch", 1, (3, 6)),
                     wall_plant("wall_green_sift_vine", "green_sift_vine", 4, max_len=4),
                     cliff_vines("cliff_vines_willow_grove", tries=64, min_len=4, max_len=9, glow_chance=0.18, count=12)],
    "amber_dunes": [patch("patch_dune_ember_grass", "soft_dune_short_grass", 6, (20, 36)),
                    patch("patch_dune_tall_ember_grass", "soft_dune_tall_grass", 3, (8, 16), half="lower"),
                    patch("patch_dune_yellow_agave", "yellow_agave", 2, (3, 6)),
                    patch("patch_clustered_yellow_flowers", "clustered_yellow_flowers", 2, (4, 8)),
                    patch("patch_yellow_leaf_litter", "yellow_leaf_litter", 2, (4, 8)),
                    patch("patch_dune_rift_orange_short_grass", "rift_orange_short_grass", 2, (6, 12)),
                    patch("patch_dune_bone_spire", "bone_spire", 1, (2, 5)),
                    patch("patch_dune_teal_grass", "soft_teal_short_grass", 1, (4, 8), floor_in=TEAL_FLOORS),
                    wall_plant("wall_dune_orange_sift_vine", "orange_sift_vine", 3, max_len=3),
                    cliff_vines("cliff_vines_amber_dunes", tries=24, min_len=2, max_len=4, glow_chance=0.05, count=2)],
    # Lullaby Hills (canyon walls of crimson vein stone, void-capped tops): sparse red / pink / orange plants
    "lullaby_hills": [patch("patch_lullaby_ember_grass", "soft_crimson_short_grass", 6, (20, 36)),
                      patch("patch_lullaby_tall_ember_grass", "soft_crimson_tall_grass", 2, (6, 12), half="lower"),
                      patch("patch_lullaby_rift_orange_short_grass", "rift_orange_short_grass", 3, (8, 16)),
                      patch("patch_lullaby_carapace_short_grass", "carapace_short_grass", 2, (6, 12)),
                      patch("patch_lullaby_puff_grass", "puff_grass", 1, (4, 8), half="lower"),
                      carpet_patch("patch_lullaby_coral_leaf_carpet", 2, (4, 10)),
                      wall_plant("wall_lullaby_carapace_vine", "carapace_vine", 4, max_len=5),
                      cliff_vines("cliff_vines_lullaby_hills", tries=40, min_len=4, max_len=10, glow_chance=0.12, count=6,
                                  max_y=130)],
    # Soul Caldera: a scorched plateau, so sparse - violet and crimson tufts in the cooled lava, soul-cyan accents,
    # bone spires in the ash; nothing grows on the hot magma veins (only the plain / cone floors support vegetation)
    "soul_caldera": [patch("patch_caldera_violet_grass", "soft_violet_short_grass", 5, (16, 32)),
                     patch("patch_caldera_tall_violet_grass", "soft_violet_tall_grass", 2, (4, 10), half="lower"),
                     patch("patch_caldera_crimson_grass", "soft_crimson_short_grass", 3, (10, 20)),
                     patch("patch_caldera_soul_cleaver_plant", "soul_cleaver_plant", 2, (3, 6)),
                     patch("patch_caldera_bone_spire", "bone_spire", 2, (3, 8)),
                     patch("patch_caldera_pink_curled_fern", "pink_curled_fern", 1, (3, 6)),
                     patch("patch_caldera_puff_grass", "puff_grass", 1, (3, 6), half="lower"),
                     patch("patch_caldera_glowcap", "gloomcap", 1, (2, 5)),
                     cliff_vines("cliff_vines_soul_caldera", tries=24, min_len=2, max_len=4, glow_chance=0.3, count=3)],
}

# ---- strata mesas (pysift:strata_spire, StrataSpireFeature.java) ----
# Big round flat-topped mesas of stacked 2-high tiers that step inward at the edge (reference video
# "I Recreated The Sift" + the user's mesa screenshots). Every biome uses the same feature with its own materials:
# top = exposed tier tops (the walkable surface), body = gradient from the top down, band = optional stripe.
def weighted(*states):
    return {"type": "minecraft:weighted", "entries": [{"data": s, "weight": 1} for s in states]}


SPIRES = {   # biome: big round flat-topped mesas (user: large radius, flat walkable tops, not pillars)
    "crimson_strata_canyon": dict(tiers=(4, 8), radius=(12, 18), cap=(2, 3),
                                  # caps whose side is blue above / pink below, over the pink ember stone body (user rule)
                                  top=weighted(state("capped_crimson_strata", facing="up", tone="teal")),
                                  body=[state("ember_stone", heat=0)],
                                  frequency={"type": "minecraft:rarity_filter", "chance": 40}),    # user: keep a few; the buttes are terrain now
    "violet_slate_abyss": dict(tiers=(3, 7), radius=(10, 17), cap=(1, 3),
                               top=VIOLET_TOP, body=[VIOLET_UNDER],
                               frequency={"type": "minecraft:rarity_filter", "chance": 9}),
    "willow_grove": dict(tiers=(2, 4), radius=(8, 14), cap=(1, 2),                                 # low, sparse
                         top=GROVE_TOP, body=[GROVE_UNDER],
                         frequency={"type": "minecraft:rarity_filter", "chance": 14}),
    "amber_dunes": dict(tiers=(3, 6), radius=(10, 16), cap=(1, 3),                                 # isolated
                        top=state("amber_sand"), body=[state("bleached_sandstone", bleach=0)],
                        band=state("cracked_sandstone", crack=0), band_every=3,
                        frequency={"type": "minecraft:rarity_filter", "chance": 12}),
}


def spire(biome_name, c):
    name = "spire_" + biome_name
    as_provider = lambda s: s if isinstance(s, dict) else {"id": s}
    feature = {"type": "pysift:strata_spire", "tiers": uniform(*c["tiers"]), "radius": uniform(*c["radius"]),
               "cap_steps": uniform(*c["cap"]), "top": as_provider(c["top"]),
               "body": [as_provider(b) for b in c["body"]]}
    if "band" in c:
        feature.update(band=as_provider(c["band"]), band_every=c["band_every"])
    wj(D / f"worldgen/feature/{name}.json", feature)
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        # origin at the chunk centre (not in_square): mesas reach 23 blocks out, the most a feature may write
        c["frequency"], {"type": "minecraft:offset", "x": 8, "y": 0, "z": 8},
        {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


SPIRE_FEATURES = {b: [spire(b, c)] for b, c in SPIRES.items()}


# ---- boss arenas (pysift:boss_arena, BossArenaFeature.java): one boss per arena, spawned at world generation ----
# Placed at the chunk centre (the arena reaches 22 blocks out); after the spires in the same step, so it flattens them.
ARENA_RARITY = 900    # about one arena per this many chunks of the biome (substantially reduced)
ARENAS = {
    "amber_dunes": dict(boss="monarch", radius=15, pillar_height=8, pillar_count=10,         # sandstone throne ruin
                        floor=weighted(state("bleached_sandstone_bricks"), state("chiseled_bleached_sandstone_bricks"),
                                       state("bleached_sandstone_bricks")),
                        wall=state("bleached_sandstone_brick_wall"), pillar=state("chiseled_bleached_sandstone_bricks")),
    "willow_grove": dict(boss="harmonizer", radius=13, pillar_height=6, pillar_count=8,        # platform in a spirit lake
                         floor=weighted(state("abyssal_strata_bricks"), state("chiseled_abyssal_strata_bricks")),
                         wall=state("abyssal_strata_brick_wall"), pillar=state("abyssal_strata_bricks"),
                         moat=state("spirit_liquid", level=0), moat_width=4),
    "violet_slate_abyss": dict(boss="sculk_monstrosity", radius=16, pillar_height=10, pillar_count=8,   # dark slate ring
                               floor=weighted(state("dark_slate_bricks"), state("chiseled_dark_slate_bricks")),
                               wall=state("dark_slate_brick_wall"), pillar=state("dark_slate_pillar", axis="y")),
}


def arena(biome_name, c):
    name = "boss_arena_" + biome_name
    as_provider = lambda st: st if isinstance(st, dict) and "type" in st else ({"id": st} if isinstance(st, str) else st)
    feature = {"type": "pysift:boss_arena", "arena_type": c["boss"], "boss": f"pysift:{c['boss']}", "radius": c["radius"],
               "pillar_height": c["pillar_height"], "pillar_count": c["pillar_count"],
               "floor": as_provider(c["floor"]), "wall": as_provider(c["wall"]), "pillar": as_provider(c["pillar"])}
    if "moat" in c:
        feature.update(moat=as_provider(c["moat"]), moat_width=c["moat_width"])
    wj(D / f"worldgen/feature/{name}.json", feature)
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:rarity_filter", "chance": ARENA_RARITY}, {"type": "minecraft:offset", "x": 8, "y": 0, "z": 8},
        {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


for _biome, _arena in ARENAS.items():
    SPIRE_FEATURES.setdefault(_biome, []).append(arena(_biome, _arena))


# ---- spirit ponds (vanilla minecraft:lake feature filled with spirit liquid) ----
# The terrain's pond hollows only fill where they dip below sea level 63; these small lakes add ponds at any
# height (on hills and plateaus too). barrier = the biome's subsoil, used where the pond wall meets air.
# protect = mesa-only blocks a pond may not dig through: a pond from a neighbouring chunk is often placed after
# the mesa, and digging under its edge left air gaps (hollows) below the mesa.
PONDS_PER_BIOME = {   # biome: (barrier block, one pond per this many chunks on average, protected blocks)
    "willow_grove": (GROVE_UNDER, 1, []),          # most ponds
    "violet_slate_abyss": (VIOLET_UNDER, 2, []),
    "crimson_strata_canyon": (CRIMSON_UNDER, 2, ["ember_stone", "capped_crimson_strata"]),
    "amber_dunes": (DUNE_STONE, 3, ["bleached_sandstone", "cracked_sandstone"]),   # fewest: oases
}


def spirit_pond(biome_name, barrier, chance, protect):
    name = "spirit_pond_" + biome_name
    wj(D / f"worldgen/feature/{name}.json", {
        "type": "minecraft:lake", "barrier": barrier if isinstance(barrier, dict) else {"id": barrier},
        "can_place_feature": {"type": "minecraft:true"},
        "can_replace_with_air_or_fluid": {"type": "minecraft:not", "predicate": {"type": "minecraft:any_of", "predicates": [
            {"type": "minecraft:matching_block_tag", "tag": "minecraft:features_cannot_replace"},
            {"type": "minecraft:matching_blocks", "blocks": [f"pysift:{b}" for b in protect] or "minecraft:bedrock"}]}},
        "can_replace_with_barrier": {"type": "minecraft:not", "predicate": {
            "type": "minecraft:matching_block_tag", "tag": "minecraft:features_cannot_replace"}},
        "fluid": {"id": "pysift:spirit_liquid", "properties": {"level": "0"}}})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:rarity_filter", "chance": chance}, {"type": "minecraft:in_square"},
        {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


POND_FEATURES = {b: [spirit_pond(b, *v)] for b, v in PONDS_PER_BIOME.items()}


def soul_crater():
    """The volcano's flat crater lake and scorched crater floor (SoulCraterFeature): once per chunk, it only acts near a
    volcano cell's centre."""
    wj(D / "worldgen/feature/soul_crater.json", {"type": "pysift:soul_crater"})
    wj(D / "worldgen/placed_feature/soul_crater.json", {"feature": "pysift:soul_crater", "placement": [
        {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, {"type": "minecraft:biome"}]})   # surface biome
    return "pysift:soul_crater"


POND_FEATURES["soul_caldera"] = [soul_crater()]


# ---- biomes ----
def spawns(**categories):
    """spawns(monster=[(mob, weight, min, max), ...], creature=[...]); the category must match the entity's MobCategory."""
    return {"minecraft:gameplay/natural_mob_spawns": {
        "argument": {"spawn_costs": {}, "spawns_by_category": {category: [
            {"type": f"pysift:{mob}", "count": {"type": "minecraft:uniform", "max_inclusive": hi, "min_inclusive": lo},
             "weight": w} for mob, w, lo, hi in entries] for category, entries in categories.items()}},
        "modifier": "overlay"}}


# ---- soul crystal block (SoulCrystal.java) in the violet slate abyss: ore clusters at the surface and underground ----
# Surface clusters sit half above ground (offset -1 under the heightmap) so the glowing blocks show from afar.
def soul_crystal_ore(name, size, count, placement):
    targets = [{"state": "pysift:soul_crystal_block",
                "target": {"predicate_type": "minecraft:block_match", "block": f"pysift:{b}"}}
               for b in ("violet_capped_dark_slate", "dark_slate", "void_stone")]
    wj(D / f"worldgen/feature/{name}.json", {"type": "minecraft:ore", "discard_chance_on_air_exposure": 0.0,
                                               "size": size, "targets": targets})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"}, *placement,
        {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


# ---- progression ores (ModProgression.java) ----
def siftite_ore(name):
    """Siftite ore in the deep stone of every biome (y -40..40), vanilla iron-like veins."""
    targets = [{"state": "pysift:siftite_ore",
                "target": {"predicate_type": "minecraft:block_match", "block": f"pysift:{b}"}}
               for b in ("void_stone", "dark_slate", "abyssal_strata", "silted_strata", "bleached_sandstone")]
    wj(D / f"worldgen/feature/{name}.json", {"type": "minecraft:ore", "discard_chance_on_air_exposure": 0.0,
                                               "size": 8, "targets": targets})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:count", "count": 6}, {"type": "minecraft:in_square"},   # ~30 ore blocks per chunk
        {"type": "minecraft:height_range", "height": {"type": "minecraft:trapezoid",
                                                       "min_inclusive": {"absolute": -40}, "max_inclusive": {"absolute": 40}}},
        {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


def charoite_clusters(name, count, placement):
    """Charoite clusters standing on the floor (facing up), on the surface or on cave floors."""
    wj(D / f"worldgen/feature/{name}.json", {"type": "minecraft:simple_block",
                                               "to_place": provider("charoite_cluster", facing="up", waterlogged="false")})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"}, *placement,
        {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [
            {"type": "minecraft:matching_blocks", "blocks": ["minecraft:air", "minecraft:cave_air"]},
            {"type": "minecraft:solid", "offset": [0, -1, 0]}]}},
        {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


SIFTITE_ORE = siftite_ore("siftite_ore")

def soul_geode(name):
    """Soul crystal geodes in the deep void stone (phase 2): void obsidian shell, corrupted slate, glowing soul crystal inside."""
    wj(D / f"worldgen/feature/{name}.json", {
        "type": "minecraft:geode",
        "blocks": {"filling_provider": {"id": "minecraft:air"}, "inner_layer_provider": provider("soul_crystal_block"),
                   "alternate_inner_layer_provider": provider("soul_crystal_block"),
                   "middle_layer_provider": provider("dark_slate", fade=0),
                   "outer_layer_provider": provider("void_obsidian"),
                   "inner_placements": [{"id": "minecraft:air"}],
                   "cannot_replace": "#minecraft:features_cannot_replace", "invalid_blocks": "#minecraft:geode_invalid_blocks"},
        "layers": {}, "crack": {"generate_crack_chance": 0.6},
        "outer_wall_distance": {"type": "minecraft:uniform", "min_inclusive": 4, "max_inclusive": 6},
        "use_alternate_layer0_chance": 0.0, "invalid_blocks_threshold": 1})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:rarity_filter", "chance": 18}, {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                       "min_inclusive": {"absolute": -50}, "max_inclusive": {"absolute": 25}}},
        {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


SOUL_GEODE = soul_geode("soul_geode")

# sinkholes (v2.1.0, SinkholeFeature): holes in the surface that open on the underground layers; the surface is no longer
# sealed off from the caves (bury_caves keeps natural cave mouths away from the ground, these are the planned entrances)
SINKHOLE_RARITY = 14      # about one chunk in 14 tries (the feature itself refuses water, steep ground and bad spots)
SINKHOLE_BIOMES = {"willow_grove", "violet_slate_abyss", "crimson_strata_canyon", "amber_dunes", "lullaby_hills"}   # not the volcano
wj(D / "worldgen/feature/sinkhole.json", {"type": "pysift:sinkhole"})
wj(D / "worldgen/placed_feature/sinkhole.json", {"feature": "pysift:sinkhole", "placement": [
    {"type": "minecraft:rarity_filter", "chance": SINKHOLE_RARITY}, {"type": "minecraft:in_square"},
    {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"},
    {"type": "minecraft:biome"}]})
SINKHOLE = "pysift:sinkhole"

# ambient particles per biome (phase 2), as vanilla nether biomes do it
AMBIENT = {"crimson_strata_canyon": ("minecraft:crimson_spore", 0.012),
           "red_zone_caves": ("minecraft:crimson_spore", 0.03),
           "withered_hollows": ("minecraft:ash", 0.02),
           "resonant_vaults": ("pysift:soul_wisp", 0.006),
           "spirit_deeps": ("pysift:soul_wisp", 0.012),
           "violet_slate_abyss": ("pysift:soul_wisp", 0.002),     # user: fewer soul wisps
           "willow_grove": ("minecraft:spore_blossom_air", 0.012),
           "amber_dunes": ("minecraft:white_ash", 0.015),
           "lullaby_hills": ("minecraft:crimson_spore", 0.008),
           "soul_caldera": ("pysift:soul_wisp", 0.004)}

CAVE_FLOOR = [{"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                             "min_inclusive": {"absolute": -40}, "max_inclusive": {"absolute": 55}}},
              {"type": "minecraft:environment_scan", "direction_of_search": "down", "max_steps": 12,
               "target_condition": {"type": "minecraft:solid"},
               "allowed_search_condition": {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"}},
              {"type": "minecraft:offset", "x": 0, "y": 1, "z": 0}]   # from the solid floor to the air above it
CHAROITE = [charoite_clusters("charoite_cluster_surface", 2, [{"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}]),
            charoite_clusters("charoite_cluster_cave", 24, CAVE_FLOOR)]

def farm_plant(name, to_place, count, placement, extra_predicates, rarity=None):
    """Phase 3 farming plants (SiftFarming.java), placed like vanilla berry bushes / mushrooms."""
    wj(D / f"worldgen/feature/{name}.json", {"type": "minecraft:simple_block", "to_place": to_place})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        *([{"type": "minecraft:rarity_filter", "chance": rarity}] if rarity else []),
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"}, *placement,
        {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [
            {"type": "minecraft:matching_blocks", "blocks": ["minecraft:air", "minecraft:cave_air"]},
            {"type": "minecraft:solid", "offset": [0, -1, 0]}, *extra_predicates]}},
        {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


NEAR_SPIRIT = {"type": "minecraft:any_of", "predicates": [   # a spirit pond next to (or 2 blocks from) the bush, one lower
    {"type": "minecraft:matching_fluids", "fluids": ["pysift:spirit_liquid", "pysift:flowing_spirit_liquid"], "offset": [dx, -1, dz]}
    for dx in range(-2, 3) for dz in range(-2, 3) if (dx, dz) != (0, 0)]}
# the small rift portal of the old ritual now appears, very rarely, out in the wild (user; reference video at night)
wj(D / "worldgen/feature/wild_rift.json", {"type": "pysift:wild_rift"})
wj(D / "worldgen/placed_feature/wild_rift.json", {"feature": "pysift:wild_rift", "placement": [
    {"type": "minecraft:rarity_filter", "chance": 600}, {"type": "minecraft:in_square"},
    {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, {"type": "minecraft:biome"}]})
WILD_RIFT = "pysift:wild_rift"

FARM_FEATURES = [
    farm_plant("soul_berry_bush_pond", provider("soul_berry_bush", age="3"), 48,
               [{"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}], [NEAR_SPIRIT], rarity=2),
    farm_plant("gloomcap_cave", provider("gloomcap"), 10, CAVE_FLOOR, []),
]

# Red sculk (lore 4.7: sculk is native to The Sift, red and alive where spirit liquid is; it rots to the vanilla blue
# sculk without it). Patches grow on the ground around the spirit ponds, with red sculk veins over them
# (tools/worldgen/build_red_sculk.py for the blocks; WildRiftFeature rots them blue around the rifts).
wj(D / "worldgen/feature/red_sculk_vein_floor.json", {"type": "minecraft:simple_block",
                                                       "to_place": provider("red_sculk_vein", down="true")})
wj(D / "worldgen/feature/red_sculk_patch.json", {
    "type": "minecraft:vegetation_patch", "surface": "floor", "depth": 1, "vertical_range": 3,
    "extra_bottom_block_chance": 0.0, "extra_edge_column_chance": 0.4, "vegetation_chance": 0.3,
    "xz_radius": uniform(2, 4), "replaceable": "#pysift:red_sculk_replaceable", "ground_state": provider("red_sculk"),
    "vegetation_feature": {"feature": "pysift:red_sculk_vein_floor", "placement": []}})
wj(D / "worldgen/placed_feature/red_sculk_patch.json", {"feature": "pysift:red_sculk_patch", "placement": [
    {"type": "minecraft:count", "count": 6}, {"type": "minecraft:in_square"},
    {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"},
    {"type": "minecraft:block_predicate_filter", "predicate": NEAR_SPIRIT}, {"type": "minecraft:biome"}]})
RED_SCULK_BIOMES = {"willow_grove", "violet_slate_abyss", "lullaby_hills", "crimson_strata_canyon"}

# night-glow flora (SiftFlora.java): glowshade grass in the meadows
SURFACE = [{"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}]
GLOW_FEATURES = {
    "willow_grove": [farm_plant("glowshade_short_grass_grove", provider("glowshade_short_grass"), 28, SURFACE, []),
                     # night-glow tufts in clusters (5 patches x 10-20 tufts per chunk) so they read as glowing meadows at night
                     patch("glowshade_tuft_grove", "glowshade_tuft", 5, (10, 20))],
}

# landmarks (tools/worldgen/build_landmarks.py, SurfaceFossilFeature / LullabyShrineFeature): placed after the vegetation
# so nothing grows on them. The Echo Den and the Humbler Husk are structures (structure_set), not biome features.
LANDMARK_FEATURES = {
    "amber_dunes": ["pysift:surface_fossil"],
    "crimson_strata_canyon": ["pysift:lullaby_shrine"],
    "violet_slate_abyss": ["pysift:lullaby_shrine"],
    "willow_grove": ["pysift:lullaby_shrine"],
    "lullaby_hills": ["pysift:lullaby_shrine"],
}

# red zone caves (underground biome, reference video "THE SIFT UPDATE"): crimson floors, coral-red plants, glowing
# shrubs and charoite on the cave floors; picked by the multi-noise "depth" parameter (see the dimension below)
RED_CAVE_FLOOR = [{"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                                "min_inclusive": {"absolute": -50}, "max_inclusive": {"absolute": 30}}},
                  {"type": "minecraft:environment_scan", "direction_of_search": "down", "max_steps": 12,
                   "target_condition": {"type": "minecraft:solid"},
                   "allowed_search_condition": {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"}},
                  {"type": "minecraft:offset", "x": 0, "y": 1, "z": 0}]
# ---- underground layers (v2.1.0): the Sift's blood vessels. Spirit liquid wells up from the deep; life follows it. ----
# The layer is picked by the multi-noise "depth" parameter (= blocks below the surface / 128), see the dimension below.
#   withered_hollows   26-54 blocks down   the cut-off shallows: no spirit liquid reaches here, red sculk rots blue
#   red_zone_caves     54-87 blocks down   the singing caves (the original underground biome), alive and red
#   resonant_vaults    87+ blocks down     crystal vaults where voices echo (Echo Den, soul geodes, charoite)
#   spirit_deeps       87+ blocks, wet     where spirit liquid wells up: glowing veins, red sculk, singers' pools
UNDER_FLOOR = [{"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                              "min_inclusive": {"absolute": -62}, "max_inclusive": {"absolute": 80}}},
               {"type": "minecraft:environment_scan", "direction_of_search": "down", "max_steps": 12,
                "target_condition": {"type": "minecraft:solid"},
                "allowed_search_condition": {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"}},
               {"type": "minecraft:offset", "x": 0, "y": 1, "z": 0}]


def cave_patch(name, ground, vegetation, count, radius=(2, 4), chance=0.3):
    """A vegetation patch on cave floors: `ground` replaces the stone floor, `vegetation` (block provider, optional) grows on it."""
    cfg = {"type": "minecraft:vegetation_patch", "surface": "floor", "depth": 1, "vertical_range": 3,
           "extra_bottom_block_chance": 0.0, "extra_edge_column_chance": 0.4, "vegetation_chance": chance,
           "xz_radius": uniform(*radius), "replaceable": "#pysift:red_sculk_replaceable", "ground_state": ground}
    if vegetation:
        wj(D / f"worldgen/feature/{name}_cover.json", {"type": "minecraft:simple_block", "to_place": vegetation})
        cfg["vegetation_feature"] = {"feature": f"pysift:{name}_cover", "placement": []}
    else:
        cfg["vegetation_chance"] = 0.0
        cfg["vegetation_feature"] = {"feature": {"type": "minecraft:no_op", "config": {}}, "placement": []}
    wj(D / f"worldgen/feature/{name}.json", cfg)
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"}, *UNDER_FLOOR, {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


CAVE_FEATURES = {"red_zone_caves": [
    farm_plant("red_cave_grass", provider("soft_crimson_short_grass"), 90, RED_CAVE_FLOOR, []),
    farm_plant("red_cave_sprouts", provider("rift_orange_short_grass"), 50, RED_CAVE_FLOOR, []),
    farm_plant("red_cave_charoite", provider("charoite_cluster", facing="up", waterlogged="false"), 6, RED_CAVE_FLOOR, []),
    cave_patch("song_cave_red_sculk", provider("red_sculk"), provider("red_sculk_vein", down="true"), 5),   # alive: the song caves
]}
CAVE_FEATURES["withered_hollows"] = [
    # the shallows are cut off from the spirit liquid: plain (rotten) blue sculk, the same dead sculk of the Overworld's deep dark
    cave_patch("withered_sculk", {"id": "minecraft:sculk"}, {"id": "minecraft:sculk_vein", "properties": {"down": "true"}}, 6, (2, 5)),
    farm_plant("withered_gloomcap", provider("gloomcap"), 4, UNDER_FLOOR, []),
]
# ---- cave decoration (v2.1.0): speleothems in the Sift's own stone, ceiling crystals, wall vines ----
def under_ceiling(lo=-62, hi=80):
    return [{"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                          "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
            {"type": "minecraft:environment_scan", "direction_of_search": "up", "max_steps": 24,
             "target_condition": {"type": "minecraft:solid"},
             "allowed_search_condition": {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"}},
            {"type": "minecraft:offset", "x": 0, "y": -1, "z": 0}]      # from the solid ceiling to the air below it


def under_floor(lo=-62, hi=80):
    return [{"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                          "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
            {"type": "minecraft:environment_scan", "direction_of_search": "down", "max_steps": 24,
             "target_condition": {"type": "minecraft:solid"},
             "allowed_search_condition": {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"}},
            {"type": "minecraft:offset", "x": 0, "y": 1, "z": 0}]


# Rough absolute heights of each layer (the ground is mostly y 60-110): most random starting points fall in solid rock and
# are dropped by the scan, so the counts are high (vanilla lush caves use 125) and the height ranges narrow
LAYER_Y = {"withered_hollows": (10, 60), "red_zone_caves": (-20, 40), "resonant_vaults": (-62, 10), "spirit_deeps": (-62, 10)}


def speleothem(name, layer, body, alt, tip, lo, hi, hanging, count):
    """Stalagmites (hanging False) or stalactites (True): pysift:speleothem, a tapered column of `body` (some `alt`) with a wall `tip`."""
    wj(D / f"worldgen/feature/{name}.json", {"type": "pysift:speleothem", "block": f"pysift:{body}", "alt_block": f"pysift:{alt}",
                                             "tip_block": f"pysift:{tip}", "min_height": lo, "max_height": hi, "hanging": hanging})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"},
        *(under_ceiling(*LAYER_Y[layer]) if hanging else under_floor(*LAYER_Y[layer])), {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


def ceiling_crystals(name, layer, count):
    """Charoite clusters growing down from the ceiling."""
    wj(D / f"worldgen/feature/{name}.json", {"type": "minecraft:simple_block",
                                             "to_place": provider("charoite_cluster", facing="down", waterlogged="false")})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"}, *under_ceiling(*LAYER_Y[layer]),
        {"type": "minecraft:block_predicate_filter", "predicate": {"type": "minecraft:all_of", "predicates": [
            {"type": "minecraft:matching_blocks", "blocks": ["minecraft:air", "minecraft:cave_air"]},
            {"type": "minecraft:solid", "offset": [0, 1, 0]}]}}, {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


# Each layer's columns use that layer's own floor blocks (see CAVE_RULES), so the colours follow the ladder.
SPELEOTHEMS = {
    "withered_hollows": [speleothem("withered_stalagmite", "withered_hollows", "dark_slate", "varied_dark_slate", "dark_slate_wall", 2, 5, False, 45),
                         speleothem("withered_stalactite", "withered_hollows", "dark_slate", "varied_dark_slate", "dark_slate_wall", 2, 6, True, 55)],
    "red_zone_caves": [speleothem("song_stalagmite", "red_zone_caves", "crimson_vein_stone", "varied_dark_slate", "crimson_vein_stone_wall", 3, 7, False, 50),
                       speleothem("song_stalactite", "red_zone_caves", "crimson_vein_stone", "varied_dark_slate", "crimson_vein_stone_wall", 3, 9, True, 60),
                       wall_plant("song_wall_vine", "orange_sift_vine", 3, tries=24, min_len=1, max_len=4, min_y=-20, max_y=40)],
    "resonant_vaults": [speleothem("vault_stalagmite", "resonant_vaults", "void_stone", "polished_void_stone", "void_stone_wall", 5, 12, False, 110),
                        speleothem("vault_stalactite", "resonant_vaults", "void_stone", "smooth_void_stone", "void_stone_wall", 5, 14, True, 130),
                        ceiling_crystals("vault_ceiling_charoite", "resonant_vaults", 40)],
    "spirit_deeps": [speleothem("deeps_stalagmite", "spirit_deeps", "violet_strata", "magma_vein_slate", "violet_strata_wall", 3, 9, False, 50),
                     speleothem("deeps_stalactite", "spirit_deeps", "violet_strata", "magma_vein_slate", "violet_strata_wall", 3, 10, True, 60),
                     ceiling_crystals("deeps_ceiling_charoite", "spirit_deeps", 30),
                     wall_plant("deeps_wall_vine", "carapace_vine", 3, tries=24, min_len=1, max_len=5, min_y=-62, max_y=10)],
}
for _b, _f in SPELEOTHEMS.items():
    CAVE_FEATURES[_b] = CAVE_FEATURES.get(_b, []) + _f


CAVE_FEATURES["resonant_vaults"] = CAVE_FEATURES["resonant_vaults"] + [
    farm_plant("vault_charoite", provider("charoite_cluster", facing="up", waterlogged="false"), 10, UNDER_FLOOR, []),
    farm_plant("vault_soul_crystal", provider("soul_crystal_block"), 3, UNDER_FLOOR, []),
    cave_patch("vault_red_sculk", provider("red_sculk"), provider("red_sculk_vein", down="true"), 3, (1, 3)),
]
CAVE_FEATURES["spirit_deeps"] = CAVE_FEATURES["spirit_deeps"] + [
    cave_patch("deeps_red_sculk", provider("red_sculk"), provider("red_sculk_vein", down="true"), 8, (3, 6), 0.45),
    farm_plant("deeps_charoite", provider("charoite_cluster", facing="up", waterlogged="false"), 6, UNDER_FLOOR, []),
    farm_plant("deeps_glow_grass", provider("glowshade_short_grass"), 40, UNDER_FLOOR, []),
]

def caldera_ore(name, ore, size, count, lo, hi):
    """Ores in the Soul Caldera's rift walls (magma vein slate) and plateau stone."""
    targets = [{"state": ore, "target": {"predicate_type": "minecraft:block_match", "block": f"pysift:{b}"}}
               for b in ("magma_vein_slate", "ember_basalt", "void_stone")]
    wj(D / f"worldgen/feature/{name}.json", {"type": "minecraft:ore", "discard_chance_on_air_exposure": 0.0,
                                               "size": size, "targets": targets})
    wj(D / f"worldgen/placed_feature/{name}.json", {"feature": f"pysift:{name}", "placement": [
        {"type": "minecraft:count", "count": count}, {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                       "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
        {"type": "minecraft:biome"}]})
    return f"pysift:{name}"


ORE_FEATURES = {"violet_slate_abyss": [
    soul_crystal_ore("soul_crystal_surface", 5, uniform(0, 1), [
        {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"},
        {"type": "minecraft:offset", "x": 0, "y": -1, "z": 0}]),
    soul_crystal_ore("soul_crystal_buried", 8, 3, [
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                       "min_inclusive": {"absolute": -40}, "max_inclusive": {"absolute": 60}}}]),
], "soul_caldera": [
    # patina ore (user: replaces argent ore): weathered green (oxidation 1) near the surface in the rift walls,
    # fresh breccia (oxidation 0) deeper down near the spirit liquid
    caldera_ore("patina_ore_caldera_walls", state("patina_ore", oxidation="1"), 6, 6, 40, 90),
    caldera_ore("patina_ore_caldera", state("patina_ore", oxidation="0"), 5, 3, 30, 62),
    soul_crystal_ore("soul_crystal_caldera", 4, uniform(0, 2), [
        {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"},
        {"type": "minecraft:offset", "x": 0, "y": -1, "z": 0}]),
]}

# the deep layers keep the surface biomes' underground ores (their depth bands now replace the surface biome underground)
ORE_FEATURES["resonant_vaults"] = ["pysift:soul_crystal_buried"]
ORE_FEATURES["spirit_deeps"] = ["pysift:soul_crystal_buried"]
ORE_FEATURES["withered_hollows"] = ["pysift:patina_ore_caldera"]

SOUND_ALIAS = {"withered_hollows": "red_zone_caves", "resonant_vaults": "red_zone_caves", "spirit_deeps": "red_zone_caves"}


def audio(name):
    """背景音樂與環境音：模組自己的音效 ID（ModSounds），實際聲音在 sounds.json（tools/worldgen/build_sift_audio.py）。
    新的地底生態域暫時沿用 red_zone_caves 的音效（SOUND_ALIAS），之後有自己的音檔再拆開。"""
    name = SOUND_ALIAS.get(name, name)
    return {
        "minecraft:audio/ambient_sounds": {
            "loop": f"pysift:ambient.the_sift.{name}.loop",
            "mood": {"sound": f"pysift:ambient.the_sift.{name}.mood", "tick_delay": 6000, "block_search_extent": 8, "offset": 2.0},
            "additions": {"sound": f"pysift:ambient.the_sift.{name}.additions", "tick_chance": 0.0111}},
        "minecraft:audio/background_music": {"default": {"sound": f"pysift:music.the_sift.{name}", "min_delay": 12000, "max_delay": 24000}},
    }


def biome(name, temperature, downfall, rain, sky, fog, water, spawn_attr):
    wj(D / f"worldgen/biome/{name}.json", {
        "attributes": {**spawn_attr, **audio(name), "minecraft:visual/sky_color": SKY_COLOR, "minecraft:visual/fog_color": SKY_FOG,
                       **({"minecraft:visual/ambient_particles": {"modifier": "append", "argument": [
                           {"particle": {"type": AMBIENT[name][0]}, "probability": AMBIENT[name][1]}]}} if name in AMBIENT else {})},
        "carvers": [],
        "downfall": downfall,
        "effects": {"water_color": water},
        # step 1 = lakes (spirit ponds), step 2 = local_modifications (spires, like vanilla boulders),
        # step 9 = vegetal_decoration
        # step 6 = underground_ores
        "features": [[], POND_FEATURES.get(name, []), SPIRE_FEATURES.get(name, []) + [SOUL_GEODE] + ([SINKHOLE] if name in SINKHOLE_BIOMES else [])] + [[], [], [], ORE_FEATURES.get(name, []) + [SIFTITE_ORE]
                    + (CHAROITE if name == "violet_slate_abyss" else []), [], []]
                    + [VEGETATION.get(name, []) + GLOW_FEATURES.get(name, []) + CAVE_FEATURES.get(name, []) + FARM_FEATURES
                       + (["pysift:red_sculk_patch"] if name in RED_SCULK_BIOMES else [])
                       + ([] if name in CAVE_FEATURES else [WILD_RIFT]) + LANDMARK_FEATURES.get(name, []), []],
        "has_precipitation": rain,
        "temperature": temperature,
    })


biome("crimson_strata_canyon", 2.0, 0.0, False, "#5a1f33", "#3a1426", "#7a3b55",
      spawns(monster=[("dartback", 50, 1, 3), ("fusefly", 40, 1, 2), ("prickle", 30, 1, 2),
                      ("nester", 8, 1, 1), ("seedling", 15, 2, 4), ("sprout", 15, 2, 3)],
             creature=[("blub", 20, 2, 3)]))
biome("violet_slate_abyss", 0.3, 0.2, False, "#2e2838", "#1d1828", "#4a3d6b",
      spawns(monster=[("sentinel", 20, 1, 1), ("stalker", 30, 1, 2), ("tuner", 15, 1, 1), ("hunter", 10, 1, 1)],
             creature=[("echo_golem", 10, 1, 1), ("blub", 15, 2, 3)]))          # each Echo Golem brings 1-2 Singers (EchoGolemEntity)
biome("willow_grove", 0.7, 0.8, True, "#8a7aa8", "#c497b4", "#7fd0d6",
      spawns(creature=[("blub", 40, 2, 4), ("nuzzle", 20, 1, 2), ("pollinator", 20, 1, 2), ("slabber", 25, 2, 3)],
             monster=[("roamroot", 8, 1, 1), ("bloombud", 20, 1, 2)]))
biome("red_zone_caves", 1.2, 0.4, False, "#4a1622", "#3a1018", "#7a3b55",
      spawns(monster=[("stalker", 30, 1, 2), ("prickle", 20, 1, 2), ("fusefly", 15, 1, 1), ("tuner", 10, 1, 1)],
             creature=[("blub", 10, 1, 2), ("echo_golem", 6, 1, 1)]))
biome("withered_hollows", 0.6, 0.0, False, "#26263a", "#1c1c2c", "#34405e",
      spawns(monster=[("stalker", 25, 1, 2), ("hunter", 15, 1, 1), ("prickle", 15, 1, 2)],
             creature=[("mourner", 5, 1, 1), ("blub", 5, 1, 2)]))      # the shallows rot: a Mourner now and then
biome("resonant_vaults", 1.0, 0.3, False, "#2a2244", "#1a1430", "#6a4a9a",
      spawns(monster=[("sentinel", 20, 1, 1), ("tuner", 20, 1, 1), ("hunter", 12, 1, 1), ("stalker", 12, 1, 2)],
             creature=[("echo_golem", 20, 1, 2), ("blub", 5, 1, 2)]))   # each Echo Golem brings 1-2 Singers
biome("spirit_deeps", 1.6, 0.8, False, "#3a1630", "#2a0e22", "#8a3a8a",
      spawns(monster=[("fusefly", 25, 1, 2), ("wobble", 20, 1, 2), ("trapper", 10, 1, 1), ("sentinel", 10, 1, 1)],
             creature=[("blub", 25, 2, 3), ("lootkin", 4, 1, 1)]))
biome("lullaby_hills", 1.4, 0.3, False, "#6a2a48", "#4a1c34", "#d06a8c",
      spawns(monster=[("dartback", 30, 1, 2), ("prickle", 25, 1, 2), ("seedling", 15, 2, 3), ("sprout", 15, 2, 3),
                      ("fusefly", 20, 1, 2)],
             creature=[("echo_golem", 14, 1, 2), ("blub", 20, 2, 3)]))
biome("soul_caldera", 2.0, 0.0, False, "#1e1a2a", "#2a2440", "#5fd8e8",
      spawns(monster=[("stalker", 30, 1, 2), ("fusefly", 25, 1, 2), ("prickle", 10, 1, 1)],
             creature=[("echo_golem", 6, 1, 1), ("blub", 10, 1, 2)]))
biome("amber_dunes", 2.0, 0.0, False, "#c98a5a", "#a8704a", "#6fb0c0",
      spawns(monster=[("scavenger", 30, 1, 2), ("hurler", 20, 1, 1), ("wobble", 25, 1, 2), ("trapper", 10, 1, 1)],
             creature=[("lootkin", 6, 1, 1), ("blub", 25, 2, 4)]))

# ---- material (surface) rule ----
ON_FLOOR, NOT_UNDERWATER = "minecraft:on_floor", "minecraft:not_underwater"
WITHIN = lambda depth: {"type": "minecraft:stone_depth", "add_surface_depth": False, "offset": depth,
                        "secondary_depth_range": 0, "surface_type": "floor"}
block = lambda s: {"type": "minecraft:block", "result_state": s}
cond = lambda c, then: {"type": "minecraft:condition", "if_true": c, "then_run": then}
seq = lambda *rules: {"type": "minecraft:sequence", "sequence": list(rules)}
in_biome = lambda b, then: cond({"type": "minecraft:biome", "biome_is": f"pysift:{b}"}, then)

NOISE = lambda lo, hi=1.0e9: {"type": "minecraft:noise_threshold", "noise": "minecraft:surface",
                              "min_threshold": lo, "max_threshold": hi}
# winding paths (reference video): the contour where pysift:the_sift_paths crosses 0, PATH_HALF_WIDTH on each side.
# Path floors are not in #supports_vegetation, so no plants grow on them.
PATH_HALF_WIDTH = 0.045
ON_PATH = {"type": "minecraft:noise_threshold", "noise": "pysift:the_sift_paths",
           "min_threshold": -PATH_HALF_WIDTH, "max_threshold": PATH_HALF_WIDTH}
CRIMSON_PATH = state("banded_mudstone", banding=0)       # pale reddish-brown earth
VIOLET_PATH = state("ash_marble", veining=0)             # pale stone
GROVE_PATH = state("cracked_sandstone", crack=0)         # warm tan

# Lullaby Hills (user design): void-capped crimson on every top surface, crimson vein stone below (the canyon walls),
# and a canyon floor in two layers: a dry land layer (Y70) with the road at the wall foot, then a river layer.
# Floor materials go from the water out to the wall foot:
#   aurum ore richness 1 (river bed, water's edge) -> richness 0 (bank) -> bleached sandstone (bleach 0 with a little
#   bleach 1; the half step and most of the land layer) -> ash marble veining 0 (the road under the wall) -> void cap (tops)
# The bands follow |canyon noise| (the same noise and coordinates as the terrain's LULLABY_CANYON), so they line up with
# the layers of the terrain. Every border blends naturally (user): A -> 25 % B -> 75 % B -> B, chosen block by block
# with a fine "dither" noise; the 25 / 75 % shares drift by about +-12 % from place to place (the low surface noise).
LULLABY_TOP = state("capped_crimson_vein_stone")
LULLABY_WALL, LULLABY_WALL_ALT = state("crimson_vein_stone", crimson_spread=4), state("crimson_vein_stone", crimson_spread=3)
wj(D / "worldgen/noise/the_sift_dither.json", {"base_amplitude": 1.0, "base_octave": 0, "octave_count": 1})
DITHER_SD = 0.38           # spread of the dither noise (measured on the test server); turns a share into a threshold
DITHER_JITTER = 0.12       # local drift of every share


def dither_threshold(share):
    """Noise value that the dither noise exceeds on `share` of the blocks (normal approximation)."""
    from statistics import NormalDist
    return DITHER_SD * NormalDist().inv_cdf(1.0 - share)


def mix(share, a, b):
    """Rule: b on about `share` of the blocks, a on the rest; the share drifts by +-DITHER_JITTER from place to place."""
    def pick(p):
        if p <= 0.0:
            return a
        if p >= 1.0:
            return b
        return seq(cond({"type": "minecraft:noise_threshold", "noise": "pysift:the_sift_dither",
                         "min_threshold": dither_threshold(p), "max_threshold": 1.0e9}, b), a)
    return seq(cond(NOISE(0.0), pick(min(1.0, share + DITHER_JITTER))), pick(max(0.0, share - DITHER_JITTER)))


def canyon_band(lo, hi, rule):
    """Run `rule` where lo <= |canyon noise| < hi (both signs of the noise)."""
    band = lambda a, b: {"type": "minecraft:noise_threshold", "noise": "pysift:the_sift_lullaby_canyon",
                         "min_threshold": a, "max_threshold": b}
    return seq(cond(band(lo, hi), rule), cond(band(-hi, -lo), rule))


def noise_band(noise):
    """band(lo, hi, rule) for one sign of a noise: rule where lo <= noise < hi."""
    return lambda lo, hi, rule: cond({"type": "minecraft:noise_threshold", "noise": noise,
                                      "min_threshold": lo, "max_threshold": hi}, rule)


def blended_bands(materials, borders, width, band=canyon_band, start=0.0):
    """materials[i] lies between borders[i-1] and borders[i] (|canyon noise| unless another band is given);
    each border blends over 2 x width."""
    canyon_band = band
    edges = [start] + borders + [1.0e9]
    parts = []
    for i, m in enumerate(materials):
        lo, hi = edges[i], edges[i + 1]
        inner_lo = lo + width if i > 0 else lo
        inner_hi = hi - width if i < len(materials) - 1 else hi
        if i > 0:                                              # just past the border: 75 % this material, 25 % the previous
            parts.append(canyon_band(lo, inner_lo, mix(0.75, materials[i - 1], m)))
        parts.append(canyon_band(inner_lo, inner_hi, m))
        if i < len(materials) - 1:                             # just before the next border: 25 % of the next material
            parts.append(canyon_band(inner_hi, hi, mix(0.25, m, materials[i + 1])))
    return seq(*parts)


SANDSTONE = mix(0.15, block(state("bleached_sandstone", bleach=0)), block(state("bleached_sandstone", bleach=1)))
LULLABY_BORDERS = [0.03, 0.05, 0.105, 0.133]   # water's edge | bank / half step | land layer / road | wall
LULLABY_BLEND = 0.008                          # |canyon| per blend step (~2 blocks on the canyon floor)
# the river bed itself (|canyon| < water's edge) gets richer towards the middle of the river (user): richness 4 (solid
# ore) -> 3 -> 2 -> 1 at the water's edge, blended block by block like every other border
RIVER_BED = blended_bands([block(state("aurum_ore", richness=r)) for r in (4, 3, 2, 1)], [0.008, 0.015, 0.022], 0.003)
FLOOR_BANDS = [RIVER_BED, block(state("aurum_ore", richness=0)), SANDSTONE, block(state("ash_marble", veining=0))]
WALL_STONE = mix(0.3, block(LULLABY_WALL), block(LULLABY_WALL_ALT))
LULLABY_RULE = seq(
    cond(ON_FLOOR, blended_bands(FLOOR_BANDS + [block(LULLABY_TOP)], LULLABY_BORDERS, LULLABY_BLEND)),
    # just under the canyon floor (the faces of the half step and the bank): the floor's own material
    cond(WITHIN(3), canyon_band(0.0, LULLABY_BORDERS[-1],
                                blended_bands(FLOOR_BANDS, LULLABY_BORDERS[:-1], LULLABY_BLEND))),
    cond(WITHIN(26), WALL_STONE))   # walls are up to ~22 tall
path = lambda floor: cond(ON_FLOOR, cond(ON_PATH, block(floor)))

# Crimson canyon (buttes). Two-tone caps (user): the layer under a cap continues the colour of the cap's lower half -
# blue (teal) under caps whose side is pink above / blue below, pink under caps that are blue above / pink below.
# Every shelf mixes all two-tone caps block by block, tones as random as possible. A column makes the same choice for
# its cap and the 3 blocks under it because every choice is a 2D noise threshold at that column.
wj(D / "worldgen/noise/the_sift_dither_tone.json", {"base_amplitude": 1.0, "base_octave": 0, "octave_count": 1})
wj(D / "worldgen/noise/the_sift_dither_layer.json", {"base_amplitude": 1.0, "base_octave": 0, "octave_count": 1})


def pick(noise, rules):
    """One of `rules`, each on about 1 / len(rules) of the columns (a fine noise ~ the dither noise's spread)."""
    parts = [cond({"type": "minecraft:noise_threshold", "noise": noise, "min_threshold": dither_threshold((i + 1) / len(rules)),
                   "max_threshold": 1.0e9}, r) for i, r in enumerate(rules[:-1])]
    return seq(*parts, rules[-1])


# user: blue layers are silted strata only (no teal / abyssal strata); pink layers and walls are ember stone (no crimson strata)
BLUE_LAYER = pick("pysift:the_sift_dither_layer", [block(state("silted_strata", silt=0)), block(state("silted_strata", silt=1))])
PINK_LAYER = block(state("ember_stone", heat=0))
# Caps whose side is pink above / blue below sit on a blue (silted) layer, caps blue above / pink below on a pink (ember)
# layer. Which of the two families a place gets is decided in PATCHES (the_sift_cap_tone, ~16 blocks), blended 25 / 75 %
# at the borders; inside a family the tone is random block by block. (A per-block family choice made the layer under
# the caps alternate blue / pink every column - vertical stripes down every step face.)
# Lower half as SHOWN in game (model face rotation applied; the canyon cap's side is turned 90 degrees, so the raw
# texture's right edge is its bottom): canyon cap, rose, mottled, deep teal -> blue below; teal cap -> pink below.
wj(D / "worldgen/noise/the_sift_cap_tone.json", {"base_amplitude": 1.0, "base_octave": -4, "octave_count": 2,
                                                 "amplitude_modifiers": [1.0, 0.5]})
BLUE_BOTTOM_CAPS = pick("pysift:the_sift_dither_tone", [block(state("capped_crimson_strata", facing="up", tone=t))
                                                        for t in ("rose", "mottled", "deep_teal")] + [block(CRIMSON_TOP)])
PINK_BOTTOM_CAPS = block(state("capped_crimson_strata", facing="up", tone="teal"))
CAP_FAMILIES = [(PINK_BOTTOM_CAPS, PINK_LAYER), (BLUE_BOTTOM_CAPS, BLUE_LAYER)]
CAP_MIX = {part: blended_bands([family[part] for family in CAP_FAMILIES], [0.0], 0.06,
                               band=noise_band("pysift:the_sift_cap_tone"), start=-1.0e9) for part in (0, 1)}
# floor patches: two-tone caps (the canyon cap alone, or the full random cap mix) and two plain blocks
FLOOR_PATCHES = [(block(state("silted_strata", silt=1)), block(CRIMSON_UNDER)),
                 (block(CRIMSON_TOP), BLUE_LAYER),
                 (CAP_MIX[0], CAP_MIX[1]),
                 (block(state("banded_mudstone", banding=1)), block(CRIMSON_UNDER))]
BUTTE_BAND, PATCH_BAND = noise_band("pysift:the_sift_buttes"), noise_band("pysift:the_sift_canyon_patches")
BUTTE_RISES = [(0.04, 78), (0.13, 89), (0.22, 100)]      # (butte noise where a wall starts, shelf height); terrain uses it too


def canyon_layer(part):
    """part 0 = the surface block, 1 = the 3 blocks under it; both built from the same choices, so they match."""
    floor = blended_bands([m[part] for m in FLOOR_PATCHES], [-0.18, 0.1, 0.28], 0.04, band=PATCH_BAND, start=-1.0e9)
    return blended_bands([floor, CAP_MIX[part]], [BUTTE_RISES[0][0] + 0.004], 0.011, band=BUTTE_BAND, start=-1.0e9)


CANYON_WALL = block(state("ember_stone", heat=0))
CANYON_RULE = seq(
    path(CRIMSON_PATH),
    cond(ON_FLOOR, canyon_layer(0)),
    cond(WITHIN(3), canyon_layer(1)),                    # continues the colour of the cap's lower half
    cond(WITHIN(26), CANYON_WALL))                       # walls are up to ~34 tall from the floor, ~12 per shelf

# Soul Caldera (user palette: cool basalt greys ~70 %, scorched violet-red ~20 %, soul-cyan light ~10 %, a little warm
# ember on the volcano's rim). Bands read the same noises as the terrain (rift: |noise|, volcano: raw), every border blends.
# rift / volcano thresholds, shared with the terrain splines below
SOUL_RIFT_FLOOR, SOUL_RIFT_BANK, SOUL_RIFT_WALL = 0.022, 0.028, 0.051   # |rift noise|: channel floor | bank | plateau
# The volcano is a true cone: on a grid of VOLCANO_CELL x VOLCANO_CELL cells, a repeating gradient gives the distance to
# the cell's centre and a spline turns it into cone, rim and crater. Whether a cell gets a volcano is read AT ITS CENTRE
# (the ridges / temperature noises shifted to the centre), so a cone is either whole or absent - only big patches, whose
# core is deep enough at the centre, get one. The crater lake is filled flat by SoulCraterFeature (same grid, same numbers).
# Ridges (weirdness) is our own noise sampled at scale 1, so surface rules can read it too (biome edge, crater lake).
SOUL_WEIRDNESS = 0.22                              # weirdness below -this (and hot) is the Soul Caldera
SOUL_HEAT = 0.25                                   # ... where temperature is above this; biome and terrain weight share it
CORE_RIDGES = (-0.235, -0.225)                     # ridges at the cell centre: full volcano below the first, none above the second
CORE_HEAT = (0.255, 0.265)                         # temperature at the cell centre: none below the first, full above the second
VOLCANO_CELL = 256                                 # one possible volcano per cell (SoulCraterFeature.CELL)
VOLCANO_JITTER = 80                                # x the jitter noise (~ +-0.5): centre moves up to ~40 blocks
EDGE_CHECK = 56                                    # probes this far from the (jittered) centre must also be biome core
CRATER_FLOOR, LAKE_LEVEL = 112, 115                # flat crater floor; the lake fills it up to LAKE_LEVEL (SoulCraterFeature)
CONE_PROFILE = [(0, CRATER_FLOOR), (13, CRATER_FLOOR), (20, 128), (23, 129), (34, 118), (52, 100)]   # (distance, height)
CONE_FOOT = 78                                     # distance where the cone meets the rifted plateau
CONE_YS = [90, 104, 120]                           # surface heights where the cone's materials change
EDGE_BLEND = (0.02, 0.05)                          # ridges past the biome edge where the soul ground still speckles in
ridge_below = lambda v: {"type": "minecraft:noise_threshold", "noise": "pysift:the_sift_ridge",
                         "min_threshold": -1.0e9, "max_threshold": v}
ridge_in = lambda a, b: {"type": "minecraft:noise_threshold", "noise": "pysift:the_sift_ridge", "min_threshold": a, "max_threshold": b}


def rift_band(lo, hi, rule):
    band = lambda a, b: {"type": "minecraft:noise_threshold", "noise": "pysift:the_sift_soul_rift", "min_threshold": a, "max_threshold": b}
    return seq(cond(band(lo, hi), rule), cond(band(-hi, -lo), rule))


# user: magma vein slate grades from the plateau into the rift, veins growing inward; the full face (vein 3) is the rarest
VEIN = lambda v: block(state("magma_vein_slate", vein=v))
LAVA_FIELD = block(state("ember_basalt"))   # cooled lava plain (user: one block; plain / speckled are its random textures)
SCORCHED = mix(0.3, block(state("crimson_capped_void_stone")), VEIN(0))   # burnt by the souls
ASH = block(state("gray_capped_void_stone", facing="up"))
EMBER = mix(0.5, block(state("warm_capped_ember_stone", facing="up")), block(state("crimson_capped_ember_stone", facing="up")))
# plateau floors by |rift|, outside in: lava field -> burnt rim (vein 0) -> bank (vein 1) -> bed (vein 2) -> a thin
# centre line where a quarter is vein 3
SOUL_PLAIN = blended_bands([mix(0.25, VEIN(2), VEIN(3)), VEIN(2), mix(0.35, VEIN(1), VEIN(2)), VEIN(1), SCORCHED, LAVA_FIELD],
                           [0.006, 0.014, SOUL_RIFT_FLOOR, SOUL_RIFT_WALL - 0.004, SOUL_RIFT_WALL + 0.03], 0.003, band=rift_band)
# volcano floors (by volcano noise): plain -> rusty scoria slopes getting rustier -> ash rim with warm embers -> burnt caldera
def height_bands(materials, ys, width=3):
    """materials[i] lies between ys[i-1] and ys[i] (surface Y); each border blends 25 / 75 % over 2 x width blocks."""
    above = lambda y: {"type": "minecraft:y_above", "anchor": {"absolute": y}, "surface_depth_multiplier": 0,
                       "add_stone_depth": False}
    parts = []
    for i in range(len(ys) - 1, -1, -1):
        lo, hi = materials[i], materials[i + 1]
        parts += [cond(above(ys[i] + width), hi), cond(above(ys[i]), mix(0.75, lo, hi)),
                  cond(above(ys[i] - width), mix(0.25, lo, hi))]
    return seq(*parts, materials[0])


SOUL_FLOORS = height_bands(
    [SOUL_PLAIN,
     mix(0.4, block(state("rusted_dark_cobble", rust=0)), block(state("rusted_dark_cobble", rust=1))),
     mix(0.4, block(state("rusted_dark_cobble", rust=2)), block(state("rusted_dark_cobble", rust=3))),
     mix(0.25, ASH, EMBER)],
    CONE_YS)
SOUL_WALL = seq(cond(WITHIN(10), mix(0.3, VEIN(0), VEIN(1))), cond(WITHIN(30), mix(0.4, VEIN(1), VEIN(2))))


def speckle(share, rule):
    """rule on ~share of the blocks, otherwise fall through to the next rule."""
    return cond({"type": "minecraft:noise_threshold", "noise": "pysift:the_sift_dither",
                 "min_threshold": dither_threshold(share), "max_threshold": 1.0e9}, rule)


# just outside the biome (ridges a little above -SOUL_WEIRDNESS) the cooled lava still speckles into the neighbour
SOUL_EDGE = cond(ON_FLOOR, seq(
    cond(ridge_in(-SOUL_WEIRDNESS - 0.01, -SOUL_WEIRDNESS + EDGE_BLEND[0]), speckle(0.5, LAVA_FIELD)),
    cond(ridge_in(-SOUL_WEIRDNESS + EDGE_BLEND[0], -SOUL_WEIRDNESS + EDGE_BLEND[1]), speckle(0.2, LAVA_FIELD))))
# user: spirit liquid in the rifts, over magma vein slate - a 1-deep stream along the rift's centre line, flush with the
# flat rift bed (only below y 80, so never on the cone's slopes where it would spill)
RIFT_STREAM = {"type": "minecraft:not", "invert": {"type": "minecraft:y_above", "anchor": {"absolute": 80},
                                                   "surface_depth_multiplier": 0, "add_stone_depth": False}}
SOUL_RULE = seq(cond(RIFT_STREAM, rift_band(0.0, 0.006, seq(cond(ON_FLOOR, block(state("spirit_liquid", level=0))),
                                                          cond(WITHIN(3), mix(0.25, VEIN(2), VEIN(3)))))),
                cond(ON_FLOOR, SOUL_FLOORS),
                cond(WITHIN(3), block(state("ember_basalt"))),
                SOUL_WALL)                                     # rift walls ~25 tall, the caldera wall deeper (void stone below)

CEILING = {"type": "minecraft:stone_depth", "add_surface_depth": False, "offset": 0, "secondary_depth_range": 0,
           "surface_type": "ceiling"}

# Cave materials (v2.1.0, user: colours must not jump). Average colours (RGB): void stone 60 62 70, dark slate 91 93 94,
# varied dark slate 106 120 120, gray strata 120 137 141 | crimson vein stone 129 88 102, canyon-capped crimson 173 156 161 |
# violet strata 87 75 88, magma vein slate 120 90 130. So the ladder runs cool grey -> rose grey -> violet grey -> violet,
# every step moves one property at a time, and each layer's floor already holds ~15-25 % of its neighbours' blocks, so a
# layer border is a gradient of shares, not a line. The old teal silted strata (78 197 189) is gone from the caves.
B = lambda name, **props: block(state(name, **props))
GREY, SLATE, VARIED = B("gray_strata", tone="teal"), B("dark_slate", fade=0), B("varied_dark_slate")
ROSE, CAP, VIOLET = B("crimson_vein_stone", crimson_spread=4), block(CRIMSON_TOP), B("violet_strata")
POLISHED, SMOOTH = B("polished_void_stone"), B("smooth_void_stone")
VEIN0, VEIN1 = B("magma_vein_slate", vein=0), B("magma_vein_slate", vein=1)
ABYSS = noise_band("pysift:the_sift_abyss")           # the same noise that picks vaults vs deeps (biome border at 0)
VAULT_FLOOR = mix(0.35, mix(0.3, POLISHED, SLATE), VIOLET)
DEEP_FLOOR = mix(0.4, mix(0.25, VEIN0, VIOLET), VEIN1)
# vaults -> deeps: bands of the abyss noise with the usual 25 / 75 % blend at the border (width 0.06 ~ 6 blocks each side)
DEEP_FLOORS = blended_bands([VAULT_FLOOR, DEEP_FLOOR], [0.0], 0.06, band=ABYSS, start=-1.0e9)
DEEP_CEILING = blended_bands([mix(0.3, SMOOTH, SLATE), mix(0.3, VIOLET, SMOOTH)], [0.0], 0.06, band=ABYSS, start=-1.0e9)
CAVE_RULES = {
    # shallows: cool greys, a little rose from the layer below
    "withered_hollows": seq(cond(ON_FLOOR, mix(0.12, mix(0.35, VARIED, SLATE), mix(0.3, GREY, ROSE))),
                            cond(WITHIN(2), mix(0.3, SLATE, VARIED)), cond(CEILING, mix(0.25, SLATE, VARIED))),
    # song caves: the user's crimson cap (its light rose-grey top) over rose stone, with grey above and violet below
    "red_zone_caves": seq(cond(ON_FLOOR, mix(0.12, mix(0.4, CAP, ROSE), mix(0.4, VARIED, VIOLET))),
                          cond(WITHIN(2), mix(0.3, ROSE, SLATE)), cond(CEILING, mix(0.3, ROSE, SLATE))),
    "deep": seq(cond(ON_FLOOR, DEEP_FLOORS), cond(WITHIN(2), mix(0.3, SLATE, VIOLET)), cond(CEILING, DEEP_CEILING)),
}
wj(D / "worldgen/material_rule/the_sift.json", seq(
    "minecraft:bedrock_floor",
    # underground layers: CAVE_RULES (below). Floors and ceilings only; walls stay void stone.
    in_biome("withered_hollows", CAVE_RULES["withered_hollows"]),
    in_biome("red_zone_caves", CAVE_RULES["red_zone_caves"]),
    in_biome("resonant_vaults", CAVE_RULES["deep"]),
    in_biome("spirit_deeps", CAVE_RULES["deep"]),
    cond({"type": "minecraft:above_preliminary_surface"}, seq(
        # crimson: buttes and hoodoos with banded caps, patchy floor, ember stone walls (CANYON_RULE)
        in_biome("crimson_strata_canyon", seq(SOUL_EDGE, CANYON_RULE)),
        # violet: violet-capped dark slate on top, dark slate below (same pair as the violet mesas)
        in_biome("violet_slate_abyss", seq(path(VIOLET_PATH), cond(ON_FLOOR, block(VIOLET_TOP)), cond(WITHIN(5), block(VIOLET_UNDER)))),
        # willow grove: crimson-capped strata on top, abyssal strata (depth=0) below
        in_biome("willow_grove", seq(path(GROVE_PATH), cond(ON_FLOOR, block(GROVE_TOP)), cond(WITHIN(6), block(GROVE_UNDER)))),
        in_biome("lullaby_hills", LULLABY_RULE),
        in_biome("soul_caldera", SOUL_RULE),
        # amber dunes: amber sand with pale sand patches, then sandstone
        in_biome("amber_dunes", seq(
            SOUL_EDGE,
            cond(WITHIN(3), seq(cond(NOISE(0.35), block(DUNE_ACCENT)), block(DUNE_SAND))),
            cond(WITHIN(6), block(DUNE_STONE)),
            cond(WITHIN(9), block(DUNE_DEEP)))),
    )),
    # steep canyon walls partly lie below the preliminary surface, where the rules above never run and the base void
    # stone showed through in black patches: any stone left in the canyon above Y58 is ember stone
    cond({"type": "minecraft:y_above", "anchor": {"absolute": 58}, "surface_depth_multiplier": 0, "add_stone_depth": False},
         in_biome("crimson_strata_canyon", block(state("ember_stone", heat=0)))),
))

# ---- noise settings: vanilla overworld router, with our own terrain shape ----
# The overworld density functions are copied into pysift:the_sift/... so caves, aquifers and the biome climate
# keep working. Only the terrain shape is replaced: no seas, no rivers, ponds only, mostly walkable land.
# Technique learned from Terralith (studied only; its license forbids copying its files, nothing here is copied):
# the terrain height is a spline over the SAME climate noises that pick the biomes, so every biome gets its own
# landform and the shapes blend smoothly at biome borders:
#   violet_slate_abyss (cold)  rolling hills            willow_grove (mild)   low flats with ponds
#   crimson canyon (hot, wet)  stepped terraces         amber_dunes (hot, dry) ridged dunes
#   + a very large "landform" noise on top: pond basins / the biome's own terrain / cliff-edged stepped plateaus
#   + pond hollows everywhere (below sea level 63 they fill with spirit liquid)
#   jaggedness -> 0 (no peaks), factor -> FACTOR (steep density gradient: the surface follows the spline closely)
# Splines take block heights here; to_offset() turns them into the router's offset (y = -64 + 128 * (1.5 + offset)).
FACTOR = 8.0
BIOME_ZOOM = 2.0       # climate noise frequency x2 = biomes half as wide as vanilla-sized ones
POND_START = 0.20      # pond noise above this digs a hollow ...
POND_BLOCKS = 12       # ... up to this many blocks deep
VANILLA_DF = VANILLA_NOISE.parent.parent / "density_function"
DF = "pysift:the_sift/terrain/"
to_offset = lambda y: (y + 64) / 128 - 1.5


def noise2d(name, scale=1.0):
    return {"type": "minecraft:noise", "noise": f"pysift:{name}", "shift_x": "minecraft:shift_x",
            "shift_z": "minecraft:shift_z", "xz_scale": scale, "y_scale": 0.0}


def spline(coordinate, *points):
    """points: (location, block height or nested spline, slope in blocks per unit location)."""
    return {"coordinate": coordinate, "points": [
        {"location": loc, "value": to_offset(v) if isinstance(v, (int, float)) else v,
         "derivative": slope / 128} for loc, v, slope in points]}


wj(D / "worldgen/noise/the_sift_hills.json", {"base_amplitude": 1.0, "base_octave": -9, "octave_count": 4,
                                              "amplitude_modifiers": [1.0, 1.0, 0.5, 0.25]})
wj(D / "worldgen/noise/the_sift_ponds.json", {"base_amplitude": 1.0, "base_octave": -6, "octave_count": 2})
# winding paths: the material rule turns the narrow band where this noise crosses 0 into a path floor (see PATH below)
wj(D / "worldgen/noise/the_sift_paths.json", {"base_amplitude": 1.0, "base_octave": -7, "octave_count": 2})
wj(D / "worldgen/noise/the_sift_dunes.json", {"base_amplitude": 1.0, "base_octave": -6, "octave_count": 2,
                                              "amplitude_modifiers": [1.0, 0.35]})
for old in (D / "worldgen/density_function/the_sift").rglob("*.json"):
    old.unlink()
wj(D / "worldgen/noise/the_sift_fissure.json", {"base_amplitude": 1.0, "base_octave": -5, "octave_count": 3,
                                               "amplitude_modifiers": [1.0, 0.6, 0.3]})
wj(D / "worldgen/noise/the_sift_landform.json", {"base_amplitude": 1.0, "base_octave": -8, "octave_count": 2,
                                                 "amplitude_modifiers": [1.0, 0.3]})
wj(D / "worldgen/density_function/the_sift/terrain/landform.json",
   {"type": "minecraft:cache", "input": noise2d("the_sift_landform")})
wj(D / "worldgen/density_function/the_sift/terrain/hills.json", {"type": "minecraft:cache", "input": noise2d("the_sift_hills")})
# ridged noise: |n| is 0 along thin winding lines -> dune crests
wj(D / "worldgen/density_function/the_sift/terrain/dune_ridge.json",
   {"type": "minecraft:cache", "input": {"type": "minecraft:abs", "input": noise2d("the_sift_dunes")}})
HILLS, RIDGE, LAND = DF + "hills", DF + "dune_ridge", DF + "landform"
# Lullaby Hills canyon: |noise| is 0 along long winding lines -> the canyon floors; it rises away from them through the
# land layer, the walls and the terraces up to the plateau. The surface rule reads the same noise (LULLABY_BORDERS, blended_bands).
# base_octave -7: about 128 blocks per noise period -> ~0.004 per block, so each 0.006 rise in the spline is a 1-2 block
# vertical wall and each shelf is ~9 blocks wide (-8 made the whole canyon a 100-block gentle slope)
wj(D / "worldgen/noise/the_sift_lullaby_canyon.json", {"base_amplitude": 1.0, "base_octave": -7, "octave_count": 2,
                                                       "amplitude_modifiers": [1.0, 0.25]})
wj(D / "worldgen/density_function/the_sift/terrain/lullaby_canyon.json",
   {"type": "minecraft:cache", "input": {"type": "minecraft:abs", "input": noise2d("the_sift_lullaby_canyon")}})
LULLABY_CANYON = DF + "lullaby_canyon"
# Soul Caldera (user: a broken basalt plateau cut by glowing rifts, ONE big volcano in the middle, spirit liquid as the lava).
# Rifts: |noise| is 0 along long winding lines, like the Lullaby canyon (base_octave -7: ~0.011 per block), but narrow and deep.
# Volcano: the peaks of a very low noise (base_octave -9) - one cone where it is high, a deep caldera where it is highest.
wj(D / "worldgen/noise/the_sift_soul_rift.json", {"base_amplitude": 1.0, "base_octave": -7, "octave_count": 2,
                                                  "amplitude_modifiers": [1.0, 0.3]})
# weirdness: vanilla minecraft:ridge (first octave -7 at xz_scale 0.25) == first octave -9 at scale 1, unshifted, so the
# surface rules (which sample noises at x, 0, z) see exactly the value the biomes and the terrain use
VANILLA_RIDGE = {"base_amplitude": 0.9147152149950137, "amplitude_modifiers": [1.0, 2.0, 1.0, 0.0, 0.0, 0.0]}
wj(D / "worldgen/noise/the_sift_ridge.json", {**VANILLA_RIDGE, "base_octave": -9, "octave_count": 6})
# temperature: vanilla first octave -10 at xz_scale 0.25 x BIOME_ZOOM 2 == first octave -11 at scale 1
assert BIOME_ZOOM == 2.0
wj(D / "worldgen/noise/the_sift_temperature.json", {"base_amplitude": 1.2453007926713473, "base_octave": -11, "octave_count": 6,
                                                    "amplitude_modifiers": [1.5, 0.0, 1.0, 0.0, 0.0, 0.0]})
wj(D / "worldgen/density_function/the_sift/terrain/soul_rift.json",
   {"type": "minecraft:cache", "input": {"type": "minecraft:abs", "input": noise2d("the_sift_soul_rift")}})
SOUL_RIFT = DF + "soul_rift"
# Crimson canyon buttes (user: random, irregular mesas and pillars instead of round feature mesas, Lullaby-style).
# The raw noise is a field of blobs of every size; a spline with flat shelves joined by 0.008 rises turns the blobs into
# mesas with vertical walls and 2-3 terraces (CANYON_BUTTES). The surface rule reads the same noise (BUTTE_BORDERS).
# 3 octaves give ragged, bay-cut edges; base_octave -7 -> mesas a few dozen blocks across.
wj(D / "worldgen/noise/the_sift_buttes.json", {"base_amplitude": 1.0, "base_octave": -7, "octave_count": 3,
                                               "amplitude_modifiers": [1.0, 0.45, 0.2]})
wj(D / "worldgen/density_function/the_sift/terrain/buttes.json", {"type": "minecraft:cache", "input": noise2d("the_sift_buttes")})
BUTTES = DF + "buttes"
# free-standing pillars (hoodoos) on the canyon floor: the peaks of a finer noise (~32 blocks per period). Terrain density
# is interpolated over 4-block cells, so anything thinner than ~6 blocks melts into a mound: the pillars are 6-10 wide.
wj(D / "worldgen/noise/the_sift_hoodoos.json", {"base_amplitude": 1.0, "base_octave": -5, "octave_count": 1})
wj(D / "worldgen/density_function/the_sift/terrain/hoodoos.json", {"type": "minecraft:cache", "input": noise2d("the_sift_hoodoos")})
HOODOOS = DF + "hoodoos"
# floor material patches (surface rule only)
wj(D / "worldgen/noise/the_sift_canyon_patches.json", {"base_amplitude": 1.0, "base_octave": -6, "octave_count": 2,
                                                       "amplitude_modifiers": [1.0, 0.4]})
# biome landforms (the "normal" terrain of each biome)
ROLLING = spline(HILLS, (-1.0, 62, 8), (0.0, 74, 16), (1.0, 92, 20))                  # violet: rolling hills
LOWLAND = spline(HILLS, (-1.0, 64, 3), (1.0, 72, 5))                                  # grove: flats, ponds
TERRACES = spline(HILLS, *[(loc, y, 0) for lo, hi, y in                               # canyon: flat steps
                           [(-1.0, -0.55, 66), (-0.45, -0.15, 72), (-0.05, 0.25, 79), (0.35, 0.6, 87), (0.7, 1.0, 96)]
                           for loc in (lo, hi)])
DUNES = spline(RIDGE, (0.0, 78, 0), (0.12, 74, -40), (0.4, 68, 0), (1.0, 66, 0))     # dunes: sharp crests


def stepped(base, steps):
    """A plateau of flat terraces (each `steps` blocks higher), chosen by the hills noise."""
    return spline(HILLS, *[(loc, base + i * steps, 0) for i, (lo, hi) in
                           enumerate([(-1.0, -0.35), (-0.25, 0.3), (0.4, 1.0)]) for loc in (lo, hi)])


def landform(normal, plateau, basin=62):
    """Terralith-style landform layer on top of each biome: a very large noise picks
    basin (low, pond-filled) -> the biome's normal terrain -> plateau with steep cliff edges.
    The narrow 0.04 band between 0.20 and 0.24 makes the plateau edge a cliff, not a slope."""
    return spline(LAND, (-1.0, spline(HILLS, (-1.0, basin, 0), (1.0, basin + 4, 0)), 0), (-0.55, normal, 0),
                  (0.20, normal, 0), (0.24, plateau, 0), (1.0, plateau, 0))


VIOLET = landform(ROLLING, stepped(92, 7))
GROVE = landform(LOWLAND, stepped(78, 5))
# canyon: floor Y66 with hoodoo pillars, butte shelves Y78 / Y89 / Y100 (user: tallest about Y100)
HOODOO_START = 0.45
CANYON_FLOOR = spline(HOODOOS, (-1.0, 66, 0), (HOODOO_START, 66, 0), (HOODOO_START + 0.02, 86, 0), (1.0, 96, 0))
CANYON_BUTTES = spline(BUTTES, (-1.0, CANYON_FLOOR, 0), (BUTTE_RISES[0][0], CANYON_FLOOR, 0),
                       *[pt for i, (loc, y) in enumerate(BUTTE_RISES)
                         for pt in ((loc + 0.008, y, 0),
                                    (BUTTE_RISES[i + 1][0] if i + 1 < len(BUTTE_RISES) else 1.0, y, 0))])
CANYON = landform(CANYON_BUTTES, CANYON_BUTTES)           # the landform layer only adds its pond basins here
DUNE_LAND = landform(DUNES, stepped(86, 6))
# Lullaby Hills cross-section (|canyon| -> block height): flat shelves joined by steep rises = vertical walls.
#   river bed 56..58 (spirit liquid up to 63) | bank 64 | half step 67 | land layer 70 (the road) | wall |
#   terraces 82 / 96 / 110 | plateau 125 with low hills on top
# measured in game: |canyon| changes ~0.011 per block, so a 0.065 shelf is ~6 blocks and a 0.006 rise is a vertical wall
LULLABY = spline(LULLABY_CANYON, (0.0, 56, 0), (0.025, 58, 0), (0.034, 64, 0), (0.048, 64, 0), (0.054, 67, 0), (0.066, 67, 0),
                 (0.072, 70, 0), (0.13, 70, 0), (0.136, 82, 0), (0.2, 82, 0), (0.206, 96, 0), (0.27, 96, 0),
                 (0.276, 110, 0), (0.34, 110, 0), (0.348, spline(HILLS, (-1.0, 124, 0), (1.0, 132, 6)), 0))
# Soul Caldera cross-sections. Rifts (|rift| -> height, user: at most ~6 deep): a channel 6 below the plateau (76-82),
# a bank 3 below it, then the plateau. Volcano (distance to its cell's centre -> height, CONE_PROFILE): a cone rising from
# the plateau at CONE_FOOT to the rim at 129, and a flat crater floor at CRATER_FLOOR inside.
SOUL_PLATEAU = spline(HILLS, (-1.0, 76, 0), (1.0, 82, 3))
RIFT_BED = spline(HILLS, (-1.0, 70, 0), (1.0, 76, 3))
RIFT_BANK = spline(HILLS, (-1.0, 73, 0), (1.0, 79, 3))
SOUL_RIFTED = spline(SOUL_RIFT, (0.0, RIFT_BED, 0), (SOUL_RIFT_FLOOR, RIFT_BED, 0), (SOUL_RIFT_BANK, RIFT_BANK, 0),
                     (SOUL_RIFT_WALL - 0.006, RIFT_BANK, 0),
                     (SOUL_RIFT_WALL, SOUL_PLATEAU, 0), (1.0, SOUL_PLATEAU, 0))
# offset from the volcano cell's centre along x / z (repeating gradient: -cell/2 .. cell/2 across every cell)
for axis in ("x", "z"):
    wj(D / f"worldgen/density_function/the_sift/terrain/volcano_d{axis}.json", {
        "type": "minecraft:gradient", "axis": axis, "tiling": "repeat", "from_coordinate": 0, "to_coordinate": VOLCANO_CELL,
        "from_value": -VOLCANO_CELL / 2, "to_value": VOLCANO_CELL / 2})
add, mul = (lambda a, b: {"type": "minecraft:add", "left": a, "right": b}), (lambda a, b: {"type": "minecraft:mul", "left": a, "right": b})


def at_centre(noise, ox=0, oz=0):
    """noise sampled at the cell's (unjittered) centre + (ox, oz): one value for the whole cell"""
    return {"type": "minecraft:noise", "noise": noise, "xz_scale": 1.0, "y_scale": 0.0,
            "shift_x": add(mul(-1.0, DF + "volcano_dx"), ox), "shift_z": add(mul(-1.0, DF + "volcano_dz"), oz)}


# random centre: shifted up to ~VOLCANO_JITTER/2 from the cell's middle by two noises read at the middle
for axis in ("x", "z"):
    wj(D / f"worldgen/noise/the_sift_volcano_j{axis}.json", {"base_amplitude": 1.0, "base_octave": -2, "octave_count": 1})
    wj(D / f"worldgen/density_function/the_sift/terrain/volcano_j{axis}.json", {"type": "minecraft:cache", "input": mul(
        VOLCANO_JITTER, at_centre(f"pysift:the_sift_volcano_j{axis}"))})
wj(D / "worldgen/density_function/the_sift/terrain/volcano_distance.json", {"type": "minecraft:cache", "input": {
    "type": "minecraft:sqrt", "input": add(
        {"type": "minecraft:square", "input": add(DF + "volcano_dx", mul(-1.0, DF + "volcano_jx"))},
        {"type": "minecraft:square", "input": add(DF + "volcano_dz", mul(-1.0, DF + "volcano_jz"))})}})
# away from the biome's edge: the core must hold at the (jittered) centre AND at four points EDGE_CHECK out (the cone)
PROBES = [(0, 0), (EDGE_CHECK, 0), (-EDGE_CHECK, 0), (0, EDGE_CHECK), (0, -EDGE_CHECK)]


def at_volcano(noise, ox, oz):
    return at_centre(noise, add(DF + "volcano_jx", ox), add(DF + "volcano_jz", oz))


def fold(kind, noise):
    out = at_volcano(noise, *PROBES[0])
    for ox, oz in PROBES[1:]:
        out = {"type": f"minecraft:{kind}", "left": out, "right": at_volcano(noise, ox, oz)}
    return {"type": "minecraft:cache", "input": out}


wj(D / "worldgen/density_function/the_sift/terrain/volcano_ridges.json", fold("max", "pysift:the_sift_ridge"))        # highest = nearest the edge
wj(D / "worldgen/density_function/the_sift/terrain/volcano_heat.json", fold("min", "pysift:the_sift_temperature"))   # coldest
SOUL_CONE = spline(DF + "volcano_distance", *[(d, h, 0) for d, h in CONE_PROFILE], (CONE_FOOT, SOUL_RIFTED, 0),
                   (VOLCANO_CELL, SOUL_RIFTED, 0))
HOT = spline("pysift:the_sift/vegetation", (-1.0, DUNE_LAND, 0), (-0.4, DUNE_LAND, 0), (-0.2, CANYON, 0), (1.0, CANYON, 0))
CLIMATE = spline(
    "pysift:the_sift/temperature", (-1.0, VIOLET, 0), (-0.4, VIOLET, 0), (-0.2, GROVE, 0), (0.3, GROVE, 0),
    (0.45, HOT, 0), (1.0, HOT, 0))
# Lullaby Hills take over where weirdness (ridges) is high, in the warm half (temperature > 0) - see the biome source.
# Blend: shape = climate + weight * (lullaby - climate); each spline lives in its own density function, written once.
raw_spline = lambda coordinate, *points: {"coordinate": coordinate, "points": [
    {"location": loc, "value": v, "derivative": 0.0} for loc, v in points]}
wj(D / "worldgen/density_function/the_sift/terrain/climate_shape.json", {"type": "minecraft:spline", "spline": CLIMATE})
wj(D / "worldgen/density_function/the_sift/terrain/lullaby_shape.json", {"type": "minecraft:spline", "spline": LULLABY})
WARM = raw_spline("pysift:the_sift/temperature", (-1.0, 0.0), (-0.08, 0.0), (0.02, 1.0), (1.0, 1.0))
wj(D / "worldgen/density_function/the_sift/terrain/lullaby_weight.json", {"type": "minecraft:cache", "input": {
    "type": "minecraft:spline", "spline": raw_spline("pysift:the_sift/ridges", (-1.0, 0.0), (0.38, 0.0), (0.46, WARM), (1.0, WARM))}})
SHAPE = {"type": "minecraft:add", "left": DF + "climate_shape", "right": {"type": "minecraft:mul", "left": DF + "lullaby_weight",
         "right": {"type": "minecraft:add", "left": DF + "lullaby_shape", "right": {"type": "minecraft:mul", "left": -1.0,
                                                                                     "right": DF + "climate_shape"}}}}
# Soul Caldera takes over where weirdness is LOW (below -SOUL_WEIRDNESS) in the hot part (temperature > 0.4), so it never
# overlaps the Lullaby Hills (high weirdness): shape += soul_weight * (soul_shape - climate_shape)
# soul_shape = rifted + core * (cone - rifted): the cone only rises in the biome's core
wj(D / "worldgen/density_function/the_sift/terrain/soul_rifted.json", {"type": "minecraft:spline", "spline": SOUL_RIFTED})
wj(D / "worldgen/density_function/the_sift/terrain/soul_cone.json", {"type": "minecraft:spline", "spline": SOUL_CONE})
CENTRE_RIDGES = raw_spline(DF + "volcano_ridges", (-1.0, 1.0), (CORE_RIDGES[0], 1.0), (CORE_RIDGES[1], 0.0), (1.0, 0.0))
wj(D / "worldgen/density_function/the_sift/terrain/soul_core.json", {"type": "minecraft:spline", "spline": raw_spline(
    DF + "volcano_heat", (-1.0, 0.0), (CORE_HEAT[0], 0.0), (CORE_HEAT[1], CENTRE_RIDGES), (1.0, CENTRE_RIDGES))})
wj(D / "worldgen/density_function/the_sift/terrain/soul_shape.json", {"type": "minecraft:add", "left": DF + "soul_rifted",
   "right": {"type": "minecraft:mul", "left": DF + "soul_core", "right": {"type": "minecraft:add", "left": DF + "soul_cone",
             "right": {"type": "minecraft:mul", "left": -1.0, "right": DF + "soul_rifted"}}}})
HOTTER = raw_spline("pysift:the_sift/temperature", (-1.0, 0.0), (SOUL_HEAT - 0.04, 0.0), (SOUL_HEAT + 0.04, 1.0), (1.0, 1.0))
wj(D / "worldgen/density_function/the_sift/terrain/soul_weight.json", {"type": "minecraft:cache", "input": {
    "type": "minecraft:spline", "spline": raw_spline("pysift:the_sift/ridges", (-1.0, HOTTER), (-SOUL_WEIRDNESS - 0.04, HOTTER), (-SOUL_WEIRDNESS + 0.04, 0.0), (1.0, 0.0))}})
SHAPE = {"type": "minecraft:add", "left": SHAPE, "right": {"type": "minecraft:mul", "left": DF + "soul_weight",
         "right": {"type": "minecraft:add", "left": DF + "soul_shape", "right": {"type": "minecraft:mul", "left": -1.0,
                                                                                  "right": DF + "climate_shape"}}}}
PONDS = {"type": "minecraft:mul", "right": -POND_BLOCKS / 128 / (1 - POND_START),
         "left": {"type": "minecraft:clamp", "min": 0.0, "max": 1.0 - POND_START,
                  "input": {"type": "minecraft:add", "left": noise2d("the_sift_ponds"), "right": -POND_START}}}
TERRAIN_OFFSET = {"type": "minecraft:add", "left": SHAPE, "right": PONDS}
SLOPED = "pysift:the_sift/sloped_cheese"
CAVE_ROOF = 7.0   # sloped_cheese value where caves may start; with FACTOR 8 it rises ~0.25 per block -> ~28 blocks deep


def bury_caves(final_density):
    """Keep caves well below the surface. Vanilla only opens cave entrances above sloped_cheese 1.5625 and full
    caves below it, but with our steep FACTOR that line sits ~6 blocks under the ground, so cheese caves broke
    through and left the surface full of hollows. Here: no entrances near the surface, caves (and noodle caves)
    only below CAVE_ROOF."""
    found = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") == "minecraft:range_choice" and n.get("input") == SLOPED:
                n["max_exclusive"] = CAVE_ROOF
                n["when_in_range"] = SLOPED
                found.append(n)
            for v in n.values():
                walk(v)
            if n.get("type") == "minecraft:min" and n.get("right") == "pysift:the_sift/caves/noodle":
                n["right"] = {"type": "minecraft:range_choice", "input": SLOPED, "min_inclusive": -1000000.0,
                              "max_exclusive": CAVE_ROOF, "when_in_range": 1.0,
                              "when_out_of_range": "pysift:the_sift/caves/noodle"}
                found.append(n)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(final_density)
    assert len(found) == 2, f"final_density layout changed ({len(found)} cave hooks found)"
    return final_density


# ---- cave shapes per layer (v2.1.0): each layer takes after a real kind of cave ----
# The vanilla cave terms (cheese chambers cut into bedding-plane slabs by cave_layer, 2D spaghetti tunnels, pillars) keep
# their structure; their constants become splines over the same wobbling depth the biomes use (biome_depth), so the cave
# shape changes exactly where the layer does and blends smoothly across the border:
#   withered hollows  joint-controlled FISSURES (karst grikes / slot caves): tall narrow cracks, thin tunnels, no chambers
#   red zone caves    PHREATIC TUBES (Mammoth Cave): fat winding horizontal passages, a few small rooms
#   resonant vaults   CATHEDRAL HALLS (Carlsbad, Son Doong): huge high chambers with rubble floors and many columns
#   spirit deeps      FLOODED LAKE CAVES (cenotes, Postojna): flat low chambers cut by bedding planes, partly under spirit liquid
# layer plateaus in biome_depth: each layer keeps its own cave recipe across most of its band; the recipes blend over the
# ~0.1 (13 block) gaps at the borders
LAYER_PLATEAUS = ((0.22, 0.38), (0.46, 0.64), (0.74, 1.4))     # withered, song caves, deep (vaults and deeps)
BIOME_DEPTH = "pysift:the_sift/biome_depth"


def layer_spline(w, r, deep):
    """DF: one value per layer, flat across the layer and smooth (zero slope) across the borders, over biome_depth."""
    points = []
    for (lo, hi), v in zip(LAYER_PLATEAUS, (w, r, deep)):
        points += [{"location": lo, "value": v, "derivative": 0.0}, {"location": hi, "value": v, "derivative": 0.0}]
    return {"type": "minecraft:spline", "spline": {"coordinate": BIOME_DEPTH, "points": points}}


def shape_caves(final_density):
    """Replace the vanilla cave constants by layer splines (see above)."""
    found = {"cheese": 0, "layer": 0, "spaghetti": 0, "pillars": 0}
    sp_extra = {"type": "minecraft:min",
                "left": {"type": "minecraft:add", "left": "pysift:the_sift/caves/spaghetti_2d",
                         "right": "pysift:the_sift/caves/spaghetti_roughness_function"},
                "right": "pysift:the_sift/caves/fissures"}

    def walk(n):
        if isinstance(n, dict):
            # cave_cheese + 0.27: chamber size (higher = fewer / smaller chambers)
            if n.get("type") == "minecraft:add" and n.get("right") == 0.27 and isinstance(n.get("left"), dict) \
                    and n["left"].get("noise") == "minecraft:cave_cheese":
                n["right"] = "pysift:the_sift/caves/cheese_offset"
                found["cheese"] += 1
            # 4 * square(cave_layer): bedding-plane slabs (higher = thinner slabs = flatter, lower rooms)
            if n.get("type") == "minecraft:mul" and n.get("right") == 4.0 and isinstance(n.get("left"), dict) \
                    and n["left"].get("type") == "minecraft:square":
                n["right"] = "pysift:the_sift/caves/layer_strength"
                found["layer"] += 1
            # tunnels: spaghetti_2d + roughness, now with a per-layer thickness offset and the fissures
            if n.get("type") == "minecraft:add" and n.get("left") == "pysift:the_sift/caves/spaghetti_2d" \
                    and n.get("right") == "pysift:the_sift/caves/spaghetti_roughness_function":
                n.clear()
                n.update({"type": "minecraft:min", "left": {"type": "minecraft:add", "left": {
                    "type": "minecraft:add", "left": "pysift:the_sift/caves/spaghetti_2d",
                    "right": "pysift:the_sift/caves/spaghetti_roughness_function"}, "right": "pysift:the_sift/caves/tunnel_offset"},
                    "right": "pysift:the_sift/caves/fissures"})
                found["spaghetti"] += 1
                return
            for v in n.values():
                walk(v)
            if n.get("type") == "minecraft:range_choice" and n.get("input") == "pysift:the_sift/caves/pillars":
                n["input"] = "pysift:the_sift/caves/pillars_layered"
                n["when_out_of_range"] = "pysift:the_sift/caves/pillars_layered"
                found["pillars"] += 1
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(final_density)
    assert all(v == 1 for v in found.values()), f"final_density layout changed: {found}"
    # the layer functions themselves (written beside the copied vanilla cave functions)
    CAVES = D / "worldgen/density_function/the_sift/caves"
    wj(CAVES / "cheese_offset.json", layer_spline(1.4, 0.38, 0.02))     # vanilla 0.27: none in the shallows, halls in the deep
    wj(CAVES / "layer_strength.json", layer_spline(4.0, 4.0, 2.2))      # vanilla 4.0
    wj(CAVES / "tunnel_offset.json", layer_spline(0.04, -0.10, -0.03))  # + thinner tunnels, - fatter ones
    wj(CAVES / "pillars_layered.json", {"type": "minecraft:add", "left": "pysift:the_sift/caves/pillars",
                                        "right": layer_spline(-5.0, -0.05, 0.14)})   # columns: none, few, many
    # fissures: near-vertical sheets where |noise| is small (y_scale 0.12 stretches the noise upwards), only in the withered layer
    wj(CAVES / "fissures.json", {"type": "minecraft:add",
        "left": {"type": "minecraft:add", "left": {"type": "minecraft:mul", "left": 11.0, "right": {
            "type": "minecraft:abs", "input": {"type": "minecraft:noise", "noise": "pysift:the_sift_fissure",
                                               "xz_scale": 1.0, "y_scale": 0.08}}}, "right": -0.7},
        "right": layer_spline(0.0, 6.0, 6.0)})   # only the withered layer is cracked
    return final_density


noise = json.loads(VANILLA_NOISE.read_text(encoding="utf-8"))
retarget = lambda text: re.sub(r'"minecraft:overworld/', '"pysift:the_sift/', text)
todo = re.findall(r'"(minecraft:overworld/[a-z0-9_/]+)"', json.dumps(noise))
seen = set()
while todo:
    ref = todo.pop()
    if ref in seen:
        continue
    seen.add(ref)
    rel = ref.split(":", 1)[1]
    text = (VANILLA_DF / f"{rel}.json").read_text(encoding="utf-8")
    todo += re.findall(r'"(minecraft:overworld/[a-z0-9_/]+)"', text)
    df = json.loads(retarget(text))
    if rel == "overworld/offset":
        df = {"type": "minecraft:cache", "input": TERRAIN_OFFSET}
    elif rel == "overworld/temperature":   # own unshifted noise at scale 1 (= vanilla x BIOME_ZOOM), readable by surface rules
        df = {"type": "minecraft:noise", "noise": "pysift:the_sift_temperature", "xz_scale": 1.0, "y_scale": 0.0}
    elif rel == "overworld/vegetation":
        df["xz_scale"] *= BIOME_ZOOM    # smaller climate zones: biomes (and their landforms) come round more often
    elif rel == "overworld/ridges":
        df = {"type": "minecraft:cache", "input": {"type": "minecraft:noise", "noise": "pysift:the_sift_ridge",
                                                   "xz_scale": 1.0, "y_scale": 0.0}}
    elif rel == "overworld/jaggedness":
        df = 0.0
    elif rel == "overworld/factor":
        df = FACTOR
    elif rel == "overworld/final_density":
        df = shape_caves(bury_caves(df))
    wj(D / "worldgen/density_function/the_sift" / f"{rel.split('/', 1)[1]}.json", df)
noise = json.loads(retarget(json.dumps(noise)))
# Underground layer borders (v2.1.0): the climate sampler reads the router's "depth" to pick the layer. Give it its own
# copy with a 3D noise wobble (+-LAYER_WOBBLE depth = about +-7 blocks) so the borders between the withered hollows,
# song caves and deep layers undulate instead of following the surface as flat sheets. Terrain, aquifers and caves
# keep reading the plain pysift:the_sift/depth by name, so nothing but the biome choice moves.
LAYER_WOBBLE = 0.055
wj(D / "worldgen/noise/the_sift_layers.json", {"base_amplitude": 1.0, "base_octave": -6, "octave_count": 3,
                                               "amplitude_modifiers": [1.0, 0.8, 0.4]})
wj(D / "worldgen/density_function/the_sift/biome_depth.json", {
    "type": "minecraft:add", "left": "pysift:the_sift/depth",
    "right": {"type": "minecraft:mul", "left": LAYER_WOBBLE,
              "right": {"type": "minecraft:noise", "noise": "pysift:the_sift_layers", "xz_scale": 1.0, "y_scale": 1.0}}})
noise["noise_router"]["depth"] = "pysift:the_sift/biome_depth"
# Vaults vs deeps: the router's "continents" feeds only the biome sampler here (the terrain has its own shape), so it
# becomes an unshifted 2D noise at scale 1. Surface rules can read the very same noise at the same coordinates
# (noise_threshold), so the floor materials blend across the biome border instead of changing at a line.
wj(D / "worldgen/noise/the_sift_abyss.json", {"base_amplitude": 1.0, "base_octave": -7, "octave_count": 3,
                                             "amplitude_modifiers": [1.0, 0.7, 0.3]})
wj(D / "worldgen/density_function/the_sift/abyss_field.json",
   {"type": "minecraft:noise", "noise": "pysift:the_sift_abyss", "xz_scale": 1.0, "y_scale": 0.0})
noise["noise_router"]["continents"] = "pysift:the_sift/abyss_field"
# flooded lake caves: the deeper, abyss-side aquifers fill with spirit liquid more often (default fluid below sea level)
wj(D / "worldgen/density_function/the_sift/floodedness.json", {
    "type": "minecraft:add", "left": noise["aquifers"]["fluid_level_floodedness"],
    "right": {"type": "minecraft:mul", "left": 0.35, "right": {"type": "minecraft:clamp", "min": 0.0, "max": 1.0, "input": {
        "type": "minecraft:mul", "left": 4.0, "right": "pysift:the_sift/abyss_field"}}}})
noise["aquifers"]["fluid_level_floodedness"] = "pysift:the_sift/floodedness"
noise["aquifers"]["lava"] = 0.0     # no aquifer lava cells (they need lava noise above 0.3); the global lava below y -54 stays
noise["default_block"] = BASE
noise["default_fluid"] = state("spirit_liquid")
noise["material_rule"] = "pysift:the_sift"
wj(D / "worldgen/noise_settings/the_sift.json", noise)

# ---- dimension: multi-noise climate, temperature x humidity ----
FULL = [-1.0, 1.0]
LULLABY_WEIRDNESS = 0.42     # weirdness above this (in the warm half) is Lullaby Hills; matches the terrain spline
NOT_LULLABY = [-1.0, LULLABY_WEIRDNESS]
NOT_EXTREME = [-SOUL_WEIRDNESS, LULLABY_WEIRDNESS]
point = lambda b, t, h, w=FULL: {"biome": f"pysift:{b}", "parameters": {
    "temperature": t, "humidity": h, "continentalness": FULL, "erosion": FULL, "weirdness": w,
    "depth": 0.0, "offset": 0.0}}
under = lambda b, d, continentalness=FULL: {"biome": f"pysift:{b}", "parameters": {
    "temperature": FULL, "humidity": FULL, "continentalness": continentalness, "erosion": FULL, "weirdness": FULL,
    "depth": d, "offset": 0.0}}
wj(D / "dimension/the_sift.json", {
    "type": "pysift:the_sift",
    "generator": {
        "type": "minecraft:noise",
        "biome_source": {"type": "minecraft:multi_noise", "biomes": [
            point("violet_slate_abyss", [-1.0, -0.3], FULL),             # cold
            point("willow_grove", [-0.3, SOUL_HEAT], FULL, NOT_LULLABY),          # mild
            point("willow_grove", [SOUL_HEAT, 0.4], FULL, [-SOUL_WEIRDNESS, LULLABY_WEIRDNESS]),   # mild, not the caldera
            point("crimson_strata_canyon", [0.4, 1.0], [-0.3, 1.0], NOT_EXTREME),    # hot, not dry
            point("amber_dunes", [0.2, 1.0], [-1.0, -0.3], NOT_EXTREME),             # hot and dry
            point("soul_caldera", [SOUL_HEAT, 1.0], FULL, [-1.0, -SOUL_WEIRDNESS]),       # hot + low weirdness: soul volcano plateau
            point("lullaby_hills", [0.0, 1.0], FULL, [LULLABY_WEIRDNESS, 1.0]),      # warm + high weirdness: grand canyons
            # underground layers by depth (blocks below the surface / 128), every climate: see "underground layers" above
            under("withered_hollows", [0.2, 0.42]),
            under("red_zone_caves", [0.42, 0.68]),
            under("resonant_vaults", [0.68, 2.0], continentalness=[-1.0, 0.0]),
            under("spirit_deeps", [0.68, 2.0], continentalness=[0.0, 1.0]),
        ]},
        "settings": "pysift:the_sift",
    },
})
# Ties flicker (v2.1.0): two climate boxes that share a boundary value (one ends at 0.4, the next starts at 0.4) tie for
# every column whose quantized value (x10000) equals it; the sampler then keeps whichever biome it found last, so such
# columns alternate between the two biomes with height (seen as 17 alternations in one column). Parameters are fixed-point
# integers, so moving the upper box's start up by one step (0.0001) leaves no integer on both sides: no tie is possible.
_dim = json.loads((D / "dimension/the_sift.json").read_text(encoding="utf-8"))
_boxes = _dim["generator"]["biome_source"]["biomes"]
for _dim_name in ("temperature", "humidity", "weirdness", "depth", "continentalness"):
    _ends = {b["parameters"][_dim_name][1] for b in _boxes if isinstance(b["parameters"][_dim_name], list)}
    for b in _boxes:
        _r = b["parameters"][_dim_name]
        if isinstance(_r, list) and _r[0] in _ends and _r[0] != -1.0:
            _r[0] = round(_r[0] + 0.0001, 4)
wj(D / "dimension/the_sift.json", _dim)
print("written:", *sorted(str(p.relative_to(P)) for p in D.rglob("*.json") if any(
    s in p.as_posix() for s in ("dimension", "worldgen"))), sep="\n  ")
