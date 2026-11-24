"""Climate variant models for the five mobs that shared one Dungeons 2 sheet (nester, pollinator, seedling, sprout,
sentinel; user 2026-11-24). Writes geckolib/models/entity/<mob>_tropical.geo.json and <mob>_cold.geo.json from
<mob>.geo.json with extra cubes on existing bones (same animation file drives them).

  cold      3D fur: a ruff / collar, fluffy cuffs low on the legs, a round tail (three crossing boxes) - never a layer on
            the back
  tropical  3D flowers (petal plate + raised centre, variant_parts.Parts.flower geometry) on the head / back and sides

Every new face gets its own uv rectangle, allocated automatically in texture space the base model does not use
(REGIONS[mob][name] = (x, y, w, h); name = "<role>.<key>", roles fluff / ball / petal / petal_edge / centre /
centre_side). tools/texture_pipeline/paint_placeholder_mobs.py paints them.

fix_base_uvs() also repairs two broken mouth faces in the base models (idempotent): the nester's mouth roof / floor
and the pollinator's mouth floor / roof shared rectangles with visible faces; they now use the unused mouth squares of
the original sheet.
Run: python -I tools/models/build_placeholder_variants.py"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "src/main/resources/assets/pysift/geckolib/models/entity"
MOBS = ("nester", "pollinator", "seedling", "sprout", "sentinel")
DENSITY = {"nester": 2, "pollinator": 1, "seedling": 1, "sprout": 2, "sentinel": 2}   # texture px per model unit
ALL = ("north", "south", "east", "west", "up", "down")

# mouth faces -> the original sheet's unused mouth squares (x, y, w, h)
MOUTH_FIX = {
    "nester": [("head", 0, "down", (10, 94, 13, 15)), ("jaw", 0, "up", (25, 94, 13, 15))],
    "pollinator": [("head", 0, "down", (76, 105, 13, 11)), ("body", 0, "up", (76, 116, 13, 11))],
}


def load(mob, suffix=""):
    return json.loads((GEO / f"{mob}{suffix}.geo.json").read_text(encoding="utf-8"))


def save(doc, name):
    (GEO / f"{name}.geo.json").write_text(json.dumps(doc, indent="\t", ensure_ascii=False) + "\n",
                                          encoding="utf-8", newline="\n")


def fix_base_uvs():
    """Line-level edit, so the Blockbench layout of the base files stays as it is."""
    import re
    for mob, fixes in MOUTH_FIX.items():
        path = GEO / f"{mob}.geo.json"
        text = path.read_text(encoding="utf-8")
        nl = "\r\n" if "\r\n" in text else "\n"
        lines = text.split(nl)
        bone, ci, changed = None, -1, False
        for i, line in enumerate(lines):
            m = re.match(r'\s*"name": "([^"]+)"', line)
            if m:
                bone, ci = m.group(1), -1
            if re.match(r'\s*"origin":', line):
                ci += 1
            m = re.match(r'(\s*)"(north|south|east|west|up|down)": \{"uv".*?\}(,?)$', line)
            if not m:
                continue
            for fb, fci, face, (x, y, w, h) in fixes:
                if (bone, ci, m.group(2)) == (fb, fci, face):
                    new = f'{m.group(1)}"{face}": {{"uv": [{x}, {y}], "uv_size": [{w}, {h}]}}{m.group(3)}'
                    if new != line:
                        lines[i], changed = new, True
        if changed:
            path.write_text(nl.join(lines), encoding="utf-8", newline="")
            print("fixed mouth uvs in", path.name)


def used_pixels(mob):
    g = load(mob)["minecraft:geometry"][0]
    used = set()
    for b in g["bones"]:
        for c in b.get("cubes", []):
            for f in c["uv"].values():
                (u, v), (w, h) = f["uv"], f["uv_size"]
                for x in range(int(min(u, u + w)), int(max(u, u + w))):
                    for y in range(int(min(v, v + h)), int(max(v, v + h))):
                        used.add((x, y))
    return used


class Alloc:
    """Hands out uv rectangles in free texture space (1 px gap around used areas)."""

    def __init__(self, mob, size=128):
        self.mob, self.size = mob, size
        self.taken = used_pixels(mob)
        self.regions = {}

    def get(self, name, w, h):
        if name in self.regions:
            assert self.regions[name][2:] == (w, h), (name, w, h)
            return self.regions[name]
        for y in range(0, self.size - h + 1):
            for x in range(0, self.size - w + 1):
                if all((xx, yy) not in self.taken for xx in range(x - 1, x + w + 1) for yy in range(y - 1, y + h + 1)):
                    for xx in range(x, x + w):
                        for yy in range(y, y + h):
                            self.taken.add((xx, yy))
                    self.regions[name] = (x, y, w, h)
                    return self.regions[name]
        raise SystemExit(f"{self.mob}: no room for {name} {w}x{h}")


class Builder:
    def __init__(self, mob, alloc):
        self.mob, self.A, self.d = mob, alloc, DENSITY[mob]
        self.bones = {bb["name"]: bb for bb in load(mob)["minecraft:geometry"][0]["bones"]}

    def cuffs(self, y_off, h, pad, legs=("front_left_leg", "front_right_leg", "back_left_leg", "back_right_leg")):
        """Fluffy cuffs low on each leg: a box pad wider than the leg's first cube, following its rotation."""
        out = {}
        for leg in legs:
            c = self.bones[leg]["cubes"][0]
            (ox, oy, oz), (sx, sy, sz) = c["origin"], c["size"]
            out[leg] = [self.box([ox - pad, oy + y_off, oz - pad], [sx + 2 * pad, h, sz + 2 * pad], "fluff", "cuff",
                                 pivot=c.get("pivot"), rotation=c.get("rotation"))]
        return out

    def px(self, units):
        v = units * self.d
        assert abs(v - round(v)) < 1e-6, (self.mob, units)
        return max(1, int(round(v)))

    def uv(self, name, w, h, rot=0):
        x, y, w, h = self.A.get(name, w, h)
        f = {"uv": [x, y], "uv_size": [w, h]}
        if rot:
            f["uv_rotation"] = rot
        return f

    def box(self, origin, size, role, key, front=None, pivot=None, rotation=None):
        """A box whose faces use <role>.<key>_side / _top / _front regions sized to the faces."""
        sx, sy, sz = (self.px(s) for s in size)
        side_ns = self.uv(f"{role}.{key}_ns", sx, sy)
        side_ew = self.uv(f"{role}.{key}_ew", sz, sy)
        top = self.uv(f"{role}.{key}_top", sx, sz)
        c = {"origin": list(origin), "size": list(size),
             "uv": {"north": self.uv(f"{role}.{front}", sx, sy) if front else side_ns, "south": side_ns,
                    "east": side_ew, "west": side_ew, "up": top, "down": top}}
        if rotation:
            c["pivot"], c["rotation"] = list(pivot), list(rotation)
        return c

    def ball(self, centre, r, key):
        """Round fluffy ball: three crossing boxes (variant_parts.Parts.ball geometry)."""
        cx, cy, cz = centre
        return [self.box([cx - r, cy - r + 0.5, cz - r + 0.5], [2 * r, 2 * r - 1, 2 * r - 1], "ball", key + "a"),
                self.box([cx - r + 0.5, cy - r, cz - r + 0.5], [2 * r - 1, 2 * r, 2 * r - 1], "ball", key + "b"),
                self.box([cx - r + 0.5, cy - r + 0.5, cz - r], [2 * r - 1, 2 * r - 1, 2 * r], "ball", key + "c")]

    def ring(self, x0, x1, z0, z1, y, h, t, key):
        """A collar of four boxes around a rectangle (x0..x1, z0..z1), thickness t, from y to y + h."""
        return [self.box([x0 - t, y, z0 - t], [x1 - x0 + 2 * t, h, t], "fluff", key + "_fb"),
                self.box([x0 - t, y, z1], [x1 - x0 + 2 * t, h, t], "fluff", key + "_fb"),
                self.box([x0 - t, y, z0], [t, h, z1 - z0], "fluff", key + "_lr"),
                self.box([x1, y, z0], [t, h, z1 - z0], "fluff", key + "_lr")]

    def flower(self, facing, x, y, z, key="a", s=2, c=1):
        """variant_parts.Parts.flower geometry with allocated regions (petals s x s, a c x c centre standing 1 out)."""
        S, C, T = self.px(s), self.px(c), self.px(1) if self.d == 1 else self.px(0.5)
        t = T / self.d                                       # plate / centre thickness in units
        P = lambda: self.uv(f"petal.{key}_{S}", S, S)
        E = lambda rot=0: self.uv(f"petal_edge.{key}_{S}", S, T, rot)
        Cn = lambda: self.uv(f"centre.{key}_{C}", C, C)
        CS = lambda rot=0: self.uv(f"centre_side.{key}_{C}", C, T, rot)
        o = (s - c) / 2
        if facing == "up":
            return [{"origin": [x, y, z], "size": [s, t, s], "uv": {"north": E(), "south": E(), "east": E(),
                                                                   "west": E(), "up": P(), "down": P()}},
                    {"origin": [x + o, y + t, z + o], "size": [c, t, c],
                     "uv": {"north": CS(), "south": CS(), "east": CS(), "west": CS(), "up": Cn(), "down": Cn()}}]
        if facing in ("east", "west"):
            plate = {"origin": [x, y, z], "size": [t, s, s],
                     "uv": {"east": P(), "west": P(), "north": E(90), "south": E(90), "up": E(90), "down": E(90)}}
            cx = x + t if facing == "east" else x - t
            centre = {"origin": [cx, y + o, z + o], "size": [t, c, c],
                      "uv": {"east": Cn(), "west": Cn(), "north": CS(90), "south": CS(90), "up": CS(90),
                             "down": CS(90)}}
            return [plate, centre]
        plate = {"origin": [x, y, z], "size": [s, s, t],
                 "uv": {"north": P(), "south": P(), "east": E(90), "west": E(90), "up": E(), "down": E()}}
        cz = z - t if facing == "north" else z + t
        centre = {"origin": [x + o, y + o, cz], "size": [c, c, t],
                  "uv": {"north": Cn(), "south": Cn(), "east": CS(90), "west": CS(90), "up": CS(), "down": CS()}}
        return [plate, centre]


