"""Read-only: propose tone groups for random pools and flag stage outliers in progressive blocks.
Usage: python -I tone_groups.py <project> <out_dir>
Distance = palette-composition distance: symmetric, pixel-count-weighted mean distance (CIELAB) from each
colour of one texture to the nearest colour of the other; groups by complete linkage."""
import json, sys, math, colorsys
from pathlib import Path
from PIL import Image, ImageDraw

P, OUT = Path(sys.argv[1]), Path(sys.argv[2])
A = P / "src/main/resources/assets/pysift"
GROUP_TH, MERGE_TH = 9.0, 9.0
SHEETS = OUT / "tone_sheets"
SHEETS.mkdir(parents=True, exist_ok=True)


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


def texture_of(model_ref):
    tex = lj(A / "models" / (model_ref.split(":", 1)[1] + ".json"))["textures"]
    ref = tex.get("all") or tex.get("side") or next(iter(tex.values()))
    return A / "textures" / (ref.split(":", 1)[1] + ".png")


class Tex:
    def __init__(self, model_ref):
        self.model = model_ref
        self.label = model_ref.rsplit("/", 1)[1]
        self.png = texture_of(model_ref)
        im = Image.open(self.png).convert("RGB")
        self.image = im
        counts = im.getcolors(4096)
        n = sum(c for c, _ in counts)
        self.palette = [(c / n, lab(rgb)) for c, rgb in counts]
        self.mean = tuple(sum(w * l[i] for w, l in self.palette) for i in range(3))


def one_way(p, q):
    return sum(w * min(math.dist(c, d) for _, d in q) for w, c in p)


def dist(a, b): return max(one_way(a.palette, b.palette), one_way(b.palette, a.palette))


def complete_linkage(items, th):
    cl = [[t] for t in items]
    while True:
        best = None
        for i in range(len(cl)):
            for j in range(i + 1, len(cl)):
                d = max(dist(a, b) for a in cl[i] for b in cl[j])
                if d < th and (best is None or d < best[0]):
                    best = (d, i, j)
        if not best:
            return cl
        _, i, j = best
        cl[i] += cl.pop(j)


def tone_name(group, block_mean_l):
    pal = [(w / len(group), c) for t in group for w, c in t.palette]
    def hue(c): return math.degrees(math.atan2(c[2], c[1])) % 360
    def chroma(c): return math.hypot(c[1], c[2])
    warm = sum(w for w, c in pal if chroma(c) > 12 and (hue(c) < 100 or hue(c) >= 345))
    cool = sum(w for w, c in pal if chroma(c) > 12 and 150 <= hue(c) < 250)
    if warm >= 0.15 and cool >= 0.15:
        base = "mottled"
    else:
        L, a, b = (sum(t.mean[i] for t in group) / len(group) for i in range(3))
        chroma, hue = math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360
        if chroma < 6:
            base = "gray"
        elif hue < 40 or hue >= 330:
            base = "crimson" if chroma > 20 else "rose"
        elif hue < 100:
            base = "warm"
        elif hue < 160:
            base = "olive"
        elif hue < 250:
            base = "teal"
        else:
            base = "violet"
    L = sum(t.mean[0] for t in group) / len(group)
    if L > block_mean_l + 8:
        base = "light_" + base
    elif L < block_mean_l - 8:
        base = "dark_" + base
    return base


