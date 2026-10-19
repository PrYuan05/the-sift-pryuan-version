#!/usr/bin/env python3
"""Stage 3: Brighten teal/cyan/silted/abyssal blocks in crimson_strata_canyon and willow_grove
(and all connected blocks sharing their textures) to match #3EC9BF while preserving 100% of
original pixel shapes and internal light/dark shading (深淺), and ensuring seamless block flow.
"""
from __future__ import annotations

import colorsys
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "src/main/resources/assets/pysift"
TEX_BLOCK = ASSETS / "textures/block"
MANIFEST_PATH = ROOT / "tools/texture_pipeline/recolor_manifest.json"
S2_BACKUP = ROOT / ".texture_backups/20261018-175357_stage2_crimson_recolor/textures/block"
S3_BASELINE = ROOT / ".texture_backups/stage3_teal_baseline/textures/block"

# Never touch the user's hand-edited ground top textures
PROTECTED_GROUND_TOPS = {
    "textures/block/sift_ground/canyon_top_a.png",
    "textures/block/sift_ground/canyon_top_b.png",
    "textures/block/sift_ground/canyon_top_c.png",
    "textures/block/sift_ground/canyon_top_d.png",
    "textures/block/sift_ground/grove_top.png",
    "textures/block/sift_ground/grove_top_b.png",
}

