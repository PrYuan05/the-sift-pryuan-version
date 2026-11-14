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
HITBOX = {"blub": (0.8, 0.8, 1), "echo_golem": (1.4, 2.6, 1), "singer": (1.0, 2.7, 1.456), "mourner": (1.0, 2.7, 1.456), "sift_warden": (0.9, 2.9, 1), "nuzzle": (1.0, 1.3, 1),
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


KINETIC_CONDITION = [{"condition": "fabric:registry_contains", "registry": "minecraft:item", "values": ["pysift:soul_shaft"]}]


def entry(cat, eid, icon, en, zh, x, y, pages, parents=(), desc=("", ""), node=None, shape=GOLD, line=True,
          locked_tip=None, kinetic=False):
    """One node on the map. node = research node id that has to be unlocked (None: always open).
    kinetic = part of the mechanical add-on (soulpower/kinetic/KineticAddon): only loaded when its blocks are registered."""
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
    if kinetic:
        data = {"fabric:load_conditions": KINETIC_CONDITION, **data}
    wj(BOOK / f"entries/{cat}/{eid}.json", data)
    for n, page in enumerate(pages):
        page = dict(page)
        page.update({"id": f"p{n}", "sort_number": n, "condition": {"type": "modonomicon:none"}})
        if "title" in page:   # Modonomicon wants the key even when the page has no title
            page["title"] = tr(f"{key}.p{n}.title", *page["title"]) if page["title"] else ""
        en_t, zh_t = page.pop("text")
        page["text"] = tr(f"{key}.p{n}.text", en_t, zh_t) if en_t else ""
        if kinetic:
            page = {"fabric:load_conditions": KINETIC_CONDITION, **page}
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
    node = f"pysift:sift_codex/met_{mob}"
    if any(f["id"] == node for f in FACTS):   # the same creature can unlock several entries
        return node
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

# story acts 4-5 (MODDING_ROADMAP 4.7): kin, hollowing, homecoming
entry(C, "kin", "minecraft:sculk_shrieker", "Kin", "親族", 10, -1, [
    text(("The Singer knows the Warden", "歌者認得監守者"),
         "Bring a Singer near a **Warden** and it trembles. Then it turns to the Warden and sings the eight notes "
         "**backwards**, slowly - the song that once shut the door.\n\nThe Warden falls quiet: for half a minute it "
         "forgets its anger and will not hunt anyone.",
         "讓歌者靠近**監守者**，牠會開始發抖。接著牠轉向監守者，慢慢地把八音**倒過來**唱，那首曾經把門關上的歌。\n\n"
         "監守者會安靜下來：半分鐘內忘掉怒氣，不會追殺任何人。")],
      parents=["way_home"], node=unlock_by_advancement("warden_soothed", "pysift:story/warden_soothed"),
      shape=PURPLE, locked_tip=("Bring a Singer to a Warden", "帶一隻歌者去見監守者"))
entry(C, "hollowing", "pysift:mourner_spawn_egg", "Hollowing", "屍化", 10, 1, [
    text(("A Singer without souls", "沒有靈魂的歌者"),
         "Our world has no souls in its air. A Singer that stays in the Overworld starves: after about **five minutes** "
         "away from Soul Crystal Blocks and spirit liquid its fur falls out and it becomes a **Mourner**.\n\n"
         "Keep a Soul Crystal Block or some spirit liquid within six blocks and it will hold on.",
         "主世界的空氣裡沒有靈魂。待在主世界的歌者會挨餓：離開靈魂晶塊和靈液大約**五分鐘**，毛就會脫落，變成**哀悼者**。\n\n"
         "在六格內放一塊靈魂晶塊或一點靈液，牠就撐得住。"),
    text(("Bringing it back", "把牠找回來"),
         "Mourners also wander the **Deep Dark**, weeping the backwards song and dimming the light around them.\n\n"
         "Let a Mourner soak in **spirit liquid** for ten seconds and its fur grows back: it is a Singer again.",
         "**深暗之域**裡也有哀悼者在徘徊，哭著唱那首倒過來的歌，讓周圍陷入黑暗。\n\n"
         "讓哀悼者在**靈液**裡泡十秒，毛就會長回來，變回歌者。")],
      parents=["way_home"], node=met("mourner"), shape=PURPLE,
      locked_tip=("Meet a Mourner", "遇到一隻哀悼者"))
entry(C, "homecoming", "minecraft:echo_shard", "Homecoming", "回家", 12, 0, [
    text(("The Warden was one of them", "監守者原本也是牠們的一員"),
         "Soak a **Warden** in spirit liquid long enough - or lead it into The Sift itself - and its fur grows back. "
         "It becomes a **Sift Warden**: calm, furred, and no longer starving.\n\nFeed it an echo shard and it will follow you.",
         "讓**監守者**在靈液裡泡得夠久，或是把牠帶進隙浮，牠的毛就會長回來，變成**隙浮守衛**：平靜、全身覆毛、不再挨餓。\n\n"
         "餵牠一個迴音碎片，牠就會跟著你走。")],
      parents=["kin", "hollowing"], node=unlock_by_advancement("warden_cured", "pysift:story/warden_cured"),
      shape="star_gold", locked_tip=("Bring a Warden home", "帶監守者回家"))
# story part 2: the tools of the story and the finale
entry(C, "mourning_horn", "pysift:mourning_horn", "Mourning Horn", "哀悼號角", 12, -2, [
    text(("The song, for your own breath", "用你自己的氣息吹出那首歌"),
         "A goat horn carved with the octave and the kin. Blow it and it plays the eight notes **backwards**: every Warden "
         "within 24 blocks falls quiet for 30 seconds, and Mourners stop weeping. One minute to recover between songs.",
         "刻上八音與親族的山羊角。吹響時會把八音**倒過來**奏出：24 格內的監守者安靜 30 秒，哀悼者停止哭泣。每吹一次要休息一分鐘。"),
    recipe("crafting", "pysift:mourning_horn")],
      parents=["kin"], shape=PURPLE)
entry(C, "censer", "pysift:lullaby_censer", "Lullaby Censer", "搖籃曲香爐", 12, 2, [
    text(("A little Sift to carry", "一小片可以帶著走的隙浮"),
         "A lantern burning spirit liquid that hums the lullaby. Singers within **16** blocks never hollow, and Mourners within "
         "**8** slowly grow their fur back - about a minute - with no need to be soaked.",
         "燒著靈液、哼著搖籃曲的燈籠。**16** 格內的歌者不會屍化；**8** 格內的哀悼者大約一分鐘後就會長回毛，不必泡進靈液。"),
    recipe("crafting", "pysift:lullaby_censer")],
      parents=["hollowing"], shape=PURPLE)
entry(C, "finale", "pysift:sift_heart", "They Went Home", "回家", 14, 0, [
    text(("The last song", "最後一首歌"),
         "When the rot is stilled, bring a **Singer** and a **Sift Warden** to the reinforced door of an Ancient City and blow "
         "the **Mourning Horn** there.\n\nThe Singer sings the eight notes the right way round - the song the ancients got wrong.",
         "腐爛止息之後，帶著一隻**歌者**和一隻**隙浮守衛**來到遠古城市那道強化深板岩的門框前，吹響**哀悼號角**。\n\n"
         "歌者會把八音正著唱一遍：那首遠古人唱錯的歌。"),
    text(None,
         "The door remembers. The two of them go home, the sculk of the city wakes up red, and somewhere in The Sift they are "
         "waiting for you.",
         "門想起來了。牠們兩個回家了，城市裡的幽匿醒來變回紅色，而在隙浮的某處，牠們正等著你。")],
      parents=["homecoming", "mourning_horn"], node=unlock_by_advancement("homecoming", "pysift:story/homecoming"),
      shape="star_gold", locked_tip=("Still the rot, then go back to the door with a Singer and a Sift Warden",
                                     "先讓腐爛止息，再帶著歌者和隙浮守衛回到那道門"))

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
entry(C, "rot", "minecraft:sculk_vein", "The Rot Spreads", "腐爛蔓延", 6, -1, [
    text(("It is still spreading", "它還在蔓延"),
         "Red sculk near a rift slowly turns blue, one block at a time. The rot is fed by the deepest knot of it: the "
         "**Sculk Monstrosity**.\n\nDefeat it, and the rot around the rifts in this world stops - and begins, very slowly, "
         "to turn red again.",
         "裂隙附近的赤紅幽匿會一塊一塊慢慢變藍。供養這些腐爛的，是腐得最深的那一團：**幽匿巨怪**。\n\n"
         "擊敗牠，這個世界裂隙周圍的腐爛就會停止，並且非常緩慢地重新變紅。")],
      parents=["rifts"], shape=GRAY)
entry(C, "rift_seal", "pysift:rift_seal", "Sealing a Rift", "封印裂縫", 8, -1, [
    text(("Close the door behind you", "把身後的門關上"),
         "Use a **Rift Seal** on a portal in The Sift: the rift closes, the rot within twelve blocks stops at once and slowly "
         "turns red again - even while the Sculk Monstrosity still lives.\n\nEvery door you open here is a rift, too.",
         "對隙浮裡的傳送門使用**封印石**：裂隙關閉，12 格內的腐爛立刻停止，並且慢慢變回紅色，就算幽匿巨怪還活著也一樣。\n\n"
         "你在這裡打開的每一道門，也都是一道裂縫。"),
    recipe("crafting", "pysift:rift_seal")],
      parents=["rot"], shape=PURPLE)
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
     "Patina ore grows in the rift walls.\n\nThe cone slopes are **Rust Blackstone**, iron-rich scoria. The crater lake breathes "
     "out a damp, soul-laden steam, and the moisture rusts the iron in the stone: the higher up the cone, the rustier. Rust "
     "Blackstone near spirit liquid keeps rusting, one stage at a time. Scrape a stage off with an axe, or seal it with "
     "honeycomb to keep it as it is. The rustiest blocks grind into iron nuggets in a Soul Grinder.",
     "由餘燼玄武岩與灰燼組成的焦黑高原，上面立著圓形的靈魂火山，火山口裡是平靜的靈液湖。裂縫的岩壁裡長著銅綠礦。\n\n"
     "火山錐的山坡是**鏽黑石**，富含鐵的火山渣。火山口的靈液湖冒出帶著靈魂的濕氣，濕氣讓石頭裡的鐵生鏽：越往山上越鏽。"
     "放在靈液附近的鏽黑石會一階一階繼續鏽下去；用斧頭可以刮掉一階鏽，用蜂巢封住就會保持原樣。最鏽的鏽黑石放進靈魂研磨機，"
     "能磨出鐵粒。"),
    ("withered_hollows", "pysift:dark_slate", "Withered Hollows", "枯竭窟",
     "The first caves under the ground, cut off from the spirit liquid: narrow cracks like the joints of a dry limestone, grey "
     "floors, rotten blue sculk and a few thin columns. Wind whistles through the cracks. Stalkers and Hunters lurk, and "
     "now and then a Mourner sits weeping.",
     "地底最淺的洞穴，和靈液隔絕：像乾燥石灰岩節理的窄長裂縫、灰色的地面、腐爛的藍色幽匿和幾根細細的石柱。"
     "風從裂縫裡鑽過去，吹出口哨聲。潛伏獵手與獵人藏在這裡，偶爾還有一位哀悼者坐著哭。"),
    ("red_zone_caves", "pysift:crimson_vein_stone", "Red Zone Caves", "紅區洞穴",
     "The singing caves: fat winding passages like the water-cut tunnels of a great limestone cave, rose-grey floors, red sculk "
     "and orange vines. Stalkers, Pricklers and Fuseflies lurk; Tuners and Echo Golems wander through.",
     "歌聲洞穴：像大型石灰岩洞裡被水切出來的粗大蜿蜒坑道，玫瑰灰色的地面、赤紅幽匿與橘色藤蔓。"
     "潛伏獵手、刺球與引信蠅藏在這裡；調音器與迴音傀儡在其中漫步。"),
    ("resonant_vaults", "pysift:polished_void_stone", "Resonant Vaults", "共鳴穹窟",
     "Huge high halls like the great chambers of Carlsbad or Son Doong, full of rock columns, with polished floors and charoite "
     "growing from the ceiling. This is where the choir sings and the Echo Dens lie. Sentinels and Tuners keep the halls; "
     "Echo Golems bring their Singers.",
     "像卡爾斯巴德與韓松洞那種巨大高廳，滿是石柱，地面光滑，天花板上倒長著紫龍晶。合唱團在這裡唱歌，回音窟也在這一層。"
     "哨兵與調音器守著大廳；迴音傀儡帶著牠們的歌者。"),
    ("spirit_deeps", "pysift:magma_vein_slate", "Spirit Deeps", "靈液深淵",
     "Where the spirit liquid wells up: low flat chambers like flooded lake caves, floors of glowing magma veins, fields of red "
     "sculk and pools of liquid. It is alive, and far too thick for you: **bring protection** or lose your soul.",
     "靈液湧上來的地方：像灌水湖洞的低矮扁平洞室，地面是發光的熔脈，大片赤紅幽匿與一池池靈液。這裡是活的，"
     "而且對你來說太濃：**帶好防護**，不然會失去靈魂。"),
]
for i, (bid, icon, en, zh, ten, tzh) in enumerate(BIOMES):
    entry(C, bid, icon, en, zh, i % 4 * 2, 2 + i // 4 * 2, [text((en, zh), ten, tzh)], parents=["spirit_liquid"], line=False)
# the underground as a whole (v2.1.0): the Sift's blood vessels, in four layers, and the ways down
entry(C, "underground", "pysift:green_sift_vine", "The Blood Vessels", "隙浮的血管", 2, 6, [
    text(("Four layers", "四層"),
         "Under the Sift's ground runs a system of caves, and the Singers call it the **blood vessels**: the spirit liquid wells up "
         "from the deepest place and life follows it. The deeper you go, the more alive; the higher, the more it rots.\n\n"
         "**Withered Hollows** (about 26-54 blocks down), **Red Zone Caves** (54-87), then the **Resonant Vaults** and the "
         "**Spirit Deeps** (87 and below). Each takes after a real kind of cave.",
         "隙浮的地面底下是一整套洞穴，歌者叫它**血管**：靈液從最深的地方湧上來，生命跟著靈液走。越深越有生氣，越淺越腐爛。\n\n"
         "**枯竭窟**（地表下約 26–54 格）、**紅區洞穴**（54–87 格），再往下是**共鳴穹窟**與**靈液深淵**（87 格以下）。"
         "每一層都像一種真實的洞穴。"),
    text(("Ways down", "通往地底的路"),
         "The ground opens in places: **sinkholes**, funnels in the earth that narrow into a shaft and end in a small chamber about "
         "34 blocks down, with green vines on the walls. One in three has a spirit spring in its wall, falling to a small pool "
         "below. Stay out of the pool.\n\nThe layers have their own sounds and music; listen for the cracks whistling, the hall "
         "answering, the liquid breathing.",
         "地面在某些地方裂開：**天坑**是地上的漏斗口，往下收成豎井，通到約 34 格深的小洞室，井壁掛著綠藤。"
         "三分之一的天坑井壁上有靈液泉眼，一道細水落進下面的小池。別踩進池子裡。\n\n"
         "每一層都有自己的聲音與音樂：聽聽裂縫的口哨聲、大廳的回音、靈液的呼吸。"),
    spotlight("pysift:charoite_cluster",
              "Charoite grows from floors and, in the vaults and the deeps, hangs from the ceiling. Columns of the layer's own "
              "stone rise and hang between them.",
              "紫龍晶長在地面上，在穹窟與深淵裡也從天花板垂下來。每一層自己的石材長成石柱，立在地上、掛在頂上。")],
      parents=["spirit_liquid"], line=False)
# the Echo Den (§4.7): the Singers' choir hall, where echo golems are born and healthy Wardens keep the door
entry(C, "echo_den", "pysift:echo_cradle", "The Echo Den", "回音窟", 6, 4, [
    text(("The choir below", "地底的合唱"),
         "Deep under every part of The Sift lie the Echo Dens: round halls where the **Singers** gather to sing the eight notes "
         "and keep the sieve in tune. Look at the candles in a resonance room: they burn in the order of the ritual discs.",
         "隙浮每個地方的地底深處都有回音窟：**歌者**聚在圓形的大廳裡齊唱八個音，替篩網調音。看看共鳴室裡的蠟燭："
         "它們燃燒的順序，就是儀式唱片的順序。"),
    spotlight("pysift:echo_cradle",
              "In the grottoes their song rings in **Echo Cradles** until it grows a body: a new Echo Golem. Feed a cradle an echo "
              "shard to help it along.",
              "在晶洞裡，歌聲在**回音晶簇**裡迴響，直到長出身體：一隻新的迴音傀儡。餵它迴音碎片可以幫它一把。"),
    text(("The guards", "守衛"),
         "Healthy, furred Wardens - **Sift Wardens** - keep the doors and the vault. They ignore you while the Singers sing, "
         "but strike a Singer or a golem, open the chests, or break the crystals and cradles, and they wake and give chase. "
         "Their anger fades, faster while a Singer is singing nearby. An awake guard will not take an echo shard.",
         "健康、全身覆毛的監守者，也就是**隙浮守衛**，守著門口和寶庫。歌者唱歌時牠們不理你；但只要你打了歌者或傀儡、"
         "打開箱子，或打破晶體和晶簇，牠們就會醒來追你。牠們的怒氣會慢慢消退，附近有歌者在唱歌時退得更快。"
         "醒著的守衛不收迴音碎片。"),
    text(None,
         "Every minute or so, while someone is listening, the lead Singer starts the octave the right way round and the "
         "choir joins in; any awake guard falls quiet at once. A **Mourning Horn** calms them too.",
         "大約每分鐘，只要有人在聽，領唱的歌者就會把八音正著唱一遍，合唱團跟著唱；醒著的守衛會立刻安靜下來。"
         "吹**哀悼號角**也能讓牠們平靜。")], parents=["spirit_liquid"], line=False)

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
      "grants Resistance; strike a Tuning Fork and the Singers around sing a whole song together. Singers keep The Sift together "
      "with their voices.",
      "隙浮的原住民：沒有眼睛、全身覆毛、總是在唱歌。在附近吹山羊角，牠會唱歌回應，給你抗性提升；敲響調音叉，附近的歌者會一起唱完一首歌。"
      "歌者用歌聲維持著隙浮。"),
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
MOBS.append([
    ("mourner", "Mourner", "哀悼者",
     "A Singer that starved in our world: bald, blue with rot, weeping the eight notes backwards. It never attacks, but its song "
     "brings darkness. Soak it in spirit liquid to bring the Singer back.",
     "在我們的世界餓壞了的歌者：毛掉光、腐成深藍色，哭著把八音倒過來唱。牠從不攻擊，但牠的歌會帶來黑暗。泡進靈液就能把歌者找回來。"),
    ("sift_warden", "Sift Warden", "隙浮守衛",
     "A Warden that came home. Give it one echo shard and it is yours: it stays close to you, appearing at your side when "
     "you get far away. Right-click it to make it sit and wait, again to call it; sculk heals it. It **hears** monsters through walls and makes them glow but never "
     "hunts them; it **guards** you only when a monster hits you or you hit one. It keeps wild Wardens **calm**, and the blue sculk it "
     "walks over turns **red** again.",
     "回到家的監守者。給牠一個迴音碎片牠就是你的了：會緊跟著你，離太遠會直接出現在你身邊。右鍵牠會坐下等待，再右鍵叫牠跟上；餵幽匿方塊會回血。"
     "牠**聽得見**牆後的怪物並讓牠們發光，但不會自己去找牠們；只有怪物打到你、或你打了怪物時才會**出手**。"
     "牠讓野生監守者保持**平靜**，走過的藍幽匿也會變回**紅色**。")])
