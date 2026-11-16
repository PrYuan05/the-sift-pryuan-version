"""Generate the animated spirit_liquid (Ichor / "ouch water") fluid textures: an opaque-ish iridescent nebula.
Usage: python -I tools/texture_pipeline/spirit_liquid.py <project> [--dry-run]

Writes NEW files only (never touches existing PNGs):
  textures/block/fluid/spirit_liquid_still.png   512x512 (32x32 blocks, for wide spirit rivers; FluidRendererMixin and
                                                 SodiumFluidRendererMixin map it in world space), STILL_FRAMES frames;
                                                 built from irregular waves (BIG_*) so nothing repeats inside the 32x32
                                                 blocks; each wave drifts at its own speed and the loop is seamless
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
STILL_SIZE = 512     # must match FluidRendererMixin.SPIRIT_TILE * 16 (32 blocks)
STILL_FRAMES = 32    # 32 x 8 ticks = 12.8 s per loop (64 frames at 512x512 would be a 64 MB sprite)
STILL_FREQ = 4       # > 1 selects the big-tile field (features ~ 6-8 blocks, as before)
STILL_FRAMETIME = 8
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


# Big tile (32 blocks): waves whose integer wave vectors point in many directions with lengths ~3-6 per tile, so the
# features are about as big as the old 8-block pattern but nothing repeats inside the 32x32 tile. Each wave's phase
# turns an integer number of times per loop (m), so every wave drifts at its own speed and the loop is seamless.
#            (kx, ky, amplitude, phase, m)
BIG_HUE = [(4, 1, 0.55, 0.10, 1), (-3, 4, 0.45, 0.37, -1), (5, -2, 0.30, 0.71, 1), (1, 5, 0.30, 0.52, -1),
           (-4, -3, 0.22, 0.05, 1), (6, 3, 0.15, 0.88, -1)]
BIG_LIGHT = [(3, -4, 0.55, 0.23, -1), (5, 3, 0.40, 0.61, 1), (-2, 6, 0.30, 0.94, 1), (7, -1, 0.20, 0.42, -1)]
BIG_WARP_U = [(2, 3, 0.022, 0.13, 1), (-3, 5, 0.012, 0.66, -1)]
BIG_WARP_V = [(3, -2, 0.022, 0.48, -1), (5, 2, 0.012, 0.29, 1)]


def waves(terms, U, V, ph):
    return sum(a * math.sin(TAU * (kx * U + ky * V + p + m * ph)) for kx, ky, a, p, m in terms)


def big_field(U, V, ph):
    U, V = U + waves(BIG_WARP_U, U, V, ph), V + waves(BIG_WARP_V, U, V, ph)
    return waves(BIG_HUE, U, V, ph) / 1.6, waves(BIG_LIGHT, U, V, ph) / 1.1


def pixel(u, v, ph, detail=0.0, big=False):
    hue, light = big_field(u, v, ph) if big else field(u, v, ph, detail)
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
            if freq > 1:   # big tile: the waves drift on their own, no shift
                r, g, b = pixel(x / size, y / size, ph, big=True)
            else:
                r, g, b = pixel(freq * ((x - shift[0]) % size) / size, freq * ((y - shift[1]) % size) / size, ph, detail)
            px[x, y] = (int(min(255, r)), int(min(255, g)), int(min(255, b)), ALPHA)
    for sx, sy, phase, speed, cross in star_list:
        tw = 0.5 + 0.5 * math.sin(TAU * (speed * ph + phase))      # integer speed -> loops
        if tw < 0.35:
            continue
        # on the big tile the nebula only drifts a quarter tile per loop, so moving stars would jump back at the loop;
        # they stay put and only twinkle there
        sh = shift if freq == 1 else (0, 0)
        x, y = (sx + sh[0]) % size, (sy + sh[1]) % size
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
    still_stars = stars(STILL_SIZE, 70 * (STILL_SIZE // 128) ** 2, 7)
    flow_stars = stars(32, 14, 11)
    step = 0                                                            # big tile: waves drift by phase instead
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
    meta = {"animation": {"frametime": 4, "interpolate": True}}
    still_meta = {"animation": {"frametime": STILL_FRAMETIME, "interpolate": True}}
    if DRY:
        print("dry run; would write", ", ".join(files))
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, img in files.items():
        img.save(OUT_DIR / name)
        print("wrote", OUT_DIR / name, img.size)
    for name, m in (("spirit_liquid_still.png", still_meta), ("spirit_liquid_flow.png", meta)):
        (OUT_DIR / (name + ".mcmeta")).write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
