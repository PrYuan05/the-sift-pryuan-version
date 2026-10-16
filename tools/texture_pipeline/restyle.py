"""Restyle block textures toward the modern vanilla (JAPPA) look: clean 16x16 pixel art, soft low-contrast
shading, no salt-and-pepper noise, cohesive warm-highlight / cool-shadow palettes, seamless tiling.

  python -I tools/texture_pipeline/restyle.py <project> preview   -> build/texture_pipeline/out/restyle/ (+ review sheets)
  python -I tools/texture_pipeline/restyle.py <project> apply     -> overwrite PNGs with the preview (backup + restyle_manifest.json)
  python -I tools/texture_pipeline/restyle.py <project> revert [unit|all]

Palette units follow the blockstates: one unit per variant pool (random pool, tone, stage); composite pools
(side + top + bottom / end) form one unit. A texture shared by several units belongs to the block that uses it
as its cube_all body. PNG orientation is never changed (orientation lives in model UVs). Parameters:
restyle_params.json. peeling_log gets generated growth-ring tops per peel stage."""
import sys, json, math, shutil, datetime, statistics
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import project_paths, lj, wj, entries, res_path, sha1, lab, iter_pools

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
HERE = Path(__file__).resolve().parent
OUT = P / "build/texture_pipeline/out/restyle"
PRM = lj(HERE / "restyle_params.json")
MANIFEST = HERE / "restyle_manifest.json"
CMD = sys.argv[2] if len(sys.argv) > 2 else "preview"


# ---------------- colour helpers ----------------
def lab_to_rgb(L, a, b):
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    inv = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    x, y, z = inv(fx) * 0.95047, inv(fy), inv(fz) * 1.08883
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    bl = 0.0557 * x - 0.2040 * y + 1.0570 * z
    gam = lambda c: 1.055 * c ** (1 / 2.4) - 0.055 if c > 0.0031308 else 12.92 * c
    return tuple(max(0, min(255, round(gam(max(0.0, c)) * 255))) for c in (r, g, bl))


def kmeans(points, k, iters=12):
    """points: list of Lab tuples (with repeats = weights). Seeds at L quantiles for stable, ordered results."""
    uniq = sorted(set(points), key=lambda c: c[0])
    k = max(1, min(k, len(uniq)))
    srt = sorted(points, key=lambda c: c[0])
    centers = [srt[min(len(srt) - 1, int((i + 0.5) * len(srt) / k))] for i in range(k)]
    for _ in range(iters):
        groups = [[] for _ in centers]
        for p in points:
            groups[min(range(len(centers)), key=lambda i: math.dist(p, centers[i]))].append(p)
        new = [tuple(sum(v) / len(g) for v in zip(*g)) if g else centers[i] for i, g in enumerate(groups)]
        if new == centers:
            break
        centers = new
    return sorted(set(centers), key=lambda c: c[0])


# ---------------- units ----------------
def model_textures(m):
    mj = lj(res_path(ASSETS, m, "models", ".json"))
    return mj.get("parent", ""), mj.get("textures", {})


TEMPL_AXIS = {"minecraft:block/cube_bottom_top": "x", "pysift:block/templates/cube_bottom_top_vflip": "x",
              "pysift:block/templates/cube_bottom_top_rot90": "y", "pysift:block/templates/cube_bottom_top_rot270": "y"}
units = {}          # unit -> {"textures": [refs], "kind": ...}
cube_all_owner = {}  # texture -> unit where it is the cube_all body
first_unit = {}
wrap_axes = {}       # texture -> set of axes allowed to wrap
side_info = {}       # generated face texture -> (side texture, parent, face)
for block, state, models in iter_pools(A):
    uname = f"{block}[{state}]" if state else block
    for m in models:
        parent, tex = model_textures(m)
        for face, r in tex.items():
            if not r.startswith("pysift:") or face == "particle":
                continue
            units.setdefault(uname, {"textures": [], "block": block})
            if r not in units[uname]["textures"]:
                units[uname]["textures"].append(r)
            first_unit.setdefault(r, uname)
            if face == "all":
                cube_all_owner.setdefault(r, uname)
            axes = {"x", "y"}
            if face == "side" and parent in TEMPL_AXIS:
                axes = {TEMPL_AXIS[parent]}
            wrap_axes[r] = wrap_axes.get(r, {"x", "y"}) & axes
            if face in ("top", "bottom") and "side" in tex:
                side_info.setdefault(r, (tex["side"], parent, face))
