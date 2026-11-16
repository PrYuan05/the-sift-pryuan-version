"""哀悼者（Mourner）：屍化的歌者（MODDING_ROADMAP §4.7）。沿用歌者的模型與動畫，換一張「毛脫落、深藍腐色、胸口留一點靈魂光」的貼圖。
Usage: python -I tools/models/build_mourner.py
寫入（都是新檔，已存在的貼圖不會覆蓋，要重畫請先刪掉）：
  geckolib/models/entity/mourner.geo.json        歌者模型照抄
  geckolib/animations/entity/mourner.animation.json  歌者的 idle／walk／sing／death：放慢 1.5 倍、頭垂低
  textures/entity/mourner.png                    歌者貼圖重新上色
  textures/item/mourner_spawn_egg.png            生怪蛋（make_spawn_eggs.make_egg）
預覽：build/previews/mourner.png（左歌者、右哀悼者，正面 3D）
"""
import json, math, sys, colorsys
from pathlib import Path
from PIL import Image

P = Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift"
sys.path.insert(0, str(P / "tools"))
sys.path.insert(0, str(P / "tools/items"))
sys.path.insert(0, str(P / "tools/models"))
import art_guard

SLOW = 1.5          # 動畫放慢倍率
DROOP = 16.0        # 脖子往前垂的角度

# 腐色色階（暗 → 亮）：監守者那種深藍綠，暗部往藍紫、亮部往灰青，整體降飽和
SKIN = ["#0a1822", "#0f2430", "#15303d", "#1c3d4a", "#264b57", "#335a63"]
FUR = ["#1a2f3a", "#2a4450", "#3d5a62", "#56727a"]        # 殘留的毛：灰掉的舊毛色
BONE = ["#5d6a68", "#86948f", "#aab7b0", "#c9d2c8"]       # 原本奶油色的爪、耳尖：褪成骨頭色
SOUL = ["#0e6f7d", "#1fb3c2", "#4fe6ee", "#a8fbf6"]      # 胸口的靈魂光（歌者胸口的菱形）


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def lum(c):
    return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255


def noise(x, y):
    """便宜的低頻雜訊（0~1），決定哪裡的毛掉光了。"""
    v = math.sin(x * 0.41 + y * 0.17) + math.sin(x * 0.13 - y * 0.37 + 1.7) + math.sin((x + y) * 0.23 + 4.1)
    return (v + 3) / 6


def ramp(colors, t):
    return hexrgb(colors[max(0, min(len(colors) - 1, int(t * len(colors))))])


def paint():
    src = Image.open(A / "textures/entity/singer.png").convert("RGBA")
    w, h = src.size
    px = src.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    o = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            hh, ll, ss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            L = lum((r, g, b))
            cream = ss > 0.15 and (hh < 0.17 or hh > 0.9) and L > 0.45      # 奶油色：爪、耳尖、胸口菱形、嘴
            if cream:
                o[x, y] = ramp(BONE, (L - 0.45) / 0.55) + (255,)
                continue
            # 毛（青綠）：低頻雜訊決定這一片毛還在不在；掉光的地方用模糊的明度畫成皮膚
            if noise(x, y) > 0.56:
                o[x, y] = ramp(FUR, (L - 0.15) / 0.75) + (255,)
            else:
                acc, n = 0.0, 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        q = px[(x + dx) % w, (y + dy) % h]
                        if q[3]:
                            acc += lum(q[:3])
                            n += 1
                o[x, y] = ramp(SKIN, (acc / n - 0.1) / 0.8) + (255,)
    # 胸口菱形（歌者貼圖右下那塊奶油色菱形）改成靈魂光：找出 BONE 色、在右下角 1/4 的連通區
    for y in range(h * 3 // 4, h):
        for x in range(w * 3 // 4, w):
            r, g, b, a = px[x, y]
            if a and lum((r, g, b)) > 0.7 and r > b:
                o[x, y] = ramp(SOUL, (lum((r, g, b)) - 0.7) / 0.3) + (255,)
    return out


def animations():
    doc = json.loads((A / "geckolib/animations/entity/singer.animation.json").read_text(encoding="utf-8"))
    out = {}
    for name in ("idle", "walk", "sing", "death"):
        anim = doc["animations"].get(f"animation.singer.{name}")
        if anim is None:
            continue
        anim = json.loads(json.dumps(anim))
        if "animation_length" in anim:
            anim["animation_length"] = round(anim["animation_length"] * SLOW, 4)
        for bone, channels in anim.get("bones", {}).items():
            for ch, keys in list(channels.items()):
                if isinstance(keys, dict) and all(_is_num(k) for k in keys):
                    channels[ch] = {_fmt(float(k) * SLOW): v for k, v in keys.items()}
        neck = anim.setdefault("bones", {}).setdefault("neck", {})
        rot = neck.get("rotation")
        if isinstance(rot, dict):
            for k, v in rot.items():
                vec = v["vector"] if isinstance(v, dict) else v
                if isinstance(vec, list):
                    vec[0] = (vec[0] if isinstance(vec[0], (int, float)) else 0) + DROOP
        elif isinstance(rot, list):
            rot[0] = (rot[0] if isinstance(rot[0], (int, float)) else 0) + DROOP
        else:
            neck["rotation"] = [DROOP, 0, 0]
        out[f"animation.mourner.{name}"] = anim
    import singer_faces   # 哀悼者自己的表情（嘴巴與耳朵），見 tools/models/singer_faces.py
    for name, anim in singer_faces.MOURNER_FACES.items():
        out[f"animation.mourner.face_{name}"] = json.loads(json.dumps(anim))
    return {"format_version": doc.get("format_version", "1.8.0"), "animations": out}


def _is_num(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def _fmt(t):
    return str(round(t, 4))


def main():
    geo = json.loads((A / "geckolib/models/entity/singer.geo.json").read_text(encoding="utf-8"))
    (A / "geckolib/models/entity/mourner.geo.json").write_text(json.dumps(geo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (A / "geckolib/animations/entity/mourner.animation.json").write_text(
        json.dumps(animations(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tex_path = A / "textures/entity/mourner.png"
    if not tex_path.exists():
        art_guard.save(paint(), tex_path)
    egg_path = A / "textures/item/mourner_spawn_egg.png"
    if not egg_path.exists():
        import make_spawn_eggs
        art_guard.save(make_spawn_eggs.make_egg("mourner"), egg_path)
    # preview
    import geo_preview3d as g3
    g = geo["minecraft:geometry"][0]
    a = g3.render(g, Image.open(A / "textures/entity/singer.png").convert("RGBA"), 4, 0, 5)
    b = g3.render(g, Image.open(tex_path).convert("RGBA"), 4, 0, 5)
    c = g3.render(g, Image.open(tex_path).convert("RGBA"), 4, 180, 5)
    egg = Image.open(egg_path).convert("RGBA").resize((128, 128), Image.NEAREST)
    sheet = Image.new("RGB", (a.width + b.width + c.width + 140, max(a.height, 140)), (40, 40, 48))
    sheet.paste(a, (0, 0))
    sheet.paste(b, (a.width, 0))
    sheet.paste(c, (a.width + b.width, 0))
    sheet.paste(egg, (a.width + b.width + c.width + 6, 6), egg)
    prev = P / "build/previews/mourner.png"
    prev.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(prev)
    print("ok; preview", prev)


if __name__ == "__main__":
    main()
