# 植被總表與 AI 產生貼圖待畫清單

由 `tools/build_art_requests.py` 產生，重跑會更新（不要手動改這份）。

**怎麼替換**：畫好後用同樣的檔名覆蓋 `src/main/resources/assets/pysift/textures/` 底下的檔案即可，路徑以下都省略這段。
產生這些圖的腳本已加上臨時圖保護（`tools/art_guard.py`），只要檔案和腳本上次畫的不同，重跑就不會蓋掉你的圖。

## A. 植被總表（40 種）

總覽圖：`art_requests/vegetation_todo_overview.png`（每格最多 3 張貼圖，第二行是狀態）。

- **使用者繪製**：你給的圖。**由使用者的圖轉出**：用你的圖套色盤、裁切或重新上色。
- **AI 產生**：腳本從零畫的臨時圖，列在下面 B 表，等你重畫。
- **匯入素材**：`sift_vegetation_assets.zip`、`rift_dimension_flora_assets.zip`，來源不確定，標成「待確認」。

| # | ID | 中文名 | 方塊模型 | 模型類型 | 貼圖（尺寸） | 物品圖示 | 材質來源 | 狀態 | 備註 |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | `soul_willow_log` | 靈魂柳原木 | `block/vegetation/soul_willow_log/soul_willow_log` | 柱狀方塊（cube_column） | `block/vegetation/soul_willow_log_side` 16x16<br>`block/vegetation/soul_willow_log/soul_willow_log_top` 16x16 | （用方塊模型） | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 2 | `soul_willow_leaves` | 靈魂柳葉 | `block/vegetation/soul_willow_leaves/soul_willow_leaves` | 方塊（cube_all） | `block/vegetation/soul_willow_leaves/soul_willow_leaves` 16x16 | （用方塊模型） | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 3 | `soul_willow_leaves_pale` | 淡藍靈魂柳葉 | `block/vegetation/soul_willow_leaves_pale/soul_willow_leaves_pale` | 方塊（cube_all） | `block/vegetation/soul_willow_leaves_pale/soul_willow_leaves_pale` 16x16 | （用方塊模型） | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 4 | `glowing_soul_willow_leaves` | 發光靈魂柳葉 | `block/vegetation/glowing_soul_willow_leaves/glowing_soul_willow_leaves` | 十字＋發光層 | `block/vegetation/glowing_soul_willow_leaves/soul_willow_leaves_glowing` 16x16 | （用方塊模型） | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 5 | `soul_willow_vine` | 靈魂柳垂藤 | `block/vegetation/soul_willow_vine/soul_willow_vine_side_0`<br>`block/vegetation/soul_willow_vine/soul_willow_vine_tip_side_0`<br>`block/vegetation/soul_willow_vine/soul_willow_vine_side_1`<br>`block/vegetation/soul_willow_vine/soul_willow_vine_tip_side_1`<br>`block/vegetation/soul_willow_vine/soul_willow_vine_side_2`<br>`block/vegetation/soul_willow_vine/soul_willow_vine_tip_side_2` | 藤（貼牆面） | `block/vegetation/_shared/soul_willow_vine_0` 16x16<br>`block/vegetation/_shared/soul_willow_vine_tip_0` 16x16<br>`block/vegetation/_shared/soul_willow_vine_1` 16x16<br>`block/vegetation/_shared/soul_willow_vine_tip_1` 16x16<br>`block/vegetation/_shared/soul_willow_vine_2` 16x16<br>`block/vegetation/_shared/soul_willow_vine_tip_2` 16x16 | `block/vegetation/_shared/soul_willow_vine_0` 16x16 | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 6 | `glowing_soul_willow_vine` | 發光靈魂柳垂藤 | `block/vegetation/glowing_soul_willow_vine/glowing_soul_willow_vine_side_0`<br>`block/vegetation/glowing_soul_willow_vine/glowing_soul_willow_vine_tip_side_0`<br>`block/vegetation/glowing_soul_willow_vine/glowing_soul_willow_vine_side_1`<br>`block/vegetation/glowing_soul_willow_vine/glowing_soul_willow_vine_tip_side_1`<br>`block/vegetation/glowing_soul_willow_vine/glowing_soul_willow_vine_side_2`<br>`block/vegetation/glowing_soul_willow_vine/glowing_soul_willow_vine_tip_side_2` | 藤（貼牆面） | `block/vegetation/_shared/soul_willow_vine_0` 16x16<br>`block/vegetation/_shared/soul_willow_vine_tip_0` 16x16<br>`block/vegetation/_shared/soul_willow_vine_1` 16x16<br>`block/vegetation/_shared/soul_willow_vine_tip_1` 16x16<br>`block/vegetation/_shared/soul_willow_vine_2` 16x16<br>`block/vegetation/_shared/soul_willow_vine_tip_2` 16x16 | `block/vegetation/_shared/soul_willow_vine_0` 16x16 | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 7 | `soul_willow_sapling` | 靈魂柳樹苗 | `block/vegetation/soul_willow_sapling/soul_willow_sapling` | 十字（自訂元素） | `block/vegetation/soul_willow_sapling/soul_willow_sapling` 16x16 | `block/vegetation/soul_willow_sapling/soul_willow_sapling` 16x16 | 待確認 | 已完成（來源待確認） |  |
| 8 | `bone_spire` | 骨刺 | `block/vegetation/bone_spire/bone_spire`<br>`block/vegetation/bone_spire/bone_spire_s80`<br>`block/vegetation/bone_spire/bone_spire_s120` | 十字（自訂元素） | `block/vegetation/bone_spire/bone_spire` 16x16 | `block/vegetation/bone_spire/bone_spire` 16x16 | 待確認 | 已完成（來源待確認） |  |
| 9 | `puff_grass` | 蓬鬆草 | `block/vegetation/puff_grass/puff_grass_bottom`<br>`block/vegetation/puff_grass/puff_grass_top` | 兩格高（上／下半）・十字（自訂元素） | `block/vegetation/puff_grass/puff_grass_bottom` 16x16<br>`block/vegetation/puff_grass/puff_grass_top` 16x16 | `block/vegetation/puff_grass/puff_grass_top` 16x16 | 待確認 | 已完成（來源待確認） |  |
| 10 | `dusk_bloom` | 暮綻花 | `block/vegetation/dusk_bloom/dusk_bloom` | 3D 模型（Blockbench／腳本） | `block/vegetation/dusk_bloom/dusk_bloom` 32x32 | `item/dusk_bloom` 21x21 | 使用者的 Blockbench 模型（待確認） | 已完成（來源待確認） |  |
| 11 | `rift_orange_short_grass` | 裂隙橙短草 | `block/vegetation/rift_orange_short_grass/rift_orange_short_grass` | 原版十字 | `block/vegetation/rift_orange_short_grass/sift_orange_short_grass` 16x16 | `block/vegetation/rift_orange_short_grass/sift_orange_short_grass` 16x16 | 待確認 | 合併後換新材質（待確認） | 原 orange_rift_grass，併入 sift_orange_short_grass 的新材質 |
| 12 | `rift_orange_tall_grass` | 裂隙橙高草 | `block/vegetation/rift_orange_tall_grass/rift_orange_tall_grass_bottom`<br>`block/vegetation/rift_orange_tall_grass/rift_orange_tall_grass` | 兩格高（上／下半）・原版十字 | `block/vegetation/rift_orange_tall_grass/sift_orange_tall_grass_down` 16x16<br>`block/vegetation/rift_orange_tall_grass/sift_orange_tall_grass_top` 16x16 | `block/vegetation/rift_orange_tall_grass/sift_orange_tall_grass_top` 16x16 | 待確認 | 合併後換新材質（待確認） | 原 orange_tall_rift_grass，併入 sift_orange_tall_grass 的新材質 |
| 13 | `rift_mint_short_grass` | 裂隙薄荷短草 | `block/vegetation/rift_mint_short_grass/rift_mint_short_grass` | 原版十字 | `block/vegetation/rift_mint_short_grass/sift_short_grass` 16x16 | `block/vegetation/rift_mint_short_grass/sift_short_grass` 16x16 | 待確認 | 合併後換新材質（待確認） | 原 mint_rift_grass，併入 sift_short_grass 的新材質 |
| 14 | `rift_mint_tall_grass` | 裂隙薄荷高草 | `block/vegetation/rift_mint_tall_grass/rift_mint_tall_grass_bottom`<br>`block/vegetation/rift_mint_tall_grass/rift_mint_tall_grass` | 兩格高（上／下半）・原版十字 | `block/vegetation/rift_mint_tall_grass/rift_mint_tall_grass_down` 16x16<br>`block/vegetation/rift_mint_tall_grass/rift_mint_tall_grass_top` 16x16 | `block/vegetation/rift_mint_tall_grass/rift_mint_tall_grass_top` 16x16 | 待確認 | 合併後換新材質（待確認） | 原 sift_tallgrass，成為薄荷短草的高草版 |
| 15 | `olive_forked_stalk` | 橄欖叉莖 | `block/vegetation/olive_forked_stalk/olive_forked_stalk` | 原版十字 | `block/vegetation/olive_forked_stalk/olive_forked_stalk` 16x16 | `block/vegetation/olive_forked_stalk/olive_forked_stalk` 16x16 | 匯入素材 rift_dimension_flora（待確認） | 已完成（來源待確認） |  |
| 16 | `blue_curled_fern` | 藍捲蕨 | `block/vegetation/blue_curled_fern/blue_curled_fern` | 十字（自訂元素） | `block/vegetation/blue_curled_fern/blue_curled_fern` 16x16 | `block/vegetation/blue_curled_fern/blue_curled_fern` 16x16 | 匯入素材 rift_dimension_flora（待確認） | 已完成（來源待確認） |  |
| 17 | `pink_curled_fern` | 粉捲蕨 | `block/vegetation/pink_curled_fern/pink_curled_fern` | 十字（自訂元素） | `block/vegetation/pink_curled_fern/pink_curled_fern` 16x16 | `block/vegetation/pink_curled_fern/pink_curled_fern` 16x16 | 匯入素材 rift_dimension_flora（待確認） | 已完成（來源待確認） |  |
| 18 | `yellow_agave` | 黃龍舌蘭 | `block/vegetation/yellow_agave/yellow_agave` | 3D 模型（Blockbench／腳本） | `block/vegetation/yellow_agave/yellow_agave_leaf` 16x16 | `item/yellow_agave` 32x32 | 匯入素材 rift_dimension_flora（待確認）<br>由模型算繪（veg_models.py icon） | 已完成（來源待確認） |  |
| 19 | `blue_giant_canopy` | 藍巨傘草 | `block/vegetation/blue_giant_canopy/blue_giant_canopy` | 3D 模型（Blockbench／腳本） | `block/vegetation/blue_giant_canopy/canopy_leaf_blue` 16x16<br>`block/vegetation/blue_giant_canopy/canopy_stem_blue` 16x16 | `item/blue_giant_canopy` 32x32 | 匯入素材 rift_dimension_flora（待確認）<br>由模型算繪（veg_models.py icon） | 已完成（來源待確認） |  |
| 20 | `clustered_yellow_flowers` | 簇生黃花 | `block/vegetation/clustered_yellow_flowers/clustered_yellow_flowers` | 3D 模型（Blockbench／腳本） | `block/vegetation/clustered_yellow_flowers/yellow_flower_head` 16x16<br>`block/vegetation/clustered_yellow_flowers/yellow_flower_stem` 16x16 | `item/clustered_yellow_flowers` 32x32 | 匯入素材 rift_dimension_flora（待確認）<br>由模型算繪（veg_models.py icon） | 已完成（來源待確認） |  |
| 21 | `coral_leaf_carpet` | 珊瑚落葉 | `block/vegetation/coral_leaf_carpet/coral_leaf_carpet_1`<br>`block/vegetation/coral_leaf_carpet/coral_leaf_carpet_2`<br>`block/vegetation/coral_leaf_carpet/coral_leaf_carpet_3`<br>`block/vegetation/coral_leaf_carpet/coral_leaf_carpet_4` | 原版花床（1~4 層） | `block/vegetation/coral_leaf_carpet/coral_leaf_carpet` 16x16<br>`block/vegetation/coral_leaf_carpet/coral_leaf_carpet_stem` 16x16 | `item/coral_leaf_carpet` 16x16 | AI 產生（gen_batch3.py） | 暫用（待補畫） |  |
| 22 | `soft_crimson_short_grass` | 柔和赤紅短草 | `block/vegetation/soft_crimson_short_grass/soft_crimson_short_grass` | 原版十字 | `block/vegetation/soft_crimson_short_grass/soft_crimson_short_grass` 16x16 | `block/vegetation/soft_crimson_short_grass/soft_crimson_short_grass` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 23 | `soft_crimson_tall_grass` | 柔和赤紅高草 | `block/vegetation/soft_crimson_tall_grass/soft_crimson_tall_grass_bottom`<br>`block/vegetation/soft_crimson_tall_grass/soft_crimson_tall_grass_top` | 兩格高（上／下半）・原版十字 | `block/vegetation/soft_crimson_tall_grass/soft_crimson_tall_grass_bottom` 16x16<br>`block/vegetation/soft_crimson_tall_grass/soft_crimson_tall_grass_top` 16x16 | `block/vegetation/soft_crimson_tall_grass/soft_crimson_tall_grass_top` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 24 | `soft_violet_short_grass` | 柔和紫晶短草 | `block/vegetation/soft_violet_short_grass/soft_violet_short_grass` | 原版十字 | `block/vegetation/soft_violet_short_grass/soft_violet_short_grass` 16x16 | `block/vegetation/soft_violet_short_grass/soft_violet_short_grass` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 25 | `soft_violet_tall_grass` | 柔和紫晶高草 | `block/vegetation/soft_violet_tall_grass/soft_violet_tall_grass_bottom`<br>`block/vegetation/soft_violet_tall_grass/soft_violet_tall_grass_top` | 兩格高（上／下半）・原版十字 | `block/vegetation/soft_violet_tall_grass/soft_violet_tall_grass_bottom` 16x16<br>`block/vegetation/soft_violet_tall_grass/soft_violet_tall_grass_top` 16x16 | `block/vegetation/soft_violet_tall_grass/soft_violet_tall_grass_top` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 26 | `soft_dune_short_grass` | 柔和沙丘短草 | `block/vegetation/soft_dune_short_grass/soft_dune_short_grass` | 原版十字 | `block/vegetation/soft_dune_short_grass/soft_dune_short_grass` 16x16 | `block/vegetation/soft_dune_short_grass/soft_dune_short_grass` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 27 | `soft_dune_tall_grass` | 柔和沙丘高草 | `block/vegetation/soft_dune_tall_grass/soft_dune_tall_grass_bottom`<br>`block/vegetation/soft_dune_tall_grass/soft_dune_tall_grass_top` | 兩格高（上／下半）・原版十字 | `block/vegetation/soft_dune_tall_grass/soft_dune_tall_grass_bottom` 16x16<br>`block/vegetation/soft_dune_tall_grass/soft_dune_tall_grass_top` 16x16 | `block/vegetation/soft_dune_tall_grass/soft_dune_tall_grass_top` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 28 | `soft_teal_short_grass` | 柔和青碧短草 | `block/vegetation/soft_teal_short_grass/soft_teal_short_grass` | 原版十字 | `block/vegetation/soft_teal_short_grass/soft_teal_short_grass` 16x16 | `block/vegetation/soft_teal_short_grass/soft_teal_short_grass` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 29 | `soft_teal_tall_grass` | 柔和青碧高草 | `block/vegetation/soft_teal_tall_grass/soft_teal_tall_grass_bottom`<br>`block/vegetation/soft_teal_tall_grass/soft_teal_tall_grass_top` | 兩格高（上／下半）・原版十字 | `block/vegetation/soft_teal_tall_grass/soft_teal_tall_grass_bottom` 16x16<br>`block/vegetation/soft_teal_tall_grass/soft_teal_tall_grass_top` 16x16 | `block/vegetation/soft_teal_tall_grass/soft_teal_tall_grass_top` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 30 | `carapace_flower` | 甲殼花 | `block/vegetation/carapace_flower/carapace_flower` | 原版十字 | `block/vegetation/carapace_flower/carapace_flower` 16x16 | `block/vegetation/carapace_flower/carapace_flower` 16x16 | 待確認 | 已完成（來源待確認） | 新匯入 |
| 31 | `carapace_short_grass` | 甲殼短草 | `block/vegetation/carapace_short_grass/carapace_short_grass` | 原版十字 | `block/vegetation/carapace_short_grass/carapace_shortgrass` 16x16 | `block/vegetation/carapace_short_grass/carapace_shortgrass` 16x16 | 待確認 | 已完成（來源待確認） | 新匯入 |
| 32 | `carapace_vine` | 甲殼藤 | `block/vegetation/carapace_vine/carapace_vine` | 藤（貼牆面） | `block/vegetation/carapace_vine/carapace_vine` 16x16 | `item/carapace_vine` 16x16 | 待確認<br>匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 33 | `yellow_flower_patch` | 黃色小花叢 | `block/vegetation/yellow_flower_patch/yellow_flower_patch` | 原版十字 | `block/vegetation/yellow_flower_patch/yellow_flower_patch` 16x16 | `block/vegetation/yellow_flower_patch/yellow_flower_patch` 16x16 | 待確認 | 已完成（來源待確認） | 新匯入 |
| 34 | `green_sift_vine` | 綠隙浮藤 | `block/vegetation/green_sift_vine/green_sift_vine` | 藤（貼牆面） | `block/vegetation/green_sift_vine/green_sift_vine` 16x16 | `item/green_sift_vine` 16x16 | 待確認<br>匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 35 | `orange_sift_vine` | 橙隙浮藤 | `block/vegetation/orange_sift_vine/orange_sift_vine` | 藤（貼牆面） | `block/vegetation/orange_sift_vine/orange_sift_vine` 16x16 | `item/orange_sift_vine` 16x16 | 待確認<br>匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 36 | `cleaver_plant` | 劈裂草 | `block/vegetation/cleaver_plant/cleaver_plant` | 3D 模型（Blockbench／腳本） | `block/vegetation/cleaver_plant/cleaver_plant` 32x32 | `item/cleaver_plant` 16x16 | 待確認<br>匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 37 | `soul_cleaver_plant` | 靈魂劈裂草 | `block/vegetation/soul_cleaver_plant/soul_cleaver_plant` | 3D 模型（Blockbench／腳本） | `block/vegetation/soul_cleaver_plant/soul_cleaver_plant` 32x32 | `item/soul_cleaver_plant` 16x16 | 待確認<br>匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 38 | `yellow_leaf_litter` | 黃色落葉 | `block/vegetation/yellow_leaf_litter/yellow_leaf_litter` | 3D 模型（Blockbench／腳本） | `block/vegetation/yellow_leaf_litter/yellow_leaf_litter` 32x32 | `item/yellow_leaf_litter` 32x32 | 待確認<br>匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 39 | `glowshade_short_grass` | 夜光短草 | `block/vegetation/glowshade_short_grass/glowshade_short_grass` | 十字＋發光層 | `block/vegetation/glowshade_short_grass/sculk_grass` 16x16<br>`block/vegetation/glowshade_short_grass/glowshade_short_grass_glow` 16x16 | `block/vegetation/glowshade_short_grass/sculk_grass` 16x16 | 待確認 | 合併後換新材質（待確認） | 原 glowshade_grass，草葉改用 sculk_grass（幽匿草）貼圖，發光層重新對齊 |
| 40 | `glowshade_tuft` | 夜光草叢 | `block/vegetation/glowshade_tuft/glowshade_tuft` | 十字＋發光層 | `block/vegetation/glowshade_tuft/glowshade_tuft` 16x16<br>`block/vegetation/glowshade_tuft/glowshade_tuft_glow` 16x16 | `block/vegetation/glowshade_tuft/glowshade_tuft` 16x16 | 待確認 | 已完成（來源待確認） |  |

