"""Record and compare the Sift mob textures (user, 2026-11-24: record the originals completely before upgrading them; a
separate reviewer compares original vs upgraded: palette error within 10 %, no over-jumping colours).

  python -I tools/texture_pipeline/mob_texture_record.py snapshot <out_dir>
      copies every mob texture (textures/entity/*.png and sift_warden/, not boats, cushions, shulkers, pots, equipment,
      projectiles) and every GeckoLib model + animation to <out_dir>/files/, and writes <out_dir>/manifest.json:
      per texture its size, sha1, opaque pixel count and palette (each colour with count, HSV and relative luminance).
  python -I tools/texture_pipeline/mob_texture_record.py compare <snapshot_dir> [names...]
      compares each current texture with its snapshot and prints, per texture:
        palette error   for every colour cluster of the original (the colours grouped by hue family), how far the closest
                        cluster of the new texture sits: hue difference / 360, saturation and value differences, as a %;
                        the texture passes when the weighted mean is <= 10 %
        jump check      for each pair of adjacent opaque pixels of different colour, the luminance step; "jumps" are steps
                        > 0.18 that the original did not already have at that place (outline edges are allowed), and the
                        share of soft steps (< 0.10) must be >= 20 % like the block rule [18]
        silhouette      the opaque mask must be identical (the UV layout is the model's, it must not move)
      writes build/mob_compare/<name>.png: original | new | per-pixel difference, 8x.
Exit code 1 when any texture fails."""
import colorsys, hashlib, json, math, shutil, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/pysift"
TEX = RES / "textures/entity"
# textures whose alpha may change, with the reason (decided with the user)
ALLOW_MASK = {"nuzzle": "fur holes on the top of the shell filled; unused uv areas (variant parts) cleared (user, 2026-11-24)"}
SKIP_DIRS = {"boat", "chest_boat", "cushion", "decorated_pot", "equipment", "projectiles", "shulker"}


def mob_textures():
    out = []
    for p in sorted(TEX.rglob("*.png")):
        rel = p.relative_to(TEX)
        if rel.parts[0] in SKIP_DIRS:
            continue
        out.append(p)
    return out


def lum(r, g, b):
    return 0.2126 * r / 255 + 0.7152 * g / 255 + 0.0722 * b / 255


def palette(img):
    counts = {}
    for px in img.convert("RGBA").getdata():
        if px[3] == 0:
            continue
        counts[px] = counts.get(px, 0) + 1
    pal = []
    for (r, g, b, a), n in sorted(counts.items(), key=lambda kv: -kv[1]):
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        pal.append({"rgba": [r, g, b, a], "count": n, "hsv": [round(h * 360, 1), round(s, 3), round(v, 3)],
                    "lum": round(lum(r, g, b), 3)})
    return pal


def snapshot(out):
    out = Path(out)
    files = out / "files"
    files.mkdir(parents=True, exist_ok=True)
    manifest = {"textures": {}, "models": []}
    for p in mob_textures():
        rel = p.relative_to(RES).as_posix()
        dst = files / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        img = Image.open(p).convert("RGBA")
        pal = palette(img)
        manifest["textures"][rel] = {"size": img.size, "sha1": hashlib.sha1(p.read_bytes()).hexdigest(),
                                     "opaque": sum(c["count"] for c in pal), "colours": len(pal), "palette": pal}
    for sub in ("geckolib/models/entity", "geckolib/animations/entity"):
        for p in sorted((RES / sub).glob("*.json")):
            rel = p.relative_to(RES).as_posix()
            dst = files / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            manifest["models"].append({"file": rel, "sha1": hashlib.sha1(p.read_bytes()).hexdigest()})
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"snapshot: {len(manifest['textures'])} textures, {len(manifest['models'])} model/animation files -> {out}")


