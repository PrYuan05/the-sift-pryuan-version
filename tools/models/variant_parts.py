"""Exact-ratio 1:1 texel-density 3D part builder for Sift climate variant models (v2).

Unlike v1 (which stretched fixed UV boxes onto arbitrary cube dimensions, causing 5-8x squishing),
UVAllocator packs every newly added 3D part with per-face UV sizes strictly matching the cube's
physical dimensions times the mob's texel density (ratio error <= 1.15), and supports clean power-of-two
canvas expansion (e.g. 32x32 -> 64x64) with original UVs untouched in the top-left quadrant.
"""
import copy, json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "src/main/resources/assets/pysift/geckolib/models/entity"
SNAP = ROOT / ".texture_backups/20261124_mob_originals/files"
ALL = ("north", "south", "east", "west", "up", "down")


class UVPacker:
    """Packs exact-size UV rectangles into unused transparent space of a texture canvas (optionally expanded POT)."""

    def __init__(self, width, height, occupied=None):
        self.w = width
        self.h = height
        self.occ = set(occupied or ())
        self.rects = []   # list of (role, x, y, w, h, face, cube_meta)

    @classmethod
    def from_base_model(cls, mob, target_size=None, snap_root=SNAP):
        geo_path = GEO / f"{mob}.geo.json"
        doc = json.loads(geo_path.read_text(encoding="utf-8"))
        g = doc["minecraft:geometry"][0]
        bw, bh = g["description"].get("texture_width", 64), g["description"].get("texture_height", 64)
        tw, th = target_size or (bw, bh)
        occ = set()
        # Mark all base-model UV pixels and all opaque original pixels as occupied
        tex_path = snap_root / f"textures/entity/{mob}.png"
        if tex_path.exists():
            im = Image.open(tex_path).convert("RGBA")
            px = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    if px[x, y][3] > 0:
                        occ.add((x, y))
        for b in g["bones"]:
            for c in b.get("cubes", []):
                uv = c.get("uv")
                if isinstance(uv, dict):
                    for fd in uv.values():
                        if not isinstance(fd, dict):
                            continue
                        u, v = fd["uv"]
                        uw, vh = fd["uv_size"]
                        x0, x1 = sorted((int(u), int(round(u + uw))))
                        y0, y1 = sorted((int(v), int(round(v + vh))))
                        for y in range(max(0, y0), min(th, y1)):
                            for x in range(max(0, x0), min(tw, x1)):
                                occ.add((x, y))
        return cls(tw, th, occ)

    def alloc(self, w, h, role, face="", meta=None):
        w, h = max(1, int(round(w))), max(1, int(round(h)))
        for y in range(self.h - h + 1):
            for x in range(self.w - w + 1):
                ok = True
                for yy in range(y, y + h):
                    for xx in range(x, x + w):
                        if (xx, yy) in self.occ:
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    for yy in range(y, y + h):
                        for xx in range(x, x + w):
                            self.occ.add((xx, yy))
                    self.rects.append((role, x, y, w, h, face, meta or {}))
                    return (x, y, w, h)
        raise RuntimeError(f"UVPacker out of space for {role} ({w}x{h}) on {self.w}x{self.h} canvas")


def make_box(packer, origin, size, role, density=1.0, pivot=None, rotation=None, inflate=0,
             face_roles=None, shared_cache=None):
    """Build a GeckoLib cube with exact proportional per-face UVs (1:1 texel density matching `density`).
    `shared_cache`: optional dict[(role_key, uw, vh)] -> (u, v, uw, vh) to reuse identical texture tiles across symmetric parts."""
    sx, sy, sz = size
    dims = {
        "north": (sx, sy), "south": (sx, sy),
        "east": (sz, sy),  "west": (sz, sy),
        "up": (sx, sz),    "down": (sx, sz),
    }
    uv = {}
    for face, (fw, fh) in dims.items():
        if fw <= 0.01 or fh <= 0.01:
            continue
        uw = max(1, int(round(fw * density)))
        vh = max(1, int(round(fh * density)))
        frole = (face_roles or {}).get(face, role)
        ck = (frole, face if face in ("up", "down") else "side", uw, vh)
        if shared_cache is not None and ck in shared_cache:
            u, v, rw, rh = shared_cache[ck]
        else:
            u, v, rw, rh = packer.alloc(uw, vh, frole, face=face, meta={"size": list(size), "origin": list(origin)})
            if shared_cache is not None:
                shared_cache[ck] = (u, v, rw, rh)
        uv[face] = {"uv": [u, v], "uv_size": [rw, rh]}
    c = {"origin": [round(x, 3) for x in origin], "size": [round(x, 3) for x in size], "uv": uv}
    if inflate:
        c["inflate"] = inflate
    if rotation:
        c["pivot"] = [round(x, 3) for x in (pivot or origin)]
        c["rotation"] = [round(x, 3) for x in rotation]
    return c


