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
# building sets (registered in a loop from ModBlocks.BUILDING_SETS; vanilla slab / stairs / wall blockstates)
_sets = re.search(r'BUILDING_SETS = List\.of\((.*?)\);', java, re.S)
set_ids = []
for base in (re.findall(r'"([a-z0-9_]+)"', _sets[1]) if _sets else []):
    for n in (f"{base}_bricks", f"chiseled_{base}_bricks", f"{base}_slab", f"{base}_stairs", f"{base}_wall",
              f"{base}_brick_slab", f"{base}_brick_stairs", f"{base}_brick_wall"):
        if n not in ids:
            set_ids.append(n)
# vegetation and fluid blocks live in their own classes (resources from tools/worldgen/build_vegetation.py)
_blk = P / "src/main/java/pryuan05/pysift"
veg_ids = re.findall(r'register\("([a-z0-9_]+)"', (_blk / "block/ModVegetation.java").read_text(encoding="utf-8")) \
    if (_blk / "block/ModVegetation.java").exists() else []
veg_ids += re.findall(r'registerBlock\("([a-z0-9_]+)"', (_blk / "fluid/ModFluids.java").read_text(encoding="utf-8")) \
    if (_blk / "fluid/ModFluids.java").exists() else []
# soul willow wood set (SoulWillowWood.java, resources from tools/worldgen/build_soul_willow_wood.py): vanilla-style
# blockstates; mineable through vanilla tags (#planks, #logs, #wooden_doors ... are all in vanilla #mineable/axe)
wood_ids = re.findall(r'(?:block|blockOnly)\("([a-z0-9_]+)"', (_blk / "block/SoulWillowWood.java").read_text(encoding="utf-8"))     if (_blk / "block/SoulWillowWood.java").exists() else []
wall_variants = {w for w in wood_ids if "_wall_" in w}   # no item / loot of their own (they drop the standing sign)
veg_ids += wood_ids
# sandstone families (SandstoneFamily.java, resources from tools/worldgen/build_sandstone.py): vanilla-style; the item
# definitions point at the block models (no models/item of their own), mineable through #mineable/pickaxe like vanilla
sandstone_ids = re.findall(r'block\("([a-z0-9_]+)",', (_blk / "block/SandstoneFamily.java").read_text(encoding="utf-8"))     if (_blk / "block/SandstoneFamily.java").exists() else []
veg_ids += sandstone_ids
# other single blocks registered outside ModBlocks.DEFS / ModVegetation (vanilla-style resources)
for _extra in ("block/SoulCrystal.java", "block/ModBlocks.java", "block/RitualBlocks.java", "block/SoulSiftAxle.java"):
    if (_blk / _extra).exists():
        veg_ids += re.findall(r'Registries\.BLOCK, PySift\.id\("([a-z0-9_]+)"\)', (_blk / _extra).read_text(encoding="utf-8"))
# phase 1 progression blocks (progression/ModProgression.java, resources from tools/progression/build_progression.py)
for _prog in sorted((_blk / "progression").glob("*.java")):
    veg_ids += re.findall(r'register(?:Block|Plant)\("([a-z0-9_]+)"', _prog.read_text(encoding="utf-8"))
# the 9 new Sift colours (block/SiftColors.java, resources from tools/progression/build_sift_colors.py): <colour>_<kind>
_colors = _blk / "block/SiftColors.java"
if _colors.exists():
    _src = _colors.read_text(encoding="utf-8")
    veg_ids += [f"{c}_{k}" for c in re.findall(r'[A-Z_]+\("([a-z_]+)", 0x', _src) for k in re.findall(r'block(?:Only)?\(c, "([a-z_]+)"', _src)]
out["vegetation_and_fluid_blocks"] = len(veg_ids)
all_ids = ids + set_ids + veg_ids
enum_vals = {}
_props_src = (P / "src/main/java/pryuan05/pysift/block/SiftStateProperties.java").read_text(encoding="utf-8")
for name, body in re.findall(r'public enum (\w+) implements StringRepresentable \{(.*?)private final String name;', _props_src, re.S):
    enum_vals[name] = re.findall(r'\w+\("(\w+)"\)', body)
