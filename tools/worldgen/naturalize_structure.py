"""Make a saved structure template sit naturally in uneven terrain.
Usage: python -I tools/worldgen/naturalize_structure.py <project> <name> [--support N] [--dry-run]
  e.g. python -I tools/worldgen/naturalize_structure.py . humbler_husk --support 6

Works on src/main/resources/data/pysift/structure/<name>.nbt:
  1. strip air: a template saved with a structure block stores every empty cell of its box as air, and placing it then
     carves the whole box out of the terrain (a flat rectangular pit in the dunes). Air cells are dropped, so the terrain
     stays where the template has nothing; air directly above chests / barrels is kept so they can still be opened.
  2. supports (--support N, default 0): under every column whose lowest block touches the template floor (y <= 1), N
     blocks of dune ground are added below it (2 amber sand, the rest amber sandstone), so on a slope the bones rest on a
     drift of sand instead of floating. The template grows N blocks downwards; the caller lowers start_height by N.
The original file is backed up to .texture_backups/<stamp>_naturalize/ first. Prints the new size."""
import gzip, sys, shutil, datetime, importlib.util
from pathlib import Path

P = Path(sys.argv[1]).resolve()
NAME = sys.argv[2]
SUPPORT = int(sys.argv[sys.argv.index("--support") + 1]) if "--support" in sys.argv else 0
DRY = "--dry-run" in sys.argv
SRC = P / "src/main/resources/data/pysift/structure" / f"{NAME}.nbt"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_naturalize")
TOP, DEEP = "pysift:amber_sand", "pysift:amber_sandstone"
SAND_LAYERS = 2

_spec = importlib.util.spec_from_file_location("import_structures", P / "tools/worldgen/import_structures.py")
NBT = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, ["import_structures.py"]
_spec.loader.exec_module(NBT)          # read_nbt / write_nbt (every tag type kept)
sys.argv = _argv

CONTAINERS = ("chest", "barrel", "trapped_chest")


def main():
    tag_name, root = NBT.read_nbt(gzip.decompress(SRC.read_bytes()))
    palette = root["palette"][1][1]
    blocks = root["blocks"][1][1]
    size = root["size"][1][1]
    ids = [p["id"][1] for p in palette]

    def state_index(block_id):
        if block_id not in ids:
            palette.append({"id": (8, block_id)})
            ids.append(block_id)
        return ids.index(block_id)

    pos = lambda b: b["pos"][1][1]
    containers = {tuple(pos(b)) for b in blocks if ids[b["state"][1]].split(":")[1] in CONTAINERS}
    keep_air = {(x, y + 1, z) for x, y, z in containers}
    air = {i for i, s in enumerate(ids) if s in ("minecraft:air", "minecraft:cave_air")}

    kept = [b for b in blocks if b["state"][1] not in air or tuple(pos(b)) in keep_air]
    stripped = len(blocks) - len(kept)

    lowest = {}
    for b in kept:
        if b["state"][1] in air:
            continue
        x, y, z = pos(b)
        lowest[(x, z)] = min(y, lowest.get((x, z), y))
    added = []
    if SUPPORT:
        for b in kept:                                   # everything moves up by SUPPORT
            b["pos"] = (9, (3, [pos(b)[0], pos(b)[1] + SUPPORT, pos(b)[2]]))
        for (x, z), y0 in lowest.items():
            if y0 > 1:
                continue
            for depth in range(1, SUPPORT + 1):          # depth 1 = right under the lowest block
                y = y0 + SUPPORT - depth
                block = TOP if depth <= SAND_LAYERS else DEEP
                added.append({"pos": (9, (3, [x, y, z])), "state": (3, state_index(block))})
        size[1] += SUPPORT
        for e in root.get("entities", (9, (10, [])))[1][1]:
            if "blockPos" in e:
                bp = e["blockPos"][1][1]; bp[1] += SUPPORT
            if "pos" in e:
                p = e["pos"][1][1]; p[1] += SUPPORT
    root["blocks"] = (9, (10, kept + added))
    print(f"{NAME}: stripped {stripped} air cells, "
          f"added {len(added)} support blocks under {sum(1 for y in lowest.values() if y <= 1) if SUPPORT else 0} columns, "
          f"size now {size}")
    if DRY:
        return
    BK.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, BK / SRC.name)
    SRC.write_bytes(NBT.write_nbt(tag_name, root))
    print("backup:", (BK / SRC.name).relative_to(P))


main()
