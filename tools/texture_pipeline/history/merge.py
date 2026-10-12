"""Integrate blockstate_restructure (c) into pysift.
Usage: python -I merge.py <project> <c_root> <out_dir>"""
import json, sys, re, shutil, hashlib, collections, csv
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1]); C = Path(sys.argv[2]); OUT = Path(sys.argv[3])
RES = P / "src/main/resources"; A = RES / "assets/pysift"; D = RES / "data"
JAVA = P / "src/main/java/pryuan05/pysift/block/ModBlocks.java"
NS_C = ["sift", "custom"]


def lj(p): return json.loads(p.read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pixkey(p):
    im = Image.open(p).convert("RGBA")
    return hashlib.sha1(repr(im.size).encode() + im.tobytes()).hexdigest()


def entries(v): return v if isinstance(v, list) else [v]


def model_file(ref, root):
    ns, path = ref.split(":", 1)
    return root / ns / "models" / (path + ".json")


def tex_file(ref, root):
    ns, path = ref.split(":", 1)
    return root / ns / "textures" / (path + ".png")


# ---------- 1. backup ----------
BK = P / "backup_before_merge"
assert not BK.exists(), "backup_before_merge already exists; refusing to overwrite"
for rel in ["assets/pysift/blockstates", "assets/pysift/models/block", "assets/pysift/textures/block",
            "assets/pysift/models/item", "assets/pysift/items", "assets/pysift/lang",
            "data/pysift/loot_table", "data/pysift/loot_tables", "data/minecraft/tags"]:
    shutil.copytree(RES / rel, BK / "src/main/resources" / rel)
(BK / "src/main/java/pryuan05/pysift/block").mkdir(parents=True)
shutil.copy2(JAVA, BK / "src/main/java/pryuan05/pysift/block/ModBlocks.java")

# ---------- 2. old (a) inventory ----------
old_ids = sorted(p.stem for p in (A / "blockstates").glob("*.json"))
assert len(old_ids) == 295, len(old_ids)
old_models, old_tex = set(), set()
old_block_tex = collections.defaultdict(set)
for oid in old_ids:
    for v in lj(A / "blockstates" / f"{oid}.json")["variants"].values():
        for e in entries(v):
            mf = model_file(e["model"], RES / "assets")
            old_models.add(mf)
            for t in lj(mf).get("textures", {}).values():
                if t.startswith("pysift:"):
                    tf = tex_file(t, RES / "assets")
                    old_tex.add(tf)
                    old_block_tex[oid].add(tf)

mat_re = re.compile(r'register(?:Pillar)?\("([a-z0-9_]+)", BlockBehaviour\.Properties\.of\(\)\.destroyTime\(([\d.]+)f\)'
                    r'\.explosionResistance\(([\d.]+)f\)\.sound\(SoundType\.(\w+)\)')
MAT = {("1.5", "6.0", "STONE"): "STONE", ("3.0", "6.0", "DEEPSLATE"): "DEEPSLATE", ("2.0", "3.0", "WOOD"): "WOOD",
       ("0.5", "0.5", "GRAVEL"): "GRAVEL", ("0.5", "0.5", "SAND"): "SAND", ("0.6", "0.6", "GRASS"): "GRASS"}
old_mat = {m[0]: MAT[m[1:]] for m in mat_re.findall(JAVA.read_text(encoding="utf-8"))}
assert len(old_mat) == 295, len(old_mat)
TAGDIR = D / "minecraft/tags/block/mineable"
old_tool = {}
for tf in TAGDIR.glob("*.json"):
    for v in lj(tf)["values"]:
        if v.startswith("pysift:") and v[7:] in old_mat:
            old_tool[v[7:]] = tf.stem
pix_to_old = collections.defaultdict(set)
for oid, tfs in old_block_tex.items():
    for tf in tfs:
        pix_to_old[pixkey(tf)].add(oid)

# ---------- 3. remove old (a) block files ----------
removed = []


def rm(p):
    if p.exists():
        p.unlink()
        removed.append(p)


for oid in old_ids:
    rm(A / "blockstates" / f"{oid}.json")
    rm(A / "models/item" / f"{oid}.json")
    rm(A / "items" / f"{oid}.json")
    rm(D / "pysift/loot_table/blocks" / f"{oid}.json")
    rm(D / "pysift/loot_tables/blocks" / f"{oid}.json")
for p in old_models | old_tex:
    rm(p)


# ---------- 4. import (c) with namespace rewrite ----------
def rewrite(o):
    if isinstance(o, dict):
        return {k: rewrite(v) for k, v in o.items()}
    if isinstance(o, list):
        return [rewrite(v) for v in o]
    if isinstance(o, str):
        for ns in NS_C:
            if o.startswith(ns + ":"):
                return "pysift:" + o[len(ns) + 1:]
    return o


CA = C / "assets"
seen_rel = {}
blocks = {}
for ns in NS_C:
    for kind in ("models/block", "textures/block"):
        for f in sorted((CA / ns / kind).rglob("*")):
            sub = f.relative_to(CA / ns / kind)
            if not f.is_file() or "layered_strata" in sub.parts:
                continue
            rel = f"{kind}/{sub.as_posix()}"
            assert rel not in seen_rel, f"namespace collision: {rel}"
            seen_rel[rel] = ns
            dst = A / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if f.suffix == ".png":
                shutil.copyfile(f, dst)  # byte-for-byte copy; no image processing at all
            else:
                wj(dst, rewrite(lj(f)))
    for bs in sorted((CA / ns / "blockstates").glob("*.json")):
        assert bs.stem not in blocks, f"block id collision: {bs.stem}"
        blocks[bs.stem] = rewrite(lj(bs))

# split layered_strata: one standalone block per layer value
ls = blocks.pop("layered_strata")
layer_ids = []
for key, v in ls["variants"].items():
    lid = key.split("=", 1)[1]
    assert lid not in blocks, lid
    layer_ids.append(lid)
    src_model = lj(model_file(entries(v)[0]["model"].replace("pysift:", "sift:", 1), CA))
    tex = {}
    for face, t in src_model["textures"].items():
        dst = A / "textures/block" / lid / f"{lid}_{face}.png"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(tex_file(t, CA), dst)
        tex[face] = f"pysift:block/{lid}/{lid}_{face}"
    wj(A / "models/block" / lid / f"{lid}.json", {"parent": src_model["parent"], "textures": tex})
    blocks[lid] = {"variants": {"": {"model": f"pysift:block/{lid}/{lid}"}}}

# frost_veined_stone: the 4 undrawn tint/veins combinations borrow the closest existing model
fv = blocks["frost_veined_stone"]["variants"]
for k in ("tint=violet,veins=0", "tint=crimson,veins=0", "tint=none,veins=1", "tint=none,veins=2"):
    assert k not in fv
    fv[k] = json.loads(json.dumps(fv["tint=none,veins=0"]))

for bid, bs in blocks.items():
    wj(A / "blockstates" / f"{bid}.json", bs)


# ---------- 5. derive block definitions ----------
def parse_key(k): return dict(x.split("=", 1) for x in k.split(",") if x)


defs = {}
for bid, bs in blocks.items():
    order = {}
    for k in bs["variants"]:
        for pn, pv in parse_key(k).items():
            order.setdefault(pn, [])
            if pv not in order[pn]:
                order[pn].append(pv)
    props = []
    for pn, vals in order.items():
        if pn == "axis":
            continue
        if all(v.isdigit() for v in vals):
            iv = sorted(int(v) for v in vals)
            assert iv == list(range(iv[0], iv[-1] + 1)), (bid, pn, iv)
            props.append(("int", pn, iv[0], iv[-1], [str(i) for i in iv]))
        else:
            props.append(("enum", pn, None, None, vals))
    defs[bid] = {"pillar": "axis" in order, "props": props}


def default_fixed(bid): return {p[1]: p[4][0] for p in defs[bid]["props"]}


def state_model(bid, fixed):
    for k, v in blocks[bid]["variants"].items():
        d = parse_key(k)
        if all(d.get(p) == val for p, val in fixed.items()) and d.get("axis", "y") == "y":
            return entries(v)[0]["model"]
    raise KeyError((bid, fixed))


# material / tool: majority vote over old blocks whose texture pixels are identical
mat_log = {}
for bid in blocks:
    vm, vt = collections.Counter(), collections.Counter()
    for v in blocks[bid]["variants"].values():
        for e in entries(v):
            for t in lj(model_file(e["model"], RES / "assets"))["textures"].values():
                for oid in pix_to_old.get(pixkey(tex_file(t, RES / "assets")), ()):
                    vm[old_mat[oid]] += 1
                    vt[old_tool.get(oid, "pickaxe")] += 1
    defs[bid]["mat"] = vm.most_common(1)[0][0] if vm else "STONE"
    defs[bid]["tool"] = vt.most_common(1)[0][0] if vt else "pickaxe"
    mat_log[bid] = {"mat": dict(vm), "tool": dict(vt)}


# ---------- 6. item models, item definitions, loot tables ----------
def leaf(model): return {"type": "minecraft:model", "model": model}


def select(bid, i, fixed):
    props = defs[bid]["props"]
    if i == len(props):
        return leaf(state_model(bid, {**default_fixed(bid), **fixed}))
    pn, vals = props[i][1], props[i][4]
    return {"type": "minecraft:select", "block_state_property": pn, "property": "minecraft:block_state",
            "cases": [{"model": select(bid, i + 1, {**fixed, pn: v}), "when": v} for v in vals],
            "fallback": leaf(f"pysift:item/{bid}")}


for bid in blocks:
    wj(A / "models/item" / f"{bid}.json", {"parent": state_model(bid, default_fixed(bid))})
    wj(A / "items" / f"{bid}.json", {"model": select(bid, 0, {}) if defs[bid]["props"] else leaf(f"pysift:item/{bid}")})
    entry = {"type": "minecraft:item", "name": f"pysift:{bid}"}
    if defs[bid]["props"]:
        entry["modifier"] = [{"type": "minecraft:copy_state", "block": f"pysift:{bid}",
                              "properties": [p[1] for p in defs[bid]["props"]]}]
    loot = {"type": "minecraft:block",
            "pools": [{"condition": {"type": "minecraft:survives_explosion"}, "entries": [entry], "rolls": 1}],
            "random_sequence": f"pysift:blocks/{bid}"}
    wj(D / "pysift/loot_table/blocks" / f"{bid}.json", loot)
    wj(D / "pysift/loot_tables/blocks" / f"{bid}.json", loot)

# ---------- 7. mineable tags ----------
old_set = {f"pysift:{o}" for o in old_ids}
for tool in ("axe", "hoe", "pickaxe", "shovel"):
    tf = TAGDIR / f"{tool}.json"
    tag = lj(tf) if tf.exists() else {"replace": False, "values": []}
    vals = [v for v in tag["values"] if v not in old_set]
    vals += [f"pysift:{b}" for b in blocks if defs[b]["tool"] == tool and f"pysift:{b}" not in vals]
    tag["values"] = vals
    wj(tf, tag)

# ---------- 8. lang ----------
reg = (C / "REGISTRY.md").read_text(encoding="utf-8")
summary = reg.split("## 二")[0]
zh = {}
for m in re.finditer(r"^\| `(?:sift|custom):([a-z0-9_]+)` \| ([^|`]+?) \|", summary, re.M):
    zh.setdefault(m.group(1), m.group(2).strip())
with open(C / "registry.csv", encoding="utf-8-sig") as fh:
    for row in csv.DictReader(fh):
        if row["方塊ID"] == "sift:layered_strata":
            zh.setdefault(row["狀態"].split("=", 1)[1], row["中文狀態"].strip())
missing_zh = [b for b in blocks if b not in zh]


def en(b): return " ".join(w.capitalize() for w in b.split("_"))


for lang in ("en_us", "zh_tw"):
    lf = A / "lang" / f"{lang}.json"
    d = lj(lf)
    d = {k: v for k, v in d.items()
         if not (k.startswith(("block.pysift.", "item.pysift.")) and k.split(".", 2)[2] in old_mat)}
    for b in blocks:
        name = zh.get(b, en(b)) if lang == "zh_tw" else en(b)
        d[f"block.pysift.{b}"] = name
        d[f"item.pysift.{b}"] = name
    wj(lf, d)

# ---------- 9. java definition table ----------
md_order = [m.group(1) for m in re.finditer(r"^\| `(?:sift|custom):([a-z0-9_]+)` \|", summary, re.M)]
order = []
for b in md_order:
    if b == "layered_strata":
        order += layer_ids
    elif b in blocks and b not in order:
        order.append(b)
assert sorted(order) == sorted(blocks), set(blocks) ^ set(order)
TODO = {"meadow_grass_block": "// TODO: verify texture pairing — grass_cover=1、2 的側面為推測配對",
        "peeling_log": "// TODO: verify texture pairing — 三階共用的頂面為推測配對",
        "frost_veined_stone": "// TODO: verify — 未繪製的 4 種 tint/veins 組合暫借 tint=none,veins=0 的模型"}
for lid in layer_ids:
    TODO[lid] = "// TODO: verify texture pairing — 頂面與底面為色彩最近鄰推測"
ENUMS = {"tint": "SiftStateProperties.Tint", "host": "SiftStateProperties.Host"}
lines = []
for b in order:
    d = defs[b]
    s = f'{"pillar" if d["pillar"] else "block"}("{b}", Mat.{d["mat"]})'
    for kind, pn, lo, hi, vals in d["props"]:
        s += f'.intProp("{pn}", {lo}, {hi})' if kind == "int" else f'.enumProp("{pn}", {ENUMS[pn]}.class)'
    s += ","
    if b in TODO:
        s += " " + TODO[b]
    lines.append(s)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "defs.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
(OUT / "mat_log.json").write_text(json.dumps(mat_log, ensure_ascii=False, indent=1), encoding="utf-8")
enum_vals = {pn: vals for b in blocks for kind, pn, _, _, vals in defs[b]["props"] if kind == "enum"}
print(json.dumps({"blocks": len(blocks), "removed_files": len(removed), "layer_ids": layer_ids,
                  "enum_values": enum_vals, "missing_zh": missing_zh,
                  "mat": collections.Counter(d["mat"] for d in defs.values()),
                  "tool": collections.Counter(d["tool"] for d in defs.values()),
                  "no_vote": [b for b, v in mat_log.items() if not v["mat"]]},
                 ensure_ascii=False, indent=1))
