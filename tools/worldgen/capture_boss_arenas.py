"""Capture the three procedural boss arenas (BossArenaFeature) as structure templates the user can edit by hand.
Usage (test server running, tools/worldgen/devserver.py): python -I tools/worldgen/capture_boss_arenas.py

For each arena the worldgen configured feature itself is placed (/place feature, so materials, moat and pillars are exactly
what world generation builds) on a barrier platform in an empty part of the test world; after save-all the box around it is read
back from the region files (a redstone-powered structure block only saves to memory, never to disk) and written as a
template. Before it goes into the mod:
  - the barrier platform is dropped (it stands for "whatever terrain is there");
  - air outside the arena's footprint is dropped, so the template only clears the space the arena itself clears.
Output: data/pysift/structure/boss_arena/<type>.nbt, 47 x 30 x 47, arena centre in the middle column, arena floor (the
feature's centre block) at template y = FLOOR_ROW. BossArenaFeature places the template with the same convention.
Templates listed in tools/worldgen/art/edited_structures.json are the user's and are never overwritten.
"""
import importlib.util, json, math, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "src/main/resources/data/pysift/structure/boss_arena"
EDITED = ROOT / "tools/worldgen/art/edited_structures.json"
HALF, HEIGHT, FLOOR_ROW = 23, 30, 5          # must match BossArenaFeature.TEMPLATE_FLOOR_ROW
ARENAS = {  # type -> configured feature (one per biome, see tools/worldgen/build_the_sift.py)
    "monarch": "pysift:boss_arena_amber_dunes",
    "harmonizer": "pysift:boss_arena_willow_grove",
    "sculk_monstrosity": "pysift:boss_arena_violet_slate_abyss",
}
BASE_X, BASE_Z, FLOOR_Y = 12000, 12000, 100
DATA_VERSION = 5023      # same as the other templates (tools/worldgen/build_structures.py)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ds = load("devserver", ROOT / "tools/worldgen/devserver.py")
nbt = load("import_structures", ROOT / "tools/worldgen/import_structures.py")


def run(*commands):
    return ds.rcon(*[f"execute in pysift:the_sift run {c}" for c in commands])


def build_and_save(kind, feature, cx, cz):
    lo_x, lo_z, lo_y = cx - HALF, cz - HALF, FLOOR_Y - FLOOR_ROW
    hi_x, hi_z = cx + HALF, cz + HALF
    run(f"forceload add {lo_x - 2} {lo_z - 2} {hi_x + 2} {hi_z + 2}")
    for y in range(lo_y - 2, lo_y + HEIGHT + 2):   # one layer per fill (the fill limit is 32768 blocks)
        run(f"fill {lo_x - 2} {y} {lo_z - 2} {hi_x + 2} {y} {hi_z + 2} {'minecraft:barrier' if y <= FLOOR_Y else 'air'}")
    print(kind, run(f"place feature {feature} {cx} {FLOOR_Y + 1} {cz}"))
    for e in ("monarch", "harmonizer", "sculk_monstrosity"):   # the feature spawns its boss; it is not part of the build
        run(f"kill @e[type=pysift:{e},x={cx},y={FLOOR_Y},z={cz},distance=..40]")
    ds.rcon("save-all flush")
    time.sleep(2)
    box = ds.blocks_in_box(lo_x, lo_y, lo_z, hi_x, lo_y + HEIGHT - 1, hi_z, with_props=True)
    run(f"forceload remove {lo_x - 2} {lo_z - 2} {hi_x + 2} {hi_z + 2}")
    return {(x - lo_x, y - lo_y, z - lo_z): name for (x, y, z), name in box.items()}


def template(box):
    """Block map -> structure template: barrier dropped, air kept only inside the arena's footprint."""
    centre, size = HALF, 2 * HALF + 1
    solid = {p: n for p, n in box.items() if not n.startswith("minecraft:barrier")}
    reach = max(math.hypot(x - centre, z - centre) for x, _, z in solid) + 1.5
    for x in range(size):
        for z in range(size):
            if math.hypot(x - centre, z - centre) > reach:
                continue
            for y in range(HEIGHT):
                if (x, y, z) not in box:
                    solid[(x, y, z)] = "minecraft:air"
    palette, blocks = [], []
    for (x, y, z), name in sorted(solid.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0])):
        if name not in palette:
            palette.append(name)
        blocks.append({"pos": (9, (3, [x, y, z])), "state": (3, palette.index(name))})

    def entry(name):
        base, _, props = name.partition("[")
        e = {"id": (8, base)}   # 26.3 palette fields are id / properties
        if props:
            e["properties"] = (10, {k: (8, v) for k, v in (kv.split("=") for kv in props.rstrip("]").split(","))})
        return e
    root = {"DataVersion": (3, DATA_VERSION), "size": (9, (3, [size, HEIGHT, size])),
            "palette": (9, (10, [entry(n) for n in palette])), "blocks": (9, (10, blocks)), "entities": (9, (10, []))}
    return root, sum(1 for n in solid.values() if n != "minecraft:air"), reach


def main():
    edited = set(json.loads(EDITED.read_text(encoding="utf-8"))) if EDITED.exists() else set()
    for i, (kind, feature) in enumerate(ARENAS.items()):
        name = f"boss_arena/{kind}"
        if name in edited:
            print("skip (edited by the user):", name)
            continue
        root, solid, reach = template(build_and_save(kind, feature, BASE_X + i * 100, BASE_Z))
        DEST.mkdir(parents=True, exist_ok=True)
        (DEST / f"{kind}.nbt").write_bytes(nbt.write_nbt("", root))
        print(f"{name}: {solid} blocks, footprint radius {reach:.1f} -> {(DEST / f'{kind}.nbt').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
