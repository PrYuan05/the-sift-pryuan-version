"""Generate the animated spirit_liquid (Ichor / "ouch water") fluid textures: an opaque-ish iridescent nebula.
Usage: python -I tools/texture_pipeline/spirit_liquid.py <project> [--dry-run]

Writes NEW files only (never touches existing PNGs):
  textures/block/fluid/spirit_liquid_still.png   128x128 (8x8 blocks; FluidRendererMixin maps it in world space),
                                                 STILL_FRAMES frames, drifts one full tile diagonally per loop
  textures/block/fluid/spirit_liquid_flow.png    32x32, FLOW_FRAMES frames, scrolls 1 px per frame along v
  textures/block/fluid/spirit_liquid_overlay.png 16x16, top-left block of the first still frame
  + .png.mcmeta for the two animated sprites
and a 4x4 tiled preview + frame strip in build/texture_pipeline/out/spirit_liquid_preview.png.
Every pattern term uses integer frequencies, so the tile repeats seamlessly and the animation loops."""
import sys, json, math, random
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]).resolve()
DRY = "--dry-run" in sys.argv
OUT_DIR = P / "src/main/resources/assets/pysift/textures/block/fluid"
PREVIEW = P / "build/texture_pipeline/out/spirit_liquid_preview.png"
STILL_SIZE = 128     # must match FluidRendererMixin.SPIRIT_TILE * 16
STILL_FRAMES = 64
STILL_FREQ = 1       # one nebula cycle per 8-block tile
STILL_DETAIL = 0.35  # off-axis harmonics: lower = larger, smoother colour patches (promo art look)
FLOW_FRAMES = 32
ALPHA = 225          # vanilla water is ~180; higher = less see-through
STAR_ALPHA = 240
TAU = math.tau

# cyclic colour ramp sampled by the nebula field, saturated like the official The Sift art:
# magenta -> hot pink -> orange -> yellow -> mint -> cyan -> sky blue -> violet -> purple
RAMP = [(0xE0, 0x3C, 0xC8), (0xFF, 0x6E, 0xB4), (0xFF, 0xA0, 0x5A), (0xF8, 0xE0, 0x6A), (0x6E, 0xF0, 0xA8),
        (0x3C, 0xE0, 0xE8), (0x48, 0xA4, 0xF4), (0x78, 0x50, 0xE6), (0xB0, 0x46, 0xE0)]
HUE_SWING = 0.95     # how much of the ramp the field sweeps (was 0.42 = pastel pink/lavender only)
HIGHLIGHT = 0.26     # pastel lift on the bright crests (was 0.14; user: brighter)
SHADE = 0.12         # darkening in the troughs (was 0.32; user: brighter)
LIFT = 0.12          # every pixel blended this much towards white (user: brighter)


def ramp(t):
    t = (t % 1.0) * len(RAMP)
    i = int(t)
    f = t - i
    f = f * f * (3 - 2 * f)
    a, b = RAMP[i % len(RAMP)], RAMP[(i + 1) % len(RAMP)]
    return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))


def field(u, v, ph, detail=0.0):
    """Domain-warped sum of periodic waves; u, v in tile units (period 1), ph = animation phase in [0, 1).
    detail > 0 mixes in higher, off-axis harmonics so a large tile does not read as a regular grid."""
    wu = 0.07 * math.sin(TAU * (v + ph)) + 0.03 * math.sin(TAU * (u - 2 * v - ph))
    wv = 0.07 * math.sin(TAU * (u - ph)) + 0.03 * math.sin(TAU * (2 * u + v + ph))
    if detail:
        wu += detail * (0.05 * math.sin(TAU * (3 * v - 2 * u + ph)) + 0.03 * math.sin(TAU * (5 * v + u - 2 * ph)))
        wv += detail * (0.05 * math.sin(TAU * (3 * u + v - ph)) + 0.03 * math.sin(TAU * (4 * u - 3 * v + ph)))
    u, v = u + wu, v + wv
    hue = (0.60 * math.sin(TAU * (u + ph))
           + 0.40 * math.sin(TAU * (v - ph))
           + 0.25 * math.sin(TAU * (u + v + 2 * ph)))
    light = 0.6 * math.sin(TAU * (u - v - ph)) + 0.4 * math.sin(TAU * (2 * v + u + ph))
    if detail:
        hue += detail * (0.35 * math.sin(TAU * (2 * u - 3 * v - ph)) + 0.25 * math.sin(TAU * (3 * u + 2 * v + ph)))
        light += detail * 0.4 * math.sin(TAU * (4 * u + 3 * v - 2 * ph))
        hue /= 1 + 0.5 * detail
    return hue / 1.25, light


