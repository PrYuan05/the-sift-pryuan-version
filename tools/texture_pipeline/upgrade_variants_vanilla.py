"""Rebuild all 11 climate-variant mobs (22 models & textures, keeping Nuzzle's approved 3D model untouched)
using authentic Vanilla Minecraft thin alpha-cutout planes (0.05 thick), X-crossed plant/crystal sprites,
and sleek Sheep-style outer fur shells (inflate 0.35..0.50 with shaggy alpha-cutout hems) — 100% 1:1 UV!

Usage: python -I tools/texture_pipeline/upgrade_variants_vanilla.py
"""
import json, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/pysift"
TEX = RES / "textures/entity"
GEO = RES / "geckolib/models/entity"

sys.path.insert(0, str(ROOT / "tools/texture_pipeline"))
sys.path.insert(0, str(ROOT / "tools/models"))
import mob_painter_v2 as mp  # noqa: E402
import variant_parts as vp   # noqa: E402


def _save(img, rel):
    p = RES / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p)
    print("wrote", rel, img.size)


def _paste_pot(img, target_size):
    if img.size == target_size:
        return img.copy()
    c = Image.new("RGBA", target_size, (0, 0, 0, 0))
    c.paste(img, (0, 0))
    return c


def _shift_base(mob, climate, cfg, protect_fn=None):
    """Shift an already-upgraded vibrant base texture for tropical/cold while protecting eyes/mouths/glow."""
    base = Image.open(TEX / f"{mob}.png").convert("RGBA")
    W, H = base.size
    px = base.load()
    owner = {}
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = mp.rgb_to_hsv((r, g, b))
            if protect_fn and protect_fn(r, g, b, h, s, v):
                continue
            owner[(x, y)] = "body"
    return base, mp.apply_climate_shift(base, owner, climate, cfg)


def _render_pair(mob, scale=7):
    base = Image.open(TEX / f"{mob}.png").convert("RGBA")
    trop = Image.open(TEX / f"{mob}_tropical.png").convert("RGBA")
    cold = Image.open(TEX / f"{mob}_cold.png").convert("RGBA")
    mp.save_3d_comparison_sheet([
        (f"{mob} BASE (Vibrant Crisp)", GEO / f"{mob}.geo.json", base),
        (f"{mob} TROPICAL (Vanilla Flat-Planes, 1:1 UV)", GEO / f"{mob}_tropical.geo.json", trop),
        (f"{mob} COLD (Vanilla Shell + Planes, 1:1 UV)", GEO / f"{mob}_cold.geo.json", cold),
    ], ROOT / f"build/vanilla_var_{mob}_3d.png", scale=scale)


# ------------------------------------------------------------------ 0. NUZZLE (Flat-plane / thin-shell Vanilla texture variants + sheared & fur maps!)
def rebuild_nuzzle():
    base = Image.open(TEX / "nuzzle.png").convert("RGBA")
    W, H = base.size
    bpx = base.load()
    owner = {}
    for y in range(H):
        for x in range(W):
            c = bpx[x, y]
            if c[3] == 0:
                continue
            h, s, v = mp.rgb_to_hsv(c[:3])
            if s < 0.08 and v < 0.35:
                continue
            if mp.hue_in(h, 335, 18) and s >= 0.40 and v >= 0.42:
                owner[(x, y)] = "fur"
            elif mp.hue_in(h, 95, 195) and s >= 0.14:
                owner[(x, y)] = "plant"
            else:
                owner[(x, y)] = "skin"

    # ---- TROPICAL: Mooshroom-style X-cross hibiscus flowers on back top ONLY (clean wool sides!)
    tp, tc = vp.UVPacker.from_base_model("nuzzle", (64, 64)), {}
    def b_trop(add, bones):
        add("body", (
            vp.make_cross(tp, -3.8, 20.0, 0.8, 5.0, 5.0, "flower", shared_cache=tc) +
            vp.make_cross(tp, 3.6, 20.0, 3.5, 4.5, 4.5, "flower_b", shared_cache=tc) +
            vp.make_cross(tp, 0.8, 20.0, -3.0, 4.0, 4.0, "flower_b", shared_cache=tc)
        ))
    vp.build_variant("nuzzle", "tropical", b_trop, (64, 64))

    trop_img = mp.apply_climate_shift(base, owner, "tropical", {
        "trop_sat": {"fur": 1.24, "skin": 1.16, "plant": 1.26},
        "trop_val": {"fur": 1.04, "plant": 1.05},
        "trop_hue_deg": {"fur": 10.0, "plant": 12.0},
    })
    mp.paint_vanilla_sprites(trop_img, tp, {
        "flower": {"shape": "flower_cross", "pal": [(212, 188, 166), (242, 226, 202), (252, 246, 230)], "accent": [(206, 146, 38), (252, 218, 86)]},
        "flower_b": {"shape": "flower_cross", "pal": [(212, 92, 82), (244, 144, 114), (252, 206, 166)], "accent": [(222, 168, 42), (252, 232, 110)]},
    }, seed=21)
    _save(trop_img, "textures/entity/nuzzle_tropical.png")

    # ---- COLD: Cozy fluffy winter fleece hood around head/shoulders + shaggy face framing + crossed snow tail + ankle cuffs!
    cp, cc = vp.UVPacker.from_base_model("nuzzle", (128, 64)), {}
    def b_cold(add, bones):
        add("body", [
            # Fluffy winter fleece hood wrapping top & sides of front head/shoulders (inflate 0.48, hugs silhouette cleanly!)
            vp.make_shell(cp, {"origin": [-8, 5, -8], "size": [16, 15, 7]}, 0.50, "hood", skip_faces=("north", "south", "down"), shared_cache=cc),
            # Shaggy face-framing frost ruff flush at front edge of the hood (z=-8.50, zero protruding fin cards!)
            vp.make_plane(cp, [-8.5, 15.8, -8.50], [17.0, 5.0, 0.05], "brow", shared_cache=cc),
            vp.make_plane(cp, [-8.5, 5.5, -8.50], [5.0, 11.0, 0.05], "cheek", shared_cache=cc),
            vp.make_plane(cp, [3.5, 5.5, -8.50], [5.0, 11.0, 0.05], "cheek", shared_cache=cc),
            vp.make_plane(cp, [-6.0, 4.4, -8.50], [12.0, 4.0, 0.05], "chin", shared_cache=cc),
            # Cute crossed flat-plane fluffy snow-rabbit tail at rear
            vp.make_plane(cp, [-2.5, 9.5, 10.12], [5.0, 5.0, 0.05], "tail", shared_cache=cc),
            vp.make_plane(cp, [-0.025, 9.5, 8.6], [0.05, 5.0, 4.0], "tail", shared_cache=cc),
        ])
        for leg in ("front_left_leg", "front_right_leg", "back_right_leg", "back_left_leg"):
            ox, oy, oz = bones[leg]["cubes"][0]["origin"]
            add(leg, [vp.make_shell(cp, {"origin": [ox, oy + 1.0, oz], "size": [4, 4, 4]}, 0.30, "cuff", skip_faces=("up", "down"), shared_cache=cc)])
    vp.build_variant("nuzzle", "cold", b_cold, (128, 64))

    cold_base = mp.apply_climate_shift(base, owner, "cold", {
        "cold_hue_target": 235.0,
        "cold_hue_deg": {"fur": 36.0, "skin": 24.0, "plant": 28.0},
        "cold_sat": {"fur": 0.72, "skin": 0.85, "plant": 0.82},
        "cold_veil": 0.22,
    })
    cold_img = _paste_pot(cold_base, (128, 64))
    mp.paint_vanilla_sprites(cold_img, cp, {
        "hood": {"shape": "shell_fur", "hem": 0.76, "pal": [(148, 114, 160), (200, 174, 210), (242, 232, 248)]},
        "brow": {"shape": "fringe_plane", "pal": [(156, 124, 168), (208, 184, 218), (244, 236, 250)]},
        "cheek": {"shape": "fringe_plane", "pal": [(144, 110, 156), (196, 170, 206), (238, 226, 244)]},
        "chin": {"shape": "fringe_plane", "pal": [(150, 118, 162), (202, 178, 212), (240, 230, 246)]},
        "tail": {"shape": "pinecone_cross", "pal": [(154, 126, 168), (206, 188, 216), (242, 236, 246)], "accent": [(228, 218, 236), (248, 244, 250)]},
        "cuff": {"shape": "shell_fur", "hem": 0.62, "pal": [(132, 98, 142), (180, 150, 188), (226, 210, 232)]},
    }, seed=22)
    _save(cold_img, "textures/entity/nuzzle_cold.png")

    # Regenerate matching _sheared.png, _dyed_base.png (tropical flowers preserved!), & _fur.png so shearing & dyeing stay 100% consistent!
    def write_sheared_and_fur(img, suffix, extra_packer=None, dye_extra=False, write_dyed_base=False):
        sheared = img.copy()
        spx = sheared.load()
        dyed_base = img.copy() if write_dyed_base else None
        dpx = dyed_base.load() if dyed_base is not None else None
        ipx = img.load()
        fur_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        fpx = fur_layer.load()

        skin_cols = sorted([ipx[x, y][:3] for (x, y), m in owner.items() if m == "skin"], key=mp.lum)
        skin_ramp = mp.build_gradient_ramp(skin_cols, steps=12, dark_mul=0.72, light_mul=1.22, cool_deg=10, warm_deg=10)
        fur_pts = [(x, y) for (x, y), m in owner.items() if m == "fur"]
        flums = [mp.lum(ipx[x, y][:3]) for x, y in fur_pts]
        flo, fhi = min(flums), max(flums)
        for (x, y) in fur_pts:
            t = (mp.lum(ipx[x, y][:3]) - flo) / max(1e-5, fhi - flo)
            skin_c = (*mp.sample_ramp(skin_ramp, 0.25 + 0.55 * t), 255)
            spx[x, y] = skin_c
            if dpx is not None:
                dpx[x, y] = skin_c
            g = 0.48 + 0.50 * t
            fpx[x, y] = (int(round(252 * g)), int(round(250 * g)), int(round(246 * g)), 255)
        if extra_packer is not None:
            for _, x0, y0, w, h, _, _ in extra_packer.rects:
                for yy in range(y0, y0 + h):
                    for xx in range(x0, x0 + w):
                        if ipx[xx, yy][3] > 0:
                            if dye_extra:
                                # Cold extra wool fur (hood/fringe/tail/cuffs) vanishes when sheared & dyes with the wool!
                                spx[xx, yy] = (0, 0, 0, 0)
                                t = max(0.0, min(1.0, (mp.lum(ipx[xx, yy][:3]) - flo) / max(1e-5, fhi - flo)))
                                g = 0.54 + 0.45 * t
                                fpx[xx, yy] = (int(round(252 * g)), int(round(252 * g)), int(round(255 * g)), 255)
                            else:
                                # Tropical flowers vanish when sheared, stay vibrant on dyed_base, transparent on _fur!
                                spx[xx, yy] = (0, 0, 0, 0)
        _save(sheared, f"textures/entity/nuzzle{suffix}_sheared.png")
        if dyed_base is not None:
            _save(dyed_base, f"textures/entity/nuzzle{suffix}_dyed_base.png")
        _save(fur_layer, f"textures/entity/nuzzle{suffix}_fur.png")

    write_sheared_and_fur(trop_img, "_tropical", extra_packer=tp, dye_extra=False, write_dyed_base=True)
    write_sheared_and_fur(cold_img, "_cold", extra_packer=cp, dye_extra=True, write_dyed_base=False)
    _render_pair("nuzzle", scale=9)


