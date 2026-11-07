"""Resources for the soul power blocks (src/main/java/pryuan05/pysift/soulpower/).
Usage: python -I tools/progression/build_soul_power.py <project>

Create-style: every block has a static model (the casing) plus moving parts that the client renderer turns
(client/soulpower/SoulPowerRenderer). The parts hang on a block that is never placed (soul_power_part, one
variant per part); all of them are modelled around the Y axis with the block centre as the pivot.

Writes blockstates, block / part / item models, item definitions, loot tables, recipes (crafting +
pysift:soul_grinding), mineable / blocks_motion_no_leaves tags, lang, the two GUI backgrounds
(painted here) and the patina gear icon. The block textures are painted by tools/progression/paint_soul_power.py (run it
first); models follow Create: a few chunky elements per block, details painted in the textures."""
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
    "soul_gearbox": ("Soul Gearbox", "靈魂齒輪箱", False),
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
    "soul_drill": ("Soul Drill", "靈魂鑽頭", False),
    "resonance_core": ("Resonance Core", "共鳴核心", False),
    "resonance_pedestal": ("Resonance Pedestal", "共鳴台座", False),
    "soul_veined_stone": ("Soul-Veined Stone", "靈脈石", True),
}

# ------------------------------------------------------------------ textures (painted by tools/progression/paint_soul_power.py)
def T(name):
    return f"pysift:block/soul_power/{name}"


CASING, CASING_TOP = T("casing"), T("casing_top")
PATINA = T("ring")                 # plain bronze (rims, bands, flanges)
SHAFT_SIDE, SHAFT_END = T("shaft"), T("shaft_end")
CORE = T("core")


def faces(side, top=None, bottom=None, **extra):
    """A face map: the same texture on the four sides, top / bottom (default: the casing top), single faces overridden."""
    f = {d: side for d in ("north", "south", "east", "west")}
    f["up"] = top or CASING_TOP
    f["down"] = bottom or CASING_TOP
    f.update(extra)
    return f


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

    def mirrored_x(self):
        """The same element mirrored across x = 8 (east <-> west)."""
        b = copy.deepcopy(self)
        b.frm = [16 - self.to[0], self.frm[1], self.frm[2]]
        b.to = [16 - self.frm[0], self.to[1], self.to[2]]
        b.origin = [16 - self.origin[0], self.origin[1], self.origin[2]]
        swap = {"east": "west", "west": "east"}
        b.tex = {swap.get(k, k): v for k, v in self.tex.items()}
        if self.rot:
            axis, angle = self.rot
            b.rot = (axis, -angle if axis != "x" else angle)
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
    """A square and the same square turned 45° (an octagon). The turned square is 0.05 px thinner at both ends: if their
    end faces sat in the same plane they would z-fight (the wheel looked cut and jagged), now the square's face always
    wins and only the turned square's corners show around it."""
    inset = 0.05
    frm2, to2 = list(frm), list(to)
    frm2[1] += inset
    to2[1] -= inset
    return [Box(frm, to, tex, faces), Box(frm2, to2, tex, faces, rot=("y", 45))]


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