## B. AI 產生與待確認的貼圖（99 張，全專案）

總覽圖：`art_requests/ai_textures_overview.png`。類別：**AI** = 腳本從零畫的；**轉出** = 由你的圖或原版貼圖重新上色／裁切，可以沿用也可以重畫；**待確認** = 腳本畫過但可能已換成你的圖，或是匯入素材、來源不明的圖：是你畫的就保留，不是就重畫。

| # | 檔案 | 用途 | 尺寸 | 產生腳本／來源 | 類別 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | `item/coral_leaf_carpet.png` | 珊瑚落葉 物品圖示 | 16x16 | `tools/models/gen_batch3.py` | AI |
| 2 | `item/bloombud_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 3 | `item/blub_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 4 | `item/dartback_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 5 | `item/echo_golem_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 6 | `item/fusefly_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 7 | `item/harmonizer_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 8 | `item/hunter_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 9 | `item/hurler_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 10 | `item/lootkin_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 11 | `item/monarch_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 12 | `item/nester_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 13 | `item/nuzzle_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 14 | `item/pollinator_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 15 | `item/prickle_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 16 | `item/roamroot_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 17 | `item/scavenger_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 18 | `item/sculk_monstrosity_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 19 | `item/seedling_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 20 | `item/sentinel_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 21 | `item/singer_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 22 | `item/slabber_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 23 | `item/sprout_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 24 | `item/stalker_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 25 | `item/trapper_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 26 | `item/tuner_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 27 | `item/wobble_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 28 | `mob_effect/ensnared.png` | 定身效果圖示 | 18x18 | `tools/models/hunter_trapper_assets.py` | AI |
| 29 | `mob_effect/soul_deprivation.png` | 靈魂剝奪效果圖示（只在缺檔時寫） | 18x18 | `tools/worldgen/build_vegetation.py` | 待確認 |
| 30 | `item/soul_antidote.png` | 靈魂解藥 | 16x16 | `tools/items/make_soul_burn_textures.py` | AI |
| 31 | `particle/soul_wisp.png` | 靈魂幽火粒子 | 12x12 | `tools/worldgen/make_soul_wisp_textures.py` | AI |
| 32 | `particle/soul_trail.png` | 靈魂拖尾粒子 | 8x8 | `tools/worldgen/make_soul_wisp_textures.py` | AI |
| 33 | `gui/sprites/hud/heart/soul_full.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 34 | `gui/sprites/hud/heart/soul_full_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 35 | `gui/sprites/hud/heart/soul_half.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 36 | `gui/sprites/hud/heart/soul_half_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 37 | `gui/sprites/hud/heart/soul_hardcore_full.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 38 | `gui/sprites/hud/heart/soul_hardcore_full_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 39 | `gui/sprites/hud/heart/soul_hardcore_half.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 40 | `gui/sprites/hud/heart/soul_hardcore_half_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 41 | `block/soul_willow/soul_willow_door_bottom.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 42 | `block/soul_willow/soul_willow_door_top.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 43 | `block/soul_willow/soul_willow_hanging_sign.png` | 靈柳木建材組（原版橡木重新上色） | 32x32 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 44 | `block/soul_willow/soul_willow_planks.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 45 | `block/soul_willow/soul_willow_shelf.png` | 靈柳木建材組（原版橡木重新上色） | 32x32 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 46 | `block/soul_willow/soul_willow_sign.png` | 靈柳木建材組（原版橡木重新上色） | 32x32 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 47 | `block/soul_willow/soul_willow_trapdoor.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 48 | `block/soul_willow/stripped_soul_willow_log.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 49 | `block/soul_willow/stripped_soul_willow_log_top.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 50 | `item/soul_willow_boat.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 51 | `item/soul_willow_chest_boat.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 52 | `item/soul_willow_door.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 53 | `item/soul_willow_hanging_sign.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 54 | `item/soul_willow_sign.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 55 | `entity/boat/soul_willow.png` | 靈柳木船 | 128x64 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 56 | `entity/chest_boat/soul_willow.png` | 靈柳木運輸船 | 128x128 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 57 | `block/soul_crystal_block.png` | 靈魂晶塊（取自 echo_golem 貼圖） | 16x16 | `tools/worldgen/build_soul_crystal.py` | 轉出 |
| 58 | `entity/hunter.png` | Hunter（可能已換成使用者的合併貼圖） | 64x64 | `tools/entity/build_sift_creatures.py` | 待確認 |
| 59 | `entity/trapper.png` | Trapper（可能已換成使用者的合併貼圖） | 64x64 | `tools/entity/build_sift_creatures.py` | 待確認 |
| 60 | `entity/sculk_cube.png` | 幽匿方塊 | 64x64 | `tools/entity/build_sift_creatures.py` | 待確認 |
| 61 | `block/vegetation/soul_willow_sapling/soul_willow_sapling.png` | 靈魂柳樹苗 貼圖 | 16x16 | 待確認 | 待確認 |
| 62 | `block/vegetation/bone_spire/bone_spire.png` | 骨刺 貼圖 | 16x16 | 待確認 | 待確認 |
| 63 | `block/vegetation/puff_grass/puff_grass_bottom.png` | 蓬鬆草 貼圖 | 16x16 | 待確認 | 待確認 |
| 64 | `block/vegetation/puff_grass/puff_grass_top.png` | 蓬鬆草 貼圖 | 16x16 | 待確認 | 待確認 |
| 65 | `block/vegetation/dusk_bloom/dusk_bloom.png` | 暮綻花 貼圖 | 32x32 | 使用者的 Blockbench 模型 | 待確認 |
| 66 | `item/dusk_bloom.png` | 暮綻花 物品圖示 | 21x21 | 使用者的 Blockbench 模型 | 待確認 |
| 67 | `block/vegetation/rift_orange_short_grass/sift_orange_short_grass.png` | 裂隙橙短草 貼圖 | 16x16 | 待確認 | 待確認 |
| 68 | `block/vegetation/rift_orange_tall_grass/sift_orange_tall_grass_down.png` | 裂隙橙高草 貼圖 | 16x16 | 待確認 | 待確認 |
| 69 | `block/vegetation/rift_orange_tall_grass/sift_orange_tall_grass_top.png` | 裂隙橙高草 貼圖 | 16x16 | 待確認 | 待確認 |
| 70 | `block/vegetation/rift_mint_short_grass/sift_short_grass.png` | 裂隙薄荷短草 貼圖 | 16x16 | 待確認 | 待確認 |
| 71 | `block/vegetation/rift_mint_tall_grass/rift_mint_tall_grass_down.png` | 裂隙薄荷高草 貼圖 | 16x16 | 待確認 | 待確認 |
| 72 | `block/vegetation/rift_mint_tall_grass/rift_mint_tall_grass_top.png` | 裂隙薄荷高草 貼圖 | 16x16 | 待確認 | 待確認 |
| 73 | `block/vegetation/olive_forked_stalk/olive_forked_stalk.png` | 橄欖叉莖 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 74 | `block/vegetation/blue_curled_fern/blue_curled_fern.png` | 藍捲蕨 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 75 | `block/vegetation/pink_curled_fern/pink_curled_fern.png` | 粉捲蕨 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 76 | `block/vegetation/yellow_agave/yellow_agave_leaf.png` | 黃龍舌蘭 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 77 | `block/vegetation/blue_giant_canopy/canopy_leaf_blue.png` | 藍巨傘草 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 78 | `block/vegetation/blue_giant_canopy/canopy_stem_blue.png` | 藍巨傘草 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 79 | `block/vegetation/clustered_yellow_flowers/yellow_flower_head.png` | 簇生黃花 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 80 | `block/vegetation/clustered_yellow_flowers/yellow_flower_stem.png` | 簇生黃花 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 81 | `block/vegetation/carapace_flower/carapace_flower.png` | 甲殼花 貼圖 | 16x16 | 待確認 | 待確認 |
| 82 | `block/vegetation/carapace_short_grass/carapace_shortgrass.png` | 甲殼短草 貼圖 | 16x16 | 待確認 | 待確認 |
| 83 | `block/vegetation/carapace_vine/carapace_vine.png` | 甲殼藤 貼圖 | 16x16 | 待確認 | 待確認 |
| 84 | `item/carapace_vine.png` | 甲殼藤 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 85 | `block/vegetation/yellow_flower_patch/yellow_flower_patch.png` | 黃色小花叢 貼圖 | 16x16 | 待確認 | 待確認 |
| 86 | `block/vegetation/green_sift_vine/green_sift_vine.png` | 綠隙浮藤 貼圖 | 16x16 | 待確認 | 待確認 |
| 87 | `item/green_sift_vine.png` | 綠隙浮藤 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 88 | `block/vegetation/orange_sift_vine/orange_sift_vine.png` | 橙隙浮藤 貼圖 | 16x16 | 待確認 | 待確認 |
| 89 | `item/orange_sift_vine.png` | 橙隙浮藤 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 90 | `block/vegetation/cleaver_plant/cleaver_plant.png` | 劈裂草 貼圖 | 32x32 | 待確認 | 待確認 |
| 91 | `item/cleaver_plant.png` | 劈裂草 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 92 | `block/vegetation/soul_cleaver_plant/soul_cleaver_plant.png` | 靈魂劈裂草 貼圖 | 32x32 | 待確認 | 待確認 |
| 93 | `item/soul_cleaver_plant.png` | 靈魂劈裂草 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 94 | `block/vegetation/yellow_leaf_litter/yellow_leaf_litter.png` | 黃色落葉 貼圖 | 32x32 | 待確認 | 待確認 |
| 95 | `item/yellow_leaf_litter.png` | 黃色落葉 物品圖示 | 32x32 | 匯入素材 sift_vegetation_assets | 待確認 |
| 96 | `block/vegetation/glowshade_short_grass/sculk_grass.png` | 夜光短草 貼圖 | 16x16 | 待確認 | 待確認 |
| 97 | `block/vegetation/glowshade_short_grass/glowshade_short_grass_glow.png` | 夜光短草 貼圖 | 16x16 | 待確認 | 待確認 |
| 98 | `block/vegetation/glowshade_tuft/glowshade_tuft.png` | 夜光草叢 貼圖 | 16x16 | 待確認 | 待確認 |
| 99 | `block/vegetation/glowshade_tuft/glowshade_tuft_glow.png` | 夜光草叢 貼圖 | 16x16 | 待確認 | 待確認 |
