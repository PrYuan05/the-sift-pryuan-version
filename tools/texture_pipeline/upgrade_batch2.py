"""Batch 2 Mob Upgrade (Prickle, Dartback, Fusefly, Wobble) — Crisp 3D Pixel-Cluster Gradients & Distinct 1:1 UV Models.

Usage: python -I tools/texture_pipeline/upgrade_batch2.py
Writes upgraded base + tropical + cold textures and distinct 1:1 UV variant models, then renders 3D comparison sheets.
"""
import json, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/pysift"
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


def _paste_to_pot(base_img, target_size):
    if base_img.size == target_size:
        return base_img.copy()
    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    canvas.paste(base_img, (0, 0))
    return canvas


# ==============================================================================
# 1. PRICKLE (Amethyst-spined hedgehog; 32x32 base -> 64x64 POT 1:1 UV variants)
#    Tropical: Rose-gold fanned desert porcupine quills + 3D succulent flower buds
#    Cold:     Rounded snowy fleece hood + icy-blue dorsal crystal peaks + snow tail
# ==============================================================================
def upgrade_prickle():
    orig_img = Image.open(SNAP / "textures/entity/prickle.png").convert("RGBA")
    rules = [
        # Protect dark eyes / nose
        {"name": "eye", "match": lambda r, g, b, h, s, v, info: v < 0.45, "kind": "keep"},
        # Rosy pink spine tips (family 10: H 285..345)
        {"name": "rose", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 285, 345) and s >= 0.12,
         "kind": "shell", "dark_mul": 0.48, "light_mul": 1.15, "cool_deg": 10, "warm_deg": 10, "steps": 9,
         "spread": 0.78, "balance_mean": 0.55, "params": {"band_h": 3, "crisp": 0.52, "macro_y": 0.58, "orig_weight": 0.22}},
        # Pale cyan-ice accents (family 6: H 150..215)
        {"name": "ice_acc", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 150, 215) and s >= 0.12,
         "kind": "skin", "dark_mul": 0.52, "light_mul": 1.12, "cool_deg": 10, "warm_deg": 10, "steps": 8,
         "spread": 0.72, "balance_mean": 0.55, "params": {"crisp": 0.48, "macro_y": 0.55, "orig_weight": 0.25}},
        # Deep violet spines (family 9: H 255..285)
        {"name": "violet", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 255, 285) and s >= 0.12,
         "kind": "shell", "dark_mul": 0.42, "light_mul": 1.32, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.84, "balance_mean": 0.78, "params": {"band_h": 3, "crisp": 0.52, "macro_y": 0.62, "orig_weight": 0.20}},
        # Soft periwinkle/lavender body (family 8: H 215..255)
        {"name": "lavender", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 215, 255) and s >= 0.12,
         "kind": "wool", "dark_mul": 0.46, "light_mul": 1.24, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.82, "balance_mean": 0.62, "params": {"crisp": 0.48, "macro_y": 0.62, "orig_weight": 0.20}},
        # Neutral cream/white underside & highlight clusters
        {"name": "belly", "match": lambda r, g, b, h, s, v, info: True,
         "kind": "wool", "dark_mul": 0.58, "light_mul": 1.10, "cool_deg": 8, "warm_deg": 8, "steps": 8,
         "spread": 0.74, "balance_mean": 0.45, "params": {"crisp": 0.45, "macro_y": 0.55, "orig_weight": 0.22}},
    ]
    base_img, owner, _ = mp.upgrade_mob_texture(orig_img, [GEO / "prickle.geo.json"], rules, seed=501)
    _save(base_img, "textures/entity/prickle.png")

    # ---- TROPICAL: Rose-gold desert porcupine fanned spines + 2 3D succulent flower buds (64x64, 1:1 UV)
    trop_packer = vp.UVPacker.from_base_model("prickle", target_size=(64, 64))
    tc = {}

    def build_prickle_trop(add, bones):
        # body bbox: x -3.5..3.5, y 0..7, z -5.24..5.76
        add("body", [
            # Dramatic swept-back desert porcupine fan quills (staggered positions -> zero Z-fighting!)
            vp.make_box(trop_packer, [-1, 7.02, -3.5], [2, 3, 1], "quill", pivot=[0, 7.02, -3.0], rotation=[-32, 0, 0], shared_cache=tc),
            vp.make_box(trop_packer, [-1, 7.02, -0.5], [2, 4, 1], "quill", pivot=[0, 7.02, 0.0], rotation=[-38, 0, 0], shared_cache=tc),
            vp.make_box(trop_packer, [-1, 7.02, 2.5], [2, 3, 1], "quill_tip", pivot=[0, 7.02, 3.0], rotation=[-45, 0, 0], shared_cache=tc),
            # Angled flank quill fans on left & right sides
            vp.make_box(trop_packer, [3.52, 4.2, -1.8], [1, 3, 2], "quill", pivot=[3.52, 4.2, -0.8], rotation=[-24, 0, 38], shared_cache=tc),
            vp.make_box(trop_packer, [-4.52, 4.2, -1.8], [1, 3, 2], "quill", pivot=[-3.52, 4.2, -0.8], rotation=[-24, 0, -38], shared_cache=tc),
            vp.make_box(trop_packer, [3.52, 3.6, 1.8], [1, 3, 2], "quill_tip", pivot=[3.52, 3.6, 2.8], rotation=[-32, 0, 42], shared_cache=tc),
            vp.make_box(trop_packer, [-4.52, 3.6, 1.8], [1, 3, 2], "quill_tip", pivot=[-3.52, 3.6, 2.8], rotation=[-32, 0, -42], shared_cache=tc),
            # 2 delicate 3D succulent flower buds nestled between spine rows
            vp.make_box(trop_packer, [-3.2, 7.04, -1.6], [2, 1, 2], "leaf", shared_cache=tc),
            vp.make_box(trop_packer, [-2.7, 8.04, -1.1], [1, 1, 1], "petal", shared_cache=tc),
            vp.make_box(trop_packer, [1.2, 7.04, 1.6], [2, 1, 2], "leaf", shared_cache=tc),
            vp.make_box(trop_packer, [1.7, 8.04, 2.1], [1, 1, 1], "petal", shared_cache=tc),
        ])

    vp.build_variant("prickle", "tropical", build_prickle_trop, target_size=(64, 64))

    # ---- COLD: Thick snowy fleece hood/mantle + icy dorsal crystal peaks + round snow tail (64x64, 1:1 UV)
    cold_packer = vp.UVPacker.from_base_model("prickle", target_size=(64, 64))
    cc = {}

    def build_prickle_cold(add, bones):
        add("body", [
            # Fluffy snowy cheek tufts flanking the face (staggered off +-3.5 and z -5.24)
            vp.make_box(cold_packer, [-5.06, 0.8, -5.0], [2, 5, 3], "ruff", shared_cache=cc),
            vp.make_box(cold_packer, [3.06, 0.8, -5.0], [2, 5, 3], "ruff", shared_cache=cc),
            # Plush snow brow hood across front top (offset Z & Y so zero coplanar overlap with cheeks or body)
            vp.make_box(cold_packer, [-4.0, 6.2, -5.8], [8, 2, 2], "ruff_bright", shared_cache=cc),
            # Rounded snow-fluff shoulder/flank bolsters wrapping the chilly body
            vp.make_box(cold_packer, [-4.54, 1.2, -1.2], [1, 4, 5], "ruff", shared_cache=cc),
            vp.make_box(cold_packer, [3.54, 1.2, -1.2], [1, 4, 5], "ruff", shared_cache=cc),
            # 3 crisp glacial crystal spine peaks poking out of the snowy back!
            vp.make_box(cold_packer, [-1, 7.04, -2.0], [2, 2, 2], "ice", pivot=[0, 7.04, -1.0], rotation=[-18, 0, 0], shared_cache=cc),
            vp.make_box(cold_packer, [-1.5, 7.04, 1.2], [3, 3, 2], "ice", pivot=[0, 7.04, 2.2], rotation=[-22, 0, 0], shared_cache=cc),
            # Cute round snow-ball tail on back
            vp.make_box(cold_packer, [-1.5, 1.6, 5.78], [3, 3, 2], "tail", shared_cache=cc),
        ])

    vp.build_variant("prickle", "cold", build_prickle_cold, target_size=(64, 64))

    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {
        "trop_sat_default": 1.65, "trop_val_default": 1.03, "trop_hue_target": 340.0,
        "trop_hue_deg": {"lavender": 48, "violet": 38, "rose": 14, "ice_acc": 25},
    })
    trop_64 = _paste_to_pot(trop_base, (64, 64))
    mp.paint_packed_parts(trop_64, trop_packer, {
        "quill": [(142, 44, 94), (192, 74, 126), (232, 122, 152), (248, 178, 166)],
        "quill_tip": [(186, 86, 68), (228, 140, 88), (248, 198, 122)],
        "leaf": [(38, 102, 78), (68, 146, 102), (114, 188, 126)],
        "petal": [(210, 62, 114), (244, 122, 158), (252, 192, 212)],
    }, seed=502)
    _save(trop_64, "textures/entity/prickle_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {
        "cold_hue_target": 210.0,
        "cold_hue_deg": {"lavender": 32, "violet": 42, "rose": 65, "ice_acc": 15},
        "cold_sat_default": 0.92, "cold_veil": 0.24,
    })
    # Also cool the tiny <=4px magenta feet strips on prickle_cold (not eyes — eyes have v < 0.45)
    cpx = cold_base.load()
    for yy in range(cold_base.height):
        for xx in range(cold_base.width):
            r, g, b, a = cpx[xx, yy]
            if a == 0 or (xx, yy) in owner:
                continue
            h, s, v = mp.rgb_to_hsv((r, g, b))
            if v >= 0.45 and mp.hue_in(h, 270, 350) and s >= 0.20:
                cpx[xx, yy] = (*mp.hsv_to_rgb(212.0, min(0.42, s * 0.75), min(0.92, v * 0.98)), a)
    cold_64 = _paste_to_pot(cold_base, (64, 64))
    mp.paint_packed_parts(cold_64, cold_packer, {
        "ruff": [(126, 152, 196), (166, 190, 224), (206, 222, 242), (232, 240, 248)],
        "ruff_bright": [(156, 180, 216), (198, 216, 238), (228, 238, 248), (244, 248, 250)],
        "tail": [(148, 174, 212), (192, 212, 236), (228, 238, 248)],
        "ice": [(52, 118, 182), (88, 168, 222), (148, 212, 244), (210, 240, 250)],
    }, seed=503)
    _save(cold_64, "textures/entity/prickle_cold.png")

    mp.save_3d_comparison_sheet([
        ("prickle ORIGINAL", GEO / "prickle.geo.json", orig_img),
        ("prickle v2 UPGRADED", GEO / "prickle.geo.json", base_img),
        ("prickle TROPICAL v2 (Porcupine Quills + Buds, 1:1 UV)", GEO / "prickle_tropical.geo.json", trop_64),
        ("prickle COLD v2 (Snow Mantle + Ice Spines, 1:1 UV)", GEO / "prickle_cold.geo.json", cold_64),
    ], ROOT / "build/batch2_prickle_3d.png", scale=10)


