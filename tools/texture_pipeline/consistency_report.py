"""Read-only colour-consistency report covering every face and every stage.
Usage: python -I tools/texture_pipeline/consistency_report.py <project> [--threshold N] [--stage-threshold M]
  A. face pools: for every variant pool, the textures used on each face (top / bottom / side / end / all)
     must stay within N (default 5) of each other.
  B. stage steps: for progressive blocks (integer properties), the colour jump between neighbouring stages
     (medoid to medoid, other properties fixed) is reported; jumps above M (default 12) are flagged.
Writes build/texture_pipeline/out/consistency_report.json and consistency_review.png."""
import sys, re, json
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import project_paths, lj, wj, entries, res_path, Tex, pdist, iter_pools

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
arg = lambda name, default: float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default
FACE_TH, STAGE_TH = arg("--threshold", 5.0), arg("--stage-threshold", 12.0)
OUT = P / "build/texture_pipeline/out"
FACE_OF = {"all": "all", "top": "top", "bottom": "bottom", "side": "side", "end": "end"}
cache = {}
tex = lambda r: cache.setdefault(r, Tex(r, ASSETS))


def faces_of(model_ref):
    t = lj(res_path(ASSETS, model_ref, "models", ".json")).get("textures", {})
    return {FACE_OF[k]: v for k, v in t.items() if k in FACE_OF and not v.startswith("minecraft:")}


def spread(refs):
    ts = [tex(r) for r in refs]
    return max((pdist(a.pal, b.pal) for i, a in enumerate(ts) for b in ts[i + 1:]), default=0.0)


def medoid(refs):
    ts = [tex(r) for r in refs]
    return min(ts, key=lambda t: sum(pdist(t.pal, o.pal) for o in ts if o is not t))


# ---- A. per-face pools ----
face_issues = []
for block, state, models in iter_pools(A):
    per_face = {}
    for m in models:
        for f, r in faces_of(m).items():
            per_face.setdefault(f, [])
            if r not in per_face[f]:
                per_face[f].append(r)
    for f, refs in per_face.items():
        if len(refs) < 2:
            continue
        s = spread(refs)
        if s > FACE_TH:
            med = medoid(refs)
            outliers = sorted(((round(pdist(tex(r).pal, med.pal), 1), r) for r in refs if r != med.ref), reverse=True)
            face_issues.append({"block": block, "state": state, "face": f, "max_dist": round(s, 1),
                                "medoid": med.ref, "textures": refs, "farthest": outliers[:3]})

# ---- B. stage steps of progressive blocks ----
java = (P / "src/main/java/pryuan05/pysift/block/ModBlocks.java").read_text(encoding="utf-8")
int_props = {}
for bid, chain in re.findall(r'^\s+(?:block|pillar|facing)\("([a-z0-9_]+)", Mat\.\w+\)((?:\.\w+\([^)]*\))*)', java, re.M):
    for name, lo, hi in re.findall(r'\.intProp\("(\w+)", (\d+), (\d+)\)', chain):
        int_props.setdefault(bid, []).append((name, int(lo), int(hi)))
stage_rows = []
for bid, props in int_props.items():
    var = lj(A / "blockstates" / f"{bid}.json")["variants"]
    parsed = [(dict(kv.split("=") for kv in k.split(",") if kv), [e["model"] for e in entries(v)]) for k, v in var.items()]
    parsed = [(d, ms) for d, ms in parsed if d.get("facing", "up") == "up" and d.get("axis", "y") == "y"]
    for name, lo, hi in props:
        groups = {}
        for d, ms in parsed:
            fixed = tuple(sorted((k, v) for k, v in d.items() if k not in (name, "facing", "axis")))
            groups.setdefault(fixed, {})[int(d[name])] = ms
        for fixed, stages in groups.items():
            meds = {}
            for i in range(lo, hi + 1):
                refs = [r for m in stages.get(i, []) for f, r in faces_of(m).items() if f in ("all", "side")]
                if refs:
                    meds[i] = medoid(list(dict.fromkeys(refs)))
            steps = [(i, round(pdist(meds[i].pal, meds[i + 1].pal), 1)) for i in range(lo, hi) if i in meds and i + 1 in meds]
            stage_rows.append({"block": bid, "property": name, "fixed": dict(fixed), "steps": steps,
                               "medoids": {i: t.ref for i, t in meds.items()},
                               "flagged": [s for s in steps if s[1] > STAGE_TH]})

OUT.mkdir(parents=True, exist_ok=True)
flagged_stages = [r for r in stage_rows if r["flagged"]]
wj(OUT / "consistency_report.json", {"face_threshold": FACE_TH, "stage_threshold": STAGE_TH,
                                      "face_issues": face_issues, "stage_steps": stage_rows})

# ---- review sheet ----
S, PAD = 5, 5
tile = 16 * S
rows = [(f"{i['block']}[{i['state'] or '-'}] {i['face']} max {i['max_dist']}", [tex(r) for r in i["textures"]], i["medoid"])
        for i in face_issues]
rows += [(f"{r['block']} {r['property']} steps {r['steps']}", [tex(t) for t in r["medoids"].values()], None)
         for r in flagged_stages]
width = 20 + max([len(t) for _, t, _ in rows] + [1]) * (tile + PAD) + 20
img = Image.new("RGB", (max(width, 900), 30 + len(rows) * (tile + 30)), (28, 28, 32))
dr = ImageDraw.Draw(img)
dr.text((PAD, 4), f"A. face pools > {FACE_TH} (green = medoid)   B. stage steps > {STAGE_TH} (one medoid per stage)", fill=(235, 235, 235))
y = 24
for title, ts, med in rows:
    dr.text((PAD, y), title[:150], fill=(250, 210, 90))
    x = 20
    for t in ts:
        img.paste(t.image.resize((tile, tile), Image.Resampling.NEAREST), (x, y + 14))
        if med and t.ref == med:
            dr.rectangle([x, y + 14, x + tile - 1, y + 13 + tile], outline=(90, 220, 120), width=3)
        x += tile + PAD
    y += tile + 30
img.save(OUT / "consistency_review.png")

print(f"A. face pools with spread > {FACE_TH}: {len(face_issues)}")
for i in face_issues:
    print(f"  {i['block']}[{i['state'] or '-'}] {i['face']:6s} max {i['max_dist']:5.1f}  farthest: " +
          ", ".join(f"{r.rsplit('/', 1)[1]}({d})" for d, r in i["farthest"]))
print(f"B. stage steps (flag > {STAGE_TH}):")
for r in sorted(stage_rows, key=lambda r: -max([s[1] for s in r["steps"]] + [0])):
    if r["steps"]:
        mark = " <<" if r["flagged"] else ""
        print(f"  {r['block']} {r['property']} {r['fixed'] or ''} steps {r['steps']}{mark}")