def sheet(path, rows, title):
    scale, pad, lab_h = 8, 6, 14
    tile = 16 * scale
    width = max(len(r[1]) for r in rows) * (tile + pad) + pad + 150
    height = len(rows) * (tile + lab_h + pad) + pad + 20
    img = Image.new("RGB", (width, height), (30, 30, 34))
    dr = ImageDraw.Draw(img)
    dr.text((pad, 4), title, fill=(230, 230, 230))
    y = 22
    for name, texs in rows:
        dr.text((pad, y + tile // 2), name, fill=(240, 220, 120))
        x = 150
        for t in texs:
            img.paste(t.image.resize((tile, tile), Image.Resampling.NEAREST), (x, y))
            dr.text((x + 2, y + tile + 1), t.label.split("_")[-1] if len(t.label.split("_")[-1]) <= 2 else t.label, fill=(220, 220, 220))
            x += tile + pad
        y += tile + lab_h + pad
    img.save(path)


proposal, outliers = {}, {}
for bs in sorted((A / "blockstates").glob("*.json")):
    var = lj(bs)["variants"]
    bid = bs.stem
    if list(var) == [""]:
        v = var[""]
        if not isinstance(v, list) or len(v) < 2:
            continue
        items = [Tex(e["model"]) for e in v]
        groups = complete_linkage(items, GROUP_TH)
        groups.sort(key=len, reverse=True)
        # fold singletons into the nearest group when close enough
        multi = [g for g in groups if len(g) > 1]
        for g in [g for g in groups if len(g) == 1]:
            near = min(multi, key=lambda m: max(dist(g[0], t) for t in m), default=None)
            if near is not None and max(dist(g[0], t) for t in near) < MERGE_TH:
                near.append(g[0])
            else:
                multi.append(g)
        groups = multi
        overall = max(dist(a, b) for a in items for b in items)
        mean_l = sum(t.mean[0] for t in items) / len(items)
        if len(groups) == 1:
            proposal[bid] = {"status": "coherent", "max_dist": round(overall, 1)}
            continue
        names, out = set(), []
        for g in groups:
            n = tone_name(g, mean_l)
            base, k = n, 2
            while n in names:
                n, k = f"{base}_{k}", k + 1
            names.add(n)
            out.append({"tone": n, "labels": [t.label for t in g], "models": [t.model for t in g],
                        "max_dist": round(max((dist(a, b) for a in g for b in g), default=0), 1)})
        proposal[bid] = {"status": "split", "max_dist_before": round(overall, 1), "groups": out}
        sheet(SHEETS / f"{bid}.png", [(o["tone"], [t for t in items if t.model in o["models"]]) for o in out],
              f"{bid}: {len(items)} variants -> {len(out)} tones (before max dist {overall:.1f})")
    else:
        # progressive / multi-state block: check in-state pools for members closer to another state
        states = {k: [Tex(e["model"]) for e in (v if isinstance(v, list) else [v])] for k, v in var.items()}
        flagged = []
        seen_pools = set()
        for k, texs in states.items():
            key = tuple(t.model for t in texs)
            if len(texs) < 2 or key in seen_pools:  # skip aliased pools (frost_veined_stone fill-ins)
                continue
            seen_pools.add(key)
            for t in texs:
                own = [o for o in texs if o is not t]
                d_own = min(dist(t, o) for o in own)
                best_k, best_d = min(((k2, min(dist(t, o) for o in ts)) for k2, ts in states.items()
                                      if k2 != k and tuple(o.model for o in ts) != key),
                                     key=lambda x: x[1], default=(None, 1e9))
                if best_k and best_d < d_own - 2:
                    flagged.append({"state": k, "label": t.label, "model": t.model, "closer_to": best_k,
                                    "dist_own": round(d_own, 1), "dist_other": round(best_d, 1)})
        if flagged:
            outliers[bid] = flagged
            rows = [(k, ts) for k, ts in states.items()]
            sheet(SHEETS / f"{bid}__states.png", rows, f"{bid}: stage pools (flagged: " +
                  ", ".join(f"{f['label'].split('_')[-1]}@{f['state']}->{f['closer_to']}" for f in flagged) + ")")

(OUT / "tone_proposal.json").write_text(json.dumps({"tones": proposal, "stage_outliers": outliers},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
for bid, p in proposal.items():
    if p["status"] == "split":
        print(f"{bid:16s} {p['max_dist_before']:5.1f} -> " + "  ".join(f"{g['tone']}[{','.join(l.split('_')[-1] for l in g['labels'])}]({g['max_dist']})" for g in p["groups"]))
    else:
        print(f"{bid:16s} coherent (max {p['max_dist']})")
print("stage outliers:")
for bid, fl in outliers.items():
    for f in fl:
        print(f"  {bid}: {f['label']} in {f['state']} closer to {f['closer_to']} ({f['dist_own']} vs {f['dist_other']})")