# ==============================================================================
# 2. DARTBACK (Armoured beetle/pangolin beast; 128x128 base, density=4 px/unit!)
#    Tropical: Serrated tropical dorsal crest fin + fanned 3D leaf tail + 2 orchid buds
#    Cold:     Glacial layered shoulder armor plates + under-shell frost tufts + frost tail club
# ==============================================================================
def upgrade_dartback():
    orig_img = Image.open(SNAP / "textures/entity/dartback.png").convert("RGBA")
    rules = [
        # Protect bright glowing scarlet/pink dart tips & eyes!
        {"name": "glow_red", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 338, 14) and s >= 0.72 and v >= 0.75, "kind": "keep"},
        {"name": "eye_dark", "match": lambda r, g, b, h, s, v, info: v < 0.28, "kind": "keep"},
        {"name": "white_hl", "match": lambda r, g, b, h, s, v, info: s < 0.12 and v >= 0.85, "kind": "keep"},
        # Warm amber/terracotta armor plates (family 1: H 15..45)
        {"name": "amber", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 14, 44) and s >= 0.12,
         "kind": "shell", "dark_mul": 0.44, "light_mul": 1.28, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.88, "balance_mean": 0.90, "params": {"band_h": 3.5, "scale": 1.2, "crisp": 0.58, "macro_y": 0.52, "orig_weight": 0.34}},
        # Golden ochre trim (family 2: H 44..75)
        {"name": "ochre", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 44, 78) and s >= 0.12,
         "kind": "shell", "dark_mul": 0.46, "light_mul": 1.26, "cool_deg": 10, "warm_deg": 10, "steps": 9,
         "spread": 0.86, "balance_mean": 0.90, "params": {"band_h": 3.5, "scale": 1.2, "crisp": 0.58, "macro_y": 0.52, "orig_weight": 0.34}},
        # Rosy magenta carapace highlights (family 11: H 315..345)
        {"name": "magenta", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 315, 345) and s >= 0.12,
         "kind": "shell", "dark_mul": 0.45, "light_mul": 1.28, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.88, "balance_mean": 0.88, "params": {"band_h": 3.5, "scale": 1.2, "crisp": 0.58, "macro_y": 0.52, "orig_weight": 0.32}},
        # Plum / purple-slate under-armor (family 10: H 285..315)
        {"name": "plum", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 285, 315) and s >= 0.12,
         "kind": "skin", "dark_mul": 0.42, "light_mul": 1.48, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.90, "balance_mean": 0.90, "params": {"scale": 1.2, "crisp": 0.55, "macro_y": 0.55, "orig_weight": 0.32}},
        # Deep indigo/violet crevices (family 8/9: H 220..285)
        {"name": "indigo", "match": lambda r, g, b, h, s, v, info: True,
         "kind": "skin", "dark_mul": 0.44, "light_mul": 1.46, "cool_deg": 10, "warm_deg": 10, "steps": 9,
         "spread": 0.85, "balance_mean": 0.90, "params": {"scale": 1.2, "crisp": 0.55, "macro_y": 0.52, "orig_weight": 0.34}},
    ]
    base_img, owner, _ = mp.upgrade_mob_texture(orig_img, [GEO / "dartback.geo.json"], rules, seed=601)
    _save(base_img, "textures/entity/dartback.png")

    # Dartback base texel density is 4 px/unit; use 256x256 POT variant sheet so every new 3D part matches 4 px/unit 1:1!
    DENS = 4.0

    # ---- TROPICAL: Serrated horned-lizard dorsal crest fin + 3D leaf tail fan + 2 jungle orchid buds
    trop_packer = vp.UVPacker.from_base_model("dartback", target_size=(256, 256))
    tc = {}

    def build_dartback_trop(add, bones):
        # head bbox: x -3.6..3.6, y 1.95..10.25, z -11.35..-2.8; body: x -3.25..3.25, y 2..8, z -2.75..4.25
        add("head", [
            # Stepped serrated dorsal ridge fins crowning the head!
            vp.make_box(trop_packer, [-0.5, 8.52, -9.2], [1.0, 2.2, 2.2], "crest", density=DENS, pivot=[0, 8.52, -8.1], rotation=[-22, 0, 0], shared_cache=tc),
            vp.make_box(trop_packer, [-0.5, 8.52, -6.2], [1.0, 2.8, 2.4], "crest_tip", density=DENS, pivot=[0, 8.52, -5.0], rotation=[-26, 0, 0], shared_cache=tc),
            # Sleek tropical cheek frills flanking the jaw
            vp.make_box(trop_packer, [3.62, 4.2, -7.8], [0.8, 2.2, 3.2], "crest", density=DENS, pivot=[3.62, 5.3, -6.2], rotation=[0, 18, 16], shared_cache=tc),
            vp.make_box(trop_packer, [-4.42, 4.2, -7.8], [0.8, 2.2, 3.2], "crest", density=DENS, pivot=[-3.62, 5.3, -6.2], rotation=[0, -18, -16], shared_cache=tc),
        ])
        add("body", [
            # Flank crest blades + 2 tiny 3D jungle orchid buds tucked by the shoulders (NO giant egg stickers!)
            vp.make_box(trop_packer, [3.28, 6.2, -1.6], [1.0, 1.5, 2.0], "leaf", density=DENS, pivot=[3.28, 6.9, -0.6], rotation=[0, 0, 28], shared_cache=tc),
            vp.make_box(trop_packer, [3.85, 7.1, -1.1], [1.0, 1.0, 1.0], "petal", density=DENS, shared_cache=tc),
            vp.make_box(trop_packer, [-4.28, 6.2, 1.2], [1.0, 1.5, 2.0], "leaf", density=DENS, pivot=[-3.28, 6.9, 2.2], rotation=[0, 0, -28], shared_cache=tc),
            vp.make_box(trop_packer, [-4.85, 7.1, 1.7], [1.0, 1.0, 1.0], "petal", density=DENS, shared_cache=tc),
        ])
        add("tail_tip", [
            # 3D fanned tropical leaf tail blades radiating cleanly from tail_tip (0.75 * 4 = 3px exact 1:1 UV!)
            vp.make_box(trop_packer, [-0.8, 3.0, 9.12], [1.6, 0.75, 3.2], "leaf", density=DENS, pivot=[0, 3.35, 9.12], rotation=[14, 0, 0], shared_cache=tc),
            vp.make_box(trop_packer, [0.4, 3.1, 8.92], [1.5, 0.75, 2.75], "leaf", density=DENS, pivot=[0.5, 3.4, 8.92], rotation=[8, 32, 0], shared_cache=tc),
            vp.make_box(trop_packer, [-1.9, 3.1, 8.92], [1.5, 0.75, 2.75], "leaf", density=DENS, pivot=[-0.5, 3.4, 8.92], rotation=[8, -32, 0], shared_cache=tc),
        ])

    vp.build_variant("dartback", "tropical", build_dartback_trop, target_size=(256, 256))

    # ---- COLD: Glacial layered shoulder armor plates + under-shell frost fur tufts + armored frost tail club
    cold_packer = vp.UVPacker.from_base_model("dartback", target_size=(256, 256))
    cc = {}

    def build_dartback_cold(add, bones):
        add("body", [
            # Heavy glacial layered shoulder pauldrons flanking upper carapace
            vp.make_box(cold_packer, [3.28, 5.2, -2.5], [1.2, 3.2, 5.5], "ice", density=DENS, pivot=[3.28, 6.8, 0.25], rotation=[0, 0, -14], shared_cache=cc),
            vp.make_box(cold_packer, [-4.48, 5.2, -2.5], [1.2, 3.2, 5.5], "ice", density=DENS, pivot=[-3.28, 6.8, 0.25], rotation=[0, 0, 14], shared_cache=cc),
            # Fluffy frosty fur tufts overflowing from under the armor flanks (cleanly off body sides)
            vp.make_box(cold_packer, [3.30, 1.5, -2.0], [1.0, 2.2, 2.5], "ruff", density=DENS, shared_cache=cc),
            vp.make_box(cold_packer, [3.30, 1.6, 1.2], [1.0, 2.0, 2.5], "ruff_bright", density=DENS, shared_cache=cc),
            vp.make_box(cold_packer, [-4.30, 1.5, -2.0], [1.0, 2.2, 2.5], "ruff", density=DENS, shared_cache=cc),
            vp.make_box(cold_packer, [-4.30, 1.6, 1.2], [1.0, 2.0, 2.5], "ruff_bright", density=DENS, shared_cache=cc),
        ])
        add("head", [
            # Frosty glacier brow plate + cheek fur tufts
            vp.make_box(cold_packer, [-3.0, 8.54, -9.8], [6.0, 1.2, 4.5], "ice", density=DENS, shared_cache=cc),
            vp.make_box(cold_packer, [3.62, 1.8, -8.5], [1.0, 2.5, 4.0], "ruff", density=DENS, shared_cache=cc),
            vp.make_box(cold_packer, [-4.62, 1.8, -8.5], [1.0, 2.5, 4.0], "ruff", density=DENS, shared_cache=cc),
        ])
        add("tail_tip", [
            # Chunky armored glacial tail club cap
            vp.make_box(cold_packer, [-2.0, 2.1, 8.8], [4.0, 2.6, 2.2], "ice", density=DENS, shared_cache=cc),
            vp.make_box(cold_packer, [-1.2, 2.5, 11.02], [2.4, 1.8, 1.2], "ruff_bright", density=DENS, shared_cache=cc),
        ])

    vp.build_variant("dartback", "cold", build_dartback_cold, target_size=(256, 256))

    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {
        "trop_sat_default": 1.38, "trop_val_default": 1.04, "trop_hue_target": 26.0,
        "trop_hue_deg": {"amber": 10, "ochre": 10, "magenta": 12, "plum": 14, "indigo": 18},
    })
    trop_256 = _paste_to_pot(trop_base, (256, 256))
    mp.paint_packed_parts(trop_256, trop_packer, {
        "crest": [(148, 38, 52), (206, 74, 58), (242, 134, 72), (250, 198, 108)],
        "crest_tip": [(186, 56, 48), (236, 114, 58), (250, 186, 86), (252, 232, 142)],
        "leaf": [(28, 104, 72), (54, 152, 92), (98, 196, 116), (154, 226, 146)],
        "petal": [(196, 42, 108), (238, 92, 148), (252, 168, 198)],
    }, seed=602)
    _save(trop_256, "textures/entity/dartback_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {
        "cold_hue_target": 212.0,
        "cold_hue_deg": {"amber": 62, "ochre": 68, "magenta": 55, "plum": 42, "indigo": 26},
        "cold_sat_default": 0.78, "cold_veil": 0.28,
    })
    cold_256 = _paste_to_pot(cold_base, (256, 256))
    mp.paint_packed_parts(cold_256, cold_packer, {
        "ice": [(54, 102, 156), (92, 152, 206), (148, 202, 238), (208, 236, 250)],
        "ruff": [(126, 152, 188), (166, 192, 222), (206, 224, 242), (232, 240, 248)],
        "ruff_bright": [(164, 188, 220), (204, 222, 242), (234, 242, 250)],
    }, seed=603)
    _save(cold_256, "textures/entity/dartback_cold.png")

    mp.save_3d_comparison_sheet([
        ("dartback ORIGINAL", GEO / "dartback.geo.json", orig_img),
        ("dartback v2 UPGRADED", GEO / "dartback.geo.json", base_img),
        ("dartback TROPICAL v2 (Horned Crest + Leaf Tail, 1:1 UV)", GEO / "dartback_tropical.geo.json", trop_256),
        ("dartback COLD v2 (Frost Armor + Ruff + Tail Club, 1:1 UV)", GEO / "dartback_cold.geo.json", cold_256),
    ], ROOT / "build/batch2_dartback_3d.png", scale=7)


