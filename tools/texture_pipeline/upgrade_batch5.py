"""Batch 5 Mob Upgrade (9 mobs: hunter, hurler, scavenger, stalker, trapper, tuner, roamroot, bloombud, echo_golem).

Usage: python -I tools/texture_pipeline/upgrade_batch5.py
Uses Clean Low-Noise 3D Vanilla Gradient Engine (mob_painter_v2.py).
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/pysift"
GEO = RES / "geckolib/models/entity"
SNAP = ROOT / ".texture_backups/20261124_mob_originals/files"

sys.path.insert(0, str(ROOT / "tools/texture_pipeline"))
import mob_painter_v2 as mp  # noqa: E402


def _save(img, rel):
    p = RES / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p)
    print("wrote", rel, img.size)


def _auto_bucket_rules(kind_map, keep_fn=None, dark_mul=0.56, light_mul=1.28, spread=0.90, bal=0.82, orig_w=0.35):
    """Build clean per-hue-family rules so every hue bucket stays within <=5% palette error while getting lush 3D volume."""
    rules = []
    if keep_fn:
        rules.append({"name": "keep", "match": keep_fn, "kind": "keep"})
    # Neutral bucket (s < 0.12 or v < 0.10)
    rules.append({
        "name": "neutral",
        "match": lambda r, g, b, h, s, v, info: s < 0.12 or v < 0.10,
        "kind": kind_map.get("neutral", "stone"),
        "dark_mul": dark_mul, "light_mul": light_mul, "cool_deg": 8, "warm_deg": 8,
        "steps": 7, "spread": spread, "balance_mean": bal,
        "params": {"macro_y": 0.85, "cube_y": 0.52, "orig_weight": orig_w},
    })
    # 12 clean 30-degree hue families matching mob_texture_record.hue_family() exactly!
    for fam in range(12):
        lo = (fam * 30 - 15) % 360
        hi = (fam * 30 + 15) % 360
        k = kind_map.get(fam, kind_map.get("default", "skin"))
        b_fam = kind_map.get(f"bal_{fam}", bal)
        rules.append({
            "name": f"fam_{fam}",
            "match": (lambda lo=lo, hi=hi: lambda r, g, b, h, s, v, info: mp.hue_in(h, lo, hi))(),
            "kind": k,
            "dark_mul": dark_mul, "light_mul": light_mul, "cool_deg": 8, "warm_deg": 8,
            "steps": 7, "spread": spread, "balance_mean": b_fam,
            "params": {"macro_y": 0.85, "cube_y": 0.52, "orig_weight": orig_w, "bark": (k == "bark")},
        })
    return rules


def upgrade_batch5():
    specs = [
        ("hunter", _auto_bucket_rules(
            {6: "shell", 7: "shell", 0: "skin", 1: "skin", "default": "shell"},
            keep_fn=lambda r, g, b, h, s, v, info: (v >= 0.90 and s >= 0.60) or (s < 0.08 and v >= 0.85),
            spread=0.94, bal=0.86, orig_w=0.30,
        ), 2001, 7),
        ("hurler", _auto_bucket_rules(
            {8: "stone", "neutral": "bone", 0: "skin", 11: "skin", "bal_8": 0.62, "bal_neutral": 0.58, "default": "stone"},
            keep_fn=lambda r, g, b, h, s, v, info: (mp.hue_in(h, 135, 185) and s >= 0.55 and v >= 0.72) or v < 0.22,
            spread=0.94, bal=0.68, orig_w=0.28,
        ), 2002, 7),
        ("scavenger", _auto_bucket_rules(
            {7: "cloth", 8: "cloth", "neutral": "bone", 1: "skin", 2: "skin", "default": "cloth"},
            keep_fn=lambda r, g, b, h, s, v, info: (mp.hue_in(h, 155, 200) and s >= 0.45 and v >= 0.72) or v < 0.14,
            spread=0.92, bal=0.82, orig_w=0.32,
        ), 2003, 7),
        ("stalker", _auto_bucket_rules(
            {6: "skin", 7: "skin", "neutral": "bone", "default": "skin"},
            keep_fn=lambda r, g, b, h, s, v, info: (mp.hue_in(h, 165, 210) and s >= 0.65 and v >= 0.72) or v < 0.12,
            spread=0.94, bal=0.85, orig_w=0.30,
        ), 2004, 7),
        ("trapper", _auto_bucket_rules(
            {8: "shell", 9: "shell", 7: "shell", 11: "plant", "default": "shell"},
            keep_fn=lambda r, g, b, h, s, v, info: (mp.hue_in(h, 155, 200) and s >= 0.40 and v >= 0.78) or (s < 0.08 and v >= 0.85),
            spread=0.94, bal=0.82, orig_w=0.30,
        ), 2005, 7),
        ("tuner", _auto_bucket_rules(
            {3: "stone", 4: "plant", "default": "stone"},
            keep_fn=lambda r, g, b, h, s, v, info: (mp.hue_in(h, 195, 255) and s >= 0.55 and v >= 0.75) or (mp.hue_in(h, 335, 15) and v >= 0.75) or v < 0.48,
            spread=0.94, bal=0.84, orig_w=0.35,
        ), 2006, 7),
        ("roamroot", _auto_bucket_rules(
            {4: "plant", 5: "plant", 6: "plant", 7: "stone", "neutral": "bone", "default": "plant"},
            keep_fn=lambda r, g, b, h, s, v, info: v < 0.18,
            spread=0.94, bal=0.80, orig_w=0.32,
        ), 2007, 7),
        ("bloombud", _auto_bucket_rules(
            {8: "stone", "neutral": "stone", 4: "plant", 6: "plant", 1: "skin", "default": "stone"},
            keep_fn=lambda r, g, b, h, s, v, info: (mp.hue_in(h, 35, 70) and s >= 0.65 and v >= 0.80) or v < 0.16,
            spread=0.94, bal=0.84, orig_w=0.30,
        ), 2008, 7),
        # Echo Golem: protect glowing lantern/soul crystal (v >= 0.68) AND preserve ALL carved ancient spiral runes (orig_w=0.90!)
        ("echo_golem", _auto_bucket_rules(
            {6: "stone", 7: "stone", "neutral": "stone", "default": "stone"},
            keep_fn=lambda r, g, b, h, s, v, info: (mp.hue_in(h, 145, 205) and v >= 0.68) or (v < 0.04),
            dark_mul=0.50, light_mul=1.36, spread=0.96, bal=0.86, orig_w=0.92,
        ), 2009, 5),
    ]

    rows_a, rows_b = [], []
    for idx, (mob, rules, seed, sc) in enumerate(specs):
        orig_img = Image.open(SNAP / f"textures/entity/{mob}.png").convert("RGBA")
        up_img, _, _ = mp.upgrade_mob_texture(orig_img, [GEO / f"{mob}.geo.json"], rules, seed=seed)
        _save(up_img, f"textures/entity/{mob}.png")
        target = rows_a if idx < 5 else rows_b
        target.append((f"{mob} ORIGINAL", GEO / f"{mob}.geo.json", orig_img))
        target.append((f"{mob} v2 CLEAN", GEO / f"{mob}.geo.json", up_img))

    mp.save_3d_comparison_sheet(rows_a, ROOT / "build/batch5a_3d.png", scale=6)
    mp.save_3d_comparison_sheet(rows_b, ROOT / "build/batch5b_3d.png", scale=5)


if __name__ == "__main__":
    upgrade_batch5()
    print("Batch 5 complete!")
