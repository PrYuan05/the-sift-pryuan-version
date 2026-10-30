"""R09 + R14 of art_requests/stone_upgrade_plan.md: the teal strata re-textured from real stones, keeping every texture's
layout and its original teal (same mask-preserving method as paint_pink_strata.py).
Usage: python -I tools/worldgen/paint_teal_strata.py <project> [--apply]

  R09 laminated siltstone (Moenkopi / Chinle): silted_strata (silt 0-2, crimson canyon + red zone caves underground)
      and teal_strata (pale / cyan, willow grove): 1-2 px laminae, gently undulating, short broken mud partings (#6);
      the higher the silt level the finer the laminae and the more partings; teal_strata a little thicker and softer.
  R14 chlorite schist (Alps): abyssal_strata (depth 0-3, willow grove underground, the boss temple's bricks): wavy
      foliation with silky lit ridges and short cleavage lines; deeper = denser foliation.
Only teal pixels (H 150-205) are repainted; the orange grains of silt 2 and the pink lines of teal_strata_b stay.
Building sets (vanilla_building_patterns.md): silted / teal bricks = end_stone_bricks skeleton (2 courses, 8 px bricks
staggered 4, 1 px joints); abyssal bricks = deepslate_bricks skeleton (2 courses, 16 px blocks staggered 8).
Chiseled heads (skill rule): abyssal = Harmonizer (the grove's boss: antlers, one eye, wide collar), teal = Blub (the
grove's commonest: bunny ears), silted = Prickle (the canyon's third creature: antennae, a row of legs). Chiseled ends
are regenerated from the new bricks (tools/texture_pipeline/chiseled_tops.py).
"""
import colorsys, datetime, json, math, random, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
A = P / "src/main/resources/assets/pysift"
T = A / "textures/block"
sys.path.insert(0, str(P / "tools"))
sys.path.insert(0, str(P / "tools/worldgen"))
sys.path.insert(0, str(P / "tools/texture_pipeline"))
import art_guard
from paint_void_stone import Canvas, mottle, ALL, BLOBS
from paint_pink_strata import repaint, ashlar, chiseled
from chiseled_tops import smooth_top

C1, C2, C3, C4, C5, C6, C7 = range(7)


