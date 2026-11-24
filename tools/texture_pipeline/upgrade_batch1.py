"""Batch 1 Mob Upgrade (Benchmark 3: Nuzzle, Lootkin, Sculk Monstrosity) — v2 Multi-Stop 3D Gradients & 1:1 UV Models.

Usage: python -I tools/texture_pipeline/upgrade_batch1.py
Writes upgraded textures and variant models directly, then generates 3D comparison sheets in build/batch1_*.png.
"""
import copy, json, math, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/pysift"
TEX = RES / "textures/entity"
GEO = RES / "geckolib/models/entity"
SNAP = ROOT / ".texture_backups/20261124_mob_originals/files"

sys.path.insert(0, str(ROOT / "tools/texture_pipeline"))
sys.path.insert(0, str(ROOT / "tools/models"))
import mob_painter_v2 as mp  # noqa: E402
import variant_parts as vp   # noqa: E402


def _save(img, rel):
    p = RES / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p)
    print("wrote", rel, img.size)


# ==============================================================================
# 1. NUZZLE (Preserves approved model shape; fixes 2 side UV stretches on cold;
#            upgrades all 9 textures with rich 14-stop wool & skin gradients)
# ==============================================================================
def upgrade_nuzzle():
    # Fill original fur-shell top/bottom holes (approved in MOB_TEXTURE_SPEC.md)
    def fill_nuzzle_holes(src, spx, out, opx):
        geo = json.loads((GEO / "nuzzle.geo.json").read_text(encoding="utf-8"))["minecraft:geometry"][0]
        # Collect fur pixels to sample average red fur colour for filling the missing top/bottom edge holes
        fur_cols = []
        for y in range(src.height):
            for x in range(src.width):
                c = spx[x, y]
                if c[3] > 0:
                    h, s, v = mp.rgb_to_hsv(c[:3])
                    if mp.hue_in(h, 335, 15) and s >= 0.42 and v >= 0.45:
                        fur_cols.append(c[:3])
        fill_col = tuple(sum(c[i] for c in fur_cols) // len(fur_cols) for i in range(3))
        for b in geo["bones"]:
            for c in b.get("cubes", []):
                uv = c.get("uv")
                if not isinstance(uv, dict):
                    continue
                for face in ("up", "down"):
                    fd = uv.get(face)
                    if not isinstance(fd, dict):
                        continue
                    (u0, v0), (uw, vh) = fd["uv"], fd["uv_size"]
                    if abs(uw) == 16:
                        x0, x1 = sorted((int(u0), int(round(u0 + uw))))
                        y0, y1 = sorted((int(v0), int(round(v0 + vh))))
                        for y in range(y0, y1):
                            for x in range(x0, x1):
                                if opx[x, y][3] == 0:
                                    opx[x, y] = (*fill_col, 255)

    nuzzle_rules = [
        {"name": "eye", "match": lambda r, g, b, h, s, v, info: s < 0.08 and v < 0.35, "kind": "keep"},
        {"name": "fur", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 335, 18) and s >= 0.40 and v >= 0.42,
         "kind": "wool", "dark_mul": 0.44, "light_mul": 1.44, "cool_deg": 12, "warm_deg": 12, "spread": 0.78,
         "balance_mean": 0.90, "params": {"macro_y": 0.80, "ao_strength": 0.65, "orig_weight": 0.18}},
        {"name": "plant", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 95, 195) and s >= 0.14,
         "kind": "plant", "dark_mul": 0.46, "light_mul": 1.46, "cool_deg": 12, "warm_deg": 12, "spread": 0.66,
         "balance_mean": 0.90, "params": {"macro_y": 0.65, "ao_strength": 0.55, "orig_weight": 0.22}},
        {"name": "skin", "match": lambda r, g, b, h, s, v, info: True,
         "kind": "skin", "dark_mul": 0.54, "light_mul": 1.54, "cool_deg": 12, "warm_deg": 12, "spread": 0.74,
         "balance_mean": 0.92, "params": {"macro_y": 0.65, "ao_strength": 0.58, "orig_weight": 0.20}},
    ]
    # Approved inward-looking eyes (MOB_TEXTURE_SPEC.md section III: Nuzzle)
    nuzzle_eyes = {(3, 2): (142, 187, 151, 255), (3, 3): (30, 26, 32, 255)}

    orig_img = Image.open(SNAP / "textures/entity/nuzzle.png").convert("RGBA")
    base_img, owner, pmap = mp.upgrade_mob_texture(
        orig_img, [GEO / "nuzzle.geo.json"], nuzzle_rules,
        seed=101, fixed_pixels=nuzzle_eyes, fill_holes=fill_nuzzle_holes, clear_unused=False,
    )
    _save(base_img, "textures/entity/nuzzle.png")

    # Rebuild nuzzle_cold.geo.json and nuzzle_tropical.geo.json with EXACT same approved 3D geometry
    # but 1:1 proportional UVs on every single face (eliminating the chin_side & ruff_back stretches!)
    cold_packer = vp.UVPacker.from_base_model("nuzzle", target_size=(64, 64))
    cold_cache = {}

    def build_nuzzle_cold(add, bones):
        # Exact same approved cubes as build_nuzzle_variants.py (face ruff, chin, rabbit tail, 4 leg cuffs)
        # Tiny 0.04 offsets on crossing boxes prevent coplanar Z-fighting in-game without altering silhouette.
        add("body", [
            vp.make_box(cold_packer, [-6, 7, -9], [2, 9, 3], "ruff", shared_cache=cold_cache),
            vp.make_box(cold_packer, [4, 7, -9], [2, 9, 3], "ruff", shared_cache=cold_cache),
            vp.make_box(cold_packer, [-5, 5.5, -9.04], [10, 2, 3.08], "ruff", shared_cache=cold_cache),
            # Round rabbit-like tail (exact approved 3 crossing boxes, staggered by 0.04 in Z to avoid coplanar shimmer)
            vp.make_box(cold_packer, [-2, 10.5, 10], [4, 4, 3], "tail", shared_cache=cold_cache),
            vp.make_box(cold_packer, [-1, 9.5, 10.48], [2, 6, 2.04], "tail", shared_cache=cold_cache),
            vp.make_box(cold_packer, [-3, 11.5, 10.52], [6, 2, 1.96], "tail", shared_cache=cold_cache),
        ])
        for leg, (x, z) in {"front_left_leg": (-7.55, -6.5), "front_right_leg": (2.55, -6.5),
                            "back_right_leg": (2.55, 2.5), "back_left_leg": (-7.55, 2.5)}.items():
            add(leg, [vp.make_box(cold_packer, [x, 2, z], [5, 3, 5], "cuff", shared_cache=cold_cache)])

    vp.build_variant("nuzzle", "cold", build_nuzzle_cold, target_size=(64, 64))

    trop_packer = vp.UVPacker.from_base_model("nuzzle", target_size=(64, 64))
    trop_cache = {}

    def flower_nuzzle(facing, x, y, z):
        if facing == "up":
            return [
                vp.make_box(trop_packer, [x, y, z], [4, 1, 4], "petal", shared_cache=trop_cache),
                vp.make_box(trop_packer, [x + 1, y + 1, z + 1], [2, 1, 2], "centre", shared_cache=trop_cache),
            ]
        cx = x + 1 if facing == "east" else x - 1
        return [
            vp.make_box(trop_packer, [x, y, z], [1, 4, 4], "petal", shared_cache=trop_cache),
            vp.make_box(trop_packer, [cx, y + 1, z + 1], [1, 2, 2], "centre", shared_cache=trop_cache),
        ]

    def build_nuzzle_trop(add, bones):
        # Exact approved 6 hibiscus flowers: 2 on back, 2 on each side
        add("body", (
            flower_nuzzle("up", -6.5, 20, 0) + flower_nuzzle("up", 1.5, 20, 3) +
            flower_nuzzle("east", 8, 12, -2) + flower_nuzzle("east", 8, 6, 3) +
            flower_nuzzle("west", -9, 13, 1) + flower_nuzzle("west", -9, 7, -4)
        ))

    vp.build_variant("nuzzle", "tropical", build_nuzzle_trop, target_size=(64, 64))

    # Paint tropical & cold textures
    trop_img = mp.apply_climate_shift(base_img, owner, "tropical", {
        "trop_sat": {"fur": 1.26, "skin": 1.18, "plant": 1.28},
        "trop_val": {"fur": 1.05, "plant": 1.06},
        "trop_hue_deg": {"fur": 10.0, "plant": 12.0},
    })
    mp.paint_packed_parts(trop_img, trop_packer, {
        "petal": [(196, 172, 152), (228, 208, 184), (244, 232, 210), (248, 242, 224)],   # warm plumeria hibiscus
        "centre": [(186, 128, 42), (228, 176, 64), (248, 218, 96)],
    }, seed=201)
    _save(trop_img, "textures/entity/nuzzle_tropical.png")

    cold_img = mp.apply_climate_shift(base_img, owner, "cold", {
        "cold_hue_target": 235.0,
        "cold_hue_deg": {"fur": 36.0, "skin": 24.0, "plant": 28.0},
        "cold_sat": {"fur": 0.72, "skin": 0.85, "plant": 0.82},
        "cold_veil": 0.22,
    })
    mp.paint_packed_parts(cold_img, cold_packer, {
        "ruff": [(108, 74, 114), (146, 110, 148), (186, 154, 188), (218, 198, 220)],
        "tail": [(122, 92, 132), (168, 142, 176), (212, 196, 218), (236, 228, 240)],
        "cuff": [(102, 70, 108), (144, 110, 148), (188, 158, 190), (220, 200, 222)],
    }, seed=202)
    _save(cold_img, "textures/entity/nuzzle_cold.png")

    # Generate shearable (_sheared + dyeable greyscale _fur) sheets for all 3 climates!
    def write_sheared_and_fur(img, suffix, extra_fur_packer=None):
        sheared = img.copy()
        spx = sheared.load()
        ipx = img.load()
        fur_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        fpx = fur_layer.load()

        # Gather skin ramp for painting sheared body where fur was
        skin_cols = sorted([ipx[x, y][:3] for (x, y), m in owner.items() if m == "skin"], key=mp.lum)
        skin_ramp = mp.build_gradient_ramp(skin_cols, steps=12, dark_mul=0.72, light_mul=1.22, cool_deg=10, warm_deg=10)
        fur_pts = [(x, y) for (x, y), m in owner.items() if m == "fur"]
        flums = [mp.lum(ipx[x, y][:3]) for x, y in fur_pts]
        flo, fhi = min(flums), max(flums)
        for (x, y) in fur_pts:
            t = (mp.lum(ipx[x, y][:3]) - flo) / max(1e-5, fhi - flo)
            spx[x, y] = (*mp.sample_ramp(skin_ramp, 0.25 + 0.55 * t), 255)
            # Rich greyscale wool map (0.48..0.98) so dyed wool preserves full 3D wool tufts & shading!
            g = 0.48 + 0.50 * t
            fpx[x, y] = (int(round(252 * g)), int(round(250 * g)), int(round(246 * g)), 255)
        if extra_fur_packer is not None:
            for _, x0, y0, w, h, _, _ in extra_fur_packer.rects:
                for yy in range(y0, y0 + h):
                    for xx in range(x0, x0 + w):
                        if ipx[xx, yy][3] > 0:
                            spx[xx, yy] = (0, 0, 0, 0)
                            t = max(0.0, min(1.0, (mp.lum(ipx[xx, yy][:3]) - flo) / max(1e-5, fhi - flo)))
                            g = 0.52 + 0.46 * t
                            fpx[xx, yy] = (int(round(252 * g)), int(round(250 * g)), int(round(246 * g)), 255)
        _save(sheared, f"textures/entity/nuzzle{suffix}_sheared.png")
        _save(fur_layer, f"textures/entity/nuzzle{suffix}_fur.png")

    write_sheared_and_fur(base_img, "")
    write_sheared_and_fur(trop_img, "_tropical")
    write_sheared_and_fur(cold_img, "_cold", extra_fur_packer=cold_packer)

    mp.save_3d_comparison_sheet([
        ("nuzzle ORIGINAL", GEO / "nuzzle.geo.json", orig_img),
        ("nuzzle v2 UPGRADED", GEO / "nuzzle.geo.json", base_img),
        ("nuzzle TROPICAL v2", GEO / "nuzzle_tropical.geo.json", trop_img),
        ("nuzzle COLD v2 (1:1 UV)", GEO / "nuzzle_cold.geo.json", cold_img),
    ], ROOT / "build/batch1_nuzzle_3d.png", scale=9)


