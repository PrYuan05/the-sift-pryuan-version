"""Climate variant models for Fusefly (the flying bug that swells up and explodes; user, 2026-11-24).
References: firefly (a pale yellow glowing lantern abdomen, a coloured shield over the head) for the colours; for the
cold one a woolly moth / bumblebee (a thick fur collar round the thorax, fuzzy tufts, a fuzzy abdomen tip).

  cold      a fur collar round the top of the body (four tufts), two fuzzy tufts on the head, fluffy cuffs on both legs
            and a fuzzy round tip at the back
  tropical  a flower crown on the head, two flowers on the body (front and side) and two leaf "antennae"
Run: python -I tools/models/build_fusefly_variants.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from variant_parts import Parts, build, check_regions  # noqa: E402

REGIONS = {
    # tropical
    "petal.a": (0, 27, 4, 4), "petal_edge.a": (0, 31, 4, 1), "centre.a": (4, 27, 2, 2), "centre_side.a": (4, 29, 2, 1),
    "petal.b": (6, 27, 4, 4), "petal_edge.b": (6, 31, 4, 1), "centre.b": (4, 30, 2, 2), "centre_side.b": (15, 5, 2, 1),
    "leaf.a": (19, 0, 6, 2),
    # cold
    "fluff.collar": (23, 27, 9, 3), "fluff.collar_top": (23, 30, 9, 2),
    "fluff.cuff": (15, 6, 3, 2), "fluff.cuff_top": (15, 8, 3, 3),
    "fluff.tuft": (29, 0, 3, 3), "fluff.tuft_top": (15, 11, 3, 2), "ball.tail": (25, 0, 4, 3),
}
P = Parts(REGIONS)


def cold(add, bones):
    # body: x -3..3, y 3.5..11.5, z -3..3; head x -2..2, y 11.55..15.55
    C, T = "fluff.collar", "fluff.collar_top"
    add("body", [P.box([-3.6, 9.4, -3.6], [7.2, 2.4, 1.3], C, T), P.box([-3.6, 9.2, 2.3], [7.2, 2.6, 1.3], C, T),
                 P.box([-3.6, 9.3, -2.4], [1.3, 2.5, 4.8], C, T), P.box([2.3, 9.5, -2.4], [1.3, 2.3, 4.8], C, T)])
    add("body", P.ball((0, 5.2, 3.5), 1.4, "ball.tail", "ball.tail"))
    add("head", [P.box([-1.9, 15.5, -0.6], [1.4, 1.6, 1.4], "fluff.tuft", "fluff.tuft_top"),
                 P.box([0.5, 15.5, -0.2], [1.4, 1.9, 1.4], "fluff.tuft", "fluff.tuft_top")])
    add("left_leg", [P.box([-2.45, 0.6, -0.7], [1.4, 1.2, 1.4], "fluff.cuff", "fluff.cuff_top",
                           pivot=[-1.25, 0.5, -0.5], rotation=[0, 0, -10])])
    add("right_leg", [P.box([1.05, 0.6, -0.7], [1.4, 1.2, 1.4], "fluff.cuff", "fluff.cuff_top",
                            pivot=[1.25, 0.5, -0.5], rotation=[0, 0, 10])])


def tropical(add, bones):
    add("head", P.flower("up", -2, 15.55, -2, "a")
        + [P.leaf("leaf.a", [-0.5, 15.6, -1.5], [3.5, 0.3, 1.2], pivot=[-0.5, 15.6, -1], rotation=[0, 0, -40]),
           P.leaf("leaf.a", [-3.0, 15.6, 0.3], [3.5, 0.3, 1.2], pivot=[0.5, 15.6, 0.8], rotation=[0, 0, 40])])
    add("body", P.flower("north", -2.6, 5, -4, "b") + P.flower("east", 3, 6.5, -1.5, "a"))


if __name__ == "__main__":
    check_regions("fusefly", REGIONS)
    build("fusefly", "cold", cold)
    build("fusefly", "tropical", tropical)