# ------------------------------------------------------------------------------------------------- per-mob parts
def parts_nester(b, v):
    if v == "cold":
        return {"body": b.ring(-2, 2, -2, 2, 10, 2, 1, "ruff")           # collar under the head
                + b.ball((0, 9.5, 3), 1.5, "tail"),
                **b.cuffs(1, 1.5, 0.25)}
    return {"head": b.flower("up", -3, 17.25, -2.5, "a", 2, 1) + b.flower("up", 0.5, 17.25, -1, "b", 2, 1),
            "body": b.flower("east", 2, 8.5, -1, "a", 2, 1) + b.flower("west", -2.5, 9, -0.5, "b", 2, 1)}


def parts_pollinator(b, v):
    if v == "cold":
        return {"body": b.ring(-6, 6, -6, 6, 15, 3, 1, "ruff") + b.ball((0, 9, 7), 2, "tail"),
                **b.cuffs(0.5, 2, 0.5)}
    return {"head": b.flower("up", -5, 23.05, -4, "a", 4, 2) + b.flower("up", 2, 23.05, 1, "b", 3, 1),
            "body": b.flower("east", 6, 9, -3, "a", 4, 2) + b.flower("west", -7, 11, 1, "b", 3, 1)
            + b.flower("north", -3, 6, -7, "b", 3, 1)}


