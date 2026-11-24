"""Batch 4 Mob Upgrade (Blub family — 5 distinct materials: jelly, carapace, fungal, meadows, ravines).

Usage: python -I tools/texture_pipeline/upgrade_batch4.py
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


def upgrade_blubs():
    specs = [
        ("blub", [
            {"name": "eye", "match": lambda r, g, b, h, s, v, info: v < 0.65, "kind": "keep"},
            {"name": "jelly", "match": lambda r, g, b, h, s, v, info: True,
             "kind": "jelly", "dark_mul": 0.58, "light_mul": 1.04, "cool_deg": 10, "warm_deg": 8,
             "cool_sat": 1.38, "warm_sat": 0.78, "steps": 7, "spread": 0.96, "balance_mean": 0.56,
             "params": {"macro_y": 0.78, "cube_y": 0.48, "orig_weight": 0.24}},
        ], 1501),
        ("blub_carapace", [
            {"name": "eye", "match": lambda r, g, b, h, s, v, info: v < 0.65, "kind": "keep"},
            {"name": "coral", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 330, 12) and s >= 0.25,
             "kind": "shell", "dark_mul": 0.56, "light_mul": 1.06, "cool_deg": 8, "warm_deg": 8, "steps": 7,
             "spread": 0.92, "balance_mean": 0.50, "params": {"band_h": 3, "macro_y": 0.80, "orig_weight": 0.28}},
            {"name": "peach", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 12, 42) and s >= 0.12,
             "kind": "shell", "dark_mul": 0.56, "light_mul": 1.08, "cool_deg": 8, "warm_deg": 8, "steps": 7,
             "spread": 0.92, "balance_mean": 0.45, "params": {"band_h": 3, "macro_y": 0.82, "orig_weight": 0.28}},
            {"name": "cream", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 42, 95) and s >= 0.12,
             "kind": "shell", "dark_mul": 0.56, "light_mul": 1.08, "cool_deg": 8, "warm_deg": 8, "steps": 7,
             "spread": 0.92, "balance_mean": 0.45, "params": {"band_h": 3, "macro_y": 0.82, "orig_weight": 0.28}},
            {"name": "mint", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 95, 185) and s >= 0.12,
             "kind": "shell", "dark_mul": 0.56, "light_mul": 1.08, "cool_deg": 8, "warm_deg": 8, "steps": 7,
             "spread": 0.92, "balance_mean": 0.45, "params": {"band_h": 3, "macro_y": 0.82, "orig_weight": 0.28}},
            {"name": "peri", "match": lambda r, g, b, h, s, v, info: True,
             "kind": "shell", "dark_mul": 0.56, "light_mul": 1.12, "cool_deg": 8, "warm_deg": 8, "steps": 7,
             "spread": 0.92, "balance_mean": 0.50, "params": {"band_h": 3, "macro_y": 0.82, "orig_weight": 0.28}},
        ], 1502),
        ("blub_fungal", [
            {"name": "eye", "match": lambda r, g, b, h, s, v, info: s >= 0.25 and v < 0.65, "kind": "keep"},
            {"name": "cap", "match": lambda r, g, b, h, s, v, info: True,
             "kind": "plant", "dark_mul": 0.58, "light_mul": 1.14, "cool_deg": 8, "warm_deg": 8, "steps": 7,
             "spread": 0.90, "balance_mean": 0.68, "params": {"macro_y": 0.85, "cube_y": 0.52, "orig_weight": 0.35}},
        ], 1503),
        ("blub_meadows", [
            # Protect dark eyes AND cute crisp white/pale-mint blossom dots on top of moss cap!
            {"name": "eye_dot", "match": lambda r, g, b, h, s, v, info: v < 0.42 or (s < 0.22 and v >= 0.85), "kind": "keep"},
            {"name": "tan", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 0, 75),
             "kind": "skin", "steps": 6, "val_amp": 0.16, "orig_v_blend": 0.82, "sat_shadow_boost": 1.18, "sat_light_keep": 1.05,
             "cool_deg": 8, "warm_deg": 8, "spread": 0.82, "balance_mean": 0.85,
             "params": {"macro_y": 0.72, "cube_y": 0.42, "orig_weight": 0.62}},
            {"name": "moss", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 110, 175),
             "kind": "plant", "steps": 6, "val_amp": 0.17, "orig_v_blend": 0.82, "sat_shadow_boost": 1.16, "sat_light_keep": 1.06,
             "cool_deg": 8, "warm_deg": 8, "spread": 0.84, "balance_mean": 0.88,
             "params": {"macro_y": 0.74, "cube_y": 0.44, "orig_weight": 0.62}},
            {"name": "aqua", "match": lambda r, g, b, h, s, v, info: True,
             "kind": "plant", "steps": 6, "val_amp": 0.17, "orig_v_blend": 0.82, "sat_shadow_boost": 1.16, "sat_light_keep": 1.06,
             "cool_deg": 8, "warm_deg": 8, "spread": 0.84, "balance_mean": 0.88,
             "params": {"macro_y": 0.74, "cube_y": 0.44, "orig_weight": 0.62}},
        ], 1504),
        ("blub_ravines", [
            {"name": "eye", "match": lambda r, g, b, h, s, v, info: v < 0.35, "kind": "keep"},
            {"name": "crystal", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 130, 210) and s >= 0.25,
             "kind": "jelly", "dark_mul": 0.60, "light_mul": 1.22, "cool_deg": 8, "warm_deg": 8, "steps": 6,
             "spread": 0.80, "balance_mean": 0.80, "params": {"macro_y": 0.72, "orig_weight": 0.35}},
            {"name": "sand", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 10, 75) and s >= 0.10,
             "kind": "stone", "dark_mul": 0.56, "light_mul": 1.24, "cool_deg": 8, "warm_deg": 8, "steps": 7,
             "spread": 0.88, "balance_mean": 0.80, "params": {"macro_y": 0.82, "cube_y": 0.48, "orig_weight": 0.35}},
            {"name": "slate", "match": lambda r, g, b, h, s, v, info: True,
             "kind": "stone", "dark_mul": 0.56, "light_mul": 1.28, "cool_deg": 8, "warm_deg": 8, "steps": 7,
             "spread": 0.90, "balance_mean": 0.85, "params": {"macro_y": 0.84, "cube_y": 0.50, "orig_weight": 0.35}},
        ], 1505),
    ]

    rows = []
    for mob, rules, seed in specs:
        orig_img = Image.open(SNAP / f"textures/entity/{mob}.png").convert("RGBA")
        up_img, _, _ = mp.upgrade_mob_texture(orig_img, [GEO / f"{mob}.geo.json"], rules, seed=seed)
        _save(up_img, f"textures/entity/{mob}.png")
        rows.append((f"{mob} ORIGINAL", GEO / f"{mob}.geo.json", orig_img))
        rows.append((f"{mob} v2 CLEAN", GEO / f"{mob}.geo.json", up_img))

    mp.save_3d_comparison_sheet(rows, ROOT / "build/batch4_blubs_3d.png", scale=10)


if __name__ == "__main__":
    upgrade_blubs()
    print("Batch 4 complete!")
