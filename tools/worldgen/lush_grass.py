"""Denser, flatter-lit grass clumps built from the user's Blockbench grass models.
Usage: python -I tools/worldgen/lush_grass.py <project> [--preview-only]

For every *_grass model below:
  1. the first run saves the user's model to tools/worldgen/art/lush_src/<model>.json; every run builds from that
     copy, so re-running never stacks copies on top of copies;
  2. the clump is doubled with a copy turned 180 degrees (two mirrors; a mirror maps every element rotation exactly,
     it just negates the rotation angles about the other two axes), then every blade (a ground segment plus the
     segments stacked on it, found by matching each segment's bottom to the nearest segment top) is moved outwards
     from the clump centre so the roots fill the whole block (REACH), made WIDEN wider and a random GROW taller.
     Tall grass is handled as one plant (top half shifted up 16), so blades still run on into the top block;
  3. blades are made 0 thick (like vanilla cross planes): the thin edge faces, which showed up as dark slivers, are
     dropped, which also halves the quads per blade;
  4. ambientocclusion off, shade off (flat light, as before).
Blade textures whose bottoms are much darker than their tips get that baked-in gradient softened (SOFTEN keeps this
much of each pixel's darkness, in HSV value; hue and saturation unchanged).
Rewritten files are backed up to .texture_backups/<stamp>_lush_grass/ first. Afterwards re-run
`veg_models.py <project> variants <name>` for the grasses that have _s80/_s120 size copies."""
import sys, json, copy, shutil, datetime, colorsys, random, importlib.util
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
PREVIEW_ONLY = "--preview-only" in sys.argv
A = P / "src/main/resources/assets/pysift"
MODELS = A / "models/block/vegetation"
SRC = P / "tools/worldgen/art/lush_src"
_spec = importlib.util.spec_from_file_location("veg_models", P / "tools/worldgen/veg_models.py")
VM = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(VM)                     # element_transform: the 26.3 element rotation (x, then y, then z)
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BK = P / ".texture_backups" / f"{STAMP}_lush_grass"

# 裂隙橙／薄荷短草、裂隙橙高草已改用 sift_vegetation_assets 的十字貼圖（tools/worldgen/rename_vegetation.py），不在這裡處理
SHORT = ["ember_grass", "abyss_grass", "humus_grass", "rift_yellow_short_grass"]
TALL = ["tall_ember_grass", "tall_humus_grass", "glowshade_tall_grass", "puff_grass"]
# (mirror x, mirror z): the original clump plus one copy turned 180 degrees (fills the gaps the original leaves)
COPIES = [(False, False), (True, True)]
REACH = 6.6          # blade roots are spread out (about the clump centre) until the outermost is this far from the
                     # block centre, so the base of the clump fills the whole block instead of a small tuft
WIDEN = 1.6          # blades are this much wider ...
GROW = (1.05, 1.25)  # ... and each blade a random amount taller (uniformly scaled about its own root)
THIN = 0.51          # elements at most this thick (in px) are blades -> made 0 thick
SOFTEN = 0.45        # keep 45% of the darkness of blade textures (bottom 0x73 -> ~0xc0)
SOFTEN_IF_MIN = 0x90  # only textures whose darkest pixel is below this


def lj(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def backup(p):
    dst = BK / p.relative_to(P)
    if p.exists() and not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)


def wj(p, obj):
    backup(p)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")


def source(model):
    """The user's original model (saved on the first run)."""
    s = SRC / f"{model}.json"
    if not s.exists():
        SRC.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MODELS / f"{model}.json", s)
    return lj(s)


def ends(e):
    """World-space bottom-centre and top-centre of an element."""
    f, t, tr = e["from"], e["to"], VM.element_transform(e)
    mx, mz = (f[0] + t[0]) / 2, (f[2] + t[2]) / 2
    return tr((mx, f[1], mz)), tr((mx, t[1], mz))