# Create-style parts: few, chunky elements; the details are painted in the textures.
SHAFT = [Box([6, 0, 6], [10, 16, 10], faces(SHAFT_SIDE, SHAFT_END, SHAFT_END))]
TOOTH = T("cog_tooth")
COG_BODY = faces(T("cog_edge"), T("cog_face"), T("cog_face"))
LARGE_BODY = faces(T("cog_edge"), T("large_cog_face"), T("large_cog_face"))
PARTS = {
    "shaft": SHAFT,
    # Create's cogwheel: an octagonal wooden wheel on the shaft, 8 bronze teeth (4 bars through the centre)
    "cog": SHAFT + octagon([2, 6, 2], [14, 10, 14], COG_BODY)
           + bars(8, 1.5, 6.5, 9.5, TOOTH, [("x", 0), ("z", 0), ("x", 45), ("z", 45)]),
    # large cogwheel: 16 teeth (8 bars every 22.5 degrees)
    "large_cog": SHAFT + octagon([-2, 6, -2], [18, 10, 18], LARGE_BODY)
                 + bars(12, 1.5, 6.5, 9.5, TOOTH, [("x", 0), ("x", 22.5), ("x", 45), ("x", -22.5),
                                                    ("z", 0), ("z", 22.5), ("z", -22.5), ("z", 45)]),
    # flywheel near the +Y face: one wheel (spokes and the crystal weight are painted) and a hub
    "flywheel": octagon([1.5, 13, 1.5], [14.5, 15.5, 14.5], faces(T("flywheel_edge"), T("flywheel"), T("flywheel")))
                + [Box([6, 12, 6], [10, 16, 10], faces(SHAFT_SIDE, SHAFT_END, SHAFT_END))],
    # piston on top of the engine: a rod and a heavy head
    "piston": [Box([8, 12, 4], [11, 16, 7], faces(SHAFT_SIDE, SHAFT_END, SHAFT_END)),
               Box([7, 16, 3], [12, 18, 8], faces(PATINA, PATINA, PATINA))],
    # millstone: one thick stone wheel
    "millstone": octagon([2, 10, 2], [14, 14, 14], faces(T("millstone_side"), T("millstone_top"), T("millstone_top"))),
    "wave_ring": [Box([1, 11, 1], [15, 11.75, 2.5], PATINA), Box([1, 11, 13.5], [15, 11.75, 15], PATINA),
                  Box([1, 11, 2.5], [2.5, 11.75, 13.5], PATINA), Box([13.5, 11, 2.5], [15, 11.75, 13.5], PATINA)],
    "wave_core": octagon([6, 9, 6], [10, 13, 10], CORE),
    "dial": [Box([7.5, 15, 7.5], [8.5, 15.05, 8.5], PATINA)],   # (the dial itself is painted on the gauge casing)
    "needle": [Box([7.5, 15.1, 3.5], [8.5, 15.5, 8.5], T("needle")),
               Box([7, 15.05, 7], [9, 15.7, 9], faces(PATINA, PATINA, PATINA))],
    # the sieve of the soul sifter: one framed mesh and the rod to the crank
    "sieve": [Box([1.5, 9, 2], [11, 10.5, 14], faces(T("sifter_frame"), T("sieve"), T("sieve"))),
              Box([11, 9.25, 7], [13, 10.25, 9], PATINA)],
    # hand crank: hub, arm and grip
    "crank": [Box([5.5, 1.5, 5.5], [10.5, 5, 10.5], faces(PATINA, PATINA, PATINA)),
              Box([7, 3.5, 7], [9, 5.5, 14], T("crank")),
              Box([6, 5.5, 11], [10, 11, 15], faces(T("crank"), SHAFT_END, SHAFT_END))],
    "half_shaft": [Box([6, 8, 6], [10, 16, 10], faces(SHAFT_SIDE, SHAFT_END, SHAFT_END))],
    # fan: hub and two broad blades
    "fan": [Box([6, 8, 6], [10, 13, 10], faces(PATINA, SHAFT_END, SHAFT_END))]
           + bars(6.5, 2, 10, 11, T("fan_blade"), [("x", 22.5), ("z", 22.5)]),
    # drill bit: three iron steps, each turned a little more (the flutes are painted), a charoite tip
    "drill": [Box([3, 10, 3], [13, 13, 13], T("drill_bit")),
              Box([4.5, 13, 4.5], [11.5, 16, 11.5], T("drill_bit"), rot=("y", 22.5)),
              Box([6, 16, 6], [10, 19, 10], T("drill_bit"), rot=("y", 45)),
              Box([7, 19, 7], [9, 21, 9], T("lens"))],
    "lens": octagon([4.5, 10, 4.5], [11.5, 13, 11.5], T("lens")),
    # bevel gear of the gearbox: a small siftite wheel near the +Y face, 8 teeth, turned to each side by the renderer
    "bevel": octagon([3.5, 11, 3.5], [12.5, 13, 12.5], COG_BODY)
             + bars(5.5, 1, 11.25, 12.75, TOOTH, [("x", 0), ("z", 0), ("x", 45), ("z", 45)]),
    "emitter_dish": octagon([1.5, 8, 1.5], [14.5, 9.5, 14.5], faces(PATINA, T("dish_emitter"), PATINA)),
    "receiver_dish": octagon([1.5, 8, 1.5], [14.5, 9.5, 14.5], faces(PATINA, T("dish_receiver"), PATINA)),
}

