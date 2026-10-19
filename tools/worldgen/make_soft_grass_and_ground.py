"""產生「校正版 v2」草地（地面）、短草、高草材質與額外方塊，供 crimson_strata_canyon 與 willow_grove 使用。
依據使用者回饋與截圖逐區比對校正：
  1. 材質與原版完全不同（自繪濃密像素畫，不沿用原版稀疏草葉與草皮噪點）：
     - 短草與高草：下半至中段（整叢核心）100% 密實無漏洞，由深玫紅內層葉（#D24E53~#E25E64）與柔粉紅前景葉（#F37685~#FD92A0）
       交錯疊合；上段（葉尖區）則參考截圖左右草叢，呈現高低錯落、向外微張的柔和分岔葉尖，既有「一叢密集無漏洞」的厚實本體，
       又有自然生動的草叢輪廓與內層深紅暗部對比。
  2. 草地頂面材質模仿影片透視地面的紋理：
     - 柔和粉紅底色之上，帶有幾道比較明顯、無縫連貫的深色草紋／地層差異道（#D44E54 ~ #E25E66），
       平鋪時自然連貫不割裂，在斜視與俯視下都能看到清楚而柔和的深色條帶差異。

Usage (from project root):
  python -I tools/worldgen/make_soft_grass_and_ground.py            產生貼圖與比對校正圖 build/previews/soft_grass_ground_preview.png
  python -I tools/worldgen/make_soft_grass_and_ground.py --apply    另外註冊額外方塊並更新模型／blockstate／語言檔（先備份）
"""
import sys, json, math, random, shutil, datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
PREVIEW = P / "build/previews/soft_grass_ground_preview.png"
STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BK = P / ".texture_backups" / f"{STAMP}_soft_grass_ground"


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lerp_rgb(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ==============================================================================
# 1. 截圖取樣校正色盤（直接對齊參考圖的 RGB 分佈）
# ==============================================================================
CANYON_GROUND_PAL = [
    hx("#D34D52"),  # 0: 明顯深色草紋道（深玫紅）
    hx("#E15D64"),  # 1: 深色差異邊緣過渡
    hx("#EC6C7A"),  # 2: 中深玫瑰粉
    hx("#F37886"),  # 3: 主色柔和粉紅
    hx("#F88392"),  # 4: 柔亮粉紅
    hx("#FD909E"),  # 5: 淺粉高光
]

GROVE_GROUND_PAL = [
    hx("#D65250"),  # 0: 明顯深珊瑚色道
    hx("#E36262"),  # 1: 深色過渡
    hx("#EE7174"),  # 2: 中深暖粉
    hx("#F47D82"),  # 3: 主色暖珊瑚粉
    hx("#F9898E"),  # 4: 柔亮蜜桃粉
    hx("#FD969B"),  # 5: 淺蜜桃高光
]

CLUMP_GRASS_PAL = [
    hx("#CF4B4E"),  # 0: 最深內層陰影葉（填補底層與葉間深處，不露洞）
    hx("#DE5A5E"),  # 1: 背層深玫紅草葉（形成參考圖草叢中明顯的深紅塊面）
    hx("#EA6872"),  # 2: 中層珊瑚紅草葉
    hx("#F37685"),  # 3: 前景主色粉紅草葉
    hx("#F88493"),  # 4: 前景柔亮粉紅葉面
    hx("#FD92A0"),  # 5: 葉尖與受光面亮粉白
]

SOFT_GRAY_SHADES = [0x9C, 0xAF, 0xC2, 0xD6, 0xE8, 0xFA]


# ==============================================================================
# 2. 地面頂面材質：柔和粉紅草地 + 幾道明顯且無縫連貫的深色差異條帶
# ==============================================================================
def value_noise_2d(seed, gx_cells, gy_cells):
    rnd = random.Random(seed)
    g = [[rnd.random() for _ in range(gx_cells)] for _ in range(gy_cells)]
    out = [[0.0] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            fx, fy = x * gx_cells / 16.0, y * gy_cells / 16.0
            x0, y0 = int(fx), int(fy)
            tx, ty = fx - x0, fy - y0
            tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
            a = g[y0 % gy_cells][x0 % gx_cells]
            b = g[y0 % gy_cells][(x0 + 1) % gx_cells]
            c = g[(y0 + 1) % gy_cells][x0 % gx_cells]
            d = g[(y0 + 1) % gy_cells][(x0 + 1) % gx_cells]
            out[y][x] = (a + (b - a) * tx) + ((c + (d - c) * tx) - (a + (b - a) * tx)) * ty
    return out


def make_streaked_grass_top(pal, seed=101):
    """生成自然柔和且帶有「幾道明顯深色差異」的草地頂面材質：
    - 四邊邊界收斂在柔和中粉紅基底區間（pal[2]~pal[4]），不會在 16x16 邊界形成重複的深色沙漏或網格線。
    - 每張貼圖內部由橫向流線場 + 3 道錯落修長的橫向／微斜向深玫紅草紋帶（長 7~13px、厚 1~2px）構成，
      外圍以次深色（pal[1]~pal[2]）自然柔化過渡，兼具俯視 4x4 自然無縫與低視角透視的鮮明深色差異道。
    """
    b_fine = value_noise_2d(607, 4, 8)
    v_flow = value_noise_2d(seed * 19 + 5, 2, 6)
    v_detail = value_noise_2d(seed * 43 + 17, 4, 8)

    # 先建立全變體無縫銜接的柔和粉紅草皮基底場（值域控制在 0.32 ~ 0.92，即 pal[2]~pal[5]）
    field = [[0.55] * 16 for _ in range(16)]
    for y in range(16):
        ey = min(1.0, min(y, 15 - y) / 2.5)
        for x in range(16):
            ex = min(1.0, min(x, 15 - x) / 2.5)
            w = ex * ey
            base_v = 0.36 + 0.50 * b_fine[y][x]
            var_v = 0.30 + 0.64 * (v_flow[y][x] * 0.68 + v_detail[y][x] * 0.32)
            field[y][x] = base_v * (1.0 - w) + var_v * w

    # 在每張貼圖中繪製 3~4 道錯落、修長且邊緣柔和漸變的深玫紅差異條帶（避免正對四邊交角產生沙漏網格）
    rnd = random.Random(seed * 37 + 11)
    y_Bands = [2, 6, 10, 13]
    for b_idx, y_base in enumerate(y_Bands):
        # 錯開每道深色條帶的水平起點與長度，其中 1 道跨左右邊界於固定 y=6 以維持跨格連貫感
        if b_idx == 1:
            x_start = rnd.randint(11, 14)
            length = rnd.randint(9, 12)
        else:
            x_start = rnd.randint(1, 5)
            length = rnd.randint(7, 11)
            if x_start + length > 15:
                length = 15 - x_start

        slope = rnd.choice([-1, 0, 1]) if b_idx != 1 else 0
        step_x = rnd.randint(3, max(3, length - 3))

        for i in range(length):
            xx = (x_start + i) % 16
            yy = (y_base + (slope if i >= step_x else 0)) % 16
            if b_idx != 1 and not (1 <= yy <= 14):
                yy = y_base
            # 條帶兩端漸柔，中段為明顯深色核心 (0.04 ~ 0.14 -> pal[0]~pal[1])
            t_end = min(i, length - 1 - i) / max(1.0, length * 0.28)
            strength = min(1.0, 0.45 + 0.55 * t_end)
            target_dark = 0.04 + (1.0 - strength) * 0.14
            field[yy][xx] = min(field[yy][xx], target_dark)

            # 上下 1px 形成柔和次深色暈染 (pal[1]~pal[2]) 與受光草尖 (pal[4]~pal[5])，消除生硬單像素線條感
            yy_dn = (yy + 1) % 16
            if 1 <= yy_dn <= 14:
                field[yy_dn][xx] = min(field[yy_dn][xx], 0.16 + (1.0 - strength) * 0.12)
            yy_up = (yy - 1) % 16
            if 1 <= yy_up <= 14 and field[yy_up][xx] > 0.25:
                field[yy_up][xx] = max(field[yy_up][xx], 0.78 + 0.14 * strength)

    im = Image.new("RGBA", (16, 16))
    px = im.load()
    for y in range(16):
        for x in range(16):
            v = field[y][x]
            if v <= 0.09:
                col = pal[0]
            elif v <= 0.20:
                col = lerp_rgb(pal[0], pal[1], (v - 0.09) / 0.11)
            elif v <= 0.36:
                col = lerp_rgb(pal[1], pal[2], (v - 0.20) / 0.16)
            elif v <= 0.56:
                col = lerp_rgb(pal[2], pal[3], (v - 0.36) / 0.20)
            elif v <= 0.76:
                col = lerp_rgb(pal[3], pal[4], (v - 0.56) / 0.20)
            else:
                col = lerp_rgb(pal[4], pal[5], min(1.0, (v - 0.76) / 0.18))
            px[x, y] = col + (255,)
    return im


def make_soft_grass_side_overlay(pal):
    """自繪濃密柔和的側面草皮垂緣，帶有深色草紋道延伸。"""
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()
    depths = [4, 5, 5, 4, 3, 4, 5, 6, 5, 4, 4, 5, 6, 5, 4, 3]
    for x in range(16):
        d = depths[x]
        for y in range(d):
            if y == 0:
                col = pal[4 if (x // 2) % 2 == 0 else 3]
            elif y == d - 1:
                col = pal[0 if x % 3 == 0 else 1]
            elif y == 1 and x in (2, 3, 7, 8, 12, 13):
                col = pal[0]
            else:
                col = pal[3 if (x + y) % 2 == 0 else 2]
            px[x, y] = col + (255,)
    return im


# ==============================================================================
# 3. 密集無漏洞、頂端自然分簇且層次分明的短草與高草材質
# ==============================================================================
def draw_tapered_blade(px, w, h, x_base, y_base, blade_h, w_base, lean_px, cols, shade_right=True):
    """繪製一片從根部寬實、中段微彎向外扇張、頂端漸收為 1px 尖端的草葉。
    cols = (col_bot, col_mid, col_top)
    """
    c_bot, c_mid, c_top = cols
    for i in range(blade_h):
        y = y_base - i
        if not (0 <= y < h):
            continue
        t = i / max(1, blade_h - 1)
        cx = x_base + lean_px * (t ** 1.35)
        if t < 0.48:
            c = lerp_rgb(c_bot, c_mid, t / 0.48)
        else:
            c = lerp_rgb(c_mid, c_top, (t - 0.48) / 0.52)

        if t > 0.78:
            cur_w = 1
        elif t > 0.48:
            cur_w = max(1, w_base - 1)
        else:
            cur_w = w_base

        ix0 = round(cx - (cur_w - 1) / 2.0)
        for dx in range(cur_w):
            xx = ix0 + dx
            if 0 <= xx < w:
                col_px = lerp_rgb(c, c_bot, 0.22) if (shade_right and cur_w >= 2 and dx == cur_w - 1 and t < 0.75) else c
                px[xx, y] = col_px + (255,)


def make_dense_clump_short_grass(pal, seed=7):
    """模仿參考圖中景「一叢密集、底座完全無空洞、深紅背葉與亮粉前葉交錯分明」的粉紅短草：
    - 底座與中段 100% 密實無漏洞。
    - 深玫紅葉（pal[0..1]）與柔亮粉紅葉（pal[3..5]）前後交錯，讓中下段也能清楚看到深紅葉脈與葉片層次。
    """
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = im.load()

    # 依前後景交錯繪製，讓深玫紅葉片不會被前景亮粉全部蓋住，呈現參考圖鮮明的深淺葉片對比
    blades = [
        # 背層深紅底襯葉
        (2.5,  10, 3, -2.2, (0, 0, 1)),
        (5.2,  14, 3, -1.3, (0, 1, 2)),
        (8.0,  13, 3,  0.0, (0, 0, 1)),
        (10.8, 14, 3,  1.2, (0, 1, 2)),
        (13.2, 10, 3,  2.2, (0, 0, 1)),
        # 中層亮粉與珊瑚粉主葉
        (1.8,   9, 2, -2.0, (1, 3, 4)),
        (4.0,  13, 2, -1.6, (2, 3, 5)),
        (6.5,  15, 2, -0.6, (2, 4, 5)),
        (9.2,  14, 2,  0.5, (2, 3, 5)),
        (11.6, 15, 2,  1.5, (2, 4, 5)),
        (13.8, 10, 2,  2.3, (1, 3, 4)),
        # 前中層深玫紅夾葉（在亮粉葉之間拉出明顯深紅立體葉影，如同參考圖草叢）
        (5.3,  12, 2, -1.0, (0, 1, 2)),
        (7.8,  13, 2, -0.1, (0, 1, 2)),
        (10.4, 12, 2,  1.0, (0, 1, 1)),
        # 最前景高光細葉尖
        (3.8,  11, 1, -1.5, (3, 4, 5)),
        (6.6,  15, 1, -0.5, (3, 5, 5)),
        (9.0,  13, 1,  0.4, (3, 4, 5)),
        (11.5, 14, 1,  1.4, (3, 5, 5)),
    ]
    for xb, bh, wb, ln, idx_tup in blades:
        draw_tapered_blade(px, 16, 16, xb, 15, bh, wb, ln, tuple(pal[i] for i in idx_tup))

    # 確保底座核心（x=1..14, y=10..15）100% 密實無任何破洞
    for y in range(10, 16):
        x0 = 1 if y >= 12 else 2
        x1 = 14 if y >= 12 else 13
        for x in range(x0, x1 + 1):
            if px[x, y][3] == 0:
                px[x, y] = pal[0 if (x + y) % 2 == 0 else 1] + (255,)

    return im


def make_dense_clump_tall_grass(pal, seed=13):
    """模仿參考圖左右兩側「高大簇擁、密實無空洞、深玫紅與柔亮粉紅交錯扇張」的高草：
    - 下半格與中段 100% 密實無漏洞。
    - 深玫紅葉束（pal[0..1]）與柔亮粉葉束（pal[3..5]）從根部到葉尖交錯穿插，
      重現參考圖特寫（2B）中深紅斜葉與亮粉受光葉交織的豐富塊面感。
    """
    full = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    px = full.load()

    # 1. 底襯寬葉層（先鋪滿密實基底）
    base_layer = [
        (2.5,  22, 3, -2.4, (0, 0, 1)),
        (5.0,  28, 3, -1.6, (0, 1, 2)),
        (7.5,  30, 3, -0.3, (0, 1, 2)),
        (10.0, 29, 3,  0.9, (0, 1, 2)),
        (12.8, 23, 3,  2.3, (0, 0, 1)),
    ]
    for xb, bh, wb, ln, idx_tup in base_layer:
        draw_tapered_blade(px, 16, 32, xb, 31, bh, wb, ln, tuple(pal[i] for i in idx_tup))

    # 2. 主體亮粉與深紅交錯層（讓深紅葉從根部一路延伸到中上段，不被亮粉完全覆蓋）
    interleaved = [
        (1.8,  19, 2, -2.2, (1, 3, 4)),  # 左側柔粉短護葉
        (3.6,  29, 2, -2.0, (2, 4, 5)),  # 左側高挑亮粉葉
        (5.0,  26, 2, -1.3, (0, 1, 1)),  # 左中深玫紅斜出葉（對齊參考圖左草叢明顯的深紅斜葉）
        (6.5,  31, 2, -0.6, (2, 4, 5)),  # 中左最高亮粉主葉
        (8.0,  27, 2,  0.1, (0, 1, 2)),  # 中央深玫紅夾葉（提供中段與下段深色立體塊面）
        (9.5,  30, 2,  0.8, (2, 4, 5)),  # 中右高挑亮粉主葉
        (11.0, 28, 2,  1.5, (0, 1, 2)),  # 右側深玫紅高分枝
        (12.4, 26, 2,  2.1, (2, 3, 5)),  # 右側亮粉外展葉
        (14.0, 19, 2,  2.5, (1, 2, 4)),  # 右側柔粉短護葉
    ]
    for xb, bh, wb, ln, idx_tup in interleaved:
        draw_tapered_blade(px, 16, 32, xb, 31, bh, wb, ln, tuple(pal[i] for i in idx_tup))

    # 3. 中上段向外分岔的羽狀側葉（模仿參考圖 2B 向外斜張的葉叢輪廓，深淺交錯）
    side_fronds = [
        (3.5,  18, 11, 2, -2.6, (1, 3, 5)),
        (5.5,  15, 11, 2, -1.9, (0, 1, 2)),
        (7.8,  14, 12, 2, -0.4, (2, 4, 5)),
        (10.2, 15, 11, 2,  1.6, (0, 1, 2)),
        (12.2, 18, 11, 2,  2.6, (2, 4, 5)),
    ]
    for xs, ys, bh, wb, ln, idx_tup in side_fronds:
        draw_tapered_blade(px, 16, 32, xs, ys, bh, wb, ln, tuple(pal[i] for i in idx_tup))

    # 4. 保底密實化：下半格（y=16..31）與上半格下段（y=11..15）主體內完全無透明破洞
    for y in range(11, 32):
        margin = 1 if y >= 16 else 2
        for x in range(margin, 16 - margin):
            if px[x, y][3] == 0:
                t = (31 - y) / 31.0
                p_idx = 0 if t < 0.40 else (1 if t < 0.72 else 2)
                px[x, y] = pal[p_idx] + (255,)

    return full.crop((0, 16, 16, 32)), full.crop((0, 0, 16, 16))


# ==============================================================================
# 4. 模擬場景與逐區比對校正圖生成
# ==============================================================================
def render_calibrated_scene(ground_tops, short_im, tall_bot_im, tall_top_im, sky_rgb=(98, 214, 198)):
    W, H = 434, 244
    canvas = Image.new("RGBA", (W, H), sky_rgb + (255,))
    draw = ImageDraw.Draw(canvas)

    horizon = 168
    for y in range(120, horizon):
        t = (y - 120) / float(horizon - 120)
        c = lerp_rgb(sky_rgb, (150, 228, 206), t * 0.55)
        draw.line([(0, y), (W, y)], fill=c + (255,))

    rnd_g = random.Random(19)
    mega_ground = Image.new("RGBA", (128, 128))
    for gy in range(8):
        for gx in range(8):
            tile = rnd_g.choice(ground_tops)
            mega_ground.paste(tile, (gx * 16, gy * 16))
    mg_px = mega_ground.load()

    for sy in range(horizon, H):
        dy = sy - horizon + 1.5
        depth = 155.0 / (dy + 4.0)
        for sx in range(W):
            wx = (sx - W / 2.0) * depth * 0.048
            wz = depth * 14.5
            tx = int(math.floor(wx)) % 128
            ty = int(math.floor(wz)) % 128
            r, g, b, _ = mg_px[tx, ty]
            canvas.putpixel((sx, sy), (r, g, b, 255))

    tall_full = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    tall_full.paste(tall_top_im, (0, 0))
    tall_full.paste(tall_bot_im, (0, 16))

    placements = [
        (82,  horizon + 12, 2.3, False, False),
        (106, horizon + 14, 2.5, False, True),
        (132, horizon + 15, 2.4, False, False),
        (156, horizon + 13, 2.2, False, True),
        (215, horizon + 12, 2.2, True,  False),
        (242, horizon + 14, 2.5, False, True),
        (265, horizon + 16, 2.8, True,  True),
        (285, horizon + 34, 3.6, True,  False),
        (318, horizon + 42, 4.2, True,  True),
        (352, horizon + 46, 4.5, True,  False),
        (388, horizon + 44, 4.1, True,  True),
        (302, horizon + 55, 4.0, False, False),
        (340, horizon + 62, 4.4, False, True),
        (378, horizon + 66, 4.6, False, False),
        (408, horizon + 60, 4.2, True,  False),
        (-8,  horizon + 68, 5.8, True,  False),
        (28,  horizon + 72, 5.4, False, True),
    ]
    for px_x, py_y, sc, is_tall, flip in sorted(placements, key=lambda item: item[1]):
        sp = tall_full if is_tall else short_im
        if flip:
            sp = sp.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        sw = max(1, round(sp.width * sc))
        sh = max(1, round(sp.height * sc))
        scaled = sp.resize((sw, sh), Image.Resampling.NEAREST)
        canvas.alpha_composite(scaled, (int(px_x), int(py_y - sh)))
        sp_back = sp.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        scaled_back = sp_back.resize((max(1, round(sw * 0.92)), sh), Image.Resampling.NEAREST)
        canvas.alpha_composite(scaled_back, (int(px_x + sc * 2.2), int(py_y - sh + sc * 0.6)))

    return canvas.convert("RGB")


def tile_grid(ims, n=4, scale=4, seed=9):
    rnd = random.Random(seed)
    cell = 16 * scale
    out = Image.new("RGB", (cell * n, cell * n))
    for gy in range(n):
        for gx in range(n):
            im = rnd.choice(ims)
            out.paste(im.resize((cell, cell), Image.Resampling.NEAREST).convert("RGB"), (gx * cell, gy * cell))
    return out


def build_all():
    canyon_tops = [make_streaked_grass_top(CANYON_GROUND_PAL, seed=100 + i * 29) for i in range(4)]
    grove_tops = [make_streaked_grass_top(GROVE_GROUND_PAL, seed=200 + i * 31) for i in range(2)]
    side_overlay = make_soft_grass_side_overlay(CANYON_GROUND_PAL)

    soft_short = make_dense_clump_short_grass(CLUMP_GRASS_PAL, seed=7)
    soft_tall_bot, soft_tall_top = make_dense_clump_tall_grass(CLUMP_GRASS_PAL, seed=13)

    gray_pal = [(v, v, v) for v in SOFT_GRAY_SHADES]
    soft_short_gray = make_dense_clump_short_grass(gray_pal, seed=7)
    soft_tall_bot_gray, soft_tall_top_gray = make_dense_clump_tall_grass(gray_pal, seed=13)

    OUT_GROUND = A / "textures/block/sift_ground"
    OUT_VEG = A / "textures/block/vegetation"
    OUT_GROUND.mkdir(parents=True, exist_ok=True)
    OUT_VEG.mkdir(parents=True, exist_ok=True)

    for i, k in enumerate("abcd"):
        canyon_tops[i].save(OUT_GROUND / f"canyon_top_{k}.png")
    grove_tops[0].save(OUT_GROUND / "grove_top.png")
    grove_tops[1].save(OUT_GROUND / "grove_top_b.png")
    side_overlay.save(OUT_GROUND / "crimson_grass_side_overlay.png")

    soft_short.save(OUT_VEG / "crimson_short_grass.png")
    soft_tall_bot.save(OUT_VEG / "crimson_tall_grass_bottom.png")
    soft_tall_top.save(OUT_VEG / "crimson_tall_grass_top.png")
    soft_short_gray.save(OUT_VEG / "soft_short_grass_gray.png")
    soft_tall_bot_gray.save(OUT_VEG / "soft_tall_grass_bottom_gray.png")
    soft_tall_top_gray.save(OUT_VEG / "soft_tall_grass_top_gray.png")

    return {
        "canyon_tops": canyon_tops,
        "grove_tops": grove_tops,
        "side_overlay": side_overlay,
        "soft_short": soft_short,
        "soft_tall_bot": soft_tall_bot,
        "soft_tall_top": soft_tall_top,
    }


def make_preview_sheet(assets):
    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 16)
        font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 14)
    except OSError:
        font_title = font = None

    W, H = 980, 1020
    sheet = Image.new("RGB", (W, H), (28, 28, 34))
    d = ImageDraw.Draw(sheet)

    d.text((16, 12), "The Sift 草地、短草、高草材質 — 逐區比對校正預覽（自繪密集草叢 + 明顯深色差異道頂面）", fill=(245, 240, 242), font=font_title)

    ref_path = Path(r"C:/Users/hoeyl/.gemini/antigravity/brain/4be9e1f3-c423-4bb6-969d-18bab289efd8/.user_uploaded/media_1792311950379_bab30983.png")
    ref_im = Image.open(ref_path).convert("RGB") if ref_path.exists() else None
    scene_im = render_calibrated_scene(assets["canyon_tops"], assets["soft_short"], assets["soft_tall_bot"], assets["soft_tall_top"])

    # Row 1: 1:1 全景對照
    if ref_im:
        d.text((16, 42), "1A. 原始參考圖（434x244）", fill=(220, 220, 225), font=font)
        sheet.paste(ref_im, (16, 66))
    d.text((480, 42), "1B. 校正後新材質模擬場景（434x244 同視角比對）", fill=(250, 200, 210), font=font)
    sheet.paste(scene_im, (480, 66))

    # Row 2: 局部放大 1:1 裁切比對
    y_crop = 324
    d.text((16, y_crop), "2. 局部特寫比對校正（左：參考圖裁切放大  vs  右：新材質模擬裁切放大）", fill=(245, 240, 242), font=font_title)
    if ref_im:
        ref_g_crop = ref_im.crop((175, 196, 355, 244)).resize((220, 96), Image.Resampling.NEAREST)
        new_g_crop = scene_im.crop((175, 196, 355, 244)).resize((220, 96), Image.Resampling.NEAREST)
        d.text((16, y_crop + 26), "【地面】參考圖（幾道明顯深色差異）", fill=(210, 210, 215), font=font)
        sheet.paste(ref_g_crop, (16, y_crop + 48))
        d.text((250, y_crop + 26), "【地面】校正後（柔和底 + 深色差異道）", fill=(250, 200, 210), font=font)
        sheet.paste(new_g_crop, (250, y_crop + 48))

        ref_c_crop = ref_im.crop((0, 48, 92, 236)).resize((180, 120), Image.Resampling.NEAREST)
        new_c_crop = scene_im.crop((0, 48, 92, 236)).resize((180, 120), Image.Resampling.NEAREST)
        d.text((510, y_crop + 26), "【高草叢】參考圖（密實分岔）", fill=(210, 210, 215), font=font)
        sheet.paste(ref_c_crop, (510, y_crop + 48))
        d.text((740, y_crop + 26), "【高草叢】校正後（密實分岔）", fill=(250, 200, 210), font=font)
        sheet.paste(new_c_crop, (740, y_crop + 48))

    # Row 3: 俯視 4x4 平鋪與單張 16x16 放大
    y3 = 508
    d.text((16, y3), "3. 赤紅峽谷頂面 (canyon_top_a..d) 4x4 平鋪 + 單張", fill=(250, 200, 210), font=font)
    sheet.paste(tile_grid(assets["canyon_tops"], n=4, scale=4), (16, y3 + 24))
    for i, im in enumerate(assets["canyon_tops"]):
        x_off = 290 + (i % 2) * 84
        y_off = y3 + 24 + (i // 2) * 96
        sheet.paste(im.resize((72, 72), Image.Resampling.NEAREST).convert("RGB"), (x_off, y_off))
        d.text((x_off, y_off + 74), f"canyon_{'abcd'[i]}", fill=(190, 190, 200), font=font)

    d.text((500, y3), "4. 柳絮林地頂面 (grove_top, grove_top_b) 4x4 平鋪 + 單張", fill=(250, 210, 200), font=font)
    sheet.paste(tile_grid(assets["grove_tops"], n=4, scale=4), (500, y3 + 24))
    for i, im in enumerate(assets["grove_tops"]):
        x_off = 774 + i * 88
        y_off = y3 + 24
        sheet.paste(im.resize((72, 72), Image.Resampling.NEAREST).convert("RGB"), (x_off, y_off))
        d.text((x_off, y_off + 74), f"grove_{'ab'[i]}", fill=(190, 190, 200), font=font)

    # Row 4: 自繪密集短草與高草 16x16 / 16x32 貼圖檢視
    y4 = 795
    d.text((16, y4), "5. 自繪密集短草與高草貼圖（與原版不同：底座與中段密實無漏洞、上段柔和分岔葉尖、深紅背葉立體層次）", fill=(245, 240, 242), font=font_title)

    soft_tall = Image.new("RGBA", (16, 32), (0, 0, 0, 0))
    soft_tall.paste(assets["soft_tall_top"], (0, 0))
    soft_tall.paste(assets["soft_tall_bot"], (0, 16))

    def paste_box(im, x, y, scale=6, bg_col=None):
        w, h = im.width * scale, im.height * scale
        box = Image.new("RGBA", (w, h), (44, 44, 52, 255) if bg_col is None else bg_col + (255,))
        if bg_col is None:
            bpx = box.load()
            for py in range(h):
                for px_i in range(w):
                    if ((px_i // scale) + (py // scale)) % 2 == 0:
                        bpx[px_i, py] = (56, 56, 66, 255)
        box.alpha_composite(im.resize((w, h), Image.Resampling.NEAREST))
        sheet.paste(box.convert("RGB"), (x, y))

    clump_short_2x = Image.new("RGBA", (20, 16), (0, 0, 0, 0))
    clump_short_2x.alpha_composite(assets["soft_short"].transpose(Image.Transpose.FLIP_LEFT_RIGHT), (3, 0))
    clump_short_2x.alpha_composite(assets["soft_short"], (0, 0))

    paste_box(assets["soft_short"], 16, y4 + 30, scale=6, bg_col=None)
    d.text((16, y4 + 132), "新密集短草 (單片)", fill=(220, 220, 225), font=font)

    paste_box(assets["soft_short"], 150, y4 + 30, scale=6, bg_col=(98, 214, 198))
    d.text((150, y4 + 132), "短草 (薄荷青天空下)", fill=(220, 220, 225), font=font)

    paste_box(clump_short_2x, 290, y4 + 30, scale=6, bg_col=(98, 214, 198))
    d.text((290, y4 + 132), "短草 (遊戲內雙層交疊)", fill=(250, 200, 210), font=font)

    paste_box(assets["soft_short"], 450, y4 + 30, scale=6, bg_col=CANYON_GROUND_PAL[3])
    d.text((450, y4 + 132), "短草 (在草地底色上)", fill=(220, 220, 225), font=font)

    paste_box(soft_tall, 600, y4 + 26, scale=5, bg_col=None)
    d.text((600, y4 + 190), "新密集高草(透明底)", fill=(220, 220, 225), font=font)

    paste_box(soft_tall, 725, y4 + 26, scale=5, bg_col=(98, 214, 198))
    d.text((725, y4 + 190), "高草(薄荷青天空下)", fill=(250, 200, 210), font=font)

    clump_tall_2x = Image.new("RGBA", (20, 32), (0, 0, 0, 0))
    clump_tall_2x.alpha_composite(soft_tall.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (3, 0))
    clump_tall_2x.alpha_composite(soft_tall, (0, 0))
    paste_box(clump_tall_2x, 845, y4 + 26, scale=5, bg_col=(98, 214, 198))
    d.text((845, y4 + 190), "高草(遊戲內交疊)", fill=(250, 200, 210), font=font)

    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)
    print("Saved calibrated preview to", PREVIEW.relative_to(P))


def backup(p):
    if p.exists():
        dst = BK / p.relative_to(P)
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)


def wj(p, obj, indent=2):
    backup(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def apply_extra_blocks():
    java_path = P / "src/main/java/pryuan05/pysift/block/ModVegetation.java"
    java_text = java_path.read_text(encoding="utf-8")
    if "CRIMSON_SHORT_GRASS" not in java_text:
        backup(java_path)
        anchor = "    public static final Block CORAL_LEAF_CARPET = register(\"coral_leaf_carpet\", p -> new FlowerBedBlock(p, 3), Blocks.PINK_PETALS, false);"
        addition = (
            anchor + "\n\n"
            "    // ===== 影片風格柔和草地與短草／高草（額外方塊） =====\n"
            "    public static final Block CRIMSON_SHORT_GRASS = register(\"crimson_short_grass\", SiftGrassBlock::new, Blocks.SHORT_GRASS, false);\n"
            "    public static final Block CRIMSON_TALL_GRASS = register(\"crimson_tall_grass\", DoublePlantBlock::new, Blocks.TALL_GRASS, true);"
        )
        assert anchor in java_text, "Could not find CORAL_LEAF_CARPET anchor in ModVegetation.java"
        java_path.write_text(java_text.replace(anchor, addition, 1), encoding="utf-8")

    wj(A / "models/block/vegetation/crimson_short_grass.json", {
        "parent": "pysift:block/vegetation/dense_rift_foliage_template",
        "textures": {"cross": "pysift:block/vegetation/crimson_short_grass"}
    }, indent="\t")
    wj(A / "models/block/vegetation/crimson_tall_grass_bottom.json", {
        "parent": "pysift:block/vegetation/dense_rift_foliage_template",
        "textures": {"cross": "pysift:block/vegetation/crimson_tall_grass_bottom"}
    }, indent="\t")
    wj(A / "models/block/vegetation/crimson_tall_grass_top.json", {
        "parent": "pysift:block/vegetation/dense_rift_foliage_template",
        "textures": {"cross": "pysift:block/vegetation/crimson_tall_grass_top"}
    }, indent="\t")

    wj(A / "blockstates/crimson_short_grass.json", {
        "variants": {"": [{"model": "pysift:block/vegetation/crimson_short_grass", **({"y": y} if y else {})} for y in (0, 90, 180, 270)]}
    })
    wj(A / "blockstates/crimson_tall_grass.json", {
        "variants": {
            "half=lower": {"model": "pysift:block/vegetation/crimson_tall_grass_bottom"},
            "half=upper": {"model": "pysift:block/vegetation/crimson_tall_grass_top"}
        }
    })

    for name, icon_tex in (("crimson_short_grass", "crimson_short_grass"), ("crimson_tall_grass", "crimson_tall_grass_top")):
        wj(A / f"items/{name}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{name}"}})
        wj(A / f"models/item/{name}.json", {
            "parent": "minecraft:item/generated",
            "textures": {"layer0": f"pysift:block/vegetation/{icon_tex}"}
        }, indent="\t")

    shears = {"type": "minecraft:any_of", "terms": ["minecraft:tool/can_shear", "minecraft:tool/can_silk_touch"]}
    short_loot = {
        "type": "minecraft:block",
        "pools": [{"condition": shears, "entries": [{"type": "minecraft:item", "name": "pysift:crimson_short_grass"}], "rolls": 1}],
        "random_sequence": "pysift:blocks/crimson_short_grass"
    }
    tall_loot = {
        "type": "minecraft:block",
        "pools": [{
            "condition": {"type": "minecraft:all_of", "terms": [
                {"type": "minecraft:match_block", "blocks": "pysift:crimson_tall_grass", "state": {"half": "lower"}},
                shears
            ]},
            "entries": [{"type": "minecraft:item", "name": "pysift:crimson_tall_grass"}],
            "rolls": 1
        }],
        "random_sequence": "pysift:blocks/crimson_tall_grass"
    }
    for folder in ("loot_table", "loot_tables"):
        wj(D / f"pysift/{folder}/blocks/crimson_short_grass.json", short_loot)
        wj(D / f"pysift/{folder}/blocks/crimson_tall_grass.json", tall_loot)

    tag_p = D / "minecraft/tags/block/replaceable_by_trees.json"
    tag_j = json.loads(tag_p.read_text(encoding="utf-8"))
    for bid in ("pysift:crimson_short_grass", "pysift:crimson_tall_grass"):
        if bid not in tag_j["values"]:
            tag_j["values"].append(bid)
    wj(tag_p, tag_j)

    names = {
        "crimson_short_grass": ("柔和赤紅短草", "Soft Crimson Short Grass"),
        "crimson_tall_grass": ("柔和赤紅高草", "Soft Crimson Tall Grass"),
    }
    for lang, idx in (("zh_tw", 0), ("en_us", 1)):
        lp = A / f"lang/{lang}.json"
        lj_data = json.loads(lp.read_text(encoding="utf-8"))
        for k, v in names.items():
            lj_data[f"block.pysift.{k}"] = lj_data[f"item.pysift.{k}"] = v[idx]
        wj(lp, lj_data)

    print("Registered extra blocks: crimson_short_grass, crimson_tall_grass")


def main():
    assets = build_all()
    make_preview_sheet(assets)
    if "--apply" in sys.argv:
        apply_extra_blocks()


if __name__ == "__main__":
    main()
