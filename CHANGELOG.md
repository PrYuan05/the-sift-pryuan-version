# Changelog

## v1.0.1

### New: the Eight-Song Ritual (replaces the old one-click portal)
- Blow a Goat Horn at an Ancient City portal frame: a **Singer** climbs out and stays in place.
- The Singer beckons until you give it an **Echo Shard**; then it calls two **Echo Golems** that climb out of the ground, carry eight
  **Resonant Jukeboxes** to the floor below the frame and set them down from left to right (all animated).
- Fill the jukeboxes with eight discs from eight places (Pigstep, Relic, Precipice, Creator, 5, Otherside, 13, Tears);
  left to right they shine red, orange, yellow, green, blue, indigo, purple, pink. When all eight play, the beams meet,
  the portal opens and the Singer waves goodbye and burrows away.
- The jukeboxes are the key: break one and the portal closes, the disc drops out.
- In The Sift: a closed **Soul Crystal** frame + an Echo Shard opens a portal back to the overworld.
- The ritual Singer stands on the exact centre of the portal, stays perfectly still while waiting, plays with a tiny
  Echo Golem when bored, and can no longer wake the Warden. New advancement "Eight Songs"; the Guidebook has a 12th page.

### New: day, night and sky
- Three phases shared with the overworld clock: a warm gold-pink **morning**, the mint **day** and a deep-blue **night**
  (use `/time set pysift:morning|pysift:day|pysift:night`).
- Night sky: seven aurora ribbons in three colour schemes; clouds almost vanish at night so stars and aurora show.

### New: portals
- Arriving in The Sift builds a decorated **arrival portal** in the biome's colours (ember stone, dark slate, silted
  strata and desert sandstone designs, built in game), randomly turned and mirrored.
- Arrival portals sit on a filled **half-circle fan of steps** in front and behind that reaches all the way to the ground
  (gentle where low, steeper over big drops), made of the local ground with matching slabs, ragged at the edge, with
  rubble at the foot. Foundations reach solid ground; trees no longer count as ground.
- You land on a safe spot in front of the portal instead of inside blocks.
- Portals glow at night: longer rays, a pink-gold haze in front and behind, light on the ground, drifting sparks.
  Rendering is much lighter, so large portals no longer lag.
- The small rift portal appears very rarely in the wild and works both ways.

### New: biomes and landmarks (after Minecraft Dungeons II)
- **Lullaby Hills**: a grand canyon of crimson vein stone walls climbing in three terraces to void-capped plateaus; on
  the canyon floor a marble road at the wall foot, bleached sandstone, and a river of Spirit Liquid lined with golden
  aurum ore. Every border between floor materials blends block by block. Echo Golems roam here.
- **Red Zone Caves**: an underground biome with crimson floors, red plants and charoite.
- **The Echo Den**: a deep underground domed singing amphitheatre of the Echo Golems, with tunnels branching to crystal
  grottoes, resonance rooms, collapsed halls and a rare vault - every one laid out differently.
- **Humbler Husks** (walk-through giant skeletons in the Amber Dunes, achievement *Carapace Explorer*), scattered
  **fossils**, and **Lullaby Hilltop shrines** on hill tops.
- Boss arenas, ruins, arrival portals and landmarks are now structure files that can be edited in game
  (`/pysift_showcase`, see `art_requests/structures_edit_guide.md`); several have been reshaped by hand.

### New: blocks, colours and dyes
- **Nine new colours**: Teal, Mint, Coral, Amber, Lavender, Crimson Rose, Soul Blue, Void and Dusk Gold, each with a dye
  and wool (with slabs and stairs), carpet, concrete (with slabs and stairs), concrete powder, terracotta, glazed
  terracotta, stained glass and panes (108 blocks), crafted like the vanilla ones. The new dyes also colour leather armour.
