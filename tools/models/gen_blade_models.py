"""Dungeons II 風格的粗短 3D 草葉：產生植被貼圖與 26.3 方塊模型，取代原版式的 X 形交叉片。
Usage (from the project root):
  python -I tools/models/gen_blade_models.py            產生到 build/sift_stage/ 並輸出預覽 build/previews/sift_batch_1.png
  python -I tools/models/gen_blade_models.py --apply    另外寫入正式資源（先備份到 .texture_backups/<stamp>_blades/）

每片葉子 = 兩段有厚度的盒子：下段從根部斜出，上段接在下段頂端再多彎一點，貼圖是根暗尖亮的灰白漸層（中間一條亮的葉脈），
顏色交給染色（FloorTint 依地板 / ModVegetation.TINTS 固定色）。發光草的黃色小方塊不染色。
"""
import sys, json, math, random, shutil, datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift"
STAGE = P / "build/sift_stage"
PREVIEW = P / "build/previews/sift_batch_1.png"
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BK = P / ".texture_backups" / f"{STAMP}_blades"
TEX_DIR = "textures/block/vegetation"
MODEL_DIR = "models/block/vegetation"


# ------------------------------------------------------------------ textures
def lerp(a, b, t):
    return a + (b - a) * t


def blade_texture(kind):
    """16x16 灰白葉片圖集。欄 0/4/8 是三種亮度的葉片（3 px 寬）：列 0-7 尖端（漸尖、透明角），列 8-15 根部。
    u12-16 v0-4：黃色發光點（不染色）；u12-16 v4-16：枝條（灌木用，3 px 寬）。"""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()
    styles = [-0.06, 0.0, 0.05]
    lo, hi = {"fern": (0.50, 0.95), "bush": (0.55, 0.95)}.get(kind, (0.56, 1.0))
    for s, off in enumerate(styles):
        u0 = s * 4
        for v in range(16):
            t = 1 - v / 15                         # 0 根 → 1 尖
            for du in range(3):
                b = lerp(lo, hi, t ** 0.8) + off
                b += 0.07 if du == 1 else (-0.05 if du == 0 else 0.0)   # 中脈亮、左緣暗
                if v < 2 and du != 1:
                    continue                       # 尖端只剩中間一欄
                if kind == "fern" and v < 14 and (v + du + s) % 3 == 0 and du != 1:
                    continue                       # 蕨：葉緣鋸齒
                g = max(0, min(255, round(b * 255)))
                px[u0 + du, v] = (g, g, g, 255)
    for v in range(4):                             # 發光點：亮黃，中心更亮
        for u in range(12, 16):
            edge = u in (12, 15) or v in (0, 3)
            px[u, v] = (255, 214, 92, 255) if edge else (255, 240, 150, 255)
    for v in range(4, 16):                         # 枝條：灰白，節點略暗
        for du in range(3):
            b = 0.78 + (0.08 if du == 1 else -0.04) - (0.10 if v % 5 == 0 else 0)
            g = round(b * 255)
            px[12 + du, v] = (g, g, g, 255)
    return im


