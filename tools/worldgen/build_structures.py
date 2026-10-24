"""Phase 2 world content: one small structure per biome of The Sift, with loot chests.
Usage: python -I tools/worldgen/build_structures.py <project>
Writes data/pysift/structure/<name>.nbt (gzipped structure templates, written by a tiny NBT writer below),
worldgen/structure, worldgen/template_pool, worldgen/structure_set, tags/worldgen/biome/has_structure/<name>.json,
loot_table/chests/<name>.json, and build/texture_pipeline/out/structures_preview.png (layer views).

| structure        | biome                  | what it is                                                        |
| strata_shrine    | crimson_strata_canyon  | ruined ring of crimson-brick pillars around an altar with a chest |
| abyss_obelisk    | violet_slate_abyss     | dark-slate obelisk crowned with a soul crystal, chest in the plinth|
| willow_hut       | willow_grove           | soul-willow hut on stilts with a chest and lantern                |
| dune_tomb        | amber_dunes            | half-buried sandstone tomb, ladder down, sarcophagus and 2 chests |
Ruin damage is random but seeded, so re-running gives the same templates."""
import gzip, io, json, random, struct, sys
from pathlib import Path

P = Path(sys.argv[1])
D = P / "src/main/resources/data/pysift"
A = P / "src/main/resources/assets/pysift"
DATA_VERSION = 5023          # Minecraft 26.3 world_version (version.json in the client jar)


# ------------------------------------------------------------------ tiny NBT writer
def _s(text):
    b = text.encode("utf-8")
    return struct.pack(">H", len(b)) + b


def _payload(tag, value):
    if tag == 3:
        return struct.pack(">i", value)
    if tag == 8:
        return _s(value)
    if tag == 10:
        out = b""
        for k, (t, v) in value.items():
            out += bytes([t]) + _s(k) + _payload(t, v)
        return out + b"\x00"
    if tag == 9:
        elem_tag, items = value
        return bytes([elem_tag]) + struct.pack(">i", len(items)) + b"".join(_payload(elem_tag, i) for i in items)
    raise ValueError(tag)


def nbt_file(root):
    raw = b"\x0a" + _s("") + _payload(10, root)
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(raw)
    return buf.getvalue()


def compound(d):
    """Plain dict -> typed NBT compound (str -> string, int -> int, dict -> compound)."""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[k] = (10, compound(v))
        elif isinstance(v, int):
            out[k] = (3, v)
        else:
            out[k] = (8, str(v))
    return out


# ------------------------------------------------------------------ template builder
class Template:
    def __init__(self, w, h, d, seed):
        self.size = (w, h, d)
        self.blocks = {}                                     # (x, y, z) -> (name, props, nbt)
        self.rnd = random.Random(seed)

    def set(self, x, y, z, name, nbt=None, **props):
        if 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]:
            if not name.startswith("minecraft:"):
                name = "pysift:" + name
            assert name.startswith("minecraft:") or (A / "blockstates" / f"{name.split(':')[1]}.json").exists(), name
            self.blocks[(x, y, z)] = (name, {k: str(v).lower() for k, v in props.items()}, nbt)

    def get(self, x, y, z):
        return self.blocks.get((x, y, z), (None,))[0]

    def chest(self, x, y, z, loot, facing="south"):
        self.set(x, y, z, "minecraft:chest", {"id": "minecraft:chest", "LootTable": f"pysift:chests/{loot}"}, facing=facing)

    def to_nbt(self):
        palette, index = [], {}
        blocks = []
        for (x, y, z), (name, props, nbt) in sorted(self.blocks.items()):
            key = (name, tuple(sorted(props.items())))
            if key not in index:
                index[key] = len(palette)
                entry = {"id": (8, name)}                     # 26.3 palette entries: "id" / "properties" (no longer Name / Properties)
                if props:
                    entry["properties"] = (10, {k: (8, v) for k, v in props.items()})
                palette.append(entry)
            b = {"pos": (9, (3, [x, y, z])), "state": (3, index[key])}
            if nbt:
                b["nbt"] = (10, compound(nbt))
            blocks.append(b)
        return nbt_file({"DataVersion": (3, DATA_VERSION), "size": (9, (3, list(self.size))),
                         "palette": (9, (10, palette)), "blocks": (9, (10, blocks)), "entities": (9, (10, []))})


