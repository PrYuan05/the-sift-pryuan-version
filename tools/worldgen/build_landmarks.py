"""Landmarks of The Sift (reference: Minecraft Dungeons II locations, https://minecraft.wiki/w/Dungeons_II:Location).
Usage: python -I tools/worldgen/build_landmarks.py <project>

| what            | Dungeons II location | biome(s)                          | how                                                    |
| echo_den        | The Echo Den         | all Sift biomes, y -36..-16       | jigsaw structure: amphitheatre hub + corridors + rooms |
| humbler_husk    | Humbler Husk         | amber_dunes                       | single-piece structure, half buried; achievement       |
| fossil/*        | Huskland fossils     | amber_dunes                       | feature pysift:surface_fossil (SurfaceFossilFeature)   |
| lullaby_shrine  | Lullaby Hilltop      | canyon, abyss, grove (hill tops)  | feature pysift:lullaby_shrine (LullabyShrineFeature)   |

The templates are drafts drawn here in code. The user edits them in game (/pysift_showcase lays every piece out with a
structure block set to SAVE next to it), saves them, and tools/worldgen/import_structures.py copies the saved files back.
Templates listed in tools/worldgen/art/edited_structures.json are the user's: this script never overwrites them.
Ruin damage is random but seeded, so re-running gives the same templates."""
import gzip, io, json, math, random, struct, sys
from pathlib import Path

P = Path(sys.argv[1])
D = P / "src/main/resources/data/pysift"
A = P / "src/main/resources/assets/pysift"
DATA_VERSION = 5023          # Minecraft 26.3
EDITED = P / "tools/worldgen/art/edited_structures.json"
edited = set(json.loads(EDITED.read_text(encoding="utf-8"))) if EDITED.exists() else set()


# ------------------------------------------------------------------ NBT writer (typed values: (tag, value))
def _s(text):
    b = text.encode("utf-8")
    return struct.pack(">H", len(b)) + b


def _payload(tag, value):
    if tag == 1:
        return struct.pack(">b", value)
    if tag == 3:
        return struct.pack(">i", value)
    if tag == 5:
        return struct.pack(">f", value)
    if tag == 6:
        return struct.pack(">d", value)
    if tag == 8:
        return _s(value)
    if tag == 10:
        return b"".join(bytes([t]) + _s(k) + _payload(t, v) for k, (t, v) in value.items()) + b"\x00"
    if tag == 9:
        elem, items = value
        return bytes([elem if items else 0]) + struct.pack(">i", len(items)) + b"".join(_payload(elem, i) for i in items)
    raise ValueError(tag)


def nbt_file(root):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(b"\x0a" + _s("") + _payload(10, root))
    return buf.getvalue()


def compound(d):
    """dict -> typed compound: str -> string, bool -> byte, int -> int, float -> float, dict -> compound."""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[k] = (10, compound(v))
        elif isinstance(v, bool):
            out[k] = (1, int(v))
        elif isinstance(v, int):
            out[k] = (3, v)
        elif isinstance(v, float):
            out[k] = (5, v)
        elif isinstance(v, list):
            out[k] = (9, (5, v))                       # only float lists (Rotation) are needed
        else:
            out[k] = (8, str(v))
    return out


# ------------------------------------------------------------------ template builder
class Template:
    def __init__(self, w, h, d, seed):
        self.size = (w, h, d)
        self.blocks = {}                                # (x, y, z) -> (name, props, nbt)
        self.entities = []
        self.rnd = random.Random(seed)

    def inside(self, x, y, z):
        return 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]

    def set(self, x, y, z, name, nbt=None, **props):
        if not self.inside(x, y, z):
            return
        if not name.startswith("minecraft:"):
            name = "pysift:" + name
        assert name.startswith("minecraft:") or (A / "blockstates" / f"{name.split(':')[1]}.json").exists(), name
        self.blocks[(x, y, z)] = (name, {k: str(v).lower() for k, v in props.items()}, nbt)

    def air(self, x, y, z):
        self.set(x, y, z, "minecraft:air")

    def fill(self, x0, y0, z0, x1, y1, z1, name, **props):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, name, **props)

    def get(self, x, y, z):
        return self.blocks.get((x, y, z), (None,))[0]

    def chest(self, x, y, z, loot, facing="south"):
        self.set(x, y, z, "minecraft:chest", {"id": "minecraft:chest", "LootTable": f"pysift:chests/{loot}"}, facing=facing)

    def jigsaw(self, x, y, z, facing, name, target, pool, final="minecraft:air"):
        """facing: the side of the piece the connector points out of (north = -z)."""
        self.set(x, y, z, "minecraft:jigsaw", {"id": "minecraft:jigsaw", "name": name, "target": target, "pool": pool,
                                               "final_state": final, "joint": "aligned", "placement_priority": 0,
                                               "selection_priority": 0}, orientation=f"{facing}_up")

    def entity(self, x, y, z, entity_id, yaw=0.0):
        self.entities.append((x + 0.5, float(y), z + 0.5, entity_id, float(yaw)))

    def to_nbt(self):
        palette, index, blocks = [], {}, []
        for (x, y, z), (name, props, nbt) in sorted(self.blocks.items()):
            key = (name, tuple(sorted(props.items())))
            if key not in index:
                index[key] = len(palette)
                entry = {"id": (8, name)}               # 26.3 palette entries: "id" / "properties"
                if props:
                    entry["properties"] = (10, {k: (8, v) for k, v in props.items()})
                palette.append(entry)
            b = {"pos": (9, (3, [x, y, z])), "state": (3, index[key])}
            if nbt:
                b["nbt"] = (10, compound(nbt))
            blocks.append(b)
        entities = [{"pos": (9, (6, [ex, ey, ez])), "blockPos": (9, (3, [int(ex), int(ey), int(ez)])),
                     "nbt": (10, compound({"id": eid, "PersistenceRequired": True, "Rotation": [yaw, 0.0]}))}
                    for ex, ey, ez, eid, yaw in self.entities]
        return nbt_file({"DataVersion": (3, DATA_VERSION), "size": (9, (3, list(self.size))),
                         "palette": (9, (10, palette)), "blocks": (9, (10, blocks)), "entities": (9, (10, entities))})