# ==============================================================================
# 3. FUSEFLY (Glowing lantern bug; 32x32 base -> 64x64 POT 1:1 UV variants)
#    Tropical: Lantern-blossom bell hood + feathered antennae + mini tropical wing-fins
#    Cold:     Rounded snow-moth thorax fur cape + feathered frost antennae + fuzzy abdomen tip
# ==============================================================================
def upgrade_fusefly():
    orig_img = Image.open(SNAP / "textures/entity/fusefly.png").convert("RGBA")
    rules = [
        # Protect tiny dark/neutral pixels (eyes/outline)
        {"name": "eye", "match": lambda r, g, b, h, s, v, info: s < 0.14 or v < 0.42, "kind": "keep"},
        # Emerald / mint head shield & cap (family 3..5: H 85..175)
        {"name": "cap", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 85, 175) and s >= 0.14,
         "kind": "plant", "dark_mul": 0.48, "light_mul": 1.32, "cool_deg": 12, "warm_deg": 12, "steps": 9,
         "spread": 0.78, "balance_mean": 0.80, "params": {"crisp": 0.45, "macro_y": 0.58, "orig_weight": 0.25}},
        # Golden yellow lantern highlights (family 2: H 45..75)
        {"name": "lantern_hi", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 45, 78) and s >= 0.14,
         "kind": "jelly", "dark_mul": 0.62, "light_mul": 1.04, "cool_deg": 8, "warm_deg": 6, "cool_sat": 1.24, "warm_sat": 0.88, "steps": 7,
         "spread": 0.94, "balance_mean": 0.72, "params": {"macro_y": 0.60, "orig_weight": 0.25}},
        # Warm amber lantern body (family 1: H 15..45)
        {"name": "lantern", "match": lambda r, g, b, h, s, v, info: True,
         "kind": "jelly", "dark_mul": 0.60, "light_mul": 1.04, "cool_deg": 8, "warm_deg": 6, "cool_sat": 1.24, "warm_sat": 0.88, "steps": 7,
         "spread": 0.96, "balance_mean": 0.72, "params": {"macro_y": 0.65, "orig_weight": 0.25}},
    ]
    base_img, owner, _ = mp.upgrade_mob_texture(
        orig_img, [GEO / "fusefly.geo.json", GEO / "fusefly_explode.geo.json"], rules, seed=701
    )
    _save(base_img, "textures/entity/fusefly.png")

    # ---- TROPICAL: Lantern-blossom bell hood + feathered antennae + mini angled wing-fins (64x64, 1:1 UV)
    trop_packer = vp.UVPacker.from_base_model("fusefly", target_size=(64, 64))
    tc = {}

    def build_fusefly_trop(add, bones):
        # head: x -2.1..2.1, y 11.55..15.55, z -2.1..2.0; body: x -3..3, y 3.5..11.5, z -3..3
        add("head", [
            # 3D lantern-blossom bell crown (base calyx + 4 angled overhanging petals + stamen)
            vp.make_box(trop_packer, [-2, 15.58, -2], [4, 1, 4], "leaf", shared_cache=tc),
            vp.make_box(trop_packer, [-2, 16.58, -3], [4, 1, 2], "petal", pivot=[0, 16.58, -2], rotation=[25, 0, 0], shared_cache=tc),
            vp.make_box(trop_packer, [-2, 16.58, 1], [4, 1, 2], "petal", pivot=[0, 16.58, 2], rotation=[-25, 0, 0], shared_cache=tc),
            vp.make_box(trop_packer, [-1, 16.60, -1], [2, 2, 2], "centre", shared_cache=tc),
            # Pair of graceful feathered tropical moth antennae
            vp.make_box(trop_packer, [-3, 15.6, -1], [1, 4, 1], "leaf", pivot=[-2, 15.6, -0.5], rotation=[16, 0, -28], shared_cache=tc),
            vp.make_box(trop_packer, [2, 15.6, -1], [1, 4, 1], "leaf", pivot=[2, 15.6, -0.5], rotation=[16, 0, 28], shared_cache=tc),
        ])
        add("body", [
            # Delicate angled translucent-style tropical wing-fins on the flanks
            vp.make_box(trop_packer, [3.04, 6.0, -1.0], [1, 4, 3], "petal", pivot=[3.04, 8.0, 0.5], rotation=[12, 22, 26], shared_cache=tc),
            vp.make_box(trop_packer, [-4.04, 6.0, -1.0], [1, 4, 3], "petal", pivot=[-3.04, 8.0, 0.5], rotation=[12, -22, -26], shared_cache=tc),
        ])

    vp.build_variant("fusefly", "tropical", build_fusefly_trop, target_size=(64, 64))

    # ---- COLD: Snow-moth rounded thorax fur cape + feathered frost antennae + fuzzy frost tail tip (64x64, 1:1 UV)
    cold_packer = vp.UVPacker.from_base_model("fusefly", target_size=(64, 64))
    cc = {}

    def build_fusefly_cold(add, bones):
        add("body", [
            # Staggered plush snow-moth collar bolsters wrapping upper thorax (zero Z-fighting!)
            vp.make_box(cold_packer, [-3.6, 9.2, -4.04], [7, 2, 1], "ruff_bright", shared_cache=cc),
            vp.make_box(cold_packer, [-3.6, 9.0, 3.04], [7, 2, 1], "ruff", shared_cache=cc),
            vp.make_box(cold_packer, [-4.06, 9.1, -3.0], [1, 2, 6], "ruff", shared_cache=cc),
            vp.make_box(cold_packer, [3.06, 9.1, -3.0], [1, 2, 6], "ruff", shared_cache=cc),
            # Cozy fuzzy abdomen tip on lower back
            vp.make_box(cold_packer, [-1.5, 4.5, 3.04], [3, 3, 2], "tail", shared_cache=cc),
        ])
        add("head", [
            # Sweeping feathered frost-moth antennae (replaces awkward bunny ears!)
            vp.make_box(cold_packer, [-2.5, 15.58, -0.5], [1, 3, 1], "ruff_bright", pivot=[-1.5, 15.58, 0], rotation=[-12, 0, -32], shared_cache=cc),
            vp.make_box(cold_packer, [1.5, 15.58, -0.5], [1, 3, 1], "ruff_bright", pivot=[1.5, 15.58, 0], rotation=[-12, 0, 32], shared_cache=cc),
        ])

    vp.build_variant("fusefly", "cold", build_fusefly_cold, target_size=(64, 64))

    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {
        "trop_sat_default": 1.48, "trop_val_default": 1.02, "trop_hue_target": 28.0,
        "trop_hue_deg": {"lantern": 10, "lantern_hi": 8, "cap": 14},
    })
    trop_64 = _paste_to_pot(trop_base, (64, 64))
    mp.paint_packed_parts(trop_64, trop_packer, {
        "petal": [(196, 52, 92), (238, 102, 134), (252, 168, 184), (252, 214, 222)],
        "centre": [(204, 148, 38), (246, 206, 72), (252, 242, 136)],
        "leaf": [(32, 108, 76), (62, 158, 102), (108, 202, 128)],
    }, seed=702)
    _save(trop_64, "textures/entity/fusefly_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {
        "cold_hue_target": 205.0,
        "cold_hue_deg": {"lantern": 56, "lantern_hi": 52, "cap": 38},
        "cold_sat_default": 0.78, "cold_veil": 0.34,
    })
    cold_64 = _paste_to_pot(cold_base, (64, 64))
    mp.paint_packed_parts(cold_64, cold_packer, {
        "ruff": [(132, 162, 202), (174, 200, 232), (212, 228, 246), (236, 244, 250)],
        "ruff_bright": [(168, 196, 228), (208, 226, 244), (238, 246, 250)],
        "tail": [(154, 184, 218), (198, 220, 242), (232, 242, 250)],
    }, seed=703)
    _save(cold_64, "textures/entity/fusefly_cold.png")

    mp.save_3d_comparison_sheet([
        ("fusefly ORIGINAL", GEO / "fusefly.geo.json", orig_img),
        ("fusefly v2 UPGRADED", GEO / "fusefly.geo.json", base_img),
        ("fusefly TROPICAL v2 (Blossom Lantern Moth, 1:1 UV)", GEO / "fusefly_tropical.geo.json", trop_64),
        ("fusefly COLD v2 (Snow Moth Cape + Antennae, 1:1 UV)", GEO / "fusefly_cold.geo.json", cold_64),
    ], ROOT / "build/batch2_fusefly_3d.png", scale=10)


