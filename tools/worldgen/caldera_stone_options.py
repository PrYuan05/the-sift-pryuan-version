"""Soul Caldera: real-stone candidates for every block, as 16x16 sketches in the chosen "mix" palette (read-only preview).
Usage: python -I tools/worldgen/caldera_stone_options.py <project>
Writes art_requests/soul_caldera_stone_options.png and .md. Nothing in the game is changed.

The palette and the current structures come from paint_soul_caldera.py (--palette=mix). Every candidate is built on the same
basalt grain so they can sit next to each other; only the structure differs.
"""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]).resolve()
sys.argv = [sys.argv[0], str(P), "--palette=mix"]
sys.path.insert(0, str(P / "tools/worldgen"))
import paint_soul_caldera as pc
from paint_soul_caldera import BAS, MOSS, CRIM, EMB, RUST, ASH, SILV, GREEN, COPPER, rock, wrap, ALL

QUARTZ = [(0xE6, 0xE2, 0xD8), (0xC9, 0xC6, 0xBE), (0xA9, 0xA8, 0xA4)]
GALENA = [(0xC8, 0xCB, 0xD2), (0x9A, 0x9F, 0xAA), (0x6E, 0x73, 0x80), (0x4A, 0x4E, 0x5A)]
AZURITE = [(0x5E, 0x86, 0xC4), (0x3E, 0x63, 0xA6), (0x2A, 0x45, 0x7E)]


def put(img, p, c): img.putpixel(wrap(*p), (*c, 255))


def voronoi(seed, n, rows=None, jitter=1.4):
    rnd = random.Random(seed)
    if rows:
        pts = [((k * 16 / rows[1] + (8 / rows[1] if r % 2 else 0) + rnd.uniform(-jitter, jitter)) % 16,
                (r * 16 / rows[0] + rnd.uniform(-jitter, jitter)) % 16) for r in range(rows[0]) for k in range(rows[1])]
    else:
        pts = [(rnd.uniform(0, 16), rnd.uniform(0, 16)) for _ in range(n)]
    d = lambda x, y, p: math.hypot(min(abs(x + .5 - p[0]), 16 - abs(x + .5 - p[0])), min(abs(y + .5 - p[1]), 16 - abs(y + .5 - p[1])))
    return {(x, y): min(range(len(pts)), key=lambda i: d(x, y, pts[i])) for (x, y) in ALL}


def plates(seed, n, body, lit, joint, rows=None, glow=None):
    """Polygonal plates: lit top-left edges, `joint` colour on the bottom-right joints, optional glow on some joints."""
    own = voronoi(seed, n, rows)
    rnd = random.Random(seed + "g")
    img = rock(seed)
    for (x, y) in ALL:
        o = own[(x, y)]
        if own[wrap(x + 1, y)] != o or own[wrap(x, y + 1)] != o:
            c = joint if not glow or rnd.random() > 0.55 else glow[rnd.randrange(len(glow))]
        elif own[wrap(x - 1, y)] != o or own[wrap(x, y - 1)] != o:
            c = lit
        else:
            c = body[(o + x // 3 + y // 4) % len(body)]
        put(img, (x, y), c)
    return img


# ---------------------------------------------------------------- red_sculk_vein_bottom (rift floor / scorched belt)
def jasper():
    """Hematite-banded jasper: wavy scorch-red bands through the basalt, lit upper edges."""
    img = rock("jasper")
    rnd = random.Random("jasper")
    ph = rnd.uniform(0, 16)
    for y in range(16):
        for x in range(16):
            v = (y + round(2 * math.sin(2 * math.pi * (x + ph) / 16))) % 8
            if v in (2, 3):
                put(img, (x, y), CRIM[0] if v == 2 else CRIM[2])
            elif v == 4:
                put(img, (x, y), CRIM[3])
    return img


def agglomerate():
    """Volcanic agglomerate: rounded scorched clasts (2-4 px) in the basalt, each lit top-left, shadowed below."""
    img = rock("agglom")
    rnd = random.Random("agglom")
    for _ in range(9):
        cx, cy, r = rnd.randrange(16), rnd.randrange(16), rnd.choice((1.2, 1.6, 2.0))
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if dx * dx + dy * dy <= r * r:
                    put(img, (cx + dx, cy + dy), CRIM[0] if dx + dy < -1 else CRIM[2] if dx + dy > 1 else CRIM[1])
        put(img, (cx, cy + round(r) + 1), BAS[6])
    return img


def lava_glaze():
    """Lava-tube glaze: dribbles of glassy scorched glaze running down the basalt, lit on top."""
    img = rock("glaze")
    rnd = random.Random("glaze")
    for x0 in rnd.sample(range(16), 6):
        y = rnd.randrange(16)
        for k in range(rnd.randint(4, 8)):
            put(img, (x0, y + k), CRIM[0] if k == 0 else CRIM[1] if k % 3 else CRIM[2])
            put(img, (x0 + 1, y + k), CRIM[3])
    return img


# ---------------------------------------------------------------- rusted_dark_cobble (volcanic slope)
def lapilli(rust):
    """Lapilli tuff: rounded lapilli (2-3 px, some rusty) in a fine ash matrix."""
    img = Image.new("RGBA", (16, 16))
    for (x, y) in ALL:
        put(img, (x, y), ASH[1] if (x * 5 + y * 3) % 7 else BAS[2])
    rnd = random.Random("lapilli")
    for i in range(14):
        cx, cy = rnd.randrange(16), rnd.randrange(16)
        cols = RUST if i < rust else BAS[1:4]
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)) if i % 2 else ((0, 0), (1, 0), (0, 1)):
            put(img, (cx + dx, cy + dy), cols[0] if (dx, dy) == (0, 0) else cols[1])
        put(img, (cx + 1, cy + 2), BAS[5])
    return img


