"""Resources for the soul power blocks (src/main/java/pryuan05/pysift/soulpower/).
Usage: python -I tools/progression/build_soul_power.py <project>

Create-style: every block has a static model (the casing) plus moving parts that the client renderer turns
(client/soulpower/SoulPowerRenderer). The parts hang on a block that is never placed (soul_power_part, one
variant per part); all of them are modelled around the Y axis with the block centre as the pivot.

Writes blockstates, block / part / item models, item definitions, loot tables, recipes (crafting +
pysift:soul_grinding), mineable / blocks_motion_no_leaves tags, lang, the two GUI backgrounds (cut from vanilla's
furnace GUI) and the gauge dial texture. Textures: patina, soul willow and soul crystal from the mod, the rest vanilla
(art_requests/soul_power_todo.md lists what still wants its own art). Existing PNGs are never rewritten (art_guard)."""
import copy, io, json, math, sys, zipfile
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import art_guard  # noqa: E402

P = Path(sys.argv[1])
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
CLIENT = zipfile.ZipFile(Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client-only.jar")


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# name: (English, 繁中, solid full cube)
BLOCKS = {
    "spirit_engine": ("Spirit Engine", "靈液引擎", False),
    "soul_shaft": ("Soul Shaft", "靈魂傳動軸", False),
    "soul_cogwheel": ("Soul Cogwheel", "靈魂齒輪", False),
    "large_soul_cogwheel": ("Large Soul Cogwheel", "大靈魂齒輪", False),
    "soul_gauge": ("Soul Gauge", "靈壓計", False),
    "soul_wave_emitter": ("Soul Wave Emitter", "靈魂振波發送器", False),
    "soul_wave_receiver": ("Soul Wave Receiver", "靈魂振波接收器", False),
    "soul_grinder": ("Soul Grinder", "靈魂研磨機", True),
    "soul_sifter": ("Soul Sifter", "靈魂淨化篩", False),
    "charoite_beam_emitter": ("Charoite Beam Emitter", "紫龍晶光束發射器", False),
    "charoite_beam_receiver": ("Charoite Beam Receiver", "紫龍晶光束接收器", False),
    "charoite_prism": ("Charoite Prism", "紫龍晶稜鏡", False),
    "soul_vein_node": ("Soul Vein Node", "靈脈節點", False),
    "spirit_pump": ("Spirit Pump", "靈液泵", False),
    "spirit_pipe": ("Spirit Pipe", "靈液管", False),
    "soul_hand_crank": ("Soul Hand Crank", "靈魂手搖曲柄", False),
    "soul_clutch": ("Soul Clutch", "靈魂離合器", False),
    "soul_gearshift": ("Soul Gearshift", "靈魂換向器", False),
    "soul_fan": ("Soul Fan", "靈魂風扇", False),
    "soul_veined_stone": ("Soul-Veined Stone", "靈脈石", True),
}

# ------------------------------------------------------------------ textures
PATINA = "pysift:block/patina_block/patina_block"
LOG = "pysift:block/soul_willow/stripped_soul_willow_log"
LOG_TOP = "pysift:block/soul_willow/stripped_soul_willow_log_top"
PLANKS = "pysift:block/soul_willow/soul_willow_planks"
CRYSTAL = "pysift:block/soul_crystal_block/soul_crystal_block_core_0"
DIAL = "pysift:block/soul_gauge/soul_gauge_dial"
DEEP = "minecraft:block/polished_deepslate"
TILES = "minecraft:block/deepslate_tiles"
COPPER = "minecraft:block/oxidized_copper"
CUT_COPPER = "minecraft:block/oxidized_cut_copper"


# ------------------------------------------------------------------ element helpers
class Box:
    """One model element: from/to in pixels, a texture per face (or one for all), optional Y/X/Z rotation."""

    def __init__(self, frm, to, tex, faces=None, rot=None, origin=(8, 8, 8)):
        self.frm, self.to = list(frm), list(to)
        self.tex = tex if isinstance(tex, dict) else {f: tex for f in ("north", "south", "east", "west", "up", "down")}
        if faces is not None:
            self.tex = {f: t for f, t in self.tex.items() if f in faces}
        self.rot = rot            # (axis, angle)
        self.origin = list(origin)

    def turned_east(self):
        """The same element with +Y turned to +X (a part modelled around Y, used on a side of a machine)."""
        b = copy.deepcopy(self)
        f = lambda p: [p[1], 16 - p[0], p[2]]
        a, c = f(self.frm), f(self.to)
        b.frm = [min(a[i], c[i]) for i in range(3)]
        b.to = [max(a[i], c[i]) for i in range(3)]
        b.origin = f(self.origin)
        remap = {"up": "east", "down": "west", "east": "down", "west": "up", "north": "north", "south": "south"}
        b.tex = {remap[k]: v for k, v in self.tex.items()}
        if self.rot:
            axis, angle = self.rot
            b.rot = ({"y": "x", "x": "y", "z": "z"}[axis], angle if axis != "x" else -angle)
        return b

    def json(self, textures):
        x1, y1, z1 = self.frm
        x2, y2, z2 = self.to
        raw = {"up": [x1, z1, x2, z2], "down": [x1, 16 - z2, x2, 16 - z1], "north": [16 - x2, 16 - y2, 16 - x1, 16 - y1],
               "south": [x1, 16 - y2, x2, 16 - y1], "east": [16 - z2, 16 - y2, 16 - z1, 16 - y1], "west": [z1, 16 - y2, z2, 16 - y1]}
        faces = {}
        for face, tex in self.tex.items():
            if tex not in textures:
                textures[tex] = f"t{len(textures)}"
            faces[face] = {"uv": fit_uv(raw[face]), "texture": "#" + textures[tex]}
        e = {"from": self.frm, "to": self.to, "faces": faces}
        if self.rot:
            e["rotation"] = {"origin": self.origin, "axis": self.rot[0], "angle": self.rot[1]}
        return e


def fit_uv(uv):
    """Keep UVs inside 0..16 (elements of the large cog stick out of the block)."""
    u1, v1, u2, v2 = uv
    out = []
    for a, b in ((u1, u2), (v1, v2)):
        lo, hi = min(a, b), max(a, b)
        w = min(16, hi - lo)
        lo = min(max(lo, 0), 16 - w)
        out.append((lo, lo + w) if a <= b else (lo + w, lo))
    return [round(out[0][0], 3), round(out[1][0], 3), round(out[0][1], 3), round(out[1][1], 3)]


def model(boxes, particle, parent="minecraft:block/block"):
    textures = {}
    elements = [b.json(textures) for b in boxes]
    tex = {v: k for k, v in textures.items()}
    tex["particle"] = particle
    out = {"parent": parent, "textures": tex, "elements": elements}
    return out


def octagon(frm, to, tex, faces=None):
    """A square and the same square turned 45° (an octagon)."""
    return [Box(frm, to, tex, faces), Box(frm, to, tex, faces, rot=("y", 45))]


def ring(half_out, half_in, y1, y2, tex, angles=(0, 45)):
    """A square ring (4 bars) at each angle: an octagonal rim."""
    bars = []
    for ang in angles:
        r = ("y", ang) if ang else None
        o, i = 8 - half_out, 8 + half_out
        n, s = 8 - half_in, 8 + half_in
        bars += [Box([o, y1, o], [i, y2, n], tex, rot=r), Box([o, y1, s], [i, y2, i], tex, rot=r),
                 Box([o, y1, n], [n, y2, s], tex, rot=r), Box([s, y1, n], [i, y2, s], tex, rot=r)]
    return bars


def bars(length_half, width_half, y1, y2, tex, lines):
    """Bars through the centre (pairs of opposite teeth); lines = (along, angle) with along 'x' or 'z'."""
    out = []
    for along, ang in lines:
        if along == "x":
            frm, to = [8 - length_half, y1, 8 - width_half], [8 + length_half, y2, 8 + width_half]
        else:
            frm, to = [8 - width_half, y1, 8 - length_half], [8 + width_half, y2, 8 + length_half]
        out.append(Box(frm, to, tex, rot=("y", ang) if ang else None))
    return out


SHAFT = [Box([6, 0, 6], [10, 16, 10], {"north": LOG, "south": LOG, "east": LOG, "west": LOG, "up": LOG_TOP, "down": LOG_TOP}),
         # two soul streaks so the turning is easy to see
         Box([5.9, 2, 7], [6.1, 14, 9], CRYSTAL, faces=("west",)), Box([9.9, 2, 7], [10.1, 14, 9], CRYSTAL, faces=("east",))]

TEETH = {"up": CUT_COPPER, "down": CUT_COPPER, **{f: DEEP for f in ("north", "south", "east", "west")}}
BODY = {"up": LOG_TOP, "down": LOG_TOP, "north": PLANKS, "south": PLANKS, "east": PLANKS, "west": PLANKS}
PARTS = {
    "shaft": SHAFT,
    # 8 teeth: bars along x and z, and the same turned 45°
    "cog": SHAFT[:1] + octagon([3, 6, 3], [13, 10, 13], BODY)
           + bars(8, 1, 6.5, 9.5, TEETH, [("x", 0), ("z", 0), ("x", 45), ("z", 45)]),
    # 16 teeth: 8 bars, every 22.5°
    "large_cog": SHAFT[:1] + [Box([-1, 6, -1], [17, 10, 17], BODY, rot=("y", a) if a else None) for a in (0, 22.5, 45, -22.5)]
                 + bars(12, 1, 6.5, 9.5, TEETH, [("x", 0), ("x", 22.5), ("x", 45), ("x", -22.5),
                                                   ("z", 0), ("z", 22.5), ("z", -22.5), ("z", 45)]),
    # flywheel near the +Y face: copper rim, spokes, hub and a soul crystal weight that shows the turning
    "flywheel": ring(5.5, 4.5, 13.5, 15.5, COPPER) + bars(4.5, 0.5, 14, 15, PATINA, [("x", 0), ("z", 0), ("x", 45), ("z", 45)])
                + [Box([7, 13, 7], [9, 16, 9], DEEP), Box([7, 13.2, 2], [9, 15.8, 3.6], CRYSTAL)],
    # piston rod and head on top of the engine (engine faces north)
    "piston": [Box([8.5, 13, 4.5], [10.5, 16.5, 6.5], CUT_COPPER), Box([7.5, 16.5, 3.5], [11.5, 17.5, 7.5], PATINA)],
    # two millstones, a crank handle
    "millstone": octagon([2, 10, 2], [14, 12.5, 14], {"up": "minecraft:block/smooth_stone", "down": "minecraft:block/smooth_stone",
                                                       **{f: "minecraft:block/smooth_stone_slab_side" for f in ("north", "south", "east", "west")}})
                 + octagon([3, 12.5, 3], [13, 14.5, 13], {"up": "minecraft:block/grindstone_round", "down": "minecraft:block/grindstone_round",
                                                          **{f: "minecraft:block/grindstone_side" for f in ("north", "south", "east", "west")}})
                 + [Box([7.5, 14.5, 2.5], [8.5, 15.5, 6], LOG), Box([7, 14.5, 1.5], [9, 16.5, 3], PATINA)],
    "wave_ring": ring(7, 6, 11, 11.6, COPPER),
    "wave_core": octagon([6.5, 9, 6.5], [9.5, 12.5, 9.5], CRYSTAL),
    # dial plate on the top face of the gauge (box 1..15) and the needle above it; the needle points to -Z at 0°
    "dial": [Box([3, 15, 3], [13, 15.2, 13], {"up": DIAL, **{f: PATINA for f in ("north", "south", "east", "west", "down")}})],
    "needle": [Box([7.6, 15.2, 4], [8.4, 15.45, 8.4], "minecraft:block/redstone_block"),
               Box([7.3, 15.2, 7.3], [8.7, 15.55, 8.7], "minecraft:block/gold_block")],
    # placeholders for the next machines
    # the sieve of the soul sifter (sifter faces north; the renderer shakes it along the facing axis)
    "sieve": [Box([3, 9.4, 3], [10, 9.8, 13], {"up": "minecraft:block/crafting_table_top", "down": "minecraft:block/crafting_table_top",
                                                 **{f: LOG for f in ("north", "south", "east", "west")}}),
              Box([2.5, 9, 2.5], [10.5, 10.6, 3], LOG), Box([2.5, 9, 13], [10.5, 10.6, 13.5], LOG),
              Box([2.5, 9, 3], [3, 10.6, 13], LOG), Box([10, 9, 3], [10.5, 10.6, 13], LOG),
              Box([10.5, 9.5, 7.5], [13.5, 10.1, 8.5], CUT_COPPER)],   # the rod to the crank
    # the turning lens of the charoite beam blocks (modelled facing up, on top of the housing)
    # hand crank (facing up from the face it is mounted on): hub, arm and a wooden grip
    "crank": [Box([6, 1.5, 6], [10, 4.5, 10], CUT_COPPER), Box([7, 3, 7], [9, 4.5, 14], LOG),
              Box([6.5, 4.5, 12], [9.5, 9, 15], {**{f: LOG for f in ("north", "south", "east", "west")}, "up": LOG_TOP, "down": LOG_TOP})],
    # one half of a split shaft (the +Y half; the renderer turns it to either end)
    "half_shaft": [Box([6, 8, 6], [10, 16, 10], {"north": LOG, "south": LOG, "east": LOG, "west": LOG, "up": LOG_TOP, "down": PATINA}),
                   Box([5.9, 9, 7], [6.1, 15, 9], CRYSTAL, faces=("west",))],
    # fan: hub and four blades (facing up)
    "fan": [Box([6, 9, 6], [10, 13, 10], CUT_COPPER)] + bars(6.5, 1.5, 10.5, 11.5, COPPER, [("x", 0), ("z", 0)])
           + bars(6, 1, 10.7, 11.3, PATINA, [("x", 45), ("z", 45)]),
    "lens": octagon([5, 10, 5], [11, 12.5, 11], "minecraft:block/amethyst_block") + ring(5, 4, 10.3, 11.5, COPPER)
            + [Box([7, 12.5, 7], [9, 13, 9], CRYSTAL)],
}


def dish(tex):
    """A hub with four petals tilted 22.5° outwards (the dish of the wave emitter / receiver)."""
    return [Box([5, 8, 5], [11, 9, 11], PATINA),
            Box([6, 8.5, 1], [10, 9.25, 5], tex, rot=("x", 22.5), origin=(8, 8.75, 5)),
            Box([6, 8.5, 11], [10, 9.25, 15], tex, rot=("x", -22.5), origin=(8, 8.75, 11)),
            Box([11, 8.5, 6], [15, 9.25, 10], tex, rot=("z", 22.5), origin=(11, 8.75, 8)),
            Box([1, 8.5, 6], [5, 9.25, 10], tex, rot=("z", -22.5), origin=(5, 8.75, 8))]


PARTS["emitter_dish"] = dish("minecraft:block/amethyst_block")
PARTS["receiver_dish"] = dish("minecraft:block/sculk_sensor_top")

for name, boxes in PARTS.items():
    wj(A / f"models/block/soul_power_parts/{name}.json", model(boxes, boxes[0].tex.get("north") or next(iter(boxes[0].tex.values()))))
wj(A / "blockstates/soul_power_part.json",
   {"variants": {f"part={n}": {"model": f"pysift:block/soul_power_parts/{n}"} for n in PARTS}})

# ------------------------------------------------------------------ static casings
ENGINE_FRONT = {False: "minecraft:block/blast_furnace_front", True: "minecraft:block/blast_furnace_front_on"}


def engine(powered):
    """Facing north: the flywheel sits on the east side (the renderer turns it), the chimney at the back left."""
    fire = {"north": ENGINE_FRONT[powered], "south": PATINA, "east": PATINA, "west": PATINA, "up": TILES, "down": TILES}
    return [Box([0, 0, 0], [16, 2, 16], {**{f: TILES for f in ("north", "south", "east", "west")}, "up": DEEP, "down": DEEP}),
            Box([1, 2, 1], [13, 11, 15], fire),
            Box([0.5, 10, 0.5], [13.5, 11.5, 15.5], CUT_COPPER),
            Box([3, 11.5, 10], [6, 16, 13], DEEP),
            Box([2.5, 15, 9.5], [6.5, 16, 13.5], CUT_COPPER),
            Box([7, 11.5, 3], [12, 13.5, 8], PATINA),
            Box([13, 5.5, 5.5], [13.5, 10.5, 10.5], DEEP)]


RED_SCULK = "pysift:block/red_sculk/red_sculk"
SIFTER = [Box([1, 0, 1], [12, 3, 15], {**{f: CUT_COPPER for f in ("north", "south", "east", "west")}, "up": RED_SCULK, "down": DEEP}),
          Box([1, 3, 1], [2.5, 13, 2.5], LOG), Box([10.5, 3, 1], [12, 13, 2.5], LOG),
          Box([1, 3, 13.5], [2.5, 13, 15], LOG), Box([10.5, 3, 13.5], [12, 13, 15], LOG),
          Box([1, 12, 1], [12, 13, 2.5], PATINA), Box([1, 12, 13.5], [12, 13, 15], PATINA),
          Box([12, 5.5, 5.5], [13.5, 10.5, 10.5], DEEP)]
BEAM_EMITTER = [Box([1, 0, 1], [15, 3, 15], DEEP), Box([0.5, 0, 0.5], [15.5, 1, 15.5], CUT_COPPER)]     + octagon([3.5, 3, 3.5], [12.5, 9.5, 12.5], {**{f: PATINA for f in ("north", "south", "east", "west")}, "up": DEEP, "down": DEEP})     + [Box([3, 9, 3], [13, 10, 13], CUT_COPPER)]
BEAM_RECEIVER = [Box([1, 0, 1], [15, 3, 15], DEEP), Box([0.5, 0, 0.5], [15.5, 1, 15.5], CUT_COPPER)]     + octagon([4, 3, 4], [12, 8, 12], {**{f: PATINA for f in ("north", "south", "east", "west")}, "up": DEEP, "down": DEEP})     + [Box([2.5, 6, 7], [4, 12, 9], CUT_COPPER), Box([12, 6, 7], [13.5, 12, 9], CUT_COPPER),
       Box([7, 6, 2.5], [9, 12, 4], CUT_COPPER), Box([7, 6, 12], [9, 12, 13.5], CUT_COPPER)]
PRISM = octagon([4, 3.5, 4], [12, 11.5, 12], "minecraft:block/amethyst_block")     + [Box([6, 11.5, 6], [10, 13.5, 10], CUT_COPPER), Box([7, 13.5, 7], [9, 14, 9], CRYSTAL),
       Box([5, 2.5, 5], [11, 3.5, 11], CUT_COPPER)]
VEINED = "pysift:block/soul_veined_stone/soul_veined_stone"
# vein node: a deepslate frame (12 edges) with the turning soul core inside
VEIN_NODE = [Box(f, t, DEEP) for f, t in (
    ([0, 0, 0], [16, 2, 2]), ([0, 0, 14], [16, 2, 16]), ([0, 14, 0], [16, 16, 2]), ([0, 14, 14], [16, 16, 16]),
    ([0, 0, 2], [2, 2, 14]), ([14, 0, 2], [16, 2, 14]), ([0, 14, 2], [2, 16, 14]), ([14, 14, 2], [16, 16, 14]),
    ([0, 2, 0], [2, 14, 2]), ([14, 2, 0], [16, 14, 2]), ([0, 2, 14], [2, 14, 16]), ([14, 2, 14], [16, 14, 16]))]     + [Box([2, 0.5, 2], [14, 1.5, 14], VEINED), Box([2, 14.5, 2], [14, 15.5, 14], VEINED)]
# pump: faces north (the intake nozzle at the front, the outlet flange at the back, the crank bearing on the east)
PUMP = [Box([1, 1, 3], [12, 13, 15], {**{f: PATINA for f in ("north", "south", "east", "west")}, "up": CUT_COPPER, "down": CUT_COPPER}),
        Box([3.5, 3.5, 0], [9.5, 9.5, 3], {**{f: CUT_COPPER for f in ("south", "east", "west", "up", "down")}, "north": DEEP}),
        Box([3, 3, 15], [10, 10, 16], COPPER), Box([12, 5.5, 5.5], [13.5, 10.5, 10.5], DEEP),
        Box([0.5, 0, 2.5], [12.5, 1, 15.5], CUT_COPPER)]
PIPE_ARM = {"north": ([5.5, 5.5, 0], [10.5, 10.5, 5]), "south": ([5.5, 5.5, 11], [10.5, 10.5, 16]),
            "west": ([0, 5.5, 5.5], [5, 10.5, 10.5]), "east": ([11, 5.5, 5.5], [16, 10.5, 10.5]),
            "down": ([5.5, 0, 5.5], [10.5, 5, 10.5]), "up": ([5.5, 11, 5.5], [10.5, 16, 10.5])}
PIPE_CORE = [Box([5, 5, 5], [11, 11, 11], CUT_COPPER)]
CRANK_BASE = [Box([4, 0, 4], [12, 1.5, 12], DEEP)]
FAN = [Box([0, 0, 0], [16, 3, 16], {**{f: CUT_COPPER for f in ("north", "south", "east", "west")}, "up": "minecraft:block/iron_bars",
                                     "down": DEEP}),
       Box([0, 3, 0], [16, 16, 2], PATINA), Box([0, 3, 14], [16, 16, 16], PATINA),
       Box([0, 3, 2], [2, 16, 14], PATINA), Box([14, 3, 2], [16, 16, 14], PATINA)]


def shift_case(side, lamp):
    """Casing of the clutch / gearshift (shaft along Y): four walls round the shaft, a lamp on one wall."""
    walls = {**{f: side for f in ("north", "south", "east", "west")}, "up": CUT_COPPER, "down": CUT_COPPER}
    return [Box([1, 1, 1], [15, 15, 3], walls), Box([1, 1, 13], [15, 15, 15], walls),
            Box([1, 1, 3], [3, 15, 13], walls), Box([13, 1, 3], [15, 15, 13], walls),
            Box([6, 6, 15], [10, 10, 15.5], lamp), Box([0.5, 0.5, 0.5], [15.5, 2, 15.5], CUT_COPPER),
            Box([0.5, 14, 0.5], [15.5, 15.5, 15.5], CUT_COPPER)]


GRINDER = [Box([0, 0, 0], [16, 9, 16], {**{f: TILES for f in ("north", "south", "east", "west")}, "up": DEEP, "down": DEEP}),
           Box([0, 9, 0], [16, 10, 16], CUT_COPPER),
           Box([0, 10, 0], [16, 11, 1.5], PATINA), Box([0, 10, 14.5], [16, 11, 16], PATINA),
           Box([0, 10, 1.5], [1.5, 11, 14.5], PATINA), Box([14.5, 10, 1.5], [16, 11, 14.5], PATINA)]
# wave blocks: modelled facing up (the back, which takes the shaft, is the bottom)
WAVE = [Box([1, 0, 1], [15, 3, 15], DEEP), Box([0.5, 0, 0.5], [15.5, 1, 15.5], CUT_COPPER),
        Box([6, 3, 6], [10, 8, 10], PATINA), Box([5, 7, 5], [11, 8, 11], COPPER)]
GAUGE = [Box([1, 1, 1], [15, 15, 15], {**{f: PATINA for f in ("north", "south", "east", "west")}, "up": CUT_COPPER, "down": CUT_COPPER}),
         Box([0.5, 0.5, 0.5], [15.5, 2, 15.5], CUT_COPPER), Box([0.5, 14, 0.5], [15.5, 15.5, 15.5], CUT_COPPER)]

STATIC = {
    "spirit_engine": engine(False), "spirit_engine_on": engine(True),
    "soul_grinder": GRINDER, "soul_sifter": SIFTER, "charoite_beam_emitter": BEAM_EMITTER,
    "charoite_beam_receiver": BEAM_RECEIVER, "charoite_prism": PRISM, "soul_vein_node": VEIN_NODE, "spirit_pump": PUMP,
    "soul_hand_crank": CRANK_BASE, "soul_fan": FAN,
    "soul_clutch": shift_case(PATINA, "minecraft:block/redstone_lamp"),
    "soul_clutch_on": shift_case(PATINA, "minecraft:block/redstone_lamp_on"),
    "soul_gearshift": shift_case(CUT_COPPER, "minecraft:block/redstone_lamp"),
    "soul_gearshift_on": shift_case(CUT_COPPER, "minecraft:block/redstone_lamp_on"), "soul_wave_emitter": WAVE, "soul_wave_receiver": WAVE, "soul_gauge": GAUGE,
}
for name, boxes in STATIC.items():
    base = name.removesuffix("_on")
    wj(A / f"models/block/{base}/{name}.json", model(boxes, PATINA))
# shaft and cogs: the renderer draws everything; the block model only gives the breaking particles
for name in ("soul_shaft", "soul_cogwheel", "large_soul_cogwheel"):
    wj(A / f"models/block/{name}/{name}.json", {"textures": {"particle": LOG}})
for stale in ("soul_shaft/soul_shaft_on", "soul_grinder/soul_grinder_on", "soul_wave_emitter/soul_wave_emitter_on",
              "soul_wave_receiver/soul_wave_receiver_on"):
    (A / f"models/block/{stale}.json").unlink(missing_ok=True)

# ------------------------------------------------------------------ blockstates
YROT = {"north": {}, "east": {"y": 90}, "south": {"y": 180}, "west": {"y": 270}}
UPROT = {"up": {}, "down": {"x": 180}, "north": {"x": 90}, "south": {"x": 90, "y": 180}, "east": {"x": 90, "y": 90},
         "west": {"x": 90, "y": 270}}
AXIS = {"y": {}, "x": {"x": 90, "y": 90}, "z": {"x": 90}}


def states(name, rots, prop, powered_model=None):
    v = {}
    for value, rot in rots.items():
        for powered in ("false", "true"):
            m = powered_model if powered == "true" and powered_model else f"pysift:block/{name}/{name}"
            v[f"{prop}={value},powered={powered}"] = {"model": m, **rot}
    wj(A / f"blockstates/{name}.json", {"variants": v})


states("spirit_engine", YROT, "facing", "pysift:block/spirit_engine/spirit_engine_on")
states("soul_grinder", {**YROT, "up": {}, "down": {}}, "facing")
states("soul_sifter", {**YROT, "up": {}, "down": {}}, "facing")
states("charoite_beam_emitter", UPROT, "facing")
states("charoite_beam_receiver", UPROT, "facing")
wj(A / "blockstates/soul_vein_node.json", {"variants": {f"powered={v}": {"model": "pysift:block/soul_vein_node/soul_vein_node"}
                                                         for v in ("false", "true")}})
wj(A / "models/block/soul_veined_stone/soul_veined_stone.json", {"parent": "minecraft:block/cube_all", "textures": {"all": VEINED}})
wj(A / "blockstates/soul_veined_stone.json", {"variants": {"": {"model": "pysift:block/soul_veined_stone/soul_veined_stone"}}})
states("spirit_pump", {"north": {}, "east": {"y": 90}, "south": {"y": 180}, "west": {"y": 270}, "up": {"x": 270},
                      "down": {"x": 90}}, "facing")
wj(A / "models/block/spirit_pipe/spirit_pipe_core.json", model(PIPE_CORE, CUT_COPPER))
for d, (f, t) in PIPE_ARM.items():
    wj(A / f"models/block/spirit_pipe/spirit_pipe_{d}.json", model([Box(f, t, COPPER)], CUT_COPPER))
wj(A / "blockstates/spirit_pipe.json", {"multipart": [{"apply": {"model": "pysift:block/spirit_pipe/spirit_pipe_core"}}] + [
    {"when": {d: "true"}, "apply": {"model": f"pysift:block/spirit_pipe/spirit_pipe_{d}"}} for d in PIPE_ARM]})
states("soul_hand_crank", UPROT, "facing")
states("soul_fan", UPROT, "facing")
for name in ("soul_clutch", "soul_gearshift"):
    wj(A / f"blockstates/{name}.json", {"variants": {
        f"axis={a},powered={pw},shifted={sh}": {"model": f"pysift:block/{name}/{name}{'_on' if sh == 'true' else ''}", **rot}
        for a, rot in AXIS.items() for pw in ("false", "true") for sh in ("false", "true")}})
wj(A / "blockstates/charoite_prism.json",
   {"variants": {f"facing={f}": {"model": "pysift:block/charoite_prism/charoite_prism", **rot} for f, rot in UPROT.items()}})
states("soul_wave_emitter", UPROT, "facing")
states("soul_wave_receiver", UPROT, "facing")
states("soul_gauge", AXIS, "axis")
for name in ("soul_shaft", "soul_cogwheel", "large_soul_cogwheel"):
    states(name, {a: {} for a in AXIS}, "axis")

# ------------------------------------------------------------------ item models (casing + parts in their resting pose)
FLYWHEEL_EAST = [b.turned_east() for b in PARTS["flywheel"]]
SHAFT_X = [b.turned_east() for b in SHAFT[:1]]
ITEMS = {
    "spirit_engine": engine(False) + FLYWHEEL_EAST + SHAFT_X + PARTS["piston"],
    "soul_grinder": GRINDER + PARTS["millstone"],
    "soul_sifter": SIFTER + PARTS["sieve"] + FLYWHEEL_EAST,
    "charoite_beam_emitter": BEAM_EMITTER + PARTS["lens"],
    "charoite_beam_receiver": BEAM_RECEIVER + PARTS["lens"],
    "charoite_prism": PRISM,
    "spirit_pump": PUMP + FLYWHEEL_EAST + SHAFT_X,
    "soul_hand_crank": CRANK_BASE + PARTS["crank"],
    "soul_fan": FAN + PARTS["fan"],
    "soul_clutch": shift_case(PATINA, "minecraft:block/redstone_lamp") + SHAFT[:1],
    "soul_gearshift": shift_case(CUT_COPPER, "minecraft:block/redstone_lamp") + SHAFT[:1],
    "spirit_pipe": PIPE_CORE + [Box(*PIPE_ARM["north"], COPPER), Box(*PIPE_ARM["south"], COPPER)],
    "soul_vein_node": VEIN_NODE + PARTS["wave_core"],
    "soul_wave_emitter": WAVE + PARTS["emitter_dish"] + PARTS["wave_ring"] + PARTS["wave_core"],
    "soul_wave_receiver": WAVE + PARTS["receiver_dish"] + PARTS["wave_ring"] + PARTS["wave_core"],
    "soul_gauge": GAUGE + SHAFT[:1] + PARTS["dial"] + PARTS["needle"],
    "soul_shaft": SHAFT,
    "soul_cogwheel": PARTS["cog"],
    "large_soul_cogwheel": PARTS["large_cog"],
}
for name, boxes in ITEMS.items():
    wj(A / f"models/item/{name}.json", model(boxes, PATINA))
    wj(A / f"items/{name}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{name}"}})