for name, boxes in PARTS.items():
    wj(A / f"models/block/soul_power_parts/{name}.json", model(boxes, next(iter(boxes[0].tex.values()))))
wj(A / "blockstates/soul_power_part.json",
   {"variants": {f"part={n}": {"model": f"pysift:block/soul_power_parts/{n}"} for n in PARTS}})

# ------------------------------------------------------------------ static casings (one or two big boxes each)
ENGINE_FRONT = {False: T("engine_front"), True: T("engine_front_on")}


def engine(powered):
    """Facing north: casing 0..12 wide (the flywheel turns on the east side, 12.5..15), a chimney at the back left."""
    return [Box([0, 0, 0], [12, 12, 16], faces(T("engine_side"), T("engine_top"), CASING_TOP, north=ENGINE_FRONT[powered])),
            Box([2, 12, 10], [6, 16, 14], faces(CASING, SHAFT_END, SHAFT_END)),
            Box([7, 12, 3], [12, 13, 8], faces(PATINA, PATINA, PATINA))]


SIFTER = [Box([0, 0, 1], [12, 3, 15], faces(PATINA, T("sifter_tray"), CASING_TOP)),
          Box([0, 3, 0], [12, 13, 2], faces(T("sifter_frame"), T("sifter_frame"))),
          Box([0, 3, 14], [12, 13, 16], faces(T("sifter_frame"), T("sifter_frame"))),
          Box([12, 4, 4], [13, 12, 12], faces(CASING))]
BEAM_EMITTER = [Box([0, 0, 0], [16, 4, 16], faces(CASING, T("beam_top"))),
                Box([2, 4, 2], [14, 10, 14], faces(T("beam_housing"), T("beam_top")))]
BEAM_RECEIVER = [Box([0, 0, 0], [16, 4, 16], faces(CASING, T("beam_top"))),
                 Box([3, 4, 3], [13, 9, 13], faces(T("beam_housing"), T("beam_top"))),
                 Box([1, 8, 7], [15, 12, 9], faces(PATINA, PATINA, PATINA)),
                 Box([7, 8, 1], [9, 12, 15], faces(PATINA, PATINA, PATINA))]
PRISM = octagon([3, 3, 3], [13, 13, 13], faces(T("prism"), T("lens"), T("lens")))
VEIN_NODE = [Box([0, 0, 0], [16, 10, 16], faces(T("vein_node_side"), T("vein_node_top"), CASING_TOP))]
PUMP = [Box([1, 0, 3], [12, 12, 15], faces(T("pump_side"))),
        Box([3, 3, 0], [10, 10, 3], faces(PATINA, PATINA, PATINA, north=T("pump_front"))),
        Box([3, 3, 15], [10, 10, 16], faces(PATINA, PATINA, PATINA, south=T("pipe_end")))]
PIPE_ARM = {"north": ([5, 5, 0], [11, 11, 5]), "south": ([5, 5, 11], [11, 11, 16]),
            "west": ([0, 5, 5], [5, 11, 11]), "east": ([11, 5, 5], [16, 11, 11]),
            "down": ([5, 0, 5], [11, 5, 11]), "up": ([5, 11, 5], [11, 16, 11])}
PIPE_CORE = [Box([4.5, 4.5, 4.5], [11.5, 11.5, 11.5], faces(T("pipe"), T("pipe_end"), T("pipe_end")))]
CRANK_BASE = [Box([3, 0, 3], [13, 2, 13], faces(PATINA, CASING_TOP))]
FAN = [Box([0, 0, 0], [16, 4, 16], faces(CASING, T("fan_side"))),
       Box([0, 4, 0], [16, 16, 2], faces(T("fan_side"), PATINA)), Box([0, 4, 14], [16, 16, 16], faces(T("fan_side"), PATINA)),
       Box([0, 4, 2], [2, 16, 14], faces(T("fan_side"), PATINA)), Box([14, 4, 2], [16, 16, 14], faces(T("fan_side"), PATINA))]


