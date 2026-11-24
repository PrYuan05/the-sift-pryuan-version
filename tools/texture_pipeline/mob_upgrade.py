"""Upgrade a Sift mob texture and paint its climate variants (user, 2026-11-24).

  python -I tools/texture_pipeline/mob_upgrade.py <mob> [--preview]

Per mob (MOBS below):
  * materials   each opaque pixel is assigned to a material by its colour (hue range, saturation, value). Every material
                gets a longer ramp built from its own colours: the darkest goes a little darker with the hue turned cool,
                the lightest a little lighter with the hue turned warm (minecraft-texture-crafter step 2), with the steps in
                between interpolated, so neighbouring ramp steps are close (soft transitions) and nothing is airbrushed.
  * shading     the pixel moves up or down its material's ramp: lit at the top of each model face, darker towards its
                bottom and edges, up faces lighter, down faces darker; fur gets hanging strands (per-column streaks) with
                lighter tips at the fur's lower edge (long outer hair is lighter: Highland cattle reference); skin gets soft
                2x2 mottling. Shifts are balanced around zero so the palette stays within 10 % of the original.
  * tropical    less fur (the fur's lower edge pulled up), more saturated, flowers on the fur.
  * cold        more fur (the lower edge hangs further down, ragged), cooler and less saturated, frosted fur tips.
The original is never read from the live file: it comes from the snapshot (.texture_backups/20261124_mob_originals), so
re-running always starts from the original. Faces come from the GeckoLib model, so only pixels the model uses are touched
and the silhouette (alpha) never changes."""
import colorsys, json, math, random, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/pysift"
SNAP = ROOT / ".texture_backups/20261124_mob_originals/files"

