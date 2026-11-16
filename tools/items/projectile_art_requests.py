"""產生「投擲物重繪」需求：art_requests/projectiles/
  drafts/<名稱>.png   要畫的底稿（尺寸正確；灰色剪影只標出要畫的區域，不含任何原版像素）
  sheet.png          總覽：目前的原版外觀（放大）、底稿版面、丟它的生物的配色
Usage: python -I tools/items/projectile_art_requests.py
原版貼圖從 Loom 快取的 client jar 讀（只在本機產生對照圖，不會放進模組）。
"""
import zipfile
from collections import Counter
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift"
OUT = P / "art_requests/projectiles"
JAR = next((P / ".gradle/loom-cache/minecraftMaven/net/minecraft").glob("minecraft-clientOnly-*/26.3/*.jar"))

# 名稱, 中文, 丟它的生物, 目前的原版貼圖, 底稿尺寸, 版面
ITEMS = [
    ("sift_dart", "尖刺飛鏢", ["dartback", "prickle"], "textures/entity/projectiles/arrow.png", (32, 32), "arrow"),
    ("hunter_javelin", "獵人標槍", ["hunter"], "textures/entity/trident/trident.png", (32, 32), "trident"),
    ("hurler_rock", "投石", ["hurler"], "textures/block/cobblestone.png", (16, 16), "sprite"),
    ("monarch_feather", "君王羽刃", ["monarch"], "textures/item/feather.png", (16, 16), "sprite"),
    ("trapper_net", "陷阱師的網", ["trapper"], "textures/block/cobweb.png", (16, 16), "sprite"),
]


def vanilla(path):
    with zipfile.ZipFile(JAR) as z:
        return Image.open(BytesIO(z.read("assets/minecraft/" + path))).convert("RGBA")


def draft(kind, size, ref):
    """灰色剪影底稿：arrow / trident 照原版版面的不透明區域（換成灰階方塊，不保留原圖細節）；sprite 是空白透明。"""
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    if kind in ("arrow", "trident"):
        src = ref.load()
        px = im.load()
        for y in range(size[1]):
            for x in range(size[0]):
                if src[x, y][3] > 0:
                    px[x, y] = (150, 150, 160, 255) if (x + y) % 2 else (130, 130, 140, 255)
    return im


def palette(mob, n=6):
    im = Image.open(A / f"textures/entity/{mob}.png").convert("RGBA")
    c = Counter((r // 16 * 16, g // 16 * 16, b // 16 * 16) for r, g, b, a in im.get_flattened_data() if a > 128
                and not (r == g == b == 199))
    return [k for k, _ in c.most_common(n)]


LABELS = {
    "arrow": [((0, 0, 32, 5), "側面（箭身、箭頭、尾羽；上下兩面共用）"), ((0, 5, 10, 10), "尾端十字截面")],
    "trident": [((0, 0, 12, 32), "長桿與叉尖的展開（各面）"), ((19, 1, 24, 32), "側面剪影")],
}


def main():
    (OUT / "drafts").mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 16)
    small = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 12)
    rows = []
    for name, zh, mobs, ref_path, size, kind in ITEMS:
        ref = vanilla(ref_path)
        d = draft(kind, size, ref)
        d.save(OUT / "drafts" / f"{name}.png")
        S = 256 // size[0]
        row = Image.new("RGB", (900, 300), (32, 32, 38))
        dr = ImageDraw.Draw(row)
        dr.text((10, 6), f"{zh}  {name}.png   {size[0]}×{size[1]}   丟它的：{'、'.join(mobs)}", fill=(240, 240, 240), font=font)
        bg = Image.new("RGBA", (size[0] * S, size[1] * S), (70, 70, 80, 255))
        bg.alpha_composite(ref.resize((size[0] * S, size[1] * S), Image.NEAREST))
        row.paste(bg.convert("RGB"), (10, 34))
        dr.text((10, 34 + size[1] * S + 2), "目前（原版）", fill=(180, 180, 180), font=small)
        bg2 = Image.new("RGBA", (size[0] * S, size[1] * S), (50, 50, 60, 255))
        bg2.alpha_composite(d.resize((size[0] * S, size[1] * S), Image.NEAREST))
        g = ImageDraw.Draw(bg2)
        for i in range(0, size[0] + 1):
            g.line([(i * S, 0), (i * S, size[1] * S)], fill=(255, 255, 255, 30))
            g.line([(0, i * S), (size[0] * S, i * S)], fill=(255, 255, 255, 30))
        for (x0, y0, x1, y1), text in LABELS.get(kind, []):
            g.rectangle([x0 * S, y0 * S, x1 * S - 1, y1 * S - 1], outline=(255, 90, 90), width=2)
        row.paste(bg2.convert("RGB"), (290, 34))
        dr.text((290, 34 + size[1] * S + 2), "底稿（灰色＝要畫的區域）", fill=(180, 180, 180), font=small)
        y = 40
        for text in [t for _, t in LABELS.get(kind, [])] or ["整張 16×16 自由畫（物品圖示風格，背景透明）"]:
            dr.text((570, y), "• " + text, fill=(220, 220, 220), font=small)
            y += 18
        y += 8
        for mob in mobs:
            dr.text((570, y), f"{mob} 的配色：", fill=(220, 220, 220), font=small)
            y += 18
            for i, c in enumerate(palette(mob)):
                dr.rectangle([570 + i * 50, y, 615 + i * 50, y + 22], fill=c)
                dr.text((570 + i * 50, y + 24), "#%02X%02X%02X" % c, fill=(200, 200, 200), font=small)
            y += 46
        rows.append(row)
    sheet = Image.new("RGB", (900, sum(r.height for r in rows)), (20, 20, 24))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    sheet.save(OUT / "sheet.png")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
