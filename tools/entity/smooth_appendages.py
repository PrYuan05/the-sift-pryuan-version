"""Make tentacles / legs that are drawn as several flat segments bend smoothly instead of swinging as one stiff piece.
Usage: python -I tools/entity/smooth_appendages.py <project> [--dry-run]

For each appendage bone listed in APPENDAGES:
  1. geometry: the segments (cubes) are sorted top -> bottom; the top one stays in the bone, every following one moves
     into its own child bone (<bone>_seg1, <bone>_seg2, ...) chained under the previous segment, pivoting at the
     segment's top centre. The existing animations of the bone itself keep working (they now move the whole chain).
  2. animation: every looping animation of the entity gets a travelling wave on the segment bones: each segment rotates
     a little more than the one above it and lags behind it in phase, so the bend runs down the appendage like a
     tentacle in water. Keyframes use catmullrom interpolation for smooth curves.
Idempotent: segment bones that already exist are rebuilt from scratch. The original files are backed up once to
.texture_backups/geckolib/ before the first change."""
import json, math, shutil, sys
from pathlib import Path

P = Path(sys.argv[1])
DRY = "--dry-run" in sys.argv
GL = P / "src/main/resources/assets/pysift/geckolib"
BACKUP = P / ".texture_backups/geckolib"

# entity: (appendage bones, {loop animation: (amplitude degrees at the tip, phase lag per segment, waves per loop)})
APPENDAGES = {
    "harmonizer": ([f"tentacle_{i}" for i in range(1, 9)],
                   {"animation.harmonizer.idle": (16.0, 0.9, 1), "animation.harmonizer.walk": (22.0, 1.0, 1)}),
    "sprout": (["front_left_leg", "front_right_leg", "back_left_leg", "back_right_leg", "middle_leg"],
               {"animation.sprout.idle": (6.0, 0.8, 1), "animation.sprout.walk": (16.0, 1.1, 1)}),
}
SAMPLES = 12          # keyframes per loop (catmullrom between them)


def lj(p): return json.loads(p.read_text(encoding="utf-8"))


def wj(p, obj):
    if DRY:
        return
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def backup(p):
    dst = BACKUP / p.relative_to(GL)
    if not dst.exists() and not DRY:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)


def top(c): return c["origin"][1] + c["size"][1]


for entity, (bones, loops) in APPENDAGES.items():
    geo_path = GL / f"models/entity/{entity}.geo.json"
    anim_path = GL / f"animations/entity/{entity}.animation.json"
    backup(geo_path)
    backup(anim_path)
    geo = lj(geo_path)
    model = geo["minecraft:geometry"][0]
    by_name = {b["name"]: b for b in model["bones"]}
    # undo a previous run: put segment cubes back into their appendage bone
    for b in list(model["bones"]):
        if "_seg" in b["name"] and b["name"].split("_seg")[0] in bones:
            by_name[b["name"].split("_seg")[0]]["cubes"] += b.get("cubes", [])
            model["bones"].remove(b)
    segments = {}
    for name in bones:
        bone = by_name[name]
        cubes = sorted(bone.get("cubes", []), key=top, reverse=True)
        bone["cubes"] = cubes[:1]
        parent, chain = name, []
        for k, cube in enumerate(cubes[1:], 1):
            o, s = cube["origin"], cube["size"]
            seg = {"name": f"{name}_seg{k}", "parent": parent,
                   "pivot": [round(o[0] + s[0] / 2, 4), round(o[1] + s[1], 4), round(o[2] + s[2] / 2, 4)],
                   "cubes": [cube]}
            model["bones"].insert(model["bones"].index(by_name[parent]) + 1, seg)
            by_name[seg["name"]] = seg
            chain.append(seg["name"])
            parent = seg["name"]
        segments[name] = chain
    wj(geo_path, geo)

    anims = lj(anim_path)
    for anim_name, (amp, lag, waves) in loops.items():
        anim = anims["animations"][anim_name]
        length = float(anim.get("animation_length", 1.0))
        bones_json = anim.setdefault("bones", {})
        for key in [k for k in bones_json if "_seg" in k]:
            del bones_json[key]
        for a_i, name in enumerate(bones):
            chain = segments[name]
            offset = a_i * 2.39                      # golden-angle offset: neighbouring appendages out of step
            for k, seg in enumerate(chain, 1):
                strength = amp * k / len(chain) / len(chain) * 1.6   # spread the tip bend over the chain
                frames = {}
                for i in range(SAMPLES + 1):
                    t = i / SAMPLES
                    ph = math.tau * waves * t - lag * k + offset
                    frames[f"{round(t * length, 4)}"] = {
                        "post": [round(strength * math.sin(ph), 3), 0, round(strength * 0.7 * math.cos(ph), 3)],
                        "lerp_mode": "catmullrom"}
                bones_json[seg] = {"rotation": frames}
    wj(anim_path, anims)
    print(f"{entity}: " + ", ".join(f"{n} -> {len(c)} segments" for n, c in segments.items()))