# ==============================================================================
# 4. WOBBLE (Translucent jelly creature; 64x64 base -> 128x128 POT 1:1 UV variants)
#    Tropical: Double-tiered 3D water-lily lotus + curling lily leaves + glossy jelly bubbles
#    Cold:     Asymmetric 3D ice-crystal prism cluster + snout icicles + frosted foot ice chunks (NO fur!)
# ==============================================================================
def upgrade_wobble():
    orig_img = Image.open(SNAP / "textures/entity/wobble.png").convert("RGBA")
    rules = [
        # Protect eyes & mouth (dark warm/neutral)
        {"name": "face", "match": lambda r, g, b, h, s, v, info: v < 0.42 or s < 0.14 or mp.hue_in(h, 330, 45), "kind": "keep"},
        # Lime-mint bright inner glow (family 4: H 105..135)
        {"name": "lime", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 105, 135) and s >= 0.14,
         "kind": "jelly", "dark_mul": 0.56, "light_mul": 1.12, "cool_deg": 8, "warm_deg": 8, "steps": 9,
         "spread": 0.80, "balance_mean": 0.72, "params": {"crisp": 0.35, "macro_y": 0.50, "orig_weight": 0.25}},
        # Seafoam mid-jelly (family 5: H 135..165)
        {"name": "seafoam", "match": lambda r, g, b, h, s, v, info: mp.hue_in(h, 135, 165) and s >= 0.14,
         "kind": "jelly", "dark_mul": 0.46, "light_mul": 1.24, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.86, "balance_mean": 0.82, "params": {"crisp": 0.38, "macro_y": 0.52, "orig_weight": 0.22}},
        # Aqua-teal outer jelly membrane (family 6: H 165..205)
        {"name": "aqua", "match": lambda r, g, b, h, s, v, info: True,
         "kind": "jelly", "dark_mul": 0.44, "light_mul": 1.28, "cool_deg": 10, "warm_deg": 10, "steps": 10,
         "spread": 0.88, "balance_mean": 0.85, "params": {"crisp": 0.38, "macro_y": 0.55, "orig_weight": 0.22}},
    ]
    base_img, owner, _ = mp.upgrade_mob_texture(orig_img, [GEO / "wobble.geo.json"], rules, seed=801)
    _save(base_img, "textures/entity/wobble.png")

    # ---- TROPICAL: Water-Lily Anemone (double-tiered lotus cup + 2 curling lily leaves + 3 jelly dew bubbles)
    trop_packer = vp.UVPacker.from_base_model("wobble", target_size=(64, 64))
    tc = {}

    def build_wobble_trop(add, bones):
        # body: x -6.1..6.1, y 0..12, z -6.1..6.0
        add("body", [
            # Double-tiered 3D water-lily lotus blooming on crown (all coordinates Z-fighting-free!)
            vp.make_box(trop_packer, [-2, 12.04, -2], [4, 1, 4], "petal.outer", shared_cache=tc),
            vp.make_box(trop_packer, [-1, 13.06, -1], [2, 1, 2], "centre", shared_cache=tc),
            # 4 tilted cupped lotus petals around the golden centre
            vp.make_box(trop_packer, [-1.5, 12.5, -3.1], [3, 2, 1], "petal.inner", pivot=[0, 12.5, -2.1], rotation=[28, 0, 0], shared_cache=tc),
            vp.make_box(trop_packer, [-1.5, 12.5, 2.1], [3, 2, 1], "petal.inner", pivot=[0, 12.5, 2.1], rotation=[-28, 0, 0], shared_cache=tc),
            vp.make_box(trop_packer, [-3.1, 12.5, -1.5], [1, 2, 3], "petal.inner", pivot=[-2.1, 12.5, 0], rotation=[0, 0, -28], shared_cache=tc),
            vp.make_box(trop_packer, [2.1, 12.5, -1.5], [1, 2, 3], "petal.inner", pivot=[2.1, 12.5, 0], rotation=[0, 0, 28], shared_cache=tc),
            # 2 curling 3D lily leaves arching behind the lotus
            vp.make_box(trop_packer, [2.5, 12.04, 1.8], [2, 4, 1], "leaf", pivot=[3.5, 12.04, 2.3], rotation=[-18, -22, 24], shared_cache=tc),
            vp.make_box(trop_packer, [-4.5, 12.04, 2.2], [2, 3, 1], "leaf", pivot=[-3.5, 12.04, 2.7], rotation=[-15, 24, -22], shared_cache=tc),
            # 3 glossy translucent jelly dew-bubbles along flanks
            vp.make_box(trop_packer, [6.12, 5.2, -1.5], [1, 2, 2], "bubble", shared_cache=tc),
            vp.make_box(trop_packer, [6.12, 8.2, 2.0], [1, 1, 1], "bubble", shared_cache=tc),
            vp.make_box(trop_packer, [-7.12, 6.0, 0.8], [1, 2, 2], "bubble", shared_cache=tc),
        ])

    vp.build_variant("wobble", "tropical", build_wobble_trop, target_size=(64, 64))

    # ---- COLD: Ice-Crystal Jellyfish (asymmetric tilted 3D ice-crystal prisms + snout icicles + frost foot crystals!)
    cold_packer = vp.UVPacker.from_base_model("wobble", target_size=(64, 64))
    cc = {}

    def build_wobble_cold(add, bones):
        add("body", [
            # Asymmetric cluster of 4 tilted 3D ice-crystal prisms crowning the jelly dome!
            vp.make_box(cold_packer, [-1.5, 12.04, -1.0], [3, 5, 3], "ice", pivot=[0, 12.04, 0.5], rotation=[-10, 15, 8], shared_cache=cc),
            vp.make_box(cold_packer, [1.8, 12.04, -2.4], [2, 4, 2], "ice_bright", pivot=[2.8, 12.04, -1.4], rotation=[16, -20, 26], shared_cache=cc),
            vp.make_box(cold_packer, [-3.6, 12.04, 0.8], [2, 3, 2], "ice_bright", pivot=[-2.6, 12.04, 1.8], rotation=[-18, 22, -24], shared_cache=cc),
            vp.make_box(cold_packer, [0.4, 12.04, 2.4], [2, 3, 2], "ice", pivot=[1.4, 12.04, 3.4], rotation=[-28, -12, 10], shared_cache=cc),
            # Side crystal shards emerging from frozen jelly flanks
            vp.make_box(cold_packer, [6.12, 7.2, -1.2], [2, 3, 2], "ice", pivot=[6.12, 8.2, -0.2], rotation=[0, 0, -28], shared_cache=cc),
            vp.make_box(cold_packer, [-8.12, 6.8, 0.6], [2, 3, 2], "ice", pivot=[-6.12, 7.8, 1.6], rotation=[0, 0, 28], shared_cache=cc),
        ])
        add("snout", [
            # 3 varied-length icicle stalactites hanging cleanly under snout (snout y=5..13, z=-8..-2)
            vp.make_box(cold_packer, [-2.4, 2.96, -7.8], [1, 2, 1], "ice_bright", shared_cache=cc),
            vp.make_box(cold_packer, [-0.5, 1.96, -7.8], [1, 3, 1], "ice_bright", shared_cache=cc),
            vp.make_box(cold_packer, [1.4, 2.96, -7.8], [1, 2, 1], "ice", shared_cache=cc),
        ])
        add("left_foot", [
            vp.make_box(cold_packer, [-10.08, 4.02, -1.5], [2, 2, 2], "ice", pivot=[-9.08, 4.02, -0.5], rotation=[8, 0, -18], shared_cache=cc),
        ])
        add("right_foot", [
            vp.make_box(cold_packer, [8.08, 4.02, -1.5], [2, 2, 2], "ice", pivot=[9.08, 4.02, -0.5], rotation=[8, 0, 18], shared_cache=cc),
        ])

    vp.build_variant("wobble", "cold", build_wobble_cold, target_size=(64, 64))

    trop_base = mp.apply_climate_shift(base_img, owner, "tropical", {
        "trop_sat_default": 1.32, "trop_val_default": 1.04, "trop_hue_target": 152.0,
        "trop_hue_deg": {"aqua": 16, "seafoam": 12, "lime": 10},
    })
    mp.paint_packed_parts(trop_base, trop_packer, {
        "petal.outer": [(186, 56, 118), (232, 104, 158), (248, 168, 202), (252, 214, 232)],
        "petal.inner": [(208, 78, 134), (244, 138, 182), (252, 204, 224)],
        "centre": [(202, 152, 42), (246, 208, 78), (252, 240, 138)],
        "leaf": [(28, 104, 78), (52, 152, 104), (96, 198, 128), (146, 226, 156)],
        "bubble": [(48, 164, 156), (98, 214, 198), (168, 244, 232), (226, 250, 246)],
    }, seed=802)
    _save(trop_base, "textures/entity/wobble_tropical.png")

    cold_base = mp.apply_climate_shift(base_img, owner, "cold", {
        "cold_hue_target": 214.0,
        "cold_hue_deg": {"aqua": 32, "seafoam": 48, "lime": 56},
        "cold_sat_default": 0.96, "cold_veil": 0.22,
    })
    mp.paint_packed_parts(cold_base, cold_packer, {
        "ice": [(46, 108, 178), (82, 162, 222), (142, 210, 244), (208, 240, 250)],
        "ice_bright": [(78, 148, 212), (132, 202, 240), (194, 234, 250), (234, 248, 252)],
    }, seed=803)
    _save(cold_base, "textures/entity/wobble_cold.png")

    mp.save_3d_comparison_sheet([
        ("wobble ORIGINAL", GEO / "wobble.geo.json", orig_img),
        ("wobble v2 UPGRADED", GEO / "wobble.geo.json", base_img),
        ("wobble TROPICAL v2 (Water-Lily Anemone, 1:1 UV)", GEO / "wobble_tropical.geo.json", trop_base),
        ("wobble COLD v2 (Ice-Crystal Jellyfish, 1:1 UV)", GEO / "wobble_cold.geo.json", cold_base),
    ], ROOT / "build/batch2_wobble_3d.png", scale=7)


if __name__ == "__main__":
    upgrade_prickle()
    upgrade_dartback()
    upgrade_fusefly()
    upgrade_wobble()
    print("Batch 2 complete!")
