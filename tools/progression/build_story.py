"""故事線第四、五幕（MODDING_ROADMAP §4.7）的資源：故事成就、哀悼者與隙浮守衛的物品定義、語系、戰利品表。
Usage: python -I tools/progression/build_story.py .
之後要重跑 tools/progression/build_codex.py（手記頁面會檢查這裡寫的物品與成就）。
程式：entity/mob/MournerEntity、SiftWardenEntity、SingerEntity（安撫監守者、屍化）、entity/WardenSoothing、
progression/StoryTriggers（頒發這裡的成就）、block/RotSpread（腐爛蔓延與止息）。
"""
import json
import sys
from pathlib import Path

P = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
LANG = {}


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tr(key, en, zh):
    LANG[key] = (en, zh)


# ------------------------------------------------------------------ story advancements (granted from StoryTriggers.java)
def adv(name, parent, icon, title, desc, frame="task", hidden=False, xp=0):
    data = {"parent": parent,
            "criteria": {"done": {"trigger": "minecraft:impossible"}},
            "display": {"icon": {"id": icon}, "title": {"translate": f"advancements.pysift.story.{name}.title"},
                        "description": {"translate": f"advancements.pysift.story.{name}.description"}, "frame": frame,
                        "show_toast": True, "announce_to_chat": frame != "task", "hidden": hidden}}
    if xp:
        data["rewards"] = {"experience": xp}
    wj(D / f"pysift/advancement/story/{name}.json", data)
    tr(f"advancements.pysift.story.{name}.title", *title)
    tr(f"advancements.pysift.story.{name}.description", *desc)


adv("warden_soothed", "pysift:progression/eight_songs", "minecraft:sculk_shrieker", ("Lullaby for the Deep", "深淵搖籃曲"),
    ("Watch a Singer sing a Warden to rest", "看著歌者把監守者唱到平靜下來"), hidden=True)
adv("mourner_cured", "pysift:story/warden_soothed", "pysift:spirit_liquid_bucket", ("Homeward Song", "歸鄉之歌"),
    ("Soak a Mourner in spirit liquid until it is a Singer again", "讓哀悼者泡在靈液裡，直到牠變回歌者"), frame="goal", xp=50)
adv("warden_cured", "pysift:story/mourner_cured", "minecraft:echo_shard", ("Bring It Home", "讓牠回家"),
    ("Let a Warden grow its fur back in The Sift's spirit liquid", "讓監守者在隙浮的靈液裡長回皮毛"), frame="challenge", xp=300)
adv("rot_stilled", "pysift:progression/kill_sculk_monstrosity", "pysift:red_sculk", ("The Rot Recedes", "腐爛退去"),
    ("Defeat the Sculk Monstrosity and stop the rot around the rifts", "擊敗幽匿巨怪，讓裂隙周圍的腐爛停止"), frame="goal")

# ------------------------------------------------------------------ mobs: names, spawn eggs, loot
MOBS = {"mourner": ("Mourner", "哀悼者"), "sift_warden": ("Sift Warden", "隙浮守衛")}
for mob, (en, zh) in MOBS.items():
    tr(f"entity.pysift.{mob}", en, zh)
    tr(f"item.pysift.{mob}_spawn_egg", f"{en} Spawn Egg", f"{zh}生怪蛋")
    wj(A / f"items/{mob}_spawn_egg.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{mob}_spawn_egg"}})
    wj(A / f"models/item/{mob}_spawn_egg.json", {"parent": "minecraft:item/generated",
                                                  "textures": {"layer0": f"pysift:item/{mob}_spawn_egg"}})

# Mourners drop nothing but a little sculk: you should not want to kill them
wj(D / "pysift/loot_table/entities/mourner.json", {"type": "minecraft:entity", "pools": [{"rolls": 1, "entries": [
    {"type": "minecraft:item", "name": "minecraft:sculk_vein",
     "functions": [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 0, "max": 2}}]}]}]})
# the Sift Warden keeps the Warden's sculk catalyst
wj(D / "pysift/loot_table/entities/sift_warden.json", {"type": "minecraft:entity", "pools": [{"rolls": 1, "entries": [
    {"type": "minecraft:item", "name": "minecraft:sculk_catalyst"}]}]})

# starved creatures drink spirit liquid instead of being hurt by it (that is how they are cured): SpiritFluid.SOUL_STARVED.
# Healthy Sift natives take too many souls in and are hurt like everyone else.
wj(D / "pysift/tags/entity_type/soul_starved.json", {"replace": False, "values": ["pysift:mourner", "minecraft:warden"]})
(D / "pysift/tags/entity_type/spirit_native.json").unlink(missing_ok=True)
tr("message.pysift.rot.stilled", "The heart of the rot is gone. Around the rifts, the sculk begins to turn red again.",
   "腐爛的核心消失了。裂隙周圍的幽匿，開始慢慢變回紅色。")
tr("message.pysift.sift_warden.follow", "The Sift Warden hums and starts to follow you", "隙浮守衛低聲哼著，開始跟著你走")
tr("message.pysift.sift_warden.stay", "The Sift Warden settles down and waits here", "隙浮守衛安靜下來，在這裡等著")

# ------------------------------------------------------------------ ancient pottery sherds (AncientPages.SHERDS)
import io
import zipfile
sys.path.insert(0, str(P / "tools"))
import art_guard
from PIL import Image

JAR = next((P / ".gradle/loom-cache/minecraftMaven/net/minecraft").glob("minecraft-clientOnly-*/26.3/*.jar"))
VANILLA = zipfile.ZipFile(JAR)


