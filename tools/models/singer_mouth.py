"""Give the Singer a mouth that opens while she sings.

Her mouth is already its own small cube on the face (1 x 0.5 px at y 34, just under the eyes). This moves that cube,
unchanged, into a new `mouth` bone (child of `head`, pivot at the cube's top edge) and keys the bone's scale in the
singing animations, so the mouth stretches downward into an open "O" and closes again. No cube is added and the
texture is not touched. Also adds `choir`, the 6.4 s animation the Echo Den choir plays while the lead sings the
Opening (8 notes, one every 0.8 s, see SingerEntity.tickChoir).
Idempotent; the geo and animation files are backed up to .texture_backups/<stamp>_singer_mouth/ before writing.
Re-run after tools/models/rig_mobs.py regenerates the singer.
Usage: python -I tools/models/singer_mouth.py <project>"""
import datetime
import json
import shutil
import sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
G = P / "src/main/resources/assets/pysift/geckolib/models/entity/singer.geo.json"
A = P / "src/main/resources/assets/pysift/geckolib/animations/entity/singer.animation.json"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_singer_mouth")

# the mouth cube: origin (-0.5, 34, -2.9), size 1 x 0.5. The tan face ends at y ~33.1, so opened (2.6x tall from the
# top edge at 34.5) the mouth reaches y 33.2 and stays on the face.
MOUTH_ORIGIN = [-0.5, 34, -2.9]
OPEN_X, OPEN_Y = 0.3, 1.6          # scale at "wide open": 1.3 wide, 2.6 tall


def keys(points):
    """[(t, open)] -> scale keyframes; open 0 = resting mouth, 1 = wide open."""
    return {"scale": {f"{t:.2f}".rstrip("0").rstrip(".") if t else "0.0":
                      [round(1 + OPEN_X * o, 3), round(1 + OPEN_Y * o, 3), 1] for t, o in points}}


def notes(starts, length, wide=1.0, hold=0.6):
    """open on each start, ease toward a held vowel, close just before the next one."""
    pts = [(0.0, 0.0)]
    for s in starts:
        pts += [(s + 0.08, wide), (s + hold * 0.6, wide * 0.75), (s + hold, wide * 0.15)]
    pts.append((length, 0.0))
    seen, out = set(), []
    for t, o in sorted(pts):
        t = round(min(t, length), 2)
        if t not in seen:
            seen.add(t)
            out.append((t, o))
    return keys(out)


MOUTH_KEYS = {
    "animation.singer.sing": notes([0.25, 0.65, 1.05], 1.5, hold=0.35),
    "animation.singer.await": notes([0.4, 1.4, 2.4, 3.4], 4.0, wide=0.35, hold=0.6),     # humming along
    "animation.singer.beckon": notes([0.3], 1.6, wide=0.4, hold=0.6),
    "animation.singer.finale": notes([0.3, 1.1, 1.9, 2.6], 3.6, wide=1.0, hold=0.7),
    "animation.singer.celebrate": notes([0.5, 1.5, 3.0], 5.0, wide=0.8, hold=0.8),
    "animation.singer.summon": notes([0.4], 2.0, wide=0.9, hold=1.2),
}

# the choir: arms lifted and swaying, head tipped up, a slow sway with each note; mouth opens on every note
ONSETS = [i * 0.8 for i in range(8)]
L = 6.4


def sway(amp, phase=0.0):
    pts = {}
    for i in range(9):
        t = round(i * 0.8, 2)
        side = (1 if (i + phase) % 2 == 0 else -1) * amp
        pts["0.0" if t == 0 else str(t)] = side
    return pts


CHOIR = {
    "animation_length": L,
    "bones": {
        "mouth": notes(ONSETS, L, wide=1.0, hold=0.7),
        "neck": {"rotation": {"0.0": [0, 0, 0], "0.4": [-18, 0, 0], "6.0": [-18, 0, 0], "6.4": [0, 0, 0]}},
        "head": {"rotation": {k: [-10 + abs(v) * 0.4, 0, v] for k, v in sway(6).items()} | {"6.4": [0, 0, 0]}},
        "body": {"rotation": {k: [0, 0, v * 0.5] for k, v in sway(5, 1).items()} | {"6.4": [0, 0, 0]}},
        "left_arm": {"rotation": {"0.0": [0, 0, 0], "0.4": [-40, 0, -45], "3.2": [-48, 0, -40], "6.0": [-40, 0, -45],
                                  "6.4": [0, 0, 0]}},
        "right_arm": {"rotation": {"0.0": [0, 0, 0], "0.4": [-40, 0, 45], "3.2": [-48, 0, 40], "6.0": [-40, 0, 45],
                                   "6.4": [0, 0, 0]}},
        "left_ear": {"rotation": {k: [0, 0, -20 - abs(v) * 2] for k, v in sway(4).items()} | {"6.4": [0, 0, 0]}},
        "right_ear": {"rotation": {k: [0, 0, 20 + abs(v) * 2] for k, v in sway(4, 1).items()} | {"6.4": [0, 0, 0]}},
    },
}

geo = json.loads(G.read_text(encoding="utf-8"))
ani = json.loads(A.read_text(encoding="utf-8"))
BK.mkdir(parents=True, exist_ok=True)
shutil.copy2(G, BK / G.name)
shutil.copy2(A, BK / A.name)

bones = geo["minecraft:geometry"][0]["bones"]
head = next(b for b in bones if b["name"] == "head")
mouth = next((b for b in bones if b["name"] == "mouth"), None)
if mouth is None:
    cube = next(c for c in head["cubes"] if c["origin"] == MOUTH_ORIGIN)
    head["cubes"].remove(cube)
    top = cube["origin"][1] + cube["size"][1]
    mouth = {"name": "mouth", "parent": "head", "pivot": [0, top, cube["origin"][2]], "cubes": [cube]}
    bones.insert(bones.index(head) + 1, mouth)

anims = ani["animations"]
for name, k in MOUTH_KEYS.items():
    anims[name].setdefault("bones", {})["mouth"] = k
anims["animation.singer.choir"] = CHOIR

G.write_text(json.dumps(geo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
A.write_text(json.dumps(ani, ensure_ascii=False, indent="	") + "\n", encoding="utf-8")
print("mouth bone + keys in", len(MOUTH_KEYS), "animations, choir", L, "s; backup", BK.relative_to(P))
