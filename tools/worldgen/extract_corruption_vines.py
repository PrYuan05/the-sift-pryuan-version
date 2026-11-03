#!/usr/bin/env python3
"""
extract_corruption_vines.py
===========================
Extracts ONLY the purple corruption vine/tendril overlays from our tall pillar masks
as transparent PNGs (`alpha=0` background, `alpha=255` purple vine pixels) so they
can be used on a stackable vine-like block (`corruption=0..3` based on placement count),
replacing the solid `corrupted_slate` block!

Outputs:
  1. `src/main/resources/assets/pysift/textures/block/corrupted_vine/` (11 extracted 16x16 transparent vine PNGs):
     - `corrupted_vine_corruption0_a.png`, `corrupted_vine_corruption0_b.png`
     - `corrupted_vine_corruption1.png`
     - `corrupted_vine_corruption2_a.png` .. `e.png`
     - `corrupted_vine_corruption3_a.png` .. `c.png`
  2. `build/previews/extracted_corruption_vine_preview.png`:
     - Side-by-side comparison of the transparent extracted vines (on checkerboard)
       AND how they look when overlaid onto `dark_slate_pillar_side.png` (or any block)
       as placement count (`corruption = 0 -> 1 -> 2 -> 3`) increases!
"""

from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
import build_corrupted_slate_pillar as bcp

ASSETS = ROOT / "src" / "main" / "resources" / "assets" / "pysift"
VINE_DIR = ASSETS / "textures" / "block" / "corrupted_vine"
PREVIEW_DIR = ROOT / "build" / "previews"


def mask_to_transparent_image(mask_rows: list[str]) -> Image.Image:
    """Converts a mask grid (`.` = transparent `(0,0,0,0)`, palette char = opaque purple pixel) to RGBA Image."""
    h = len(mask_rows)
    w = len(mask_rows[0])
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y, r in enumerate(mask_rows):
        for x, ch in enumerate(r):
            if ch != ".":
                px[x, y] = bcp.hex_rgba(bcp.VINE_COLORS[ch])
    return img