out["registered_blocks"] = len(all_ids)
out["building_set_blocks"] = len(set_ids)
out["duplicate_ids"] = [i for i, n in collections.Counter(all_ids).items() if n > 1]
bs_ids = sorted(p.stem for p in (A / "blockstates").glob("*.json"))
out["blockstate_vs_java_diff"] = sorted(set(bs_ids) ^ set(all_ids))

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
            if e["model"].startswith("minecraft:"):   # vanilla models always exist (banners: minecraft:block/banner)
                continue
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
for bid in set_ids + veg_ids:   # vanilla-style blockstates: only check that every model and texture exists
    j = lj(A / "blockstates" / f"{bid}.json")
    pools = [p["apply"] for p in j["multipart"]] if "multipart" in j else list(j["variants"].values())
    for v in pools:
        for e in entries(v):
            if e["model"].startswith("minecraft:"):
                continue
            mf = res_path(ASSETS, e["model"], "models", ".json")
            if not mf.exists():
                missing_models.append((bid, e["model"]))
                continue
            used_models.add(mf)
            for t in lj(mf).get("textures", {}).values():
                t = t.get("sprite", "") if isinstance(t, dict) else t   # 26.3: {"sprite": ..., "force_translucent": true}
                if not t.startswith(("minecraft:", "#")):   # "#x" 是同模型內另一個貼圖變數
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
item_parents = {res_path(ASSETS, lj(A / "models/item" / f"{b}.json")["parent"], "models", ".json") for b in all_ids
                if (A / "models/item" / f"{b}.json").exists()}
all_models = set((A / "models/block").rglob("*.json"))
parent_models = set()   # shared parents such as vegetation/template_big_flower are used through their children
for mf in used_models | item_parents:
    if mf.exists():
        parent = lj(mf).get("parent", "")
        if parent.startswith("pysift:"):
            parent_models.add(res_path(ASSETS, parent, "models", ".json"))
out["unused_block_models"] = sorted(p.relative_to(A).as_posix() for p in all_models - used_models - item_parents - templates - parent_models)
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

# ---- 4b. composite faces (warnings): top/bottom vs the side band seen in game, and per-face pool spread ----
import math
from PIL import Image
from palette_lib import palette as _palette
_rules = lj(HERE / "face_rules.json")
_T = Image.Transpose
_GRASS = {"minecraft:block/cube_bottom_top": None, "pysift:block/templates/cube_bottom_top_vflip": _T.FLIP_TOP_BOTTOM,
          "pysift:block/templates/cube_bottom_top_rot90": _T.ROTATE_270, "pysift:block/templates/cube_bottom_top_rot270": _T.ROTATE_90}


class _ImgTex(Tex):
    def __init__(self, image):
        self.image = image.convert("RGB")
        px = self.image.load()
        self.grid = [[px[x, y] for x in range(16)] for y in range(16)]
        self.pal = _palette([c for row in self.grid for c in row])


def _mean(pal): return tuple(sum(w * c[i] for w, c in pal) for i in range(3))


face_far, face_spread = [], []
for kind, bid, mat, chain in defs:
    if kind not in ("facing", "pillar") or bid in _rules["skip_blocks"]:
        continue
    var = lj(A / "blockstates" / f"{bid}.json")["variants"]
    key = next((k for k in var if k in ("facing=up", "axis=y")), None)
    if key is None:
        continue
    per_face, seen = {}, set()
    for e in entries(var[key]):
        mj = lj(res_path(ASSETS, e["model"], "models", ".json"))
        t = mj.get("textures", {})
        for f in ("top", "bottom", "end"):
            if f in t:
                per_face.setdefault(f, set()).add(t[f])
        if mj.get("parent") in _GRASS:
            side = _tex.setdefault(t["side"], Tex(t["side"], ASSETS))
            o = _ImgTex(side.image.transpose(_GRASS[mj["parent"]]) if _GRASS[mj["parent"]] else side.image)
            for f, edge in (("top", "top"), ("bottom", "bottom")):
                if (t["side"], f, t[f]) in seen:
                    continue
                seen.add((t["side"], f, t[f]))
                ft = _tex.setdefault(t[f], Tex(t[f], ASSETS))
                d = math.dist(_mean(o.band(edge)["band_pal"]), _mean(ft.pal))
                if d > _rules["max_band_delta"]:
                    face_far.append((bid, f, t[f].rsplit("/", 1)[1], round(d, 1)))
    for f, refs in per_face.items():
        ts = [_tex.setdefault(r, Tex(r, ASSETS)) for r in refs]
        s = max((pdist(a.pal, b.pal) for i, a in enumerate(ts) for b in ts[i + 1:]), default=0.0)
        if s > _rules["max_pool_spread"]:
            face_spread.append((bid, f, round(s, 1)))
out["warn_face_far_from_side_band"] = face_far
out["warn_face_pool_spread"] = face_spread

