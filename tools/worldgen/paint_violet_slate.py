"""R10 + R11 of art_requests/stone_upgrade_plan.md: the violet slate abyss, re-textured from real stones while keeping every
texture's layout and colours (mask-preserving, like paint_pink_strata.py / paint_teal_strata.py).
Usage: python -I tools/worldgen/paint_violet_slate.py <project> [--apply] [--only=a,b]

  R10 purple slate (Penrhyn, Wales): dark_slate fade 0-4 (k o p r s t u v), violet_capped_dark_slate side (q) and
      bottom - long thin cleavage flakes (7-13 px), only adjacent steps, cleavage lines in #6 / #5: smooth (user).
  R11 purple phyllite (Appalachians): violet_strata (b c e h i) - finer, silky, one gentle wave per tile.
Colour families (H / S bins: grey, green, warm, purple) are repainted separately, each in its own colour, so the fade
patches stay where they were; pink and teal pixels belong to other stones and are left as they are. No macro light /
dark shift (user: no dark band across a block).
Building sets (vanilla_building_patterns.md): both on the deepslate_bricks skeleton (2 courses, 16 px blocks staggered 8).
Chiseled heads: dark slate = Sculk Monstrosity (the abyss's boss: tusks, glowing visor, massive shoulders); violet
strata = Sentinel (second commonest: small head, two pairs of whiskers). Chiseled ends from the new bricks.
"""
import colorsys, datetime, json, shutil, sys
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
from paint_void_stone import Canvas
from paint_pink_strata import repaint, ashlar, chiseled
from chiseled_tops import smooth_top

C1, C2, C3, C4, C5, C6, C7 = range(7)
import math


