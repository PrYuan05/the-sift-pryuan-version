# 石材升級對印表（現實石材 → 生態域方塊）

由 `tools/worldgen/stone_reference_sheet.py` 產生（不會改任何遊戲貼圖）。總覽圖：`art_requests/stone_upgrade_references.png`（每種現實石材三張 16×16：現實色／套上生態域色相／目前貼圖）。

**做法**：紋理結構（層理、裂紋、氣孔、劈理、脈紋）取自現實石材；色相保留各生態域原本的色系（青碧、粉紅、紫、金…），亮暗階與色相偏移照 skill 的 7 色雙層色階。參考樣式是照現實石材的結構手繪的像素草圖，不是照片。

**這一版的修改**：粉紅系方塊改用更柔和的石材（凝灰岩、粉紅砂岩、流紋岩、黏土、玫瑰大理石），色階跨度壓窄到 0.12~0.20；紫色板岩、千枚岩也磨平；`aurum_ore` 改成四種「礦脈佈滿整個方塊」的候選；已完成的琥珀／淺砂岩不再列出。

## 一、現實參考石材（21 種）

| 編號 | 現實石材 | 英文／產地 | 要畫出的結構 | 現實色 7 階（亮→暗） |
| :-- | :-- | :-- | :-- | :-- |
| R01 | 風紋沙 | Wind-rippled dune sand（納米布沙漠、撒哈拉） | 沙丘表面的風成漣漪：背風面較陡較暗、迎風面長而緩，漣漪線微微起伏；沙粒細，只有零星的亮暗顆粒 | `#D4C39C` `#D4B787` `#D8A972` `#DC9B63` `#D69162` `#C68468` `#B1756B` |
| R02 | 科科尼諾白砂岩 | Coconino sandstone（美國亞利桑那 大峽谷） | 風成交錯層理：細白的石英砂，層理線斜著穿過；顏色最淡、顆粒最細 | `#E6E5D0` `#E1DDC3` `#DCD4B7` `#D8CCAD` `#D3C3A9` `#C9B9A7` `#BCACA1` |
| R03 | 龜裂泥岩 | Mud-cracked playa mudstone（死亡谷 Badwater、乾涸湖床） | 乾縮龜裂：多邊形泥片，邊緣翹起（左上亮緣）、裂縫右下較深，一半是淺裂 | `#BEB7A3` `#BAAD96` `#B8A388` `#B4997E` `#AD907A` `#A18678` `#917872` |
| R04 | 粉紅凝灰岩 | Pink rhyolitic tuff（土耳其 卡帕多奇亞、匈牙利 Eger） | 柔軟細緻的火山灰固結岩：幾乎平滑，只有細小的孔點與團粒，色階只用相鄰 3~4 階，跨度很窄 | `#C4A6A4` `#C89C9C` `#CC9197` `#CE8893` `#C58493` `#B58091` `#A27B8E` |
| R05 | 粉紅砂岩 | Coral pink sandstone（美國猶他 Coral Pink Sand Dunes） | 細粒風成砂岩，只有很淡的寬層理（2~3 px 一層、相鄰色階），沒有深色夾層線 | `#BEA598` `#C29B8C` `#C98F81` `#CF8378` `#CA7D77` `#BB777A` `#A4727C` |
| R06 | 粉紅流紋岩 | Pink flow-banded rhyolite（美國黃石、墨西哥） | 火山熔岩流動形成的斜向細條帶（4 px 一條、相鄰色階），偶有極小的氣孔；整體平順 | `#AF998F` `#B28F85` `#B6847B` `#BA7A74` `#B57372` `#A46F73` `#906972` |
| R07 | 粉紅黏土 | Pink kaolin clay（澳洲 Pilbara、法國 Provence） | 細膩的黏土團粒：2~4 px 的柔和團塊交織，色階只差一階，沒有礫石也沒有裂縫 | `#C4A9A7` `#C8A1A1` `#CC979D` `#CD8F9A` `#C68C99` `#B98A99` `#AA8597` |
| R08 | 玫瑰大理石 | Rosa Portogallo marble（葡萄牙 Estremoz、義大利 Rosa Aurora） | 粉紅基底，幾條很淡的亮色斜脈（只比底色亮兩階），脈兩側有柔和暈邊；沒有高對比的白脈 | `#C1A8A5` `#C19D9B` `#C49192` `#C2878C` `#B68189` `#A57B85` `#91717E` |
| R09 | 層紋粉砂岩 | Laminated siltstone（美國 Moenkopi／Chinle 地層） | 細密的薄層紋理（1~2 px 一層），層面平整略起伏，偶有較暗的泥質夾層；綠灰色（含海綠石／綠泥石） | `#95A29E` `#8A9A95` `#7F948B` `#768C81` `#708478` `#68796D` `#5D6A60` |
| R10 | 條帶泥岩 | Banded bentonite mudstone (Chinle)（彩繪沙漠（Painted Desert）） | 寬而平的灰、紅、淡紫色帶，色帶之間界線清楚 | `#AB9E94` `#A49285` `#9E8478` `#97786D` `#8C6C65` `#7B5F5D` `#624E50` |
| R11 | 紫色板岩 | Purple slate（威爾斯 Penrhyn） | 板狀劈理：長而細的 1 px 薄片（7~13 px）整齊疊放，相鄰色階接近、劈理線只用次暗色，整體平順 | `#736873` `#6E6270` `#695B6D` `#64556A` `#5D5164` `#544B5B` `#48444F` |
| R12 | 紫色千枚岩 | Purple phyllite（阿帕拉契山脈） | 比板岩更細膩、有絲絹光澤的波浪狀劈理，起伏一個週期、對比同樣收窄 | `#887988` `#847085` `#7F6782` `#79607F` `#715B77` `#64556C` `#564D5D` |
| R13 | 卡拉拉大理石 | Carrara marble（義大利 托斯卡尼） | 白到淺灰的細粒基底，1 px 的灰色斜向脈紋蜿蜒穿過，脈兩側有淡淡的暗暈 | `#EAE9E3` `#DFDDD6` `#D4D2C9` `#CBC7BE` `#C0BCB5` `#B2ADA9` `#A09B99` |
| R14 | 綠泥片岩 | Chlorite schist（阿爾卑斯、格陵蘭） | 波浪狀葉理的暗綠色片岩，帶絲絹光澤的亮脊，葉理起伏明顯 | `#71847F` `#647D74` `#567568` `#4C6D5C` `#456252` `#3E5345` `#334136` |
| R15 | 虎眼石 | Tiger's eye（南非 Northern Cape、西澳） | 金棕色平行纖維（1~2 px 一條、微微起伏），纖維上有 3~6 px 的絲絹亮條（貓眼光），整塊都是礦 | `#8E8459` `#877541` `#83662B` `#7E561C` `#71481B` `#5B391E` `#3D251B` |
| R16 | 褐鐵礦（葡萄狀） | Botryoidal limonite / goethite（德國、英國 Cumbria） | 棕橘色圓球狀結核連成一片（4 px 左右的小圓丘），左上受光、縫淺，整塊都是礦 | `#978763` `#94794E` `#946A39` `#935B29` `#884E28` `#73412C` `#57312A` |
| R17 | 黃銅礦（虹彩） | Iridescent chalcopyrite（秘魯、美國 Bisbee） | 黃銅色團塊，局部氧化出藍紫色虹彩膜；金黃主體加少量藍紫斑，整塊都是礦 | `#ADAE6B` `#A8A34F` `#A59634` `#A28820` `#9B7A21` `#8C692C` `#775332` |
| R18 | 自然銅 | Native copper (with verdigris)（美國密西根 Keweenaw） | 橘棕色的銅片與樹枝狀結構，夾少量綠色銅鏽；整塊都是礦 | `#AC9372` `#AB855C` `#AF7346` `#B26335` `#A65734` `#904A39` `#703A38` |
| R19 | 玄武岩 | Basalt（冰島、愛爾蘭 巨人堤道） | 細粒暗灰，結構緻密：幾個 1~2 px 小氣孔，加上稀疏的垂直節理（短、錯開） | `#57575A` `#505155` `#4A4B4F` `#434549` `#3D3F42` `#353839` `#2B2D2E` |
| R20 | 鐵染玄武岩 | Oxidized (iron-stained) basalt（夏威夷、澳洲玄武岩紅土） | 同玄武岩的緻密結構，表面鐵氧化成紅褐，氣孔邊緣鏽色更深 | `#786E62` `#736457` `#71594C` `#6C4F43` `#64473F` `#573E3A` `#443132` |
| R21 | 橄欖岩／蛇紋岩 | Peridotite / serpentinite（阿曼、加州 Coast Range） | 橄欖綠顆粒基底，白綠色的蛇紋石細脈（1 px）蜿蜒穿過，脈旁有暗暈 | `#6E7D6A` `#63765D` `#5A6D4F` `#536545` `#4C5B3F` `#454D38` `#393C2F` |