# ------------------------------------------------------------------ The Echo Den (jigsaw)
# Pieces connect through 5-wide x 5-tall doorways. A connector sits in the doorway's bottom-middle cell on the piece edge.
#   parent exit  : name pysift:den_exit,  target pysift:den_entry, pool = what may come next
#   child entry  : name pysift:den_entry, target pysift:den_exit,  pool minecraft:empty
ENTRY = ("pysift:den_entry", "pysift:den_exit", "minecraft:empty")


def den_exit(pool):
    return ("pysift:den_exit", "pysift:den_entry", pool)


def den_stone(t):
    r = t.rnd.random()
    if r < 0.55:
        return "dark_slate_bricks"
    if r < 0.75:
        return "void_stone_bricks"
    if r < 0.92:
        return "abyssal_strata_bricks"
    return "corrupted_slate_bricks"


def den_floor(t):
    r = t.rnd.random()
    if r < 0.12:
        return "minecraft:sculk"                          # healthy sculk still lives in the Sift
    return "abyssal_strata_bricks" if r < 0.7 else "dark_slate_bricks"


def tube(t, length, w=7, h=7, sculk=0.06):
    """A corridor shell along z: floor y0, walls x0 / x(w-1), ceiling y(h-1), air inside."""
    for z in range(length):
        for x in range(w):
            for y in range(h):
                wall = x in (0, w - 1) or y in (0, h - 1)
                if not wall:
                    t.air(x, y, z)
                elif y == 0:
                    t.set(x, y, z, "minecraft:sculk" if t.rnd.random() < sculk else den_floor(t))
                else:
                    t.set(x, y, z, den_stone(t))