# ------------------------------------------------------------------ 1. LOOTKIN (Restored 3D Fennec+Cactus / Arctic Fox models on crisp vibrant base!)
def rebuild_lootkin():
    prot = lambda r, g, b, h, s, v: v < 0.54 or (mp.hue_in(h, 335, 14) and s >= 0.36 and v >= 0.56)
    _, tbase = _shift_base("lootkin", "tropical", {"trop_sat_default": 1.65, "trop_val_default": 1.02, "trop_hue_target": 32.0}, prot)
    _, cbase = _shift_base("lootkin", "cold", {"cold_hue_target": 212.0, "cold_hue_deg": {"body": 40}, "cold_sat_default": 0.96, "cold_veil": 0.25}, prot)

    # ---- TROPICAL 3D: Desert Fennec Ears + Multi-Tier Cactus Flower Crown + Trailing Succulent Leaves & Bud (64x64 POT, 1:1 UV)
    tp, tc = vp.UVPacker.from_base_model("lootkin", (64, 64)), {}
    def b_trop(add, bones):
        add("body", [
            vp.make_box(tp, [-7, 7, -6], [3, 4, 1], "ear", pivot=[-4.5, 8, -5.5], rotation=[0, 12, -24], shared_cache=tc),
            vp.make_box(tp, [4, 7, -6], [3, 4, 1], "ear", pivot=[4.5, 8, -5.5], rotation=[0, -12, 24], shared_cache=tc),
            vp.make_box(tp, [-8, 9, -6], [2, 2, 1], "ear_tip", pivot=[-4.5, 8, -5.5], rotation=[0, 12, -24], shared_cache=tc),
            vp.make_box(tp, [6, 9, -6], [2, 2, 1], "ear_tip", pivot=[4.5, 8, -5.5], rotation=[0, -12, 24], shared_cache=tc),
        ])
        add("crest", [
            vp.make_box(tp, [-2, 19, -9], [4, 1, 4], "petal.outer", shared_cache=tc),
            vp.make_box(tp, [-1, 20, -8], [2, 1, 2], "petal.inner", shared_cache=tc),
            vp.make_box(tp, [-1, 21, -8], [2, 1, 2], "centre", shared_cache=tc),
            vp.make_box(tp, [1, 15, -8], [3, 1, 2], "leaf", pivot=[1, 15.5, -7], rotation=[0, 0, 22], shared_cache=tc),
            vp.make_box(tp, [-4, 14, -8], [3, 1, 2], "leaf", pivot=[-1, 14.5, -7], rotation=[0, 0, -22], shared_cache=tc),
        ])
        add("sack", [
            vp.make_box(tp, [-3, 8, 2], [3, 1, 2], "leaf", pivot=[-1.5, 8, 3], rotation=[14, 12, -10], shared_cache=tc),
            vp.make_box(tp, [0, 8, 3], [3, 1, 2], "leaf", pivot=[1.5, 8, 4], rotation=[-12, -18, 12], shared_cache=tc),
            vp.make_box(tp, [-1, 8, 2], [2, 2, 2], "petal.bud", shared_cache=tc),
        ])
    vp.build_variant("lootkin", "tropical", b_trop, (64, 64))
    t64 = _paste_pot(tbase, (64, 64))
    mp.paint_packed_parts(t64, tp, {
        "ear": [(176, 128, 108), (218, 174, 148), (242, 212, 186), (248, 232, 210)],
        "ear_tip": [(196, 118, 96), (234, 158, 122), (248, 198, 154)],
        "petal.outer": [(178, 48, 112), (222, 86, 148), (246, 148, 188), (252, 196, 218)],
        "petal.inner": [(210, 74, 124), (244, 132, 168), (252, 186, 206)],
        "petal.bud": [(208, 94, 52), (242, 148, 76), (252, 206, 126)],
        "centre": [(198, 142, 46), (242, 198, 78), (252, 236, 134)],
        "leaf": [(42, 98, 78), (68, 142, 102), (112, 184, 126), (156, 214, 148)],
    }, seed=304)
    _save(t64, "textures/entity/lootkin_tropical.png")

    # ---- COLD 3D: Arctic Fox Layered Ruff + Rounded Winter Ear Tufts + Big Bushy Sweeping Tail + 6 Ankle Cuffs (64x64 POT, 1:1 UV)
    cp, cc = vp.UVPacker.from_base_model("lootkin", (64, 64)), {}
    LEGS = {"left_front_leg": (-3, -3), "right_front_leg": (1, -3), "left_middle_leg": (-3, 0),
            "right_middle_leg": (1, 0), "left_back_leg": (-3, 3), "right_back_leg": (1, 3)}
    def b_cold(add, bones):
        add("body", [
            vp.make_box(cp, [-6.06, 4, -7.08], [2, 5, 3], "ruff", shared_cache=cc),
            vp.make_box(cp, [4.06, 4, -7.08], [2, 5, 3], "ruff", shared_cache=cc),
            vp.make_box(cp, [-5, 3.06, -8.04], [10, 2, 2], "ruff", shared_cache=cc),
            vp.make_box(cp, [-3, 2.02, -8.10], [6, 1, 2], "ruff_bright", shared_cache=cc),
            vp.make_box(cp, [-5, 10.02, -5], [2, 2, 2], "ruff_bright", shared_cache=cc),
            vp.make_box(cp, [3, 10.02, -5], [2, 2, 2], "ruff_bright", shared_cache=cc),
        ])
        add("sack", [
            vp.make_box(cp, [-2, 3, 6], [4, 4, 5], "tail", pivot=[0, 5, 6], rotation=[20, 0, 0], shared_cache=cc),
            vp.make_box(cp, [-1.5, 4.5, 10], [3, 3, 3], "tail_tip", pivot=[0, 5, 6], rotation=[20, 0, 0], shared_cache=cc),
        ])
        for leg, (x, z) in LEGS.items():
            add(leg, [vp.make_box(cp, [x - 0.5, 1, z - 0.5], [3, 2, 3], "cuff", shared_cache=cc)])
    vp.build_variant("lootkin", "cold", b_cold, (64, 64))
    c64 = _paste_pot(cbase, (64, 64))
    mp.paint_packed_parts(c64, cp, {
        "ruff": [(122, 146, 184), (160, 184, 214), (198, 216, 236), (228, 238, 248)],
        "ruff_bright": [(146, 170, 206), (188, 208, 232), (224, 236, 248), (242, 246, 250)],
        "tail": [(118, 142, 180), (158, 182, 214), (198, 216, 236), (228, 238, 246)],
        "tail_tip": [(176, 198, 224), (214, 228, 242), (240, 245, 250)],
        "cuff": [(114, 138, 176), (154, 178, 210), (194, 212, 234), (224, 234, 246)],
    }, seed=305)
    _save(c64, "textures/entity/lootkin_cold.png")
    _render_pair("lootkin", scale=9)


