"""Soulshale building family (SoulshaleFamily.java): vanilla deepslate's whole family in the colours of chiseled soulshale.
Usage: python -I tools/worldgen/build_soulshale_family.py <project>

chiseled_soulshale.png (textures/block/soulshale/) is the user's reference picture, used as-is; its six colours are the
palette for every other texture. The other textures are vanilla deepslate's, recoloured by rank (texture skill method C):
  vanilla's processed-deepslate greys #242424..#585858 (the six chiseled_deepslate uses) -> the six soulshale colours,
  the darkest crack grey and the brightest polish grey -> one derived tone each (cooler and darker / warmer and lighter),
  natural deepslate greys -> the nearest palette tone by brightness, keeping their order.
Blockstates, models, item definitions, recipes, loot and tags are copied from vanilla and renamed
("cobbled_deepslate" and "deepslate" -> "soulshale"). Cracked bricks and cracked tiles get slab / stairs / wall from the
polished_deepslate forms (user rule: every block has them, except chiseled). Soulshale itself comes from abyssal strata:
8 abyssal strata around a soul sand or soul soil -> 8 soulshale. New full blocks go into #minecraft:blocks_motion_no_leaves.
"""
import colorsys, io, json, re, sys, zipfile
from pathlib import Path

from PIL import Image

P = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(P / "tools"))
import art_guard

RES = P / "src/main/resources"
A, D = RES / "assets/pysift", RES / "data"
CACHE = P / ".gradle/loom-cache/minecraftMaven/net/minecraft"
CLIENT = zipfile.ZipFile(next(CACHE.glob("minecraft-clientOnly-*/26.3/minecraft-clientOnly-*-26.3.jar")))
COMMON = zipfile.ZipFile(next(CACHE.glob("minecraft-common-*/26.3/minecraft-common-*-26.3.jar")))
TEX = A / "textures/block/soulshale"

PARTS = ["deepslate", "cobbled_deepslate_slab", "cobbled_deepslate_stairs", "cobbled_deepslate_wall",
         "polished_deepslate", "polished_deepslate_slab", "polished_deepslate_stairs", "polished_deepslate_wall",
         "deepslate_bricks", "deepslate_brick_slab", "deepslate_brick_stairs", "deepslate_brick_wall",
         "cracked_deepslate_bricks", "deepslate_tiles", "deepslate_tile_slab", "deepslate_tile_stairs", "deepslate_tile_wall",
         "cracked_deepslate_tiles", "chiseled_deepslate"]
FULL = ["deepslate", "polished_deepslate", "deepslate_bricks", "cracked_deepslate_bricks", "deepslate_tiles",
        "cracked_deepslate_tiles", "chiseled_deepslate"]
