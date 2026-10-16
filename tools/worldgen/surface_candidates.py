"""Read-only: rank cleaner block states for each The Sift surface role.
Usage: python -I tools/worldgen/surface_candidates.py <project>
For every role, candidates are block states whose top-face colours are close to the current choice; they are ranked
by texture noise (mean CIELAB difference between neighbouring pixels, averaged over the state's random pool).
Writes build/texture_pipeline/out/surface_candidates.json and surface_review.png."""
import sys, json, math, itertools
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "texture_pipeline"))
from palette_lib import project_paths, lj, entries, res_path, lab, palette, pdist

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
OUT = P / "build/texture_pipeline/out"
COLOR_TH = 10.0     # max palette distance to the current choice for a state to count as a candidate
TOP_N = 8

# role -> (current block, current properties, candidate block families). Candidates are every state of those blocks.
CRIMSON = ["crimson_strata", "crimson_vein_stone", "ember_stone", "veined_crimson_stone", "bleached_clay",
           "banded_mudstone", "crimson_capped_crimson_strata", "crimson_capped_crimson_strata_2", "rose_capped_crimson_strata",
           "capped_crimson_strata", "stone_capped_rose_01", "rose_capped_stone_01", "crimson_capped_void_01",
           "ash_capped_crimson_01"]
VIOLET = ["violet_strata", "violet_marble", "violet_solid_block", "corrupted_slate", "violet_capped_dark_slate",
          "violet_capped_crimson_strata", "crimson_capped_violet_strata", "crimson_capped_violet_strata_2",
          "ash_capped_violet_01", "magma_vein_slate", "stone_capped_violet_01"]
PINK = ["crimson_strata", "rose_capped_stone_01", "stone_capped_rose_01", "rose_capped_dark_slate_01",
        "rose_capped_crimson_strata", "capped_crimson_strata", "dark_slate_capped_rose_01", "bleached_clay",
        "banded_mudstone", "crimson_vein_stone", "ember_stone", "cracked_sandstone"]
SAND = ["pale_sand", "amber_sand", "bleached_sandstone", "cracked_sandstone", "banded_mudstone", "silted_strata"]
ROLES = {
    "crimson_top": ("crimson_capped_crimson_strata_3", {}, CRIMSON + ["crimson_capped_crimson_strata_3"]),
    "violet_top": ("ash_capped_violet_01", {}, VIOLET),
    "violet_under": ("violet_strata", {}, VIOLET),
    "grove_top": ("sift_pink_loam", {}, PINK),
    "dunes_top": ("pale_sand", {}, SAND),
    "base_stone": ("void_stone", {"tone": "dark"}, ["dark_slate", "varied_dark_slate", "void_stone", "circle_slate", "framed_slate"]),
}
TOP_KEYS = ("top", "end", "all", "up")
_tex_cache = {}


def tex_info(ref):
    if ref not in _tex_cache:
        im = Image.open(res_path(ASSETS, ref, "textures", ".png")).convert("RGB")
        px = im.load()
        w, h = im.size
        L = [[lab(px[x, y]) for x in range(w)] for y in range(h)]
        diffs = [math.dist(L[y][x], L[y][x + 1]) for y in range(h) for x in range(w - 1)] + \
                [math.dist(L[y][x], L[y + 1][x]) for y in range(h - 1) for x in range(w)]
        _tex_cache[ref] = {"img": im, "noise": sum(diffs) / len(diffs), "pal": palette(list(im.getdata())),
                           "colors": len(set(im.getdata()))}
    return _tex_cache[ref]


def top_textures(model_ref):
    m = lj(res_path(ASSETS, model_ref, "models", ".json"))
    t = m.get("textures", {})
    for k in TOP_KEYS:
        if k in t and t[k].startswith("pysift:"):
            return [t[k]]
    return [v for v in t.values() if v.startswith("pysift:")][:1]


