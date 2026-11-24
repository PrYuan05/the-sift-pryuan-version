"""Climate variant models for Wobble (the wobbly, comical jelly creature; user, 2026-11-24).
Reference: axolotl / jelly animals (translucent skin: lighter where the light passes through the top, deeper colour in
the core and the lower part) for the texture; a water garden (lotus and lily pad) for the tropical one; for the cold one
fluffy frost tufts and icicles (a jelly has no fur, so the "fur" is frosty fluff).

  cold      two fluffy tufts on the sides of the head, a round fluffy pompom on top, fluffy cuffs on both feet and three
            icicles hanging under the snout
  tropical  a small lotus on top (a petal cup round a seed head), three small 3D leaves round it (two standing up,
            one drooping over the back edge) and a flower on each side; no flat pad lying on the back (user, 11-24)
Run: python -I tools/models/build_wobble_variants.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from variant_parts import ALL, Parts, build, check_regions  # noqa: E402

REGIONS = {
    # cold
    "fluff.muff": (0, 40, 6, 8), "fluff.muff_top": (6, 40, 6, 6), "fluff.cuff": (0, 50, 10, 4),
    "fluff.cuff_top": (10, 50, 10, 10), "ball.pom": (20, 40, 8, 8), "ice.drip": (28, 40, 2, 6),
    # tropical
    "petal.a": (32, 40, 8, 8), "petal_edge.a": (32, 48, 8, 2), "centre.a": (40, 40, 4, 4), "centre_side.a": (40, 44, 4, 2),
    "petal.b": (44, 40, 6, 6), "petal_edge.b": (44, 46, 6, 1), "centre.b": (50, 40, 2, 2), "centre_side.b": (50, 42, 2, 1),
    "leaf.blade": (30, 52, 3, 6), "leaf.rim": (33, 52, 1, 6), "petal.a_cup": (34, 52, 3, 4),
}
P = Parts(REGIONS)


def cold(add, bones):
    # body: x -6..6, y 0..12, z -6..6; snout x -3..3, y 5..13, z -8..-2; feet 4x4x4 at x -10..-6 and 6..10
    add("body", [P.box([-7.6, 7.5, -2.5], [1.7, 4.5, 5], "fluff.muff", "fluff.muff_top"),
                 P.box([5.9, 7.5, -2.5], [1.7, 4.5, 5], "fluff.muff", "fluff.muff_top")])
    add("body", P.ball((0, 13.8, 0.5), 1.8, "ball.pom", "ball.pom"))
    for (x, h) in ((-2.2, 2.2), (-0.4, 3.0), (1.4, 1.8)):
        add("snout", [P.box([x, 5 - h, -7.9], [0.8, h, 0.8], "ice.drip", "ice.drip")])
    add("left_foot", [P.box([-10.55, 0.4, -2.5], [5, 1.8, 5], "fluff.cuff", "fluff.cuff_top",
                            pivot=[-10.05, 0.0, -2.0], rotation=[7.5, 0, 0])])
    add("right_foot", [P.box([5.55, 0.4, -2.5], [5, 1.8, 5], "fluff.cuff", "fluff.cuff_top",
                             pivot=[10.05, 0.0, -2.0], rotation=[7.5, 0, 0])])


def tropical(add, bones):
    # the lotus: a 4x1x4 petal plate with the seed head on the top centre (y 12), and four petals standing round it,
    # tilted outwards (a cup)
    lotus = P.flower("up", -2, 12, -1.5, "a", s=4, c=2)
    cup = [P.faces([-1.2, 12.6, -1.9], [2.4, 2.2, 0.6], {f: "petal.a_cup" for f in ALL}, [0, 12.6, -1.6], [25, 0, 0]),
           P.faces([-1.2, 12.6, 1.9], [2.4, 2.2, 0.6], {f: "petal.a_cup" for f in ALL}, [0, 12.6, 2.2], [-25, 0, 0]),
           P.faces([-2.4, 12.6, -0.7], [0.6, 2.2, 2.4], {f: "petal.a_cup" for f in ALL}, [-2.1, 12.6, 0.5], [0, 0, -25]),
           P.faces([1.8, 12.6, -0.7], [0.6, 2.2, 2.4], {f: "petal.a_cup" for f in ALL}, [2.1, 12.6, 0.5], [0, 0, 25])]
    # leaves (0.5 thick): two standing up behind the lotus, leaning out; one drooping over the back edge (z 6)
    leaves = [P.blade("leaf.blade", "leaf.rim", [2.8, 12, 1.5], [2, 4, 0.5], [3.8, 12, 1.75], [0, -20, 22]),
              P.blade("leaf.blade", "leaf.rim", [-4.6, 12, 2.5], [2, 3.4, 0.5], [-3.6, 12, 2.75], [-12, 25, -20]),
              P.blade("leaf.blade", "leaf.rim", [-0.5, 8.6, 6.0], [2.2, 3.6, 0.5], [0.6, 12.2, 6.0], [16, 0, 0])]
    add("body", lotus + cup + leaves + P.flower("east", 6, 4.5, -2, "b") + P.flower("west", -7, 5, 0.5, "b"))


if __name__ == "__main__":
    check_regions("wobble", REGIONS)
    build("wobble", "cold", cold)
    build("wobble", "tropical", tropical)