# ==============================================================================
# 2. LOOTKIN (Rich pastel patchwork wool gradients + DISTINCT 1:1 UV 64x64
#             Desert Fennec/Cactus tropical model & Arctic Fox cold model!)
# ==============================================================================
def upgrade_lootkin():
    # Base lootkin: pastel patchwork wool (mint, peach, cream, lilac) + cyan crest + pale blue-grey feet
    lootkin_rules = [
        {"name": "eye", "match": lambda r, g, b, h, s, v, info: v < 0.56, "kind": "keep"},
        {"name": "mouth", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 335, 14) and s >= 0.36 and v >= 0.56, "kind": "keep"},
        {"name": "crest", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 168, 215) and s >= 0.28,
         "kind": "plant", "dark_mul": 0.55, "light_mul": 1.32, "cool_deg": 18, "warm_deg": 16, "spread": 0.44,
         "params": {"macro_y": 0.65, "ao_strength": 0.45, "orig_weight": 0.30}},
        {"name": "feet", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 200, 250) and 0.11 <= s <= 0.35,
         "kind": "skin", "dark_mul": 0.56, "light_mul": 1.24, "cool_deg": 16, "warm_deg": 12, "spread": 0.45,
         "params": {"macro_y": 0.70, "ao_strength": 0.70, "orig_weight": 0.25}},
        {"name": "mint", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 100, 175) and v >= 0.65,
         "kind": "wool", "dark_mul": 0.58, "light_mul": 1.12, "cool_deg": 10, "warm_deg": 10, "cool_sat": 1.65, "warm_sat": 0.96, "spread": 0.72,
         "balance_mean": 0.18, "params": {"macro_y": 0.80, "ao_strength": 0.75, "orig_weight": 0.20}},
        {"name": "peach", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 345, 42) and v >= 0.65,
         "kind": "wool", "dark_mul": 0.58, "light_mul": 1.12, "cool_deg": 10, "warm_deg": 10, "cool_sat": 1.65, "warm_sat": 0.96, "spread": 0.72,
         "balance_mean": 0.18, "params": {"macro_y": 0.80, "ao_strength": 0.75, "orig_weight": 0.20}},
        {"name": "cream", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 42, 100) and v >= 0.65,
         "kind": "wool", "dark_mul": 0.58, "light_mul": 1.12, "cool_deg": 10, "warm_deg": 10, "cool_sat": 1.65, "warm_sat": 0.96, "spread": 0.72,
         "balance_mean": 0.18, "params": {"macro_y": 0.80, "ao_strength": 0.75, "orig_weight": 0.20}},
        {"name": "lilac", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 250, 345) and v >= 0.65,
         "kind": "wool", "dark_mul": 0.58, "light_mul": 1.12, "cool_deg": 10, "warm_deg": 10, "cool_sat": 1.65, "warm_sat": 0.96, "spread": 0.72,
         "balance_mean": 0.18, "params": {"macro_y": 0.80, "ao_strength": 0.75, "orig_weight": 0.20}},
    ]

    orig_img = Image.open(SNAP / "textures/entity/lootkin.png").convert("RGBA")
    base_img, owner, _ = mp.upgrade_mob_texture(
        orig_img, [GEO / "lootkin.geo.json"], lootkin_rules, seed=303
    )
    _save(base_img, "textures/entity/lootkin.png")

    # ---- DISTINCT TROPICAL MODEL: Desert Fennec Ears + Layered Cactus Flower Crown + Trailing Sack Vines (64x64 POT, 1:1 UV)
    trop_packer = vp.UVPacker.from_base_model("lootkin", target_size=(64, 64))
    trop_cache = {}

    def build_lootkin_trop(add, bones):
        # 1. Wide fennec-fox desert ears flanking the head (angled gracefully outward!)
        add("body", [
            vp.make_box(trop_packer, [-7, 7, -6], [3, 4, 1], "ear", pivot=[-4.5, 8, -5.5], rotation=[0, 12, -24], shared_cache=trop_cache),
            vp.make_box(trop_packer, [4, 7, -6], [3, 4, 1], "ear", pivot=[4.5, 8, -5.5], rotation=[0, -12, 24], shared_cache=trop_cache),
            # Inner ear tuft tips
            vp.make_box(trop_packer, [-8, 9, -6], [2, 2, 1], "ear_tip", pivot=[-4.5, 8, -5.5], rotation=[0, 12, -24], shared_cache=trop_cache),
            vp.make_box(trop_packer, [6, 9, -6], [2, 2, 1], "ear_tip", pivot=[4.5, 8, -5.5], rotation=[0, -12, 24], shared_cache=trop_cache),
        ])
        # 2. Iconic multi-tier 3D Desert Cactus Bloom crowning the top of the crest + drooping succulent leaves
        add("crest", [
            # Outer star petals (4 angled 3D petal blades radiating from crest top y=19, z=-7)
            vp.make_box(trop_packer, [-2, 19, -9], [4, 1, 4], "petal.outer", shared_cache=trop_cache),
            vp.make_box(trop_packer, [-1, 20, -8], [2, 1, 2], "petal.inner", shared_cache=trop_cache),
            vp.make_box(trop_packer, [-1, 21, -8], [2, 1, 2], "centre", shared_cache=trop_cache),
            # Angled side bloom petals & trailing succulent leaves along the stem
            vp.make_box(trop_packer, [1, 15, -8], [3, 1, 2], "leaf", pivot=[1, 15.5, -7], rotation=[0, 0, 22], shared_cache=trop_cache),
            vp.make_box(trop_packer, [-4, 14, -8], [3, 1, 2], "leaf", pivot=[-1, 14.5, -7], rotation=[0, 0, -22], shared_cache=trop_cache),
        ])
        # 3. Graceful pair of 3D succulent leaves + small apricot bud tucked on the treasure sack
        add("sack", [
            vp.make_box(trop_packer, [-3, 8, 2], [3, 1, 2], "leaf", pivot=[-1.5, 8, 3], rotation=[14, 12, -10], shared_cache=trop_cache),
            vp.make_box(trop_packer, [0, 8, 3], [3, 1, 2], "leaf", pivot=[1.5, 8, 4], rotation=[-12, -18, 12], shared_cache=trop_cache),
            vp.make_box(trop_packer, [-1, 8, 2], [2, 2, 2], "petal.bud", shared_cache=trop_cache),
        ])

    vp.build_variant("lootkin", "tropical", build_lootkin_trop, target_size=(64, 64))

    # ---- DISTINCT COLD MODEL: Arctic Fox Layered Ruff + Big Bushy Sweeping Tail + Ear Tufts + Ankle Cuffs (64x64 POT, 1:1 UV)
    cold_packer = vp.UVPacker.from_base_model("lootkin", target_size=(64, 64))
    cold_cache = {}
    LEGS = {"left_front_leg": (-3, -3), "right_front_leg": (1, -3), "left_middle_leg": (-3, 0),
            "right_middle_leg": (1, 0), "left_back_leg": (-3, 3), "right_back_leg": (1, 3)}

    def build_lootkin_cold(add, bones):
        # 1. Double-tiered fluffy arctic fox ruff framing cheeks + thick chest bib (all offsets Z-fighting-free!)
        add("body", [
            vp.make_box(cold_packer, [-6.06, 4, -7.08], [2, 5, 3], "ruff", shared_cache=cold_cache),
            vp.make_box(cold_packer, [4.06, 4, -7.08], [2, 5, 3], "ruff", shared_cache=cold_cache),
            vp.make_box(cold_packer, [-5, 3.06, -8.04], [10, 2, 2], "ruff", shared_cache=cold_cache),
            vp.make_box(cold_packer, [-3, 2.02, -8.10], [6, 1, 2], "ruff_bright", shared_cache=cold_cache),
            # Cozy rounded winter ear tufts on upper corners of head
            vp.make_box(cold_packer, [-5, 10.02, -5], [2, 2, 2], "ruff_bright", shared_cache=cold_cache),
            vp.make_box(cold_packer, [3, 10.02, -5], [2, 2, 2], "ruff_bright", shared_cache=cold_cache),
        ])
        # 2. Big bushy Arctic Fox tail sweeping upward behind the treasure sack!
        add("sack", [
            vp.make_box(cold_packer, [-2, 3, 6], [4, 4, 5], "tail", pivot=[0, 5, 6], rotation=[20, 0, 0], shared_cache=cold_cache),
            vp.make_box(cold_packer, [-1.5, 4.5, 10], [3, 3, 3], "tail_tip", pivot=[0, 5, 6], rotation=[20, 0, 0], shared_cache=cold_cache),
        ])
        # 3. Clean 1:1 UV ankle fur cuffs on all 6 legs
        for leg, (x, z) in LEGS.items():
            add(leg, [vp.make_box(cold_packer, [x - 0.5, 1, z - 0.5], [3, 2, 3], "cuff", shared_cache=cold_cache)])

    vp.build_variant("lootkin", "cold", build_lootkin_cold, target_size=(64, 64))

    # Paint 64x64 tropical & cold textures (original 32x32 shifted cleanly in top-left, new 1:1 parts painted in free space!)
    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {
        "trop_sat_default": 1.65, "trop_val_default": 1.02, "trop_hue_target": 32.0,
        "trop_hue_deg": {"mint": 10, "peach": 8, "cream": 8, "lilac": 10, "crest": 10},
    })
    trop_64 = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    trop_64.paste(trop_base, (0, 0))
    mp.paint_packed_parts(trop_64, trop_packer, {
        "ear": [(176, 128, 108), (218, 174, 148), (242, 212, 186), (248, 232, 210)],
        "ear_tip": [(196, 118, 96), (234, 158, 122), (248, 198, 154)],
        "petal.outer": [(178, 48, 112), (222, 86, 148), (246, 148, 188), (252, 196, 218)],
        "petal.inner": [(210, 74, 124), (244, 132, 168), (252, 186, 206)],
        "petal.bud": [(208, 94, 52), (242, 148, 76), (252, 206, 126)],
        "centre": [(198, 142, 46), (242, 198, 78), (252, 236, 134)],
        "leaf": [(42, 98, 78), (68, 142, 102), (112, 184, 126), (156, 214, 148)],
    }, seed=304)
    _save(trop_64, "textures/entity/lootkin_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {
        "cold_hue_target": 212.0,
        "cold_hue_deg": {"mint": 38, "peach": 48, "cream": 46, "lilac": 38, "crest": 24},
        "cold_sat_default": 0.96, "cold_veil": 0.26,
    })
    cold_64 = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    cold_64.paste(cold_base, (0, 0))
    mp.paint_packed_parts(cold_64, cold_packer, {
        "ruff": [(122, 146, 184), (160, 184, 214), (198, 216, 236), (228, 238, 248)],
        "ruff_bright": [(146, 170, 206), (188, 208, 232), (224, 236, 248), (242, 246, 250)],
        "tail": [(118, 142, 180), (158, 182, 214), (198, 216, 236), (228, 238, 246)],
        "tail_tip": [(176, 198, 224), (214, 228, 242), (240, 245, 250)],
        "cuff": [(114, 138, 176), (154, 178, 210), (194, 212, 234), (224, 234, 246)],
    }, seed=305)
    _save(cold_64, "textures/entity/lootkin_cold.png")

    mp.save_3d_comparison_sheet([
        ("lootkin ORIGINAL", GEO / "lootkin.geo.json", orig_img),
        ("lootkin v2 UPGRADED", GEO / "lootkin.geo.json", base_img),
        ("lootkin TROPICAL v2 (Fennec + Cactus Crown, 1:1 UV)", GEO / "lootkin_tropical.geo.json", trop_64),
        ("lootkin COLD v2 (Arctic Fox Ruff + Tail, 1:1 UV)", GEO / "lootkin_cold.geo.json", cold_64),
    ], ROOT / "build/batch1_lootkin_3d.png", scale=9)