# ------------------------------------------------------------------ geometry
def rx(p, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    x, y, z = p
    return (x, y * c - z * s, y * s + z * c)


def ry(p, a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    x, y, z = p
    return (x * c + z * s, y, -x * s + z * c)


def box(frm, to, rot, origin, faces, light=False):
    e = {"from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to],
         "rotation": {"x": round(rot[0], 2), "y": round(rot[1], 2), "z": 0, "origin": [round(v, 3) for v in origin]},
         "shade_direction_override": "up", "faces": faces}   # 26.3 原版植物的打光：每一面都當作朝上的面
    if light:
        e["light_emission"] = 15
    return e


def blade_faces(col, part, tint=True, thick=0.5):
    """col 0..2 選欄，part 'tip' / 'base'。前後面貼整欄，側面貼中脈那條細縫。"""
    u0 = col * 4
    v0, v1 = (0, 8) if part == "tip" else (8, 16)
    f = {}
    for d, uv in (("north", [u0 + 3, v0, u0, v1]), ("south", [u0, v0, u0 + 3, v1]),
                  ("east", [u0 + 1, v0, u0 + 1 + thick, v1]), ("west", [u0 + 1, v0, u0 + 1 + thick, v1])):
        f[d] = {"uv": uv, "texture": "#0"}
        if tint:
            f[d]["tintindex"] = 0
    return f


def blade(cx, cz, yaw, h1, h2, lean1, lean2, col, w=3.0, thick=0.5, y0=0.0, split_at=None):
    """回傳 (下段元素, 上段元素, 上段基點)。上段的基點 = 下段頂端經同樣旋轉後的位置，兩段在接點相連。"""
    lower = box((cx - w / 2, y0, cz - thick / 2), (cx + w / 2, y0 + h1, cz + thick / 2), (lean1, yaw, 0), (cx, y0, cz),
                blade_faces(col, "base", thick=thick))
    top = ry(rx((0, h1, 0), lean1), yaw)
    px_, py_, pz_ = cx + top[0], y0 + top[1], cz + top[2]
    if split_at is not None:
        py_ -= split_at
    w2 = w * 0.85
    upper = box((px_ - w2 / 2, py_, pz_ - thick / 2), (px_ + w2 / 2, py_ + h2, pz_ + thick / 2), (lean1 + lean2, yaw, 0),
                (px_, py_, pz_), blade_faces(col, "tip", thick=thick))
    return lower, upper


def speck(x, y, z, s=1.0):
    uv = [12.5, 0.5, 13.5, 1.5]
    faces = {d: {"uv": uv, "texture": "#0"} for d in ("north", "south", "east", "west", "up", "down")}
    return box((x - s / 2, y - s / 2, z - s / 2), (x + s / 2, y + s / 2, z + s / 2), (0, 45, 0), (x, y, z), faces, light=True)


def twig(x0, z0, y0, h, lean, yaw):
    """灌木枝條：1x1 截面的細盒子。"""
    uv = [12, 4, 13, 4 + min(12, h)]
    faces = {d: {"uv": uv, "texture": "#0", "tintindex": 0} for d in ("north", "south", "east", "west")}
    return box((x0 - 0.5, y0, z0 - 0.5), (x0 + 0.5, y0 + h, z0 + 0.5), (lean, yaw, 0), (x0, y0, z0), faces)


def spread_bases(rnd, n, margin=1.5):
    """根部位置鋪滿整格底部：k x k 網格（k = ceil(sqrt(n))）每格最多一株，加隨機偏移；回傳 [(x, z, yaw)]。
    yaw 讓葉子朝遠離方塊中心的方向斜（靠邊的往外倒），正中間那格方向隨機。"""
    k = math.ceil(math.sqrt(n))
    step = (16 - 2 * margin) / k
    cells = [(margin + step * (i + 0.5), margin + step * (j + 0.5)) for i in range(k) for j in range(k)]
    rnd.shuffle(cells)
    picks = cells[:n]
    jitter = step * 0.45
    out = []
    for cx, cz in picks:
        x = min(16 - margin, max(margin, cx + rnd.uniform(-jitter, jitter)))
        z = min(16 - margin, max(margin, cz + rnd.uniform(-jitter, jitter)))
        if abs(x - 8) < 1.5 and abs(z - 8) < 1.5:
            yaw = rnd.uniform(0, 360)
        else:
            yaw = math.degrees(math.atan2(z - 8, x - 8)) - 90 + rnd.uniform(-45, 45)
        out.append((x, z, yaw))
    return out


def tuft(seed, n, h1r, h2r, lean1r, lean2r, radius=None, w=2.5):
    """一叢短草：n 片兩段葉子，根部鋪滿整格（radius 已不使用，保留參數相容）。"""
    rnd = random.Random(seed)
    els = []
    for i, (cx, cz, yaw) in enumerate(spread_bases(rnd, n)):
        lo, up = blade(cx, cz, yaw, rnd.uniform(*h1r), rnd.uniform(*h2r), rnd.uniform(*lean1r), rnd.uniform(*lean2r),
                       i % 3, w=w)
        els += [lo, up]
    return els


def tall_tuft(seed, n):
    """兩格高：下段（根部，幾乎直立，頂端接近 16）放下半格模型，上段放上半格模型（y 往下移 16）。根部鋪滿整格。"""
    rnd = random.Random(seed)
    bottom, top = [], []
    for i, (cx, cz, yaw) in enumerate(spread_bases(rnd, n)):
        lean1 = rnd.uniform(5, 11)
        h1 = 15.5 / math.cos(math.radians(lean1)) - rnd.uniform(0, 2.5)
        lo, up = blade(cx, cz, yaw, h1, rnd.uniform(8, 13), lean1, rnd.uniform(12, 24), i % 3, w=2.5, split_at=16)
        bottom.append(lo)
        top.append(up)
    return bottom, top


def bush(seed):
    """淡紫枯灌木：幾根主枝斜出，每根再分一根短枝。"""
    rnd = random.Random(seed)
    els = []
    for i in range(6):
        yaw = 60 * i + rnd.uniform(-15, 15)
        lean = rnd.uniform(18, 32)
        h = rnd.uniform(8, 12)
        els.append(twig(8, 8, 0, h, lean, yaw))
        t = rnd.uniform(0.45, 0.7) * h
        p = ry(rx((0, t, 0), lean), yaw)
        els.append(twig(8 + p[0], 8 + p[2], p[1], rnd.uniform(3, 5), lean + rnd.choice((-35, 30)), yaw + rnd.uniform(-40, 40)))
    return els


def model(tex, elements, emissive=False):
    j = {"format_version": "26.3", "ambientocclusion": False,
         "textures": {"0": f"pysift:block/vegetation/{tex}", "particle": f"pysift:block/vegetation/{tex}"},
         "elements": elements}
    return j


def build():
    """回傳 {model_name: (json, tex_name)} 與 {tex_name: Image}。"""
    tex = {"ember_grass": blade_texture("grass"), "abyss_grass": blade_texture("grass"),
           "humus_grass": blade_texture("grass"), "humus_fern": blade_texture("fern"),
           "humus_bush": blade_texture("bush"), "tall_ember_grass": blade_texture("grass"),
           "tall_humus_grass": blade_texture("grass")}
    m = {}
    m["ember_grass"] = (model("ember_grass", tuft(11, 15, (5, 7.5), (4.5, 7), (8, 20), (10, 24), 5.8)), "ember_grass")
    glow = tuft(23, 13, (6, 8.5), (5.5, 8), (5, 14), (8, 18), 5.4)
    rnd = random.Random(5)
    for _ in range(3):
        a = rnd.uniform(0, math.tau)
        glow.append(speck(8 + math.cos(a) * rnd.uniform(2, 5.5), rnd.uniform(5, 11), 8 + math.sin(a) * rnd.uniform(2, 5.5)))
    m["abyss_grass"] = (model("abyss_grass", glow), "abyss_grass")
    m["humus_grass"] = (model("humus_grass", tuft(37, 15, (4.5, 6.5), (4, 6.5), (10, 22), (10, 26), 5.6)), "humus_grass")
    m["humus_fern"] = (model("humus_fern", tuft(41, 10, (4.5, 6), (5.5, 7.5), (22, 34), (14, 26), 3.4, w=4.2)), "humus_fern")
    m["humus_bush"] = (model("humus_bush", bush(53)), "humus_bush")
    b, t = tall_tuft(61, 13)
    m["tall_ember_grass_bottom"] = (model("tall_ember_grass", b), "tall_ember_grass")
    m["tall_ember_grass_top"] = (model("tall_ember_grass", t), "tall_ember_grass")
    b, t = tall_tuft(67, 13)
    m["tall_humus_grass_bottom"] = (model("tall_humus_grass", b), "tall_humus_grass")
    m["tall_humus_grass_top"] = (model("tall_humus_grass", t), "tall_humus_grass")
    # 寬葉蕨的貼圖欄是 3 px，但葉子 5 px 寬：把前後面的 u 範圍拉成 0..3 不變（貼圖會被拉寬），葉緣鋸齒照樣看得到
    return m, tex


# ------------------------------------------------------------------ preview renderer
FACE_CORNERS = {
    "north": ((1, 1, 0), (0, 1, 0), (0, 0, 0), (1, 0, 0)),
    "south": ((0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)),
    "east": ((1, 1, 1), (1, 1, 0), (1, 0, 0), (1, 0, 1)),
    "west": ((0, 1, 0), (0, 1, 1), (0, 0, 1), (0, 0, 0)),
    "up": ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)),
    "down": ((0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)),
}