NAMES = {  # our id -> (en, zh)
    "soulshale": ("Soulshale", "魂頁岩"),
    "soulshale_slab": ("Soulshale Slab", "魂頁岩半磚"), "soulshale_stairs": ("Soulshale Stairs", "魂頁岩階梯"),
    "soulshale_wall": ("Soulshale Wall", "魂頁岩牆"),
    "polished_soulshale": ("Polished Soulshale", "磨製魂頁岩"), "polished_soulshale_slab": ("Polished Soulshale Slab", "磨製魂頁岩半磚"),
    "polished_soulshale_stairs": ("Polished Soulshale Stairs", "磨製魂頁岩階梯"), "polished_soulshale_wall": ("Polished Soulshale Wall", "磨製魂頁岩牆"),
    "soulshale_bricks": ("Soulshale Bricks", "魂頁岩磚"), "soulshale_brick_slab": ("Soulshale Brick Slab", "魂頁岩磚半磚"),
    "soulshale_brick_stairs": ("Soulshale Brick Stairs", "魂頁岩磚階梯"), "soulshale_brick_wall": ("Soulshale Brick Wall", "魂頁岩磚牆"),
    "cracked_soulshale_bricks": ("Cracked Soulshale Bricks", "裂紋魂頁岩磚"),
    "cracked_soulshale_brick_slab": ("Cracked Soulshale Brick Slab", "裂紋魂頁岩磚半磚"),
    "cracked_soulshale_brick_stairs": ("Cracked Soulshale Brick Stairs", "裂紋魂頁岩磚階梯"),
    "cracked_soulshale_brick_wall": ("Cracked Soulshale Brick Wall", "裂紋魂頁岩磚牆"),
    "soulshale_tiles": ("Soulshale Tiles", "魂頁岩磚瓦"), "soulshale_tile_slab": ("Soulshale Tile Slab", "魂頁岩磚瓦半磚"),
    "soulshale_tile_stairs": ("Soulshale Tile Stairs", "魂頁岩磚瓦階梯"), "soulshale_tile_wall": ("Soulshale Tile Wall", "魂頁岩磚瓦牆"),
    "cracked_soulshale_tiles": ("Cracked Soulshale Tiles", "裂紋魂頁岩磚瓦"),
    "cracked_soulshale_tile_slab": ("Cracked Soulshale Tile Slab", "裂紋魂頁岩磚瓦半磚"),
    "cracked_soulshale_tile_stairs": ("Cracked Soulshale Tile Stairs", "裂紋魂頁岩磚瓦階梯"),
    "cracked_soulshale_tile_wall": ("Cracked Soulshale Tile Wall", "裂紋魂頁岩磚瓦牆"),
    "chiseled_soulshale": ("Chiseled Soulshale", "雕紋魂頁岩"),
}
DERIVE = {   # base -> (prefix of the new ids, texture); forms are slab / stairs / wall from polished_deepslate
    "cracked_soulshale_bricks": ("cracked_soulshale_brick", "cracked_soulshale_bricks"),
    "cracked_soulshale_tiles": ("cracked_soulshale_tile", "cracked_soulshale_tiles"),
}
TEMPLATE = "polished_deepslate"
# vanilla tags worth copying: tool, slab / stairs / wall groups (not the worldgen "replaceable" ones deepslate is in)
TAG_KEEP = re.compile(r"/(mineable/|slabs|stairs|walls|stone_crafting_materials|stone_tool_materials)")


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
        out.append("soulshale" if t == "deepslate" else t)
    return "_".join(out)


IDS = {f"minecraft:{p}": f"pysift:{rename(p)}" for p in PARTS} | {"minecraft:cobbled_deepslate": "pysift:soulshale"}
textures, models = {}, {}


# ------------------------------------------------------------------ textures
def hexes(*cs): return [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in cs]


def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


REF = Image.open(TEX / "chiseled_soulshale.png").convert("RGBA")
PALETTE = sorted({REF.getpixel((x, y))[:3] for y in range(16) for x in range(16) if REF.getpixel((x, y))[3]}, key=lum)
assert len(PALETTE) == 6, PALETTE


def shifted(c, dh, dv, ds):
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
    return tuple(round(x * 255) for x in colorsys.hsv_to_rgb((h + dh / 360) % 1, min(0.9, max(0, s + ds)), min(0.95, max(0, v + dv))))


CRACK = shifted(PALETTE[0], +12, -0.07, +0.06)    # darker and cooler (towards blue) than the darkest tone
POLISH = shifted(PALETTE[-1], -12, +0.10, -0.06)  # lighter, warmer (towards green) and a little greyer than the lightest
ANCHORS = [CRACK] + PALETTE + [POLISH]
# vanilla's processed-deepslate greys, one per anchor
VANILLA = hexes("#1a1a1a", "#242424", "#2d2d2d", "#383737", "#414141", "#4b4c4f", "#585858", "#6e6e6e")


def recolour(img):
    """Exact processed greys go to their anchor; any other grey (natural deepslate) to the anchor nearest in brightness,
    never to the same or a darker anchor than the next darker grey, so the texture keeps every step."""
    cols = sorted({img.getpixel((x, y))[:3] for y in range(img.height) for x in range(img.width) if img.getpixel((x, y))[3]}, key=lum)
    picks, last = [], -1
    for c in cols:
        if c in VANILLA:
            i = VANILLA.index(c)
        else:
            i = min(range(len(VANILLA)), key=lambda k: abs(lum(VANILLA[k]) - lum(c)))
        last = max(i, last + 1)
        picks.append(last)
    over = max(0, picks[-1] - (len(ANCHORS) - 1))   # natural deepslate is lighter: slide down so only its top step is POLISH
    table = {c: ANCHORS[max(0, i - over)] for c, i in zip(cols, picks)}
    out = img.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = table[(r, g, b)] + (a,)
    return out