def hue_family(h, s, v):
    if s < 0.12 or v < 0.10:
        return "neutral"
    return int(((h + 15) % 360) // 30)


def clusters(pal):
    """Group a palette by hue family: weighted mean HSV per family."""
    fam = {}
    for c in pal:
        h, s, v = c["hsv"]
        k = hue_family(h, s, v)
        f = fam.setdefault(k, {"n": 0, "x": 0.0, "y": 0.0, "s": 0.0, "v": 0.0})
        n = c["count"]
        f["n"] += n
        f["x"] += math.cos(math.radians(h)) * n
        f["y"] += math.sin(math.radians(h)) * n
        f["s"] += s * n
        f["v"] += v * n
    out = {}
    for k, f in fam.items():
        out[k] = (math.degrees(math.atan2(f["y"], f["x"])) % 360, f["s"] / f["n"], f["v"] / f["n"], f["n"])
    return out


def palette_error(old_pal, new_pal):
    a, b = clusters(old_pal), clusters(new_pal)
    total = sum(c[3] for c in a.values())
    err = 0.0
    worst = []
    for k, (h, s, v, n) in a.items():
        best = None
        for (h2, s2, v2, _n2) in b.values():
            dh = min(abs(h - h2), 360 - abs(h - h2)) / 360 if k != "neutral" else 0
            e = max(dh * 2, abs(s - s2), abs(v - v2))   # hue weighted x2: a 18 degree shift alone = 10 %
            if best is None or e < best:
                best = e
        best = best if best is not None else 1.0
        err += best * n / total
        worst.append((best, k))
    return err, sorted(worst, key=lambda t: t[0], reverse=True)[:3]   # families are ints and "neutral"


def steps(img):
    px = img.load()
    w, h = img.size
    out = {}
    for y in range(h):
        for x in range(w):
            a = px[x, y]
            if a[3] == 0:
                continue
            for dx, dy in ((1, 0), (0, 1)):
                if x + dx < w and y + dy < h:
                    b = px[x + dx, y + dy]
                    if b[3] == 0 or b[:3] == a[:3]:
                        continue
                    out[(x, y, dx)] = abs(lum(*a[:3]) - lum(*b[:3]))
    return out


def compare(snap, names):
    snap = Path(snap)
    man = json.loads((snap / "manifest.json").read_text(encoding="utf-8"))
    outdir = ROOT / "build/mob_compare"
    outdir.mkdir(parents=True, exist_ok=True)
    failed = 0
    for rel, rec in man["textures"].items():
        name = Path(rel).stem
        if names and name not in names:
            continue
        cur = RES / rel
        old = Image.open(snap / "files" / rel).convert("RGBA")
        new = Image.open(cur).convert("RGBA")
        if old.tobytes() == new.tobytes():
            continue
        problems = []
        if old.size != new.size:
            problems.append(f"size {old.size} -> {new.size}")
        else:
            om = [p[3] > 0 for p in old.getdata()]
            nm = [p[3] > 0 for p in new.getdata()]
            moved = sum(1 for i in range(len(om)) if om[i] != nm[i])
            if moved and name not in ALLOW_MASK:
                problems.append(f"silhouette changed on {moved} px")
            elif moved:
                print(f"  note: {name}: alpha changed on {moved} px (allowed: {ALLOW_MASK[name]})")
        err, worst = palette_error(rec["palette"], palette(new))
        if err > 0.10:
            problems.append(f"palette error {err:.1%} > 10% (worst families {worst})")
        so, sn = steps(old), steps(new)
        # a new hard jump: a step > 0.18 that is also clearly harder (+0.06) than the original's step at the same place;
        # borders between materials (fur next to an eye hole) keep roughly their original contrast and are not counted
        jumps = [k for k, d in sn.items() if d > 0.18 and d > so.get(k, 0) + 0.06]
        soft = sum(1 for d in sn.values() if d < 0.10) / max(1, len(sn))
        if len(jumps) > max(3, 0.01 * len(sn)):
            problems.append(f"{len(jumps)} new hard jumps (> 0.18 luminance)")
        if soft < 0.20:
            problems.append(f"soft transitions {soft:.0%} < 20%")
        colours = len(palette(new))
        status = "FAIL" if problems else "ok"
        failed += bool(problems)
        print(f"[{status}] {rel}: palette error {err:.1%}, colours {rec['colours']} -> {colours}, "
              f"new hard jumps {len(jumps)}, soft {soft:.0%}" + ("".join("\n    - " + p for p in problems)))
        z = 8 if old.size[0] <= 64 else 4
        W, H = old.size
        sheet = Image.new("RGBA", (W * z * 3, H * z), (20, 20, 28, 255))
        diff = Image.new("RGBA", old.size)
        diff.putdata([(min(255, abs(a[0] - b[0]) * 3), min(255, abs(a[1] - b[1]) * 3), min(255, abs(a[2] - b[2]) * 3), 255)
                      if (a[3] or b[3]) else (0, 0, 0, 0) for a, b in zip(old.getdata(), new.getdata())])
        for i, im in enumerate((old, new, diff)):
            sheet.alpha_composite(im.resize((W * z, H * z), Image.NEAREST), (i * W * z, 0))
        sheet.save(outdir / f"{name}.png")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    if sys.argv[1] == "snapshot":
        snapshot(sys.argv[2])
    elif sys.argv[1] == "compare":
        compare(sys.argv[2], set(sys.argv[3:]))
