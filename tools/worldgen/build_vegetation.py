"""Generate resources for ModVegetation / ModFluids / ModEffects (Minecraft 26.3 formats).
Usage: python -I tools/worldgen/build_vegetation.py <project>

Textures are vanilla greyscale placeholders tinted by ModVegetation.TINTS. When the real art arrives, put the PNGs
under assets/pysift/textures/block/vegetation/ and point TEXTURES at them ("pysift:block/vegetation/<name>"), then
rerun this script. Colours are read from ModVegetation.java so Java and item tints never drift apart."""
import json, re, sys, struct, zlib
from pathlib import Path

P = Path(sys.argv[1])
RES = P / "src/main/resources"
A, D = RES / "assets/pysift", RES / "data"
JAVA = P / "src/main/java/pryuan05/pysift/block/ModVegetation.java"

TEXTURES = {
    # soul willow: the user's art (tools/worldgen/art/soul_willow_sheet.png), cut and varied by
    # make_soul_willow_textures.py; already coloured, so these blocks are not tinted
    "soul_willow_log_side": "pysift:block/vegetation/soul_willow_log_side",
    "soul_willow_log_top": "pysift:block/vegetation/soul_willow_log_top",
    "soul_willow_leaves": "pysift:block/vegetation/soul_willow_leaves",
    "soul_willow_leaves_pale": "pysift:block/vegetation/soul_willow_leaves_pale",
    "soul_willow_leaves_glowing": "pysift:block/vegetation/soul_willow_leaves_glowing",
    "soul_willow_vine": "pysift:block/vegetation/soul_willow_vine",          # + _<shade> (0 / 1 / 2)
    "soul_willow_vine_tip": "pysift:block/vegetation/soul_willow_vine_tip",  # + _<shade>; wispier end piece
    "grass": "minecraft:block/short_grass",
    "ember_grass": "pysift:block/vegetation/ember_grass",
    "tall_ember_grass_bottom": "pysift:block/vegetation/tall_ember_grass_bottom",
    "tall_ember_grass_top": "pysift:block/vegetation/tall_ember_grass_top",
    "tall_grass_bottom": "minecraft:block/tall_grass_bottom",
    "tall_grass_top": "minecraft:block/tall_grass_top",
    "fern": "minecraft:block/fern",
    "bush": "minecraft:block/bush",
    "golden_bloom": "pysift:block/vegetation/golden_bloom",
    "spirit_liquid": "minecraft:block/water_still",
    "sun_bloom": "pysift:block/vegetation/sun_bloom",
    "rose_bloom": "pysift:block/vegetation/rose_bloom",
    "dusk_bloom": "pysift:block/vegetation/dusk_bloom",
    "soul_willow_sapling": "minecraft:block/pale_oak_sapling",
    "sift_pink_loam": "pysift:block/vegetation/sift_pink_loam",   # make_pink_loam.py
    "abyss_grass": "pysift:block/vegetation/abyss_grass",         # make_abyss_grass.py (grey blades, FloorTint)
    "glowcap": "pysift:block/vegetation/glowcap",                 # make_decor_textures.py
    "bone_spire": "pysift:block/vegetation/bone_spire",           # make_decor_textures.py
    "puff_grass_bottom": "pysift:block/vegetation/puff_grass_bottom",   # make_decor_textures.py (grey, FloorTint)
    "puff_grass_top": "pysift:block/vegetation/puff_grass_top",
}
# block -> (kind, texture keys, zh_tw name)
REMOVED = ["willow_log", "willow_leaves", "willow_hanging_leaves", "willow_sapling",   # replaced by the soul willow
           "abyss_fern"]                                                                 # renamed to abyss_grass
