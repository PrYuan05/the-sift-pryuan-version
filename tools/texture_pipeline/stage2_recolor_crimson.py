"""Stage 2: Recolor the crimson/rose/ember textures in related_crimson_capped_crimson_strata_2.md
to match the user-edited soft rose-pink ground tops (canyon_top_a..d, grove_top..b) while
strictly preserving every original texture's pixel shapes and light/dark shading (深淺).

Usage:
  python -I tools/texture_pipeline/stage2_recolor_crimson.py --apply
"""
import sys, json, math, shutil, datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import project_paths, lj, wj, res_path, sha1, lab, lab_to_rgb, lum

P, RES, A, D = project_paths(".")
ASSETS = RES / "assets"
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "recolor_manifest.json"


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_hex(c):
    return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"


def lerp_rgb(c1, c2, t):
    return tuple(max(0, min(255, round(a + (b - a) * t))) for a, b in zip(c1, c2))


# ==============================================================================
# 1. Exact color mapping table preserving original light/dark shading (深淺)
#    and matching the user's edited canyon_top / grove_top soft rose-pink (#e86973 ~ #fc909c)
# ==============================================================================
# Target soft rose-pink reference (from user-edited canyon_top_b / grove_top):
#   Darkest shade: #e86974 (L=61.3)
#   Mid-dark:      #ed6f7c (L=63.2)
#   Median shade:  #f27683 ~ #f47a87 (L=65.8 ~ 66.4)
#   Light shade:   #f9828f ~ #fa8591 (L=68.8 ~ 69.4)

EXACT_COLOR_MAP = {
    # --- A. Bright Crimson Cap / Vein / Ember family (ember_stone_heat0_a, heat2_a, spread4, void_01_top, caps) ---
    # 3-shade crimson cap (#994257 < #a64656 < #b04954) -> preserves exact 3-step light/dark shading
    hx("#994257"): hx("#e86975"),
    hx("#a64656"): hx("#f27683"),
    hx("#b04954"): hx("#fa8390"),
    # 3-shade ember_stone_heat2_a cap (#b74d60 < #b55758 < #b46057) -> preserves exact 3-step light/dark shading
    hx("#b74d60"): hx("#ed6f7b"),
    hx("#b55758"): hx("#f47a87"),
    hx("#b46057"): hx("#fa8591"),

    # --- B. Dusty-Rose Strata family (crimson_strata_a, crimson_strata_d, lower body of crimson_strata_b & dark_slate_b/c) ---
    # Preserves the exact original pixel-by-pixel light/dark shading and sits slightly deeper than the top cap
    # so crimson_capped_crimson_strata keeps its distinct cap-to-strata layering.
    hx("#705656"): hx("#ba5f6b"),
    hx("#785e5e"): hx("#c46773"),
    hx("#856969"): hx("#d2737f"),
    hx("#8e726a"): hx("#dc7c86"),
    hx("#9a826f"): hx("#e88991"),

    hx("#75696a"): hx("#c06571"),
    hx("#77686a"): hx("#c26672"),
    hx("#77696a"): hx("#c36773"),
    hx("#78686a"): hx("#c46773"),
    hx("#7a686a"): hx("#c76975"),
    hx("#816a6b"): hx("#cf6f7b"),
    hx("#8a6c68"): hx("#d87580"),
    hx("#8d6c67"): hx("#db7782"),
    hx("#a36270"): hx("#e67481"),  # cap-to-body transition pixel on crimson_strata_b / c / gray_strata_a

    # --- C. Deep Crimson Strata family (crimson_strata_j, k, l, m, n) ---
    # Preserves the exact 3-step light/dark shading (#542e2e < #7b4343 < #9c5555) in the new soft rose-pink hue
    hx("#542e2e"): hx("#ba5563"),
    hx("#5e3333"): hx("#c45b69"),
    hx("#7b4343"): hx("#df6b79"),
    hx("#7f4545"): hx("#e36e7c"),
    hx("#9c5555"): hx("#f57c89"),
    hx("#9d5555"): hx("#f67d8a"),

    # --- D. Transition / anti-aliased border pixels on composite textures ---
    # 1. crimson_strata_i (transition between crimson cap #a64656->#f27683 and silted_strata_silt1 #557c85)
    hx("#7d5a6a"): lerp_rgb(hx("#557c85"), hx("#e86975"), 0.52),
    hx("#825c6c"): lerp_rgb(hx("#557c85"), hx("#ed6f7b"), 0.56),
    hx("#835464"): lerp_rgb(hx("#547981"), hx("#e86975"), 0.62),
    hx("#855c69"): lerp_rgb(hx("#557c85"), hx("#f27683"), 0.60),
    hx("#8a5663"): lerp_rgb(hx("#547981"), hx("#f27683"), 0.68),
    hx("#8a5d67"): lerp_rgb(hx("#557c85"), hx("#f27683"), 0.65),
    hx("#8a5f6b"): lerp_rgb(hx("#61828a"), hx("#f27683"), 0.63),
    hx("#8b5e68"): lerp_rgb(hx("#557c85"), hx("#f47a87"), 0.66),
    hx("#8f606a"): lerp_rgb(hx("#61828a"), hx("#f47a87"), 0.68),
    hx("#905862"): lerp_rgb(hx("#547981"), hx("#f9828f"), 0.72),

    # 2. crimson_strata_e, g & rose_capped_crimson_strata_top (transition between crimson and teal #42787b)
    hx("#796168"): lerp_rgb(hx("#42787b"), hx("#f27683"), 0.52),
    hx("#796067"): lerp_rgb(hx("#42787b"), hx("#f27683"), 0.52),

    # 3. crimson_vein_stone_crimson_spread1..3 (transition between purple-slate #5a4f64 and crimson #f27683)
    hx("#7d495b"): lerp_rgb(hx("#5a4f64"), hx("#f27683"), 0.50),

    # 4. ember_stone_heat1..3 (transition between warm amber #b57c4d and soft rose-pink #f27683)
    hx("#b36350"): lerp_rgb(hx("#b57c4d"), hx("#f27683"), 0.52),

    # 5. crimson_capped_void_01_side (smooth gradient from top cap #e86975..#fa8390 into dark void #3d2f41)
    hx("#783d4c"): lerp_rgb(hx("#3d2f41"), hx("#f27683"), 0.62),
    hx("#763c4a"): lerp_rgb(hx("#3d2f41"), hx("#f27683"), 0.58),
    hx("#6e3947"): lerp_rgb(hx("#3d2f41"), hx("#e86975"), 0.52),
    hx("#6a374a"): lerp_rgb(hx("#3d2f41"), hx("#e86975"), 0.46),
    hx("#5c3849"): lerp_rgb(hx("#3d2f41"), hx("#e86975"), 0.34),
    hx("#593546"): lerp_rgb(hx("#3d2f41"), hx("#e86975"), 0.28),
    hx("#523240"): lerp_rgb(hx("#3d2f41"), hx("#e86975"), 0.20),
    hx("#523144"): lerp_rgb(hx("#403245"), hx("#e86975"), 0.18),
}

