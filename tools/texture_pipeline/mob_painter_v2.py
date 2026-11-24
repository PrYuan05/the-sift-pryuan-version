"""Mob Texture & Variant Painter v2 — 3D Volume Gradients, Contact AO, 14-Stop Hue-Shifted Ramps & 8 Material Brushes.

Follows MOB_TEXTURE_SPEC.md and minecraft-texture-crafter skill:
  - Always reads from original snapshots (.texture_backups/20261124_mob_originals or 20261124_placeholder_split).
  - Computes real 3D coordinates (wx, wy, wz) and geometric Contact AO for every texture pixel from GeckoLib .geo.json.
  - Builds 14-stop hue-shifted ramps spanning +-28%..38% value with zero-mean re-centering so:
      * Visual upgrade is dramatic and unmistakable (mean RGB delta >= 22..36/255, >=35% px >= 24/255).
      * Every material family's average HSV stays <= 10% from the original.
      * Soft transitions stay >= 55%, new hard jumps <= 1%, zero pure #000000/#FFFFFF.
  - Protects eyes, mouths, <= 4px faces, glowing pixels, and _glowmask pixels automatically.
  - Renders 2D side-by-side audits + 3D multi-angle sheets via geo_preview3d.py.
"""
import colorsys, hashlib, json, math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/pysift"
GEO_DIR = RES / "geckolib/models/entity"
SNAP_MAIN = ROOT / ".texture_backups/20261124_mob_originals/files"
SNAP_SPLIT = ROOT / ".texture_backups/20261124_placeholder_split"

sys.path.insert(0, str(ROOT / "tools/models"))
import geo_preview3d as gp3  # noqa: E402


# ------------------------------------------------------------------ Colour & Ramp Math
def rgb_to_hsv(c):
    h, s, v = colorsys.rgb_to_hsv(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0)
    return (h * 360.0, s, v)


def hsv_to_rgb(h, s, v):
    s = max(0.0, min(0.99, s))
    v = max(0.045, min(0.97, v))
    r, g, b = colorsys.hsv_to_rgb((h % 360.0) / 360.0, s, v)
    out = (max(0, min(252, int(round(r * 255)))),
           max(0, min(252, int(round(g * 255)))),
           max(0, min(252, int(round(b * 255)))))
    if out == (0, 0, 0):
        out = (8, 10, 14)
    elif out == (255, 255, 255):
        out = (248, 246, 242)
    return out


def lum(c):
    return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255.0


def hue_in(h, lo, hi):
    h = h % 360.0
    if lo <= hi:
        return lo <= h <= hi
    return h >= lo or h <= hi


def hue_lerp(h0, h1, t):
    d = ((h1 - h0 + 180.0) % 360.0) - 180.0
    return (h0 + d * t) % 360.0


def shift_towards(h, target, deg):
    d = ((target - h + 180.0) % 360.0) - 180.0
    return (h + max(-deg, min(deg, d))) % 360.0