def spatter(rust):
    """Spatter agglutinate: flattened welded lava blobs stacked like pancakes, a few rusty ones."""
    img = rock("spatter")
    rnd = random.Random("spatter")
    for i in range(10):
        cx, cy, w = rnd.randrange(16), rnd.randrange(16), rnd.randint(4, 6)
        cols = RUST if i < rust else BAS[1:4]
        for k in range(w):
            put(img, (cx + k, cy), cols[0])
            put(img, (cx + k, cy + 1), cols[1])
        put(img, (cx + w, cy + 1), BAS[6])
        for k in range(w):
            put(img, (cx + k, cy + 2), BAS[5])
    return img


# ---------------------------------------------------------------- capped ember stones (crater rim)
def aa_clinker(crust):
    """Aa lava clinker: jagged broken clumps of crust with dark gaps and a few warm embers deep in them."""
    own = voronoi("aa", 11)
    rnd = random.Random("aa")
    img = rock("aa")
    for (x, y) in ALL:
        o = own[(x, y)]
        edge = own[wrap(x + 1, y)] != o or own[wrap(x, y + 1)] != o
        if edge:
            put(img, (x, y), EMB[2] if rnd.random() < 0.12 else BAS[6])
        else:
            put(img, (x, y), crust[0] if own[wrap(x - 1, y)] != o or own[wrap(x, y - 1)] != o else crust[(x + y + o) % 2 + 1 if len(crust) > 2 else 1])
    return img


def lava_lake(crust):
    """Lava-lake crust: smooth cooled plates with glowing ember joints between them."""
    return plates("lake", 7, [crust[1]], crust[0], EMB[3], glow=EMB[1:3])


# ---------------------------------------------------------------- magma_vein_slate (cliffs)
def columnar(vein):
    """Columnar basalt with glowing joints: 4 / 5 px columns, cross joints staggered; vein level = how many joints glow."""
    img = rock("columns")
    widths, x = [4, 5, 4, 3], 0
    for k, w in enumerate(widths):
        for y in range(16):
            for i in range(w):
                c = BAS[1] if i == 0 else BAS[5] if i == w - 1 else None
                if c:
                    put(img, (x + i, y), c)
            put(img, (x + w - 1, y), BAS[6] if vein == 0 or (y + k) % 4 else EMB[2 if vein == 1 else 1])
        yc = (3 + 5 * k) % 16
        for i in range(w - 1):
            put(img, (x + i, yc), CRIM[2] if vein == 0 else EMB[2])
        x += w
    return img


