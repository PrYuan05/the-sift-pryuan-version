# The Sift — PrYuan's Version

<!-- TODO before publishing: add a banner image here, e.g. ![The Sift](https://cdn.modrinth.com/...) -->

**An AI-powered Minecraft mod: a new dimension of layered strata, soul willows and glowing spirit liquid — guarded by three bosses.**

The Sift is a Fabric mod for Minecraft **26.3** that adds a whole dimension to explore: four handcrafted biomes,
round stepped mesas, spirit-liquid ponds, 26 creatures with their own AI and animations, three boss fights,
a full gear progression up to **Soulite** (beyond netherite), farming and brewing, and more than 450 blocks to build with.

It is also an experiment in **AI-powered mod development**: one creator, hand-drawn art, and AI-powered tools
for code, terrain generation and texture pipelines — see [How it was made](#how-it-was-made).

[繁體中文說明在下方](#繁體中文)

---

## At a glance

| | |
| :-- | :-- |
| 🌌 Dimension | 5 biomes, stepped mesas, ponds of Spirit Liquid, ruins with loot, underground soul geodes |
| 🐾 Creatures | 26 animated creatures, 3 bosses with enrage phases and death sequences |
| ⚔️ Progression | Siftite → boss weapons → Sift Beacon → **Soulite** gear with boss powers |
| 🧭 Helpers | Sift Codex (interactive book with a bestiary), Soul Compass, Homeward Stone |
| 🌱 Life | Soul Berries, Gloomcaps, two new potions, a tameable Blub that fights and fetches |
| 🧱 Blocks | 450+ blocks, 38 building sets, the full Soul Willow wood set |
| 🤖 Made with | hand-drawn art + AI-powered development tools |

## Requirements

| | |
| :-- | :-- |
| Minecraft | 26.3 |
| Mod loader | Fabric Loader 0.19.5 or newer |
| Java | 25 or newer |
| Required mods | [Fabric API](https://modrinth.com/mod/fabric-api), [GeckoLib](https://modrinth.com/mod/geckolib) 5.5.7 or newer, [Modonomicon](https://modrinth.com/mod/modonomicon) 2.20.0 or newer (Fabric) |

Install the mod on **both the client and the server** (it adds blocks, entities and a dimension).

## Getting there

The way into The Sift is hidden in an **Ancient City** — and it takes eight songs to open it:

1. Stand near the Reinforced Deepslate frame of the city's great portal and **blow a Goat Horn**.
   A **Singer** climbs out of the ground in front of the portal, stays there and beckons you.
2. Right-click the Singer with an **Echo Shard**. It calls two **Echo Golems** that climb out of the ground,
   carry eight **Resonant Jukeboxes** to the floor below the frame and set them down in a row, from left to right.
3. Fill the jukeboxes from left to right with these eight discs (each jukebox only takes its own; a faint beam hints the colour):

   | Colour | Disc | Where to find it |
   | :-- | :-- | :-- |
   | 🔴 Red | Pigstep | Bastion Remnant |
   | 🟠 Orange | Relic | Trail Ruins (suspicious gravel) |
   | 🟡 Yellow | Precipice | Trial Chambers vault |
   | 🟢 Green | Creator | Trial Chambers ominous vault |
   | 🔵 Blue | 5 | Ancient City (disc fragments) |
   | 🟦 Indigo | Otherside | Stronghold / Dungeon chests |
   | 🟣 Purple | 13 | Dungeon chests / a creeper killed by a skeleton |
   | 🩷 Pink | Tears | A Ghast killed by its own fireball |

4. When all eight play, the Singer sings the finale, the beams meet in the frame and it fills with a shining portal;
   the Singer waves goodbye and burrows back into the ground.
   (Without a closed frame nearby, a rift-shaped portal opens in front of the Singer instead.)
5. Stand in the portal for two seconds to travel. **The jukeboxes are the key**: break one and the portal closes
   (its disc drops back out).

**Coming home:** in The Sift, build a closed frame of **Soul Crystal** blocks and right-click it with an Echo Shard to open
a portal back to the overworld — or use a Homeward Stone.

The first time you arrive you receive the **Sift Codex**, an interactive book (Modonomicon) covering everything below,
with a bestiary that fills in as you meet each creature and eight **Ancient Pages** to collect.

**The story goes on:** a Singer that stays too long in the Overworld starves into a weeping **Mourner** (soak it in
spirit liquid to bring it back); Singers sing Wardens to rest; a Warden soaked in spirit liquid grows its red fur back
and becomes a friendly **Sift Warden**; and the rot that leaks in through the rifts stops once the Sculk Monstrosity
falls. Four ancient **pottery sherds** carry the rest of the story - and craft its tools: the **Mourning Horn**, the
**Rift Seal** and the **Lullaby Censer**. The finale takes a Singer and a Sift Warden back to the Ancient City's door.

## The dimension

A permanent dusk under a mint-coloured sky, with soft fog, gentle rolling land, cliff-edged plateaus and
large round mesas built of stepped two-block-high tiers. The terrain was shaped with AI-powered worldgen tooling
(spline-based noise, studied from — not copied from — the best terrain mods) and tuned by hand.

| Biome | Ground | What you will find |
| :-- | :-- | :-- |
| **Crimson Strata Canyon** | patchwork of canyon cap, silted strata, teal cap and mudstone; ember stone walls | irregular buttes with up to three shelves, rock pillars, a few round mesas, ember grass |
| **Violet Slate Abyss** | violet-capped dark slate | rolling hills, glowcaps, bone spires, charoite clusters, soul crystals, a boss arena |
| **Willow Grove** | crimson-capped strata over abyssal strata | soul willows (and rare giant weeping willows), the most ponds, flowers everywhere, a boss arena |
| **Amber Dunes** | amber and pale sand over bleached sandstone | ridged dunes, sandstone mesas, agave and oasis ponds, a boss arena |
| **Soul Caldera** | ember basalt and magma vein slate | a soul volcano plateau: shallow rifts with Spirit Liquid streams, round volcanoes with flat crater lakes, patina ore |

Each biome hides its own ruins with loot — a crimson **Strata Shrine**, an **Abyss Obelisk** crowned with a soul
crystal, **Willow Huts** on stilts and half-buried **Dune Tombs** — and deep below lie glowing **soul crystal geodes**.

**Lullaby Hills** (after Minecraft Dungeons II) is a grand canyon: towering walls of crimson vein stone climb in three
terraces to void-capped plateaus, and down on the canyon floor a pale marble road runs along the wall foot above a
river of Spirit Liquid lined with golden aurum ore. Echo Golems roam here.

Bigger landmarks, after the locations of Minecraft Dungeons II:
- **The Echo Den** — deep underground (y −16 to −46), a domed singing amphitheatre where Echo Golems gather, with
  tunnels branching out to crystal grottoes, resonance rooms, collapsed halls and a rare vault. Every den is laid out differently.
- **Humbler Husks** — colossal skeletons half sunk in the Amber Dunes; walk through the ribcage (achievement *Carapace
  Explorer*). Smaller fossils stick out of the sand all around.
- **Lullaby Hilltop shrines** — rings of pillars on hill tops, where two Echo Golems hum around a jukebox.

### Spirit Liquid and Soul Deprivation

The ponds are filled with glowing **Spirit Liquid**. You can swim in it and carry it in a bucket, but touching it
inflicts **Soul Deprivation**: your health is drawn down to a fifth. Take any damage while deprived and the lost
health is **shattered** — your maximum health stays locked low. Water and rain will not help;
only a **Soul Antidote** restores what was taken. Spirit Liquid that meets water hardens into **Soul Crystal**.

**Soul Antidote** (shapeless crafting): Glass Bottle + Glowcap + Golden Bloom + Echo Shard.

Mobs suffer from it too: deprived mobs burn with blue soul fire, take 30 % more damage and slowly lose health.

## Getting started: helpers

| Item | How to use | Recipe |
| :-- | :-- | :-- |
| **Sift Codex** | given on your first visit; maps of entries for the ritual, biomes, a bestiary, the guardians, gear and the ancient pages | Book + Echo Shard |
| **Soul Compass** | use it in The Sift: the needle points to a boss arena or the nearest ruins (it shows the distance). Sneak + use to switch target. If an arena has not been found yet, it points to that boss's biome | Compass + 3 Charoite + Soul Essence |
| **Homeward Stone** | hold use for 3 seconds in The Sift to return to your overworld spawn point (bed / respawn anchor) | Soul Essence + Charoite + Ender Pearl → 2 |

## Creatures

26 creatures, each with its own model, animations and behaviour — hunters that mark their prey, trappers that set
snares and throw nets, explosive Fuseflies (kill them from a distance!), stone-throwing Hurlers, Dartbacks that
shoot darts, Echo Golems that grow soul crystals, Slabbers with flowers growing on their backs, and the gentle Blub.

Blub · Bloombud · Dartback · Echo Golem · Fusefly · Hunter · Hurler · Lootkin · Nester · Nuzzle · Pollinator ·
Prickle · Roamroot · Scavenger · Seedling · Sentinel · Singer · Slabber · Sprout · Stalker · Trapper · Tuner · Wobble

Every creature has its own voice, with a sound for each of its skills; the Singers sing in a synthesised choir voice.
Each biome has its own ambience, and the three bosses have their own fight music.

### Taming the Blub

Feed a wild Blub **Soul Sand or Soul Soil** (each try has a 1 in 3 chance; hearts mean success).
A tamed Blub follows you, sits when you right-click it empty-handed, and:

- **fights for you** like a wolf — it attacks what you attack and what attacks you (never creepers or your other pets);
- **fetches items** — it picks up drops within 8 blocks and brings them straight into your inventory
  (it ignores items you threw away yourself).

Feed it more soul sand to heal it or to breed two Blubs.

### Bosses

| Boss | Arena | |
| :-- | :-- | :-- |
| **Harmonizer** | Willow Grove | a floating, many-tentacled caster of sonic cones, resonance rings and vortices |
| **Monarch** | Amber Dunes | a crowned duellist that dashes, leaps, hovers and calls a mirror Echo of itself |
| **Sculk Monstrosity** | Violet Slate Abyss | a towering brute with mega punches, sonic charges and barrages of rolling sculk cubes |

Every boss enrages below half health (stronger, faster, calls reinforcements), heals when left alone,
guards its arena, and has a three-second death sequence.

**Fighting a boss again:** craft a **Sift Altar** and place it within **48 blocks** of an arena's centre — the chat tells
you which boss it is linked to, or how far and in which direction the nearest arena is. Then right-click the altar with a
**Summoning Sigil** (don't sneak). The boss returns as long as it is not still alive near its arena.

## Progression

- **Siftite** ore deep underground (y −40 to 40) and **Charoite** clusters in the Violet Slate Abyss and soul geodes.
- **Siftite tools and armor** (between iron and diamond); the full set halves the health Spirit Liquid drains.
- Every boss drops a **core** and **shards** — each core is used once, so you will want to fight every boss more than once.
- Three boss weapons: the **Sonic Staff** (sonic boom, chain hits), the **Dash Charm** (double dash, leaves a decoy of you)
  and the **Sculk Hammer** (charged ground slam, exploding sculk tendrils). **Awaken** each one at a smithing table with the
  other two bosses' shards.
- Combine all three cores into a **Sift Beacon Gem** and inlay it into a chestplate: everyone within 8 blocks is immune to
  Soul Deprivation.
- **Soulite**, beyond netherite: forge Soulite Ingots from netherite, all three bosses' shards and charoite, then upgrade
  netherite gear with the **Soulite Upgrade** template (boss drop, ruin loot). Every piece carries a boss power — sonic chains
  on the sword, exploding sculk tendrils on the axe, glowing enemies, a decoy that saves you at low health, sculk thorns,
  walking on Spirit Liquid — and the full set makes you immune to Soul Deprivation.
- An advancement line guides you from your first step into The Sift to Soulite.
- **Patina** from the Soul Caldera (raw patina, patina ingots) builds the frames, shafts and pipes of the soul machines;
  their gears are **Siftite Gears**.
  Metal blocks for siftite and patina.
- **Soul Essence** reshapes blocks: use it on a block to switch to its next variant (sneak to pick which one).

## Soul power: soul redstone

Redstone with a soul in it. A **soul signal** is a redstone signal (0-15) that also carries soul pressure (SP), so it
can run machines. The **Spirit Engine** burns spirit liquid and sends out strength 15 with 256 SP.

| | Vanilla redstone | Soul redstone |
| :-- | :-- | :-- |
| Range | 15 blocks | about 30 (one level every 2 blocks) |
| Wiring | on top of blocks | **Soul Conduit**: joins on all six sides, runs up walls and through the air |
| Power | none | machines run on it; a stronger signal works faster |
| Wireless | none | **charoite beams** (32 blocks, no loss, turned by prisms) |

- **Both ways with vanilla.** A conduit is a redstone source: dust, lamps, pistons, repeaters and comparators read it.
  A lever, repeater, comparator, torch or redstone block against a conduit sends its signal down the wire - but that
  signal has no soul, so machines do not run on it (the wire turns the dead blue of Overworld sculk).
- **Control.** A vanilla signal on a machine pauses it; on the engine it switches the engine off.
- **Hidden wiring.** Right-click a conduit with any full block to wrap it in that block (empty hand takes it off).
  Small parts that do not touch the conduit - levers, buttons, torches - are reached by a thin tendril.
- **Sculk joins in.** A Sculk Catalyst against a conduit feeds it for 10 seconds when a creature dies nearby; a Sculk
  Shrieker against a conduit shrieks when the circuit is overloaded.
- **Machines:** Soul Grinder, Soul Sifter (sifts the rot out of blue sculk), Soul Drill, Soul Fan, Spirit Pump,
  Resonance Array. The **Soul Gauge** shows the load; an overloaded circuit burns the souls around it.

Shafts and cogwheels are not part of the base game any more. With the Create mod, The Sift is meant to add abilities on
top of Create's own kinetics (spec: `docs/CREATE_ADDON.md`; waiting for a Create release for this Minecraft version).
The Sift's own shafts and cogwheels remain as a test layer behind `kinetic_addon=on` in `config/pysift.properties`.
See the Soul Power chapter of the Sift Codex.

## Farming and brewing

| | |
| :-- | :-- |
| **Soul Berry Bush** | grows only with Spirit Liquid within 4 blocks, glows brighter as it ripens; right-click when ripe for 2–3 Soul Berries. Found wild beside spirit ponds |
| **Soul Berries** | food; eating one grants a few seconds of Soul Ward |
| **Gloomcap** | a small glowing mushroom on cave floors that slowly spreads in the dark |
| **Gloomcap Stew** | Bowl + 2 Gloomcaps + Soul Berries: filling, and grants Echo Sight |

Brew them in a vanilla **Brewing Stand** (Awkward Potion as the base; Redstone extends, Gunpowder and Dragon's Breath
make splash and lingering versions):

| Ingredient | Potion | Effect |
| :-- | :-- | :-- |
| Soul Berries | **Soul Ward** (3:00 / 8:00) | complete immunity to Soul Deprivation |
| Gloomcap | **Echo Sight** (3:00 / 8:00) | hostile creatures within 32 blocks glow, with sculk sparks only you can see |

**Nine new colours**: Teal, Mint, Coral, Amber, Lavender, Crimson Rose, Soul Blue, Void and Dusk Gold. Each has its own
dye, crafted from Sift plants of that colour (teal and mint grass, coral leaves, rift-orange grass, violet grass, carapace
flowers, soul cleavers, gloomcaps, dusk blooms...), and its own wool (with slabs and stairs), carpet, concrete (with slabs
and stairs), concrete powder, terracotta, glazed terracotta, stained glass and panes - crafted just like the vanilla ones.
The new dyes also colour leather armour. Plants without a new colour of their own craft into vanilla dyes; tall plants
give two.

## Blocks

More than 450 blocks, most with several visual stages you can pick in the creative tab:

- layered strata, capped stones, slates, sandstones, marbles and ores in the dimension's palette
- **38 building sets** — every stone comes with bricks, chiseled bricks, slabs, stairs and walls (stonecutter recipes included)
- the full **Soul Willow** wood set — logs, planks, doors, trapdoors, fences, signs, hanging signs, shelves and boats
- plants, flowers and vines, many tinted by the ground beneath them

## How it was made

The Sift is an **AI-powered** project made by a single creator:

- **Art** — every texture, model and animation was drawn and made for this mod by PrYuan05, using AI-assisted tools
  along the way. Several creature designs are inspired by *Minecraft Dungeons 2*.
- **Code** — the Java code (creature AI, bosses, items, worldgen features) was written with AI-powered coding assistants
  and reviewed, play-tested and directed by PrYuan05.
- **World generation and tooling** — the terrain, biome, structure and texture pipelines are AI-powered Python tools
  that generate the datapack files and check every block, model and texture for consistency.

AI-powered development made it possible for one person to build a dimension of this size; every design decision —
what goes in, how it looks and how it plays — was made by a human.

## FAQ

**Does it work with Forge / NeoForge?** No, Fabric only.

**Can I add it to an existing world?** Yes. The dimension is generated the first time you enter it.

**My Sift Altar does nothing.** Place it within 48 blocks of an arena's centre (the chat message after placing it tells you),
use the Summoning Sigil without sneaking, and make sure the arena's original boss is no longer alive.

**Can I use it in a modpack?** Yes — the mod is MIT-licensed. A link back to this page is appreciated.

## Links

- Source code and issue tracker: https://github.com/PrYuan05/the-sift-pryuan-version
<!-- TODO after the first upload: add the Modrinth and CurseForge page links here -->

## Credits & license

Made by **PrYuan05** — hand-drawn art, AI-powered development.
Released under the [MIT License](LICENSE).
Sound sources and music are credited in [`sounds/CREDITS.md`](src/main/resources/assets/pysift/sounds/CREDITS.md).

*Not an official Minecraft product. Not approved by or associated with Mojang or Microsoft.*

---

## 繁體中文

**一款 AI-powered 的 Minecraft 模組：層層地層、靈魂柳與發光靈液交織的全新維度，由三隻 Boss 鎮守。**

The Sift（篩靈界）是 Minecraft **26.3** 的 Fabric 模組，新增一整個可以探索的維度：五個生態域、層層內縮的圓台地形、
靈液池塘、26 種擁有專屬 AI 與動畫的生物、三場 Boss 戰、一路升級到**靈髓**（比獄髓更強）的裝備、種植與釀造，以及 450 種以上的建築方塊。

這也是一次 **AI-powered 模組開發**的實驗：一位創作者、親手繪製的美術，加上 AI-powered 的程式、地形生成與貼圖流程工具（見〈製作方式〉）。

### 一覽

| | |
| :-- | :-- |
| 🌌 維度 | 4 個生態域、階梯圓台、靈液池塘、附戰利品的遺跡、地底靈魂晶洞 |
| 🐾 生物 | 26 種有動畫的生物、3 隻會狂暴並有死亡演出的 Boss |
| ⚔️ 進度 | 篩金石 → Boss 武器 → 篩靈信標 → 帶有 Boss 能力的**靈髓**裝備 |
| 🧭 上手輔助 | 隙浮手記（附生物圖鑑的互動書）、靈魂羅盤、回程符石 |
| 🌱 生活 | 靈莓、幽光菇、兩種新藥水、會打架和撿東西的布魯布 |
| 🧱 方塊 | 450 種以上、38 組建材、完整靈魂柳木組 |
| 🤖 製作 | 親手繪製的美術 ＋ AI-powered 開發工具 |

### 需求
- Minecraft 26.3、Fabric Loader 0.19.5 以上、Java 25 以上
- 前置模組：Fabric API、GeckoLib 5.5.7 以上、Modonomicon 2.20.0 以上（Fabric 版）
- 用戶端與伺服器都要安裝

### 如何前往
通往篩靈界的路藏在**遠古城市**裡，要八首歌才能開啟：

1. 在遠古城市的強化深板岩巨口附近**吹響山羊角**，會有一隻**歌者**從傳送門前方的地底爬出來，站在原地向你招手。
2. 手持**迴音碎片**右鍵歌者：它會召喚兩隻**迴音傀儡**從地底爬出，把 8 個**共鳴唱片盒**搬到框架下方的地面，由左到右排成一列。
3. 由左到右依序放進下面這 8 張唱片（每個唱片盒只收自己那一張，淡淡的光柱會提示顏色）：

   | 顏色 | 唱片 | 取得地點 |
   | :-- | :-- | :-- |
   | 🔴 紅 | Pigstep | 堡壘遺跡 |
   | 🟠 橙 | Relic | 古跡廢墟（可疑的礫石） |
   | 🟡 黃 | Precipice | 試煉密室的寶庫 |
   | 🟢 綠 | Creator | 試煉密室的不祥寶庫 |
   | 🔵 藍 | 5 | 遠古城市（唱片碎片） |
   | 🟦 靛 | Otherside | 要塞／地牢的箱子 |
   | 🟣 紫 | 13 | 地牢的箱子／被骷髏射死的苦力怕 |
   | 🩷 粉 | Tears | 被自己火球打死的地獄惡魂 |

4. 8 張都放好時，歌者唱出終曲，光柱匯聚到框架中，填滿發光的傳送門（附近沒有封閉框架時，會在歌者前方開出裂隙型傳送門）；歌者揮手道別後鑽回地底離開。
5. 站進傳送門兩秒即可傳送。**唱片盒就是門的鑰匙**：打破任一個，門就會關閉，唱片會掉出來。

**回家的路**：在篩靈界用**靈魂晶塊**蓋一個封閉框架，手持迴音碎片右鍵框架，就能開出回主世界的傳送門；也可以用回程符石。

第一次抵達時會獲得互動式的**《隙浮手記》**（Modonomicon），介紹下面所有內容；生物圖鑑會隨著你遇到的生物補上，還有 8 張**遠古殘頁**可以收集。

**故事還沒結束**：在主世界待太久的歌者會餓成哭泣的**哀悼者**（泡進靈液就能變回來）；歌者會唱歌安撫監守者；監守者泡在靈液裡會長回赤紅的毛，變成友善的**隙浮守衛**；擊敗幽匿巨怪後，從裂隙滲進來的腐爛就會停止。四種遠古**陶器碎片**刻著剩下的故事，也能做成故事的道具：**哀悼號角**、**封印石**、**搖籃曲香爐**。終章要帶著歌者和隙浮守衛回到遠古城市的門框前。

### 維度與生態域
永恆的黃昏、薄荷色天空、淡淡的霧，平緩起伏的大地上有懸崖台地，以及一座座每層 2 格高、逐層內縮的大型圓台。
地形用 AI-powered 的世界生成工具打造（以 spline 雜訊為基礎，參考但不複製優秀的地形模組），再由人工調整。

| 生態域 | 地表 | 特色 |
| :-- | :-- | :-- |
| **赤紅沉積峽谷** | 峽谷覆蓋岩、淤積地層岩、青色覆蓋岩與條紋泥岩交錯；餘燼石崖壁 | 最多三層平台的不規則台地、石柱、少量圓形台地、餘燼草 |
| **紫晶深板岩區** | 紫晶覆蓋深色板岩 | 起伏丘陵、螢光菇、骨刺、紫龍晶簇、靈魂晶塊、Boss 競技場 |
| **柳絮林地** | 赤紅覆蓋地層岩、深淵地層岩 | 靈魂柳與罕見的巨型垂柳、最多池塘、滿地花草、Boss 競技場 |
| **琥珀沙丘** | 琥珀沙、淺沙、漂白砂岩 | 稜線沙丘、砂岩圓台、龍舌蘭與綠洲池塘、Boss 競技場 |
| **靈魂火山高原** | 餘燼玄武岩、熔脈板岩 | 噴發靈魂的火山高原：有靈液細流的淺裂谷、湖面平整的圓形火山口湖、銅綠礦 |

每個生態域都藏著自己的遺跡與寶箱：赤紅的**地層神殿**、頂著靈魂晶塊的**深淵方尖碑**、架在高腳上的**靈柳小屋**、半埋在沙裡的**沙丘古墓**；地底深處還有會發光的**靈魂晶洞**。

**搖籃曲山丘**（參考 Minecraft Dungeons II）是一座大峽谷：赤紅脈石的高聳地形牆分三層階梯爬上虛黑覆蓋的台地；谷底的牆腳有一條灰白大理石道路，再往下一階是金岩礦河岸圍著的靈液河。迴音傀儡在這裡出沒。

參考 Minecraft Dungeons II 的地點，還有幾個大型地標：
- **迴音穴**：地底深處（y −16～−46）的圓頂歌唱劇場，迴音傀儡聚在這裡唱歌；隧道往外分岔，通往晶洞、共鳴室、坍塌的大廳和稀有的寶庫，每一座的格局都不一樣。
- **迅從者殘骸**：半埋在琥珀沙丘裡的巨大骨架，可以從肋骨中間走進去（成就「甲殼探險家」）；附近沙地上到處插著小化石。
- **搖籃曲山丘神殿**：山頂上的一圈石柱，兩隻迴音傀儡圍著唱片機哼歌。

### 靈液與靈魂剝奪
池塘裡是會發光的**靈液**，可以游泳也能用桶子裝。但碰到它會陷入**靈魂剝奪**：血量被抽到原本的五分之一；
在這期間再受到任何傷害，被抽走的血量會**碎裂**消散，最大生命值被鎖住。水和雨都沒有用，只有**靈魂解藥**能把失去的血量拿回來。
靈液碰到水會凝結成**靈魂晶塊**。

**靈魂解藥**（無序合成）：玻璃瓶 + 螢光菇 + 金綻花 + 迴音碎片。

怪物也會被靈魂剝奪：身上燃起藍色靈魂火、受到的傷害 +30%，並持續流失血量。

### 上手輔助

| 物品 | 用法 | 合成 |
| :-- | :-- | :-- |
| **隙浮手記** | 第一次進入篩靈界時自動獲得；儀式、生態域、生物圖鑑、守護者、裝備與遠古殘頁的條目地圖 | 書＋迴音碎片 |
| **靈魂羅盤** | 在篩靈界右鍵：指針指向 Boss 競技場或最近的遺跡，並顯示距離；蹲下右鍵切換目標。還沒發現競技場時，會先指向那隻 Boss 的生態域 | 羅盤＋3 紫龍晶＋靈魂精華 |
| **回程符石** | 在篩靈界按住右鍵 3 秒，傳回主世界的重生點（床／重生錨） | 靈魂精華＋紫龍晶＋終界珍珠 → 2 個 |

### 生物
26 種生物，包括會標記獵物的獵人、設陷阱丟網的陷阱師、死後會爆炸的引信蠅（請從遠處解決）、投石的投擲者、
發射飛鏢的飛鏢背、頭頂長出靈魂晶塊的迴音傀儡、背上長花的泥板獸，以及溫和的布魯布。
每隻生物都有自己的聲音，每個技能也各有音效；歌者用合成的合唱嗓音唱歌。每個生態域有自己的環境音，三隻 Boss 各有戰鬥配樂。

#### 馴服布魯布
拿**靈魂晶塊**餵野生布魯布（只吃這個）（每次 1/3 機率，冒愛心就是成功）。馴服後牠會跟著你，空手右鍵讓牠坐下，而且：
- **幫你打架**：像狼一樣攻擊你打的、或打你的目標（不打苦力怕和你的其他寵物）；
- **幫你撿東西**：把 8 格內的掉落物叼回來，直接放進你的背包（你自己丟掉的東西不撿）。

再餵靈魂晶塊可以回血，兩隻也能繁殖。

#### Boss

| Boss | 競技場 | |
| :-- | :-- | :-- |
| **調和者** | 柳絮林地 | 漂浮的觸手施法者，音波錐、共鳴環與漩渦 |
| **君王** | 琥珀沙丘 | 會衝刺、跳躍、懸空，還會召喚鏡像分身的戴冠劍士 |
| **幽匿巨怪** | 紫晶深板岩區 | 巨拳、音波衝鋒與滾動幽匿方塊彈幕 |

血量低於一半會狂暴並召喚援軍，脫戰會回血、會守住競技場，死亡時有 3 秒的倒地演出。

**再次挑戰 Boss**：合成**篩靈祭壇**，放在競技場中心 **48 格內**（放下時聊天欄會告訴你連結到哪隻 Boss，或最近的競技場在哪個方向、多遠），
再手持**召喚印記**（不要蹲下）對祭壇右鍵。只要競技場原本的 Boss 已經不在，就會重新出現。

### 進度與裝備
- 地下的**篩金石礦**（y −40～40）、紫晶深板岩區與靈魂晶洞裡的**紫龍晶簇**。
- **篩金石工具與盔甲**（介於鐵和鑽石之間），穿滿一套時靈液只抽走一半的血量。
- 每隻 Boss 必掉**核心**與**碎片**；每顆核心只能用一次，所以每隻 Boss 都值得多打幾次。
- 三把 Boss 武器：**音波法杖**（音爆、連鎖攻擊）、**衝刺護符**（二段衝刺並留下你的分身）、**重錘**（蓄力砸地、會爆炸的幽匿藤蔓）；
  在鍛造台用另外兩隻 Boss 的碎片讓它們**覺醒**。
- 三種核心合成**篩靈信標寶石**，鑲嵌到胸甲上，8 格內的玩家都免疫靈魂剝奪。
- 比獄髓更強的**靈髓**：用獄髓錠、三隻 Boss 的碎片與紫龍晶鍛造靈髓錠，再用**靈髓升級模板**（Boss 掉落、遺跡寶箱）把獄髓裝備升級。
  每件都帶著 Boss 的能力：劍的音波連鎖、斧的爆炸幽匿藤蔓、讓敵人發光、瀕死時留下分身、幽匿荊棘、在靈液上行走；整套免疫靈魂剝奪。
- 一條成就線，從踏進篩靈界一路引導到靈髓。
- 靈魂火山高原的**銅綠**（粗銅綠、銅綠錠）用來做靈魂機械的機殼、導線與管線；機械裡會動的齒輪則是**隙浮金齒輪**。隙浮金與銅綠都有金屬方塊。
- **靈魂精華**能改變方塊型態：對方塊右鍵換成下一種型態（潛行可以選要換哪一種）。

### 靈魂動力：靈魂紅石

帶著靈魂的紅石。**靈魂訊號**是一種紅石訊號（0～15），但還帶著靈壓（SP），所以能推動機器。**靈液引擎**燒靈液，送出強度 15、256 SP。

| | 原版紅石 | 靈魂紅石 |
| :-- | :-- | :-- |
| 距離 | 15 格 | 約 30 格（每 2 格少一級） |
| 走線 | 鋪在方塊頂面 | **靈魂導線**：六個方向都能接，可以貼牆往上、懸在空中 |
| 動力 | 沒有 | 機器靠它運轉，訊號越強做得越快 |
| 無線 | 沒有 | **紫龍晶光束**（32 格、不損耗、靠稜鏡轉向） |

- **和原版雙向相接。** 導線對原版元件就是訊號源：紅石粉、紅石燈、活塞、中繼器、比較器都讀得到。把拉桿、中繼器、比較器、紅石火把或
  紅石塊貼著導線，訊號就沿著線傳出去；但那訊號沒有靈魂，機器不會動（導線變成主世界幽匿那種枯死的藍色）。
- **控制。** 機器貼著原版訊號會暫停；引擎貼著原版訊號會關閉。
- **藏線。** 拿任何完整方塊對導線右鍵，導線就包成那個方塊的外觀（空手右鍵拆下來）。拉桿、按鈕、紅石火把這類沒貼著導線的小元件，
  導線會長出細觸鬚去碰。
- **幽匿也接得上。** 幽匿催化體貼著導線：附近有生物死亡時，供應 10 秒的靈魂訊號。幽匿尖嘯體貼著導線：迴路過載時尖叫示警。
- **機器：** 靈魂研磨機、靈魂淨化篩（把藍色幽匿的腐爛篩掉）、靈魂鑽頭、靈魂風扇、靈液泵、共鳴靈陣。**靈壓計**顯示負載；
  過載的迴路會燒掉周圍的靈魂。

傳動軸與齒輪不再是基礎內容。裝了 Create 模組時，隙浮的定位是在 Create 自己的傳動上疊加能力（規格在 `docs/CREATE_ADDON.md`，
要等 Create 出這個 Minecraft 版本）。隙浮自己的傳動軸與齒輪保留成測試用的一層，在 `config/pysift.properties` 設定
`kinetic_addon=on` 才會出現。詳見《隙浮手記》的「靈魂動力」章。

### 種植與釀造

| | |
| :-- | :-- |
| **靈莓叢** | 4 格內有靈液才會長，越熟越亮；熟了右鍵採 2～3 顆靈莓。野外長在靈液池邊 |
| **靈莓** | 可以吃，吃下會得到短暫的靈魂守護 |
| **幽光菇** | 洞穴地面會發光的小菇，在暗處會慢慢蔓延 |
| **幽光菇燉湯** | 碗＋2 幽光菇＋靈莓：飽足，並獲得回音視界 |

用原版**釀造台**釀造（以粗製藥水為底；紅石延長，火藥、龍息做成飛濺與滯留型）：

| 材料 | 藥水 | 效果 |
| :-- | :-- | :-- |
| 靈莓 | **靈魂守護**（3:00／8:00） | 完全免疫靈魂剝奪 |
| 幽光菇 | **回音視界**（3:00／8:00） | 32 格內的敵對生物發光，頭上冒出只有你看得到的幽匿粒子 |

**9 種新顏色**：青碧、薄荷、珊瑚、琥珀、薰衣草、赤紅玫瑰、靈魂藍、虛黑、暮光金。每種都有自己的染料，由同色的篩靈界植物合成（青碧草、薄荷草、珊瑚落葉、裂隙橙草、紫晶草、甲殼花、靈魂劈裂草、幽光菇、暮綻花……），還有自己的羊毛（含半磚、階梯）、地毯、混凝土（含半磚、階梯）、混凝土粉末、陶土、彩繪陶瓦、染色玻璃與玻璃片，做法和原版一樣。新染料也能染皮甲。沒有專屬新顏色的植物則合成原版染料；高的植物一次給 2 個。

### 方塊
450 種以上的方塊，多數有多種外觀階段可在創造模式分頁中挑選：地層岩、覆蓋石、板岩、砂岩、大理石與礦石；
**38 組建材**（石磚、浮雕石磚、半磚、樓梯、牆，含切石機配方）；完整的**靈魂柳木**組；以及會依地面變色的植物、花與垂藤。

### 製作方式
The Sift 是由一位創作者完成的 **AI-powered** 專案：
- **美術**：所有貼圖、模型與動畫皆由 PrYuan05 為本模組親手繪製與製作，過程中使用 AI 輔助工具；部分生物設計靈感來自《Minecraft Dungeons 2》。
- **程式**：Java 程式（生物 AI、Boss、物品、世界生成特徵）由 AI-powered 程式助手撰寫，並由 PrYuan05 審閱、實機測試與主導方向。
- **世界生成與工具**：地形、生態域、結構與貼圖流程都是 AI-powered 的 Python 工具，負責產生資料包檔案，並檢查每個方塊、模型與貼圖是否一致。

AI-powered 開發讓一個人也能做出這種規模的維度；但要放什麼、長什麼樣、怎麼玩，每一個決定都由人來做。

### 常見問題
- **支援 Forge／NeoForge 嗎？** 不支援，只有 Fabric 版。
- **可以加進現有世界嗎？** 可以，第一次進入時才會生成維度。
- **篩靈祭壇沒有反應？** 把它放在競技場中心 48 格內（放下後聊天欄會提示），不要蹲著用召喚印記，並確認競技場原本的 Boss 已經不在。
- **可以放進整合包嗎？** 可以，本模組採 MIT 授權，歡迎附上本頁連結。

### 製作與授權
由 **PrYuan05** 製作：親手繪製的美術，AI-powered 的開發。以 [MIT 授權](LICENSE) 釋出。
聲音素材與配樂的出處見 [`sounds/CREDITS.md`](src/main/resources/assets/pysift/sounds/CREDITS.md)。

*本模組並非 Minecraft 官方產品，與 Mojang 或 Microsoft 無關，亦未經其認可。*