# plain blocks: the item is the block model
for name in [n for n in BLOCKS if n not in ITEMS]:
    wj(A / f"models/item/{name}.json", {"parent": f"pysift:block/{name}/{name}"})
    wj(A / f"items/{name}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{name}"}})

for name in BLOCKS:
    loot = {"type": "minecraft:block", "pools": [{"rolls": 1, "condition": {"type": "minecraft:survives_explosion"},
                                                   "entries": [{"type": "minecraft:item", "name": f"pysift:{name}"}]}],
            "random_sequence": f"pysift:blocks/{name}"}
    for folder in ("loot_table", "loot_tables"):
        wj(D / f"pysift/{folder}/blocks/{name}.json", loot)


def tag(path, values, remove=()):
    f = D / path
    cur = json.loads(f.read_text(encoding="utf-8-sig")) if f.exists() else {"replace": False, "values": []}
    cur["values"] = [v for v in cur["values"] if v not in remove]
    cur["values"] += [v for v in values if v not in cur["values"]]
    wj(f, cur)


tag("minecraft/tags/block/mineable/pickaxe.json", [f"pysift:{n}" for n in BLOCKS])
tag("minecraft/tags/block/blocks_motion_no_leaves.json", [f"pysift:{n}" for n, v in BLOCKS.items() if v[2]],
    remove=[f"pysift:{n}" for n, v in BLOCKS.items() if not v[2]])