def pixel(u, v, ph, detail=0.0):
    hue, light = field(u, v, ph, detail)
    r, g, b = ramp(0.05 + hue * HUE_SWING)          # sweeps most of the saturated ramp
    if light > 0:                                   # light highlights on the crests
        k = light * HIGHLIGHT
        r, g, b = r + (255 - r) * k, g + (255 - g) * k, b + (255 - b) * k
    else:                                           # deeper troughs
        k = 1 + light * SHADE
        r, g, b = r * k, g * k, b * k
    return [c + (255 - c) * LIFT for c in (r, g, b)]


def stars(size, count, seed):
    rnd = random.Random(seed)
    return [(rnd.randrange(size), rnd.randrange(size), rnd.random(), rnd.choice((1, 1, 2)), rnd.random() < 0.25)
            for _ in range(count)]


def frame(size, ph, star_list, shift=(0, 0), freq=1, detail=0.0):
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            r, g, b = pixel(freq * ((x - shift[0]) % size) / size, freq * ((y - shift[1]) % size) / size, ph, detail)
            px[x, y] = (int(min(255, r)), int(min(255, g)), int(min(255, b)), ALPHA)
    for sx, sy, phase, speed, cross in star_list:
        tw = 0.5 + 0.5 * math.sin(TAU * (speed * ph + phase))      # integer speed -> loops
        if tw < 0.35:
            continue
        x, y = (sx + shift[0]) % size, (sy + shift[1]) % size
        pts = [(x, y)] + ([((x + dx) % size, (y + dy) % size) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                           if cross and tw > 0.8 else [])
        for i, (qx, qy) in enumerate(pts):
            k = tw if i == 0 else tw * 0.45
            r, g, b, _ = px[qx, qy]
            c = (255, 255, 255) if i == 0 else (225, 250, 255)
            px[qx, qy] = (int(r + (c[0] - r) * k), int(g + (c[1] - g) * k), int(b + (c[2] - b) * k), STAR_ALPHA)
    return img


def sheet(frames):
    w, h = frames[0].size
    out = Image.new("RGBA", (w, h * len(frames)))
    for i, f in enumerate(frames):
        out.paste(f, (0, i * h))
    return out


def main():
    still_stars = stars(STILL_SIZE, 70, 7)
    flow_stars = stars(32, 14, 11)
    step = STILL_SIZE // STILL_FRAMES                                   # 2 px/frame -> one full tile per loop
    still = [frame(STILL_SIZE, i / STILL_FRAMES, still_stars, shift=(i * step, i * step), freq=STILL_FREQ, detail=STILL_DETAIL)
             for i in range(STILL_FRAMES)]
    flow = [frame(32, i / FLOW_FRAMES, flow_stars, shift=(0, i)) for i in range(FLOW_FRAMES)]   # 1 px/frame

    alphas = {a for f in still + flow for *_, a in f.get_flattened_data()}
    assert min(alphas) >= 200 and max(alphas) <= 240, alphas

    # preview: still frame 0 tiled 2x2 (= 16x16 blocks, seam check), flow frame 0 tiled 2x2, every 8th still frame
    W = STILL_SIZE * 2 * 2
    prev = Image.new("RGBA", (W + 16 + 64 * 8, W + 16 + STILL_SIZE), (20, 20, 24, 255))
    tile = Image.new("RGBA", (STILL_SIZE * 2, STILL_SIZE * 2))
    for ty in range(2):
        for tx in range(2):
            tile.paste(still[0], (tx * STILL_SIZE, ty * STILL_SIZE))
    prev.alpha_composite(tile.resize((W, W), Image.NEAREST), (0, 0))
    ftile = Image.new("RGBA", (64, 64))
    for ty in range(2):
        for tx in range(2):
            ftile.paste(flow[0], (tx * 32, ty * 32))
    prev.alpha_composite(ftile.resize((64 * 8, 64 * 8), Image.NEAREST), (W + 16, 0))
    for i, f in enumerate(still[::8]):
        prev.alpha_composite(f, (i * (STILL_SIZE + 4), W + 16))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    prev.save(PREVIEW)
    print("preview:", PREVIEW)

    files = {
        "spirit_liquid_still.png": sheet(still),
        "spirit_liquid_flow.png": sheet(flow),
        "spirit_liquid_overlay.png": still[0].crop((0, 0, 16, 16)),
    }
    meta = {"animation": {"frametime": 4, "interpolate": True}}   # still: 64 x 4 ticks = 12.8 s per loop
    if DRY:
        print("dry run; would write", ", ".join(files))
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, img in files.items():
        img.save(OUT_DIR / name)
        print("wrote", OUT_DIR / name, img.size)
    for name in ("spirit_liquid_still.png", "spirit_liquid_flow.png"):
        (OUT_DIR / (name + ".mcmeta")).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
