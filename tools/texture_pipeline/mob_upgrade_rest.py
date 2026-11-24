"""Upgrade the remaining Sift mob textures (no climate variants), reusing mob_upgrade's helpers (user, 2026-11-24).

  python -I tools/texture_pipeline/mob_upgrade_rest.py [names...] [--apply] [--sheet]

  default    writes candidates to build/mob_rest/res/textures/entity/ (the live textures are not touched) and runs the
             reviewer's compare (mob_texture_record) against them
  --apply    writes the live textures under src/main/resources/assets/pysift/textures/entity/ instead
  --sheet    renders original vs upgraded 3D previews into build/mob_rest_sheet.png

Per texture:
  * materials   the model's face pixels are grouped by hue family (30 degree buckets, low-saturation colours as one neutral
                family, the same grouping the reviewer uses); each family gets an 8-step ramp from its own colours, the dark
                end turned towards blue (cooler, a bit more saturated), the light end towards yellow (warmer, a bit less
                saturated), with a desaturated midtone bridge (minecraft-texture-crafter step 2.2).
  * keep        glowing colours (bright and saturated), families of only a few pixels (eyes, mouths, accents) and every face
                of 4 px or less (mob_upgrade.face_map) are never touched.
  * shading     each pixel moves up or down its family's ramp: lit at the top of each side face, up faces lighter, down
                faces darker, a darker bottom rim; per kind: fur = per-column strands with lighter tips, skin = soft 2x2
                mottle, shell = lit top rim + darker lower half, jelly = a light core, plant/stone = gentle.
The original always comes from the snapshot (.texture_backups/20261124_mob_originals), alpha never changes, and pure
#000000 / #FFFFFF are replaced by near-black / near-white."""
import json, math, random, sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mob_upgrade as mu  # noqa: E402

ROOT = mu.ROOT
RES = mu.RES
SNAP = mu.SNAP
GEO = RES / "geckolib/models/entity"
CAND = ROOT / "build/mob_rest/res"
WARDEN_GEO = ROOT / "build/mob_rest/sift_warden.geo.json"

