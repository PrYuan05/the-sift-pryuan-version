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
    ns, path = ref.split(":", 1)
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
                        "rest_pal": rp, "share": len(band_px) / 256}
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
        for key, v in lj(bs)["variants"].items():
            if ("facing=" in key and "facing=up" not in key) or ("axis=" in key and "axis=y" not in key):
                continue
            yield bs.stem, key, [e["model"] for e in entries(v)]


def cube_all_texture(assets_root, model_ref):
    m = lj(res_path(assets_root, model_ref, "models", ".json"))
    return m["textures"]["all"] if m.get("parent", "").endswith("cube_all") else None