def teal(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    return "teal" if s >= 0.18 and v >= 0.3 and 150 <= h * 360 <= 205 else None


def siltstone(rnd, fine=1, partings=2, thick=(1, 2, 2)):
    c = Canvas()
    lam, k = [], 0
    while len(lam) < 16:
        lam += [[C3, C4, C5, C4, C3, C5][k % 6]] * rnd.choice(thick if fine < 2 else (1, 1, 2))
        k += 1
    lam = lam[:16]
    ph = rnd.uniform(0, 16)
    wave = [round(1.6 * math.sin(2 * math.pi * (x + ph) / 16) + 0.7 * math.sin(2 * math.pi * (x + ph) / 8)) for x in range(16)]
    for y in range(16):
        for x in range(16):
            c.set(x, y, lam[(y + wave[x]) % 16])
    for _ in range(8):                       # silt grains across the laminae
        x, y = rnd.randrange(16), rnd.randrange(16)
        col = rnd.choice((C3, C5, C2))
        for dx, dy in rnd.choice(BLOBS[:5]):
            c.set(x + dx, y + dy, col)
    for _ in range(partings):                # broken mud partings: #6 with a lit #3 under them, 3-5 px
        x, y = rnd.randrange(16), rnd.randrange(16)
        for q in range(rnd.randint(3, 5)):
            yy = y - wave[(x + q) % 16]
            c.set(x + q, yy, C6)
            c.set(x + q, yy + 1, C3)
    return c


def schist(rnd, density=0):
    g = Canvas()
    for y in range(16):
        x, covered = rnd.randrange(16), 0
        while covered < 16:
            n = rnd.randint(5 - min(density, 2), 10 - density)
            col = rnd.choice((C4, C4, C5, C3, C5, C3))
            for q in range(n):
                if covered + q < 16:
                    g.set(x + covered + q, y, col)
            covered += n
    for _ in range(3 + density):             # silky lit ridges (#2 over #3) and cleavage lines (#6 over #7)
        x, y, n = rnd.randrange(16), rnd.randrange(16), rnd.randint(3, 5)
        lit = rnd.random() < 0.5
        for q in range(n):
            g.set(x + q, y, C2 if lit else C6)
            g.set(x + q, y + (1 if lit else -1), C3 if lit else C5)
    c = Canvas()
    ph = rnd.uniform(0, 16)
    off = [round(1.8 * math.sin(2 * math.pi * (x + ph) / 16)) for x in range(16)]
    for y in range(16):
        for x in range(16):
            c.set(x, y, g.get(x, y + off[x]))
    return c


def small_bricks(rnd, face):
    """end_stone_bricks skeleton: 2 courses of 8 px (7 brick + 1 joint), 8 px bricks staggered 4."""
    c = face(rnd)
    for course, off in ((0, 0), (1, 4)):
        y0 = course * 8
        for x in range(16):
            c.set(x, y0, C2 if (x - off) % 8 not in (6, 7) else C3)
            c.set(x, y0 + 6, C5 if c.get(x, y0 + 6) in (C2, C3) else c.get(x, y0 + 6))
            c.set(x, y0 + 7, C7)
        for b in range(2):
            jx = off + 8 * b + 7
            for y in range(y0, y0 + 7):
                c.set(jx, y, C7)
                c.set(jx - 1, y, C6 if y > y0 else C3)
                c.set(jx + 1, y, C3 if y > y0 else C2)
    return c


HARMONIZER = ["#.#......#.#", ".#..####..#.", "..#.####.#..", "...##EE##...", "...######...", "############",
              ".##########.", "....#..#...."]
BLUB = [".##......##.", ".##......##.", ".##########.", ".##########.", ".##E####E##.", ".####EE####.",
        ".##########.", "..##....##.."]
PRICKLE = ["...#....#...", "...#....#...", "..########..", ".##########.", ".##E####E##.", ".##########.",
           ".#.#.##.#.#.", "............"]


def lvl(stem):
    return int(next((ch for ch in reversed(stem) if ch.isdigit()), "0"))


CALIBRATE = {"teal_strata_c", "teal_strata_d", "teal_strata_f", "teal_strata_g"}
REF = T / "teal_strata/teal_strata_e.png"


def jobs():
    out = []
    for p in sorted((T / "silted_strata").glob("*.png")):
        out.append((p, lambda r, n=lvl(p.stem): siltstone(r, fine=n, partings=1 + n), ("teal",), 0.18))
    for p in sorted((T / "teal_strata").glob("*.png")):
        out.append((p, lambda r: siltstone(r, fine=0, partings=1, thick=(2, 2, 3)), ("teal",), 0.16))
    for p in sorted((T / "abyssal_strata").glob("*.png")):
        out.append((p, lambda r, n=lvl(p.stem): schist(r, density=n), ("teal",), 0.22))
    # teal layers inside the pink composites (crimson canyon / grove): teal_strata's siltstone, only the teal pixels
    for d in ("crimson_strata", "capped_crimson_strata", "ember_stone"):
        for p in sorted((T / d).glob("*.png")):
            if sum(1 for c in Image.open(p).convert("RGBA").get_flattened_data() if c[3] and teal(c[:3])) >= 8:
                out.append((p, lambda r: siltstone(r, fine=0, partings=1, thick=(2, 2, 3)), ("teal",), 0.16, "teal_e"))
    for k, (p, fn, fams, span, *_) in enumerate(out):     # user: these share teal_e's light teal, no dark band (no macro)
        if p.stem in CALIBRATE or p.parent.name == "abyssal_strata":
            out[k] = (p, fn, fams, span, "teal_e")
    B = lambda base, name: T / f"{base}_bricks" / f"{name}.png"
    out += [(B("silted_strata", "silted_strata_bricks"), lambda r: small_bricks(r, lambda q: siltstone(q, 1, 1)), None, 0.22),
            (B("silted_strata", "chiseled_silted_strata_bricks"), lambda r: chiseled(r, lambda q: siltstone(q, 1, 1), PRICKLE), None, 0.24),
            (B("teal_strata", "teal_strata_bricks"), lambda r: small_bricks(r, lambda q: siltstone(q, 0, 1, (2, 2, 3))), None, 0.22),
            (B("teal_strata", "chiseled_teal_strata_bricks"), lambda r: chiseled(r, lambda q: siltstone(q, 0, 1, (2, 2, 3)), BLUB), None, 0.24),
            (B("abyssal_strata", "abyssal_strata_bricks"), lambda r: ashlar(r, schist, False), None, 0.24),
            (B("abyssal_strata", "chiseled_abyssal_strata_bricks"), lambda r: chiseled(r, schist, HARMONIZER), None, 0.26)]
    return out


def main():
    results = []
    tmp = P / "build/previews/teal_strata_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    only = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), None)
    ref = [c[:3] for c in Image.open(REF).convert("RGBA").get_flattened_data() if teal(c[:3])]
    for job in jobs():
        path, fn, fams, span = job[:4]
        if only and not any(o in path.stem for o in only):
            continue
        calibrated = len(job) > 4
        new, _ = repaint(path, fn, fams, span, classify=teal, macro=fams is not None and not calibrated,
                         base=ref if calibrated else None)
        results.append((path, new))
        new.save(tmp / path.name)
    bricks = {p.stem: img for p, img in results if p.stem.endswith("_bricks") and not p.stem.startswith("chiseled_")}
    for base in ("silted_strata", "teal_strata", "abyssal_strata"):          # chiseled ends from the new bricks
        if f"{base}_bricks" not in bricks:
            continue
        top = smooth_top(bricks[f"{base}_bricks"], f"chiseled_{base}_bricks")
        results.append((T / f"{base}_bricks" / f"chiseled_{base}_bricks_top.png", top.convert("RGBA")))
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 11)
    S, per = 64, 9
    rows = (len(results) + per - 1) // per
    sheet = Image.new("RGB", (per * (S + 6) + 12, rows * (2 * S + 30) + 8), (30, 30, 36))
    tiles = Image.new("RGB", (per * 54 + 12, rows * 60 + 8), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    for i, (path, new) in enumerate(results):
        x, y = 6 + (i % per) * (S + 6), 4 + (i // per) * (2 * S + 30)
        sheet.paste(Image.open(path).convert("RGB").crop((0, 0, 16, 16)).resize((S, S), Image.NEAREST), (x, y))
        sheet.paste(new.convert("RGB").crop((0, 0, 16, 16)).resize((S, S), Image.NEAREST), (x, y + S + 2))
        d.text((x, y + 2 * S + 4), path.stem.replace("_strata", "").replace("chiseled_", "ch_")[:12], fill=(200, 205, 215), font=f)
        t = Image.new("RGB", (48, 48))
        for a in range(3):
            for b in range(3):
                t.paste(new.convert("RGB").crop((0, 0, 16, 16)), (a * 16, b * 16))
        tiles.paste(t, (6 + (i % per) * 54, 4 + (i // per) * 60))
    sheet.save(P / "build/previews/teal_strata_paint.png")
    tiles.resize((tiles.width * 2, tiles.height * 2), Image.NEAREST).save(P / "build/previews/teal_strata_tiles.png")
    print("preview: build/previews/teal_strata_paint.png -", len(results), "textures")
    if not APPLY:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_teal_strata")
    written = []
    for path, new in results:
        (bk / path.relative_to(P)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, bk / path.relative_to(P))
        if not art_guard.is_ours(path) and "--force" in sys.argv:
            path.unlink()
        if art_guard.save(new.convert("RGB") if path.stem.endswith("_top") else new, path):
            written.append(path.relative_to(A).as_posix())
    man = P / "tools/texture_pipeline/recolor_manifest.json"
    doc = json.loads(man.read_text(encoding="utf-8"))
    keep = [e for e in doc["entries"] if e["file"] not in written]
    if len(keep) != len(doc["entries"]):
        doc["entries"] = keep
        man.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("written:", len(written), "; backups in", bk.relative_to(P))


if __name__ == "__main__":
    main()
