"""The Sift Codex (隙浮手記) in The Sift's own look (user: "the book's background should fit The Sift").
Usage: python -I tools/progression/paint_codex_theme.py <project> [--apply]

Without --apply only build/previews/codex_theme.png is written. With --apply:
  1. theme sprites  - Modonomicon looks for a book theme's sprites under
     <theme id namespace>:textures/gui/sprites/modonomicon/themes/<theme id path>/... and falls back to its default theme
     per sprite (DefaultBookTheme.spriteId), so the codex gets its own pages / frame / tabs without touching other books.
     The default sprites are recoloured by luminance rank (texture-crafter method C): the cream parchment becomes a pale
     blush vellum, the dark wood and leather soul willow teal, the gold tabs and frame gems spirit-liquid pink.
  2. category backdrops - textures/gui/codex/<category>.png, a 512 x 512 scene per category painted at 128 x 128 and
     scaled 4x: a banded dusk sky in The Sift's colours over strata silhouettes, kept mid-dark so the node map reads.
  3. parallax layers - textures/gui/codex/motes_<n>.png, drifting soul motes (spirit pink / soul teal / cyan) instead of
     Modonomicon's night-sky stars.
build_codex.py points the book at all of this (theme id pysift:sift_codex, palette, backgrounds, parallax).
"""
import colorsys, io, math, random, shutil, sys, zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
A = P / "src/main/resources/assets/pysift"
sys.path.insert(0, str(P / "tools"))
import art_guard

JAR = next(Path.home().glob(".gradle/caches/modules-2/files-2.1/maven.modrinth/modonomicon/*/*/modonomicon-*.jar"))
DEF = "assets/modonomicon/textures/gui/sprites/modonomicon/themes/default/"
OUT = A / "textures/gui/sprites/modonomicon/themes/sift_codex"
RECOLOUR = ("content/backgrounds/", "content/buttons/category/category_button_", "content/buttons/collection/collection_button_",
            "content/decorations/", "content/fields/search/background", "content/pages/media/frame", "frame/")

hexes = lambda s: [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in s.split()]
# light -> dark. Paper: blush vellum leaning lavender in the shade; wood / leather / thread: soul willow teal-blue
# (soul_willow_planks' hue, darker for a frame); accents (gold tabs, frame gems): spirit liquid pink -> magenta
PAPER = hexes("#fbeee8 #f5e3de #eed6d5 #e4c7cc #d5b4bf #c09fb2 #a3849b")
WOOD = hexes("#86c0cd #67a3b4 #4f889b #3e6f82 #2f586a #234452 #18303c")
ACCENT = hexes("#ffd6ea #fba0cb #f47cb8 #d65cc2 #a5459f")
TEXT_COLOUR, TITLE_COLOUR = 0xFF3A2440, 0xFF1F5A63          # deep plum text, deep soul-teal titles on the blush paper


def lum(c): return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255


def family(c):
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
    if s > 0.42 and v > 0.5:
        return "accent"
    return "paper" if lum(c) >= 0.6 else "wood"


def theme_sprites():
    z = zipfile.ZipFile(JAR)
    names = [n for n in z.namelist() if n.startswith(DEF) and n.endswith(".png") and n[len(DEF):].startswith(RECOLOUR)]
    ims = {n[len(DEF):]: Image.open(io.BytesIO(z.read(n))).convert("RGBA") for n in names}
    metas = {n[len(DEF):]: z.read(n) for n in z.namelist() if n.startswith(DEF) and n.endswith(".mcmeta")
             and n[len(DEF):-7] in ims}
    # luminance range of every family over all sprites, so one cream maps to the same blush everywhere
    rng = {}
    for im in ims.values():
        for c in im.get_flattened_data():
            if c[3]:
                f = family(c[:3])
                lo, hi = rng.get(f, (1, 0))
                rng[f] = (min(lo, lum(c[:3])), max(hi, lum(c[:3])))
    ramps = {"paper": PAPER, "wood": WOOD, "accent": ACCENT}
    out = {}
    for rel, im in ims.items():
        o = Image.new("RGBA", im.size)
        px = []
        for c in im.get_flattened_data():
            if not c[3]:
                px.append(c)
                continue
            f = family(c[:3])
            lo, hi = rng[f]
            t = 0 if hi <= lo else (hi - lum(c[:3])) / (hi - lo)          # 0 = lightest of the family
            ramp = ramps[f]
            px.append((*ramp[min(len(ramp) - 1, round(t * (len(ramp) - 1)))], c[3]))
        o.putdata(px)
        out[rel] = o
    return out, metas


