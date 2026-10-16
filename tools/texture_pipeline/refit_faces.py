"""Re-pick orientation and top/bottom (or end) faces of the pipeline-made composite blocks.
Usage: python -I tools/texture_pipeline/refit_faces.py <project> [--dry-run]

Orientation: kept as is unless face_rules.json "orientation" names a transform for the block (the automatic
drip score -- does the band hang away from the edge? -- is only reported, it was too unreliable to apply).
Pillars keep their orientation.
Faces: candidates are cube_all textures of non-excluded blocks (face_rules.json), never banded/side textures.
A candidate must be within max_band_delta (mean CIELAB) of the side band it meets, and the variants of one face
within max_pool_spread (palette distance) of each other. PNGs are never written."""
import sys, re, json, math, statistics, shutil
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import project_paths, lj, wj, entries, res_path, Tex, pdist, palette, lab

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
HERE = Path(__file__).resolve().parent
OUT = P / "build/texture_pipeline/out"
DRY = "--dry-run" in sys.argv
RULES = lj(HERE / "face_rules.json")
T = Image.Transpose
GRASS = {"minecraft:block/cube_bottom_top": "none", "pysift:block/templates/cube_bottom_top_vflip": "vflip",
         "pysift:block/templates/cube_bottom_top_rot90": "rot90", "pysift:block/templates/cube_bottom_top_rot270": "rot270"}
PARENT = {v: k for k, v in GRASS.items()}
PILLAR = {"minecraft:block/cube_column": None, "pysift:block/templates/cube_column_vflip": T.FLIP_TOP_BOTTOM}
ORIENT = {"none": None, "vflip": T.FLIP_TOP_BOTTOM, "rot90": T.ROTATE_270, "rot270": T.ROTATE_90}
FACING_ROT = {"up": {}, "down": {"x": 180}, "north": {"x": 90}, "south": {"x": 90, "y": 180},
              "east": {"x": 90, "y": 90}, "west": {"x": 90, "y": 270}}
AXIS_ROT = {"y": {}, "z": {"x": 90}, "x": {"x": 90, "y": 90}}


class ImgTex(Tex):
    """Tex built from an in-memory (oriented) image, so Tex.band works in the orientation seen in game."""

    def __init__(self, image):
        self.image = image.convert("RGB")
        px = self.image.load()
        self.grid = [[px[x, y] for x in range(16)] for y in range(16)]
        self.pal = palette([c for row in self.grid for c in row])


def mean_lab(pal): return tuple(sum(w * c[i] for w, c in pal) for i in range(3))


def drip_score(img, edge):
    """Positive when the colour class touching `edge` reaches further into the texture in a few columns."""
    g = [[lab(img.getpixel((x, y))) for x in range(16)] for y in range(16)]
    flat = [c for row in g for c in row]
    a, b = min(flat), max(flat)                       # 2-means seeded with darkest / lightest
    for _ in range(8):
        ca = [c for c in flat if math.dist(c, a) <= math.dist(c, b)]
        cb = [c for c in flat if math.dist(c, a) > math.dist(c, b)]
        if not ca or not cb:
            return 0.0
        a, b = tuple(sum(v) / len(ca) for v in zip(*ca)), tuple(sum(v) / len(cb) for v in zip(*cb))
    cls = [[math.dist(c, a) <= math.dist(c, b) for c in row] for row in g]
    rows = range(16) if edge == "top" else range(15, -1, -1)
    first = next(iter(rows))
    edge_cls = sum(cls[first]) >= 8
    runs = []
    for x in range(16):
        n = 0
        for y in rows:
            if cls[y][x] != edge_cls:
                break
            n += 1
        runs.append(n)
    return statistics.mean(runs) - statistics.median(runs)


def choose_transform(side_img, current):
    if current in ("none", "vflip"):
        options = ("none", "vflip")
    else:
        options = ("rot90", "rot270")
    scores = {}
    for tf in options:
        o = side_img.transpose(ORIENT[tf]) if ORIENT[tf] else side_img
        scores[tf] = drip_score(o, "top") - drip_score(o, "bottom")
    best = max(scores, key=scores.get)
    other = next(t for t in options if t != best)
    return (best if scores[best] - scores[other] > 0.75 else current), {k: round(v, 2) for k, v in scores.items()}


# ---- candidate library ----
java = (P / "src/main/java/pryuan05/pysift/block/ModBlocks.java").read_text(encoding="utf-8")
composite = [b for b in re.findall(r'^\s+(?:facing|pillar)\("([a-z0-9_]+)"', java, re.M) if b not in RULES["skip_blocks"]]
banned = set(RULES["exclude_sources"]) | set(composite)
side_like = set()
for mf in (A / "models/block").rglob("*.json"):
    t = lj(mf).get("textures", {})
    if "side" in t:
        side_like.add(t["side"])