BLOCKS = {
    "soul_willow_log": ("log", ("soul_willow_log_side", "soul_willow_log_top"), "靈魂柳原木"),
    "soul_willow_leaves": ("leaves", ("soul_willow_leaves",), "靈魂柳葉"),
    "soul_willow_leaves_pale": ("leaves", ("soul_willow_leaves_pale",), "淡藍靈魂柳葉"),
    "glowing_soul_willow_leaves": ("leaves", ("soul_willow_leaves_glowing",), "發光靈魂柳葉"),
    "soul_willow_vine": ("vine", ("soul_willow_vine", "soul_willow_vine_tip"), "靈魂柳垂藤"),
    "glowing_soul_willow_vine": ("vine", ("soul_willow_vine", "soul_willow_vine_tip"), "發光靈魂柳垂藤"),
    "soul_willow_sapling": ("sapling", ("soul_willow_sapling",), "靈魂柳樹苗"),
    "sift_pink_loam": ("cube", ("sift_pink_loam",), "粉壤土"),
    "ember_grass": ("cross", ("ember_grass",), "餘燼草"),
    "tall_ember_grass": ("tall", ("tall_ember_grass_bottom", "tall_ember_grass_top"), "高餘燼草"),
    "humus_grass": ("cross", ("grass",), "腐殖草"),
    "tall_humus_grass": ("tall", ("tall_grass_bottom", "tall_grass_top"), "高腐殖草"),
    "humus_fern": ("cross", ("fern",), "腐殖蕨"),
    "humus_bush": ("cross", ("bush",), "腐殖灌木"),
    "abyss_grass": ("cross", ("abyss_grass",), "深淵草"),
    "glowcap": ("cross", ("glowcap",), "螢光菇"),
    "bone_spire": ("cross", ("bone_spire",), "骨刺"),
    "puff_grass": ("tall", ("puff_grass_bottom", "puff_grass_top"), "蓬鬆草"),
    "golden_bloom": ("flower", ("golden_bloom",), "金綻花"),
    "sun_bloom": ("big_flower", ("sun_bloom",), "陽綻花"),
    "rose_bloom": ("big_flower", ("rose_bloom",), "玫綻花"),
    "dusk_bloom": ("big_flower", ("dusk_bloom",), "暮綻花"),
}
TAGS = {  # vanilla tag -> entries to add
    "block/mineable/axe": ["soul_willow_log"],
    "block/mineable/hoe": ["soul_willow_leaves", "soul_willow_leaves_pale", "glowing_soul_willow_leaves",
                           "soul_willow_vine", "glowing_soul_willow_vine"],
    "block/mineable/shovel": ["sift_pink_loam"],
    "block/logs": ["soul_willow_log"],
    "block/leaves": ["soul_willow_leaves", "soul_willow_leaves_pale", "glowing_soul_willow_leaves"],
    "block/saplings": ["soul_willow_sapling"],
    "item/saplings": ["soul_willow_sapling"],
    "block/climbable": ["soul_willow_vine", "glowing_soul_willow_vine"],
    "block/small_flowers": ["golden_bloom", "sun_bloom", "rose_bloom", "dusk_bloom"],
    "item/small_flowers": ["golden_bloom", "sun_bloom", "rose_bloom", "dusk_bloom"],   # Slabber flower planting
    "block/replaceable_by_trees": ["soul_willow_vine", "glowing_soul_willow_vine", "ember_grass", "tall_ember_grass", "humus_grass",
                                   "tall_humus_grass", "humus_fern", "humus_bush", "abyss_grass", "glowcap", "bone_spire",
                                   "puff_grass", "golden_bloom",
                                   "sun_bloom", "rose_bloom", "dusk_bloom"],
    # The Sift surface blocks plants may grow on (VegetationBlock#mayPlaceOn checks this tag)
    "block/supports_vegetation": ["meadow_grass_block", "rich_dirt", "forest_floor", "ash_capped_crimson_01",
                                  "crimson_strata", "ash_capped_violet_01", "violet_strata", "crimson_capped_void_01",
                                  "crimson_capped_crimson_strata_3", "amber_sand", "pale_sand", "void_capped_crimson_01",
                                  "crimson_capped_crimson_strata_2", "violet_capped_dark_slate", "capped_crimson_strata",
                                  "abyssal_strata", "dark_slate", "silted_strata"],
    "fluid/water": ["spirit_liquid", "flowing_spirit_liquid"],
}