def element_points(e):
    f, t = e["from"], e["to"]
    r = e.get("rotation", {})
    o = r.get("origin", [8, 8, 8])

    def tr(p):
        q = tuple(p[i] - o[i] for i in range(3))
        q = rx(q, r.get("x", 0))
        q = ry(q, r.get("y", 0))
        return tuple(q[i] + o[i] for i in range(3))
    return lambda c: tr(tuple(f[i] if c[i] == 0 else t[i] for i in range(3)))


class Canvas:
    def __init__(self, w, h, scale, yaw=35, pitch=28, cx=0, cy=0, bg=(56, 54, 66)):
        self.w, self.h, self.s, self.yaw, self.pitch = w, h, scale, yaw, pitch
        self.cx, self.cy = cx, cy
        self.img = Image.new("RGB", (w, h), bg)
        self.px = self.img.load()
        self.z = [[-1e9] * h for _ in range(w)]

    def proj(self, p):
        x, y, z = ry((p[0] - 8, p[1], p[2] - 8), self.yaw)
        x, y, z = rx((x, y, z), -self.pitch)
        return (self.w / 2 + (x + self.cx) * self.s, self.h * 0.78 - (y + self.cy) * self.s, -z)

    def tri(self, a, b, c, ta, tb, tc, tex, tint, light=1.0):
        xs = [a[0], b[0], c[0]]
        ys = [a[1], b[1], c[1]]
        x0, x1 = max(0, int(min(xs))), min(self.w - 1, int(max(xs)) + 1)
        y0, y1 = max(0, int(min(ys))), min(self.h - 1, int(max(ys)) + 1)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9:
            return
        tw, th = tex.size
        tp = tex.load()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                l1 = ((b[1] - c[1]) * (x + .5 - c[0]) + (c[0] - b[0]) * (y + .5 - c[1])) / d
                l2 = ((c[1] - a[1]) * (x + .5 - c[0]) + (a[0] - c[0]) * (y + .5 - c[1])) / d
                l3 = 1 - l1 - l2
                if l1 < 0 or l2 < 0 or l3 < 0:
                    continue
                z = l1 * a[2] + l2 * b[2] + l3 * c[2]
                if z <= self.z[x][y]:
                    continue
                u = l1 * ta[0] + l2 * tb[0] + l3 * tc[0]
                v = l1 * ta[1] + l2 * tb[1] + l3 * tc[1]
                tx = min(tw - 1, max(0, int(u / 16 * tw)))
                ty = min(th - 1, max(0, int(v / 16 * th)))
                r, g, bb, al = tp[tx, ty]
                if al < 128:
                    continue
                self.z[x][y] = z
                self.px[x, y] = (min(255, int(r * tint[0] / 255 * light)), min(255, int(g * tint[1] / 255 * light)),
                                 min(255, int(bb * tint[2] / 255 * light)))

    def element(self, e, texs, tint, offset=(0, 0, 0)):
        pts = element_points(e)
        for face, fd in e["faces"].items():
            tex = texs[fd["texture"]]
            u0, v0, u1, v1 = fd.get("uv", [0, 0, 16, 16])
            corners = [pts(c) for c in FACE_CORNERS[face]]
            corners = [self.proj((p[0] + offset[0], p[1] + offset[1], p[2] + offset[2])) for p in corners]
            uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            t = tint if "tintindex" in fd else (255, 255, 255)
            lt = 1.0 if face in ("north", "south", "up") else 0.85
            self.tri(corners[0], corners[1], corners[2], uvs[0], uvs[1], uvs[2], tex, t, lt)
            self.tri(corners[0], corners[2], corners[3], uvs[0], uvs[2], uvs[3], tex, t, lt)

    def ground(self, offset, color, size=16):
        x, y, z = offset
        tex = Image.new("RGBA", (16, 16), color + (255,))
        e = {"from": [0, -2, 0], "to": [size, 0, size], "faces": {"up": {"uv": [0, 0, 16, 16], "texture": "#g"}}}
        self.element(e, {"#g": tex}, (255, 255, 255), (x, y, z))


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load_old(name):
    """舊模型的預覽（元素 + 貼圖），找不到就回傳 None。"""
    f = A / MODEL_DIR / f"{name}.json"
    if not f.exists():
        return None
    j = json.loads(f.read_text(encoding="utf-8-sig"))
    ts = {}
    for k, ref in j.get("textures", {}).items():
        ns, path = ref.split(":")
        root = A if ns == "pysift" else P / "build/vegwork/vanilla/assets/minecraft"
        tp = root / "textures" / (path + ".png")
        if tp.exists():
            ts["#" + k] = Image.open(tp).convert("RGBA").crop((0, 0, 16, 16)) if ns != "pysift" else Image.open(tp).convert("RGBA")
    return j, ts