## 琥珀沙丘（`amber_dunes`）

| 層位 | 現有方塊 | 貼圖數* | 參考石材 | 升級的方塊（含衍生） | 備註 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 地表（0~3 格） | `amber_sand`、`pale_sand` | 2 | R01 風紋沙 | 本體（單一方塊，無衍生） | 兩種沙都畫成風紋沙；色階相同、色相不同 |
| 地下（3~6 格） | `bleached_sandstone` | 7 | R02 科科尼諾白砂岩 | 本體＋8 個衍生：`bleached_sandstone_bricks`、`chiseled_bleached_sandstone_bricks`、`bleached_sandstone_slab`、`bleached_sandstone_stairs`、`bleached_sandstone_wall`、`bleached_sandstone_brick_slab`、`bleached_sandstone_brick_stairs`、`bleached_sandstone_brick_wall` | bleach 0~4 五階：越白越接近最淡階（琥珀／淺砂岩建材組上一輪已完成，不列入） |
| 深層（6~9 格） | `cracked_sandstone` | 4 | R03 龜裂泥岩 | 本體（單一方塊，無衍生） | crack 0~3：裂得越多多邊形越小；也是柳絮林地的路徑 |

## 赤紅沉積峽谷（`crimson_strata_canyon`）

| 層位 | 現有方塊 | 貼圖數* | 參考石材 | 升級的方塊（含衍生） | 備註 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 地表 | `crimson_capped_crimson_strata_3` | 見備註 | R04 粉紅凝灰岩、R05 粉紅砂岩 | 本體（單一方塊，無衍生） | 頂面（canyon_top_a~d）→ 粉紅凝灰岩；側面 crimson_strata_i → 粉紅砂岩；底面沿用地下的 silted_strata |
| 地下（0~4 格） | `silted_strata` | 6 | R09 層紋粉砂岩 | 本體＋8 個衍生：`silted_strata_bricks`、`chiseled_silted_strata_bricks`、`silted_strata_slab`、`silted_strata_stairs`、`silted_strata_wall`、`silted_strata_brick_slab`、`silted_strata_brick_stairs`、`silted_strata_brick_wall` | silt 0~2：越深層紋越密、含更多暗色泥質夾層 |
| 路徑 | `banded_mudstone` | 6 | R10 條帶泥岩 | 本體＋8 個衍生：`banded_mudstone_bricks`、`chiseled_banded_mudstone_bricks`、`banded_mudstone_slab`、`banded_mudstone_stairs`、`banded_mudstone_wall`、`banded_mudstone_brick_slab`、`banded_mudstone_brick_stairs`、`banded_mudstone_brick_wall` | banding 0~3：色帶由窄到寬 |
| 桌山頂 | `capped_crimson_strata` | 4 | R04 粉紅凝灰岩、R05 粉紅砂岩 | 本體（單一方塊，無衍生） | tone teal／rose／mottled／deep_teal 四種：頂面凝灰岩、側面粉紅砂岩 |
| 桌山身 | `ember_stone` | 10 | R06 粉紅流紋岩 | 本體＋8 個衍生：`ember_stone_bricks`、`chiseled_ember_stone_bricks`、`ember_stone_slab`、`ember_stone_stairs`、`ember_stone_wall`、`ember_stone_brick_slab`、`ember_stone_brick_stairs`、`ember_stone_brick_wall` | heat 0~4：粉紅流紋岩由淺到深（越熱越偏赭紅） |
| 岩壁與層 | `crimson_strata` | 16 | R05 粉紅砂岩 | 本體＋8 個衍生：`crimson_strata_bricks`、`chiseled_crimson_strata_bricks`、`crimson_strata_slab`、`crimson_strata_stairs`、`crimson_strata_wall`、`crimson_strata_brick_slab`、`crimson_strata_brick_stairs`、`crimson_strata_brick_wall` | 14 張側面貼圖：tone rose／mottled／crimson／plum |