# ------------------------------------------------------------------ recipes
SHAPED = {
    "patina_gear": ([" I ", "IEI", " I "], {"I": "pysift:patina_ingot", "E": "pysift:soul_essence"}, 2),
    "spirit_engine": (["PIP", "IBI", "PEP"], {"P": "minecraft:polished_deepslate", "I": "pysift:patina_gear",
                                              "B": "minecraft:blast_furnace", "E": "pysift:soul_essence"}, 1),
    "soul_shaft": (["I", "S", "I"], {"I": "pysift:patina_ingot", "S": "pysift:stripped_soul_willow_log"}, 8),
    "soul_cogwheel": ([" P ", "PSP", " P "], {"P": "pysift:soul_willow_planks", "S": "pysift:soul_shaft"}, 1),
    "large_soul_cogwheel": (["PCP"], {"P": "pysift:soul_willow_planks", "C": "pysift:soul_cogwheel"}, 1),
    "soul_gauge": (["I", "S", "C"], {"I": "minecraft:compass", "S": "pysift:soul_shaft", "C": "pysift:patina_ingot"}, 1),
    "soul_wave_emitter": (["PAP", "ESE", "PIP"], {"P": "minecraft:polished_deepslate", "A": "minecraft:amethyst_shard",
                                                  "E": "pysift:soul_essence", "S": "minecraft:sculk_sensor",
                                                  "I": "pysift:patina_gear"}, 1),
    "soul_wave_receiver": (["PIP", "ESE", "PAP"], {"P": "minecraft:polished_deepslate", "A": "minecraft:amethyst_shard",
                                                   "E": "pysift:soul_essence", "S": "minecraft:sculk_sensor",
                                                   "I": "pysift:patina_gear"}, 1),
    "soul_sifter": (["LCL", "GSG", "LTL"], {"L": "pysift:stripped_soul_willow_log", "C": "minecraft:crafting_table",
                                            "G": "pysift:patina_gear", "S": "pysift:soul_crystal_block", "T": "minecraft:hopper"}, 1),
    "charoite_beam_emitter": (["CCC", "GEG", "PGP"], {"C": "pysift:charoite", "G": "pysift:patina_gear",
                                                      "E": "pysift:soul_essence", "P": "minecraft:polished_deepslate"}, 1),
    "charoite_beam_receiver": (["PGP", "GEG", "CCC"], {"C": "pysift:charoite", "G": "pysift:patina_gear",
                                                       "E": "pysift:soul_essence", "P": "minecraft:polished_deepslate"}, 1),
    "spirit_pump": (["IGI", "IBI", "III"], {"I": "pysift:patina_ingot", "G": "pysift:patina_gear", "B": "minecraft:bucket"}, 1),
    "spirit_pipe": (["III"], {"I": "pysift:patina_ingot"}, 6),
    "soul_hand_crank": (["LLL", "  I"], {"L": "pysift:soul_willow_planks", "I": "pysift:patina_ingot"}, 1),
    "soul_fan": ([" B ", "IGI", " S "], {"B": "minecraft:iron_bars", "I": "pysift:patina_ingot", "G": "pysift:patina_gear",
                                         "S": "pysift:soul_shaft"}, 1),
    "soul_vein_node": (["DGD", "GCG", "DGD"], {"D": "minecraft:polished_deepslate", "G": "pysift:patina_gear",
                                               "C": "pysift:soul_crystal_block"}, 2),
    "charoite_prism": (["GCG", "CAC", "GCG"], {"G": "minecraft:glass", "C": "pysift:charoite", "A": "minecraft:amethyst_shard"}, 2),
    "soul_grinder": (["PSP", "IGI", "PEP"], {"P": "minecraft:polished_deepslate", "S": "minecraft:stonecutter",
                                             "I": "pysift:patina_gear", "G": "minecraft:grindstone",
                                             "E": "pysift:soul_essence"}, 1),
}
for name, (pattern, key, count) in SHAPED.items():
    result = {"id": f"pysift:{name}"}
    if count > 1:
        result["count"] = count
    wj(D / f"pysift/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": "redstone",
                                          "key": key, "pattern": pattern, "result": result})
