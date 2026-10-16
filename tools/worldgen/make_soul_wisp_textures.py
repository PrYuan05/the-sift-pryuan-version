"""Draw the soul wisp particle textures (textures/particle/, picked up by the vanilla particle atlas).
Usage: python -I tools/worldgen/make_soul_wisp_textures.py <project>
  soul_wisp.png  12x12, an 8 wide x 12 tall ghost: white face, cyan rim, dark blue eyes and mouth, wispy tails (not tinted)
  soul_trail.png 8x8 soft round glow, white with an alpha falloff; tinted per particle (trail and halo)"""
import math, sys
from pathlib import Path
from PIL import Image

OUT = Path(sys.argv[1]) / "src/main/resources/assets/pysift/textures/particle"
OUT.mkdir(parents=True, exist_ok=True)

HEAD = ["....####....",      # 12x12 canvas, the ghost is 8 wide and 12 tall (taller face, user request);
        "...#WWWW#...",      # the particle quad is square, so the canvas must stay square
        "..#WWWWWW#..",
        "..#WWWWWW#..",
        "..#WEWWEW#..",
        "..#WEWWEW#..",
        "..#WWWWWW#..",
        "..#WWMMWW#..",      # vertical mouth, 2 wide x 3 tall (user request)
        "..#WWMMWW#..",
        "..#WWMMWW#..",
        "...#WWWW#...",
        "...#.##.#..."]
COLOURS = {"#": (127, 232, 255, 255), "W": (236, 252, 255, 255), "E": (27, 74, 138, 255), "M": (60, 120, 190, 255),
           ".": (0, 0, 0, 0)}
head = Image.new("RGBA", (12, 12))
head.putdata([COLOURS[ch] for row in HEAD for ch in row])
head.save(OUT / "soul_wisp.png")

trail = Image.new("RGBA", (8, 8))
trail.putdata([(255, 255, 255, int(255 * max(0.0, 1 - math.hypot(x - 3.5, y - 3.5) / 4.2) ** 1.6))
               for y in range(8) for x in range(8)])
trail.save(OUT / "soul_trail.png")
print("wrote", *(p.name for p in sorted(OUT.glob("soul_*.png"))))