## 紫晶深板岩區（`violet_slate_abyss`）

| 層位 | 現有方塊 | 貼圖數* | 參考石材 | 升級的方塊（含衍生） | 備註 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 地表 | `violet_capped_dark_slate` | 1 | R12 紫色千枚岩、R11 紫色板岩 | 本體（單一方塊，無衍生） | 頂面（violet_strata_e）→ 千枚岩；側面（dark_slate_q）→ 板岩 |
| 地下（0~5 格） | `dark_slate` | 22 | R11 紫色板岩 | 本體＋8 個衍生：`dark_slate_bricks`、`chiseled_dark_slate_bricks`、`dark_slate_slab`、`dark_slate_stairs`、`dark_slate_wall`、`dark_slate_brick_slab`、`dark_slate_brick_stairs`、`dark_slate_brick_wall` | fade 0~4、共 20 張：由暗紫板岩漸變，要保留每個階段的辨識度 |
| 路徑 | `ash_marble` | 6 | R13 卡拉拉大理石 | 本體＋8 個衍生：`ash_marble_bricks`、`chiseled_ash_marble_bricks`、`ash_marble_slab`、`ash_marble_stairs`、`ash_marble_wall`、`ash_marble_brick_slab`、`ash_marble_brick_stairs`、`ash_marble_brick_wall` | veining 0~3：脈紋由少到多（也用在搖籃曲山丘的台地） |
| 結構（Boss 神殿、方尖碑） | `dark_slate_pillar` | 3 | R11 紫色板岩 | 本體（單一方塊，無衍生） | 柱身（top／side／bottom）：切割過的板岩柱，劈理沿柱軸方向 |
| 岩壁與紫層 | `violet_strata` | 7 | R12 紫色千枚岩 | 本體＋8 個衍生：`violet_strata_bricks`、`chiseled_violet_strata_bricks`、`violet_strata_slab`、`violet_strata_stairs`、`violet_strata_wall`、`violet_strata_brick_slab`、`violet_strata_brick_stairs`、`violet_strata_brick_wall` | 紫色地層本體 |