- Sift plants craft into dyes: the new colours from matching plants, vanilla dyes from the rest.
- **Amber and pale sandstone** families (chiseled, cut, smooth, slabs, stairs, walls); amber and pale sand now fall.
- **Spiritlogging**: any block that can hold water can hold Spirit Liquid instead (buckets, placing blocks in it).
- Covered natural surface blocks turn into the block below, like vanilla grass.
- Night-glow tufts grow in clusters in the Willow Grove.
- Crimson vein stone and void-capped crimson share one hue; crimson vein stone no longer looks like ember stone.

### New: creatures
- **Blub**: lies down when told to sit, has a bite attack, dog-like subtitles (hurts, dies, growls, whines, lies down)
  and action-bar hints; it is tamed, healed, bred and tempted with **Soul Crystal Blocks** only.

### Changes
- Creative tabs are grouped and sorted (block families together, blocks that generate in the world first).
- Monarch model lowered so it no longer floats above the ground.

## v1.0.1（繁體中文）

篩靈界的中文名稱改為**隙浮**。

### 新增：八音開門儀式（取代原本一鍵開門）
- 在遠古城市的傳送門框架附近吹山羊角：**歌者**從地底爬出並站在原地。
- 歌者會一直招手，直到你給它**迴音碎片**：它召喚兩隻**迴音傀儡**從地底爬出，把 8 個**共鳴唱片盒**搬到框架下方的地面，由左到右放好（全程有動畫）。
- 放入 8 張來自 8 個地方的唱片（Pigstep、Relic、Precipice、Creator、5、Otherside、13、Tears），由左到右依序是紅橙黃綠藍靛紫粉的光柱；8 張都放好時光柱匯聚、傳送門開啟，歌者揮手道別後鑽回地底。
- 唱片盒就是鑰匙：打破任一個，門就關閉，唱片掉出來。
- 隙浮：用**靈魂晶塊**蓋封閉框架，拿迴音碎片右鍵，就能開出回主世界的傳送門。
- 儀式歌者精準出現在傳送門正中央，等待時完全不轉頭，無聊時會和小傀儡玩；儀式不會再引來伏守者。新成就「八音共鳴」；指南書增加第 12 頁。

### 新增：日夜與天空
- 三個時段，跟主世界共用時鐘：暖金粉色的**晨間**、薄荷色的**日間**、深藍的**夜間**（可用 `/time set pysift:morning|pysift:day|pysift:night`）。
- 夜空：七條三種配色的極光；入夜後雲淡到幾乎看不見，星星和極光更清楚。

### 新增：傳送門
- 抵達隙浮時會蓋出一座依生態域色系裝飾的**到達傳送門**（餘燼石、深色板岩、淤積地層岩與沙漠砂岩四種，在遊戲裡設計），每座隨機轉向與鏡像。
- 到達門前後是一片完全填滿的**半圓扇形階梯**，一路鋪到地面（低的地方緩、落差大的地方陡），用當地地表方塊與同色系半磚，外緣自然參差、坡腳散落碎石；地基會補到實心地面，樹不再被當成地面。
- 傳送後會站在門前的空地，不會卡在方塊裡。
- 夜晚的傳送門更明顯：光芒拉長、門前後浮出粉金光霧、地上鋪一片光、光點往外飄；渲染大幅減輕，靠近大型傳送門不再卡頓。
- 小裂隙門極少數在野外生成，可雙向傳送。

### 新增：生態域與地標（參考 Minecraft Dungeons II）
- **搖籃曲山丘**：赤紅脈石的高聳地形牆分三層階梯爬上虛黑覆蓋的台地；谷底牆腳是灰白大理石道路，再來是漂白砂岩，最低一層是金岩礦河岸圍著的靈液河與湖。谷底每條材質交界都一格一格互相滲透。迴音傀儡在這裡出沒。
- **紅區洞穴**：新的地底生態域，赤紅地面、紅色植物與紫龍晶。
- **迴音穴**：地底深處的圓頂歌唱劇場，迴音傀儡聚在這裡；隧道往外分岔到晶洞、共鳴室、坍塌大廳與稀有的寶庫，每座格局都不一樣。
- **迅從者殘骸**（琥珀沙丘裡可以走進去的巨大骨架，成就「甲殼探險家」）、散落的**小化石**、山頂的**搖籃曲山丘神殿**。
- Boss 競技場、遺跡、到達門與地標都改成可以在遊戲裡修改的結構檔（`/pysift_showcase`，見 `art_requests/structures_edit_guide.md`），其中幾座已經手工改過。

