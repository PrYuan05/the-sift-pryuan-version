"""Clean up vegetation models and orphan textures, backing them up to .texture_backups first.
Usage: python -I tools/worldgen/cleanup_vegetation.py .
"""
import sys, json, shutil, datetime
from pathlib import Path

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift"
MODELS = A / "models/block/vegetation"
TEXTURES = A / "textures/block/vegetation"

STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BK = P / ".texture_backups" / f"{STAMP}_veg_cleanup"
BK.mkdir(parents=True, exist_ok=True)

def lj(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))

def wj(p, obj):
    p = Path(p)
    if p.exists():
        dst = BK / p.relative_to(P)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")

def backup_and_remove(p):
    p = Path(p)
    if p.exists():
        dst = BK / p.relative_to(P)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        p.unlink()
        print(f"Removed and backed up: {p.relative_to(P)}")

# 1. Remove duplicate/orphan dusk_bloom_1.json
backup_and_remove(MODELS / "dusk_bloom_1.json")

# 2. Remove unused 16x16 placeholder textures (now that 64x64 textures are used)
unused_textures = [
    "dusk_bloom_leaves.png",
    "dusk_bloom_petals.png",
    "rose_bloom_leaves.png",
    "rose_bloom_petals.png",
    "sun_bloom_leaves.png",
    "sun_bloom_petals.png",
]
for t in unused_textures:
    backup_and_remove(TEXTURES / t)

# 3. Clean zero-area faces and shading on custom 3D models
AXIS_OF = {"north": 2, "south": 2, "east": 0, "west": 0, "up": 1, "down": 1}
def face_area(e, face):
    f, t = e["from"], e["to"]
    dims = [abs(t[i] - f[i]) for i in range(3)]
    dims[AXIS_OF[face]] = 1
    return dims[0] * dims[1] * dims[2]

def clean_and_flat(name, add_particle=None):
    path = MODELS / f"{name}.json"
    if not path.exists():
        return
    j = lj(path)
    j["ambientocclusion"] = False
    if add_particle and "textures" in j:
        j["textures"]["particle"] = add_particle
    dropped = 0
    for e in j.get("elements", []):
        e["shade"] = False
        e.pop("shade_direction_override", None)
        for face in list(e.get("faces", {})):
            if face_area(e, face) == 0 or e["faces"][face].get("texture") == "#missing":
                del e["faces"][face]
                dropped += 1
    wj(path, j)
    print(f"{name}: dropped {dropped} zero-area faces, set ambientocclusion: false, shade: false")

clean_and_flat("abyss_grass")
clean_and_flat("golden_bloom", add_particle="pysift:block/vegetation/golden_bloom")
clean_and_flat("dusk_bloom")
clean_and_flat("sun_bloom")
clean_and_flat("rose_bloom")
clean_and_flat("ember_grass")

print("Cleanup completed successfully.")
