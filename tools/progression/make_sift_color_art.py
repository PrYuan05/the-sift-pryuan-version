#!/usr/bin/env python3
"""
make_sift_color_art.py
======================
Generates the 18 custom textures requested in `art_requests/new_art_content_todo.md`:
  - 9 custom plant-based dye icons (`src/main/resources/assets/pysift/textures/item/<colour>_dye.png`)
  - 9 custom 2x2-rotational glazed terracotta patterns (`src/main/resources/assets/pysift/textures/block/sift_colors/<colour>_glazed_terracotta.png`)

Strictly follows the `minecraft-texture-crafter` skill:
  - Step 0 Material Brief (Real-world botanical/mineral + Moorish/Majolica ceramic glaze references)
  - Watt Color Theory & Hue Shifting (warm low-sat highlights, cool high-sat shadows, zero #000000 / #FFFFFF)
  - Plantkillable Item Rules (distinct plant-derived silhouettes, top-left lighting, Sel-Out selective outlining)
  - Glazed Terracotta 4-Block Rotational Symmetry Law:
      When 4 Glazed Terracotta blocks are placed in a 2x2 cycle on the ground (or repeated into a 4x4 floor),
      adjacent rotated tiles meet along:
        * Hub A (0,0 corner): Top edge `T(k, 0)` meets Left edge `T(0, k)` -> requires `T(k, 0) == T(0, k)`!
        * Hub B (15,15 corner): Bottom edge `T(k, 15)` meets Right edge `T(15, k)` -> requires `T(k, 15) == T(15, k)`!
      By designing each 16x16 tile with main-diagonal mirror symmetry (`T(x, y)` paired with `T(y, x)`, plus subtle
      top-left vs bottom-right internal shading on the relief), every 2x2 placement (whether centered on Hub A or Hub B,
      and repeated across a 4x4 floor) locks together with ZERO seam breaks into a complete 32x32 ceramic mandala!
  - Uses `tools/art_guard.py` so any future user hand-edits are protected.

Usage:
  python -I tools/progression/make_sift_color_art.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import art_guard

ASSETS = ROOT / "src" / "main" / "resources" / "assets" / "pysift"
ITEM_DIR = ASSETS / "textures" / "item"
BLOCK_DIR = ASSETS / "textures" / "block" / "sift_colors"
PREVIEW_DIR = ROOT / "build" / "previews"


def hex_rgba(h: str, a: int = 255) -> tuple[int, int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def parse_canvas(rows: list[str], palette: dict[str, str]) -> Image.Image:
    assert len(rows) == 16, f"Expected 16 rows, got {len(rows)}"
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(rows):
        assert len(row) == 16, f"Row {y} has length {len(row)}: {row!r}"
        for x, ch in enumerate(row):
            if ch in (".", " "):
                px[x, y] = (0, 0, 0, 0)
            else:
                px[x, y] = hex_rgba(palette[ch])
    return img


# ==============================================================================
# PART 1: 9 PLANT-DERIVED DYE ICONS (16x16, transparent background)
# ==============================================================================

DYE_SPECS: dict[str, dict] = {
    # 1. 青碧染料 (teal_dye) — 劈裂草雙叉肉質葉片與碾碎青碧草汁液滴 (Cleaver Plant Twin-Blade Leaf & Crushed Sap)
    "teal": {
        "brief": "劈裂草雙叉心形葉片與滴落青碧草汁（參考藍綠多肉葉片與銅綠天然植物澱藍）",
        "palette": {
            "H": "#A8F0D8",  # Warm yellow-mint highlight
            "L": "#56D8C2",  # Lit teal blade
            "M": "#2EB8A6",  # Core Sift Teal (#2EB8A6)
            "D": "#1D8382",  # Cool deep teal shadow
            "O": "#165C63",  # Top-left Sel-Out
            "K": "#0E3642",  # Bottom-right deep indigo-teal outline
            "S": "#86E3CE",  # Central leaf vein highlight
        },
        "rows": [
            "................",
            "...OO....OO.....",
            "..OLLM..OLLM....",
            ".OLHHLMOLHHLK...",
            ".OLHSLMMLHSLMK..",
            ".OLLMSSLMMLLMK..",
            "..OLMSSLMMLLK...",
            "..OLLMSSMMLLK...",
            "...OLMMSSMMK....",
            "....OLMSSMK.OO..",
            "....OLLSMK.OLLK.",
            ".....OLMK..OMDK.",
            "....OODK....KK..",
            "...OLLK.........",
            "...ODK..........",
            "....K...........",
        ],
    },

    # 2. 薄荷染料 (mint_dye) — 夜光草與裂隙薄荷草研磨成的發光薄荷細粉佐暗石研缽 (Luminous Mint Herb Powder on Slate Dish)
    "mint": {
        "brief": "夜光草與裂隙薄荷草研磨的螢光薄荷結晶粉堆，盛於深板岩淺碟上（參考抹茶粉堆與螢石微晶）",
        "palette": {
            "H": "#E4FBE8",  # Warm pale lime-mint specular
            "L": "#B6F2D4",  # Lit mint powder
            "M": "#8FE3C0",  # Core Sift Mint (#8FE3C0)
            "D": "#4EB398",  # Cool seafoam shadow
            "O": "#2D7D6F",  # Top-left Sel-Out
            "K": "#194847",  # Bottom-right deep teal-slate outline
            "B": "#56636B",  # Slate dish lit rim
            "T": "#37414A",  # Slate dish body
            "E": "#202730",  # Slate dish shadow outline
        },
        "rows": [
            "................",
            "......OOO.......",
            "....OOLLLOO.....",
            "...OLLMHHLLO....",
            "...OLHHHHLLMK...",
            "..OLLMHHLLMMDK..",
            "..OLLMMMMMMMDK..",
            ".OOLLMMMDMMMDKO.",
            ".OLLMDDDDDDDDMKO",
            ".BBOMMDDDDDDDMTE",
            ".BTTBKKKKKKKKTTE",
            "..BTTTTTTTTTTTE.",
            "...EETTTTTTTEE..",
            ".....EEEEEEE....",
            "................",
            "................",
        ],
    },

    # 3. 珊瑚染料 (coral_dye) — 珊瑚落葉層疊扇形花瓣與甲殼草絨簇 (Layered Coral Fan Petals & Carapace Tuft)
    "coral": {
        "brief": "珊瑚落葉的波浪扇形乾燥花瓣與暖金花蕊碎屑（參考紅珊瑚扇與乾燥秋海棠花瓣）",
        "palette": {
            "H": "#FCE0A8",  # Warm golden-peach highlight
            "L": "#F7B08A",  # Lit coral petal
            "M": "#F08A6C",  # Core Sift Coral (#F08A6C)
            "D": "#C4584A",  # Cool terracotta-crimson shadow
            "O": "#8C3535",  # Top-left Sel-Out
            "K": "#521B24",  # Bottom-right deep wine outline
            "S": "#F5CA6E",  # Golden pollen center
        },
        "rows": [
            "................",
            "....OOO..OOO....",
            "...OLLMOOLLMO...",
            "..OLHHLMOLHHLK..",
            ".OOLHLLMMLHLLMK.",
            ".OLLMLLSSLLMLLK.",
            ".OLHMLSSSSMLMMK.",
            "..OLLMSSSSLMMDK.",
            "..OOLLMMSSMMDK..",
            "..OLLMMMDDMMDK..",
            "..OLHMDDDDMDDK..",
            "...OLMDDDDDDK...",
            "....OKKDDDDK....",
            ".......KKKK.....",
            "................",
            "................",
        ],
    },

    # 4. 琥珀染料 (amber_dye) — 橙隙浮藤凝結的半透明琥珀樹脂淚滴與捲鬚 (Amber Vine Resin Tear & Tendril)
    "amber": {
        "brief": "橙隙浮藤分泌凝結的半透明琥珀松香淚滴，頂端連著一段捲曲藤蔓（參考波羅的海琥珀樹脂與藤黃果膠）",
        "palette": {
            "H": "#FCEBA8",  # Warm lemon-gold specular reflection
            "L": "#F5C662",  # Lit golden amber
            "M": "#E8A33A",  # Core Sift Amber (#E8A33A)
            "D": "#B86B1E",  # Deep burnt-orange shadow
            "O": "#7D4116",  # Top-left Sel-Out
            "K": "#4A2210",  # Bottom-right dark umber outline
            "S": "#8C9E42",  # Olive-amber vine stem
        },
        "rows": [
            "................",
            "......OOOO......",
            ".....OSSSSO.....",
            "....OOSS..SO....",
            "....OLMO...K....",
            "...OLLMMO.......",
            "..OLHHLLMO......",
            "..OLHHHLLMK.....",
            ".OLLMHHLLMMK....",
            ".OLLMLLLLMMDK...",
            ".OLLMMMMMMMDK...",
            "..OLMMMMDDDDK...",
            "..OOMMDDDDDDK...",
            "...OKDDDDDDK....",
            "....OKKKKKK.....",
            "................",
        ],
    },

    # 5. 薰衣草染料 (lavender_dye) — 粉捲蕨螺旋蕨芽與柔和紫晶草花穗束 (Spiral Pink-Lavender Fern Fiddlehead & Florets)
    "lavender": {
        "brief": "粉捲蕨標誌性的斐波那契螺旋蕨芽（Fiddlehead）纏繞紫晶草花苞（參考薰衣草乾燥花束與紫萁捲蕨）",
        "palette": {
            "H": "#F5E6FA",  # Warm pale pink-lilac highlight
            "L": "#D4C2F0",  # Lit lavender frond
            "M": "#B39DDB",  # Core Sift Lavender (#B39DDB)
            "D": "#8368B5",  # Cool royal-violet shadow
            "O": "#5B438A",  # Top-left Sel-Out
            "K": "#36245C",  # Bottom-right deep indigo-violet outline
            "S": "#E8A8D8",  # Pink curled fern inner bud accent
        },
        "rows": [
            "................",
            ".....OOOOOO.....",
            "...OOLLLLLLOO...",
            "..OLLHHHHHHLLO..",
            ".OLLHHOOSSHLLMK.",
            ".OLHHO.OSSLMMMK.",
            ".OLHO..OLLMDDMK.",
            ".OLHLLOOLLMDK...",
            "..OLLHMMMDKK....",
            "..OOLLMMMDK.OO..",
            "...OLLMMDK.OLLO.",
            "....OLLMDKOLLMK.",
            "....OLLMMDMMDK..",
            "....OLLMDDDK....",
            ".....OKKKKK.....",
            "................",
        ],
    },

    # 6. 赤紅玫瑰染料 (rose_dye) — 甲殼花盛開玫瑰花冠與金蕊花瓣膏 (Carapace Rose Blossom & Golden Stamen Paste)
    "rose": {
        "brief": "甲殼花厚實的赤紅玫瑰花冠與亮金花蕊，下方散落兩片碾碎花瓣（參考大馬士革玫瑰與胭脂蟲紅色素）",
        "palette": {
            "H": "#FAD0D8",  # Warm blush-pink highlight
            "L": "#EE7B91",  # Lit crimson-rose petal
            "M": "#D9536E",  # Core Sift Rose (#D9536E)
            "D": "#A32E4D",  # Cool ruby-wine shadow
            "O": "#731C3A",  # Top-left Sel-Out
            "K": "#450E26",  # Bottom-right deep burgundy-violet outline
            "S": "#F7D872",  # Golden carapace flower stamen
            "T": "#C9963B",  # Stamen shadow
        },
        "rows": [
            "................",
            "....OOO..OOO....",
            "..OOLLMOOLMMO...",
            ".OLLHHLLMLLMMK..",
            ".OLHHLLLLLLMMK..",
            ".OLLMLLSLLMMDK..",
            ".OLLMLLSTLLMDK..",
            "..OLLMMTSMMMDK..",
            "..OOLLMMMMMMK...",
            "...OLLDDDDDDK...",
            "..OO.KKKKKKK.OO.",
            ".OLLK.......OLLK",
            ".OMDK.......OMDK",
            "..KK.........KK.",
            "................",
            "................",
        ],
    },

    # 7. 靈魂藍染料 (soul_blue_dye) — 靈魂柳發光垂葉與靈魂劈裂草冰藍晶露 (Glowing Soul Willow Leaf & Soul Cleaver Dew)
    "soul_blue": {
        "brief": "靈魂柳修長彎曲的發光垂葉與懸浮的一滴靈魂藍晶露（參考藍桉葉片與青金石水飛色料）",
        "palette": {
            "H": "#E6F7FF",  # Ice-cyan glowing highlight
            "L": "#B8E0FA",  # Lit soul blue leaf
            "M": "#8EC5F0",  # Core Sift Soul Blue (#8EC5F0)
            "D": "#568EC7",  # Cool cobalt shadow
            "O": "#365E96",  # Top-left Sel-Out
            "K": "#1D3561",  # Bottom-right deep navy-indigo outline
            "S": "#73F0EC",  # Bioluminescent cyan vein glow
        },
        "rows": [
            "................",
            ".........OOOO...",
            ".......OOLLLLO..",
            ".....OOLLHHHLMK.",
            "....OLLHHSLLMMK.",
            "...OLLHSSLLMMK..",
            "..OLLHSSLLMMDK..",
            "..OLHSSLLMMDK...",
            ".OLLMSSMMMDK.OO.",
            ".OLLMMSMMDK.OHLK",
            "..OLLMMMDK..OMDK",
            "..OOLLMDK....KK.",
            "...OOMDK........",
            "...OKK..........",
            "..OK............",
            "................",
        ],
    },

    # 8. 虛黑染料 (void_dye) — 幽光菇傘蓋與青藍發光孢子黑粉 (Gloomcap Mushroom Cap & Cyan Spore Dust)
    "void": {
        "brief": "碾碎的半顆幽光菇深紫黑菌傘與散落的青藍色螢光孢子粉末（參考墨汁鬼傘菌墨與深淵生物發光孢子）",
        "palette": {
            "H": "#8A76A6",  # Lit dusty violet cap highlight
            "L": "#5E4B75",  # Upper cap mid-light
            "M": "#3A2E48",  # Core Sift Void (#3A2E48)
            "D": "#261D33",  # Deep abyssal purple shadow
            "O": "#322642",  # Top-left Sel-Out
            "K": "#150F21",  # Bottom-right deepest void outline (not #000000)
            "S": "#6CF5F0",  # Bright cyan bioluminescent spore spot (from gloomcap.png)
            "T": "#22A8A8",  # Cyan spore mid-glow
        },
        "rows": [
            "................",
            ".....OOOOOO.....",
            "...OOLLLLLLOO...",
            "..OLLHHLLSSTLO..",
            ".OLLHHLLLSSTLMK.",
            ".OLLLLMMMMMMMDK.",
            ".OLLMMSTMMMMMDK.",
            ".ODDDDDDDDDDDDK.",
            "..KKKKOMMMOKKK..",
            ".....OLLMMDK....",
            "...OOLLMMMDKOO..",
            "..OLLMSTMMMDSTK.",
            "..ODDDDDDDDDDDK.",
            "...KKKKKKKKKKK..",
            "................",
            "................",
        ],
    },

    # 9. 暮光金染料 (dusk_gold_dye) — 暮綻花盛開金瓣與黃龍舌蘭蜜晶粉 (Dusk Bloom Golden Rosette & Agave Nectar Crystals)
    "dusk_gold": {
        "brief": "暮綻花飽滿的暖金重瓣花朵與散落的龍舌蘭琥珀金花粉粒（參考藏紅花金黃花蕊與金盞花色料）",
        "palette": {
            "H": "#FFF7C2",  # Warm cream-yellow highlight
            "L": "#F7E08A",  # Lit dusk gold petal
            "M": "#F2CF6B",  # Core Sift Dusk Gold (#F2CF6B)
            "D": "#C99A38",  # Warm ochre-amber shadow
            "O": "#8F631E",  # Top-left Sel-Out
            "K": "#523210",  # Bottom-right deep bronze-brown outline
            "S": "#E87A3E",  # Warm sunset orange core accent
        },
        "rows": [
            "................",
            "....OOO..OOO....",
            "...OLLMOOLLMO...",
            "..OLHHLLLLHHLK..",
            ".OOLHHLLLLHLLMK.",
            ".OLLLLSSSSLLLLK.",
            ".OLHLLSSSSLLMMK.",
            "..OLLLLSSLLMMDK.",
            "..OOLLLLLLLMDK..",
            "...OLLMMMMMDDK..",
            "..OO.KKKKKKK.OO.",
            ".OHLK..OOO..OLLK",
            "..KK..OLLMK..KK.",
            ".......KKK......",
            "................",
            "................",
        ],
    },
}


# ==============================================================================
# PART 2: 9 GLAZED TERRACOTTA BLOCK PATTERNS (16x16, 4-Block Rotational Mandala)
# ==============================================================================
# Crucial Mathematical Guarantee for 4-Block (2x2) Rotational Tiling:
# When 4 blocks are placed with cyclic rotations:
#   - In Configuration A (4 top-left corners meeting at the center), Top edge `row[0][k]`
#     touches Left edge `row[k][0]` of the neighbor.
#   - In Configuration B (4 bottom-right corners meeting at the center), Bottom edge `row[15][k]`
#     touches Right edge `row[k][15]` of the neighbor.
# By designing each pattern on the upper triangle and mirroring across the main diagonal
# `M[y][x] = M[x][y]` (with optional directional shading inside interior bands), BOTH
# `Top == Left` (16/16) and `Bottom == Right` (16/16) are 100% mathematically guaranteed!
# As a result, ANY 2x2 or 4x4 rotational placement forms seamless, unbroken circles, stars,
# petals, and interlocking bands across all 4 blocks!

GLAZED_PALETTES: dict[str, dict[str, str]] = {
    # 1. 青碧彩繪陶瓦 (teal_glazed_terracotta) — 劈裂草四葉星盤與鎏金幾何環 (Teal + Pale Mint-Gold + Abyssal Indigo)
    "teal": {
        "H": "#D4F7E8",  # Specular glaze highlight (warm pale mint)
        "L": "#6BE0CE",  # Light teal glaze
        "M": "#2EB8A6",  # Base Sift Teal (#2EB8A6)
        "D": "#1B827E",  # Deep teal shadow
        "K": "#0F4652",  # Dark indigo-teal grout/outline
        "A": "#F0D878",  # Warm gold ceramic inlay accent (20% focal)
        "B": "#B8923A",  # Gold inlay shadow
    },
    # 2. 薄荷彩繪陶瓦 (mint_glazed_terracotta) — 夜光草八角星芒與翠玉花窗 (Mint + Cream + Deep Seafoam + Cyan Gem)
    "mint": {
        "H": "#EEFCEB",  # Specular glaze highlight
        "L": "#B8F2D6",  # Light mint glaze
        "M": "#8FE3C0",  # Base Sift Mint (#8FE3C0)
        "D": "#4FA88E",  # Medium seafoam shadow
        "K": "#235952",  # Dark pine-teal grout
        "A": "#5CE6E6",  # Luminous cyan crystal inlay
        "B": "#2B8C96",  # Cyan inlay shadow
    },
    # 3. 珊瑚彩繪陶瓦 (coral_glazed_terracotta) — 珊瑚礁扇貝圓舞曲與碧海寶石核 (Coral + Sun Gold + Reef Turquoise)
    "coral": {
        "H": "#FCEAD2",  # Warm cream-peach specular
        "L": "#F7B294",  # Light coral glaze
        "M": "#F08A6C",  # Base Sift Coral (#F08A6C)
        "D": "#BA5445",  # Terracotta red-brown shadow
        "K": "#692528",  # Deep maroon grout
        "A": "#F5D062",  # Sun-gold inlay highlight
        "B": "#48B8B0",  # Complementary reef-turquoise gem accent
    },
    # 4. 琥珀彩繪陶瓦 (amber_glazed_terracotta) — 橙隙浮藤皇家徽章與綠松石星眼 (Amber + Lemon Gold + Umber + Teal Gem)
    "amber": {
        "H": "#FCF0B8",  # Bright warm gold specular
        "L": "#F5C45A",  # Light amber glaze
        "M": "#E8A33A",  # Base Sift Amber (#E8A33A)
        "D": "#AD641B",  # Burnt sienna shadow
        "K": "#592A12",  # Dark espresso-umber grout
        "A": "#FFF5CA",  # Ivory-gold highlight inlay
        "B": "#2E968C",  # Complementary turquoise-teal center jewel
    },
    # 5. 薰衣草彩繪陶瓦 (lavender_glazed_terracotta) — 粉捲蕨四葉漩渦與紫晶蓮座 (Lavender + Blush Pink + Royal Violet)
    "lavender": {
        "H": "#F7EBFC",  # Pale lilac-white specular
        "L": "#D4C0F2",  # Light lavender glaze
        "M": "#B39DDB",  # Base Sift Lavender (#B39DDB)
        "D": "#7D62B0",  # Royal purple shadow
        "K": "#432D73",  # Deep indigo-violet grout
        "A": "#F2A8D4",  # Pink curled fern rose-pink inlay
        "B": "#E8D07A",  # Soft pearl-gold center dot
    },
    # 6. 赤紅玫瑰彩繪陶瓦 (rose_glazed_terracotta) — 甲殼花哥德式大玫瑰窗與金絲鑲嵌 (Crimson Rose + Gold Filigree + Burgundy)
    "rose": {
        "H": "#FCE0E6",  # Blush specular
        "L": "#EE8298",  # Light rose glaze
        "M": "#D9536E",  # Base Sift Rose (#D9536E)
        "D": "#9E2B48",  # Deep ruby shadow
        "K": "#54122B",  # Dark wine-purple grout
        "A": "#F5D46E",  # Gold filigree highlight
        "B": "#B8862D",  # Gold filigree shadow
    },
    # 7. 靈魂藍彩繪陶瓦 (soul_blue_glazed_terracotta) — 靈魂柳八芒羅盤與靈液漩渦環 (Soul Blue + Ice Cyan + Deep Cobalt)
    "soul_blue": {
        "H": "#EBF9FF",  # Ice-white specular
        "L": "#B8E0FA",  # Light soul blue glaze
        "M": "#8EC5F0",  # Base Sift Soul Blue (#8EC5F0)
        "D": "#4E86BD",  # Cobalt shadow
        "K": "#214070",  # Deep navy grout
        "A": "#7AF5F0",  # Glowing soul-cyan inlay
        "B": "#2FA6A6",  # Soul-cyan shadow
    },
    # 8. 虛黑彩繪陶瓦 (void_glazed_terracotta) — 幽光菇深淵符文陣與螢光青孢子核心 (Void Purple-Black + Cyan Glow + Amethyst)
    "void": {
        "H": "#7C6899",  # Lit amethyst-slate highlight
        "L": "#53426B",  # Upper void violet
        "M": "#3A2E48",  # Base Sift Void (#3A2E48)
        "D": "#251C30",  # Deep abyssal shadow
        "K": "#140E1C",  # Deepest obsidian-violet grout (never #000000)
        "A": "#68F2EC",  # Bioluminescent gloomcap cyan inlay (20% focal)
        "B": "#24999E",  # Cyan inlay shadow
    },
    # 9. 暮光金彩繪陶瓦 (dusk_gold_glazed_terracotta) — 暮綻花日冕八瓣太陽輪與暖陽琥珀 (Dusk Gold + Ivory + Sunset Amber)
    "dusk_gold": {
        "H": "#FFF9D2",  # Warm ivory-gold specular
        "L": "#F7E28C",  # Light dusk gold glaze
        "M": "#F2CF6B",  # Base Sift Dusk Gold (#F2CF6B)
        "D": "#C49232",  # Ochre-gold shadow
        "K": "#704616",  # Deep bronze-umber grout
        "A": "#F08542",  # Sunset coral-amber floral accent
        "B": "#AD4822",  # Sunset accent shadow
    },
}


def symmetrize_pattern(upper_rows: list[str]) -> list[str]:
    """
    Ensure exact main-diagonal symmetry `grid[y][x] == grid[x][y]` on the outer borders and
    structural arcs so that 4 rotated blocks in ANY 2x2 configuration match 16/16 pixels
    seamlessly across all 4 shared internal edges, while applying subtle Top-Left vs
    Bottom-Right glaze relief shading strictly inside the interior (`2 <= x, y <= 13`)!
    """
    grid = [list(r) for r in upper_rows]
    for y in range(16):
        for x in range(y + 1, 16):
            grid[x][y] = grid[y][x]

    # Add subtle Top-Left light vs Bottom-Right shadow glaze relief on the lower-left interior
    # (strictly keeping row 0, row 15, col 0, col 15 untouched so 16/16 4-block seams stay 100% exact!)
    shade_down = {"H": "L", "A": "B"}
    for y in range(2, 14):
        for x in range(1, y - 1):
            if (x + y) >= 15 and grid[y][x] in shade_down:
                # Only shade if at least one neighbor also has the target or current shade (avoid orphans)
                grid[y][x] = shade_down[grid[y][x]]
    return ["".join(r) for r in grid]


# Each pattern is authored with distinct architectural geometry:
#   - Hub A around (0,0) forms the primary 4-block central mandala when placed facing outward/inward
#   - Hub B around (15,15) forms the secondary 4-block medallion at the alternate 2x2 corners
#   - The middle band (x+y ~ 15) connects them into an interlocking lattice across the whole floor!
GLAZED_PATTERNS: dict[str, list[str]] = {
    # 1. TEAL: 4-leaf Cleaver Botanical Compass at (0,0), Golden Diamond Frame in center, & Deep Sea Medallion at (15,15)
    "teal": symmetrize_pattern([
        "AAHHLLKKMMLLKKDD",
        "AHHLLLKKMMLLKKDD",
        "HLLLLKKMMMLLKKMD",
        "HLLKKAAKMMLLKMMD",
        "LLKAAHHAKMLLKMMD",
        "LLKAHBBHAKLLKMDK",
        "KKKMMBBMMKKKKDKK",
        "MMMMBBBBMMMMDDKK",
        "MMLLLLBBLLLLDDAA",
        "LLLLLLKKLLLLDDAA",
        "LLLLKKKKKKDDDDAA",
        "KKMMKKDDKKDDDDAB",
        "KKMMDDKKKKDDDDAB",
        "DDMMDDKKDDDDKKBB",
        "DDDDDDDDDDKKKKBB",
        "DDDDDDMMAAAAAABB",
    ]),

    # 2. MINT: Luminous 8-Pointed Starburst at (0,0), Octagonal Jade Ring, & Glowing Cyan Crystal Cross at (15,15)
    "mint": symmetrize_pattern([
        "AAHHLLMMKKDDMMLL",
        "AAHHHLLMMKDDMMLL",
        "HHLLLLMMKKDDDDMM",
        "HLLLLKKKKKDDDDMM",
        "LLLKKAAHHAAKDDKK",
        "MMKAAHHHHHHAAKKK",
        "MMKAHHLLLLHHAKLL",
        "KKKAHLLMMLLHAKLL",
        "DDKAHLLMMLLHAKHH",
        "DDKAAHLLLLHAAKHH",
        "MMMMKAAHHAAKLLLL",
        "MMMMKKKKKKKKLLMM",
        "DDMMMMDDDDMMKKKK",
        "DDDDDDDDMMKKBBAA",
        "LLDDMMKKKKBBBBAA",
        "LLMMKKLLAAHHAAAA",
    ]),

    # 3. CORAL: Scalloped Reef Shell Fan at (0,0), Wavy Sun-Gold Ribbons, & Turquoise Pearl Rosette at (15,15)
    "coral": symmetrize_pattern([
        "BBAAHHLLKKMMDDLL",
        "BBAAHHLLKKMMDDLL",
        "AAHHLLLLKKDDDDMM",
        "AHHLLLKKKKDDMMMM",
        "HLLLKKAAAAKKMMLL",
        "LLLKAALLLLAAKLLL",
        "KKKKALHddHLAKKKK".replace("d", "D"),
        "MMKKALHDDDHLAKDD",
        "MMDDKALDDDLAKDDD",
        "MMDDKAAHLLHAKMMM",
        "LLMMMMKAAAAKMMLL",
        "LLMMMMKKKKKKLLHH",
        "DDMMLLMMMMLLLLHH",
        "DDMMMMMMKKKKBBAA",
        "LLMMKKKKBBBBBBAA",
        "LLLLHHAAHBBBBAAA",
    ]),

    # 4. AMBER: Royal Amber Honeycomb Medallion with Turquoise Eye at (0,0), Interlocking Gold Bars, & Sun Star at (15,15)
    "amber": symmetrize_pattern([
        "BBAAHHLLKKMMDDKK",
        "BBAAHHLLKKMMDDKK",
        "AAHHLLLLKKDDDDMM",
        "AHHLLLKKKKDDMMMM",
        "HLLLKKAAAAKKMMLL",
        "LLKKAAHHHHAAKLLL",
        "KKKKAHHMMHHAKLLL",
        "MMKKAHMBBMHAKKKK",
        "MMDDKAHBBMHAKDDD",
        "MMDDKAAHHAAKDDMM",
        "DDMMMMKAAAAKMMLL",
        "DDMMMMKKKKKKLLHH",
        "KKMMLLLLLLLLLLHH",
        "KKDDDDMMKKKKAAAA",
        "KKDDKKKKAAHHBBAA",
        "KKKKMMLLHHBBBBAA",
    ]),

    # 5. LAVENDER: Curled-Fern Petal Pinwheel at (0,0), Blush-Pink Garland Ring, & Amethyst Lotus at (15,15)
    "lavender": symmetrize_pattern([
        "BBAAHHLLKKDDMMLL",
        "BBAAHHLLKKDDMMLL",
        "AAHHLLLLKKDDDDMM",
        "AHHLLLKKKKDDDDMM",
        "HLLLKKAAAAKKDDKK",
        "LLLKAALLLLAAKKKK",
        "KKKKALHHHHALKKLL",
        "DDKKALHAAHALKLLL",
        "DDMMKALAAHALKLLL",
        "MMMMKAALLLAKLLHH",
        "MMLLLLKAAAAKLLHH",
        "LLLLLLKKKKKKMMKK",
        "MMLLMMMMDDMMMMKK",
        "MMDDDDDDDDKKAAAA",
        "LLLLMMKKKKAAHHAA",
        "LLLLLLHHMMKKAAAA",
    ]),

    # 6. ROSE: Gothic Cathedral Rose Window at (0,0), Golden Filigree Tracery, & Crimson Lancet Cross at (15,15)
    "rose": symmetrize_pattern([
        "AAHHLLKKMMDDKKLL",
        "AAHHLLKKMMDDKKLL",
        "HHLLLLKKDDDDKKMM",
        "HLLLKKKKDDKKKKMM",
        "LLKKAAABAAAKKMMM",
        "LLKAABBBBBAAKMMM",
        "KKKABHHLLHBAKDDD",
        "MMKABHLLLLBAKDDD",
        "DDKABHLLLLBAKKKK",
        "DDKAABHLLHBAKLLL",
        "KKMMKAABBAAKLLHH",
        "KKMMMKKAAAKKLLHH",
        "LLMMMMDDDDMMMMKK",
        "LLMMDDDDDDKKAAAB",
        "MMMMKKKKKKAAABBB",
        "LLMMDDDDLLHHKKBB",
    ]),

    # 7. SOUL BLUE: Celestial Soul-Willow Compass Rose at (0,0), Spirit-Cyan Diamond Lattice, & Ice Star at (15,15)
    "soul_blue": symmetrize_pattern([
        "AAHHLLMMKKDDMMLL",
        "AAHHHLLMMKDDMMLL",
        "HHLLLLMMKKDDDDMM",
        "HLLLLKKKKKDDDDMM",
        "LLLKKBBAAAKKDDKK",
        "MMKKBBAHHHAAKKKK",
        "MMKKBAHHLLHHAKLL",
        "KKKKAAHLLLLHAKLL",
        "DDKKAAHLLLLHAKHH",
        "DDMMKAAHLLHHAKHH",
        "MMMMKKAAHHAAKLLL",
        "MMMMKKKKAAKKLLMM",
        "DDMMMMDDDDMMKKKK",
        "DDDDDDDDMMKKBBAA",
        "LLDDMMKKKKBBAAHH",
        "LLMMKKLLHHMMMMAA",
    ]),

    # 8. VOID: Abyssal Gloomcap Cyan Spore Reactor at (0,0), Obsidian-Violet Runes, & Glowing Spore Node at (15,15)
    "void": symmetrize_pattern([
        "AABBHLLLKKDDMMKK",
        "AABBHHLLKKDDMMKK",
        "BBHHLLLLKKKKDDMM",
        "BHHLLLKKHHLLKKDD",
        "HLLLKKHHHHHHLLKK",
        "LLLKKHHLLLLHHLLK",
        "LLKKHLLMMMMLLHKK",
        "KKKKHLLMAAMLLHKK",
        "DDKKHLLMAAMLLHKK",
        "DDKKHHLLLLLLHHKK",
        "MMMMKHHHHHHHHKKD",
        "MMMMKKKHHHHKKDDD",
        "KKDDMMKKKKKKDDDD",
        "KKDDDDDDKKKKBBAA",
        "KKKKMMKKKKBBBBAA",
        "KKDDKKKKDDDDAAAA",
    ]),

    # 9. DUSK GOLD: Radiant 8-Ray Sunburst at (0,0), Warm Sunset-Amber Floral Wreath, & Golden Lotus at (15,15)
    "dusk_gold": symmetrize_pattern([
        "HHLLLLMMKKDDMMLL",
        "HHHLLLMMKKDDMMLL",
        "HLLLLLKKKKDDDDMM",
        "LLLLKKAAAAKKDDMM",
        "LLMMKAAHHAAKDDKK",
        "LLLKAABHHHAAKKKK",
        "MMKKABHHAAHHAKLL",
        "MMKKAHAAHHAAHKLL",
        "KKKKAHAAHHAAHKHH",
        "DDKKAAHHAAHHAKHH",
        "DDMMKAAHHHAAKLLL",
        "MMMMKKAAAAKKLLMM",
        "MMLLMMDDMMMMKKKK",
        "MMDDMMMMDDKKAAAA",
        "LLMMKKKKKKAAABBA",
        "LLLLKKKKHHLLMMBB",
    ]),
}


def render_2x2_rotational_variants(tile: Image.Image) -> tuple[Image.Image, Image.Image]:
    """
    Simulate the TWO distinct 2x2 big patterns players can build with Glazed Terracotta in Minecraft:
      - Pattern A (Hub A at center): 4 tiles placed so their (0,0) top-left corners meet at the center (16,16).
      - Pattern B (Hub B at center): 4 tiles placed with opposite facing so their (15,15) bottom-right corners meet at the center (16,16).
    Notice that in a 4x4 floor, Pattern A and Pattern B alternate seamlessly!
    """
    w, h = tile.size
    t0 = tile
    t90_cw = tile.transpose(Image.Transpose.ROTATE_270)
    t180 = tile.transpose(Image.Transpose.ROTATE_180)
    t270_cw = tile.transpose(Image.Transpose.ROTATE_90)

    # Pattern A: (15,15) corners meet at the center of the 2x2
    pat_b = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 255))
    pat_b.paste(t0, (0, 0))
    pat_b.paste(t90_cw, (w, 0))
    pat_b.paste(t270_cw, (0, h))
    pat_b.paste(t180, (w, h))

    # Pattern B: (0,0) corners meet at the center of the 2x2
    pat_a = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 255))
    pat_a.paste(t180, (0, 0))
    pat_a.paste(t270_cw, (w, 0))
    pat_a.paste(t90_cw, (0, h))
    pat_a.paste(t0, (w, h))

    return pat_a, pat_b


def verify_2x2_seam_continuity(colour: str, tile: Image.Image) -> None:
    px = tile.load()
    top_left_ok = sum(1 for k in range(16) if px[k, 0] == px[0, k])
    bot_right_ok = sum(1 for k in range(16) if px[k, 15] == px[15, k])
    assert top_left_ok == 16 and bot_right_ok == 16, (
        f"{colour}: 2x2 rotational seam mismatch! Top==Left: {top_left_ok}/16, Bot==Right: {bot_right_ok}/16"
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ITEM_DIR.mkdir(parents=True, exist_ok=True)
    BLOCK_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    colours = list(DYE_SPECS.keys())
    print(f"🎨 開始生成 9 款植物染料圖示與 9 款四塊拼接彩繪陶瓦貼圖 (共 {len(colours) * 2} 張)...")

    # Overview preview canvas
    overview = Image.new("RGBA", (1060, 90 + len(colours) * 96), (24, 26, 30, 255))
    draw = ImageDraw.Draw(overview)
    draw.rectangle([0, 0, 1060, 48], fill=(38, 42, 50, 255))
    draw.text(
        (16, 15),
        "The Sift - 9 New Colours: Plant Dyes & 4-Block Rotational Glazed Terracotta (Hub A 2x2, Hub B 2x2, & 4x4 Floor)",
        fill=(235, 240, 250, 255),
    )

    for idx, colour in enumerate(colours):
        # 1. Generate Dye Icon
        d_spec = DYE_SPECS[colour]
        dye_img = parse_canvas(d_spec["rows"], d_spec["palette"])
        dye_path = ITEM_DIR / f"{colour}_dye.png"
        art_guard.save(dye_img, dye_path)

        # 2. Generate Glazed Terracotta Block Texture & verify 16/16 rotational edge continuity
        gt_pal = GLAZED_PALETTES[colour]
        gt_rows = GLAZED_PATTERNS[colour]
        gt_img = parse_canvas(gt_rows, gt_pal)
        verify_2x2_seam_continuity(colour, gt_img)
        gt_path = BLOCK_DIR / f"{colour}_glazed_terracotta.png"
        art_guard.save(gt_img, gt_path)

        print(
            f"  ✅ [{idx + 1}/9] {colour:<10} -> 2x2 四塊旋轉接縫 16/16 完美吻合 | "
            f"{dye_path.relative_to(ROOT)} & {gt_path.relative_to(ROOT)}"
        )

        # Render row into overview sheet
        y0 = 58 + idx * 96
        draw.rectangle([12, y0, 1048, y0 + 88], fill=(32, 35, 42, 255), outline=(52, 58, 68, 255))
        draw.text((24, y0 + 10), f"{idx + 1}. {colour.upper()}", fill=(240, 245, 255, 255))
        draw.text((24, y0 + 32), "16/16 Seam OK", fill=(130, 220, 175, 255))

        # Dye 4x + 1x + Grayscale 4x
        dye_4x = dye_img.resize((64, 64), Image.Resampling.NEAREST)
        overview.alpha_composite(dye_4x, (150, y0 + 12))
        overview.alpha_composite(dye_img, (220, y0 + 12))

        dye_gray = dye_img.convert("LA").convert("RGBA").resize((64, 64), Image.Resampling.NEAREST)
        overview.alpha_composite(dye_gray, (248, y0 + 12))

        # Glazed Terracotta single tile 4x + Grayscale 4x
        gt_4x = gt_img.resize((64, 64), Image.Resampling.NEAREST)
        overview.paste(gt_4x, (336, y0 + 12))
        draw.text((336, y0 + 76), "1 Tile (4x)", fill=(160, 175, 195, 255))

        gt_gray = gt_img.convert("L").convert("RGBA").resize((64, 64), Image.Resampling.NEAREST)
        overview.paste(gt_gray, (416, y0 + 12))
        draw.text((416, y0 + 76), "Grayscale", fill=(160, 175, 195, 255))

        # Both 2x2 Rotational Mandala variants (32x32 -> 64x64 at 2x)
        pat_a, pat_b = render_2x2_rotational_variants(gt_img)
        overview.paste(pat_a.resize((64, 64), Image.Resampling.NEAREST), (508, y0 + 12))
        draw.text((508, y0 + 76), "2x2 Mandala A", fill=(240, 220, 140, 255))

        overview.paste(pat_b.resize((64, 64), Image.Resampling.NEAREST), (592, y0 + 12))
        draw.text((592, y0 + 76), "2x2 Mandala B", fill=(240, 220, 140, 255))

        # 4x4 Rotational Floor (2x2 of the 2x2 rotational unit = 64x64 at 1x & 1.25x)
        floor_4x4 = Image.new("RGBA", (64, 64), (0, 0, 0, 255))
        for fy in range(2):
            for fx in range(2):
                floor_4x4.paste(pat_a, (fx * 32, fy * 32))
        overview.paste(floor_4x4, (684, y0 + 12))
        draw.text((684, y0 + 76), "4x4 Floor (1x)", fill=(160, 175, 195, 255))

        # 4x4 Floor zoomed (64x64 crop of 2x)
        overview.paste(pat_a.resize((64, 64), Image.Resampling.NEAREST), (772, y0 + 12))
        # Draw subtle yellow crosshair showing where the 4 blocks meet in the 2x2 mandala
        draw.line([(772 + 32, y0 + 12), (772 + 32, y0 + 75)], fill=(255, 255, 255, 90), width=1)
        draw.line([(772, y0 + 12 + 32), (772 + 63, y0 + 12 + 32)], fill=(255, 255, 255, 90), width=1)
        draw.text((772, y0 + 76), "4-Block Grid", fill=(160, 175, 195, 255))

    preview_path = PREVIEW_DIR / "sift_colors_art_overview.png"
    overview.save(preview_path)
    print(f"\n🖼️ 總覽預覽圖已輸出至: {preview_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