# ---- 4c. stage steps (info): mean-colour jump between neighbouring stages of progressive blocks ----
STAGE_TH = 12.0
stage_jumps = []
for kind, bid, mat, chain in defs:
    for name, lo, hi in re.findall(r'\.intProp\("(\w+)", (\d+), (\d+)\)', chain):
        groups = {}
        for k, v in lj(A / "blockstates" / f"{bid}.json")["variants"].items():
            d = dict(kv.split("=") for kv in k.split(",") if kv)
            if d.get("facing", "up") != "up" or d.get("axis", "y") != "y":
                continue
            fixed = tuple(sorted((a, b) for a, b in d.items() if a not in (name, "facing", "axis")))
            refs = []
            for e in entries(v):
                tt = lj(res_path(ASSETS, e["model"], "models", ".json")).get("textures", {})
                r = tt.get("all") or tt.get("side")
                if r:
                    refs.append(_tex.setdefault(r, Tex(r, ASSETS)))
            if refs:
                groups.setdefault(fixed, {})[int(d[name])] = _mean([(w / len(refs), c) for t in refs for w, c in t.pal])
        for fixed, st in groups.items():
            for i in range(int(lo), int(hi)):
                if i in st and i + 1 in st and math.dist(st[i], st[i + 1]) > STAGE_TH:
                    stage_jumps.append((bid, name, dict(fixed) or None, f"{i}->{i + 1}", round(math.dist(st[i], st[i + 1]), 1)))
out["info_stage_jumps"] = stage_jumps

# ---- 5. companion files ----
lang = {l: lj(A / "lang" / f"{l}.json") for l in ("en_us", "zh_tw")}
tags = {t.stem: set(lj(t)["values"]) for t in (D / "minecraft/tags/block/mineable").glob("*.json")}
gaps = collections.defaultdict(list)
fluid_ids = set(veg_ids) - set(re.findall(r'register\("([a-z0-9_]+)"', (_blk / "block/ModVegetation.java").read_text(encoding="utf-8")))


_replaceable = D / "minecraft/tags/block/replaceable_by_trees.json"
_plants = set(lj(_replaceable)["values"]) if _replaceable.exists() else set()
_saplings = D / "minecraft/tags/block/saplings.json"
_plants |= set(lj(_saplings)["values"]) if _saplings.exists() else set()   # saplings break instantly too


def is_plant(bid):  # vegetation (listed in #replaceable_by_trees) breaks instantly and, like vanilla grass, needs no mineable tag
    return f"pysift:{bid}" in _plants


for bid in all_ids:
    if bid in fluid_ids:   # fluid blocks have no item, item model or loot table (like vanilla water)
        continue
    for rel, label in ((A / "items" / f"{bid}.json", "items"), (A / "models/item" / f"{bid}.json", "models_item"),
                       (D / "pysift/loot_table/blocks" / f"{bid}.json", "loot_table"),
                       (D / "pysift/loot_tables/blocks" / f"{bid}.json", "loot_tables")):
        if not rel.exists() and bid not in wall_variants and not ((bid in wood_ids or bid in sandstone_ids) and label == "models_item"):
            gaps[label].append(bid)
    if bid in wood_ids:
        if not any(f"pysift:{bid}" in lj(t)["values"] for t in (*(D / "minecraft/tags/block").glob("*.json"),
                                                                *(D / "pysift/tags/block").glob("*.json"))):
            gaps["wood_without_block_tag"].append(bid)
        if bid in wall_variants:
            continue
    n = sum(f"pysift:{bid}" in v for v in tags.values())
    if bid in wood_ids:
        pass
    elif n != 1 and not (n == 0 and bid in veg_ids and is_plant(bid)):
        gaps["mineable_tag_count!=1"].append((bid, n))
    for l, d in lang.items():
        if f"block.pysift.{bid}" not in d:
            gaps[f"lang_{l}"].append(bid)
out["companion_gaps"] = dict(gaps)
out["mineable_counts"] = {k: sum(1 for v in vs if v.split(":", 1)[1] in all_ids) for k, vs in tags.items()}
bad_item_refs = []


def walk(o, bid):
    if isinstance(o, dict):
        if (o.get("type") == "minecraft:model" and not o["model"].startswith("minecraft:")   # vanilla models always exist
                and not res_path(ASSETS, o["model"], "models", ".json").exists()):
            bad_item_refs.append((bid, o["model"]))
        for v in o.values():
            walk(v, bid)
    elif isinstance(o, list):
        for v in o:
            walk(v, bid)


for bid in all_ids:
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
