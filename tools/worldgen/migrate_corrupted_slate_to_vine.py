#!/usr/bin/env python3
"""
migrate_corrupted_slate_to_vine.py
==================================
1. Registers `corrupted_vine` (`CorruptedVineBlock` in `ModVegetation.java`) with:
   - 6-face attachment (`up`, `down`, `north`, `east`, `south`, `west`)
   - Placement-count progression (`corruption = 0..3`, upgrading `0 -> 1 -> 2 -> 3` when right-clicked with `corrupted_vine`)
   - Complete blockstate (`corrupted_vine.json`), face models (`models/block/corrupted_vine/`), item model, item definition,
     loot tables (dropping 1..4 `corrupted_vine` matching `corruption = 0..3`), tags (`replaceable_by_trees.json`), and lang (`en_us.json`, `zh_tw.json`).
2. Removes `corrupted_slate`, `corrupted_slate_bricks`, and their 7 building-set derivatives (`chiseled_corrupted_slate_bricks`,
   `corrupted_slate_slab`, `corrupted_slate_stairs`, `corrupted_slate_wall`, `corrupted_slate_brick_slab`,
   `corrupted_slate_brick_stairs`, `corrupted_slate_brick_wall`) from:
   - `ModBlocks.java` (`DEFS` and `BUILDING_SETS`)
   - `BossArenaFeature.java` (replaced with `dark_slate_bricks` / `chiseled_dark_slate_bricks`)
   - `tools/worldgen/build_the_sift.py`, `tools/worldgen/build_landmarks.py`, `tools/worldgen/build_structures.py`,
     `tools/worldgen/spire_palette.py`, `tools/worldgen/surface_candidates.py`
   - Worldgen JSONs (`boss_arena_violet_slate_abyss.json`, `soul_crystal_buried.json`, `soul_crystal_surface.json`, `soul_geode.json`)
   - All structure `.nbt` files (`lullaby_shrine.nbt`, `boss_arena/sculk_monstrosity.nbt`, `echo_den/*.nbt`, `abyss_obelisk.nbt`)
   - Blockstates, block/item models, item definitions, recipes, loot tables, tags, lang, and `recolor_manifest.json`.
"""

from __future__ import annotations

import datetime
import gzip
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "src" / "main" / "resources" / "assets" / "pysift"
DATA = ROOT / "src" / "main" / "resources" / "data"
PYSIFT_DATA = DATA / "pysift"
MC_DATA = DATA / "minecraft"
MANIFEST_PATH = ROOT / "tools" / "texture_pipeline" / "recolor_manifest.json"

REMOVED_BLOCKS = [
    "corrupted_slate",
    "corrupted_slate_bricks",
    "chiseled_corrupted_slate_bricks",
    "corrupted_slate_slab",
    "corrupted_slate_stairs",
    "corrupted_slate_wall",
    "corrupted_slate_brick_slab",
    "corrupted_slate_brick_stairs",
    "corrupted_slate_brick_wall",
]

VINE_VARIANTS = {
    0: ["corrupted_vine_corruption0_a", "corrupted_vine_corruption0_b"],
    1: ["corrupted_vine_corruption1"],
    2: [
        "corrupted_vine_corruption2_a",
        "corrupted_vine_corruption2_b",
        "corrupted_vine_corruption2_c",
        "corrupted_vine_corruption2_d",
        "corrupted_vine_corruption2_e",
    ],
    3: [
        "corrupted_vine_corruption3_a",
        "corrupted_vine_corruption3_b",
        "corrupted_vine_corruption3_c",
    ],
}


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


