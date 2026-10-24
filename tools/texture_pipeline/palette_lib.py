"""Shared helpers for the pysift texture pipeline: JSON IO, resource paths, CIELAB palettes and the
palette-composition distance used to judge whether textures belong to the same colour family."""
import json, math, hashlib
from pathlib import Path
from PIL import Image

COHERENCE_TH = 9.0  # max palette distance inside one random pool / stage


def project_paths(project):
    P = Path(project)
    res = P / "src/main/resources"
    return P, res, res / "assets/pysift", res / "data"


def lj(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def entries(v): return v if isinstance(v, list) else [v]


def res_path(assets_root, ref, kind, ext):
    """'pysift:block/x' -> <assets_root>/<ns>/<kind>/block/x<ext>; assets_root is .../resources/assets."""
    ns, path = ref.split(":", 1) if ":" in ref else ("minecraft", ref)   # no namespace = minecraft (as in the game)
    return Path(assets_root) / ns / kind / (path + ext)


def sha1(path): return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def pixel_sha1(path):
    im = Image.open(path).convert("RGBA")
    return hashlib.sha1(repr(im.size).encode() + im.tobytes()).hexdigest()


def lab(rgb):
    def f(c):
        c /= 255
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    r, g, b = (f(x) for x in rgb[:3])
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    h = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return 116 * h(y) - 16, 500 * (h(x) - h(y)), 200 * (h(y) - h(z))


def lab_to_rgb(L, a, b):
    """Inverse of lab() (same white point and gamma), clamped to 0..255."""
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    inv = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    x, y, z = inv(fx) * 0.95047, inv(fy), inv(fz) * 1.08883
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    bl = 0.0557 * x - 0.2040 * y + 1.0570 * z
    gam = lambda c: 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c
    return tuple(max(0, min(255, round(gam(max(0.0, c)) * 255))) for c in (r, g, bl))


def _ab_stats(labs):
    n = len(labs)
    ma = sum(l[1] for l in labs) / n
    mb = sum(l[2] for l in labs) / n
    sa = (sum((l[1] - ma) ** 2 for l in labs) / n) ** 0.5
    sb = (sum((l[2] - mb) ** 2 for l in labs) / n) ** 0.5
    return ma, mb, sa, sb


def tone_transfer(src_img, ref_img, mask=None, stats_img=None, match_l=False):
    """Tone mode: move only the colour (Lab a*, b*: hue and saturation) onto the reference by matching mean and
    spread; lightness L is kept, so pattern, shading and brightness stages stay exactly as they were.
    mask(rgba) -> False keeps a pixel untouched (caps, deliberate accents). The source statistics come from
    stats_img (e.g. the plain stone face of the same block, so a capped side matches its bottom) or else from
    the masked pixels of the source itself. Spread ratios are clamped to 0.5..1: variation is never amplified
    (amplifying it turns stray hues into new colours). match_l also shifts the mean lightness onto the reference
    (the light/dark pattern itself is kept), so a darker or lighter stone ends up at the reference's brightness."""
    ref = [lab(c) for c in ref_img.convert("RGBA").get_flattened_data() if c[3] > 0]
    src = src_img.convert("RGBA")
    px = list(src.get_flattened_data())
    keep = (lambda c: c[3] == 0 or (mask is not None and not mask(c)))
    if stats_img is not None:
        basis = [lab(c) for c in stats_img.convert("RGBA").get_flattened_data() if c[3] > 0]
    else:
        basis = [lab(c) for c in px if not keep(c)]
    if not basis:                       # mask left nothing to recolour
        return src.copy()
    ra, rb, rsa, rsb = _ab_stats(ref)
    ma, mb, sa, sb = _ab_stats(basis)
    dl = (sum(l[0] for l in ref) / len(ref) - sum(l[0] for l in basis) / len(basis)) if match_l else 0.0
    ka = min(1.0, max(0.5, rsa / sa)) if sa > 1e-6 else 1.0
    kb = min(1.0, max(0.5, rsb / sb)) if sb > 1e-6 else 1.0
    cache = {}

    def one(c):
        if keep(c):
            return c
        if c not in cache:
            L, a, b = lab(c)
            cache[c] = lab_to_rgb(min(100.0, max(0.0, L + dl)), (a - ma) * ka + ra, (b - mb) * kb + rb) + (c[3],)
        return cache[c]
    out = Image.new("RGBA", src.size)
    out.putdata([one(c) for c in px])
    return out


def cap_mask(stone_cols, cap_cols, keep_hue=None):
    """Pixel -> True when it belongs to the stone part: nearer (Lab) to the stone palette than to every cap colour,
    and not inside the protected hue range keep_hue=(from_deg, to_deg) with HSV saturation >= 0.25."""
    import colorsys
    stone = [lab(c) for c in stone_cols]
    cap = [lab(c) for c in cap_cols]
    memo = {}

    def test(c):
        if c in memo:
            return memo[c]
        ok = True
        if keep_hue:
            h, s, _ = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
            h *= 360
            lo, hi = keep_hue
            inside = lo <= h <= hi if lo <= hi else (h >= lo or h <= hi)
            if inside and s >= 0.25:
                ok = False
        if ok and cap:
            l = lab(c)
            ok = min(math.dist(l, s_) for s_ in stone) <= min(math.dist(l, c_) for c_ in cap)
        memo[c] = ok
        return ok
    return test


def palette(pixels):
    counts = {}
    for p in pixels:
        counts[p] = counts.get(p, 0) + 1
    n = len(pixels)
    return [(c / n, lab(rgb)) for rgb, c in counts.items()]


def one_way(p, q): return sum(w * min(math.dist(c, d) for _, d in q) for w, c in p)


def pdist(p, q):
    """Palette-composition distance: pixel-weighted mean distance to the nearest colour of the other texture."""
    return max(one_way(p, q), one_way(q, p))


class Tex:
    """A 16x16 block texture addressed by resource id (e.g. 'pysift:block/dark_slate/dark_slate_a')."""

    def __init__(self, ref, assets_root):
        self.ref = ref
        self.name = ref.rsplit("/", 1)[1]
        self.path = res_path(assets_root, ref, "textures", ".png")
        self.image = Image.open(self.path).convert("RGB")
        px = self.image.load()
        w, h = self.image.size
        self.grid = [[px[x, y] for x in range(w)] for y in range(h)]
        self.pal = palette([c for row in self.grid for c in row])

    def region(self, rows, cols): return [self.grid[y][x] for y in rows for x in cols]

    def band(self, side):
        """Best split line inside the half nearest `side` -> band palette, remaining palette and split score."""
        full = range(16)
        ks = range(2, 8) if side in ("top", "left") else range(9, 15)
        best = None
        for k in ks:
            if side in ("top", "bottom"):
                rb = range(0, k) if side == "top" else range(k, 16)
                rr = range(k, 16) if side == "top" else range(0, k)
                band_px, rest_px = self.region(rb, full), self.region(rr, full)
                halves = (self.region(rb, range(0, 8)), self.region(rb, range(8, 16)))
            else:
                cb = range(0, k) if side == "left" else range(k, 16)
                cr = range(k, 16) if side == "left" else range(0, k)
                band_px, rest_px = self.region(full, cb), self.region(full, cr)
                halves = (self.region(range(0, 8), cb), self.region(range(8, 16), cb))
            bp, rp = palette(band_px), palette(rest_px)
            d = pdist(bp, rp)
            if best is None or d > best["score"]:
                best = {"score": d, "halves": pdist(palette(halves[0]), palette(halves[1])), "band_pal": bp,
                        "rest_pal": rp, "share": len(band_px) / 256, "k": k, "band_px": band_px}
        return best

    def stripes(self):
        cols = [palette(self.region(range(16), [x])) for x in range(16)]
        rows = [palette(self.region([y], range(16))) for y in range(16)]
        adj = lambda seq: sum(pdist(a, b) for a, b in zip(seq, seq[1:])) / 15
        return adj(cols), adj(rows)


def iter_pools(assets_pysift):
    """Yield (block, state_key, [model refs]) for every variant pool, skipping orientation duplicates
    (only facing=up / axis=y are reported)."""
    for bs in sorted((Path(assets_pysift) / "blockstates").glob("*.json")):
        j = lj(bs)
        if "multipart" in j:   # walls: each part is a pool of its own
            for i, part in enumerate(j["multipart"]):
                yield bs.stem, f"part{i}", [e["model"] for e in entries(part["apply"])]
            continue
        for key, v in j["variants"].items():
            if ("facing=" in key and "facing=up" not in key) or ("axis=" in key and "axis=y" not in key):
                continue
            yield bs.stem, key, [e["model"] for e in entries(v)]


def cube_all_texture(assets_root, model_ref):
    m = lj(res_path(assets_root, model_ref, "models", ".json"))
    return m["textures"]["all"] if m.get("parent", "").endswith("cube_all") else None


def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def remap(src_img, ref_img):
    """Palette mode: stretch the source brightness range onto the reference's and take the reference colour
    with the nearest brightness. Shapes never change; transparent pixels are kept."""
    ref_cols = sorted({c for c in ref_img.convert("RGBA").getdata() if c[3] > 0}, key=lum)
    rl = [lum(c) for c in ref_cols]
    src = src_img.convert("RGBA")
    px = list(src.getdata())
    ls = [lum(c) for c in px if c[3] > 0]
    lo, hi = min(ls), max(ls)

    def one(c):
        if c[3] == 0:
            return c
        t = (lum(c) - lo) / (hi - lo) if hi > lo else 0.5
        target = rl[0] + t * (rl[-1] - rl[0])
        r = min(ref_cols, key=lambda rc: abs(lum(rc) - target))
        return (r[0], r[1], r[2], c[3])
    out = Image.new("RGBA", src.size)
    out.putdata([one(c) for c in px])
    return out


def remap_rank(src_img, ref_pixels):
    """Rank mode: order the source pixels by brightness and hand out the reference pixels (also ordered by
    brightness) at the same percentile, so the colour proportions follow the reference exactly while the
    light/dark arrangement of the source is kept. Used for generated faces whose band mixes several hues."""
    src = src_img.convert("RGB")
    px = list(src.getdata())
    ref = sorted(ref_pixels, key=lum)
    order = sorted(range(len(px)), key=lambda i: (lum(px[i]), i))
    out = [None] * len(px)
    for rank, i in enumerate(order):
        out[i] = ref[min(len(ref) - 1, rank * len(ref) // len(px))]
    img = Image.new("RGB", src.size)
    img.putdata(out)
    return img
