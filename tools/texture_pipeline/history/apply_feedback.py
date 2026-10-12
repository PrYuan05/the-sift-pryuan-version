"""Apply the user's random-pool feedback (round 2).
Usage: python -I apply_feedback.py <project> <out_dir>
- tone labels on random pools, dark_slate becomes progressive (fade), new cube / facing / pillar blocks,
  teal_strata d joins abyssal_strata. PNGs are never written; orientation lives in UV template models."""
import json, sys, re
from pathlib import Path

P, OUT = Path(sys.argv[1]), Path(sys.argv[2])
RES = P / "src/main/resources"; A = RES / "assets/pysift"; D = RES / "data"
JAVA = P / "src/main/java/pryuan05/pysift/block/ModBlocks.java"
TAGS = D / "minecraft/tags/block/mineable"

# palette helpers shared with the scanner
ns = {"__name__": "lib"}  # the scanner header reads sys.argv[1:3], which match this script's arguments
exec((Path(__file__).parent / "directional_scan.py").read_text(encoding="utf-8").split("# ---- gather")[0], ns)
Tex, pdist = ns["Tex"], ns["pdist"]


def lj(p): return json.loads(p.read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def entries(v): return v if isinstance(v, list) else [v]


def models_by_label(block):
    out = {}
    for v in lj(A / "blockstates" / f"{block}.json")["variants"].values():
        for e in entries(v):
            out.setdefault(e["model"].rsplit("_", 1)[1], e["model"])
    return out


def ref(block, label):
    m = f"pysift:block/{block}/{block}_{label}"
    assert (A / "models" / (m.split(":", 1)[1] + ".json")).exists(), m
    return m


def texture_of(model):
    t = lj(A / "models" / (model.split(":", 1)[1] + ".json"))["textures"]
    return t.get("all") or t.get("side")


java = JAVA.read_text(encoding="utf-8")
MAT = dict(re.findall(r'(?:block|pillar|facing)\("([a-z0-9_]+)", Mat\.(\w+)\)', java))
TOOL = {}
for tf in TAGS.glob("*.json"):
    for v in lj(tf)["values"]:
        TOOL[v.split(":", 1)[1]] = tf.stem
lang = {l: lj(A / f"lang/{l}.json") for l in ("en_us", "zh_tw")}
LIB = sorted({ref for bs in (A / "blockstates").glob("*.json") for v in lj(bs)["variants"].values()
              for e in entries(v) for ref in lj(A / "models" / (e["model"].split(":", 1)[1] + ".json"))["textures"].values()
              if ref.startswith("pysift:")})
SIDES = set()
for mf in (A / "models/block").rglob("*.json"):
    mj = lj(mf)
    if "side" in mj.get("textures", {}) and not mf.parent.name == "templates":
        SIDES.add(mj["textures"]["side"])
SIDES |= {c["texture"] for c in lj(OUT / "directional_proposal.json")}
SIDES |= {f"pysift:block/void_stone/void_stone_{l}" for l in "hi"} | {"pysift:block/teal_strata/teal_strata_g"}
LIB = [r for r in LIB if r not in SIDES]
_lib = {}


def lib_tex(ref):
    if ref not in _lib:
        _lib[ref] = Tex(ref)
    return _lib[ref]


def best(pal, exclude, k=3):
    scored = sorted(((pdist(pal, lib_tex(r).pal), r) for r in LIB if r not in exclude), key=lambda s: s[0])
    return [r for _, r in scored[:k]]


FACING_ROT = {"up": {}, "down": {"x": 180}, "north": {"x": 90}, "south": {"x": 90, "y": 180},
              "east": {"x": 90, "y": 90}, "west": {"x": 90, "y": 270}}
AXIS_ROT = {"y": {}, "z": {"x": 90}, "x": {"x": 90, "y": 90}}
java_lines = {}


def write_block(bid, shape, props, variants, mat, tool, zh, note=None):
    """props: [(name, kind, values)], variants: {"k=v,...": [model, ...]} without orientation keys."""
    def pool(models, rot): return [{"model": m, "weight": 1, **rot} for m in models]
    bs = {}
    for key, models in variants.items():
        if shape == "facing":
            for f, rot in FACING_ROT.items():
                bs[",".join(filter(None, [f"facing={f}", key]))] = pool(models, rot)
        elif shape == "pillar":
            for a, rot in AXIS_ROT.items():
                bs[",".join(filter(None, [f"axis={a}", key]))] = pool(models, rot)
        else:
            bs[key] = pool(models, {})
    wj(A / "blockstates" / f"{bid}.json", {"variants": bs})
    default_key = ",".join(f"{n}={vals[0]}" for n, _, vals in props)
    wj(A / "models/item" / f"{bid}.json", {"parent": variants[default_key][0]})

    def select(i, fixed):
        if i == len(props):
            return {"type": "minecraft:model", "model": variants[",".join(f"{n}={fixed[n]}" for n, _, _ in props)][0]}
        n, _, vals = props[i]
        return {"type": "minecraft:select", "block_state_property": n, "property": "minecraft:block_state",
                "cases": [{"model": select(i + 1, {**fixed, n: v}), "when": v} for v in vals],
                "fallback": {"type": "minecraft:model", "model": f"pysift:item/{bid}"}}
    wj(A / "items" / f"{bid}.json", {"model": select(0, {}) if props else {"type": "minecraft:model", "model": f"pysift:item/{bid}"}})
    entry = {"type": "minecraft:item", "name": f"pysift:{bid}"}
    if props:
        entry["modifier"] = [{"type": "minecraft:copy_state", "block": f"pysift:{bid}", "properties": [n for n, _, _ in props]}]
    loot = {"type": "minecraft:block", "pools": [{"condition": {"type": "minecraft:survives_explosion"},
                                                  "entries": [entry], "rolls": 1}], "random_sequence": f"pysift:blocks/{bid}"}
    wj(D / "pysift/loot_table/blocks" / f"{bid}.json", loot)
    wj(D / "pysift/loot_tables/blocks" / f"{bid}.json", loot)
    for tf in TAGS.glob("*.json"):
        tag = lj(tf)
        vals = [v for v in tag["values"] if v != f"pysift:{bid}"]
        if tf.stem == tool:
            vals.append(f"pysift:{bid}")
        tag["values"] = vals
        wj(tf, tag)
    if zh:
        en = " ".join(w.capitalize() for w in bid.split("_"))
        for key in (f"block.pysift.{bid}", f"item.pysift.{bid}"):
            lang["en_us"][key], lang["zh_tw"][key] = en, zh
    line = f'{shape if shape != "cube" else "block"}("{bid}", Mat.{mat})'
    for n, kind, vals in props:
        line += f'.intProp("{n}", {vals[0]}, {vals[-1]})' if kind == "int" else '.tones(' + ", ".join(f'"{v}"' for v in vals) + ')'
    java_lines[bid] = line + "," + (f" {note}" if note else "")


# ---------- templates ----------
def face(tex, cull, tf="none"):
    f = {"uv": [0, 0, 16, 16], "texture": tex, "cullface": cull}
    if tf == "vflip":
        f["uv"] = [0, 16, 16, 0]
    return f


wj(A / "models/block/templates/cube_column_vflip.json",
   {"parent": "minecraft:block/block", "textures": {"particle": "#side"},
    "elements": [{"from": [0, 0, 0], "to": [16, 16, 16],
                  "faces": {"down": face("#end", "down"), "up": face("#end", "up"),
                            **{d: face("#side", d, "vflip") for d in ("north", "south", "west", "east")}}}]})

TEMPLATE = {"none": "minecraft:block/cube_bottom_top", "vflip": "pysift:block/templates/cube_bottom_top_vflip",
            "rot90": "pysift:block/templates/cube_bottom_top_rot90", "rot270": "pysift:block/templates/cube_bottom_top_rot270"}

# ---------- snapshot of current pools ----------
M = {b: models_by_label(b) for b in ("dark_slate", "stone_bricks", "crimson_strata", "edged_stone", "gray_strata",
                                     "smooth_stone", "teal_strata", "violet_strata", "void_stone", "rose_strata",
                                     "veined_teal_stone")}
TONES = {
    "stone_bricks": [("smooth", "d"), ("rough", "c"), ("paneled", "e"), ("dark", "ab")],
    "crimson_strata": [("rose", "ad"), ("mottled", "g"), ("crimson", "jk"), ("plum", "mn")],
    "edged_stone": [("olive", "bcd"), ("warm", "ae")],
    "gray_strata": [("teal", "dej"), ("lavender", "ck"), ("violet", "fg"), ("warm", "b")],
    "smooth_stone": [("light", "ad"), ("warm", "ce"), ("blue", "b")],
    "teal_strata": [("pale", "ef"), ("cyan", "ab")],
    "violet_strata": [("dusk", "ad"), ("violet", "fg"), ("slate", "e")],
    "void_stone": [("dark", "c"), ("rusty", "f"), ("olive", "e")],
    "rose_strata": [("violet", "a"), ("rose", "b")],
    "veined_teal_stone": [("teal", "a"), ("mottled", "b")],
}
MOVED_OUT = {"crimson_strata": "i", "teal_strata": "dg", "void_stone": "abdghi"}  # handled by the blocks below
for b, tones in TONES.items():
    covered = "".join(l for _, ls in tones for l in ls) + MOVED_OUT.get(b, "")
    assert set(M[b]) <= set(covered), (b, sorted(set(M[b]) - set(covered)))
    write_block(b, "cube", [("tone", "enum", [t for t, _ in tones])],
                {f"tone={t}": [ref(b, l) for l in ls] for t, ls in tones}, MAT[b], TOOL[b], None)

# dark_slate: progressive fade (violet fades into grey-green)
DS = {l: ref("dark_slate", l) for l in "kopqrstuaeghijd" if l != "q"}
FADE = ["k", "op", "rs", "tu"]
write_block("dark_slate", "cube", [("fade", "int", [str(i) for i in range(len(FADE))])],
            {f"fade={i}": [DS[l] for l in ls] for i, ls in enumerate(FADE)}, "DEEPSLATE", TOOL["dark_slate"], "深色板岩",
            "// k → o,p → r,s → t,u：紫色漸少、灰綠漸多")
write_block("varied_dark_slate", "cube", [("tone", "enum", ["gray", "mottled", "violet"])],
            {"tone=gray": [DS[l] for l in "ghi"], "tone=mottled": [DS["d"]], "tone=violet": [DS["j"]]},
            "DEEPSLATE", TOOL["dark_slate"], "雜色深色板岩")
write_block("framed_dark_slate", "cube", [], {"": [DS["a"]]}, "DEEPSLATE", TOOL["dark_slate"], "框紋深色板岩")
write_block("blotched_dark_slate", "cube", [], {"": [DS["e"]]}, "DEEPSLATE", TOOL["dark_slate"], "斑紋深色板岩")

VS = {l: ref("void_stone", l) for l in "abcdefghi"}
write_block("umber_void_stone", "cube", [], {"": [VS["a"]]}, MAT["void_stone"], TOOL["void_stone"], "褐色虛黑岩")
write_block("void_stone_bricks", "cube", [], {"": [VS["b"], VS["d"]]}, MAT["void_stone"], TOOL["void_stone"], "虛黑岩磚")
write_block("speckled_void_stone", "cube", [], {"": [VS["g"]]}, MAT["void_stone"], TOOL["void_stone"], "斑點虛黑岩")


# ---------- facing (grass-block style) and pillar blocks ----------
def facing_block(bid, src_block, label, transform, band_side, zh):
    side = texture_of(ref(src_block, label))
    t = Tex(side)
    band = t.band(band_side)
    tops, bottoms = best(band["band_pal"], {side}), best(band["rest_pal"], {side})
    models = []
    for top in tops:
        for bottom in bottoms:
            m = f"pysift:block/{bid}/{bid}_{len(models) + 1}"
            wj(A / "models/block" / bid / f"{bid}_{len(models) + 1}.json",
               {"parent": TEMPLATE[transform], "textures": {"top": top, "bottom": bottom, "side": side}})
            models.append(m)
    write_block(bid, "facing", [], {"": models}, MAT[src_block], TOOL[src_block], zh,
                f"// TODO: verify texture pairing — 頂面／底面為色彩相近的推測配對（來源 {src_block}_{label}，{transform}）")
    return {"side": side, "transform": transform, "top": tops, "bottom": bottoms}


report = {}
# crimson_strata i: teal edge on the left -> rotate so it faces up
report["crimson_capped_crimson_strata_3"] = facing_block("crimson_capped_crimson_strata_3", "crimson_strata", "i", "rot90", "left", "赤紅覆蓋赤紅地層岩 3")
# teal_strata g: user — the right side goes to the bottom (clockwise 90°, left edge becomes the top)
report["teal_capped_teal_strata_2"] = facing_block("teal_capped_teal_strata_2", "teal_strata", "g", "rot90", "left", "青碧覆蓋青碧地層岩 2")
# void_stone i: dark band already at the top
report["gray_capped_void_stone"] = facing_block("gray_capped_void_stone", "void_stone", "i", "none", "top", "灰覆蓋虛黑岩")

# void_stone h: flipped upside down as a pillar side
h_side = texture_of(VS["h"])
ends = best(Tex(h_side).pal, {h_side})
pillar_models = []
for j, end in enumerate(ends, 1):
    wj(A / "models/block/void_stone_pillar" / f"void_stone_pillar_{j}.json",
       {"parent": "pysift:block/templates/cube_column_vflip", "textures": {"end": end, "side": h_side}})
    pillar_models.append(f"pysift:block/void_stone_pillar/void_stone_pillar_{j}")
write_block("void_stone_pillar", "pillar", [], {"": pillar_models}, MAT["void_stone"], TOOL["void_stone"], "虛黑岩柱",
            "// TODO: verify texture pairing — 端面為色彩相近的推測配對（來源 void_stone_h，側面上下翻轉）")
report["void_stone_pillar"] = {"side": h_side, "transform": "vflip", "end": ends}

# teal_strata d -> abyssal_strata, into the depth stage it resembles most
ab = lj(A / "blockstates/abyssal_strata.json")
d_model = ref("teal_strata", "d")
d_tex = Tex(texture_of(d_model))
scores = {k: min(pdist(d_tex.pal, Tex(texture_of(e["model"])).pal) for e in entries(v) if e["model"] != d_model)
          for k, v in ab["variants"].items()}
target = min(scores, key=scores.get)
if d_model not in [e["model"] for e in entries(ab["variants"][target])]:
    ab["variants"][target] = entries(ab["variants"][target]) + [{"model": d_model, "weight": 1}]
wj(A / "blockstates/abyssal_strata.json", ab)
report["abyssal_strata"] = {"added": d_model, "to": target, "distances": {k: round(v, 1) for k, v in scores.items()}}

for l, d in lang.items():
    wj(A / f"lang/{l}.json", d)
(OUT / "feedback_java.json").write_text(json.dumps(java_lines, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "feedback_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=1))