prop = OUT / "directional_proposal.json"
if prop.exists():
    side_like |= {c["texture"] for c in lj(prop)}
library = {}
for bs in sorted((A / "blockstates").glob("*.json")):
    if bs.stem in banned:
        continue
    for v in lj(bs)["variants"].values():
        for e in entries(v):
            m = lj(res_path(ASSETS, e["model"], "models", ".json"))
            if m.get("parent", "").endswith("cube_all"):
                r = m["textures"]["all"]
                if r not in side_like and r not in library:
                    library[r] = Tex(r, ASSETS)
lib_mean = {r: mean_lab(t.pal) for r, t in library.items()}
extra_lib = {}
for bid_, sources in RULES.get("allow_sources", {}).items():
    for src in sources:
        for v in lj(A / "blockstates" / f"{src}.json")["variants"].values():
            for e in entries(v):
                m = lj(res_path(ASSETS, e["model"], "models", ".json"))
                r = m.get("textures", {}).get("all")
                if r and r not in side_like:
                    library.setdefault(r, Tex(r, ASSETS))
                    lib_mean[r] = mean_lab(library[r].pal)
                    extra_lib.setdefault(bid_, set()).add(r)
global_lib = [r for r in library if not any(r in s for s in extra_lib.values())]


def face_score(target_pal, ref):
    """Worse of mean-colour difference and palette-composition distance: both the overall colour and the
    individual colours (e.g. no green moss on a red band) have to match."""
    return max(math.dist(mean_lab(target_pal), lib_mean[ref]), pdist(target_pal, library[ref].pal))


def pick(target_pal, bid):
    pool = global_lib + sorted(extra_lib.get(bid, ()))
    scores = {r: face_score(target_pal, r) for r in pool}
    ranked = sorted(pool, key=scores.get)
    ok = [r for r in ranked if scores[r] <= RULES["max_band_delta"]]
    chosen = []
    for r in ok:
        if all(pdist(library[r].pal, library[c].pal) <= RULES["max_pool_spread"] for c in chosen):
            chosen.append(r)
        if len(chosen) == RULES["max_variants"]:
            break
    fallback = not chosen
    if fallback:
        chosen = ranked[:1]
    return chosen, [round(scores[r], 1) for r in chosen], fallback


# ---- refit ----
report = []
for bid in composite:
    var = lj(A / "blockstates" / f"{bid}.json")["variants"]
    key = next(k for k in var if k in ("facing=up", "axis=y"))
    models = [e["model"] for e in entries(var[key])]
    mjs = [lj(res_path(ASSETS, m, "models", ".json")) for m in models]
    parents = {mj["parent"] for mj in mjs}
    sides = list(dict.fromkeys(mj["textures"]["side"] for mj in mjs))
    is_pillar = parents <= set(PILLAR)
    if not is_pillar and not parents <= set(GRASS):
        report.append({"block": bid, "skipped": f"unexpected parents {sorted(parents)}"})
        continue
    entry = {"block": bid, "kind": "pillar" if is_pillar else "grass", "sides": sides}
    new_models = []
    if is_pillar:
        parent = next(iter(parents))
        side_img = Tex(sides[0], ASSETS).image
        o = side_img.transpose(PILLAR[parent]) if PILLAR[parent] else side_img
        ends, d, fb = pick(ImgTex(o).pal, bid)
        entry.update({"parent": parent, "end": ends, "end_delta": d, "fallback": fb})
        for side in sides:
            for end in ends:
                new_models.append({"parent": parent, "textures": {"end": end, "side": side}})
    else:
        side_tf = {mj["textures"]["side"]: GRASS[mj["parent"]] for mj in mjs}
        first = sides[0]
        _, scores = choose_transform(Tex(first, ASSETS).image, side_tf[first])   # reported only
        new_tf = RULES.get("orientation", {}).get(bid, side_tf[first])
        changed = new_tf != side_tf[first]
        if changed:  # flip the choice for every side texture the same way
            swap = {"none": "vflip", "vflip": "none", "rot90": "rot270", "rot270": "rot90"}
            side_tf = {s: swap[t] for s, t in side_tf.items()}
        o = ImgTex(Tex(first, ASSETS).image.transpose(ORIENT[side_tf[first]]) if ORIENT[side_tf[first]] else Tex(first, ASSETS).image)
        gen = RULES.get("generated_faces", {}).get(bid, {})

        def face_pick(edge):
            band = o.band(edge)["band_pal"]
            if edge in gen:  # dedicated texture made by generate_faces.py
                t = Tex(gen[edge], ASSETS)
                score = max(math.dist(mean_lab(band), mean_lab(t.pal)), pdist(band, t.pal))
                return [gen[edge]], [round(score, 1)], False
            return pick(band, bid)
        tops, td, tfb = face_pick("top")
        bots, bd, bfb = face_pick("bottom")
        entry.update({"transform_before": GRASS[mjs[0]["parent"]], "transform": side_tf[first], "orientation_changed": changed,
                      "drip_scores": scores, "top": tops, "top_delta": td, "bottom": bots, "bottom_delta": bd,
                      "fallback": tfb or bfb})
        for side in sides:
            for top in tops:
                for bot in bots:
                    new_models.append({"parent": PARENT[side_tf[side]], "textures": {"top": top, "bottom": bot, "side": side}})
    entry["variants"] = len(new_models)
    report.append(entry)
    if DRY:
        continue
    folder = A / "models/block" / bid
    for f in folder.glob("*.json"):
        f.unlink()
    refs = []
    for i, m in enumerate(new_models, 1):
        wj(folder / f"{bid}_{i}.json", m)
        refs.append(f"pysift:block/{bid}/{bid}_{i}")
    pool = lambda rot: [{"model": r, "weight": 1, **rot} for r in refs]
    variants = ({f"axis={a}": pool(rot) for a, rot in AXIS_ROT.items()} if is_pillar
                else {f"facing={f}": pool(rot) for f, rot in FACING_ROT.items()})
    wj(A / "blockstates" / f"{bid}.json", {"variants": variants})
    wj(A / "models/item" / f"{bid}.json", {"parent": refs[0]})

