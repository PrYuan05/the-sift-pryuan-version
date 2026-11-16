"""Generate every resource of the soul willow wood set (SoulWillowWood.java) by copying vanilla oak and rewriting it.
Usage: python -I tools/worldgen/build_soul_willow_wood.py <project> [--retexture]

Vanilla 26.3 assets / data are read from the Loom cache jars (nothing vanilla is edited):
  blockstates, block / item models, item definitions  <- minecraft-clientOnly jar (oak_* files)
  recipes, loot tables, tags, axe block transformer   <- minecraft-common jar
Every "minecraft:oak_*" id becomes "pysift:soul_willow_*"; "#minecraft:oak_logs" becomes "#pysift:soul_willow_logs".
Textures: each vanilla oak texture the copied models use is recoloured onto a colour ramp taken from the soul willow
log textures (log_ramp) and saved under textures/block/soul_willow/, textures/item/, textures/entity/(chest_)boat/,
textures/gui/(hanging_)signs/. Existing PNGs are kept (real art can replace them) unless --retexture is given.
The soul willow log itself stays in ModVegetation / build_vegetation.py; oak_log textures map onto its own textures.
Stripping (axe) is data driven in 26.3: data/minecraft/block_transformer/axe.json = vanilla + the soul willow rules."""
import bisect, colorsys, copy, io, json, re, sys
import zipfile
from pathlib import Path
from PIL import Image

P = Path(sys.argv[1])
RETEXTURE = "--retexture" in sys.argv
RES = P / "src/main/resources"
A, D = RES / "assets/pysift", RES / "data"
CACHE = P / ".gradle/loom-cache/minecraftMaven/net/minecraft"
CLIENT = zipfile.ZipFile(next(CACHE.glob("minecraft-clientOnly-*/26.3/minecraft-clientOnly-*-26.3.jar")))
COMMON = zipfile.ZipFile(next(CACHE.glob("minecraft-common-*/26.3/minecraft-common-*-26.3.jar")))

WOOD = "soul_willow"
# vanilla oak name -> ours. oak_log is the existing ModVegetation log (assets made by build_vegetation.py).
PARTS = ["oak_planks", "oak_wood", "stripped_oak_log", "stripped_oak_wood", "oak_slab", "oak_stairs", "oak_fence",
         "oak_fence_gate", "oak_door", "oak_trapdoor", "oak_pressure_plate", "oak_button", "oak_sign", "oak_wall_sign",
         "oak_hanging_sign", "oak_wall_hanging_sign", "oak_shelf", "oak_boat", "oak_chest_boat"]
rename = lambda name: name.replace("oak", WOOD)
IDS = {f"minecraft:{n}": f"pysift:{rename(n)}" for n in PARTS + ["oak_log"]}
IDS["#minecraft:oak_logs"] = f"#pysift:{WOOD}_logs"
LOG_TEXTURES = {"minecraft:block/oak_log": "pysift:block/vegetation/soul_willow_log_side",
                "minecraft:block/oak_log_top": "pysift:block/vegetation/soul_willow_log_top"}
SKIP_TAGS = {"block/overworld_natural_logs.json"}      # vanilla overworld generation only
NAMES = {  # ours -> (en_us, zh_tw)
    "soul_willow_wood": ("Soul Willow Wood", "靈魂柳木頭"),
    "stripped_soul_willow_log": ("Stripped Soul Willow Log", "去皮靈魂柳原木"),
    "stripped_soul_willow_wood": ("Stripped Soul Willow Wood", "去皮靈魂柳木頭"),
    "soul_willow_planks": ("Soul Willow Planks", "靈魂柳木材"),
    "soul_willow_slab": ("Soul Willow Slab", "靈魂柳木半磚"),
    "soul_willow_stairs": ("Soul Willow Stairs", "靈魂柳木階梯"),
    "soul_willow_fence": ("Soul Willow Fence", "靈魂柳木柵欄"),
    "soul_willow_fence_gate": ("Soul Willow Fence Gate", "靈魂柳木柵欄門"),
    "soul_willow_door": ("Soul Willow Door", "靈魂柳木門"),
    "soul_willow_trapdoor": ("Soul Willow Trapdoor", "靈魂柳木活板門"),
    "soul_willow_pressure_plate": ("Soul Willow Pressure Plate", "靈魂柳木壓力板"),
    "soul_willow_button": ("Soul Willow Button", "靈魂柳木按鈕"),
    "soul_willow_sign": ("Soul Willow Sign", "靈魂柳木告示牌"),
    "soul_willow_hanging_sign": ("Soul Willow Hanging Sign", "靈魂柳木懸掛式告示牌"),
    "soul_willow_shelf": ("Soul Willow Shelf", "靈魂柳木層架"),
    "soul_willow_boat": ("Soul Willow Boat", "靈魂柳木船"),
    "soul_willow_chest_boat": ("Soul Willow Boat with Chest", "附儲物箱的靈魂柳木船"),
}
RAMP_STEPS = 7
LIGHTEN = 0.12  # added to each shade's HLS lightness, hue and saturation kept (user: wood a little paler than the log)
LOG_TEXTURE_FILES = [A / "textures/block/vegetation/soul_willow_log_side.png",
                     A / "textures/block/vegetation/soul_willow_log_top.png"]