# ==============================================================================
# 3. SCULK MONSTROSITY (Boss, 256x256, glowmask-safe rich abyssal sculk veins +
#                       ivory whalebone armor plates + weathered deepslate legs)
# ==============================================================================
def upgrade_sculk_monstrosity():
    orig_img = Image.open(SNAP / "textures/entity/sculk_monstrosity.png").convert("RGBA")
    glowmask = Image.open(TEX / "sculk_monstrosity_glowmask.png").convert("RGBA")

    sm_rules = [
        # Protect bright glowing cyan spots even if slightly outside glowmask
        {"name": "glow", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 165, 205) and s >= 0.55 and v >= 0.52, "kind": "keep"},
        # Crisp, vibrant, NON-smooth whalebone / weathered stone / deep abyssal sculk!
        # High orig_v_blend (0.82) + 6 crisp vanilla steps preserves EVERY leg brick, bone seam, and sharp pixel cluster!
        {"name": "bone_ivory", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 15, 45) and s >= 0.12 and v >= 0.35,
         "kind": "bone", "steps": 6, "val_amp": 0.18, "orig_v_blend": 0.80, "sat_shadow_boost": 1.15, "sat_light_keep": 1.04,
         "cool_deg": 8, "warm_deg": 8, "spread": 0.85, "balance_mean": 0.90,
         "params": {"scale": 1.4, "macro_y": 0.65, "cube_y": 0.42, "ao_strength": 0.52, "orig_weight": 0.60}},
        {"name": "bone_aged", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 45, 75) and s >= 0.12 and v >= 0.30,
         "kind": "bone", "steps": 6, "val_amp": 0.18, "orig_v_blend": 0.80, "sat_shadow_boost": 1.15, "sat_light_keep": 1.04,
         "cool_deg": 8, "warm_deg": 8, "spread": 0.85, "balance_mean": 0.90,
         "params": {"scale": 1.4, "macro_y": 0.65, "cube_y": 0.42, "ao_strength": 0.52, "orig_weight": 0.60}},
        {"name": "bone_moss", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 75, 165) and s >= 0.12 and v >= 0.18,
         "kind": "plant", "steps": 6, "val_amp": 0.18, "orig_v_blend": 0.82, "sat_shadow_boost": 1.14, "sat_light_keep": 1.05,
         "cool_deg": 8, "warm_deg": 8, "spread": 0.85, "balance_mean": 0.90,
         "params": {"scale": 1.4, "macro_y": 0.65, "cube_y": 0.42, "ao_strength": 0.50, "orig_weight": 0.62}},
        # Weathered slate / stone legs: orig_v_blend=0.86 keeps every single carved brick line razor-sharp!
        {"name": "stone", "match": lambda r, g, b, h, s, v, info: s < 0.12 or v < 0.10,
         "kind": "stone", "steps": 6, "val_amp": 0.20, "orig_v_blend": 0.86, "sat_shadow_boost": 1.08, "sat_light_keep": 1.00,
         "cool_deg": 8, "warm_deg": 8, "spread": 0.88, "balance_mean": 0.92,
         "params": {"scale": 1.4, "macro_y": 0.68, "cube_y": 0.42, "ao_strength": 0.55, "orig_weight": 0.68}},
        # Vivid cyan-teal sculk veins (family 6) — full jewel saturation, crisp stepped volume!
        {"name": "sculk_teal", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 165, 195) and s >= 0.12,
         "kind": "sculk", "steps": 6, "val_amp": 0.22, "orig_v_blend": 0.78, "sat_shadow_boost": 1.08, "sat_light_keep": 1.04,
         "cool_deg": 6, "warm_deg": 8, "spread": 0.90, "balance_mean": 0.92,
         "params": {"scale": 1.5, "macro_y": 0.68, "cube_y": 0.40, "ao_strength": 0.50, "orig_weight": 0.55}},
        # Deep abyssal navy sculk tissue (family 7) — stays deep rich saturated navy with crisp 3D depth, ZERO blur!
        {"name": "sculk_deep", "match": lambda r, g, b, h, s, v, info: True,
         "kind": "sculk", "steps": 6, "val_amp": 0.22, "orig_v_blend": 0.78, "sat_shadow_boost": 1.08, "sat_light_keep": 1.04,
         "cool_deg": 6, "warm_deg": 6, "spread": 0.90, "balance_mean": 0.90,
         "params": {"scale": 1.5, "macro_y": 0.68, "cube_y": 0.40, "ao_strength": 0.50, "orig_weight": 0.55}},
    ]

    upgraded, owner, _ = mp.upgrade_mob_texture(
        orig_img, [GEO / "sculk_monstrosity.geo.json"], sm_rules,
        seed=404, glowmask_img=glowmask,
    )
    _save(upgraded, "textures/entity/sculk_monstrosity.png")

    mp.save_3d_comparison_sheet([
        ("sculk_monstrosity ORIGINAL", GEO / "sculk_monstrosity.geo.json", orig_img),
        ("sculk_monstrosity v2 UPGRADED", GEO / "sculk_monstrosity.geo.json", upgraded),
    ], ROOT / "build/batch1_sculk_monstrosity_3d.png", scale=4)


if __name__ == "__main__":
    upgrade_nuzzle()
    upgrade_lootkin()
    upgrade_sculk_monstrosity()
    print("Batch 1 complete!")