def shift_case(name, on):
    """Clutch / gearshift: one encased box round the shaft (the shaft ends stick out); the lamp is painted."""
    side = T(name + ("_on" if on else ""))
    return [Box([1, 1, 1], [15, 15, 15], faces(side, T("shift_end"), T("shift_end")))]


DRILL = [Box([0, 0, 0], [16, 10, 16], faces(T("drill_side"), CASING_TOP))]
RES_CORE = [Box([0, 0, 0], [16, 3, 16], faces(CASING, CASING_TOP))] \
    + octagon([2.5, 3, 2.5], [13.5, 11, 13.5], faces(T("res_core_side"), T("res_core_top"))) \
    + [Box([1.5, 11, 1.5], [14.5, 13, 14.5], faces(PATINA, T("res_core_top")))]
RES_PEDESTAL = [Box([3, 0, 3], [13, 2, 13], faces(PATINA, CASING_TOP)),
                Box([5, 2, 5], [11, 10, 11], faces(T("pedestal_side"))),
                Box([3, 10, 3], [13, 12, 13], faces(PATINA, T("pedestal_top")))]
GRINDER = [Box([0, 0, 0], [16, 10, 16], faces(T("grinder_side"), CASING_TOP))]
# wave blocks: modelled facing up (the back, which takes the shaft, is the bottom)
WAVE = [Box([0, 0, 0], [16, 4, 16], faces(T("wave_base_side"), T("wave_base_top"))),
        Box([6, 4, 6], [10, 8, 10], faces(SHAFT_SIDE, SHAFT_END))]
# gearbox (axis Y): top and bottom casing plates and four bronze corner posts; the sides are open so the four bevel
# gears inside show
GEARBOX = [Box([0, 0, 0], [16, 2, 16], faces(CASING, CASING_TOP)), Box([0, 14, 0], [16, 16, 16], faces(CASING, CASING_TOP)),
           Box([0, 2, 0], [2, 14, 2], PATINA), Box([14, 2, 0], [16, 14, 2], PATINA),
           Box([0, 2, 14], [2, 14, 16], PATINA), Box([14, 2, 14], [16, 14, 16], PATINA)]
GAUGE = [Box([1, 1, 1], [15, 15, 15], faces(T("gauge_side"), T("shift_end"), T("shift_end")))]

STATIC = {
    "spirit_engine": engine(False), "spirit_engine_on": engine(True),
    "soul_grinder": GRINDER, "soul_sifter": SIFTER, "charoite_beam_emitter": BEAM_EMITTER,
    "charoite_beam_receiver": BEAM_RECEIVER, "charoite_prism": PRISM, "soul_vein_node": VEIN_NODE, "spirit_pump": PUMP,
    "soul_hand_crank": CRANK_BASE, "soul_fan": FAN, "resonance_core": RES_CORE, "resonance_pedestal": RES_PEDESTAL, "soul_drill": DRILL,
    "soul_clutch": shift_case("clutch", False), "soul_clutch_on": shift_case("clutch", True),
    "soul_gearshift": shift_case("gearshift", False), "soul_gearshift_on": shift_case("gearshift", True),
    "soul_wave_emitter": WAVE, "soul_wave_receiver": WAVE, "soul_gauge": GAUGE, "soul_gearbox": GEARBOX,
}
for name, boxes in STATIC.items():
    base = name.removesuffix("_on")
    wj(A / f"models/block/{base}/{name}.json", model(boxes, CASING))
# shaft and cogs: the renderer draws everything; the block model only gives the breaking particles
for name in ("soul_shaft", "soul_cogwheel", "large_soul_cogwheel"):
    wj(A / f"models/block/{name}/{name}.json", {"textures": {"particle": SHAFT_SIDE}})
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


states("spirit_engine", {**YROT, "up": {}, "down": {}}, "facing", "pysift:block/spirit_engine/spirit_engine_on")
states("soul_grinder", {**YROT, "up": {}, "down": {}}, "facing")
states("soul_sifter", {**YROT, "up": {}, "down": {}}, "facing")
states("charoite_beam_emitter", UPROT, "facing")
states("charoite_beam_receiver", UPROT, "facing")
wj(A / "blockstates/soul_vein_node.json", {"variants": {f"powered={v}": {"model": "pysift:block/soul_vein_node/soul_vein_node"}
                                                         for v in ("false", "true")}})