# every block state (orientation fixed to up / y) -> its top-face texture pool
states = []
for bs in sorted((A / "blockstates").glob("*.json")):
    j = lj(bs)
    if "variants" not in j:
        continue
    for key, v in j["variants"].items():
        props = dict(x.split("=", 1) for x in key.split(",") if x)
        if props.get("facing", "up") != "up" or props.get("axis", "y") != "y" or "half" in props or "type" in props:
            continue
        texs = [t for e in entries(v) for t in top_textures(e["model"])]
        if not texs:
            continue
        props = {k: v for k, v in props.items() if k not in ("facing", "axis")}
        infos = [tex_info(t) for t in dict.fromkeys(texs)]
        pal = [(w / len(infos), c) for i in infos for w, c in i["pal"]]
        states.append({"block": bs.stem, "props": props, "textures": list(dict.fromkeys(texs)), "pal": pal,
                       "noise": sum(i["noise"] for i in infos) / len(infos),
                       "spread": max((pdist(a["pal"], b["pal"]) for a, b in itertools.combinations(infos, 2)), default=0.0)})

result = {}
find = lambda block, props: next(s for s in states if s["block"] == block and all(s["props"].get(k) == v for k, v in props.items()))
for role, (block, props, family) in ROLES.items():
    cur = find(block, props)
    target = cur
    cands = [s for s in states if s["block"] in family]
    cur.setdefault("score", round(cur["noise"] + 0.5 * cur["spread"], 1))
    # cleanliness = texture noise + penalty for a random pool whose variants differ in colour
    for s in cands:
        s["score"] = round(s["noise"] + 0.5 * s["spread"], 1)
    cands.sort(key=lambda s: s["score"])
    top = cands[:TOP_N]
    if cur not in top:
        top.append(cur)
    result[role] = {"current": {"block": cur["block"], "props": cur["props"], "score": cur["score"]},
                    "candidates": [{"block": s["block"], "props": s["props"], "score": s["score"],
                                    "color_dist": round(pdist(s["pal"], target["pal"]), 1), "textures": s["textures"]}
                                   for s in top]}

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "surface_candidates.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

S, PAD = 5, 8
tile = 16 * S
cols = TOP_N + 1
sheet = Image.new("RGB", (170 + cols * (tile + PAD), 24 + len(result) * (tile + 40)), (28, 28, 32))
dr = ImageDraw.Draw(sheet)
dr.text((6, 4), "role | candidates, cleanest first (score = noise; lower is cleaner)   [cur] = current choice   * = suggested",
        fill=(235, 235, 235))
y = 24
for role, r in result.items():
    dr.text((6, y + tile // 2 - 6), role, fill=(250, 210, 90))
    x = 170
    for i, c in enumerate(r["candidates"]):
        img = _tex_cache[c["textures"][0]]["img"].resize((tile, tile), Image.Resampling.NEAREST)
        sheet.paste(img, (x, y))
        is_cur = c["block"] == r["current"]["block"] and c["props"] == r["current"]["props"]
        if is_cur:
            dr.rectangle([x - 2, y - 2, x + tile + 1, y + tile + 1], outline=(120, 200, 255), width=2)
        label = c["block"][:18] + ("".join(f" {v}" for v in c["props"].values()))[:12]
        dr.text((x, y + tile + 2), label[:22], fill=(220, 220, 220))
        dr.text((x, y + tile + 14), f"{'* ' if i == 0 else ''}{c['score']}{' [cur]' if is_cur else ''}",
                fill=(140, 230, 150) if i == 0 else (180, 180, 180))
        x += tile + PAD
    y += tile + 40
sheet.save(OUT / "surface_review.png")
for role, r in result.items():
    best = r["candidates"][0]
    print(f"{role:17s} current {r['current']['block']}{r['current']['props']} {r['current']['score']:5.1f}  ->  "
          f"best {best['block']}{best['props']} {best['score']:5.1f}")
