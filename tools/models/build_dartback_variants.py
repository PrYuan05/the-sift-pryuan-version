"""Climate variant models for Dartback (the armoured beast that shoots its back spikes; user, 2026-11-24).
References: armadillo / pangolin (overlapping keratin scutes in bands, soft hair growing out between the plates and on
the belly; the hairy armadillo of cold Patagonia has long hair from under its shell).

  cold      a long hair fringe hanging from under the armour along both flanks (body and head), a fur ruff round the
            neck between head and body, fluffy cuffs on the six legs and a fluffy pompom on the tail tip
  tropical  five 3D flowers growing from the armour between the spikes (back, head, both flanks) and leaves
The texture is 128 px for a small model (about 4 px per unit), so the regions are about 4 px per unit too.
Run: python -I tools/models/build_dartback_variants.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from variant_parts import Parts, build, check_regions  # noqa: E402

REGIONS = {
    # cold (free block x 17..50, y 52..67; pompom bottom right)
    "fluff.fringe": (17, 52, 28, 5), "fluff.fringe_edge": (45, 52, 4, 5), "fluff.fringe_top": (17, 57, 28, 3),
    "fluff.cuff": (17, 60, 10, 4), "fluff.cuff_top": (27, 60, 10, 7),
    "fluff.ruff": (37, 60, 10, 7), "fluff.ruff_top": (47, 57, 4, 8), "ball.tail": (114, 114, 8, 8),
    # tropical (free column x 9..21, y 84..110)
    "petal.a": (9, 84, 8, 8), "petal_edge.a": (9, 92, 8, 2), "centre.a": (17, 84, 3, 3), "centre_side.a": (17, 87, 3, 1),
    "petal.b": (9, 94, 8, 8), "petal_edge.b": (9, 102, 8, 2), "centre.b": (17, 94, 3, 3), "centre_side.b": (17, 97, 3, 1),
    "leaf.a": (9, 105, 12, 5),
}
P = Parts(REGIONS)
LEGS = {"left_front_leg": (-3, -5.25), "right_front_leg": (1, -5.25), "left_middle_leg": (-2.75, -1.75),
        "right_middle_leg": (0.75, -1.75), "left_back_leg": (-2.75, 1.75), "right_back_leg": (0.75, 1.75)}


def fringe(x0, y0, z0, w, h, d):
    return P.box([x0, y0, z0], [w, h, d], "fluff.fringe", "fluff.fringe_top", front="fluff.fringe_edge")


def cold(add, bones):
    # body: x -3.25..3.25, y 2..8, z -2.75..4.25; head: x -3.5..3.5, y 1.95..8.5, z -11.3..-2.8
    for side in (-1, 1):
        add("body", [fringe(3.2 if side > 0 else -3.75, 1.2, -2.6, 0.55, 1.7, 6.7)])
        add("head", [fringe(3.45 if side > 0 else -4.0, 1.15, -10.9, 0.55, 1.6, 8)])
        # neck ruff: thick tufts at the sides of the neck, between the head armour and the body
        add("body", [P.box([3.0 if side > 0 else -4.3, 1.6, -3.8], [1.3, 3.6, 2.0], "fluff.ruff", "fluff.ruff_top")])
    for leg, (x, z) in LEGS.items():                    # legs are 2 x 2.25 x 2.25 from y 0
        add(leg, [P.box([x - 0.3, 0.25, z - 0.3], [2.6, 0.9, 2.85], "fluff.cuff", "fluff.cuff_top")])
    add("tail_tip", P.ball((0, 3.4, 9.6), 1.1, "ball.tail", "ball.tail"))


def tropical(add, bones):
    add("body", P.flower("up", -3.1, 8, -1.2, "a", s=3, c=1.2, t=0.45)
        + P.flower("up", 0.2, 8, 1.4, "b", s=3, c=1.2, t=0.45)
        + P.flower("east", 3.25, 3.6, -0.2, "b", s=3, c=1.2, t=0.45)
        + P.flower("west", -3.7, 4.0, -2.2, "a", s=3, c=1.2, t=0.45)
        + [P.leaf("leaf.a", [-1.0, 8.05, 1.5], [2.6, 0.15, 1.0], pivot=[-1.0, 8.05, 2], rotation=[0, 30, 0]),
           P.leaf("leaf.a", [1.6, 8.05, -1.0], [2.4, 0.15, 0.9], pivot=[1.6, 8.05, -0.5], rotation=[0, -35, 0])])
    add("head", P.flower("up", -1.5, 8.5, -9.3, "a", s=3, c=1.2, t=0.45)
        + [P.leaf("leaf.a", [0.6, 8.55, -8.4], [2.4, 0.15, 0.9], pivot=[0.6, 8.55, -8], rotation=[0, 20, 0])])


if __name__ == "__main__":
    check_regions("dartback", REGIONS)
    build("dartback", "cold", cold)
    build("dartback", "tropical", tropical)