# ------------------------------------------------------------------ 2. PRICKLE
def rebuild_prickle():
    prot = lambda r, g, b, h, s, v: v < 0.45
    _, tbase = _shift_base("prickle", "tropical", {"trop_sat_default": 1.65, "trop_hue_target": 340.0, "trop_hue_deg": {"body": 42}}, prot)
    _, cbase = _shift_base("prickle", "cold", {"cold_hue_target": 210.0, "cold_hue_deg": {"body": 40}, "cold_veil": 0.24}, prot)

    tp, tc = vp.UVPacker.from_base_model("prickle", (64, 64)), {}
    def b_trop(add, bones):
        # Fanned porcupine quill planes + 2 X-cross desert succulent flowers!
        add("body", [
            vp.make_plane(tp, [-3.0, 6.8, -1.5], [6.0, 4.0, 0.05], "quill", pivot=[0, 6.8, -1.5], rotation=[-38, 0, 0], shared_cache=tc),
            vp.make_plane(tp, [-3.0, 6.8, 2.0], [6.0, 4.0, 0.05], "quill", pivot=[0, 6.8, 2.0], rotation=[-44, 0, 0], shared_cache=tc),
            vp.make_plane(tp, [3.52, 2.5, -2.5], [0.05, 4.0, 7.0], "quill", pivot=[3.52, 4.5, 1.0], rotation=[0, 0, 32], shared_cache=tc),
            vp.make_plane(tp, [-3.57, 2.5, -2.5], [0.05, 4.0, 7.0], "quill", pivot=[-3.52, 4.5, 1.0], rotation=[0, 0, -32], shared_cache=tc),
        ] + vp.make_cross(tp, -1.6, 7.0, -2.8, 4.0, 4.0, "flower", shared_cache=tc)
          + vp.make_cross(tp, 1.6, 7.0, 3.2, 4.0, 4.0, "flower", yaw=20, shared_cache=tc))
    vp.build_variant("prickle", "tropical", b_trop, (64, 64))
    t64 = _paste_pot(tbase, (64, 64))
    mp.paint_vanilla_sprites(t64, tp, {
        "quill": {"shape": "quill_plane", "pal": [(154, 48, 102), (212, 86, 138), (246, 148, 166)], "accent": [(232, 142, 74), (252, 210, 128)]},
        "flower": {"shape": "flower_cross", "pal": [(204, 52, 108), (246, 118, 158), (252, 192, 214)], "accent": [(214, 162, 42), (252, 232, 114)]},
    }, seed=21)
    _save(t64, "textures/entity/prickle_tropical.png")

    cp, cc = vp.UVPacker.from_base_model("prickle", (64, 64)), {}
    def b_cold(add, bones):
        # Sleek snowy outer wool mantle + 2 X-cross glacial ice crystal spires + brow fur fringe!
        add("body", [
            vp.make_shell(cp, bones["body"]["cubes"][0], 0.42, "coat", skip_faces=("down",), shared_cache=cc),
            vp.make_plane(cp, [-3.6, 4.2, -5.72], [7.0, 3.0, 0.05], "fringe", shared_cache=cc),
        ] + vp.make_cross(cp, 0.0, 7.3, -1.2, 4.0, 4.0, "crystal", shared_cache=cc)
          + vp.make_cross(cp, 0.0, 7.3, 2.5, 4.0, 5.0, "crystal", yaw=25, shared_cache=cc))
    vp.build_variant("prickle", "cold", b_cold, (64, 64))
    c64 = _paste_pot(cbase, (64, 64))
    mp.paint_vanilla_sprites(c64, cp, {
        "coat": {"shape": "shell_fur", "hem": 0.68, "pal": [(134, 162, 204), (186, 208, 236), (236, 244, 250)]},
        "fringe": {"shape": "fringe_plane", "pal": [(154, 182, 218), (206, 224, 244), (242, 248, 252)]},
        "crystal": {"shape": "crystal_cross", "pal": [(46, 112, 182), (96, 174, 228), (174, 226, 248), (232, 248, 252)]},
    }, seed=22)
    _save(c64, "textures/entity/prickle_cold.png")
    _render_pair("prickle", scale=10)


