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
- Singers that spawn naturally in The Sift still wander as before.
- New advancement "Eight Songs"; the Guidebook has a 12th page.

### New: day and night in The Sift
- Three phases shared with the overworld clock: a warm gold-pink **morning**, the mint **day** and a deep-blue **night**
  with bright stars (use `/time set pysift:morning|pysift:day|pysift:night`).
- Portals glow brighter at night, with pink edges and a golden inner light.
- Portals now spill light outward: soft glowing layers in front of and behind the portal, rays reaching out over the
  frame, a glowing patch on the ground and drifting sparks. Arrival portals get gentle half-block ramps on both sides.

### New: portals and places
- Arriving in The Sift now builds a decorated **arrival portal** in the colours of the biome (ember stone, dark slate, silted strata and desert sandstone versions, designed in-game).
- The small rift portal now appears very rarely out in the wild; it works both ways.
- **Red Zone Caves**: a new underground biome with crimson floors, red plants, starlit shrubs and charoite.
- **Glowshade Grass**, **Glowshade Tuft** and **Starlit Shrub**: plants with glowing tips that shed little lights at night.

### Changes
- Monarch model lowered so it no longer floats above the ground.
- The ritual Singer appears on the exact centre of the portal (aligned with the Ancient City's central steps), stays
  perfectly still while waiting, and plays with a tiny Echo Golem (scoop, lift overhead, one turn, put down).
- The ritual can no longer wake the Warden.

## v1.0.1（繁體中文）

### 新增：八音開門儀式（取代原本一鍵開門）
- 在遠古城市的傳送門框架附近吹山羊角：**歌者**從地底爬出並站在原地。
- 歌者會一直招手，直到你給它**迴音碎片**：它召喚兩隻**迴音傀儡**從地底爬出，把 8 個**共鳴唱片盒**搬到框架下方的地面，由左到右放好（全程有動畫）。
- 放入 8 張來自 8 個地方的唱片（Pigstep、Relic、Precipice、Creator、5、Otherside、13、Tears），由左到右依序是紅橙黃綠藍靛紫粉的光柱；8 張都放好時光柱匯聚、傳送門開啟，歌者揮手道別後鑽回地底。
- 唱片盒就是鑰匙：打破任一個，門就關閉，唱片掉出來。
- 篩靈界：用**靈魂晶塊**蓋封閉框架，拿迴音碎片右鍵，就能開出回主世界的傳送門。
- 篩靈界自然生成的歌者照常走動。
- 新成就「八音共鳴」；指南書增加第 12 頁。

### 新增：篩靈界的日夜
- 三個時段，跟主世界共用時鐘：暖金粉色的**晨間**、薄荷色的**日間**、星光明亮的深藍**夜間**（可用 `/time set pysift:morning|pysift:day|pysift:night`）。
- 傳送門夜晚更亮，邊緣轉成粉紅、內側透出金黃。
- 傳送門的光會往外擴散：門面前後的柔光、浮在框架上的外延光芒、地面光圈與往外飄的光點；到達門前後各有一道半格一階的緩坡，好走進去。
- 夜晚的傳送門更明顯：光芒拉長近三倍、門前後浮出兩層粉金光霧、地上鋪一片光、光點往外飄（東西向的門也有）。夜空極光增加到七條三種配色，夜晚的雲淡到幾乎看不見。
- 到達門每次都不一樣：隨機轉向與鏡像、緩坡寬 5～9 格且邊緣參差、坡腳散落碎石；緩坡用當地地表方塊與同色系半磚鋪成，像地面延伸上去；地基會往下補到實心地面，不再懸空。
- 新地標（參考 Minecraft Dungeons II 的地點，tools/worldgen/build_landmarks.py）：地底的**迴音穴**（jigsaw 拼接：圓頂歌唱劇場＋隧道、樓梯、十字路口、晶洞、共鳴室、坍塌大廳、寶庫，迴音傀儡聚集）、琥珀沙丘的**迅從者殘骸**（可走進去的巨大骨架，成就「甲殼探險家」）與散落的**小化石**、山頂的**搖籃曲山丘神殿**。
- 結構修改流程：`/pysift_showcase` 把所有結構草稿排在玩家旁邊並放好設定為儲存的結構方塊；改完按儲存後用 `tools/worldgen/import_structures.py <世界資料夾>` 匯回模組（之後產生器不會覆蓋使用者改過的結構）。
- Blub 改成只吃靈魂晶塊（馴服、回血、繁殖、拿在手上吸引牠），靈魂沙與靈魂土不再有用；指南書與 README 同步更新。
- Blub 坐下改成趴著（肚子貼地、前腳往前伸、後腳往後伸、慢慢呼吸）；新增跟原版狗一樣的字幕：受傷、死亡、低吼（有目標時）、嗚咽（受傷的寵物）、趴下。修正受傷與死亡時字幕顯示「落地」。叫牠趴下／站起來、馴服成功時，快捷列上方會跳出提示（例如「布魯布 趴下了」）。
- Blub 新增攻擊動畫（五種變體都有）：往後一縮蓄力、撲上去、身體前端往下一咬，耳朵與前後腳跟著甩，有尾巴／鰭的變體尾巴會甩、鰭會張開。
- 靈柳林的夜光草叢改成成叢生長（每區塊 5 叢、每叢 10～20 株），入夜後像一片片發光的草地。
- 傳送門效能：渲染不再每幀建立暫時陣列、夜晚光霧合成一層、被門框擋住的面不畫；粒子與音效頻率降低（靠近大型傳送門不再卡頓）。
- 修正穿過傳送門後卡在方塊裡：落點改在回程門蓋好之後才決定（站到門前的空地），找不到就挖出兩格高的空間。

### 新增：傳送門與地點
- 抵達篩靈界時會蓋出一座依生態域色系裝飾的**到達傳送門**（余燼石、深色板岩、淤積地層岩與沙漠砂岩四種版本，在遊戲裡設計）。
- 原本的小裂隙門改成極少數在野外生成，可雙向傳送。
- **紅區洞穴**：新的地底生態域，赤紅地面、紅色植物、星光灌木與紫龍晶。
- **夜光草、夜光草叢、星光灌木**：葉尖發光，入夜後會飄出小光點。

### 調整
- Monarch 模型下移，不再懸空。
- 儀式歌者精準出現在傳送門正中央（對齊遠古城市的中央台階），等待時完全不轉頭；無聊時會和小傀儡玩（撈起、高舉、轉一圈、放下）。
- 儀式過程不會再引來伏守者。


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