# kinds: (hue_lo, hue_hi, sat_lo, sat_hi, val_lo, val_hi, kind) - first match decides the kind of a family (by its mean
# colour); "default" for the rest. glow: (sat_min, val_min) - colours at least this saturated and bright are glow (kept);
# None = no glow on this mob. min_px: families with fewer face pixels are details (kept).
MOBS = {
    "bloombud": {"default": "stone", "kinds": [(40, 70, 0.5, 1, 0, 1, "plant"), (90, 200, 0.12, 1, 0, 1, "plant")],
                 "glow": None},
    "blub": {"default": "jelly", "glow": None},
    "blub_carapace": {"default": "shell", "glow": None, "min_px": 30},
    "blub_fungal": {"default": "jelly", "glow": None},
    "blub_meadows": {"default": "skin", "kinds": [(150, 210, 0.3, 1, 0, 1, "plant")], "glow": (0.7, 0.95)},
    "blub_ravines": {"default": "shell", "kinds": [(20, 50, 0, 1, 0, 1, "skin")], "glow": (0.5, 0.88)},
    # the head is a glowing lantern: its whole cyan gradient (saturated mid steps too) is kept, only the stone shaded
    # (review 11-24: the family ramps pulled its big panels towards blue and the stone mottle drew a swirl pattern;
    # now every pixel keeps its own hue and only steps lighter / darker: "local", no mottle, at most 0.06 luminance)
    "echo_golem": {"default": "stone", "glow": [(0.35, 0.85), (0.55, 0.45), (0.0, 0.88)],
                   "local": {"step": 0.06, "hue": 0, "sat": 0, "quant": 1}, "mottle": False, "max_dl": 0.06},
    "harmonizer": {"default": "skin", "geos": ["harmonizer", "harmonizer_body", "harmonizer_head"], "glow": None},
    # (review 11-24: five family ramps of 8 steps merged its colours, 45 -> 43, and muted the vivid orange; now each
    # pixel steps along its own short hue-shifted ramp: darker = a little bluer, lighter = a little warmer)
    "hunter": {"default": "shell", "glow": None, "local": {"step": 0.07, "hue": 4, "sat": 0.04, "quant": 1},
               "min_px": 6, "split": 0.08, "max_off": 2.5, "shell_grad": 1.4, "max_dl": 0.1},
    "hurler": {"default": "skin", "glow": (0.6, 0.85)},
    "monarch": {"default": "shell", "geos": ["monarch", "monarch_body", "monarch_head"], "glow": (0.2, 0.85)},
    "mourner": {"default": "fur", "kinds": [(0, 360, 0, 0.12, 0.5, 1, "skin")], "glow": (0.25, 0.95)},
    "roamroot": {"default": "plant", "kinds": [(180, 260, 0, 1, 0.6, 1, "skin")], "glow": None},
    "scavenger": {"default": "skin", "kinds": [(25, 60, 0.3, 1, 0, 1, "shell")], "glow": (0.5, 0.75)},
    "sculk_cube": {"default": "skin", "glow": (0.6, 0.55)},
    "sculk_maw": {"default": "skin", "glow": (0.25, 0.75)},
    "singer": {"default": "fur", "kinds": [(0, 90, 0, 1, 0, 1, "skin")], "glow": None},
    "stalker": {"default": "skin", "glow": (0.4, 0.75)},
    "trapper": {"default": "skin", "kinds": [(300, 345, 0.3, 1, 0, 1, "shell")], "glow": (0.3, 0.99)},
    "tuner": {"default": "skin", "kinds": [(200, 260, 0.5, 1, 0, 1, "shell")], "glow": None},
    "sift_warden": {"default": "fur", "kinds": [(0, 60, 0, 0.45, 0.3, 1, "stone")], "glow": None,
                    "tex": "sift_warden/sift_warden", "geo_path": WARDEN_GEO},
}
# ramp span per kind: (darkest *, lightest *) on the value of the material's own darkest / lightest colour
SPLIT = 0.12
MAX_DL = 0.08
SPAN = {"fur": (0.92, 1.05), "skin": (0.86, 1.12), "shell": (0.86, 1.10), "jelly": (0.90, 1.05),
        "plant": (0.90, 1.08), "stone": (0.88, 1.08)}


# -------------------------------------------------------------------------------------------- vanilla warden uv layout
def warden_geo():
    """The Sift Warden uses the vanilla warden model (WardenModel, 128x128): its box uvs as a GeckoLib-style geo so the
    face map and the previewer can use it. Positions are only approximate (for the preview)."""
    def box(u, v, w, h, d, origin):
        f = {"north": [[u + d, v + d], [w, h]], "east": [[u, v + d], [d, h]], "west": [[u + d + w, v + d], [d, h]],
             "south": [[u + 2 * d + w, v + d], [w, h]], "up": [[u + d, v], [w, d]], "down": [[u + d + w, v], [w, d]]}
        uv = {k: {"uv": a, "uv_size": b} for k, (a, b) in f.items() if b[0] > 0 and b[1] > 0}
        return {"origin": origin, "size": [w, h, d], "uv": uv}
    cubes = [
        box(0, 0, 18, 21, 11, [-9, 13, -4]),            # body
        box(0, 32, 16, 16, 10, [-8, 34, -5]),           # head
        box(52, 32, 16, 16, 0, [-24, 37, 0]),           # right tendril
        box(58, 0, 16, 16, 0, [8, 37, 0]),              # left tendril
        box(44, 50, 8, 28, 8, [-17, 6, -4]),            # right arm
        box(0, 58, 8, 28, 8, [9, 6, -4]),               # left arm
        box(76, 48, 6, 13, 6, [-6, 0, -3]),             # right leg
        box(76, 76, 6, 13, 6, [0, 0, -3]),              # left leg
        box(90, 11, 9, 21, 0, [-9, 13, -4.2]),          # ribcage (front of the body)
    ]
    doc = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": "geometry.sift_warden", "texture_width": 128, "texture_height": 128},
        "bones": [{"name": "root", "pivot": [0, 0, 0], "cubes": cubes}]}]}
    WARDEN_GEO.parent.mkdir(parents=True, exist_ok=True)
    WARDEN_GEO.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return WARDEN_GEO


