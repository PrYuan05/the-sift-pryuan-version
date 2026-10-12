"""Read-only: find cube_all textures with a distinct edge band (grass-block style) or vertical stripes (pillar),
work out which UV transform brings the edge band to the top, and propose top/bottom (or end) faces from the
existing texture library. Writes only to <out_dir>.
Usage: python -I directional_scan.py <project> <out_dir>"""
import json, sys, math, itertools
from pathlib import Path
from PIL import Image, ImageDraw

P, OUT = Path(sys.argv[1]), Path(sys.argv[2])
A = P / "src/main/resources/assets/pysift"
SPLIT_TH = 12.0     # palette distance between the two sides of the best split line to count as an edge band
HALF_TH = 15.0      # the band must look alike along the whole edge (first half vs second half)
EXCLUDE_BLOCKS = {"glyph_block"}      # designed rune patterns, not natural bands
STRIPE_RATIO, STRIPE_MIN = 2.0, 6.0
MANUAL = {"dark_slate_l": "pillar"}   # user-requested
# PIL transposes that reproduce each in-game UV transform (face rotation is clockwise in Minecraft)
TRANSFORMS = {"none": None, "vflip": Image.Transpose.FLIP_TOP_BOTTOM,
              "rot90": Image.Transpose.ROTATE_270, "rot270": Image.Transpose.ROTATE_90}
EDGE_TO_TRANSFORM = {"top": "none", "bottom": "vflip", "left": "rot90", "right": "rot270"}
OPPOSITE = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}
COLOR_ZH = {"gray": "灰", "warm": "暖褐", "olive": "橄欖", "teal": "青碧", "violet": "紫晶", "crimson": "赤紅",
            "rose": "玫瑰", "mottled": "斑駁"}


def lj(p): return json.loads(p.read_text(encoding="utf-8"))


def lab(rgb):
    def f(c):
        c /= 255
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    r, g, b = (f(x) for x in rgb)
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


def pdist(p, q): return max(one_way(p, q), one_way(q, p))


class Tex:
    def __init__(self, ref):
        self.ref = ref
        self.name = ref.rsplit("/", 1)[1]
        self.image = Image.open(A / "textures" / (ref.split(":", 1)[1] + ".png")).convert("RGB")
        px = self.image.load()
        self.grid = [[px[x, y] for x in range(16)] for y in range(16)]
        self.pal = palette([c for row in self.grid for c in row])

    def region(self, rows, cols): return [self.grid[y][x] for y in rows for x in cols]

    def band(self, side):
        """Best split line inside the half nearest `side`; returns band palette, the rest, and the split score."""
        full = range(16)
        ks = range(2, 8) if side in ("top", "left") else range(9, 15)
        best = None
        for k in ks:
            if side in ("top", "bottom"):
                rows_band = range(0, k) if side == "top" else range(k, 16)
                rows_rest = range(k, 16) if side == "top" else range(0, k)
                band_px, rest_px = self.region(rows_band, full), self.region(rows_rest, full)
                halves = (self.region(rows_band, range(0, 8)), self.region(rows_band, range(8, 16)))
            else:
                cols_band = range(0, k) if side == "left" else range(k, 16)
                cols_rest = range(k, 16) if side == "left" else range(0, k)
                band_px, rest_px = self.region(full, cols_band), self.region(full, cols_rest)
                halves = (self.region(range(0, 8), cols_band), self.region(range(8, 16), cols_band))
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

    def oriented(self, transform):
        t = TRANSFORMS[transform]
        return self.image if t is None else self.image.transpose(t)


def hue_word(pal):
    L, a, b = (sum(w * c[i] for w, c in pal) for i in range(3))
    chroma, hue = math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360
    if chroma < 6:
        return "gray"
    if hue < 40 or hue >= 330:
        return "crimson" if chroma > 20 else "rose"
    if hue < 100:
        return "warm"
    if hue < 160:
        return "olive"
    if hue < 250:
        return "teal"
    return "violet"


# ---- gather every texture referenced by a blockstate, remembering where cube_all ones are used ----
usage, library = {}, {}
for bs in sorted((A / "blockstates").glob("*.json")):
    for key, v in lj(bs)["variants"].items():
        for e in (v if isinstance(v, list) else [v]):
            m = lj(A / "models" / (e["model"].split(":", 1)[1] + ".json"))
            for face, ref in m["textures"].items():
                library.setdefault(ref, None)
            if m["parent"].endswith("cube_all"):
                usage.setdefault(m["textures"]["all"], []).append({"block": bs.stem, "state": key, "model": e["model"]})
texs = {ref: Tex(ref) for ref in library}
zh = lj(A / "lang/zh_tw.json")