# ------------------------------------------------------------------ designs
def strata_shrine():
    """11x8x11: cracked crimson-brick floor disc, 8 broken pillars, central altar with the chest, ember braziers."""
    t = Template(11, 8, 11, 101)
    c = 5
    for x in range(11):
        for z in range(11):
            r2 = (x - c) ** 2 + (z - c) ** 2
            if r2 <= 25 and t.rnd.random() > 0.08:            # floor with a few gaps
                t.set(x, 0, z, "ember_stone" if t.rnd.random() < 0.15 else "crimson_strata_bricks")
            if r2 <= 25:
                for y in range(1, 8):
                    t.set(x, y, z, "minecraft:air")            # clear grass / plants inside the ring
    pillars = [(c + 4, c), (c - 4, c), (c, c + 4), (c, c - 4), (c + 3, c + 3), (c - 3, c - 3), (c + 3, c - 3), (c - 3, c + 3)]
    for px, pz in pillars:
        height = t.rnd.randint(2, 6)
        for y in range(1, height + 1):
            t.set(px, y, pz, "chiseled_crimson_strata_bricks" if y == 1 else "crimson_strata_bricks")
        if height >= 4:
            t.set(px, height + 1, pz, "crimson_strata_brick_slab", type="bottom")
        elif t.rnd.random() < 0.6:                            # fallen rubble next to short pillars
            t.set(px + t.rnd.choice((-1, 1)), 1, pz, "crimson_strata_brick_slab", type="bottom")
    for dx in (-1, 0, 1):                                      # altar
        for dz in (-1, 0, 1):
            t.set(c + dx, 1, c + dz, "chiseled_crimson_strata_bricks")
    for (dx, dz, facing) in ((0, -2, "south"), (0, 2, "north"), (-2, 0, "east"), (2, 0, "west")):
        t.set(c + dx, 1, c + dz, "crimson_strata_brick_stairs", facing=facing, half="bottom", shape="straight")
    t.chest(c, 2, c, "strata_shrine")
    for dx, dz in ((-1, -1), (1, 1)):                          # glowing braziers
        t.set(c + dx, 2, c + dz, "ember_stone", heat=4)
    return t


def abyss_obelisk():
    """9x13x9: slate plinth, obelisk of dark slate pillar with a soul crystal crown, corner posts, chest in front."""
    t = Template(9, 13, 9, 202)
    c = 4
    for x in range(9):
        for z in range(9):
            corruption = t.rnd.choice((0, 0, 1, 2))
            t.set(x, 0, z, "corrupted_slate_bricks", corruption=corruption)
            for y in range(1, 13):
                t.set(x, y, z, "minecraft:air")
    for x in range(1, 8):
        for z in range(1, 8):
            t.set(x, 1, z, "dark_slate_bricks" if (x + z) % 3 else "chiseled_dark_slate_bricks")
    for y in range(2, 11):
        t.set(c, y, c, "dark_slate_pillar", axis="y")
    t.set(c, 11, c, "soul_crystal_block")
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):          # base buttresses
        t.set(c + dx, 2, c + dz, "dark_slate_bricks")
        t.set(c + dx, 3, c + dz, "dark_slate_bricks")
    for px, pz in ((1, 1), (7, 7), (1, 7), (7, 1)):
        h = t.rnd.randint(2, 3)
        for y in range(2, 2 + h):
            t.set(px, y, pz, "dark_slate_pillar", axis="y")
        t.set(px, 2 + h, pz, "soul_crystal_block")
    t.chest(c, 2, c + 2, "abyss_obelisk", facing="south")
    return t


def willow_hut():
    """9x11x11: soul-willow hut on 3-block stilts, stairs up to the door, slab roof, chest + lantern inside."""
    t = Template(9, 11, 11, 303)
    x0, x1, z0, z1 = 1, 7, 1, 7                                # 7x7 room
    floor = 3
    for x in range(9):
        for z in range(11):
            for y in range(0, 11):
                t.set(x, y, z, "minecraft:air")
    for px, pz in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        for y in range(0, floor + 4):
            t.set(px, y, pz, "soul_willow_log", axis="y")
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            t.set(x, floor, z, "soul_willow_planks")
            if x in (x0, x1) or z in (z0, z1):
                for y in range(floor + 1, floor + 4):
                    if t.get(x, y, z) is None or t.get(x, y, z) == "minecraft:air":
                        t.set(x, y, z, "soul_willow_planks")
    for x in (3, 5):                                           # windows
        t.set(x, floor + 2, z0, "minecraft:air")
        t.set(x, floor + 2, z1, "minecraft:air")
    t.set(x0, floor + 2, 4, "minecraft:air")
    t.set(x1, floor + 2, 4, "minecraft:air")
    t.set(4, floor + 1, z1, "minecraft:air")                   # door gap (south side)
    t.set(4, floor + 2, z1, "minecraft:air")
    for i, z in enumerate((z1 + 1, z1 + 2, z1 + 3)):           # stairs down to the ground
        t.set(4, floor - i, z, "soul_willow_stairs", facing="north", half="bottom", shape="straight")
    for x in range(0, 9):                                      # roof: slab skirt, plank layer, slab cap
        for z in range(0, 9):
            t.set(x, floor + 4, z, "soul_willow_slab", type="bottom")
    for x in range(2, 7):
        for z in range(2, 7):
            t.set(x, floor + 5, z, "soul_willow_planks")
    for x in range(3, 6):
        for z in range(3, 6):
            t.set(x, floor + 6, z, "soul_willow_slab", type="bottom")
    t.chest(2, floor + 1, 2, "willow_hut", facing="south")
    t.set(6, floor + 1, 2, "minecraft:crafting_table")
    t.set(6, floor + 1, 6, "minecraft:soul_lantern", hanging="false")
    return t


