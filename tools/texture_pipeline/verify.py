"""Verify pysift block resources against ModBlocks.java.
Usage: python -I tools/texture_pipeline/verify.py <project> [--json]
Exit code 1 when an error-level check fails (missing models/textures, state gaps, manifest mismatch, ...)."""
import sys, re, itertools, collections, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import (project_paths, lj, entries, res_path, sha1, pixel_sha1, Tex, pdist, COHERENCE_TH)

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
HERE = Path(__file__).resolve().parent
java = (P / "src/main/java/pryuan05/pysift/block/ModBlocks.java").read_text(encoding="utf-8")
out = collections.OrderedDict()
errors = []

# ---- 1. Java definition table vs blockstates ----
defs = re.findall(r'^\s+(block|pillar|facing)\("([a-z0-9_]+)", Mat\.(\w+)\)((?:\.\w+\([^)]*\))*)', java, re.M)
ids = [d[1] for d in defs]
enum_vals = {}
_props_src = (P / "src/main/java/pryuan05/pysift/block/SiftStateProperties.java").read_text(encoding="utf-8")
for name, body in re.findall(r'public enum (\w+) implements StringRepresentable \{(.*?)private final String name;', _props_src, re.S):
    enum_vals[name] = re.findall(r'\w+\("(\w+)"\)', body)
out["registered_blocks"] = len(ids)
out["duplicate_ids"] = [i for i, n in collections.Counter(ids).items() if n > 1]
bs_ids = sorted(p.stem for p in (A / "blockstates").glob("*.json"))
out["blockstate_vs_java_diff"] = sorted(set(bs_ids) ^ set(ids))

prop_mismatch, uncovered, missing_models, missing_tex = [], [], [], []
used_models, used_tex = set(), set()
for kind, bid, mat, chain in defs:
    jp = {}
    for m in re.finditer(r'\.intProp\("(\w+)", (\d+), (\d+)\)', chain):
        jp[m[1]] = [str(i) for i in range(int(m[2]), int(m[3]) + 1)]
    for m in re.finditer(r'\.enumProp\("(\w+)", SiftStateProperties\.(\w+)\.class\)', chain):
        jp[m[1]] = enum_vals[m[2]]
    for m in re.finditer(r'\.tones\(([^)]*)\)', chain):
        jp["tone"] = re.findall(r'"(\w+)"', m[1])
    if kind == "pillar":
        jp["axis"] = ["x", "y", "z"]
    if kind == "facing":
        jp["facing"] = ["down", "up", "north", "south", "west", "east"]
    var = lj(A / "blockstates" / f"{bid}.json")["variants"]
    keys = {tuple(sorted(tuple(x.split("=")) for x in k.split(",") if x)) for k in var}
    bp = collections.defaultdict(set)
    for k in keys:
        for a, b in k:
            bp[a].add(b)
    if {k: set(v) for k, v in jp.items()} != dict(bp):
        prop_mismatch.append((bid, {k: v for k, v in jp.items()}, {k: sorted(v) for k, v in bp.items()}))
    names = sorted(jp)
    for combo in itertools.product(*[jp[n] for n in names]):
        if tuple(sorted(zip(names, combo))) not in keys:
            uncovered.append((bid, dict(zip(names, combo))))
    for v in var.values():
        for e in entries(v):
            mf = res_path(ASSETS, e["model"], "models", ".json")
            if not mf.exists():
                missing_models.append((bid, e["model"]))
                continue
            used_models.add(mf)
            for t in lj(mf).get("textures", {}).values():
                if t.startswith("minecraft:"):
                    continue
                tf = res_path(ASSETS, t, "textures", ".png")
                (used_tex.add(tf) if tf.exists() else missing_tex.append((bid, t)))
out["java_vs_blockstate_property_mismatch"] = prop_mismatch
out["uncovered_states"] = uncovered
out["missing_models"] = missing_models
out["missing_textures"] = missing_tex
errors += [k for k in ("duplicate_ids", "blockstate_vs_java_diff", "java_vs_blockstate_property_mismatch",
                       "uncovered_states", "missing_models", "missing_textures") if out[k]]

# ---- 2. templates and orphans ----
templates = set((A / "models/block/templates").glob("*.json"))
bad_templates = []
for t in templates:
    faces = lj(t)["elements"][0]["faces"]
    if set(faces) != {"down", "up", "north", "south", "west", "east"} or any("uv" not in f or "texture" not in f for f in faces.values()):
        bad_templates.append(t.name)
out["bad_templates"] = bad_templates
item_parents = {res_path(ASSETS, lj(A / "models/item" / f"{b}.json")["parent"], "models", ".json") for b in ids
                if (A / "models/item" / f"{b}.json").exists()}