def paint():
    for src in ("deepslate", "deepslate_top", "polished_deepslate", "deepslate_bricks", "cracked_deepslate_bricks",
                "deepslate_tiles", "cracked_deepslate_tiles"):
        img = Image.open(io.BytesIO(CLIENT.read(f"assets/minecraft/textures/block/{src}.png"))).convert("RGBA")
        art_guard.save(recolour(img), TEX / f"{rename(src)}.png")


# ------------------------------------------------------------------ resources (as build_void_stone_family.py)
def is_ours(ref):
    name = ref.split(":", 1)[-1].split("/")[-1]
    return "deepslate" in name


def texture_ref(ref):
    if not ref.startswith("minecraft:block/") or not is_ours(ref):
        return ref
    name = ref.split("/", 1)[1]
    ours = f"pysift:block/soulshale/{rename(name) if name != 'cobbled_deepslate' else 'soulshale'}"
    textures[ours] = ref
    return ours


def model_ref(ref):
    if not ref.startswith("minecraft:block/") or not is_ours(ref):
        return ref
    name = ref.split("/", 1)[1]
    if name == "cobbled_deepslate":               # the cobbled slab's double slab: the full soulshale block
        return "pysift:block/soulshale/soulshale"
    ours = "pysift:block/" + rename(name)
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


def add_tags(vanilla_id, ours):
    for n in COMMON.namelist():
        if not (n.startswith("data/minecraft/tags/") and n.endswith(".json")) or not TAG_KEEP.search(n):
            continue
        if vanilla_id in jar_json(COMMON, n)["values"]:
            path = D / "minecraft/tags" / n[len("data/minecraft/tags/"):]
            data = lj(path) if path.exists() else {"replace": False, "values": []}
            if ours not in data["values"]:
                data["values"].append(ours)
            wj(path, data)


def derive():
    made = []
    for base, (prefix, tex) in DERIVE.items():
        def sub(obj, key=None):
            if isinstance(obj, dict):
                return {k: sub(v, k) for k, v in obj.items()}
            if isinstance(obj, list):
                return [sub(v, key) for v in obj]
            if isinstance(obj, str):
                if obj == f"minecraft:block/{TEMPLATE}" and key not in ("model", "parent"):
                    return f"pysift:block/soulshale/{tex}"
                if obj == f"minecraft:block/{TEMPLATE}":
                    return f"pysift:block/{base}"
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
        for f in ("slab", "stairs", "wall"):
            part, ours = f"{TEMPLATE}_{f}", f"{prefix}_{f}"
            made.append(ours)
            for kind in ("blockstates", "items"):
                wj(A / f"{kind}/{ours}.json", sub(jar_json(CLIENT, f"assets/minecraft/{kind}/{part}.json")))
            for n in CLIENT.namelist():
                m = re.fullmatch(rf"assets/minecraft/models/block/({part}[a-z_]*)\.json", n)
                if m:
                    wj(A / f"models/block/{prefix}_{f}{m[1][len(part):]}.json", sub(jar_json(CLIENT, n)))
            for n in (part, f"{part}_from_{TEMPLATE}_stonecutting"):
                wj(D / ("pysift/recipe/" + ours + ("" if n == part else f"_from_{base}_stonecutting") + ".json"),
                   sub(jar_json(COMMON, f"data/minecraft/recipe/{n}.json")))
            table = sub(jar_json(COMMON, f"data/minecraft/loot_table/blocks/{part}.json"))
            for d in ("loot_table", "loot_tables"):
                wj(D / f"pysift/{d}/blocks/{ours}.json", table)
            add_tags(f"minecraft:{part}", f"pysift:{ours}")
    return made