wj(A / "models/block/soul_veined_stone/soul_veined_stone.json", {"parent": "minecraft:block/cube_all", "textures": {"all": T("soul_veined_stone")}})
wj(A / "blockstates/soul_veined_stone.json", {"variants": {"": {"model": "pysift:block/soul_veined_stone/soul_veined_stone"}}})
states("spirit_pump", {"north": {}, "east": {"y": 90}, "south": {"y": 180}, "west": {"y": 270}, "up": {"x": 270},
                      "down": {"x": 90}}, "facing")
wj(A / "models/block/spirit_pipe/spirit_pipe_core.json", model(PIPE_CORE, T("pipe")))
for d, (f, t) in PIPE_ARM.items():
    wj(A / f"models/block/spirit_pipe/spirit_pipe_{d}.json", model([Box(f, t, T("pipe"))], T("pipe")))
wj(A / "blockstates/spirit_pipe.json", {"multipart": [{"apply": {"model": "pysift:block/spirit_pipe/spirit_pipe_core"}}] + [
    {"when": {d: "true"}, "apply": {"model": f"pysift:block/spirit_pipe/spirit_pipe_{d}"}} for d in PIPE_ARM]})
states("soul_hand_crank", UPROT, "facing")
wj(A / "blockstates/resonance_core.json", {"variants": {f"powered={v}": {"model": "pysift:block/resonance_core/resonance_core"}
                                                         for v in ("false", "true")}})
wj(A / "blockstates/resonance_pedestal.json", {"variants": {"": {"model": "pysift:block/resonance_pedestal/resonance_pedestal"}}})
states("soul_fan", UPROT, "facing")
states("soul_drill", UPROT, "facing")
for name in ("soul_clutch", "soul_gearshift"):
    wj(A / f"blockstates/{name}.json", {"variants": {
        f"axis={a},powered={pw},shifted={sh}": {"model": f"pysift:block/{name}/{name}{'_on' if sh == 'true' else ''}", **rot}
        for a, rot in AXIS.items() for pw in ("false", "true") for sh in ("false", "true")}})
wj(A / "blockstates/charoite_prism.json",
   {"variants": {f"facing={f}": {"model": "pysift:block/charoite_prism/charoite_prism", **rot} for f, rot in UPROT.items()}})