def dune_tomb():
    """11x8x11 (sunk 5 blocks into the sand): sandstone-brick room, roof hatch with a ladder, sarcophagus, two chests."""
    t = Template(11, 8, 11, 404)
    for x in range(11):
        for z in range(11):
            for y in range(8):
                shell = x in (0, 10) or z in (0, 10) or y in (0, 6)
                if y == 7:
                    if 2 <= x <= 8 and 2 <= z <= 8 and (x in (2, 8) or z in (2, 8)):
                        t.set(x, y, z, "bleached_sandstone_brick_slab", type="bottom")     # low parapet above the sand
                    continue
                if shell:
                    name = "chiseled_bleached_sandstone_bricks" if y in (0, 6) and (x + z) % 4 == 0 else "bleached_sandstone_bricks"
                    if t.rnd.random() < 0.12:
                        name = "cracked_sandstone"
                    t.set(x, y, z, name, **({"crack": t.rnd.randint(0, 3)} if name == "cracked_sandstone" else {}))
                else:
                    t.set(x, y, z, "minecraft:air")
    for y in range(1, 7):                                      # roof hatch + ladder down the north wall
        t.set(5, y, 1, "minecraft:ladder", facing="south")
    t.set(5, 6, 1, "minecraft:air")
    t.set(5, 7, 1, "minecraft:air")
    t.set(5, 6, 2, "minecraft:air")
    for x in range(4, 7):                                      # sarcophagus
        t.set(x, 1, 6, "chiseled_bleached_sandstone_bricks")
        t.set(x, 2, 6, "bleached_sandstone_brick_slab", type="bottom")
    t.chest(2, 1, 8, "dune_tomb", facing="north")
    t.chest(8, 1, 8, "dune_tomb", facing="north")
    for x, z in ((2, 2), (8, 2)):
        t.set(x, 1, z, "minecraft:soul_lantern", hanging="false")
    for x in (1, 9):                                           # cobwebs in the corners
        t.set(x, 5, 9, "minecraft:cobweb")
    return t


# ------------------------------------------------------------------ registry JSON
STRUCTURES = {   # name: (design, biome, terrain adaptation, start height offset, spacing, separation, salt)
    "strata_shrine": (strata_shrine, "crimson_strata_canyon", "beard_thin", 0, 26, 8, 70531001),
    "abyss_obelisk": (abyss_obelisk, "violet_slate_abyss", "beard_thin", 0, 28, 9, 70531002),
    "willow_hut": (willow_hut, "willow_grove", "beard_thin", 0, 24, 8, 70531003),
    "dune_tomb": (dune_tomb, "amber_dunes", "bury", -5, 30, 10, 70531004),
}


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


previews = []
for name, (design, biome, adaptation, start_y, spacing, separation, salt) in STRUCTURES.items():
    t = design()
    (D / "structure").mkdir(parents=True, exist_ok=True)
    (D / f"structure/{name}.nbt").write_bytes(t.to_nbt())
    wj(D / f"worldgen/template_pool/{name}.json", {"fallback": "minecraft:empty", "elements": [{"weight": 1, "element": {
        "element_type": "minecraft:single_pool_element", "location": f"pysift:{name}",
        "processors": "minecraft:empty", "projection": "rigid"}}]})
    wj(D / f"worldgen/structure/{name}.json", {
        "type": "minecraft:jigsaw", "biomes": f"#pysift:has_structure/{name}", "max_distance_from_center": 80,
        "project_start_to_heightmap": "WORLD_SURFACE_WG", "size": 1, "spawn_overrides": {},
        "start_height": {"absolute": start_y}, "start_pool": f"pysift:{name}", "step": "surface_structures",
        "terrain_adaptation": adaptation, "use_expansion_hack": False})
    wj(D / f"worldgen/structure_set/{name}.json", {
        "placement": {"type": "minecraft:random_spread", "salt": salt, "separation": separation, "spacing": spacing},
        "structures": [{"structure": f"pysift:{name}", "weight": 1}]})
    wj(D / f"tags/worldgen/biome/has_structure/{name}.json", {"values": [f"pysift:{biome}"]})
    previews.append((name, t))


