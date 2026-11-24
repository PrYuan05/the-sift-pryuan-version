"""Climate variant models for Nuzzle (user, 2026-11-24: the tropical and cold versions should differ more, e.g. add model
parts such as more fur). Writes geckolib/models/entity/nuzzle_tropical.geo.json and nuzzle_cold.geo.json from nuzzle.geo.json
with extra cubes on the existing bones, so the same animation file drives them.

  cold      a fur ruff around the face (left, right, under the chin), a round fluffy rabbit-like tail on the back and fluffy
            fur cuffs low on each leg (Highland cattle / musk ox: long hair on the cheeks, neck and lower legs in the cold)
  tropical  six 3D hibiscus flowers: two on the back, two on each side (petals + a raised centre), the fur itself is
            shorter (the texture)

Every new face has its own uv rectangle in an unused part of the 64x64 texture (REGIONS); mob_upgrade.py paints those
rectangles (the "extras" of the nuzzle entry) for the variant textures and leaves them transparent elsewhere.
Run: python -I tools/models/build_nuzzle_variants.py"""
import copy, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "src/main/resources/assets/pysift/geckolib/models/entity"

# uv rectangles (x, y, w, h) in the texture's free space (see the used-area map in the commit notes)
REGIONS = {
    "cuff_side": (0, 26, 5, 3), "cuff_top": (5, 26, 5, 5),
    "ruff_side": (0, 30, 3, 9), "ruff_face": (3, 30, 2, 9), "ruff_top": (5, 31, 2, 3),
    "chin_front": (16, 36, 10, 2), "chin_top": (16, 38, 10, 3),
    "tail_face": (26, 36, 4, 4), "tail_side": (30, 36, 3, 4), "tail_top": (33, 36, 4, 3),
    "tail_v": (26, 40, 2, 6), "tail_v_top": (28, 40, 2, 2), "tail_h": (30, 40, 6, 2), "tail_h_end": (36, 40, 2, 2),
    "petal": (0, 40, 4, 4), "petal_edge": (4, 40, 4, 1), "centre": (8, 40, 2, 2), "centre_side": (8, 42, 2, 1),
}


def uv(region, rot=0):
    x, y, w, h = REGIONS[region]
    f = {"uv": [x, y], "uv_size": [w, h]}
    if rot:
        f["uv_rotation"] = rot
    return f


def cube(origin, size, faces):
    return {"origin": origin, "size": size, "uv": faces}


def box(origin, size, side, top, front=None, inflate=0):
    c = cube(origin, size, {"north": uv(front or side), "south": uv(side), "east": uv(side), "west": uv(side),
                            "up": uv(top), "down": uv(top)})
    if inflate:
        c["inflate"] = inflate
    return c


def flower_flat(x, y, z):
    """A flower lying on the back: petals 4x1x4 with a 2x1x2 centre on top."""
    return [box([x, y, z], [4, 1, 4], "petal_edge", "petal"),
            box([x + 1, y + 1, z + 1], [2, 1, 2], "centre_side", "centre")]


def flower_side(x, y, z):
    """A flower on the right (+x) side: petals 1x4x4, centre 1x2x2 standing out."""
    return [cube([x, y, z], [1, 4, 4], {"east": uv("petal"), "west": uv("petal"), "north": uv("petal_edge", 90),
                                        "south": uv("petal_edge", 90), "up": uv("petal_edge"), "down": uv("petal_edge")}),
            cube([x + 1, y + 1, z + 1], [1, 2, 2], {"east": uv("centre"), "west": uv("centre"), "north": uv("centre_side", 90),
                                                    "south": uv("centre_side", 90), "up": uv("centre_side"),
                                                    "down": uv("centre_side")})]


def flower_west(x, y, z):
    """A flower on the left (-x) side: petals 1x4x4 with the centre standing out to -x."""
    return [cube([x, y, z], [1, 4, 4], {"east": uv("petal"), "west": uv("petal"), "north": uv("petal_edge", 90),
                                        "south": uv("petal_edge", 90), "up": uv("petal_edge"), "down": uv("petal_edge")}),
            cube([x - 1, y + 1, z + 1], [1, 2, 2], {"east": uv("centre"), "west": uv("centre"), "north": uv("centre_side", 90),
                                                    "south": uv("centre_side", 90), "up": uv("centre_side"),
                                                    "down": uv("centre_side")})]


def build(variant):
    doc = json.loads((GEO / "nuzzle.geo.json").read_text(encoding="utf-8"))
    geo = doc["minecraft:geometry"][0]
    geo["description"]["identifier"] = f"geometry.nuzzle_{variant}"
    bones = {b["name"]: b for b in geo["bones"]}
    add = lambda bone, cubes: bones[bone].setdefault("cubes", []).extend(copy.deepcopy(cubes))
    if variant == "cold":
        # ruff around the face (the head is x -4..4, y 8..16, front at z -9)
        add("body", [box([-6, 7, -9], [2, 9, 3], "ruff_side", "ruff_top", front="ruff_face"),
                     box([4, 7, -9], [2, 9, 3], "ruff_side", "ruff_top", front="ruff_face"),
                     box([-5, 5.5, -9], [10, 2, 3], "chin_front", "chin_top")])
        # a round fluffy tail like a rabbit's on the back (user: no extra layer on top, a round tail instead); three
        # crossing boxes read as a ball (the shell's back is at z 8, the body box behind it reaches z 10)
        add("body", [box([-2, 10.5, 10], [4, 4, 3], "tail_side", "tail_top", front="tail_face"),
                     cube([-1, 9.5, 10.5], [2, 6, 2], {f: uv("tail_v_top" if f in ("up", "down") else "tail_v")
                                                       for f in ("north", "south", "east", "west", "up", "down")}),
                     cube([-3, 11.5, 10.5], [6, 2, 2], {f: uv("tail_h_end" if f in ("east", "west") else "tail_h")
                                                        for f in ("north", "south", "east", "west", "up", "down")})])
        # fluffy cuffs low on the legs (legs are 4x9x4 from y 0; the green hooves are the bottom 2 px)
        for leg, (x, z) in {"front_left_leg": (-7.55, -6.5), "front_right_leg": (2.55, -6.5),
                            "back_right_leg": (2.55, 2.5), "back_left_leg": (-7.55, 2.5)}.items():
            add(leg, [box([x, 2, z], [5, 3, 5], "cuff_side", "cuff_top")])
    else:
        # every flower is a 3D part (user: no flat painted flowers mixed with 3D ones): two on the back, two on each side
        add("body", flower_flat(-6.5, 20, 0) + flower_flat(1.5, 20, 3)
            + flower_side(8, 12, -2) + flower_side(8, 6, 3)
            + flower_west(-9, 13, 1) + flower_west(-9, 7, -4))
    (GEO / f"nuzzle_{variant}.geo.json").write_text(json.dumps(doc, indent="\t", ensure_ascii=False) + "\n",
                                                   encoding="utf-8", newline="\n")
    print("wrote", f"nuzzle_{variant}.geo.json")


if __name__ == "__main__":
    build("cold")
    build("tropical")