states("soul_wave_emitter", UPROT, "facing")
states("soul_wave_receiver", UPROT, "facing")
states("soul_gauge", AXIS, "axis")
states("soul_gearbox", AXIS, "axis")
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
    "resonance_core": RES_CORE,
    "soul_drill": DRILL + PARTS["drill"],
    "resonance_pedestal": RES_PEDESTAL,
    "soul_fan": FAN + PARTS["fan"],
    "soul_clutch": shift_case("clutch", False) + SHAFT,
    "soul_gearshift": shift_case("gearshift", False) + SHAFT,
    "spirit_pipe": PIPE_CORE + [Box(*PIPE_ARM["north"], T("pipe")), Box(*PIPE_ARM["south"], T("pipe"))],
    "soul_vein_node": VEIN_NODE + PARTS["wave_core"],
    "soul_wave_emitter": WAVE + PARTS["emitter_dish"] + PARTS["wave_ring"] + PARTS["wave_core"],
    "soul_wave_receiver": WAVE + PARTS["receiver_dish"] + PARTS["wave_ring"] + PARTS["wave_core"],
    "soul_gauge": GAUGE + PARTS["needle"],
    "soul_gearbox": GEARBOX + [b.turned_east() for b in PARTS["bevel"] + PARTS["half_shaft"]]
                    + [b.mirrored_x() for b in (b2.turned_east() for b2 in PARTS["bevel"] + PARTS["half_shaft"])],
    "soul_shaft": SHAFT,
    "soul_cogwheel": PARTS["cog"],
    "large_soul_cogwheel": PARTS["large_cog"],
}
for name, boxes in ITEMS.items():
    wj(A / f"models/item/{name}.json", model(boxes, CASING))
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
    "siftite_gear": ([" I ", "IEI", " I "], {"I": "pysift:siftite_ingot", "E": "pysift:soul_essence"}, 2),
    "spirit_engine": (["PIP", "IBI", "PEP"], {"P": "minecraft:polished_deepslate", "I": "pysift:siftite_gear",
                                              "B": "minecraft:blast_furnace", "E": "pysift:soul_essence"}, 1),
    "soul_shaft": (["I", "S", "I"], {"I": "pysift:patina_ingot", "S": "pysift:stripped_soul_willow_log"}, 8),
    "soul_gauge": (["I", "S", "C"], {"I": "minecraft:compass", "S": "pysift:soul_shaft", "C": "pysift:patina_ingot"}, 1),
    "soul_wave_emitter": (["PAP", "ESE", "PIP"], {"P": "minecraft:polished_deepslate", "A": "minecraft:amethyst_shard",
                                                  "E": "pysift:soul_essence", "S": "minecraft:sculk_sensor",
                                                  "I": "pysift:siftite_gear"}, 1),
    "soul_wave_receiver": (["PIP", "ESE", "PAP"], {"P": "minecraft:polished_deepslate", "A": "minecraft:amethyst_shard",
                                                   "E": "pysift:soul_essence", "S": "minecraft:sculk_sensor",
                                                   "I": "pysift:siftite_gear"}, 1),
    "soul_sifter": (["LCL", "GSG", "LTL"], {"L": "pysift:stripped_soul_willow_log", "C": "minecraft:crafting_table",
                                            "G": "pysift:siftite_gear", "S": "pysift:soul_crystal_block", "T": "minecraft:hopper"}, 1),
    "charoite_beam_emitter": (["CCC", "GEG", "PGP"], {"C": "pysift:charoite", "G": "pysift:siftite_gear",
                                                      "E": "pysift:soul_essence", "P": "minecraft:polished_deepslate"}, 1),
    "charoite_beam_receiver": (["PGP", "GEG", "CCC"], {"C": "pysift:charoite", "G": "pysift:siftite_gear",
                                                       "E": "pysift:soul_essence", "P": "minecraft:polished_deepslate"}, 1),
    "spirit_pump": (["IGI", "IBI", "III"], {"I": "pysift:patina_ingot", "G": "pysift:siftite_gear", "B": "minecraft:bucket"}, 1),
    "spirit_pipe": (["III"], {"I": "pysift:patina_ingot"}, 6),
    "soul_drill": ([" I ", "IXI", "PGP"], {"I": "minecraft:iron_ingot", "X": "minecraft:iron_block", "P": "pysift:patina_ingot",
                                           "G": "pysift:siftite_gear"}, 1),
    "resonance_core": (["CEC", "GXG", "DDD"], {"C": "pysift:charoite", "E": "minecraft:echo_shard", "G": "pysift:siftite_gear",
                                               "X": "pysift:soul_crystal_block", "D": "minecraft:polished_deepslate"}, 1),
    "resonance_pedestal": ([" A ", "PPP", "DDD"], {"A": "minecraft:amethyst_shard", "P": "pysift:patina_ingot",
                                                   "D": "minecraft:polished_deepslate"}, 2),
    "soul_hand_crank": (["LLL", "  I"], {"L": "pysift:soul_willow_planks", "I": "pysift:patina_ingot"}, 1),
    "soul_fan": ([" B ", "IGI", " S "], {"B": "minecraft:iron_bars", "I": "pysift:patina_ingot", "G": "pysift:siftite_gear",
                                         "S": "pysift:soul_shaft"}, 1),
    "soul_vein_node": (["DGD", "GCG", "DGD"], {"D": "minecraft:polished_deepslate", "G": "pysift:siftite_gear",
                                               "C": "pysift:soul_crystal_block"}, 2),
    "charoite_prism": (["GCG", "CAC", "GCG"], {"G": "minecraft:glass", "C": "pysift:charoite", "A": "minecraft:amethyst_shard"}, 2),
    "soul_grinder": (["PSP", "IGI", "PEP"], {"P": "minecraft:polished_deepslate", "S": "minecraft:stonecutter",
                                             "I": "pysift:siftite_gear", "G": "minecraft:grindstone",
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
# siftite cogwheels: the gear goes on a shaft; a large one is a cogwheel with two more gears; the gearbox is a cogwheel
# encased in deepslate and patina (Create's way)
for name, ingredients in (("soul_cogwheel", ["pysift:soul_shaft", "pysift:siftite_gear"]),
                          ("large_soul_cogwheel", ["pysift:soul_cogwheel", "pysift:siftite_gear", "pysift:siftite_gear"]),
                          ("soul_gearbox", ["pysift:soul_cogwheel", "minecraft:polished_deepslate", "pysift:patina_ingot"])):
    wj(D / f"pysift/recipe/{name}.json", {"type": "minecraft:crafting_shapeless", "category": "redstone",
                                          "ingredients": ingredients, "result": {"id": f"pysift:{name}"}})
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
# recipe-book unlocks (like the rest of the mod): a recipe shows up once you carry one of its pysift ingredients
for f in sorted((D / "pysift/recipe").glob("*.json")):
    r = json.loads(f.read_text(encoding="utf-8"))
    if r.get("category") != "redstone" or r.get("result", {}).get("id", "").removeprefix("pysift:") not in set(BLOCKS) | {"siftite_gear"}:
        continue
    used = list(r["key"].values()) if "key" in r else r["ingredients"]
    needs = sorted({u for u in used if isinstance(u, str) and u.startswith("pysift:")}) or sorted({u for u in used if isinstance(u, str)})
    crit = {f"has_{n.split(':')[1]}": {"trigger": "minecraft:inventory_changed", "conditions": {"items": [{"items": n}]}} for n in needs}
    crit["has_the_recipe"] = {"trigger": "minecraft:recipe_unlocked", "conditions": {"recipes": f"pysift:{f.stem}"}}
    wj(D / f"pysift/advancement/recipes/redstone/{f.stem}.json", {
        "parent": "minecraft:recipes/root", "criteria": crit, "requirements": [sorted(crit)],
        "rewards": {"recipes": [f"pysift:{f.stem}"]}})
(D / "pysift/advancement/recipes/redstone/patina_gear.json").unlink(missing_ok=True)
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

# ------------------------------------------------------------------ GUI backgrounds (176 x 166 on a 256 x 256 sheet), painted
# Same layout as vanilla containers (title at 8,6, inventory label at 8,72, player slots at 8,84 / hotbar 8,142) and
# the slot positions of SpiritEngineMenu / SoulGrinderMenu. The panel stays light so the dark label text reads.
G_OUT = (24, 30, 38)
G_HI = (236, 244, 240)
G_PANEL = (188, 200, 199)
G_PANEL2 = (178, 191, 191)
G_SHADOW = (92, 108, 112)
G_SLOT_IN = (132, 144, 146)
G_SLOT_DARK = (58, 66, 74)
G_SOUL = [(18, 70, 84), (30, 116, 126), (60, 170, 172)]
G_GEAR = [(110, 28, 64), (184, 46, 106), (230, 92, 148)]


def gui_panel():
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    px = im.load()
    W, H = 176, 166
    for y in range(H):
        for x in range(W):
            corner = (x < 2 or x > W - 3) and (y < 2 or y > H - 3)
            if corner and (x in (0, W - 1) or y in (0, H - 1)):
                continue                                   # rounded outer corners
            edge = x == 0 or y == 0 or x == W - 1 or y == H - 1
            if edge or (corner and (x in (1, W - 2) or y in (1, H - 2))):
                px[x, y] = (*G_OUT, 255)
            elif x <= 2 or y <= 2:
                px[x, y] = (*G_HI, 255)
            elif x >= W - 3 or y >= H - 3:
                px[x, y] = (*G_SHADOW, 255)
            else:   # a faint diagonal brushed texture so the panel is not flat
                px[x, y] = (*(G_PANEL2 if (x + 2 * y) % 11 == 0 else G_PANEL), 255)
    return im


def recess(im, x0, y0, w, h, inner=G_SLOT_IN):
    """A recessed box (slot style): dark top-left edge, light bottom-right edge."""
    px = im.load()
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if x == x0 or y == y0:
                px[x, y] = (*G_SLOT_DARK, 255)
            elif x == x0 + w - 1 or y == y0 + h - 1:
                px[x, y] = (*G_HI, 255)
            else:
                px[x, y] = (*inner, 255)


def slot(im, x, y):
    recess(im, x - 1, y - 1, 18, 18)


def inventory(im):
    for r in range(3):
        for c in range(9):
            slot(im, 8 + c * 18, 84 + r * 18)
    for c in range(9):
        slot(im, 8 + c * 18, 142)


def gear_emblem(im, cx, cy):
    """A small siftite cogwheel emblem (8 teeth) in the corner of the panel."""
    px = im.load()
    for y in range(cy - 7, cy + 8):
        for x in range(cx - 7, cx + 8):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx)) % 45
            tooth = abs(a - 22.5) > 11
            if d <= 2:
                continue
            if d <= 5 or (d <= 7 and tooth):
                px[x, y] = (*G_GEAR[2 if dx + dy < -2 else 1 if dx + dy < 3 else 0], 255)