def vanilla(name):
    return Image.open(io.BytesIO(VANILLA.read(f"assets/minecraft/textures/{name}.png"))).convert("RGBA")


# 10x10 motifs, placed at (3, 3) on the pot side like the vanilla patterns. '#' = carved
OCTAVE = [1, 3, 7, 6, 5, 2, 4, 8]   # the right order: bar heights
SHERDS = {
    "gate": (("Gate", "門扉"), [
        ".########.",
        ".#......#.",
        ".#..##..#.",
        ".#.#..#.#.",
        ".#..#.#.#.",
        ".#.#..#.#.",
        ".#..##..#.",
        ".#......#.",
        ".#......#.",
        "##......##"]),
    "singer": (("Singer", "歌者"), [
        "#.#....#.#",
        ".##....##.",
        "..#.##.#..",
        "...####...",
        "...#..#...",
        "...####...",
        "..######..",
        "..######..",
        "..#.##.#..",
        "..#....#.."]),
    "kin": (("Kin", "親族"), [
        "#........#",
        ".#.####.#.",
        "..######..",
        "..#.##.#..",
        "..######..",
        "...####...",
        "..#.##.#..",
        "..######..",
        "..#.##.#..",
        "..##..##.."]),
    "octave": (("Octave", "八音"), [
        "".join("#" if 1 <= x <= 8 and y >= 9 - OCTAVE[x - 1] else "." for x in range(10)) for y in range(10)]),
}
CARVE, CARVE_DARK, LIP = (0x5e, 0x37, 0x2f), (0x52, 0x2d, 0x25), (0x9f, 0x59, 0x49)


def pattern(motif, striped=False):
    # a vanilla pattern (with the pot's rim bands), its own carving replaced by the plain pot side
    img = vanilla("entity/decorated_pot/skull_pottery_pattern")
    side = vanilla("entity/decorated_pot/decorated_pot_side")
    px = img.load()
    for y in range(2, 14):
        for x in range(2, 14):
            px[x, y] = side.getpixel((x, y))
    for y, row in enumerate(motif):
        for x, c in enumerate(row):
            if c == "#":
                below = y + 1 < 10 and motif[y + 1][x] == "#"
                dark = (x % 2 == 0) if striped else not below      # octave: every other bar darker, so the eight read apart
                px[3 + x, 3 + y] = (CARVE_DARK if dark else CARVE) + (255,)
            elif (y > 0 and motif[y - 1][x] == "#") or (x > 0 and row[x - 1] == "#"):
                px[3 + x, 3 + y] = LIP + (255,)       # the lower-right lip of the carving catches the light
    return img


def sherd(pat):
    """The vanilla sherd's shape (skull sherd), filled with our carved face; edges shaded like the vanilla piece."""
    shape = vanilla("item/skull_pottery_sherd")
    out = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    m = lambda x, y: 0 <= x < 16 and 0 <= y < 16 and shape.getpixel((x, y))[3] > 0
    for y in range(16):
        for x in range(16):
            if not m(x, y):
                continue
            if not m(x + 1, y) or not m(x, y + 1):
                c = (0x47, 0x25, 0x1d)
            elif not m(x + 2, y) or not m(x, y + 2):
                c = (0x5e, 0x37, 0x2f)
            elif not m(x - 1, y) or not m(x, y - 1):
                c = (0x9f, 0x59, 0x49)
            else:
                c = pat.getpixel((x, y))[:3]
            out.putpixel((x, y), c + (255,))
    return out


sherd_tag = []
for name, ((en, zh), motif) in SHERDS.items():
    wj(D / f"pysift/decorated_pot_pattern/{name}.json", {"asset_id": f"pysift:{name}_pottery_pattern"})
    pat = pattern(motif, striped=name == "octave")
    art_guard.save(pat, A / f"textures/entity/decorated_pot/{name}_pottery_pattern.png") \
        if not (A / f"textures/entity/decorated_pot/{name}_pottery_pattern.png").exists() else None
    item_png = A / f"textures/item/{name}_pottery_sherd.png"
    if not item_png.exists():
        art_guard.save(sherd(pat), item_png)
    wj(A / f"items/{name}_pottery_sherd.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{name}_pottery_sherd"}})
    wj(A / f"models/item/{name}_pottery_sherd.json", {"parent": "minecraft:item/generated",
                                                       "textures": {"layer0": f"pysift:item/{name}_pottery_sherd"}})
    tr(f"item.pysift.{name}_pottery_sherd", f"{en} Pottery Sherd", f"{zh}陶器碎片")
    sherd_tag.append(f"pysift:{name}_pottery_sherd")
tag = D / "minecraft/tags/item/decorated_pot_sherds.json"
data = json.loads(tag.read_text(encoding="utf-8")) if tag.exists() else {"replace": False, "values": []}
data["values"] = list(dict.fromkeys(data["values"] + sherd_tag))
wj(tag, data)
preview = Image.new("RGBA", (16 * len(SHERDS), 32), (90, 90, 100, 255))
for i, name in enumerate(SHERDS):
    preview.alpha_composite(Image.open(A / f"textures/entity/decorated_pot/{name}_pottery_pattern.png").convert("RGBA"), (i * 16, 0))
    preview.alpha_composite(Image.open(A / f"textures/item/{name}_pottery_sherd.png").convert("RGBA"), (i * 16, 16))
(P / "build/previews").mkdir(parents=True, exist_ok=True)
preview.resize((preview.width * 10, preview.height * 10), Image.NEAREST).save(P / "build/previews/sherds.png")

# ------------------------------------------------------------------ lang
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in LANG.items():
        data[key] = names[i]
    wj(f, data)
print("story resources:", len(LANG), "lang keys")
