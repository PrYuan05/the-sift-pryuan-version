"""Hunter / Trapper 的動畫、名稱、生怪蛋圖示、定身效果圖示、生態域生成（模型在 build_hunter_trapper.py）。
Usage: python -I tools/models/hunter_trapper_assets.py
旋轉慣例（GeckoLib）：+x 頂端往前；手臂往前／往上舉用負 x。
"""
import json, shutil, datetime
from pathlib import Path
from PIL import Image

P = Path(__file__).resolve().parents[2]
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data/pysift"
BK = P / ".texture_backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "_hunter_trapper")


def k(d):
    return {str(t): v for t, v in d.items()}


def backup(p):
    if p.exists():
        dst = BK / p.relative_to(P)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)


def wj(p, obj, indent="\t"):
    backup(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


WALK = lambda swing: {"animation_length": 1.0, "loop": True, "bones": {
    "left_leg": {"rotation": k({0.0: [swing, 0, 0], 0.5: [-swing, 0, 0], 1.0: [swing, 0, 0]})},
    "right_leg": {"rotation": k({0.0: [-swing, 0, 0], 0.5: [swing, 0, 0], 1.0: [-swing, 0, 0]})},
    "left_arm": {"rotation": k({0.0: [-swing * 0.6, 0, 0], 0.5: [swing * 0.6, 0, 0], 1.0: [-swing * 0.6, 0, 0]})},
    "right_arm": {"rotation": k({0.0: [swing * 0.6, 0, 0], 0.5: [-swing * 0.6, 0, 0], 1.0: [swing * 0.6, 0, 0]})},
    "body": {"position": k({0.0: [0, 0, 0], 0.25: [0, 0.5, 0], 0.5: [0, 0, 0], 0.75: [0, 0.5, 0], 1.0: [0, 0, 0]})}}}

IDLE = {"animation_length": 3.0, "loop": True, "bones": {
    "head": {"rotation": k({0.0: [0, 0, 0], 1.0: [2, 12, 0], 2.0: [2, -12, 0], 3.0: [0, 0, 0]})},
    "body": {"position": k({0.0: [0, 0, 0], 1.5: [0, 0.4, 0], 3.0: [0, 0, 0]})},
    "left_arm": {"rotation": k({0.0: [0, 0, 0], 1.5: [-4, 0, 0], 3.0: [0, 0, 0]})},
    "right_arm": {"rotation": k({0.0: [0, 0, 0], 1.5: [-4, 0, 0], 3.0: [0, 0, 0]})}}}

HUNTER = {
    "idle": IDLE,
    "walk": WALK(28),
    # 標槍近戰：右手往前上舉起再往下刺
    "attack": {"animation_length": 0.6, "bones": {
        "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.2: [-120, 0, 0], 0.35: [-30, 0, 0], 0.6: [0, 0, 0]})},
        "body": {"rotation": k({0.0: [0, 0, 0], 0.2: [-5, 15, 0], 0.35: [10, -10, 0], 0.6: [0, 0, 0]})}}},
    # 投擲：右手往後上舉、身體扭轉蓄力，第 0.55 秒（11 tick）甩出
    "throw": {"animation_length": 1.0, "bones": {
        "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.35: [-165, 0, -10], 0.5: [-150, 0, -10], 0.6: [-50, 0, 0], 1.0: [0, 0, 0]})},
        "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.35: [-60, 0, 0], 0.6: [10, 0, 0], 1.0: [0, 0, 0]})},
        "body": {"rotation": k({0.0: [0, 0, 0], 0.35: [-8, 25, 0], 0.6: [12, -15, 0], 1.0: [0, 0, 0]})},
        "head": {"rotation": k({0.0: [0, 0, 0], 0.35: [0, -20, 0], 0.6: [0, 10, 0], 1.0: [0, 0, 0]})}}},
    # 標記：左手直直指向目標
    "mark": {"animation_length": 1.0, "bones": {
        "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.3: [-90, 0, 0], 0.8: [-90, 0, 0], 1.0: [0, 0, 0]})},
        "head": {"rotation": k({0.0: [0, 0, 0], 0.3: [-8, 0, 0], 0.8: [-8, 0, 0], 1.0: [0, 0, 0]})},
        "body": {"rotation": k({0.0: [0, 0, 0], 0.3: [0, -10, 0], 0.8: [0, -10, 0], 1.0: [0, 0, 0]})}}},
    # 後跳：蹲低再往後彈
    "leap": {"animation_length": 0.7, "bones": {
        "body": {"rotation": k({0.0: [0, 0, 0], 0.15: [15, 0, 0], 0.3: [-20, 0, 0], 0.7: [0, 0, 0]}),
                 "position": k({0.0: [0, 0, 0], 0.15: [0, -2, 0], 0.3: [0, 0, 0]})},
        "left_leg": {"rotation": k({0.0: [0, 0, 0], 0.3: [30, 0, 0], 0.7: [0, 0, 0]})},
        "right_leg": {"rotation": k({0.0: [0, 0, 0], 0.3: [30, 0, 0], 0.7: [0, 0, 0]})},
        "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.3: [-40, 0, -20], 0.7: [0, 0, 0]})},
        "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.3: [-40, 0, 20], 0.7: [0, 0, 0]})}}},
}

TRAPPER = {
    "idle": IDLE,
    "walk": WALK(22),
    # 長爪交叉揮抓
    "attack": {"animation_length": 0.6, "bones": {
        "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.2: [-45, 20, 0], 0.35: [25, -15, 0], 0.6: [0, 0, 0]})},
        "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.25: [-45, -20, 0], 0.4: [25, 15, 0], 0.6: [0, 0, 0]})},
        "body": {"rotation": k({0.0: [0, 0, 0], 0.3: [12, 0, 0], 0.6: [0, 0, 0]})}}},
    # 佈陷阱：彎腰把雙爪按進地面，第 0.6 秒（12 tick）陷阱成形
    "set_trap": {"animation_length": 1.2, "bones": {
        "body": {"rotation": k({0.0: [0, 0, 0], 0.4: [35, 0, 0], 0.8: [35, 0, 0], 1.2: [0, 0, 0]})},
        "left_arm": {"rotation": k({0.0: [0, 0, 0], 0.4: [30, 0, 0], 0.6: [45, 0, 0], 0.8: [30, 0, 0], 1.2: [0, 0, 0]})},
        "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.4: [30, 0, 0], 0.6: [45, 0, 0], 0.8: [30, 0, 0], 1.2: [0, 0, 0]})},
        "head": {"rotation": k({0.0: [0, 0, 0], 0.4: [-20, 0, 0], 0.8: [-20, 0, 0], 1.2: [0, 0, 0]})}}},
    # 丟網：右爪往後拉，第 0.5 秒（10 tick）甩出
    "throw_net": {"animation_length": 0.9, "bones": {
        "right_arm": {"rotation": k({0.0: [0, 0, 0], 0.3: [50, 0, 20], 0.5: [-110, 0, 0], 0.9: [0, 0, 0]})},
        "body": {"rotation": k({0.0: [0, 0, 0], 0.3: [-5, 20, 0], 0.5: [10, -15, 0], 0.9: [0, 0, 0]})}}},
}


def animations():
    for mob, anims in (("hunter", HUNTER), ("trapper", TRAPPER)):
        doc = {"format_version": "1.8.0", "animations": {f"animation.{mob}.{n}": a for n, a in anims.items()}}
        wj(A / f"geckolib/animations/entity/{mob}.animation.json", doc)


def lang():
    names = {
        "zh_tw": {"entity.pysift.hunter": "獵人", "entity.pysift.trapper": "陷阱師", "entity.pysift.trapper_net": "陷阱師的網",
                  "entity.pysift.soul_snare": "靈魂陷阱", "item.pysift.hunter_spawn_egg": "獵人生怪蛋",
                  "item.pysift.trapper_spawn_egg": "陷阱師生怪蛋", "effect.pysift.ensnared": "定身"},
        "en_us": {"entity.pysift.hunter": "Hunter", "entity.pysift.trapper": "Trapper", "entity.pysift.trapper_net": "Trapper Net",
                  "entity.pysift.soul_snare": "Soul Snare", "item.pysift.hunter_spawn_egg": "Hunter Spawn Egg",
                  "item.pysift.trapper_spawn_egg": "Trapper Spawn Egg", "effect.pysift.ensnared": "Ensnared"},
    }
    for l, entries in names.items():
        p = A / f"lang/{l}.json"
        backup(p)
        j = json.loads(p.read_text(encoding="utf-8"))
        j.update(entries)
        p.write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def spawn_eggs():
    """以潛伏獵手的蛋為形狀：底色像素換成主色、斑點換成副色（亮度保留）。"""
    src = Image.open(A / "textures/item/stalker_spawn_egg.png").convert("RGBA")
    px = src.load()
    for mob, base, spot in (("hunter", (16, 56, 70), (240, 122, 58)), ("trapper", (44, 40, 76), (240, 122, 176))):
        out = Image.new("RGBA", src.size)
        op = out.load()
        for y in range(src.height):
            for x in range(src.width):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                lum = (r + g + b) / 3 / 255
                is_spot = b > r + 25          # 原本的紫色斑點
                c = spot if is_spot else base
                f = 0.55 + lum * 1.6 if not is_spot else 0.7 + lum * 0.8
                op[x, y] = tuple(min(255, int(ch * f)) for ch in c) + (a,)
        p = A / f"textures/item/{mob}_spawn_egg.png"
        backup(p)
        out.save(p)
        wj(A / f"items/{mob}_spawn_egg.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{mob}_spawn_egg"}}, 2)
        wj(A / f"models/item/{mob}_spawn_egg.json", {"parent": "minecraft:item/generated",
                                                     "textures": {"layer0": f"pysift:item/{mob}_spawn_egg"}}, 2)


def effect_icon():
    """18x18 定身圖示：粉紅色的網格陷阱。"""
    im = Image.new("RGBA", (18, 18), (0, 0, 0, 0))
    pink, dark = (240, 122, 176, 255), (120, 50, 100, 255)
    for i in range(2, 16):
        for j in (3, 8, 13):
            im.putpixel((i, j), pink)
            im.putpixel((j, i), pink)
    for i in range(2, 16):   # 外框鋸齒（陷阱的齒）
        if i % 2 == 0:
            im.putpixel((i, 1), dark)
            im.putpixel((i, 16), dark)
    p = A / "textures/mob_effect/ensnared.png"
    backup(p)
    im.save(p)


def biome_spawns():
    """低權重自然生成：獵人和潛伏獵手一起在紫晶區，陷阱師和食腐獸一起在沙丘。build_the_sift.py 也同步加上。"""
    for biome, mob, w in (("violet_slate_abyss", "hunter", 10), ("amber_dunes", "trapper", 10)):
        p = D / f"worldgen/biome/{biome}.json"
        backup(p)
        j = json.loads(p.read_text(encoding="utf-8"))
        cat = j["attributes"]["minecraft:gameplay/natural_mob_spawns"]["argument"]["spawns_by_category"]["monster"]
        if not any(e["type"] == f"pysift:{mob}" for e in cat):
            cat.append({"type": f"pysift:{mob}", "count": {"type": "minecraft:uniform", "max_inclusive": 1, "min_inclusive": 1},
                        "weight": w})
        p.write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    animations()
    lang()
    spawn_eggs()
    effect_icon()
    biome_spawns()
    print("done; backups in", BK)