def lj(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tex(key): return TEXTURES[key]


# ---- colours from Java: tint(register("name", ...), 0xAARRGGBB) ----
java = JAVA.read_text(encoding="utf-8")
TINT = {}
for m in re.finditer(r'tint\(register\("([a-z_]+)".*?\),\s*0x([0-9A-Fa-f]{8})\)', java, re.S):
    TINT[m[1]] = int(m[2], 16) - (1 << 32)          # signed ARGB, as vanilla item tints use
# plants coloured by the floor under them (client FloorTint): floorTint(register("name", ...), 0xAARRGGBB) = default colour
FLOOR = {}
for m in re.finditer(r'floorTint\(register\("([a-z_]+)".*?\),\s*0x([0-9A-Fa-f]{8})\)', java, re.S):
    FLOOR[m[1]] = int(m[2], 16) - (1 << 32)
registered = set(re.findall(r'register\("([a-z_]+)"', java))
assert registered == set(BLOCKS), ("ModVegetation and BLOCKS differ", registered ^ set(BLOCKS))


def model(name, parent, textures):
    wj(A / f"models/block/vegetation/{name}.json", {"parent": parent, "textures": textures})
    return f"pysift:block/vegetation/{name}"


def _face(tinted, uv=(0, 0, 16, 16), tex_ref="#cross"):
    d = {"uv": list(uv), "texture": tex_ref}
    if tinted:
        d["tintindex"] = 0
    return d


def _plane(frm, to, faces, rotation, tinted, light_emission=0):
    el = {"from": list(frm), "to": list(to), "shade": False, "rotation": rotation,
          "faces": {f: _face(tinted) for f in faces}}
    if light_emission:
        el["light_emission"] = light_emission
    return el


def lush_tuft_elements(tinted):
    """8-plane volumetric 3D grass tuft: 4 inner angled blades + 4 outer perimeter flaring blades."""
    f = _face(tinted)
    ns = {"north": f, "south": f}
    return [
        {"from": [0, 0, 13], "to": [16, 15, 13], "shade": False,
         "rotation": {"x": 5, "y": -56, "z": 0, "origin": [8, 7, 8]}, "faces": ns},
        {"from": [0, 0, 3], "to": [16, 15, 3], "shade": False,
         "rotation": {"x": 175, "y": -34, "z": -180, "origin": [8, 7, 8]}, "faces": ns},
        {"from": [0, 0, 3], "to": [16, 15, 3], "shade": False,
         "rotation": {"x": -7, "y": -56, "z": 0, "origin": [8, 7, 8]}, "faces": ns},
        {"from": [0, 0, 13], "to": [16, 15, 13], "shade": False,
         "rotation": {"x": -175, "y": -34, "z": -180, "origin": [8, 7, 8]}, "faces": ns},
        {"from": [0, 0, 14.5], "to": [16, 14, 14.5], "shade": False,
         "rotation": {"angle": 12.5, "axis": "x", "origin": [8, 7, 8]}, "faces": ns},
        {"from": [0, 0, 1.5], "to": [16, 14, 1.5], "shade": False,
         "rotation": {"x": 0, "y": -90, "z": -12.5, "origin": [8, 7, 8]}, "faces": ns},
        {"from": [0, 0, 1.5], "to": [16, 14, 1.5], "shade": False,
         "rotation": {"angle": -12.5, "axis": "x", "origin": [8, 7, 8]}, "faces": ns},
        {"from": [0, 0, 14.5], "to": [16, 14, 14.5], "shade": False,
         "rotation": {"x": 0, "y": -90, "z": 12.5, "origin": [8, 7, 8]}, "faces": ns},
    ]


def lush_fern_elements(tinted):
    """10-plane spreading 3D fern rosette: 2 upright centre fronds + 4 mid-angle fronds + 4 low wide-flaring basal fronds."""
    return [
        _plane([0.8, 0, 8], [15.2, 16, 8], ("north", "south"),
               {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True}, tinted),
        _plane([8, 0, 0.8], [8, 16, 15.2], ("east", "west"),
               {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True}, tinted),
        # 4 mid-tier outward-leaning fronds (22.5 deg)
        _plane([1, 0, 12], [15, 15, 12], ("north", "south"),
               {"origin": [8, 0, 12], "axis": "x", "angle": -22.5}, tinted),
        _plane([1, 0, 4], [15, 15, 4], ("north", "south"),
               {"origin": [8, 0, 4], "axis": "x", "angle": 22.5}, tinted),
        _plane([12, 0, 1], [12, 15, 15], ("east", "west"),
               {"origin": [12, 0, 8], "axis": "z", "angle": 22.5}, tinted),
        _plane([4, 0, 1], [4, 15, 15], ("east", "west"),
               {"origin": [4, 0, 8], "axis": "z", "angle": -22.5}, tinted),
        # 4 outer wide-arching basal fronds (35 deg)
        _plane([0, 0, 13.5], [16, 13, 13.5], ("north", "south"),
               {"origin": [8, 0, 13.5], "axis": "x", "angle": -35}, tinted),
        _plane([0, 0, 2.5], [16, 13, 2.5], ("north", "south"),
               {"origin": [8, 0, 2.5], "axis": "x", "angle": 35}, tinted),
        _plane([13.5, 0, 0], [13.5, 13, 16], ("east", "west"),
               {"origin": [13.5, 0, 8], "axis": "z", "angle": 35}, tinted),
        _plane([2.5, 0, 0], [2.5, 13, 16], ("east", "west"),
               {"origin": [2.5, 0, 8], "axis": "z", "angle": -35}, tinted),
    ]


def lush_bush_elements(tinted):
    """10-plane dense 3D shrub: 8-plane tuft + 2 tilted canopy planes filling the top silhouette."""
    return lush_tuft_elements(tinted) + [
        _plane([1, 1, 8], [15, 16, 8], ("north", "south"),
               {"origin": [8, 8, 8], "axis": "x", "angle": 22.5}, tinted),
        _plane([8, 1, 1], [8, 16, 15], ("east", "west"),
               {"origin": [8, 8, 8], "axis": "z", "angle": -22.5}, tinted),
    ]


def lush_cluster_elements(tinted, light_emission=0, tilt=12.5):
    """6-plane 3D cluster for mushrooms (glowcap), coral spikes (bone_spire), and bushy saplings."""
    return [
        _plane([0.8, 0, 8], [15.2, 16, 8], ("north", "south"),
               {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True}, tinted, light_emission),
        _plane([8, 0, 0.8], [8, 16, 15.2], ("east", "west"),
               {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True}, tinted, light_emission),
        _plane([1, 0, 12.2], [15, 15, 12.2], ("north", "south"),
               {"origin": [8, 0, 12.2], "axis": "x", "angle": -tilt}, tinted, light_emission),
        _plane([1, 0, 3.8], [15, 15, 3.8], ("north", "south"),
               {"origin": [8, 0, 3.8], "axis": "x", "angle": tilt}, tinted, light_emission),
        _plane([12.2, 0, 1], [12.2, 15, 15], ("east", "west"),
               {"origin": [12.2, 0, 8], "axis": "z", "angle": tilt}, tinted, light_emission),
        _plane([3.8, 0, 1], [3.8, 15, 15], ("east", "west"),
               {"origin": [3.8, 0, 8], "axis": "z", "angle": -tilt}, tinted, light_emission),
    ]


def lush_tall_elements(tinted, is_top):
    """8-plane 3D double-high plant half: 4 vertical crossed planes (seamless across lower/upper boundary)
    + 4 outer flaring planes (basal tuft on bottom, arching plumes on top)."""
    core = [
        _plane([0.8, 0, 8], [15.2, 16, 8], ("north", "south"),
               {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True}, tinted),
        _plane([8, 0, 0.8], [8, 16, 15.2], ("east", "west"),
               {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True}, tinted),
        _plane([1, 0, 11.8], [15, 16, 11.8], ("north", "south"),
               {"origin": [8, 8, 8], "axis": "y", "angle": -22.5}, tinted),
        _plane([1, 0, 4.2], [15, 16, 4.2], ("north", "south"),
               {"origin": [8, 8, 8], "axis": "y", "angle": 22.5}, tinted),
    ]
    z_pos, z_neg, h, ang = (13.5, 2.5, 15, 10.0) if is_top else (14.2, 1.8, 16, 12.5)
    outer = [
        _plane([0, 0, z_pos], [16, h, z_pos], ("north", "south"),
               {"origin": [8, 0, z_pos], "axis": "x", "angle": -ang}, tinted),
        _plane([0, 0, z_neg], [16, h, z_neg], ("north", "south"),
               {"origin": [8, 0, z_neg], "axis": "x", "angle": ang}, tinted),
        _plane([z_pos, 0, 0], [z_pos, h, 16], ("east", "west"),
               {"origin": [z_pos, 0, 8], "axis": "z", "angle": ang}, tinted),
        _plane([z_neg, 0, 0], [z_neg, h, 16], ("east", "west"),
               {"origin": [z_neg, 0, 8], "axis": "z", "angle": -ang}, tinted),
    ]
    return core + outer


def lush_model(name, texture_ref, elements):
    wj(A / f"models/block/vegetation/{name}.json", {
        "format_version": "26.3",
        "ambientocclusion": False,
        "textures": {"cross": texture_ref, "particle": texture_ref},
        "elements": elements,
    })
    return f"pysift:block/vegetation/{name}"


def item(name, model_ref):
    m = {"type": "minecraft:model", "model": model_ref}
    if name in TINT or name in FLOOR:
        m["tints"] = [{"type": "minecraft:constant", "value": TINT.get(name, FLOOR.get(name))}]
    wj(A / f"items/{name}.json", {"model": m})


def generated_item(name, texture):
    wj(A / f"models/item/{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": texture}})
    item(name, f"pysift:item/{name}")


