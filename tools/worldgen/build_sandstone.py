"""Every resource of the sandstone families (SandstoneFamily.java), copied from vanilla sandstone and rewritten.
Usage: python -I tools/worldgen/build_sandstone.py <project> [--preview]

For each sand in SANDS (ModBlocks amber_sand / pale_sand), every vanilla sandstone part is copied from the Loom cache jars
(nothing vanilla is edited) and "minecraft:sandstone" becomes "pysift:<colour>_sandstone" (cut_, chiseled_, smooth_ and the
slab / stairs / wall forms the same way); "minecraft:sand" in the recipes becomes the matching pysift sand.
  blockstates, block / item models, item definitions  <- minecraft-clientOnly jar
  recipes (crafting, smelting, stonecutting), loot tables, tags  <- minecraft-common jar
Textures: each vanilla sandstone texture is moved onto that sand's average colour (every pixel keeps its light / dark and
hue offset from the texture's average, so the layering and the carving stay as drawn; see recolor) and saved under
textures/block/<colour>_sandstone/. Written through
tools/art_guard.py, so a texture the user has redrawn is kept. --preview only writes build/previews/sandstone.png.
"""
import colorsys, io, json, re, sys, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
PREVIEW = "--preview" in sys.argv
RES = P / "src/main/resources"
A, D = RES / "assets/pysift", RES / "data"
CACHE = P / ".gradle/loom-cache/minecraftMaven/net/minecraft"
CLIENT = zipfile.ZipFile(next(CACHE.glob("minecraft-clientOnly-*/26.3/minecraft-clientOnly-*-26.3.jar")))
COMMON = zipfile.ZipFile(next(CACHE.glob("minecraft-common-*/26.3/minecraft-common-*-26.3.jar")))
sys.path.insert(0, str(P / "tools"))
import art_guard

# colour -> (sand block, en name, zh name)
SANDS = {"amber": ("amber_sand", "Amber", "琥珀"), "pale": ("pale_sand", "Pale", "淺")}
PARTS = ["sandstone", "chiseled_sandstone", "cut_sandstone", "smooth_sandstone", "sandstone_slab", "sandstone_stairs",
         "sandstone_wall", "cut_sandstone_slab", "smooth_sandstone_slab", "smooth_sandstone_stairs"]
PART_NAMES = {  # vanilla part -> (en pattern, zh pattern); {c} = colour name
    "sandstone": ("{c} Sandstone", "{c}砂岩"),
    "chiseled_sandstone": ("Chiseled {c} Sandstone", "雕紋{c}砂岩"),
    "cut_sandstone": ("Cut {c} Sandstone", "切製{c}砂岩"),
    "smooth_sandstone": ("Smooth {c} Sandstone", "平滑{c}砂岩"),
    "sandstone_slab": ("{c} Sandstone Slab", "{c}砂岩半磚"),
    "sandstone_stairs": ("{c} Sandstone Stairs", "{c}砂岩階梯"),
    "sandstone_wall": ("{c} Sandstone Wall", "{c}砂岩牆"),
    "cut_sandstone_slab": ("Cut {c} Sandstone Slab", "切製{c}砂岩半磚"),
    "smooth_sandstone_slab": ("Smooth {c} Sandstone Slab", "平滑{c}砂岩半磚"),
    "smooth_sandstone_stairs": ("Smooth {c} Sandstone Stairs", "平滑{c}砂岩階梯"),
}
CONTRAST = 1.15   # vanilla light / dark differences are kept and stretched this much (the layering, the carving)