def slate_family(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    h *= 360
    if s >= 0.3 and v >= 0.5 and (h >= 330 or h <= 20):
        return None                                  # pink / red: the crimson layers
    if s >= 0.3 and 150 <= h <= 205:
        return None                                  # teal layers
    if s < 0.1:
        return "grey"
    if 60 <= h < 200:
        return "green"
    if 200 <= h < 345:
        return "purple"
    return "warm"


def foliation(rnd, seg=(7, 13), wavy=False, lines=2, cols=(C4, C4, C4, C5, C3, C3)):
    g = Canvas()
    for y in range(16):
        x, covered = rnd.randrange(16), 0
        while covered < 16:
            n = rnd.randint(*seg)
            col = rnd.choice(cols)
            for q in range(n):
                if covered + q < 16:
                    g.set(x + covered + q, y, col)
            covered += n
    for _ in range(lines):                           # cleavage lines: #6 with a #5 above
        x, y, n = rnd.randrange(16), rnd.randrange(16), rnd.randint(5, 8)
        for q in range(n):
            g.set(x + q, y, C6)
            g.set(x + q, y - 1, C5)
    for _ in range(2):                               # a lit flake edge
        x, y, n = rnd.randrange(16), rnd.randrange(16), rnd.randint(3, 5)
        for q in range(n):
            g.set(x + q, y, C2)
    if not wavy:
        return g
    c = Canvas()
    ph = rnd.uniform(0, 16)
    off = [round(1.7 * math.sin(2 * math.pi * (x + ph) / 16)) for x in range(16)]
    for y in range(16):
        for x in range(16):
            c.set(x, y, g.get(x, y + off[x]))
    return c


slate = lambda r: foliation(r)
phyllite = lambda r: foliation(r, seg=(5, 9), wavy=True, cols=(C4, C4, C5, C3, C3, C5))

MONSTROSITY = ["...######...", "..########..", ".#.#EEEE#.#.", ".#.######.#.", ".#.######.#.", "############",
               "############", "##.##..##.##"]
SENTINEL = ["....####....", "...######...", "##.#E##E#.##", "...######...", "##.######.##", "...######...",
            "....#..#....", "............"]
FAMS = ("grey", "green", "purple", "warm")


def jobs():
    out = []
    for k in "koprstuv":                     # fade 0-4; q removed (user), its block uses k
        out.append((T / f"dark_slate/dark_slate_{k}.png", slate, FAMS, 0.08 if k == "k" else 0.15, "k"))   # k = worldgen: calmer
    out.append((T / "violet_capped_dark_slate/violet_capped_dark_slate_bottom.png", slate, FAMS, 0.15, "k"))
    for k in "bcehi":
        out.append((T / f"violet_strata/violet_strata_{k}.png", phyllite, FAMS, 0.18))
    out += [(T / "dark_slate_bricks/dark_slate_bricks.png", lambda r: ashlar(r, slate, False), None, 0.22),
            (T / "dark_slate_bricks/chiseled_dark_slate_bricks.png", lambda r: chiseled(r, slate, MONSTROSITY), None, 0.24),
            (T / "violet_strata_bricks/violet_strata_bricks.png", lambda r: ashlar(r, phyllite, False), None, 0.22),
            (T / "violet_strata_bricks/chiseled_violet_strata_bricks.png", lambda r: chiseled(r, phyllite, SENTINEL), None, 0.24)]
    return out


def main():
    only = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), None)
    results = []
    tmp = P / "build/previews/violet_slate_paint"
    tmp.mkdir(parents=True, exist_ok=True)
    # user: like abyssal strata, the fade levels share dark_slate_k's colour (no transition across stacked blocks)
    # each colour family gets ONE palette shared by every fade level: grey from k, purple / green / warm pooled over
    # all fades - the purple patches stay, but the same patch colour is the same in every block (no step between blocks)
    ref = {}
    for k in "koprstuv":
        for c in Image.open(T / f"dark_slate/dark_slate_{k}.png").convert("RGBA").get_flattened_data():
            f = slate_family(c[:3])
            if f and (f != "grey" or k == "k"):
                ref.setdefault(f, []).append(c[:3])
    for job in jobs():
        path, fn, fams, span = job[:4]
        if only and not any(o in path.stem for o in only):
            continue
        use = ref
        if path.stem == "dark_slate_k":          # worldgen block: patches pulled halfway to the grey ground (calmer)
            g = [sum(c[i] for c in ref["grey"]) / len(ref["grey"]) for i in range(3)]
            use = dict(ref)
            for f in ("purple", "green", "warm"):
                if f in ref:
                    m = [sum(c[i] for c in ref[f]) / len(ref[f]) for i in range(3)]
                    use[f] = [tuple(round((a + b) / 2) for a, b in zip(m, g))]
        new, _ = repaint(path, fn, fams, span, classify=slate_family, base=use if len(job) > 4 else None)
        results.append((path, new))
        new.save(tmp / path.name)
    bricks = {p.stem: img for p, img in results if p.stem.endswith("_bricks") and not p.stem.startswith("chiseled_")}
    for base in ("dark_slate", "violet_strata"):
        if f"{base}_bricks" in bricks:
            top = smooth_top(bricks[f"{base}_bricks"], f"chiseled_{base}_bricks")
            results.append((T / f"{base}_bricks" / f"chiseled_{base}_bricks_top.png", top.convert("RGBA")))
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 11)
    S, per = 64, 10
    rows = (len(results) + per - 1) // per
    sheet = Image.new("RGB", (per * (S + 6) + 12, rows * (2 * S + 30) + 8), (30, 30, 36))
    tiles = Image.new("RGB", (per * 54 + 12, rows * 60 + 8), (30, 30, 36))
    d = ImageDraw.Draw(sheet)
    for i, (path, new) in enumerate(results):
        x, y = 6 + (i % per) * (S + 6), 4 + (i // per) * (2 * S + 30)
        sheet.paste(Image.open(path).convert("RGB").crop((0, 0, 16, 16)).resize((S, S), Image.NEAREST), (x, y))
        sheet.paste(new.convert("RGB").crop((0, 0, 16, 16)).resize((S, S), Image.NEAREST), (x, y + S + 2))
        d.text((x, y + 2 * S + 4), path.stem.replace("dark_slate", "ds").replace("violet_strata", "vs").replace("chiseled_", "ch_")[:12],
               fill=(200, 205, 215), font=f)
        t = Image.new("RGB", (48, 48))
        for a in range(3):
            for b in range(3):
                t.paste(new.convert("RGB").crop((0, 0, 16, 16)), (a * 16, b * 16))
        tiles.paste(t, (6 + (i % per) * 54, 4 + (i // per) * 60))
    sheet.save(P / "build/previews/violet_slate_paint.png")
    tiles.resize((tiles.width * 2, tiles.height * 2), Image.NEAREST).save(P / "build/previews/violet_slate_tiles.png")
    print("preview: build/previews/violet_slate_paint.png -", len(results), "textures")
    if not APPLY:
        return
    bk = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_paint_violet_slate")
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