def loot(name, pools):
    table = {"type": "minecraft:block", "pools": pools, "random_sequence": f"pysift:blocks/{name}"}
    for d in ("loot_table", "loot_tables"):
        wj(D / f"pysift/{d}/blocks/{name}.json", table)


SHEARS = {"type": "minecraft:any_of", "terms": ["minecraft:tool/can_shear", "minecraft:tool/can_silk_touch"]}
self_drop = lambda name, cond: [{"condition": cond, "entries": [{"type": "minecraft:item", "name": f"pysift:{name}"}], "rolls": 1}]

# hand-made 3D Blockbench models by the user: models, item models and textures are edited directly; do not overwrite them
CUSTOM = {"rose_bloom", "dusk_bloom", "sun_bloom", "golden_bloom", "abyss_grass", "ember_grass"}

for name, (kind, keys, zh) in BLOCKS.items():
    if name in CUSTOM:
        continue
    tinted = name in TINT or name in FLOOR
    cross_parent = "minecraft:block/tinted_cross" if tinted else "minecraft:block/cross"
    if kind == "log":
        m = model(name, "minecraft:block/cube_column", {"side": tex(keys[0]), "end": tex(keys[1])})
        wj(A / f"blockstates/{name}.json", {"variants": {"axis=y": {"model": m}, "axis=z": {"model": m, "x": 90},
                                                         "axis=x": {"model": m, "x": 90, "y": 90}}})
        wj(A / f"models/item/{name}.json", {"parent": m})
        item(name, f"pysift:item/{name}")
        loot(name, self_drop(name, {"type": "minecraft:survives_explosion"}))
    elif kind == "leaves":
        m = model(name, "minecraft:block/leaves", {"all": tex(keys[0])})
        wj(A / f"blockstates/{name}.json", {"variants": {"": {"model": m}}})
        wj(A / f"models/item/{name}.json", {"parent": m})
        item(name, f"pysift:item/{name}")
        # shears / silk touch -> the leaves; otherwise a 5% sapling chance (like vanilla leaves)
        loot(name, [{"entries": [{"type": "minecraft:alternatives", "children": [
            {"type": "minecraft:item", "condition": SHEARS, "name": f"pysift:{name}"},
            {"type": "minecraft:item", "name": "pysift:soul_willow_sapling", "condition": {"type": "minecraft:all_of", "terms": [
                {"type": "minecraft:survives_explosion"}, {"type": "minecraft:random_chance", "chance": 0.05}]}}]}],
            "rolls": 1}])
    elif kind == "hanging":
        body = model(name, cross_parent, {"cross": tex(keys[0])})
        tip = model(f"{name}_tip", cross_parent, {"cross": tex(keys[1])})
        wj(A / f"blockstates/{name}.json", {"variants": {"tip=false": {"model": body}, "tip=true": {"model": tip}}})
        generated_item(name, tex(keys[0]))
        loot(name, self_drop(name, SHEARS))
    elif kind == "vine":
        # per-side vine (like vanilla vine): one plane just inside the north face (template_vine_side), rotated onto
        # each side whose property is true; one texture per shade (colour gradient down the strand) for body and tip
        side_model = lambda suffix, key, shade: model(f"{name}{suffix}_side_{shade}", "pysift:block/vegetation/template_vine_side",
                                                      {"vine": f"{tex(key)}_{shade}"})
        parts = []
        for s in range(3):
            for t in ("false", "true"):
                m = side_model("_tip", keys[1], s) if t == "true" else side_model("", keys[0], s)
                for side, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
                    parts.append({"when": {side: "true", "shade": str(s), "tip": t},
                                  "apply": {"model": m, "y": y} if y else {"model": m}})
        wj(A / f"blockstates/{name}.json", {"multipart": parts})
        wj(A / f"models/item/{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"{tex(keys[0])}_0"}})
        item(name, f"pysift:item/{name}")
        loot(name, self_drop(name, SHEARS))
    elif kind == "cube":
        m = model(name, "minecraft:block/cube_all", {"all": tex(keys[0])})
        wj(A / f"blockstates/{name}.json", {"variants": {"": {"model": m}}})
        wj(A / f"models/item/{name}.json", {"parent": m})
        item(name, f"pysift:item/{name}")
        loot(name, self_drop(name, {"type": "minecraft:survives_explosion"}))
    elif kind == "sapling":
        m = lush_model(name, tex(keys[0]), lush_cluster_elements(tinted, tilt=10.0))
        rot_variants = [{"model": m, **({"y": y} if y else {})} for y in (0, 90, 180, 270)]
        wj(A / f"blockstates/{name}.json", {"variants": {"stage=0": rot_variants, "stage=1": rot_variants}})
        generated_item(name, tex(keys[0]))
        loot(name, self_drop(name, {"type": "minecraft:survives_explosion"}))
    elif kind in ("cross", "flower"):
        if name == "humus_fern":
            elems = lush_fern_elements(tinted)
        elif name == "humus_bush":
            elems = lush_bush_elements(tinted)
        elif name == "glowcap":
            elems = lush_cluster_elements(tinted, light_emission=10, tilt=10.0)
        elif name == "bone_spire":
            elems = lush_cluster_elements(tinted, tilt=12.5)
        else:
            elems = lush_tuft_elements(tinted)
        m = lush_model(name, tex(keys[0]), elems)
        wj(A / f"blockstates/{name}.json", {"variants": {"": {"model": m}}})
        generated_item(name, tex(keys[0]))
        loot(name, self_drop(name, SHEARS if kind == "cross" else {"type": "minecraft:survives_explosion"}))
    elif kind == "big_flower":
        m = model(name, "pysift:block/vegetation/template_big_flower", {"petals": tex(keys[0]), "leaves": tex(keys[1])})
        wj(A / f"blockstates/{name}.json", {"variants": {"": [{"model": m, "y": r} if r else {"model": m}
                                                             for r in (0, 90, 180, 270)]}})
        generated_item(name, tex(keys[0]))
        if name in TINT:   # the leaf tint must not colour the petal icon
            item_def = lj(A / f"items/{name}.json")
            item_def["model"].pop("tints", None)
            wj(A / f"items/{name}.json", item_def)
        loot(name, self_drop(name, {"type": "minecraft:survives_explosion"}))
    elif kind == "tall":
        lower = lush_model(f"{name}_bottom", tex(keys[0]), lush_tall_elements(tinted, is_top=False))
        upper = lush_model(f"{name}_top", tex(keys[1]), lush_tall_elements(tinted, is_top=True))
        wj(A / f"blockstates/{name}.json", {"variants": {"half=lower": {"model": lower}, "half=upper": {"model": upper}}})
        generated_item(name, tex(keys[1]))
        loot(name, [{"condition": {"type": "minecraft:all_of", "terms": [
            {"type": "minecraft:match_block", "blocks": f"pysift:{name}", "state": {"half": "lower"}}, SHEARS]},
            "entries": [{"type": "minecraft:item", "name": f"pysift:{name}"}], "rolls": 1}])

# ---- shared parent model for the big flat flowers: a petal sheet 3px above ground + a low tinted leaf cross ----
leaf = lambda frm, to, faces: {"from": frm, "to": to, "shade_direction_override": "up",
                               "rotation": {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True},
                               "faces": {f: {"uv": [0, 10, 16, 16], "texture": "#leaves"} for f in faces}}
wj(A / "models/block/vegetation/template_big_flower.json", {
    "ambientocclusion": False,
    "textures": {"particle": "#petals"},
    "elements": [
        {"from": [0, 3, 0], "to": [16, 3, 16],
         "faces": {"up": {"uv": [0, 0, 16, 16], "texture": "#petals"}, "down": {"uv": [0, 0, 16, 16], "texture": "#petals"}}},
        leaf([0.8, 0, 8], [15.2, 6, 8], ("north", "south")),
        leaf([8, 0, 0.8], [8, 6, 15.2], ("east", "west")),
    ],
})

# ---- vine side template: one plane 0.8px inside the north face, textured on both sides; the blockstate rotates it
#      onto east / south / west (y = 90 / 180 / 270) for every side property that is true ----
plane = lambda frm, to, faces: {"from": frm, "to": to, "shade": False,
                                "faces": {f: {"uv": [0, 0, 16, 16], "texture": "#vine"} for f in faces}}
wj(A / "models/block/vegetation/template_vine_side.json", {
    "ambientocclusion": False,
    "textures": {"particle": "#vine"},
    "elements": [plane([0, 0, 0.8], [16, 16, 0.8], ("north", "south"))],
})
(A / "models/block/vegetation/template_four_sided_vine.json").unlink(missing_ok=True)   # replaced by template_vine_side

# ---- pysift tag: blocks a soul willow vine can hang from (SoulWillowVineBlock.SUPPORTS) ----
wj(D / "pysift/tags/block/soul_willow_vine_supports.json", {"replace": False, "values": [
    "pysift:soul_willow_leaves", "pysift:soul_willow_leaves_pale", "pysift:glowing_soul_willow_leaves",
    "#minecraft:leaves", "#minecraft:supports_vegetation"]})

# ---- spirit liquid: block (no item, no loot), bucket ----
wj(A / "models/block/vegetation/spirit_liquid.json", {"textures": {"particle": tex("spirit_liquid")}})
wj(A / "blockstates/spirit_liquid.json", {"variants": {"": {"model": "pysift:block/vegetation/spirit_liquid"}}})
wj(A / "items/spirit_liquid_bucket.json", {"model": {"type": "minecraft:model", "model": "minecraft:item/water_bucket"}})

# ---- mob effect icon placeholder (18x18 violet orb), written only if missing so real art is never overwritten ----
icon = A / "textures/mob_effect/soul_deprivation.png"
if not icon.exists():
    rows = []
    for y in range(18):
        row = bytearray([0])
        for x in range(18):
            d = ((x - 8.5) ** 2 + (y - 8.5) ** 2) ** 0.5
            if d < 7.5:
                k = max(0.0, 1 - d / 7.5)
                row += bytes((int(70 + 120 * k), int(40 + 60 * k), int(120 + 110 * k), 255))
            else:
                row += bytes(4)
        rows.append(bytes(row))
    chunk = lambda t, b: struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    icon.parent.mkdir(parents=True, exist_ok=True)
    icon.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 18, 18, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))

