"""Climate variant models for Lootkin (the treasure goblin of the amber dunes; user, 2026-11-24).
Reference: fennec fox (pale sandy coat, dense fur on the feet) for the dune look; arctic fox (thick neck ruff, fluffy
tail, furry feet) for the cold one.

  cold      a fur ruff around the face (both cheeks and under the chin), fluffy cuffs on all six legs and a round fluffy
            tail under the treasure sack
  tropical  four 3D desert flowers (one on the sack, one on the back, one on each side) and a bloom with two leaves on the
            crest's tip

Writes geckolib/models/entity/lootkin_tropical.geo.json and lootkin_cold.geo.json (same bones, same animations).
Run: python -I tools/models/build_lootkin_variants.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from variant_parts import Parts, build, check_regions  # noqa: E402

# 32x32 texture: only small free pockets (left column, bottom rows)
REGIONS = {
    # tropical
    "petal.a": (0, 10, 4, 4), "petal_edge.a": (0, 14, 4, 1), "centre.a": (4, 15, 2, 2), "centre_side.a": (0, 20, 2, 1),
    "petal.b": (0, 15, 4, 4), "petal_edge.b": (0, 19, 4, 1), "centre.b": (4, 17, 2, 2), "centre_side.b": (2, 20, 2, 1),
    "leaf.a": (9, 26, 4, 2),
    # cold
    "fluff.ruff": (13, 27, 3, 5), "fluff.ruff_front": (16, 27, 1, 5), "fluff.ruff_top": (17, 27, 1, 3),
    "fluff.chin": (19, 27, 9, 2), "fluff.chin_top": (19, 29, 9, 2),
    "fluff.cuff": (28, 27, 3, 2), "fluff.cuff_top": (28, 29, 3, 2), "ball.tail": (29, 21, 3, 3),
}
P = Parts(REGIONS)
LEGS = {"left_front_leg": (-3, -3), "right_front_leg": (1, -3), "left_middle_leg": (-3, 0),
        "right_middle_leg": (1, 0), "left_back_leg": (-3, 3), "right_back_leg": (1, 3)}


def cold(add, bones):
    # cheek ruff (the body is x -4.5..4.5, y 3..10, its face at z -7): staggered tufts so the outline is ragged, and
    # three hanging chin tufts of different lengths
    for sx, x in ((-1, -4.5), (1, 4.5)):
        for (y0, h, d, out) in ((2.8, 2.6, 3.4, 1.4), (5.0, 2.8, 2.8, 1.8), (7.4, 2.4, 2.2, 1.1)):
            add("body", [P.box([x if sx > 0 else x - out, y0, -7.6], [out, h, d], "fluff.ruff", "fluff.ruff_top",
                               front="fluff.ruff_front")])
    for (x0, w, h) in ((-4.6, 3.2, 1.4), (-1.7, 3.4, 2.1), (1.4, 3.2, 1.5)):
        add("body", [P.box([x0, 3.9 - h, -7.7], [w, h, 2.2], "fluff.chin", "fluff.chin_top")])
    # round fluffy tail under the sack's back (the sack reaches z 7)
    add("sack", P.ball((0, 4.2, 7.6), 1.5, "ball.tail", "ball.tail"))
    for leg, (x, z) in LEGS.items():                      # legs are 2x4x2 from y 0
        add(leg, [P.box([x - 0.5, 0.6, z - 0.5], [3, 1.6, 3], "fluff.cuff", "fluff.cuff_top")])


def tropical(add, bones):
    add("sack", P.flower("up", -3, 8, 2, "a"))              # sack top is y 8
    add("body", P.flower("up", 0.5, 10, -3.5, "b")          # back (body top y 10, the crest sits at the front)
        + P.flower("east", 4.5, 4.5, -5, "b") + P.flower("west", -5.5, 4.5, -2, "a"))
    # the crest blooms: a flower facing forward on its stem top with two leaves (crest plane z -7, y 10..22)
    add("crest", P.flower("north", -2, 18.5, -7.6, "a")
        + [P.leaf("leaf.a", [1.5, 15, -7.3], [3, 1.5, 0.3]), P.leaf("leaf.a", [-4.5, 14, -7.3], [3, 1.5, 0.3])])


if __name__ == "__main__":
    check_regions("lootkin", REGIONS)
    build("lootkin", "cold", cold)
    build("lootkin", "tropical", tropical)