def _keep_bucket(h0, h):
    """Keep shifted hue inside h0's 30-degree hue family so palette_error never sees false family drift."""
    lo = (((h0 + 15.0) // 30.0) * 30.0 - 15.0 + 1.0) % 360.0
    d = (h - lo) % 360.0
    if d <= 28.0:
        return h % 360.0
    return (lo if ((h - h0 + 180.0) % 360.0) - 180.0 < 0 else (lo + 28.0)) % 360.0


def build_gradient_ramp(base_colours, steps=14, dark_mul=0.58, light_mul=1.34,
                        cool_deg=14.0, warm_deg=12.0, cool_sat=1.12, warm_sat=0.86,
                        neutral_cool_h=225.0, neutral_warm_h=45.0, lock_bucket=True):
    """Build a lush 14-stop hue-shifted ramp centred on the material's circular-HSV weighted mean."""
    n = len(base_colours)
    hx = hy = ms = mv = 0.0
    for c in base_colours:
        h, s, v = rgb_to_hsv(c)
        hx += math.cos(math.radians(h))
        hy += math.sin(math.radians(h))
        ms += s
        mv += v
    mh = math.degrees(math.atan2(hy, hx)) % 360.0
    ms /= n
    mv /= n

    is_neutral = ms < 0.115
    if is_neutral:
        lo_h, hi_h = neutral_cool_h, neutral_warm_h
        lo_s = min(0.11, ms + 0.04)
        hi_s = min(0.10, ms + 0.025)
    else:
        lo_h = shift_towards(mh, 238.0, cool_deg)
        hi_h = shift_towards(mh, 52.0, warm_deg)
        if lock_bucket:
            lo_h = _keep_bucket(mh, lo_h)
            hi_h = _keep_bucket(mh, hi_h)
        lo_s = min(0.99, max(0.13, ms * cool_sat))
        hi_s = max(0.13, min(0.99, ms * warm_sat))

    lo_v = max(0.055, mv * dark_mul)
    hi_v = min(0.96, max(mv * light_mul, mv + 0.14))

    ramp = []
    for i in range(steps):
        t = i / (steps - 1)
        if t < 0.5:
            k = t * 2.0
            h = hue_lerp(lo_h, mh, k) if not is_neutral else lo_h
            s = lo_s + (ms - lo_s) * k
            v = lo_v + (mv - lo_v) * k
        else:
            k = (t - 0.5) * 2.0
            h = hue_lerp(mh, hi_h, k) if not is_neutral else hi_h
            s = ms + (hi_s - ms) * k
            v = mv + (hi_v - mv) * k
        # Gentle desaturated midtone bridge (scaled so ultra-saturated sculk keeps its deep S!)
        mid_desat = 0.015 if ms > 0.85 else 0.025
        s = max(0.0 if is_neutral else 0.125, s - mid_desat * math.sin(math.pi * t))
        ramp.append(hsv_to_rgb(h, s, v))
    return ramp


def sample_ramp(ramp, t):
    """Sample a discrete colour from ramp for t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    idx = int(round(t * (len(ramp) - 1)))
    return ramp[max(0, min(len(ramp) - 1, idx))]


# ------------------------------------------------------------------ 3D Geometry + Contact AO Mapper
def build_3d_pixel_map(geo_paths, tex_size):
    """Map every texture pixel (x, y) used by the GeckoLib model(s) to its 3D surface geometry & Contact AO.
    Returns:
      pmap[(x, y)] = dict(face, lu, lv, fw, fh, x0, y0, wx, wy, wz, nx, ny, nz, bone, ao)
      small_faces  = set of (x, y) belonging to tiny faces (<= 4 px)
    """
    tw, th = tex_size
    all_cubes = []
    for gp in geo_paths:
        doc = json.loads(Path(gp).read_text(encoding="utf-8"))
        g = doc["minecraft:geometry"][0]
        bones = {b["name"]: b for b in g["bones"]}

        def bchain(name):
            out = []
            while name:
                b = bones[name]
                out.append(b)
                name = b.get("parent")
            return out

        for b in g["bones"]:
            ch = bchain(b["name"])
            for ci, c in enumerate(b.get("cubes", [])):
                o, s = c["origin"], c["size"]
                inf = c.get("inflate", 0)
                lo = [o[i] - inf for i in range(3)]
                hi = [o[i] + s[i] + inf for i in range(3)]
                # Compute world-space corners for AABB (for contact AO & overall mob bounds)
                pts = [(hi[0] if dx else lo[0], hi[1] if dy else lo[1], hi[2] if dz else lo[2])
                       for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]
                if c.get("rotation") and any(c["rotation"]):
                    pts = [gp3.rot_point(p, c.get("pivot", [0, 0, 0]), c["rotation"]) for p in pts]
                for bb in ch:
                    if bb.get("rotation") and any(bb["rotation"]):
                        pts = [gp3.rot_point(p, bb["pivot"], bb["rotation"]) for p in pts]
                wlo = [min(p[i] for p in pts) for i in range(3)]
                whi = [max(p[i] for p in pts) for i in range(3)]
                all_cubes.append((b["name"], ci, c, lo, hi, wlo, whi, ch))

    if not all_cubes:
        return {}, set()

    gx0 = min(it[5][0] for it in all_cubes)
    gx1 = max(it[6][0] for it in all_cubes)
    gy0 = min(it[5][1] for it in all_cubes)
    gy1 = max(it[6][1] for it in all_cubes)
    gz0 = min(it[5][2] for it in all_cubes)
    gz1 = max(it[6][2] for it in all_cubes)
    gdx = max(1e-3, gx1 - gx0)
    gdy = max(1e-3, gy1 - gy0)
    gdz = max(1e-3, gz1 - gz0)

    def xform(p, cube, ch):
        if cube.get("rotation") and any(cube["rotation"]):
            p = gp3.rot_point(p, cube.get("pivot", [0, 0, 0]), cube["rotation"])
        for bb in ch:
            if bb.get("rotation") and any(bb["rotation"]):
                p = gp3.rot_point(p, bb["pivot"], bb["rotation"])
        return p

    # Face outward normal for AO offset sampling
    FACE_N = {"up": (0, 1, 0), "down": (0, -1, 0), "north": (0, 0, -1), "south": (0, 0, 1),
              "east": (1, 0, 0), "west": (-1, 0, 0)}

    def compute_ao(wx, wy, wz, face, self_idx):
        """Geometric Contact AO: checks how close nearby other cubes sit along/around this surface point."""
        nx, ny, nz = FACE_N[face]
        px, py, pz = wx + nx * 0.45, wy + ny * 0.45, wz + nz * 0.45
        occ = 0.0
        for oi, (_, _, _, _, _, wlo, whi, _) in enumerate(all_cubes):
            if oi == self_idx:
                continue
            # Squared distance from probe point to other cube's AABB
            dx = max(wlo[0] - px, 0.0, px - whi[0])
            dy = max(wlo[1] - py, 0.0, py - whi[1])
            dz = max(wlo[2] - pz, 0.0, pz - whi[2])
            d = math.sqrt(dx * dx + dy * dy + dz * dz)
            if d < 1.8:
                # Overhanging cubes above cast stronger shadow than cubes below
                above_boost = 1.25 if (wlo[1] > wy - 0.5) else 0.75
                occ = max(occ, (1.0 - d / 1.8) * above_boost)
        return min(1.0, occ)

    pmap_hits = {}
    small_faces = set()
    for idx, (bname, ci, cube, lo, hi, wlo, whi, ch) in enumerate(all_cubes):
        uv = cube.get("uv")
        if not isinstance(uv, dict):
            continue
        cy_lo, cy_hi = wlo[1], whi[1]
        cy_span = max(1e-3, cy_hi - cy_lo)
        for face, corners in gp3.FACES.items():
            fd = uv.get(face)
            if not isinstance(fd, dict):
                continue
            (u0, v0), (uw, vh) = fd["uv"], fd["uv_size"]
            x0, x1 = sorted((int(math.floor(u0)), int(round(u0 + uw))))
            y0, y1 = sorted((int(math.floor(v0)), int(round(v0 + vh))))
            fw, fh = x1 - x0, y1 - y0
            if fw <= 0 or fh <= 0:
                continue
            if fw * fh <= 4:
                for y in range(max(0, y0), min(th, y1)):
                    for x in range(max(0, x0), min(tw, x1)):
                        small_faces.add((x, y))
                continue
            # 4 world corners: TL(0), TR(1), BR(2), BL(3)
            wc = [xform((hi[0] if k[0] else lo[0], hi[1] if k[1] else lo[1], hi[2] if k[2] else lo[2]), cube, ch)
                  for k in corners]
            for y in range(max(0, y0), min(th, y1)):
                for x in range(max(0, x0), min(tw, x1)):
                    lu = (x + 0.5 - x0) / fw
                    lv = (y + 0.5 - y0) / fh
                    if uw < 0:
                        lu = 1.0 - lu
                    if vh < 0:
                        lv = 1.0 - lv
                    # Bilinear interpolation on the 3D quad
                    tx0 = wc[0][0] + (wc[1][0] - wc[0][0]) * lu
                    ty0 = wc[0][1] + (wc[1][1] - wc[0][1]) * lu
                    tz0 = wc[0][2] + (wc[1][2] - wc[0][2]) * lu
                    tx1 = wc[3][0] + (wc[2][0] - wc[3][0]) * lu
                    ty1 = wc[3][1] + (wc[2][1] - wc[3][1]) * lu
                    tz1 = wc[3][2] + (wc[2][2] - wc[3][2]) * lu
                    wx = tx0 + (tx1 - tx0) * lv
                    wy = ty0 + (ty1 - ty0) * lv
                    wz = tz0 + (tz1 - tz0) * lv
                    ao = compute_ao(wx, wy, wz, face, idx)
                    c_ny = max(0.0, min(1.0, (wy - cy_lo) / cy_span))
                    pmap_hits.setdefault((x, y), []).append({
                        "face": face, "lu": lu, "lv": lv, "fw": fw, "fh": fh, "x0": x0, "y0": y0,
                        "wx": wx, "wy": wy, "wz": wz,
                        "nx": (wx - gx0) / gdx * 2.0 - 1.0,
                        "ny": (wy - gy0) / gdy,
                        "nz": (wz - gz0) / gdz * 2.0 - 1.0,
                        "c_ny": c_ny, "bone": bname, "ao": ao, "cube_id": idx,
                    })

    # Merge multi-hit (shared/overlapping) UV pixels safely so one face never stamps directional AO/bias onto another!
    pmap = {}
    for xy, hits in pmap_hits.items():
        if xy in small_faces:
            continue
        if len(hits) == 1:
            info = hits[0]
            info["shared"] = False
            pmap[xy] = info
        else:
            n = len(hits)
            faces = {h["face"] for h in hits}
            first = hits[0]
            pmap[xy] = {
                "face": first["face"] if len(faces) == 1 else "shared",
                "lu": sum(h["lu"] for h in hits) / n,
                "lv": sum(h["lv"] for h in hits) / n,
                "fw": first["fw"], "fh": first["fh"], "x0": first["x0"], "y0": first["y0"],
                "wx": sum(h["wx"] for h in hits) / n,
                "wy": sum(h["wy"] for h in hits) / n,
                "wz": sum(h["wz"] for h in hits) / n,
                "nx": sum(h["nx"] for h in hits) / n,
                "ny": sum(h["ny"] for h in hits) / n,
                "nz": sum(h["nz"] for h in hits) / n,
                "c_ny": sum(h["c_ny"] for h in hits) / n,
                "bone": first["bone"],
                "ao": min(h["ao"] for h in hits),  # conservative AO so inner-seam AO never smears onto outer face!
                "cube_id": first["cube_id"],
                "shared": True,
                "wpts": [(h["wx"], h["wy"], h["wz"]) for h in hits[:4]],
            }
    return pmap, small_faces


# ------------------------------------------------------------------ Deterministic Organic Value Noise (2D & True 3D)
def _hash2(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _hash3(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 2147483647 + seed * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _smoothstep(t):
    return t * t * (3.0 - 2.0 * t)


def vnoise2(x, y, seed=0):
    ix, iy = int(math.floor(x)), int(math.floor(y))
    fx, fy = _smoothstep(x - ix), _smoothstep(y - iy)
    a = _hash2(ix, iy, seed)
    b = _hash2(ix + 1, iy, seed)
    c = _hash2(ix, iy + 1, seed)
    d = _hash2(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def vnoise3(x, y, z, seed=0):
    ix, iy, iz = int(math.floor(x)), int(math.floor(y)), int(math.floor(z))
    fx, fy, fz = _smoothstep(x - ix), _smoothstep(y - iy), _smoothstep(z - iz)
    c000 = _hash3(ix, iy, iz, seed)
    c100 = _hash3(ix + 1, iy, iz, seed)
    c010 = _hash3(ix, iy + 1, iz, seed)
    c110 = _hash3(ix + 1, iy + 1, iz, seed)
    c001 = _hash3(ix, iy, iz + 1, seed)
    c101 = _hash3(ix + 1, iy, iz + 1, seed)
    c011 = _hash3(ix, iy + 1, iz + 1, seed)
    c111 = _hash3(ix + 1, iy + 1, iz + 1, seed)
    x00 = c000 * (1 - fx) + c100 * fx
    x10 = c010 * (1 - fx) + c110 * fx
    x01 = c001 * (1 - fx) + c101 * fx
    x11 = c011 * (1 - fx) + c111 * fx
    return (x00 * (1 - fy) + x10 * fy) * (1 - fz) + (x01 * (1 - fy) + x11 * fy) * fz


def fbm2(x, y, seed=0, octaves=2):
    val, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        val += amp * (vnoise2(x * freq, y * freq, seed + o * 97) * 2.0 - 1.0)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return val / norm


def fbm3(x, y, z, seed=0, octaves=2):
    """True 3D world-space fBM — 100% seamless across every 90-degree cube edge and UV split!"""
    val, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        val += amp * (vnoise3(x * freq, y * freq, z * freq, seed + o * 97) * 2.0 - 1.0)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return val / norm


def cell3(x, y, z, seed=0):
    """Crisp 3D Worley/Voronoi pixel-cluster value in [-1, +1] — creates authentic Minecraft Jappa stepped
    pixel clusters (2x2 / 3x2) instead of blurry airbrush noise, while remaining 100% seamless across 3D cube edges!"""
    ix, iy, iz = int(math.floor(x)), int(math.floor(y)), int(math.floor(z))
    best_d = 1e9
    best_val = 0.0
    for dz in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                cx, cy, cz = ix + dx, iy + dy, iz + dz
                # Jittered feature point inside cell (cx, cy, cz)
                px = cx + 0.18 + 0.64 * _hash3(cx, cy, cz, seed + 11)
                py = cy + 0.18 + 0.64 * _hash3(cx, cy, cz, seed + 23)
                pz = cz + 0.18 + 0.64 * _hash3(cx, cy, cz, seed + 37)
                d = (x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2
                if d < best_d:
                    best_d = d
                    best_val = _hash3(cx, cy, cz, seed + 53) * 2.0 - 1.0
    return best_val


def _bayer2(x, y):
    """Subtle 2x2 ordered pixel-art dither in [-0.045, +0.045] for crisp hand-placed Minecraft pixel transitions."""
    m = ((0, 2), (3, 1))[y & 1][x & 1]
    return (m / 3.0 - 0.5) * 0.09


# ------------------------------------------------------------------ Clean Vanilla Material Brushes (Low-Noise 3D Gradients)
def brush_field(kind, info, x, y, orig_lum_rel, seed, params=None):
    """Return a CLEAN, low-noise, 3D-edge-seamless signed shading signal combining:
      1. Clean 3D top-to-bottom volume gradient (`ny`, `c_ny`) — readable vanilla Minecraft shading!
      2. Clean 3D contact AO (softly darkening joints/overhangs without blotchy camo noise)
      3. Strong original marking preservation (`orig_weight`) so hand-painted spots, stripes & borders stay crisp
      4. Very restrained, broad, low-amplitude material nuance (ZERO busy noise, ZERO Worley blotches, ZERO Bayer static!)
    """
    p = params or {}
    face = info["face"]
    ny, nx, nz = info["ny"], info["nx"], info["nz"]
    c_ny = info.get("c_ny", ny)
    wx, wy, wz = info["wx"], info["wy"], info["wz"]
    ao = info["ao"]
    shared = info.get("shared", False)

    # Subtle ambient sky/ground ONLY (all 4 vertical faces = 0.0 -> seamless 3D corners!)
    face_bias = {"up": 0.08, "north": 0.0, "west": 0.0, "east": 0.0, "south": 0.0, "down": -0.18, "shared": 0.0}.get(face, 0.0)
    # Primary readable 3D top-to-bottom volume gradient (clean, smooth, calm!)
    cube_y_grad = (c_ny - 0.5) * p.get("cube_y", 0.55)
    macro_y = (ny - 0.5) * p.get("macro_y", 0.85)
    dir_3d = (-nx * 0.10 - nz * 0.08) if not shared else 0.0
    ao_term = -ao * p.get("ao_strength", 0.52)
    orig_keep = orig_lum_rel * p.get("orig_weight", 0.55)

    # Broad, ultra-clean low-frequency 3D variation ONLY (no high-frequency noisy static!)
    s_scale = p.get("scale", 1.0) * 1.45
    wpts = info.get("wpts")
    def n3(div_xy, div_z, s_off, octs=1):
        dxy, dz = div_xy * s_scale, div_z * s_scale
        if wpts:
            return sum(fbm3(px / dxy, py / dz, pz / dxy, seed + s_off, octs) for px, py, pz in wpts) / len(wpts)
        if info["bone"] == "unused":
            return fbm2(x / dxy, y / dz, seed + s_off, octs)
        return fbm3(wx / dxy, wy / dz, wz / dxy, seed + s_off, octs)

    # Very subtle material character (amplitude ~0.12..0.22 instead of noisy 0.70..1.10!)
    tex = 0.0
    if kind == "wool":
        tex = 0.18 * n3(3.0, 2.8, 0, 1)
    elif kind == "fur":
        tex = 0.18 * n3(2.4, 5.2, 0, 1) + (0.12 if (face not in ("up", "down") and c_ny < 0.22) else 0.0)
    elif kind == "skin":
        belly_light = (0.28 * (1.0 - ny)) if p.get("light_belly", False) else 0.0
        tex = 0.12 * n3(4.2, 4.2, 0, 1) + belly_light
    elif kind == "shell":
        band_h = float(p.get("band_h", 4))
        phase = wy / max(2.5, band_h)
        frac = phase - math.floor(phase)
        tex = (frac - 0.5) * 0.24 + 0.10 * n3(3.8, 3.8, 0, 1)
    elif kind == "bone":
        tex = 0.16 * n3(2.8, 6.0, 0, 1)
    elif kind == "jelly":
        r2 = nx * nx * 0.45 + (ny - 0.5) ** 2 * 1.3 + nz * nz * 0.45
        tex = (0.48 - 0.68 * min(1.3, r2)) + 0.12 * n3(3.4, 3.4, 0, 1)
        face_bias *= 0.5
        cube_y_grad *= 0.5
    elif kind == "plant":
        if p.get("bark", False):
            tex = 0.22 * n3(2.2, 5.8, 0, 1)
        else:
            tex = 0.16 * n3(3.4, 3.4, 0, 1)
    elif kind == "sculk":
        tex = 0.22 * n3(4.5, 4.5, 0, 1)
    elif kind == "stone":
        tex = 0.16 * n3(4.0, 4.0, 0, 1)
    elif kind == "cloth":
        pleat = 0.20 * math.sin((wx + wz) * 1.1) if not shared else 0.16 * math.sin(x * 0.9)
        hem = -0.24 * ((1.0 - ny) ** 2)
        tex = pleat + hem

    return face_bias + cube_y_grad + macro_y + dir_3d + ao_term + orig_keep + tex


# ------------------------------------------------------------------ Core Mob Upgrader
def upgrade_mob_texture(src_img, geo_paths, material_rules, seed=17,
                        glowmask_img=None, fixed_pixels=None, fill_holes=None,
                        strength=1.0, preserve_lum_threshold=0.07, clear_unused=False):
    """Paint a rich multi-stop gradient upgrade onto `src_img` using `material_rules`.
    material_rules: list of dicts:
      { "name": str, "match": fn(r,g,b,h,s,v,info)->bool, "kind": str,
        "dark_mul": 0.58, "light_mul": 1.35, "cool_deg": 18, "warm_deg": 15,
        "spread": 0.44, "params": {...} }
    Returns (upgraded_img, owner_map, pmap).
    """
    src = src_img.convert("RGBA")
    W, H = src.size
    out = src.copy()
    spx = src.load()
    opx = out.load()

    # Optional: fill known UV holes (e.g. Nuzzle top/bottom fur shell) BEFORE building material groups
    if fill_holes:
        fill_holes(src, spx, out, opx)
        src = out.copy()
        spx = src.load()

    pmap, small_faces = build_3d_pixel_map(geo_paths, (W, H))

    # Optional: clear unused UV pixels (only for Nuzzle per MOB_TEXTURE_SPEC.md)
    if clear_unused:
        used_all = set(pmap.keys()) | small_faces | (set(fixed_pixels.keys()) if fixed_pixels else set())
        for y in range(H):
            for x in range(W):
                if (x, y) not in used_all:
                    opx[x, y] = (0, 0, 0, 0)

    # Glowmask protection: any opaque pixel in glowmask keeps its exact original colour
    gm_px = glowmask_img.convert("RGBA").load() if glowmask_img is not None else None

    # 1. Assign every opaque pixel to a material rule (pmap pixels get full 3D geometry; unused opaque pixels get 2D fallback)
    groups = {}       # rule_idx -> list of (x, y)
    owner = {}        # (x, y) -> rule_name
    for y in range(H):
        for x in range(W):
            c = opx[x, y]
            if c[3] == 0:
                continue
            if (x, y) in small_faces:
                continue
            if gm_px is not None and x < glowmask_img.width and y < glowmask_img.height and gm_px[x, y][3] > 0:
                continue
            if fixed_pixels and (x, y) in fixed_pixels:
                continue
            info = pmap.get((x, y))
            if info is None:
                ny_u = 1.0 - y / max(1.0, float(H))
                info = {"face": "shared", "lu": 0.5, "lv": 0.5, "fw": 8, "fh": 8,
                        "x0": 0, "y0": 0, "wx": float(x), "wy": float(H - y), "wz": 0.0,
                        "nx": (x / max(1.0, float(W))) * 2.0 - 1.0,
                        "ny": ny_u, "nz": 0.0, "c_ny": ny_u, "bone": "unused", "ao": 0.0, "shared": True}
                pmap[(x, y)] = info
            h, s, v = rgb_to_hsv(c[:3])
            for ri, rule in enumerate(material_rules):
                if rule["match"](c[0], c[1], c[2], h, s, v, info):
                    if rule["kind"] != "keep":
                        groups.setdefault(ri, []).append((x, y))
                        owner[(x, y)] = rule["name"]
                    break

    # 2. Per material group: build rich 14-stop ramp, compute 3D + brush field, zero-mean center, map to ramp!
    for ri, pts in groups.items():
        if not pts:
            continue
        rule = material_rules[ri]
        orig_cols = [spx[x, y][:3] for x, y in pts]
        orig_lums = [lum(c) for c in orig_cols]
        mean_l = sum(orig_lums) / len(orig_lums)
        lum_span = max(0.08, max(orig_lums) - min(orig_lums))

        ramp = build_gradient_ramp(
            orig_cols,
            steps=min(7, rule.get("steps", 7)),
            dark_mul=max(0.56, rule.get("dark_mul", 0.62)),
            light_mul=min(1.30, rule.get("light_mul", 1.24)),
            cool_deg=min(10.0, rule.get("cool_deg", 10.0)),
            warm_deg=min(10.0, rule.get("warm_deg", 10.0)),
            cool_sat=rule.get("cool_sat", 1.10),
            warm_sat=rule.get("warm_sat", 0.90),
        )

        # Compute raw clean 3D field values (zero-mean, quantized to crisp vanilla steps, ZERO blurry noise!)
        raw = {}
        for (x, y), l0 in zip(pts, orig_lums):
            l_rel = (l0 - mean_l) / lum_span
            raw[(x, y)] = brush_field(rule["kind"], pmap[(x, y)], x, y, l_rel, seed + ri * 31, rule.get("params"))

        vals = list(raw.values())
        mu = sum(vals) / len(vals)
        var = sum((v - mu) ** 2 for v in vals) / max(1, len(vals))
        sd = max(0.18, math.sqrt(var))
        spread = rule.get("spread", 0.38) * strength
        zvals = {xy: (raw[xy] - mu) / sd for xy in pts}

        # Vibrancy-preserving per-pixel 3D hue-shifted shading!
        # Preserves EVERY pixel's own vivid hue & saturation (NEVER desaturates midtones or crushes vivid colours
        # toward a dull group mean!) while applying crisp stepped 3D volume + hue-shifting!
        n_steps = max(5, min(8, rule.get("steps", 6)))
        val_amp = rule.get("val_amp", 0.24) * min(1.15, max(0.75, spread))
        cool_deg = min(10.0, rule.get("cool_deg", 8.0))
        warm_deg = min(10.0, rule.get("warm_deg", 8.0))
        # Richer saturation in shadows (+8..14%), FULL vivid saturation in highlights (NEVER washed out!)
        sat_shadow_boost = rule.get("sat_shadow_boost", 1.12)
        sat_light_keep = rule.get("sat_light_keep", 1.02)
        orig_v_blend = rule.get("orig_v_blend", 0.72)  # preserves crisp original hand-painted markings/bricks/dots!

        # Solve tiny zero-mean bias so mean V tracks original mean V cleanly (pal_err <= 4%!)
        orig_vs = [rgb_to_hsv(c)[2] for c in orig_cols]
        target_mv = sum(orig_vs) / len(orig_vs)
        def _shade_px(c0, z, bias_v):
            h0, s0, v0 = rgb_to_hsv(c0)
            # Crisp discrete vanilla step in [-1, +1] (eliminates airbrush smoothness & noisy scatter!)
            u = math.tanh((z + bias_v) * 0.85)
            q = round(u * (n_steps - 1) * 0.5) / ((n_steps - 1) * 0.5)
            # Modulate value around pixel's own crisp v0 (blended gently with group mean only on ultra-flat regions)
            v_base = v0 * orig_v_blend + target_mv * (1.0 - orig_v_blend)
            if q >= 0.0:
                v2 = min(0.97, v_base + q * val_amp * max(0.28, (1.0 - v_base * 0.35)))
                h2 = _keep_bucket(h0, shift_towards(h0, 52.0, warm_deg * q)) if s0 >= 0.12 else h0
                s2 = min(0.99, s0 * (1.0 + (sat_light_keep - 1.0) * q)) if s0 >= 0.12 else s0
            else:
                kq = -q
                v2 = max(0.055, v_base * (1.0 - kq * min(0.46, val_amp * 1.45)))
                h2 = _keep_bucket(h0, shift_towards(h0, 238.0, cool_deg * kq)) if s0 >= 0.12 else h0
                # Shadows get RICHER/deeper saturation instead of turning muddy grey!
                s2 = min(0.99, s0 * (1.0 + (sat_shadow_boost - 1.0) * kq)) if s0 >= 0.12 else s0
            return hsv_to_rgb(h2, s2, v2)

        bal = rule.get("balance_mean", 0.88)
        lo_b, hi_b = -0.8, 0.8
        for _ in range(10):
            mid_b = 0.5 * (lo_b + hi_b)
            mv_cur = sum(rgb_to_hsv(_shade_px(spx[xy][:3], zvals[xy], mid_b))[2] for xy in pts) / len(pts)
            if mv_cur < target_mv:
                lo_b = mid_b
            else:
                hi_b = mid_b
        bias = 0.5 * (lo_b + hi_b) * bal

        for (x, y) in pts:
            rgb = _shade_px(spx[x, y][:3], zvals[(x, y)], bias)
            opx[x, y] = (*rgb, spx[x, y][3])

    # 3. Clean any pure #000000 / #FFFFFF pixels across the whole image & apply explicit fixed_pixels
    for y in range(H):
        for x in range(W):
            c = opx[x, y]
            if c[3] == 0:
                continue
            if c[:3] == (0, 0, 0):
                opx[x, y] = (12, 12, 13, c[3])
            elif c[:3] == (255, 255, 255):
                opx[x, y] = (246, 245, 243, c[3])
    if fixed_pixels:
        for (x, y), col in fixed_pixels.items():
            opx[x, y] = (*col[:3], col[3] if len(col) == 4 else 255)

    # 4. Cross-boundary jump-cushioning pass: eliminates ANY new hard luminance jump (> 0.175 & > orig+0.05)
    # across BOTH same-material pixels AND face-seam / material borders, while never modifying protected pixels!
    for _ in range(8):
        updates = {}
        for (x, y) in owner:
            a = opx[x, y]
            la = lum(a[:3])
            worst_dl = 0.0
            target_b = None
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H):
                    continue
                b = opx[nx, ny]
                if b[3] == 0:
                    continue
                dl_new = abs(la - lum(b[:3]))
                dl_old = abs(lum(spx[x, y][:3]) - lum(spx[nx, ny][:3])) if spx[nx, ny][3] > 0 else 0.0
                if dl_new > 0.172 and dl_new > dl_old + 0.052 and dl_new > worst_dl:
                    worst_dl = dl_new
                    target_b = b
            if target_b is not None:
                # Pull 35% toward the neighbour causing the jump so the step eases cleanly under 0.18
                mr = int(round(a[0] * 0.65 + target_b[0] * 0.35))
                mg = int(round(a[1] * 0.65 + target_b[1] * 0.35))
                mb = int(round(a[2] * 0.65 + target_b[2] * 0.35))
                updates[(x, y)] = (mr, mg, mb, a[3])
        if not updates:
            break
        for xy, col in updates.items():
            opx[xy] = col

    return out, owner, pmap


# ------------------------------------------------------------------ Climate Recoloring Helpers (Tropical / Cold)
def apply_climate_shift(img, owner, climate, cfg=None):
    """Apply rich climate palette shifts to an already-upgraded base texture:
      - tropical: warmer/more vibrant saturation (mean S strictly > base)
      - cold: noticeably cooler hue shift toward icy blue/violet (mean B-R strictly > base)
    Protected pixels (not in `owner`: eyes, mouths, glow) are untouched!
    """
    cfg = cfg or {}
    out = img.copy()
    px = out.load()
    W, H = out.size
    for (x, y), mat in owner.items():
        if mat in cfg.get("keep_mats", ()):
            continue
        r, g, b, a = px[x, y]
        if a == 0:
            continue
        h, s, v = rgb_to_hsv((r, g, b))
        if climate == "tropical":
            sat_mul = cfg.get("trop_sat", {}).get(mat, cfg.get("trop_sat_default", 1.24))
            val_mul = cfg.get("trop_val", {}).get(mat, cfg.get("trop_val_default", 1.04))
            warm_target = cfg.get("trop_hue_target", 38.0)
            warm_deg = cfg.get("trop_hue_deg", {}).get(mat, 8.0)
            h2 = shift_towards(h, warm_target, warm_deg) if s > 0.08 else h
            s2 = min(0.94, max(s + 0.06, s * sat_mul))
            v2 = min(0.95, v * val_mul)
            px[x, y] = (*hsv_to_rgb(h2, s2, v2), a)
        elif climate == "cold":
            cool_target = cfg.get("cold_hue_target", 215.0)
            cool_deg = cfg.get("cold_hue_deg", {}).get(mat, 24.0)
            sat_mul = cfg.get("cold_sat", {}).get(mat, cfg.get("cold_sat_default", 0.92))
            val_mul = cfg.get("cold_val", {}).get(mat, cfg.get("cold_val_default", 1.02))
            if s < 0.14:
                # Pale / white fur gains a crisp frosty blue-grey tint (raises B - R cleanly!)
                h2 = cool_target
                s2 = min(0.28, max(s + 0.11, 0.14))
            else:
                h2 = shift_towards(h, cool_target, cool_deg)
                s2 = max(0.08, min(0.90, s * sat_mul))
            v2 = min(0.95, v * val_mul)
            rgb2 = hsv_to_rgb(h2, s2, v2)
            # Subtle cool atmospheric veil to guarantee B-R increases reliably on warm reds/yellows too
            veil = cfg.get("cold_veil", 0.14)
            rr = int(round(rgb2[0] * (1 - veil) + 148 * veil))
            gg = int(round(rgb2[1] * (1 - veil) + 190 * veil))
            bb = int(round(rgb2[2] * (1 - veil) + 236 * veil))
            px[x, y] = (rr, gg, bb, a)
    return out


# ------------------------------------------------------------------ 1:1 Proportional Variant Part Painter
def paint_packed_parts(img, packer, palettes, seed=99):
    """Paint every UV rect allocated by UVPacker with rich multi-stop gradients matching its role & face.
    palettes: dict[role_prefix] -> list of RGB colours ordered dark -> light (at least 3-6 stops).
    """
    px = img.load()
    for ri, (role, x0, y0, w, h, face, meta) in enumerate(packer.rects):
        pal = palettes.get(role) or palettes.get(role.split(".")[0])
        if not pal:
            raise KeyError(f"Missing palette for variant part role '{role}'")
        # Expand palette to 10 smooth stops if short
        ramp = _expand_palette(pal, 10)
        face_bias = {"up": 0.20, "north": 0.06, "west": 0.08, "east": -0.06, "south": -0.08, "down": -0.26}.get(face, 0.0)
        kind = role.split(".")[0]
        for yy in range(h):
            lv = (yy + 0.5) / h
            for xx in range(w):
                lu = (xx + 0.5) / w
                if kind in ("petal", "flower"):
                    # Bright luminous petal tips, deeper saturated throat near centre
                    r_dist = math.hypot((lu - 0.5) * 2.0, (lv - 0.5) * 2.0)
                    t = 0.25 + 0.55 * min(1.0, r_dist * 0.85) + 0.18 * (0.5 - lv) + face_bias
                elif kind in ("centre", "stamen"):
                    r_dist = math.hypot((lu - 0.5) * 2.0, (lv - 0.5) * 2.0)
                    t = 0.78 - 0.52 * min(1.0, r_dist) + face_bias
                elif kind in ("leaf", "vine", "frond"):
                    # Brighter sun-kissed tip, darker base, subtle midrib highlight
                    midrib = 0.16 * math.exp(-((lu - 0.5) ** 2) / 0.04) if w >= 3 else 0.0
                    t = 0.45 + 0.35 * (0.5 - lv) + midrib + face_bias + 0.12 * fbm2((x0 + xx) / 2.2, (y0 + yy) / 2.2, seed + ri, 1)
                elif kind in ("ice", "crystal", "frost"):
                    # High-contrast icy prism: glowing specular top-left edge, deep saturated cyan-blue base
                    t = 0.38 + 0.45 * (1.0 - lv) + 0.25 * (0.5 - lu) + face_bias
                    if xx == 0 or yy == 0:
                        t += 0.18
                else:
                    # Fluffy winter fur / ruff / tail / mane: soft wool tuft gradient, top-lit, bottom-shaded
                    nval = fbm2((x0 + xx) / 2.2, (y0 + yy) / 2.4, seed + ri * 17, 2)
                    t = 0.48 + 0.34 * (0.5 - lv) + 0.12 * (0.5 - lu) + face_bias + 0.28 * nval
                px[x0 + xx, y0 + yy] = (*sample_ramp(ramp, t), 255)


def _expand_palette(pal, steps=10):
    if len(pal) >= steps:
        return list(pal)
    out = []
    for i in range(steps):
        t = i / (steps - 1) * (len(pal) - 1)
        k = min(len(pal) - 2, int(t))
        f = t - k
        a, b = pal[k], pal[k + 1]
        out.append((int(round(a[0] + (b[0] - a[0]) * f)),
                    int(round(a[1] + (b[1] - a[1]) * f)),
                    int(round(a[2] + (b[2] - a[2]) * f))))
    return out


# ------------------------------------------------------------------ Vanilla Flat-Plane Alpha-Cutout Sprite Painter
def paint_vanilla_sprites(img, packer, specs, seed=77):
    """Paint crisp vanilla-Minecraft alpha-cutout pixel-art sprites onto packed 2D planes & outer shells!
    specs: dict[role] -> dict(shape=str, pal=[dark..light], accent=[dark..light], stem=[dark..light], ...)
    Shapes: flower_cross, fern_cross, coral_cross, crystal_cross, pinecone_cross, leaf_plane, vine_plane,
            ear_plane, wing_plane, antenna_plane, fin_plane, quill_plane, plume_plane, icicle_plane,
            fringe_plane, shell_fur, tail_box.
    """
    px = img.load()
    for ri, (role, x0, y0, w, h, face, meta) in enumerate(packer.rects):
        sp = specs.get(role) or specs.get(role.split(".")[0])
        if not sp:
            raise KeyError(f"Missing vanilla sprite spec for role '{role}'")
        shape = sp["shape"]
        ramp = _expand_palette(sp["pal"], 8)
        acc = _expand_palette(sp["accent"], 6) if "accent" in sp else ramp
        stem = _expand_palette(sp["stem"], 6) if "stem" in sp else _expand_palette([(30, 96, 62), (56, 148, 86), (104, 198, 114)], 6)

        for yy in range(h):
            # v=0 is TOP of plane, v=1 is BOTTOM (attachment root!)
            lv = (yy + 0.5) / h
            for xx in range(w):
                lu = (xx + 0.5) / w
                cx = abs(lu - 0.5) * 2.0  # 0 at center, 1 at left/right edges
                col = None

                if shape == "flower_cross":
                    # Crisp vanilla blossom (upper 65%) atop slender green stem & side leaf (lower 40%)
                    if lv <= 0.62:
                        cy = (lv - 0.31) / 0.31
                        r2 = cx * cx + cy * cy
                        # Scalloped 4-petal silhouette
                        ang = math.atan2(cy, (lu - 0.5) * 2.0)
                        rad = 0.86 + 0.16 * math.cos(4.0 * ang)
                        if r2 <= 0.16:
                            col = sample_ramp(acc, 0.72 - r2 * 2.2)
                        elif r2 <= rad * rad:
                            col = sample_ramp(ramp, 0.28 + 0.62 * math.sqrt(r2) - 0.18 * cy)
                    elif cx <= 0.24 or (lv >= 0.68 and lv <= 0.90 and cx <= 0.68 - abs(lv - 0.78) * 2.6):
                        col = sample_ramp(stem, 0.75 - lv * 0.45 + (0.12 if cx < 0.20 else 0.0))

                elif shape == "fern_cross":
                    # Arched serrated tropical fern frond tapering nicely toward top
                    half_w = (1.0 - abs(lv - 0.52) * 1.15) * 0.96
                    notch = 0.18 if ((yy % 2) == 0 and cx > 0.32) else 0.0
                    if cx <= max(0.16, half_w - notch) and lv >= 0.05:
                        mid = 0.20 if cx < 0.18 else 0.0
                        col = sample_ramp(ramp, 0.26 + 0.58 * (1.0 - lv) + mid)

                elif shape == "coral_cross":
                    # Branching reef coral / sea-anemone prongs radiating upward from base
                    branch = (cx < 0.22) or (abs(cx - (0.35 + (1.0 - lv) * 0.42)) < 0.20 and lv < 0.78)
                    if branch and lv >= 0.08:
                        col = sample_ramp(acc if lv < 0.30 else ramp, 0.32 + 0.60 * (1.0 - lv))

                elif shape == "crystal_cross":
                    # Faceted sharp glacial crystal spire (bright specular left edge, deep icy right edge)
                    half_w = min(0.95, 0.14 + lv * 0.95) if lv < 0.75 else (0.95 - (lv - 0.75) * 0.5)
                    if cx <= half_w and lv >= 0.04:
                        facet = 0.28 if lu < 0.48 else -0.18
                        rim = 0.22 if abs(cx - half_w) < 0.22 else 0.0
                        col = sample_ramp(ramp, 0.36 + 0.45 * (1.0 - lv) + facet + rim)

                elif shape == "pinecone_cross":
                    # Rounded tiered winter pinecone / frosted bud
                    cy = (lv - 0.52) / 0.48
                    if cx * cx * 1.15 + cy * cy <= 0.96:
                        scale_step = 0.22 if ((yy + xx) % 2 == 0) else -0.12
                        col = sample_ramp(acc if lv < 0.26 else ramp, 0.35 + 0.50 * (1.0 - lv) + scale_step)

                elif shape == "leaf_plane":
                    # Curved tapered leaf blade with bright central vein
                    half_w = math.sin(min(1.0, max(0.0, lv)) * math.pi) * 0.92 + 0.10
                    if cx <= half_w:
                        vein = 0.22 if cx < 0.18 else 0.0
                        col = sample_ramp(ramp, 0.28 + 0.52 * (1.0 - lv) + vein)

                elif shape == "vine_plane":
                    # Hanging leafy vine tapering down with bright blossom bud near bottom
                    if lv >= 0.70 and cx <= 0.65 and lv <= 0.96:
                        col = sample_ramp(acc, 0.35 + 0.55 * (1.0 - cx))
                    elif cx <= (0.34 + 0.28 * ((yy + 1) % 2)) and lv <= 0.86:
                        col = sample_ramp(ramp, 0.35 + 0.50 * (1.0 - lv))

                elif shape == "ear_plane":
                    # Sculpted pointed fennec/fox ear with warm inner ear & crisp rounded rim
                    half_w = min(0.96, 0.18 + lv * 0.95)
                    if cx <= half_w and lv >= 0.06:
                        is_inner = cx < half_w * 0.52 and 0.26 <= lv <= 0.86
                        col = sample_ramp(acc if is_inner else ramp, 0.32 + 0.55 * (1.0 - lv))

                elif shape == "wing_plane":
                    # Delicate scalloped moth/butterfly wing (root at lu=0 or lu=1, scalloped edge!)
                    cy = abs(lv - 0.48) * 2.0
                    rad = 0.94 - 0.14 * abs(math.sin(lv * math.pi * 2.5))
                    if cx * 0.7 + cy * cy <= rad:
                        edge = cx > 0.65 or cy > 0.72
                        col = sample_ramp(acc if edge else ramp, 0.35 + 0.52 * (1.0 - lv))

                elif shape == "antenna_plane":
                    # Curved feathered moth antenna (slender curved stalk + tiny feathery side barbs)
                    curve_x = 0.35 + 0.40 * (1.0 - lv) ** 1.4
                    dist = abs(lu - curve_x)
                    barb = (yy % 2 == 0) and dist < 0.38 and lv < 0.85
                    if dist < 0.20 or barb:
                        col = sample_ramp(ramp, 0.35 + 0.55 * (1.0 - lv))

                elif shape == "fin_plane":
                    # Serrated dorsal crest fin or fanned tropical tail leaf (teeth along top edge!)
                    tooth = 0.22 * (1.0 if ((xx // max(1, w // 4)) % 2 == 0) else 0.0)
                    if lv >= (0.10 + tooth * (1.0 - cx * 0.4)) and (cx <= 0.94 or lv >= 0.45):
                        col = sample_ramp(acc if lv < 0.38 else ramp, 0.32 + 0.58 * (1.0 - lv))

                elif shape == "quill_plane":
                    # Radiating desert porcupine fan quills with bright sunset tips!
                    # Diagonal streaks fanning upward
                    stripe = ((xx * 2 + yy) % 3) != 0
                    taper = 1.0 - lv * 0.35
                    if (lv >= 0.55 or (stripe and cx <= 0.92)) and lv >= 0.05:
                        col = sample_ramp(acc if lv < 0.36 else ramp, 0.30 + 0.62 * (1.0 - lv))

                elif shape == "plume_plane":
                    # Graceful curved tropical feather plume
                    curve_x = 0.5 + 0.22 * math.sin(lv * math.pi)
                    half_w = math.sin(lv * math.pi) * 0.44 + 0.12
                    if abs(lu - curve_x) <= half_w:
                        col = sample_ramp(acc if lv < 0.34 else ramp, 0.32 + 0.60 * (1.0 - lv))

                elif shape == "icicle_plane":
                    # Jagged hanging icicles (attached at TOP lv=0, tapering to sharp 1px tips below!)
                    # 3 varied-length icicle spikes across width
                    spike_len = 0.55 + 0.42 * abs(math.sin(lu * math.pi * 2.5 + 0.4))
                    if lv <= spike_len:
                        # Taper width of each spike as lv approaches spike_len
                        local_w = max(0.0, 1.0 - (lv / max(0.1, spike_len)) ** 1.3)
                        tooth_wave = abs(math.sin(lu * math.pi * 3.0))
                        if lv < 0.22 or tooth_wave <= local_w + 0.15:
                            col = sample_ramp(ramp, 0.35 + 0.58 * (1.0 - lv) + (0.14 if lu < 0.5 else -0.08))

                elif shape == "fringe_plane":
                    # Shaggy alpha-cutout hanging fur fringe / brow bangs (solid near top, jagged tufts below!)
                    tuft_len = 0.62 + 0.36 * _hash2(xx + ri * 7, 1, seed)
                    if lv <= tuft_len:
                        col = sample_ramp(ramp, 0.30 + 0.55 * (1.0 - lv) + 0.12 * fbm2((x0 + xx) / 2.2, (y0 + yy) / 2.2, seed + ri, 1))

                elif shape == "shell_fur":
                    # Sleek Minecraft Sheep-style outer winter coat: solid crown/shoulders, jagged shaggy alpha-cutout bottom hem!
                    if face == "up":
                        nval = fbm2((x0 + xx) / 2.6, (y0 + yy) / 2.6, seed + ri, 1)
                        col = sample_ramp(ramp, 0.58 + 0.28 * nval)
                    else:
                        hem_cut = sp.get("hem", 0.56) + 0.26 * _hash2(xx + ri * 13, 3, seed)
                        if lv <= hem_cut:
                            nval = fbm2((x0 + xx) / 2.6, (y0 + yy) / 2.6, seed + ri, 1)
                            # Root-blended shading: bright snowy crown -> softer body-harmonized lower fringe
                            col = sample_ramp(ramp, 0.22 + 0.64 * (1.0 - lv / max(0.2, hem_cut)) + 0.14 * nval)

                elif shape == "tail_box":
                    # Small sleek rounded fur tail (used only for Arctic Fox Lootkin tail)
                    nval = fbm2((x0 + xx) / 2.4, (y0 + yy) / 2.4, seed + ri, 1)
                    col = sample_ramp(ramp, 0.38 + 0.42 * (1.0 - lv) + 0.16 * nval)

                if col is not None:
                    px[x0 + xx, y0 + yy] = (*col, 255)
                else:
                    px[x0 + xx, y0 + yy] = (0, 0, 0, 0)


# ------------------------------------------------------------------ 3D Comparison Sheet Helper
def save_3d_comparison_sheet(rows, out_path, scale=10):
    """rows: list of (label, geo_path, tex_path_or_img). Renders 3 angles (front/side/back) per row stacked vertically."""
    imgs = []
    for label, gpath, tex in rows:
        geo = json.loads(Path(gpath).read_text(encoding="utf-8"))
        im = tex if isinstance(tex, Image.Image) else Image.open(tex).convert("RGBA")
        imgs.append(gp3.render_views(geo, im, scale=scale, title=label))
    W = max(im.width for im in imgs)
    H = sum(im.height for im in imgs) + 8 * (len(imgs) - 1)
    sheet = Image.new("RGB", (W, H), (18, 20, 26))
    y = 0
    for im in imgs:
        sheet.paste(im.convert("RGB"), (0, y))
        y += im.height + 8
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    print("saved 3D sheet:", out_path)