# ---- solid blocks for heightmaps ----
# 26.3 heightmaps (MOTION_BLOCKING / OCEAN_FLOOR, used by tree placement, spawning, etc.) treat a block as solid only if it
# is in #minecraft:blocks_motion_no_leaves. Every full pysift block goes in, except vegetation, the fluid and blocks
# already covered through #slabs / #stairs / #walls / #logs / #leaves.
NON_SOLID = {b for b, (kind, _, _) in BLOCKS.items() if kind not in ("log", "cube")} | {"spirit_liquid"}
NON_SOLID |= {"charoite_cluster"}    # progression (ModProgression): a small crystal, not a full block
COVERED_SUFFIXES = ("_slab", "_stairs", "_wall")
solid = sorted(f"pysift:{p.stem}" for p in (A / "blockstates").glob("*.json")
               if p.stem not in NON_SOLID and not p.stem.endswith(COVERED_SUFFIXES)
               and "soul_willow" not in p.stem)   # the wood set is covered by vanilla #logs / #planks / #fences ...
TAGS["block/blocks_motion_no_leaves"] = [s.split(":", 1)[1] for s in solid]

# ---- blocks that were replaced: delete their resources, tag entries and lang keys ----
for stale in ("soul_willow_vine", "soul_willow_vine_tip", "glowing_soul_willow_vine", "glowing_soul_willow_vine_tip"):
    (A / f"models/block/vegetation/{stale}.json").unlink(missing_ok=True)   # models from before the per-shade textures
    for shade in range(3):   # four-sided models from before the per-side faces
        (A / f"models/block/vegetation/{stale}_{shade}.json").unlink(missing_ok=True)