# ------------------------------------------------------------------ 3. DARTBACK (density=4.0, 256x256)
def rebuild_dartback():
    # Per-material climate recoloring for Dartback so ZERO clashing hue jumps occur (no mint-green feet on cold,
    # no neon-clashing hues on tropical, unified head+body frost coat on cold!)
    base = Image.open(TEX / "dartback.png").convert("RGBA")
    W, H = base.size
    bpx = base.load()

    # Build harmonious TROPICAL base (cohesive warm sunset-rose carapace + golden-amber feet, gentle saturation boost!)
    tbase = base.copy()
    tpx = tbase.load()
    # Build harmonious COLD base (cohesive glacier-indigo carapace + cool slate-cream feet — NO lime/mint green! —
    # and softly frosted rose-berry spines so nothing screams neon red!)
    cbase = base.copy()
    cpx = cbase.load()
    for y in range(H):
        for x in range(W):
            r, g, b, a = bpx[x, y]
            if a == 0:
                continue
            h, s, v = mp.rgb_to_hsv((r, g, b))
            if v < 0.26 or (s < 0.12 and v >= 0.85):
                continue  # protect dark eyes & crisp white teeth/highlights
            is_dart = mp.hue_in(h, 338, 14) and s >= 0.72 and v >= 0.75
            is_feet = mp.hue_in(h, 15, 75) and s >= 0.15

            # --- Tropical: unified warm sunset-plum & rich amber-gold ---
            if not is_dart:
                if is_feet:
                    h2 = mp.shift_towards(h, 32.0, 6.0)
                    s2 = min(0.76, s * 1.18)
                    v2 = min(0.92, v * 1.04)
                else:
                    # Carapace purple/magenta shifts gently toward warm sunset rose-berry
                    h2 = mp.shift_towards(h, 338.0, 14.0)
                    s2 = min(0.74, s * 1.18)
                    v2 = min(0.92, v * 1.03)
                tpx[x, y] = (*mp.hsv_to_rgb(h2, s2, v2), a)

            # --- Cold: unified glacial indigo-slate & frosty pearl-slate feet (NO green!) ---
            if is_dart:
                # Cool the scarlet dart dots gently to frosted crystal-violet/cool berry so they harmonize with ice!
                h2 = mp.shift_towards(h, 245.0, 48.0)
                cpx[x, y] = (*mp.hsv_to_rgb(h2, s * 0.62, min(0.92, v * 0.96)), a)
            elif is_feet:
                # Directly re-hue warm amber feet to cool frost-slate/icy-grey (avoids passing through yellow-green!)
                h2 = 216.0
                s2 = min(0.24, max(0.12, s * 0.36))
                v2 = min(0.88, v * 0.98)
                cpx[x, y] = (*mp.hsv_to_rgb(h2, s2, v2), a)
            else:
                # Carapace shifts smoothly from plum-magenta to cohesive glacier-periwinkle/slate-blue
                h2 = mp.shift_towards(h, 224.0, 56.0)
                s2 = max(0.18, min(0.46, s * 0.80))
                v2 = min(0.86, v * 1.02)
                rr, gg, bb = mp.hsv_to_rgb(h2, s2, v2)
                cpx[x, y] = (int(rr * 0.88 + 150 * 0.12), int(gg * 0.88 + 186 * 0.12), int(bb * 0.88 + 230 * 0.12), a)

    D = 4.0

    # ---- TROPICAL: Planted X-cross tropical flowers on head & back (NO straight fin strip!) + sleek leaf tail
    tp, tc = vp.UVPacker.from_base_model("dartback", (256, 256)), {}
    def b_trop(add, bones):
        add("head", vp.make_cross(tp, -1.5, 8.5, -8.8, 2.75, 2.75, "flower", density=D, yaw=35, shared_cache=tc)
            + vp.make_cross(tp, 1.6, 8.5, -5.8, 2.5, 2.5, "flower_b", density=D, yaw=15, shared_cache=tc))
        add("body", vp.make_cross(tp, 2.0, 8.0, 0.2, 2.5, 2.5, "flower", density=D, yaw=50, shared_cache=tc)
            + vp.make_cross(tp, -1.8, 8.0, 2.4, 2.5, 2.5, "flower_b", density=D, yaw=20, shared_cache=tc))
        add("tail_tip", [
            vp.make_plane(tp, [-2.25, 3.4, 9.0], [4.5, 0.05, 3.5], "tail_leaf", density=D, pivot=[0, 3.4, 9.0], rotation=[14, 0, 0], shared_cache=tc),
        ])
    vp.build_variant("dartback", "tropical", b_trop, (256, 256))
    t256 = _paste_pot(tbase, (256, 256))
    mp.paint_vanilla_sprites(t256, tp, {
        "flower": {"shape": "flower_cross", "pal": [(186, 62, 98), (232, 114, 126), (250, 178, 168)], "accent": [(214, 158, 56), (250, 220, 124)], "stem": [(42, 96, 74), (72, 138, 96)]},
        "flower_b": {"shape": "flower_cross", "pal": [(208, 92, 62), (242, 146, 82), (252, 206, 128)], "accent": [(196, 64, 92), (246, 134, 146)], "stem": [(42, 96, 74), (72, 138, 96)]},
        "tail_leaf": {"shape": "leaf_plane", "pal": [(42, 92, 74), (66, 132, 96), (104, 172, 118)]},
    }, seed=31)
    _save(t256, "textures/entity/dartback_tropical.png")

    # ---- COLD: Unified head (including front brow!) + body frosted slate-blue outer mantle + soft frost fringe + subtle ice crest
    cp, cc = vp.UVPacker.from_base_model("dartback", (256, 256)), {}
    def b_cold(add, bones):
        add("body", [
            vp.make_shell(cp, bones["body"]["cubes"][0], 0.34, "coat", skip_faces=("down",), density=D, shared_cache=cc),
            vp.make_plane(cp, [3.55, 1.0, -2.5], [0.05, 2.0, 6.5], "fringe", density=D, shared_cache=cc),
            vp.make_plane(cp, [-3.60, 1.0, -2.5], [0.05, 2.0, 6.5], "fringe", density=D, shared_cache=cc),
        ])
        add("head", [
            # Full upper head ice/frost cover INCLUDING the front brow (`north` face, safely above mouth/eyes!)
            vp.make_shell(cp, bones["head"]["cubes"][0], 0.34, "coat", skip_faces=("down",), density=D, shared_cache=cc),
            vp.make_plane(cp, [3.65, 1.1, -10.5], [0.05, 2.0, 7.5], "fringe", density=D, shared_cache=cc),
            vp.make_plane(cp, [-3.70, 1.1, -10.5], [0.05, 2.0, 7.5], "fringe", density=D, shared_cache=cc),
        ] + vp.make_cross(cp, 0.0, 8.8, -7.2, 2.5, 2.5, "crystal", density=D, shared_cache=cc))
        add("tail_tip", vp.make_cross(cp, 0.0, 4.2, 8.6, 2.25, 2.25, "crystal", density=D, shared_cache=cc))
    vp.build_variant("dartback", "cold", b_cold, (256, 256))
    c256 = _paste_pot(cbase, (256, 256))
    mp.paint_vanilla_sprites(c256, cp, {
        # Harmonized glacier-indigo root -> soft frost-blue top (blends organically with the carapace!)
        "coat": {"shape": "shell_fur", "hem": 0.50, "pal": [(96, 118, 162), (138, 164, 206), (186, 208, 236)]},
        "fringe": {"shape": "fringe_plane", "pal": [(108, 132, 174), (154, 178, 214), (200, 218, 240)]},
        "crystal": {"shape": "crystal_cross", "pal": [(66, 118, 178), (118, 174, 222), (182, 220, 244)]},
    }, seed=32)
    _save(c256, "textures/entity/dartback_cold.png")
    _render_pair("dartback", scale=7)


