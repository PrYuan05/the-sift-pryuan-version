"""Pixel art for the soul burn system.
Usage: python -I tools/items/make_soul_burn_textures.py <project>

  textures/item/soul_antidote.png      16x16 potion bottle: glass outline, cork, cyan-blue liquid with gold sparkles
  (the 18x18 soul flame below is only drawn into the preview; soul_burn was merged into soul_deprivation)
Both are new files; a preview goes to build/texture_pipeline/out/soul_burn_textures.png."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import art_guard   # 臨時圖保護：使用者用同檔名覆蓋過的貼圖不會被重跑蓋掉
from PIL import Image

P = Path(sys.argv[1]).resolve()
A = P / "src/main/resources/assets/pysift/textures"

# 16x16 bottle, same silhouette as the vanilla potion: '.' empty, 'o' glass outline, 'g' glass highlight,
# 'c' cork, 'L' liquid light, 'l' liquid, 'd' liquid dark, '*' gold sparkle
BOTTLE = [
    "................",
    "......cccc......",
    "......cccc......",
    ".....oooooo.....",
    "......ogLo......",
    "......oLlo......",
    ".....ogLllo.....",
    "....oglL*llo....",
    "...ogLLllldlo...",
    "...oLlll*lldo...",
    "...oLl*lllldo...",
    "...olllllldlo...",
    "...oldllldddo...",
    "....oddddddo....",
    ".....oooooo.....",
    "................",
]
BOTTLE_COLOURS = {
    "o": (70, 92, 110, 255), "g": (230, 248, 255, 255), "c": (150, 104, 60, 255),
    "L": (150, 246, 255, 255), "l": (56, 210, 236, 255), "d": (24, 120, 168, 255), "*": (255, 222, 120, 255),
}

# 18x18 soul flame: 'O' outline, 'B' body, 'H' hot core
FLAME = [
    "..................",
    "........O.........",
    ".......OBO........",
    ".......OBO....O...",
    "......OBBBO..OBO..",
    "...O..OBHBO..OBO..",
    "..OBO.OBHBBO.OBO..",
    "..OBO.OBHHBBOBBO..",
    "..OBBOBBHHBBBBO...",
    "...OBBBHHHHBBBO...",
    "...OBBHHHHHHBBO...",
    "..OBBHHHHHHHHBBO..",
    "..OBBHHHHHHHHBBO..",
    "..OBBBHHHHHHBBBO..",
    "...OBBBHHHHBBBO...",
    "....OOBBBBBBOO....",
    "......OOOOOO......",
    "..................",
]
FLAME_COLOURS = {"O": (16, 70, 92, 255), "B": (41, 223, 235, 255), "H": (200, 255, 252, 255)}


def draw(rows, colours):
    img = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in colours:
                px[x, y] = colours[ch]
    return img


def main():
    bottle, flame = draw(BOTTLE, BOTTLE_COLOURS), draw(FLAME, FLAME_COLOURS)
    # soul_burn was merged into soul_deprivation (which keeps its own icon), so only the antidote is written
    for img, path in ((bottle, A / "item/soul_antidote.png"),):
        path.parent.mkdir(parents=True, exist_ok=True)
        art_guard.save(img, path)
        print("wrote", path.relative_to(P))
    prev = Image.new("RGBA", (16 * 10 + 18 * 10 + 20, 180), (40, 40, 46, 255))
    prev.alpha_composite(bottle.resize((160, 160), Image.Resampling.NEAREST), (0, 10))
    prev.alpha_composite(flame.resize((180, 180), Image.Resampling.NEAREST), (180, 0))
    out = P / "build/texture_pipeline/out/soul_burn_textures.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    prev.save(out)


if __name__ == "__main__":
    main()
