"""Red sculk (ModVegetation RED_SCULK, RED_SCULK_VEIN): living sculk of The Sift (lore 4.7 - healthy sculk is red,
it rots to the vanilla blue sculk without spirit liquid).
Usage: python -I tools/worldgen/build_red_sculk.py <project>

Textures reuse the vanilla sculk / sculk_vein frames and animation (texture skill, method C) and take their colours
from the mod's own swatches: the body from the rose dye's red-pink ramp, the glowing specks from the spirit liquid pinks. Block states, models, item models,
loot (silk touch, like vanilla sculk), tags and names are written too."""
import colorsys, io, json, sys, zipfile
from pathlib import Path

from PIL import Image

P = Path(sys.argv[1])
sys.path.insert(0, str(P / "tools"))
import art_guard

A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
JAR = next((P / ".gradle/loom-cache/minecraftMaven/net/minecraft").glob("minecraft-clientOnly-*/26.3/*.jar"))
VANILLA = zipfile.ZipFile(JAR)


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def hexes(*codes):
    return [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in codes]


# the mod's own palettes (user: follow the mod's pink and red-pink swatches)
#   body  = the rose dye's red-pink ramp (item/rose_dye.png), extended two steps darker because sculk is mostly shadow
#   glow  = the spirit liquid / magma vein slate vein 3 pinks: what glows in sculk is soul, the same colour as the liquid
BODY = hexes("#1c0610", "#2c0a19", "#360c1f", "#450e26", "#5c1430", "#731c3a", "#8c2444", "#a32e4d")   # #360c1f: a micro step between the two vanilla shadow greys
GLOW = hexes("#450e26", "#731c3a", "#a32e4d", "#c94fb8", "#e66aa8", "#ee7b91")   # dim specks stay rose, mid ones spirit pink, the brightest warm to the rose dye's light pink (hue shift)


# vanilla sculk / sculk_vein colour -> ours, one by one, so the steps between tones stay as gentle as vanilla's
# (shadow greys -> the rose ramp's dark end, teal outlines -> rose, cyan glow -> spirit pink, brightest -> rose light)
EXACT = {   # user: lighter, fewer colour jumps, then lighter and pinker after ember stone (#e67788 / #f87f8c)
    "#0d1217": "#8a3a5e", "#111b21": "#742e63", "#0b212a": "#9b4462", "#052a32": "#a84a66", "#194648": "#b4506b",
    "#034150": "#bd566e", "#05625d": "#cc6276", "#009295": "#e67788", "#29dfeb": "#fbb0a8",
    # shadows lean cool (333 deg), the glow is ember stone's coral pink, the brightest warms to peach (+20 deg);
    # #742e63 is a cooler, darker shadow under the base so the block keeps its contrast
}
EXACT = {tuple(int(k[i:i + 2], 16) for i in (1, 3, 5)): tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in EXACT.items()}


def redden(img):
    """Recolour by brightness (texture skill, method C) so the structure and animation frames stay exactly vanilla:
    the grey-teal shadows (saturation < 0.6) go onto BODY, the saturated teal / cyan specks onto GLOW - both by value,
    so a dim speck stays dim rose and only the brightest ones reach the spirit pinks."""
    out = img.copy()
    px = out.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            if (r, g, b) in EXACT:
                px[x, y] = EXACT[(r, g, b)] + (a,)
                continue
            h, s_, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)   # any colour not in the table: by value
            ramp, top = (GLOW, 0.92) if s_ >= 0.6 else (BODY, 0.45)
            px[x, y] = ramp[min(len(ramp) - 1, round(v / top * (len(ramp) - 1)))] + (a,)
    return out


T = A / "textures/block"
for name in ("sculk", "sculk_vein"):
    src = Image.open(io.BytesIO(VANILLA.read(f"assets/minecraft/textures/block/{name}.png"))).convert("RGBA")
    dst = T / f"red_{name}/red_{name}.png"
    if art_guard.save(redden(src), dst):
        (dst.parent / f"red_{name}.png.mcmeta").write_bytes(VANILLA.read(f"assets/minecraft/textures/block/{name}.png.mcmeta"))

# ---- red_sculk: a plain cube
wj(A / "blockstates/red_sculk.json", {"variants": {"": {"model": "pysift:block/red_sculk/red_sculk"}}})
wj(A / "models/block/red_sculk/red_sculk.json", {"parent": "minecraft:block/cube_all",
                                                  "textures": {"all": "pysift:block/red_sculk/red_sculk"}})
