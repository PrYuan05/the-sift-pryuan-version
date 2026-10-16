"""Tools for the user's Blockbench vegetation models (Java block models, 26.3 format).
Usage: python -I tools/worldgen/veg_models.py <project> <command> <name> [args]

  clean <name>               drop zero-area faces (the edges of 0-thick planes, exported with texture "#missing")
  flat <name>                light like vanilla plants: ambientocclusion false, shade false on every element
  tint <name>                add "tintindex": 0 to every face (for blocks coloured by FloorTint)
  variants <name> [s1,s2..]  write scaled copies <name>_s<pct> (default 80,120; scaled about the bottom centre) and a
                             blockstate picking every size x 4 y-rotations at random; the original model is not changed
  icon <name> [#rrggbb]      render a 32x32 flat item icon (textures/item/<name>.png) from the block model, seen like a
                             vanilla block in the GUI (from above-front, 45 deg); faces with a tintindex are multiplied by
                             the colour; also writes models/item/<name>.json (item/generated) and a preview
Every command backs the files it rewrites up to .texture_backups/<stamp>_veg_models/ first."""
import sys, json, math, shutil, datetime, copy
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift"
MODELS = A / "models/block/vegetation"
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BK = P / ".texture_backups" / f"{STAMP}_veg_models"
PREVIEW = P / "build/texture_pipeline/out/veg_icons"


def lj(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p = Path(p)
    if p.exists():
        dst = BK / p.relative_to(P)
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")


def load_model(ref):
    """Resolve a model ref with its parents; returns (elements, textures)."""
    ns, path = ref.split(":") if ":" in ref else ("minecraft", ref)
    if ns != "pysift":
        return None, {}
    j = lj(A / "models" / (path + ".json"))
    elements, textures = None, {}
    if "parent" in j:
        elements, textures = load_model(j["parent"])
    textures = {**textures, **j.get("textures", {})}
    if "elements" in j:
        elements = j["elements"]
    return elements, textures


# ------------------------------------------------------------------ geometry
FACE_CORNERS = {   # face -> corners TL, TR, BR, BL as (x?, y?, z?) picks of (min=0 / max=1), seen from outside
    "north": ((1, 1, 0), (0, 1, 0), (0, 0, 0), (1, 0, 0)),
    "south": ((0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)),
    "east": ((1, 1, 1), (1, 1, 0), (1, 0, 0), (1, 0, 1)),
    "west": ((0, 1, 0), (0, 1, 1), (0, 0, 1), (0, 0, 0)),
    "up": ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)),
    "down": ((0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)),
}
AXIS_OF = {"north": 2, "south": 2, "east": 0, "west": 0, "up": 1, "down": 1}