## 柳絮林地（`willow_grove`）

| 層位 | 現有方塊 | 貼圖數* | 參考石材 | 升級的方塊（含衍生） | 備註 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 地表 | `crimson_capped_crimson_strata_2` | 見備註 | R07 粉紅黏土、R05 粉紅砂岩 | 本體（單一方塊，無衍生） | 頂面（grove_top、grove_top_b）→ 粉紅黏土；側面 crimson_strata_c → 粉紅砂岩；底面 teal_strata_a |
| 地下（0~6 格） | `abyssal_strata` | 9 | R14 綠泥片岩 | 本體＋8 個衍生：`abyssal_strata_bricks`、`chiseled_abyssal_strata_bricks`、`abyssal_strata_slab`、`abyssal_strata_stairs`、`abyssal_strata_wall`、`abyssal_strata_brick_slab`、`abyssal_strata_brick_stairs`、`abyssal_strata_brick_wall` | depth 0~3、共 7 張：越深葉理越密越暗（Boss 神殿的磚用這個） |
| 路徑 | `cracked_sandstone` | 4 | R03 龜裂泥岩 | 本體（單一方塊，無衍生） | 與琥珀沙丘共用，不重畫 |
| 底面與層 | `teal_strata` | 9 | R09 層紋粉砂岩 | 本體＋8 個衍生：`teal_strata_bricks`、`chiseled_teal_strata_bricks`、`teal_strata_slab`、`teal_strata_stairs`、`teal_strata_wall`、`teal_strata_brick_slab`、`teal_strata_brick_stairs`、`teal_strata_brick_wall` | tone pale／cyan |

## 搖籃曲山丘（`lullaby_hills`）

| 層位 | 現有方塊 | 貼圖數* | 參考石材 | 升級的方塊（含衍生） | 備註 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 台地地表 | `void_capped_crimson_01` | 3 | R20 鐵染玄武岩、R19 玄武岩 | 本體（單一方塊，無衍生） | 頂面鐵染玄武岩、底面玄武岩、側面兩者交界 |
| 岩壁 | `crimson_vein_stone` | 8 | R08 玫瑰大理石 | 本體＋8 個衍生：`crimson_vein_stone_bricks`、`chiseled_crimson_vein_stone_bricks`、`crimson_vein_stone_slab`、`crimson_vein_stone_stairs`、`crimson_vein_stone_wall`、`crimson_vein_stone_brick_slab`、`crimson_vein_stone_brick_stairs`、`crimson_vein_stone_brick_wall` | crimson_spread 0~4：灰紫底 → 粉紅（spread 4 整塊玫瑰大理石；spread 3、4 是牆面） |
| 谷地 | `ash_marble` | 6 | R13 卡拉拉大理石 | 本體（單一方塊，無衍生） | 與紫晶區共用，不重畫 |
| 河岸與河床 | `aurum_ore` | 2 | 四選一：R15 虎眼石、R16 褐鐵礦（葡萄狀）、R17 黃銅礦（虹彩）、R18 自然銅 | 本體（單一方塊，無衍生） | richness 0~1；**四種礦脈材質擇一**，礦脈佈滿整個方塊（richness 0 留較多灰色圍岩、1 幾乎全滿）；谷底砂岩層用 bleached_sandstone |