# ----------------------------------------------------------------------------------------------------------- helpers
def family(c):
    h, s, v = mu.hsv(c)
    if s < 0.12 or v < 0.10:
        return "neutral"
    # the reviewer's 30 degree family, halved: two materials of close hues (navy cloth next to a deep teal fade) keep
    # their own ramps instead of being blended into one
    return f"{int(((h + 15) % 360) // 30)}{'ab'[int(((h + 15) % 360) % 30 // 15)]}"


def towards(h, target, deg):
    d = ((target - h + 180) % 360) - 180
    return (h + max(-deg, min(deg, d))) % 360


def keep_bucket(h0, h):
    """The shifted hue stays in the original's 30 degree hue family (the reviewer groups colours by family: a ramp end
    that drifts into the next family reads as a different colour there)."""
    lo = ((h0 + 15) // 30) * 30 - 15 + 1
    d = ((h - lo) % 360)
    return h if d <= 28 else (lo if ((h - h0 + 180) % 360) - 180 < 0 else lo + 28) % 360


def ramp_for(colours, kind, steps=8, own_hue=False, span=None, own_sat=False):
    """Hue-shifted ramp: dark end cooler (towards 240) and a bit more saturated, light end warmer (towards 55) and a bit
    less saturated, a desaturated bridge in the middle. own_hue=True: the material's own colours only, darker and
    lighter (no hue turn, no saturation change): for mobs whose look must stay as it is (echo_golem)."""
    dk, lt = span or SPAN[kind]
    cs = sorted(colours, key=mu.lum)
    d, l = mu.hsv(cs[0]), mu.hsv(cs[-1])
    if own_hue:
        # piecewise through the material's own colours (sorted dark -> light), the ends stretched a little darker /
        # lighter in value only, so every step keeps one of the original hues
        anchors = [mu.hsv(c) for c in cs]
        anchors[0] = (anchors[0][0], anchors[0][1], max(0.05, anchors[0][2] * dk))
        anchors[-1] = (anchors[-1][0], anchors[-1][1], min(0.97, anchors[-1][2] * lt))
        out = []
        for i in range(steps):
            t = i / (steps - 1) * (len(anchors) - 1)
            k = min(len(anchors) - 2, int(t)) if len(anchors) > 1 else 0
            a, b = anchors[k], anchors[min(k + 1, len(anchors) - 1)]
            f = t - k
            out.append(mu.rgb(mu.hue_lerp(a[0], b[0], f), a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f))
        return out
    sm = sum(mu.hsv(c)[1] for c in cs) / len(cs)       # the material's own saturation, not one odd accent colour's
    if own_sat:                                        # saturated accents (hunter's orange) keep their own saturation
        sm = None
    lo = (keep_bucket(d[0], towards(d[0], 240, 10)), min(1, (d[1] if sm is None else (d[1] + sm) / 2) * 1.06),
          max(0.05, d[2] * dk))
    hi = (keep_bucket(l[0], towards(l[0], 55, 8)), (l[1] if sm is None else (l[1] + sm) / 2) * 0.97 ** (sm is None)
          * 0.93 ** (sm is not None), min(0.97, l[2] * lt + 0.01))
    out = []
    for i in range(steps):
        t = i / (steps - 1)
        s = lo[1] + (hi[1] - lo[1]) * t - 0.03 * math.sin(math.pi * t)
        v = lo[2] + (hi[2] - lo[2]) * t
        if own_sat:
            # the saturation follows the material's own colours of about this value (a vivid orange between a dark
            # brown and a pale peach stays vivid instead of being interpolated into a muted middle)
            w = [(math.exp(-((mu.hsv(c)[2] - v) / 0.06) ** 2), mu.hsv(c)[1]) for c in cs]
            tw = sum(k for k, _ in w)
            if tw > 1e-3:
                s = sum(k * sc for k, sc in w) / tw - 0.02 * math.sin(math.pi * t)
        out.append(mu.rgb(mu.hue_lerp(lo[0], hi[0], t), s, v))
    return out


def local_shade(c, off, opt, max_dl):
    """Per-pixel ramp ("local" mobs: hunter, echo_golem): the pixel keeps its own hue and saturation and steps along a
    short ramp of its own colour: each half step of shading moves the value by opt["step"] (relative), darker steps turn
    the hue opt["hue"] degrees towards blue and gain a little saturation, lighter ones turn towards yellow and lose a
    little (hue 0 = no hue turn: the original hues stay). The luminance never moves more than max_dl."""
    h, s, v = mu.hsv(c)
    l0 = mu.lum(c)
    q = opt.get("quant", 0.5)                   # whole / half steps: a small set of shades per colour, no airbrush
    k = round(off / q) * q
    while True:
        hh = towards(h, 240 if k < 0 else 55, abs(k) * opt.get("hue", 0)) if s > 0.12 else h
        ss = max(0.0, min(1.0, s * (1 - opt.get("sat", 0.0) * k)))
        vv = max(0.04, min(0.97, v * (1 + opt["step"] * k)))
        out = mu.rgb(hh, ss, vv)
        if abs(mu.lum(out) - l0) <= max_dl or k == 0:
            return out
        k = round(k - q, 3) if k > 0 else round(k + q, 3)


def safe(c):
    if c[:3] == (0, 0, 0):
        return (13, 13, 13)
    if c[:3] == (255, 255, 255):
        return (247, 245, 240)
    return c[:3]


def kind_of(cfg, mean):
    h, s, v = mu.hsv(mean)
    for hlo, hhi, slo, shi, vlo, vhi, k in cfg.get("kinds", []):
        if mu.hue_in(h, hlo, hhi) and slo <= s <= shi and vlo <= v <= vhi:
            return k
    return cfg["default"]


def merged_face_map(img, geos):
    fmap, protected = {}, set()
    for g in geos:
        for x0, y0, w, h, *_ in mu.faces(g):
            if w * h <= 4:
                protected.update((x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h))
        for xy, info in mu.face_map(img, g).items():
            fmap.setdefault(xy, info)
    for xy in protected:
        fmap.pop(xy, None)
    return fmap


def geos_of(name, cfg):
    if "geo_path" in cfg:
        return [warden_geo()]
    return [GEO / f"{g}.geo.json" for g in cfg.get("geos", [name])]


def tex_rel(name, cfg):
    return f"textures/entity/{cfg.get('tex', name)}.png"


# ---------------------------------------------------------------------------------------------------------- painting
def upgrade(name, seed=11):
    cfg = MOBS[name]
    src = Image.open(SNAP / tex_rel(name, cfg)).convert("RGBA")
    px = src.load()
    W, H = src.size
    fmap = merged_face_map(src, geos_of(name, cfg))
    rnd = random.Random(seed)
    glow = cfg.get("glow")

    def is_glow(c):
        if not glow:
            return False
        _, s, v = mu.hsv(c)
        rules = glow if isinstance(glow, list) else [glow]
        return any(s >= r[0] and v >= r[1] for r in rules)

    fam_px = {}
    for (x, y) in fmap:
        c = px[x, y]
        if c[3] == 0 or is_glow(c[:3]) or mu.hsv(c[:3])[2] < 0.08:      # glow and near-black outlines/gaps: kept
            continue
        fam_px.setdefault(family(c[:3]), []).append((x, y))
    # a family spanning a wide luminance range is really two materials (dark plates + light fur): split it at gaps in
    # its colours' luminance larger than SPLIT, so each part gets its own short ramp and no step jumps
    for f in list(fam_px):
        pts = fam_px.pop(f)
        cols = sorted({px[x, y][:3] for x, y in pts}, key=mu.lum)
        band, cut = {}, 0
        for a, b in zip(cols, cols[1:]):
            band.setdefault(a, cut)
            if mu.lum(b) - mu.lum(a) > cfg.get("split", SPLIT):
                cut += 1
            band[b] = cut
        band.setdefault(cols[0], 0)
        for x, y in pts:
            fam_px.setdefault(f"{f}.{band[px[x, y][:3]]}", []).append((x, y))
    ramps, kinds = {}, {}
    for f, pts in list(fam_px.items()):
        if len(pts) < cfg.get("min_px", 14):
            del fam_px[f]
            continue
        cols = [px[x, y][:3] for x, y in pts]
        mean = tuple(sum(c[i] for c in cols) // len(cols) for i in range(3))
        kinds[f] = kind_of(cfg, mean)
        ramps[f] = ramp_for(list(set(cols)), kinds[f], cfg.get("steps", 8), cfg.get("own_hue", False),
                            cfg.get("span", {}).get(kinds[f]), cfg.get("own_sat", False))

    owner = {p: f for f, pts in fam_px.items() for p in pts}
    strand, mottle = {}, {}

    def pick(d, key, choices):
        if key not in d:
            d[key] = rnd.choice(choices)
        return d[key]

    out = src.copy()
    op = out.load()
    for (x, y), f in owner.items():
        face, lu, lv, fw, fh, x0, y0 = fmap[(x, y)]
        kind, ramp = kinds[f], ramps[f]
        idx = mu.nearest_index(px[x, y][:3], ramp)
        off = 0.0
        if face == "up":
            off += 0.6
        elif face == "down":
            off -= 1.0
        else:
            off += 0.9 * (0.5 - lv)
            if fh >= 4 and y - y0 == fh - 1:
                off -= 0.5
        if kind == "fur":
            off += pick(strand, (face, x0, y0, x, y // 3 if face in ("up", "down") else 0), (-0.5, -0.25, 0, 0, 0.25, 0.5))
            below = (x, y + 1)
            if owner.get(below) != f and fmap.get(below, ("",))[0] == face and face not in ("up", "down"):
                off += 0.6                               # lighter hair tips at the lower edge
        elif kind == "skin":
            off += 0.6 * (0.5 - lv) + 0.8 * (0.25 - abs(lu - 0.5))
            if fw > 6 and fh > 3:
                off += pick(mottle, (x // 2, y // 2), (-0.5, 0, 0, 0.5))
        elif kind == "shell":
            off += cfg.get("shell_grad", 0.9) * (0.5 - lv) + 0.6 * (0.25 - abs(lu - 0.5))
            if fh >= 3 and y - y0 == 0 and face not in ("up", "down"):
                off += 0.6
        elif kind == "jelly":
            off += 0.8 * (0.5 - lv) + 0.8 * (0.25 - abs(lu - 0.5))
            if fw > 6:
                off += 0.5 * pick(mottle, (x // 3, y // 3), (-0.5, 0, 0, 0.5))
        elif kind in ("plant", "stone"):
            off += 0.3 * (0.5 - lv)
            if fw > 5 and fh > 3 and cfg.get("mottle", True):
                off += pick(mottle, (x // 2, y // 2), (-0.5, 0, 0, 0.5))
        off = max(-cfg.get("max_off", 1.5), min(cfg.get("max_off", 1.5), off))
        # the shaded step may not move the pixel's luminance more than MAX_DL from the original (no over-jumping
        # colours, the original's own pattern stays readable): the allowed step closest to the shaded target
        l0 = mu.lum(px[x, y][:3])
        if "local" in cfg:
            op[x, y] = safe(local_shade(px[x, y][:3], off, cfg["local"], cfg.get("max_dl", MAX_DL))) + (255,)
            continue
        t = idx + off
        ok = [j for j in range(len(ramp)) if abs(mu.lum(ramp[j]) - l0) <= cfg.get("max_dl", MAX_DL)] or [idx]
        i = min(ok, key=lambda j: abs(j - t))
        op[x, y] = safe(ramp[i]) + (255,)
    # where two neighbours (usually two materials meeting) were shaded apart into a harder step than the original had,
    # both go back to their unshaded ramp step (and then to the original colour) so borders keep their contrast
    for rnd_pass in range(3):
        fix = set()
        for (x, y) in fmap:
            if not op[x, y][3]:
                continue
            for q in ((x + 1, y), (x, y + 1)):
                if q[0] >= W or q[1] >= H or not op[q][3]:
                    continue
                dn = abs(mu.lum(op[x, y][:3]) - mu.lum(op[q][:3]))
                do = abs(mu.lum(px[x, y][:3]) - mu.lum(px[q][:3]))
                if dn > 0.16 and dn > do + 0.05:
                    fix.update(((x, y), q))
        if not fix:
            break
        for p in fix:
            f = owner.get(p)
            if f and rnd_pass == 0 and "local" not in cfg:
                op[p] = safe(ramps[f][mu.nearest_index(px[p][:3], ramps[f])]) + (255,)
            else:
                op[p] = safe(px[p][:3]) + (px[p][3],)
    for y in range(H):
        for x in range(W):
            c = op[x, y]
            if c[3] and c[:3] in ((0, 0, 0), (255, 255, 255)):
                op[x, y] = safe(c) + (c[3],)
    return out, {f: (kinds[f], len(fam_px[f])) for f in fam_px}


def compare(names, live):
    import mob_texture_record as mtr
    if not live:
        mtr.RES = CAND
    # mob_texture_record.palette_error sorts (error, family) tuples; two families with the same error (e.g. two kept
    # families at 0.0) compare "neutral" with an int and crash. Same maths, ties sorted by error only.
    orig = mtr.palette_error

    def palette_error(old_pal, new_pal):
        a, b = mtr.clusters(old_pal), mtr.clusters(new_pal)
        total = sum(c[3] for c in a.values())
        err, worst = 0.0, []
        for k, (h, s, v, n) in a.items():
            best = min((max((min(abs(h - h2), 360 - abs(h - h2)) / 360 if k != "neutral" else 0) * 2,
                            abs(s - s2), abs(v - v2)) for (h2, s2, v2, _n) in b.values()), default=1.0)
            err += best * n / total
            worst.append((best, str(k)))
        return err, sorted(worst, key=lambda t: t[0], reverse=True)[:3]
    mtr.palette_error = palette_error if orig else orig
    try:
        mtr.compare(SNAP.parent, set(names))
    except SystemExit as e:
        return e.code or 0
    return 0


def sheet(names, root):
    sys.path.insert(0, str(ROOT / "tools/models"))
    import subprocess
    rows = []
    tmp = ROOT / "build/mob_rest/prev"
    tmp.mkdir(parents=True, exist_ok=True)
    for n in names:
        cfg = MOBS[n]
        geo = geos_of(n, cfg)[0]
        pair = []
        for tag, tex in (("orig", SNAP / tex_rel(n, cfg)), ("new", root / tex_rel(n, cfg))):
            o = tmp / f"{n}_{tag}.png"
            subprocess.run([sys.executable, "-I", str(ROOT / "tools/models/geo_preview3d.py"), str(geo), str(tex), str(o)],
                           check=True, capture_output=True)
            im = Image.open(o).convert("RGB")
            pair.append(im.resize((int(im.width * 220 / im.height), 220), Image.LANCZOS))
        rows.append(pair)
    w = max(a.width + b.width for a, b in rows) + 8
    out = Image.new("RGB", (w, 224 * len(rows)), (20, 20, 28))
    for i, (a, b) in enumerate(rows):
        out.paste(a, (0, i * 224))
        out.paste(b, (a.width + 8, i * 224))
    out.save(ROOT / "build/mob_rest_sheet.png")
    print("sheet build/mob_rest_sheet.png", out.size)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    live = "--apply" in sys.argv
    names = args or list(MOBS)
    root = RES if live else CAND
    for n in names:
        img, fams = upgrade(n)
        path = root / tex_rel(n, MOBS[n])
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path)
        print("wrote", path.relative_to(ROOT), " families:", fams)
    code = compare(names, live)
    if "--sheet" in sys.argv:
        sheet(names, root)
    sys.exit(code)


if __name__ == "__main__":
    main()