def parts_seedling(b, v):
    if v == "cold":
        return {"body": [b.box([-6, 4, -4], [1, 3, 8], "fluff", "tuft"), b.box([5, 4, -4], [1, 3, 8], "fluff", "tuft")]
                + b.ball((0, 6, 6), 1.5, "tail"),
                **b.cuffs(0.5, 2, 0.5)}
    return {"upper_jaw": b.flower("up", -4, 12, -4, "a", 3, 1) + b.flower("up", 0, 12, -1, "b", 2, 2)
            + b.flower("east", 5, 8.5, -3, "a", 3, 1) + b.flower("west", -6, 8.5, -1, "b", 2, 2)}


def parts_sprout(b, v):
    if v == "cold":
        out = {"head": b.ring(-4, 4, -4, 4, 15.45, 1.5, 0.5, "ruff") + b.ball((0, 20, 4.75), 1.5, "tail")}
        piv = {"front_left_leg_seg1": [-3.27, 12, -2.27], "front_right_leg_seg1": [3.27, 12, -2.27],
               "back_left_leg_seg1": [-3.77, 12.3, 2.27], "back_right_leg_seg1": [3.27, 12, 2.27],
               "middle_leg_seg1": [-0.7892, 12, -1.1909]}
        for bone, (x, y, z) in piv.items():     # fluffy knees at the first joint of each leg
            out[bone] = [b.box([x - 1, y - 1, z - 1], [2, 2, 2], "fluff", "knee")]
        return out
    return {"head": b.flower("up", -3.5, 24.45, -3, "a", 3, 1) + b.flower("up", 0.5, 24.45, 0.5, "b", 2, 1)
            + b.flower("east", 4, 19, -1.5, "a", 3, 1) + b.flower("west", -4.5, 20, -1, "b", 2, 1)
            + b.flower("south", -1.5, 18.5, 4, "a", 3, 1)}