# ------------------------------------------------------------------ 4. FUSEFLY
def rebuild_fusefly():
    prot = lambda r, g, b, h, s, v: s < 0.14 or v < 0.42
    _, tbase = _shift_base("fusefly", "tropical", {"trop_sat_default": 1.48, "trop_val_default": 1.02, "trop_hue_target": 28.0}, prot)
    _, cbase = _shift_base("fusefly", "cold", {"cold_hue_target": 205.0, "cold_hue_deg": {"body": 52}, "cold_sat_default": 0.78, "cold_veil": 0.34}, prot)

    tp, tc = vp.UVPacker.from_base_model("fusefly", (64, 64)), {}
    def b_trop(add, bones):
        # X-cross tropical lantern blossom + curved feathered antennae planes + scalloped butterfly wing planes!
        add("head", vp.make_cross(tp, 0.0, 15.55, 0.0, 5.0, 4.0, "flower", shared_cache=tc) + [
            vp.make_plane(tp, [-4.0, 15.2, -0.5], [3.0, 4.0, 0.05], "ant", pivot=[-1.5, 15.5, -0.5], rotation=[16, 0, -24], shared_cache=tc),
            vp.make_plane(tp, [1.0, 15.2, -0.5], [3.0, 4.0, 0.05], "ant", pivot=[1.5, 15.5, -0.5], rotation=[16, 0, 24], shared_cache=tc),
        ])
        add("body", [
            vp.make_plane(tp, [3.02, 5.5, 0.5], [4.0, 6.0, 0.05], "wing", pivot=[3.02, 8.5, 0.5], rotation=[0, -28, 0], shared_cache=tc),
            vp.make_plane(tp, [-7.02, 5.5, 0.5], [4.0, 6.0, 0.05], "wing", pivot=[-3.02, 8.5, 0.5], rotation=[0, 28, 0], shared_cache=tc),
        ])
    vp.build_variant("fusefly", "tropical", b_trop, (64, 64))
    t64 = _paste_pot(tbase, (64, 64))
    mp.paint_vanilla_sprites(t64, tp, {
        "flower": {"shape": "flower_cross", "pal": [(198, 52, 96), (244, 112, 146), (252, 188, 206)], "accent": [(214, 162, 40), (252, 236, 122)]},
        "ant": {"shape": "antenna_plane", "pal": [(34, 112, 76), (72, 172, 106), (132, 222, 142)]},
        "wing": {"shape": "wing_plane", "pal": [(212, 72, 108), (248, 138, 162), (252, 206, 212)], "accent": [(244, 178, 68), (252, 230, 134)]},
    }, seed=41)
    _save(t64, "textures/entity/fusefly_tropical.png")

    cp, cc = vp.UVPacker.from_base_model("fusefly", (64, 64)), {}
    def b_cold(add, bones):
        # Sleek fluffy snow-moth upper-thorax fur collar shell + feathered frost moth antennae planes + pale moth wing planes!
        add("body", [
            vp.make_shell(cp, bones["body"]["cubes"][0], 0.42, "coat", skip_faces=("down",), shared_cache=cc),
            vp.make_plane(cp, [3.04, 6.2, 0.5], [4.0, 5.0, 0.05], "wing", pivot=[3.04, 8.7, 0.5], rotation=[0, -24, 0], shared_cache=cc),
            vp.make_plane(cp, [-7.04, 6.2, 0.5], [4.0, 5.0, 0.05], "wing", pivot=[-3.04, 8.7, 0.5], rotation=[0, 24, 0], shared_cache=cc),
        ])
        add("head", [
            vp.make_plane(cp, [-3.8, 15.3, -0.5], [3.0, 4.0, 0.05], "ant", pivot=[-1.2, 15.5, -0.5], rotation=[12, 0, -26], shared_cache=cc),
            vp.make_plane(cp, [0.8, 15.3, -0.5], [3.0, 4.0, 0.05], "ant", pivot=[1.2, 15.5, -0.5], rotation=[12, 0, 26], shared_cache=cc),
        ])
    vp.build_variant("fusefly", "cold", b_cold, (64, 64))
    c64 = _paste_pot(cbase, (64, 64))
    mp.paint_vanilla_sprites(c64, cp, {
        "coat": {"shape": "shell_fur", "hem": 0.36, "pal": [(142, 174, 214), (196, 218, 242), (240, 246, 252)]},
        "ant": {"shape": "antenna_plane", "pal": [(156, 188, 224), (210, 228, 246), (244, 248, 252)]},
        "wing": {"shape": "wing_plane", "pal": [(138, 174, 214), (192, 218, 242), (234, 244, 252)], "accent": [(96, 146, 198), (156, 202, 238)]},
    }, seed=42)
    _save(c64, "textures/entity/fusefly_cold.png")
    _render_pair("fusefly", scale=10)