# v2.2 mob drops (progression/MobDrops.java): what each creature leaves and what it is for, a page of its own
DROP_NOTES = {
    "blub": ("**Blub Gel**: eat it, turn it into a slime ball, or mix 3 with sugar into **Blub Jelly** (slow falling).",
             "**布魯布凝膠**：可以吃、可以換成黏液球，3 個加糖做成**布魯布果凍**（吃了緩降）。"),
    "slabber": ("**Raw Slabber Steak**: cook it (furnace, smoker or campfire) into a steak as filling as beef. Also leather.",
                "**生泥板獸排**：用熔爐、煙燻爐或營火煮熟，跟牛排一樣飽。也會掉皮革。"),
    "nuzzle": ("**Raw Nuzzle Meat**: cook it like mutton. **Nuzzle Fluff**: 4 make white wool; an Awkward Potion with fluff brews **Regeneration**.",
               "**生蹭蹭肉**：像羊肉一樣煮熟來吃。**蹭蹭軟毛**：4 個做成白色羊毛；粗製藥水加軟毛釀成**再生藥水**。"),
    "pollinator": ("Honeycomb, and sometimes **Soul Nectar**: drink it for Soul Ward.",
                   "蜜脾，有時還有**靈魂花蜜**：喝了獲得靈魂守護。"),
    "nester": ("**Nester Egg**: fry it, or use it as an egg in cake. Also feathers.",
               "**築巢者蛋**：可以煎來吃，也能當蛋做蛋糕。也會掉羽毛。"),
    "roamroot": ("**Roamroot Tuber**: bake it like a potato. Also Soul Willow saplings.",
                 "**漫遊根塊莖**：像馬鈴薯一樣烤來吃。也會掉靈柳樹苗。"),
    "bloombud": ("Soul berries and **Bloombud Petals** (yellow dye).", "靈莓與**花苞花瓣**（做黃色染料）。"),
    "wobble": ("**Wobble Jelly**: edible, but it may make you dizzy. Or turn it into a slime ball.",
               "**搖晃凍**：能吃，但可能會頭暈；也能換成黏液球。"),
    "dartback": ("**Raw Dartback Meat** (cooked: a short burst of Resistance) and **Dartback Spines** for **Spine Arrows** (+1 damage).",
                 "**生飛鏢背殼肉**（煮熟吃了短暫抗性）與**飛鏢背棘刺**：做成**棘刺箭**（多 1 點傷害）。"),
    "prickle": ("**Prickle Quills**: arrowheads for **Spine Arrows**.", "**刺球棘**：當箭頭做**棘刺箭**。"),
    "scavenger": ("**Scavenger Fang**: one fang and 4 arrows make 4 **Bleeding Arrows**.",
                  "**清道夫獠牙**：1 顆獠牙加 4 支箭做成 4 支**放血箭**（命中流血）。"),
    "trapper": ("**Trapper Nets**: throw them to root a target in place, or pull one apart for string.",
                "**陷阱師的網**：丟出去能網住目標，也能拆成線。"),
    "hurler": ("**Hurler Rocks**: throw them yourself.", "**投石**：你也能拿來丟。"),
    "stalker": ("**Shadow Hide**: an Awkward Potion with it brews **Invisibility**; 4 make leather.",
                "**暗影皮**：粗製藥水加暗影皮釀成**隱形藥水**；4 張拼成皮革。"),
    "hunter": ("**Hunter Spearhead**: on two sticks it becomes a **Soul Javelin** you can throw and pick back up.",
               "**標槍頭**：接上兩根木棍就是可以擲出、撿回的**靈魂標槍**。"),
    "tuner": ("Amethyst shards, and rarely a **Tuning Fork**: copy a note block's pitch to another, or strike it near Singers - they "
              "sing along (low: lullaby, middle: twinkle, high: Ode to Joy), giving Regeneration and charging nearby soul conduits.",
              "紫水晶碎片，偶爾還有**調音叉**：把一個音符盒的音高抄到另一個；在歌者附近敲響，牠們會跟著唱（低音搖籃曲、中音小星星、"
              "高音快樂頌），給你再生，也替附近的靈魂導線充能。"),
    "fusefly": ("**Fuse Powder** works like gunpowder: TNT, fireworks and splash potions.",
                "**引信粉**可以代替火藥：做 TNT、煙火、飛濺型藥水。"),
}
ROW_NAMES = [("Willow Grove", "柳絮林地"), ("Lullaby Hills and the Abyss", "搖籃曲山丘與深板岩區"),
             ("Crimson Strata Canyon", "赤紅沉積峽谷"), ("Amber Dunes", "琥珀沙丘"), ("The Deep Dark", "深暗之域")]