def lj(p): return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def wj(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def jar_json(jar, name): return json.loads(jar.read(name))


def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def sand_colour(sand):
    """Average colour of the sand texture (HLS)."""
    px = [c[:3] for c in Image.open(A / f"textures/block/{sand}/{sand}.png").convert("RGBA").get_flattened_data() if c[3] > 0]
    return colorsys.rgb_to_hls(*(sum(c[k] for c in px) / len(px) / 255 for k in range(3)))


def recolor(img, target):
    """Move the vanilla texture onto the sand colour: every pixel keeps its offset from the texture's average lightness
    (times CONTRAST), its relative saturation and its small hue offset, so the layering and the carving stay exactly
    as drawn; only the overall hue / saturation / lightness becomes the sand's."""
    img = img.convert("RGBA")
    px = list(img.get_flattened_data())
    hls = [colorsys.rgb_to_hls(*(v / 255 for v in c[:3])) if c[3] > 0 else None for c in px]
    opaque = [x for x in hls if x]
    mh = sum(x[0] for x in opaque) / len(opaque)
    ml = sum(x[1] for x in opaque) / len(opaque)
    ms = sum(x[2] for x in opaque) / len(opaque) or 1
    th, tl, ts = target
    out = []
    for c, x in zip(px, hls):
        if x is None:
            out.append(c)
            continue
        h, l, sat = x
        rgb = colorsys.hls_to_rgb((th + (h - mh)) % 1.0, min(1.0, max(0.0, tl + (l - ml) * CONTRAST)), min(1.0, ts * sat / ms))
        out.append(tuple(round(v * 255) for v in rgb) + (c[3],))
    res = Image.new("RGBA", img.size)
    res.putdata(out)
    return res


def is_part(name): return name in PARTS


class Family:
    def __init__(self, colour):
        self.c = colour
        self.sand = SANDS[colour][0]
        self.ids = {f"minecraft:{p}": f"pysift:{self.rename(p)}" for p in PARTS}
        self.ids["minecraft:sand"] = f"pysift:{self.sand}"
        self.textures, self.models = {}, {}

    def rename(self, name): return name.replace("sandstone", f"{self.c}_sandstone")

    def texture_ref(self, ref):
        if not ref.startswith("minecraft:block/") or "sandstone" not in ref or "red_sandstone" in ref:
            return ref
        name = ref.split("/", 1)[1]
        ours = f"pysift:block/{self.c}_sandstone/{self.rename(name)}"
        self.textures[ours] = ref
        return ours

    def model_ref(self, ref):
        if not ref.startswith("minecraft:") or "sandstone" not in ref or "red_sandstone" in ref:
            return ref
        ours = "pysift:" + self.rename(ref.split(":", 1)[1])
        self.models[ours] = ref
        return ours

    def rewrite(self, obj, key=None):
        if isinstance(obj, dict):
            if key == "textures":
                return {k: self.texture_ref(v) if isinstance(v, str) and not v.startswith("#") else v for k, v in obj.items()}
            return {k: self.rewrite(v, k) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.rewrite(v, key) for v in obj]
        if isinstance(obj, str):
            if key in ("model", "parent", "base"):
                return self.model_ref(obj)
            if obj in self.ids:
                return self.ids[obj]
            if obj.startswith("minecraft:blocks/") and is_part(obj.split("/", 1)[1]):   # loot random_sequence
                return f"pysift:blocks/{self.rename(obj.split('/', 1)[1])}"
        return obj

    def build(self):
        for name in PARTS:
            for kind in ("blockstates", "items"):
                src = f"assets/minecraft/{kind}/{name}.json"
                wj(A / f"{kind}/{self.rename(name)}.json", self.rewrite(jar_json(CLIENT, src)))
        done = set()
        while set(self.models) - done:
            for ours in sorted(set(self.models) - done):
                done.add(ours)
                path = self.models[ours].split(":", 1)[1]
                wj(A / f"models/{ours.split(':', 1)[1]}.json", self.rewrite(jar_json(CLIENT, f"assets/minecraft/models/{path}.json")))
        target = sand_colour(self.sand)
        for ours, vanilla in self.textures.items():
            src = "assets/minecraft/textures/" + vanilla.split(":", 1)[1] + ".png"
            art_guard.save(recolor(Image.open(io.BytesIO(CLIENT.read(src))), target), A / "textures" / (ours.split(":", 1)[1] + ".png"))
        # recipes: every vanilla recipe whose result is one of the parts (crafting, smelting, stonecutting)
        recipes = 0
        for n in COMMON.namelist():
            m = re.fullmatch(r"data/minecraft/recipe/([a-z_]+)\.json", n)
            if not m or "sandstone" not in m[1] or "red_sandstone" in m[1]:
                continue
            recipe = jar_json(COMMON, n)
            result = recipe.get("result", {})
            if (result.get("id") if isinstance(result, dict) else result) not in self.ids:
                continue
            wj(D / f"pysift/recipe/{self.rename(m[1])}.json", self.rewrite(recipe))
            recipes += 1
        for name in PARTS:
            table = self.rewrite(jar_json(COMMON, f"data/minecraft/loot_table/blocks/{name}.json"))
            for d in ("loot_table", "loot_tables"):
                wj(D / f"pysift/{d}/blocks/{self.rename(name)}.json", table)
        # tags: wherever vanilla lists a sandstone part, list ours too
        tags = 0
        for n in COMMON.namelist():
            if not (n.startswith("data/minecraft/tags/") and n.endswith(".json")) or "/worldgen/" in n:
                continue
            add = [self.ids[v] for v in jar_json(COMMON, n)["values"] if isinstance(v, str) and v in self.ids and v != "minecraft:sand"]
            if not add:
                continue
            path = D / "minecraft/tags" / n[len("data/minecraft/tags/"):]
            data = lj(path) if path.exists() else {"replace": False, "values": []}
            data["values"] += [v for v in add if v not in data["values"]]
            wj(path, data)
            tags += 1
        return recipes, tags


def preview():
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
    names = ["sandstone_top", "sandstone", "sandstone_bottom", "cut_sandstone", "chiseled_sandstone"]
    S = 80
    img = Image.new("RGB", (130 + len(names) * (S + 8), 3 * (S + 24) + 10), (30, 30, 36))
    d = ImageDraw.Draw(img)
    rows = [("原版", None)] + [(SANDS[c][2] + "砂岩", sand_colour(SANDS[c][0])) for c in SANDS]
    for r, (label, target) in enumerate(rows):
        y = 8 + r * (S + 24)
        d.text((8, y + S // 2 - 8), label, fill=(230, 230, 230), font=f)
        for k, n in enumerate(names):
            im = Image.open(io.BytesIO(CLIENT.read(f"assets/minecraft/textures/block/{n}.png")))
            im = recolor(im, target) if target else im.convert("RGBA")
            img.paste(im.convert("RGB").resize((S, S), Image.NEAREST), (130 + k * (S + 8), y))
            if r == 0:
                d.text((130 + k * (S + 8), y + S + 2), n, fill=(170, 200, 255), font=f)
    out = P / "build/previews/sandstone.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print("preview:", out.relative_to(P))


def main():
    if PREVIEW:
        preview()
        return
    lang = {"en_us": lj(A / "lang/en_us.json"), "zh_tw": lj(A / "lang/zh_tw.json")}
    for colour, (sand, en, zh) in SANDS.items():
        fam = Family(colour)
        recipes, tags = fam.build()
        for part, (en_pat, zh_pat) in PART_NAMES.items():
            for key in ("block", "item"):
                lang["en_us"][f"{key}.pysift.{fam.rename(part)}"] = en_pat.format(c=en)
                lang["zh_tw"][f"{key}.pysift.{fam.rename(part)}"] = zh_pat.format(c=zh)
        print(f"{colour}: {len(PARTS)} blocks, {len(fam.models)} models, {len(fam.textures)} textures, {recipes} recipes, {tags} tags")
    for code, d in lang.items():
        wj(A / f"lang/{code}.json", d)


if __name__ == "__main__":
    main()