def lj(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jar_json(jar, name): return json.loads(jar.read(name))


textures = {}   # our texture ref -> vanilla texture ref
models = {}     # our model ref -> vanilla model ref


def texture_ref(ref):
    if ref in LOG_TEXTURES:
        return LOG_TEXTURES[ref]
    if not ref.startswith("minecraft:") or "oak" not in ref:
        return ref
    kind, name = ref.split(":", 1)[1].split("/", 1)
    ours = f"pysift:{kind}/{WOOD}/{rename(name)}" if kind == "block" else f"pysift:{kind}/{rename(name)}"
    textures[ours] = ref
    return ours


def model_ref(ref):
    if not ref.startswith("minecraft:") or "oak" not in ref:
        return ref
    ours = "pysift:" + rename(ref.split(":", 1)[1])
    models[ours] = ref
    return ours


def rewrite(obj, key=None):
    """Rename oak ids everywhere; texture maps and model / parent references get their own rules."""
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
        if obj.startswith("minecraft:blocks/") and obj.split("/", 1)[1] in PARTS:   # loot random_sequence
            return f"pysift:blocks/{rename(obj.split('/', 1)[1])}"
    return obj


# ---- assets: blockstates, item definitions, models (followed recursively) ----
for name in PARTS:
    ours = rename(name)
    for kind in ("blockstates", "items"):
        src = f"assets/minecraft/{kind}/{name}.json"
        if src in CLIENT.namelist():
            wj(A / f"{kind}/{ours}.json", rewrite(jar_json(CLIENT, src)))
done = set()
while set(models) - done:
    for ours in sorted(set(models) - done):
        done.add(ours)
        path = models[ours].split(":", 1)[1]
        wj(A / f"models/{ours.split(':', 1)[1]}.json", rewrite(jar_json(CLIENT, f"assets/minecraft/models/{path}.json")))

# ---- textures: vanilla oak recoloured onto the iron-grey ramp ----
ENTITY = {f"pysift:entity/boat/{WOOD}": "minecraft:entity/boat/oak",
          f"pysift:entity/chest_boat/{WOOD}": "minecraft:entity/chest_boat/oak",
          f"pysift:gui/signs/{WOOD}": "minecraft:gui/signs/oak",
          f"pysift:gui/hanging_signs/{WOOD}": "minecraft:gui/hanging_signs/oak"}


def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def log_ramp():
    """Colour ramp (dark -> light) taken from the soul willow log textures: all opaque pixels sorted by brightness,
    split into RAMP_STEPS equal-count groups, each averaged. Rerun with --retexture after the log art changes."""
    px = [c[:3] for f in LOG_TEXTURE_FILES for c in Image.open(f).convert("RGBA").get_flattened_data() if c[3] > 0]
    px.sort(key=lum)
    ramp = []
    for i in range(RAMP_STEPS):
        group = px[i * len(px) // RAMP_STEPS:(i + 1) * len(px) // RAMP_STEPS]
        avg = [sum(c[k] for c in group) / len(group) / 255 for k in range(3)]
        h, l, sat = colorsys.rgb_to_hls(*avg)
        ramp.append(tuple(round(v * 255) for v in colorsys.hls_to_rgb(h, min(1.0, l + LIGHTEN), sat)))
    return ramp


RAMP = log_ramp()


def recolor(img):
    img = img.convert("RGBA")
    px = list(img.get_flattened_data())
    ls = sorted(lum(c) for c in px if c[3] > 0)
    out = []
    for c in px:
        if c[3] == 0:
            out.append(c)
            continue
        rank = bisect.bisect_left(ls, lum(c)) / max(1, len(ls))   # brightness rank keeps the grain contrast
        out.append((*RAMP[min(len(RAMP) - 1, int(rank * len(RAMP)))], c[3]))
    res = Image.new("RGBA", img.size)
    res.putdata(out)
    return res


written = 0
for ours, vanilla in {**textures, **ENTITY}.items():
    dst = A / "textures" / (ours.split(":", 1)[1] + ".png")
    if dst.exists() and not RETEXTURE:
        continue
    src = "assets/minecraft/textures/" + vanilla.split(":", 1)[1] + ".png"
    dst.parent.mkdir(parents=True, exist_ok=True)
    recolor(Image.open(io.BytesIO(CLIENT.read(src)))).save(dst)
    meta = src + ".mcmeta"
    if meta in CLIENT.namelist():
        dst.with_suffix(".png.mcmeta").write_bytes(CLIENT.read(meta))
    written += 1

# ---- data: recipes, loot tables ----
recipes = [n for n in COMMON.namelist() if re.fullmatch(r"data/minecraft/recipe/(stripped_)?oak_[a-z_]+\.json", n)
           and Path(n).stem in PARTS]
for n in recipes:
    wj(D / f"pysift/recipe/{rename(Path(n).stem)}.json", rewrite(jar_json(COMMON, n)))
for name in PARTS:
    src = f"data/minecraft/loot_table/blocks/{name}.json"
    if src in COMMON.namelist():
        table = rewrite(jar_json(COMMON, src))
        for d in ("loot_table", "loot_tables"):
            wj(D / f"pysift/{d}/blocks/{rename(name)}.json", table)

# ---- tags: wherever vanilla lists an oak part (or #oak_logs), list ours too ----
tag_count = 0
for n in COMMON.namelist():
    if not (n.startswith("data/minecraft/tags/") and n.endswith(".json")):
        continue
    rel = n[len("data/minecraft/tags/"):]
    if rel in SKIP_TAGS or rel.endswith("/oak_logs.json"):
        continue
    add = [IDS[v] for v in jar_json(COMMON, n)["values"] if isinstance(v, str) and v in IDS]
    if not add:
        continue
    path = D / "minecraft/tags" / rel
    data = lj(path) if path.exists() else {"replace": False, "values": []}
    data["values"] += [v for v in add if v not in data["values"]]
    wj(path, data)
    tag_count += 1
LOGS = [f"pysift:{WOOD}_log", f"pysift:{WOOD}_wood", f"pysift:stripped_{WOOD}_log", f"pysift:stripped_{WOOD}_wood"]
for kind in ("block", "item"):
    wj(D / f"pysift/tags/{kind}/{WOOD}_logs.json", {"replace": False, "values": LOGS})

# ---- axe stripping: vanilla transformer + a copy of the oak rules for the soul willow ----
axe = jar_json(COMMON, "data/minecraft/block_transformer/axe.json")
added = 0
for entry in axe:
    rules = entry.get("block_state_provider", {}).get("rules", [])
    for i, rule in enumerate(list(rules)):
        blocks = rule.get("if_true", {}).get("blocks")
        if blocks in ("minecraft:oak_log", "minecraft:oak_wood"):
            rules.insert(rules.index(rule) + 1, rewrite(copy.deepcopy(rule)))
            added += 1
assert added == 2, f"expected the oak log + wood strip rules, found {added}"
wj(D / "minecraft/block_transformer/axe.json", axe)

# ---- lang (merge: other tools write these files too) ----
for i, lang in enumerate(("en_us", "zh_tw")):
    lf = A / f"lang/{lang}.json"
    d = lj(lf)
    for name, pair in NAMES.items():
        d[f"block.pysift.{name}"] = pair[i]
        d[f"item.pysift.{name}"] = pair[i]
    for boat in ("soul_willow_boat", "soul_willow_chest_boat"):
        d.pop(f"block.pysift.{boat}", None)
        d[f"entity.pysift.{boat}"] = NAMES[boat][i]
    wj(lf, d)

print("ramp from the log:", " ".join("#%02x%02x%02x" % c for c in RAMP))
print(f"{len(PARTS)} parts, {len(models)} models, {len(textures) + len(ENTITY)} textures ({written} written), "
      f"{len(recipes)} recipes, {tag_count} vanilla tags, axe strip rules +{added}")
