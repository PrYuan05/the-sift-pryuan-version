"""The Sift Codex (隙浮手記): a Modonomicon book that replaces the old written guidebook.
Usage: python -I tools/progression/build_codex.py <project>

Writes
  data/pysift/modonomicon/books/sift_codex/   book, categories, entries and pages (node view, like Alex's Mobs' bestiary)
  data/pysift/modonomicon/research/sift_codex/ facts, hooks and nodes that unlock entries
  data/pysift/advancement/codex/               hidden "met <mob>" advancements (kill, hurt, get hurt by or interact)
  assets/pysift/textures/gui/codex/            category backgrounds tiled from the mod's own block textures
  ancient pages (AncientPages.java): item models, one texture recoloured from vanilla paper, written-book text
  recipe: book + echo shard -> codex; lang en_us / zh_tw

Unlocking
  bestiary and bosses: an entry opens when you first meet that creature (advancement hook)
  ancient pages: an entry opens when you pick the page up (item_acquired hook); all 8 open the full story
Story text follows MODDING_ROADMAP_AND_SPECS.md 4.7."""
import io, json, sys, zipfile
from pathlib import Path

from PIL import Image, ImageEnhance

P = Path(sys.argv[1])
sys.path.insert(0, str(P / "tools"))
import art_guard

A = P / "src/main/resources/assets/pysift"
D = P / "src/main/resources/data"
BOOK = D / "pysift/modonomicon/books/sift_codex"
RESEARCH = D / "pysift/modonomicon/research/sift_codex"
JAR = next((P / ".gradle/loom-cache/minecraftMaven/net/minecraft").glob("minecraft-clientOnly-*/26.3/*.jar"))
VANILLA = zipfile.ZipFile(JAR)
LANG = {}   # key -> (en, zh)


