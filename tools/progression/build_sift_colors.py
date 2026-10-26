"""Resources for the 9 new Sift colours (SiftColors.java): dye items and 12 coloured blocks per colour.
Usage: python -I tools/progression/build_sift_colors.py <project>

Every file is derived from vanilla's WHITE version (read from the Loom cache jars), with minecraft:white_<kind> swapped
for pysift:<colour>_<kind> and minecraft:white_dye for pysift:<colour>_dye, so recipes, loot (slabs drop 2, glass needs
silk touch), recipe unlocks and tags behave exactly like vanilla. Models keep vanilla's white textures (nothing is copied):
each vanilla parent is flattened into a pysift:block/sift_colors/template/* copy whose faces carry tintindex 0, and the
block / item is tinted with the colour (block: SiftColorsClient, item: "tints" in items/*.json).
Hand-drawn art replaces the tinted vanilla texture automatically: put textures/block/sift_colors/<colour>_<kind>.png
(e.g. teal_glazed_terracotta.png, teal_wool.png - slabs / stairs / carpet follow their full block) or
textures/item/<colour>_dye.png and run this script again; those use the drawing as-is, without tint.
Colours must match SiftColors.SiftColor in Java."""
import json, re, sys, zipfile
from pathlib import Path

P = Path(sys.argv[1])
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
LOOM = Path.home() / ".gradle/caches/fabric-loom/26.3"
CLIENT = zipfile.ZipFile(LOOM / "minecraft-client-only.jar")
COMMON = zipfile.ZipFile(LOOM / "minecraft-common.jar")

COLOURS = {   # id: (0xRRGGBB, English, 繁中) - same order and values as SiftColors.SiftColor
    "teal": (0x2EB8A6, "Teal", "青碧"),
    "mint": (0x8FE3C0, "Mint", "薄荷"),
    "coral": (0xF08A6C, "Coral", "珊瑚"),
    "amber": (0xE8A33A, "Amber", "琥珀"),
    "lavender": (0xB39DDB, "Lavender", "薰衣草"),
    "rose": (0xD9536E, "Crimson Rose", "赤紅玫瑰"),
    "soul_blue": (0x8EC5F0, "Soul Blue", "靈魂藍"),
    "void": (0x3A2E48, "Void", "虛黑"),
    "dusk_gold": (0xF2CF6B, "Dusk Gold", "暮光金"),
}
KINDS = {   # kind: (English, 繁中)
    "wool": ("Wool", "羊毛"), "wool_slab": ("Wool Slab", "羊毛半磚"), "wool_stairs": ("Wool Stairs", "羊毛階梯"),
    "carpet": ("Carpet", "地毯"),
    "concrete": ("Concrete", "混凝土"), "concrete_slab": ("Concrete Slab", "混凝土半磚"),
    "concrete_stairs": ("Concrete Stairs", "混凝土階梯"), "concrete_powder": ("Concrete Powder", "混凝土粉末"),
    "terracotta": ("Terracotta", "陶土"), "glazed_terracotta": ("Glazed Terracotta", "彩繪陶瓦"),
    "stained_glass": ("Stained Glass", "染色玻璃"), "stained_glass_pane": ("Stained Glass Pane", "染色玻璃片"),
    "candle": ("Candle", "蠟燭"), "candle_cake": ("Candle Cake", "蠟燭蛋糕"),
}
NO_ITEM = {"candle_cake"}       # you get it by putting the candle on a cake
NOT_SOLID = {"carpet", "candle", "candle_cake"}          # everything else goes into #blocks_motion_no_leaves (CLAUDE.md)
VANILLA_COLOURS = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "light_gray", "cyan",
                   "purple", "blue", "brown", "green", "red", "black"]


def jr(z, name):
    return json.loads(z.read(name).decode("utf-8"))


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def argb(rgb):
    v = 0xFF000000 | rgb
    return v - (1 << 32)          # signed int, like vanilla items/lily_pad.json


def swap(obj, colour):
    """minecraft:white_<kind> -> pysift:<colour>_<kind>, minecraft:white_dye -> pysift:<colour>_dye (strings, recursively)."""
    text = json.dumps(obj)
    text = text.replace('"minecraft:white_dye"', f'"pysift:{colour}_dye"')
    for kind in sorted(KINDS, key=len, reverse=True):
        text = re.sub(rf'"(minecraft:)?white_{kind}"', f'"pysift:{colour}_{kind}"', text)
    return json.loads(text)


# ------------------------------------------------------------------ tinted templates (flattened vanilla parents)
TEMPLATES = {}


def model_json(ref):
    ns, path = ref.split(":", 1) if ":" in ref else ("minecraft", ref)
    return jr(CLIENT, f"assets/{ns}/models/{path}.json")