# ------------------------------------------------------------------ 5. WOBBLE
def rebuild_wobble():
    prot = lambda r, g, b, h, s, v: v < 0.42 or s < 0.14 or mp.hue_in(h, 330, 45)
    _, tbase = _shift_base("wobble", "tropical", {"trop_sat_default": 1.32, "trop_val_default": 1.04, "trop_hue_target": 152.0, "trop_hue_deg": {"body": 14}}, prot)
    _, cbase = _shift_base("wobble", "cold", {"cold_hue_target": 214.0, "cold_hue_deg": {"body": 42}, "cold_veil": 0.22}, prot)

    tp, tc = vp.UVPacker.from_base_model("wobble", (64, 64)), {}
    def b_trop(add, bones):
        # Classic X-cross pink water-lily lotus + 2 curved lily leaf planes + tiny side coral fins!
        add("body", vp.make_cross(tp, 0.0, 12.0, 0.5, 6.0, 5.0, "lotus", shared_cache=tc) + [
            vp.make_plane(tp, [2.0, 12.0, 2.0], [4.0, 5.0, 0.05], "leaf", pivot=[3.0, 12.0, 2.0], rotation=[-22, -24, 24], shared_cache=tc),
            vp.make_plane(tp, [-6.0, 12.0, 2.0], [4.0, 5.0, 0.05], "leaf", pivot=[-3.0, 12.0, 2.0], rotation=[-22, 24, -24], shared_cache=tc),
        ])
    vp.build_variant("wobble", "tropical", b_trop, (64, 64))
    mp.paint_vanilla_sprites(tbase, tp, {
        "lotus": {"shape": "flower_cross", "pal": [(192, 54, 118), (242, 118, 168), (252, 198, 224)], "accent": [(214, 164, 42), (252, 236, 124)]},
        "leaf": {"shape": "leaf_plane", "pal": [(26, 102, 74), (56, 156, 102), (108, 206, 132)]},
    }, seed=51)
    _save(tbase, "textures/entity/wobble_tropical.png")

    cp, cc = vp.UVPacker.from_base_model("wobble", (64, 64)), {}
    def b_cold(add, bones):
        # 3 varied-height X-cross faceted ice-crystal spires + jagged hanging icicle plane under snout!
        add("body", vp.make_cross(cp, 0.0, 12.0, 0.5, 5.0, 6.0, "crystal", shared_cache=cc)
            + vp.make_cross(cp, 2.8, 12.0, -1.6, 3.0, 4.0, "crystal", yaw=20, pitch=14, shared_cache=cc)
            + vp.make_cross(cp, -2.8, 12.0, 2.0, 3.0, 4.0, "crystal", yaw=70, pitch=-14, shared_cache=cc))
        add("snout", [
            vp.make_plane(cp, [-2.5, 2.0, -7.85], [5.0, 3.0, 0.05], "icicle", shared_cache=cc),
        ])
    vp.build_variant("wobble", "cold", b_cold, (64, 64))
    mp.paint_vanilla_sprites(cbase, cp, {
        "crystal": {"shape": "crystal_cross", "pal": [(44, 108, 178), (92, 172, 226), (172, 226, 248), (234, 248, 252)]},
        "icicle": {"shape": "icicle_plane", "pal": [(62, 132, 202), (126, 196, 238), (208, 240, 252)]},
    }, seed=52)
    _save(cbase, "textures/entity/wobble_cold.png")
    _render_pair("wobble", scale=7)


# ------------------------------------------------------------------ 6. SLABBER
def rebuild_slabber():
    prot = lambda r, g, b, h, s, v: (s < 0.08 and v >= 0.85) or v < 0.16
    _, tbase = _shift_base("slabber", "tropical", {"trop_sat_default": 1.38, "trop_val_default": 1.05, "trop_hue_target": 136.0, "trop_hue_deg": {"body": 14}}, prot)
    _, cbase = _shift_base("slabber", "cold", {"cold_hue_target": 216.0, "cold_hue_deg": {"body": 38}, "cold_sat_default": 0.85, "cold_veil": 0.24}, prot)

    tp, tc = vp.UVPacker.from_base_model("slabber", (128, 128)), {}
    def b_trop(add, bones):
        # Keep the center flowerbed (flower_1..5: (0,1), (-6,-5), (6,6), (-6,7), (6,-6)) 100% CLEAR for player-planted flowers!
        # Frame the outer rim & flanks with lush draping jungle vines & angled back-corner fern fronds!
        add("body", [
            vp.make_plane(tp, [11.08, 14.0, -6.0], [0.05, 10.0, 5.0], "vine", shared_cache=tc),
            vp.make_plane(tp, [11.08, 15.0, 3.0], [0.05, 9.0, 5.0], "vine", shared_cache=tc),
            vp.make_plane(tp, [-11.13, 14.0, -4.0], [0.05, 10.0, 5.0], "vine", shared_cache=tc),
            vp.make_plane(tp, [-11.13, 15.0, 5.0], [0.05, 9.0, 5.0], "vine", shared_cache=tc),
            vp.make_plane(tp, [-4.0, 15.0, 13.08], [6.0, 9.0, 0.05], "vine", shared_cache=tc),
            # Perimeter tropical fern fronds arching outward at far rear corners (well clear of flower_1..5!)
            vp.make_plane(tp, [9.5, 25.5, 9.5], [6.0, 0.05, 5.0], "fern_leaf", pivot=[10.0, 25.5, 11.5], rotation=[-18, -22, 26], shared_cache=tc),
            vp.make_plane(tp, [-15.5, 25.5, 9.5], [6.0, 0.05, 5.0], "fern_leaf", pivot=[-10.0, 25.5, 11.5], rotation=[-18, 22, -26], shared_cache=tc),
        ])
    vp.build_variant("slabber", "tropical", b_trop, (128, 128))
    mp.paint_vanilla_sprites(tbase, tp, {
        "fern_leaf": {"shape": "leaf_plane", "pal": [(22, 98, 56), (48, 152, 78), (98, 204, 108), (154, 232, 142)]},
        "vine": {"shape": "vine_plane", "pal": [(24, 92, 56), (52, 148, 82), (102, 198, 112)], "accent": [(212, 68, 128), (252, 164, 198)]},
    }, seed=61)
    _save(tbase, "textures/entity/slabber_tropical.png")

    cp, cc = vp.UVPacker.from_base_model("slabber", (128, 128)), {}
    def b_cold(add, bones):
        # Sleek Highland frost-fur outer mantle on body (inflate=0.38 so flower_1..5 sprout cleanly through!)
        # PLUS matching icy frost & wispy ice-mist cover across the ENTIRE head crown & brow (above eyes at y=15..17)!
        add("body", [
            vp.make_shell(cp, bones["body"]["cubes"][0], 0.38, "coat", skip_faces=("down",), shared_cache=cc),
        ])
        add("head", [
            # Frost & ice-mist outer cap covering head top, brow, and upper cheeks (hem=0.52 stops cleanly above eyes!)
            vp.make_shell(cp, bones["head"]["cubes"][0], 0.42, "head_mist", skip_faces=("down",), shared_cache=cc),
            # Delicate wispy ice-mist crystal crest floating/rising subtly off head crown (y=27.4)
            vp.make_plane(cp, [-5.0, 27.4, -12.5], [10.0, 3.0, 0.05], "mist_wisp", pivot=[0, 27.4, -12.5], rotation=[-16, 0, 0], shared_cache=cc),
            vp.make_plane(cp, [-4.0, 27.4, -8.5], [8.0, 3.0, 0.05], "mist_wisp", pivot=[0, 27.4, -8.5], rotation=[-22, 0, 0], shared_cache=cc),
        ])
    vp.build_variant("slabber", "cold", b_cold, (128, 128))
    mp.paint_vanilla_sprites(cbase, cp, {
        "coat": {"shape": "shell_fur", "hem": 0.60, "pal": [(96, 126, 164), (146, 176, 212), (202, 222, 242), (234, 244, 250)]},
        "head_mist": {"shape": "shell_fur", "hem": 0.48, "pal": [(118, 152, 194), (172, 202, 232), (218, 236, 248), (240, 248, 252)]},
        "mist_wisp": {"shape": "fin_plane", "pal": [(126, 176, 222), (182, 220, 246), (228, 244, 252)], "accent": [(208, 238, 252), (242, 250, 252)]},
    }, seed=62)
    _save(cbase, "textures/entity/slabber_cold.png")
    _render_pair("slabber", scale=5)


