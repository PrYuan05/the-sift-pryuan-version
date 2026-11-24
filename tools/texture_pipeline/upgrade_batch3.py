"""Batch 3 Mob Upgrade (Slabber, Nester, Pollinator, Seedling, Sprout, Sentinel) — Crisp 3D Pixel-Cluster Gradients & Distinct 1:1 UV Models.

Usage: python -I tools/texture_pipeline/upgrade_batch3.py
Note: Nester, Pollinator, Seedling, Sprout, Sentinel read from .texture_backups/20261124_placeholder_split per MOB_TEXTURE_SPEC.md!
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/pysift"
GEO = RES / "geckolib/models/entity"
SNAP_MAIN = ROOT / ".texture_backups/20261124_mob_originals/files"
SNAP_SPLIT = ROOT / ".texture_backups/20261124_placeholder_split"

sys.path.insert(0, str(ROOT / "tools/texture_pipeline"))
sys.path.insert(0, str(ROOT / "tools/models"))
import mob_painter_v2 as mp  # noqa: E402
import variant_parts as vp   # noqa: E402


def _save(img, rel):
    p = RES / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p)
    print("wrote", rel, img.size)


def _split_orig(mob):
    p = SNAP_SPLIT / f"{mob}.png"
    if not p.exists():
        p = SNAP_SPLIT / f"files/textures/entity/{mob}.png"
    return Image.open(p).convert("RGBA")


# ==============================================================================
# 1. SLABBER (Mossy mud-slab cow with mushrooms; 128x128, dens=1.0)
#    Tropical: Layered 3D tropical fern fronds arching off back + 2 flank orchid buds
#    Cold:     Highland Musk-Ox layered hanging shoulder fur cloak + shaggy brow bangs
# ==============================================================================
def upgrade_slabber():
    orig_img = Image.open(SNAP_MAIN / "textures/entity/slabber.png").convert("RGBA")
    rules = [
        # Protect white highlights & eyes (neutral bright or very dark)
        {"name": "eye_white", "match": lambda r, g, b, h, s, v, info: (s < 0.08 and v >= 0.85) or v < 0.16, "kind": "keep"},
        # Bright golden/amber glowing mushroom spots (family 1..2: H 25..75)
        {"name": "shroom_glow", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 25, 75) and s >= 0.25 and v >= 0.80,
         "kind": "plant", "dark_mul": 0.62, "light_mul": 1.05, "cool_deg": 8, "warm_deg": 8, "steps": 8,
         "spread": 0.72, "balance_mean": 0.75, "params": {"crisp": 0.45, "macro_y": 0.50, "orig_weight": 0.28}},
        # Pink tongue & gills (family 11 + family 0: H 315..25)
        {"name": "tongue", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 315, 25) and s >= 0.14,
         "kind": "skin", "dark_mul": 0.52, "light_mul": 1.24, "cool_deg": 10, "warm_deg": 10, "steps": 9,
         "spread": 0.78, "balance_mean": 0.82, "params": {"crisp": 0.45, "macro_y": 0.50, "orig_weight": 0.25}},
        # Slate-violet body hide (family 9: H 230..315)
        {"name": "hide", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 230, 315) and s >= 0.10,
         "kind": "skin", "dark_mul": 0.42, "light_mul": 1.56, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.88, "balance_mean": 0.90, "params": {"scale": 1.3, "crisp": 0.52, "macro_y": 0.58, "orig_weight": 0.26}},
        # Teal-slate mud stone / dark moss (family 6: H 165..225)
        {"name": "mud", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 165, 225) and s >= 0.10,
         "kind": "stone", "dark_mul": 0.40, "light_mul": 1.62, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.90, "balance_mean": 0.92, "params": {"scale": 1.3, "crisp": 0.55, "macro_y": 0.58, "orig_weight": 0.26}},
        # Lush emerald back moss (family 5: H 100..165)
        {"name": "moss", "match": lambda r, g, b, h, s, v, info: True,
         "kind": "plant", "dark_mul": 0.42, "light_mul": 1.48, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.88, "balance_mean": 0.90, "params": {"scale": 1.2, "crisp": 0.52, "macro_y": 0.60, "orig_weight": 0.24}},
    ]
    base_img, owner, _ = mp.upgrade_mob_texture(orig_img, [GEO / "slabber.geo.json"], rules, seed=901)
    _save(base_img, "textures/entity/slabber.png")

    # ---- TROPICAL: Rainforest Swamp Beast (3D spreading fern fronds + 2 flank orchid buds, 128x128, 1:1 UV)
    trop_packer = vp.UVPacker.from_base_model("slabber", target_size=(128, 128))
    tc = {}

    def build_slabber_trop(add, bones):
        # body: x -11..11, y 9..26, z -13..13; head: x -7..7, y 13..27, z -15..-5
        add("body", [
            # Spreading 3D tropical fern fronds arching out over the mossy back flanks!
            vp.make_box(trop_packer, [10.2, 24.5, -8.0], [5, 1, 3], "leaf", pivot=[10.5, 25.0, -6.5], rotation=[0, 12, 24], shared_cache=tc),
            vp.make_box(trop_packer, [10.2, 24.8, 1.0], [6, 1, 3], "leaf", pivot=[10.5, 25.3, 2.5], rotation=[0, -14, 28], shared_cache=tc),
            vp.make_box(trop_packer, [-15.2, 24.5, -6.0], [5, 1, 3], "leaf", pivot=[-10.5, 25.0, -4.5], rotation=[0, -12, -24], shared_cache=tc),
            vp.make_box(trop_packer, [-16.2, 24.8, 3.0], [6, 1, 3], "leaf", pivot=[-10.5, 25.3, 4.5], rotation=[0, 14, -28], shared_cache=tc),
            # Hanging jungle vine fringes + 2 side orchid buds (NO flat square stickers!)
            vp.make_box(trop_packer, [11.06, 14.0, -3.0], [1, 7, 2], "vine", shared_cache=tc),
            vp.make_box(trop_packer, [11.06, 18.0, 5.0], [2, 2, 2], "petal", shared_cache=tc),
            vp.make_box(trop_packer, [-12.06, 14.0, 2.0], [1, 7, 2], "vine", shared_cache=tc),
            vp.make_box(trop_packer, [-13.06, 18.0, -6.0], [2, 2, 2], "petal", shared_cache=tc),
        ])

    vp.build_variant("slabber", "tropical", build_slabber_trop, target_size=(128, 128))

    # ---- COLD: Highland Musk-Ox (layered hanging fur shoulder cloak + shaggy brow bangs + frost cuffs)
    cold_packer = vp.UVPacker.from_base_model("slabber", target_size=(128, 128))
    cc = {}

    def build_slabber_cold(add, bones):
        add("body", [
            # Sleek layered Highland Musk-Ox shaggy shoulder mantle (1-px slim, stepped cleanly off flanks)
            vp.make_box(cold_packer, [11.06, 15.0, -10.5], [1, 10, 9], "ruff", shared_cache=cc),
            vp.make_box(cold_packer, [11.12, 16.0, -0.5], [1, 9, 9], "ruff_bright", shared_cache=cc),
            vp.make_box(cold_packer, [-12.06, 15.0, -10.5], [1, 10, 9], "ruff", shared_cache=cc),
            vp.make_box(cold_packer, [-12.12, 16.0, -0.5], [1, 9, 9], "ruff_bright", shared_cache=cc),
            # Shaggy winter chest bib & back tail tuft
            vp.make_box(cold_packer, [-7.0, 9.5, -14.08], [14, 4, 1], "ruff_bright", shared_cache=cc),
            vp.make_box(cold_packer, [-2.5, 13.0, 13.06], [5, 5, 2], "tail", shared_cache=cc),
        ])
        add("head", [
            # Iconic Highland cattle shaggy forehead bangs overhanging the brow!
            vp.make_box(cold_packer, [-6.5, 23.5, -16.16], [13, 3, 1], "ruff_bright", shared_cache=cc),
            vp.make_box(cold_packer, [-5.0, 27.04, -14.0], [10, 2, 7], "ruff", shared_cache=cc),
        ])

    vp.build_variant("slabber", "cold", build_slabber_cold, target_size=(128, 128))

    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {
        "trop_sat_default": 1.38, "trop_val_default": 1.05, "trop_hue_target": 136.0,
        "trop_hue_deg": {"moss": 18, "mud": 14, "hide": 12, "tongue": 8},
    })
    mp.paint_packed_parts(trop_base, trop_packer, {
        "leaf": [(26, 98, 62), (48, 148, 84), (92, 194, 106), (144, 226, 136)],
        "vine": [(24, 88, 56), (44, 134, 74), (82, 178, 96)],
        "petal": [(196, 52, 118), (240, 108, 158), (252, 178, 208)],
    }, seed=902)
    _save(trop_base, "textures/entity/slabber_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {
        "cold_hue_target": 216.0,
        "cold_hue_deg": {"moss": 46, "mud": 32, "hide": 24, "shroom_glow": 62},
        "cold_sat_default": 0.85, "cold_veil": 0.24,
    })
    mp.paint_packed_parts(cold_base, cold_packer, {
        "ruff": [(98, 122, 162), (138, 164, 200), (182, 204, 232), (218, 232, 246)],
        "ruff_bright": [(138, 164, 202), (182, 204, 232), (222, 236, 248)],
        "tail": [(118, 144, 184), (166, 190, 222), (214, 228, 244)],
    }, seed=903)
    _save(cold_base, "textures/entity/slabber_cold.png")

    mp.save_3d_comparison_sheet([
        ("slabber ORIGINAL", GEO / "slabber.geo.json", orig_img),
        ("slabber v2 UPGRADED", GEO / "slabber.geo.json", base_img),
        ("slabber TROPICAL v2 (Rainforest Ferns + Orchids, 1:1 UV)", GEO / "slabber_tropical.geo.json", trop_base),
        ("slabber COLD v2 (Musk-Ox Fur Cloak + Bangs, 1:1 UV)", GEO / "slabber_cold.geo.json", cold_base),
    ], ROOT / "build/batch3_slabber_3d.png", scale=5)


# ==============================================================================
# Shared rules builder for the 5 placeholder-split mobs (cream/peach + teal/blue)
# ==============================================================================
def _split_mob_rules(body_kind="skin", accent_kind="plant", scale=1.0, eye_v=0.45):
    return [
        # Protect eyes (dark blue/neutral or pure white shine)
        {"name": "eye", "match": lambda r, g, b, h, s, v, info: v < eye_v or (s < 0.08 and v >= 0.72), "kind": "keep"},
        # Warm rosy-coral accents (family 0: H 345..18)
        {"name": "coral", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 345, 18) and s >= 0.14,
         "kind": "skin", "dark_mul": 0.48, "light_mul": 1.18, "cool_deg": 10, "warm_deg": 10, "steps": 9,
         "spread": 0.86, "balance_mean": 0.74, "params": {"scale": scale, "crisp": 0.50, "macro_y": 0.56, "orig_weight": 0.22}},
        # Warm cream / tan / ochre body (family 1..2: H 18..75)
        {"name": "cream", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 18, 75) and s >= 0.12,
         "kind": body_kind, "dark_mul": 0.50, "light_mul": 1.12, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.90, "balance_mean": 0.65, "params": {"scale": scale, "crisp": 0.50, "macro_y": 0.58, "orig_weight": 0.20}},
        # Cyan / teal / blue-indigo foliage & carapace (family 6..8)
        {"name": "teal", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 150, 200) and s >= 0.12,
         "kind": accent_kind, "dark_mul": 0.44, "light_mul": 1.32, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.88, "balance_mean": 0.85, "params": {"scale": scale, "crisp": 0.52, "macro_y": 0.58, "orig_weight": 0.22}},
        {"name": "blue", "match": lambda r, g, b, h, s, v, info: True,
         "kind": accent_kind, "dark_mul": 0.42, "light_mul": 1.48, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.88, "balance_mean": 0.88, "params": {"scale": scale, "crisp": 0.52, "macro_y": 0.58, "orig_weight": 0.22}},
    ]


# ==============================================================================
# 2. NESTER (Long-legged forest nester; 128x128, dens=2.0)
#    Tropical: Forked 3D bird-of-paradise crest plumes + nested twig & flower bud
#    Cold:     Downy snowy-owl shoulder shawl + feathered leg warmers
# ==============================================================================
def upgrade_nester():
    orig_img = _split_orig("nester")
    base_img, owner, _ = mp.upgrade_mob_texture(orig_img, [GEO / "nester.geo.json"], _split_mob_rules("skin", "plant", 1.2), seed=1001)
    _save(base_img, "textures/entity/nester.png")

    D = 2.0
    trop_packer = vp.UVPacker.from_base_model("nester", target_size=(128, 128))
    tc = {}

    def build_nester_trop(add, bones):
        # main head cube: x -3.5..3.5, y 14.8..17.3, z -3.75..3.75 (ears stand at z=3.475)
        add("head", [
            # Forked tropical crest plumes seated FLUSH on top of the head cube (y=17.32)!
            vp.make_box(trop_packer, [-2.25, 17.32, -1.5], [1.5, 4.0, 1.0], "plume", density=D, pivot=[-1.5, 17.32, -1.0], rotation=[-18, 0, -22], shared_cache=tc),
            vp.make_box(trop_packer, [0.75, 17.32, -1.5], [1.5, 4.0, 1.0], "plume", density=D, pivot=[1.5, 17.32, -1.0], rotation=[-18, 0, 22], shared_cache=tc),
            vp.make_box(trop_packer, [-1.0, 17.32, 0.2], [2.0, 4.5, 1.0], "plume_tip", density=D, pivot=[0, 17.32, 0.7], rotation=[-24, 0, 0], shared_cache=tc),
            # Side nest twig + blooming flower bud seated flush on right crown edge
            vp.make_box(trop_packer, [2.0, 17.32, -2.0], [2.5, 1.0, 2.5], "leaf", density=D, pivot=[2.5, 17.32, -0.75], rotation=[0, 0, 14], shared_cache=tc),
            vp.make_box(trop_packer, [2.75, 18.34, -1.5], [1.5, 1.5, 1.5], "petal", density=D, shared_cache=tc),
        ])

    vp.build_variant("nester", "tropical", build_nester_trop, target_size=(128, 128))

    cold_packer = vp.UVPacker.from_base_model("nester", target_size=(128, 128))
    cc = {}

    def build_nester_cold(add, bones):
        add("body", [
            # Cozy downy snowy-owl shoulder shawl wrapping torso (cleanly off x +-2, z +-2)
            vp.make_box(cold_packer, [-3.06, 9.2, -2.5], [1.0, 3.0, 5.0], "ruff", density=D, shared_cache=cc),
            vp.make_box(cold_packer, [2.06, 9.2, -2.5], [1.0, 3.0, 5.0], "ruff", density=D, shared_cache=cc),
            vp.make_box(cold_packer, [-2.5, 9.0, -3.06], [5.0, 3.0, 1.0], "ruff_bright", density=D, shared_cache=cc),
            vp.make_box(cold_packer, [-2.5, 9.0, 2.06], [5.0, 3.0, 1.0], "ruff", density=D, shared_cache=cc),
        ])
        for leg, (lx, lz) in (("front_left_leg", (-2.5, -2.5)), ("front_right_leg", (0.5, -2.5)),
                              ("back_left_leg", (-2.5, 3.0)), ("back_right_leg", (0.5, 3.0))):
            add(leg, [vp.make_box(cold_packer, [lx - 0.5, 1.5, lz - 0.5], [3.0, 3.0, 2.5], "ruff_bright", density=D, shared_cache=cc)])

    vp.build_variant("nester", "cold", build_nester_cold, target_size=(128, 128))

    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {"trop_sat_default": 1.38, "trop_hue_target": 152.0, "trop_hue_deg": {"teal": 24, "cream": 10}})
    mp.paint_packed_parts(trop_base, trop_packer, {
        "plume": [(38, 128, 118), (64, 184, 154), (118, 224, 178)],
        "plume_tip": [(198, 72, 92), (242, 134, 118), (252, 206, 148)],
        "leaf": [(34, 108, 76), (68, 158, 98), (118, 206, 126)],
        "petal": [(208, 56, 104), (246, 122, 152), (252, 194, 212)],
    }, seed=1002)
    _save(trop_base, "textures/entity/nester_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {"cold_hue_target": 216.0, "cold_hue_deg": {"teal": 28, "cream": 46, "coral": 56}, "cold_veil": 0.25})
    mp.paint_packed_parts(cold_base, cold_packer, {
        "ruff": [(126, 154, 194), (168, 194, 226), (210, 226, 244)],
        "ruff_bright": [(166, 192, 224), (208, 226, 244), (238, 246, 250)],
    }, seed=1003)
    _save(cold_base, "textures/entity/nester_cold.png")

    mp.save_3d_comparison_sheet([
        ("nester ORIGINAL (split)", GEO / "nester.geo.json", orig_img),
        ("nester v2 UPGRADED", GEO / "nester.geo.json", base_img),
        ("nester TROPICAL v2 (Plume Crest + Bud, 1:1 UV)", GEO / "nester_tropical.geo.json", trop_base),
        ("nester COLD v2 (Owl Shawl + Leg Warmers, 1:1 UV)", GEO / "nester_cold.geo.json", cold_base),
    ], ROOT / "build/batch3_nester_3d.png", scale=7)


# ==============================================================================
# 3. POLLINATOR (Winged nectar beast; 128x128, dens=1.0)
#    Tropical: Cupped 3D orchid blossom crown + dual 3D golden pollen saddlebags
#    Cold:     Plump highland bumblebee striped fur coat + fuzzy antennae
# ==============================================================================
def upgrade_pollinator():
    orig_img = _split_orig("pollinator")
    base_img, owner, _ = mp.upgrade_mob_texture(orig_img, [GEO / "pollinator.geo.json"], _split_mob_rules("wool", "plant", 1.0), seed=1101)
    _save(base_img, "textures/entity/pollinator.png")

    trop_packer = vp.UVPacker.from_base_model("pollinator", target_size=(128, 128))
    tc = {}

    def build_poll_trop(add, bones):
        # head: x -6.1..6.1, y 18.05..23.05, z -6.12..6; body: x -6..6, y 4..18, z -6.1..6
        add("head", [
            # Cupped 3D royal blossom crown (4 flared petals + tall golden stamen!)
            vp.make_box(trop_packer, [-3, 23.08, -3], [6, 1, 6], "petal.outer", shared_cache=tc),
            vp.make_box(trop_packer, [-1.5, 24.10, -1.5], [3, 3, 3], "centre", shared_cache=tc),
            vp.make_box(trop_packer, [-2, 23.6, -4.5], [4, 3, 1], "petal.inner", pivot=[0, 23.6, -3.5], rotation=[30, 0, 0], shared_cache=tc),
            vp.make_box(trop_packer, [-2, 23.6, 3.5], [4, 3, 1], "petal.inner", pivot=[0, 23.6, 3.5], rotation=[-30, 0, 0], shared_cache=tc),
            vp.make_box(trop_packer, [-4.5, 23.6, -2], [1, 3, 4], "petal.inner", pivot=[-3.5, 23.6, 0], rotation=[0, 0, -30], shared_cache=tc),
            vp.make_box(trop_packer, [3.5, 23.6, -2], [1, 3, 4], "petal.inner", pivot=[3.5, 23.6, 0], rotation=[0, 0, 30], shared_cache=tc),
        ])
        add("body", [
            # Dual 3D golden pollen saddlebags flanking torso!
            vp.make_box(trop_packer, [6.06, 7.0, -2.5], [3, 6, 5], "pollen", shared_cache=tc),
            vp.make_box(trop_packer, [-9.06, 7.0, -2.5], [3, 6, 5], "pollen", shared_cache=tc),
        ])

    vp.build_variant("pollinator", "tropical", build_poll_trop, target_size=(128, 128))

    cold_packer = vp.UVPacker.from_base_model("pollinator", target_size=(128, 128))
    cc = {}

    def build_poll_cold(add, bones):
        add("body", [
            # Plump Highland Bumblebee striped winter fur bolsters wrapping body (zero Z-fighting!)
            vp.make_box(cold_packer, [-6.8, 12.2, -7.14], [14, 4, 1], "ruff_bright", shared_cache=cc),
            vp.make_box(cold_packer, [-6.8, 12.2, 6.08], [14, 4, 1], "ruff_bright", shared_cache=cc),
            vp.make_box(cold_packer, [-7.12, 12.3, -6.0], [1, 4, 12], "ruff", shared_cache=cc),
            vp.make_box(cold_packer, [6.08, 12.3, -6.0], [1, 4, 12], "ruff", shared_cache=cc),
            vp.make_box(cold_packer, [-6.8, 6.0, -7.18], [14, 3, 1], "ruff_stripe", shared_cache=cc),
            vp.make_box(cold_packer, [-6.8, 6.0, 6.12], [14, 3, 1], "ruff_stripe", shared_cache=cc),
        ])
        add("head", [
            # Thick fuzzy bumblebee winter antennae
            vp.make_box(cold_packer, [-4.0, 23.08, -3.5], [2, 4, 2], "ruff_bright", pivot=[-3.0, 23.08, -2.5], rotation=[20, 0, -22], shared_cache=cc),
            vp.make_box(cold_packer, [2.0, 23.08, -3.5], [2, 4, 2], "ruff_bright", pivot=[3.0, 23.08, -2.5], rotation=[20, 0, 22], shared_cache=cc),
        ])

    vp.build_variant("pollinator", "cold", build_poll_cold, target_size=(128, 128))

    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {"trop_sat_default": 1.38, "trop_hue_target": 36.0, "trop_hue_deg": {"teal": 18, "cream": 10}})
    mp.paint_packed_parts(trop_base, trop_packer, {
        "petal.outer": [(186, 48, 108), (232, 98, 148), (250, 166, 196)],
        "petal.inner": [(210, 74, 128), (246, 134, 174), (252, 202, 220)],
        "centre": [(204, 152, 38), (246, 208, 76), (252, 240, 138)],
        "pollen": [(198, 132, 32), (242, 188, 56), (252, 230, 114)],
    }, seed=1102)
    _save(trop_base, "textures/entity/pollinator_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {"cold_hue_target": 212.0, "cold_hue_deg": {"teal": 32, "cream": 46, "coral": 56}, "cold_veil": 0.26})
    mp.paint_packed_parts(cold_base, cold_packer, {
        "ruff": [(122, 148, 188), (164, 188, 222), (206, 224, 242)],
        "ruff_bright": [(168, 194, 228), (210, 228, 244), (238, 246, 250)],
        "ruff_stripe": [(72, 96, 142), (108, 136, 182), (154, 180, 214)],
    }, seed=1103)
    _save(cold_base, "textures/entity/pollinator_cold.png")

    mp.save_3d_comparison_sheet([
        ("pollinator ORIGINAL (split)", GEO / "pollinator.geo.json", orig_img),
        ("pollinator v2 UPGRADED", GEO / "pollinator.geo.json", base_img),
        ("pollinator TROPICAL v2 (Orchid Crown + Pollen Bags, 1:1 UV)", GEO / "pollinator_tropical.geo.json", trop_base),
        ("pollinator COLD v2 (Bumblebee Coat + Antennae, 1:1 UV)", GEO / "pollinator_cold.geo.json", cold_base),
    ], ROOT / "build/batch3_pollinator_3d.png", scale=6)


# ==============================================================================
# 4. SEEDLING (Chomping sprout spirit; 128x128, dens=1.0)
#    Tropical: Wide angled 3D broad-leaves + central blooming flower bud
#    Cold:     Layered 3D pinecone / winter-bud cap + mossy-frost skirt tufts
# ==============================================================================
def upgrade_seedling():
    orig_img = _split_orig("seedling")
    base_img, owner, _ = mp.upgrade_mob_texture(orig_img, [GEO / "seedling.geo.json"], _split_mob_rules("skin", "plant", 1.0), seed=1201)
    _save(base_img, "textures/entity/seedling.png")

    trop_packer = vp.UVPacker.from_base_model("seedling", target_size=(128, 128))
    tc = {}

    def build_seed_trop(add, bones):
        # upper_jaw: x -5.1..5.1, y 8..12, z -5.17..5; body: x -5..5, y 3.95..7.95, z -5..5
        add("upper_jaw", [
            # Wide unfurling tropical broad-leaves + central blooming flower bud!
            vp.make_box(trop_packer, [2.0, 12.04, -2.5], [6, 1, 5], "leaf", pivot=[2.5, 12.04, 0], rotation=[0, 0, -28], shared_cache=tc),
            vp.make_box(trop_packer, [-8.0, 12.04, -2.5], [6, 1, 5], "leaf", pivot=[-2.5, 12.04, 0], rotation=[0, 0, 28], shared_cache=tc),
            vp.make_box(trop_packer, [-2.0, 12.08, -2.0], [4, 2, 4], "petal", shared_cache=tc),
            vp.make_box(trop_packer, [-1.0, 14.10, -1.0], [2, 2, 2], "centre", shared_cache=tc),
        ])

    vp.build_variant("seedling", "tropical", build_seed_trop, target_size=(128, 128))

    cold_packer = vp.UVPacker.from_base_model("seedling", target_size=(128, 128))
    cc = {}

    def build_seed_cold(add, bones):
        add("upper_jaw", [
            # Layered 3D winter pinecone / frosted bud cap crowning the head!
            vp.make_box(cold_packer, [-3.0, 12.04, -3.0], [6, 2, 6], "cone", shared_cache=cc),
            vp.make_box(cold_packer, [-2.0, 14.06, -2.0], [4, 2, 4], "cone_tip", shared_cache=cc),
            vp.make_box(cold_packer, [-1.0, 16.08, -1.0], [2, 2, 2], "ruff_bright", shared_cache=cc),
        ])
        add("body", [
            # Plush frost-moss winter skirt tufts hugging the lower body
            vp.make_box(cold_packer, [-5.6, 3.8, -6.06], [11, 3, 1], "ruff_bright", shared_cache=cc),
            vp.make_box(cold_packer, [-5.6, 3.8, 5.06], [11, 3, 1], "ruff", shared_cache=cc),
            vp.make_box(cold_packer, [-6.08, 3.9, -5.0], [1, 3, 10], "ruff", shared_cache=cc),
            vp.make_box(cold_packer, [5.08, 3.9, -5.0], [1, 3, 10], "ruff", shared_cache=cc),
        ])

    vp.build_variant("seedling", "cold", build_seed_cold, target_size=(128, 128))

    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {"trop_sat_default": 1.38, "trop_hue_target": 136.0, "trop_hue_deg": {"teal": 22, "cream": 10}})
    mp.paint_packed_parts(trop_base, trop_packer, {
        "leaf": [(28, 104, 68), (56, 158, 92), (104, 206, 118), (156, 232, 146)],
        "petal": [(204, 54, 108), (244, 112, 152), (252, 184, 206)],
        "centre": [(208, 156, 40), (248, 212, 78), (252, 242, 140)],
    }, seed=1202)
    _save(trop_base, "textures/entity/seedling_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {"cold_hue_target": 212.0, "cold_hue_deg": {"teal": 36, "cream": 46, "coral": 56}, "cold_veil": 0.25})
    mp.paint_packed_parts(cold_base, cold_packer, {
        "cone": [(78, 98, 128), (112, 134, 166), (156, 178, 206)],
        "cone_tip": [(108, 132, 166), (152, 176, 208), (198, 216, 238)],
        "ruff": [(126, 154, 194), (168, 194, 226), (210, 226, 244)],
        "ruff_bright": [(168, 194, 228), (210, 228, 244), (238, 246, 250)],
    }, seed=1203)
    _save(cold_base, "textures/entity/seedling_cold.png")

    mp.save_3d_comparison_sheet([
        ("seedling ORIGINAL (split)", GEO / "seedling.geo.json", orig_img),
        ("seedling v2 UPGRADED", GEO / "seedling.geo.json", base_img),
        ("seedling TROPICAL v2 (Broad-Leaves + Bud, 1:1 UV)", GEO / "seedling_tropical.geo.json", trop_base),
        ("seedling COLD v2 (Pinecone Cap + Frost Skirt, 1:1 UV)", GEO / "seedling_cold.geo.json", cold_base),
    ], ROOT / "build/batch3_seedling_3d.png", scale=7)


# ==============================================================================
# 5. SPROUT (Floating umbrella spore; 128x128, dens=2.0)
#    Tropical: Coral reef branches & anemone crown + hanging rim petal tendrils
#    Cold:     Faceted 3D ice-prism crown + hanging icicle mist spikes
# ==============================================================================
def upgrade_sprout():
    orig_img = _split_orig("sprout")
    sprout_rules = [
        # Protect Sprout's iconic bright sky-blue eye ring & white pupil!
        {"name": "eye_ring", "match": lambda r, g, b, h, s, v, info: (mp.hue_in(h, 192, 214) and s >= 0.38 and v >= 0.48) or (s < 0.08 and v >= 0.72) or v < 0.22, "kind": "keep"},
    ] + _split_mob_rules("jelly", "jelly", 1.2, eye_v=0.22)[1:]
    base_img, owner, _ = mp.upgrade_mob_texture(orig_img, [GEO / "sprout.geo.json"], sprout_rules, seed=1301)
    _save(base_img, "textures/entity/sprout.png")

    D = 2.0
    trop_packer = vp.UVPacker.from_base_model("sprout", target_size=(128, 128))
    tc = {}

    def build_sprout_trop(add, bones):
        # head: x -4..4, y 16.45..24.45, z -4.65..4
        add("head", [
            # Tropical sea-anemone coral crown branching out of the cap top!
            vp.make_box(trop_packer, [-2.5, 24.48, -1.5], [1.5, 3.5, 1.5], "coral", density=D, pivot=[-1.75, 24.48, -0.75], rotation=[16, 0, -24], shared_cache=tc),
            vp.make_box(trop_packer, [1.0, 24.48, -1.5], [1.5, 4.0, 1.5], "coral", density=D, pivot=[1.75, 24.48, -0.75], rotation=[12, 0, 22], shared_cache=tc),
            vp.make_box(trop_packer, [-1.0, 24.48, 1.0], [2.0, 3.0, 1.5], "petal", density=D, pivot=[0, 24.48, 1.75], rotation=[-22, 0, 0], shared_cache=tc),
            # Frilly hanging sea-anemone petal tendrils around umbrella rim
            vp.make_box(trop_packer, [4.04, 15.0, -2.0], [1.0, 3.0, 1.5], "petal", density=D, shared_cache=tc),
            vp.make_box(trop_packer, [-5.04, 15.0, 0.5], [1.0, 3.0, 1.5], "petal", density=D, shared_cache=tc),
            vp.make_box(trop_packer, [-1.0, 15.0, 4.04], [2.0, 3.0, 1.0], "coral", density=D, shared_cache=tc),
        ])

    vp.build_variant("sprout", "tropical", build_sprout_trop, target_size=(128, 128))

    cold_packer = vp.UVPacker.from_base_model("sprout", target_size=(128, 128))
    cc = {}

    def build_sprout_cold(add, bones):
        add("head", [
            # Faceted 3D glacial ice-prism crown atop the floating spore dome!
            vp.make_box(cold_packer, [-1.5, 24.48, -1.5], [3.0, 4.5, 3.0], "ice", density=D, pivot=[0, 24.48, 0], rotation=[-8, 18, 6], shared_cache=cc),
            vp.make_box(cold_packer, [1.5, 24.48, -2.0], [1.5, 3.0, 1.5], "ice_bright", density=D, pivot=[2.25, 24.48, -1.25], rotation=[18, 0, 26], shared_cache=cc),
            vp.make_box(cold_packer, [-3.0, 24.48, 0.5], [1.5, 3.0, 1.5], "ice_bright", density=D, pivot=[-2.25, 24.48, 1.25], rotation=[-18, 0, -26], shared_cache=cc),
            # Hanging frost icicles ringing the umbrella underside!
            vp.make_box(cold_packer, [-3.5, 13.40, -3.5], [1.0, 3.0, 1.0], "ice_bright", density=D, shared_cache=cc),
            vp.make_box(cold_packer, [2.5, 13.90, -3.5], [1.0, 2.5, 1.0], "ice", density=D, shared_cache=cc),
            vp.make_box(cold_packer, [-3.0, 13.90, 2.5], [1.0, 2.5, 1.0], "ice", density=D, shared_cache=cc),
            vp.make_box(cold_packer, [2.0, 13.40, 2.5], [1.0, 3.0, 1.0], "ice_bright", density=D, shared_cache=cc),
        ])

    vp.build_variant("sprout", "cold", build_sprout_cold, target_size=(128, 128))

    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {"trop_sat_default": 1.65, "trop_hue_target": 320.0, "trop_hue_deg": {"blue": 52, "cream": 12}})
    mp.paint_packed_parts(trop_base, trop_packer, {
        "coral": [(186, 52, 92), (234, 98, 128), (252, 166, 178)],
        "petal": [(208, 92, 62), (246, 152, 88), (252, 212, 138)],
    }, seed=1302)
    _save(trop_base, "textures/entity/sprout_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {"cold_hue_target": 208.0, "cold_hue_deg": {"blue": 18, "cream": 52}, "cold_veil": 0.24})
    mp.paint_packed_parts(cold_base, cold_packer, {
        "ice": [(48, 108, 178), (88, 166, 224), (152, 212, 246), (212, 240, 250)],
        "ice_bright": [(86, 154, 216), (144, 208, 242), (206, 238, 250)],
    }, seed=1303)
    _save(cold_base, "textures/entity/sprout_cold.png")

    mp.save_3d_comparison_sheet([
        ("sprout ORIGINAL (split)", GEO / "sprout.geo.json", orig_img),
        ("sprout v2 UPGRADED", GEO / "sprout.geo.json", base_img),
        ("sprout TROPICAL v2 (Coral Anemone Spore, 1:1 UV)", GEO / "sprout_tropical.geo.json", trop_base),
        ("sprout COLD v2 (Glacial Ice-Spore, 1:1 UV)", GEO / "sprout_cold.geo.json", cold_base),
    ], ROOT / "build/batch3_sprout_3d.png", scale=6)


# ==============================================================================
# 6. SENTINEL (Wide-brimmed hat guardian; 128x128, dens=2.0)
#    Tropical: Layered tropical palm-frond hat crown + draping brim vine buds
#    Cold:     Thick sculpted snow-drift cap on hat + paired glacial shoulder ice-plates
# ==============================================================================
def upgrade_sentinel():
    orig_img = _split_orig("sentinel")
    base_img, owner, _ = mp.upgrade_mob_texture(orig_img, [GEO / "sentinel.geo.json"], _split_mob_rules("skin", "shell", 1.2), seed=1401)
    _save(base_img, "textures/entity/sentinel.png")

    D = 2.0
    trop_packer = vp.UVPacker.from_base_model("sentinel", target_size=(128, 128))
    tc = {}

    def build_sent_trop(add, bones):
        # head: x -4.33..4.33, y 10.95..14, z -4.17..4.4; crest brim: x -6.5..6.8, y ~11, z -6.5..6.75; body: x -2..2, y 6.9..10.9
        add("head", [
            # Tropical broadleaf bamboo-hat palm plumes & crown blossom!
            vp.make_box(trop_packer, [-2.5, 14.04, -2.5], [5.0, 1.0, 5.0], "leaf", density=D, shared_cache=tc),
            vp.make_box(trop_packer, [-1.5, 15.06, -1.5], [3.0, 1.5, 3.0], "petal", density=D, shared_cache=tc),
            vp.make_box(trop_packer, [2.0, 13.8, -1.0], [4.5, 1.0, 2.5], "leaf", density=D, pivot=[2.5, 14.0, 0.25], rotation=[0, 0, 22], shared_cache=tc),
            vp.make_box(trop_packer, [-6.5, 13.8, -1.0], [4.5, 1.0, 2.5], "leaf", density=D, pivot=[-2.5, 14.0, 0.25], rotation=[0, 0, -22], shared_cache=tc),
        ])
        add("crest", [
            # Draping tropical brim vine buds attached solidly right under the hat brim corners
            vp.make_box(trop_packer, [4.0, 8.2, -4.0], [1.0, 2.75, 1.0], "vine", density=D, shared_cache=tc),
            vp.make_box(trop_packer, [-4.8, 8.2, 3.4], [1.0, 2.75, 1.0], "vine", density=D, shared_cache=tc),
            vp.make_box(trop_packer, [3.75, 7.2, -4.25], [1.5, 1.0, 1.5], "petal", density=D, shared_cache=tc),
            vp.make_box(trop_packer, [-5.05, 7.2, 3.15], [1.5, 1.0, 1.5], "petal", density=D, shared_cache=tc),
        ])

    vp.build_variant("sentinel", "tropical", build_sent_trop, target_size=(128, 128))

    cold_packer = vp.UVPacker.from_base_model("sentinel", target_size=(128, 128))
    cc = {}

    def build_sent_cold(add, bones):
        add("head", [
            # Thick sculpted snow-drift cap crowning the hat + frosted brim snow mounds!
            vp.make_box(cold_packer, [-3.5, 14.04, -3.5], [7.0, 1.5, 7.0], "ruff_bright", density=D, shared_cache=cc),
            vp.make_box(cold_packer, [-2.0, 15.56, -2.0], [4.0, 1.5, 4.0], "ruff_bright", density=D, shared_cache=cc),
        ])
        add("body", [
            # Paired 3D glacial ice-plate shoulder mantle flanking torso!
            vp.make_box(cold_packer, [2.06, 7.5, -2.0], [2.0, 3.0, 4.0], "ice", density=D, pivot=[2.06, 10.0, 0], rotation=[0, 0, -20], shared_cache=cc),
            vp.make_box(cold_packer, [-4.06, 7.5, -2.0], [2.0, 3.0, 4.0], "ice", density=D, pivot=[-2.06, 10.0, 0], rotation=[0, 0, 20], shared_cache=cc),
        ])

    vp.build_variant("sentinel", "cold", build_sent_cold, target_size=(128, 128))

    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {"trop_sat_default": 1.35, "trop_hue_target": 152.0, "trop_hue_deg": {"blue": 34, "cream": 10}})
    mp.paint_packed_parts(trop_base, trop_packer, {
        "leaf": [(28, 106, 68), (58, 158, 92), (108, 206, 118)],
        "vine": [(24, 92, 60), (48, 142, 82), (88, 188, 104)],
        "petal": [(208, 62, 104), (246, 124, 154), (252, 196, 212)],
    }, seed=1402)
    _save(trop_base, "textures/entity/sentinel_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {"cold_hue_target": 212.0, "cold_hue_deg": {"blue": 14, "cream": 52}, "cold_veil": 0.24})
    mp.paint_packed_parts(cold_base, cold_packer, {
        "ruff_bright": [(166, 196, 228), (208, 228, 246), (238, 246, 250)],
        "ice": [(48, 108, 178), (88, 166, 224), (154, 214, 246), (214, 242, 250)],
    }, seed=1403)
    _save(cold_base, "textures/entity/sentinel_cold.png")

    mp.save_3d_comparison_sheet([
        ("sentinel ORIGINAL (split)", GEO / "sentinel.geo.json", orig_img),
        ("sentinel v2 UPGRADED", GEO / "sentinel.geo.json", base_img),
        ("sentinel TROPICAL v2 (Palm-Leaf Hat + Vines, 1:1 UV)", GEO / "sentinel_tropical.geo.json", trop_base),
        ("sentinel COLD v2 (Snow Cap + Ice Mantle, 1:1 UV)", GEO / "sentinel_cold.geo.json", cold_base),
    ], ROOT / "build/batch3_sentinel_3d.png", scale=7)


if __name__ == "__main__":
    upgrade_slabber()
    upgrade_nester()
    upgrade_pollinator()
    upgrade_seedling()
    upgrade_sprout()
    upgrade_sentinel()
    print("Batch 3 complete!")
