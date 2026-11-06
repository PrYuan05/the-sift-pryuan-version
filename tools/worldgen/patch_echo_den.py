"""Add entities to Echo Den templates the user edited in game (listed in tools/worldgen/art/edited_structures.json),
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
ADD = {
    # the choir's singers on the stage (user's hub: chest under trapdoors in the middle, note blocks around it at r=3);
    # the lead singer faces south, the other two face each other across the chest
    "echo_den/hub": [
        (16, 1, 14, "pysift:singer", 0.0, ["pysift_den_choir", "pysift_den_lead"]),
        (14, 1, 16, "pysift:singer", 270.0, ["pysift_den_choir"]),
        (18, 1, 16, "pysift:singer", 90.0, ["pysift_den_choir"]),
        # den guards (healthy wardens, §4.7): just inside the north and south doorways, facing out
        (16, 2, 5, "pysift:sift_warden", 180.0, ["pysift_den_guard"]),
        (16, 2, 27, "pysift:sift_warden", 0.0, ["pysift_den_guard"]),
    ],
}


def entity(x, y, z, eid, yaw, tags):
    nbt = {"id": (8, eid), "PersistenceRequired": (1, 1), "Rotation": (9, (5, [yaw, 0.0]))}
    if tags:
        nbt["Tags"] = (9, (8, list(tags)))
    return {"pos": (9, (6, [x + 0.5, float(y), z + 0.5])), "blockPos": (9, (3, [x, y, z])), "nbt": (10, nbt)}


for name, wanted in ADD.items():
    f = S / f"{name}.nbt"
    tag_name, root = NBT.read_nbt(gzip.decompress(f.read_bytes()))
    ents = root.setdefault("entities", (9, (10, [])))[1][1]
    have = {(tuple(e["blockPos"][1][1]), e["nbt"][1]["id"][1]) for e in ents if "blockPos" in e}
    added = 0
    for x, y, z, eid, yaw, tags in wanted:
        if ((x, y, z), eid) in have:
            continue
        ents.append(entity(x, y, z, eid, yaw, tags))
        added += 1
    print(f"{name}: +{added} entities ({len(ents)} total)")
    if added and not DRY:
        BK.mkdir(parents=True, exist_ok=True)
        (BK / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, BK / f"{name}.nbt")
        root["entities"] = (9, (10, ents))
        f.write_bytes(NBT.write_nbt(tag_name, root))