def rot(p, axis, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    x, y, z = p
    if axis == "x":
        return (x, y * c - z * s, y * s + z * c)
    if axis == "y":
        return (x * c + z * s, y, -x * s + z * c)
    return (x * c - y * s, x * s + y * c, z)


def element_transform(e):
    r = e.get("rotation")
    if not r:
        return lambda p: p
    o = r.get("origin", [8, 8, 8])
    if "axis" in r:
        axis, ang = r["axis"], r.get("angle", 0)
        sc = [1, 1, 1]
        if r.get("rescale") and abs(math.cos(math.radians(ang))) > 1e-6:
            k = 1 / math.cos(math.radians(ang))
            sc = [1 if ax == axis else k for ax in "xyz"]
        steps = [(axis, ang)]
    else:   # 26.3 multi-axis rotation: x first, then y, then z (Blockbench's ZYX euler order)
        sc, steps = [1, 1, 1], [(ax, r.get(ax, 0)) for ax in "xyz" if r.get(ax, 0)]

    def f(p):
        q = tuple((p[i] - o[i]) * sc[i] for i in range(3))
        for ax, ang in steps:
            q = rot(q, ax, ang)
        return tuple(q[i] + o[i] for i in range(3))
    return f


def face_area(e, face):
    f, t = e["from"], e["to"]
    dims = [abs(t[i] - f[i]) for i in range(3)]
    dims[AXIS_OF[face]] = 1
    return dims[0] * dims[1] * dims[2]


# ------------------------------------------------------------------ commands
def cmd_clean(name):
    path = MODELS / f"{name}.json"
    j = lj(path)
    dropped = 0
    for e in j.get("elements", []):
        for face in list(e.get("faces", {})):
            if face_area(e, face) == 0 or e["faces"][face].get("texture") == "#missing":
                del e["faces"][face]
                dropped += 1
    wj(path, j)
    print(f"{name}: dropped {dropped} zero-area / #missing faces")


def cmd_flat(name):
    """Light like vanilla plants (minecraft:block/cross): no ambient occlusion and no per-direction face shading, so
    tilted blades are not darkened differently from each other."""
    path = MODELS / f"{name}.json"
    j = lj(path)
    j["ambientocclusion"] = False
    for e in j.get("elements", []):
        e["shade"] = False
        e.pop("shade_direction_override", None)
    wj(path, j)
    print(f"{name}: ambientocclusion off, shade off on {len(j.get('elements', []))} elements")


def cmd_tint(name):
    path = MODELS / f"{name}.json"
    j = lj(path)
    n = 0
    for e in j.get("elements", []):
        for f in e.get("faces", {}).values():
            f["tintindex"] = 0
            n += 1
    wj(path, j)
    print(f"{name}: tintindex on {n} faces")


def scaled(model, s):
    m = copy.deepcopy(model)
    c = (8.0, 0.0, 8.0)
    sp = lambda p: [round(c[i] + (p[i] - c[i]) * s, 4) for i in range(3)]
    for e in m.get("elements", []):
        e["from"], e["to"] = sp(e["from"]), sp(e["to"])
        if e.get("rotation") and "origin" in e["rotation"]:
            e["rotation"]["origin"] = sp(e["rotation"]["origin"])
        for v in e["from"] + e["to"]:
            assert -16 <= v <= 32, f"scaled element leaves the -16..32 range ({v}); use a smaller scale"
    m.pop("groups", None)
    return m


def cross_elements(tinted):
    """The two diagonal planes of minecraft:block/cross (tinted_cross adds tintindex 0)."""
    face = lambda: {"uv": [0, 0, 16, 16], "texture": "#cross", **({"tintindex": 0} if tinted else {})}
    rot = lambda: {"origin": [8, 8, 8], "axis": "y", "angle": 45, "rescale": True}
    return [{"from": [0.8, 0, 8], "to": [15.2, 16, 8], "shade": False, "rotation": rot(),
             "faces": {"north": face(), "south": face()}},
            {"from": [8, 0, 0.8], "to": [8, 16, 15.2], "shade": False, "rotation": rot(),
             "faces": {"east": face(), "west": face()}}]


def cmd_variants(name, scales="80,120"):
    base = lj(MODELS / f"{name}.json")
    if "elements" not in base and base.get("parent") in ("minecraft:block/cross", "minecraft:block/tinted_cross"):
        base = {"ambientocclusion": False, "textures": {**base.get("textures", {}), "particle": base["textures"]["cross"]},
                "elements": cross_elements(base["parent"].endswith("tinted_cross"))}
    refs = [(f"pysift:block/vegetation/{name}", 2)]           # the original size is the most common
    for pct in (int(x) for x in scales.split(",")):
        wj(MODELS / f"{name}_s{pct}.json", scaled(base, pct / 100))
        refs.append((f"pysift:block/vegetation/{name}_s{pct}", 1))
    variants = [{"model": ref, "weight": w, **({"y": y} if y else {})} for ref, w in refs for y in (0, 90, 180, 270)]
    bs = A / f"blockstates/{name}.json"
    j = lj(bs)
    key = next(iter(j["variants"])) if "variants" in j else ""
    wj(bs, {"variants": {key: variants}})
    print(f"{name}: {len(refs)} sizes x 4 rotations")


def cmd_icon(name, colour=None):
    tint = tuple(int(colour.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) if colour else None
    bs = lj(A / f"blockstates/{name}.json")
    first = next(iter(bs["variants"].values())) if "variants" in bs else None
    if isinstance(first, list):
        first = first[0]
    ref = first["model"]
    elements, textures = load_model(ref)
    if elements is None:   # vanilla parent (cross / tinted_cross): two diagonal planes
        tex = textures.get("cross")
        elements = [{"from": [0.8, 0, 8], "to": [15.2, 16, 8], "rotation": {"origin": [8, 8, 8], "axis": "y", "angle": 45,
                     "rescale": True}, "faces": {f: {"uv": [0, 0, 16, 16], "texture": "#cross", "tintindex": 0}
                                                for f in ("north", "south")}},
                    {"from": [8, 0, 0.8], "to": [8, 16, 15.2], "rotation": {"origin": [8, 8, 8], "axis": "y", "angle": 45,
                     "rescale": True}, "faces": {f: {"uv": [0, 0, 16, 16], "texture": "#cross", "tintindex": 0}
                                                for f in ("east", "west")}}]
        textures = {"cross": tex}
    img = render(elements, textures, tint)
    out = A / f"textures/item/{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        dst = BK / out.relative_to(P)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out, dst)
    img.save(out)
    wj(A / f"models/item/{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"pysift:item/{name}"}})
    PREVIEW.mkdir(parents=True, exist_ok=True)
    big = render(elements, textures, tint, size=192)
    sheet = Image.new("RGBA", (192 + 16 + 192, 192), (36, 36, 42, 255))
    sheet.alpha_composite(big, (0, 0))
    sheet.alpha_composite(img.resize((192, 192), Image.Resampling.NEAREST), (208, 0))
    sheet.save(PREVIEW / f"{name}.png")
    print(f"{name}: icon {out.relative_to(P)} (model {ref})")


def tex_image(ref, cache={}):
    if ref not in cache:
        ns, path = ref.split(":") if ":" in ref else ("minecraft", ref)
        root = A if ns == "pysift" else None
        if root is None:
            raise SystemExit(f"vanilla texture {ref} needs a local copy")
        cache[ref] = Image.open(root / "textures" / (path + ".png")).convert("RGBA")
    return cache[ref]


def resolve(textures, key):
    seen = 0
    while key.startswith("#") and seen < 8:
        key = textures.get(key[1:], key)
        seen += 1
    return key


def render(elements, textures, tint, size=32, yaw=45.0, pitch=32.0):
    """Orthographic z-buffered render seen from above-front; returns an RGBA image of size x size."""
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, spch = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def view(p):
        x, y, z = p[0] - 8, p[1] - 8, p[2] - 8
        x, z = x * cy - z * sy, x * sy + z * cy            # yaw around y
        y, z = y * cp - z * spch, y * spch + z * cp        # pitch: tilt the top towards the viewer
        return x, -y, z                                    # screen x, screen y (down), depth (bigger = farther)

    quads = []
    for e in elements:
        tf = element_transform(e)
        f, t = e["from"], e["to"]
        lo = [min(f[i], t[i]) for i in range(3)]
        hi = [max(f[i], t[i]) for i in range(3)]
        for face, fd in e.get("faces", {}).items():
            if face_area(e, face) == 0:
                continue
            ref = resolve(textures, fd.get("texture", "#missing"))
            if ref.startswith("#"):
                continue
            pts = [view(tf(tuple(hi[i] if c[i] else lo[i] for i in range(3)))) for c in FACE_CORNERS[face]]
            u1, v1, u2, v2 = fd.get("uv", [0, 0, 16, 16])
            uvs = [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]
            r = (fd.get("rotation", 0) // 90) % 4
            uvs = uvs[r:] + uvs[:r]
            quads.append((pts, uvs, tex_image(ref), "tintindex" in fd))
    xs = [p[0] for q in quads for p in q[0]]
    ys = [p[1] for q in quads for p in q[0]]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1
    k = (size - 2) / span
    ox, oy = (size - (max(xs) - min(xs)) * k) / 2 - min(xs) * k, (size - (max(ys) - min(ys)) * k) / 2 - min(ys) * k
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = out.load()
    zbuf = [[math.inf] * size for _ in range(size)]
    for pts, uvs, tex, tinted in quads:
        sp = [(p[0] * k + ox, p[1] * k + oy, p[2]) for p in pts]
        tw, th = tex.size
        tpx = tex.load()
        for tri in ((0, 1, 2), (0, 2, 3)):
            (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = (sp[i] for i in tri)
            den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(den) < 1e-9:
                continue
            for yy in range(max(0, int(min(y0, y1, y2))), min(size, int(max(y0, y1, y2)) + 1)):
                for xx in range(max(0, int(min(x0, x1, x2))), min(size, int(max(x0, x1, x2)) + 1)):
                    cx, cyy = xx + 0.5, yy + 0.5
                    a = ((y1 - y2) * (cx - x2) + (x2 - x1) * (cyy - y2)) / den
                    b = ((y2 - y0) * (cx - x2) + (x0 - x2) * (cyy - y2)) / den
                    c = 1 - a - b
                    if a < -1e-6 or b < -1e-6 or c < -1e-6:
                        continue
                    z = a * z0 + b * z1 + c * z2
                    if z >= zbuf[yy][xx]:
                        continue
                    u = a * uvs[tri[0]][0] + b * uvs[tri[1]][0] + c * uvs[tri[2]][0]
                    v = a * uvs[tri[0]][1] + b * uvs[tri[1]][1] + c * uvs[tri[2]][1]
                    sx = min(tw - 1, max(0, int(u / 16 * tw)))
                    syy = min(th - 1, max(0, int(v / 16 * th)))
                    col = tpx[sx, syy]
                    if col[3] < 128:
                        continue
                    if tinted and tint:
                        col = (col[0] * tint[0] // 255, col[1] * tint[1] // 255, col[2] * tint[2] // 255, 255)
                    zbuf[yy][xx] = z
                    px[xx, yy] = (col[0], col[1], col[2], 255)
    return out


if __name__ == "__main__":
    cmd, name, *rest = sys.argv[2:]
    {"clean": cmd_clean, "flat": cmd_flat, "tint": cmd_tint, "variants": cmd_variants, "icon": cmd_icon}[cmd](name, *rest)
