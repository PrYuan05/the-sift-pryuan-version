"""Every resource of the void stone building family (VoidStoneFamily.java), copied from vanilla and rewritten.
Usage: python -I tools/worldgen/build_void_stone_family.py <project>

Vanilla deepslate's polished / tiles / cracked forms and vanilla smooth stone, as void stone (the basalt bedrock); the
plain stone, bricks, chiseled bricks and pillar already exist (ModBlocks, building sets).
  blockstates, block / item models, item definitions  <- minecraft-clientOnly jar
  recipes (crafting, smelting, stonecutting), loot tables, tags  <- minecraft-common jar
Names: "cobbled_deepslate" and "deepslate" become "void_stone", a whole word "stone" (smooth stone) becomes "void_stone".
Ingredients: cobbled deepslate / stone -> pysift:void_stone, deepslate bricks -> pysift:void_stone_bricks.
Textures are hand-painted by tools/worldgen/paint_void_stone.py (textures/block/void_stone/<name>.png); this script only
points the models at them. New full blocks also go into #minecraft:blocks_motion_no_leaves (CLAUDE.md).
"""
import json, re, sys, zipfile
from pathlib import Path

P = Path(sys.argv[1]).resolve()
RES = P / "src/main/resources"
A, D = RES / "assets/pysift", RES / "data"
CACHE = P / ".gradle/loom-cache/minecraftMaven/net/minecraft"
CLIENT = zipfile.ZipFile(next(CACHE.glob("minecraft-clientOnly-*/26.3/minecraft-clientOnly-*-26.3.jar")))
COMMON = zipfile.ZipFile(next(CACHE.glob("minecraft-common-*/26.3/minecraft-common-*-26.3.jar")))

PARTS = ["polished_deepslate", "polished_deepslate_slab", "polished_deepslate_stairs", "polished_deepslate_wall",
         "deepslate_tiles", "deepslate_tile_slab", "deepslate_tile_stairs", "deepslate_tile_wall",
         "cracked_deepslate_bricks", "cracked_deepslate_tiles", "smooth_stone", "smooth_stone_slab"]
FULL = ["polished_deepslate", "deepslate_tiles", "cracked_deepslate_bricks", "cracked_deepslate_tiles", "smooth_stone"]
INGREDIENTS = {"minecraft:cobbled_deepslate": "pysift:void_stone", "minecraft:stone": "pysift:void_stone",
               "minecraft:deepslate_bricks": "pysift:void_stone_bricks"}
NAMES = {  # our id -> (en, zh)
    "polished_void_stone": ("Polished Void Stone", "磨製虛黑岩"),
    "polished_void_stone_slab": ("Polished Void Stone Slab", "磨製虛黑岩半磚"),
    "polished_void_stone_stairs": ("Polished Void Stone Stairs", "磨製虛黑岩階梯"),
    "polished_void_stone_wall": ("Polished Void Stone Wall", "磨製虛黑岩牆"),
    "void_stone_tiles": ("Void Stone Tiles", "虛黑岩磚瓦"),
    "void_stone_tile_slab": ("Void Stone Tile Slab", "虛黑岩磚瓦半磚"),
    "void_stone_tile_stairs": ("Void Stone Tile Stairs", "虛黑岩磚瓦階梯"),
    "void_stone_tile_wall": ("Void Stone Tile Wall", "虛黑岩磚瓦牆"),
    "cracked_void_stone_bricks": ("Cracked Void Stone Bricks", "裂紋虛黑岩磚"),
    "cracked_void_stone_tiles": ("Cracked Void Stone Tiles", "裂紋虛黑岩磚瓦"),
    "smooth_void_stone": ("Smooth Void Stone", "平滑虛黑岩"),
    "smooth_void_stone_slab": ("Smooth Void Stone Slab", "平滑虛黑岩半磚"),
    "cracked_void_stone_brick_slab": ("Cracked Void Stone Brick Slab", "裂紋虛黑岩磚半磚"),
    "cracked_void_stone_brick_stairs": ("Cracked Void Stone Brick Stairs", "裂紋虛黑岩磚階梯"),
    "cracked_void_stone_brick_wall": ("Cracked Void Stone Brick Wall", "裂紋虛黑岩磚牆"),
    "cracked_void_stone_tile_slab": ("Cracked Void Stone Tile Slab", "裂紋虛黑岩磚瓦半磚"),
    "cracked_void_stone_tile_stairs": ("Cracked Void Stone Tile Stairs", "裂紋虛黑岩磚瓦階梯"),
    "cracked_void_stone_tile_wall": ("Cracked Void Stone Tile Wall", "裂紋虛黑岩磚瓦牆"),
    "smooth_void_stone_stairs": ("Smooth Void Stone Stairs", "平滑虛黑岩階梯"),
    "smooth_void_stone_wall": ("Smooth Void Stone Wall", "平滑虛黑岩牆"),
}
# every block gets slab / stairs / wall (user rule); forms vanilla has no template for are made from the
# polished_deepslate ones: base block id -> (prefix of the new ids, texture, forms)
DERIVE = {
    "cracked_void_stone_bricks": ("cracked_void_stone_brick", "cracked_void_stone_bricks", ("slab", "stairs", "wall")),
    "cracked_void_stone_tiles": ("cracked_void_stone_tile", "cracked_void_stone_tiles", ("slab", "stairs", "wall")),
    "smooth_void_stone": ("smooth_void_stone", "smooth_void_stone", ("stairs", "wall")),
}
TEMPLATE = "polished_deepslate"