GRINDING = {
    "siftite_ore": ("pysift:siftite_ore", "pysift:raw_siftite", 2),
    "iron_ores": ("#minecraft:iron_ores", "minecraft:raw_iron", 2),
    "gold_ores": ("#minecraft:gold_ores", "minecraft:raw_gold", 2),
    "copper_ores": ("#minecraft:copper_ores", "minecraft:raw_copper", 6),
    "cobblestone": ("minecraft:cobblestone", "minecraft:gravel", 1),
    "gravel": ("minecraft:gravel", "minecraft:sand", 1),
    "bone": ("minecraft:bone", "minecraft:bone_meal", 6),
    "soul_soil": ("minecraft:soul_soil", "minecraft:soul_sand", 1),
}
# clutch / gearshift: a shaft (or cog), patina and redstone
for name, core in (("soul_clutch", "pysift:soul_shaft"), ("soul_gearshift", "pysift:soul_cogwheel")):
    wj(D / f"pysift/recipe/{name}.json", {"type": "minecraft:crafting_shapeless", "category": "redstone",
                                          "ingredients": [core, "pysift:patina_ingot", "minecraft:redstone"],
                                          "result": {"id": f"pysift:{name}"}})
# soul haunting: a soul fan blowing through soul fire
HAUNTING = {
    "sand": ("#minecraft:sand", "minecraft:soul_sand"),
    "dirt": ("minecraft:dirt", "minecraft:soul_soil"),
    "torch": ("minecraft:torch", "minecraft:soul_torch"),
    "lantern": ("minecraft:lantern", "minecraft:soul_lantern"),
    "campfire": ("minecraft:campfire", "minecraft:soul_campfire"),
    "sculk_vein": ("minecraft:sculk_vein", "pysift:red_sculk_vein"),
}
for name, (ingredient, item) in HAUNTING.items():
    wj(D / f"pysift/recipe/soul_haunting/{name}.json",
       {"type": "pysift:soul_haunting", "ingredient": ingredient, "result": {"id": item}})