def ignimbrite(vein):
    """Welded ignimbrite: grey ash with flattened dark fiamme lenses; vein 1-2 add scorched / glowing lenses."""
    img = Image.new("RGBA", (16, 16))
    for (x, y) in ALL:
        put(img, (x, y), BAS[2] if (x + 2 * y) % 5 else BAS[3])
    rnd = random.Random("ign")
    for i in range(9):
        cx, cy, w = rnd.randrange(16), rnd.randrange(16), rnd.randint(3, 6)
        c = BAS[5] if i >= (1, 3, 5)[vein] else (CRIM[1] if vein == 1 else EMB[1])
        for k in range(w):
            put(img, (cx + k, cy), c)
        put(img, (cx, cy - 1), BAS[1])
    return img


def obsidian(vein):
    """Flow-banded obsidian: glassy dark bands with a 1 px sheen, scorched / glowing flow lines for higher veins."""
    img = Image.new("RGBA", (16, 16))
    rnd = random.Random("obs")
    ph = rnd.uniform(0, 16)
    for y in range(16):
        for x in range(16):
            v = (y + round(1.5 * math.sin(2 * math.pi * (x + ph) / 16))) % 5
            put(img, (x, y), (BAS[5], BAS[6], BAS[4], BAS[6], BAS[5])[v])
    for k in range(5):
        x, y = rnd.randrange(16), rnd.randrange(16)
        for q in range(4):
            put(img, (x + q, y), BAS[1])
    for k in range((1, 3, 5)[vein]):
        y0 = rnd.randrange(16)
        for x in range(16):
            put(img, (x, y0 + round(1.5 * math.sin(2 * math.pi * (x + ph) / 16))), CRIM[1] if vein < 2 else EMB[1])
    return img


# ---------------------------------------------------------------- ores
def silver_quartz():
    img = rock("mossy_top_rock")
    for x in range(2, 14):
        y = 6 + round(1.2 * math.sin(x / 2))
        for dy in range(3):
            put(img, (x, y + dy), QUARTZ[0] if dy == 0 else QUARTZ[1])
        put(img, (x, y + 3), BAS[6])
    for x in (4, 8, 11):
        y = 6 + round(1.2 * math.sin(x / 2))
        put(img, (x, y + 1), SILV[0])
        put(img, (x + 1, y + 1), SILV[2])
    return img


def galena():
    img = rock("mossy_top_rock")
    for cx, cy in ((3, 3), (9, 4), (5, 9), (10, 10)):
        for dx in range(3):
            for dy in range(3):
                put(img, (cx + dx, cy + dy), GALENA[0] if dy == 0 else GALENA[1] if dx < 2 else GALENA[2])
        for dx in range(3):
            put(img, (cx + dx, cy + 3), BAS[6])
    return img


def malachite_nodule():
    img = rock("mossy_top_rock")
    for cx, cy, r in ((6, 6, 3.4), (11, 11, 2.2)):
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                d = math.hypot(dx, dy)
                if d <= r:
                    put(img, (cx + dx, cy + dy), GREEN[int(d) % 3])
        put(img, (cx, cy + round(r) + 1), BAS[6])
    return img


def azurite():
    img = rock("mossy_top_rock")
    rnd = random.Random("azur")
    for cx, cy in ((4, 4), (10, 5), (6, 10), (11, 11)):
        for k in range(4):
            a = rnd.uniform(0, 6.28)
            for t in range(3):
                put(img, (cx + round(math.cos(a) * t), cy + round(math.sin(a) * t)), AZURITE[t] if k % 2 else GREEN[t])
        put(img, (cx, cy + 3), BAS[6])
    return img


