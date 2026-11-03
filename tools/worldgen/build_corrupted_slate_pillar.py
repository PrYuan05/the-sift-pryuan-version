#!/usr/bin/env python3
"""
build_corrupted_slate_pillar.py
===============================
Generates the 14 coordinated textures for the Purple Corrupted Pillar assembly:
  - `textures/block/dark_slate_pillar/dark_slate_pillar_top.png`
  - `textures/block/dark_slate_pillar/dark_slate_pillar_bottom.png` (100% identical to top)
  - `textures/block/dark_slate_pillar/dark_slate_pillar_side.png`
  - `textures/block/corrupted_slate/corrupted_slate_corruption0_a.png`
  - `textures/block/corrupted_slate/corrupted_slate_corruption0_b.png`
  - `textures/block/corrupted_slate/corrupted_slate_corruption1.png`
  - `textures/block/corrupted_slate/corrupted_slate_corruption2_a.png` .. `e.png`
  - `textures/block/corrupted_slate/corrupted_slate_corruption3_a.png` .. `c.png`

Design Workflow (per user instructions):
  1. **Base Pillar Calibration (Eliminating Top/Bottom Shadow Banding)**:
     - Starts from the user's uploaded dark slate pillar base (`media_1793103000901_cd84f65e.png`).
     - In the original image, rows `0..4` and `13..15` had a dark horizontal shadow band (`1`/`3` = `#353A42`/`#3A3F44`)
       across the pillar ridges, which created a visible dark seam when stacked vertically, while rows `6..11` in the
       center had lighter ridges (`6`/`8` = `#444750`/`#4B4D57`) and deep vertical grooves (`0`/`1` = `#313740`/`#353A42`).
     - We calibrate the top and bottom connecting rows (`y=0..4` and `y=12..15`) so their ridge colors match the
       lighter center (`#444750` ~ `#4B4D57`) while keeping the 4 deep vertical grooves (`x = 2, 6, 9, 13`) continuous
       from `y=0` to `y=15`!
  2. **Tall Strip Painting -> 16x16 Slicing (Vertical + Horizontal Vine Continuity)**:
     - Instead of drawing isolated 16x16 tiles with vines only in the middle, we paint **full tall vertical pillar strips**
       (`16x32` for `corruption=0`, `16x16` cyclic for `corruption=1`, `16x80` 5-block strip for `corruption=2`, and
       `16x48` 3-block strip for `corruption=3`) where purple vines/tendrils grow continuously across the `y=0 / y=15`
       top/bottom boundaries AND wrap left/right across `x=0 / x=15`!
     - Because all vertical cuts pass through consistent top/bottom vine anchor points (`x = 2, 6, 9, 13` grooves and
       adjacent ribs), the end of a vine on an upper block connects directly into the start of a vine on the lower block!
"""

from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import art_guard

ASSETS = ROOT / "src" / "main" / "resources" / "assets" / "pysift"
PILLAR_DIR = ASSETS / "textures" / "block" / "dark_slate_pillar"
CORRUPTED_DIR = ASSETS / "textures" / "block" / "corrupted_slate"
PREVIEW_DIR = ROOT / "build" / "previews"
MANIFEST_PATH = ROOT / "tools" / "texture_pipeline" / "recolor_manifest.json"
BACKUP_DIR = ROOT / ".texture_backups" / "20261027-194500_corrupted_slate_pillar"

# ==============================================================================
# 1. PALETTE: Exact Base Pillar Swatches + High-Contrast True Violet Vines
# ==============================================================================
# Base Pillar Swatches (0..8) from `media_1793103000901_cd84f65e.png`:
BASE_COLORS: dict[str, str] = {
    "0": "#313740",  # Deepest vertical groove shadow
    "1": "#353A42",  # Deep groove edge
    "2": "#373C44",  # Dark slate transition
    "3": "#3A3F44",  # Lower-mid slate shadow
    "4": "#3D4149",  # Mid-dark slate
    "5": "#42464C",  # Mid slate flute face
    "6": "#444750",  # Upper-mid slate flute face (center tone)
    "7": "#494C54",  # Bright slate ridge transition
    "8": "#4B4D57",  # Brightest center slate ridge highlight
    # Extra deep crevice for Pillar Top/Bottom carving only:
    "K": "#272B33",
}

# High-Contrast True Violet Vine Palette (H = 264° ~ 272°, strong luminance contrast):
VINE_COLORS: dict[str, str] = {
    "P": "#C49BFF",  # Bright glowing violet vine tip / node highlight (Lum ~ 0.69)
    "L": "#9E6EE8",  # Lit purple main vine body (Lum ~ 0.52)
    "V": "#7B4BC7",  # Mid purple vine stem / tendril (Lum ~ 0.38)
    "W": "#5A319E",  # Deep violet vine shadow / bark edge (Lum ~ 0.26)
    "U": "#3E2170",  # Darkest purple-slate root / groove taint (Lum ~ 0.17)
}

