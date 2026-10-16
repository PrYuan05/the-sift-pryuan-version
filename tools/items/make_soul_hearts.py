"""Soul-fire heart sprites for Soul Deprivation (shown like the withered hearts while the effect is on; HudMixin).
Usage: python -I tools/items/make_soul_hearts.py <project>

Every vanilla 9x9 heart sprite (full / half / blinking / hardcore variants) is read from the local Minecraft client
jar and recoloured: the red body goes to a soul-fire cyan gradient by brightness (dark teal -> cyan -> white-cyan),
the near-white highlight stays light, the dark outline becomes deep teal; two flame-tongue pixels are lit on the
body so it reads as burning. Writes NEW files textures/gui/sprites/hud/heart/soul_<name>.png and a preview."""
import sys, zipfile, io, colorsys
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
JAR = Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client.jar"
OUT = P / "src/main/resources/assets/pysift/textures/gui/sprites/hud/heart"
NAMES = ["full", "full_blinking", "half", "half_blinking",
         "hardcore_full", "hardcore_full_blinking", "hardcore_half", "hardcore_half_blinking"]
OUTLINE, DEEP, BODY, LIGHT, HOT = (6, 42, 51), (14, 96, 112), (41, 223, 235), (150, 246, 255), (225, 255, 252)


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def recolour(img):
    out = img.copy()
    px = out.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if v < 0.25:
                c = OUTLINE
            elif s < 0.25:
                c = HOT                                         # white highlight
            elif s < 0.55:
                c = lerp(BODY, LIGHT, 0.65)                     # blinking (vanilla pink) -> light cyan
            elif v >= 0.95:
                c = BODY                                        # red body -> soul-fire cyan
            else:
                c = lerp(DEEP, BODY, max(0.0, (v - 0.45) / 0.5))   # shading / hardcore dark parts -> deep teal
            px[x, y] = c + (a,)
    return out


FLAME = ((4, 3), (4, 4), (3, 5), (4, 5), (5, 5), (4, 6))      # small upward flame in the heart's centre


def flames(img):
    """A lighter flame shape in the middle of the heart, only on filled body pixels (not on the highlight)."""
    px = img.load()
    for x, y in FLAME:
        if px[x, y][3] and px[x, y][:3] not in (OUTLINE, HOT):
            px[x, y] = lerp(px[x, y][:3], HOT, 0.6) + (255,)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    with zipfile.ZipFile(JAR) as z:
        for name in NAMES:
            src = Image.open(io.BytesIO(z.read(f"assets/minecraft/textures/gui/sprites/hud/heart/{name}.png"))).convert("RGBA")
            img = flames(recolour(src))
            img.save(OUT / f"soul_{name}.png")
            made.append((src, img))
    prev = Image.new("RGBA", (len(made) * 80, 160), (40, 40, 46, 255))
    for i, (a, b) in enumerate(made):
        prev.alpha_composite(a.resize((72, 72), Image.Resampling.NEAREST), (i * 80, 0))
        prev.alpha_composite(b.resize((72, 72), Image.Resampling.NEAREST), (i * 80, 80))
    out = P / "build/texture_pipeline/out/soul_hearts.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    prev.save(out)
    print(f"wrote {len(made)} soul heart sprites to {OUT.relative_to(P)}")


if __name__ == "__main__":
    main()