def make_checkerboard(w: int, h: int, cell: int = 8) -> Image.Image:
    """Creates a dark-gray checkerboard background to clearly visualize transparency."""
    img = Image.new("RGBA", (w, h), (28, 30, 36, 255))
    draw = ImageDraw.Draw(img)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if ((x // cell) + (y // cell)) % 2 == 1:
                draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(42, 45, 54, 255))
    return img


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    VINE_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Slice the tall masks into 16x16 transparent vine textures
    c0_masks = bcp.slice_strip(bcp.STRIP_CORRUPTION_0_MASK)
    c1_masks = bcp.slice_strip(bcp.STRIP_CORRUPTION_1_MASK)
    c2_masks = bcp.slice_strip(bcp.STRIP_CORRUPTION_2_MASK)
    c3_masks = bcp.slice_strip(bcp.STRIP_CORRUPTION_3_MASK)

    vine_specs: dict[str, list[str]] = {
        "corrupted_vine_corruption0_a": c0_masks[0],
        "corrupted_vine_corruption0_b": c0_masks[1],
        "corrupted_vine_corruption1": c1_masks[0],
        "corrupted_vine_corruption2_a": c2_masks[0],
        "corrupted_vine_corruption2_b": c2_masks[1],
        "corrupted_vine_corruption2_c": c2_masks[2],
        "corrupted_vine_corruption2_d": c2_masks[3],
        "corrupted_vine_corruption2_e": c2_masks[4],
        "corrupted_vine_corruption3_a": c3_masks[0],
        "corrupted_vine_corruption3_b": c3_masks[1],
        "corrupted_vine_corruption3_c": c3_masks[2],
    }

    vine_imgs: dict[str, Image.Image] = {}
    for name, mrows in vine_specs.items():
        im = mask_to_transparent_image(mrows)
        vine_imgs[name] = im
        out_p = VINE_DIR / f"{name}.png"
        im.save(out_p)
        print(f"  ✅ 已提取透明藤蔓貼圖: {out_p.relative_to(ROOT)}")

    # Also save the full tall transparent vine strips to build/previews/
    tall_vine_strips = {
        "vine_strip_c0": mask_to_transparent_image(bcp.STRIP_CORRUPTION_0_MASK),
        "vine_strip_c1": mask_to_transparent_image(bcp.STRIP_CORRUPTION_1_MASK),
        "vine_strip_c2": mask_to_transparent_image(bcp.STRIP_CORRUPTION_2_MASK),
        "vine_strip_c3": mask_to_transparent_image(bcp.STRIP_CORRUPTION_3_MASK),
    }
    for sname, sim in tall_vine_strips.items():
        sim.save(PREVIEW_DIR / f"{sname}.png")

    # 2. Build visual preview showing:
    #    - Left of each stage: Extracted transparent vine strip on checkerboard (showing pure alpha cutout!)
    #    - Right of each stage: The same transparent vine strip overlaid on `dark_slate_pillar_side.png`
    pillar_side = bcp.grid_to_image(bcp.BASE_PILLAR_SIDE_ROWS)

    canvas = Image.new("RGBA", (1260, 760), (18, 20, 25, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, 1260, 48], fill=(30, 34, 44, 255))
    draw.text(
        (16, 15),
        "The Sift - Extracted Transparent Corruption Vine Overlay (Checkerboard = Alpha Cutout | Right = Overlaid on Dark Slate Pillar)",
        fill=(235, 240, 250, 255),
    )

    scale = 4  # 16px -> 64px

    stage_columns = [
        (
            "Stage 0 (1x Placed / corruption=0)",
            "16x32 Transparent Strip (0_a, 0_b)",
            ["corrupted_vine_corruption0_a", "corrupted_vine_corruption0_b"],
            20,
        ),
        (
            "Stage 1 (2x Placed / corruption=1)",
            "16x32 Stacked Transparent Strip",
            ["corrupted_vine_corruption1", "corrupted_vine_corruption1"],
            280,
        ),
        (
            "Stage 2 (3x Placed / corruption=2)",
            "16x80 5-Block Transparent Strip (2_a..2_e)",
            [
                "corrupted_vine_corruption2_a",
                "corrupted_vine_corruption2_b",
                "corrupted_vine_corruption2_c",
                "corrupted_vine_corruption2_d",
                "corrupted_vine_corruption2_e",
            ],
            540,
        ),
        (
            "Stage 3 (4x Placed / corruption=3)",
            "16x48 3-Block Transparent Strip (3_a..3_c)",
            [
                "corrupted_vine_corruption3_a",
                "corrupted_vine_corruption3_b",
                "corrupted_vine_corruption3_c",
            ],
            830,
        ),
    ]

    for title, subtitle, names, x0 in stage_columns:
        box_w = 245 if len(names) <= 3 else 270
        draw.rectangle([x0 - 6, 58, x0 + box_w, 740], fill=(24, 27, 34, 255), outline=(52, 58, 72, 255))
        draw.text((x0, 64), title, fill=(240, 220, 150, 255))
        draw.text((x0, 82), subtitle, fill=(175, 185, 205, 255))
        draw.text((x0, 102), "Pure Vine (Alpha)     On Pillar Base", fill=(150, 210, 180, 255))

        n_blocks = len(names)
        strip_h = n_blocks * 16
        # 1) Pure transparent vine on checkerboard (2x wide = 32px -> 128px? Let's do 1.5x or 1x + 2x)
        # Let's show 16px wide (64px) pure transparent vine on checkerboard on the left,
        # and 32px wide (128px) overlaid on `dark_slate_pillar_side` on the right!
        chk = make_checkerboard(64, strip_h * scale, cell=8)
        raw_strip = Image.new("RGBA", (16, strip_h), (0, 0, 0, 0))
        over_strip = Image.new("RGBA", (32, (n_blocks + 2) * 16), (0, 0, 0, 255))

        # Top & bottom cap with clean pillar_side on the overlaid preview
        for tx in range(2):
            over_strip.paste(pillar_side, (tx * 16, 0))
            over_strip.paste(pillar_side, (tx * 16, (n_blocks + 1) * 16))

        for i, nm in enumerate(names):
            vim = vine_imgs[nm]
            raw_strip.paste(vim, (0, i * 16))
            for tx in range(2):
                cell_bg = pillar_side.copy()
                cell_bg.alpha_composite(vim)
                over_strip.paste(cell_bg, (tx * 16, (i + 1) * 16))

        raw_up = raw_strip.resize((64, strip_h * scale), Image.Resampling.NEAREST)
        chk.alpha_composite(raw_up)

        y_top = 124
        # Paste pure vine aligned with middle of the sandwiched pillar (offset by +64px for the top pillar cap)
        canvas.paste(chk, (x0 + 4, y_top + 64))
        # Draw slice lines on pure vine
        for i, nm in enumerate(names):
            sy = y_top + 64 + i * 64
            draw.rectangle([x0 + 4, sy, x0 + 68, sy + 64], outline=(90, 75, 130, 180))
            short = nm.replace("corrupted_vine_corruption", "c")
            draw.text((x0 + 72, sy + 24), short, fill=(210, 215, 235, 255))

        # Paste 2x-wide sandwiched pillar + vine overlay on the right
        over_up = over_strip.resize((112, (n_blocks + 2) * 56), Image.Resampling.NEAREST)
        # Wait: let's keep exact 4x scale (64px per block) so slices align 1:1 horizontally!
        over_1x = Image.new("RGBA", (16, (n_blocks + 2) * 16))
        over_1x.paste(pillar_side, (0, 0))
        over_1x.paste(pillar_side, (0, (n_blocks + 1) * 16))
        for i, nm in enumerate(names):
            cell_bg = pillar_side.copy()
            cell_bg.alpha_composite(vine_imgs[nm])
            over_1x.paste(cell_bg, (0, (i + 1) * 16))
        canvas.paste(over_1x.resize((64, (n_blocks + 2) * 64), Image.Resampling.NEAREST), (x0 + 110, y_top))
        # Also 1 more column right next to it to show 2x horizontal connection!
        canvas.paste(over_1x.resize((64, (n_blocks + 2) * 64), Image.Resampling.NEAREST), (x0 + 174, y_top))

    # Rightmost column: Placement Count Progression Demo (1 -> 2 -> 3 -> 4 placed on the same block!)
    px0 = 1090
    draw.rectangle([px0 - 6, 58, px0 + 155, 740], fill=(24, 27, 34, 255), outline=(90, 70, 140, 255))
    draw.text((px0, 64), "Placement Growth", fill=(240, 220, 150, 255))
    draw.text((px0, 82), "(1x -> 2x -> 3x -> 4x):", fill=(195, 185, 225, 255))

    demo_stages = [
        ("1x (c=0_a)", "corrupted_vine_corruption0_a"),
        ("2x (c=1)", "corrupted_vine_corruption1"),
        ("3x (c=2_a)", "corrupted_vine_corruption2_a"),
        ("4x (c=3_a)", "corrupted_vine_corruption3_a"),
    ]
    for idx, (label, vname) in enumerate(demo_stages):
        yy = 116 + idx * 150
        draw.text((px0, yy), label, fill=(220, 225, 240, 255))
        # Pure transparent vine on 64x64 checkerboard
        c_box = make_checkerboard(64, 64, cell=8)
        c_box.alpha_composite(vine_imgs[vname].resize((64, 64), Image.Resampling.NEAREST))
        canvas.paste(c_box, (px0, yy + 18))
        # Overlaid on dark_slate_pillar_side
        ov = pillar_side.copy()
        ov.alpha_composite(vine_imgs[vname])
        canvas.paste(ov.resize((64, 64), Image.Resampling.NEAREST), (px0 + 74, yy + 18))
        draw.text((px0 + 4, yy + 86), "Alpha       On Pillar", fill=(150, 160, 180, 255))

    out_preview = PREVIEW_DIR / "extracted_corruption_vine_preview.png"
    canvas.save(out_preview)
    print(f"\n🖼️ 透明腐化藤蔓提取預覽圖已輸出至: {out_preview.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