def sha1_file(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def generate_corrupted_vine_resources() -> None:
    """Generates models, blockstate, item definition, loot tables, and tags for `corrupted_vine`."""
    # 1. Shared template model for a single face (`north` wall at z=0.1, rotatable to all 6 directions via blockstate x/y)
    # Notice `from: [0, 0, 0.1]` to `[16, 16, 0.1]` with both `north` and `south` faces so when `north=true` (attached to
    # the block at `pos.north()`), it sits flush against `z=0.1`!
    template_dir = ASSETS / "models" / "block" / "corrupted_vine"
    template_dir.mkdir(parents=True, exist_ok=True)

    template_face = {
        "ambientocclusion": False,
        "textures": {
            "particle": "#vine",
        },
        "elements": [
            {
                "from": [0, 0, 0.1],
                "to": [16, 16, 0.1],
                "faces": {
                    "north": {"uv": [0, 0, 16, 16], "texture": "#vine"},
                    "south": {"uv": [0, 0, 16, 16], "texture": "#vine"},
                },
            }
        ],
    }
    write_json(template_dir / "template_corrupted_vine_face.json", template_face)

    # 2. Individual variant models for each of the 11 extracted textures
    for stage, names in VINE_VARIANTS.items():
        for name in names:
            model_obj = {
                "parent": "pysift:block/corrupted_vine/template_corrupted_vine_face",
                "textures": {
                    "vine": f"pysift:block/corrupted_vine/{name}",
                },
            }
            write_json(template_dir / f"{name}.json", model_obj)

    # 3. Multipart blockstate (`assets/pysift/blockstates/corrupted_vine.json`)
    # Rotations from `north` (z = 0.1):
    #   - `north`: {}
    #   - `east`:  {"y": 90}
    #   - `south`: {"y": 180}
    #   - `west`:  {"y": 270}
    #   - `up`:    {"x": 270} (rotates z=0.1 to y=15.9 ceiling!)
    #   - `down`:  {"x": 90}  (rotates z=0.1 to y=0.1 floor!)
    face_rotations = [
        ("north", {}),
        ("east", {"y": 90}),
        ("south", {"y": 180}),
        ("west", {"y": 270}),
        ("up", {"x": 270}),
        ("down", {"x": 90}),
    ]

    multipart = []
    for stage, names in VINE_VARIANTS.items():
        for face_name, rot in face_rotations:
            if len(names) == 1:
                apply_val: object = {"model": f"pysift:block/corrupted_vine/{names[0]}", **rot}
            else:
                apply_val = [{"model": f"pysift:block/corrupted_vine/{n}", "weight": 1, **rot} for n in names]
            multipart.append(
                {
                    "when": {face_name: "true", "corruption": str(stage)},
                    "apply": apply_val,
                }
            )

    write_json(ASSETS / "blockstates" / "corrupted_vine.json", {"multipart": multipart})

    # 4. Item model & Item definition (`corrupted_vine`)
    # Use `corrupted_vine_corruption2_a` as the crisp 2D item icon so the purple vine tendrils are clearly visible in hand/inventory!
    write_json(
        ASSETS / "models" / "item" / "corrupted_vine.json",
        {
            "parent": "minecraft:item/generated",
            "textures": {
                "layer0": "pysift:block/corrupted_vine/corrupted_vine_corruption2_a",
            },
        },
    )
    write_json(
        ASSETS / "items" / "corrupted_vine.json",
        {
            "model": {
                "type": "minecraft:model",
                "model": "pysift:item/corrupted_vine",
            }
        },
    )

    # 5. Loot table (`loot_table/blocks/corrupted_vine.json` and `loot_tables/blocks/corrupted_vine.json`)
    # Drops 1, 2, 3, or 4 `pysift:corrupted_vine` corresponding to `corruption = 0, 1, 2, 3`!
    loot_obj = {
        "type": "minecraft:block",
        "pools": [
            {
                "entries": [
                    {
                        "type": "minecraft:item",
                        "name": "pysift:corrupted_vine",
                        "modifier": [
                            {
                                "type": "minecraft:set_count",
                                "condition": {
                                    "type": "minecraft:match_block",
                                    "blocks": "pysift:corrupted_vine",
                                    "state": {"corruption": "0"},
                                },
                                "count": 1,
                            },
                            {
                                "type": "minecraft:set_count",
                                "condition": {
                                    "type": "minecraft:match_block",
                                    "blocks": "pysift:corrupted_vine",
                                    "state": {"corruption": "1"},
                                },
                                "count": 2,
                            },
                            {
                                "type": "minecraft:set_count",
                                "condition": {
                                    "type": "minecraft:match_block",
                                    "blocks": "pysift:corrupted_vine",
                                    "state": {"corruption": "2"},
                                },
                                "count": 3,
                            },
                            {
                                "type": "minecraft:set_count",
                                "condition": {
                                    "type": "minecraft:match_block",
                                    "blocks": "pysift:corrupted_vine",
                                    "state": {"corruption": "3"},
                                },
                                "count": 4,
                            },
                            {"type": "minecraft:explosion_decay"},
                        ],
                    }
                ],
                "rolls": 1,
            }
        ],
        "random_sequence": "pysift:blocks/corrupted_vine",
    }
    for sub in ("loot_table", "loot_tables"):
        write_json(PYSIFT_DATA / sub / "blocks" / "corrupted_vine.json", loot_obj)

    # 6. Add `pysift:corrupted_vine` to `minecraft/tags/block/replaceable_by_trees.json` so `verify.py` recognizes it as a plant
    rep_tag_path = MC_DATA / "tags" / "block" / "replaceable_by_trees.json"
    if rep_tag_path.exists():
        rep_data = json.loads(rep_tag_path.read_text(encoding="utf-8"))
        if "pysift:corrupted_vine" not in rep_data["values"]:
            rep_data["values"].append("pysift:corrupted_vine")
            write_json(rep_tag_path, rep_data)


def update_java_files() -> None:
    # 1. ModVegetation.java: add CORRUPTED_VINE
    veg_java = ROOT / "src" / "main" / "java" / "pryuan05" / "pysift" / "block" / "ModVegetation.java"
    txt = veg_java.read_text(encoding="utf-8")
    target = 'public static final Block ORANGE_SIFT_VINE = register("orange_sift_vine", p -> new SiftWallPlantBlock(p.noOcclusion()), Blocks.VINE, false);'
    addition = (
        target
        + '\n    /** 腐化藤蔓：六面可貼附，依放置次數將 corruption 從 0 -> 1 -> 2 -> 3 升級。 */\n'
        + '    public static final Block CORRUPTED_VINE = register("corrupted_vine", p -> new CorruptedVineBlock(p.noOcclusion()), Blocks.VINE, false);'
    )
    if "CORRUPTED_VINE" not in txt:
        assert target in txt, "Could not find ORANGE_SIFT_VINE in ModVegetation.java"
        txt = txt.replace(target, addition, 1)
        veg_java.write_text(txt, encoding="utf-8")
        print("  ✅ 已於 ModVegetation.java 註冊 CORRUPTED_VINE")

    # 2. ModBlocks.java: remove corrupted_slate and corrupted_slate_bricks from DEFS, and corrupted_slate from BUILDING_SETS
    mod_blocks = ROOT / "src" / "main" / "java" / "pryuan05" / "pysift" / "block" / "ModBlocks.java"
    btxt = mod_blocks.read_text(encoding="utf-8")
    lines = btxt.splitlines(keepends=True)
    new_lines = []
    for line in lines:
        if 'block("corrupted_slate",' in line or 'block("corrupted_slate_bricks",' in line or '"corrupted_slate",' in line:
            continue
        new_lines.append(line)
    mod_blocks.write_text("".join(new_lines), encoding="utf-8")
    print("  ✅ 已從 ModBlocks.java 移除 corrupted_slate、corrupted_slate_bricks 與其建材組")

    # 3. BossArenaFeature.java: replace getBlock("corrupted_slate_bricks") with getBlock("chiseled_dark_slate_bricks")
    arena_java = ROOT / "src" / "main" / "java" / "pryuan05" / "pysift" / "worldgen" / "BossArenaFeature.java"
    atxt = arena_java.read_text(encoding="utf-8")
    if '"corrupted_slate_bricks"' in atxt:
        atxt = atxt.replace('getBlock("corrupted_slate_bricks")', 'getBlock("chiseled_dark_slate_bricks")')
        arena_java.write_text(atxt, encoding="utf-8")
        print("  ✅ 已更新 BossArenaFeature.java 中的方塊引用")


def remove_old_assets_and_data() -> None:
    # 1. Remove blockstates, models/item, items, loot_table, loot_tables for REMOVED_BLOCKS
    for bid in REMOVED_BLOCKS:
        for p in [
            ASSETS / "blockstates" / f"{bid}.json",
            ASSETS / "models" / "item" / f"{bid}.json",
            ASSETS / "items" / f"{bid}.json",
            PYSIFT_DATA / "loot_table" / "blocks" / f"{bid}.json",
            PYSIFT_DATA / "loot_tables" / "blocks" / f"{bid}.json",
        ]:
            if p.exists():
                p.unlink()

    # 2. Remove block model folders & texture folders for removed blocks
    for folder in [
        ASSETS / "models" / "block" / "corrupted_slate",
        ASSETS / "models" / "block" / "corrupted_slate_bricks",
        ASSETS / "models" / "block" / "corrupted_slate_slab",
        ASSETS / "models" / "block" / "corrupted_slate_stairs",
        ASSETS / "models" / "block" / "corrupted_slate_wall",
        ASSETS / "models" / "block" / "corrupted_slate_brick_slab",
        ASSETS / "models" / "block" / "corrupted_slate_brick_stairs",
        ASSETS / "models" / "block" / "corrupted_slate_brick_wall",
        ASSETS / "textures" / "block" / "corrupted_slate",
        ASSETS / "textures" / "block" / "corrupted_slate_bricks",
    ]:
        if folder.exists():
            shutil.rmtree(folder)

    # 3. Remove recipes referencing corrupted_slate
    recipe_dir = PYSIFT_DATA / "recipe"
    if recipe_dir.exists():
        for rp in recipe_dir.glob("*corrupted_slate*.json"):
            rp.unlink()

    # 4. Clean tags (`slabs.json`, `stairs.json`, `walls.json`, `mineable/pickaxe.json`, `blocks_motion_no_leaves.json`, `in_worldgen.json`, `not_in_worldgen.json`)
    removed_ids = {f"pysift:{b}" for b in REMOVED_BLOCKS}
    for tag_path in DATA.rglob("tags/**/*.json"):
        tdata = json.loads(tag_path.read_text(encoding="utf-8"))
        if "values" in tdata:
            orig_len = len(tdata["values"])
            tdata["values"] = [v for v in tdata["values"] if v not in removed_ids]
            if len(tdata["values"]) != orig_len:
                write_json(tag_path, tdata)

    # 5. Update lang files (`en_us.json`, `zh_tw.json`): remove old keys and add `corrupted_vine`
    lang_names = {
        "en_us": "Corrupted Vine",
        "zh_tw": "腐化藤蔓",
    }
    for lcode, lname in lang_names.items():
        lpath = ASSETS / "lang" / f"{lcode}.json"
        raw = lpath.read_text(encoding="utf-8-sig")
        ldata = json.loads(raw)
        for bid in REMOVED_BLOCKS:
            ldata.pop(f"block.pysift.{bid}", None)
            ldata.pop(f"item.pysift.{bid}", None)
        ldata["block.pysift.corrupted_vine"] = lname
        ldata["item.pysift.corrupted_vine"] = lname
        write_json(lpath, ldata)


def update_worldgen_and_structures() -> None:
    # 1. Update worldgen feature JSONs
    arena_json = PYSIFT_DATA / "worldgen" / "feature" / "boss_arena_violet_slate_abyss.json"
    if arena_json.exists():
        write_json(
            arena_json,
            {
                "type": "pysift:boss_arena",
                "arena_type": "sculk_monstrosity",
                "boss": "pysift:sculk_monstrosity",
                "radius": 16,
                "pillar_height": 10,
                "pillar_count": 8,
                "floor": {
                    "type": "minecraft:weighted",
                    "entries": [
                        {"data": "pysift:dark_slate_bricks", "weight": 3},
                        {"data": "pysift:chiseled_dark_slate_bricks", "weight": 1},
                    ],
                },
                "wall": {"id": "pysift:dark_slate_brick_wall"},
                "pillar": {"id": "pysift:dark_slate_pillar", "properties": {"axis": "y"}},
            },
        )

    for ore_file in ("soul_crystal_surface.json", "soul_crystal_buried.json"):
        op = PYSIFT_DATA / "worldgen" / "feature" / ore_file
        if op.exists():
            odata = json.loads(op.read_text(encoding="utf-8"))
            odata["targets"] = [
                t for t in odata.get("targets", []) if t.get("target", {}).get("block") != "pysift:corrupted_slate"
            ]
            write_json(op, odata)

    geode_json = PYSIFT_DATA / "worldgen" / "feature" / "soul_geode.json"
    if geode_json.exists():
        gdata = json.loads(geode_json.read_text(encoding="utf-8"))
        gdata["blocks"]["middle_layer_provider"] = {
            "id": "pysift:dark_slate",
            "properties": {"fade": "0"},
        }
        write_json(geode_json, gdata)

    # 2. Update Python worldgen scripts so future runs don't reference `corrupted_slate`
    for py_rel, replacements in [
        (
            "tools/worldgen/build_the_sift.py",
            [
                (
                    'floor=weighted(*[state("corrupted_slate_bricks", corruption=c) for c in (0, 1, 2)],\n                                              state("dark_slate_bricks"))',
                    'floor=weighted(state("dark_slate_bricks"), state("chiseled_dark_slate_bricks"))',
                ),
                (
                    'for b in ("violet_capped_dark_slate", "dark_slate", "void_stone", "corrupted_slate")',
                    'for b in ("violet_capped_dark_slate", "dark_slate", "void_stone")',
                ),
                (
                    'middle_layer_provider": provider("corrupted_slate", corruption=1)',
                    'middle_layer_provider": provider("dark_slate", fade=0)',
                ),
            ],
        ),
        (
            "tools/worldgen/build_landmarks.py",
            [
                ('return "corrupted_slate_bricks"', 'return "chiseled_dark_slate_bricks"'),
            ],
        ),
        (
            "tools/worldgen/build_structures.py",
            [
                (
                    'corruption = t.rnd.choice((0, 0, 1, 2))\n            t.set(x, 0, z, "corrupted_slate_bricks", corruption=corruption)',
                    't.set(x, 0, z, "dark_slate_bricks")',
                ),
            ],
        ),
    ]:
        py_path = ROOT / py_rel
        if py_path.exists():
            ptxt = py_path.read_text(encoding="utf-8")
            for old, new in replacements:
                ptxt = ptxt.replace(old, new)
            py_path.write_text(ptxt, encoding="utf-8")

    # 3. Patch gzipped structure `.nbt` files that contain `pysift:corrupted_slate_bricks` or `pysift:corrupted_slate`
    # In NBT binary format, strings are prefixed with a 2-byte big-endian length (`\x00\x1d` for `pysift:corrupted_slate_bricks`).
    # Let's parse or replace length-prefixed UTF-8 strings cleanly!
    for nbt_path in (PYSIFT_DATA / "structure").rglob("*.nbt"):
        raw = gzip.decompress(nbt_path.read_bytes())
        if b"corrupted_slate" not in raw:
            continue
        # Replace length-prefixed `pysift:corrupted_slate_bricks` -> `pysift:dark_slate_bricks`
        # and `pysift:corrupted_slate` -> `pysift:dark_slate`
        for old_str, new_str in [
            (b"pysift:corrupted_slate_bricks", b"pysift:dark_slate_bricks"),
            (b"pysift:chiseled_corrupted_slate_bricks", b"pysift:chiseled_dark_slate_bricks"),
            (b"pysift:corrupted_slate_brick_slab", b"pysift:dark_slate_brick_slab"),
            (b"pysift:corrupted_slate_brick_stairs", b"pysift:dark_slate_brick_stairs"),
            (b"pysift:corrupted_slate_brick_wall", b"pysift:dark_slate_brick_wall"),
            (b"pysift:corrupted_slate_slab", b"pysift:dark_slate_slab"),
            (b"pysift:corrupted_slate_stairs", b"pysift:dark_slate_stairs"),
            (b"pysift:corrupted_slate_wall", b"pysift:dark_slate_wall"),
            (b"pysift:corrupted_slate", b"pysift:dark_slate"),
        ]:
            old_lp = len(old_str).to_bytes(2, "big") + old_str
            new_lp = len(new_str).to_bytes(2, "big") + new_str
            raw = raw.replace(old_lp, new_lp)

        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
            gz.write(raw)
        nbt_path.write_bytes(buf.getvalue())
        print(f"  ✅ 已更新結構檔中的舊方塊 ID: {nbt_path.relative_to(ROOT)}")


def update_manifest() -> None:
    if not MANIFEST_PATH.exists():
        return
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    kept = [
        e
        for e in data.get("entries", [])
        if not e["file"].startswith("textures/block/corrupted_slate/")
        and not e["file"].startswith("textures/block/corrupted_slate_bricks/")
    ]
    by_file = {e["file"]: e for e in kept}

    for p in sorted((ASSETS / "textures" / "block" / "corrupted_vine").glob("*.png")):
        rel = p.relative_to(ASSETS).as_posix()
        stage = p.stem.split("corruption")[1].split("_")[0]
        by_file[rel] = {
            "file": rel,
            "pool": f"corrupted_vine:corruption={stage}",
            "reference": "pysift:block/dark_slate_pillar/dark_slate_pillar_side",
            "source": rel,
            "mode": "extracted_transparent_vine",
            "method": "minecraft_texture_crafter",
            "sha1_before": None,
            "sha1_after": sha1_file(p),
            "backup": None,
            "date": stamp,
        }

    data["entries"] = [by_file[k] for k in sorted(by_file.keys())]
    write_json(MANIFEST_PATH, data)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    generate_corrupted_vine_resources()
    update_java_files()
    remove_old_assets_and_data()
    update_worldgen_and_structures()
    update_manifest()
    print("\n🎉 已完成 corrupted_vine 六向貼附腐化藤蔓方塊建置，並完整移除 corrupted_slate 與 corrupted_slate_bricks 系列！")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