for row, mobs in enumerate(MOBS):
    for col, (mob, en, zh, ten, tzh) in enumerate(mobs):
        node = met(mob)
        entry(C, mob, f"pysift:{mob}_spawn_egg", en, zh, 2 + col * 2, row * 2 - 3,
              [entity(f"pysift:{mob}", *ROW_NAMES[row]), text((en, zh), ten, tzh)]
              + ([text(("Drops", "掉落物"), *DROP_NOTES[mob])] if mob in DROP_NOTES else []),
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
entry(C, "sift_heart", "pysift:sift_heart", "The Sift Heart", "隙浮之心", 4, 2, [
    text(("The rot, healed", "被治好的腐爛"),
         "Drop the **Sculk Monstrosity's heart** into spirit liquid and wait: it is purified into a **Sift Heart**.\n\n"
         "Use it on a **Warden** and it becomes a Sift Warden at once; use it on a **Mourner** and the Singer comes back.",
         "把**幽匿巨怪之心**丟進靈液裡等一下，它就會被淨化成**隙浮之心**。\n\n對**監守者**使用，牠立刻變成隙浮守衛；"
         "對**哀悼者**使用，歌者就回來了。"),
    spotlight("pysift:sift_heart", "Purified in spirit liquid.", "在靈液裡淨化而成。")],
      parents=["sculk_monstrosity"], line=True, shape=PURPLE)

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
         "It builds the frames, shafts, pipes and pumps of the soul machines (see **Soul Power**); their gears are siftite.",
         "銅綠礦長在靈魂火山高原的裂縫岩壁裡，靠近地表的已經風化成綠色。靈魂機械的機殼、傳動軸、管線與泵都用銅綠打造（見「靈魂動力」）；裡面的齒輪則是隙浮金。"),
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