# ------------------------------------------------------------------ 7-11. NESTER, POLLINATOR, SEEDLING, SPROUT, SENTINEL
def rebuild_split_5():
    prot = lambda r, g, b, h, s, v: v < 0.42 or (s < 0.08 and v >= 0.72)

    # 7. NESTER (dens=2.0)
    _, tb = _shift_base("nester", "tropical", {"trop_sat_default": 1.38, "trop_hue_target": 152.0, "trop_hue_deg": {"body": 18}}, prot)
    _, cb = _shift_base("nester", "cold", {"cold_hue_target": 216.0, "cold_hue_deg": {"body": 38}, "cold_veil": 0.25}, prot)
    tp, tc = vp.UVPacker.from_base_model("nester", (128, 128)), {}
    vp.build_variant("nester", "tropical", lambda add, bones: add("head", [
        vp.make_plane(tp, [-2.5, 17.3, -1.0], [3.0, 5.0, 0.05], "plume", density=2.0, pivot=[-1.0, 17.3, -1.0], rotation=[-18, 0, -24], shared_cache=tc),
        vp.make_plane(tp, [-0.5, 17.3, -1.0], [3.0, 5.0, 0.05], "plume", density=2.0, pivot=[1.0, 17.3, -1.0], rotation=[-18, 0, 24], shared_cache=tc),
    ] + vp.make_cross(tp, 1.5, 17.3, -1.8, 3.0, 3.0, "flower", density=2.0, shared_cache=tc)), (128, 128))
    mp.paint_vanilla_sprites(tb, tp, {
        "plume": {"shape": "plume_plane", "pal": [(34, 128, 114), (72, 192, 158)], "accent": [(212, 74, 96), (252, 184, 134)]},
        "flower": {"shape": "flower_cross", "pal": [(208, 56, 108), (248, 124, 158)], "accent": [(220, 172, 44), (252, 236, 128)]},
    }, seed=71)
    _save(tb, "textures/entity/nester_tropical.png")

    cp, cc = vp.UVPacker.from_base_model("nester", (128, 128)), {}
    vp.build_variant("nester", "cold", lambda add, bones: add("body", [
        vp.make_shell(cp, bones["body"]["cubes"][0], 0.42, "coat", skip_faces=("down",), density=2.0, shared_cache=cc),
    ]) or add("head", [
        vp.make_shell(cp, bones["head"]["cubes"][0], 0.36, "coat", skip_faces=("down", "north"), density=2.0, shared_cache=cc),
    ]), (128, 128))
    mp.paint_vanilla_sprites(cb, cp, {
        "coat": {"shape": "shell_fur", "hem": 0.60, "pal": [(132, 162, 202), (186, 210, 238), (236, 244, 250)]},
    }, seed=72)
    _save(cb, "textures/entity/nester_cold.png")
    _render_pair("nester", scale=7)

    # 8. POLLINATOR (dens=1.0)
    _, tb = _shift_base("pollinator", "tropical", {"trop_sat_default": 1.38, "trop_hue_target": 36.0, "trop_hue_deg": {"body": 14}}, prot)
    _, cb = _shift_base("pollinator", "cold", {"cold_hue_target": 212.0, "cold_hue_deg": {"body": 42}, "cold_veil": 0.26}, prot)
    tp, tc = vp.UVPacker.from_base_model("pollinator", (128, 128)), {}
    vp.build_variant("pollinator", "tropical", lambda add, bones: (
        add("head", vp.make_cross(tp, 0.0, 23.05, 0.0, 8.0, 6.0, "flower", shared_cache=tc)),
        add("body", [
            vp.make_plane(tp, [6.08, 7.0, -3.0], [0.05, 7.0, 6.0], "wing", pivot=[6.08, 10.5, 0.0], rotation=[0, 0, 18], shared_cache=tc),
            vp.make_plane(tp, [-6.13, 7.0, -3.0], [0.05, 7.0, 6.0], "wing", pivot=[-6.08, 10.5, 0.0], rotation=[0, 0, -18], shared_cache=tc),
        ]),
    ), (128, 128))
    mp.paint_vanilla_sprites(tb, tp, {
        "flower": {"shape": "flower_cross", "pal": [(196, 52, 114), (242, 112, 158), (252, 192, 214)], "accent": [(214, 164, 42), (252, 236, 124)]},
        "wing": {"shape": "wing_plane", "pal": [(212, 146, 36), (248, 198, 68), (252, 236, 134)], "accent": [(198, 76, 118), (246, 144, 174)]},
    }, seed=81)
    _save(tb, "textures/entity/pollinator_tropical.png")

    cp, cc = vp.UVPacker.from_base_model("pollinator", (128, 128)), {}
    vp.build_variant("pollinator", "cold", lambda add, bones: (
        add("body", [vp.make_shell(cp, bones["body"]["cubes"][0], 0.45, "coat", skip_faces=("down",), shared_cache=cc)]),
        add("head", [
            vp.make_plane(cp, [-5.0, 23.05, -2.5], [4.0, 5.0, 0.05], "ant", pivot=[-3.0, 23.05, -2.5], rotation=[16, 0, -20], shared_cache=cc),
            vp.make_plane(cp, [1.0, 23.05, -2.5], [4.0, 5.0, 0.05], "ant", pivot=[3.0, 23.05, -2.5], rotation=[16, 0, 20], shared_cache=cc),
        ]),
    ), (128, 128))
    mp.paint_vanilla_sprites(cb, cp, {
        "coat": {"shape": "shell_fur", "hem": 0.65, "pal": [(118, 148, 192), (174, 202, 234), (232, 242, 250)]},
        "ant": {"shape": "antenna_plane", "pal": [(154, 184, 222), (208, 228, 246), (244, 248, 252)]},
    }, seed=82)
    _save(cb, "textures/entity/pollinator_cold.png")
    _render_pair("pollinator", scale=6)

    # 9. SEEDLING (dens=1.0)
    _, tb = _shift_base("seedling", "tropical", {"trop_sat_default": 1.38, "trop_hue_target": 136.0, "trop_hue_deg": {"body": 18}}, prot)
    _, cb = _shift_base("seedling", "cold", {"cold_hue_target": 212.0, "cold_hue_deg": {"body": 42}, "cold_veil": 0.25}, prot)
    tp, tc = vp.UVPacker.from_base_model("seedling", (128, 128)), {}
    vp.build_variant("seedling", "tropical", lambda add, bones: add("upper_jaw", vp.make_cross(tp, 0.0, 12.0, 0.0, 6.0, 6.0, "flower", shared_cache=tc) + [
        vp.make_plane(tp, [2.0, 12.0, -3.0], [6.0, 0.05, 6.0], "leaf", pivot=[2.0, 12.0, 0.0], rotation=[0, 0, -28], shared_cache=tc),
        vp.make_plane(tp, [-8.0, 12.0, -3.0], [6.0, 0.05, 6.0], "leaf", pivot=[-2.0, 12.0, 0.0], rotation=[0, 0, 28], shared_cache=tc),
    ]), (128, 128))
    mp.paint_vanilla_sprites(tb, tp, {
        "flower": {"shape": "flower_cross", "pal": [(204, 54, 108), (246, 118, 158), (252, 192, 212)], "accent": [(218, 168, 42), (252, 238, 128)]},
        "leaf": {"shape": "leaf_plane", "pal": [(28, 106, 68), (58, 162, 94), (112, 214, 124)]},
    }, seed=91)
    _save(tb, "textures/entity/seedling_tropical.png")

    cp, cc = vp.UVPacker.from_base_model("seedling", (128, 128)), {}
    vp.build_variant("seedling", "cold", lambda add, bones: (
        add("upper_jaw", vp.make_cross(cp, 0.0, 12.0, 0.0, 6.0, 6.0, "cone", shared_cache=cc)),
        add("body", [vp.make_shell(cp, bones["body"]["cubes"][0], 0.42, "coat", skip_faces=("down",), shared_cache=cc)]),
    ), (128, 128))
    mp.paint_vanilla_sprites(cb, cp, {
        "cone": {"shape": "pinecone_cross", "pal": [(74, 98, 134), (122, 148, 184), (176, 198, 224)], "accent": [(206, 226, 246), (242, 248, 252)]},
        "coat": {"shape": "shell_fur", "hem": 0.68, "pal": [(132, 162, 202), (186, 210, 238), (236, 244, 250)]},
    }, seed=92)
    _save(cb, "textures/entity/seedling_cold.png")
    _render_pair("seedling", scale=7)

    # 10. SPROUT (dens=2.0) — protect bright sky-blue eye ring!
    prot_sp = lambda r, g, b, h, s, v: (mp.hue_in(h, 192, 214) and s >= 0.38 and v >= 0.48) or (s < 0.08 and v >= 0.72) or v < 0.22
    _, tb = _shift_base("sprout", "tropical", {"trop_sat_default": 1.65, "trop_hue_target": 320.0, "trop_hue_deg": {"body": 48}}, prot_sp)
    _, cb = _shift_base("sprout", "cold", {"cold_hue_target": 208.0, "cold_hue_deg": {"body": 28}, "cold_veil": 0.24}, prot_sp)
    tp, tc = vp.UVPacker.from_base_model("sprout", (128, 128)), {}
    vp.build_variant("sprout", "tropical", lambda add, bones: add("head", vp.make_cross(tp, 0.0, 24.45, 0.0, 6.0, 5.0, "coral", density=2.0, shared_cache=tc) + [
        vp.make_plane(tp, [4.05, 13.5, -2.5], [0.05, 4.0, 5.0], "vine", density=2.0, shared_cache=tc),
        vp.make_plane(tp, [-4.10, 13.5, -2.5], [0.05, 4.0, 5.0], "vine", density=2.0, shared_cache=tc),
    ]), (128, 128))
    mp.paint_vanilla_sprites(tb, tp, {
        "coral": {"shape": "coral_cross", "pal": [(192, 52, 98), (238, 102, 136)], "accent": [(244, 152, 82), (252, 216, 134)]},
        "vine": {"shape": "vine_plane", "pal": [(198, 68, 114), (242, 128, 156)], "accent": [(248, 184, 96), (252, 228, 148)]},
    }, seed=101)
    _save(tb, "textures/entity/sprout_tropical.png")

    cp, cc = vp.UVPacker.from_base_model("sprout", (128, 128)), {}
    vp.build_variant("sprout", "cold", lambda add, bones: add("head", vp.make_cross(cp, 0.0, 24.45, 0.0, 6.0, 5.5, "crystal", density=2.0, shared_cache=cc) + [
        vp.make_plane(cp, [-3.5, 13.4, -4.05], [7.0, 3.0, 0.05], "icicle", density=2.0, shared_cache=cc),
        vp.make_plane(cp, [-3.5, 13.4, 4.05], [7.0, 3.0, 0.05], "icicle", density=2.0, shared_cache=cc),
    ]), (128, 128))
    mp.paint_vanilla_sprites(cb, cp, {
        "crystal": {"shape": "crystal_cross", "pal": [(46, 110, 180), (96, 174, 228), (176, 228, 248), (234, 248, 252)]},
        "icicle": {"shape": "icicle_plane", "pal": [(64, 134, 204), (132, 198, 238), (212, 242, 252)]},
    }, seed=102)
    _save(cb, "textures/entity/sprout_cold.png")
    _render_pair("sprout", scale=6)

    # 11. SENTINEL (dens=2.0)
    _, tb = _shift_base("sentinel", "tropical", {"trop_sat_default": 1.35, "trop_hue_target": 152.0, "trop_hue_deg": {"body": 34}}, prot)
    _, cb = _shift_base("sentinel", "cold", {"cold_hue_target": 212.0, "cold_hue_deg": {"body": 24}, "cold_veil": 0.24}, prot)
    tp, tc = vp.UVPacker.from_base_model("sentinel", (128, 128)), {}
    vp.build_variant("sentinel", "tropical", lambda add, bones: (
        add("head", vp.make_cross(tp, 0.0, 14.0, 0.0, 5.0, 4.5, "flower", density=2.0, shared_cache=tc) + [
            vp.make_plane(tp, [2.0, 14.0, -2.0], [4.5, 0.05, 4.0], "leaf", density=2.0, pivot=[2.0, 14.0, 0.0], rotation=[0, 0, 22], shared_cache=tc),
            vp.make_plane(tp, [-6.5, 14.0, -2.0], [4.5, 0.05, 4.0], "leaf", density=2.0, pivot=[-2.0, 14.0, 0.0], rotation=[0, 0, -22], shared_cache=tc),
        ]),
        add("crest", [
            vp.make_plane(tp, [3.0, 7.2, -4.2], [2.5, 3.8, 0.05], "vine", density=2.0, shared_cache=tc),
            vp.make_plane(tp, [-5.5, 7.2, 3.5], [2.5, 3.8, 0.05], "vine", density=2.0, shared_cache=tc),
        ]),
    ), (128, 128))
    mp.paint_vanilla_sprites(tb, tp, {
        "flower": {"shape": "flower_cross", "pal": [(204, 56, 108), (246, 120, 158)], "accent": [(218, 168, 44), (252, 236, 128)]},
        "leaf": {"shape": "leaf_plane", "pal": [(26, 104, 66), (56, 158, 92), (108, 208, 118)]},
        "vine": {"shape": "vine_plane", "pal": [(24, 94, 60), (54, 148, 86)], "accent": [(214, 68, 122), (252, 166, 196)]},
    }, seed=111)
    _save(tb, "textures/entity/sentinel_tropical.png")

    cp, cc = vp.UVPacker.from_base_model("sentinel", (128, 128)), {}
    vp.build_variant("sentinel", "cold", lambda add, bones: (
        add("head", [vp.make_shell(cp, bones["head"]["cubes"][0], 0.36, "coat", skip_faces=("down",), density=2.0, shared_cache=cc)]),
        add("crest", [
            vp.make_plane(cp, [-4.0, 8.2, -4.3], [8.0, 2.8, 0.05], "icicle", density=2.0, shared_cache=cc),
            vp.make_plane(cp, [-4.0, 8.2, 4.3], [8.0, 2.8, 0.05], "icicle", density=2.0, shared_cache=cc),
        ]),
    ), (128, 128))
    mp.paint_vanilla_sprites(cb, cp, {
        "coat": {"shape": "shell_fur", "hem": 0.44, "pal": [(152, 184, 222), (206, 226, 246), (242, 248, 252)]},
        "icicle": {"shape": "icicle_plane", "pal": [(62, 132, 202), (128, 198, 238), (212, 242, 252)]},
    }, seed=112)
    _save(cb, "textures/entity/sentinel_cold.png")
    _render_pair("sentinel", scale=7)


if __name__ == "__main__":
    rebuild_lootkin()
    rebuild_prickle()
    rebuild_dartback()
    rebuild_fusefly()
    rebuild_wobble()
    rebuild_slabber()
    rebuild_split_5()
    print("All 11 vanilla flat-plane/shell climate variants rebuilt!")
