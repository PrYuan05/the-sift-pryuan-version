"""Shared 3D parts for the climate variant models (tools/models/build_<mob>_variants.py, user 2026-11-24).

Each builder defines REGIONS {"<role>.<key>": (x, y, w, h)} in unused texture space (mob_upgrade.paint_parts paints them
by role) and builds cubes with the helpers below. Flowers are real 3D parts: a thin petal plate with a raised centre,
facing up, +x (east), -x (west), -z (north) or +z (south)."""
import copy, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "src/main/resources/assets/pysift/geckolib/models/entity"
ALL = ("north", "south", "east", "west", "up", "down")


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

    def flower(self, facing, x, y, z, key="a", s=4, c=2, t=1):
        """Petals s x s (t thick) with a c x c centre standing t out; (x, y, z) is the petal plate's min corner."""
        P, E, C, CS = f"petal.{key}", f"petal_edge.{key}", f"centre.{key}", f"centre_side.{key}"
        o = (s - c) / 2
        if facing == "up":
            return [self.box([x, y, z], [s, t, s], E, P), self.box([x + o, y + t, z + o], [c, t, c], CS, C)]
        if facing in ("east", "west"):
            plate = self.faces([x, y, z], [t, s, s], {"east": P, "west": P, "north": (E, 90), "south": (E, 90),
                                                     "up": E, "down": E})
            cx = x + t if facing == "east" else x - t
            centre = self.faces([cx, y + o, z + o], [t, c, c], {"east": C, "west": C, "north": (CS, 90),
                                                               "south": (CS, 90), "up": CS, "down": CS})
            return [plate, centre]
        plate = self.faces([x, y, z], [s, s, t], {"north": P, "south": P, "east": (E, 90), "west": (E, 90),
                                                 "up": E, "down": E})
        cz = z - t if facing == "north" else z + t
        centre = self.faces([x + o, y + o, cz], [c, c, t], {"north": C, "south": C, "east": (CS, 90), "west": (CS, 90),
                                                           "up": CS, "down": CS})
        return [plate, centre]

    def leaf(self, region, origin, size, pivot=None, rotation=None):
        """A flat leaf: every face shows the leaf region (thin plates read as leaves from all sides)."""
        return self.faces(origin, size, {f: region for f in ALL}, pivot, rotation)

    def blade(self, blade, rim, origin, size, pivot=None, rotation=None):
        """A 3D leaf with some thickness: its two broad faces show the blade region, the thin sides the rim region."""
        thin = min(range(3), key=lambda i: size[i])
        broad = {0: ("east", "west"), 1: ("up", "down"), 2: ("north", "south")}[thin]
        return self.faces(origin, size, {f: (blade if f in broad else rim) for f in ALL}, pivot, rotation)

    def tuft(self, centre, radii, region):
        """A small round fluffy tuft: three crossing boxes (like ball) with radii (rx, ry, rz); each box is 65 % as deep
        on the other two axes, so the outline steps in at the corners."""
        out = []
        for full in range(3):
            size = [round(2 * radii[i] * (1 if i == full else 0.65), 3) for i in range(3)]
            origin = [round(c - sz / 2, 3) for c, sz in zip(centre, size)]
            out.append(self.box(origin, size, region, region))
        return out

    def ball(self, centre, r, side, top):
        """A round fluffy ball: three crossing boxes (a 2r x 2r x 2r-2 core plus two thinner bars), reads as a sphere."""
        cx, cy, cz = centre
        return [self.box([cx - r, cy - r + 0.5, cz - r + 0.5], [2 * r, 2 * r - 1, 2 * r - 1], side, top),
                self.box([cx - r + 0.5, cy - r, cz - r + 0.5], [2 * r - 1, 2 * r, 2 * r - 1], side, top),
                self.box([cx - r + 0.5, cy - r + 0.5, cz - r], [2 * r - 1, 2 * r - 1, 2 * r], side, top)]


def build(mob, variant, add_fn):
    """Copy <mob>.geo.json to <mob>_<variant>.geo.json and let add_fn(add, bones) add cubes to existing bones."""
    doc = json.loads((GEO / f"{mob}.geo.json").read_text(encoding="utf-8"))
    geo = doc["minecraft:geometry"][0]
    geo["description"]["identifier"] = f"geometry.{mob}_{variant}"
    bones = {b["name"]: b for b in geo["bones"]}

    def add(bone, cubes):
        bones[bone].setdefault("cubes", []).extend(copy.deepcopy(cubes))

    add_fn(add, bones)
    (GEO / f"{mob}_{variant}.geo.json").write_text(json.dumps(doc, indent="\t", ensure_ascii=False) + "\n",
                                                  encoding="utf-8", newline="\n")
    print("wrote", f"{mob}_{variant}.geo.json")


def check_regions(mob, regions):
    """Every region must lie in texture space that the base model does not use and the original leaves transparent."""
    import sys
    from PIL import Image
    sys.path.insert(0, str(ROOT / "tools/texture_pipeline"))
    import mob_upgrade as mu
    tex = Image.open(mu.SNAP / f"textures/entity/{mob}.png").convert("RGBA")
    used = set()
    for x0, y0, w, h, *_ in mu.faces(GEO / f"{mob}.geo.json"):
        used.update((x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h))
    cold = ("fluff", "ball", "ice", "tuft")                 # cold and tropical regions may share space (never both painted)
    px, seen, bad = tex.load(), {}, []
    for name, (x0, y0, w, h) in regions.items():
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                if not (0 <= x < tex.width and 0 <= y < tex.height) or px[x, y][3] or (x, y) in used:
                    bad.append((name, x, y))
                elif (x, y) in seen and (name.split(".")[0] in cold) == (seen[(x, y)].split(".")[0] in cold):
                    bad.append((name, x, y, "overlaps " + seen[(x, y)]))
                seen[(x, y)] = name
    if bad:
        raise SystemExit(f"{mob}: regions overlap used texture space: {bad[:8]}")