# Exact lookup table for pure teal / cyan / silted / abyssal shades -> #3EC9BF family
# Preserves full original light/dark contrast (深淺) within every texture
EXACT_TEAL_MAP: dict[str, tuple[int, int, int]] = {
    # 1. Deep shadow bands in abyssal_strata (depth=0..3) & teal_strata_c/d
    "#054a56": (24, 146, 138),   # #18928a (deep shadow band)
    "#184a55": (28, 150, 142),   # #1c968e
    "#07515f": (32, 158, 150),   # #209e96
    "#075260": (34, 161, 152),
    "#075462": (36, 164, 155),
    "#0b5762": (38, 167, 158),
    "#065866": (40, 170, 161),   # #28aaa1
    "#105a63": (42, 173, 164),
    "#0f5e67": (45, 177, 168),
    "#105f67": (46, 179, 170),
    "#1b6567": (49, 184, 174),
    "#236461": (48, 183, 173),   # #30b7ad (mid-step band in depth0_c, depth1_a/b, teal_strata_c/d)
    "#1f656b": (50, 185, 175),
    "#1d6768": (51, 187, 177),
    "#1e676a": (51, 187, 177),
    "#1e6868": (52, 189, 179),
    "#2d706d": (55, 193, 183),

    # 2. Mid/bright abyssal_strata (depth=0) & teal_strata_a..d & crimson_strata_c/e/g
    "#486378": (40, 173, 165),   # #28ada5 (darker blue-teal shade in teal_strata_a & depth0)
    "#32736d": (52, 188, 178),
    "#32746d": (53, 189, 179),
    "#337370": (53, 189, 179),
    "#33746d": (54, 190, 180),
    "#397869": (52, 188, 178),   # #34bcb2 (mid green-teal in depth0)
    "#486d7c": (53, 190, 181),   # #35beb5 (mid blue-teal in teal_strata_a & depth0)
    "#4d6d7b": (54, 191, 182),
    "#3b796f": (56, 194, 184),
    "#437570": (56, 194, 184),
    "#3c7a6a": (58, 196, 186),
    "#3f7b70": (60, 199, 189),
    "#437972": (60, 199, 189),
    "#3e7d6b": (62, 201, 191),   # #3ec9bf (Target!)
    "#42787b": (62, 201, 191),   # #3ec9bf (Target! Bright shade in teal_strata_a)
    "#427a76": (64, 204, 194),
    "#407d6f": (66, 206, 196),
    "#417d6f": (67, 207, 197),
    "#427d6e": (67, 207, 197),
    "#417d71": (68, 208, 198),
    "#417e6c": (70, 210, 200),
    "#417e6d": (70, 210, 200),
    "#417e6e": (70, 210, 200),
    "#417e6f": (70, 210, 200),
    "#417f6c": (72, 212, 202),   # #48d4ca (brightest highlight in depth0 & crimson_strata_c)

    # 3. Silted strata (silt=0, 1) & crimson_strata_i & teal_strata_g
    "#5e6b74": (34, 160, 151),   # #22a097 (darkest silt speck shadow)
    "#626e76": (43, 172, 163),   # #2baca3
    "#636e76": (43, 172, 163),   # #2baca3 (darker border shade in silt0_a)
    "#4a7075": (48, 180, 171),
    "#536d74": (46, 178, 169),
    "#4e7078": (50, 183, 174),
    "#4e7179": (51, 185, 176),
    "#4f6e7b": (50, 183, 174),
    "#52727e": (54, 189, 180),
    "#53747b": (55, 191, 182),
    "#607378": (54, 188, 179),
    "#567681": (56, 192, 183),
    "#54777e": (57, 194, 185),
    "#54777f": (57, 194, 185),
    "#497879": (62, 201, 191),   # #3ec9bf
    "#4b787a": (62, 201, 191),   # #3ec9bf
    "#547981": (53, 189, 179),   # #35bdb3 (mid-dark teal in silt0_a)
    "#67727b": (58, 182, 174),   # #3ab6ae (muted mid silt speck)
    "#557c85": (62, 201, 191),   # #3ec9bf (main body teal in silt0_a!)
    "#61828a": (80, 215, 205),   # #50d7cd (light highlight teal in silt0_a)
    "#7b848b": (106, 223, 214),  # #6adfd6 (light mineral silt speck in silt0_b & silt1)
    "#8c858c": (130, 229, 221),  # #82e5dd (brightest mineral silt speck in silt0_b & silt1)

    # 4. Bricks (abyssal_strata_bricks, silted_strata_bricks, teal_strata_bricks + chiseled)
    "#035145": (28, 158, 149),   # Shade 1: mortar shadow
    "#2b555f": (28, 158, 149),
    "#3e5156": (32, 162, 153),
    "#256659": (45, 181, 171),   # Shade 2: dark bevel
    "#436a74": (45, 181, 171),
    "#54676a": (48, 184, 174),
    # Shade 3 (#397869, #557c85, #66787b) is #34bcb2 / #3ec9bf
    "#478574": (82, 214, 204),   # Shade 4: light face
    "#638991": (82, 214, 204),
    "#738586": (86, 216, 206),
    "#559280": (108, 226, 217),  # Shade 5: highlight bevel
    "#70969d": (108, 226, 217),
    "#819292": (112, 228, 219),

    # 5. Pale teal strata (teal_strata_e, teal_strata_f, gray_strata_f, gray_strata_g)
    "#488170": (68, 208, 198),
    "#66787b": (48, 182, 173),   # darker mottled patches in teal_strata_e & brick mid-face
    "#5b857d": (74, 212, 202),
    "#5e867f": (78, 215, 205),
    "#6e8286": (62, 201, 191),
    "#678886": (86, 219, 209),
    "#698887": (88, 220, 210),
    "#6f8a8b": (96, 224, 214),
    "#748b8e": (104, 228, 218),
    "#7a9194": (114, 232, 222),
}

# For capped_crimson_strata (teal_top, rose_top, crimson_strata_h, crimson_strata_f):
# Here #054a56, #07515f, #065866 are the BRIGHT TOP CAP (69% of teal_top, 46% of rose_top),
# and #5a4f64 is the darker groove/seam around the teal plates!
CAPPED_CRIMSON_MAP: dict[str, tuple[int, int, int]] = {
    "#054a56": (44, 182, 173),   # #2cb6ad (darker cap shade)
    "#07515f": (54, 193, 184),   # #36c1b8 (mid cap shade)
    "#065866": (66, 206, 196),   # #42cec4 (bright cap shade, centered on #3EC9BF)
    "#5a4f64": (92, 152, 154),   # #5c989a (darker teal-slate groove / transition rim)
    "#994257": (232, 105, 117),  # #e86975
    "#a64656": (242, 118, 131),  # #f27683
    "#b04954": (250, 131, 144),  # #fa8390
}