warm = ASH + [BAS[2]]
scorch = [CRIM[0], CRIM[1], CRIM[3]]
GROUPS = [
    ("苔蘚虛黑岩（地表）", "mossy_void_stone", [
        ("目前：冰島玄武岩＋羊毛蘚", "Basalt + woolly moss", lambda: pc.moss_top(2)[0]),
        ("側面垂苔", "side", lambda: pc.moss_side(2)[0]),
        ("厚苔 moss 3", "moss 3", lambda: pc.moss_top(3)[0])]),
    ("赤紅紋岩（裂谷底、燒焦帶）", "red_sculk_vein_bottom", [
        ("目前：氧化脈網", "Oxidised veinlets", pc.sculk_vein),
        ("赤鐵碧玉（條帶）", "Banded hematite jasper", jasper),
        ("火山集塊岩", "Volcanic agglomerate", agglomerate),
        ("熔岩管釉", "Lava-tube glaze", lava_glaze)]),
    ("鏽蝕深色圓石（火山坡，rust 2）", "rusted_dark_cobble", [
        ("目前：火山渣圓石", "Scoria cobbles", lambda: pc.cobble(7)),
        ("火山礫凝灰岩", "Lapilli tuff", lambda: lapilli(6)),
        ("熔結堆積（餅狀）", "Spatter agglutinate", lambda: spatter(5))]),
    ("暖褐覆蓋餘燼石（火山口緣，頂面）", "warm_capped_ember_stone", [
        ("目前：繩狀熔岩殼", "Pahoehoe ropes", lambda: pc.crust_top(warm, "warm_capped_ember_stone")[0]),
        ("渣狀熔岩（aa）", "Aa clinker", lambda: aa_clinker(warm)),
        ("熔岩湖冷卻殼", "Lava-lake crust", lambda: lava_lake(warm))]),
    ("赤紅覆蓋餘燼石（燒焦口，頂面）", "crimson_capped_ember_stone", [
        ("目前：焦紅繩狀殼", "Scorched pahoehoe", lambda: pc.crust_top(scorch, "crimson_capped_ember_stone")[0]),
        ("焦紅渣狀熔岩", "Scorched aa", lambda: aa_clinker(scorch)),
        ("焦紅熔岩湖殼", "Scorched lake crust", lambda: lava_lake(scorch))]),
    ("熔脈板岩（崖壁，vein 2）", "magma_vein_slate", [
        ("目前：板岩＋岩脈", "Slate cut by dykes", lambda: pc.vein_slate(2, "magma_vein_slate_vein2_a")[0]),
        ("柱狀玄武岩發光節理", "Columnar basalt", lambda: columnar(2)),
        ("熔結凝灰岩（火焰石）", "Welded ignimbrite", lambda: ignimbrite(2)),
        ("流紋黑曜岩", "Flow-banded obsidian", lambda: obsidian(2))]),
    ("銀白礦", "argent_ore", [
        ("目前：樹枝狀自然銀", "Dendritic native silver", pc.argent),
        ("含銀石英脈", "Silver in quartz", silver_quartz),
        ("方鉛礦（含銀）", "Argentiferous galena", galena)]),
    ("銅綠礦（oxidation 1）", "patina_ore", [
        ("目前：銅＋矽孔雀石", "Copper + chrysocolla", lambda: pc.patina(1)),
        ("孔雀石結核", "Malachite nodules", malachite_nodule),
        ("藍銅礦＋孔雀石", "Azurite + malachite", azurite)]),
]


def main():
    fb = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 15)
    f = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 12)
    S, cw = 80, 2 * 80 + 24
    W = 12 + 4 * cw
    H = 40 + len(GROUPS) * (S + 74)
    sheet = Image.new("RGB", (W, H), (24, 24, 30))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "靈魂火山口石材對照（混合色票：A 的苔／焦紅／銅綠＋暖餘燼；苔參考 soul_willow_planks）每格：單張｜3×3 平鋪",
           fill=(240, 232, 205), font=fb)
    lines = ["# 靈魂火山口石材對照", "", "由 `tools/worldgen/caldera_stone_options.py` 產生（不改遊戲檔）。圖：`art_requests/soul_caldera_stone_options.png`。", ""]
    y = 40
    for title, block, cands in GROUPS:
        d.text((10, y), f"{title}  `{block}`", fill=(255, 215, 150), font=fb)
        lines += [f"## {title}（`{block}`）", ""]
        for i, (zh, en, fn) in enumerate(cands):
            im = fn().convert("RGB")
            x = 10 + i * cw
            sheet.paste(im.resize((S, S), Image.NEAREST), (x, y + 22))
            t = Image.new("RGB", (48, 48))
            for a in range(3):
                for b in range(3):
                    t.paste(im, (a * 16, b * 16))
            sheet.paste(t.resize((S, S), Image.NEAREST), (x + S + 4, y + 22))
            d.text((x, y + 24 + S), f"{chr(65 + i)} {zh}", fill=(220, 225, 235), font=f)
            d.text((x, y + 40 + S), en, fill=(160, 170, 185), font=f)
            lines.append(f"- **{chr(65 + i)}** {zh}（{en}）")
        lines.append("")
        y += S + 74
    out = P / "art_requests/soul_caldera_stone_options.png"
    sheet.save(out)
    (P / "art_requests/soul_caldera_stone_options.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out.relative_to(P))


if __name__ == "__main__":
    main()