# soul sifting: rotten (blue) sculk back to red; a few sifting classics
SIFTING = {
    "sculk": ("minecraft:sculk", "pysift:red_sculk", 1),
    "sculk_vein": ("minecraft:sculk_vein", "pysift:red_sculk_vein", 1),
    "gravel": ("minecraft:gravel", "minecraft:flint", 1),
    "soul_sand": ("minecraft:soul_sand", "minecraft:soul_soil", 1),
    "sand": ("#minecraft:sand", "minecraft:clay_ball", 1),
}
for name, (ingredient, item, count) in SIFTING.items():
    wj(D / f"pysift/recipe/soul_sifting/{name}.json",
       {"type": "pysift:soul_sifting", "ingredient": ingredient, "result": {"id": item, "count": count}})
wj(D / "pysift/advancement/story/sifted.json", {
    "parent": "pysift:story/warden_soothed",
    "criteria": {"done": {"trigger": "minecraft:impossible"}},
    "display": {"icon": {"id": "pysift:soul_sifter"}, "title": {"translate": "advancements.pysift.story.sifted.title"},
                "description": {"translate": "advancements.pysift.story.sifted.description"},
                "frame": "goal", "show_toast": True, "announce_to_chat": True, "hidden": False},
    "rewards": {"experience": 100}})
