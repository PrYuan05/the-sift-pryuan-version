"""Turn approved directional candidates into new blocks.
- grass type: facing (6 directions, top face points to `facing`), weighted pool of side x top x bottom variants
- pillar type: axis, weighted pool of end variants
Side textures are oriented by UV-only template models; PNGs are never written.
Usage: python -I apply_directional.py <project> <out_dir>"""
import json, sys, itertools, re
from pathlib import Path

P, OUT = Path(sys.argv[1]), Path(sys.argv[2])
RES = P / "src/main/resources"; A = RES / "assets/pysift"; D = RES / "data"
JAVA = P / "src/main/java/pryuan05/pysift/block/ModBlocks.java"

ADOPT = [1, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 25, 26, 27, 29, 30]
MERGE_SIDE = {15: [16]}                 # #16 is #15 upside-down: extra side variant of the same block
BOTTOM_ONLY = {29: [1]}                 # user: #29 bottom candidates 2 and 3 do not fit
FACING_ROT = {"up": {}, "down": {"x": 180}, "north": {"x": 90}, "south": {"x": 90, "y": 180},
              "east": {"x": 90, "y": 90}, "west": {"x": 90, "y": 270}}
TEMPLATE = {"none": "minecraft:block/cube_bottom_top", "vflip": "pysift:block/templates/cube_bottom_top_vflip",
            "rot90": "pysift:block/templates/cube_bottom_top_rot90",
            "rot270": "pysift:block/templates/cube_bottom_top_rot270"}