def tinted_template(parent):
    """Flatten `parent` (and its parents) into a model with tintindex 0 on every face; returns its id."""
    if parent in TEMPLATES:
        return TEMPLATES[parent]
    chain, ref = [], parent
    while ref and not ref.endswith("block/block") and not ref.endswith("block/thin_block"):
        m = model_json(ref)
        chain.append(m)
        ref = m.get("parent")
    out = {"parent": ref or "minecraft:block/block"}
    textures = {}
    for m in reversed(chain):                       # parents first, children override
        textures.update(m.get("textures", {}))
        for key in ("ambientocclusion", "display", "elements", "gui_light"):
            if key in m:
                out[key] = m[key]
    out["textures"] = textures
    for el in out.get("elements", []):
        for face in el.get("faces", {}).values():
            face["tintindex"] = 0
    name = "pysift:block/sift_colors/template/" + parent.split("/")[-1]
    wj(A / "models/block/sift_colors/template" / (parent.split("/")[-1] + ".json"), out)
    TEMPLATES[parent] = name
    return name


def custom_texture(ref, colour):
    """Hand-drawn replacement for a vanilla white texture, if the user put one in textures/block/sift_colors/:
    minecraft:block/white_<x> -> pysift:block/sift_colors/<colour>_<x> (e.g. teal_glazed_terracotta.png). None if absent."""
    m = re.fullmatch(r"minecraft:block/white_([a-z_]+)", ref)
    if m and (A / f"textures/block/sift_colors/{colour}_{m.group(1)}.png").exists():
        return f"pysift:block/sift_colors/{colour}_{m.group(1)}"
    m = re.fullmatch(r"minecraft:item/white_([a-z_]+)", ref)          # item sprites (the candle): <colour>_item_<x>.png
    if m and (A / f"textures/block/sift_colors/{colour}_item_{m.group(1)}.png").exists():
        return f"pysift:block/sift_colors/{colour}_item_{m.group(1)}"
    return None


def colour_model(vanilla_ref, colour):
    """pysift:block/sift_colors/<colour>_<rest>: vanilla white model's textures on the tinted copy of its parent.
    If the user drew the texture (custom_texture), the model uses that drawing on vanilla's own (untinted) parent."""
    m = model_json(vanilla_ref)
    rest = vanilla_ref.split("/")[-1].replace("white_", "", 1)
    name = f"{colour}_{rest}"
    textures, drawn = {}, False
    for key, tex in m.get("textures", {}).items():
        sprite = tex.get("sprite") if isinstance(tex, dict) else tex
        own = custom_texture(sprite, colour) if isinstance(sprite, str) else None
        drawn = drawn or own is not None
        textures[key] = ({**tex, "sprite": own} if isinstance(tex, dict) else own) if own else tex
    out = {"parent": m["parent"] if drawn else tinted_template(m["parent"]), "textures": textures}
    wj(A / f"models/block/sift_colors/{name}.json", out)
    if drawn:
        DRAWN.add(f"pysift:block/sift_colors/{name}")
    return f"pysift:block/sift_colors/{name}"


DRAWN = set()   # pysift model ids that use the user's drawings (those must not be tinted)


def item_model(vanilla_ref, colour):
    """Vanilla item model (e.g. item/white_stained_glass_pane): if its sprite has a drawing, our own copy using it."""
    m = model_json(vanilla_ref)
    textures = {k: custom_texture(v, colour) or v for k, v in m.get("textures", {}).items() if isinstance(v, str)}
    if textures == m.get("textures", {}):
        return vanilla_ref
    name = f"{colour}_" + vanilla_ref.split("/")[-1].replace("white_", "", 1)
    wj(A / f"models/item/sift_colors/{name}.json", {"parent": m["parent"], "textures": textures})
    DRAWN.add(f"pysift:item/sift_colors/{name}")
    return f"pysift:item/sift_colors/{name}"


