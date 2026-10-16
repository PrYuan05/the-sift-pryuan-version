"""The Sift 地表專屬頂面（Dungeons II 風格：柔和漸層、大色塊、低對比、少量細節）。
只換世界生成實際用到的地表方塊的 top（build_the_sift.py 的 CRIMSON_TOP / GROVE_TOP / VIOLET_TOP / 沙丘），側面與共用貼圖的其他方塊不動。
Usage (from the project root):
  python -I tools/texture_pipeline/sift_ground.py            產生預覽 build/previews/sift_batch_2.png
  python -I tools/texture_pipeline/sift_ground.py --apply    寫入 textures/block/sift_ground/ 並把地表模型的 top 指過去（先備份）
"""
import sys, json, math, random, shutil, datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift"
OUT = A / "textures/block/sift_ground"
PREVIEW = P / "build/previews/sift_batch_2.png"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_sift_ground")


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ------------------------------------------------------------------ tileable noise
def value_noise(seed, cells):
    """16x16 可無縫平鋪的值雜訊（cells x cells 格點，平滑插值）。"""
    rnd = random.Random(seed)
    g = [[rnd.random() for _ in range(cells)] for _ in range(cells)]
    out = [[0.0] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            fx, fy = x * cells / 16, y * cells / 16
            x0, y0 = int(fx), int(fy)
            tx, ty = fx - x0, fy - y0
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = g[y0 % cells][x0 % cells]
            b = g[y0 % cells][(x0 + 1) % cells]
            c = g[(y0 + 1) % cells][x0 % cells]
            d = g[(y0 + 1) % cells][(x0 + 1) % cells]
            out[y][x] = (a + (b - a) * tx) + ((c + (d - c) * tx) - (a + (b - a) * tx)) * ty
    return out


def field(seed, octaves=((2, 0.6), (4, 0.3), (8, 0.1))):
    layers = [value_noise(seed * 31 + i, c) for i, (c, _) in enumerate(octaves)]
    f = [[sum(l[y][x] * w for l, (_, w) in zip(layers, octaves)) for x in range(16)] for y in range(16)]
    lo = min(min(r) for r in f)
    hi = max(max(r) for r in f)
    return [[(v - lo) / (hi - lo) for v in r] for r in f]


def ramp(f, pal, bias=0.0, cuts=None):
    """依雜訊值選調色盤階（暗→亮），形成大塊平面色。"""
    n = len(pal)
    cuts = cuts or [(i + 1) / n for i in range(n - 1)]
    im = Image.new("RGBA", (16, 16))
    px = im.load()
    for y in range(16):
        for x in range(16):
            v = min(1, max(0, f[y][x] + bias))
            i = sum(v > c for c in cuts)
            px[x, y] = pal[i] + (255,)
    return im


def soften_edges(im, pal):
    """色塊邊界上，亮的那側加一格過渡色（模擬手繪柔邊），只在相鄰階之間。"""
    src = im.copy().load()
    px = im.load()
    idx = {c: i for i, c in enumerate(pal)}
    for y in range(16):
        for x in range(16):
            c = idx.get(src[x, y][:3])
            if c is None or c == 0:
                continue
            above = idx.get(src[x, (y - 1) % 16][:3])
            if above is not None and above < c:   # 上方較暗：這格當陰影過渡（光從下方/前方）
                m = tuple((a + b) // 2 for a, b in zip(pal[c], pal[c - 1]))
                px[x, y] = m + (255,)
    return im


# ------------------------------------------------------------------ details
def pebbles(im, seed, n, light, dark):
    rnd = random.Random(seed)
    px = im.load()
    for _ in range(n):
        x, y = rnd.randrange(16), rnd.randrange(16)
        w = rnd.choice((1, 2, 2))
        for dx in range(w):
            px[(x + dx) % 16, y] = light + (255,)
            px[(x + dx) % 16, (y + 1) % 16] = dark + (255,)
    return im


def cracks(im, seed, n, color):
    rnd = random.Random(seed)
    px = im.load()
    for _ in range(n):
        x, y = rnd.randrange(16), rnd.randrange(16)
        for _ in range(rnd.randint(3, 5)):
            px[x % 16, y % 16] = color + (255,)
            x += rnd.choice((1, 1, 0))
            y += rnd.choice((1, 0, -1))
    return im


def leaves(im, seed, n, cols, outline):
    """珊瑚色落葉：2x3 / 3x2 的小葉片，一側較暗。"""
    rnd = random.Random(seed)
    px = im.load()
    shapes = [((0, 0), (1, 0), (0, 1), (1, 1), (1, 2)), ((0, 0), (1, 0), (2, 0), (1, 1), (2, 1)),
              ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2))]
    for _ in range(n):
        x, y = rnd.randrange(16), rnd.randrange(16)
        c = rnd.choice(cols)
        sh = rnd.choice(shapes)
        for dx, dy in sh:
            px[(x + dx) % 16, (y + dy) % 16] = c + (255,)
        dx, dy = sh[-1]
        px[(x + dx) % 16, (y + dy + 1) % 16] = outline + (255,)
    return im


