"""Sync The Sift biome temperatures & natural_mob_spawns directly into data/pysift/worldgen/biome/*.json
matching tools/worldgen/build_the_sift.py, and verify 12/12 climate-variant mobs cover NORMAL + TROPICAL + COLD.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BDIR = ROOT / "src/main/resources/data/pysift/worldgen/biome"

SPEC = {
    "crimson_strata_canyon": (2.0, {
        "monster": [("dartback", 45, 1, 3), ("fusefly", 35, 1, 2), ("prickle", 28, 1, 2), ("nester", 8, 1, 1),
                    ("seedling", 15, 2, 4), ("sprout", 15, 2, 3), ("hurler", 10, 1, 1)],
        "creature": [("blub", 20, 2, 3), ("nuzzle", 8, 1, 2), ("pollinator", 12, 1, 2)],
    }),
    "violet_slate_abyss": (0.3, {
        "monster": [("sentinel", 20, 1, 1), ("stalker", 30, 1, 2), ("tuner", 15, 1, 1), ("hunter", 10, 1, 1),
                    ("dartback", 12, 1, 2), ("fusefly", 14, 1, 2), ("wobble", 14, 1, 2)],
        "creature": [("echo_golem", 10, 1, 1), ("blub", 15, 2, 3), ("nuzzle", 8, 1, 2), ("lootkin", 6, 1, 1)],
    }),
    "willow_grove": (0.9, {
        "creature": [("blub", 40, 2, 4), ("nuzzle", 20, 1, 2), ("pollinator", 20, 1, 2),
                     ("slabber", 25, 2, 3), ("lootkin", 5, 1, 1)],
        "monster": [("roamroot", 8, 1, 1), ("bloombud", 20, 1, 2), ("wobble", 12, 1, 2)],
    }),
    "red_zone_caves": (1.2, {
        "monster": [("stalker", 30, 1, 2), ("prickle", 20, 1, 2), ("fusefly", 15, 1, 1), ("tuner", 10, 1, 1),
                    ("dartback", 12, 1, 2), ("nester", 5, 1, 1), ("seedling", 10, 2, 3), ("sprout", 10, 1, 2)],
        "creature": [("blub", 10, 1, 2), ("echo_golem", 6, 1, 1)],
    }),
    "withered_hollows": (0.6, {
        "monster": [("stalker", 25, 1, 2), ("hunter", 15, 1, 1), ("prickle", 18, 1, 2), ("dartback", 18, 1, 2),
                    ("fusefly", 18, 1, 2), ("wobble", 12, 1, 2), ("nester", 6, 1, 1),
                    ("seedling", 12, 2, 3), ("sprout", 12, 1, 2)],
        "creature": [("mourner", 5, 1, 1), ("blub", 8, 1, 2), ("nuzzle", 10, 1, 2),
                     ("slabber", 12, 1, 2), ("pollinator", 10, 1, 2), ("lootkin", 5, 1, 1)],
    }),
    "resonant_vaults": (1.0, {
        "monster": [("sentinel", 20, 1, 1), ("tuner", 20, 1, 1), ("hunter", 12, 1, 1), ("stalker", 12, 1, 2)],
        "creature": [("echo_golem", 20, 1, 2), ("blub", 5, 1, 2)],
    }),
    "spirit_deeps": (1.6, {
        "monster": [("fusefly", 20, 1, 2), ("wobble", 20, 1, 2), ("trapper", 10, 1, 1), ("sentinel", 12, 1, 1)],
        "creature": [("blub", 25, 2, 3), ("lootkin", 5, 1, 1), ("slabber", 10, 1, 2), ("pollinator", 10, 1, 2)],
    }),
    "lullaby_hills": (1.1, {
        "monster": [("dartback", 28, 1, 2), ("prickle", 22, 1, 2), ("nester", 6, 1, 1), ("seedling", 14, 2, 3),
                    ("sprout", 14, 2, 3), ("fusefly", 18, 1, 2), ("wobble", 12, 1, 2), ("bloombud", 8, 1, 1)],
        "creature": [("echo_golem", 14, 1, 2), ("blub", 20, 2, 3), ("nuzzle", 12, 1, 2),
                     ("slabber", 10, 1, 2), ("pollinator", 18, 1, 2), ("lootkin", 6, 1, 1)],
    }),
    "soul_caldera": (2.0, {
        "monster": [("stalker", 30, 1, 2), ("fusefly", 25, 1, 2), ("prickle", 10, 1, 1), ("dartback", 15, 1, 2)],
        "creature": [("echo_golem", 6, 1, 1), ("blub", 10, 1, 2)],
    }),
    "amber_dunes": (2.0, {
        "monster": [("scavenger", 30, 1, 2), ("hurler", 20, 1, 1), ("wobble", 25, 1, 2), ("trapper", 10, 1, 1)],
        "creature": [("lootkin", 8, 1, 1), ("blub", 25, 2, 4), ("nuzzle", 8, 1, 2), ("slabber", 6, 1, 2)],
    }),
}


def fmt_list(lst):
    return [
        {"type": f"pysift:{m}", "count": {"type": "minecraft:uniform", "max_inclusive": hi, "min_inclusive": lo}, "weight": w}
        for m, w, lo, hi in lst
    ]


cov = {}
for name, (temp, cats) in SPEC.items():
    p = BDIR / f"{name}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["temperature"] = temp
    d["attributes"]["minecraft:gameplay/natural_mob_spawns"]["argument"]["spawns_by_category"] = {
        k: fmt_list(v) for k, v in cats.items()
    }
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    clim = "TROPICAL" if temp >= 1.4 else ("COLD" if temp <= 0.7 else "NORMAL")
    for lst in cats.values():
        for m, w, lo, hi in lst:
            cov.setdefault(m, set()).add(clim)

CLIMATE_MOBS = ["nuzzle", "lootkin", "slabber", "prickle", "dartback", "fusefly",
                "wobble", "nester", "pollinator", "seedling", "sprout", "sentinel"]
all_ok = True
for m in CLIMATE_MOBS:
    c = sorted(cov.get(m, set()))
    ok = len(c) == 3
    all_ok &= ok
    tag = "OK" if ok else "MISS"
    print(f"[{tag}] {m:12s} -> {c}")
print("ALL 12 CLIMATE MOBS COVER ALL 3 CLIMATES:", all_ok)