def remap_models(obj, colour):
    if isinstance(obj, dict):
        def one(k, v):
            if k == "model" and isinstance(v, str) and "block/white_" in v:
                return colour_model(v, colour)
            if k == "model" and isinstance(v, str) and "item/white_" in v:
                return item_model(v, colour)
            return remap_models(v, colour)
        return {k: one(k, v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [remap_models(v, colour) for v in obj]
    return obj


def add_tint(obj, rgb):
    if isinstance(obj, dict):
        if obj.get("type") == "minecraft:model":
            obj = {**obj, "tints": [{"type": "minecraft:constant", "value": argb(rgb)}]}
        return {k: add_tint(v, rgb) for k, v in obj.items()}
    if isinstance(obj, list):
        return [add_tint(v, rgb) for v in obj]
    return obj


lang = {}
for colour, (rgb, en, zh) in COLOURS.items():
    # dye item: vanilla white dye sprite, tinted - or the user's drawing at textures/item/<colour>_dye.png (not tinted)
    if (A / f"textures/item/{colour}_dye.png").exists():
        wj(A / f"models/item/{colour}_dye.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"pysift:item/{colour}_dye"}})
        wj(A / f"items/{colour}_dye.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{colour}_dye"}})
    else:
        wj(A / f"items/{colour}_dye.json", add_tint(jr(CLIENT, "assets/minecraft/items/white_dye.json"), rgb))
    lang[f"item.pysift.{colour}_dye"] = (f"{en} Dye", f"{zh}色染料")
    for kind, (ken, kzh) in KINDS.items():
        bs = jr(CLIENT, f"assets/minecraft/blockstates/white_{kind}.json")
        wj(A / f"blockstates/{colour}_{kind}.json", remap_models(bs, colour))
        if kind in NO_ITEM:
            lang[f"block.pysift.{colour}_{kind}"] = (f"{en} {ken}", f"{zh}色{kzh}")
            continue
        item = remap_models(jr(CLIENT, f"assets/minecraft/items/white_{kind}.json"), colour)
        drawn = any(f'"{ref}"' in json.dumps(item) for ref in DRAWN)
        wj(A / f"items/{colour}_{kind}.json", item if drawn else add_tint(item, rgb))   # a drawn texture is not tinted
        for prefix in ("block", "item"):
            lang[f"{prefix}.pysift.{colour}_{kind}"] = (f"{en} {ken}", f"{zh}色{kzh}")

# ------------------------------------------------------------------ data: loot, recipes, recipe unlocks, tags
names = COMMON.namelist()
for colour in COLOURS:
    for kind in KINDS:
        loot = swap(jr(COMMON, f"data/minecraft/loot_table/blocks/white_{kind}.json"), colour)
        loot["random_sequence"] = f"pysift:blocks/{colour}_{kind}"
        for folder in ("loot_table", "loot_tables"):
            wj(D / f"pysift/{folder}/blocks/{colour}_{kind}.json", loot)
# recipes: every vanilla recipe that makes a white <kind> (except dye-less dyeing like dye_white_bed)
RECIPES = [n for n in names if re.fullmatch(r"data/minecraft/recipe/(dye_)?white_(" + "|".join(KINDS) + r")(_from_[a-z_]+)?\.json", n)]
RECIPES = [n for n in RECIPES if not n.endswith("_from_string.json")]   # string makes white wool only
# (no clean-up pass: colour prefixes like amber_ / void_ also start other blocks' recipes; files are overwritten by name)
for colour in COLOURS:
    others = [c for c in COLOURS if c != colour]
    for n in RECIPES:
        stem = Path(n).stem
        out = swap(jr(COMMON, n), colour)
        if stem.startswith("dye_"):
            # dyeing (after the swap, so vanilla white stays white): all 16 vanilla colours + the other Sift colours
            kind = stem[len("dye_white_"):]
            out["ingredients"][1] = [f"minecraft:{v}_{kind}" for v in VANILLA_COLOURS] + [f"pysift:{c}_{kind}" for c in others]
        out_name = stem.replace("white_", f"{colour}_")
        wj(D / f"pysift/recipe/{out_name}.json", out)
        adv = [m for m in names if m.startswith("data/minecraft/advancement/recipes/") and m.endswith(f"/{stem}.json")]
        if adv:
            a = swap(jr(COMMON, adv[0]), colour)
            text = json.dumps(a).replace(f'"minecraft:{stem}"', f'"pysift:{out_name}"')
            folder = adv[0].split("/")[-2]
            wj(D / f"pysift/advancement/recipes/{folder}/{out_name}.json", json.loads(text))
# leather armour, wolf armour: SiftDyeRecipe (pysift:crafting_sift_dye)
wj(D / "pysift/recipe/sift_dye_armor.json", {"type": "pysift:crafting_sift_dye"})

# tags: wherever vanilla lists minecraft:white_<kind> directly, list ours too (wool, slabs, stairs, mineable, ...)
ours_for = {f"minecraft:white_{k}": [f"pysift:{c}_{k}" for c in COLOURS] for k in KINDS}
for n in names:
    if not re.match(r"data/minecraft/tags/(block|item)/.+\.json$", n):
        continue
    values = jr(COMMON, n).get("values", [])
    add = [o for v in values if isinstance(v, str) and v in ours_for for o in ours_for[v]]
    if not add:
        continue
    f = D / n.split("data/", 1)[1]
    cur = json.loads(f.read_text(encoding="utf-8-sig")) if f.exists() else {"replace": False, "values": []}
    cur["values"] = cur["values"] + [a for a in add if a not in cur["values"]]
    wj(f, cur)
motion = D / "minecraft/tags/block/blocks_motion_no_leaves.json"
cur = json.loads(motion.read_text(encoding="utf-8-sig"))
cur["values"] += [f"pysift:{c}_{k}" for c in COLOURS for k in KINDS if k not in NOT_SOLID and f"pysift:{c}_{k}" not in cur["values"]]
wj(motion, cur)

# ------------------------------------------------------------------ lang (merge, keep the file's line endings)
for code, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{code}.json"
    raw = f.read_bytes().decode("utf-8-sig")
    data = json.loads(raw)
    for k, v in lang.items():
        data[k] = v[i]
    out = json.dumps(data, ensure_ascii=False, indent=2)
    if "\r\n" in raw:
        out = out.replace("\n", "\r\n")
    f.write_bytes((out + ("\r\n" if raw.endswith("\n") else "")).encode("utf-8"))
print(f"{len(COLOURS)} colours x {len(KINDS)} blocks, {len(TEMPLATES)} tinted templates, {len(RECIPES)} recipe kinds")