OUT.mkdir(parents=True, exist_ok=True)
wj(OUT / "refit_faces_report.json", report)

# ---- review sheet: side as seen in game, chosen top / bottom (or end) ----
tile, PAD = 64, 4
img = Image.new("RGB", (300 + 8 * (tile + PAD) + 60, 24 + len(report) * (tile + 22)), (28, 28, 32))
dr = ImageDraw.Draw(img)
dr.text((4, 4), "block | side as seen in game | TOP (or END) | BOTTOM   (* orientation changed, ! fallback)", fill=(235, 235, 235))
y = 22
for r in report:
    if "skipped" in r:
        continue
    mark = ("*" if r.get("orientation_changed") else "") + ("!" if r.get("fallback") else "")
    dr.text((4, y + 18), f"{mark}{r['block']}\n({r.get('transform', 'pillar')})", fill=(250, 210, 90))
    x = 300
    for s in r["sides"]:
        im = Tex(s, ASSETS).image
        tf = r.get("transform")
        if tf and ORIENT[tf]:
            im = im.transpose(ORIENT[tf])
        elif r["kind"] == "pillar" and PILLAR[r["parent"]]:
            im = im.transpose(PILLAR[r["parent"]])
        img.paste(im.resize((tile, tile), Image.Resampling.NEAREST), (x, y))
        x += tile + PAD
    x += 16
    groups = [("E", r["end"], r["end_delta"])] if r["kind"] == "pillar" else [("T", r["top"], r["top_delta"]), ("B", r["bottom"], r["bottom_delta"])]
    for lab_, refs, ds in groups:
        for ref, d in zip(refs, ds):
            img.paste(Tex(ref, ASSETS).image.resize((tile, tile), Image.Resampling.NEAREST), (x, y))
            dr.text((x + 2, y + tile + 1), f"{lab_} {ref.rsplit('/', 1)[1][-11:]} {d}", fill=(210, 210, 210))
            x += tile + PAD
        x += 16
    y += tile + 22
img.save(OUT / "refit_review.png")
for r in report:
    if "skipped" in r:
        print(f"{r['block']}: SKIPPED {r['skipped']}")
    elif r["kind"] == "pillar":
        print(f"{r['block']:34s} pillar end={[e.rsplit('/', 1)[1] for e in r['end']]} Δ{r['end_delta']}{' FALLBACK' if r['fallback'] else ''}")
    else:
        print(f"{r['block']:34s} {r['transform_before']}->{r['transform']}{' CHANGED' if r['orientation_changed'] else ''} "
              f"top={[t.rsplit('/', 1)[1] for t in r['top']]}Δ{r['top_delta']} bottom={[t.rsplit('/', 1)[1] for t in r['bottom']]}Δ{r['bottom_delta']}"
              f"{' FALLBACK' if r['fallback'] else ''}")