# ------------------------------------------------------------------ chest loot
def item(name, weight, lo=1, hi=1):
    e = {"type": "minecraft:item", "name": name, "weight": weight}
    if hi > 1:
        e["modifier"] = [{"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
    return e


COMMON = [item("minecraft:bread", 15, 1, 3), item("minecraft:iron_ingot", 12, 1, 4), item("minecraft:gold_ingot", 8, 1, 3),
          item("minecraft:bone", 10, 1, 4), item("minecraft:arrow", 8, 2, 8), item("pysift:gloomcap", 8, 1, 3),
          item("pysift:soul_berries", 8, 1, 3), item("pysift:soul_essence", 10, 1, 3), item("pysift:raw_siftite", 10, 1, 3),
          item("pysift:charoite", 8, 1, 3)]
RARE = [item("pysift:siftite_ingot", 20, 1, 3), item("pysift:soul_antidote", 15), item("minecraft:echo_shard", 10, 1, 2),
        item("pysift:summoning_sigil", 6), item("minecraft:diamond", 6, 1, 2), item("pysift:spirit_liquid_bucket", 8),
        item("pysift:soulite_upgrade_smithing_template", 3),
        {"type": "minecraft:empty", "weight": 25}]          # often no rare item at all
EXTRA = {   # per-structure flavour
    "strata_shrine": [item("pysift:fuse_powder", 10, 1, 4), item("pysift:ember_stone", 8, 2, 6)],
    "abyss_obelisk": [item("pysift:soul_crystal_block", 6, 1, 2), item("minecraft:amethyst_shard", 10, 2, 6)],
    "willow_hut": [item("pysift:soul_willow_sapling", 12, 1, 2), item("pysift:soul_willow_planks", 10, 4, 12)],
    "dune_tomb": [item("minecraft:gold_ingot", 12, 2, 5), item("minecraft:emerald", 8, 1, 3)],
}
for name in STRUCTURES:
    data = {"type": "minecraft:chest", "random_sequence": f"pysift:chests/{name}", "pools": [
        {"rolls": {"type": "minecraft:uniform", "min": 4, "max": 7}, "entries": COMMON + EXTRA[name]},
        {"rolls": {"type": "minecraft:uniform", "min": 1, "max": 2}, "entries": RARE}]}
    for folder in ("loot_table", "loot_tables"):
        wj(D / f"{folder}/chests/{name}.json", data)


# ------------------------------------------------------------------ preview: side elevation + top view of each template
try:
    from PIL import Image, ImageDraw
    COLOURS = {"crimson": (176, 70, 82), "ember": (214, 120, 60), "slate": (70, 66, 86), "corrupted": (90, 60, 100),
               "soul_crystal": (120, 240, 230), "willow": (120, 140, 150), "sandstone": (226, 210, 170), "cracked": (180, 150, 120),
               "chest": (160, 110, 40), "lantern": (120, 230, 255), "ladder": (150, 110, 60), "crafting": (150, 100, 60),
               "cobweb": (230, 230, 230)}

    def colour(name):
        for k, c in COLOURS.items():
            if k in name:
                return c
        return (140, 140, 140)

    S = 10
    sheet_w = sum((t.size[0] + t.size[2] + 3) * S + 20 for _, t in previews) + 20
    sheet_h = max(max(t.size[1], t.size[2]) for _, t in previews) * S + 50
    img = Image.new("RGB", (sheet_w, sheet_h), (34, 32, 40))
    d = ImageDraw.Draw(img)
    ox = 20
    for name, t in previews:
        w, h, dep = t.size
        d.text((ox, 6), name, fill=(240, 240, 240))
        for x in range(w):                                     # front elevation (looking north, nearest block)
            for y in range(h):
                for z in range(dep - 1, -1, -1):
                    n = t.get(x, y, z)
                    if n and n != "minecraft:air":
                        d.rectangle([ox + x * S, 30 + (h - 1 - y) * S, ox + x * S + S - 1, 30 + (h - y) * S - 1], fill=colour(n))
                        break
        tx = ox + (w + 2) * S
        for x in range(w):                                     # top view (highest block)
            for z in range(dep):
                for y in range(h - 1, -1, -1):
                    n = t.get(x, y, z)
                    if n and n != "minecraft:air":
                        k = 0.5 + 0.5 * y / max(1, h - 1)
                        c = tuple(int(v * k) for v in colour(n))
                        d.rectangle([tx + x * S, 30 + z * S, tx + x * S + S - 1, 30 + z * S + S - 1], fill=c)
                        break
        ox += (w + dep + 3) * S + 20
    out = P / "build/texture_pipeline/out/structures_preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
except ImportError:
    pass
print("structures:", ", ".join(f"{n} ({len(t.blocks)} blocks)" for n, t in previews))