def blade_roots(elements):
    """For each element, the index of the ground segment its blade grows from."""
    info = [ends(e) for e in elements]
    parent = {}
    for i, (bot, _) in enumerate(info):
        if bot[1] < 0.75:
            continue
        best = min((j for j in range(len(elements)) if j != i),
                   key=lambda j: sum((info[j][1][k] - bot[k]) ** 2 for k in range(3)))
        parent[i] = best
    roots = []
    for i in range(len(elements)):
        j, seen = i, set()
        while j in parent and j not in seen:
            seen.add(j)
            j = parent[j]
        roots.append(j)
    return roots, info


def scale_about(e, b, s):
    for key in ("from", "to"):
        e[key] = [b[i] + (e[key][i] - b[i]) * s for i in range(3)]
    if "rotation" in e and "origin" in e["rotation"]:
        e["rotation"]["origin"] = [b[i] + (e["rotation"]["origin"][i] - b[i]) * s for i in range(3)]


def move(e, d):
    for key in ("from", "to"):
        e[key] = [e[key][i] + d[i] for i in range(3)]
    if "rotation" in e and "origin" in e["rotation"]:
        e["rotation"]["origin"] = [e["rotation"]["origin"][i] + d[i] for i in range(3)]


def widen(e):
    """Wider blade: stretch the wide horizontal axis of a 0-thick blade about its own centre (the joints to the
    segments above and below sit on that centre line, so they stay put)."""
    f, t = e["from"], e["to"]
    dims = [t[i] - f[i] for i in range(3)]
    if 0 in (dims[0], dims[2]):
        ax = 2 if dims[0] == 0 else 0
        mid = (f[ax] + t[ax]) / 2
        f[ax], t[ax] = mid - (mid - f[ax]) * WIDEN, mid + (t[ax] - mid) * WIDEN


def spread(elements, rnd):
    roots, info = blade_roots(elements)
    bases = {r: info[r][0] for r in set(roots)}
    cx = sum(b[0] for b in bases.values()) / len(bases)
    cz = sum(b[2] for b in bases.values()) / len(bases)
    # per axis, so a clump that was long and narrow still fills the block both ways (capped for near-lines)
    kx = min(4.0, REACH / (max(abs(b[0] - cx) for b in bases.values()) or 1))
    kz = min(4.0, REACH / (max(abs(b[2] - cz) for b in bases.values()) or 1))
    grow = {r: rnd.uniform(*GROW) for r in bases}
    for e, r in zip(elements, roots):
        b = bases[r]
        scale_about(e, b, grow[r])
        widen(e)
        move(e, ((8 + (b[0] - cx) * kx) - b[0], 0, (8 + (b[2] - cz) * kz) - b[2]))
        for key in ("from", "to"):
            e[key] = [round(v, 3) for v in e[key]]
        if "rotation" in e and "origin" in e["rotation"]:
            e["rotation"]["origin"] = [round(v, 3) for v in e["rotation"]["origin"]]


def centre(elements):
    xs = [e.get("rotation", {}).get("origin", [(e["from"][0] + e["to"][0]) / 2, 0, 0])[0] for e in elements]
    zs = [e.get("rotation", {}).get("origin", [0, 0, (e["from"][2] + e["to"][2]) / 2])[2] for e in elements]
    return sum(xs) / len(xs), sum(zs) / len(zs)


def mirror_rotation(r, axis):
    """Mirror along `axis` ('x' or 'z'): rotations about the other two axes change sign."""
    r = dict(r)
    if "axis" in r:
        if r["axis"] != axis:
            r["angle"] = -r.get("angle", 0)
    else:
        for ax in "xyz":
            if ax != axis and r.get(ax):
                r[ax] = -r[ax]
    return r


