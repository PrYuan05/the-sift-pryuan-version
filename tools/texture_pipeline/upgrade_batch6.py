"""Batch 6 Mob Upgrade (7 mobs: monarch, harmonizer, mourner, singer, sculk_cube, sculk_maw, sift_warden).

Usage: python -I tools/texture_pipeline/upgrade_batch6.py
Uses Clean Low-Noise 3D Vanilla Gradient Engine (mob_painter_v2.py) with strong original detail preservation.
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


def _auto_bucket_rules(kind_map, keep_fn=None, dark_mul=0.56, light_mul=1.28, spread=0.90, bal=0.84, orig_w=0.50):
    rules = []
    if keep_fn:
        rules.append({"name": "keep", "match": keep_fn, "kind": "keep"})
    rules.append({
        "name": "neutral",
        "match": lambda r, g, b, h, s, v, info: s < 0.12 or v < 0.10,
        "kind": kind_map.get("neutral", "stone"),
        "dark_mul": dark_mul, "light_mul": light_mul, "cool_deg": 8, "warm_deg": 8,
        "steps": 7, "spread": spread, "balance_mean": bal,
        "params": {"macro_y": 0.78, "cube_y": 0.45, "orig_weight": orig_w},
    })
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
            "params": {"macro_y": 0.78, "cube_y": 0.45, "orig_weight": orig_w},
        })
    return rules


def upgrade_batch6():
    specs = [
        ("monarch", [GEO / "monarch.geo.json", GEO / "monarch_body.geo.json", GEO / "monarch_head.geo.json"],
         _auto_bucket_rules(
             {8: "shell", 9: "shell", 10: "shell", 5: "jelly", 6: "shell", 7: "stone", "default": "shell"},
             keep_fn=lambda r, g, b, h, s, v, info: (s < 0.08 and v >= 0.85) or (mp.hue_in(h, 140, 185) and v >= 0.85),
             dark_mul=0.52, light_mul=1.34, spread=0.92, bal=0.88, orig_w=0.45,
         ), 3001, 4),
        ("harmonizer", [GEO / "harmonizer.geo.json", GEO / "harmonizer_body.geo.json", GEO / "harmonizer_head.geo.json"],
         _auto_bucket_rules(
             {9: "shell", 8: "shell", 7: "shell", 1: "bone", "bal_1": 0.72, "default": "shell"},
             keep_fn=lambda r, g, b, h, s, v, info: (s < 0.08 and v >= 0.88),
             dark_mul=0.54, light_mul=1.30, spread=0.90, bal=0.86, orig_w=0.48,
         ), 3002, 4),
        ("mourner", [GEO / "mourner.geo.json"],
         _auto_bucket_rules(
             {6: "skin", 7: "skin", "neutral": "bone", "default": "skin"},
             keep_fn=lambda r, g, b, h, s, v, info: (mp.hue_in(h, 165, 205) and v >= 0.78 and s >= 0.55) or v < 0.12,
             dark_mul=0.56, light_mul=1.28, spread=0.82, bal=0.88, orig_w=1.15,
         ), 3003, 4),
        ("singer", [GEO / "singer.geo.json"],
         _auto_bucket_rules(
             {6: "skin", 1: "bone", "neutral": "bone", "default": "skin"},
             keep_fn=lambda r, g, b, h, s, v, info: v < 0.16,
             dark_mul=0.56, light_mul=1.24, spread=0.80, bal=0.86, orig_w=1.20,
         ), 3004, 4),
        ("sculk_cube", [GEO / "sculk_cube.geo.json"],
         _auto_bucket_rules(
             {6: "sculk", 7: "sculk", "neutral": "stone", "default": "sculk"},
             keep_fn=lambda r, g, b, h, s, v, info: mp.hue_in(h, 170, 205) and s >= 0.65 and v >= 0.55,
             dark_mul=0.48, light_mul=1.42, spread=0.94, bal=0.90, orig_w=0.45,
         ), 3005, 8),
        ("sculk_maw", [GEO / "sculk_maw.geo.json"],
         _auto_bucket_rules(
             {6: "sculk", 7: "sculk", "default": "sculk"},
             keep_fn=lambda r, g, b, h, s, v, info: mp.hue_in(h, 165, 200) and s >= 0.50 and v >= 0.80,
             dark_mul=0.48, light_mul=1.38, spread=0.94, bal=0.88, orig_w=0.45,
         ), 3006, 8),
    ]

    rows_a, rows_b = [], []
    for idx, (mob, geos, rules, seed, sc) in enumerate(specs):
        orig_img = Image.open(SNAP / f"textures/entity/{mob}.png").convert("RGBA")
        up_img, _, _ = mp.upgrade_mob_texture(orig_img, geos, rules, seed=seed)
        _save(up_img, f"textures/entity/{mob}.png")
        target = rows_a if idx < 3 else rows_b
        target.append((f"{mob} ORIGINAL", geos[0], orig_img))
        target.append((f"{mob} v2 CLEAN", geos[0], up_img))

    mp.save_3d_comparison_sheet(rows_a, ROOT / "build/batch6a_3d.png", scale=4)
    mp.save_3d_comparison_sheet(rows_b, ROOT / "build/batch6b_3d.png", scale=5)

    # 7. SIFT_WARDEN (vanilla Warden geometry, 128x128, 4 emissive overlays 100% locked!)
    sw_dir = RES / "textures/entity/sift_warden"
    sw_orig = Image.open(SNAP / "textures/entity/sift_warden/sift_warden.png").convert("RGBA")
    # Build composite glowmask from all 4 emissive overlay layers so 100% of emissive pixels stay untouched!
    gm = Image.new("RGBA", sw_orig.size, (0, 0, 0, 0))
    gm_px = gm.load()
    for overlay in ("sift_warden_bioluminescent_layer.png", "sift_warden_heart.png",
                    "sift_warden_pulsating_spots_1.png", "sift_warden_pulsating_spots_2.png"):
        ov = Image.open(sw_dir / overlay).convert("RGBA")
        opx = ov.load()
        for y in range(min(gm.height, ov.height)):
            for x in range(min(gm.width, ov.width)):
                if opx[x, y][3] > 0:
                    gm_px[x, y] = (255, 255, 255, 255)

    sw_rules = _auto_bucket_rules(
        {10: "skin", 11: "skin", 0: "skin", 1: "bone", "default": "skin"},
        keep_fn=lambda r, g, b, h, s, v, info: v < 0.14,
        dark_mul=0.58, light_mul=1.24, spread=0.78, bal=0.90, orig_w=1.20,
    )
    sw_up, _, _ = mp.upgrade_mob_texture(sw_orig, [], sw_rules, seed=3007, glowmask_img=gm)
    _save(sw_up, "textures/entity/sift_warden/sift_warden.png")


if __name__ == "__main__":
    upgrade_batch6()
    print("Batch 6 complete!")