## 紅區洞穴（`red_zone_caves`）

| 層位 | 現有方塊 | 貼圖數* | 參考石材 | 升級的方塊（含衍生） | 備註 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 洞穴地面與天花板 | `crimson_capped_crimson_strata_3`、`silted_strata` | 6 | R04 粉紅凝灰岩、R05 粉紅砂岩、R09 層紋粉砂岩 | 本體（單一方塊，無衍生） | 與赤紅沉積峽谷共用同一組方塊，不重畫（洞穴的光照會改變觀感，進遊戲再看一次） |

## 地底 void_stone

| 層位 | 現有方塊 | 貼圖數* | 參考石材 | 升級的方塊（含衍生） | 備註 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 底岩（深度 5~8 格起） | `void_stone` | 10 | R19 玄武岩 | 本體＋8 個衍生：`void_stone_bricks`、`chiseled_void_stone_bricks`、`void_stone_slab`、`void_stone_stairs`、`void_stone_wall`、`void_stone_brick_slab`、`void_stone_brick_stairs`、`void_stone_brick_wall` | 只保留 tone dark → 玄武岩（施工中）；rusty、olive 之後刪除或改成別的方塊，見待辦 |

\* 貼圖數 = 本體資料夾的 PNG ＋（有建材組時）石磚、浮雕石磚資料夾的 PNG；半磚、階梯、牆直接用本體或石磚的貼圖，不另外畫。

## 二、工作量

- 要重畫的本體方塊：**22 種**（已排除共用與已完成的）。
- 連動升級的衍生方塊：**約 96 個**（半磚、階梯、牆等只改模型引用，不另畫貼圖）。
- 要重畫的 PNG：**約 135 張**（本體、石磚、浮雕石磚）；另外地表複合方塊的頂面在 `sift_ground/`（canyon_top_a~d、grove_top、grove_top_b 共 6 張）、側面沿用 `crimson_strata`，不重複計算。
- 浮雕石磚（`chiseled_*`）依 skill 規則要換成該生態域的生物頭像：柳絮林地 Harmonizer、紫晶深板岩區 Sculk Monstrosity、赤紅峽谷 Dartback、搖籃曲山丘 Echo Golem、紅區洞穴 Stalker；琥珀沙丘的 `chiseled_bleached_sandstone_bricks` 用 Monarch。

## 三、建議的施工順序

1. **地底 void_stone**（玄武岩、鐵染玄武岩、橄欖岩，9 張＋建材組）：全世界都會看到，先做。
2. **地表複合方塊**：赤紅峽谷、柳絮林地、紫晶區、搖籃曲山丘的地表（頂面 ＋ 側面）。
3. **地下層與路徑**：silted／abyssal／dark_slate、bleached／cracked sandstone、banded_mudstone、ash_marble。
4. **建材組**：每種石頭的石磚與浮雕石磚（浮雕換生物頭像）。

## 四、待辦

- [ ] **void_stone 只留第一種變體**：`void_stone` 之後只保留 tone `dark`（玄武岩）；`rusty`（`void_stone_f`）和 `olive`（`void_stone_e`）兩個 tone 會刪除或改成別的方塊，等使用者決定。注意 `void_stone_f` 也被 `gray_capped_void_stone`、`crimson_capped_violet_strata` 用到，刪之前要換掉。R20 鐵染玄武岩、R21 橄欖岩因此暫不畫。
- [ ] **R17 黃銅礦、R18 自然銅先不要套用**（使用者 2026-10-30）；`aurum_ore` 的礦脈材質還沒選定（剩 R15 虎眼石／R16 褐鐵礦）。
- [x] **地底 void_stone（玄武岩）**：本體 `void_stone_c`、石磚 `void_stone_b`／`void_stone_d`、雕紋 `chiseled_void_stone_bricks`（Stalker 頭像）、柱 `void_stone_h`＋六角柱頂面。

## 五、需要你確認

1. 色相保留生態域色系（預設）？還是改成更接近現實石材的顏色？（對照圖中間那張就是「保留色系」的樣子）
2. `aurum_ore` 的礦脈材質四選一：R15 虎眼石／R16 褐鐵礦／R17 黃銅礦／R18 自然銅。
3. 先做哪一批？
4. `bleached_sandstone`、`cracked_sandstone` 是否也算「砂岩不需要修改」？如果是，我會把它們和琥珀沙丘的地表一起拿掉。