# ---------------------------------------------------------------------------------------------------------------- mobs
# material: (name, hue_lo, hue_hi, sat_lo, sat_hi, val_lo, val_hi, kind)  - first match wins; kind = fur | skin | plant | keep
MOBS = {
    "nuzzle": {
        "materials": [
            ("eye", 0, 360, 0.0, 0.08, 0.0, 0.35, "keep"),
            ("fur", 335, 15, 0.42, 1.0, 0.45, 1.0, "fur"),
            ("skin", 0, 30, 0.15, 0.42, 0.25, 0.55, "skin"),
            ("plant", 100, 190, 0.15, 1.0, 0.3, 1.0, "plant"),
        ],
        # tropical flowers on the fur: plumeria (warm white petals, yellow centre) - reads well on red fur
        "flower": [(244, 236, 214), (226, 212, 186), (248, 205, 92), (214, 170, 72)],
        "flowers": 0,          # no flat painted flowers: they are all 3D parts of the tropical model (user)
        # the eyes (a 2x1 plate each, uv x 3, y 2..3) were one light green and one pure black pixel: a half green, half
        # black dash; that was the design: looking outwards, the black pupil on the outer side, light green on the inner side
        # (user). Kept, with the palette's light green and a near-black pupil instead of pure black.
        "pixels": {(3, 2): (142, 187, 151), (3, 3): (30, 26, 32)},   # looking inwards: black pupil inside (user, 11-24)
        # shearable like a sheep (user): also writes <mob><climate>_sheared.png (skin where the fur was) and
        # <mob><climate>_fur.png (the fur alone in light greys, tinted with the dye colour in game)
        "shearable": True,
        # the top of the fur shell had transparent ragged holes along one edge (copied from the side fringe): on the model
        # they showed as missing fur at the top-back corner (user, screenshot). Fill them with fur (up/down faces, 16 wide)
        "fill_holes": [("up", 16), ("down", 16)],
    },
    # ---- the mobs below use the generic part painter (paint_parts; regions in tools/models/build_<mob>_variants.py)
    "lootkin": {
        # pastel patchwork coat (mint, peach, cream, lilac at the same lightness): one material per hue so the pattern
        # stays; reference fennec fox (pale sandy coat, lighter hair tips) / arctic fox for the cold ruff
        "materials": [
            ("eye", 0, 360, 0.0, 1.0, 0.0, 0.55, "keep"),
            ("mouth", 340, 10, 0.4, 1.0, 0.6, 1.0, "keep"),
            ("crest", 170, 210, 0.3, 1.0, 0.55, 1.0, "plant"),
            ("feet", 205, 245, 0.13, 0.3, 0.7, 1.0, "skin"),
            ("mint", 100, 170, 0.05, 0.25, 0.7, 1.0, "fur"),
            ("peach", 0, 40, 0.05, 0.25, 0.7, 1.0, "fur"),
            ("cream", 40, 90, 0.05, 0.25, 0.7, 1.0, "fur"),
            ("lilac", 280, 340, 0.05, 0.25, 0.7, 1.0, "fur"),
        ],
        "ramps": {"mint": (0.8, 1.03), "peach": (0.8, 1.03), "cream": (0.8, 1.03), "lilac": (0.8, 1.03),
                  "crest": (0.8, 1.1)},
        "coverage": False, "cold_hue": 200, "cold_fur_shift": 0.2,
        "parts": {
            "fluff": [(150, 166, 196), (186, 200, 222), (220, 228, 240)],      # arctic-fox winter coat: blue-grey
            "flowers": {   # desert rose (magenta, yellow eye) and an apricot dune flower (dark red-brown eye)
                "a": {"petal": [(250, 178, 206), (236, 116, 162), (200, 72, 128)],
                      "centre": [(252, 228, 112), (240, 198, 82), (240, 198, 82), (206, 150, 58)]},
                "b": {"petal": [(252, 214, 150), (244, 156, 82), (212, 106, 58)],
                      "centre": [(158, 76, 62), (128, 56, 50), (128, 56, 50), (98, 42, 42)]},
            },
            "leaf": [(56, 116, 94), (88, 158, 116), (148, 198, 138)],          # succulent green
        },
    },
    "slabber": {
        # moss (hanging drips = the "fur": lighter tips), teal-grey lichen patches and the purple-grey soil (mottled, the
        # soil look stays); flowers, tongue and eyes keep their own colours. Reference Highland cattle / musk ox.
        "materials": [
            ("eye", 0, 360, 0.0, 0.05, 0.9, 1.0, "keep"),
            ("pupil", 200, 250, 0.4, 1.0, 0.5, 1.0, "keep"),
            ("stem", 0, 25, 0.3, 0.6, 0.3, 0.6, "keep"),
            ("bloom", 35, 70, 0.3, 1.0, 0.85, 1.0, "plant"),
            ("tongue", 320, 350, 0.15, 0.5, 0.7, 1.0, "skin"),
            ("moss", 145, 168, 0.3, 0.7, 0.4, 0.7, "fur"),
            ("lichen", 168, 185, 0.1, 0.45, 0.25, 0.6, "skin"),
            ("soil", 250, 300, 0.05, 0.3, 0.2, 0.5, "skin"),
        ],
        "ramps": {"moss": (0.82, 1.12), "soil": (0.8, 1.16), "lichen": (0.94, 1.12)},
        # the eye whites were pure #FFFFFF: a warm off-white, a touch darker on the lower row
        "pixels": {**{(x, 5): (240, 240, 230) for x in range(2, 6)}, **{(x, 6): (224, 226, 216) for x in range(2, 6)}},
        "coverage": False, "cold_hue": 195, "cold_fur_shift": 0.35,
        "parts": {
            "fluff": [(82, 116, 112), (128, 162, 152), (192, 214, 204)],       # frosted silver-green moss locks
            "flowers": {   # hibiscus (coral pink, yellow eye) and a golden allamanda (orange throat)
                "a": {"petal": [(252, 170, 176), (238, 96, 120), (196, 52, 86)],
                      "centre": [(252, 232, 120), (238, 196, 76), (238, 196, 76), (204, 150, 52)]},
                "b": {"petal": [(254, 238, 132), (246, 196, 64), (214, 146, 40)],
                      "centre": [(232, 120, 52), (204, 92, 44), (204, 92, 44), (164, 70, 40)]},
            },
            "leaf": [(34, 96, 62), (56, 140, 80), (112, 186, 98)],             # glossy rainforest green
        },
    },
    "prickle": {
        # banded lavender / violet spine coat (the "fur": strands, lighter tips), pink and icy-cyan crystal spine tips
        # (glossy), a pale muzzle and belly; reference hedgehog (spines banded, pale tips)
        "materials": [
            ("eye", 0, 360, 0.0, 1.0, 0.0, 0.4, "keep"),
            ("pale", 0, 360, 0.0, 0.07, 0.8, 1.0, "skin"),
            ("pink", 285, 315, 0.15, 1.0, 0.7, 1.0, "shell"),
            ("crystal", 170, 195, 0.08, 0.5, 0.7, 1.0, "shell"),
            ("band", 235, 270, 0.45, 1.0, 0.5, 1.0, "shell"),           # the dark violet spine bands
            ("coat", 235, 270, 0.12, 0.45, 0.5, 1.0, "fur"),
        ],
        "ramps": {"pale": (0.9, 1.05), "crystal": (0.88, 1.06), "pink": (0.88, 1.04), "coat": (1.0, 0.99),
                  "band": (1.0, 1.06)},
        # cold: clearly cooler (user 11-24: the white fur alone had lowered blue-minus-red): the lavender coat and the
        # spine tips turn towards periwinkle / ice blue and keep their saturation, pale fur gets a blue-grey tint
        "coverage": False, "cold_hue": 212, "cold_fur_shift": 0.5, "cold_fur_sat": 1.0,
        "cold_body_hue": 205, "cold_shift": 0.35, "cold_sat": 1.0, "cold_tint": (212, 0.16),
        "parts": {
            "fluff": [(128, 142, 190), (170, 186, 224), (206, 220, 240)],      # frosty blue-grey face fur
            "flowers": {   # orchid-pink with a gold eye, and a sunny yellow bloom with an orange eye
                "a": {"petal": [(252, 196, 236), (238, 112, 206), (196, 64, 168)],
                      "centre": [(252, 232, 120), (238, 196, 76), (238, 196, 76), (204, 150, 52)]},
                "b": {"petal": [(254, 240, 140), (248, 204, 70), (216, 150, 40)],
                      "centre": [(236, 124, 56), (206, 94, 46), (206, 94, 46), (166, 72, 42)]},
            },
            "leaf": [(40, 110, 76), (66, 156, 96), (128, 202, 112)],
        },
    },
    "dartback": {
        # purple armour plates with a pink ridge stripe (glossy, lit top rim: armadillo / pangolin scutes), red spike
        # tips, an ochre-and-tan banded underside (skin); eyes and teeth kept
        "materials": [
            ("eye", 0, 360, 0.0, 1.0, 0.0, 0.36, "keep"),
            ("tooth", 0, 40, 0.0, 0.2, 0.9, 1.0, "keep"),
            ("spike", 340, 362, 0.4, 1.0, 0.6, 1.0, "shell"),
            ("ridge", 295, 335, 0.38, 0.7, 0.7, 1.0, "shell"),
            ("plate", 270, 335, 0.35, 0.7, 0.3, 0.7, "shell"),
            ("ochre", 36, 56, 0.3, 0.8, 0.5, 1.0, "plant"),          # the underside bands already step in colour:
            ("rust", 12, 25, 0.6, 0.8, 0.5, 1.0, "plant"),           # only a gentle top-down light on them
            ("sand", 12, 36, 0.3, 0.6, 0.8, 1.0, "plant"),
            ("tan", 12, 36, 0.3, 0.8, 0.5, 0.8, "plant"),
        ],
        "ramps": {"plate": (0.97, 1.03), "ridge": (0.96, 1.03), "ochre": (0.97, 1.02), "tan": (0.97, 1.02),
                  "sand": (0.97, 1.02), "rust": (0.96, 1.03),
                  "spike": (0.94, 1.0)},
        "coverage": False,
        "parts": {
            "fluff": [(150, 112, 96), (196, 160, 136), (232, 214, 200)],       # pale ochre-grey under-shell hair, frosted
            "flowers": {   # magenta passion-flower pink and a golden bloom, both with dark eyes (reads on the purple)
                "a": {"petal": [(254, 214, 236), (246, 136, 196), (204, 76, 150)],
                      "centre": [(252, 232, 120), (238, 196, 76), (238, 196, 76), (204, 150, 52)]},
                "b": {"petal": [(254, 244, 170), (250, 210, 84), (220, 156, 44)],
                      "centre": [(176, 70, 52), (146, 52, 46), (146, 52, 46), (112, 40, 40)]},
            },
            "leaf": [(40, 112, 70), (70, 160, 90), (138, 206, 112)],
        },
    },
    "fusefly": {
        # a glowing yellow lantern body (firefly lantern: lit core, a slightly deeper orange at the lower edges) with
        # green spots; the eye (a black pixel and a white glint) is kept, the glint no longer pure #FFFFFF
        "materials": [
            ("eye", 0, 360, 0.0, 1.0, 0.0, 0.3, "keep"),
            ("spot", 95, 170, 0.3, 1.0, 0.5, 1.0, "plant"),
            ("glow", 25, 55, 0.3, 0.7, 0.85, 1.0, "jelly"),
        ],
        "ramps": {"glow": (0.9, 1.0), "spot": (0.9, 1.08)},
        "pixels": {(0, 1): (238, 238, 228)},
        "coverage": False, "cold_shift": 0.04, "cold_sat": 0.72,   # cold: a paler lemon glow (a hue turn makes it lime)
        "parts": {
            "fluff": [(166, 170, 194), (204, 208, 226), (232, 234, 242)],      # woolly-moth pile, frosted
            "flowers": {   # a scarlet bloom (reads on the yellow) and a magenta orchid
                "a": {"petal": [(254, 150, 136), (232, 70, 70), (180, 36, 52)],
                      "centre": [(252, 236, 140), (240, 200, 80), (240, 200, 80), (206, 150, 52)]},
                "b": {"petal": [(250, 190, 240), (226, 108, 214), (168, 58, 168)],
                      "centre": [(252, 214, 96), (232, 170, 64), (232, 170, 64), (196, 130, 52)]},
            },
            "leaf": [(36, 120, 74), (64, 168, 96), (130, 214, 116)],
        },
    },
    "wobble": {
        # teal jelly (light gathers in the upper part of each face, a deeper core: translucent like an axolotl's skin)
        # over a green lower band; the pale highlight, eyes, glints and the mouth line are kept
        "materials": [
            ("eye", 0, 360, 0.0, 1.0, 0.0, 0.3, "keep"),
            ("glint", 0, 360, 0.0, 0.1, 0.9, 1.0, "keep"),
            ("shine", 185, 200, 0.1, 0.3, 0.85, 1.0, "keep"),
            ("algae", 115, 150, 0.4, 1.0, 0.6, 1.0, "jelly"),
            ("pale", 150, 200, 0.3, 0.5, 0.4, 1.0, "jelly"),          # the light, see-through rim
            ("jelly", 150, 200, 0.5, 1.0, 0.4, 1.0, "jelly"),
        ],
        "ramps": {"jelly": (1.0, 1.08), "algae": (0.94, 1.08), "pale": (0.94, 1.06)},
        # cold: the teal jelly turns an icy azure (clearly cooler, user 11-24), the green band a cold sea-green
        "coverage": False, "cold_body_hue": 212, "cold_shift": 0.5, "cold_sat": 1.0, "cold_tint": (208, 0.16),
        "parts": {
            "fluff": [(118, 156, 204), (166, 200, 234), (206, 226, 246)],      # frosty blue-grey fluff
            "ice": [(120, 178, 210), (180, 220, 238), (222, 240, 248)],
            "flowers": {   # pink lotus with a golden seed head, and a violet water hyacinth
                "a": {"petal": [(254, 222, 236), (244, 150, 190), (206, 88, 146)],
                      "centre": [(250, 226, 110), (236, 192, 70), (236, 192, 70), (200, 148, 52)]},
                "b": {"petal": [(226, 206, 252), (170, 128, 236), (116, 80, 196)],
                      "centre": [(252, 222, 96), (232, 176, 60), (232, 176, 60), (196, 136, 48)]},
            },
            "leaf": [(34, 110, 70), (60, 158, 88), (120, 200, 104)],           # lily pad green
        },
    },
}