def parts_sentinel(b, v):
    if v == "cold":
        return {"body": b.ring(-2, 2, -2, 2, 8.5, 2, 0.5, "ruff") + b.ball((0, 8, 2.75), 1, "tail"),
                **b.cuffs(1, 1.5, 0.5)}
    return {"head": b.flower("up", -3.5, 14, -3, "a", 3, 1) + b.flower("up", 0.5, 14, 0, "b", 2, 1),
            "body": b.flower("east", 2, 7.5, -1, "a", 2, 1) + b.flower("west", -2.5, 7.5, -1, "b", 2, 1)}


PARTS = {"nester": parts_nester, "pollinator": parts_pollinator, "seedling": parts_seedling, "sprout": parts_sprout,
         "sentinel": parts_sentinel}


def regions(mob):
    """{variant: {name: (x, y, w, h)}}; tropical and cold allocate independently (they never share a texture)."""
    out = {}
    for v in ("tropical", "cold"):
        A = Alloc(mob)
        PARTS[mob](Builder(mob, A), v)
        out[v] = A.regions
    return out


def build(mob, v):
    doc = load(mob)
    geo = doc["minecraft:geometry"][0]
    geo["description"]["identifier"] = f"geometry.{mob}_{v}"
    bones = {bb["name"]: bb for bb in geo["bones"]}
    A = Alloc(mob)
    for bone, cubes in PARTS[mob](Builder(mob, A), v).items():
        bones[bone].setdefault("cubes", []).extend(copy.deepcopy(cubes))
    save(doc, f"{mob}_{v}")
    print("wrote", f"{mob}_{v}.geo.json", f"({len(A.regions)} regions)")


if __name__ == "__main__":
    fix_base_uvs()
    for m in MOBS:
        for v in ("tropical", "cold"):
            build(m, v)