for name in REMOVED:
    for f in (A / f"blockstates/{name}.json", A / f"items/{name}.json", A / f"models/item/{name}.json",
              D / f"pysift/loot_table/blocks/{name}.json", D / f"pysift/loot_tables/blocks/{name}.json"):
        f.unlink(missing_ok=True)
    for f in (A / "models/block/vegetation").glob(f"{name}*.json"):
        f.unlink()
for path in (D / "minecraft/tags").rglob("*.json"):
    data = lj(path)
    kept = [v for v in data["values"] if not (isinstance(v, str) and v.removeprefix("pysift:") in REMOVED)]
    if len(kept) != len(data["values"]):
        data["values"] = kept
        wj(path, data)

# ---- tags (merge, keep other entries) ----
for tag, names in TAGS.items():
    path = D / f"minecraft/tags/{tag}.json"
    data = lj(path) if path.exists() else {"replace": False, "values": []}
    for n in names:
        if f"pysift:{n}" not in data["values"]:
            data["values"].append(f"pysift:{n}")
    wj(path, data)

# ---- lang ----
EXTRA = {"block.pysift.spirit_liquid": ("Spirit Liquid", "靈液"),
         "item.pysift.spirit_liquid_bucket": ("Spirit Liquid Bucket", "靈液桶"),
         "effect.pysift.soul_deprivation": ("Soul Deprivation", "靈魂剝奪")}
