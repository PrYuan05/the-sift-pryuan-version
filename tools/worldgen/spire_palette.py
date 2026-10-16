"""Read-only: candidate body / band blocks for the strata spires of each biome, ranked by texture noise.
Usage: python -I tools/worldgen/spire_palette.py <project>  ->  build/texture_pipeline/out/spire_palette.png (+ .json)"""
import sys, json, math
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "texture_pipeline"))
from palette_lib import project_paths, lj, entries, res_path, lab

P, RES, A, D = project_paths(sys.argv[1])
ASSETS, OUT = RES / "assets", P / "build/texture_pipeline/out"
ROLES = {   # (biome, part): [(block, {props}), ...]
    ("crimson_strata_canyon", "body"): [("ember_stone", {"heat": "0"}), ("crimson_vein_stone", {"crimson_spread": "4"}),
                                        ("crimson_capped_void_01", {}), ("crimson_strata", {"tone": "crimson"})],
    ("crimson_strata_canyon", "band"): [("abyssal_strata", {"depth": "0"}), ("abyssal_strata", {"depth": "1"}),
                                        ("abyssal_strata", {"depth": "2"}), ("teal_deep_block", {"depth": "0"}),
                                        ("teal_deep_block", {"depth": "2"}), ("teal_strata", {"tone": "cyan"}),
                                        ("teal_solid_block", {}), ("veined_teal_stone", {"tone": "teal"})],
    ("violet_slate_abyss", "body"): [("violet_strata", {}),
                                     ("violet_marble", {}), ("violet_solid_block", {})],
    ("violet_slate_abyss", "band"): [("corrupted_slate", {"corruption": "0"}), ("void_stone", {"tone": "dark"}),
                                     ("dark_slate", {"fade": "0"}), ("magma_vein_slate", {"vein": "0"})],
    ("willow_grove", "body"): [("crimson_strata", {"tone": "rose"}), ("banded_mudstone", {"banding": "0"}),
                               ("bleached_clay", {"bleach": "0"})],
    ("willow_grove", "band"): [("sift_pink_loam", {}), ("bleached_clay", {"bleach": "2"}), ("rose_capped_stone_01", {})],
    ("amber_dunes", "body"): [("bleached_sandstone", {"bleach": "0"}), ("cracked_sandstone", {"crack": "0"}),
                              ("amber_sand", {}), ("banded_mudstone", {"banding": "0"})],
    ("amber_dunes", "band"): [("cracked_sandstone", {"crack": "0"}), ("banded_mudstone", {"banding": "0"}),
                              ("bleached_sandstone", {"bleach": "4"}), ("pale_sand", {})],
}


def state_texture(block, props):
    for key, v in lj(A / "blockstates" / f"{block}.json")["variants"].items():
        kv = dict(x.split("=", 1) for x in key.split(",") if x)
        if all(kv.get(k) == val for k, val in props.items()) and kv.get("facing", "up") == "up" and kv.get("axis", "y") == "y":
            t = lj(res_path(ASSETS, entries(v)[0]["model"], "models", ".json"))["textures"]
            return t.get("all") or t.get("side") or t.get("top")
    raise KeyError((block, props))


def noise(ref):
    im = Image.open(res_path(ASSETS, ref, "textures", ".png")).convert("RGB")
    px, (w, h) = im.load(), im.size
    L = [[lab(px[x, y]) for x in range(w)] for y in range(h)]
    d = [math.dist(L[y][x], L[y][x + 1]) for y in range(h) for x in range(w - 1)] + \
        [math.dist(L[y][x], L[y + 1][x]) for y in range(h - 1) for x in range(w)]
    return im, sum(d) / len(d)


S, PAD = 5, 8
tile = 16 * S
rows = []
for (biome, part), cands in ROLES.items():
    scored = []
    for block, props in cands:
        if not (A / "blockstates" / f"{block}.json").exists():
            continue                     # block no longer registered (e.g. merged into another block)
        try:
            ref = state_texture(block, props)
        except KeyError:
            continue
        im, n = noise(ref)
        scored.append({"block": block, "props": props, "score": round(n, 1), "img": im})
    scored.sort(key=lambda c: c["score"])
    rows.append((biome, part, scored))
sheet = Image.new("RGB", (240 + 8 * (tile + PAD), 20 + len(rows) * (tile + 34)), (28, 28, 32))
dr = ImageDraw.Draw(sheet)
dr.text((6, 4), "spire materials per biome: body / band (cleanest first, * = suggested)", fill=(235, 235, 235))
y = 20
for biome, part, scored in rows:
    dr.text((6, y + tile // 2 - 6), f"{biome} / {part}", fill=(250, 210, 90))
    x = 240
    for i, c in enumerate(scored):
        sheet.paste(c["img"].resize((tile, tile), Image.Resampling.NEAREST), (x, y))
        dr.text((x, y + tile + 2), (c["block"][:16] + " " + " ".join(c["props"].values()))[:20], fill=(220, 220, 220))
        dr.text((x, y + tile + 14), f"{'* ' if i == 0 else ''}{c['score']}", fill=(140, 230, 150) if i == 0 else (180, 180, 180))
        x += tile + PAD
    y += tile + 34
OUT.mkdir(parents=True, exist_ok=True)
sheet.save(OUT / "spire_palette.png")
(OUT / "spire_palette.json").write_text(json.dumps({f"{b}/{p}": [{k: v for k, v in c.items() if k != "img"} for c in s]
                                                    for b, p, s in rows}, ensure_ascii=False, indent=1), encoding="utf-8")
for b, p, s in rows:
    print(f"{b:22s} {p:4s} -> " + ", ".join(f"{c['block']}{'[' + ','.join(c['props'].values()) + ']' if c['props'] else ''} {c['score']}" for c in s))