# ================================================================== 7. soul power (靈魂動力)
category("soul_power", 6, "pysift:siftite_gear", "Soul Power", "靈魂動力", "patina_block/patina_block")
C = "soul_power"
entry(C, "engine", "pysift:spirit_engine", "Spirit Engine", "靈液引擎", 0, 0, [
    text(("Turning souls into song", "把靈魂變成歌聲"),
         "Everything in the Sift speaks by sound, and sculk listens. A **soul signal** is that song put to work: a redstone "
         "signal (0-15) that also carries **soul pressure** (SP), enough to run machines.\n\n"
         "The Spirit Engine burns a bucket of spirit liquid (or soul essence, soul sand, soul soil) and sings at "
         "**strength 15**, giving **256 SP**. Every side but the front takes a conduit.",
         "隙浮的一切靠聲音溝通，而幽匿會聽。**靈魂訊號**就是拿來做事的歌聲：一種紅石訊號（0～15），但還帶著**靈壓**（SP），"
         "足以推動機器。\n\n靈液引擎燒一桶靈液（或靈魂精華、靈魂沙、靈魂土），送出**強度 15** 的訊號，提供 **256 SP**。"
         "除了正面，其他面都能接導線。"),
    text(("The master switch", "總開關"),
         "A **vanilla redstone signal** on the engine switches it off and holds its fuel. The same signal on a machine "
         "pauses that machine, like a locked hopper.",
         "引擎貼著**原版紅石訊號**時會關閉，燃料也暫停燃燒。機器貼著原版紅石訊號時會暫停，和漏斗被鎖住一樣。"),
    recipe("crafting", "pysift:siftite_gear", "pysift:spirit_engine")])