owner = {r: cube_all_owner.get(r, u) for r, u in first_unit.items()}
GENERATED_TOPS = {f"pysift:block/peeling_log/peeling_log_peel{i}_top" for i in range(3)}
man_recolor = lj(HERE / "recolor_manifest.json")["entries"] if (HERE / "recolor_manifest.json").exists() else []
generated_faces = {"pysift:" + e["file"].removeprefix("textures/").removesuffix(".png") for e in man_recolor if e.get("mode") == "generated"}


def load(ref): return Image.open(res_path(ASSETS, ref, "textures", ".png")).convert("RGBA")


# ---------------- per-unit restyle ----------------
def restyle_unit(uname, refs):
    imgs = {r: load(r) for r in refs}
    pts = [lab(c) for im in imgs.values() for c in im.getdata() if c[3] > 0]
    k = max(PRM["k_min"], min(PRM["k_max"], PRM["k_min"] + (len(refs) - 1) // 3))
    centers = kmeans(pts, k)
    meanL = statistics.mean(p[0] for p in pts)
    span = max(1e-6, max(abs(c[0] - meanL) for c in centers))
    styled = []
    for L, a, b in centers:
        t = (L - meanL) / span                              # -1 (dark) .. 1 (light)
        L2 = min(PRM["l_max"], max(PRM["l_min"], meanL + (L - meanL) * PRM["contrast"]))
        a2 = (a + max(t, 0) * PRM["warm_shift"] / 2) * PRM["chroma"]
        b2 = (b + (t * PRM["warm_shift"] if t > 0 else t * PRM["cool_shift"])) * PRM["chroma"]
        styled.append((L2, a2, b2))
    rgb = [lab_to_rgb(*c) for c in styled]
    out = {}
    for r, im in imgs.items():
        px = im.load()
        idx = [[min(range(len(centers)), key=lambda i: math.dist(lab(px[x, y]), centers[i])) if px[x, y][3] > 0 else -1
                for x in range(16)] for y in range(16)]
        axes = wrap_axes.get(r, {"x", "y"})
        idx = denoise(idx, axes)
        if PRM["soft_edge"]:
            idx = soften(idx, centers)
        idx = seam(idx, axes, centers)
        if r in generated_faces and r in side_info:
            idx = align_ring(idx, r, centers)
        o = Image.new("RGBA", (16, 16))
        o.putdata([(*rgb[idx[y][x]], 255) if idx[y][x] >= 0 else (0, 0, 0, 0) for y in range(16) for x in range(16)])
        out[r] = o
    return out, rgb


def nb(y, x, axes):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == dy == 0:
                continue
            yy, xx = y + dy, x + dx
            if not 0 <= xx < 16:
                if "x" not in axes:
                    continue
                xx %= 16
            if not 0 <= yy < 16:
                if "y" not in axes:
                    continue
                yy %= 16
            yield yy, xx


def denoise(idx, axes):
    for _ in range(PRM["denoise_passes"]):
        new = [row[:] for row in idx]
        for y in range(16):
            for x in range(16):
                if idx[y][x] < 0:
                    continue
                ns = [idx[yy][xx] for yy, xx in nb(y, x, axes) if idx[yy][xx] >= 0]
                if ns and sum(1 for n in ns if n == idx[y][x]) < PRM["min_same"]:
                    new[y][x] = max(set(ns), key=ns.count)
        idx = new
    return idx


def soften(idx, centers):
    new = [row[:] for row in idx]
    for y in range(16):
        for x in range(16):
            i = idx[y][x]
            if i < 0:
                continue
            same = sum(1 for yy, xx in nb(y, x, {"x", "y"}) if idx[yy][xx] == i)
            if same > 4:
                continue
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < 16 and 0 <= xx < 16 and idx[yy][xx] >= 0 and idx[yy][xx] - i >= 2:
                    new[y][x] = i + 1   # centers are sorted by L: i+1 is the next lighter step
                    break
    return new


def seam(idx, axes, centers):
    def fix(p, q):
        (y1, x1), (y2, x2) = p, q
        i, j = idx[y1][x1], idx[y2][x2]
        if i < 0 or j < 0 or abs(centers[i][0] - centers[j][0]) <= PRM["seam_delta"]:
            return
        mid = tuple((a + b) / 2 for a, b in zip(centers[i], centers[j]))
        m = min(range(len(centers)), key=lambda n: math.dist(mid, centers[n]))
        idx[y1][x1] = idx[y2][x2] = m
    for t in range(16):
        if "x" in axes:
            fix((t, 0), (t, 15))
        if "y" in axes:
            fix((0, t), (15, t))
    return idx


def align_ring(idx, ref, centers):
    """Generated top/bottom faces: outer ring uses only colours found on the side row that meets this face."""
    side, parent, face = side_info[ref]
    sim = load(side)
    T = Image.Transpose
    orient = {"pysift:block/templates/cube_bottom_top_vflip": T.FLIP_TOP_BOTTOM,
              "pysift:block/templates/cube_bottom_top_rot90": T.ROTATE_270,
              "pysift:block/templates/cube_bottom_top_rot270": T.ROTATE_90}.get(parent)
    if orient:
        sim = sim.transpose(orient)
    row = 0 if face == "top" else 15
    allowed = {min(range(len(centers)), key=lambda n: math.dist(lab(sim.getpixel((x, row))), centers[n])) for x in range(16)}
    for y in range(16):
        for x in range(16):
            if (x in (0, 15) or y in (0, 15)) and idx[y][x] not in allowed:
                idx[y][x] = min(allowed, key=lambda n: abs(centers[n][0] - centers[idx[y][x]][0]))
    return idx


def ring_top(side_img, stage):
    """Growth rings for peeling_log: bark ring (thins out as the log peels), light wood, darker rings, pith."""
    cols = sorted({c[:3] for c in side_img.getdata() if c[3] > 0}, key=lambda c: lab(c)[0])
    dark, mid_dark = cols[0], cols[min(1, len(cols) - 1)]
    light, mid_light = cols[-1], cols[max(len(cols) - 2, 0)]
    out = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            dx, dy = abs(x - 7.5), abs(y - 7.5)
            if max(dx, dy) == 7.5:                      # outermost pixel ring: bark
                c = dark if stage < 2 else mid_dark
            elif max(dx, dy) == 6.5 and stage == 0:     # thick bark before peeling
                c = mid_dark
            else:                                      # rounded-square growth rings (superellipse, p=4)
                r = (dx ** 4 + dy ** 4) ** 0.25
                ring = int(r + 0.5)
                c = mid_dark if r < 1.2 else (mid_light if ring % 3 == 0 else light)
            out.putpixel((x, y), (*c, 255))
    return out


# ---------------- commands ----------------
def preview():
    if OUT.exists():
        shutil.rmtree(OUT)
    results, palettes, report = {}, {}, {}
    owned = {}
    for r, u in owner.items():
        owned.setdefault(u, []).append(r)
    for uname in sorted(owned):
        if uname in PRM["exclude_units"]:
            continue
        refs = [r for r in owned[uname] if r not in GENERATED_TOPS]
        if not refs:
            continue
        out, rgb = restyle_unit(uname, refs)
        results.update(out)
        palettes[uname] = rgb
        report[uname] = refs
    # peeling_log growth-ring tops from the restyled sides
    for i in range(3):
        side = f"pysift:block/peeling_log/peeling_log_peel{i}_side"
        top = f"pysift:block/peeling_log/peeling_log_peel{i}_top"
        results[top] = ring_top(results.get(side, load(side)), i)
        report.setdefault(f"peeling_log[peel={i}]", []).append(top)
    for r, im in results.items():
        p = OUT / "textures" / (r.split(":", 1)[1] + ".png")
        p.parent.mkdir(parents=True, exist_ok=True)
        im.save(p)
    wj(OUT / "restyle_units.json", report)
    sheets(report, results)
    print(f"preview: {len(results)} textures in {len(report)} units -> {OUT.relative_to(P)}")


def sheets(report, results):
    tile, PAD, per = 64, 4, 34
    items = sorted(report.items())
    for n in range(0, len(items), per):
        chunk = items[n:n + per]
        cols = max(len(refs) for _, refs in chunk)
        img = Image.new("RGB", (250 + cols * (2 * tile + PAD * 4), 24 + len(chunk) * (tile + 20)), (28, 28, 32))
        dr = ImageDraw.Draw(img)
        dr.text((4, 4), "unit | each texture: original, restyled", fill=(235, 235, 235))
        y = 22
        for uname, refs in chunk:
            dr.text((4, y + tile // 2 - 6), uname[:40], fill=(250, 210, 90))
            x = 250
            for r in refs:
                for im in (load(r), results[r]):
                    img.paste(im.convert("RGB").resize((tile, tile), Image.Resampling.NEAREST), (x, y))
                    x += tile + PAD
                dr.text((x - 2 * tile - PAD * 2, y + tile + 2), r.rsplit("/", 1)[1][-24:], fill=(200, 200, 200))
                x += PAD * 2
            y += tile + 20
        img.save(OUT / f"restyle_review_{n // per + 1:02d}.png")


def apply():
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = P / ".texture_backups" / f"{stamp}_restyle"
    man = lj(MANIFEST) if MANIFEST.exists() else {"entries": []}
    by_file = {e["file"]: e for e in man["entries"]}
    units_of = {r: u for u, refs in lj(OUT / "restyle_units.json").items() for r in refs}
    n = 0
    for src in sorted((OUT / "textures").rglob("*.png")):
        rel = src.relative_to(OUT).as_posix()
        dst = A / rel
        b = bdir / rel
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dst, b)
        before = sha1(dst)
        shutil.copyfile(src, dst)
        ref = "pysift:" + rel.removeprefix("textures/").removesuffix(".png")
        prev = by_file.get(rel)
        by_file[rel] = {"file": rel, "unit": units_of.get(ref), "mode": "generated" if ref in GENERATED_TOPS else "restyle",
                        "sha1_before": prev["sha1_before"] if prev else before, "sha1_after": sha1(dst),
                        "backup": prev["backup"] if prev else b.relative_to(P).as_posix(), "date": stamp}
        n += 1
    man["entries"] = sorted(by_file.values(), key=lambda e: e["file"])
    wj(MANIFEST, man)
    print(f"applied {n} textures; backups in {bdir.relative_to(P)}")


def revert(sel):
    man = lj(MANIFEST)
    keep, n = [], 0
    for e in man["entries"]:
        if sel != "all" and e["unit"] != sel and not (e["unit"] or "").startswith(sel + "["):
            keep.append(e)
            continue
        shutil.copy2(P / e["backup"], A / e["file"])
        n += 1
    man["entries"] = keep
    wj(MANIFEST, man)
    print(f"restored {n} textures")


if CMD == "preview":
    preview()
elif CMD == "apply":
    apply()
elif CMD == "revert":
    revert(sys.argv[3] if len(sys.argv) > 3 else "all")
else:
    sys.exit(__doc__)