# For crimson_strata_c and gray_strata_a, #816a6b and #8d6c67 sit between the cap (#f47a87) and teal (#42787b)
CAP_TEAL_TRANSITION_MAP = {
    hx("#816a6b"): lerp_rgb(hx("#42787b"), hx("#f47a87"), 0.48),
    hx("#8d6c67"): lerp_rgb(hx("#42787b"), hx("#f47a87"), 0.56),
    hx("#a36270"): lerp_rgb(hx("#42787b"), hx("#f47a87"), 0.74),
}

TARGET_TEXTURES = [
    ("ember_stone", "textures/block/ember_stone/ember_stone_heat0_a.png", "pysift:block/sift_ground/canyon_top_b"),
    ("ember_stone", "textures/block/ember_stone/ember_stone_heat1_a.png", "pysift:block/sift_ground/canyon_top_b"),
    ("ember_stone", "textures/block/ember_stone/ember_stone_heat2_a.png", "pysift:block/sift_ground/grove_top"),
    ("ember_stone", "textures/block/ember_stone/ember_stone_heat2_b.png", "pysift:block/sift_ground/canyon_top_b"),
    ("ember_stone", "textures/block/ember_stone/ember_stone_heat3_a.png", "pysift:block/sift_ground/canyon_top_b"),
    ("ember_stone", "textures/block/ember_stone/ember_stone_heat3_b.png", "pysift:block/sift_ground/grove_top"),
    ("crimson_vein_stone", "textures/block/crimson_vein_stone/crimson_vein_stone_crimson_spread1_a.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_vein_stone", "textures/block/crimson_vein_stone/crimson_vein_stone_crimson_spread1_b.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_vein_stone", "textures/block/crimson_vein_stone/crimson_vein_stone_crimson_spread2.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_vein_stone", "textures/block/crimson_vein_stone/crimson_vein_stone_crimson_spread3.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_vein_stone", "textures/block/crimson_vein_stone/crimson_vein_stone_crimson_spread4.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_a.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_b.png", "pysift:block/sift_ground/grove_top"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_c.png", "pysift:block/sift_ground/grove_top"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_d.png", "pysift:block/sift_ground/grove_top"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_e.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_f.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_g.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_h.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_i.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_j.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_k.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_l.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_m.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata/crimson_strata_n.png", "pysift:block/sift_ground/canyon_top_b"),
    ("capped_crimson_strata", "textures/block/capped_crimson_strata/capped_crimson_strata_rose_top.png", "pysift:block/sift_ground/canyon_top_b"),
    ("rose_capped_crimson_strata", "textures/block/rose_capped_crimson_strata/rose_capped_crimson_strata_top.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_capped_void_01", "textures/block/crimson_capped_void_01/crimson_capped_void_01_top.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_capped_void_01", "textures/block/crimson_capped_void_01/crimson_capped_void_01_side.png", "pysift:block/sift_ground/canyon_top_b"),
    ("gray_strata", "textures/block/gray_strata/gray_strata_a.png", "pysift:block/sift_ground/grove_top"),
    ("dark_slate", "textures/block/dark_slate/dark_slate_b.png", "pysift:block/sift_ground/grove_top"),
    ("dark_slate", "textures/block/dark_slate/dark_slate_c.png", "pysift:block/sift_ground/grove_top"),
    ("crimson_strata", "textures/block/crimson_strata_bricks/crimson_strata_bricks.png", "pysift:block/sift_ground/canyon_top_b"),
    ("crimson_strata", "textures/block/crimson_strata_bricks/chiseled_crimson_strata_bricks.png", "pysift:block/sift_ground/canyon_top_b"),
    ("ember_stone", "textures/block/ember_stone_bricks/ember_stone_bricks.png", "pysift:block/sift_ground/canyon_top_b"),
    ("ember_stone", "textures/block/ember_stone_bricks/chiseled_ember_stone_bricks.png", "pysift:block/sift_ground/canyon_top_b"),
]


def recolor_image(im, rel_path):
    """Recolor crimson/rose pixels while keeping 100% of original pixel shapes and relative light/dark depth."""
    rgba = im.convert("RGBA")
    px = list(rgba.get_flattened_data())
    is_cap_teal = rel_path.endswith(("crimson_strata_c.png", "gray_strata_a.png"))
    is_brick = "_bricks" in rel_path

    if is_brick:
        # For generated brick/chiseled textures of crimson_strata and ember_stone, shift Lab hue/chroma
        # and lightness offset while preserving exact mortar/highlight shading depth
        ref_im = Image.open(A / "textures/block/sift_ground/canyon_top_b.png").convert("RGB")
        ref_labs = [lab(c) for c in ref_im.get_flattened_data()]
        rL = sum(l[0] for l in ref_labs) / len(ref_labs)
        ra = sum(l[1] for l in ref_labs) / len(ref_labs)
        rb = sum(l[2] for l in ref_labs) / len(ref_labs)
        if "crimson_strata_bricks" in rel_path:
            # Match crimson_strata_a (#d2737f, L=58.2, a=38.8, b=11.0)
            rL, ra, rb = 58.2, 38.8, 11.0
        src_labs = [lab(c[:3]) for c in px if c[3] > 0]
        sL = sum(l[0] for l in src_labs) / len(src_labs)
        out_px = []
        for c in px:
            if c[3] == 0:
                out_px.append(c)
                continue
            L, a, b = lab(c[:3])
            dL = L - sL
            new_rgb = lab_to_rgb(max(4.0, min(96.0, rL + dL)), ra, rb)
            out_px.append(new_rgb + (c[3],))
        out = Image.new("RGBA", rgba.size)
        out.putdata(out_px)
        return out

    out_px = []
    for c in px:
        if c[3] == 0:
            out_px.append(c)
            continue
        rgb = c[:3]
        if is_cap_teal and rgb in CAP_TEAL_TRANSITION_MAP:
            new_rgb = CAP_TEAL_TRANSITION_MAP[rgb]
        elif rgb in EXACT_COLOR_MAP:
            new_rgb = EXACT_COLOR_MAP[rgb]
        else:
            new_rgb = rgb
        out_px.append(new_rgb + (c[3],))

    out = Image.new("RGBA", rgba.size)
    out.putdata(out_px)
    return out


def restore_surface_models_without_overlay():
    """Ensure crimson_capped_crimson_strata_2 and _3 use their original cube_bottom_top / cube_bottom_top_rot90
    parents (so side textures crimson_strata_c and crimson_strata_i show their original shapes without overlay)
    while keeping the user-edited grove_top(_b) and canyon_top_a..d on top.
    """
    m2_1 = A / "models/block/crimson_capped_crimson_strata_2/crimson_capped_crimson_strata_2_1.json"
    m2_2 = A / "models/block/crimson_capped_crimson_strata_2/crimson_capped_crimson_strata_2_2.json"
    wj(m2_1, {
        "parent": "minecraft:block/cube_bottom_top",
        "textures": {
            "top": "pysift:block/sift_ground/grove_top",
            "bottom": "pysift:block/teal_strata/teal_strata_a",
            "side": "pysift:block/crimson_strata/crimson_strata_c"
        }
    })
    wj(m2_2, {
        "parent": "minecraft:block/cube_bottom_top",
        "textures": {
            "top": "pysift:block/sift_ground/grove_top_b",
            "bottom": "pysift:block/teal_strata/teal_strata_a",
            "side": "pysift:block/crimson_strata/crimson_strata_c"
        }
    })

    bots = ["silted_strata_silt1", "silted_strata_silt0_b", "silted_strata_silt1", "silted_strata_silt0_b"]
    for i, k in enumerate("abcd"):
        m3 = A / f"models/block/crimson_capped_crimson_strata_3/crimson_capped_crimson_strata_3_{i + 1}.json"
        wj(m3, {
            "parent": "pysift:block/templates/cube_bottom_top_rot90",
            "textures": {
                "top": f"pysift:block/sift_ground/canyon_top_{k}",
                "bottom": f"pysift:block/silted_strata/{bots[i]}",
                "side": "pysift:block/crimson_strata/crimson_strata_i"
            }
        })

    # Clean up temporary overlay models and unused gray/overlay PNGs
    for unused in [
        A / "models/block/templates/cube_bottom_top_overlay.json",
        A / "models/block/templates/cube_bottom_top_rot90_overlay.json",
        A / "textures/block/sift_ground/crimson_grass_side_overlay.png",
        A / "textures/block/vegetation/soft_short_grass_gray.png",
        A / "textures/block/vegetation/soft_tall_grass_bottom_gray.png",
        A / "textures/block/vegetation/soft_tall_grass_top_gray.png",
    ]:
        if unused.exists():
            unused.unlink()


def main():
    apply_changes = "--apply" in sys.argv
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = P / ".texture_backups" / f"{stamp}_stage2_crimson_recolor"

    man = lj(MANIFEST) if MANIFEST.exists() else {"entries": []}
    by_file = {e["file"]: e for e in man["entries"]}

    pairs = []
    for pool, rel, ref_tex in TARGET_TEXTURES:
        path = A / rel
        orig_im = Image.open(path).convert("RGBA")
        new_im = recolor_image(orig_im, rel)
        pairs.append((pool, rel, path, orig_im.copy(), new_im))

        if apply_changes:
            bk_path = bdir / rel
            bk_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, bk_path)
            before_sha = sha1(path)
            new_im.save(path)
            after_sha = sha1(path)

            prev = by_file.get(rel)
            has_backup = bool(prev and prev.get("backup"))
            entry = {
                "file": rel,
                "pool": f"{pool}:stage2_pink",
                "reference": ref_tex,
                "mode": "tone",
                "sha1_before": prev["sha1_before"] if has_backup else before_sha,
                "sha1_after": after_sha,
                "backup": prev["backup"] if has_backup else bk_path.relative_to(P).as_posix(),
                "date": stamp,
            }
            if prev and (prev.get("mode") == "generated" or prev.get("previous")):
                entry["previous"] = prev.get("previous") or prev
            by_file[rel] = entry

    if apply_changes:
        restore_surface_models_without_overlay()
        man["entries"] = sorted(by_file.values(), key=lambda e: e["file"])
        wj(MANIFEST, man)
        print(f"Recolored {len(pairs)} textures and updated recolor_manifest.json; backups in {bdir.relative_to(P)}")

    # Render before/after texture comparison grid
    cols = 4
    rows = (len(pairs) + cols - 1) // cols
    cell_w, cell_h = 230, 86
    sheet = Image.new("RGB", (cols * cell_w + 20, rows * cell_h + 54), (28, 28, 34))
    d = ImageDraw.Draw(sheet)
    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 15)
        font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 12)
    except OSError:
        font_title = font = None

    d.text((14, 12), "第二階段：相關方塊貼圖色相轉換對照（左：原圖  →  右：保留原深淺與形狀、改為柔和粉紅色相）", fill=(245, 240, 242), font=font_title)
    for idx, (pool, rel, path, orig_im, new_im) in enumerate(pairs):
        gx, gy = idx % cols, idx // cols
        x0 = 14 + gx * cell_w
        y0 = 46 + gy * cell_h
        name = Path(rel).stem
        sheet.paste(orig_im.convert("RGB").resize((56, 56), Image.Resampling.NEAREST), (x0, y0))
        d.text((x0 + 62, y0 + 20), "→", fill=(220, 200, 205), font=font_title)
        sheet.paste(new_im.convert("RGB").resize((56, 56), Image.Resampling.NEAREST), (x0 + 84, y0))
        d.text((x0, y0 + 60), name[:28], fill=(200, 200, 210), font=font)

    out_preview = P / "build/previews/stage2_recolor_comparison.png"
    out_preview.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_preview)
    print("Saved comparison preview to", out_preview)


if __name__ == "__main__":
    main()