# ----------------------------------------------------------------------------------------------------------- helpers
def hsv(c):
    h, s, v = colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)
    return h * 360, s, v


def rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, max(0, min(1, s)), max(0, min(1, v)))
    return (round(r * 255), round(g * 255), round(b * 255))


def lum(c):
    return 0.2126 * c[0] / 255 + 0.7152 * c[1] / 255 + 0.0722 * c[2] / 255


def hue_in(h, lo, hi):
    return lo <= h <= hi if lo <= hi else (h >= lo or h <= hi)


def hue_lerp(a, b, t):
    d = ((b - a + 180) % 360) - 180
    return (a + d * t) % 360


def material_of(c, mats):
    h, s, v = hsv(c)
    for m in mats:
        name, hlo, hhi, slo, shi, vlo, vhi, kind = m
        if hue_in(h, hlo, hhi) and slo <= s <= shi and vlo <= v <= vhi:
            return name, kind
    return None, "keep"


def build_ramp(colours, steps=8, warm=+9.0, cool=-12.0, dark=0.93, light=1.04):
    """A ramp from the material's own colours: darkest a bit darker and cooler, lightest a bit lighter and warmer."""
    DARK, LIGHT = dark, light
    cs = sorted(colours, key=lum)
    dark, light = hsv(cs[0]), hsv(cs[-1])
    lo = (dark[0] + cool, min(1, dark[1] * 1.06), dark[2] * DARK)
    hi = (light[0] + warm, light[1] * 0.93, min(0.97, light[2] * LIGHT + 0.01))
    ramp = []
    for i in range(steps):
        t = i / (steps - 1)
        # a slightly desaturated middle (desaturated midtone bridge)
        s = lo[1] + (hi[1] - lo[1]) * t - 0.03 * math.sin(math.pi * t)
        ramp.append(rgb(hue_lerp(lo[0], hi[0], t), s, lo[2] + (hi[2] - lo[2]) * t))
    return ramp