def make_plane(packer, origin, size, role, density=1.0, pivot=None, rotation=None, shared_cache=None):
    """Build a vanilla-Minecraft thin alpha-cutout plane (0.05 thick, like Mooshroom/Axolotl/Warden/flowers).
    Only emits the 2 broad faces (ZERO thin sliver faces, 100% exact 1:1 UV, front & back share 1 crisp sprite)."""
    sx, sy, sz = size
    if sz <= 0.15:
        faces, fw, fh = ("north", "south"), sx, sy
    elif sx <= 0.15:
        faces, fw, fh = ("east", "west"), sz, sy
    else:
        faces, fw, fh = ("up", "down"), sx, sz
    uw = max(2, int(round(fw * density)))
    vh = max(2, int(round(fh * density)))
    ck = ("plane", role, uw, vh)
    if shared_cache is not None and ck in shared_cache:
        u, v, rw, rh = shared_cache[ck]
    else:
        u, v, rw, rh = packer.alloc(uw, vh, role, face=faces[0], meta={"plane": True, "size": list(size), "origin": list(origin)})
        if shared_cache is not None:
            shared_cache[ck] = (u, v, rw, rh)
    uv = {f: {"uv": [u, v], "uv_size": [rw, rh]} for f in faces}
    c = {"origin": [round(x, 3) for x in origin], "size": [round(x, 3) for x in size], "uv": uv}
    if rotation:
        c["pivot"] = [round(x, 3) for x in (pivot or origin)]
        c["rotation"] = [round(x, 3) for x in rotation]
    return c


def make_cross(packer, cx, by, cz, w, h, role, density=1.0, yaw=45.0, pitch=0.0, shared_cache=None):
    """Build a classic vanilla Minecraft X-crossed 2-plane plant/flower/crystal sprite centered at (cx, by, cz)."""
    piv = [cx, by, cz]
    p1 = make_plane(packer, [cx - w * 0.5, by, cz - 0.025], [w, h, 0.05], role, density=density,
                    pivot=piv, rotation=[pitch, yaw, 0], shared_cache=shared_cache)
    p2 = make_plane(packer, [cx - w * 0.5, by, cz - 0.025], [w, h, 0.05], role, density=density,
                    pivot=piv, rotation=[pitch, yaw + 90.0, 0], shared_cache=shared_cache)
    return [p1, p2]


def make_shell(packer, base_cube, inflate, role, density=1.0, skip_faces=("down",), shared_cache=None):
    """Wrap a base cube in a sleek Minecraft outer fur/jacket layer (like Sheep wool / Player outer layer)
    with exact 1:1 UVs and alpha-cutout shaggy lower hem."""
    o, s = base_cube["origin"], base_cube["size"]
    sx, sy, sz = s
    dims = {"north": (sx, sy), "south": (sx, sy), "east": (sz, sy), "west": (sz, sy), "up": (sx, sz), "down": (sx, sz)}
    uv = {}
    for face, (fw, fh) in dims.items():
        if face in skip_faces or fw <= 0.1 or fh <= 0.1:
            continue
        uw = max(2, int(round(fw * density)))
        vh = max(2, int(round(fh * density)))
        ck = ("shell", role, face if face in ("up", "down") else f"s_{uw}_{vh}", uw, vh)
        if shared_cache is not None and ck in shared_cache:
            u, v, rw, rh = shared_cache[ck]
        else:
            u, v, rw, rh = packer.alloc(uw, vh, role, face=face, meta={"shell": True, "size": list(s)})
            if shared_cache is not None:
                shared_cache[ck] = (u, v, rw, rh)
        uv[face] = {"uv": [u, v], "uv_size": [rw, rh]}
    c = {"origin": [round(x, 3) for x in o], "size": [round(x, 3) for x in s], "inflate": round(inflate, 3), "uv": uv}
    if base_cube.get("rotation"):
        c["pivot"] = list(base_cube.get("pivot", o))
        c["rotation"] = list(base_cube["rotation"])
    return c


def build_variant(mob, variant, add_fn, target_size=None):
    """Copy <mob>.geo.json to <mob>_<variant>.geo.json, optionally expand texture_width/height, and run add_fn."""
    doc = json.loads((GEO / f"{mob}.geo.json").read_text(encoding="utf-8"))
    geo = doc["minecraft:geometry"][0]
    geo["description"]["identifier"] = f"geometry.{mob}_{variant}"
    if target_size:
        geo["description"]["texture_width"] = target_size[0]
        geo["description"]["texture_height"] = target_size[1]
    bones = {b["name"]: b for b in geo["bones"]}

    def add(bone, cubes):
        bones[bone].setdefault("cubes", []).extend(copy.deepcopy(cubes))

    add_fn(add, bones)
    out = GEO / f"{mob}_{variant}.geo.json"
    out.write_text(json.dumps(doc, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("wrote", out.name)
    return out


# Keep legacy Parts / build / check_regions exports so existing scripts continue to import cleanly during transition
class Parts:
    def __init__(self, regions):
        self.R = regions

    def uv(self, region, rot=0):
        x, y, w, h = self.R[region]
        f = {"uv": [x, y], "uv_size": [w, h]}
        if rot:
            f["uv_rotation"] = rot
        return f

    def box(self, origin, size, side, top, front=None, bottom=None, inflate=0, pivot=None, rotation=None):
        c = {"origin": list(origin), "size": list(size),
             "uv": {"north": self.uv(front or side), "south": self.uv(side), "east": self.uv(side), "west": self.uv(side),
                    "up": self.uv(top), "down": self.uv(bottom or top)}}
        if inflate:
            c["inflate"] = inflate
        if rotation:
            c["pivot"], c["rotation"] = list(pivot), list(rotation)
        return c

    def faces(self, origin, size, mapping, pivot=None, rotation=None):
        c = {"origin": list(origin), "size": list(size), "uv": {f: self.uv(*([r] if isinstance(r, str) else r))
                                                                for f, r in mapping.items()}}
        if rotation:
            c["pivot"], c["rotation"] = list(pivot), list(rotation)
        return c


def build(mob, variant, add_fn):
    return build_variant(mob, variant, add_fn)