# ---- detect ----
candidates = []
for ref, uses in usage.items():
    t = texs[ref]
    if all(u["block"] in EXCLUDE_BLOCKS for u in uses):
        continue
    edges = {s: t.band(s) for s in ("top", "bottom", "left", "right")}
    banded = {s: e for s, e in edges.items() if e["score"] >= SPLIT_TH and e["halves"] < HALF_TH}
    col_adj, row_adj = t.stripes()
    vertical = col_adj > STRIPE_MIN and col_adj > STRIPE_RATIO * max(row_adj, 0.1)
    kind = MANUAL.get(t.name)
    if kind is None:
        if vertical and not banded:
            kind = "pillar"
        elif banded:
            kind = "grass"
        else:
            continue
    entry = {"texture": ref, "name": t.name, "uses": uses, "kind": kind,
             "edges": {s: round(e["score"], 1) for s, e in edges.items()},
             "stripes": {"col": round(col_adj, 1), "row": round(row_adj, 1)}}
    if banded:
        # top edge = the most distinctive band (edge-like material); ties go to the band with the larger colour share
        order = sorted(banded, key=lambda s: (round(banded[s]["score"]), banded[s]["share"]), reverse=True)
        entry["top_edge"] = order[0]
        entry["transform"] = EDGE_TO_TRANSFORM[order[0]]
        entry["alt_transform"] = EDGE_TO_TRANSFORM[order[1]] if len(order) > 1 else None
        entry["_top_pal"] = banded[order[0]]["band_pal"]
        opp = OPPOSITE[order[0]]
        entry["_bottom_pal"] = edges[opp]["band_pal"] if opp in banded else banded[order[0]]["rest_pal"]
    candidates.append(entry)

cand_refs = {c["texture"] for c in candidates}
lib = [texs[r] for r in library if r not in cand_refs]


def best(pal, exclude, k=3):
    scored = sorted(((pdist(pal, x.pal), x) for x in lib if x.ref not in exclude), key=lambda s: s[0])
    return [{"texture": x.ref, "dist": round(d, 1)} for d, x in scored[:k]]


used_ids = set(p.stem for p in (A / "blockstates").glob("*.json"))
for i, c in enumerate(candidates, 1):
    c["id"] = i
    src = c["uses"][0]["block"]
    src_zh = zh.get(f"block.pysift.{src}", src)
    if c["kind"] == "pillar":
        c["end_candidates"] = best(texs[c["texture"]].pal, {c["texture"]})
        new_id, new_zh = f"{src}_pillar", f"{src_zh}柱"
    else:
        c["top_candidates"] = best(c.pop("_top_pal"), {c["texture"]})
        c["bottom_candidates"] = best(c.pop("_bottom_pal"), {c["texture"]})
        word = hue_word(texs[c["top_candidates"][0]["texture"]].pal)
        new_id, new_zh = f"{word}_capped_{src}", f"{COLOR_ZH[word]}覆蓋{src_zh}"
    base, k = new_id, 2
    while new_id in used_ids:
        new_id, k = f"{base}_{k}", k + 1
    used_ids.add(new_id)
    c["proposed_id"], c["proposed_zh"] = new_id, new_zh
    c.pop("_top_pal", None)
    c.pop("_bottom_pal", None)

# ---- review sheet ----
S, PAD, LH = 6, 6, 12
TILE = 16 * S
cols = 9
W = 70 + cols * (TILE + PAD)
H = 24 + len(candidates) * (TILE + LH * 2 + PAD)
sheet = Image.new("RGB", (W, H), (28, 28, 32))
dr = ImageDraw.Draw(sheet)
dr.text((PAD, 4), "#  | original | oriented (UV) | top 1-3 | bottom 1-3   (pillar: original | end 1-3)", fill=(235, 235, 235))
y = 24
for c in candidates:
    t = texs[c["texture"]]
    dr.text((PAD, y + TILE // 2), f"#{c['id']}", fill=(250, 210, 90))
    x = 70
    tiles = [(t.image, t.name)]
    if c["kind"] == "pillar":
        tiles += [(texs[e["texture"]].image, f"end{j}") for j, e in enumerate(c["end_candidates"], 1)]
    else:
        tiles += [(t.oriented(c["transform"]), c["transform"])]
        tiles += [(texs[e["texture"]].image, f"top{j}") for j, e in enumerate(c["top_candidates"], 1)]
        tiles += [(texs[e["texture"]].image, f"bot{j}") for j, e in enumerate(c["bottom_candidates"], 1)]
    for img, label in tiles:
        sheet.paste(img.resize((TILE, TILE), Image.Resampling.NEAREST), (x, y))
        dr.text((x, y + TILE + 1), label[:16], fill=(210, 210, 210))
        x += TILE + PAD
    where = ", ".join(sorted({f"{u['block']}[{u['state'] or '-'}]" for u in c["uses"]}))
    dr.text((70, y + TILE + LH), f"{c['kind']} -> {c['proposed_id']}  ({where})", fill=(150, 200, 255))
    y += TILE + LH * 2 + PAD
OUT.mkdir(parents=True, exist_ok=True)
sheet.save(OUT / "directional_review.png")
(OUT / "directional_proposal.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=1), encoding="utf-8")
for c in candidates:
    faces = (f"end={c['end_candidates'][0]['texture'].rsplit('/', 1)[1]}" if c["kind"] == "pillar" else
             f"{c['transform']}(alt {c['alt_transform']}) top={c['top_candidates'][0]['texture'].rsplit('/', 1)[1]} "
             f"bottom={c['bottom_candidates'][0]['texture'].rsplit('/', 1)[1]}")
    print(f"#{c['id']:2d} {c['name']:36s} {c['kind']:6s} -> {c['proposed_id']:34s} {faces}  edges={c['edges']} stripes={c['stripes']}")