def book_item():
    """The codex's item (user: the book item still looked like Modonomicon's): Modonomicon's purple book recoloured the
    same way - soul willow teal cover, spirit-pink emblem, blush pages. book.json "model" points at pysift:sift_codex."""
    src = Image.open(io.BytesIO(zipfile.ZipFile(JAR).read("assets/modonomicon/textures/item/modonomicon_purple.png"))).convert("RGBA")

    def fam(c):                                   # by hue: the book's four materials
        h, s_, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
        h *= 360
        if s_ > 0.55 and 30 <= h <= 65 and v > 0.8:
            return "emblem"                       # gold glyph
        if 25 <= h <= 45 and s_ < 0.45:
            return "pages"
        return "cover" if h >= 270 else "edge"    # purple cover / dark blue page edges
    ramps = {"emblem": ACCENT[:4], "pages": PAPER[1:6] + hexes("#8a6a83 #6d5068"),
             "cover": WOOD[2:] + hexes("#10222c #0a161d"), "edge": hexes("#2b5a78 #23475f #1a3549 #122635")}
    ranked = {}
    for c in sorted({c[:3] for c in src.get_flattened_data() if c[3]}, key=lum, reverse=True):
        ranked.setdefault(fam(c), []).append(c)
    m = {}
    for f, cols in ranked.items():                # rank inside the family, spread over its ramp
        r = ramps[f]
        for i, c in enumerate(cols):
            m[c] = r[min(len(r) - 1, round(i * (len(r) - 1) / max(1, len(cols) - 1)))]
    out = Image.new("RGBA", src.size)
    px = [(*m[c[:3]], c[3]) if c[3] else c for c in src.get_flattened_data()]
    out.putdata(px)
    return out


# ------------------------------------------------------------------------------------------------ category backdrops
def mix(a, b, t): return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


SCENES = {   # sky top, sky horizon, glow at the horizon, strata light / dark, accent motes
    "journey": hexes("#141a2b #23344a #2f6b74 #2a3550 #1a2236 #43c6c8"),   # deep dark, the sculk-teal of the door
    "sift": hexes("#1d1430 #4a2a4f #b0587a #3a3355 #241f3a #f87cb8"),      # The Sift's dusk: violet to rose
    "bestiary": hexes("#251526 #4d2638 #a34e62 #5a2f43 #2f1a2a #54d2c4"),  # rose strata canyon, teal bands
    "bosses": hexes("#24170f #4a2f1a #b07a3a #5a3d22 #2f2014 #f2c46b"),    # amber dunes at dusk
    "gear": hexes("#0f2229 #1d4450 #4d90a4 #24525e #153640 #a4d7e9"),      # soul willow teal, spirit-liquid shine
    "lore": hexes("#1e1527 #3c2640 #8a5a78 #43304a #281d30 #e7b8d4"),      # old violet pages, faded rose
}