PALETTE: dict[str, str] = {**BASE_COLORS, **VINE_COLORS}


def hex_rgba(h: str) -> tuple[int, int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def grid_to_image(rows: list[str]) -> Image.Image:
    h = len(rows)
    w = len(rows[0])
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    px = img.load()
    for y, r in enumerate(rows):
        assert len(r) == w, f"Row {y} length {len(r)} != {w}: {r!r}"
        for x, ch in enumerate(r):
            px[x, y] = hex_rgba(PALETTE[ch])
    return img


def sha1_file(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


# ==============================================================================
# 2. SEAMLESS BASE PILLAR (`dark_slate_pillar_side.png`)
# ==============================================================================
# Compare with the uploaded image:
# Original rows 6..11 (the lighter center of the pillar):
#   row 6: 8506550860886156
#   row 7: 8808851880887186
#   row 8: 6808880860888088
#   row 9: 6806880660888088
#   row10: 6616860651885085
#   row11: 6516550650585055
# Notice how in the center rows 6..11:
#   - Cols `2, 6, 9, 13` are the 4 vertical dark grooves (`0` or `1` = `#313740` / `#353A42`).
#   - The ridges between the grooves (`cols 0..1`, `3..5`, `7..8`, `10..12`, `14..15`) use the lighter
#     center tones `5, 6, 7, 8` (`#42464C` ~ `#4B4D57`).
# By replacing the dark top/bottom shadow bands (rows `0..5` and `12..15`) with the same lighter center
# ridge tones (`5, 6, 7, 8`) and continuous grooves (`0, 1` at `x = 2, 6, 9, 13`), stacking the pillar
# vertically produces ZERO dark horizontal seam!

BASE_PILLAR_SIDE_ROWS: list[str] = [
    "6806860860886086",  # y=0  (matches y=15 seamlessly, light center tones!)
    "6606850660885166",  # y=1
    "6516650650685065",  # y=2
    "6505650650665056",  # y=3
    "6606650660685066",  # y=4
    "8606850860886066",  # y=5
    "8506550860886156",  # y=6  (original center row 6)
    "8808851880887186",  # y=7  (original center row 7)
    "6808880860888088",  # y=8  (original center row 8)
    "6806880660888088",  # y=9  (original center row 9)
    "6616860651885085",  # y=10 (original center row 10)
    "6516550650585055",  # y=11 (original center row 11)
    "6505660650685056",  # y=12 (lightened from original to remove bottom shadow)
    "6606650660685166",  # y=13
    "6806850860886086",  # y=14
    "6806860860886086",  # y=15 (connects straight into y=0 with zero dark shadow!)
]


# ==============================================================================
# 3. PILLAR TOP & BOTTOM (`dark_slate_pillar_top.png` == `dark_slate_pillar_bottom.png`)
# ==============================================================================
# Calibrated to the exact same `#4B4D57` (`8`) .. `#313740` (`0`) dark slate palette, with outer edge
# notches at `2, 6, 9, 13` matching the 4 vertical grooves of `BASE_PILLAR_SIDE_ROWS`!
PILLAR_TOP_ROWS: list[str] = [
    "6806860860886086",
    "8818881881888186",
    "0100000000000010",
    "6807888888886086",
    "8808555555545086",
    "6808511111145085",
    "0108516887145010",
    "8808518766145086",
    "6808518656145086",
    "0108517665145010",
    "8808511111145086",
    "8808444444435085",
    "6806655555554086",
    "0100000000000010",
    "6816861861885165",
    "6806860860886086",
]


def overlay_vines(base_rows: list[str], vine_mask: list[str]) -> list[str]:
    """
    Overlays a vine mask (`'.'` = keep base pillar pixel, any palette char = paint vine/crack pixel)
    onto a tall pillar strip created by repeating `BASE_PILLAR_SIDE_ROWS`.
    """
    h = len(vine_mask)
    assert h % 16 == 0, f"Strip height {h} must be a multiple of 16"
    out: list[str] = []
    for y in range(h):
        base_r = base_rows[y % 16]
        mask_r = vine_mask[y]
        assert len(mask_r) == 16, f"Mask row {y} length {len(mask_r)} != 16: {mask_r!r}"
        row_chars = [base_r[x] if mask_r[x] == "." else mask_r[x] for x in range(16)]
        out.append("".join(row_chars))
    return out


def slice_strip(strip_rows: list[str]) -> list[list[str]]:
    """Slices a `16 x (16*N)` tall pillar strip into `N` individual `16x16` block textures."""
    n = len(strip_rows) // 16
    return [strip_rows[i * 16 : (i + 1) * 16] for i in range(n)]


# ==============================================================================
# 4. TALL PILLAR STRIPS FOR CORRUPTED SLATE (SLICED INTO 16x16 TILES)
# ==============================================================================
# Key Rule for Multi-Directional & Vertical Vine Continuity:
#   - Every `16x16` slice has **matching top (`y=0`) and bottom (`y=15`) vine anchor points**!
#   - When any block's bottom (`y=15`) meets another block's top (`y=0`), the vine stems at the
#     vertical boundary connect directly (上方方塊的藤蔓結尾連接下方方塊的藤蔓)!
#   - Moreover, within each tall strip, lateral branches and tendrils reach across the left (`x=0`)
#     and right (`x=15`) edges so horizontal adjacency also forms connected vine networks.

# ------------------------------------------------------------------------------
# STAGE 0: `16 x 32` Tall Strip (2 blocks high -> `corruption0_a` and `corruption0_b`)
# ------------------------------------------------------------------------------
# Nascent violet rootlets and hairline cracks creeping continuously along Grooves 1 (`x=2`) and 3 (`x=9`),
# with fine lateral tendrils branching between them.
# Anchor at `y % 16 == 0` and `y % 16 == 15`: nascent violet root at `x=2` (`W/U`) and `x=9` (`U/W`).
STRIP_CORRUPTION_0_MASK: list[str] = [
    # === Slice 0: `corrupted_slate_corruption0_a` (y = 0..15) ===
    "..W......U......",  # y=0  (top boundary anchor: connects to y=15 below)
    "..W......W......",  # y=1
    "..V......W...U..",  # y=2
    "..W.U....V...W..",  # y=3
    "..U.W....W...W..",  # y=4
    "..U..W...U...U..",  # y=5
    ".....W...U......",  # y=6
    "..U..V..U.......",  # y=7
    "..W..W..W.......",  # y=8
    "..V..U..W.......",  # y=9
    "..W.....V.U.....",  # y=10
    "..U.....W.W.....",  # y=11
    "......U.U.W.....",  # y=12
    "..U...W...U.....",  # y=13
    "..W...U..U......",  # y=14
    "..W......U......",  # y=15 (bottom boundary anchor -> connects straight into Slice 1 y=16!)
    # === Slice 1: `corrupted_slate_corruption0_b` (y = 16..31) ===
    "..W......U......",  # y=16 (top boundary anchor: receives vine from y=15!)
    "..V......W......",  # y=17
    "..W..U...V......",  # y=18
    "..U..W...W..U...",  # y=19
    ".....V...U..W...",  # y=20
    ".....W......V...",  # y=21
    "..U..U..U...W...",  # y=22
    "..W.....W...U...",  # y=23
    "..W....UV.......",  # y=24
    "..V...UW........",  # y=25
    "..W..WU..U......",  # y=26
    "..U..V...W...U..",  # y=27
    ".....W...V...W..",  # y=28
    "..U..U...W...U..",  # y=29
    "..W......U......",  # y=30
    "..W......U......",  # y=31 (bottom boundary anchor -> loops seamlessly to y=0!)
]

# ------------------------------------------------------------------------------
# STAGE 1: `16 x 16` Continuous Vine Strip (`corruption1`)
# ------------------------------------------------------------------------------
# Two main climbing vine stems at `x=1..3` and `x=8..10` run unbroken from `y=0` to `y=15`,
# while lateral offshoots branch out left-to-right (`x=0` <-> `x=15`) and diagonally across the flutes!
STRIP_CORRUPTION_1_MASK: list[str] = [
    ".WLU....WLU..U..",  # y=0  (top vine anchor at x=1..3 and x=8..10, plus x=13)
    ".WLVU...WLV..W..",  # y=1
    "..WLVU...WLU.V..",  # y=2
    "...WLV....WLVW..",  # y=3
    "U..UWLV....WLW..",  # y=4  (wraps across x=0 / x=15)
    "WU..WLVU...VLW.U",  # y=5
    "VW..UWLV..UVLW.W",  # y=6
    ".WU..WLVU.WLPW.V",  # y=7
    ".VW.UWLPW.VLPW.W",  # y=8
    "..WUWLPW..WLVU.U",  # y=9
    "..VWLPV...WLV...",  # y=10
    "..WLPW...UWLVU..",  # y=11
    ".UWLVU..UWLVWU..",  # y=12
    ".WLVU...WLV..W..",  # y=13
    ".WLV....WLU..W..",  # y=14
    ".WLU....WLU..U..",  # y=15 (bottom vine anchor: matches y=0 & connects into Stage 2!)
]

# ------------------------------------------------------------------------------
# STAGE 2: `16 x 80` Tall 5-Block Pillar Strip (`corruption2_a` .. `corruption2_e`)
# ------------------------------------------------------------------------------
# Drawn as ONE continuous 5-block-tall (`16x80`) climbing vine network and then sliced into 5 `16x16` blocks!
# All 5 block boundaries (`y = 0, 15/16, 31/32, 47/48, 63/64, 79`) share the primary vertical vine stems
# at `x=1..3`, `x=8..10`, and `x=13..14` so ANY combination of `2_a..2_e` (or `corruption1` / `corruption3`)
# stacked vertically connects its top/bottom vine tips without breaking, while each slice features distinct
# multi-directional lateral branches (left-to-right wraps, forks, diagonal bridges, and curling tendrils)!
STRIP_CORRUPTION_2_MASK: list[str] = [
    # === Slice 0: `corrupted_slate_corruption2_a` (y = 0..15) — Upward S-curve + Left-to-Right branch ===
    ".WLU....WLVU.WU.",  # y=0  (Top seam anchor)
    ".WLVU...WLPW.VW.",  # y=1
    "..WLPW..VLPU.VW.",  # y=2
    "..VLPWU.WLV..UW.",  # y=3
    "U..WLPWUWLVU..W.",  # y=4  (Left/Right wrap starts)
    "WU..WLPWLPWU..WU",  # y=5
    "VW...WLPLPW..UWV",  # y=6
    "LVU..UWLPW..UWLW",  # y=7
    "LPWU..WLPW.UWLPV",  # y=8  (Horizontal wrap across x=15 -> x=0)
    "WLPW.UWLPV.WLPWU",  # y=9
    "UWLPWWLPVU.VLPW.",  # y=10
    ".UWLPWLVU..WLVU.",  # y=11
    ".WLPWLVU...WLV..",  # y=12
    ".WLPVWU....WLPW.",  # y=13
    ".WLVU......WLPW.",  # y=14
    ".WLU....WLVU.WU.",  # y=15 (Bottom seam anchor -> connects into y=16!)

    # === Slice 1: `corrupted_slate_corruption2_b` (y = 16..31) — Dual Forking Vines & Cross-Flute Tendrils ===
    ".WLU....WLVU.WU.",  # y=16 (Top seam anchor: receives vine from y=15)
    ".WLPW...WLPW.VW.",  # y=17
    ".VLPLW.UWLPV.UW.",  # y=18
    "UWLPVW.WLPWU..WU",  # y=19
    "WLPW.WUWLPW..UWV",  # y=20
    "VLPW.VWLPV..UWLW",  # y=21
    "WLVU..WLPW.UWLPV",  # y=22
    "UWU...VLPWUWLPWU",  # y=23
    ".U...UWLPLPLPW..",  # y=24
    "....UWLPVWLPWU..",  # y=25
    "...UWLPV.WLPW...",  # y=26
    "..UWLPV..VLPWU..",  # y=27
    ".UWLPV...WLPW.U.",  # y=28
    ".WLPWU...WLVU.W.",  # y=29
    ".WLVU....WLV..WU",  # y=30
    ".WLU....WLVU.WU.",  # y=31 (Bottom seam anchor -> connects into y=32!)

    # === Slice 2: `corrupted_slate_corruption2_c` (y = 32..47) — Sweeping Diagonal & Horizontal Vine Web ===
    ".WLU....WLVU.WU.",  # y=32 (Top seam anchor)
    ".WLVU...WLPW.VW.",  # y=33
    ".WLPWU..VLPW.UW.",  # y=34
    "..WLPW..WLPWU.WU",  # y=35
    "..VLPWU.UWLPW.WV",  # y=36
    "...WLPW..WLPWUWV",  # y=37
    "U...WLPW..WLPWLV",  # y=38
    "WU..UWLPW.UWLPWL",  # y=39
    "LPW..WLPWU.WLPWL",  # y=40 (Crosses left-right border x=15 -> x=0)
    "WLPW..WLPW..WLPW",  # y=41
    "UWLPW.UWLPW.VLPW",  # y=42
    ".UWLPW.WLPWUWLVU",  # y=43
    ".WLPWU.VLPW.WLV.",  # y=44
    ".WLVU..WLPW.WLU.",  # y=45
    ".WLV...WLVU..WU.",  # y=46
    ".WLU....WLVU.WU.",  # y=47 (Bottom seam anchor -> connects into y=48!)

    # === Slice 3: `corrupted_slate_corruption2_d` (y = 48..63) — Counter-Diagonal & Arching Tendril Bridge ===
    ".WLU....WLVU.WU.",  # y=48 (Top seam anchor)
    ".WLV...UWLPW.VW.",  # y=49
    ".WLPW.UWLPV..V..",  # y=50
    ".VLPWUWLPWU..W..",  # y=51
    ".UWLPWLPW...UWU.",  # y=52
    "..WLPLPV...UWLW.",  # y=53
    ".UWLPVW...UWLPVU",  # y=54
    "UWLPV.U..UWLPVW.",  # y=55
    "WLPWU...UWLPV...",  # y=56
    "VLPW...UWLPV....",  # y=57
    "WLPWU.UWLPV..U..",  # y=58
    "UWLPWUWLPW...W..",  # y=59
    ".UWLPWLPW...UWU.",  # y=60
    ".WLPWLVU....WLV.",  # y=61
    ".WLVU.WU....WLU.",  # y=62
    ".WLU....WLVU.WU.",  # y=63 (Bottom seam anchor -> connects into y=64!)

    # === Slice 4: `corrupted_slate_corruption2_e` (y = 64..79) — Lateral Ringing Vine & Multi-Flute Anastomosis ===
    ".WLU....WLVU.WU.",  # y=64 (Top seam anchor)
    ".WLPW...WLPW.VW.",  # y=65
    ".VLPWU.UWLPV.UW.",  # y=66
    ".UWLPW.WLPWU.WV.",  # y=67
    "..WLPWUWLPW.UWLW",  # y=68
    "U.VLPWLPW..UWLPV",  # y=69
    "WUWLPWLPW.UWLPVW",  # y=70
    "LPWLPWLPWUWLPV.U",  # y=71 (Full horizontal & vertical vine nexus)
    "VLPLPVLPLPLPV...",  # y=72
    "UWLPW.WLPWLPW...",  # y=73
    ".WLPW.VLPWLPWU..",  # y=74
    ".WLPWUWLPW.WLPW.",  # y=75
    ".VLPW.WLPW.VLPW.",  # y=76
    ".WLVU.WLVU.WLVU.",  # y=77
    ".WLV..WLV...WLU.",  # y=78
    ".WLU....WLVU.WU.",  # y=79 (Bottom seam anchor -> loops to y=0 & connects into Stage 3!)
]

# ------------------------------------------------------------------------------
# STAGE 3: `16 x 48` Tall 3-Block Pillar Strip (`corruption3_a` .. `corruption3_c`)
# ------------------------------------------------------------------------------
# Drawn as ONE continuous 3-block-tall (`16x48`) heavy overgrown violet vine column and sliced into 3 `16x16` blocks!
# Thick glowing purple vines (`P/L/V/W`) climb across all 4 vertical grooves (`x=1..3`, `5..7`, `8..10`, `12..14`)
# and wrap across `x=0 / x=15`, while keeping dark slate pillar ribs peeking through so the vertical column structure
# remains unmistakably readable!
STRIP_CORRUPTION_3_MASK: list[str] = [
    # === Slice 0: `corrupted_slate_corruption3_a` (y = 0..15) — Heavy Overgrown Vines Climbing & Branching ===
    ".WLPW..UWLPW.WLU",  # y=0  (Heavy top seam anchor — aligns with Stage 2 stems + thicker overgrowth)
    ".WLPLW.WLPW..WLV",  # y=1
    "U.WLPLWLPV..UWLP",  # y=2
    "W.VLPPLPW..UWLPV",  # y=3
    "LWUWLPPLW.UWLPLW",  # y=4
    "LPW.WLPLWUWLPPLV",  # y=5
    "PLPW.WLPLPLPPLW.",  # y=6
    "WLPWUWLPPLPLPW..",  # y=7
    "UWLPWLPLPWLPWU.U",  # y=8
    ".WLPPLPV.VLPW.UW",  # y=9
    ".VLPLPW..WLPWUWV",  # y=10
    "UWLPVW...WLPLPLW",  # y=11
    "WLPW.U...VLPPLPV",  # y=12
    "VLPW....UWLPLPWU",  # y=13
    "WLPWU..UWLPV.WLV",  # y=14
    ".WLPW..UWLPW.WLU",  # y=15 (Heavy bottom seam anchor -> connects straight into y=16!)

    # === Slice 1: `corrupted_slate_corruption3_b` (y = 16..31) — Criss-Crossing Violet Vine Canopy ===
    ".WLPW..UWLPW.WLU",  # y=16 (Top seam anchor: receives thick vines from y=15!)
    "UWLPLW.WLPWU.WLV",  # y=17
    "WLPPLWUWLPW.UWLP",  # y=18
    "VLPWLPWLPW.UWLPV",  # y=19
    "WLPWWLPLPWUWLPW.",  # y=20
    "UWLPWLPLPLPLPW..",  # y=21
    ".WLPPLPVWLPLPW.U",  # y=22
    ".VLPLPW.VLPPLWUW",  # y=23
    "UWLPVW..UWLPPLPL",  # y=24
    "WLPW....UWLPLPPL",  # y=25
    "LPWU...UWLPVWLPV",  # y=26
    "PLPW..UWLPV.WLPW",  # y=27
    "WLPW.UWLPV..VLPW",  # y=28
    "UWLPWWLPV...WLPW",  # y=29
    ".WLPLPLW...UWLVU",  # y=30
    ".WLPW..UWLPW.WLU",  # y=31 (Bottom seam anchor -> connects straight into y=32!)

    # === Slice 2: `corrupted_slate_corruption3_c` (y = 32..47) — Dense Blooming Violet Vine Root-Work ===
    ".WLPW..UWLPW.WLU",  # y=32 (Top seam anchor: receives thick vines from y=31!)
    ".VLPLW.VLPW..WLV",  # y=33
    ".UWLPLWWLPWU.WLP",  # y=34
    "..WLPLPLPLPWUWLP",  # y=35
    "U.VLPPLPPLPLPLPV",  # y=36
    "WUWLPWLPWWLPPLW.",  # y=37
    "LPWLPW.WUWLPPLW.",  # y=38
    "PLPLPV..VWLPLPWU",  # y=39
    "WLPLPW..UWLPWLPW",  # y=40
    "UWLPWU...WLPWLPW",  # y=41
    ".WLPW...UWLPLPLV",  # y=42
    ".VLPWU.UWLPLPPLW",  # y=43
    ".UWLPWUWLPW.WLPW",  # y=44
    "..WLPLPLPW..VLPW",  # y=45
    ".UWLPLLPW...WLVU",  # y=46
    ".WLPW..UWLPW.WLU",  # y=47 (Bottom seam anchor -> loops to y=0!)
]


def build_all_corrupted_textures() -> tuple[dict[str, Image.Image], dict[str, Image.Image]]:
    """
    First builds the full tall pillar strips (`16x32`, `16x16`, `16x80`, `16x48`),
    then slices them into the 11 `16x16` block textures.
    Returns `(corrupted_imgs_dict, tall_strips_dict)`.
    """
    s0_rows = overlay_vines(BASE_PILLAR_SIDE_ROWS, STRIP_CORRUPTION_0_MASK)
    s1_rows = overlay_vines(BASE_PILLAR_SIDE_ROWS, STRIP_CORRUPTION_1_MASK)
    s2_rows = overlay_vines(BASE_PILLAR_SIDE_ROWS, STRIP_CORRUPTION_2_MASK)
    s3_rows = overlay_vines(BASE_PILLAR_SIDE_ROWS, STRIP_CORRUPTION_3_MASK)

    tall_strips = {
        "strip_c0 (16x32)": grid_to_image(s0_rows),
        "strip_c1 (16x16)": grid_to_image(s1_rows),
        "strip_c2 (16x80)": grid_to_image(s2_rows),
        "strip_c3 (16x48)": grid_to_image(s3_rows),
    }

    c0_slices = slice_strip(s0_rows)
    c1_slices = slice_strip(s1_rows)
    c2_slices = slice_strip(s2_rows)
    c3_slices = slice_strip(s3_rows)

    corrupted_imgs: dict[str, Image.Image] = {
        "corrupted_slate_corruption0_a": grid_to_image(c0_slices[0]),
        "corrupted_slate_corruption0_b": grid_to_image(c0_slices[1]),
        "corrupted_slate_corruption1": grid_to_image(c1_slices[0]),
        "corrupted_slate_corruption2_a": grid_to_image(c2_slices[0]),
        "corrupted_slate_corruption2_b": grid_to_image(c2_slices[1]),
        "corrupted_slate_corruption2_c": grid_to_image(c2_slices[2]),
        "corrupted_slate_corruption2_d": grid_to_image(c2_slices[3]),
        "corrupted_slate_corruption2_e": grid_to_image(c2_slices[4]),
        "corrupted_slate_corruption3_a": grid_to_image(c3_slices[0]),
        "corrupted_slate_corruption3_b": grid_to_image(c3_slices[1]),
        "corrupted_slate_corruption3_c": grid_to_image(c3_slices[2]),
    }
    return corrupted_imgs, tall_strips


def update_recolor_manifest(written_files: list[tuple[Path, str]]) -> None:
    if not MANIFEST_PATH.exists():
        return
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    by_file = {e["file"]: e for e in data.get("entries", [])}
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    for path, pool_name in written_files:
        rel = path.relative_to(ASSETS).as_posix()
        bkp_sub = "dark_slate_pillar" if "dark_slate_pillar" in rel else "corrupted_slate"
        bkp_file = BACKUP_DIR / bkp_sub / path.name
        sha_before = sha1_file(bkp_file) if bkp_file.exists() else None
        sha_after = sha1_file(path)
        prev = by_file.get(rel, {})
        by_file[rel] = {
            "file": rel,
            "pool": pool_name,
            "reference": "pysift:block/dark_slate/dark_slate_l",
            "source": prev.get("source", rel),
            "mode": "tall_strip_vine_pillar_sliced",
            "method": "minecraft_texture_crafter",
            "sha1_before": prev.get("sha1_before") or sha_before,
            "sha1_after": sha_after,
            "backup": bkp_file.relative_to(ROOT).as_posix() if bkp_file.exists() else prev.get("backup"),
            "date": stamp,
        }

    data["entries"] = [by_file[k] for k in sorted(by_file.keys())]
    MANIFEST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_tall_strip_preview(
    pillar_top: Image.Image,
    pillar_side: Image.Image,
    corrupted_imgs: dict[str, Image.Image],
    tall_strips: dict[str, Image.Image],
) -> Path:
    """
    Renders a comprehensive preview showing:
      1. Base Pillar seam fix comparison (`pillar_side` stacked 3x vertically with NO dark horizontal seam, plus `pillar_top == bottom`).
      2. The Tall Continuous Pillar Strips BEFORE and AFTER slicing (`16x32` for c=0, `16x32` 2x loop for c=1, `16x80` for c=2, `16x48` for c=3),
         sandwiched between `dark_slate_pillar_side` at top and bottom, plus 2x horizontal width to show left-right vine wrapping!
      3. Mixed random vertical permutations & progressive tower (`pillar_side -> c0 -> c1 -> c2 -> c3 -> pillar_side`) proving that
         any block's upper vine tip connects into the lower block's vine stem!
    """
    canvas = Image.new("RGBA", (1260, 820), (18, 20, 25, 255))
    draw = ImageDraw.Draw(canvas)

    draw.rectangle([0, 0, 1260, 46], fill=(30, 34, 44, 255))
    draw.text(
        (16, 14),
        "The Sift - Tall Continuous Vine Pillar Strips -> Sliced 16x16 Blocks (No Seam Shadow + Connected Vines)",
        fill=(235, 240, 250, 255),
    )

    scale = 4  # 16px -> 64px per block

    # Column 1: Base Pillar Side (3x vertical stack) & Top/Bottom
    col1_x = 20
    draw.rectangle([col1_x - 6, 58, col1_x + 210, 800], fill=(25, 28, 35, 255), outline=(50, 56, 70, 255))
    draw.text((col1_x, 64), "1. Base Pillar (No Shadow Seam)", fill=(240, 220, 150, 255))
    draw.text((col1_x, 82), "pillar_top == pillar_bottom:", fill=(190, 200, 220, 255))
    canvas.paste(pillar_top.resize((64, 64), Image.Resampling.NEAREST), (col1_x, 102))
    canvas.paste(pillar_top.resize((64, 64), Image.Resampling.NEAREST), (col1_x + 76, 102))

    draw.text((col1_x, 180), "pillar_side (4x vertical stack):", fill=(190, 200, 220, 255))
    draw.text((col1_x, 196), "(Top/Bottom match light center)", fill=(145, 155, 175, 255))
    p_stack = Image.new("RGBA", (32, 64))
    for py in range(4):
        for px in range(2):
            p_stack.paste(pillar_side, (px * 16, py * 16))
    canvas.paste(p_stack.resize((128, 256), Image.Resampling.NEAREST), (col1_x, 218))
    draw.text((col1_x + 134, 240), "<- 2x4 tiled", fill=(150, 160, 180, 255))

    # Progressive 6-block tower at bottom of Col 1
    draw.text((col1_x, 490), "Progressive Tower (0->1->2->3):", fill=(240, 220, 150, 255))
    prog_blocks = [
        pillar_side,
        corrupted_imgs["corrupted_slate_corruption0_a"],
        corrupted_imgs["corrupted_slate_corruption1"],
        corrupted_imgs["corrupted_slate_corruption2_a"],
        corrupted_imgs["corrupted_slate_corruption3_a"],
        pillar_side,
    ]
    prog_im = Image.new("RGBA", (16, 16 * len(prog_blocks)))
    for i, im in enumerate(prog_blocks):
        prog_im.paste(im, (0, i * 16))
    canvas.paste(prog_im.resize((48, 48 * len(prog_blocks)), Image.Resampling.NEAREST), (col1_x, 510))
    for i, lbl in enumerate(["pillar", "c=0_a", "c=1", "c=2_a", "c=3_a", "pillar"]):
        draw.text((col1_x + 56, 526 + i * 48), lbl, fill=(180, 190, 210, 255))

    # Columns 2..5: The 4 Tall Strips (c=0 16x32, c=1 16x32, c=2 16x80, c=3 16x48)
    # For each strip, we show:
    #   - Left: Continuous tall strip sandwiched between `pillar_side` (1x width = 64px) with dashed slice guides
    #   - Right: 2x horizontal tiled strip (128px wide) so you can see both vertical AND left/right vine connections!
    strip_configs = [
        (
            "2. corruption=0 (16x32 Strip)",
            ["corrupted_slate_corruption0_a", "corrupted_slate_corruption0_b"],
            250,
        ),
        (
            "3. corruption=1 (Stacked 2x)",
            ["corrupted_slate_corruption1", "corrupted_slate_corruption1"],
            495,
        ),
        (
            "4. corruption=2 (16x80 5-Block Strip)",
            [
                "corrupted_slate_corruption2_a",
                "corrupted_slate_corruption2_b",
                "corrupted_slate_corruption2_c",
                "corrupted_slate_corruption2_d",
                "corrupted_slate_corruption2_e",
            ],
            740,
        ),
        (
            "5. corruption=3 (16x48 3-Block Strip)",
            [
                "corrupted_slate_corruption3_a",
                "corrupted_slate_corruption3_b",
                "corrupted_slate_corruption3_c",
            ],
            1005,
        ),
    ]

    for title, slice_names, x0 in strip_configs:
        draw.rectangle([x0 - 6, 58, x0 + 235, 800], fill=(25, 28, 35, 255), outline=(50, 56, 70, 255))
        draw.text((x0, 64), title, fill=(240, 220, 150, 255))
        draw.text((x0, 82), "1x Column (with Top/Bot Pillar) & 2x Wide:", fill=(175, 185, 205, 255))

        # Build sandwiched column: [pillar_side] + slices + [pillar_side]
        all_blocks = [("pillar", pillar_side)] + [(n.replace("corrupted_slate_corruption", "c"), corrupted_imgs[n]) for n in slice_names] + [("pillar", pillar_side)]
        total_h = len(all_blocks) * 16
        col_1x = Image.new("RGBA", (16, total_h))
        col_2x = Image.new("RGBA", (32, total_h))
        for bi, (_, bim) in enumerate(all_blocks):
            col_1x.paste(bim, (0, bi * 16))
            col_2x.paste(bim, (0, bi * 16))
            col_2x.paste(bim, (16, bi * 16))

        y_start = 106
        canvas.paste(col_1x.resize((64, total_h * scale), Image.Resampling.NEAREST), (x0, y_start))
        canvas.paste(col_2x.resize((128, total_h * scale), Image.Resampling.NEAREST), (x0 + 96, y_start))

        # Draw slice boundary ticks & labels between 1x and 2x columns
        for bi, (blbl, _) in enumerate(all_blocks):
            by = y_start + bi * 64
            if bi > 0:
                draw.line([(x0 - 3, by), (x0 + 66, by)], fill=(140, 110, 200, 180), width=1)
            draw.text((x0 + 66, by + 24), blbl, fill=(210, 215, 235, 255))

    out_path = PREVIEW_DIR / "corrupted_slate_pillar_sandwich.png"
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return out_path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    PILLAR_DIR.mkdir(parents=True, exist_ok=True)
    CORRUPTED_DIR.mkdir(parents=True, exist_ok=True)

    written: list[tuple[Path, str]] = []

    # 1. Generate Pillar Top, Bottom (100% identical), and Seamless Base Pillar Side
    pillar_top_img = grid_to_image(PILLAR_TOP_ROWS)
    pillar_side_img = grid_to_image(BASE_PILLAR_SIDE_ROWS)

    top_path = PILLAR_DIR / "dark_slate_pillar_top.png"
    bot_path = PILLAR_DIR / "dark_slate_pillar_bottom.png"
    side_path = PILLAR_DIR / "dark_slate_pillar_side.png"

    for p, im, pool in [
        (top_path, pillar_top_img, "dark_slate_pillar:top"),
        (bot_path, pillar_top_img, "dark_slate_pillar:bottom"),
        (side_path, pillar_side_img, "dark_slate_pillar:side"),
    ]:
        if p.exists():
            art_guard.record(p)
        art_guard.save(im, p)
        written.append((p, pool))

    assert sha1_file(top_path) == sha1_file(bot_path), "dark_slate_pillar_top and bottom must be identical!"
    print("✅ 已修正柱子底圖上下連接處黑影（改為與中心淺色相近）並同步更新 dark_slate_pillar (top == bottom, side)！")

    # 2. Paint Tall Vine Pillar Strips (16x32, 16x16, 16x80, 16x48) and slice into 11 16x16 textures
    corrupted_imgs, tall_strips = build_all_corrupted_textures()
    for name, im in corrupted_imgs.items():
        out_p = CORRUPTED_DIR / f"{name}.png"
        if out_p.exists():
            art_guard.record(out_p)
        art_guard.save(im, out_p)
        stage = name.split("corruption")[1].split("_")[0]
        written.append((out_p, f"corrupted_slate:corruption={stage}"))
        print(f"  ✅ 已從長條柱切分生成: {out_p.relative_to(ROOT)}")

    # Also save the raw tall strips to build/previews/ for reference
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for sname, sim in tall_strips.items():
        safe = sname.split(" ")[0]
        sim.save(PREVIEW_DIR / f"{safe}.png")

    # 3. Update recolor_manifest.json
    update_recolor_manifest(written)

    # 4. Render Tall Strip & Sliced Pillar Preview
    preview_path = build_tall_strip_preview(pillar_top_img, pillar_side_img, corrupted_imgs, tall_strips)
    print(f"\n🖼️ 長條柱體切分與上下左右藤蔓連接預覽圖已輸出至: {preview_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