def ribs(t, length, w=7, h=7, every=4):
    """Pillars and a lintel every few blocks, a hanging soul lantern on every other arch."""
    for i, z in enumerate(range(2, length - 1, every)):
        for y in range(1, h - 1):
            t.set(1, y, z, "dark_slate_pillar", axis="y")
            t.set(w - 2, y, z, "dark_slate_pillar", axis="y")
        for x in range(1, w - 1):
            t.set(x, h - 2, z, "dark_slate_bricks")
        if i % 2 == 0:
            t.set(w // 2, h - 3, z, "minecraft:soul_lantern", hanging="true")


def doorway(t, x0, y0, z, axis_x=True):
    """Clear a 5 x 5 opening (x0..x0+4 or z0..z0+4 along the wall), floor below stays."""
    for a in range(5):
        for y in range(y0, y0 + 5):
            if axis_x:
                t.air(x0 + a, y, z)
            else:
                t.air(z, y, x0 + a)


def den_hub():
    """33 x 22 x 33 singing amphitheatre: tiers of seats around a crystal stage, a dome hung with crystals, note blocks
    around the stage, echo golems on the seats; four doorways on the top tier (walk level y4)."""
    t = Template(33, 22, 33, 1101)
    c = 16
    for x in range(33):
        for z in range(33):
            r = math.hypot(x - c, z - c)
            if r > 16.5:
                continue
            dome = 4 + int(round(16 * math.sqrt(max(0.0, 1 - (r / 16.8) ** 2))))
            for y in range(0, 22):
                if y == 0 or r >= 15.2 or y >= dome:
                    if y <= dome + 1:
                        t.set(x, y, z, den_stone(t))
                    continue
                # tiers (solid up to): stage r<4 -> 1; pit r<7 -> 0; seats 7..9 -> 1, 9..11 -> 2, 11..15 -> 3 (top walkway)
                top = 1 if r < 4 else 0 if r < 7 else 1 if r < 9 else 2 if r < 11 else 3
                if y <= top:
                    if y == top and top >= 1 and r >= 7:
                        t.set(x, y, z, "minecraft:sculk" if t.rnd.random() < 0.15 else "ash_marble_bricks")
                    elif y == top and r < 4:
                        t.set(x, y, z, "violet_strata_bricks")
                    else:
                        t.set(x, y, z, "abyssal_strata_bricks")
                else:
                    t.air(x, y, z)
    # floor of the pit
    for x in range(33):
        for z in range(33):
            if math.hypot(x - c, z - c) < 7:
                t.set(x, 0, z, "minecraft:sculk" if t.rnd.random() < 0.3 else "dark_slate_bricks")
    # the stage: a soul crystal column wreathed in charoite, note blocks in a ring around it
    for y in range(2, 6):
        t.set(c, y, c, "soul_crystal_block")
    for dx, dz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
        t.set(c + dx, 2, c + dz, "charoite_cluster", facing="up", waterlogged="false")
        t.set(c + dx, 5, c + dz, "charoite_cluster", facing=f, waterlogged="false")
    t.set(c, 6, c, "charoite_cluster", facing="up", waterlogged="false")
    for i in range(8):
        a = i * math.pi / 4
        x, z = c + round(5.5 * math.cos(a)), c + round(5.5 * math.sin(a))
        t.set(x, 1, z, "minecraft:note_block", note=(i * 3) % 25, instrument="chime")
    # crystals hanging from the dome, lanterns around the walkway
    for i in range(12):
        a = i * math.pi / 6
        x, z = c + round(9 * math.cos(a)), c + round(9 * math.sin(a))
        dome = 4 + int(round(16 * math.sqrt(max(0.0, 1 - (9 / 16.8) ** 2))))
        for y in range(dome - 1 - (i % 3), dome):
            t.set(x, y, z, "soul_crystal_block")
        t.set(x, dome - 2 - (i % 3), z, "charoite_cluster", facing="down", waterlogged="false")
    for i in range(16):
        a = i * math.pi / 8 + math.pi / 16
        x, z = c + round(14.3 * math.cos(a)), c + round(14.3 * math.sin(a))
        t.set(x, 4, z, "minecraft:soul_lantern", hanging="false")
    # four doorways on the top tier, each with its connector on the piece edge
    for (x0, z, along_x, jx, jz, facing) in ((14, 0, True, 16, 0, "north"), (14, 32, True, 16, 32, "south"),
                                             (14, 0, False, 0, 16, "west"), (14, 32, False, 32, 16, "east")):
        for d in range(0, 4):
            zz = z + (d if z == 0 else -d)
            doorway(t, x0, 4, zz, along_x)
            for a in range(5):                     # walkway into the doorway
                if along_x:
                    t.set(x0 + a, 3, zz, "abyssal_strata_bricks")
                else:
                    t.set(zz, 3, x0 + a, "abyssal_strata_bricks")
        t.jigsaw(jx, 4, jz, facing, *den_exit("pysift:echo_den/corridors"))
    # the choir: four echo golems on the seats, facing the stage
    for i, (x, z) in enumerate(((c, c - 10), (c + 10, c), (c, c + 10), (c - 10, c))):
        t.entity(x, 3, z, "pysift:echo_golem", yaw=(0, 90, 180, 270)[i])
    t.chest(c + 2, 2, c, "echo_den", facing="east")
    return t


def den_corridor():
    t = Template(7, 7, 12, 1102)
    tube(t, 12)
    ribs(t, 12)
    for _ in range(3):                                   # a little rubble
        x, z = t.rnd.randint(1, 5), t.rnd.randint(2, 9)
        t.set(x, 1, z, "void_stone_brick_slab", type="bottom")
    t.jigsaw(3, 1, 0, "north", *ENTRY)
    t.jigsaw(3, 1, 11, "south", *den_exit("pysift:echo_den/branches"))
    return t


def den_stairs():
    """Goes 4 blocks down over 12: entry at walk level y5, exit at y1."""
    t = Template(7, 11, 12, 1103)
    for z in range(12):
        floor = 4 if z < 3 else 0 if z > 8 else 4 - (z - 2) // 2 - (1 if z >= 3 and (z - 3) % 2 == 1 else 0)
        floor = max(0, min(4, floor))
        for x in range(7):
            for y in range(11):
                wall = x in (0, 6) or y <= floor or y >= floor + 6
                if y > floor + 6:
                    continue
                if not wall:
                    t.air(x, y, z)
                elif y <= floor:
                    if y == floor and 3 <= z <= 9 and 1 <= x <= 5 and floor > 0:
                        t.set(x, y, z, "dark_slate_brick_stairs", facing="north", half="bottom", shape="straight",
                              waterlogged="false")
                    else:
                        t.set(x, y, z, den_floor(t) if y == floor else den_stone(t))
                else:
                    t.set(x, y, z, den_stone(t))
    t.set(3, 8, 6, "minecraft:soul_lantern", hanging="true")
    t.jigsaw(3, 5, 0, "north", *ENTRY)
    t.jigsaw(3, 1, 11, "south", *den_exit("pysift:echo_den/branches"))
    return t


def den_crossing():
    """13 x 8 x 13 junction: entry north, exits east / south / west; a crystal pillar in the middle."""
    t = Template(13, 8, 13, 1104)
    for x in range(13):
        for z in range(13):
            for y in range(8):
                wall = x in (0, 12) or z in (0, 12) or y in (0, 7)
                if wall:
                    t.set(x, y, z, den_floor(t) if y == 0 else den_stone(t))
                else:
                    t.air(x, y, z)
    for y in range(1, 7):
        t.set(6, y, 6, "dark_slate_pillar", axis="y")
    for dx, dz, f in ((1, 0, "east"), (-1, 0, "west"), (0, 1, "south"), (0, -1, "north")):
        t.set(6 + dx, 3, 6 + dz, "soul_crystal_block")
        t.set(6 + dx * 2, 3, 6 + dz * 2, "charoite_cluster", facing=f, waterlogged="false")
    for x0, z, ax in ((4, 0, True), (4, 12, True)):
        doorway(t, x0, 1, z, ax)
    for z0, x in ((4, 0), (4, 12)):
        doorway(t, z0, 1, x, False)
    t.jigsaw(6, 1, 0, "north", *ENTRY)
    for x, z, f in ((12, 6, "east"), (6, 12, "south"), (0, 6, "west")):
        t.jigsaw(x, 1, z, f, *den_exit("pysift:echo_den/branches"))
    return t


def cave_room(t, w, h, d):
    """A rough, rounded chamber: shell of stone, air inside an ellipsoid, flat floor at y0."""
    cx, cz = (w - 1) / 2, (d - 1) / 2
    for x in range(w):
        for z in range(d):
            for y in range(h):
                ex = (x - cx) / (w / 2 - 0.5)
                ez = (z - cz) / (d / 2 - 0.5)
                ey = (y - 0.5) / (h - 1.2)
                inside = 1 <= y < h - 1 and ex * ex + ez * ez + max(0.0, ey) ** 2 < 1.0 + 0.12 * t.rnd.random()
                if inside:
                    t.air(x, y, z)
                else:
                    t.set(x, y, z, den_floor(t) if y == 0 else ("abyssal_strata" if t.rnd.random() < 0.6 else den_stone(t)))


def entry_door(t, w):
    x0 = w // 2 - 2
    for z in range(0, 3):
        doorway(t, x0, 1, z, True)
    t.jigsaw(w // 2, 1, 0, "north", *ENTRY)


def den_crystal_grotto():
    """Charoite and soul crystals grow out of the walls; a small spirit-liquid pool and a chest."""
    t = Template(15, 10, 15, 1105)
    cave_room(t, 15, 10, 15)
    for _ in range(26):
        x, y, z = t.rnd.randint(1, 13), t.rnd.randint(1, 8), t.rnd.randint(3, 13)
        if t.get(x, y, z) == "minecraft:air":
            for dx, dy, dz, f in ((1, 0, 0, "west"), (-1, 0, 0, "east"), (0, 0, 1, "north"), (0, 0, -1, "south"),
                                  (0, 1, 0, "down"), (0, -1, 0, "up")):
                n = t.get(x + dx, y + dy, z + dz)
                if n and n != "minecraft:air" and n != "minecraft:chest":
                    if t.rnd.random() < 0.35:
                        t.set(x + dx, y + dy, z + dz, "soul_crystal_block")
                    t.set(x, y, z, "charoite_cluster", facing=f, waterlogged="false")
                    break
    for x in range(6, 9):
        for z in range(9, 12):
            t.set(x, 0, z, "spirit_liquid")
    t.chest(7, 1, 7, "echo_den", facing="north")
    entry_door(t, 15)
    return t


def den_resonance_room():
    """Where the golems practise: a wall organ of note blocks, a jukebox, two golems, two chests."""
    t = Template(13, 9, 13, 1106)
    for x in range(13):
        for z in range(13):
            for y in range(9):
                wall = x in (0, 12) or z in (0, 12) or y in (0, 8)
                if wall:
                    t.set(x, y, z, den_floor(t) if y == 0 else den_stone(t))
                else:
                    t.air(x, y, z)
    for x in range(2, 11):                               # the organ on the back wall
        for y in range(1, 1 + 2 + abs(6 - x) % 3 + (2 if x == 6 else 0)):
            t.set(x, y, 11, "minecraft:note_block", note=(x * 2 + y) % 25, instrument=("chime", "bell", "flute")[y % 3])
    t.set(6, 1, 9, "minecraft:jukebox", {"id": "minecraft:jukebox"}, has_record="false")
    for x in (2, 10):
        t.set(x, 1, 2, "minecraft:soul_lantern", hanging="false")
        t.set(x, 6, 6, "soul_crystal_block")
    t.chest(1, 1, 6, "echo_den", facing="east")
    t.chest(11, 1, 6, "echo_den", facing="west")
    t.entity(4, 1, 8, "pysift:echo_golem", yaw=180)
    t.entity(8, 1, 8, "pysift:echo_golem", yaw=180)
    entry_door(t, 13)
    return t


def den_collapsed_room():
    """Half the ceiling came down: rubble, cobwebs, a chest under the debris."""
    t = Template(11, 8, 13, 1107)
    cave_room(t, 11, 8, 13)
    for _ in range(40):
        x, z = t.rnd.randint(1, 9), t.rnd.randint(5, 11)
        h = t.rnd.randint(1, 3)
        for y in range(1, h + 1):
            if t.get(x, y, z) == "minecraft:air":
                t.set(x, y, z, t.rnd.choice(["void_stone_bricks", "dark_slate_bricks", "abyssal_strata"]))
        if t.get(x, h + 1, z) == "minecraft:air" and t.rnd.random() < 0.5:
            t.set(x, h + 1, z, "void_stone_brick_slab", type="bottom")
    for _ in range(6):
        x, y, z = t.rnd.randint(1, 9), t.rnd.randint(4, 6), t.rnd.randint(2, 11)
        if t.get(x, y, z) == "minecraft:air":
            t.set(x, y, z, "minecraft:cobweb")
    t.chest(5, 1, 3, "echo_den", facing="north")
    entry_door(t, 11)
    return t


def den_vault():
    """Rare: the den's hoard behind a ring of crystals."""
    t = Template(11, 8, 11, 1108)
    for x in range(11):
        for z in range(11):
            for y in range(8):
                wall = x in (0, 10) or z in (0, 10) or y in (0, 7)
                t.set(x, y, z, ("ash_marble_bricks" if y == 0 else "dark_slate_bricks") if wall else "minecraft:air")
    for i in range(8):
        a = i * math.pi / 4
        x, z = 5 + round(3 * math.cos(a)), 5 + round(3 * math.sin(a))
        t.set(x, 1, z, "soul_crystal_block")
        t.set(x, 2, z, "charoite_cluster", facing="up", waterlogged="false")
    t.set(5, 1, 5, "violet_strata_bricks")
    t.chest(5, 2, 5, "echo_den_vault", facing="north")
    t.set(5, 6, 5, "minecraft:soul_lantern", hanging="true")
    entry_door(t, 11)
    return t


def den_cap():
    """Closes a doorway when nothing else fits: a wall plug (the connector turns into stone)."""
    t = Template(7, 7, 2, 1109)
    for x in range(7):
        for y in range(7):
            for z in range(2):
                t.set(x, y, z, den_stone(t))
    t.jigsaw(3, 1, 0, "north", "pysift:den_entry", "pysift:den_exit", "minecraft:empty", final="pysift:dark_slate_bricks")
    return t


# ------------------------------------------------------------------ Humbler Husk (amber dunes)
def bone(t, x, y, z, axis="y"):
    t.set(x, y, z, "minecraft:bone_block" if t.rnd.random() < 0.9 else "minecraft:calcite", **({"axis": axis} if t.rnd.random() < 0.9 else {}))


def humbler_husk():
    """A colossal skeleton half sunk in the sand (bottom 3 layers are buried): skull at the front (z 0..9), a spine arching
    over a walk-through ribcage, a tail running back into the dunes, two forelegs. Chests inside the ribcage and the skull."""
    W, H, L = 23, 20, 46
    t = Template(W, H, L, 1201)
    cx = W // 2
    sand = lambda: "amber_sand" if t.rnd.random() < 0.75 else "pale_sand"
    # buried floor inside the ribcage and skull (y0..2), so the inside is a walkable sand floor at y3
    for z in range(2, 36):
        half = 3 if z < 10 else 8
        for x in range(cx - half, cx + half + 1):
            for y in range(0, 3):
                t.set(x, y, z, sand())
    # spine: an arch from the skull (z 9, y 9) up to y 15 over the middle and down to the tail
    spine = {}
    for z in range(8, L):
        if z <= 34:
            y = 9 + int(round(6 * math.sin(math.pi * (z - 8) / 30)))
        else:
            y = max(0, 9 - (z - 34))                       # the tail sinks back into the dunes
        spine[z] = y
        bone(t, cx, y, z, "z")
        if z % 3 == 0 and z <= 34:                         # vertebra spikes
            bone(t, cx, y + 1, z)
            if y + 2 < H:
                bone(t, cx, y + 2, z)
    # ribs: pairs every 3 blocks from z 12 to 33, curving out and down to the buried floor
    for z in range(12, 34, 3):
        top = spine[z]
        for side in (-1, 1):
            for s in range(0, 40):
                a = s / 39 * math.pi * 0.62
                x = cx + side * int(round(9 * math.sin(a)))
                y = int(round(top - (top - 1) * (1 - math.cos(a)) / (1 - math.cos(math.pi * 0.62)) ))
                if 0 <= y < H:
                    bone(t, x, y, z, "x" if a < 0.8 else "y")
        if t.rnd.random() < 0.25:                           # a broken rib
            for y in range(1, 5):
                t.blocks.pop((cx + 8, y, z), None)
    # clear the walkway through the ribcage
    for z in range(10, 35):
        for x in range(cx - 6, cx + 7):
            for y in range(3, spine.get(z, 9)):
                if (x, y, z) not in t.blocks:
                    t.air(x, y, z)
    # skull: a hollow block-ish head, open mouth at the front, eye sockets with soul light
    for x in range(cx - 4, cx + 5):
        for y in range(3, 12):
            for z in range(0, 10):
                shell = x in (cx - 4, cx + 4) or y in (3, 11) or z in (0, 9)
                jaw_gap = z == 0 and 4 <= y <= 6 and cx - 2 <= x <= cx + 2
                if shell and not jaw_gap:
                    bone(t, x, y, z, "z")
                elif not shell:
                    t.air(x, y, z)
    for y in range(4, 8):                                   # the back of the skull opens into the ribcage
        for x in range(cx - 2, cx + 3):
            t.air(x, y, 9)
    for x in (cx - 2, cx + 2):                              # eye sockets
        t.air(x, 9, 0)
        t.set(x, 9, 1, "minecraft:soul_lantern", hanging="false")
    for x in range(cx - 3, cx + 4, 2):                       # teeth
        bone(t, x, 4, 0)
    # forelegs: two bony columns in front of the ribcage with claws in the sand
    for side in (-1, 1):
        lx = cx + side * 7
        for y in range(1, 7):
            bone(t, lx, y, 11)
        for d in range(1, 4):                               # claws reaching forward
            bone(t, lx, 1, 11 - d, "z")
    # loot: two chests under the ribs, one in the skull
    t.chest(cx - 5, 3, 20, "humbler_husk", facing="east")
    t.chest(cx + 5, 3, 27, "humbler_husk", facing="west")
    t.chest(cx, 4, 6, "humbler_husk", facing="south")
    t.set(cx, 3, 6, "minecraft:bone_block", axis="y")
    for _ in range(8):                                       # cobwebs and dead bushes
        x, y, z = t.rnd.randint(cx - 6, cx + 6), t.rnd.randint(5, 12), t.rnd.randint(12, 32)
        if t.get(x, y, z) == "minecraft:air":
            t.set(x, y, z, "minecraft:cobweb")
    for _ in range(10):
        x, z = t.rnd.randint(cx - 6, cx + 6), t.rnd.randint(11, 34)
        if t.get(x, 3, z) == "minecraft:air":
            t.set(x, 3, z, "minecraft:dead_bush")
    return t


# ------------------------------------------------------------------ small fossils (SurfaceFossilFeature)
def fossil_rib_arch():
    t = Template(9, 7, 3, 1301)
    for s in range(30):
        a = s / 29 * math.pi
        x, y = 4 + int(round(4 * math.cos(a))), int(round(6 * math.sin(a)))
        bone(t, x, y, 1, "y" if abs(math.cos(a)) > 0.5 else "x")
    bone(t, 4, 6, 0, "z")
    bone(t, 4, 6, 2, "z")
    return t


def fossil_spine():
    t = Template(3, 4, 11, 1302)
    for z in range(11):
        y = 1 + int(round(1.2 * math.sin(z / 10 * math.pi)))
        bone(t, 1, y, z, "z")
        if z % 2 == 0:
            bone(t, 1, y + 1, z)
            if z % 4 == 0:
                bone(t, 0, y, z, "x")
                bone(t, 2, y, z, "x")
    return t


def fossil_skull():
    t = Template(5, 5, 6, 1303)
    for x in range(5):
        for y in range(5):
            for z in range(6):
                shell = x in (0, 4) or y in (0, 4) or z in (0, 5)
                if shell and not (z == 0 and y in (1, 2) and x in (1, 2, 3)):
                    bone(t, x, y, z, "z")
    t.air(1, 3, 0)
    t.air(3, 3, 0)
    return t


def fossil_claw():
    t = Template(5, 5, 5, 1304)
    for y in range(0, 4):
        bone(t, 2, y, 2)
    for dx, dz in ((-2, -1), (0, -2), (2, -1)):
        bone(t, 2 + dx, 0, 2 + dz, "z")
        bone(t, 2 + dx // 2, 1, 2 + dz // 2, "z")
    bone(t, 2, 4, 2, "y")
    return t


# ------------------------------------------------------------------ Lullaby Hilltop shrine (LullabyShrineFeature)
def lullaby_shrine():
    """15 x 9 x 15: a round platform of ash marble on a hill top, six pillars with soul lanterns, a jukebox in the middle
    ringed by note blocks, two echo golems humming a lullaby, one chest. Bottom layer (y0) is the foundation."""
    t = Template(15, 9, 15, 1401)
    c = 7
    for x in range(15):
        for z in range(15):
            r = math.hypot(x - c, z - c)
            if r <= 7.2:
                t.set(x, 0, z, "ash_marble_bricks" if r < 6.2 else "violet_strata_bricks")
                for y in range(1, 9):
                    t.air(x, y, z)
            if 2.6 < r <= 3.4:
                t.set(x, 0, z, "violet_strata_bricks")
    for i in range(6):
        a = i * math.pi / 3
        x, z = c + round(5.5 * math.cos(a)), c + round(5.5 * math.sin(a))
        for y in range(1, 6):
            t.set(x, y, z, "dark_slate_pillar", axis="y")
        t.set(x, 6, z, "dark_slate_bricks")
        t.set(x, 7, z, "minecraft:soul_lantern", hanging="false")
        if t.rnd.random() < 0.35:                           # one or two pillars broken
            for y in range(4, 8):
                t.air(x, y, z)
            t.set(x + (1 if x < c else -1), 1, z, "dark_slate_brick_slab", type="bottom")
    t.set(c, 1, c, "minecraft:jukebox", {"id": "minecraft:jukebox"}, has_record="false")
    for i in range(8):
        a = i * math.pi / 4
        x, z = c + round(2 * math.cos(a)), c + round(2 * math.sin(a))
        t.set(x, 1, z, "minecraft:note_block", note=(0, 2, 4, 5, 7, 9, 11, 12)[i], instrument="harp")
    t.chest(c, 1, c + 4, "lullaby_shrine", facing="north")
    t.entity(c - 3, 1, c - 1, "pysift:echo_golem", yaw=90)
    t.entity(c + 3, 1, c + 1, "pysift:echo_golem", yaw=270)
    return t


# ------------------------------------------------------------------ write templates
TEMPLATES = {
    "echo_den/hub": den_hub, "echo_den/corridor": den_corridor, "echo_den/stairs": den_stairs,
    "echo_den/crossing": den_crossing, "echo_den/crystal_grotto": den_crystal_grotto,
    "echo_den/resonance_room": den_resonance_room, "echo_den/collapsed_room": den_collapsed_room,
    "echo_den/vault": den_vault, "echo_den/cap": den_cap,
    "humbler_husk": humbler_husk,
    "fossil/rib_arch": fossil_rib_arch, "fossil/spine": fossil_spine, "fossil/skull": fossil_skull, "fossil/claw": fossil_claw,
    "lullaby_shrine": lullaby_shrine,
}


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


built = {}
for name, design in TEMPLATES.items():
    t = design()
    built[name] = t
    if name in edited:
        print(f"  {name}: kept (edited by the user)")
        continue
    f = D / f"structure/{name}.nbt"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(t.to_nbt())
# the order /pysift_showcase lays them out in (read by StructureShowcase.java)
wj(D / "structure_showcase/landmarks.json", {"templates": [f"pysift:{n}" for n in TEMPLATES]})


# ------------------------------------------------------------------ jigsaw pools and structures
def pool(name, elements, fallback="minecraft:empty"):
    wj(D / f"worldgen/template_pool/{name}.json", {"fallback": fallback, "elements": [
        {"weight": w, "element": {"element_type": "minecraft:single_pool_element", "location": f"pysift:{loc}",
                                  "processors": "minecraft:empty", "projection": "rigid"}} for loc, w in elements]})


pool("echo_den/hub", [("echo_den/hub", 1)])
pool("echo_den/corridors", [("echo_den/corridor", 3), ("echo_den/stairs", 1)], fallback="pysift:echo_den/caps")
# tunnels branch out several times before ending in rooms (rooms are dead ends, so they stay rarer than corridors)
pool("echo_den/branches", [("echo_den/corridor", 8), ("echo_den/stairs", 2), ("echo_den/crossing", 4),
                           ("echo_den/crystal_grotto", 2), ("echo_den/resonance_room", 2), ("echo_den/collapsed_room", 2),
                           ("echo_den/vault", 1)], fallback="pysift:echo_den/caps")
pool("echo_den/caps", [("echo_den/cap", 1)])
pool("humbler_husk", [("humbler_husk", 1)])

SIFT_BIOMES = ["pysift:crimson_strata_canyon", "pysift:violet_slate_abyss", "pysift:willow_grove", "pysift:amber_dunes",
               "pysift:red_zone_caves", "pysift:lullaby_hills"]
STRUCTURES = {
    # name: (structure json, biomes, spacing, separation, salt)
    "echo_den": ({"type": "minecraft:jigsaw", "start_pool": "pysift:echo_den/hub", "size": 7, "max_distance_from_center": 96,
                  "start_height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": -36}, "max_inclusive": {"absolute": -16}},
                  "step": "underground_structures", "terrain_adaptation": "beard_box", "use_expansion_hack": False,
                  "spawn_overrides": {}}, SIFT_BIOMES, 40, 14, 70531101),
    "humbler_husk": ({"type": "minecraft:jigsaw", "start_pool": "pysift:humbler_husk", "size": 1, "max_distance_from_center": 80,
                      "project_start_to_heightmap": "WORLD_SURFACE_WG", "start_height": {"absolute": -3},
                      "step": "surface_structures", "terrain_adaptation": "beard_thin", "use_expansion_hack": False,   # sunk 3, not covered
                      "spawn_overrides": {}}, ["pysift:amber_dunes"], 34, 12, 70531102),
}
for name, (data, biomes, spacing, separation, salt) in STRUCTURES.items():
    wj(D / f"worldgen/structure/{name}.json", {**data, "biomes": f"#pysift:has_structure/{name}"})
    wj(D / f"worldgen/structure_set/{name}.json", {
        "placement": {"type": "minecraft:random_spread", "salt": salt, "separation": separation, "spacing": spacing},
        "structures": [{"structure": f"pysift:{name}", "weight": 1}]})
    wj(D / f"tags/worldgen/biome/has_structure/{name}.json", {"values": biomes})


# ------------------------------------------------------------------ features (Java feature types, placed by biome)
wj(D / "worldgen/feature/surface_fossil.json", {"type": "pysift:surface_fossil"})          # 26.3: configured features live in worldgen/feature
wj(D / "worldgen/placed_feature/surface_fossil.json", {"feature": "pysift:surface_fossil", "placement": [
    {"type": "minecraft:rarity_filter", "chance": 5}, {"type": "minecraft:in_square"},
    {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, {"type": "minecraft:biome"}]})
wj(D / "worldgen/feature/lullaby_shrine.json", {"type": "pysift:lullaby_shrine"})
wj(D / "worldgen/placed_feature/lullaby_shrine.json", {"feature": "pysift:lullaby_shrine", "placement": [
    {"type": "minecraft:rarity_filter", "chance": 8}, {"type": "minecraft:in_square"},
    {"type": "minecraft:heightmap", "heightmap": "WORLD_SURFACE_WG"}, {"type": "minecraft:biome"}]})   # the feature itself picks the peak


# ------------------------------------------------------------------ chest loot
def item(name, weight, lo=1, hi=1):
    e = {"type": "minecraft:item", "name": name, "weight": weight}
    if hi > 1:
        e["modifier"] = [{"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}]
    return e


COMMON = [item("minecraft:bread", 12, 1, 3), item("minecraft:iron_ingot", 12, 1, 4), item("minecraft:gold_ingot", 8, 1, 3),
          item("minecraft:bone", 10, 1, 4), item("pysift:gloomcap", 8, 1, 3), item("pysift:soul_berries", 8, 1, 3),
          item("pysift:soul_essence", 10, 1, 3), item("pysift:raw_siftite", 10, 1, 3), item("pysift:charoite", 8, 1, 3)]
RARE = [item("pysift:siftite_ingot", 20, 1, 3), item("pysift:soul_antidote", 15), item("minecraft:echo_shard", 10, 1, 2),
        item("minecraft:diamond", 6, 1, 2), item("pysift:soulite_upgrade_smithing_template", 3),
        {"type": "minecraft:empty", "weight": 25}]
LOOT = {
    "echo_den": ([item("minecraft:echo_shard", 10, 1, 3), item("minecraft:note_block", 8, 1, 2), item("minecraft:amethyst_shard", 8, 2, 5),
                  item("pysift:soul_crystal_block", 4, 1, 2)], (4, 7), (1, 2)),
    "echo_den_vault": ([item("minecraft:echo_shard", 20, 2, 5), item("pysift:soul_crystal_block", 10, 1, 3),
                        item("minecraft:diamond", 8, 1, 3), item("pysift:summoning_sigil", 6)], (5, 8), (2, 4)),
    "humbler_husk": ([item("minecraft:bone_block", 12, 1, 4), item("minecraft:bone", 15, 2, 8), item("minecraft:gold_ingot", 10, 2, 5),
                      item("minecraft:emerald", 8, 1, 3), item("pysift:fuse_powder", 6, 1, 3)], (4, 7), (1, 2)),
    "lullaby_shrine": ([item("minecraft:note_block", 10, 1, 3), item("minecraft:amethyst_shard", 10, 2, 5),
                        item("pysift:soul_berries", 10, 2, 5)], (3, 5), (0, 1)),
}
for name, (extra, rolls, rare_rolls) in LOOT.items():
    data = {"type": "minecraft:chest", "random_sequence": f"pysift:chests/{name}", "pools": [
        {"rolls": {"type": "minecraft:uniform", "min": rolls[0], "max": rolls[1]}, "entries": COMMON + extra},
        {"rolls": {"type": "minecraft:uniform", "min": rare_rolls[0], "max": rare_rolls[1]}, "entries": RARE}]}
    for folder in ("loot_table", "loot_tables"):
        wj(D / f"{folder}/chests/{name}.json", data)


# ------------------------------------------------------------------ achievement: Carapace Explorer (enter a humbler husk)
wj(D / "advancement/progression/carapace_explorer.json", {
    "parent": "pysift:progression/root",
    # 26.3 format (same as vanilla nether/find_fortress): one condition object with "type" and "minecraft:location"
    "criteria": {"entered": {"trigger": "minecraft:location", "conditions": {"player": {
        "type": "minecraft:entity_properties", "entity": "this",
        "predicate": {"minecraft:location": {"structures": "pysift:humbler_husk"}}}}}},
    "display": {"icon": {"id": "minecraft:bone_block"}, "title": {"translate": "advancements.pysift.carapace_explorer.title"},
                "description": {"translate": "advancements.pysift.carapace_explorer.description"}, "frame": "task",
                "show_toast": True, "announce_to_chat": False, "hidden": False},
    "requirements": [["entered"]]})
LANG = {
    "advancements.pysift.carapace_explorer.title": ("Carapace Explorer", "甲殼探險家"),
    "advancements.pysift.carapace_explorer.description": ("Step inside the bones of a Humbler Husk", "走進迅從者殘骸的骨架裡"),
}
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    raw = f.read_bytes().decode("utf-8-sig")
    data = json.loads(raw)
    changed = False
    for key, names in LANG.items():
        if data.get(key) != names[i]:
            data[key] = names[i]
            changed = True
    if changed:
        out = json.dumps(data, ensure_ascii=False, indent=2)
        if "\r\n" in raw:
            out = out.replace("\n", "\r\n")
        f.write_bytes((out + ("\r\n" if "\r\n" in raw else "\n")).encode("utf-8"))


# ------------------------------------------------------------------ preview sheet (front elevation + top view)
try:
    from PIL import Image, ImageDraw
    COLOURS = {"bone": (232, 226, 200), "calcite": (210, 210, 210), "sand": (226, 190, 120), "sculk": (20, 60, 70),
               "soul_crystal": (120, 240, 230), "charoite": (170, 110, 220), "abyssal": (40, 80, 90), "void": (60, 60, 80),
               "dark_slate": (70, 66, 86), "corrupted": (90, 60, 100), "ash_marble": (200, 200, 205), "violet": (150, 90, 170),
               "note_block": (120, 80, 50), "jukebox": (140, 90, 60), "chest": (160, 110, 40), "lantern": (120, 230, 255),
               "jigsaw": (255, 60, 200), "spirit": (250, 170, 230), "cobweb": (230, 230, 230), "bush": (140, 110, 60)}

    def colour(name):
        for k, c in COLOURS.items():
            if k in name:
                return c
        return (140, 140, 140)

    S = 6
    rows = [list(TEMPLATES)[:9], list(TEMPLATES)[9:]]
    sheets = []
    for row in rows:
        w_total = sum((built[n].size[0] + built[n].size[2] + 3) * S + 16 for n in row) + 16
        h_total = max(max(built[n].size[1], built[n].size[2]) for n in row) * S + 40
        img = Image.new("RGB", (w_total, h_total), (34, 32, 40))
        d = ImageDraw.Draw(img)
        ox = 16
        for n in row:
            t = built[n]
            w, h, dep = t.size
            d.text((ox, 4), n, fill=(240, 240, 240))
            for x in range(w):
                for y in range(h):
                    for z in range(dep):
                        b = t.get(x, y, z)
                        if b and b != "minecraft:air":
                            d.rectangle([ox + x * S, 24 + (h - 1 - y) * S, ox + x * S + S - 1, 24 + (h - y) * S - 1], fill=colour(b))
                            break
            tx = ox + (w + 2) * S
            for x in range(w):
                for z in range(dep):
                    for y in range(h - 1, -1, -1):
                        b = t.get(x, y, z)
                        if b and b != "minecraft:air":
                            k = 0.45 + 0.55 * y / max(1, h - 1)
                            d.rectangle([tx + x * S, 24 + z * S, tx + x * S + S - 1, 24 + z * S + S - 1],
                                        fill=tuple(int(v * k) for v in colour(b)))
                            break
            ox += (w + dep + 3) * S + 16
        sheets.append(img)
    sheet = Image.new("RGB", (max(s.width for s in sheets), sum(s.height for s in sheets)), (34, 32, 40))
    y = 0
    for s in sheets:
        sheet.paste(s, (0, y))
        y += s.height
    out = P / "build/texture_pipeline/out/landmarks_preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
except ImportError:
    pass
print("templates:", ", ".join(f"{n} ({len(t.blocks)} blocks, {len(t.entities)} mobs)" for n, t in built.items()))
