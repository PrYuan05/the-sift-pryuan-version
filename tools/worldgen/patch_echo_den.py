"""Add (or move) entities in landmark templates the user edited in game (listed in tools/worldgen/art/edited_structures.json),
without regenerating their blocks. build_landmarks.py skips those templates, so their extra entities live here.
Idempotent: an entity already standing on the same block with the same id is not added twice.
The file is backed up to .texture_backups/<stamp>_patch_echo_den/ before it is changed.
Usage: python -I tools/worldgen/patch_echo_den.py <project> [--dry-run]"""
import datetime
import gzip
import importlib.util
import shutil
import sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
DRY = "--dry-run" in sys.argv
S = P / "src/main/resources/data/pysift/structure"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_patch_echo_den")

_spec = importlib.util.spec_from_file_location("import_structures", P / "tools/worldgen/import_structures.py")
NBT = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, ["import_structures.py"]
_spec.loader.exec_module(NBT)
sys.argv = _argv

# template: [(x, y, z, entity id, yaw, tags)]  -- block coordinates inside the template; the entity stands at the centre
# yaw: 0 faces south, 90 west, 180 north, 270 east
ADD = {
    # the user's 25 x 22 x 25 hub (re-saved 2026-11-06 with structure voids; the in-game save drops entities):
    # chest on the stage at (12, 1, 12), note blocks around it, doorways with jigsaws on the four edges at y 2
    "echo_den/hub": [
        # the choir on the stage: the lead north of the chest facing south, the other two either side facing each other
        (12, 1, 10, "pysift:singer", 0.0, ["pysift_den_choir", "pysift_den_lead"]),
        (10, 1, 12, "pysift:singer", 270.0, ["pysift_den_choir"]),
        (14, 1, 12, "pysift:singer", 90.0, ["pysift_den_choir"]),
        # echo golems on the first tier around the stage, facing it (a golem is 1.4 wide: it needs the 3 x 3 blocks
        # around its own clear for 3 blocks up, or it spawns wedged into the seats and never moves)
        (12, 2, 6, "pysift:echo_golem", 0.0, []),
        (18, 2, 12, "pysift:echo_golem", 90.0, []),
        (12, 2, 18, "pysift:echo_golem", 180.0, []),
        (6, 2, 12, "pysift:echo_golem", 270.0, []),
        # den guards (healthy wardens, §4.7): inside the north and south doorways, facing out
        (12, 2, 4, "pysift:sift_warden", 180.0, ["pysift_den_guard"]),
        (12, 2, 20, "pysift:sift_warden", 0.0, ["pysift_den_guard"]),
    ],
}
EXPECTED_SIZE = {"echo_den/hub": [25, 22, 25], "lullaby_shrine": [15, 9, 15]}   # the coordinates only fit these layouts

# entities already in a template that stand wedged into blocks: (old block pos, id) -> new block pos
MOVE = {
    "echo_den/hub": {((12, 1, 7), "pysift:echo_golem"): (12, 2, 6), ((17, 1, 12), "pysift:echo_golem"): (18, 2, 12),
                     ((12, 1, 17), "pysift:echo_golem"): (12, 2, 18), ((7, 1, 12), "pysift:echo_golem"): (6, 2, 12)},
    # the two golems beside the note blocks were half inside them
    "lullaby_shrine": {((4, 1, 6), "pysift:echo_golem"): (4, 1, 7), ((10, 1, 8), "pysift:echo_golem"): (10, 1, 7)},
}

# every hub doorway must be an exit (name den_exit, target den_entry) so a corridor attaches by its entry end and keeps
# branching; a doorway saved as den_entry only takes a corridor backwards, which then dead-ends
EXIT = ("pysift:den_exit", "pysift:den_entry")
FIX_EXITS = {"echo_den/hub"}


def entity(x, y, z, eid, yaw, tags):
    nbt = {"id": (8, eid), "PersistenceRequired": (1, 1), "Rotation": (9, (5, [yaw, 0.0]))}
    if tags:
        nbt["Tags"] = (9, (8, list(tags)))
    return {"pos": (9, (6, [x + 0.5, float(y), z + 0.5])), "blockPos": (9, (3, [x, y, z])), "nbt": (10, nbt)}


for name in sorted(set(ADD) | set(MOVE)):
    wanted = ADD.get(name, [])
    f = S / f"{name}.nbt"
    tag_name, root = NBT.read_nbt(gzip.decompress(f.read_bytes()))
    size = [v for v in root["size"][1][1]]
    if name in EXPECTED_SIZE and size != EXPECTED_SIZE[name]:
        sys.exit(f"{name}: size {size}, expected {EXPECTED_SIZE[name]} - the template changed, update ADD first")
    fixed = 0
    if name in FIX_EXITS:
        for b in root["blocks"][1][1]:
            nbt = b.get("nbt", (10, {}))[1]
            if nbt.get("id", (8, ""))[1] == "minecraft:jigsaw" and nbt.get("name", (8, ""))[1] != EXIT[0]:
                nbt["name"], nbt["target"] = (8, EXIT[0]), (8, EXIT[1])
                fixed += 1
    ents = root.setdefault("entities", (9, (10, [])))[1][1]
    moved = 0
    for e in ents:
        key = (tuple(e.get("blockPos", (9, (3, [])))[1][1]), e["nbt"][1]["id"][1])
        if key in MOVE.get(name, {}):
            x, y, z = MOVE[name][key]
            e["blockPos"], e["pos"] = (9, (3, [x, y, z])), (9, (6, [x + 0.5, float(y), z + 0.5]))
            moved += 1
    have = {(tuple(e["blockPos"][1][1]), e["nbt"][1]["id"][1]) for e in ents if "blockPos" in e}
    added = 0
    for x, y, z, eid, yaw, tags in wanted:
        if ((x, y, z), eid) in have:
            continue
        ents.append(entity(x, y, z, eid, yaw, tags))
        added += 1
    print(f"{name}: +{added} entities ({len(ents)} total), {moved} moved, {fixed} doorway jigsaws turned into exits")
    if (added or moved or fixed) and not DRY:
        BK.mkdir(parents=True, exist_ok=True)
        (BK / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, BK / f"{name}.nbt")
        root["entities"] = (9, (10, ents))
        f.write_bytes(NBT.write_nbt(tag_name, root))