engine_gui = gui_panel()
inventory(engine_gui)
slot(engine_gui, 56, 53)                                    # fuel
recess(engine_gui, 55, 35, 16, 16, inner=G_SOUL[0])         # the firebox (the screen fills it with the burn level)
recess(engine_gui, 82, 17, 88, 52, inner=(200, 212, 210))   # read-out plaque for speed / capacity / load
gear_emblem(engine_gui, 160, 8)
grinder_gui = gui_panel()
inventory(grinder_gui)
slot(grinder_gui, 56, 35)                                   # input
slot(grinder_gui, 116, 35)                                  # result
slot(grinder_gui, 116, 60)                                  # soul essence
recess(grinder_gui, 79, 38, 26, 8, inner=G_SOUL[0])         # progress trough (filled by the screen)
for x in (83, 89, 95, 101):                                 # trough ribs
    grinder_gui.putpixel((x, 41), (*G_SOUL[1], 255))
gear_emblem(grinder_gui, 160, 8)
for name, im in (("spirit_engine", engine_gui), ("soul_grinder", grinder_gui)):
    out = A / f"textures/gui/container/{name}.png"
    art_guard.save(im, out)


def siftite_gear():
    """16x16 item: an 8-tooth gear in the siftite ingot's palette (pink gold, like every gear). Hand-made mask; lit from the top left,
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
    pal = [(61, 16, 36), (125, 28, 71), (184, 46, 106), (220, 62, 133), (240, 98, 156), (250, 130, 181), (252, 196, 214)]
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


art_guard.save(siftite_gear(), A / "textures/item/siftite_gear.png")
wj(A / "models/item/siftite_gear.json", {"parent": "minecraft:item/generated", "textures": {"layer0": "pysift:item/siftite_gear"}})
wj(A / "items/siftite_gear.json", {"model": {"type": "minecraft:model", "model": "pysift:item/siftite_gear"}})
for stale in ("textures/item/patina_gear.png", "models/item/patina_gear.json", "items/patina_gear.json"):
    (A / stale).unlink(missing_ok=True)
(D / "pysift/recipe/patina_gear.json").unlink(missing_ok=True)

# ------------------------------------------------------------------ lang (merge, keep line endings)
LANG = {f"block.pysift.{n}": (v[0], v[1]) for n, v in BLOCKS.items()}
# 26.3 block items read item.pysift.<id> (the registration may not use the block key)
LANG.update({f"item.pysift.{n}": (v[0], v[1]) for n, v in BLOCKS.items()})
LANG["item.pysift.siftite_gear"] = ("Siftite Gear", "隙浮金齒輪")
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
    "gui.pysift.soul_power.liquid": ("Piped: %s mB", "管線靈液：%s mB"),
    "message.pysift.soul_wave.frequency": ("Tuned to %s", "頻率：%s"),
    "message.pysift.soul_wave.empty": ("Tune it with a resonant music disc", "放入一張共鳴唱片來設定頻率"),
    "message.pysift.soul_gauge.status": ("%s RPM · load %s / %s SP (%s%%)", "%s RPM · 負載 %s / %s SP（%s%%）"),
    "message.pysift.soul_gauge.overloaded": ("Overloaded! %s / %s SP", "過載！%s / %s SP"),
    "message.pysift.soul_crank.too_heavy": ("Too heavy to crank: load %s / %s SP", "負載太大，搖不動：%s / %s SP"),
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
