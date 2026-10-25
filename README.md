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
| 🧭 Helpers | Sift Guidebook, Soul Compass, Homeward Stone |
| 🌱 Life | Soul Berries, Gloomcaps, two new potions, a tameable Blub that fights and fetches |
| 🧱 Blocks | 450+ blocks, 38 building sets, the full Soul Willow wood set |
| 🤖 Made with | hand-drawn art + AI-powered development tools |

## Requirements

| | |
| :-- | :-- |
| Minecraft | 26.3 |
| Mod loader | Fabric Loader 0.19.5 or newer |
| Java | 25 or newer |
| Required mods | [Fabric API](https://modrinth.com/mod/fabric-api), [GeckoLib](https://modrinth.com/mod/geckolib) 5.5.7 or newer |

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

The first time you arrive you receive the **Sift Guidebook**, a 12-page in-game guide to everything below.

## The dimension

A permanent dusk under a mint-coloured sky, with soft fog, gentle rolling land, cliff-edged plateaus and
large round mesas built of stepped two-block-high tiers. The terrain was shaped with AI-powered worldgen tooling
(spline-based noise, studied from — not copied from — the best terrain mods) and tuned by hand.

| Biome | Ground | What you will find |
| :-- | :-- | :-- |
| **Crimson Strata Canyon** | crimson-capped strata over silted strata | stepped terraces, red mesas ringed in teal and rose, ember grass |
| **Violet Slate Abyss** | violet-capped dark slate | rolling hills, glowcaps, bone spires, charoite clusters, soul crystals, a boss arena |
| **Willow Grove** | crimson-capped strata over abyssal strata | soul willows (and rare giant weeping willows), the most ponds, flowers everywhere, a boss arena |
| **Amber Dunes** | amber and pale sand over bleached sandstone | ridged dunes, sandstone mesas, agave and oasis ponds, a boss arena |

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
| **Sift Guidebook** | given on your first visit (12 pages); covers spirit liquid, ores, bosses, the altar, awakening, the beacon, Soulite, farming and pets | Book + Charoite |
| **Soul Compass** | use it in The Sift: the needle points to a boss arena or the nearest ruins (it shows the distance). Sneak + use to switch target. If an arena has not been found yet, it points to that boss's biome | Compass + 3 Charoite + Soul Essence |
| **Homeward Stone** | hold use for 3 seconds in The Sift to return to your overworld spawn point (bed / respawn anchor) | Soul Essence + Charoite + Ender Pearl → 2 |

## Creatures

26 creatures, each with its own model, animations and behaviour — hunters that mark their prey, trappers that set
snares and throw nets, explosive Fuseflies (kill them from a distance!), stone-throwing Hurlers, Dartbacks that
shoot darts, Echo Golems that grow soul crystals, Slabbers with flowers growing on their backs, and the gentle Blub.

Blub · Bloombud · Dartback · Echo Golem · Fusefly · Hunter · Hurler · Lootkin · Nester · Nuzzle · Pollinator ·
Prickle · Roamroot · Scavenger · Seedling · Sentinel · Singer · Slabber · Sprout · Stalker · Trapper · Tuner · Wobble

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
| 🧭 上手輔助 | 篩靈指南書、靈魂羅盤、回程符石 |
| 🌱 生活 | 靈莓、幽光菇、兩種新藥水、會打架和撿東西的布魯布 |
| 🧱 方塊 | 450 種以上、38 組建材、完整靈魂柳木組 |
| 🤖 製作 | 親手繪製的美術 ＋ AI-powered 開發工具 |

### 需求
- Minecraft 26.3、Fabric Loader 0.19.5 以上、Java 25 以上
- 前置模組：Fabric API、GeckoLib 5.5.7 以上
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

第一次抵達時會獲得 12 頁的**《篩靈指南書》**，介紹下面所有內容。

### 維度與生態域
永恆的黃昏、薄荷色天空、淡淡的霧，平緩起伏的大地上有懸崖台地，以及一座座每層 2 格高、逐層內縮的大型圓台。
地形用 AI-powered 的世界生成工具打造（以 spline 雜訊為基礎，參考但不複製優秀的地形模組），再由人工調整。

| 生態域 | 地表 | 特色 |
| :-- | :-- | :-- |
| **赤紅沉積峽谷** | 赤紅覆蓋地層岩、淤積地層岩 | 階梯狀階地、青與玫瑰色環的紅色圓台、餘燼草 |
| **紫晶深板岩區** | 紫晶覆蓋深色板岩 | 起伏丘陵、螢光菇、骨刺、紫龍晶簇、靈魂晶塊、Boss 競技場 |
| **柳絮林地** | 赤紅覆蓋地層岩、深淵地層岩 | 靈魂柳與罕見的巨型垂柳、最多池塘、滿地花草、Boss 競技場 |
| **琥珀沙丘** | 琥珀沙、淺沙、漂白砂岩 | 稜線沙丘、砂岩圓台、龍舌蘭與綠洲池塘、Boss 競技場 |

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
| **篩靈指南書** | 第一次進入篩靈界時自動獲得；介紹靈液、礦石、Boss、祭壇、覺醒、信標、靈髓、種植與寵物 | 書＋紫龍晶 |
| **靈魂羅盤** | 在篩靈界右鍵：指針指向 Boss 競技場或最近的遺跡，並顯示距離；蹲下右鍵切換目標。還沒發現競技場時，會先指向那隻 Boss 的生態域 | 羅盤＋3 紫龍晶＋靈魂精華 |
| **回程符石** | 在篩靈界按住右鍵 3 秒，傳回主世界的重生點（床／重生錨） | 靈魂精華＋紫龍晶＋終界珍珠 → 2 個 |

### 生物
26 種生物，包括會標記獵物的獵人、設陷阱丟網的陷阱師、死後會爆炸的引信蠅（請從遠處解決）、投石的投擲者、
發射飛鏢的飛鏢背、頭頂長出靈魂晶塊的迴音傀儡、背上長花的泥板獸，以及溫和的布魯布。

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

*本模組並非 Minecraft 官方產品，與 Mojang 或 Microsoft 無關，亦未經其認可。*
