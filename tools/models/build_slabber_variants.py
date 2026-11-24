"""Climate variant models for Slabber (the Sift "cow": a soil slab on its back where flowers grow; user, 2026-11-24).
References: Highland cattle / musk ox (long shaggy guard hair hanging from the flanks, a forelock over the brow, hairy
lower legs) for the cold one; a rainforest floor (big glossy leaves, hibiscus) for the tropical one. The moss that hangs
over the soil is Slabber's "fur".

  cold      a shaggy moss skirt hanging from both flanks and the rump, a forelock over the brow, fluffy cuffs on the four
            legs and a round fluffy tail
  tropical  five big 3D flowers (two on each flank, one tucked on the brow) and small 3D leaves (0.6 thick) round the
            soil slab: some drooping over its edges down the flanks and the rump, two standing up at its corners; no
            large flat leaves lying on the back (user, 11-24)
The flower_1..5 bones (real flower block models drawn by SlabberRenderer) and the mushrooms bone are untouched.
Run: python -I tools/models/build_slabber_variants.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from variant_parts import Parts, build, check_regions  # noqa: E402

# 128x128 texture, 1 px per unit: everything below y 64 is free
REGIONS = {
    # cold
    "fluff.skirt": (0, 64, 24, 7), "fluff.skirt_edge": (24, 64, 3, 7), "fluff.skirt_top": (27, 64, 24, 2),
    "fluff.lock": (0, 74, 12, 6), "fluff.lock_side": (12, 74, 2, 6), "fluff.lock_top": (14, 74, 12, 2),
    "fluff.cuff": (0, 82, 7, 3), "fluff.cuff_top": (7, 82, 7, 7), "ball.tail": (14, 82, 4, 4),
    # tropical
    "petal.a": (40, 80, 6, 6), "petal_edge.a": (46, 80, 6, 1), "centre.a": (46, 82, 2, 2), "centre_side.a": (48, 82, 2, 1),
    "petal.b": (40, 88, 6, 6), "petal_edge.b": (46, 88, 6, 1), "centre.b": (46, 90, 2, 2), "centre_side.b": (48, 90, 2, 1),
    "leaf.blade": (60, 80, 4, 7), "leaf.rim": (64, 80, 1, 7),
}
P = Parts(REGIONS)
LEGS = {"front_left_leg": (-8, -8), "front_right_leg": (3, -8), "back_right_leg": (3, 6), "back_left_leg": (-8, 6)}


def cold(add, bones):
    # body is x -11..11, y 9..26, z -13..13: shaggy tufts hanging from the flanks (different lengths = ragged hem)
    for side in (-1, 1):
        x = 11 if side > 0 else -12.4
        for i, (z0, length) in enumerate(((-12.5, 7.5), (-6.5, 9), (0, 8), (6.2, 9.5))):
            add("body", [P.box([x, 15 - length, z0], [1.4, length, 6.6 if i < 3 else 6.8], "fluff.skirt",
                               "fluff.skirt_top", front="fluff.skirt_edge")])
    for (x0, length) in ((-10.5, 8), (-3.5, 9.5), (3.5, 7.5)):          # rump (back is z 13)
        add("body", [P.faces([x0, 15 - length, 13], [7, length, 1.4],
                             {"north": "fluff.skirt", "south": "fluff.skirt", "east": "fluff.skirt_edge",
                              "west": "fluff.skirt_edge", "up": "fluff.skirt_top", "down": "fluff.skirt_top"})])
    # forelock over the brow (the face is at z -15, the eyes at y 15..17)
    for (x0, w, bottom) in ((-6.5, 4.5, 21.5), (-2.4, 4.8, 19.8), (2, 4.5, 21))[::1]:
        add("head", [P.box([x0, bottom, -15.9], [w, 27.4 - bottom, 1.6], "fluff.lock_side", "fluff.lock_top",
                           front="fluff.lock")])
    add("body", P.ball((0, 19, 14.8), 2, "ball.tail", "ball.tail"))
    for leg, (x, z) in LEGS.items():                  # legs are 5x11x5 from y 0
        add(leg, [P.box([x - 0.7, 1.5, z - 0.7], [6.4, 3.2, 6.4], "fluff.cuff", "fluff.cuff_top")])


def tropical(add, bones):
    add("body", P.flower("east", 11, 15, -9, "a", s=6) + P.flower("east", 11, 12, 4, "b", s=6)
        + P.flower("west", -12, 14, -2, "b", s=6) + P.flower("west", -12, 16, 7, "a", s=6))
    add("head", P.flower("north", 1.5, 20.5, -15.6, "a", s=6))
    # small leaves drooping over the soil slab's edges (the top is y 26, flanks x +-11, rump z 13): rooted at the top
    # edge, hanging down outside the body with the tip leaning out
    for origin, size, pivot, rot in (([11.05, 20.5, -2.2], [0.6, 5.5, 3], [11.05, 26, -0.7], [0, 0, 14]),
                                     ([11.05, 21.5, 7.5], [0.6, 4.5, 2.6], [11.05, 26, 8.8], [0, 0, 10]),
                                     ([-11.65, 21, 2], [0.6, 5, 3], [-11.05, 26, 3.5], [0, 0, -12]),
                                     ([-11.65, 22, -9.5], [0.6, 4, 2.4], [-11.05, 26, -8.3], [0, 0, -9]),
                                     ([-4, 20.8, 13.05], [3, 5.2, 0.6], [-2.5, 26, 13.05], [-12, 0, 0]),
                                     ([5, 22, 13.05], [2.6, 4, 0.6], [6.3, 26, 13.05], [-9, 0, 0])):
        add("body", [P.blade("leaf.blade", "leaf.rim", origin, size, pivot, rot)])
    # two leaves standing up at the slab's corners, leaning outwards
    add("body", [P.blade("leaf.blade", "leaf.rim", [8, 26, -11.8], [2.6, 5, 0.6], [9.3, 26, -11.5], [16, 0, 14]),
                 P.blade("leaf.blade", "leaf.rim", [-10.4, 26, 10.6], [2.6, 4.4, 0.6], [-9.1, 26, 10.9], [-16, 0, -14])])


if __name__ == "__main__":
    check_regions("slabber", REGIONS)
    build("slabber", "cold", cold)
    build("slabber", "tropical", tropical)