def main():
    paint()
    for name in PARTS:
        for kind in ("blockstates", "items"):
            wj(A / f"{kind}/{rename(name)}.json", rewrite(jar_json(CLIENT, f"assets/minecraft/{kind}/{name}.json")))
    done = set()
    while set(models) - done:
        for ours in sorted(set(models) - done):
            done.add(ours)
            path = models[ours].split(":", 1)[1]
            wj(A / f"models/{ours.split(':', 1)[1]}.json", rewrite(jar_json(CLIENT, f"assets/minecraft/models/{path}.json")))
    # recipes whose result is one of the parts; ingredient == result (cobbled -> deepslate smelting) is dropped
    recipes, skipped = 0, []
    results = {f"minecraft:{p}" for p in PARTS}
    for n in COMMON.namelist():
        m = re.fullmatch(r"data/minecraft/recipe/([a-z_]+)\.json", n)
        if not m:
            continue
        recipe = jar_json(COMMON, n)
        result = recipe.get("result", {})
        if (result.get("id") if isinstance(result, dict) else result) not in results:
            continue
        out = rewrite(recipe)
        text = json.dumps(out)
        if re.search(r'"minecraft:[a-z_]*deepslate', text) or out.get("ingredient") == out.get("result", {}).get("id"):
            skipped.append(m[1])
            continue
        wj(D / f"pysift/recipe/{rename(m[1])}.json", out)
        recipes += 1
    # soulshale itself: abyssal strata steeped in souls
    wj(D / "pysift/recipe/soulshale.json", {"type": "minecraft:crafting_shaped", "category": "building",
        "pattern": ["SSS", "SXS", "SSS"],
        "key": {"S": "pysift:abyssal_strata", "X": ["minecraft:soul_sand", "minecraft:soul_soil"]},
        "result": {"id": "pysift:soulshale", "count": 8}})
    for name in PARTS:
        table = rewrite(jar_json(COMMON, f"data/minecraft/loot_table/blocks/{name}.json"))
        for d in ("loot_table", "loot_tables"):
            wj(D / f"pysift/{d}/blocks/{rename(name)}.json", table)
        add_tags(f"minecraft:{name}", f"pysift:{rename(name)}")
    add_tags("minecraft:cobbled_deepslate", "pysift:soulshale")
    motion = D / "minecraft/tags/block/blocks_motion_no_leaves.json"
    data = lj(motion)
    data["values"] += [f"pysift:{rename(p)}" for p in FULL if f"pysift:{rename(p)}" not in data["values"]]
    wj(motion, data)
    print("derived:", derive())
    for code in ("en_us", "zh_tw"):
        f = A / f"lang/{code}.json"
        raw = f.read_bytes().decode("utf-8-sig")
        lang = json.loads(raw)
        for bid, (en, zh) in NAMES.items():
            lang[f"block.pysift.{bid}"] = en if code == "en_us" else zh
            lang[f"item.pysift.{bid}"] = lang[f"block.pysift.{bid}"]   # block items read item.* in 26.3
        lang["tooltip.pysift.chiseled_soulshale"] = ("Plays one of the eight notes when placed" if code == "en_us"
                                                     else "放下時會響起八個音的其中一個")
        out = json.dumps(lang, ensure_ascii=False, indent=2)
        if "\r\n" in raw:
            out = out.replace("\n", "\r\n")
        f.write_bytes((out + ("\r\n" if raw.endswith("\n") else "")).encode("utf-8"))
    missing = [t for t in textures if not (A / "textures" / (t.split(":", 1)[1] + ".png")).exists()]
    print(f"{len(PARTS)} blocks, {len(models)} models, {len(textures)} textures, {recipes} recipes")
    print("palette:", ["#%02x%02x%02x" % c for c in ANCHORS])
    if skipped:
        print("recipes skipped:", skipped)
    if missing:
        print("MISSING textures:", missing)
    import subprocess
    subprocess.run([sys.executable, "-I", str(P / "tools/texture_pipeline/group_models.py"), str(P)], check=True)


if __name__ == "__main__":
    main()