def backdrop(cid):
    top, horizon, glow, s_light, s_dark, mote = SCENES[cid]
    rnd = random.Random("codex " + cid)
    W = 128
    g = Image.new("RGB", (W, W))
    # banded sky: 9 bands top -> horizon, the band edges broken by 2-3 px steps (no airbrush gradient)
    bands = [mix(top, horizon, i / 8) for i in range(9)]
    edge = [[rnd.choice((-1, 0, 0, 1)) for _ in range(W)] for _ in range(9)]
    for y in range(W):
        for x in range(W):
            b = min(8, max(0, (y + edge[min(8, y * 9 // W)][x] * 2) * 9 // 96))
            g.putpixel((x, y), bands[b])
    # a soft horizon glow (two bands) behind the strata
    for y in range(78, 92):
        for x in range(W):
            t = 0.35 if 81 <= y + (x * 7 % 3 - 1) <= 88 else 0.18
            g.putpixel((x, y), mix(g.getpixel((x, y)), glow, t))
    # three strata / mesa silhouettes, back to front, each lit on its top edge
    for k, (base, amp, col) in enumerate(((84, 6, mix(s_light, horizon, 0.45)), (94, 8, s_light), (106, 7, s_dark))):
        ph, ph2 = rnd.uniform(0, 6.3), rnd.uniform(0, 6.3)
        steps = [base - round(amp * (0.6 * math.sin(x / 13 + ph) + 0.4 * math.sin(x / 5.3 + ph2))) for x in range(W)]
        for x in range(1, W):                                  # mesa look: flat tops, stepped sides
            if abs(steps[x] - steps[x - 1]) < 2:
                steps[x] = steps[x - 1]
        for x in range(W):
            for y in range(steps[x], W):
                c = col
                if y == steps[x]:
                    c = mix(col, glow, 0.45)                     # lit rim
                elif (y - steps[x]) % 6 == 3 and (x + k * 5) % 9 < 6:
                    c = mix(col, s_dark, 0.4)                    # layer line
                g.putpixel((x, y), c)
    # a few large soft motes in the sky (the parallax layers carry the small ones)
    for _ in range(14):
        x, y = rnd.randrange(W), rnd.randrange(8, 76)
        g.putpixel((x, y), mix(g.getpixel((x, y)), mote, 0.8))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = ((x + dx) % W, y + dy)
            g.putpixel(q, mix(g.getpixel(q), mote, 0.3))
    return g.resize((512, 512), Image.NEAREST)


def motes(n):
    """256 x 256 transparent parallax layer (tiles): sparse 1-2 px soul motes with a faint halo."""
    rnd = random.Random(f"motes {n}")
    cols = hexes("#f87cb8 #54d2c4 #a4d7e9 #e7b8d4")
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for _ in range((40, 26, 14)[n - 1]):
        x, y, c = rnd.randrange(256), rnd.randrange(256), rnd.choice(cols)
        big = n == 3 or rnd.random() < 0.25
        core = [(0, 0)] + ([(1, 0), (0, 1), (1, 1)] if big else [])
        for dx, dy in core:
            im.putpixel(((x + dx) % 256, (y + dy) % 256), (*c, 235))
        for dx, dy in ((-1, 0), (0, -1), (2 if big else 1, 0), (0, 2 if big else 1)):
            q = ((x + dx) % 256, (y + dy) % 256)
            if im.getpixel(q)[3] == 0:
                im.putpixel(q, (*c, 80))
    return im


# ------------------------------------------------------------------------------------------------ preview / apply
def preview(sprites, backs, layers):
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
    sheet = Image.new("RGBA", (1340, 1010), (24, 23, 28, 255))
    d = ImageDraw.Draw(sheet)
    d.text((10, 6), "隙浮手記主題：上 = 書頁、外框、分類籤（左原版 → 右新）；下 = 6 張分類背景（疊上靈魂光點視差層）", fill=(240, 230, 210), font=f)
    z = zipfile.ZipFile(JAR)
    x, y = 10, 30
    for rel in ("frame/frame.png", "frame/top_overlay.png", "content/buttons/category/category_button_normal.png",
                "content/buttons/category/category_button_golden.png", "content/buttons/collection/collection_button_normal.png",
                "content/decorations/book/title_separator.png", "content/fields/search/background.png"):
        old = Image.open(io.BytesIO(z.read(DEF + rel))).convert("RGBA")
        k = 2 if old.width > 100 else 3
        for i, im in enumerate((old, sprites[rel])):
            im = im.resize((im.width * k, im.height * k), Image.NEAREST)
            sheet.alpha_composite(im, (x + i * (im.width + 6), y))
        y += old.height * k + 10
        if y > 330:
            x, y = x + old.width * k * 2 + 30, 30
    dp = sprites["content/backgrounds/book/double_page_background.png"]
    # a page with sample text in the new colours
    page = sprites["content/backgrounds/book/double_page_background.png"].resize((272 * 2, 178 * 2), Image.NEAREST)
    pd = ImageDraw.Draw(page)
    pd.text((40, 40), "啟程", fill=((TITLE_COLOUR >> 16) & 255, (TITLE_COLOUR >> 8) & 255, TITLE_COLOUR & 255), font=f)
    pd.text((40, 64), "在遠古城市的強化深板岩門框前\n吹響山羊角……", fill=((TEXT_COLOUR >> 16) & 255, (TEXT_COLOUR >> 8) & 255, TEXT_COLOUR & 255), font=f)
    sheet.alpha_composite(page, (10, 400))
    old = Image.open(io.BytesIO(z.read(DEF + "content/backgrounds/book/double_page_background.png"))).convert("RGBA")
    sheet.alpha_composite(old.resize((272, 178), Image.NEAREST), (580, 30))
    for i, (cid, im) in enumerate(backs.items()):
        im = im.convert("RGBA").resize((200, 200), Image.NEAREST)
        lay = Image.new("RGBA", (512, 512))
        for L in layers:
            for a in range(2):
                for b in range(2):
                    lay.alpha_composite(L, (a * 256, b * 256))
        im.alpha_composite(lay.resize((200, 200), Image.NEAREST))
        sheet.alpha_composite(im, (580 + (i % 3) * 250, 400 + (i // 3) * 230))
        d.text((580 + (i % 3) * 250, 400 + (i // 3) * 230 + 202), cid, fill=(220, 225, 235), font=f)
    out = P / "build/previews/codex_theme.png"
    sheet.convert("RGB").save(out)
    print("preview:", out.relative_to(P))


def main():
    sprites, metas = theme_sprites()
    backs = {cid: backdrop(cid) for cid in SCENES}
    layers = [motes(n) for n in (1, 2, 3)]
    book = book_item()
    preview(sprites, backs, layers)
    old = Image.open(io.BytesIO(zipfile.ZipFile(JAR).read("assets/modonomicon/textures/item/modonomicon_purple.png"))).convert("RGBA")
    pair = Image.new("RGBA", (16 * 12 * 2 + 20, 16 * 12), (24, 23, 28, 255))
    pair.alpha_composite(old.resize((192, 192), Image.NEAREST), (0, 0))
    pair.alpha_composite(book.resize((192, 192), Image.NEAREST), (212, 0))
    pair.convert("RGB").save(P / "build/previews/codex_book_item.png")
    if not APPLY:
        return
    for rel, im in sprites.items():
        art_guard.save(im, OUT / rel)
        if rel in metas:                                           # nine-slice scaling of the frames stays the same
            (OUT / f"{rel}.mcmeta").write_bytes(metas[rel])
    for cid, im in backs.items():
        dst = A / f"textures/gui/codex/{cid}.png"
        if dst.exists() and not art_guard.is_ours(dst):
            print("  kept (edited by the user):", dst.relative_to(P))
            continue
        art_guard.save(im, dst)
    for n, im in enumerate(layers, 1):
        art_guard.save(im, A / f"textures/gui/codex/motes_{n}.png")
    import json
    tex = A / "textures/item/sift_codex.png"
    if not tex.exists() or art_guard.is_ours(tex):
        art_guard.save(book, tex)
    (A / "models/item/sift_codex.json").write_text(json.dumps(
        {"parent": "minecraft:item/generated", "textures": {"layer0": "pysift:item/sift_codex"}}, indent=2) + "\n", encoding="utf-8")
    (A / "items/sift_codex.json").write_text(json.dumps(
        {"model": {"type": "minecraft:model", "model": "pysift:item/sift_codex"}}, indent=2) + "\n", encoding="utf-8")
    print("applied:", len(sprites), "theme sprites,", len(backs), "backdrops,", len(layers), "parallax layers")


if __name__ == "__main__":
    main()