for name, (ingredient, item, count) in GRINDING.items():
    wj(D / f"pysift/recipe/soul_grinding/{name}.json",
       {"type": "pysift:soul_grinding", "ingredient": ingredient, "result": {"id": item, "count": count}})

# ------------------------------------------------------------------ GUI backgrounds from vanilla's furnace (only if missing)
furnace = Image.open(io.BytesIO(CLIENT.read("assets/minecraft/textures/gui/container/furnace.png"))).convert("RGBA")
BG = furnace.getpixel((60, 70))
slot = furnace.crop((55, 16, 73, 34))


def clear(im, box):
    im.paste(Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), BG), box[:2])


engine_gui = furnace.copy()
clear(engine_gui, (55, 16, 73, 34))
clear(engine_gui, (78, 32, 140, 60))
grinder_gui = furnace.copy()
clear(grinder_gui, (55, 16, 73, 71))
grinder_gui.paste(slot, (55, 34))
grinder_gui.paste(slot, (115, 59))
for name, im in (("spirit_engine", engine_gui), ("soul_grinder", grinder_gui)):
    art_guard.save(im, A / f"textures/gui/container/{name}.png")


# ------------------------------------------------------------------ gauge dial (new texture)
def dial():
    """16x16: dark patina bezel, cream face, a 270° scale from the lower left (green) over the top to the lower
    right (red). The needle points up at 0° and swings clockwise as the load rises (SoulPowerRenderer)."""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    bezel, bezel_hi, face, face_lo = (41, 74, 68, 255), (72, 112, 98, 255), (226, 214, 184, 255), (204, 190, 160, 255)
    green, yellow, red = (78, 146, 84, 255), (214, 170, 58, 255), (180, 56, 46, 255)
    for v in range(16):
        for u in range(16):
            dx, dy = u - 7.5, v - 7.5
            r = math.hypot(dx, dy)
            if r > 7.9:
                continue
            if r > 6.6:
                im.putpixel((u, v), bezel_hi if dx + dy < -2 else bezel)
                continue
            im.putpixel((u, v), face if dx + dy < 3 else face_lo)
            phi = math.degrees(math.atan2(dx, -dy))       # clockwise from up
            if 4.6 < r <= 6.6 and -135 <= phi <= 135:
                load = (phi + 135) / 270
                im.putpixel((u, v), green if load < 0.6 else yellow if load < 0.85 else red)
    for u, v in ((7, 7), (8, 7), (7, 8), (8, 8)):
        im.putpixel((u, v), bezel)
    return im