entry(C, "conduit", "pysift:soul_conduit", "Soul Conduit", "靈魂導線", 2, 0, [
    text(("The song in the wire", "線裡的歌聲"),
         "A soul conduit is a strand of **living red sculk vein**: it carries the song from an engine to wherever you need "
         "it. With a soul in it, it glows red. It joins on **all six sides**, so it runs up walls, across gaps and straight "
         "through the air.\n\nThe signal loses one level every **2 blocks** - about 30 blocks from an engine.",
         "靈魂導線是一段**活的赤紅幽匿脈**，把引擎的歌聲帶到你需要的地方。裡面有靈魂時，它發出紅光。它**六個方向**都能接，"
         "所以可以貼牆往上、跨過空隙、直接懸在空中。\n\n訊號每 **2 格**少一級，從引擎出發大約能傳 30 格。"),
    text(("Better redstone", "更好的紅石"),
         "To redstone parts a conduit is a signal source: dust joins it, lamps light, pistons push, repeaters and "
         "comparators read it.\n\nIt takes vanilla signals too. Put a lever, repeater, comparator, torch or redstone "
         "block **against** a conduit and the signal travels the wire - but it has **no soul**: the wire turns the "
         "**dead blue** of Overworld sculk, and machines stay still. Redstone dust cannot feed a conduit.",
         "對紅石元件來說，導線就是訊號源：紅石粉會接上來，紅石燈會亮，活塞會推，中繼器和比較器讀得到。\n\n"
         "它也收原版訊號。把拉桿、中繼器、比較器、紅石火把或紅石塊**貼著**導線，訊號就沿著線傳出去，但那訊號**沒有靈魂**："
         "導線變成主世界幽匿那種**枯死的藍色**，機器不會動。紅石粉不能把訊號送進導線。"),
    text(("What the ancients built", "遠古人造的東西"),
         "Under the great frame in every Ancient City there are rooms of pistons, dust and sensors. The ancients had seen "
         "the song-lines of the Sift and tried to build their own out of redstone. Their wires worked - and carried "
         "nothing. *A signal with no soul in it opens no door.*",
         "每座遠古城市的大門框底下，都有幾間裝滿活塞、紅石粉與感測器的房間。遠古人見過隙浮的歌聲線路，想用紅石照著做一套。"
         "他們的線路會動，卻什麼也沒帶著。*沒有靈魂的訊號，打不開任何一道門。*"),
    text(("Hiding and reaching", "藏線與接線"),
         "Right-click a conduit with **any full block** to wrap it in that block; an empty hand takes it off. A wrapped "
         "conduit still carries the signal and gives off no light.\n\n"
         "Where it meets a vanilla part the conduit grows the right end: a **collar** on lamps, pistons and hoppers, a "
         "**bend to the floor** for dust, rails and repeaters, and a thin **tendril** out to levers, buttons and torches.",
         "拿**任何完整方塊**對導線右鍵，導線就包成那個方塊的外觀；空手右鍵拆下來。包起來的導線照樣傳訊號，而且不發光。\n\n"
         "碰到原版元件時，導線會長出合適的接頭：接紅石燈、活塞、漏斗用**接環**，接紅石粉、鐵軌、中繼器會**彎到地面**，"
         "接拉桿、按鈕、紅石火把則伸出一條細細的**觸鬚**。"),
    recipe("crafting", "pysift:soul_conduit")], parents=["engine"])
entry(C, "singer", "minecraft:goat_horn", "A Singer on the Line", "線上的歌者", 0, -2, [
    text(("The song itself", "歌聲本身"),
         "A soul signal is a song, so a **Singer** can be the engine. A Singer within 3 blocks of a conduit stops, faces "
         "it and sings a whole set: the *Song of the Sieve* between three older tunes, about two and a half minutes. "
         "While it sings, that conduit is a source: **strength 15, 64 SP** - one grinder, no fuel. Then it rests for "
         "half a minute.\n\nKeep it fed: a Singer in the Overworld starves without spirit liquid or soul crystal near.",
         "靈魂訊號就是歌聲，所以**歌者**自己就能當引擎。歌者在導線 3 格內會停下來、面向導線，唱完一整套歌：《篩網之歌》"
         "穿插三首老曲子，大約兩分半鐘。牠唱歌的期間，那段導線就是訊號源：**強度 15、64 SP**，夠帶一台研磨機，不用燃料。"
         "唱完休息半分鐘。\n\n要照顧好牠：歌者在主世界，附近沒有靈液或靈魂晶塊就會挨餓。"),
    text(("The Mourner's song", "哀悼者的歌"),
         "A **Mourner** sings too - backwards. Its song runs down the wire as a signal with **no soul**: the conduit turns "
         "dead blue, lamps light, machines stay still.",
         "**哀悼者**也唱歌，只是倒著唱。牠的歌沿著導線傳出去，卻是**沒有靈魂**的訊號：導線變成枯死的藍色，紅石燈會亮，機器不會動。")],
      parents=["conduit"])
entry(C, "parts", "pysift:soul_repeater", "Repeater and Filter", "中繼器與濾波器", 4, -3, [
    text(("Soul Repeater", "靈魂中繼器"),
         "Set it into a conduit line, pointing the way the signal should go. What comes in at the back leaves the front "
         "at **strength 15** again. It never passes a signal backwards. Carrying a soul signal costs **16 SP**.",
         "串在導線中間，朝著訊號要走的方向。從背面進來的訊號，從正面出去時補回**強度 15**，而且不會倒著走。"
         "傳靈魂訊號時吃 **16 SP**。"),
    recipe("crafting", "pysift:soul_repeater"),
    text(("Soul Filter", "靈魂濾波器"),
         "A conduit carries soul signals and plain redstone signals on the same wire. The filter lets only one kind "
         "through; right-click to switch. **Red core:** soul signals only. **Blue core:** plain signals only - machines "
         "past it stay still.",
         "導線把靈魂訊號和原版紅石訊號放在同一條線上。濾波器只讓其中一種通過，右鍵切換。**紅色核心：**只過靈魂訊號。"
         "**藍色核心：**只過原版訊號，後面的機器不會動。"),
    recipe("crafting", "pysift:soul_filter")], parents=["gauge"])
entry(C, "note", "pysift:soul_note_block", "Soul Note Block", "靈魂音符盒", 6, -3, [
    text(("The eight notes", "八個音"),
         "It holds the eight notes of the door's song; right-click to step through them. It sounds once when a signal "
         "arrives: with a **soul signal** it is a Singer's voice, with a plain redstone signal only a dull knock.\n\n"
         "Line up eight of them, feed them one after another through repeaters, and you can play **1 3 7 6 5 2 4 8** "
         "at home.",
         "它裝著開門那首歌的八個音，右鍵換音。訊號到達的那一刻響一聲：帶著**靈魂訊號**時是歌者的歌聲，只有原版紅石訊號時"
         "只剩一聲悶響。\n\n排八個，用中繼器一個接一個送訊號，你就能在家裡奏出 **1 3 7 6 5 2 4 8**。"),
    recipe("crafting", "pysift:soul_note_block")], parents=["parts"])
entry(C, "sculk", "minecraft:sculk_catalyst", "Sculk on the Line", "線路上的幽匿", 2, -2, [
    text(("Old kin", "老親戚"),
         "Vanilla sculk still knows the song.\n\n"
         "**Sculk Catalyst** against a conduit: when a creature dies nearby, its soul flows into the wire - strength 15 for "
         "10 seconds, 32 SP. Enough for one fan, no fuel needed.\n\n"
         "**Sculk Shrieker** against a conduit: it shrieks while the circuit is overloaded. It calls no Warden.\n\n"
         "**Sculk Sensor**: its output is a plain signal. It travels the wire, but runs no machine.",
         "原版的幽匿還記得這首歌。\n\n"
         "**幽匿催化體**貼著導線：附近有生物死亡時，牠的靈魂流進導線，強度 15、持續 10 秒、32 SP。夠帶一台風扇，不用燃料。\n\n"
         "**幽匿尖嘯體**貼著導線：迴路過載時它會尖叫示警，不會召喚監守者。\n\n"
         "**幽匿感測器**：它的輸出是沒有靈魂的訊號，會沿著導線傳，但推不動機器。")], parents=["conduit"])
entry(C, "gauge", "pysift:soul_gauge", "Soul Gauge", "靈壓計", 4, -1, [
    text(("Reading the load", "讀取負載"),
         "Set it into a conduit line. The needle swings from green to red as the load nears the capacity. Right-click it "
         "for the signal strength and the exact numbers; a comparator reads the load (0-15).\n\n"
         "A machine's load is its full load x its signal strength / 15. Past 100% the circuit is **overloaded**: the soul "
         "signal drops to nothing, and after 5 seconds the machines tear the souls out of every creature nearby.",
         "把它串在導線中間。負載接近容量時，指針從綠區擺到紅區。右鍵看訊號強度與精確的數字；比較器讀得到負載（0～15）。\n\n"
         "機器的負載 = 滿載值 × 訊號強度 ÷ 15。超過 100% 迴路就**過載**：靈魂訊號歸零，5 秒後機器會把附近所有生物的靈魂扯出來。"),
    recipe("crafting", "pysift:soul_gauge")], parents=["conduit"])
