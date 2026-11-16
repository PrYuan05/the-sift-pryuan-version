"""Render an area of the test server's Sift save: a top view (surface block per column) and two cross-sections
through the centre (along x and along z), plus surface-block counts.

  python -I .claude/skills/sift-terrain/scripts/render_area.py <x> <z> [radius=112] [out_prefix=build/terrain/area]

Run from the project root after `python -I tools/worldgen/devserver.py gen <radius> <wait> <x> <z>` (it reads the saved
region files, so the chunks must be generated and saved). Colours come from COLOURS below (substring match on the block
id, properties included); add entries for the blocks you are checking. Height lines on the sections mark every 10 Y."""
import sys, collections
from pathlib import Path

sys.path.insert(0, "tools/worldgen")
import devserver as ds
from PIL import Image, ImageDraw

X, Z = int(sys.argv[1]), int(sys.argv[2])
R = int(sys.argv[3]) if len(sys.argv) > 3 else 112
OUT = sys.argv[4] if len(sys.argv) > 4 else "build/terrain/area"
Y0, Y1 = 40, 170
PLANTS = ("grass", "fern", "flower", "bloom", "vine", "litter", "carpet", "agave", "stalk", "canopy", "plant", "tuft",
          "sprout", "bush", "puff", "cobweb", "lantern", "leaves", "_log")
# block id (or id[props]) substring -> colour. NOTE: blocks in their DEFAULT state are saved without properties,
# so "bleached_sandstone" (no props) is bleach=0; match the bare id for the default state.
COLOURS = [("red_sculk", (196, 40, 84)), ("minecraft:sculk", (16, 70, 90)), ("ember_basalt", (180, 132, 82)), ("magma_vein_slate", (97, 61, 88)),
           ("rusted_dark_cobble", (120, 84, 60)), ("gray_capped_void_stone", (110, 110, 114)), ("red_sculk_vein", (171, 71, 84)),
           ("crimson_capped_void_stone", (126, 73, 89)), ("ember_stone", (220, 130, 90)), ("soul_crystal", (120, 220, 235)),
           ("aurum_ore[richness=1", (235, 175, 30)), ("aurum_ore", (175, 140, 80)),
           ("bleached_sandstone[bleach=1", (190, 165, 120)), ("bleached_sandstone", (240, 232, 208)),
           ("ash_marble", (150, 152, 160)), ("void_capped", (60, 44, 70)), ("crimson_vein_stone", (176, 70, 92)),
           ("spirit_liquid", (250, 150, 220)), ("crimson_capped", (200, 90, 110)), ("violet_capped", (130, 90, 170)),
           ("amber_sand", (226, 190, 120)), ("pale_sand", (236, 220, 180)), ("dark_slate", (70, 66, 86)),
           ("abyssal_strata", (40, 80, 90)), ("void_stone", (50, 50, 60)), ("sift_portal", (255, 120, 255))]


ASSETS = Path("src/main/resources/assets/pysift")
_tex_cache = {}


def texture_colour(name, faces):
    """Mean colour of the block's real texture (pysift blocks): the blockstate variant matching the saved properties
    (default state = first variant; facing blocks facing=up), its model's first texture among `faces`."""
    if not name.startswith("pysift:"):
        return None
    key = (name, faces)
    if key in _tex_cache:
        return _tex_cache[key]
    import json
    bid, _, props = name[7:].partition("[")
    props = dict(kv.split("=", 1) for kv in props.rstrip("]").split(",") if "=" in kv)
    props.setdefault("facing", "up")
    out = None
    try:
        variants = json.loads((ASSETS / "blockstates" / f"{bid}.json").read_text(encoding="utf-8"))["variants"]
        pick = None
        for k, v in variants.items():
            kv = dict(x.split("=", 1) for x in k.split(",") if "=" in x)
            if all(props.get(a) == b for a, b in kv.items()):
                pick = v
                break
        pick = pick or next(iter(variants.values()))
        model = (pick[0] if isinstance(pick, list) else pick)["model"].split(":", 1)[1]
        tex = json.loads((ASSETS / "models" / f"{model}.json").read_text(encoding="utf-8")).get("textures", {})
        for f in faces:
            t = tex.get(f)
            t = t.get("sprite") if isinstance(t, dict) else t
            if t and not t.startswith("#") and t.startswith("pysift:"):
                im = Image.open(ASSETS / "textures" / f"{t.split(':', 1)[1]}.png").convert("RGBA")
                px = [c[:3] for c in im.get_flattened_data() if c[3] > 128][:256 * 4]
                out = tuple(sum(c[i] for c in px) // len(px) for i in range(3))
                break
    except (OSError, KeyError, StopIteration, ValueError):
        out = None
    _tex_cache[key] = out
    return out


def colour(name, faces=("top", "all", "end", "particle")):
    c = texture_colour(name, faces)                      # the real texture first, so new paint shows in the renders
    if c:
        return c
    for key, c in COLOURS:
        if key in name:
            return c
    return (110, 110, 116)


box = ds.blocks_in_box(X - R, Y0, Z - R, X + R - 1, Y1, Z + R - 1, with_props=True)
top = {}
for (x, y, z), n in box.items():
    if any(p in n for p in PLANTS) or n.endswith("air"):     # cave_air: the open space above lakes and pits
        continue
    if y > top.get((x, z), (-999, ""))[0]:
        top[(x, z)] = (y, n)
Path(OUT).parent.mkdir(parents=True, exist_ok=True)
S = 3
img = Image.new("RGB", (2 * R * S, 2 * R * S), (20, 20, 26))
d = ImageDraw.Draw(img)
for (x, z), (y, n) in top.items():
    k = 0.6 + 0.4 * (y - Y0) / (Y1 - Y0)
    c = tuple(max(0, min(255, int(v * k))) for v in colour(n))
    d.rectangle([(x - X + R) * S, (z - Z + R) * S, (x - X + R) * S + S - 1, (z - Z + R) * S + S - 1], fill=c)
img.save(f"{OUT}_top.png")
S = 3
sections = []
for axis in ("x", "z"):
    im = Image.new("RGB", (2 * R * S, (Y1 - Y0) * S), (24, 26, 34))
    dd = ImageDraw.Draw(im)
    for a in range(-R, R):
        for y in range(Y0, Y1):
            n = box.get((X + a, y, Z) if axis == "x" else (X, y, Z + a))
            if n and not n.endswith("air") and not any(p in n for p in PLANTS):
                dd.rectangle([(a + R) * S, (Y1 - 1 - y) * S, (a + R) * S + S - 1, (Y1 - y) * S - 1], fill=colour(n, ("side", "all", "particle")))
    for yl in range(Y0 - Y0 % 10 + 10, Y1, 10):
        dd.line([(0, (Y1 - 1 - yl) * S), (10, (Y1 - 1 - yl) * S)], fill=(255, 255, 255))
    sections.append(im)
sheet = Image.new("RGB", (sections[0].width, sections[0].height * 2 + 8), (0, 0, 0))
sheet.paste(sections[0], (0, 0))
sheet.paste(sections[1], (0, sections[0].height + 8))
sheet.save(f"{OUT}_sections.png")
counts = collections.Counter(n.split(":")[1] for _, n in top.values())
ys = [y for y, _ in top.values()]
print(f"saved {OUT}_top.png, {OUT}_sections.png; surface y {min(ys)}..{max(ys)}")
print("surface blocks:", counts.most_common(15))
