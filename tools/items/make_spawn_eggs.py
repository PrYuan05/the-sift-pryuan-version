"""每隻生物一顆專屬生怪蛋（仿 26.3 原版新式生怪蛋：把生物最有辨識度的臉畫在蛋上）。
Usage: python -I tools/items/make_spawn_eggs.py [--apply]
  預覽 build/previews/spawn_eggs.png（左：新蛋，右：生物正面 3D）；--apply 寫入 textures/item/<mob>_spawn_egg.png（先備份）。

做法：
  1. 蛋形剪影（自己畫的 16x16，上窄下寬）。
  2. 把生物從正面渲染成每單位 1 像素的平面圖（包含眼睛等小方塊）；蛋殼底色＝這張圖最常見的顏色，加球面光影。
  3. 臉：整隻很小就整隻放上去，否則放頭部那段，以原本像素大小貼在蛋的正面（太大才縮到 10x10）。
  4. 邊緣一圈加深成外框，左上一點高光。
OVERRIDE 可以為個別生物指定改用哪個骨骼（例如臉不在 head 上的生物）。
"""
import sys, json, shutil, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import art_guard   # 臨時圖保護：使用者用同檔名覆蓋過的貼圖不會被重跑蓋掉
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift"
GEO = A / "geckolib/models/entity"
OUT = A / "textures/item"
PREVIEW = P / "build/previews/spawn_eggs.png"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_spawn_eggs")
OVERRIDE = {}   # mob → 骨骼名稱

# 蛋形：每一列（y=1..15）的左右界（含），16x16
ROWS = {1: (6, 9), 2: (5, 10), 3: (4, 11), 4: (4, 11), 5: (3, 12), 6: (3, 12), 7: (3, 12), 8: (2, 13), 9: (2, 13),
        10: (2, 13), 11: (2, 13), 12: (3, 12), 13: (3, 12), 14: (4, 11), 15: (6, 9)}


def egg_mask():
    m = [[False] * 16 for _ in range(16)]
    for y, (a, b) in ROWS.items():
        for x in range(a, b + 1):
            m[y][x] = True
    return m


def north_faces(geo, bone_names):
    """[(bone, (x0, y0, x1, y1, flip_x, flip_y))]：這些骨骼裡每塊方塊的正面（north）貼圖範圍。"""
    out = []
    for bone in geo["bones"]:
        if bone["name"] not in bone_names:
            continue
        for c in bone.get("cubes", []):
            uv = c.get("uv")
            w, h, d = c["size"]
            if isinstance(uv, dict) and "north" in uv:
                (u, v), (su, sv) = uv["north"]["uv"], uv["north"]["uv_size"]
            elif isinstance(uv, list):
                u, v, su, sv = uv[0] + d, uv[1] + d, w, h
            else:
                continue
            if abs(su) >= 3 and abs(sv) >= 3:
                out.append((bone["name"], (min(u, u + su), min(v, v + sv), max(u, u + su), max(v, v + sv), su < 0, sv < 0)))
    return out


def crop_face(tex, r):
    x0, y0, x1, y1, fx, fy = r
    face = tex.crop((int(x0), int(y0), max(int(x0) + 1, int(round(x1))), max(int(y0) + 1, int(round(y1)))))
    if fx:
        face = face.transpose(Image.FLIP_LEFT_RIGHT)
    if fy:
        face = face.transpose(Image.FLIP_TOP_BOTTOM)
    return face


def variety(im):
    """顏色的豐富程度（有眼睛、嘴巴的臉分數高）：不同顏色數 × 亮度差。"""
    px = [p[:3] for p in im.get_flattened_data() if p[3] > 128]
    if len(px) < 6:
        return 0
    ls = [lum(p) for p in px]
    return len(set(px)) * (max(ls) - min(ls)) * min(1.0, len(px) / 16)