def flowers(im, seed, n, petal, centre):
    """黃色四瓣小花（十字形，中心深黃）。"""
    rnd = random.Random(seed)
    px = im.load()
    spots = []
    while len(spots) < n:
        x, y = rnd.randrange(16), rnd.randrange(16)
        if all(min(abs(x - a), 16 - abs(x - a)) + min(abs(y - b), 16 - abs(y - b)) > 6 for a, b in spots):
            spots.append((x, y))
    for x, y in spots:
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            px[(x + dx) % 16, (y + dy) % 16] = petal + (255,)
        px[x, y] = centre + (255,)
    return im


def ripples(im, seed, col, every=4):
    """沙紋：斜向波浪的亮線。"""
    rnd = random.Random(seed)
    px = im.load()
    ph = rnd.uniform(0, math.tau)
    for x in range(16):
        off = round(1.2 * math.sin(x / 16 * math.tau + ph))
        for k in range(0, 16, every):
            px[x, (k + off) % 16] = col + (255,)
    return im


# ------------------------------------------------------------------ the tops
CANYON = [hx(c) for c in ("#A63A4A", "#B44452", "#C0505C", "#CB5E68")]
GROVE = [hx(c) for c in ("#C25648", "#CE6250", "#D96E58", "#E27C62")]
VIOLET = [hx(c) for c in ("#7A6A98", "#8676A4", "#9282AE", "#9E8FB8")]
AMBER = [hx(c) for c in ("#D9A654", "#E0AE5C", "#E6B664", "#ECBF6E")]
PALE = [hx(c) for c in ("#E8C892", "#EDD09C", "#F1D7A6", "#F5DFB2")]


def canyon(seed):
    im = ramp(field(seed), CANYON)
    return pebbles(im, seed + 1, 1, hx("#D8828A"), hx("#9A3444"))


def grove(seed, n_flowers=1):
    im = ramp(field(seed), GROVE)
    leaves(im, seed + 1, 4, [hx("#E8866A"), hx("#EC9474")], hx("#B85044"))
    return flowers(im, seed + 2, n_flowers, hx("#FFD34A"), hx("#E8962E")) if n_flowers else im


def violet(seed):
    im = ramp(field(seed), VIOLET)
    pebbles(im, seed + 1, 1, hx("#B8A9D0"), hx("#6E5E8C"))
    return cracks(im, seed + 2, 1, hx("#6E5E8C"))


def sand(seed, pal):
    im = ramp(field(seed), pal)
    return ripples(im, seed + 1, tuple(min(255, c + 8) for c in pal[-1]), every=8)


def build():
    """回傳 {貼圖名: Image} 與 [(模型檔, 新 top 貼圖名)]。"""
    tex = {f"canyon_top_{k}": canyon(100 + i) for i, k in enumerate("abcd")}
    tex["grove_top"] = grove(200, 1)
    tex["grove_top_b"] = grove(210, 0)
    tex["violet_top"] = violet(300)
    tex["violet_top_b"] = violet(310)
    sands = {"amber_sand": sand(400, AMBER), "pale_sand": sand(410, PALE)}
    models = [(f"crimson_capped_crimson_strata_3/crimson_capped_crimson_strata_3_{i + 1}", f"canyon_top_{k}") for i, k in enumerate("abcd")]
    models += [("crimson_capped_crimson_strata_2/crimson_capped_crimson_strata_2_1", "grove_top"),
               ("violet_capped_dark_slate/violet_capped_dark_slate_1", "violet_top")]
    return tex, sands, models


# ------------------------------------------------------------------ preview
def old_top(model):
    j = json.loads((A / "models/block" / f"{model}.json").read_text(encoding="utf-8"))
    ref = j["textures"]["top"].split(":")[1]
    return Image.open(A / "textures" / f"{ref}.png").convert("RGBA").crop((0, 0, 16, 16))


