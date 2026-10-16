"""Pixel-art textures for the decorations seen in the reference video (The Sift, 6:34 on), 16x16 cross-model sprites.
Usage: python -I tools/worldgen/make_decor_textures.py <project> [seed]

  glowcap           a cluster of small teal glowing mushrooms (pale stems, bright caps with light spots)
  bone_spire        white / ivory branching coral-like spikes
  puff_grass_bottom grey fluffy grass base   (coloured in game by FloorTint, so it is kept grey)
  puff_grass_top    grey fluffy rounded tufts
Writes into textures/block/vegetation/ and a preview build/texture_pipeline/out/decor_textures.png."""
import sys, random
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 11
OUT = P / "src/main/resources/assets/pysift/textures/block/vegetation"
PREVIEW = P / "build/texture_pipeline/out/decor_textures.png"


def canvas():
    return Image.new("RGBA", (16, 16), (0, 0, 0, 0))


def put(px, x, y, c):
    if 0 <= x < 16 and 0 <= y < 16:
        px[x, y] = c + (255,) if len(c) == 3 else c


def glowcap(rnd):
    img = canvas(); px = img.load()
    STEM, STEM_D = (214, 238, 230), (168, 200, 192)
    CAP_HI, CAP, CAP_D, UNDER = (120, 250, 232), (58, 206, 196), (30, 140, 140), (22, 92, 96)
    for cx, h, r in ((4, 6, 2), (10, 9, 3), (7, 4, 1), (13, 5, 1)):          # (centre x, stem height, cap radius)
        base = 15
        for y in range(base - h + 1, base + 1):
            put(px, cx, y, STEM if y % 3 else STEM_D)
        top = base - h - r
        for dy in range(r + 1):
            w = r + (1 if dy == r else 0) - (1 if dy == 0 and r > 1 else 0)
            for dx in range(-w, w + 1):
                c = CAP_HI if dy == 0 else (CAP_D if abs(dx) == w else CAP)
                put(px, cx + dx, top + dy, c)
        for dx in range(-r, r + 1):
            put(px, cx + dx, top + r + 1, UNDER)
        if r >= 2:
            put(px, cx - 1, top + 1, (236, 255, 250)); put(px, cx + 1, top, (236, 255, 250))
    return img


def bone_spire(rnd):
    img = canvas(); px = img.load()
    LIGHT, MID, DARK = (244, 240, 222), (214, 206, 182), (176, 166, 140)
    for x0, h in ((7, 15), (3, 10), (12, 12)):
        for i in range(h):
            y = 15 - i
            x = x0 + (1 if i > h * 0.6 and x0 != 7 else 0) * (1 if x0 > 7 else -1)
            put(px, x, y, LIGHT if i % 4 else MID)
            if i < h - 2:
                put(px, x + 1, y, DARK)
            if i in (h // 3, (2 * h) // 3):                   # side branches
                d = -1 if (i // 2) % 2 else 1
                for k in range(1, 3):
                    put(px, x + d * k, y - k, LIGHT if k == 2 else MID)
    return img


def puff(rnd, top):
    """Thin grass blades with soft rounded tufts (solid blobs lit from above-left, shadowed underneath)."""
    img = canvas(); px = img.load()
    greys = [(186, 186, 186), (206, 206, 206), (228, 228, 228), (246, 246, 246)]
    if not top:   # base: thin blades from the ground, a few tufts starting at the top edge
        for x in range(0, 16):
            if rnd.random() < 0.7:
                y0 = rnd.randint(3, 9)
                for y in range(y0, 16):
                    put(px, x, y, greys[x % 2])
        blobs = [(rnd.randint(2, 13), rnd.randint(1, 5), rnd.choice((2, 3))) for _ in range(4)]
    else:         # top: a cloud of rounded tufts sitting on the base
        blobs = [(rnd.randint(3, 12), rnd.randint(7, 13), rnd.choice((3, 3, 4))) for _ in range(5)]
    for cx, cy, r in sorted(blobs, key=lambda b: b[1]):          # back (higher) tufts first
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                dx, dy = x - cx, y - cy
                if dx * dx + dy * dy <= r * r + 1:
                    light = -dx - dy * 1.5                         # lit from above-left
                    shade = 3 if light > r * 0.9 else 2 if light > -r * 0.3 else 1
                    put(px, x, y, greys[shade])
    return img


def main():
    rnd = random.Random(SEED)
    imgs = {"glowcap": glowcap(rnd), "bone_spire": bone_spire(rnd),
            "puff_grass_bottom": puff(rnd, False), "puff_grass_top": puff(rnd, True)}
    OUT.mkdir(parents=True, exist_ok=True)
    prev = Image.new("RGBA", (len(imgs) * 136, 128 * 2 + 8), (36, 36, 42, 255))
    for i, (name, im) in enumerate(imgs.items()):
        im.save(OUT / f"{name}.png")
        prev.alpha_composite(im.resize((128, 128), Image.Resampling.NEAREST), (i * 136, 0))
    # puff grass stacked (bottom under top), tinted pink / teal like in game
    for j, tint in enumerate(((240, 138, 176), (79, 216, 196))):
        stack = Image.new("RGBA", (16, 32))
        stack.alpha_composite(imgs["puff_grass_top"], (0, 0)); stack.alpha_composite(imgs["puff_grass_bottom"], (0, 16))
        px = stack.load()
        for y in range(32):
            for x in range(16):
                r, g, b, a = px[x, y]
                if a:
                    px[x, y] = (r * tint[0] // 255, g * tint[1] // 255, b * tint[2] // 255, a)
        prev.alpha_composite(stack.resize((64, 128), Image.Resampling.NEAREST), (2 * 136 + j * 72, 136))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    prev.save(PREVIEW)
    print("wrote", ", ".join(imgs))


if __name__ == "__main__":
    main()
