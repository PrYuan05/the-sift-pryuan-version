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
tr("message.pysift.den_guard.roused", "The den's guards wake to a stranger's noise", "回音窟的守衛被陌生的聲響吵醒了")

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

# ================================================================== part 2: story items (StoryItems.java, Homecoming.java)
import colorsys


def recolour(img, fn):
    """Per pixel (h, l, s) -> (h, l, s); alpha kept."""
    out = img.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a:
                h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
                h, l, s = fn(h, l, s)
                rr, gg, bb = colorsys.hls_to_rgb(h % 1.0, max(0, min(1, l)), max(0, min(1, s)))
                px[x, y] = (round(rr * 255), round(gg * 255), round(bb * 255), a)
    return out


def save_new(img, rel):
    path = A / rel
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        art_guard.save(img, path)


SPIRIT_HUE = 0.92   # spirit liquid pink-magenta
# Mourning Horn: the goat horn turned sculk-teal, its pale tip left as bone
save_new(recolour(vanilla("item/goat_horn"), lambda h, l, s: (h, l, s) if l > 0.62 else (0.48, l * 0.85, min(0.55, s + 0.15))),
         "textures/item/mourning_horn.png")
# Rift Seal: an echo shard set in spirit-pink
save_new(recolour(vanilla("item/echo_shard"), lambda h, l, s: (SPIRIT_HUE, l, min(0.8, s + 0.2))), "textures/item/rift_seal.png")
# Sift Heart: the Sculk Monstrosity's heart, healed red
heart = Image.open(A / "textures/item/sculk_monstrosity_heart.png").convert("RGBA")
save_new(recolour(heart, lambda h, l, s: (0.95 if s > 0.12 else h, l, s)), "textures/item/sift_heart.png")
# Ancient Chronicle: a written book with a teal sculk-leather cover
save_new(recolour(vanilla("item/written_book"), lambda h, l, s: (h, l, s) if l > 0.7 or s < 0.15 else (0.5, l * 0.9, s * 0.8)),
         "textures/item/ancient_chronicle.png")
# Lullaby Censer: a soul lantern burning spirit liquid (block + item textures)
censer = lambda h, l, s: (SPIRIT_HUE, l, min(0.85, s + 0.1)) if 0.4 < h < 0.62 and s > 0.25 else (h, l, s)
save_new(recolour(vanilla("block/soul_lantern"), censer), "textures/block/lullaby_censer.png")
save_new(recolour(vanilla("item/soul_lantern"), censer), "textures/item/lullaby_censer.png")
mcmeta = VANILLA.read("assets/minecraft/textures/block/soul_lantern.png.mcmeta") if "assets/minecraft/textures/block/soul_lantern.png.mcmeta" in VANILLA.namelist() else None
if mcmeta and not (A / "textures/block/lullaby_censer.png.mcmeta").exists():
    (A / "textures/block/lullaby_censer.png.mcmeta").write_bytes(mcmeta)

for item in ("mourning_horn", "rift_seal", "sift_heart", "ancient_chronicle"):
    wj(A / f"items/{item}.json", {"model": {"type": "minecraft:model", "model": f"pysift:item/{item}"}})
    wj(A / f"models/item/{item}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"pysift:item/{item}"}})
wj(A / "blockstates/lullaby_censer.json", {"variants": {"hanging=false": {"model": "pysift:block/lullaby_censer"},
                                                         "hanging=true": {"model": "pysift:block/lullaby_censer_hanging"}}})
wj(A / "models/block/lullaby_censer.json", {"parent": "minecraft:block/template_lantern", "textures": {"lantern": "pysift:block/lullaby_censer"}})
wj(A / "models/block/lullaby_censer_hanging.json", {"parent": "minecraft:block/template_hanging_lantern",
                                                    "textures": {"lantern": "pysift:block/lullaby_censer"}})
wj(A / "items/lullaby_censer.json", {"model": {"type": "minecraft:model", "model": "pysift:item/lullaby_censer"}})
wj(A / "models/item/lullaby_censer.json", {"parent": "minecraft:item/generated", "textures": {"layer0": "pysift:item/lullaby_censer"}})
censer_loot = {"type": "minecraft:block", "pools": [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": "pysift:lullaby_censer"}],
                                                     "conditions": [{"condition": "minecraft:survives_explosion"}]}]}
wj(D / "pysift/loot_table/blocks/lullaby_censer.json", censer_loot)
wj(D / "pysift/loot_tables/blocks/lullaby_censer.json", censer_loot)
pick = D / "minecraft/tags/block/mineable/pickaxe.json"
data = json.loads(pick.read_text(encoding="utf-8"))
if "pysift:lullaby_censer" not in data["values"]:
    data["values"].append("pysift:lullaby_censer")
    wj(pick, data)

R = D / "pysift/recipe"
wj(R / "mourning_horn.json", {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": [
    "minecraft:goat_horn", "pysift:octave_pottery_sherd", "pysift:kin_pottery_sherd", "minecraft:echo_shard"],
    "result": {"id": "pysift:mourning_horn", "count": 1}})
wj(R / "rift_seal.json", {"type": "minecraft:crafting_shaped", "category": "misc", "pattern": ["ECE", "CGC", "ECE"],
                          "key": {"E": "minecraft:echo_shard", "C": "pysift:soul_crystal_block", "G": "pysift:gate_pottery_sherd"},
                          "result": {"id": "pysift:rift_seal", "count": 1}})
wj(R / "lullaby_censer.json", {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": [
    "minecraft:soul_lantern", "pysift:singer_pottery_sherd", "pysift:soul_crystal_block", "pysift:spirit_liquid_bucket"],
    "result": {"id": "pysift:lullaby_censer", "count": 1}})