# Exact lookup table for crimson/rose pixels & crimson-teal transitions in dual-material textures
EXACT_CRIMSON_AND_TRANSITION_MAP: dict[str, tuple[int, int, int]] = {
    # Bright crimson cap (#994257 < #a64656 < #b04954) -> soft rose-pink
    "#994257": (232, 105, 117),  # #e86975
    "#a64656": (242, 118, 131),  # #f27683
    "#b04954": (250, 131, 144),  # #fa8390

    # Ember heat2_a cap (#b74d60, #b55758, #b46057) -> soft rose-pink
    "#b74d60": (237, 111, 123),  # #ed6f7b
    "#b55758": (244, 122, 135),  # #f47a87
    "#b46057": (250, 133, 145),  # #fa8591

    # Seam / groove between teal (#3ec9bf) and rose-pink (#f27683)
    "#796067": (146, 164, 168),  # #92a4a8 (crimson_strata_e, g, dark_slate_d)
    "#796168": (146, 164, 168),  # #92a4a8 (rose_capped_crimson_strata_top)
    "#a36270": (200, 142, 151),  # #c88e97 (crimson_strata_c, gray_strata_a upper transition)
    "#6a7463": (176, 132, 140),  # #b0848c (dark_slate_b, c, e, gray_strata_b transition near dusty-rose bottom)

    # Transition pixels in crimson_strata_i, gray_strata_i, teal_capped_gray_strata_2_bottom
    "#4e7179": (51, 185, 176),
    "#607378": (54, 188, 179),
    "#7d5a6a": (144, 162, 166),
    "#825c6c": (154, 158, 164),
    "#835464": (166, 148, 156),
    "#855c69": (162, 154, 160),
    "#8a5663": (182, 142, 150),
    "#8a5d67": (176, 148, 156),
    "#8a5f6b": (174, 150, 158),
    "#8b5e68": (178, 148, 156),
    "#8d5a83": (178, 146, 162),
    "#8f606a": (186, 146, 154),
    "#905862": (194, 138, 147),
}


def clamp8(v: float) -> int:
    return max(0, min(255, int(round(v))))


