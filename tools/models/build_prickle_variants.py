"""Climate variant models for Prickle (the spiky hedgehog-like ball; user, 2026-11-24).
Reference: hedgehog (banded spines with pale tips, soft fur only on the face and belly; desert hedgehogs are paler and
thinner-coated, northern ones have a fuller face and belly fringe).

  cold      a fur collar round the face (cheek tufts and a fringe above the brow), four small round fur tufts along each
            flank (the belly fringe) and a round fluffy tail
  tropical  four 3D flowers growing between the spines (two on the back, one on each flank) with leaves
Run: python -I tools/models/build_prickle_variants.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from variant_parts import Parts, build, check_regions  # noqa: E402

REGIONS = {
    # tropical
    "petal.a": (0, 25, 4, 4), "petal_edge.a": (0, 29, 4, 1), "centre.a": (4, 25, 2, 2), "centre_side.a": (4, 27, 2, 1),
    "petal.b": (6, 25, 4, 4), "petal_edge.b": (6, 29, 4, 1), "centre.b": (10, 25, 2, 2), "centre_side.b": (10, 27, 2, 1),
    "leaf.a": (12, 25, 5, 2),
    # cold
    "fluff.ruff": (17, 25, 4, 6), "fluff.ruff_front": (21, 25, 2, 6), "fluff.ruff_top": (23, 25, 4, 2),
    "fluff.brow": (6, 21, 8, 2), "fluff.brow_top": (14, 21, 8, 2),
    "tuft.belly": (23, 27, 8, 3), "ball.tail": (13, 28, 3, 3),
}
P = Parts(REGIONS)


def cold(add, bones):
    # body: x -3.5..3.5, y 0..7, z -5.24..5.76; the head sits low in front (z -6.74)
    for x in (-4.8, 3.5):
        add("body", [P.box([x, 0.4, -5.7], [1.3, 6.2, 3.2], "fluff.ruff", "fluff.ruff_top", front="fluff.ruff_front")])
    # the belly fringe: small round fluffy tufts along each flank (a long strip read as a wooden stick; user, 11-24),
    # different sizes and heights so the fringe is soft and uneven
    for side in (-1, 1):
        for z, ry, rz, y in ((-1.6, 0.95, 1.05, 1.0), (0.6, 1.1, 1.15, 0.9), (2.8, 0.9, 1.0, 1.1), (4.7, 0.8, 0.85, 1.3)):
            add("body", P.tuft((side * 3.85, y, z), (0.7, ry, rz), "tuft.belly"))
    add("body", [P.box([-3.9, 6.4, -5.9], [7.8, 1.7, 2.2], "fluff.brow", "fluff.brow_top")])
    add("body", P.ball((0, 2.6, 6.5), 1.4, "ball.tail", "ball.tail"))


def tropical(add, bones):
    add("body", P.flower("up", -3.2, 7, -2.5, "a") + P.flower("up", -0.2, 7, 1.5, "b")
        + P.flower("east", 3.5, 2, -1.5, "b") + P.flower("west", -4.5, 2.5, 2, "a")
        + [P.leaf("leaf.a", [0.8, 7.1, -2.8], [3.2, 0.3, 1.6], pivot=[0.8, 7.1, -2], rotation=[0, 0, -20]),
           P.leaf("leaf.a", [-4.6, 7.1, 2.5], [3.2, 0.3, 1.6], pivot=[-1.4, 7.1, 3.3], rotation=[0, 0, 20])])


if __name__ == "__main__":
    check_regions("prickle", REGIONS)
    build("prickle", "cold", cold)
    build("prickle", "tropical", tropical)