### 新增：方塊、顏色與染料
- **9 種新顏色**：青碧、薄荷、珊瑚、琥珀、薰衣草、赤紅玫瑰、靈魂藍、虛黑、暮光金。每種有染料，以及羊毛（含半磚、階梯）、地毯、混凝土（含半磚、階梯）、混凝土粉末、陶土、彩繪陶瓦、染色玻璃與玻璃片（共 108 個方塊），做法和原版一樣；新染料也能染皮甲。
- 隙浮的植物可以合成染料：顏色相符的做新顏色，其他做原版染料。
- **琥珀砂岩、蒼白砂岩**整套（雕紋、切製、平滑、半磚、階梯、牆）；琥珀沙與蒼白沙會像原版沙一樣掉落。
- **含靈液**：所有能含水的方塊都能改成含靈液（桶子倒入、舀起、在靈液裡放方塊都可以）。
- 被蓋住的天然地表方塊會像原版草地一樣變成下面那層。
- 靈柳林的夜光草叢改成成叢生長。
- 赤紅脈石與虛黑覆蓋赤紅岩統一色相，赤紅脈石不再和餘燼石長得一樣。

### 新增：生物
- **布魯布**：坐下時改成趴著，新增咬擊動畫、跟原版狗一樣的字幕（受傷、死亡、低吼、嗚咽、趴下）與快捷列提示；改成只吃**靈魂晶塊**（馴服、回血、繁殖、吸引）。

### 調整
- 創造模式分頁分組排序（同一族的方塊放在一起，會在世界生成的排前面）。
- Monarch 模型下移，不再懸空。

## v1.0.0 — First release (Minecraft 26.3, Fabric)

The first public release of The Sift, an AI-powered Minecraft mod made by PrYuan05.

### Dimension
- New dimension **The Sift**, reached through a Singer-activated portal in an Ancient City.
- 4 biomes: Crimson Strata Canyon, Violet Slate Abyss, Willow Grove, Amber Dunes.
- Gently rolling terrain, cliff-edged plateaus, large round stepped mesas and Spirit Liquid ponds (no rivers or oceans).
- 4 ruins with loot: Strata Shrine, Abyss Obelisk, Willow Hut, Dune Tomb. Soul crystal geodes underground.
- Ambient particles per biome, soft pale fog, mint sky.

### Spirit Liquid & Soul Deprivation
- Spirit Liquid drains your health to a fifth; damage taken while deprived shatters the lost health.
- Soul Antidote restores it. Spirit Liquid + water → Soul Crystal.
- Deprived mobs burn with blue soul fire, take 30 % more damage and slowly lose health.

### Creatures & bosses
- 26 animated creatures with their own AI, including new Hunter, Trapper and Sculk Cube models.
- 3 bosses — Harmonizer, Monarch, Sculk Monstrosity — with enrage phases, arenas and death sequences.
- Fusefly explosions match their damage radius.
- **Blub** can be tamed with Soul Sand / Soul Soil; it fights for you and fetches dropped items into your inventory.

### Progression
- Siftite ore, Charoite clusters, Raw Siftite, Fuse Powder, Soul Essence.
- Siftite tools and armor (full set halves Spirit Liquid drain).
- Boss cores and shards; three boss weapons (Sonic Staff, Dash Charm, Sculk Hammer) with smithing-table **awakening**.
- **Sift Altar** + **Summoning Sigil** to fight a boss again (within 48 blocks of its arena; the chat tells you where the nearest arena is).
- **Sift Beacon Gem** inlaid in a chestplate: Soul Deprivation immunity within 8 blocks.
- **Soulite** — stronger than netherite: tools and armor carrying boss powers, upgraded from netherite with the Soulite Upgrade template.
- Advancement line from your first step into The Sift to Soulite.