def lj(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jar_json(jar, name): return json.loads(jar.read(name))


def rename(name):
    out, toks = [], name.split("_")
    for i, t in enumerate(toks):
        if t == "cobbled" and i + 1 < len(toks) and toks[i + 1] == "deepslate":
            continue
        out += ["void", "stone"] if t in ("deepslate", "stone") else [t]
    return "_".join(out)


IDS = {f"minecraft:{p}": f"pysift:{rename(p)}" for p in PARTS} | INGREDIENTS
textures, models = {}, {}


def is_ours(ref):
    name = ref.split(":", 1)[-1].split("/")[-1]
    return any(k in name for k in ("deepslate", "smooth_stone")) and "cobbled" not in name


def texture_ref(ref):
    if not ref.startswith("minecraft:block/") or not is_ours(ref):
        return ref
    ours = f"pysift:block/void_stone/{rename(ref.split('/', 1)[1])}"
    textures[ours] = ref
    return ours


def model_ref(ref):
    if not ref.startswith("minecraft:block/") or not is_ours(ref):
        return ref
    ours = "pysift:block/" + rename(ref.split("/", 1)[1])
    models[ours] = ref
    return ours


def rewrite(obj, key=None):
    if isinstance(obj, dict):
        if key == "textures":
            return {k: texture_ref(v) if isinstance(v, str) and not v.startswith("#") else v for k, v in obj.items()}
        return {k: rewrite(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rewrite(v, key) for v in obj]
    if isinstance(obj, str):
        if key in ("model", "parent", "base"):
            return model_ref(obj)
        if obj in IDS:
            return IDS[obj]
        if obj.startswith("minecraft:blocks/") and obj.split("/", 1)[1] in PARTS:      # loot random_sequence
            return f"pysift:blocks/{rename(obj.split('/', 1)[1])}"
    return obj


def derive():
    """Slab / stairs / wall for the blocks vanilla leaves without them, from the polished_deepslate forms: block ids,
    model names and the texture are swapped; recipes (crafting + stonecutting from the base), loot and tags the same way."""
    made = []
    for base, (prefix, tex, forms) in DERIVE.items():
        def sub(obj, key=None):
            if isinstance(obj, dict):
                return {k: sub(v, k) for k, v in obj.items()}
            if isinstance(obj, list):
                return [sub(v, key) for v in obj]
            if isinstance(obj, str):
                if obj == f"minecraft:block/{TEMPLATE}" and key not in ("model", "parent"):
                    return f"pysift:block/void_stone/{tex}"                       # the texture
                if obj == f"minecraft:block/{TEMPLATE}":
                    return f"pysift:block/{base}"                                 # double slab -> the full block
                for f in ("slab", "stairs", "wall"):
                    if obj.startswith(f"minecraft:block/{TEMPLATE}_{f}"):
                        return f"pysift:block/{prefix}_{f}" + obj[len(f"minecraft:block/{TEMPLATE}_{f}"):]
                    if obj == f"minecraft:{TEMPLATE}_{f}":
                        return f"pysift:{prefix}_{f}"
                    if obj == f"minecraft:blocks/{TEMPLATE}_{f}":
                        return f"pysift:blocks/{prefix}_{f}"
                if obj == f"minecraft:{TEMPLATE}":
                    return f"pysift:{base}"
            return obj
        for f in forms:
            part, ours = f"{TEMPLATE}_{f}", f"{prefix}_{f}"
            made.append(ours)
            for kind in ("blockstates", "items"):
                wj(A / f"{kind}/{ours}.json", sub(jar_json(CLIENT, f"assets/minecraft/{kind}/{part}.json")))
            for n in CLIENT.namelist():
                m = re.fullmatch(rf"assets/minecraft/models/block/({part}[a-z_]*)\.json", n)
                if m:
                    wj(A / f"models/block/{prefix}_{f}{m[1][len(part):]}.json", sub(jar_json(CLIENT, n)))
            for n in (f"{part}", f"{part}_from_{TEMPLATE}_stonecutting"):
                wj(D / ("pysift/recipe/" + ours + ("" if n == part else f"_from_{base}_stonecutting") + ".json"),
                   sub(jar_json(COMMON, f"data/minecraft/recipe/{n}.json")))
            table = sub(jar_json(COMMON, f"data/minecraft/loot_table/blocks/{part}.json"))
            for d in ("loot_table", "loot_tables"):
                wj(D / f"pysift/{d}/blocks/{ours}.json", table)
            for n in COMMON.namelist():
                if n.startswith("data/minecraft/tags/") and n.endswith(".json") and "/worldgen/" not in n                         and f"minecraft:{part}" in jar_json(COMMON, n)["values"]:
                    path = D / "minecraft/tags" / n[len("data/minecraft/tags/"):]
                    data = lj(path) if path.exists() else {"replace": False, "values": []}
                    if f"pysift:{ours}" not in data["values"]:
                        data["values"].append(f"pysift:{ours}")
                    wj(path, data)
    return made


def main():
    for name in PARTS:
        for kind in ("blockstates", "items"):
            wj(A / f"{kind}/{rename(name)}.json", rewrite(jar_json(CLIENT, f"assets/minecraft/{kind}/{name}.json")))
    done = set()
    while set(models) - done:
        for ours in sorted(set(models) - done):
            done.add(ours)
            path = models[ours].split(":", 1)[1]
            wj(A / f"models/{ours.split(':', 1)[1]}.json", rewrite(jar_json(CLIENT, f"assets/minecraft/models/{path}.json")))
    missing = [t for t in textures if not (A / "textures" / (t.split(":", 1)[1] + ".png")).exists()]
    # recipes: every vanilla recipe whose result is one of the parts; skipped if an ingredient is still vanilla deepslate
    recipes, skipped = 0, []
    for n in COMMON.namelist():
        m = re.fullmatch(r"data/minecraft/recipe/([a-z_]+)\.json", n)
        if not m:
            continue
        recipe = jar_json(COMMON, n)
        result = recipe.get("result", {})
        if (result.get("id") if isinstance(result, dict) else result) not in {f"minecraft:{p}" for p in PARTS}:
            continue
        out = rewrite(recipe)
        if re.search(r'"minecraft:[a-z_]*(deepslate|smooth_stone)', json.dumps(out)):
            skipped.append(m[1])
            continue
        wj(D / f"pysift/recipe/{rename(m[1])}.json", out)
        recipes += 1
    for name in PARTS:
        table = rewrite(jar_json(COMMON, f"data/minecraft/loot_table/blocks/{name}.json"))
        for d in ("loot_table", "loot_tables"):
            wj(D / f"pysift/{d}/blocks/{rename(name)}.json", table)
    tags = 0
    for n in COMMON.namelist():
        if not (n.startswith("data/minecraft/tags/") and n.endswith(".json")) or "/worldgen/" in n:
            continue
        add = [IDS[v] for v in jar_json(COMMON, n)["values"]
               if isinstance(v, str) and v in IDS and v.split(":", 1)[1] in PARTS]
        if not add:
            continue
        path = D / "minecraft/tags" / n[len("data/minecraft/tags/"):]
        data = lj(path) if path.exists() else {"replace": False, "values": []}
        data["values"] += [v for v in add if v not in data["values"]]
        wj(path, data)
        tags += 1
    motion = D / "minecraft/tags/block/blocks_motion_no_leaves.json"
    data = lj(motion)
    data["values"] += [f"pysift:{rename(p)}" for p in FULL if f"pysift:{rename(p)}" not in data["values"]]
    wj(motion, data)
    print("derived:", derive())
    for code in ("en_us", "zh_tw"):
        lang = lj(A / f"lang/{code}.json")
        for bid, (en, zh) in NAMES.items():
            lang[f"block.pysift.{bid}"] = en if code == "en_us" else zh
            lang[f"item.pysift.{bid}"] = lang[f"block.pysift.{bid}"]   # block items read item.* in 26.3
        wj(A / f"lang/{code}.json", lang)
    print(f"{len(PARTS)} blocks, {len(models)} models, {len(textures)} textures, {recipes} recipes, {tags} tags")
    import subprocess, sys as _sys                          # keep models grouped per block (tools/texture_pipeline/group_models.py)
    subprocess.run([_sys.executable, "-I", str(Path(__file__).resolve().parents[1] / "texture_pipeline/group_models.py"), str(P)], check=True)
    print("textures:", sorted(t.split("/")[-1] for t in textures))
    if skipped:
        print("recipes skipped (vanilla ingredient left):", skipped)
    if missing:
        print("MISSING textures (run paint_void_stone.py --apply):", missing)


if __name__ == "__main__":
    main()
