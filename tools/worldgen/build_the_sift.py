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
CRIMSON_TOP = state("crimson_capped_crimson_strata_3", facing="up")     # user choice; facing block, top face up
CRIMSON_UNDER = state("silted_strata", silt=0)                           # user choice: only silt=0 under the cap
VIOLET_TOP, VIOLET_UNDER = state("violet_capped_dark_slate", facing="up"), state("dark_slate", fade=0)   # user choice
GROVE_TOP = state("crimson_capped_crimson_strata_2", facing="up")         # user choice (no more pink loam)
GROVE_UNDER = state("abyssal_strata", depth=0)
DUNE_SAND, DUNE_ACCENT = state("amber_sand"), state("pale_sand")          # ~70 / 30 by surface noise
DUNE_STONE, DUNE_DEEP = state("bleached_sandstone", bleach=0), state("cracked_sandstone", crack=0)

# start from a clean slate so removed biomes / features leave no orphan JSON behind
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
    "minecraft:visual/cloud_color": track([(0, "#ffffeedd"), (3500, "#ffffffff"), (11000, "#ffffffff"), (12200, "#ffe0b0e0"),
                                           (13500, "#ff2a2a4a"), (22000, "#ff2a2a4a"), (23300, "#ffd0a8c0")]),
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
SOFT_GRASS = {"crimson_short_grass", "crimson_tall_grass", "soft_violet_short_grass", "soft_violet_tall_grass",
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


VEGETATION = {
    # ember_grass / abyss_grass / puff_grass are coloured by the floor under them (client FloorTint), so the same plant
    # is orange on crimson rock, teal on violet rock, pink on pink loam (reference video, The Sift 6:34 on).
    # (lo, hi) tries are random per patch centre; every patch is noise-clustered (patch() default).
    "crimson_strata_canyon": [patch("patch_ember_grass", "crimson_short_grass", 12, (48, 80)),
                              patch("patch_tall_ember_grass", "crimson_tall_grass", 5, (16, 32), half="lower"),
                              patch("patch_canyon_puff_grass", "puff_grass", 2, (6, 14), half="lower"),
                              patch("patch_canyon_abyss_grass", "crimson_short_grass", 3, (10, 24)),
                              patch("patch_sun_bloom_canyon", "sun_bloom", 2, (6, 12)),
                              patch("patch_golden_bloom_sparse", "golden_bloom", 2, (6, 12)),
                              # 裂隙植被（使用者提供的 rift_dimension_flora_assets）
                              patch("patch_canyon_teal_grass", "soft_teal_short_grass", 8, (32, 56), floor_in=TEAL_FLOORS),
                              patch("patch_canyon_tall_teal_grass", "soft_teal_tall_grass", 4, (12, 24), half="lower", floor_in=TEAL_FLOORS),
                              patch("patch_crimson_short_sprouts", "crimson_short_sprouts", 4, (16, 32)),
                              carpet_patch("patch_canyon_coral_leaf_carpet", 2, (6, 12)),
                              patch("patch_orange_rift_grass", "orange_rift_grass", 3, (12, 24)),
                              patch("patch_orange_tall_rift_grass", "orange_tall_rift_grass", 2, (6, 12), half="lower"),
                              patch("patch_canyon_agave_rosette", "agave_rosette", 1, (2, 5)),
                              cliff_vines("cliff_vines_crimson_canyon", tries=54, min_len=3, max_len=8, glow_chance=0.10, count=9)],
    "violet_slate_abyss": [patch("patch_abyss_grass", "soft_violet_short_grass", 12, (48, 80)),
                           patch("patch_violet_ember_grass", "soft_violet_tall_grass", 4, (16, 32), half="lower"),
                           patch("patch_violet_puff_grass", "puff_grass", 4, (10, 20), half="lower"),
                           patch("patch_glowcap", "gloomcap", 3, (6, 12)),
                           patch("patch_bone_spire", "bone_spire", 2, (4, 10)),
                           patch("patch_dusk_bloom", "dusk_bloom", 2, (6, 12)),
                           patch("patch_violet_golden_bloom", "golden_bloom", 1, (4, 8)),
                           patch("patch_violet_teal_grass", "soft_teal_short_grass", 3, (12, 24), floor_in=TEAL_FLOORS),
                           patch("patch_curled_fern_blue", "curled_fern_blue", 3, (8, 16)),
                           patch("patch_tall_glow_grass", "tall_glow_grass", 3, (8, 16), half="lower"),
                           patch("patch_curled_fern_white", "curled_fern_white", 2, (6, 12)),
                           patch("patch_giant_canopy_blue", "giant_canopy_blue", 1, (2, 5)),
                           patch("patch_giant_canopy_white", "giant_canopy_white", 1, (2, 4)),
                           cliff_vines("cliff_vines_violet_abyss", tries=48, min_len=3, max_len=7, glow_chance=0.35, count=7)],
    "willow_grove": [trees("soul_willows_giant", SOUL_WILLOW_GIANT, {"type": "minecraft:rarity_filter", "chance": 16}),
                     trees("soul_willows", SOUL_WILLOW, {"type": "minecraft:count", "count": uniform(1, 2)}),
                     patch("patch_grove_ember_grass", "crimson_short_grass", 8, (32, 56)),
                     patch("patch_grove_abyss_grass", "crimson_short_grass", 6, (24, 48)),
                     patch("patch_grove_puff_grass", "puff_grass", 3, (8, 16), half="lower"),
                     patch("patch_humus_grass", "crimson_short_grass", 4, (16, 32)),
                     patch("patch_tall_humus_grass", "crimson_tall_grass", 2, (8, 16), half="lower"),
                     patch("patch_humus_fern", "humus_fern", 3, (8, 16)),
                     patch("patch_humus_bush", "humus_bush", 2, (4, 10)),
                     patch("patch_grove_glowcap", "gloomcap", 2, (4, 10)),
                     patch("patch_sun_bloom", "sun_bloom", 2, (6, 12)),
                     patch("patch_rose_bloom", "rose_bloom", 2, (6, 12)),
                     patch("patch_grove_dusk_bloom", "dusk_bloom", 1, (4, 10)),
                     patch("patch_golden_bloom", "golden_bloom", 2, (6, 12)),
                     patch("patch_grove_teal_grass", "soft_teal_short_grass", 6, (24, 40), floor_in=TEAL_FLOORS),
                     patch("patch_grove_tall_teal_grass", "soft_teal_tall_grass", 2, (8, 16), half="lower", floor_in=TEAL_FLOORS),
                     patch("patch_mint_rift_grass", "mint_rift_grass", 4, (16, 32)),
                     patch("patch_grove_tall_glow_grass", "tall_glow_grass", 2, (6, 12), half="lower"),
                     carpet_patch("patch_coral_leaf_carpet", 3, (8, 16)),
                     patch("patch_curled_fern_pink", "curled_fern_pink", 2, (6, 12)),
                     patch("patch_giant_canopy_green", "giant_canopy_green", 1, (2, 5)),
                     patch("patch_grove_clustered_yellow_flowers", "clustered_yellow_flowers", 1, (4, 8)),
                     cliff_vines("cliff_vines_willow_grove", tries=64, min_len=4, max_len=9, glow_chance=0.18, count=12)],
    "amber_dunes": [patch("patch_dune_tall_ember_grass", "soft_dune_tall_grass", 2, (6, 12), half="lower"),
                    patch("patch_dune_ember_grass", "soft_dune_short_grass", 3, (10, 20)),
                    patch("patch_dune_golden_bloom", "golden_bloom", 1, (4, 8)),
                    patch("patch_dune_teal_grass", "soft_teal_short_grass", 2, (8, 16), floor_in=TEAL_FLOORS),
                    patch("patch_yellow_short_grass", "yellow_short_grass", 4, (12, 24)),
                    patch("patch_dune_agave_rosette", "agave_rosette", 1, (2, 5)),
                    patch("patch_olive_forked_stalk", "olive_forked_stalk", 1, (2, 5)),
                    patch("patch_clustered_yellow_flowers", "clustered_yellow_flowers", 1, (4, 8)),
                    cliff_vines("cliff_vines_amber_dunes", tries=32, min_len=2, max_len=5, glow_chance=0.08, count=3)],
}

# ---- strata mesas (pysift:strata_spire, StrataSpireFeature.java) ----
# Big round flat-topped mesas of stacked 2-high tiers that step inward at the edge (reference video
# "I Recreated The Sift" + the user's mesa screenshots). Every biome uses the same feature with its own materials:
# top = exposed tier tops (the walkable surface), body = gradient from the top down, band = optional stripe.
def weighted(*states):
    return {"type": "minecraft:weighted", "entries": [{"data": s, "weight": 1} for s in states]}


SPIRES = {   # biome: big round flat-topped mesas (user: large radius, flat walkable tops, not pillars)
    "crimson_strata_canyon": dict(tiers=(4, 8), radius=(12, 18), cap=(2, 3),
                                  top=weighted(state("capped_crimson_strata", facing="up", tone="teal"),
                                               state("capped_crimson_strata", facing="up", tone="rose")),
                                  body=[state("ember_stone", heat=0)],
                                  frequency={"type": "minecraft:rarity_filter", "chance": 6}),     # most common
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
                               floor=weighted(*[state("corrupted_slate_bricks", corruption=c) for c in (0, 1, 2)],
                                              state("dark_slate_bricks")),
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
               for b in ("violet_capped_dark_slate", "dark_slate", "void_stone", "corrupted_slate")]
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
                   "middle_layer_provider": provider("corrupted_slate", corruption=1),
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

# ambient particles per biome (phase 2), as vanilla nether biomes do it
AMBIENT = {"crimson_strata_canyon": ("minecraft:crimson_spore", 0.012),
           "red_zone_caves": ("minecraft:crimson_spore", 0.03),
           "violet_slate_abyss": ("pysift:soul_wisp", 0.002),     # user: fewer soul wisps
           "willow_grove": ("minecraft:spore_blossom_air", 0.012),
           "amber_dunes": ("minecraft:white_ash", 0.015)}

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

# night-glow flora (SiftFlora.java): glowshade grass in the meadows, starlit shrubs here and there
SURFACE = [{"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}]
GLOW_FEATURES = {
    "willow_grove": [farm_plant("glowshade_grass_grove", provider("glowshade_grass"), 28, SURFACE, []),
                     farm_plant("glowshade_tuft_grove", provider("glowshade_tuft"), 10, SURFACE, []),
                     farm_plant("starlit_shrub_grove", provider("starlit_shrub"), 3, SURFACE, [])],
    "violet_slate_abyss": [farm_plant("glowshade_grass_violet", provider("glowshade_grass"), 18, SURFACE, []),
                           farm_plant("starlit_shrub_violet", provider("starlit_shrub"), 5, SURFACE, [])],
}

# red zone caves (underground biome, reference video "THE SIFT UPDATE"): crimson floors, coral-red plants, glowing
# shrubs and charoite on the cave floors; picked by the multi-noise "depth" parameter (see the dimension below)
RED_CAVE_FLOOR = [{"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                                "min_inclusive": {"absolute": -50}, "max_inclusive": {"absolute": 30}}},
                  {"type": "minecraft:environment_scan", "direction_of_search": "down", "max_steps": 12,
                   "target_condition": {"type": "minecraft:solid"},
                   "allowed_search_condition": {"type": "minecraft:matching_block_tag", "tag": "minecraft:air"}},
                  {"type": "minecraft:offset", "x": 0, "y": 1, "z": 0}]
CAVE_FEATURES = {"red_zone_caves": [
    farm_plant("red_cave_grass", provider("crimson_short_grass"), 90, RED_CAVE_FLOOR, []),
    farm_plant("red_cave_sprouts", provider("crimson_short_sprouts"), 50, RED_CAVE_FLOOR, []),
    farm_plant("red_cave_shrub", provider("starlit_shrub"), 10, RED_CAVE_FLOOR, []),
    farm_plant("red_cave_charoite", provider("charoite_cluster", facing="up", waterlogged="false"), 6, RED_CAVE_FLOOR, []),
]}

ORE_FEATURES = {"violet_slate_abyss": [
    soul_crystal_ore("soul_crystal_surface", 5, uniform(0, 1), [
        {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"},
        {"type": "minecraft:offset", "x": 0, "y": -1, "z": 0}]),
    soul_crystal_ore("soul_crystal_buried", 8, 3, [
        {"type": "minecraft:height_range", "height": {"type": "minecraft:uniform",
                                                       "min_inclusive": {"absolute": -40}, "max_inclusive": {"absolute": 60}}}]),
]}

def biome(name, temperature, downfall, rain, sky, fog, water, spawn_attr):
    wj(D / f"worldgen/biome/{name}.json", {
        "attributes": {**spawn_attr, "minecraft:visual/sky_color": SKY_COLOR, "minecraft:visual/fog_color": SKY_FOG,
                       **({"minecraft:visual/ambient_particles": {"modifier": "append", "argument": [
                           {"particle": {"type": AMBIENT[name][0]}, "probability": AMBIENT[name][1]}]}} if name in AMBIENT else {})},
        "carvers": [],
        "downfall": downfall,
        "effects": {"water_color": water},
        # step 1 = lakes (spirit ponds), step 2 = local_modifications (spires, like vanilla boulders),
        # step 9 = vegetal_decoration
        # step 6 = underground_ores
        "features": [[], POND_FEATURES.get(name, []), SPIRE_FEATURES.get(name, []) + [SOUL_GEODE]] + [[], [], [], ORE_FEATURES.get(name, []) + [SIFTITE_ORE]
                    + (CHAROITE if name == "violet_slate_abyss" else []), [], []]
                    + [VEGETATION.get(name, []) + GLOW_FEATURES.get(name, []) + CAVE_FEATURES.get(name, []) + FARM_FEATURES
                       + ([] if name in CAVE_FEATURES else [WILD_RIFT]), []],
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
      spawns(monster=[("stalker", 30, 1, 2), ("prickle", 20, 1, 2), ("fusefly", 15, 1, 1)],
             creature=[("blub", 10, 1, 2)]))
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
path = lambda floor: cond(ON_FLOOR, cond(ON_PATH, block(floor)))

CEILING = {"type": "minecraft:stone_depth", "add_surface_depth": False, "offset": 0, "secondary_depth_range": 0,
           "surface_type": "ceiling"}
wj(D / "worldgen/material_rule/the_sift.json", seq(
    "minecraft:bedrock_floor",
    # red zone caves: crimson-capped floors over silted strata, silted strata on the ceilings
    in_biome("red_zone_caves", seq(cond(ON_FLOOR, block(CRIMSON_TOP)), cond(WITHIN(2), block(CRIMSON_UNDER)),
                                   cond(CEILING, block(CRIMSON_UNDER)))),
    cond({"type": "minecraft:above_preliminary_surface"}, seq(
        # crimson: capped strata on top, silted strata (silt=0) below, ragged hand-off to void_stone at depth 5-8
        in_biome("crimson_strata_canyon", seq(
            path(CRIMSON_PATH),
            cond(ON_FLOOR, block(CRIMSON_TOP)),
            cond(WITHIN(4), block(CRIMSON_UNDER)),
            cond(WITHIN(8), cond(NOISE(0.0), block(CRIMSON_UNDER))))),
        # violet: violet-capped dark slate on top, dark slate below (same pair as the violet mesas)
        in_biome("violet_slate_abyss", seq(path(VIOLET_PATH), cond(ON_FLOOR, block(VIOLET_TOP)), cond(WITHIN(5), block(VIOLET_UNDER)))),
        # willow grove: crimson-capped strata on top, abyssal strata (depth=0) below
        in_biome("willow_grove", seq(path(GROVE_PATH), cond(ON_FLOOR, block(GROVE_TOP)), cond(WITHIN(6), block(GROVE_UNDER)))),
        # amber dunes: amber sand with pale sand patches, then sandstone
        in_biome("amber_dunes", seq(
            cond(WITHIN(3), seq(cond(NOISE(0.35), block(DUNE_ACCENT)), block(DUNE_SAND))),
            cond(WITHIN(6), block(DUNE_STONE)),
            cond(WITHIN(9), block(DUNE_DEEP)))),
    )),
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
wj(D / "worldgen/noise/the_sift_landform.json", {"base_amplitude": 1.0, "base_octave": -8, "octave_count": 2,
                                                 "amplitude_modifiers": [1.0, 0.3]})
wj(D / "worldgen/density_function/the_sift/terrain/landform.json",
   {"type": "minecraft:cache", "input": noise2d("the_sift_landform")})
wj(D / "worldgen/density_function/the_sift/terrain/hills.json", {"type": "minecraft:cache", "input": noise2d("the_sift_hills")})
# ridged noise: |n| is 0 along thin winding lines -> dune crests
wj(D / "worldgen/density_function/the_sift/terrain/dune_ridge.json",
   {"type": "minecraft:cache", "input": {"type": "minecraft:abs", "input": noise2d("the_sift_dunes")}})
HILLS, RIDGE, LAND = DF + "hills", DF + "dune_ridge", DF + "landform"
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
CANYON = landform(TERRACES, stepped(100, 9))
DUNE_LAND = landform(DUNES, stepped(86, 6))
HOT = spline("pysift:the_sift/vegetation", (-1.0, DUNE_LAND, 0), (-0.4, DUNE_LAND, 0), (-0.2, CANYON, 0), (1.0, CANYON, 0))
SHAPE = {"type": "minecraft:spline", "spline": spline(
    "pysift:the_sift/temperature", (-1.0, VIOLET, 0), (-0.4, VIOLET, 0), (-0.2, GROVE, 0), (0.3, GROVE, 0),
    (0.45, HOT, 0), (1.0, HOT, 0))}
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
    elif rel in ("overworld/temperature", "overworld/vegetation"):
        df["xz_scale"] *= BIOME_ZOOM    # smaller climate zones: biomes (and their landforms) come round more often
    elif rel == "overworld/jaggedness":
        df = 0.0
    elif rel == "overworld/factor":
        df = FACTOR
    elif rel == "overworld/final_density":
        df = bury_caves(df)
    wj(D / "worldgen/density_function/the_sift" / f"{rel.split('/', 1)[1]}.json", df)
noise = json.loads(retarget(json.dumps(noise)))
noise["default_block"] = BASE
noise["default_fluid"] = state("spirit_liquid")
noise["material_rule"] = "pysift:the_sift"
wj(D / "worldgen/noise_settings/the_sift.json", noise)

# ---- dimension: multi-noise climate, temperature x humidity ----
FULL = [-1.0, 1.0]
point = lambda b, t, h: {"biome": f"pysift:{b}", "parameters": {
    "temperature": t, "humidity": h, "continentalness": FULL, "erosion": FULL, "weirdness": FULL,
    "depth": 0.0, "offset": 0.0}}
wj(D / "dimension/the_sift.json", {
    "type": "pysift:the_sift",
    "generator": {
        "type": "minecraft:noise",
        "biome_source": {"type": "minecraft:multi_noise", "biomes": [
            point("violet_slate_abyss", [-1.0, -0.3], FULL),             # cold
            point("willow_grove", [-0.3, 0.4], FULL),                   # mild
            point("crimson_strata_canyon", [0.4, 1.0], [-0.3, 1.0]),    # hot, not dry
            point("amber_dunes", [0.2, 1.0], [-1.0, -0.3]),             # hot and dry
            {"biome": "pysift:red_zone_caves", "parameters": {           # underground, like vanilla lush caves
                "temperature": [-0.2, 1.0], "humidity": [0.1, 1.0], "continentalness": FULL, "erosion": FULL,
                "weirdness": FULL, "depth": [0.2, 0.9], "offset": 0.0}},
        ]},
        "settings": "pysift:the_sift",
    },
})
print("written:", *sorted(str(p.relative_to(P)) for p in D.rglob("*.json") if any(
    s in p.as_posix() for s in ("dimension", "worldgen"))), sep="\n  ")
