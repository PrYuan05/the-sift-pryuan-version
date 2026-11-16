"""Fix flickering (z-fighting) in the GeckoLib entity models.
Usage: python -I tools/models/fix_zfight.py <project> [mob ...] [--write]

Two causes are fixed, geometry only (UVs, rotations, bones and animations are untouched):
  1. zero-thickness planes: GeckoLib entity render types do not cull back faces, so a plane's front and back quads sit
     at exactly the same depth and fight. Every zero-size axis becomes PLANE (0.05 px), centred on the old plane.
  2. coplanar overlapping faces of different cubes (details glued onto a body surface, duplicated cubes): the smaller
     cube is pushed PUSH px along the shared plane's normal, away from the larger cube. Repeated until clean (max 10).
Without --write it only reports. With --write the geo files are backed up to .texture_backups/<time>_zfight/ first."""
import sys, json, math, shutil, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rig_view import cube_corners, bone_chain, FACES  # noqa: E402

P = Path(sys.argv[1])
WRITE = "--write" in sys.argv
GEO_DIR = P / "src/main/resources/assets/pysift/geckolib/models/entity"
mobs = [a for a in sys.argv[2:] if not a.startswith("--")] or sorted(f.name.split(".")[0] for f in GEO_DIR.glob("*.geo.json"))
PLANE = 0.05
PUSH = 0.05


def sub(a, b): return [a[i] - b[i] for i in range(3)]
def dot(a, b): return sum(a[i] * b[i] for i in range(3))
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def norm(v):
    n = math.sqrt(dot(v, v))
    return [x / n for x in v] if n > 1e-9 else None


def faces_of(cube, chain):
    pts = cube_corners(cube, chain)
    out = []
    for name, ids in FACES.items():
        q = [pts[k] for k in ids]
        n = norm(cross(sub(q[1], q[0]), sub(q[3], q[0])))
        if n is None:
            continue
        out.append((name, q, n, dot(n, q[0])))
    return out, [sum(p[i] for p in pts) / 8 for i in range(3)]


def overlap(qa, qb, n):
    """Area of overlap of two coplanar quads, approximated by their 2D bounding boxes in the plane."""
    u = norm(cross(n, [0, 1, 0] if abs(n[1]) < 0.9 else [1, 0, 0]))
    v = cross(n, u)
    ra = [(dot(p, u), dot(p, v)) for p in qa]
    rb = [(dot(p, u), dot(p, v)) for p in qb]
    w = min(max(x for x, _ in ra), max(x for x, _ in rb)) - max(min(x for x, _ in ra), min(x for x, _ in rb))
    h = min(max(y for _, y in ra), max(y for _, y in rb)) - max(min(y for _, y in ra), min(y for _, y in rb))
    return w * h if w > 0.01 and h > 0.01 else 0.0


def size_key(c):
    w, h, d = c["size"]
    return 2 * (w * h + h * d + w * d)


def fix_planes(geo):
    n = 0
    for b in geo["bones"]:
        for c in b.get("cubes", []):
            for i in range(3):
                if abs(c["size"][i]) < 1e-6:
                    c["size"][i] = PLANE
                    c["origin"][i] = round(c["origin"][i] - PLANE / 2, 4)
                    n += 1
    return n


def drop_duplicates(geo):
    """Exact duplicate cubes (same origin, size, rotation, pivot) always flicker against each other: keep the first."""
    seen, n = set(), 0
    for b in geo["bones"]:
        keep = []
        for c in b.get("cubes", []):
            key = (b["name"], tuple(c["origin"]), tuple(c["size"]), tuple(c.get("rotation", [0, 0, 0])),
                   tuple(c.get("pivot", [0, 0, 0])), c.get("inflate", 0))
            if key in seen:
                n += 1
                continue
            seen.add(key)
            keep.append(c)
        if "cubes" in b:
            b["cubes"] = keep
    return n


def find_conflicts(geo):
    by_name = {b["name"]: b for b in geo["bones"]}
    items = []
    for b in geo["bones"]:
        chain = bone_chain(by_name, b["name"])
        for c in b.get("cubes", []):
            fs, centre = faces_of(c, chain)
            items.append((c, fs, centre))
    conflicts = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            ci, fi, cen_i = items[i]
            cj, fj, cen_j = items[j]
            for _, qa, na, da in fi:
                hit = None
                for _, qb, nb, db in fj:
                    s = dot(na, nb)
                    if abs(s) > 0.999 and abs(da - (db if s > 0 else -db)) < 0.02 and overlap(qa, qb, na) > 0:
                        hit = na
                        break
                if hit:
                    small, big, cs, cb = (ci, cj, cen_i, cen_j) if size_key(ci) <= size_key(cj) else (cj, ci, cen_j, cen_i)
                    away = hit if dot(hit, sub(cs, cb)) >= 0 else [-x for x in hit]
                    conflicts.append((small, away))
                    break
    return conflicts


def push(c, d):
    c["origin"] = [round(c["origin"][i] + d[i] * PUSH, 4) for i in range(3)]
    if "pivot" in c:
        c["pivot"] = [round(c["pivot"][i] + d[i] * PUSH, 4) for i in range(3)]


stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
bdir = P / ".texture_backups" / f"{stamp}_zfight"
total = 0
for mob in mobs:
    f = GEO_DIR / f"{mob}.geo.json"
    doc = json.loads(f.read_text(encoding="utf-8"))
    geo = doc["minecraft:geometry"][0]
    dups = drop_duplicates(geo)
    planes = fix_planes(geo)
    pushed = 0
    for _ in range(10):
        conf = find_conflicts(geo)
        if not conf:
            break
        done = set()
        for c, d in conf:
            if id(c) not in done:
                push(c, d)
                done.add(id(c))
                pushed += 1
    # cubes squeezed between two surfaces bounce back and forth when pushed: grow them slightly instead
    inflated = 0
    for _ in range(8):
        conf = find_conflicts(geo)
        if not conf:
            break
        done = set()
        for c, _d in conf:
            if id(c) not in done:
                # a different amount per cube, so identical duplicate cubes separate too
                c["inflate"] = round(c.get("inflate", 0) + 0.02 * (len(done) + 1), 4)
                done.add(id(c))
                inflated += 1
    left = len(find_conflicts(geo))
    total += dups + planes + pushed + inflated
    print(f"{mob:24s} duplicates removed {dups:2d}, planes thickened {planes:3d}, cubes pushed {pushed:3d}, inflated {inflated:2d}, remaining conflicts {left}")
    if WRITE and (dups or planes or pushed or inflated):
        bdir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, bdir / f.name)
        f.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
print(("wrote" if WRITE else "would change"), total, "items", ("; backup in " + str(bdir.relative_to(P)) if WRITE else ""))