def preview(models, texs):
    # (標題, 模型(下[,上]), 染色, 地板色)：染色用 FloorTints / ModVegetation 的預設色
    rows = [
        ("ember_grass 赤紅地", ["ember_grass"], "#E6A394", "#B04150"),
        ("ember_grass 紫岩地", ["ember_grass"], "#C2A0E7", "#6E5A8C"),
        ("abyss_grass 青地（黃點發光）", ["abyss_grass"], "#7BE0D0", "#2E7F7A"),
        ("tall_ember_grass", ["tall_ember_grass_bottom", "tall_ember_grass_top"], "#E6A394", "#B04150"),
        ("humus_grass", ["humus_grass"], "#7CC79A", "#6E8C5A"),
        ("tall_humus_grass", ["tall_humus_grass_bottom", "tall_humus_grass_top"], "#7CC79A", "#6E8C5A"),
        ("humus_fern", ["humus_fern"], "#5DAE8C", "#6E8C5A"),
        ("humus_bush 淡紫枯枝", ["humus_bush"], "#C7A8E0", "#CFC2E2"),
    ]
    W, H = 300, 300
    sheet = Image.new("RGB", (W * 3 + 40, len(rows) * (H + 28) + 20), (34, 33, 40))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 14)
    for i, (title, names, tint, floor) in enumerate(rows):
        y = 10 + i * (H + 28)
        d.text((10, y), f"{title}   左：舊   中：新（單株）   右：新（3x3 一片）", fill=(235, 235, 235), font=font)
        tall = len(names) == 2
        sc = 9 if tall else 13
        # 舊
        c = Canvas(W, H, sc)
        c.ground((0, 0, 0), hexrgb(floor))
        for k, nm in enumerate(names):
            old = load_old(nm)
            if old:
                for e in old[0].get("elements", []):
                    if all(f.get("texture") in old[1] for f in e["faces"].values()):
                        c.element(e, old[1], hexrgb(tint), (0, 16 * k, 0))
        sheet.paste(c.img, (10, y + 20))
        # 新：單株
        c = Canvas(W, H, sc)
        c.ground((0, 0, 0), hexrgb(floor))
        for k, nm in enumerate(names):
            j, tn = models[nm]
            for e in j["elements"]:
                c.element(e, {"#0": texs[tn]}, hexrgb(tint), (0, 16 * k, 0))
        sheet.paste(c.img, (20 + W, y + 20))
        # 新：3x3 一片（各格用不同 y 旋轉）
        c = Canvas(W, H, 4.2 if tall else 5.2)
        for gx in range(3):
            for gz in range(3):
                off = ((gx - 1) * 16, 0, (gz - 1) * 16)
                c.ground(off, hexrgb(floor))
        for gx in range(3):
            for gz in range(3):
                off = ((gx - 1) * 16, 0, (gz - 1) * 16)
                yrot = ((gx * 3 + gz) * 90) % 360
                for k, nm in enumerate(names):
                    j, tn = models[nm]
                    for e in j["elements"]:
                        e2 = rotate_y_model(e, yrot)
                        c.element(e2, {"#0": texs[tn]}, hexrgb(tint), (off[0], off[1] + 16 * k, off[2]))
        sheet.paste(c.img, (30 + 2 * W, y + 20))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)
    # 貼圖放大圖
    tsheet = Image.new("RGBA", (len(texs) * 136 + 8, 160), (34, 33, 40, 255))
    td = ImageDraw.Draw(tsheet)
    for i, (n, im) in enumerate(texs.items()):
        bg = Image.new("RGBA", (128, 128), (90, 90, 100, 255))
        bg.alpha_composite(im.resize((128, 128), Image.NEAREST))
        tsheet.paste(bg, (8 + i * 136, 8))
        td.text((8 + i * 136, 140), n, fill=(230, 230, 230))
    tsheet.save(PREVIEW.with_name("sift_batch_1_textures.png"))


