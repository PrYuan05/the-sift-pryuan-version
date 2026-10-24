"""把裂隙植被（install_rift_flora.py 裝進來的交叉平面草）改成和 gen_blade_models.py 一樣的粗短 3D 葉片。
顏色不靠染色：從使用者原本的貼圖取色（依亮度由暗到亮），畫成 <name>_blades.png 葉片圖集；原貼圖保留給物品圖示與粒子。
Usage: python -I tools/models/gen_rift_blades.py [--apply]
  不加 --apply 只輸出預覽 build/previews/rift_blades.png；--apply 另外寫入正式資源（先備份到 .texture_backups/）。
"""
import sys, json, math, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import art_guard   # 臨時圖保護：使用者用同檔名覆蓋過的貼圖不會被重跑蓋掉
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_blade_models as g

A = g.A
VEG = A / "textures/block/vegetation"
PREVIEW = g.P / "build/previews/rift_blades.png"


def palette(src, n=6):
    im = Image.open(VEG / f"{src}.png").convert("RGBA")
    cols = sorted({c[:3] for c in im.get_flattened_data() if c[3] > 128}, key=lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
    return [cols[round(i * (len(cols) - 1) / (n - 1))] for i in range(n)]


def colorize(gray, pal):
    """灰階葉片圖集 → 依亮度對到調色盤（暗 = 根部，亮 = 尖端）。"""
    out = gray.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, gg, b, a = px[x, y]
            if a == 0 or (x >= 12 and y < 4):   # 發光點區不動
                continue
            t = min(1.0, max(0.0, (r / 255 - 0.45) / 0.62)) * (len(pal) - 1)
            i = min(len(pal) - 2, int(t))
            f = t - i
            c = tuple(round(pal[i][k] + (pal[i + 1][k] - pal[i][k]) * f) for k in range(3))
            px[x, y] = c + (255,)
    return out


def untint(els):
    for e in els:
        for f in e["faces"].values():
            f.pop("tintindex", None)
    return els


def curled_tuft(seed, n):
    """捲蕨：每片葉子三段，最後一段大幅往外捲（像蕨類的捲頭）。"""
    rnd = random.Random(seed)
    els = []
    for i in range(n):
        yaw = 360 * i / n + rnd.uniform(-20, 20)
        r = rnd.uniform(1.0, 3.6)
        a = math.radians(yaw + 90)
        cx, cz = 8 + math.cos(a) * r, 8 + math.sin(a) * r
        lean1, lean2 = rnd.uniform(10, 20), rnd.uniform(8, 16)
        h1, h2 = rnd.uniform(5, 7), rnd.uniform(4, 6)
        lo, up = g.blade(cx, cz, yaw, h1, h2, lean1, lean2, i % 3, w=2.0)
        top = g.ry(g.rx((0, h1, 0), lean1), yaw)
        tip = g.ry(g.rx((0, h2, 0), lean1 + lean2), yaw)
        p = (cx + top[0] + tip[0], top[1] + tip[1], cz + top[2] + tip[2])
        hook = g.box((p[0] - 0.9, p[1], p[2] - 0.45), (p[0] + 0.9, p[1] + 2.6, p[2] + 0.45), (lean1 + lean2 + 75, yaw, 0), p,
                     g.blade_faces(i % 3, "tip", thick=0.9))
        els += [lo, up, hook]
    return els


def forked_stalk():
    """橄欖叉莖：中央 2x2 主幹，兩側各兩根先橫出再往上的分枝（像燭台仙人掌）。"""
    def stick(frm, to, col=1, part="base"):
        faces = {d: dict(f) for d, f in g.blade_faces(col, part).items()}
        u0 = col * 4
        for d in ("east", "west"):   # 主幹有厚度：側面也貼整欄
            faces[d]["uv"] = [u0, faces[d]["uv"][1], u0 + 3, faces[d]["uv"][3]]
        faces["up"] = {"uv": [u0, 8, u0 + 2, 10], "texture": "#0"}
        return {"from": list(frm), "to": list(to), "shade_direction_override": "up", "faces": faces}
    els = [stick((7, 0, 7), (9, 13, 9), 1, "base"), stick((7.25, 13, 7.25), (8.75, 15, 8.75), 2, "tip")]
    for side, y, length, up in ((-1, 5, 3, 4), (1, 8, 3, 4), (-1, 10, 2, 3), (1, 3, 2, 3)):
        x0 = 7 if side < 0 else 9
        x1 = x0 + side * length
        els.append(stick((min(x0, x1), y, 7.25), (max(x0, x1), y + 1.5, 8.75), 0, "base"))
        xa = min(x1, x1 - side * 1.5)
        els.append(stick((xa, y + 1.5, 7.25), (xa + 1.5, y + 1.5 + up, 8.75), 2, "tip"))
    return els


def build():
    m, tex = {}, {}

    def grass(name, src, seed, n, h1, h2, l1, l2, rad, w=3.0):
        tex[name] = colorize(g.blade_texture("grass"), palette(src))
        m[name] = (untint(g.tuft(seed, n, h1, h2, l1, l2, rad, w=w)), name)
    # 裂隙橙／紅／薄荷短草與橙高草已改用 sift_vegetation_assets 的十字貼圖（tools/worldgen/rename_vegetation.py），不再產生 3D 葉片
    grass("rift_yellow_short_grass", "rift_yellow_short_grass", 83, 10, (3.5, 5), (3, 5), (6, 16), (8, 20), 4.2, w=2.5)
    for c, seed in (("blue", 91), ("pink", 97), ("white", 101)):
        name = f"{c}_curled_fern"
        tex[name] = colorize(g.blade_texture("grass"), palette(name))
        m[name] = (untint(curled_tuft(seed, 6)), name)
    tex["olive_forked_stalk"] = colorize(g.blade_texture("bush"), palette("olive_forked_stalk"))
    m["olive_forked_stalk"] = (untint(forked_stalk()), "olive_forked_stalk")
    return m, tex


def model_json(els, atlas, particle):
    return {"format_version": "26.3", "ambientocclusion": False,
            "textures": {"0": f"pysift:block/vegetation/{atlas}_blades", "particle": f"pysift:block/vegetation/{particle}"},
            "elements": els}


def preview(m, tex):
    rows = list(dict.fromkeys(k.replace("_bottom", "").replace("_top", "") for k in m))
    W = 230
    cols = 5
    sheet = Image.new("RGB", (cols * (W + 10) + 10, ((len(rows) + cols - 1) // cols) * (W + 30) + 10), (34, 33, 40))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 14)
    for i, r in enumerate(rows):
        parts = [r] if r in m else [r + "_bottom", r + "_top"]
        c = g.Canvas(W, W, 5.5 if len(parts) == 2 else 9)
        c.ground((0, 0, 0), (150, 135, 170))
        for k, p in enumerate(parts):
            els, tn = m[p]
            for e in els:
                c.element(e, {"#0": tex[tn]}, (255, 255, 255), (0, 16 * k, 0))
        x, y = 10 + (i % cols) * (W + 10), 10 + (i // cols) * (W + 30)
        sheet.paste(c.img, (x, y + 22))
        d.text((x, y + 2), r, fill=(235, 235, 235), font=font)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)


def main():
    m, tex = build()
    preview(m, tex)
    if "--apply" in sys.argv:
        for n, im in tex.items():
            p = VEG / f"{n}_blades.png"
            g.backup(p)
            art_guard.save(im, p)
        for n, (els, tn) in m.items():
            particle = n if (VEG / f"{n}.png").exists() else tn
            p = A / g.MODEL_DIR / f"{n}.json"
            g.backup(p)
            g.write_json(p, model_json(els, tn, particle))
        print("applied; backups in", g.BK)
    for n, (els, _) in m.items():
        print(n, len(els), "elements")
    print("preview:", PREVIEW)


if __name__ == "__main__":
    main()