def wj(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def tr(key, en, zh):
    LANG[key] = (en, zh)
    return key


def item_exists(item_id):
    ns, path = item_id.split(":")
    return ns == "minecraft" or path.startswith("ancient_page_") or (A / f"items/{path}.json").exists()   # pages: written below


# ------------------------------------------------------------------ backgrounds
def background(name, texture, darken=0.42):
    """512x512 backdrop. The Sift's own scenes are painted by tools/progression/paint_codex_theme.py (user: the book
    should look like The Sift); only a category without a painted backdrop falls back to one of our block textures,
    tiled at 2x and darkened, so the node map reads on top of it."""
    painted = A / f"textures/gui/codex/{name}.png"
    if painted.exists() and name in PAINTED:
        return f"pysift:textures/gui/codex/{name}.png"
    src = Image.open(A / f"textures/block/{texture}.png").convert("RGBA")
    tile = src.crop((0, 0, src.width, src.width)).resize((32, 32), Image.NEAREST)   # first frame of animated ones
    out = Image.new("RGBA", (512, 512))
    for y in range(0, 512, 32):
        for x in range(0, 512, 32):
            out.paste(tile, (x, y))
    out = ImageEnhance.Brightness(out).enhance(darken)
    art_guard.save(out, A / f"textures/gui/codex/{name}.png")
    return f"pysift:textures/gui/codex/{name}.png"


PAINTED = {"journey", "sift", "bestiary", "bosses", "gear", "lore"}    # backdrops from paint_codex_theme.py
# drifting soul motes (paint_codex_theme.py) instead of Modonomicon's night-sky stars
STARS = [{"background": f"pysift:textures/gui/codex/motes_{i}.png", "speed": s} for i, s in ((1, 0.8), (2, 1.1), (3, 1.4))]

# ------------------------------------------------------------------ book
wj(BOOK / "book.json", {
    "name": tr("book.pysift.sift_codex.name", "The Sift Codex", "隙浮手記"),
    "tooltip": tr("book.pysift.sift_codex.tooltip", "Notes on The Sift, its creatures and the song that broke the door",
                  "關於隙浮、牠的生物，以及那首把門撕開的歌"),
    "description": "", "model": "pysift:sift_codex", "generate_book_item": True,   # own item (paint_codex_theme.py)
    "creative_tab": "pysift:pysift_items", "display_mode": "node", "page_display_mode": "double_page",
    "font": "minecraft:default",   # modonomicon:default has no CJK glyphs (zh_tw showed boxes); vanilla falls back to unifont "turn_page_sound": "modonomicon:turn_page", "show_recently_unlocked": True,
    "default_auto_scale": True, "default_allow_page_split": False, "allow_open_book_with_invalid_links": True})
# the codex's own theme: Modonomicon finds its sprites under pysift:textures/gui/sprites/modonomicon/themes/sift_codex/
# (painted by paint_codex_theme.py) and falls back to the default theme for the rest; text in deep plum, titles in
# deep soul teal on the blush pages
wj(BOOK / "theme.json", {"type": "modonomicon:default", "id": "pysift:sift_codex",
                         "palette": {"default_text_color": 0xFF3A2440 - (1 << 32), "default_title_color": 0xFF1F5A63 - (1 << 32)}})

CATEGORIES = []   # (id, sort, icon, en, zh, texture)


def category(cid, sort, icon, en, zh, texture):
    assert item_exists(icon), icon
    wj(BOOK / f"categories/{cid}.json", {
        "name": tr(f"book.pysift.sift_codex.{cid}.name", en, zh), "description": "", "icon": {"id": icon},
        "sort_number": sort, "display_mode": "node", "show_category_button": True,
        "background": background(cid, texture), "background_width": 512, "background_height": 512,
        "background_texture_zoom_multiplier": 1.0, "background_parallax_layers": STARS,
        "max_scroll_x": 512, "max_scroll_y": 512})


# ------------------------------------------------------------------ pages
def text(title, en, zh):
    return {"type": "modonomicon:text", "title": title, "text": (en, zh), "show_title_separator": bool(title)}


# hitbox (ModEntities) x the SCALE attribute, in blocks: (width, height, scale)
HITBOX = {"blub": (0.8, 0.8, 1), "echo_golem": (1.4, 2.6, 1), "singer": (1.0, 2.7, 1.456), "nuzzle": (1.0, 1.3, 1),
          "lootkin": (0.6, 0.8, 1), "fusefly": (0.6, 1.0, 1), "dartback": (0.6, 0.53, 3.15), "hurler": (1.0, 1.0, 1),
          "pollinator": (0.8, 1.5, 1), "nester": (0.6, 1.08, 1.67), "seedling": (0.6, 0.8, 1), "sprout": (0.7, 1.6, 1),
          "stalker": (0.8, 1.3, 1.89), "scavenger": (1.0, 1.6, 1), "hunter": (0.8, 2.1, 1), "trapper": (0.9, 1.75, 1),
          "slabber": (1.4, 1.7, 1), "prickle": (0.6, 0.8, 1), "sentinel": (0.6, 0.89, 1.8 / (14.25 / 16.0)),
          "tuner": (0.7, 1.3, 1), "bloombud": (0.9, 2.4, 0.5), "roamroot": (1.1, 2.4, 1), "wobble": (0.8, 0.85, 1),
          "harmonizer": (2.4, 3.8, 2.35), "monarch": (1.2, 3.6, 2.5), "sculk_monstrosity": (3.2, 4.25, 1.8)}


def entity(eid, en="", zh="", scale=1.0, offset=None):
    """Modonomicon puts the feet max(height, size) / 2 below the frame centre on top of half the height (its own demo
    lifts the spider by -0.5): cancel that so the model sits centred in the frame."""
    if offset is None:
        w, h, k = HITBOX[eid.split(":")[1]]
        offset = -max(w * k, h * k, 1.0) / 2
    return {"type": "modonomicon:entity", "entity_id": eid, "entity_name": "", "scale": scale, "offset": offset,
            "rotate": True, "default_rotation": -45.0, "text": (en, zh)}


def spotlight(item, en, zh):
    assert item_exists(item), item
    return {"type": "modonomicon:spotlight", "item": {"id": item}, "title": "", "text": (en, zh)}


def recipe(kind, r1, r2=None, en="", zh=""):
    for r in (r1, r2):
        if r:
            assert (D / f"pysift/recipe/{r.split(':')[1]}.json").exists() or r.startswith("minecraft:"), r
    page = {"type": f"modonomicon:{kind}_recipe", "recipe_id_1": r1, "text": (en, zh)}
    if r2:
        page["recipe_id_2"] = r2
    return page


GOLD, GRAY, PURPLE = "square_gold", "square_gray", "square_purple"
SPRITES = "modonomicon:modonomicon/themes/default/node/entry_backgrounds/"


def entry(cat, eid, icon, en, zh, x, y, pages, parents=(), desc=("", ""), node=None, shape=GOLD, line=True,
          locked_tip=None):
    """One node on the map. node = research node id that has to be unlocked (None: always open)."""
    assert item_exists(icon), icon
    key = f"book.pysift.sift_codex.{cat}.{eid}"
    data = {"type": "modonomicon:content", "category": f"pysift:{cat}", "id": f"pysift:{cat}/{eid}",
            "name": tr(key + ".name", en, zh), "description": tr(key + ".description", *desc) if desc[0] else "",
            "icon": {"id": icon}, "x": x, "y": y, "sort_number": x * 100 + y,
            "background": {"sprite": SPRITES + shape, "width": 26, "height": 26},
            "parents": [{"entry": f"pysift:{cat}/{p}", "line_enabled": line} for p in parents],
            "condition": {"type": "modonomicon:none"}, "marker_condition": {"type": "modonomicon:none"}}
    if node:
        data["condition"] = {"type": "modonomicon:research_node_unlocked", "node_id": node}
        if locked_tip:
            data["condition"]["tooltip"] = {"translate": tr(key + ".locked", *locked_tip)}
    wj(BOOK / f"entries/{cat}/{eid}.json", data)
    for n, page in enumerate(pages):
        page = dict(page)
        page.update({"id": f"p{n}", "sort_number": n, "condition": {"type": "modonomicon:none"}})
        if "title" in page:   # Modonomicon wants the key even when the page has no title
            page["title"] = tr(f"{key}.p{n}.title", *page["title"]) if page["title"] else ""
        en_t, zh_t = page.pop("text")
        page["text"] = tr(f"{key}.p{n}.text", en_t, zh_t) if en_t else ""
        wj(BOOK / f"entries/{cat}/{eid}/pages/p{n}.json", page)


# ------------------------------------------------------------------ research
FACTS, HOOKS, NODES = [], [], []


def unlock_by_advancement(name, advancement, toast=None):
    node = f"pysift:sift_codex/{name}"
    FACTS.append({"id": node})
    HOOKS.append({"id": node + "_hook", "fact_id": node, "trigger_type": "modonomicon:advancement",
                  "trigger_target": advancement})
    NODES.append({"id": node, "required_facts": [node], **({"toast": toast} if toast else {})})
    return node


def unlock_by_item(name, item, toast=None):
    node = f"pysift:sift_codex/{name}"
    FACTS.append({"id": node})
    HOOKS.append({"id": node + "_hook", "fact_id": node, "trigger_type": "modonomicon:item_acquired",
                  "trigger_target": {"id": item}})
    NODES.append({"id": node, "required_facts": [node], **({"toast": toast} if toast else {})})
    return node


def toast(icon, key, en, zh):
    return {"title": tr("book.pysift.sift_codex.toast.title", "Sift Codex updated", "隙浮手記更新了"),
            "description": tr(key, en, zh), "icon": {"id": icon}}


ADV = D / "pysift/advancement/codex"


def met(mob):
    """Hidden advancement: you met this creature - killed it, hit it, got hit by it or used an item on it."""
    is_mob = {"type": "minecraft:entity_properties", "entity": "this", "predicate": {"minecraft:entity_type": f"pysift:{mob}"}}
    wj(ADV / f"met_{mob}.json", {"criteria": {
        "killed": {"trigger": "minecraft:player_killed_entity", "conditions": {"entity": is_mob}},
        "hurt": {"trigger": "minecraft:player_hurt_entity", "conditions": {"entity": is_mob}},
        "hurt_by": {"trigger": "minecraft:entity_hurt_player", "conditions": {"damage": {
            "source_entity": {"minecraft:entity_type": f"pysift:{mob}"}}}},
        "touched": {"trigger": "minecraft:player_interacted_with_entity", "conditions": {"entity": is_mob}}},
        "requirements": [["killed", "hurt", "hurt_by", "touched"]]})
    return unlock_by_advancement(f"met_{mob}", f"pysift:codex/met_{mob}")


# ================================================================== 1. journey (啟程)
category("journey", 0, "minecraft:echo_shard", "The Way In", "啟程", "void_stone/polished_void_stone")
C = "journey"
entry(C, "intro", "minecraft:echo_shard", "This Codex", "這本手記", 0, 0, [
    text(("The Sift Codex", "隙浮手記"),
         "Beneath the Deep Dark lies a door that was sealed long ago. This codex collects what is known of the world behind it: "
         "**The Sift**.\n\nEntries open as you go. Meet a creature and its page fills in; pick up an "
         "[#](8a3a5e)ancient page[#]() and a piece of the old story returns.",
         "深暗之域底下有一道很久以前被封住的門。這本手記收集了門後那個世界的一切：**隙浮**。\n\n"
         "條目會隨著你的旅程打開。遇到一種生物，牠的那一頁就會補上；撿到一張[#](8a3a5e)遠古殘頁[#]()，就能拼回一段舊故事。"),
    text(None,
         "- [Getting there](entry://journey/ritual): the eight-disc ritual\n- [The Sift](entry://sift/spirit_liquid): spirit liquid and the land\n"
         "- [Bestiary](entry://bestiary/guide): who lives there\n- [Guardians](entry://bosses/guide): three bosses and their artifacts\n"
         "- [Ancient pages](entry://lore/guide): what really happened",
         "- [怎麼過去](entry://journey/ritual)：八音儀式\n- [隙浮](entry://sift/spirit_liquid)：靈液與地貌\n"
         "- [生物圖鑑](entry://bestiary/guide)：誰住在那裡\n- [守護者](entry://bosses/guide)：三隻 Boss 與牠們的神器\n"
         "- [遠古殘頁](entry://lore/guide)：當年究竟發生了什麼")],
      desc=("Start here", "從這裡開始"))
entry(C, "singer", "pysift:singer_spawn_egg", "Calling a Singer", "召喚歌者", 2, 0, [
    text(("The horn at the frame", "門框前的號角"),
         "Find the great frame of **reinforced deepslate** in an Ancient City. Within 16 blocks of it, blow a **goat horn**: "
         "a **Singer** claws its way out of the ground in front of you and stays there, listening.\n\n"
         "Singers have no eyes. They talk, and keep their world together, by singing.",
         "在遠古城市找到那座**強化深板岩**的大門框。在它 16 格內吹響**山羊角**：一隻**歌者**會從你面前的地底爬出來，"
         "然後站在原地聽著。\n\n歌者沒有眼睛。牠們靠歌聲說話，也靠歌聲維持自己的世界。"),
    entity("pysift:singer", "Hold an echo shard and use it on the Singer to begin.", "手持迴音碎片右鍵歌者，儀式就會開始。")],
      parents=["intro"])
entry(C, "ritual", "minecraft:jukebox", "The Eight Discs", "八音儀式", 4, 0, [
    text(("Eight resonant jukeboxes", "八個共鳴唱片盒"),
         "The Singer calls two **Echo Golems**, who set eight **Resonant Jukeboxes** in a row before the frame. "
         "Each jukebox shows a faint beam in the colour of the disc it wants.\n\nFill them from left to right, in rainbow order:",
         "歌者會叫來兩隻**迴音傀儡**，把八個**共鳴唱片盒**排在門框前。每個唱片盒都有一道淡淡的光柱，顏色就是它想要的唱片。"
         "\n\n由左到右，照彩虹的順序放："),
    text(None,
         "1. [#](e0413a)Pigstep[#]() - bastions\n2. [#](f08a2a)Relic[#]() - trail ruins\n3. [#](c9a800)Precipice[#]() - trial chambers\n"
         "4. [#](4f9a1f)Creator[#]() - ominous vaults\n5. [#](3d8bff)5[#]() - ancient cities\n6. [#](4b3fc0)Otherside[#]() - strongholds\n"
         "7. [#](a050e0)13[#]() - dungeons\n8. [#](d0559c)Tears[#]() - ghasts",
         "1. [#](e0413a)Pigstep[#]()：堡壘遺跡\n2. [#](f08a2a)Relic[#]()：古道遺跡\n3. [#](c9a800)Precipice[#]()：試煉密室\n"
         "4. [#](4f9a1f)Creator[#]()：不祥寶庫\n5. [#](3d8bff)5[#]()：遠古城市\n6. [#](4b3fc0)Otherside[#]()：要塞\n"
         "7. [#](a050e0)13[#]()：地牢\n8. [#](d0559c)Tears[#]()：地獄幽靈"),
    text(("The song", "那首歌"),
         "When all eight are in, the jukeboxes play the scale one by one and the Singer sings along. "
         "The beams meet in the frame and the door to The Sift opens.\n\nThe jukeboxes are the key: break any one and the door closes again.",
         "八張放滿後，唱片盒會由左到右奏出八音，歌者跟著唱。八道光柱匯聚到門框中央，通往隙浮的門就打開了。\n\n"
         "唱片盒就是門的鑰匙：打破任何一個，門就會再次關上。")],
      parents=["singer"])
entry(C, "discord", "minecraft:sculk", "A Wrong Note", "走調", 6, -1, [
    text(("Out of tune", "放錯的那一格"),
         "A disc fits in any jukebox. Put one in the wrong place and that note plays flat.\n\n"
         "The door **tears**. It flickers, dark sculk bursts out across the floor, and the Singer sings the melody "
         "*backwards* to force it shut. The discs are thrown out and you must start again.",
         "唱片放進哪個盒子都行。放錯一張，那一格就會走調。\n\n門會被**撕開**：它劇烈閃爍，深色的幽匿從門前爆開蔓延，"
         "歌者只好把旋律*倒過來唱*，硬把門闔上。唱片全部彈出來，得重新放一次。"),
    text(None, "*This is not the first time it has happened.*", "*這不是第一次發生這種事。*")],
      parents=["ritual"], shape=GRAY)
entry(C, "arrival", "pysift:spirit_liquid_bucket", "Arrival", "抵達", 6, 1, [
    text(("Through the door", "穿過門之後"),
         "You arrive on a Sift portal of the biome you land in. The violet pools are **spirit liquid**: touching it drains your "
         "health and leaves you with **Soul Deprivation**.\n\nCraft a **Soul Antidote** before you go.",
         "你會抵達落點生態域的隙浮傳送門上。那些紫色的池子是**靈液**：碰到會抽走血量，並留下**靈魂剝奪**。\n\n出發前先做好**靈魂解藥**。"),
    recipe("crafting", "pysift:soul_antidote", None, "Cures Soul Deprivation.", "解除靈魂剝奪。")],
      parents=["ritual"])
entry(C, "way_home", "pysift:homeward_stone", "The Way Home", "回家的路", 8, 1, [
    text(("Leaving The Sift", "離開隙浮"),
         "There are no Ancient Cities in The Sift. To open a door back, build a closed frame of **Soul Crystal Blocks** and use an "
         "**echo shard** on it.\n\nOr hold a **Homeward Stone** for 3 seconds to return to your overworld spawn.",
         "隙浮裡沒有遠古城市。想開一道回去的門，用**靈魂晶塊**蓋一個封閉的框架，再拿**迴音碎片**右鍵它。\n\n"
         "或者按住**回程符石** 3 秒，直接回到主世界的重生點。"),
    recipe("crafting", "pysift:homeward_stone", "pysift:soul_compass"),
    text(("Soul Compass", "靈魂羅盤"),
         "In The Sift the needle points at the current target: one of the three boss arenas, or the nearest ruins. "
         "Sneak and use it to switch.",
         "在隙浮裡，指針會指向目前的目標：三座 Boss 競技場之一，或最近的遺跡。蹲下右鍵切換目標。")],
      parents=["arrival"])

# ================================================================== 2. the Sift (隙浮)
category("sift", 1, "pysift:red_sculk", "The Sift", "隙浮", "soul_willow/soul_willow_planks")
C = "sift"
entry(C, "spirit_liquid", "pysift:spirit_liquid_bucket", "Spirit Liquid", "靈液", 0, 0, [
    text(("The blood of The Sift", "隙浮的血"),
         "Where spirit liquid flows, everything is alive and singing. It keeps the sculk red and the Singers furred.\n\n"
         "Our bodies cannot take that many souls: it **drains your health** and causes **Soul Deprivation**. "
         "A full set of Siftite armour halves the drain.",
         "靈液流過的地方，萬物都活著、都會唱歌。它讓幽匿保持紅色，讓歌者保有毛髮。\n\n"
         "主世界的身體承受不了這麼濃的靈魂：碰到會**抽走血量**並造成**靈魂剝奪**。整套隙浮金盔甲可以讓抽走的血量減半。"),
    spotlight("pysift:soul_antidote", "Drink it to cure Soul Deprivation.", "喝下就能解除靈魂剝奪。")],
      desc=("What the violet pools are", "紫色池子是什麼"))
entry(C, "red_sculk", "pysift:red_sculk", "Red Sculk", "赤紅幽匿", 2, -1, [
    text(("Sculk is from here", "幽匿屬於這裡"),
         "Sculk is **native to The Sift**. Healthy sculk is red and glows, and it listens, because everything here talks by sound. "
         "It grows on the ground around the spirit pools.\n\nThe blue sculk of the Deep Dark is the same thing, **starved and rotting**.",
         "幽匿是**隙浮原生的生命**。健康的幽匿是紅色的、會發光，而且會「聽」，因為這裡的一切都靠聲音溝通。牠長在靈液池周圍的地面上。"
         "\n\n深暗之域那種藍色的幽匿其實是同一種東西，只是**餓壞了、正在腐爛**。"),
    spotlight("pysift:red_sculk", "Only silk touch keeps it.", "只有絲綢之觸挖得下來。")],
      parents=["spirit_liquid"])
entry(C, "rifts", "minecraft:sculk", "Wild Rifts", "野外裂隙", 4, -1, [
    text(("Where the rot comes in", "腐爛從這裡進來"),
         "Small rift portals stand alone in the wild. Around every one of them the red sculk has turned **blue**: "
         "close to the rift it is all blue, further out red and blue mix, and at the edge only red remains.",
         "野外有一些孤零零的小型裂隙傳送門。每一道的周圍，赤紅幽匿都變成了**藍色**：門邊全是藍的，往外紅藍交錯，最外圈才只剩紅色。"),
    text(None,
         "Air from the overworld has no souls in it. It pours in through the rifts, and the sculk it touches starves.\n\n"
         "*The Sift is not spreading into our world. Our world is spreading into it.*",
         "主世界的空氣裡沒有靈魂。它從裂縫倒灌進來，碰到的幽匿就餓死了。\n\n*不是隙浮在感染我們的世界，是我們的世界在感染隙浮。*")],
      parents=["red_sculk"], shape=GRAY)
BIOMES = [   # (id, icon, en, zh, text en, text zh)
    ("willow_grove", "pysift:soul_willow_sapling", "Willow Grove", "柳絮林地",
     "Soft violet meadows under soul willows. Blubs, Nuzzles, Slabbers and Pollinators graze here; watch the ground for Bloombuds. "
     "The **Harmonizer** guards its arena in the grove.",
     "靈魂柳樹下柔軟的紫色草甸。布魯布、蹭蹭怪、泥板獸與授粉者在這裡生活；小心地上偽裝的盛開花苞。**調和者**守在林地裡的競技場。"),
    ("amber_dunes", "pysift:amber_sandstone", "Amber Dunes", "琥珀沙丘",
     "Hot amber sand, bleached sandstone and buried tombs. Scavengers hunt the wounded, Hurlers throw rocks, Trappers lay snares. "
     "The **Monarch** rules here.",
     "炎熱的琥珀沙、褪色的砂岩與埋在沙裡的古墓。清道夫專挑受傷的獵物、投擲者會丟石頭、陷阱師到處埋陷阱。這裡是**君王**的領地。"),
    ("violet_slate_abyss", "pysift:violet_capped_dark_slate", "Violet Slate Abyss", "紫晶深板岩區",
     "Dark slate under a violet crust, with Soul Crystal and charoite growing from it. Echo Golems gather crystals for the Singers. "
     "The **Sculk Monstrosity** waits at its heart.",
     "紫色外殼下的深色板岩，長著靈魂晶塊與紫龍晶。迴音傀儡在這裡替歌者採集晶塊。**幽匿巨怪**就在它的中心等著。"),
    ("crimson_strata_canyon", "pysift:crimson_strata", "Crimson Strata Canyon", "赤紅沉積峽谷",
     "Deep canyons cut through red layered rock, stepping down to rivers of spirit liquid. Dartbacks and Fuseflies make it dangerous.",
     "深切進紅色層狀岩石的峽谷，一階一階往下到靈液河。飛鏢背與引信蠅讓這裡很危險。"),
    ("lullaby_hills", "pysift:crimson_vein_stone", "Lullaby Hills", "搖籃曲山丘",
     "Rolling hills of crimson vein stone, where the Echo Golems wander and the Singers sing at night.",
     "赤紅脈石組成的起伏山丘，迴音傀儡在這裡漫步，歌者在夜裡唱歌。"),
    ("soul_caldera", "pysift:ember_basalt", "Soul Caldera", "靈魂火山高原",
     "A scorched plateau of ember basalt and ash, with round soul volcanoes whose craters hold flat lakes of spirit liquid. "
     "Patina ore grows in the rift walls.",
     "由餘燼玄武岩與灰燼組成的焦黑高原，上面立著圓形的靈魂火山，火山口裡是平靜的靈液湖。裂縫的岩壁裡長著銅綠礦。"),
    ("red_zone_caves", "pysift:void_stone", "Red Zone Caves", "紅區洞穴",
     "Caves of void stone deep below everything else. Stalkers hide in the dark here.",
     "深埋在一切底下的虛黑岩洞穴。潛伏獵手藏在這裡的黑暗中。"),
]
for i, (bid, icon, en, zh, ten, tzh) in enumerate(BIOMES):
    entry(C, bid, icon, en, zh, i % 4 * 2, 2 + i // 4 * 2, [text((en, zh), ten, tzh)], parents=["spirit_liquid"], line=False)

# ================================================================== 3. bestiary (生物圖鑑)
category("bestiary", 2, "pysift:blub_spawn_egg", "Bestiary", "生物圖鑑", "crimson_strata_bricks/crimson_strata_bricks")
C = "bestiary"
entry(C, "guide", "minecraft:spyglass", "How to read this", "怎麼看這本圖鑑", 0, 0, [
    text(("Bestiary", "生物圖鑑"),
         "Each creature of The Sift has a page. Locked pages show only a shadow: **meet the creature** (fight it, get hit by it, or "
         "use something on it) and its page fills in.\n\nYou can turn the model on each page by dragging it.",
         "隙浮的每種生物都有一頁。還沒解鎖的只看得到影子：**遇到牠**（打牠、被牠打，或對牠用東西）那一頁就會補上。\n\n"
         "每一頁的模型都可以拖曳旋轉。")])
MOBS = [   # rows by home; (id, en, zh, text en, text zh)
    [("blub", "Blub", "布魯布",
      "The Sift's friendliest creature, in five variants by biome. Feed it a **Soul Crystal Block** to tame it (1 in 3). "
      "A tamed Blub fights beside you and carries dropped items back to your inventory.",
      "隙浮最友善的生物，依生態域有五種變體。餵**靈魂晶塊**有 1/3 機率馴服。馴服後會幫你打架，還會把掉落物叼回你的背包。"),
     ("nuzzle", "Nuzzle", "蹭蹭怪",
      "A gentle creature that walks up to rub its face against you, giving Regeneration and Glowing. If you hit it, it shrieks and runs.",
      "溫馴的小生物，會走過來蹭你的臉，給你生命恢復與發光。被打會尖叫逃走。"),
     ("slabber", "Slabber", "泥板獸",
      "The Sift's cattle, with a patch of soil on its back. Plant a flower there, let it grow, and shear it for more flowers. "
      "Breeds on Soul Crystal Blocks.",
      "隙浮的「牛」，背上有一塊土。在上面種一朵花，等它長大，用剪刀剪下就能收成更多花。用靈魂晶塊繁殖。"),
     ("pollinator", "Pollinator", "授粉者",
      "Walks from plant to plant and bone-meals crops and saplings. Hit one and every Pollinator nearby stings back with poison.",
      "在作物與樹苗之間走來走去，替它們施骨粉。打了一隻，附近的授粉者會一起用毒刺反擊。"),
     ("roamroot", "Roamroot", "漫遊根",
      "A slow, peaceful plant giant. Leave it alone: provoked, it stomps the ground and throws you into the air.",
      "緩慢、溫和的植物巨像。別惹牠：被激怒時會重踏地面，把人震飛。"),
     ("bloombud", "Bloombud", "盛開花苞",
      "Looks like a closed flower bud and never moves. Step within two blocks and it snaps shut on you, holding you in place.",
      "看起來是一朵閉合的花苞，完全不動。走進兩格內，它會猛然咬合，把你定在原地。")],
    [("singer", "Singer", "歌者",
      "The people of The Sift: eyeless, furred, and always singing. Blow a goat horn near one and it answers with a song that "
      "grants Resistance. Singers keep The Sift together with their voices.",
      "隙浮的原住民：沒有眼睛、全身覆毛、總是在唱歌。在附近吹山羊角，牠會唱歌回應，給你抗性提升。歌者用歌聲維持著隙浮。"),
     ("echo_golem", "Echo Golem", "迴音傀儡",
      "A neutral worker that gathers souls from soul sand and absorbs Soul Crystal Blocks, carrying one on its head for the Singers. "
      "Sign a pact with an echo shard and it brings you soul soil, soul sand and sometimes echo shards.",
      "中立的工人，從靈魂沙採集靈魂、吸收靈魂晶塊，頭頂扛著一塊要送給歌者。用迴音碎片和牠簽約，牠會帶靈魂土、靈魂沙，偶爾還有迴音碎片給你。"),
     ("sentinel", "Sentinel", "哨兵",
      "A crested ruin warrior with a heavy blade. Its charged cleave hits hard enough to **shatter a raised shield**.",
      "頭戴羽冠、手持重刃的遺跡武士。蓄力重劈強到能**擊碎舉起的盾牌**。"),
     ("stalker", "Stalker", "潛伏獵手",
      "Invisible in the dark. It circles behind you; its first strike from behind does double damage. Bring light.",
      "在暗處是隱形的。牠會繞到你背後，第一刀從背後打出雙倍傷害。帶上光源。"),
     ("tuner", "Tuner", "調音器",
      "Never attacks, keeps its distance, and fills nearby monsters with Speed and Strength. Kill it first.",
      "自己不攻擊，總是保持距離，替附近的怪物加上速度與力量。先解決牠。"),
     ("hunter", "Hunter", "獵人",
      "One of the Monarch's soldiers. Throws soul javelins from range and **marks** you, so every Sift monster nearby comes for you.",
      "君王麾下的士兵。從遠處投擲靈魂標槍，還會**標記**你，讓附近所有隙浮怪物一起追過來。")],
    [("dartback", "Dartback", "飛鏢背",
      "A shelled shooter that fires spines from its back and charges in a straight line. Sidestep the charge, and hit it "
      "from the front: its shell halves damage from behind.",
      "背甲獸，會從背上射出尖刺，也會直線衝撞。側閃躲開衝撞；從背後打只有一半傷害，所以從正面打。"),
     ("fusefly", "Fusefly", "引信蠅",
      "A flying pest that swells and **explodes** a moment after it dies. The warning ring shows the blast radius: kill it from a distance.",
      "會飛的小蟲，死後膨脹，過一下就**爆炸**。閃出來的警示環就是爆炸範圍：從遠處打死牠。"),
     ("prickle", "Prickle", "刺球",
      "A spiny creature that reflects part of every melee hit and fires a ring of spines. Use a bow.",
      "全身是刺，近戰打牠會反彈一部分傷害，還會射出一圈尖刺。用弓。"),
     ("nester", "Nester", "築巢者",
      "A heavy brood-mother that keeps calling Seedlings and Sprouts. When it dies its young go berserk.",
      "重裝的母體，不停召喚幼苗與萌芽。牠死的時候，幼體會陷入狂暴。"),
     ("seedling", "Seedling", "幼苗", "A swarm hatchling. Alone it is weak; in numbers it is not.", "蟲群幼體。單隻很弱，成群就不是了。"),
     ("sprout", "Sprout", "萌芽", "Another swarm hatchling, often called in by a Nester.", "另一種蟲群幼體，常被築巢者召喚出來。")],
    [("scavenger", "Scavenger", "清道夫",
      "A carrion hunter that goes for whoever is below half health. Its bite makes you bleed until it dies.",
      "食腐的掠食者，專挑血量不到一半的獵物。被咬會一直流血，直到牠死掉。"),
     ("hurler", "Hurler", "投擲者",
      "Tears rocks out of the ground and throws them from afar. Close the distance.",
      "從地上挖起石塊遠遠丟過來。拉近距離打牠。"),
     ("wobble", "Wobble", "搖晃怪",
      "A wobbly, silly creature that leaves a cloud of nausea behind when it dies.",
      "搖搖晃晃、有點滑稽的生物，死後會留下一團讓人反胃的迷霧。"),
     ("trapper", "Trapper", "陷阱師",
      "Another of the Monarch's servants. It throws nets and buries soul snares on the path you are about to take.",
      "君王的另一名部下。會丟網子，還會把靈魂陷阱埋在你正要走的路上。"),
     ("lootkin", "Lootkin", "掠奪精",
      "A tiny, very fast treasure goblin that flees on sight. Catch it for ores and rare Sift materials.",
      "跑得飛快、膽子很小的藏寶小鬼，一看到人就逃。抓到牠能得到礦物與稀有的隙浮材料。")],
]
ROW_NAMES = [("Willow Grove", "柳絮林地"), ("Lullaby Hills and the Abyss", "搖籃曲山丘與深板岩區"),
             ("Crimson Strata Canyon", "赤紅沉積峽谷"), ("Amber Dunes", "琥珀沙丘")]
for row, mobs in enumerate(MOBS):
    for col, (mob, en, zh, ten, tzh) in enumerate(mobs):
        node = met(mob)
        entry(C, mob, f"pysift:{mob}_spawn_egg", en, zh, 2 + col * 2, row * 2 - 3,
              [entity(f"pysift:{mob}", *ROW_NAMES[row]), text((en, zh), ten, tzh)],
              parents=["guide"], line=False, node=node, shape=PURPLE,
              locked_tip=("Meet this creature to fill in its page", "遇到這種生物，就會補上這一頁"))

# ================================================================== 4. guardians & artifacts (守護者與神器)
category("bosses", 3, "pysift:sculk_monstrosity_heart", "Guardians", "守護者", "amber_sandstone/amber_sandstone")
C = "bosses"
entry(C, "guide", "pysift:soul_compass", "The Three Guardians", "三位守護者", 0, 0, [
    text(("Guardians", "守護者"),
         "Three great creatures guard arenas in The Sift. The **Soul Compass** points to them. Each drops a **core**, used to make a "
         "weapon, and a **shard**, used to awaken it.\n\nAt half health every guardian grows stronger and calls help. Away from a fight, "
         "they heal and stay at their arena.",
         "隙浮有三隻巨大的生物守著自己的競技場，**靈魂羅盤**會指向牠們。每一隻都會掉落**核心**（做武器）與**碎片**（覺醒武器）。"
         "\n\n血量降到一半時，守護者會變強並召來幫手。脫離戰鬥後會回血、回到競技場。"),
    recipe("crafting", "pysift:summoning_sigil", "pysift:sift_altar",
           "Rematch: place an altar near an arena and use a sigil on it.", "想再打一次：把祭壇放在競技場附近，拿符印對它右鍵。")])
BOSSES = [
    ("harmonizer", "Harmonizer", "調和者", "harmonizer_core", "sonic_staff",
     "A jellyfish-like giant that keeps its distance. A cone of sound in front, a ring of sound that expands outward "
     "(jump it or stay inside it), and a slam if you get too close. It calls Fuseflies.",
     "像水母的巨大生物，總是保持距離。前方的音波錐、一圈往外擴散的音波環（跳過它，或待在內側），太靠近時會砸地。牠會召喚引信蠅。",
     "**Sonic Staff**: poke enemies from further away; hold use to chant and fire a sonic beam.",
     "**音波法杖**：用戳的，攻擊距離更遠；按住右鍵詠唱，射出音波光束。"),
    ("monarch", "Monarch", "君王", "monarch_crown", "dash_charm",
     "A caped king who fights up close: a two-hit combo, a leaping slam, a ground shockwave you can sidestep, and a spinning "
     "dash that leaves feathers which fire at you later. Its melee heals it.",
     "披著斗篷的國王，喜歡近戰：兩段連擊、跳躍砸地、可以側閃的地面衝擊波，還有迴旋衝刺，留下的羽毛之後會射向你。牠的近戰會替自己回血。",
     "**Dash Charm**: thrust both hands forward and dash.", "**衝刺護符**：雙手前推，向前衝刺。"),
    ("sculk_monstrosity", "Sculk Monstrosity", "幽匿巨怪", "sculk_monstrosity_heart", "sculk_hammer",
     "The deepest-rotted mass of sculk in The Sift. It swipes, slams, throws sculk cubes that roll after you, and grows sculk "
     "catalysts that **explode and heal it** unless you break them in time.",
     "隙浮裡腐爛得最深的一團幽匿。會橫掃、砸地、丟出追著你滾的幽匿方塊，還會長出幽匿觸媒：沒及時挖掉，觸媒就會**爆開並替牠回血**。",
     "**Sculk Hammer**: alternate left and right swings; charge it to raise biting sculk maws from the ground.",
     "**幽匿重錘**：左右輪流揮錘；蓄力後從地面長出會咬人的幽匿咬刺。"),
]
for i, (boss, en, zh, core, weapon, ten, tzh, wen, wzh) in enumerate(BOSSES):
    node = met(boss)
    entry(C, boss, f"pysift:{core}", en, zh, 2, i * 2 - 2,
          [entity(f"pysift:{boss}", scale=0.9), text((en, zh), ten, tzh),
           recipe("crafting", f"pysift:{weapon}", None, wen, wzh),
           recipe("smithing", f"pysift:{weapon}_awakening", None,
                  "Awaken it with the boss's shard at a smithing table.", "在鍛造台用 Boss 碎片覺醒它。")],
          parents=["guide"], node=node, shape=GOLD,
          locked_tip=("Find this guardian to fill in its page", "找到這位守護者，就會補上這一頁"))

# ================================================================== 5. gear (器物)
category("gear", 4, "pysift:siftite_ingot", "Craft", "器物", "void_stone/smooth_void_stone")
C = "gear"
entry(C, "siftite", "pysift:siftite_ingot", "Siftite", "隙浮金", 0, 0, [
    text(("Siftite", "隙浮金"),
         "Siftite ore hides underground in The Sift (y -40 to 40). Smelt raw siftite into ingots. "
         "A full set of Siftite armour **halves the health spirit liquid drains**.",
         "隙浮金礦藏在隙浮的地底（y -40 到 40）。粗隙浮金燒成錠。整套隙浮金盔甲可以讓**靈液抽走的血量減半**。"),
    recipe("crafting", "pysift:siftite_pickaxe", "pysift:siftite_chestplate")])
entry(C, "charoite", "pysift:charoite", "Charoite", "紫龍晶", 2, -1, [
    text(("Charoite", "紫龍晶"),
         "Grows in the Violet Slate Abyss and in soul geodes deep below. Used for the Soul Compass, Homeward Stones, "
         "Summoning Sigils and Soulite.",
         "長在紫晶深板岩區，以及地底深處的靈魂晶洞。靈魂羅盤、回程符石、召喚符印與靈髓都會用到。"),
    spotlight("pysift:charoite", "", "")], parents=["siftite"])
entry(C, "patina", "pysift:patina_ingot", "Patina", "銅綠", 2, 1, [
    text(("Patina", "銅綠"),
         "Patina ore grows in the rift walls of the Soul Caldera, weathered green near the surface. "
         "It will power the soul machines of a later age.",
         "銅綠礦長在靈魂火山高原的裂縫岩壁裡，靠近地表的已經風化成綠色。它將來會用來驅動靈魂機械。"),
    spotlight("pysift:patina_ingot", "", "")], parents=["siftite"])
entry(C, "beacon", "pysift:sift_beacon_gem", "Sift Beacon", "隙浮信標", 4, -1, [
    text(("Sift Beacon", "隙浮信標"),
         "Inlay a Sift Beacon gem into a chestplate at a smithing table. While worn, every player within 8 blocks is immune "
         "to Soul Deprivation.",
         "在鍛造台把隙浮信標寶石鑲進胸甲。穿著時，8 格內的所有玩家都免疫靈魂剝奪。"),
    recipe("crafting", "pysift:sift_beacon_gem", None)], parents=["charoite"])
entry(C, "soulite", "pysift:soulite_ingot", "Soulite", "靈髓", 6, 0, [
    text(("Soulite", "靈髓"),
         "Stronger than netherite. Forge a Soulite Ingot, then upgrade netherite gear with the Soulite Upgrade template "
         "(dropped by guardians, found in ruins).\n\nEach piece carries a guardian's power; the full set makes you immune to Soul "
         "Deprivation, and the boots walk on spirit liquid.",
         "比獄髓更強。先合成靈髓錠，再用靈髓升級模板（守護者掉落、遺跡箱子）把獄髓裝備升級。\n\n每件都帶有守護者的能力；"
         "整套免疫靈魂剝奪，靴子還能在靈液上行走。"),
    recipe("crafting", "pysift:soulite_ingot", None),
    recipe("smithing", "pysift:soulite_chestplate_smithing", None)], parents=["beacon", "patina"])
entry(C, "essence", "pysift:soul_essence", "Soul Essence", "靈魂精華", 4, 1, [
    text(("Reshaping blocks", "改變方塊型態"),
         "Use Soul Essence on a block to cycle its shape (sneak and use to choose which property). Each change costs one essence.",
         "拿靈魂精華對方塊右鍵，可以切換它的型態（蹲下右鍵選擇要改哪一項）。每改一次消耗一個精華。"),
    spotlight("pysift:soul_essence", "", "")], parents=["patina"])
entry(C, "brewing", "pysift:soul_berries", "Brewing", "釀造", 0, 2, [
    text(("Soul Berries and Gloomcaps", "靈莓與幽光菇"),
         "Soul Berries grow beside spirit liquid; Gloomcaps glow in caves. Brew them into Awkward Potions for **Soul Ward** and "
         "**Echo Sight**.",
         "靈莓長在靈液旁，幽光菇長在洞穴裡。把它們加進粗製藥水，可以釀出**靈魂守護**與**回音視界**。")],
      parents=["siftite"])

# ================================================================== 6. ancient pages (遠古殘頁)
category("lore", 5, "pysift:ancient_page_1", "Ancient Pages", "遠古殘頁", "red_sculk/red_sculk")
C = "lore"
PAGES = [   # (where, en title, zh title, [(en, zh) pages])
    ("ancient_city", "We Heard Singing", "牆後的歌聲", [
        ("We dug down past the dark stone and found a wall that hummed. Put an ear to it and you hear singing - not one voice, "
         "a thousand, all in tune. Something lives behind the wall, and it is *happy*.",
         "我們挖穿了黑色的岩層，找到一面會嗡嗡作響的牆。把耳朵貼上去，就聽得到歌聲：不是一個聲音，是上千個，全都合著音。"
         "牆後面住著什麼，而且牠們很*快樂*。"),
        ("The elders say the wall is a door, and doors can be opened. We have begun the frame.",
         "長老說那面牆是一道門，而門是可以打開的。我們已經開始砌門框了。")]),
    ("ancient_city", "The Eight Notes", "八個音", [
        ("The door answers to sound. We have learned its song: eight notes, played by eight boxes, in this order:\n\n"
         "**1 3 7 6 5 2 4 8**\n\nEach box wants its own disc. Each disc is a colour. Do not mix them up.",
         "這道門只聽聲音。我們學會了它的歌：八個音，由八個盒子奏出，順序是：\n\n**1 3 7 6 5 2 4 8**\n\n"
         "每個盒子要自己的唱片，每張唱片有自己的顏色。千萬不要放錯。")]),
    ("ancient_city", "A Wrong Note", "放錯的那一張", [
        ("Someone swapped the third disc. The song came out as **1 3 4 6 5 2 4 8**, and the door did not open - it *tore*.",
         "有人把第三張唱片放錯了。那首歌變成了 **1 3 4 6 5 2 4 8**，門沒有打開，而是被*撕開*了。"),
        ("Red things poured through, glowing, singing. One of the singers was swept in with them. Then the red things touched our "
         "air, and began to turn blue, and began to scream.",
         "紅色的東西湧了進來，會發光、會唱歌。一隻歌者也被一起捲了進來。然後那些紅色的東西碰到我們的空氣，開始變藍，開始尖叫。")]),
    ("ancient_city", "The Frame of Bones", "骨頭砌的門框", [
        ("The singer closed the door. It sang our song *backwards* until the tear sealed. We are few now.\n\n"
         "We have reinforced the frame with the only thing we have left in plenty: **our dead**. Let no one dig it out.",
         "那隻歌者把門關上了。牠把我們的歌*倒過來*唱，直到裂口闔上。我們剩下的人不多了。\n\n"
         "我們用僅剩的、數量還多的東西加固了門框：**我們的死者**。誰都不准把它挖開。"),
        ("The big blue thing that was once furred will not stop howling. Any sound sends it into a rage. "
         "We think it is guarding the door now. We think it is starving.",
         "那隻原本全身是毛的藍色大東西一直在嚎叫，任何聲音都會讓牠暴怒。我們覺得牠現在在守著這道門。我們覺得牠正在挨餓。")]),
    ("sift", "Song of the Sieve", "篩網之歌", [
        ("*(Translated from a Singer's song.)*\n\nThe liquid is our blood, the liquid is our breath. Where it flows we are warm, "
         "where it flows the red ones listen and the hills hum back.",
         "*（譯自一首歌者的歌。）*\n\n靈液是我們的血，靈液是我們的呼吸。它流到哪裡，我們就暖到哪裡；它流到哪裡，紅色的那些就聽著，山丘就跟著哼。"),
        ("We sing so the sieve holds. We sing so souls pass through and do not fall.",
         "我們唱歌，篩網才不會破。我們唱歌，靈魂才能穿過去，不會掉下來。")]),
    ("sift", "The One Who Went Away", "離開的那一位", [
        ("*(A Singer's lament.)*\n\nOne of us went through the torn door and did not come home. It sang the door shut from the other "
         "side. There is no liquid there. Its fur will fall. Its song will turn to weeping.",
         "*（一首歌者的哀歌。）*\n\n我們之中有一位穿過了被撕開的門，再也沒有回家。牠從另一邊把門唱著闔上。那裡沒有靈液。"
         "牠的毛會掉光，牠的歌會變成哭聲。"),
        ("If you meet a **mourner**, it is ours. Bring it home.", "如果你遇到一位**哀悼者**，那是我們的家人。帶牠回家。")]),
    ("sift", "Where the Rot Gets In", "腐爛的入口", [
        ("The tear never closed all the way. Small rifts remain, and through them comes *their* air - air with no souls in it. "
         "The red ones near a rift go hungry, then blue, then quiet.",
         "那道裂口從來沒有完全闔上。小小的裂縫還留著，*那邊*的空氣從裡面吹進來，那是沒有靈魂的空氣。"
         "裂縫附近的紅色生命先是餓，接著變藍，最後安靜下來。")]),
    ("boss", "The Heart of the Rot", "腐爛之心", [
        ("All the rot that came through the rifts gathered in one place, deep in the abyss, and grew into something huge. "
         "It is not one of us any more. It is the hunger itself.",
         "所有從裂縫進來的腐爛都聚到同一個地方，在深板岩區的深處，長成了一個巨大的東西。牠已經不是我們的一份子了，牠就是飢餓本身。"),
        ("Cut out the heart and the rot will stop spreading. Then, perhaps, the howling ones beyond the door can be fed, and "
         "made warm, and brought home.",
         "把那顆心挖出來，腐爛就不會再擴散。到那時，門另一邊那些嚎叫的家人，也許就能再被餵飽、再暖起來，被帶回家。")]),
]
PAGE_WHERE = {"ancient_city": ("Found in Ancient City chests", "在遠古城市的箱子裡找到"),
              "sift": ("Found in Sift ruins", "在隙浮遺跡的箱子裡找到"),
              "boss": ("Carried by the Sculk Monstrosity", "幽匿巨怪身上帶著")}
entry(C, "guide", "minecraft:paper", "Ancient Pages", "遠古殘頁", 0, 0, [
    text(("Ancient Pages", "遠古殘頁"),
         "Eight pages survive. The first four were written by the people of the Ancient City; the rest come from The Sift itself.\n\n"
         "Pick a page up and its entry opens here. Use a page in your hand to read it. Find all eight to see the whole story.",
         "留存下來的殘頁共有八張。前四張是遠古城市的人寫的，其餘的來自隙浮本身。\n\n撿起一張殘頁，這裡對應的條目就會打開；"
         "手持殘頁右鍵也能直接閱讀。集滿八張，就能看到完整的故事。")])
page_nodes = []
for i, (where, en, zh, body) in enumerate(PAGES, 1):
    item = f"pysift:ancient_page_{i}"
    node = unlock_by_item(f"page_{i}", item, toast(item, f"book.pysift.sift_codex.toast.page_{i}", f"Ancient Page: {en}",
                                                   f"遠古殘頁：{zh}"))
    page_nodes.append(node)
    pages = [text((en, zh), *body[0])] + [text(None, *b) for b in body[1:]]
    entry(C, f"page_{i}", item, f"{['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'][i - 1]}. {en}", f"其{'一二三四五六七八'[i - 1]}：{zh}",
          2 + (i - 1) % 4 * 2, -1 if i <= 4 else 1, pages, parents=["guide"] if i in (1, 5) else [f"page_{i - 1}"],
          node=node, shape=GRAY if i <= 4 else PURPLE, desc=PAGE_WHERE[where],
          locked_tip=(PAGE_WHERE[where][0], PAGE_WHERE[where][1]))
NODES.append({"id": "pysift:sift_codex/all_pages", "required_facts": [n for n in page_nodes],
              "toast": toast("minecraft:echo_shard", "book.pysift.sift_codex.toast.all_pages", "The whole story", "完整的故事")})
entry(C, "whole_story", "minecraft:echo_shard", "The Whole Story", "完整的故事", 10, 0, [
    text(("It was never an invasion", "從來都不是入侵"),
         "Sculk did not invade our world. **Our world infected The Sift.**\n\nThe ancients opened a door to a living world by song, "
         "and played one note wrong. Red, singing sculk and a Singer were swept through. Without spirit liquid they starved: "
         "the sculk rotted blue, and the Singer became a weeping **Mourner**.",
         "不是幽匿入侵了我們的世界，**是我們的世界感染了隙浮**。\n\n遠古人用歌聲打開一道通往活著的世界的門，卻彈錯了一個音。"
         "紅色、會唱歌的幽匿與一隻歌者被捲了過來。沒有靈液，牠們開始挨餓：幽匿腐爛成藍色，歌者變成了哭泣的**哀悼者**。"),
    text(None,
         "The **Warden** is a starved creature of The Sift, kin to the Singers, kept alive only by the souls it swallowed. "
         "It rages at sound because sound is what opens the door.\n\nThe rifts still leak our soulless air into The Sift, and the rot "
         "gathered into the **Sculk Monstrosity**. Stop the rot - and then, perhaps, bring them home.",
         "**監守者**是餓壞了的隙浮生物，是歌者的近親，只靠吞下去的靈魂苟活。牠對聲音暴怒，因為聲音正是開門的方法。\n\n"
         "裂縫至今仍把我們沒有靈魂的空氣灌進隙浮，那些腐爛聚成了**幽匿巨怪**。阻止腐爛，然後，也許，帶牠們回家。")],
      parents=["page_4", "page_8"], node="pysift:sift_codex/all_pages", shape="star_gold",
      locked_tip=("Find all eight pages", "集滿八張殘頁"))

wj(RESEARCH / "facts.json", FACTS)
wj(RESEARCH / "hooks.json", HOOKS)
wj(RESEARCH / "nodes.json", NODES)
wj(RESEARCH / "values.json", [])

# ------------------------------------------------------------------ ancient page items (AncientPages.java)
src = Image.open(io.BytesIO(VANILLA.read("assets/minecraft/textures/item/paper.png"))).convert("RGBA")
# paper has five tones: outline (cool, red-brown), shadow, mid parchment, light, highlight (warmer, less saturated)
ramp = ["#4a3328", "#7a5c48", "#a88c68", "#cfb88c", "#f1e8b9"]
lum = sorted({src.getpixel((x, y))[:3] for y in range(16) for x in range(16) if src.getpixel((x, y))[3]}, key=sum)
page_img = src.copy()
pix = page_img.load()
for y in range(16):
    for x in range(16):
        r, g, b, a = pix[x, y]
        if a:
            k = round(lum.index((r, g, b)) / max(1, len(lum) - 1) * (len(ramp) - 1))
            pix[x, y] = tuple(int(ramp[k][i:i + 2], 16) for i in (1, 3, 5)) + (a,)
INK = (0x2b, 0x5f, 0x66)   # sculk-teal ink: three short written lines inside the page
inside = [(x, y) for y in range(16) for x in range(16) if pix[x, y][3] and sum(pix[x, y][:3]) > 3 * 0xb0]
rows = sorted({y for _, y in inside})
for row in rows[2:-2:3][:3]:
    xs = sorted(x for x, y in inside if y == row)
    for x in xs[1:-2]:
        pix[x, row] = INK + (255,)
art_guard.save(page_img, A / "textures/item/ancient_page.png")
wj(A / "models/item/ancient_page.json", {"parent": "minecraft:item/generated", "textures": {"layer0": "pysift:item/ancient_page"}})
for i, (where, en, zh, body) in enumerate(PAGES, 1):
    wj(A / f"items/ancient_page_{i}.json", {"model": {"type": "minecraft:model", "model": "pysift:item/ancient_page"}})
    tr(f"item.pysift.ancient_page_{i}", f"Ancient Page {['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'][i - 1]}",
       f"遠古殘頁・其{'一二三四五六七八'[i - 1]}")
    tr(f"tooltip.pysift.ancient_page_{i}", en, zh)
    for n, (ben, bzh) in enumerate(body):   # the written-book text the item opens (markdown stripped)
        tr(f"book.pysift.ancient_page_{i}.page{n + 1}", ben.replace("**", "").replace("*", ""), bzh.replace("**", "").replace("*", ""))
tr("tooltip.pysift.ancient_page.use", "Use to read; it is copied into the Sift Codex", "右鍵閱讀；內容會抄進隙浮手記")
tr("tooltip.pysift.reinforced_deepslate", "Bones of the ancients are mortared into it", "裡面砌著遠古人的骨頭")
tr("tooltip.pysift.echo_shard", "It still remembers a little of the song", "它還記得一點點那首歌")
tr("message.pysift.codex.received", "You received the Sift Codex. Read it to survive The Sift!",
   "你獲得了《隙浮手記》，讀一讀，才能在隙浮活下去！")
# where pages are found: AncientPages.java adds them to the loot tables with LootTableEvents

# ------------------------------------------------------------------ recipe: book + echo shard
wj(D / "pysift/recipe/sift_codex.json", {"type": "minecraft:crafting_shapeless", "category": "misc",
    "ingredients": ["minecraft:book", "minecraft:echo_shard"],
    "result": {"id": "modonomicon:modonomicon", "components": {"modonomicon:book_id": "pysift:sift_codex"}}})
(D / "pysift/recipe/sift_guidebook.json").unlink(missing_ok=True)   # the codex replaces the written guidebook

# ------------------------------------------------------------------ lang
for lang, i in (("en_us", 0), ("zh_tw", 1)):
    f = A / f"lang/{lang}.json"
    raw = f.read_bytes().decode("utf-8-sig")
    data = json.loads(raw)
    for k, v in LANG.items():
        data[k] = v[i]
    out = json.dumps(data, ensure_ascii=False, indent=2)
    if "\r\n" in raw:
        out = out.replace("\n", "\r\n")
    f.write_bytes((out + ("\r\n" if raw.endswith("\n") else "")).encode("utf-8"))
print(f"sift codex: {len(list(BOOK.rglob('entries/*/*.json')))} entries, {len(NODES)} research nodes, {len(LANG)} strings")
