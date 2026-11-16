"""把使用者畫的投擲物（art_requests/projectiles/drafts/）裝進模組。
Usage: python -I tools/items/install_projectile_art.py
  sift_dart.png        → textures/entity/projectiles/sift_dart.png（原版箭矢版面，直接用）
  hunter_javelin.png   → textures/entity/projectiles/hunter_javelin.png：取右邊的側面剪影（x20-22, y1-31，槍尖朝上），
                         轉成箭矢模型的版面、兩倍解析度（64x64）：正面一條槍尖在左、背面一條槍尖在右，尾端截面畫桿子切面。
  hurler_rock / monarch_feather / trapper_net → textures/item/（投擲物物品的圖示）
已存在的檔案先備份到 .texture_backups/。"""
import shutil, datetime
from pathlib import Path
from PIL import Image

P = Path(__file__).resolve().parents[2]
SRC = P / "art_requests/projectiles/drafts"
A = P / "src/main/resources/assets/pysift/textures"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_projectile_art")


def put(img, dst):
    if dst.exists():
        BK.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dst, BK / dst.name)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)


def javelin():
    src = Image.open(SRC / "hunter_javelin.png").convert("RGBA")
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for r in range(1, 32):              # 槍尖在 r=1
        for sx in range(20, 23):
            p = src.getpixel((sx, r))
            if p[3] == 0:
                continue
            c = r - 1                    # 0..30
            # 只有中間一欄的桿身補成 3 px 粗（側邊稍暗）；槍頭那幾排照原樣 3 px
            thin = sx == 21 and src.getpixel((20, r))[3] == 0 and src.getpixel((22, r))[3] == 0
            rows = [(3, 0.75), (4, 1.0), (5, 0.75)] if thin else [(3 + (sx - 20), 1.0)]
            for row, k in rows:
                q = (int(p[0] * k), int(p[1] * k), int(p[2] * k), p[3])
                out.putpixel((c, row), q)            # 正面（u 0-32）：槍尖在左
                out.putpixel((63 - c, row), q)       # 背面（u 32-64）：槍尖在右
    pole = src.getpixel((21, 20))
    for ox in (0, 10):                   # 尾端截面兩面（10x10）：中間 2x2 桿子切面
        for dx in (4, 5):
            for dy in (4, 5):
                out.putpixel((ox + dx, 10 + dy), pole)
    return out


def main():
    put(Image.open(SRC / "sift_dart.png").convert("RGBA"), A / "entity/projectiles/sift_dart.png")
    put(javelin(), A / "entity/projectiles/hunter_javelin.png")
    for n in ("hurler_rock", "monarch_feather", "trapper_net"):
        put(Image.open(SRC / f"{n}.png").convert("RGBA"), A / f"item/{n}.png")
    print("installed; backups (if any) in", BK)


if __name__ == "__main__":
    main()