wj(A / "models/item/red_sculk.json", {"parent": "pysift:block/red_sculk/red_sculk"})
wj(A / "items/red_sculk.json", {"model": {"type": "minecraft:model", "model": "pysift:item/red_sculk"}})

# ---- red_sculk_vein: the vanilla sculk_vein multipart with our model
vein_model = "pysift:block/red_sculk_vein/red_sculk_vein"
vanilla_state = json.loads(VANILLA.read("assets/minecraft/blockstates/sculk_vein.json"))
for part in vanilla_state["multipart"]:
    part["apply"]["model"] = vein_model
wj(A / "blockstates/red_sculk_vein.json", vanilla_state)
wj(A / "models/block/red_sculk_vein/red_sculk_vein.json", {
    "ambientocclusion": False,
    "textures": {"particle": "pysift:block/red_sculk_vein/red_sculk_vein", "sculk_vein": "pysift:block/red_sculk_vein/red_sculk_vein"},
    "elements": [{"from": [0, 0, 0.1], "to": [16, 16, 0.1], "faces": {
        "north": {"uv": [16, 0, 0, 16], "texture": "#sculk_vein"}, "south": {"uv": [0, 0, 16, 16], "texture": "#sculk_vein"}}}]})
wj(A / "models/item/red_sculk_vein.json", {"parent": "minecraft:item/generated",
                                            "textures": {"layer0": "pysift:block/red_sculk_vein/red_sculk_vein"}})
wj(A / "items/red_sculk_vein.json", {"model": {"type": "minecraft:model", "model": "pysift:item/red_sculk_vein"}})

# ---- loot: like vanilla sculk, only with silk touch
for name in ("red_sculk", "red_sculk_vein"):
    loot = {"type": "minecraft:block", "random_sequence": f"pysift:blocks/{name}", "pools": [{
        "rolls": 1, "condition": "minecraft:tool/can_silk_touch",
        "entries": [{"type": "minecraft:item", "name": f"pysift:{name}"}]}]}
    for folder in ("loot_table", "loot_tables"):
        wj(D / f"pysift/{folder}/blocks/{name}.json", loot)


def add_tag(path, values):
    values = [v for v in values if v.startswith("#") or not v.startswith("pysift:")
              or (A / f"blockstates/{v.split(':')[1]}.json").exists()]   # a missing id would break the whole tag
    f = D / path
    tag = json.loads(f.read_text(encoding="utf-8-sig")) if f.exists() else {"replace": False, "values": []}
    tag["values"] += [v for v in values if v not in tag["values"]]
    wj(f, tag)


add_tag("minecraft/tags/block/mineable/hoe.json", ["pysift:red_sculk", "pysift:red_sculk_vein"])
add_tag("minecraft/tags/block/blocks_motion_no_leaves.json", ["pysift:red_sculk"])
# the ground red sculk patches may grow over (vegetation_patch, build_the_sift.py) and rifts rot (WildRiftFeature)
add_tag("pysift/tags/block/red_sculk_replaceable.json", [
    "#minecraft:sculk_replaceable", "pysift:violet_capped_dark_slate", "pysift:dark_slate", "pysift:capped_crimson_vein_stone",
    "pysift:crimson_vein_stone", "pysift:grove_capped_crimson_strata", "pysift:abyssal_strata", "pysift:canyon_capped_crimson_strata",
    "pysift:silted_strata", "pysift:capped_crimson_strata", "pysift:ember_basalt", "pysift:crimson_capped_void_stone",
    "pysift:gray_capped_void_stone", "pysift:rusted_dark_cobble", "pysift:amber_sand", "pysift:pale_sand",
    # underground layers (v2.1.0): the cave floors of the withered hollows, resonant vaults and spirit deeps
    "pysift:void_stone", "pysift:gray_strata", "pysift:polished_void_stone", "pysift:smooth_void_stone",
    "pysift:magma_vein_slate"])

NAMES = {"block.pysift.red_sculk": ("Red Sculk", "赤紅幽匿"), "block.pysift.red_sculk_vein": ("Red Sculk Vein", "赤紅幽匿脈絡")}
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    raw = f.read_bytes().decode("utf-8-sig")
    data = json.loads(raw)
    for k, v in NAMES.items():
        data[k] = v[i]
        data["item" + k[len("block"):]] = v[i]
    out = json.dumps(data, ensure_ascii=False, indent=2)
    if "\r\n" in raw:
        out = out.replace("\n", "\r\n")
    f.write_bytes((out + ("\r\n" if raw.endswith("\n") else "")).encode("utf-8"))
print("red sculk: blocks, textures, loot, tags, names")