entry(C, "grinder", "pysift:soul_grinder", "Soul Grinder", "靈魂研磨機", 4, 1, [
    text(("Grinding", "研磨"),
         "Doubles ores, breaks cobblestone into gravel and sand, bones into bone meal, and sometimes leaves a soul essence. "
         "64 SP at full signal; a weaker signal grinds slower and costs less.",
         "礦石變兩倍，鵝卵石磨成礫石再磨成沙，骨頭磨成骨粉，偶爾還多出一個靈魂精華。訊號強度 15 時吃 64 SP；訊號越弱磨得越慢，也越省。"),
    recipe("crafting", "pysift:soul_grinder")], parents=["conduit"])
entry(C, "sifter", "pysift:soul_sifter", "Soul Sifter", "靈魂淨化篩", 6, 1, [
    text(("Sifting the rot back to red", "把腐爛篩回赤紅"),
         "The craft of the ancients. While it turns, the sifter slowly turns **rotten blue sculk within 8 blocks back into "
         "red sculk**. Put sculk on its sieve to sift it red; gravel gives flint, sand gives clay, soul sand gives soul soil. "
         "96 SP at full signal; feed it from the wheel side.",
         "遠古人的工藝。轉動時，淨化篩會慢慢把 **8 格內腐爛的藍色幽匿變回赤紅幽匿**。把幽匿放上篩網就能篩紅；礫石篩出燧石、"
         "沙篩出黏土、靈魂沙篩出靈魂土。訊號強度 15 時吃 96 SP，從飛輪那一側接導線。"),
    recipe("crafting", "pysift:soul_sifter")], parents=["grinder"])
entry(C, "beams", "pysift:charoite_beam_emitter", "Charoite Beams", "紫龍晶光束", 0, 2, [
    text(("Wireless: through the air", "無線：穿過空氣"),
         "The emitter shoots a violet beam up to 32 blocks; **prisms** turn it (right-click to point them, sneak to go back). "
         "It passes glass and plants and links on the **front** of a receiver. It loses **nothing**, but it must be aimed, and it "
         "burns whatever stands in it.",
         "發射器射出最遠 32 格的紫色光束；**稜鏡**會讓它轉向（右鍵換方向、潛行右鍵往回換）。光束能穿過玻璃與花草，"
         "打中接收器的**正面**就連通。強度**不損耗**，但要瞄準，而且會灼傷站在光束裡的東西。"),
    recipe("crafting", "pysift:charoite_beam_emitter", "pysift:charoite_prism")], parents=["engine"])

entry(C, "pump", "pysift:spirit_pump", "Spirit Pump", "靈液泵", 2, 1, [
    text(("Piping spirit liquid", "用管子送靈液"),
         "Point the pump's nozzle at a spirit liquid pool and give it a soul signal: it drinks the source in front of it and sends "
         "the liquid down Spirit Pipes to your engines, which burn it when their fuel slot is empty.\n\n"
         "A pipe left open at one end **leaks**, and the ground below it rots into soul soil.",
         "把泵的吸口對著靈液池、接上靈魂訊號：它會吸走正前方的靈液源頭，沿著靈液管送給引擎；引擎燃料格空著時就燒這些靈液。\n\n"
         "只接一頭、另一頭空著的管子會**漏**，下面的地面會被汙染成靈魂土。"),
    recipe("crafting", "pysift:spirit_pump", "pysift:spirit_pipe")], parents=["engine"])

# -- the mechanical add-on (soulpower/kinetic/KineticAddon): only when Create is installed, or kinetic_addon=on
entry(C, "shafts", "pysift:soul_cogwheel", "Shafts and Cogwheels", "傳動軸與齒輪", -2, -2, [
    text(("The mechanical add-on", "機械擴充"),
         "*The Sift's own shafts and cogwheels: only with kinetic_addon=on in config/pysift.properties. Soul redstone "
         "does not need them, and with the Create mod you use Create's.*\n\n"
         "Shafts carry **rotation** along their axis and drive a machine directly, without a conduit. Cogwheels side by "
         "side drive each other and **turn the other way**. A **large cogwheel** meshes with small ones on its diagonals: "
         "the small one turns **twice as fast**.",
         "*隙浮自己的傳動軸與齒輪：只有在 config/pysift.properties 設定 kinetic_addon=on 時才出現。靈魂紅石用不到它們；"
         "裝了 Create 模組時，用 Create 的就好。*\n\n"
         "傳動軸沿著自己的軸傳遞**轉動**，不用導線就能直接帶動機器。並排的齒輪互相帶動，**方向相反**。"
         "**大齒輪**和斜角的小齒輪咬合，小齒輪轉**兩倍快**。"),
    recipe("crafting", "pysift:soul_shaft", "pysift:large_soul_cogwheel"),
    text(("Speed conflict", "轉速衝突"),
         "If two paths ask one block to turn at different speeds (or two engines disagree), the gears jam: the whole "
         "network stops and smokes until you fix it.",
         "如果兩條路要求同一個方塊轉不同的速度（或兩台引擎方向相反），齒輪就會卡住：整個網路停下來冒煙，直到你修好為止。")],
      parents=["engine"], kinetic=True)
entry(C, "crank", "pysift:soul_hand_crank", "Hand Crank", "手搖曲柄", -2, 0, [
    text(("Muscle power", "人力"),
         "Mount it on a shaft or a machine and hold right-click: 32 RPM and 96 SP, enough for one grinder or one sifter. "
         "Cranking makes you hungry.",
         "裝在傳動軸或機器的一面，按住右鍵：32 RPM、96 SP，夠帶一台研磨機或一台淨化篩。搖久了會餓。"),
    recipe("crafting", "pysift:soul_hand_crank")], parents=["engine"], kinetic=True)
entry(C, "shift", "pysift:soul_gearshift", "Clutch and Gearshift", "離合器與換向器", -4, 0, [
    text(("Redstone control", "紅石控制"),
         "Both hold two half-shafts. Give them a redstone signal (the lamp lights up): the **clutch** lets go of the half on "
         "the far side (east, south or up); the **gearshift** turns that half the other way.",
         "兩者裡面都是兩段半軸。給它紅石訊號（燈會亮）：**離合器**放開遠端那一段（東、南或上方那一頭）；**換向器**讓那一段反轉。"),
    recipe("crafting", "pysift:soul_clutch", "pysift:soul_gearshift")], parents=["shafts"], kinetic=True)
entry(C, "fan", "pysift:soul_fan", "Soul Fan", "靈魂風扇", 6, -1, [
    text(("Wind and haunting", "風與靈魂薰染"),
         "Blows creatures and items away, up to 8 blocks at full signal (a weaker signal blows less far). Put **soul fire** in the stream: "
         "items resting behind it are haunted - sand into soul sand, dirt into soul soil, torches, lanterns and campfires "
         "into their soul versions.",
         "把生物和掉落物吹走，訊號強度 15 時最遠 8 格（訊號越弱吹得越近）。在氣流裡放**靈魂火**：停在火後面的掉落物會被靈魂薰染——沙變靈魂沙、"
         "泥土變靈魂土，火把、燈籠與營火變成靈魂版本。"),
    recipe("crafting", "pysift:soul_fan")], parents=["gauge"])