def transform(e, mx, mz, s, dx, dz, cx, cz, ground):
    e = copy.deepcopy(e)
    pivot = (cx, ground, cz)

    def pt(p):
        q = list(p)
        if mx: q[0] = 2 * cx - q[0]
        if mz: q[2] = 2 * cz - q[2]
        q = [pivot[i] + (q[i] - pivot[i]) * s for i in range(3)]
        return [round(q[0] + dx, 3), round(q[1], 3), round(q[2] + dz, 3)]

    a, b = pt(e["from"]), pt(e["to"])
    e["from"], e["to"] = [min(a[i], b[i]) for i in range(3)], [max(a[i], b[i]) for i in range(3)]
    if "rotation" in e:
        r = e["rotation"]
        if mx: r = mirror_rotation(r, "x")
        if mz: r = mirror_rotation(r, "z")
        if "origin" in r:
            r["origin"] = pt(r["origin"])
        e["rotation"] = r
    # mirroring swaps which side a face is on: east<->west for x, north<->south for z
    faces = e.get("faces", {})
    if mx and ("east" in faces or "west" in faces):
        faces["east"], faces["west"] = faces.pop("west", None), faces.pop("east", None)
    if mz and ("north" in faces or "south" in faces):
        faces["north"], faces["south"] = faces.pop("south", None), faces.pop("north", None)
    e["faces"] = {k: v for k, v in faces.items() if v is not None}
    return e


def flatten_blade(e):
    """0-thick blade: collapse the thin horizontal axis and drop the faces that lose their area."""
    dims = [e["to"][i] - e["from"][i] for i in range(3)]
    for ax in (0, 2):
        if 0 < dims[ax] <= THIN and dims[ax] == min(d for d in dims if d > 0):
            mid = round((e["from"][ax] + e["to"][ax]) / 2, 3)
            e["from"][ax] = e["to"][ax] = mid
            keep = ("west", "east") if ax == 0 else ("north", "south")
            e["faces"] = {k: v for k, v in e["faces"].items() if k in keep}
            break
    return e


def build(parts, ground_of):
    """parts: model names forming one plant (1 for short grass, bottom+top for tall grass). The halves are joined into
    one element list (top shifted up by -ground) so blades are traced across the two blocks, then split again."""
    srcs = {m: source(m) for m in parts}
    joined = []
    for m in parts:
        for e in srcs[m]["elements"]:
            e = copy.deepcopy(e)
            move(e, (0, -ground_of[m], 0))
            joined.append((m, e))
    cx, cz = centre([e for _, e in joined])
    rnd = random.Random(parts[0])
    out = {m: [] for m in parts}
    for mx, mz in COPIES:
        layer = [(m, flatten_blade(transform(e, mx, mz, 1.0, 0, 0, cx, cz, 0))) for m, e in joined]
        spread([e for _, e in layer], rnd)
        for m, e in layer:
            move(e, (0, ground_of[m], 0))
            e["from"] = [round(v, 3) for v in e["from"]]
            e["to"] = [round(v, 3) for v in e["to"]]
            if "rotation" in e and "origin" in e["rotation"]:
                e["rotation"]["origin"] = [round(v, 3) for v in e["rotation"]["origin"]]
            e["shade"] = False
            out[m].append(e)
    result = {}
    for m in parts:
        j = copy.deepcopy(srcs[m])
        j["elements"] = out[m]
        j["ambientocclusion"] = False
        result[m] = j
    return result


def soften(tex_ref):
    ns, path = tex_ref.split(":")
    p = A / "textures" / (path + ".png")
    img = Image.open(p).convert("RGBA")
    vals = [max(px[:3]) for px in img.getdata() if px[3]]
    if not vals or min(vals) >= SOFTEN_IF_MIN:
        return None
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            v = 1 - (1 - v) * SOFTEN
            px[x, y] = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, s, v)) + (a,)
    return p, img, min(vals)


def main():
    plants = [([m], {m: 0}) for m in SHORT] + \
             [([f"{t}_bottom", f"{t}_top"], {f"{t}_bottom": 0, f"{t}_top": -16}) for t in TALL]
    textures = set()
    for parts, ground in plants:
        for m, j in build(parts, ground).items():
            before = len(source(m)["elements"])
            print(f"{m}: {before} -> {len(j['elements'])} elements")
            textures.update(v for k, v in j["textures"].items() if k != "particle")
            if not PREVIEW_ONLY:
                wj(MODELS / f"{m}.json", j)
    for t in sorted(textures):
        r = soften(t)
        if r:
            p, img, lo = r
            print(f"soften {p.relative_to(P)} (darkest {lo:#x})")
            if not PREVIEW_ONLY:
                backup(p)
                img.save(p)
    if not PREVIEW_ONLY:
        print("backups:", BK.relative_to(P))


main()