def nearest_index(c, ramp):
    l = lum(c)
    return min(range(len(ramp)), key=lambda i: abs(lum(ramp[i]) - l))


# ------------------------------------------------------------------------------------------------------------ faces
def faces(geo_path):
    """Every textured face rectangle: (x0, y0, w, h, face, flip_u, flip_v). Mirrored (negative) uv sizes are normalised."""
    g = json.loads(Path(geo_path).read_text(encoding="utf-8"))["minecraft:geometry"][0]
    out = []
    for bone in g["bones"]:
        for cube in bone.get("cubes", []):
            uv = cube.get("uv")
            if not isinstance(uv, dict):
                continue
            for face, f in uv.items():
                (u, v), (w, h) = f["uv"], f["uv_size"]
                fu, fv = w < 0, h < 0
                x0, y0 = (u + w, v + h) if False else (min(u, u + w), min(v, v + h))
                w, h = abs(w), abs(h)
                if w >= 1 and h >= 1:
                    out.append((int(round(x0)), int(round(y0)), int(round(w)), int(round(h)), face, fu, fv,
                                f.get("uv_rotation", 0)))
    return out


def face_map(img, geo_path):
    """pixel -> (face, local u 0..1, local v 0..1 (0 = top of the face as seen on the model), face size)."""
    W, H = img.size
    m = {}
    protected = set()
    for x0, y0, w, h, face, fu, fv, rot in faces(geo_path):
        if w * h <= 4:                          # eyes, eyelids and other tiny details: never touched
            protected.update((x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h))
        for y in range(y0, min(H, y0 + h)):
            for x in range(x0, min(W, x0 + w)):
                lu = (x - x0 + 0.5) / w
                lv = (y - y0 + 0.5) / h
                if fv:
                    lv = 1 - lv
                if face in ("up", "down"):
                    lv = 0.5
                if (x, y) not in m:
                    m[(x, y)] = (face, lu, lv, w, h, x0, y0)
    for xy in protected:
        m.pop(xy, None)
    return m


