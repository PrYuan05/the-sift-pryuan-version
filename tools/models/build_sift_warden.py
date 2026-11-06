"""隙浮守衛（Sift Warden）：治癒後的監守者（MODDING_ROADMAP §4.7 第六幕），沿用原版監守者模型，只換貼圖。
Usage: python -I tools/models/build_sift_warden.py
從原版 26.3 的監守者貼圖重新上色（都是新檔，已存在的不覆蓋，要重畫請先刪掉）：
  textures/entity/sift_warden/sift_warden.png                    身體：深青黑的皮 → 赤紅幽匿色的毛（有毛流紋路），骨頭留著
  textures/entity/sift_warden/sift_warden_{bioluminescent_layer,heart,pulsating_spots_1,pulsating_spots_2}.png
                                                                  發光層：青色靈魂光 → 靈液的粉洋紅
  textures/item/sift_warden_spawn_egg.png                         原版監守者生怪蛋重新上色
預覽：build/previews/sift_warden.png
"""
import colorsys
import io
import sys
import zipfile
from pathlib import Path
from PIL import Image

P = Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift"
sys.path.insert(0, str(P / "tools"))
import art_guard

JAR = next((P / ".gradle/loom-cache/minecraftMaven/net/minecraft").glob("minecraft-clientOnly-*/26.3/*.jar"))
Z = zipfile.ZipFile(JAR)

# 毛：赤紅幽匿（red_sculk.png）的色階往暗處延伸，暗部偏紫、亮部偏暖
FUR = ["#2c0f26", "#421733", "#5c2048", "#742e63", "#8a3a5e", "#a84a66", "#bd566e", "#d4727c"]
BONE = ["#5e4a3c", "#8c7560", "#b9a283", "#ddd0ae"]           # 原本灰綠的骨頭：暖一點
GLOW = ["#1d0a17", "#4a1636", "#9a2f6b", "#e0569a", "#ff9cc8", "#ffe0ef"]   # 靈液的粉洋紅


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def lum(c):
    return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255


def pick(ramp, t):
    return hexrgb(ramp[max(0, min(len(ramp) - 1, int(t * len(ramp))))])


def vanilla(name):
    return Image.open(io.BytesIO(Z.read(f"assets/minecraft/textures/{name}.png"))).convert("RGBA")


def body(src):
    out = src.copy()
    px, o = src.load(), out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            L = lum((r, g, b))
            if L > 0.42 and 0.12 < h < 0.3:            # 骨頭（肋骨、牙齒、指節）
                o[x, y] = pick(BONE, (L - 0.42) / 0.45) + (a,)
                continue
            # 皮 → 毛：明度決定基準，再疊一個斜向的毛流紋路（每 3 列錯開，像歌者的毛）
            base = min(1.0, L / 0.32)
            stroke = ((x + (y // 3) * 2) % 4 == 0) * 0.16 - ((x + y // 2) % 5 == 0) * 0.1
            o[x, y] = pick(FUR, 0.2 + base * 0.6 + stroke) + (a,)
    return out


def glow(src):
    out = src.copy()
    px, o = src.load(), out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            if a:
                o[x, y] = pick(GLOW, lum((r, g, b)) / 0.75) + (a,)
    return out


def egg(src):
    """原版監守者蛋：暗色的皮換成毛色、青色的斑點換成粉洋紅。"""
    out = src.copy()
    px, o = src.load(), out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            L = lum((r, g, b))
            if s > 0.35 and 0.42 < h < 0.6 and L > 0.25:   # 青色光點
                o[x, y] = pick(GLOW, 0.4 + L * 0.7) + (a,)
            elif L > 0.45:
                o[x, y] = pick(BONE, (L - 0.45) / 0.45) + (a,)
            else:
                o[x, y] = pick(FUR, L / 0.4) + (a,)
    return out


def main():
    d = A / "textures/entity/sift_warden"
    d.mkdir(parents=True, exist_ok=True)
    outs = {"sift_warden": body(vanilla("entity/warden/warden"))}
    for layer in ("bioluminescent_layer", "heart", "pulsating_spots_1", "pulsating_spots_2"):
        outs[f"sift_warden_{layer}"] = glow(vanilla(f"entity/warden/warden_{layer}"))
    for name, img in outs.items():
        p = d / f"{name}.png"
        if not p.exists():
            art_guard.save(img, p)
    e = A / "textures/item/sift_warden_spawn_egg.png"
    if not e.exists():
        art_guard.save(egg(vanilla("item/warden_spawn_egg")), e)
    # preview: vanilla vs new body texture, and the egg
    v = vanilla("entity/warden/warden")
    sheet = Image.new("RGBA", (128 * 3 * 2 + 16 * 8 + 30, 128 * 3), (40, 40, 48, 255))
    sheet.alpha_composite(v.resize((384, 384), Image.NEAREST), (0, 0))
    sheet.alpha_composite(Image.open(d / "sift_warden.png").convert("RGBA").resize((384, 384), Image.NEAREST), (394, 0))
    sheet.alpha_composite(Image.open(e).convert("RGBA").resize((128, 128), Image.NEAREST), (788, 0))
    prev = P / "build/previews/sift_warden.png"
    prev.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(prev)
    print("ok; preview", prev)


if __name__ == "__main__":
    main()