entry(C, "resonance", "pysift:resonance_core", "Resonance Array", "共鳴靈陣", 8, 0, [
    text(("The ancients' craft", "遠古人的工藝"),
         "Place up to eight Resonance Pedestals around a Resonance Core, 3 blocks away on the sides and diagonals. "
         "Put a catalyst on the core, ingredients on the pedestals, and give the core a soul signal (128 SP at full signal).\n\n"
         "A running core also makes grinders and sifters within 8 blocks 50% faster.",
         "在共鳴核心周圍 3 格處（四邊與四個斜角）擺最多八個共鳴台座。核心放觸媒、台座放材料，給核心靈魂訊號（訊號強度 15 時吃 128 SP）。\n\n"
         "運轉中的核心也讓 8 格內的研磨機與淨化篩快 50%。"),
    text(("Resonances", "共鳴配方"),
         "**Amethyst shard** + 4 sculk + 4 soul essence → 2 echo shards.\n"
         "**Amethyst cluster** + 4 soul essence → 4 charoite.\n"
         "**Deepslate** + 4 bone blocks + 4 soul crystal blocks → reinforced deepslate.\n"
         "**A resonant disc** + 4 amethyst shards + 2 soul essence + 2 note blocks → 2 of that disc.",
         "**紫水晶碎片**＋4 幽匿＋4 靈魂精華 → 2 迴音碎片。\n"
         "**紫水晶簇**＋4 靈魂精華 → 4 紫龍晶。\n"
         "**深板岩**＋4 骨塊＋4 靈魂晶塊 → 強化深板岩。\n"
         "**共鳴唱片**＋4 紫水晶碎片＋2 靈魂精華＋2 音符盒 → 2 張同樣的唱片。"),
    recipe("crafting", "pysift:resonance_core", "pysift:resonance_pedestal")], parents=["sifter"])

entry(C, "drill", "pysift:soul_drill", "Soul Drill", "靈魂鑽頭", 6, 3, [
    text(("Boring through rock", "鑽穿岩石"),
         "Feed it from the back: the bit bores out the block in front and drops what an iron pickaxe would. Harder blocks "
         "take longer; a stronger signal digs faster. Bedrock and the like resist it. Keep clear of the bit.",
         "從背面接導線：鑽頭會鑽掉正前方的方塊，掉落物和用鐵鎬挖的一樣。越硬的方塊鑽越久，訊號越強鑽越快；基岩之類的方塊鑽不動。"
         "別站在鑽頭前面。"),
    recipe("crafting", "pysift:soul_drill")], parents=["grinder"])

entry(C, "gearbox", "pysift:soul_gearbox", "Soul Gearbox", "靈魂齒輪箱", -4, -2, [
    text(("Turning the corner", "轉個彎"),
         "Four bevel gears round its axis: a shaft on any of the four sides drives the other three, so the power can turn "
         "90 degrees. The shaft straight across turns the other way.",
         "軸向四周有四片傘齒輪：任何一面接進來的轉動，都會傳到另外三面，所以動力可以轉 90°。正對面那一根會反著轉。"),
    recipe("crafting", "pysift:soul_gearbox")], parents=["shafts"], kinetic=True)

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
    # ninth page (an extra, not one of the chronicle's eight): what the Singers teach in the Echo Den (§4.7)
    ("den", "The Choir Below", "地底的合唱", [
        ("*(Sung in the Echo Den.)*\n\nCome down, little ones, and learn the song. Eight notes, eight boxes, the colours in a row: "
         "**red, orange, yellow, green, blue, indigo, violet, pink**. Sing it so and the sieve stays in tune.",
         "*（在回音窟裡唱的歌。）*\n\n下來吧，孩子們，來學這首歌。八個音，八個盒子，顏色排成一列："
         "**紅、橙、黃、綠、藍、靛、紫、粉**。照著唱，篩網就不會走音。"),
        ("Our song rings in the crystals until the echo grows a body: so the golems are born, and they follow us. "
         "Our furred kin keep the door; while we sing they sleep. Wake them with a stranger's noise and they will not.",
         "我們的歌在晶體裡迴響，直到回音長出身體：傀儡就是這樣出生的，所以牠們一直跟著我們。"
         "覆毛的親族守著門口；我們唱歌時牠們就睡著。用陌生的聲響吵醒牠們，牠們就不會再睡了。")]),
    # tenth page (an extra): why the Ancient City has redstone rooms under its frame - the ancients copied the Sift's
    # song-lines (soul conduits, soulpower/SoulCircuit) in redstone and got a signal with no soul in it
    ("ancient_city", "The Wires That Do Not Sing", "不會唱歌的線", [
        ("The red things carry their song in threads. Where a thread runs, things *move*: stone turns, water climbs, doors "
         "open. We cut one out and it went grey in our hands.\n\nSo we are making our own. The red dust from the deep mines "
         "carries a spark from one end of a line to the other.",
         "那些紅色的東西把歌聲裝在細線裡。線通到哪裡，東西就*動*起來：石頭會轉、水會往上爬、門會打開。我們割下一段，"
         "它在我們手裡變成了灰色。\n\n所以我們自己做。礦坑深處的紅色粉末，能把火花從線的一頭帶到另一頭。"),
        ("Our lines work. A piston pushes, a lamp lights. But the door does not hear them. The elders say the spark is only a "
         "spark: there is **no one in it**.\n\nThe singers' threads are red because something in them is alive. Ours never "
         "will be. *We will need the song itself.*",
         "我們的線路會動。活塞會推，燈會亮。可是那道門聽不見。長老說，火花就只是火花，**裡面沒有任何人**。\n\n"
         "歌者的線是紅色的，因為裡面有活的東西。我們的永遠不會有。*我們需要的是那首歌本身。*")]),
    # pages 11-13 (extras, v2.1.0): the Singers on the underground layers - the Sift's blood vessels
    ("under", "Cracks in the Shallows", "淺處的裂縫", [
        ("*(Sung by a Singer who went up.)*\n\nAbove the singing caves the stone is dry. The liquid does not climb this high, "
         "and the cracks that run through it are old, narrow and quiet. The red ones that wandered up here turned blue and "
         "stopped listening.",
         "*（一位往上走過的歌者唱的。）*\n\n在歌聲洞穴的上面，岩石是乾的。靈液爬不到這麼高，穿過岩石的裂縫又老又窄又安靜。"
         "走到這裡的紅色生命都變藍了，也不再聆聽。"),
        ("Sometimes one of ours is here, weeping in a crack. It is not angry. It is only thirsty. **Do not sing to it from far "
         "away: bring it down to the liquid.**",
         "有時候我們的家人也在這裡，躲在裂縫裡哭。牠沒有生氣，只是渴。**不要隔得遠遠地對牠唱歌，把牠帶下去，帶到靈液旁邊。**")]),
    ("under", "The Hall That Remembers", "記得聲音的大廳", [
        ("*(A choir song, sung in the great hall.)*\n\nSing here and the hall sings back. Every note we ever sang is still "
         "in the stone, turning slowly, and the stone has grown it into columns. Walk between them softly.",
         "*（在大廳裡合唱的歌。）*\n\n在這裡唱歌，大廳會唱回來。我們唱過的每一個音都還留在石頭裡慢慢打轉，"
         "石頭把它們長成了一根根石柱。走在石柱之間要輕一點。"),
        ("The crystals above are the notes that did not fall. When a golem is born here it is only an echo that learned to "
         "walk. It will follow whoever sings it home.",
         "天花板上的晶簇，是沒有掉下來的音。傀儡在這裡出生，只是一個學會了走路的回音。牠會跟著把牠唱回家的人。")]),
    ("under", "Where the Liquid Is Born", "靈液出生的地方", [
        ("*(The oldest song the Singers know.)*\n\nDeeper than the hall the stone is warm. The liquid wells up from below in "
         "slow gulps, and everything it touches is alive, glowing, humming. This is the bottom of the sieve. This is where "
         "we are made.",
         "*（歌者最古老的一首歌。）*\n\n比大廳更深的地方，石頭是暖的。靈液從下面一口一口緩緩湧上來，它碰到的一切都是活的、"
         "發著光、哼著歌。這裡是篩網的底。我們是在這裡被造出來的。"),
        ("But it is too thick for a body from the other world. It takes the soul out of you as gently as the tide takes sand. "
         "**Come with your charms on, and leave before the song goes quiet in your chest.**",
         "可是它對另一個世界來的身體太濃了。它會把你的靈魂取走，輕得像潮水帶走沙子。"
         "**戴著護符來，在胸口的歌安靜下來以前離開。**")]),
]
PAGE_WHERE = {"ancient_city": ("Found in Ancient City chests", "在遠古城市的箱子裡找到"),
              "sift": ("Found in Sift ruins", "在隙浮遺跡的箱子裡找到"),
              "boss": ("Carried by the Sculk Monstrosity", "幽匿巨怪身上帶著"),
              "den": ("Found in the Echo Den's vault", "在回音窟的寶庫裡找到"),
              "under": ("Found in Echo Den vaults and Sift ruins", "在回音窟的寶庫與隙浮遺跡裡找到")}