wj(R / "ancient_chronicle.json", {"type": "minecraft:crafting_shapeless", "category": "misc",
                                  "ingredients": [f"pysift:ancient_page_{i}" for i in range(1, 9)] + ["minecraft:book"],
                                  "result": {"id": "pysift:ancient_chronicle", "count": 1}})

adv("rift_sealed", "pysift:story/warden_soothed", "pysift:rift_seal", ("Stitched Shut", "縫合"),
    ("Seal a rift in The Sift with a Rift Seal", "用封印石封住隙浮裡的一道裂隙"), frame="goal", xp=100)
adv("chronicle", "pysift:progression/eight_songs", "pysift:ancient_chronicle", ("The Ancient Chronicle", "遠古編年史"),
    ("Bind the eight ancient pages into one book and read it", "把八張遠古殘頁裝訂成一本書，讀完它"), frame="goal", xp=100)
adv("homecoming", "pysift:story/warden_cured", "pysift:sift_heart", ("They Went Home", "牠們回家了"),
    ("At the Ancient City's door, let a Singer sing a Sift Warden home", "在遠古城市的門框前，讓歌者把隙浮守衛唱回家"),
    frame="challenge", xp=1000)

for key, en, zh in [
    ("item.pysift.mourning_horn", "Mourning Horn", "哀悼號角"),
    ("item.pysift.rift_seal", "Rift Seal", "封印石"),
    ("item.pysift.sift_heart", "Sift Heart", "隙浮之心"),
    ("item.pysift.ancient_chronicle", "Ancient Chronicle", "遠古編年史"),
    ("block.pysift.lullaby_censer", "Lullaby Censer", "搖籃曲香爐"),
    # echo den (another session's block, tools/worldgen/build_echo_cradle.py): names live here because this script owns lang
    ("block.pysift.echo_cradle", "Echo Cradle", "回音晶簇"),
    ("item.pysift.echo_cradle", "Echo Cradle", "回音晶簇"),
    ("item.pysift.lullaby_censer", "Lullaby Censer", "搖籃曲香爐"),
    ("tooltip.pysift.ancient_chronicle", "The whole story, in the ancients' own words", "遠古人親手寫下的完整故事"),
    ("tooltip.pysift.mourning_horn", "Plays the eight notes backwards: Wardens within 24 blocks calm down for 30 s",
     "倒著吹出八音：24 格內的監守者平靜 30 秒"),
    ("tooltip.pysift.mourning_horn.finale", "At the Ancient City's door, with a Singer and a Sift Warden beside you...",
     "在遠古城市的門框前，身邊有歌者和隙浮守衛的時候……"),
    ("tooltip.pysift.rift_seal", "Use on a portal in The Sift: the rift closes and the rot around it heals",
     "對隙浮裡的傳送門使用：裂隙關閉，周圍的腐爛慢慢痊癒"),
    ("tooltip.pysift.sift_heart", "Use on a Warden or a Mourner to bring it home at once", "對監守者或哀悼者使用，立刻把牠帶回來"),
    ("tooltip.pysift.lullaby_censer", "Singers within 16 blocks never hollow; Mourners within 8 slowly heal",
     "16 格內的歌者不會屍化；8 格內的哀悼者慢慢痊癒"),
    ("tooltip.pysift.octave_pottery_sherd", "Use: plays the eight jukeboxes' notes, left to right", "右鍵：由左到右奏出八個唱片盒的音"),
    ("tooltip.pysift.sculk_monstrosity_heart.purify", "Drop it in spirit liquid to purify it", "丟進靈液可以淨化"),
    ("message.pysift.mourning_horn.calmed", "%s Warden(s) fall quiet", "%s 隻監守者安靜了下來"),
    ("message.pysift.octave_sherd.seat", "Jukebox %s: %s", "第 %s 個唱片盒：%s"),
    ("message.pysift.rift_seal.sealed", "The rift closes. Around it, the rot begins to heal.", "裂隙闔上了。周圍的腐爛開始慢慢痊癒。"),
    ("message.pysift.rift_seal.not_here", "Only rifts in The Sift can be sealed", "只能封印隙浮裡的裂隙"),
    ("message.pysift.homecoming.missing_rot", "The door listens... but the rot still spreads. Defeat the Sculk Monstrosity first.",
     "門在聽……但腐爛還在蔓延。先擊敗幽匿巨怪。"),
    ("message.pysift.homecoming.missing_singer", "The door listens... but no Singer is here to sing it open.",
     "門在聽……但這裡沒有能把它唱開的歌者。"),
    ("message.pysift.homecoming.missing_warden", "The door listens... but no Sift Warden is here to go home.",
     "門在聽……但這裡沒有要回家的隙浮守衛。"),
    ("message.pysift.homecoming.begin", "The Singer turns to the door and sings the eight notes the right way round.",
     "歌者轉向門框，把八音正著唱了一遍。"),
    ("message.pysift.homecoming.done", "The door remembers its song. The Singer and the Sift Warden go home, and the sculk here wakes up red.",
     "門想起了自己的歌。歌者和隙浮守衛回家了，這裡的幽匿醒了過來，變回紅色。"),
    ("message.pysift.homecoming.reunion", "Somewhere close, you hear a familiar hum.", "附近傳來熟悉的哼唱聲。"),
]:
    tr(key, en, zh)

# ------------------------------------------------------------------ lang
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for key, names in LANG.items():
        data[key] = names[i]
    wj(f, data)
print("story resources:", len(LANG), "lang keys")