def pick_face(geo, tex, mob):
    """臉＝head（沒有就 body，再沒有就全部）骨骼裡顏色最豐富的正面。"""
    names = {b["name"] for b in geo["bones"]}
    groups = [[OVERRIDE[mob]]] if mob in OVERRIDE else [[n for n in names if "head" in n], ["body"], list(names)]
    for g in groups:
        cands = [(variety(crop_face(tex, r)), r) for _, r in north_faces(geo, g)]
        cands = [c for c in cands if c[0] > 0]
        if cands:
            return crop_face(tex, max(cands, key=lambda c: c[0])[1])
    return None


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def portrait(geo, tex):
    """正面（從 -z 看過去）每 1 個模型單位 = 1 像素的平面渲染，回傳 (整隻, 頭部裁切)；背景透明。
    用渲染而不是單一貼圖面，才會包含眼睛之類的小方塊和薄片。"""
    sys.path.insert(0, str(P / "tools/models"))
    import geo_preview3d as g3
    quads = g3.world_quads(geo)
    xs = [p[0] for q in quads for p in q[0]]
    ys = [p[1] for q in quads for p in q[1:2] for p in []] or [p[1] for q in quads for p in q[0]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    W, H = int(x1 - x0) + 2, int(y1 - y0) + 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    zb = {}
    tw, th = tex.size
    tp = tex.load()
    for pts, face, f in quads:
        if face != "north":          # 正面只看得到朝 -z 的面（旋轉過的小方塊也大多是 north）
            continue
        u0, v0 = f["uv"]
        su, sv = f["uv_size"]
        P2 = [(x1 - p[0], y1 - p[1], p[2]) for p in pts]   # 由觀察者看：+x 在左
        minx, maxx = min(p[0] for p in P2), max(p[0] for p in P2)
        miny, maxy = min(p[1] for p in P2), max(p[1] for p in P2)
        z = sum(p[2] for p in P2) / 4
        for py in range(int(miny), int(maxy + 0.999)):
            for px in range(int(minx), int(maxx + 0.999)):
                if (px, py) in zb and zb[(px, py)] <= z:
                    continue
                fu = (px + 0.5 - minx) / max(1e-6, maxx - minx)
                fv = (py + 0.5 - miny) / max(1e-6, maxy - miny)
                c = tp[min(tw - 1, max(0, int(u0 + su * fu))), min(th - 1, max(0, int(v0 + sv * fv)))]
                if c[3] < 128:
                    continue
                zb[(px, py)] = z
                if 0 <= px < W and 0 <= py < H:
                    img.putpixel((px, py), c[:3] + (255,))
    bb = img.getbbox()
    full = img.crop(bb) if bb else img
    head = None
    hb = [b for b in geo["bones"] if "head" in b["name"]]
    if hb:
        names = {b["name"] for b in hb}
        hq = [q for q, b in zip(quads, [None] * len(quads))]
        hp = []
        for b in geo["bones"]:
            if b["name"] in names:
                for c in b.get("cubes", []):
                    hp += [c["origin"][1], c["origin"][1] + c["size"][1]]
        if hp:
            top = int(y1 - max(hp)) - (bb[1] if bb else 0)
            bot = int(y1 - min(hp)) - (bb[1] if bb else 0) + 1
            head = full.crop((0, max(0, top), full.width, min(full.height, bot)))
            hb2 = head.getbbox()
            head = head.crop(hb2) if hb2 else None
    return full, head


def shell_color(full):
    """蛋殼底色：正面渲染裡最常見的顏色區間（只看這隻生物自己的像素）。"""
    from collections import Counter
    px = [p[:3] for p in full.get_flattened_data() if p[3] > 128]
    q = Counter((r // 24, g // 24, b // 24) for r, g, b in px).most_common(1)[0][0]
    group = [p for p in px if (p[0] // 24, p[1] // 24, p[2] // 24) == q]
    return tuple(sum(p[i] for p in group) // len(group) for i in range(3))


def make_egg(mob):
    doc = json.loads((GEO / f"{mob}.geo.json").read_text(encoding="utf-8"))
    geo = doc["minecraft:geometry"][0]
    tex = Image.open(A / f"textures/entity/{mob}.png").convert("RGBA")
    full, head = portrait(geo, tex)
    # 臉：整隻夠小（≤10x11）就放整隻；不然放頭部；都太大就縮到 10x10 內
    face = full if full.width <= 10 and full.height <= 11 else (head if head is not None else full)
    if face.width > 10 or face.height > 10:
        sc = min(10 / face.width, 10 / face.height)
        face = face.resize((max(1, round(face.width * sc)), max(1, round(face.height * sc))), Image.NEAREST)
    base = shell_color(full)
    m = egg_mask()
    egg = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            if m[y][x]:
                nx, ny = (x - 7.5) / 6, (y - 8) / 7
                k = 1.0 - 0.14 * (nx + ny) - 0.12 * max(0.0, nx * nx + ny * ny - 0.45)
                egg.putpixel((x, y), tuple(max(0, min(255, int(v * k))) for v in base) + (255,))
    fx0 = 8 - (face.width + 1) // 2
    fy0 = max(3, min(15 - face.height, 9 - face.height // 2 + 1))
    for y in range(face.height):
        for x in range(face.width):
            p = face.getpixel((x, y))
            X, Y = fx0 + x, fy0 + y
            if p[3] > 128 and 0 <= X < 16 and 0 <= Y < 16 and m[Y][X]:
                egg.putpixel((X, Y), p[:3] + (255,))
    px = egg.load()
    for y in range(16):
        for x in range(16):
            if m[y][x] and any(not (0 <= x + dx < 16 and 0 <= y + dy < 16 and m[y + dy][x + dx])
                               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c = px[x, y]
                px[x, y] = (int(c[0] * 0.55), int(c[1] * 0.55), int(c[2] * 0.55), 255)
    for x, y in ((5, 3), (4, 4), (4, 5)):
        c = px[x, y]
        px[x, y] = tuple(min(255, int(v * 1.3) + 20) for v in c[:3]) + (255,)
    return egg


def mobs():
    from_items = sorted(p.name[:-len("_spawn_egg.png")] for p in OUT.glob("*_spawn_egg.png"))
    return [m for m in from_items if (GEO / f"{m}.geo.json").exists() and (A / f"textures/entity/{m}.png").exists()]


def preview(eggs):
    sys.path.insert(0, str(P / "tools/models"))
    import geo_preview3d as g3
    font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
    cols, cw, ch = 6, 220, 130
    sheet = Image.new("RGB", (cols * cw, ((len(eggs) + cols - 1) // cols) * ch), (34, 33, 40))
    d = ImageDraw.Draw(sheet)
    for i, (mob, egg) in enumerate(eggs.items()):
        x, y = (i % cols) * cw, (i // cols) * ch
        bg = Image.new("RGBA", (96, 96), (70, 70, 80, 255))
        bg.alpha_composite(egg.resize((96, 96), Image.NEAREST))
        sheet.paste(bg.convert("RGB"), (x + 4, y + 4))
        try:
            doc = json.loads((GEO / f"{mob}.geo.json").read_text(encoding="utf-8"))
            r = g3.render(doc["minecraft:geometry"][0], Image.open(A / f"textures/entity/{mob}.png").convert("RGBA"), 2.5, 0, 5)
            r.thumbnail((110, 110))
            sheet.paste(r, (x + 104, y + 4))
        except Exception as e:   # 預覽失敗不影響蛋
            d.text((x + 104, y + 40), str(e)[:20], fill=(255, 120, 120), font=font)
        d.text((x + 4, y + 104), mob, fill=(230, 230, 230), font=font)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)


def main():
    eggs = {m: make_egg(m) for m in mobs()}
    preview(eggs)
    print(len(eggs), "eggs; preview", PREVIEW)
    if "--apply" in sys.argv:
        for m, egg in eggs.items():
            p = OUT / f"{m}_spawn_egg.png"
            if p.exists():
                BK.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, BK / p.name)
            art_guard.save(egg, p)
        print("applied; backups in", BK)


if __name__ == "__main__":
    main()