def hex_of(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def recolor_dusty_rose(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """Same dusty-rose mapping as Stage 2 for crimson_strata_a/d and dark_slate_b/c/e."""
    r, g, b = [c / 255.0 for c in rgb]
    _, s, v = colorsys.rgb_to_hsv(r, g, b)
    target_h = 355.0 / 360.0
    new_s = max(0.45, min(0.54, 0.49 + (s - 0.16) * 0.30))
    new_v = max(0.70, min(0.92, 0.75 + (v - 0.44) * 1.10))
    nr, ng, nb = colorsys.hsv_to_rgb(target_h, new_s, new_v)
    return (clamp8(nr * 255), clamp8(ng * 255), clamp8(nb * 255))


def map_silt_transition(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """For silted_strata_silt2, gray_strata_h, and teal_capped_gray_strata_bottom:
    Map pure teal pixels via EXACT_TEAL_MAP, keep warm sand/silt pixels (#d1c4a7..#f2d7bb)
    intact, and smoothly interpolate intermediate teal-to-sand transition pixels.
    """
    hx = hex_of(rgb)
    if hx in EXACT_TEAL_MAP:
        return EXACT_TEAL_MAP[hx]
    r, g, b = rgb
    if r >= g and r >= 200:
        return rgb
    ratio = r / max(1.0, float(g))
    t = max(0.0, min(1.0, (ratio - 0.70) / (1.08 - 0.70)))
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    scale = max(0.85, min(1.18, lum / 115.0))
    teal_r = clamp8(62 * scale)
    teal_g = clamp8(201 * scale)
    teal_b = clamp8(191 * scale)
    out_r = clamp8((1.0 - t) * teal_r + t * r)
    out_g = clamp8((1.0 - t) * teal_g + t * g)
    out_b = clamp8((1.0 - t) * teal_b + t * b)
    return (out_r, out_g, out_b)


def recolor_pixel_stage3(rel_path: str, rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    name = Path(rel_path).stem
    hx = hex_of(rgb)

    # 1. Capped crimson strata (teal_top, rose_top, crimson_strata_h, crimson_strata_f)
    if name in {"capped_crimson_strata_teal_top", "capped_crimson_strata_rose_top", "crimson_strata_h", "crimson_strata_f"}:
        if hx in CAPPED_CRIMSON_MAP:
            return CAPPED_CRIMSON_MAP[hx]
        return rgb

    # 2. Silted-to-sand transition textures
    if name in {"silted_strata_silt2", "gray_strata_h", "teal_capped_gray_strata_bottom"}:
        return map_silt_transition(rgb)

    # 3. teal_strata_b: variant of teal_strata_a on teal_capped_dark_slate_2 top
    if name == "teal_strata_b":
        if hx in EXACT_TEAL_MAP:
            return EXACT_TEAL_MAP[hx]
        if hx == "#796067":
            return (92, 178, 174)
        if hx == "#b04954":
            return (156, 156, 160)
        return rgb

    # 4. crimson_strata_c and gray_strata_a: #816a6b is a transition pixel, while in dark_slate_b/c/e it's dusty-rose
    if name in {"crimson_strata_c", "gray_strata_a"}:
        if hx in EXACT_TEAL_MAP:
            return EXACT_TEAL_MAP[hx]
        if hx in {"#816a6b", "#8d6c67"}:
            return (148, 164, 168)
        if hx in EXACT_CRIMSON_AND_TRANSITION_MAP:
            return EXACT_CRIMSON_AND_TRANSITION_MAP[hx]
        return rgb

    # 5. dark_slate_b, dark_slate_c, dark_slate_e, gray_strata_b: teal cap + #6a7463 transition + dusty-rose body
    if name in {"dark_slate_b", "dark_slate_c", "dark_slate_e", "gray_strata_b"}:
        if hx in EXACT_TEAL_MAP:
            return EXACT_TEAL_MAP[hx]
        if hx in EXACT_CRIMSON_AND_TRANSITION_MAP:
            return EXACT_CRIMSON_AND_TRANSITION_MAP[hx]
        return recolor_dusty_rose(rgb)

    # 6. All other target & connected teal/silted/abyssal/crimson textures
    if hx in EXACT_TEAL_MAP:
        return EXACT_TEAL_MAP[hx]
    if hx in EXACT_CRIMSON_AND_TRANSITION_MAP:
        return EXACT_CRIMSON_AND_TRANSITION_MAP[hx]

    return rgb


STAGE3_TEXTURES = [
    # 1. Canyon: silted_strata, capped_crimson_strata, crimson_capped_crimson_strata_3
    "textures/block/silted_strata/silted_strata_silt0_a.png",
    "textures/block/silted_strata/silted_strata_silt0_b.png",
    "textures/block/silted_strata/silted_strata_silt1.png",
    "textures/block/silted_strata/silted_strata_silt2.png",
    "textures/block/silted_strata_bricks/silted_strata_bricks.png",
    "textures/block/silted_strata_bricks/chiseled_silted_strata_bricks.png",
    "textures/block/capped_crimson_strata/capped_crimson_strata_teal_top.png",
    "textures/block/capped_crimson_strata/capped_crimson_strata_rose_top.png",
    "textures/block/crimson_strata/crimson_strata_h.png",
    "textures/block/crimson_strata/crimson_strata_f.png",
    "textures/block/crimson_strata/crimson_strata_i.png",
    # 2. Willow Grove: abyssal_strata, abyssal_strata_bricks, chiseled_abyssal_strata_bricks, crimson_capped_crimson_strata_2
    "textures/block/abyssal_strata/abyssal_strata_depth0_a.png",
    "textures/block/abyssal_strata/abyssal_strata_depth0_b.png",
    "textures/block/abyssal_strata/abyssal_strata_depth0_c.png",
    "textures/block/abyssal_strata/abyssal_strata_depth0_d.png",
    "textures/block/abyssal_strata/abyssal_strata_depth1_a.png",
    "textures/block/abyssal_strata/abyssal_strata_depth1_b.png",
    "textures/block/abyssal_strata/abyssal_strata_depth2.png",
    "textures/block/abyssal_strata_bricks/abyssal_strata_bricks.png",
    "textures/block/abyssal_strata_bricks/chiseled_abyssal_strata_bricks.png",
    "textures/block/teal_strata/teal_strata_a.png",
    "textures/block/crimson_strata/crimson_strata_c.png",
    # 3. Connected blocks sharing these textures (for 100% block continuity)
    "textures/block/teal_strata/teal_strata_b.png",
    "textures/block/teal_strata/teal_strata_c.png",
    "textures/block/teal_strata/teal_strata_d.png",
    "textures/block/teal_strata/teal_strata_e.png",
    "textures/block/teal_strata/teal_strata_f.png",
    "textures/block/teal_strata/teal_strata_g.png",
    "textures/block/teal_strata_bricks/teal_strata_bricks.png",
    "textures/block/teal_strata_bricks/chiseled_teal_strata_bricks.png",
    "textures/block/crimson_strata/crimson_strata_e.png",
    "textures/block/crimson_strata/crimson_strata_g.png",
    "textures/block/rose_capped_crimson_strata/rose_capped_crimson_strata_top.png",
    "textures/block/teal_capped_abyssal_strata/teal_capped_abyssal_strata_bottom.png",
    "textures/block/teal_capped_teal_strata_2/teal_capped_teal_strata_2_top.png",
    "textures/block/teal_capped_gray_strata/teal_capped_gray_strata_bottom.png",
    "textures/block/teal_capped_gray_strata_2/teal_capped_gray_strata_2_bottom.png",
    "textures/block/gray_strata/gray_strata_a.png",
    "textures/block/gray_strata/gray_strata_b.png",
    "textures/block/gray_strata/gray_strata_f.png",
    "textures/block/gray_strata/gray_strata_g.png",
    "textures/block/gray_strata/gray_strata_h.png",
    "textures/block/gray_strata/gray_strata_i.png",
    "textures/block/dark_slate/dark_slate_b.png",
    "textures/block/dark_slate/dark_slate_c.png",
    "textures/block/dark_slate/dark_slate_d.png",
    "textures/block/dark_slate/dark_slate_e.png",
]


def sha1_file(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest()


def get_clean_source(rel: str) -> Path:
    """Return the unmodified original texture path from Stage 2 backup or Stage 3 baseline."""
    sub = rel.removeprefix("textures/block/")
    s2 = S2_BACKUP / sub
    if s2.exists():
        return s2
    s3 = S3_BASELINE / sub
    if not s3.exists():
        s3.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ASSETS / rel, s3)
    return s3


def apply_stage3(write_files: bool = True) -> list[tuple[str, Image.Image, Image.Image]]:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = ROOT / ".texture_backups" / f"{stamp}_stage3_teal_recolor"
    if write_files:
        backup_dir.mkdir(parents=True, exist_ok=True)

    manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_file = {e["file"]: e for e in manifest_data.get("entries", [])}

    pairs: list[tuple[str, Image.Image, Image.Image]] = []
    for rel in STAGE3_TEXTURES:
        assert rel not in PROTECTED_GROUND_TOPS, f"Refusing to touch protected ground top {rel}"
        dst_path = ASSETS / rel
        src_path = get_clean_source(rel)

        orig_img = Image.open(src_path).convert("RGBA")
        new_img = orig_img.copy()
        px = new_img.load()
        w, h = new_img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a > 0:
                    nr, ng, nb = recolor_pixel_stage3(rel, (r, g, b))
                    px[x, y] = (nr, ng, nb, a)

        pairs.append((rel, orig_img, new_img))

        if write_files:
            bak_path = backup_dir / rel
            bak_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst_path, bak_path)
            new_img.save(dst_path, "PNG")
            new_sha = sha1_file(dst_path)
            if rel in by_file:
                by_file[rel]["sha1_after"] = new_sha

    if write_files:
        MANIFEST_PATH.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Recolored {len(pairs)} textures and updated recolor_manifest.json; backups in {backup_dir.relative_to(ROOT)}")

    return pairs


def render_comparison_sheet(pairs: list[tuple[str, Image.Image, Image.Image]], out_path: Path) -> None:
    scale = 4
    tile = 16 * scale
    cols = 4
    rows = (len(pairs) + cols - 1) // cols
    cell_w = 260
    cell_h = 98
    pad = 16
    header_h = 48

    img = Image.new("RGBA", (cols * cell_w + pad * 2, rows * cell_h + header_h + pad * 2), (24, 26, 30, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
        title_font = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 16)
    except Exception:
        font = ImageFont.load_default()
        title_font = font

    draw.text((pad, 12), "第三階段：青色／淤積／深淵系列方塊調亮至 #3EC9BF 對照（保留原深淺與形狀）", fill=(240, 240, 245), font=title_font)
    draw.rectangle([pad + 640, 10, pad + 672, 36], fill=(62, 201, 191, 255), outline=(255, 255, 255, 200))
    draw.text((pad + 680, 14), "目標色 #3EC9BF", fill=(62, 201, 191), font=font)

    for idx, (rel, orig_im, new_im) in enumerate(pairs):
        r = idx // cols
        c = idx % cols
        x0 = pad + c * cell_w
        y0 = header_h + pad + r * cell_h

        o_up = orig_im.resize((tile, tile), Image.Resampling.NEAREST)
        n_up = new_im.resize((tile, tile), Image.Resampling.NEAREST)
        img.paste(o_up, (x0, y0))
        draw.text((x0 + tile + 8, y0 + tile // 2 - 8), "→", fill=(200, 200, 210), font=title_font)
        img.paste(n_up, (x0 + tile + 28, y0))

        short_name = Path(rel).stem
        px = new_im.convert("RGB").load()
        npix = [px[x, y] for y in range(new_im.height) for x in range(new_im.width)]
        avg_hex = f"#{int(sum(p[0] for p in npix)/len(npix)):02x}{int(sum(p[1] for p in npix)/len(npix)):02x}{int(sum(p[2] for p in npix)/len(npix)):02x}"
        draw.text((x0, y0 + tile + 4), f"{short_name[:22]} ({avg_hex})", fill=(210, 214, 222), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"Saved comparison preview to {out_path.relative_to(ROOT)}")


def perspective_coeffs(dst, src):
    m = []
    for (x, y), (u, v) in zip(dst, src):
        m.append([x, y, 1, 0, 0, 0, -u * x, -u * y, u])
        m.append([0, 0, 0, x, y, 1, -v * x, -v * y, v])
    for col in range(8):
        piv = max(range(col, 8), key=lambda r: abs(m[r][col]))
        m[col], m[piv] = m[piv], m[col]
        for r in range(8):
            if r != col:
                f = m[r][col] / m[col][col]
                m[r] = [a - f * b for a, b in zip(m[r], m[col])]
    return [m[i][8] / m[i][i] for i in range(8)]


def iso_cube(top_im: Image.Image, side_im: Image.Image, size: int = 56) -> Image.Image:
    h = size / 2
    W, H = size + 2, int(size * 1.15) + 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    c = (W / 2, h / 2)
    top_q = [(c[0], 0), (W - 1, h / 2), (c[0], h), (0, h / 2)]
    left_q = [(0, h / 2), (c[0], h), (c[0], H - 1), (0, H - 1 - h / 2)]
    right_q = [(c[0], h), (W - 1, h / 2), (W - 1, H - 1 - h / 2), (c[0], H - 1)]
    src = [(0, 0), (16, 0), (16, 16), (0, 16)]

    def shade(im: Image.Image, f: float) -> Image.Image:
        r, g, b, a = im.split()
        return Image.merge("RGBA", (r.point(lambda x: int(x * f)), g.point(lambda x: int(x * f)), b.point(lambda x: int(x * f)), a))

    for quad, tex in ((top_q, top_im), (left_q, shade(side_im, 0.82)), (right_q, shade(side_im, 0.66))):
        warped = tex.transform((W, H), Image.Transform.PERSPECTIVE, perspective_coeffs(quad, src), Image.Resampling.NEAREST)
        img.alpha_composite(warped)
    return img


def render_3d_blocks_sheet(out_path: Path) -> None:
    """Render 3D isometric + top/side/bottom sheet for all Canyon & Willow Grove target blocks and connected teal blocks."""
    rows_spec = [
        # (Label, Role, top_rel, side_rel, bottom_rel, side_transform)
        ("silted_strata [silt=0] 淤積地層岩", "赤紅沉積峽谷：地表下4-8格／池塘邊壁", "silted_strata/silted_strata_silt0_a.png", "silted_strata/silted_strata_silt0_a.png", "silted_strata/silted_strata_silt0_a.png", None),
        ("silted_strata [silt=1] 淤積地層岩", "赤紅沉積峽谷：過渡層／地表底面", "silted_strata/silted_strata_silt1.png", "silted_strata/silted_strata_silt1.png", "silted_strata/silted_strata_silt1.png", None),
        ("silted_strata [silt=2] 淤積地層岩", "赤紅沉積峽谷：過渡層", "silted_strata/silted_strata_silt2.png", "silted_strata/silted_strata_silt2.png", "silted_strata/silted_strata_silt2.png", None),
        ("capped_crimson_strata [tone=teal] 覆蓋赤紅地層岩", "赤紅沉積峽谷：圓台頂面（青色）", "capped_crimson_strata/capped_crimson_strata_teal_top.png", "crimson_strata/crimson_strata_h.png", "crimson_vein_stone/crimson_vein_stone_crimson_spread4.png", None),
        ("capped_crimson_strata [tone=rose] 覆蓋赤紅地層岩", "赤紅沉積峽谷：圓台頂面（玫瑰色）", "capped_crimson_strata/capped_crimson_strata_rose_top.png", "crimson_strata/crimson_strata_f.png", "crimson_vein_stone/crimson_vein_stone_crimson_spread4.png", Image.Transpose.FLIP_TOP_BOTTOM),
        ("crimson_capped_crimson_strata_3 赤紅覆蓋赤紅地層岩 3", "赤紅沉積峽谷：地表方塊", "sift_ground/canyon_top_a.png", "crimson_strata/crimson_strata_i.png", "silted_strata/silted_strata_silt1.png", Image.Transpose.ROTATE_270),
        ("abyssal_strata [depth=0] 深淵地層岩 (a)", "柳絮林地：地表下6格／池塘／圓台主體", "abyssal_strata/abyssal_strata_depth0_a.png", "abyssal_strata/abyssal_strata_depth0_a.png", "abyssal_strata/abyssal_strata_depth0_a.png", None),
        ("abyssal_strata [depth=0] 深淵地層岩 (d)", "柳絮林地：地表下6格／池塘／圓台主體", "abyssal_strata/abyssal_strata_depth0_d.png", "abyssal_strata/abyssal_strata_depth0_d.png", "abyssal_strata/abyssal_strata_depth0_d.png", None),
        ("abyssal_strata [depth=1..3] 深淵地層岩", "深淵地層岩過渡階段 (depth=1, 2, 3)", "abyssal_strata/abyssal_strata_depth0_c.png", "abyssal_strata/abyssal_strata_depth1_a.png", "abyssal_strata/abyssal_strata_depth2.png", None),
        ("abyssal_strata_bricks 深淵地層岩磚", "柳絮林地：Boss 競技場", "abyssal_strata_bricks/abyssal_strata_bricks.png", "abyssal_strata_bricks/abyssal_strata_bricks.png", "abyssal_strata_bricks/abyssal_strata_bricks.png", None),
        ("chiseled_abyssal_strata_bricks 浮雕深淵地層岩磚", "柳絮林地：Boss 競技場", "abyssal_strata_bricks/chiseled_abyssal_strata_bricks.png", "abyssal_strata_bricks/chiseled_abyssal_strata_bricks.png", "abyssal_strata_bricks/chiseled_abyssal_strata_bricks.png", None),
        ("crimson_capped_crimson_strata_2 赤紅覆蓋赤紅地層岩 2", "柳絮林地：地表方塊", "sift_ground/grove_top.png", "crimson_strata/crimson_strata_c.png", "teal_strata/teal_strata_a.png", None),
        ("teal_capped_abyssal_strata 青碧覆蓋深淵地層岩", "同系列青碧覆蓋方塊", "abyssal_strata/abyssal_strata_depth2.png", "abyssal_strata/abyssal_strata_depth0_b.png", "teal_capped_abyssal_strata/teal_capped_abyssal_strata_bottom.png", None),
        ("teal_capped_teal_strata 青碧覆蓋青碧地層岩", "同系列青碧覆蓋方塊", "abyssal_strata/abyssal_strata_depth2.png", "teal_strata/teal_strata_c.png", "abyssal_strata/abyssal_strata_depth1_a.png", None),
        ("teal_capped_teal_strata_2 青碧覆蓋青碧地層岩 2", "同系列青碧覆蓋方塊", "teal_capped_teal_strata_2/teal_capped_teal_strata_2_top.png", "teal_strata/teal_strata_g.png", "silted_strata/silted_strata_silt0_a.png", Image.Transpose.ROTATE_270),
        ("teal_capped_gray_strata 青碧覆蓋灰色地層岩", "同系列青碧覆蓋方塊", "silted_strata/silted_strata_silt0_a.png", "gray_strata/gray_strata_h.png", "teal_capped_gray_strata/teal_capped_gray_strata_bottom.png", Image.Transpose.FLIP_TOP_BOTTOM),
        ("teal_capped_gray_strata_2 青碧覆蓋灰色地層岩 2", "同系列青碧覆蓋方塊", "silted_strata/silted_strata_silt0_a.png", "gray_strata/gray_strata_i.png", "teal_capped_gray_strata_2/teal_capped_gray_strata_2_bottom.png", None),
    ]

    row_h = 84
    header_h = 44
    W = 920
    H = header_h + len(rows_spec) * row_h + 16
    img = Image.new("RGBA", (W, H), (22, 24, 28, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
        bold = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 14)
    except Exception:
        font = ImageFont.load_default()
        bold = font

    draw.text((16, 12), "方塊名稱與生態域用途", fill=(220, 224, 232), font=bold)
    draw.text((390, 12), "3D 預覽", fill=(220, 224, 232), font=bold)
    draw.text((480, 12), "頂面 (Top)", fill=(220, 224, 232), font=bold)
    draw.text((610, 12), "側面 (Side)", fill=(220, 224, 232), font=bold)
    draw.text((740, 12), "底面 (Bottom)", fill=(220, 224, 232), font=bold)

    for i, (title, role, top_r, side_r, bot_r, tr) in enumerate(rows_spec):
        y0 = header_h + i * row_h
        draw.line([(12, y0), (W - 12, y0)], fill=(45, 49, 58, 255), width=1)
        if i < 12:
            draw.rectangle([8, y0 + 2, W - 8, y0 + row_h - 2], outline=(62, 201, 191, 110), width=1)

        draw.text((16, y0 + 14), title, fill=(245, 247, 250), font=bold)
        draw.text((16, y0 + 40), role, fill=(160, 195, 192), font=font)

        top_im = Image.open(TEX_BLOCK / top_r).convert("RGBA")
        side_im = Image.open(TEX_BLOCK / side_r).convert("RGBA")
        bot_im = Image.open(TEX_BLOCK / bot_r).convert("RGBA")
        side_oriented = side_im.transpose(tr) if tr is not None else side_im

        cube = iso_cube(top_im, side_oriented, size=56)
        img.alpha_composite(cube, (385, y0 + 8))

        for x_col, face_im, rname in ((480, top_im, top_r), (610, side_oriented, side_r), (740, bot_im, bot_r)):
            up = face_im.resize((56, 56), Image.Resampling.NEAREST)
            img.paste(up, (x_col, y0 + 6))
            px = face_im.convert("RGB").load()
            npix = [px[x, y] for y in range(16) for x in range(16)]
            avg_hex = f"#{int(sum(p[0] for p in npix)/256):02x}{int(sum(p[1] for p in npix)/256):02x}{int(sum(p[2] for p in npix)/256):02x}"
            draw.text((x_col, y0 + 64), f"{Path(rname).stem[:14]} ({avg_hex})", fill=(185, 190, 200), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    print(f"Saved 3D blocks preview to {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    pairs = apply_stage3(write_files=apply)
    render_comparison_sheet(pairs, ROOT / "build/previews/stage3_teal_comparison.png")
    render_3d_blocks_sheet(ROOT / "build/previews/stage3_teal_blocks_3d.png")