# ---------------------------------------------------------------------------------------------------------- painting
def upgrade(mob, variant="normal", seed=7):
    cfg = MOBS[mob]
    src = Image.open(SNAP / f"textures/entity/{mob}.png").convert("RGBA")
    geo = RES / f"geckolib/models/entity/{mob}.geo.json"
    W, H = src.size
    px = src.load()
    fmap = face_map(src, geo)
    rnd = random.Random(seed)

    # materials and their ramps
    mat_px = {}
    for (x, y), _ in fmap.items():
        c = px[x, y]
        if c[3] == 0:
            continue
        name, kind = material_of(c[:3], cfg["materials"])
        if name and kind != "keep":
            mat_px.setdefault(name, []).append((x, y))
    kinds = {m[0]: m[7] for m in cfg["materials"]}
    ramps = {}
    for name, pts in mat_px.items():
        cols = list({px[x, y][:3] for x, y in pts})
        # skin has only two close browns in the original: a wider ramp so its light and shade actually show
        span = cfg.get("ramps", {}).get(name)          # per material (dark, light) when its own colours are too close
        if span:
            ramps[name] = build_ramp(cols, dark=span[0], light=span[1])
        else:
            ramps[name] = build_ramp(cols, dark=0.84, light=1.14) if kinds.get(name) == "skin" else build_ramp(cols)

    def is_mat(x, y, name):
        return 0 <= x < W and 0 <= y < H and px[x, y][3] and material_of(px[x, y][:3], cfg["materials"])[0] == name

    # fur coverage edits (climate) on side faces: fur directly above skin = the fur's lower edge
    fur_names = [n for n, k in kinds.items() if k == "fur" and n in mat_px]
    skin_names = [n for n, k in kinds.items() if k == "skin" and n in mat_px]
    owner = {}                                  # pixel -> material after coverage edits
    for name, pts in mat_px.items():
        for p in pts:
            owner[p] = name
    added, removed = set(), set()
    fur_first = next((n for n, k in kinds.items() if k == "fur" and n in mat_px), None)
    for face_name, min_w in cfg.get("fill_holes", []):
        for (x, y), info in fmap.items():
            if info[0] == face_name and info[3] >= min_w and px[x, y][3] == 0 and fur_first:
                owner[(x, y)] = fur_first
    if fur_names and variant in ("tropical", "cold") and cfg.get("coverage", True):
        # Nuzzle's fur is a shell (the outer 16x16x16 box) with ragged transparent holes; the skin is a box inside it.
        # cold: the fur grows into the holes next to it (a fuller coat); tropical: the fur's ragged edges thin out.
        fur = fur_names[0]
        passes, chance = (3, 0.7) if variant == "cold" else (2, 0.75)
        for _ in range(passes):
            change = []
            for (x, y), info in fmap.items():
                face = info[0]
                opaque = (x, y) in owner and (x, y) not in removed
                if variant == "cold" and not opaque and px[x, y][3] == 0 and (x, y) not in added:
                    near = [q for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                            if owner.get(q) == fur and fmap.get(q, ("",))[0] == face]
                    if near and rnd.random() < chance:
                        change.append((x, y))
                elif variant == "tropical" and owner.get((x, y)) == fur and (x, y) not in removed                         and face not in ("up", "down"):          # only the side fringes thin out; the top stays covered
                    holes = [q for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                             if fmap.get(q, ("",))[0] == face and (px[q[0], q[1]][3] == 0 or q in removed)]
                    if holes and rnd.random() < chance:
                        change.append((x, y))
            for xy in change:
                if variant == "cold":
                    owner[xy] = fur
                    added.add(xy)
                else:
                    removed.add(xy)
        for xy in removed:
            owner.pop(xy, None)

    # per-column strand offsets for fur, per 2x2 block mottling for skin
    strand = {}
    mottle = {}

    def strand_at(key):
        if key not in strand:
            strand[key] = rnd.choice((-0.5, -0.25, 0, 0, 0.25, 0.5))
        return strand[key]

    def mottle_at(key):
        if key not in mottle:
            mottle[key] = rnd.choice((-0.5, 0, 0, 0.5))
        return mottle[key]

    out = src.copy()
    op = out.load()
    for (x, y), name in owner.items():
        face, lu, lv, fw, fh, x0, y0 = fmap[(x, y)]
        kind = kinds[name]
        ramp = ramps[name]
        base = px[x, y][:3]
        if material_of(base, cfg["materials"])[0] != name:      # pixel changed material (fur coverage edit)
            base = ramp[len(ramp) // 2]
        idx = nearest_index(base, ramp)
        # light: faces lit from the top; up faces lighter, down darker; 1 px darker rim on the face's sides and bottom
        off = 0.0
        if face == "up":
            off += 0.6
        elif face == "down":
            off -= 1.0
        else:
            off += 0.9 * (0.5 - lv)
            if fh >= 4 and (y - y0 == fh - 1):
                off -= 0.5
        if kind == "fur":
            off += strand_at((face, x0, y0, x, y // 3 if face in ("up", "down") else 0))
            below = (x, y + 1)
            if owner.get(below) != name and fmap.get(below, ("",))[0] == face and face not in ("up", "down"):
                off += 0.6                       # lighter hair tips at the fur's lower edge
        elif kind == "skin":
            off += 1.0 * (0.5 - lv)              # skin: a stronger top-to-bottom gradient so it is not one flat brown
            off += 1.2 * (0.25 - abs(lu - 0.5)) # and lighter in the middle of the face than at its sides
            if fw > 8:                           # no mottling on small faces (the head): it smudges the eyes and nose
                off += mottle_at((x // 2, y // 2))
        elif kind == "plant":
            off += 0.3 * (0.5 - lv)
        elif kind == "shell":                    # chitin / armour plates: a lit top rim, darker lower half (beetle shell)
            off += 1.1 * (0.5 - lv) + 0.6 * (0.25 - abs(lu - 0.5))
            if fh >= 3 and y - y0 == 0 and face not in ("up", "down"):
                off += 0.6
        elif kind == "jelly":                    # jelly: light gathers in the upper part of each face, a soft core
            off += 1.0 * (0.5 - lv) + 0.8 * (0.25 - abs(lu - 0.5))
            if fw > 8:
                off += 0.5 * mottle_at((x // 3, y // 3))
        i = max(0, min(len(ramp) - 1, int(round(idx + off))))
        c = ramp[i]
        h, s, v = hsv(c)
        if variant == "tropical":
            s = min(0.92, s * 1.18 + 0.03)
            v = min(0.97, v * 1.03)
            if kind == "plant":
                h = hue_lerp(h, 110, 0.15)
        elif variant == "cold":
            if kind == "fur":
                h = hue_lerp(h, cfg.get("cold_hue", 330), cfg.get("cold_fur_shift", 0.45))  # nuzzle: red -> rose
                s *= cfg.get("cold_fur_sat", 0.78)
                below = (x, y + 1)
                if owner.get(below) != name and fmap.get(below, ("",))[0] == face and face not in ("up", "down"):
                    v = min(0.95, v * 1.12)      # frosted tips
                    s *= 0.7
            else:
                h = hue_lerp(h, cfg.get("cold_body_hue", 200), cfg.get("cold_shift", 0.12))
                s *= cfg.get("cold_sat", 0.85)
            tint = cfg.get("cold_tint")          # (hue, min saturation): pale / white pixels turn a frosty blue-grey
            if tint and s < tint[1]:
                h, s = tint[0], tint[1] * 0.5 + s * 0.5
        op[x, y] = rgb(h, s, v) + (255,)

    for (x, y) in removed:
        op[x, y] = (0, 0, 0, 0)
    if variant == "tropical":
        paint_flowers(out, owner, fmap, fur_names, cfg, rnd)
    if "parts" in cfg:
        extra_fur = paint_parts(out, mob, variant, cfg, ramps, rnd)
    else:
        extra_fur = paint_model_extras(out, mob, variant, ramps.get(fur_names[0]) if fur_names else None, rnd)
    for (x, y), c in cfg.get("pixels", {}).items():
        out.putpixel((x, y), c + (255,))
    extras = {}
    if cfg.get("shearable") and fur_names and skin_names:
        fur, skin = fur_names[0], skin_names[0]
        sheared = out.copy()
        sp = sheared.load()
        furimg = Image.new("RGBA", out.size)
        fp = furimg.load()
        skin_ramp = ramps[skin]
        fur_px = [xy for xy, n in owner.items() if n == fur]
        lums = [lum(op[x, y]) for x, y in fur_px]
        lo, hi = (min(lums), max(lums)) if lums else (0, 1)
        for (x, y) in fur_px:
            face, lu, lv, fw, fh, x0, y0 = fmap[(x, y)]
            # sheared: bare skin, lit like the rest (no strands, a soft 2x2 mottle)
            off = 0.6 if face == "up" else -1.0 if face == "down" else 0.9 * (0.5 - lv)
            off += mottle_at((x // 2, y // 2)) * 0.6
            i = max(0, min(len(skin_ramp) - 1, int(round(len(skin_ramp) / 2 - 0.5 + off))))
            c = skin_ramp[i]
            if variant == "cold":
                h_, s_, v_ = hsv(c)
                c = rgb(hue_lerp(h_, 200, 0.12), s_ * 0.85, v_)
            sp[x, y] = c + (255,)
            # fur layer: the fur's own light and shade as light greys (vanilla sheep wool is white, tinted by the dye)
            t = (lum(op[x, y]) - lo) / max(1e-6, hi - lo)
            g = 0.60 + 0.38 * t
            fp[x, y] = (round(255 * g), round(252 * g), round(248 * g), 255)
        for (x, y) in extra_fur:
            sp[x, y] = (0, 0, 0, 0)               # sheared: the extra fur parts (ruff, mane, cuffs) are gone
            t = (lum(op[x, y]) - lo) / max(1e-6, hi - lo)
            g = 0.60 + 0.38 * max(0.0, min(1.0, t))
            fp[x, y] = (round(255 * g), round(252 * g), round(248 * g), 255)
        extras["_sheared"] = sheared
        extras["_fur"] = furimg
    return out, extras


def paint_model_extras(img, mob, variant, fur_ramp, rnd):
    """Paint the uv rectangles of the parts the climate variant models add (tools/models/build_<mob>_variants.py).
    Returns the pixels that are fur (for the sheared and dye textures)."""
    path = ROOT / f"tools/models/build_{mob}_variants.py"
    if not path.exists() or not fur_ramp:
        return set()
    import importlib.util
    spec = importlib.util.spec_from_file_location("variants", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p = img.load()
    fur_px = set()
    if variant == "normal":                      # the normal model does not use these areas: leave them empty
        for (x0, y0, w, h) in mod.REGIONS.values():
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    p[x, y] = (0, 0, 0, 0)
        return fur_px
    if variant == "cold":
        for name, (x0, y0, w, h) in mod.REGIONS.items():
            if name.startswith(("petal", "centre")):
                continue
            strands = [rnd.choice((-0.5, 0, 0, 0.5)) for _ in range(w)]
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    v = (y - y0 + 0.5) / h
                    i = len(fur_ramp) / 2 + 1.4 * (0.5 - v) + strands[x - x0] + (0.8 if y == y0 + h - 1 and h > 2 else 0)
                    if name.startswith("tail"):          # the tail is the lightest, fluffiest fur (a rabbit's scut)
                        i = len(fur_ramp) - 2 + 0.8 * (0.5 - v) - 0.6 * abs((x - x0 + 0.5) / w - 0.5)
                    c = fur_ramp[max(0, min(len(fur_ramp) - 1, int(round(i))))]
                    hh, ss, vv = hsv(c)
                    hh, ss = hue_lerp(hh, 330, 0.45), ss * 0.78
                    if y == y0 + h - 1 and h > 2:          # frosted tips
                        vv, ss = min(0.95, vv * 1.12), ss * 0.7
                    p[x, y] = rgb(hh, ss, vv) + (255,)
                    fur_px.add((x, y))
    else:
        # hibiscus: cream petals with a pink blush towards the edge, a yellow centre (reads on the red fur)
        x0, y0, w, h = mod.REGIONS["petal"]
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
                corner = x in (x0, x0 + w - 1) and y in (y0, y0 + h - 1)
                # every petal pixel opaque (a cut-out corner shows a gap in the petal's thickness from the side):
                # the corners are a deeper pink, so the bloom still reads round
                p[x, y] = ((206, 104, 132, 255) if corner else (238, 150, 170, 255) if edge else (250, 232, 214, 255))
        x0, y0, w, h = mod.REGIONS["petal_edge"]
        for x in range(x0, x0 + w):
            p[x, y0] = (226, 128, 152, 255)
        x0, y0, w, h = mod.REGIONS["centre"]
        cols = [(250, 214, 92), (236, 186, 70), (236, 186, 70), (214, 156, 58)]
        for i, (x, y) in enumerate((x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)):
            p[x, y] = cols[i] + (255,)
        x0, y0, w, h = mod.REGIONS["centre_side"]
        for x in range(x0, x0 + w):
            p[x, y0] = (214, 156, 58, 255)
    return fur_px


def _lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def paint_parts(img, mob, variant, cfg, ramps, rnd):
    """Generic painter for the parts the climate models add (mobs with a "parts" entry; Nuzzle keeps its own painter).
    REGIONS in tools/models/build_<mob>_variants.py are named "<role>.<key>":
      cold      fluff.*   long frosty fur (tufts, ruffs, cuffs): per-column strands, lit top, frosted lighter tips
                ball.*    a round fluffy tail / pompom: the lightest fluff, darker towards its sides
                ice.*     frost crystals: pale icy blue, lit top, a light rim
      tropical  petal.<k> / petal_edge.<k> / centre.<k> / centre_side.<k>   flower <k> (cfg parts.flowers[<k>])
                leaf.*    leaves (a darker midrib, lighter towards the tip), stem.*  stems
    parts.fluff is a material name (its ramp, turned cool like the cold fur) or a list of colours."""
    path = ROOT / f"tools/models/build_{mob}_variants.py"
    if not path.exists():
        return set()
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"variants_{mob}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p = img.load()
    if variant == "normal":
        for (x0, y0, w, h) in mod.REGIONS.values():
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    p[x, y] = (0, 0, 0, 0)
        return set()
    parts = cfg["parts"]

    def fluff_ramp():
        f = parts.get("fluff")
        if isinstance(f, str):
            hue, amt = cfg.get("cold_hue", 330), cfg.get("cold_fur_shift", 0.45)
            return [rgb(hue_lerp(hsv(c)[0], hue, amt), hsv(c)[1] * 0.78, hsv(c)[2]) for c in ramps[f]]
        return build_ramp(f)

    def put(x, y, c):
        p[x, y] = tuple(max(8, min(247, v)) for v in c[:3]) + (255,)

    cold_roles, tropical_roles = ("fluff", "ball", "ice", "tuft"), ("petal", "petal_edge", "centre", "centre_side", "leaf", "stem")
    for name, (x0, y0, w, h) in mod.REGIONS.items():
        role, _, key = name.partition(".")
        if (variant == "cold") != (role in cold_roles) or role not in cold_roles + tropical_roles:
            continue
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                p[x, y] = (0, 0, 0, 0)
        if role in ("fluff", "ball"):
            ramp = fluff_ramp()
            n = len(ramp)
            # hair locks: neighbouring columns alternate light / dark so single strands read; long regions get a
            # ragged hem (some columns end one pixel early)
            strands = [rnd.choice((-0.5, 0, 0.5)) + (0.6 if c % 2 == 0 else -0.6) for c in range(w)]
            short = {c for c in range(w) if h >= 5 and rnd.random() < 0.4}
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    v = (y - y0 + 0.5) / h
                    u = (x - x0 + 0.5) / w
                    if role == "fluff" and y == y0 + h - 1 and (x - x0) in short:
                        # the ragged hem in colour, not transparency (a hole shows a gap in the part's thickness):
                        # the short column's last pixel is the shaded under-hair
                        put(x, y, ramp[max(0, min(n - 1, int(round(n / 2 - 1.6 + strands[x - x0]))))])
                        continue
                    tip = (y == y0 + h - 1 or (y == y0 + h - 2 and (x - x0) in short)) and h > 2
                    if role == "ball":
                        i = n - 2 + 0.8 * (0.5 - v) - 1.2 * abs(u - 0.5)
                    else:
                        i = n / 2 + 1.6 * (0.5 - v) + strands[x - x0] + (0.8 if tip else 0)
                    c = ramp[max(0, min(n - 1, int(round(i))))]
                    if tip and role == "fluff":
                        hh, ss, vv = hsv(c)
                        c = rgb(hh, ss * 0.7, min(0.95, vv * 1.1))
                    put(x, y, c)
        elif role == "tuft":
            # a small round fluffy tuft (crossing boxes): darker roots at the top, short strands, lighter frosted tips
            # at the bottom, the corners a step darker so the tuft reads round
            ramp = fluff_ramp()
            n = len(ramp)
            strands = [rnd.choice((-0.5, 0, 0.5)) + (0.4 if c % 2 == 0 else -0.4) for c in range(w)]
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    v, u = (y - y0 + 0.5) / h, (x - x0 + 0.5) / w
                    i = n / 2 - 0.5 + 2.0 * (v - 0.5) + strands[x - x0] - 1.6 * max(0.0, abs(u - 0.5) - 0.25)
                    c = ramp[max(0, min(n - 1, int(round(i))))]
                    if y == y0 + h - 1 and h > 2:
                        hh, ss, vv = hsv(c)
                        c = rgb(hh, ss * 0.8, min(0.95, vv * 1.08))
                    put(x, y, c)
        elif role == "ice":
            ramp = build_ramp(parts.get("ice", [(150, 190, 214), (196, 226, 238), (226, 240, 246)]))
            n = len(ramp)
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    v = (y - y0 + 0.5) / h
                    i = (n - 1) * (1 - v) + (0.6 if x == x0 else -0.4 if x == x0 + w - 1 else 0)
                    put(x, y, ramp[max(0, min(n - 1, int(round(i))))])
        elif role in ("petal", "petal_edge", "centre", "centre_side"):
            fl = parts["flowers"][key.split("_")[0]]          # "a_cup": flower a's colours on another region
            light, mid, edge = fl["petal"]
            cen = fl["centre"]
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    u, v = (x - x0 + 0.5) / w - 0.5, (y - y0 + 0.5) / h - 0.5
                    ring = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
                    corner = x in (x0, x0 + w - 1) and y in (y0, y0 + h - 1)
                    if role == "petal":
                        # every petal pixel is opaque (a transparent corner shows a gap in the petal's thickness from
                        # the side): the bloom is rounded with colour, the corners a deeper shade of the petal (it curls
                        # back there), the big petals' diagonal corners too
                        lx, ly = x - x0, y - y0
                        if (corner and w >= 3 and h >= 3) or (w >= 6 and h >= 6 and
                                                               min(lx, w - 1 - lx) + min(ly, h - 1 - ly) < 2):
                            put(x, y, _lerp(mid, edge, 0.75))
                            continue
                        if key.endswith("_cup"):                 # a standing cup petal: deeper base, light tip
                            c = _lerp(mid, light, 1 - (y - y0) / max(1, h - 1))
                        elif w <= 5 and h <= 5:                  # small petals: light tips round a deeper throat
                            c = light if ring else mid
                        else:                                    # big: deep throat -> petal -> light tips (hibiscus)
                            d = min(1.0, math.hypot(u, v) * 2 / 0.95)
                            c = _lerp(edge, mid, d / 0.45) if d < 0.45 else _lerp(mid, light, (d - 0.45) / 0.55)
                    elif role == "petal_edge":
                        c = _lerp(mid, edge, 0.5 + 0.5 * abs(u) * 2)
                    elif role == "centre":
                        d = max(abs(u), abs(v)) * 2
                        c = _lerp(cen[0], cen[-1], d) if w > 2 or h > 2 else cen[(x - x0) + 2 * (y - y0)]
                    else:
                        c = cen[-1]
                    put(x, y, c)
        elif role in ("leaf", "stem"):
            dark, mid, light = parts.get("leaf", [(52, 112, 60), (78, 150, 78), (128, 190, 96)])
            for y in range(y0, y0 + h):
                for x in range(x0, x0 + w):
                    u, v = (x - x0 + 0.5) / w, (y - y0 + 0.5) / h
                    if role == "stem":
                        c = _lerp(mid, dark, v)
                    else:
                        along = u if w >= h else v               # leaves get lighter towards the tip
                        across = v if w >= h else u
                        c = _lerp(mid, light, along)
                        if abs(across - 0.5) < 0.5 / max(1, min(w, h)) + 0.01 and min(w, h) >= 3:
                            c = _lerp(dark, mid, along)          # midrib
                        elif min(w, h) >= 3 and (across < 1 / min(w, h) or across > 1 - 1 / min(w, h)):
                            c = _lerp(c, dark, 0.35)             # a slightly darker rim
                    put(x, y, c)
    return set()


def paint_flowers(img, owner, fmap, fur_names, cfg, rnd):
    """Small 5-pixel flowers (plus shape, shaded petals, a centre) on the fur, away from face borders."""
    if not fur_names or not cfg.get("flowers", 0):
        return
    p = img.load()
    petal, petal_dark, centre, centre_dark = cfg["flower"]
    spots = [xy for xy, n in owner.items() if n == fur_names[0]]
    rnd.shuffle(spots)
    placed = []
    for (x, y) in spots:
        if len(placed) >= cfg.get("flowers", 0):
            break
        cells = [(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        face = fmap[(x, y)][0]
        if face in ("up", "down"):                  # the model's own 3D flowers sit on the top
            continue
        if any(owner.get(c) != fur_names[0] or fmap.get(c, ("",))[0] != face for c in cells):
            continue
        if any(abs(x - a) + abs(y - b) < 6 for a, b in placed):
            continue
        p[x, y] = centre + (255,)
        p[x - 1, y] = petal + (255,)
        p[x, y - 1] = petal + (255,)
        p[x + 1, y] = petal_dark + (255,)
        p[x, y + 1] = petal_dark + (255,)
        placed.append((x, y))
        if (x + 1, y + 1) in owner and owner[(x + 1, y + 1)] == fur_names[0]:
            p[x + 1, y + 1] = centre_dark + (255,) if False else p[x + 1, y + 1]


def main():
    mob = sys.argv[1]
    outs = {}
    for variant, suffix in (("normal", ""), ("tropical", "_tropical"), ("cold", "_cold")):
        img, extras = upgrade(mob, variant)
        path = RES / f"textures/entity/{mob}{suffix}.png"
        img.save(path)
        outs[variant] = path
        print("wrote", path.relative_to(ROOT))
        for part, im in extras.items():
            ep = RES / f"textures/entity/{mob}{suffix}{part}.png"
            im.save(ep)
            outs[variant + part] = ep
            print("wrote", ep.relative_to(ROOT))
    if "--preview" in sys.argv:
        sys.path.insert(0, str(ROOT / "tools/models"))
        import geo_preview3d  # noqa
        geo = RES / f"geckolib/models/entity/{mob}.geo.json"
        rows = []
        for variant, path in [("original", SNAP / f"textures/entity/{mob}.png")] + list(outs.items()):
            tmp = ROOT / f"build/mob_preview_{mob}_{variant}.png"
            import subprocess
            subprocess.run([sys.executable, "-I", str(ROOT / "tools/models/geo_preview3d.py"), str(geo), str(path), str(tmp)],
                           check=True)
            rows.append((variant, Image.open(tmp).convert("RGB")))
        w = max(r[1].width for r in rows)
        sheet = Image.new("RGB", (w, sum(r[1].height for r in rows)), (20, 20, 28))
        y = 0
        for _, im in rows:
            sheet.paste(im, (0, y))
            y += im.height
        sheet.save(ROOT / f"build/mob_preview_{mob}.png")
        print("preview build/mob_preview_" + mob + ".png")


if __name__ == "__main__":
    main()