def lj(p): return json.loads(p.read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def side_face(transform):
    face = {"uv": [0, 0, 16, 16], "texture": "#side"}
    if transform == "vflip":
        face["uv"] = [0, 16, 16, 0]
    elif transform == "rot90":
        face["rotation"] = 90
    elif transform == "rot270":
        face["rotation"] = 270
    return face


for tf in ("vflip", "rot90", "rot270"):
    faces = {"down": {"uv": [0, 0, 16, 16], "texture": "#bottom", "cullface": "down"},
             "up": {"uv": [0, 0, 16, 16], "texture": "#top", "cullface": "up"}}
    for d in ("north", "south", "west", "east"):
        faces[d] = {**side_face(tf), "cullface": d}
    wj(A / f"models/block/templates/cube_bottom_top_{tf}.json",
       {"parent": "minecraft:block/block", "textures": {"particle": "#side"},
        "elements": [{"from": [0, 0, 0], "to": [16, 16, 16], "faces": faces}]})

cands = {c["id"]: c for c in lj(OUT / "directional_proposal.json")}
java = JAVA.read_text(encoding="utf-8")
src_mat = dict(re.findall(r'(?:block|pillar)\("([a-z0-9_]+)", Mat\.(\w+)\)', java))
tool_of = {}
for tf in (D / "minecraft/tags/block/mineable").glob("*.json"):
    for v in lj(tf)["values"]:
        tool_of[v.split(":", 1)[1]] = tf.stem
lang = {l: lj(A / f"lang/{l}.json") for l in ("en_us", "zh_tw")}
zh_seen = {}
java_lines, extracted = [], []
for cid in ADOPT:
    c = cands[cid]
    bid, src = c["proposed_id"], c["uses"][0]["block"]
    models = []
    if c["kind"] == "pillar":
        for j, end in enumerate(c["end_candidates"], 1):
            m = f"pysift:block/{bid}/{bid}_{j}"
            wj(A / "models/block" / bid / f"{bid}_{j}.json",
               {"parent": "minecraft:block/cube_column", "textures": {"end": end["texture"], "side": c["texture"]}})
            models.append(m)
        pool = [{"model": m, "weight": 1} for m in models]
        variants = {"axis=y": pool, "axis=z": [{**e, "x": 90} for e in pool],
                    "axis=x": [{**e, "x": 90, "y": 90} for e in pool]}
        java_kind = "pillar"
    else:
        sides = [(c["texture"], c["transform"])] + [(cands[o]["texture"], cands[o]["transform"]) for o in MERGE_SIDE.get(cid, [])]
        bottoms = [b for j, b in enumerate(c["bottom_candidates"], 1) if j in BOTTOM_ONLY.get(cid, [1, 2, 3])]
        n = 0
        for (side, tf), top, bottom in itertools.product(sides, c["top_candidates"], bottoms):
            n += 1
            m = f"pysift:block/{bid}/{bid}_{n}"
            wj(A / "models/block" / bid / f"{bid}_{n}.json",
               {"parent": TEMPLATE[tf], "textures": {"top": top["texture"], "bottom": bottom["texture"], "side": side}})
            models.append(m)
        pool = [{"model": m, "weight": 1} for m in models]
        variants = {f"facing={f}": [{**e, **rot} for e in pool] for f, rot in FACING_ROT.items()}
        java_kind = "facing"
    wj(A / "blockstates" / f"{bid}.json", {"variants": variants})
    wj(A / "models/item" / f"{bid}.json", {"parent": models[0]})
    wj(A / "items" / f"{bid}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{bid}"}})
    loot = {"type": "minecraft:block",
            "pools": [{"condition": {"type": "minecraft:survives_explosion"},
                       "entries": [{"type": "minecraft:item", "name": f"pysift:{bid}"}], "rolls": 1}],
            "random_sequence": f"pysift:blocks/{bid}"}
    wj(D / "pysift/loot_table/blocks" / f"{bid}.json", loot)
    wj(D / "pysift/loot_tables/blocks" / f"{bid}.json", loot)
    tool = tool_of.get(src, "pickaxe")
    tf = D / "minecraft/tags/block/mineable" / f"{tool}.json"
    tag = lj(tf)
    if f"pysift:{bid}" not in tag["values"]:
        tag["values"].append(f"pysift:{bid}")
    wj(tf, tag)
    zh = c["proposed_zh"]
    zh_seen[zh] = zh_seen.get(zh, 0) + 1
    if zh_seen[zh] > 1:
        zh = f"{zh} {zh_seen[zh]}"
    en = " ".join(w.capitalize() for w in bid.split("_"))
    for key in (f"block.pysift.{bid}", f"item.pysift.{bid}"):
        lang["en_us"][key], lang["zh_tw"][key] = en, zh
    java_lines.append(f'{java_kind}("{bid}", Mat.{src_mat[src]}), // TODO: verify texture pairing — '
                      f'{"端面" if java_kind == "pillar" else "頂面／底面"}為色彩相近的推測配對（來源 {c["name"]}）')
    for o in [cid] + MERGE_SIDE.get(cid, []):
        extracted.extend((u["block"], u["state"], u["model"]) for u in cands[o]["uses"])

for l, d in lang.items():
    wj(A / f"lang/{l}.json", d)

# remove extracted side textures from their source pools (keep it when a state would become empty)
kept = []
by_block = {}
for block, state, model in extracted:
    by_block.setdefault(block, []).append((state, model))
for block, items in by_block.items():
    bp = A / "blockstates" / f"{block}.json"
    bs = lj(bp)
    for state, model in items:
        for key, v in bs["variants"].items():
            entries = v if isinstance(v, list) else [v]
            remaining = [e for e in entries if e["model"] != model]
            if len(remaining) == len(entries):
                continue
            if not remaining:
                kept.append((block, key, model))
                continue
            bs["variants"][key] = remaining if len(remaining) > 1 else remaining[0]
    wj(bp, bs)
    # item model / item definition may point at a removed model: re-point to the first remaining model
    for f in (A / "models/item" / f"{block}.json",):
        im = lj(f)
        first = next(iter(bs["variants"].values()))
        first = first[0] if isinstance(first, list) else first
        if any(im["parent"] == m for _, m in items):
            im["parent"] = first["model"]
            wj(f, im)

(OUT / "directional_java.txt").write_text("\n".join(java_lines) + "\n", encoding="utf-8")
print(json.dumps({"new_blocks": len(java_lines), "removed_from_pools": len(extracted) - len(kept),
                  "kept_to_avoid_empty_state": kept}, ensure_ascii=False, indent=1))