### Helpers
- **Sift Guidebook** (11 pages), given on your first visit and craftable.
- **Soul Compass** — points to boss arenas or the nearest ruins.
- **Homeward Stone** — returns you to your overworld spawn.

### Farming & brewing
- **Soul Berry Bush** (grows beside Spirit Liquid), **Soul Berries**, **Gloomcap**, **Gloomcap Stew**.
- New potions (vanilla brewing stand): **Soul Ward** (Soul Deprivation immunity) and **Echo Sight** (enemies within 32 blocks glow).

### Blocks
- 450+ blocks, 38 building sets with stonecutter recipes, the full Soul Willow wood set, ground-tinted plants and flowers.

### Known issues
- Some item and block textures are still placeholders (see `art_requests/texture_todo.md`).

---

## v1.0.0 — 首次發布（Minecraft 26.3，Fabric）

The Sift（篩靈界）的第一個公開版本，由 PrYuan05 製作的 AI-powered Minecraft 模組。

### 維度
- 新維度**篩靈界**：在遠古城市由歌者開啟傳送門前往。
- 4 個生態域：赤紅沉積峽谷、紫晶深板岩區、柳絮林地、琥珀沙丘。
- 平緩起伏的地形、懸崖台地、大型階梯圓台與靈液池塘（沒有河流與海洋）。
- 4 種附戰利品的遺跡：地層神殿、深淵方尖碑、靈柳小屋、沙丘古墓；地底有靈魂晶洞。
- 各生態域的環境粒子、淡色薄霧、薄荷色天空。

### 靈液與靈魂剝奪
- 靈液會把血量抽到五分之一；剝奪期間受傷，被抽走的血量會碎裂。
- 靈魂解藥可以恢復；靈液碰到水會凝結成靈魂晶塊。
- 被剝奪的怪物會燃起藍色靈魂火、受到傷害 +30%，並持續流失血量。

### 生物與 Boss
- 26 種有專屬 AI 與動畫的生物（含重做的獵人、陷阱師、幽匿方塊模型）。
- 3 隻 Boss：調和者、君王、幽匿巨怪，有狂暴階段、競技場與死亡演出。
- 引信蠅的爆炸範圍與傷害範圍一致。
- **布魯布**可用靈魂沙／靈魂土馴服，會幫你打架、把掉落物叼回你的背包。

### 進度與裝備
- 篩金石礦、紫龍晶簇、粗篩金石、引信粉、靈魂精華。
- 篩金石工具與盔甲（整套時靈液抽血減半）。
- Boss 核心與碎片；三把 Boss 武器（音波法杖、衝刺護符、幽匿重錘），可在鍛造台**覺醒**。
- **篩靈祭壇**＋**召喚印記**再次挑戰 Boss（放在競技場中心 48 格內，聊天欄會提示最近的競技場在哪）。
- **篩靈信標寶石**鑲嵌胸甲：8 格內免疫靈魂剝奪。
- **靈髓**：比獄髓更強，帶有 Boss 能力的工具與盔甲，用靈髓升級模板從獄髓裝備升級。
- 從進入篩靈界到靈髓的成就線。

### 上手輔助
- **篩靈指南書**（11 頁）：第一次進入時獲得，也能合成。
- **靈魂羅盤**：指向 Boss 競技場或最近的遺跡。
- **回程符石**：傳回主世界的重生點。

### 種植與釀造
- **靈莓叢**（長在靈液旁）、**靈莓**、**幽光菇**、**幽光菇燉湯**。
- 新藥水（原版釀造台）：**靈魂守護**（免疫靈魂剝奪）、**回音視界**（32 格內敵人發光）。

### 方塊
- 450 種以上的方塊、38 組建材（含切石機配方）、完整靈魂柳木組、會依地面變色的植物與花。

### 已知問題
- 部分物品與方塊貼圖仍是臨時圖（見 `art_requests/texture_todo.md`）。