art_guard.save(dial(), A / "textures/block/soul_gauge/soul_gauge_dial.png")


def veined_stone():
    """Vanilla deepslate with a seamless, glowing cyan soul vein (core + softer glow beside it)."""
    base = Image.open(io.BytesIO(CLIENT.read("assets/minecraft/textures/block/deepslate.png"))).convert("RGBA")
    core = [(0, 5), (1, 5), (2, 6), (3, 6), (4, 6), (5, 7), (6, 7), (7, 8), (8, 8), (9, 8), (10, 7), (11, 6), (12, 6),
            (13, 5), (14, 5), (15, 5), (8, 9), (8, 10), (9, 11), (9, 12), (10, 13), (10, 14), (10, 15),
            (10, 0), (10, 1), (9, 2), (9, 3), (8, 4), (4, 7), (3, 8), (3, 9), (2, 10)]
    bright, mid = (150, 238, 236), (84, 176, 186)
    im = base.copy()
    cs = set(core)
    for x, y in core:
        im.putpixel((x, y), (*(bright if (x + y) % 3 else mid), 255))
    for x, y in core:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = ((x + dx) % 16, (y + dy) % 16)
            if q not in cs:
                b = base.getpixel(q)
                im.putpixel(q, tuple((b[i] + (60, 140, 150)[i]) // 2 for i in range(3)) + (255,))
    return im


art_guard.save(veined_stone(), A / "textures/block/soul_veined_stone/soul_veined_stone.png")


def patina_gear():
    """16x16 item: an 8-tooth patina gear in the patina ingot's palette. Hand-made mask; lit from the top left,
    sel-out outline (lighter on the lit side), shaded rim around the hole."""
    mask = ["................",
            "......XXXX......",
            "..XX.XXXXXX.XX..",
            "..XXXXXXXXXXXX..",
            "...XXXXXXXXXX...",
            "..XXXXXXXXXXXX..",
            ".XXXXXX..XXXXXX.",
            ".XXXXX....XXXXX.",
            ".XXXXX....XXXXX.",
            ".XXXXXX..XXXXXX.",
            "..XXXXXXXXXXXX..",
            "...XXXXXXXXXX...",
            "..XXXXXXXXXXXX..",
            "..XX.XXXXXX.XX..",
            "......XXXX......",
            "................"]
    pal = [(29, 59, 71), (40, 88, 95), (54, 118, 116), (71, 145, 133), (100, 171, 149), (148, 201, 166), (198, 226, 182)]
    on = lambda u, v: 0 <= u < 16 and 0 <= v < 16 and mask[v][u] == "X"
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for v in range(16):
        for u in range(16):
            if not on(u, v):
                continue
            dx, dy = u - 7.5, v - 7.5
            r = math.hypot(dx, dy)
            light = -(dx + dy)
            outer = [(du, dv) for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1)) if not on(u + du, v + dv)]
            if outer and r > 3:
                idx = 1 if light > 0 else 0
            elif outer:   # rim of the hole: the side facing the light is in shadow, the far side catches it
                idx = 1 if light > 0 else 4
            else:
                idx = 5 if light > 6 else 4 if light > 2 else 2 if light < -3 else 3
            im.putpixel((u, v), (*pal[idx], 255))
    return im