entry(C, "guide", "minecraft:paper", "Ancient Pages", "遠古殘頁", 0, 0, [
    text(("Ancient Pages", "遠古殘頁"),
         "Eight pages survive. The first four were written by the people of the Ancient City; the rest come from The Sift itself.\n\n"
         "Pick a page up and its entry opens here. Use a page in your hand to read it. Find all eight to see the whole story.\n\n"
         "A ninth page, a Singers' song, is kept in the vault of an Echo Den. A tenth, about the rooms under the great "
         "frame, turns up in Ancient City chests. Three more, in which the Singers describe the layers of the underground, lie in "
         "Echo Den vaults and Sift ruins.",
         "留存下來的殘頁共有八張。前四張是遠古城市的人寫的，其餘的來自隙浮本身。\n\n撿起一張殘頁，這裡對應的條目就會打開；"
         "手持殘頁右鍵也能直接閱讀。集滿八張，就能看到完整的故事。\n\n第九張是一首歌者的歌，收在回音窟的寶庫裡。"
         "第十張寫的是大門框底下那幾間房間，偶爾出現在遠古城市的箱子裡。另外三張是歌者描述地底各層的歌，收在回音窟的寶庫與隙浮遺跡裡。")])
page_nodes = []
for i, (where, en, zh, body) in enumerate(PAGES, 1):
    item = f"pysift:ancient_page_{i}"
    node = unlock_by_item(f"page_{i}", item, toast(item, f"book.pysift.sift_codex.toast.page_{i}", f"Ancient Page: {en}",
                                                   f"遠古殘頁：{zh}"))
    if i <= 8:   # page 9 (the Echo Den's song) is an extra: not needed for the whole story
        page_nodes.append(node)
    pages = [text((en, zh), *body[0])] + [text(None, *b) for b in body[1:]]
    entry(C, f"page_{i}", item, f"{['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII'][i - 1]}. {en}", f"其{['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三'][i - 1]}：{zh}",
          *((2 + (i - 1) % 4 * 2, -1 if i <= 4 else 1) if i <= 8 else (2, 3) if i == 9 else (8, -3) if i == 10
            else (4, 3) if i == 11 else (6, 3) if i == 12 else (8, 3)), pages,
          parents=["guide"] if i in (1, 5) else ["page_5"] if i == 9 else ["page_4"] if i == 10
          else ["page_9"] if i == 11 else [f"page_{i - 1}"],
          node=node, shape=GRAY if i <= 4 else PURPLE, desc=PAGE_WHERE[where],
          locked_tip=(PAGE_WHERE[where][0], PAGE_WHERE[where][1]))
entry(C, "sherds", "pysift:octave_pottery_sherd", "Pottery Sherds", "陶器碎片", 0, 2, [
    text(("What the ancients carved", "遠古人刻下的東西"),
         "Four sherds from Ancient Cities and Sift ruins: the **gate**, the **Singer**, its **kin** the Warden, and the **octave**. "
         "Like any sherd they can be crafted into a decorated pot.\n\n"
         "Look closely at the octave: the height of each of its eight bars is the right order of the discs.",
         "遠古城市與隙浮遺跡裡有四種陶器碎片：**門扉**、**歌者**、牠的**親族**監守者，以及**八音**。和其他陶片一樣，可以拼成飾紋陶罐。\n\n"
         "仔細看八音那一片：八根長條的高度，就是唱片正確的順序。"),
    spotlight("pysift:gate_pottery_sherd", "The torn door.", "被撕開的門。"),
    spotlight("pysift:singer_pottery_sherd", "The one who closed it.", "把門關上的那一位。"),
    spotlight("pysift:kin_pottery_sherd", "Its kin, left behind as a guard.", "被留下來守門的親族。"),
    spotlight("pysift:octave_pottery_sherd", "Use it: it plays the eight jukeboxes left to right and names each disc.",
              "右鍵使用：由左到右奏出八個唱片盒的音，並說出每一盒要的唱片。"),
    text(("What the sherds make", "陶片能做什麼"),
         "**Octave + Kin** and a goat horn: the Mourning Horn. **Gate** and soul crystals: the Rift Seal. "
         "**Singer** and a soul lantern: the Lullaby Censer.",
         "**八音＋親族**加山羊角：哀悼號角。**門扉**加靈魂晶塊：封印石。**歌者**加靈魂燈籠：搖籃曲香爐。")],
      parents=["guide"], node=unlock_by_item("sherd", "pysift:octave_pottery_sherd"), shape=GRAY,
      desc=("Found in Ancient City and Sift ruin chests", "在遠古城市與隙浮遺跡的箱子裡找到"),
      locked_tip=("Find the octave sherd", "找到八音陶器碎片"))
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
entry(C, "chronicle", "pysift:ancient_chronicle", "The Ancient Chronicle", "遠古編年史", 12, 0, [
    text(("All eight, bound", "八張，裝訂成冊"),
         "Bind the eight ancient pages with a book: the whole account in one volume, in order.",
         "把八張遠古殘頁和一本書放在一起合成：整段記錄依序收在同一本書裡。"),
    recipe("crafting", "pysift:ancient_chronicle")],
      parents=["whole_story"], node="pysift:sift_codex/all_pages", shape=GOLD)

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
    tr(f"item.pysift.ancient_page_{i}", f"Ancient Page {['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII'][i - 1]}",
       f"遠古殘頁・其{['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三'][i - 1]}")
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