all_models = set((A / "models/block").rglob("*.json"))
out["unused_block_models"] = sorted(p.relative_to(A).as_posix() for p in all_models - used_models - item_parents - templates)
all_png = set((A / "textures/block").rglob("*.png"))
out["unused_block_png"] = sorted(p.relative_to(A).as_posix() for p in all_png - used_tex)
errors += [k for k in ("bad_templates",) if out[k]]

# ---- 3. PNG provenance: original / recolor pipeline / external edit ----
base = lj(HERE / "texture_baseline.json")
src_sha, atlas_pix = set(base["source_file_sha1"]), set(base["atlas_pixel_sha1"])
manifest_path = HERE / "recolor_manifest.json"
manifest = lj(manifest_path)["entries"] if manifest_path.exists() else []
by_file = {e["file"]: e for e in manifest}
pipeline_ok, manifest_mismatch, external = [], [], []
for p in sorted(all_png):
    rel = p.relative_to(A).as_posix()
    h = sha1(p)
    if rel in by_file:
        (pipeline_ok.append(rel) if by_file[rel]["sha1_after"] == h else manifest_mismatch.append(rel))
    elif h not in src_sha and pixel_sha1(p) not in atlas_pix:
        external.append(rel)
out["png_recolored_by_pipeline"] = len(pipeline_ok)
out["png_manifest_mismatch"] = manifest_mismatch
out["png_edited_outside_pipeline"] = external
errors += [k for k in ("png_manifest_mismatch",) if out[k]]

# ---- 4. random-pool coherence ----
_tex = {}
incoherent = []
for kind, bid, mat, chain in defs:
    for key, v in lj(A / "blockstates" / f"{bid}.json")["variants"].items():
        if not isinstance(v, list) or len(v) < 2 or ("facing=" in key and "facing=up" not in key) or ("axis=" in key and "axis=y" not in key):
            continue
        texs = []
        for e in v:
            mt = lj(res_path(ASSETS, e["model"], "models", ".json"))
            if mt.get("parent", "").endswith("cube_all"):
                r = mt["textures"]["all"]
                texs.append(_tex.setdefault(r, Tex(r, ASSETS)))
        if len(texs) > 1:
            worst = max(pdist(a.pal, b.pal) for a in texs for b in texs)
            if worst > COHERENCE_TH:
                incoherent.append((bid, key, round(worst, 1)))
out["incoherent_random_pools"] = incoherent

# ---- 5. companion files ----
lang = {l: lj(A / "lang" / f"{l}.json") for l in ("en_us", "zh_tw")}
tags = {t.stem: set(lj(t)["values"]) for t in (D / "minecraft/tags/block/mineable").glob("*.json")}
gaps = collections.defaultdict(list)
for bid in ids:
    for rel, label in ((A / "items" / f"{bid}.json", "items"), (A / "models/item" / f"{bid}.json", "models_item"),
                       (D / "pysift/loot_table/blocks" / f"{bid}.json", "loot_table"),
                       (D / "pysift/loot_tables/blocks" / f"{bid}.json", "loot_tables")):
        if not rel.exists():
            gaps[label].append(bid)
    n = sum(f"pysift:{bid}" in v for v in tags.values())
    if n != 1:
        gaps["mineable_tag_count!=1"].append((bid, n))
    for l, d in lang.items():
        if f"block.pysift.{bid}" not in d:
            gaps[f"lang_{l}"].append(bid)
out["companion_gaps"] = dict(gaps)
out["mineable_counts"] = {k: sum(1 for v in vs if v.split(":", 1)[1] in ids) for k, vs in tags.items()}
bad_item_refs = []


def walk(o, bid):
    if isinstance(o, dict):
        if o.get("type") == "minecraft:model" and not res_path(ASSETS, o["model"], "models", ".json").exists():
            bad_item_refs.append((bid, o["model"]))
        for v in o.values():
            walk(v, bid)
    elif isinstance(o, list):
        for v in o:
            walk(v, bid)


for bid in ids:
    if (A / "items" / f"{bid}.json").exists():
        walk(lj(A / "items" / f"{bid}.json"), bid)
out["item_definition_missing_models"] = bad_item_refs
out["files_with_sift_or_custom_namespace"] = sorted(p.relative_to(RES).as_posix() for p in RES.rglob("*.json")
                                                    if re.search(r'"(sift|custom):', p.read_text(encoding="utf-8-sig")))
errors += [k for k in ("companion_gaps", "item_definition_missing_models", "files_with_sift_or_custom_namespace") if out[k]]
out["errors"] = errors

if "--json" in sys.argv:
    print(json.dumps(out, ensure_ascii=False, indent=1))
else:
    for k, v in out.items():
        shown = v if not isinstance(v, (list, dict)) or len(v) <= 12 else f"{len(v)} items: {list(v)[:12]} ..."
        print(f"{k}: {shown}")
sys.exit(1 if errors else 0)