for lang in ("en_us", "zh_tw"):
    lf = A / f"lang/{lang}.json"
    d = lj(lf)
    for name, (_, _, zh) in BLOCKS.items():
        for key in (f"block.pysift.{name}", f"item.pysift.{name}"):   # items are registered without the block prefix
            d[key] = zh if lang == "zh_tw" else " ".join(w.capitalize() for w in name.split("_"))
    for name in REMOVED:
        d.pop(f"block.pysift.{name}", None)
        d.pop(f"item.pysift.{name}", None)
    for k, (en, zh) in EXTRA.items():
        d[k] = zh if lang == "zh_tw" else en
    wj(lf, d)
print(f"{len(BLOCKS)} vegetation blocks, spirit liquid, effect icon, {len(TAGS)} tags; tinted: {sorted(TINT)}")

# ---- random size + rotation: every single-block plant gets 0.8x / 1.0x / 1.2x model copies x 4 y-rotations
#      (veg_models.py variants; the user's Blockbench models are only read, never changed) ----
sys.path.insert(0, str(Path(__file__).resolve().parent))
import veg_models
SIZE_VARIANTS = ["ember_grass", "abyss_grass", "golden_bloom", "sun_bloom", "rose_bloom", "dusk_bloom",
                 "humus_grass", "humus_fern", "humus_bush", "glowcap", "bone_spire"]
for plant in SIZE_VARIANTS:
    veg_models.cmd_variants(plant)