def tile(im, n=4, s=8):
    big = im.resize((16 * s, 16 * s), Image.NEAREST)
    out = Image.new("RGBA", (16 * s * n, 16 * s * n))
    for i in range(n):
        for j in range(n):
            out.paste(big, (i * 16 * s, j * 16 * s))
    return out


def mixed_tile(ims, n=4, s=8, seed=7):
    """隨機變體平鋪（模擬 blockstate 的隨機模型）。"""
    rnd = random.Random(seed)
    out = Image.new("RGBA", (16 * s * n, 16 * s * n))
    for i in range(n):
        for j in range(n):
            out.paste(rnd.choice(ims).resize((16 * s, 16 * s), Image.NEAREST), (i * 16 * s, j * 16 * s))
    return out


def preview(tex, sands, models):
    font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 15)
    rows = [("赤紅峽谷地表（4 種隨機變體）", [old_top(m) for m, _ in models[:4]], [tex[f"canyon_top_{k}"] for k in "abcd"]),
            ("柳林地表：珊瑚落葉＋黃色四瓣小花", [old_top(models[4][0])], [tex["grove_top"], tex["grove_top_b"]]),
            ("紫晶區地表：淡紫石面", [old_top(models[5][0])], [tex["violet_top"], tex["violet_top_b"]]),
            ("沙丘：琥珀沙", [Image.open(A / "textures/block/amber_sand/amber_sand.png").convert("RGBA")], [sands["amber_sand"]]),
            ("沙丘點綴：淡沙", [Image.open(A / "textures/block/pale_sand/pale_sand.png").convert("RGBA")], [sands["pale_sand"]])]
    T = 256
    sheet = Image.new("RGB", (T * 2 + 3 * 10 + 140, len(rows) * (T + 34) + 10), (34, 33, 40))
    d = ImageDraw.Draw(sheet)
    for i, (title, old, new) in enumerate(rows):
        y = 10 + i * (T + 34)
        d.text((10, y), f"{title}    左：舊（4x4 平鋪）  右：新（4x4 平鋪）", fill=(235, 235, 235), font=font)
        sheet.paste(mixed_tile(old, s=4).convert("RGB"), (10, y + 24))
        sheet.paste(mixed_tile(new, s=4).convert("RGB"), (20 + T, y + 24))
        for k, im in enumerate(new[:4]):   # 單張放大
            sheet.paste(im.resize((64, 64), Image.NEAREST).convert("RGB"), (30 + 2 * T + (k % 2) * 68, y + 24 + (k // 2) * 68))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)


# ------------------------------------------------------------------ apply
def backup(p):
    if p.exists():
        dst = BK / p.relative_to(P)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)


def main():
    tex, sands, models = build()
    preview(tex, sands, models)
    print("preview:", PREVIEW)
    if "--apply" not in sys.argv:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for n, im in tex.items():
        backup(OUT / f"{n}.png")
        im.save(OUT / f"{n}.png")
    for n, im in sands.items():
        p = A / f"textures/block/{n}/{n}.png"
        backup(p)
        im.save(p)
    for m, t in models:
        p = A / "models/block" / f"{m}.json"
        backup(p)
        j = json.loads(p.read_text(encoding="utf-8"))
        j["textures"]["top"] = f"pysift:block/sift_ground/{t}"
        p.write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 柳林、紫晶區多一個頂面變體：複製模型成 <model>_b，並在 blockstate 每個 facing 的清單裡加一筆同樣旋轉的項目
    for m, t in ((models[4][0], "grove_top_b"), (models[5][0], "violet_top_b")):
        j = json.loads((A / "models/block" / f"{m}.json").read_text(encoding="utf-8"))
        j["textures"]["top"] = f"pysift:block/sift_ground/{t}"
        (A / "models/block" / f"{m}_b.json").write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        bs = A / "blockstates" / f"{m.split('/')[0]}.json"
        backup(bs)
        js = json.loads(bs.read_text(encoding="utf-8"))
        ref, ref_b = f"pysift:block/{m}", f"pysift:block/{m}_b"
        for key, v in js["variants"].items():
            lst = v if isinstance(v, list) else [v]
            if not any(e["model"] == ref_b for e in lst):
                lst += [{**e, "model": ref_b} for e in lst if e["model"] == ref]
            js["variants"][key] = lst
        bs.write_text(json.dumps(js, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("applied; backups in", BK)


if __name__ == "__main__":
    main()