def rotate_y_model(e, deg):
    """模擬 blockstate 的 y 旋轉（繞方塊中心）：只用來畫預覽。"""
    if deg == 0:
        return e
    e = json.loads(json.dumps(e))
    r = e["rotation"]
    o = r["origin"]
    # 把 origin 繞 (8,8) 轉，元素本身跟著平移，再把 yaw 加上去
    dx, dz = o[0] - 8, o[2] - 8
    nx, ny, nz = ry((dx, 0, dz), -deg)
    shift = (8 + nx - o[0], 8 + nz - o[2])
    e["from"][0] += shift[0]; e["to"][0] += shift[0]
    e["from"][2] += shift[1]; e["to"][2] += shift[1]
    r["origin"] = [o[0] + shift[0], o[1], o[2] + shift[1]]
    r["y"] = r.get("y", 0) - deg
    return e


# ------------------------------------------------------------------ write
def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")


def backup(path):
    if path.exists():
        dst = BK / path.relative_to(P)
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)


def main():
    models, texs = build()
    for root in [STAGE] + ([A] if "--apply" in sys.argv else []):
        for n, im in texs.items():
            p = root / TEX_DIR / f"{n}.png"
            if root == A:
                backup(p)
            p.parent.mkdir(parents=True, exist_ok=True)
            im.save(p)
        for n, (j, _) in models.items():
            p = root / MODEL_DIR / f"{n}.json"
            if root == A:
                backup(p)
            write_json(p, j)
    preview(models, texs)
    for n, (j, _) in models.items():
        print(f"{n}: {len(j['elements'])} elements")
    print("preview:", PREVIEW)
    if "--apply" in sys.argv:
        print("applied; backups in", BK)


if __name__ == "__main__":
    main()