art_guard.save(patina_gear(), A / "textures/item/patina_gear.png")
wj(A / "models/item/patina_gear.json", {"parent": "minecraft:item/generated", "textures": {"layer0": "pysift:item/patina_gear"}})
wj(A / "items/patina_gear.json", {"model": {"type": "minecraft:model", "model": "pysift:item/patina_gear"}})

# ------------------------------------------------------------------ lang (merge, keep line endings)
LANG = {f"block.pysift.{n}": (v[0], v[1]) for n, v in BLOCKS.items()}
# 26.3 block items read item.pysift.<id> (the registration may not use the block key)
LANG.update({f"item.pysift.{n}": (v[0], v[1]) for n, v in BLOCKS.items()})
LANG["item.pysift.patina_gear"] = ("Patina Gear", "銅綠齒輪")
LANG["advancements.pysift.story.sifted.title"] = ("Sifted Back to Red", "篩回赤紅")
LANG["advancements.pysift.story.sifted.description"] = ("Let a Soul Sifter turn rotten blue sculk back into red sculk",
                                                       "讓靈魂淨化篩把腐爛的藍色幽匿篩回赤紅幽匿")
LANG.update({
    "block.pysift.soul_power_part": ("Soul Power Part", "靈魂動力部件"),
    "gui.pysift.soul_power.speed": ("Speed: %s RPM", "轉速：%s RPM"),
    "gui.pysift.soul_power.capacity": ("Capacity: %s SP", "靈壓容量：%s SP"),
    "gui.pysift.soul_power.stress": ("Load: %s SP", "需求：%s SP"),
    "gui.pysift.soul_power.overloaded": ("Overloaded!", "過載！"),
    "gui.pysift.soul_power.running": ("Running at %s RPM", "運轉中：%s RPM"),
    "gui.pysift.soul_power.idle": ("No soul power", "沒有靈魂動力"),
    "message.pysift.soul_wave.frequency": ("Tuned to %s", "頻率：%s"),
    "message.pysift.soul_wave.empty": ("Tune it with a resonant music disc", "放入一張共鳴唱片來設定頻率"),
    "message.pysift.soul_gauge.status": ("%s RPM · load %s / %s SP (%s%%)", "%s RPM · 負載 %s / %s SP（%s%%）"),
    "message.pysift.soul_gauge.overloaded": ("Overloaded! %s / %s SP", "過載！%s / %s SP"),
    "message.pysift.soul_gauge.conflict": ("Speed conflict: gears are fighting each other", "轉速衝突：齒輪互相卡住了"),
})
for code, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{code}.json"
    raw = f.read_bytes().decode("utf-8-sig")
    data = json.loads(raw)
    for k, v in LANG.items():
        data[k] = v[i]
    out = json.dumps(data, ensure_ascii=False, indent=2)
    if "\r\n" in raw:
        out = out.replace("\n", "\r\n")
    f.write_bytes((out + ("\r\n" if raw.endswith("\n") else "")).encode("utf-8"))
print(f"{len(BLOCKS)} soul power blocks, {len(PARTS)} moving parts, {len(GRINDING)} grinding recipes")
