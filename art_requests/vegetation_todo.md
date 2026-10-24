# 植被總表與 AI 產生貼圖待畫清單

由 `tools/build_art_requests.py` 產生，重跑會更新（不要手動改這份）。

**怎麼替換**：畫好後用同樣的檔名覆蓋 `src/main/resources/assets/pysift/textures/` 底下的檔案即可，路徑以下都省略這段。
產生這些圖的腳本已加上臨時圖保護（`tools/art_guard.py`），只要檔案和腳本上次畫的不同，重跑就不會蓋掉你的圖。

## A. 植被總表（60 種）

總覽圖：`art_requests/vegetation_todo_overview.png`（每格最多 3 張貼圖，第二行是狀態）。

- **使用者繪製**：你給的圖。**由使用者的圖轉出**：用你的圖套色盤、裁切或重新上色。
- **AI 產生**：腳本從零畫的臨時圖，列在下面 B 表，等你重畫。
- **匯入素材**：`sift_vegetation_assets.zip`、`rift_dimension_flora_assets.zip`，來源不確定，標成「待確認」。

| # | ID | 中文名 | 方塊模型 | 模型類型 | 貼圖（尺寸） | 物品圖示 | 材質來源 | 狀態 | 備註 |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | `soul_willow_log` | 靈魂柳原木 | `block/vegetation/soul_willow_log` | 柱狀方塊（cube_column） | `block/vegetation/soul_willow_log_side` 16x16<br>`block/vegetation/soul_willow_log_top` 16x16 | （用方塊模型） | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 2 | `soul_willow_leaves` | 靈魂柳葉 | `block/vegetation/soul_willow_leaves` | 方塊（cube_all） | `block/vegetation/soul_willow_leaves` 16x16 | （用方塊模型） | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 3 | `soul_willow_leaves_pale` | 淡藍靈魂柳葉 | `block/vegetation/soul_willow_leaves_pale` | 方塊（cube_all） | `block/vegetation/soul_willow_leaves_pale` 16x16 | （用方塊模型） | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 4 | `glowing_soul_willow_leaves` | 發光靈魂柳葉 | `block/vegetation/glowing_soul_willow_leaves` | 十字＋發光層 | `block/vegetation/soul_willow_leaves_glowing` 16x16 | （用方塊模型） | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 5 | `soul_willow_vine` | 靈魂柳垂藤 | `block/vegetation/soul_willow_vine_side_0`<br>`block/vegetation/soul_willow_vine_tip_side_0`<br>`block/vegetation/soul_willow_vine_side_1`<br>`block/vegetation/soul_willow_vine_tip_side_1`<br>`block/vegetation/soul_willow_vine_side_2`<br>`block/vegetation/soul_willow_vine_tip_side_2` | 藤（貼牆面） | `block/vegetation/soul_willow_vine_0` 16x16<br>`block/vegetation/soul_willow_vine_tip_0` 16x16<br>`block/vegetation/soul_willow_vine_1` 16x16<br>`block/vegetation/soul_willow_vine_tip_1` 16x16<br>`block/vegetation/soul_willow_vine_2` 16x16<br>`block/vegetation/soul_willow_vine_tip_2` 16x16 | `block/vegetation/soul_willow_vine_0` 16x16 | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 6 | `glowing_soul_willow_vine` | 發光靈魂柳垂藤 | `block/vegetation/glowing_soul_willow_vine_side_0`<br>`block/vegetation/glowing_soul_willow_vine_tip_side_0`<br>`block/vegetation/glowing_soul_willow_vine_side_1`<br>`block/vegetation/glowing_soul_willow_vine_tip_side_1`<br>`block/vegetation/glowing_soul_willow_vine_side_2`<br>`block/vegetation/glowing_soul_willow_vine_tip_side_2` | 藤（貼牆面） | `block/vegetation/soul_willow_vine_0` 16x16<br>`block/vegetation/soul_willow_vine_tip_0` 16x16<br>`block/vegetation/soul_willow_vine_1` 16x16<br>`block/vegetation/soul_willow_vine_tip_1` 16x16<br>`block/vegetation/soul_willow_vine_2` 16x16<br>`block/vegetation/soul_willow_vine_tip_2` 16x16 | `block/vegetation/soul_willow_vine_0` 16x16 | 由使用者的圖轉出（soul_willow_sheet.png） | 已完成 |  |
| 7 | `soul_willow_sapling` | 靈魂柳樹苗 | `block/vegetation/soul_willow_sapling` | 十字（自訂元素） | `block/vegetation/soul_willow_sapling` 16x16 | `block/vegetation/soul_willow_sapling` 16x16 | 待確認 | 已完成（來源待確認） |  |
| 8 | `humus_fern` | 腐殖蕨 | `block/vegetation/humus_fern`<br>`block/vegetation/humus_fern_s120`<br>`block/vegetation/humus_fern_s134` | 3D 模型（Blockbench／腳本） | `block/vegetation/humus_fern` 16x16 | `item/humus_fern` 32x32 | AI 產生（gen_blade_models.py）<br>由模型算繪（veg_models.py icon） | 暫用（待補畫） |  |
| 9 | `humus_bush` | 腐殖灌木 | `block/vegetation/humus_bush`<br>`block/vegetation/humus_bush_s120`<br>`block/vegetation/humus_bush_s134` | 3D 模型（Blockbench／腳本） | `block/vegetation/humus_bush` 16x16 | `item/humus_bush` 32x32 | AI 產生（gen_blade_models.py）<br>由模型算繪（veg_models.py icon） | 暫用（待補畫） |  |
| 10 | `bone_spire` | 骨刺 | `block/vegetation/bone_spire`<br>`block/vegetation/bone_spire_s80`<br>`block/vegetation/bone_spire_s120` | 十字（自訂元素） | `block/vegetation/bone_spire` 16x16 | `block/vegetation/bone_spire` 16x16 | AI 產生（make_decor_textures.py） | 暫用（待補畫） |  |
| 11 | `puff_grass` | 蓬鬆草 | `block/vegetation/puff_grass_bottom`<br>`block/vegetation/puff_grass_top` | 兩格高（上／下半）・十字（自訂元素） | `block/vegetation/puff_grass_bottom` 16x16<br>`block/vegetation/puff_grass_top` 16x16 | `block/vegetation/puff_grass_top` 16x16 | AI 產生（make_decor_textures.py） | 暫用（待補畫） |  |
| 12 | `golden_bloom` | 金綻花 | `block/vegetation/golden_bloom`<br>`block/vegetation/golden_bloom_s80`<br>`block/vegetation/golden_bloom_s120` | 3D 模型（Blockbench／腳本） | `block/vegetation/golden_bloom` 128x128 | `item/golden_bloom` 32x32 | 使用者的 Blockbench 模型（待確認） | 已完成（來源待確認） |  |
| 13 | `sun_bloom` | 陽綻花 | `block/vegetation/sun_bloom`<br>`block/vegetation/sun_bloom_s80`<br>`block/vegetation/sun_bloom_s120` | 3D 模型（Blockbench／腳本） | `block/vegetation/sun_bloom` 64x64 | `item/sun_bloom` 32x32 | 使用者的 Blockbench 模型（待確認） | 已完成（來源待確認） |  |
| 14 | `rose_bloom` | 玫綻花 | `block/vegetation/rose_bloom`<br>`block/vegetation/rose_bloom_s80`<br>`block/vegetation/rose_bloom_s120` | 3D 模型（Blockbench／腳本） | `block/vegetation/rose_bloom` 64x64 | `item/rose_bloom` 32x32 | 使用者的 Blockbench 模型（待確認） | 已完成（來源待確認） |  |
| 15 | `dusk_bloom` | 暮綻花 | `block/vegetation/dusk_bloom`<br>`block/vegetation/dusk_bloom_s80`<br>`block/vegetation/dusk_bloom_s120` | 3D 模型（Blockbench／腳本） | `block/vegetation/dusk_bloom` 64x64 | `item/dusk_bloom` 32x32 | 使用者的 Blockbench 模型（待確認） | 已完成（來源待確認） |  |
| 16 | `rift_orange_short_grass` | 裂隙橙短草 | `block/rift_orange_short_grass` | 原版十字 | `block/sift_orange_short_grass` 16x16 | `block/sift_orange_short_grass` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 合併後換新材質（待確認） | 原 orange_rift_grass，併入 sift_orange_short_grass 的新材質 |
| 17 | `rift_orange_tall_grass` | 裂隙橙高草 | `block/rift_orange_tall_grass_bottom`<br>`block/rift_orange_tall_grass` | 兩格高（上／下半）・原版十字 | `block/sift_orange_tall_grass_down` 16x16<br>`block/sift_orange_tall_grass_top` 16x16 | `block/sift_orange_tall_grass_top` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 合併後換新材質（待確認） | 原 orange_tall_rift_grass，併入 sift_orange_tall_grass 的新材質 |
| 18 | `rift_red_short_grass` | 裂隙紅短草 | `block/rift_red_short_grass` | 原版十字 | `block/sift_red_tallgrass` 16x16 | `block/sift_red_tallgrass` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 合併後換新材質（待確認） | 原 crimson_short_sprouts，併入 sift_red_short_grass 的新材質 |
| 19 | `rift_mint_short_grass` | 裂隙薄荷短草 | `block/rift_mint_short_grass` | 原版十字 | `block/sift_short_grass` 16x16 | `block/sift_short_grass` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 合併後換新材質（待確認） | 原 mint_rift_grass，併入 sift_short_grass 的新材質 |
| 20 | `rift_mint_tall_grass` | 裂隙薄荷高草 | `block/rift_mint_tall_grass_bottom`<br>`block/rift_mint_tall_grass` | 兩格高（上／下半）・原版十字 | `block/rift_mint_tall_grass_down` 16x16<br>`block/rift_mint_tall_grass_top` 16x16 | `block/rift_mint_tall_grass_top` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 合併後換新材質（待確認） | 原 sift_tallgrass，成為薄荷短草的高草版 |
| 21 | `rift_yellow_short_grass` | 裂隙黃短草 | `block/vegetation/rift_yellow_short_grass` | 十字（自訂元素） | `block/vegetation/rift_yellow_short_grass` 16x16 | `block/vegetation/rift_yellow_short_grass` 16x16 | 匯入素材 rift_dimension_flora（待確認） | 已完成（來源待確認） |  |
| 22 | `olive_forked_stalk` | 橄欖叉莖 | `block/vegetation/olive_forked_stalk` | 原版十字 | `block/vegetation/olive_forked_stalk` 16x16 | `block/vegetation/olive_forked_stalk` 16x16 | 匯入素材 rift_dimension_flora（待確認） | 已完成（來源待確認） |  |
| 23 | `blue_curled_fern` | 藍捲蕨 | `block/vegetation/blue_curled_fern` | 十字（自訂元素） | `block/vegetation/blue_curled_fern` 16x16 | `block/vegetation/blue_curled_fern` 16x16 | 匯入素材 rift_dimension_flora（待確認） | 已完成（來源待確認） |  |
| 24 | `pink_curled_fern` | 粉捲蕨 | `block/vegetation/pink_curled_fern` | 十字（自訂元素） | `block/vegetation/pink_curled_fern` 16x16 | `block/vegetation/pink_curled_fern` 16x16 | 匯入素材 rift_dimension_flora（待確認） | 已完成（來源待確認） |  |
| 25 | `white_curled_fern` | 白捲蕨 | `block/vegetation/white_curled_fern` | 十字（自訂元素） | `block/vegetation/white_curled_fern` 16x16 | `block/vegetation/white_curled_fern` 16x16 | 匯入素材 rift_dimension_flora（待確認） | 已完成（來源待確認） |  |
| 26 | `yellow_agave` | 黃龍舌蘭 | `block/vegetation/yellow_agave` | 3D 模型（Blockbench／腳本） | `block/vegetation/yellow_agave_leaf` 16x16 | `item/yellow_agave` 32x32 | 匯入素材 rift_dimension_flora（待確認）<br>由模型算繪（veg_models.py icon） | 已完成（來源待確認） |  |
| 27 | `green_giant_canopy` | 綠巨傘草 | `block/vegetation/green_giant_canopy` | 3D 模型（Blockbench／腳本） | `block/vegetation/canopy_leaf_green` 32x32<br>`block/vegetation/canopy_stem_green` 32x32 | `item/green_giant_canopy` 32x32 | 匯入素材 rift_dimension_flora（待確認）<br>由模型算繪（veg_models.py icon） | 已完成（來源待確認） |  |
| 28 | `blue_giant_canopy` | 藍巨傘草 | `block/vegetation/blue_giant_canopy` | 3D 模型（Blockbench／腳本） | `block/vegetation/canopy_leaf_blue` 32x32<br>`block/vegetation/canopy_stem_blue` 32x32 | `item/blue_giant_canopy` 32x32 | 匯入素材 rift_dimension_flora（待確認）<br>由模型算繪（veg_models.py icon） | 已完成（來源待確認） |  |
| 29 | `white_giant_canopy` | 白巨傘草 | `block/vegetation/white_giant_canopy` | 3D 模型（Blockbench／腳本） | `block/vegetation/canopy_leaf_white` 32x32<br>`block/vegetation/canopy_stem_white` 32x32 | `item/white_giant_canopy` 32x32 | 匯入素材 rift_dimension_flora（待確認）<br>由模型算繪（veg_models.py icon） | 已完成（來源待確認） |  |
| 30 | `clustered_yellow_flowers` | 簇生黃花 | `block/vegetation/clustered_yellow_flowers` | 3D 模型（Blockbench／腳本） | `block/vegetation/yellow_flower_head` 16x16<br>`block/vegetation/yellow_flower_stem` 16x16 | `item/clustered_yellow_flowers` 32x32 | 匯入素材 rift_dimension_flora（待確認）<br>由模型算繪（veg_models.py icon） | 已完成（來源待確認） |  |
| 31 | `glowshade_tall_grass` | 夜光高草 | `block/vegetation/glowshade_tall_grass_bottom`<br>`block/vegetation/glowshade_tall_grass_top` | 兩格高（上／下半）・3D 模型（Blockbench／腳本） | `block/vegetation/glowshade_tall_grass` 16x16 | `item/glowshade_tall_grass` 32x32 | AI 產生（gen_batch3.py） | 暫用（待補畫） |  |
| 32 | `coral_leaf_carpet` | 珊瑚落葉 | `block/vegetation/coral_leaf_carpet_1`<br>`block/vegetation/coral_leaf_carpet_2`<br>`block/vegetation/coral_leaf_carpet_3`<br>`block/vegetation/coral_leaf_carpet_4` | 原版花床（1~4 層） | `block/vegetation/coral_leaf_carpet` 16x16<br>`block/vegetation/coral_leaf_carpet_stem` 16x16 | `item/coral_leaf_carpet` 16x16 | AI 產生（gen_batch3.py） | 暫用（待補畫） |  |
| 33 | `soft_crimson_short_grass` | 柔和赤紅短草 | `block/vegetation/soft_crimson_short_grass` | 原版十字 | `block/vegetation/soft_crimson_short_grass` 16x16 | `block/vegetation/soft_crimson_short_grass` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 34 | `soft_crimson_tall_grass` | 柔和赤紅高草 | `block/vegetation/soft_crimson_tall_grass_bottom`<br>`block/vegetation/soft_crimson_tall_grass_top` | 兩格高（上／下半）・原版十字 | `block/vegetation/soft_crimson_tall_grass_bottom` 16x16<br>`block/vegetation/soft_crimson_tall_grass_top` 16x16 | `block/vegetation/soft_crimson_tall_grass_top` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 35 | `soft_violet_short_grass` | 柔和紫晶短草 | `block/vegetation/soft_violet_short_grass` | 原版十字 | `block/vegetation/soft_violet_short_grass` 16x16 | `block/vegetation/soft_violet_short_grass` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 36 | `soft_violet_tall_grass` | 柔和紫晶高草 | `block/vegetation/soft_violet_tall_grass_bottom`<br>`block/vegetation/soft_violet_tall_grass_top` | 兩格高（上／下半）・原版十字 | `block/vegetation/soft_violet_tall_grass_bottom` 16x16<br>`block/vegetation/soft_violet_tall_grass_top` 16x16 | `block/vegetation/soft_violet_tall_grass_top` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 37 | `soft_dune_short_grass` | 柔和沙丘短草 | `block/vegetation/soft_dune_short_grass` | 原版十字 | `block/vegetation/soft_dune_short_grass` 16x16 | `block/vegetation/soft_dune_short_grass` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 38 | `soft_dune_tall_grass` | 柔和沙丘高草 | `block/vegetation/soft_dune_tall_grass_bottom`<br>`block/vegetation/soft_dune_tall_grass_top` | 兩格高（上／下半）・原版十字 | `block/vegetation/soft_dune_tall_grass_bottom` 16x16<br>`block/vegetation/soft_dune_tall_grass_top` 16x16 | `block/vegetation/soft_dune_tall_grass_top` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 39 | `soft_teal_short_grass` | 柔和青碧短草 | `block/vegetation/soft_teal_short_grass` | 原版十字 | `block/vegetation/soft_teal_short_grass` 16x16 | `block/vegetation/soft_teal_short_grass` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 40 | `soft_teal_tall_grass` | 柔和青碧高草 | `block/vegetation/soft_teal_tall_grass_bottom`<br>`block/vegetation/soft_teal_tall_grass_top` | 兩格高（上／下半）・原版十字 | `block/vegetation/soft_teal_tall_grass_bottom` 16x16<br>`block/vegetation/soft_teal_tall_grass_top` 16x16 | `block/vegetation/soft_teal_tall_grass_top` 16x16 | 由使用者的圖轉出（灰色母版＋色盤） | 已完成 |  |
| 41 | `carapace_flower` | 甲殼花 | `block/carapace_flower` | 原版十字 | `block/carapace_flower` 16x16 | `block/carapace_flower` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 42 | `carapace_short_grass` | 甲殼短草 | `block/carapace_short_grass` | 原版十字 | `block/carapace_shortgrass` 16x16 | `block/carapace_shortgrass` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 43 | `carapace_vine` | 甲殼藤 | `block/carapace_vine` | 自訂立體模型（models/custom） | `block/carapace_vine` 16x16 | `item/carapace_vine` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 44 | `white_flower_patch` | 白色小花叢 | `block/white_flower_patch` | 原版十字 | `block/white_flower_patch` 16x16 | `block/white_flower_patch` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 45 | `yellow_flower_patch` | 黃色小花叢 | `block/yellow_flower_patch` | 原版十字 | `block/yellow_flower_patch` 16x16 | `block/yellow_flower_patch` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 46 | `soul_bubble_flower` | 靈魂氣泡花 | `block/soul_bubble_flower` | 自訂立體模型（models/custom） | `block/soul_bubble_flower` 32x32 | `item/soul_bubble_flower` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 47 | `green_sift_vine` | 綠篩靈藤 | `block/green_sift_vine` | 自訂立體模型（models/custom） | `block/green_sift_vine` 16x16 | `item/green_sift_vine` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 48 | `orange_sift_vine` | 橙篩靈藤 | `block/orange_sift_vine` | 自訂立體模型（models/custom） | `block/orange_sift_vine` 16x16 | `item/orange_sift_vine` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 49 | `soul_vine` | 靈魂藤 | `block/soul_vine` | 原版十字 | `block/souls_vine` 16x16 | `item/souls_vine` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 50 | `sift_wall_leaves` | 篩靈攀牆葉 | `block/sift_wall_leaves` | 自訂立體模型（models/custom） | `block/sift_wall_leaves` 16x16 | （用方塊模型） | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 51 | `cleaver_plant` | 劈裂草 | `block/cleaver_plant` | 自訂立體模型（models/custom） | `block/cleaver_plant` 32x32 | `item/cleaver_plant` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 52 | `soul_cleaver_plant` | 靈魂劈裂草 | `block/soul_cleaver_plant` | 自訂立體模型（models/custom） | `block/soul_cleaver_plant` 32x32 | `item/soul_cleaver_plant` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 53 | `sift_wheat_sprout` | 篩靈小麥幼苗 | `block/sift_wheat_sprout` | 原版十字 | `block/sift_wheat_plant2` 15x16 | `block/sift_wheat_plant2` 15x16 | 匯入素材 sift_vegetation_assets（待確認） | 尺寸異常（15x16，十字模型會被拉伸） | 新匯入 |
| 54 | `sift_wheat_plant` | 篩靈小麥植株 | `block/sift_wheat_plant` | 原版十字 | `block/sift_wheat_plant` 16x16 | `block/sift_wheat_plant` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 55 | `sift_wheat` | 篩靈小麥 | `block/sift_wheat` | 自訂立體模型（models/custom） | `block/sift_wheat` 32x32<br>`block/sift_wheat_plant` 16x16 | （用方塊模型） | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 56 | `yellow_leaf_litter` | 黃色落葉 | `block/yellow_leaf_litter` | 自訂立體模型（models/custom） | `block/yellow_leaf_litter` 32x32 | `item/yellow_leaf_litter` 16x16 | 匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 57 | `glowshade_short_grass` | 夜光短草 | `block/progression/glowshade_short_grass` | 十字＋發光層 | `block/sculk_grass` 16x16<br>`block/progression/glowshade_short_grass_glow` 16x16 | `block/sculk_grass` 16x16 | 匯入素材 sift_vegetation_assets（待確認）<br>AI 產生（build_progression.py 臨時圖） | 合併後換新材質（待確認） | 原 glowshade_grass，草葉改用 sculk_grass（幽匿草）貼圖，發光層重新對齊 |
| 58 | `glowshade_tuft` | 夜光草叢 | `block/progression/glowshade_tuft` | 十字＋發光層 | `block/progression/glowshade_tuft` 16x16<br>`block/progression/glowshade_tuft_glow` 16x16 | `block/progression/glowshade_tuft` 16x16 | AI 產生（build_progression.py 臨時圖） | 暫用（待補畫） |  |
| 59 | `starlit_shrub` | 星光灌木 | `block/progression/starlit_shrub` | 十字＋發光層 | `block/progression/starlit_shrub` 16x16<br>`block/progression/starlit_shrub_glow` 16x16 | `block/progression/starlit_shrub` 16x16 | AI 產生（build_progression.py 臨時圖） | 暫用（待補畫） |  |
| 60 | `sift_pink_loam` | 粉壤土 | `block/vegetation/sift_pink_loam` | 方塊（cube_all） | `block/vegetation/sift_pink_loam` 16x16 | （用方塊模型） | 由圖轉出（make_pink_loam.py） | 已完成 |  |

## B. AI 產生與待確認的貼圖（130 張，全專案）

總覽圖：`art_requests/ai_textures_overview.png`。類別：**AI** = 腳本從零畫的；**轉出** = 由你的圖或原版貼圖重新上色／裁切，可以沿用也可以重畫；**待確認** = 腳本畫過但可能已換成你的圖，或是匯入素材、來源不明的圖：是你畫的就保留，不是就重畫。

| # | 檔案 | 用途 | 尺寸 | 產生腳本／來源 | 類別 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | `block/vegetation/humus_fern.png` | 腐殖蕨 葉片 | 16x16 | `tools/models/gen_blade_models.py` | AI |
| 2 | `block/vegetation/humus_bush.png` | 腐殖灌木 葉片 | 16x16 | `tools/models/gen_blade_models.py` | AI |
| 3 | `block/vegetation/bone_spire.png` | 骨刺 | 16x16 | `tools/worldgen/make_decor_textures.py` | AI |
| 4 | `block/vegetation/puff_grass_bottom.png` | 蓬鬆草（上／下半） | 16x16 | `tools/worldgen/make_decor_textures.py` | AI |
| 5 | `block/vegetation/puff_grass_top.png` | 蓬鬆草（上／下半） | 16x16 | `tools/worldgen/make_decor_textures.py` | AI |
| 6 | `block/vegetation/glowshade_tall_grass.png` | 夜光高草 葉片 | 16x16 | `tools/models/gen_batch3.py` | AI |
| 7 | `item/glowshade_tall_grass.png` | 夜光高草 物品圖示 | 32x32 | `tools/models/gen_batch3.py` | AI |
| 8 | `block/vegetation/coral_leaf_carpet.png` | 珊瑚落葉（葉、枝） | 16x16 | `tools/models/gen_batch3.py` | AI |
| 9 | `block/vegetation/coral_leaf_carpet_stem.png` | 珊瑚落葉（葉、枝） | 16x16 | `tools/models/gen_batch3.py` | AI |
| 10 | `item/coral_leaf_carpet.png` | 珊瑚落葉 物品圖示 | 16x16 | `tools/models/gen_batch3.py` | AI |
| 11 | `block/vegetation/sift_pink_loam.png` | 粉壤土（由帶狀泥岩重新上色） | 16x16 | `tools/worldgen/make_pink_loam.py` | 轉出 |
| 12 | `item/bloombud_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 13 | `item/blub_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 14 | `item/dartback_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 15 | `item/echo_golem_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 16 | `item/fusefly_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 17 | `item/harmonizer_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 18 | `item/hunter_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 19 | `item/hurler_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 20 | `item/lootkin_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 21 | `item/monarch_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 22 | `item/nester_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 23 | `item/nuzzle_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 24 | `item/pollinator_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 25 | `item/prickle_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 26 | `item/roamroot_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 27 | `item/scavenger_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 28 | `item/sculk_monstrosity_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 29 | `item/seedling_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 30 | `item/sentinel_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 31 | `item/singer_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 32 | `item/slabber_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 33 | `item/sprout_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 34 | `item/stalker_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 35 | `item/trapper_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 36 | `item/tuner_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 37 | `item/wobble_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 38 | `mob_effect/ensnared.png` | 定身效果圖示 | 18x18 | `tools/models/hunter_trapper_assets.py` | AI |
| 39 | `mob_effect/soul_deprivation.png` | 靈魂剝奪效果圖示（只在缺檔時寫） | 18x18 | `tools/worldgen/build_vegetation.py` | 待確認 |
| 40 | `item/soul_antidote.png` | 靈魂解藥 | 16x16 | `tools/items/make_soul_burn_textures.py` | AI |
| 41 | `particle/soul_wisp.png` | 靈魂幽火粒子 | 12x12 | `tools/worldgen/make_soul_wisp_textures.py` | AI |
| 42 | `particle/soul_trail.png` | 靈魂拖尾粒子 | 8x8 | `tools/worldgen/make_soul_wisp_textures.py` | AI |
| 43 | `gui/sprites/hud/heart/soul_full.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 44 | `gui/sprites/hud/heart/soul_full_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 45 | `gui/sprites/hud/heart/soul_half.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 46 | `gui/sprites/hud/heart/soul_half_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 47 | `gui/sprites/hud/heart/soul_hardcore_full.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 48 | `gui/sprites/hud/heart/soul_hardcore_full_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 49 | `gui/sprites/hud/heart/soul_hardcore_half.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 50 | `gui/sprites/hud/heart/soul_hardcore_half_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 51 | `block/soul_willow/soul_willow_door_bottom.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 52 | `block/soul_willow/soul_willow_door_top.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 53 | `block/soul_willow/soul_willow_hanging_sign.png` | 靈柳木建材組（原版橡木重新上色） | 32x32 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 54 | `block/soul_willow/soul_willow_planks.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 55 | `block/soul_willow/soul_willow_shelf.png` | 靈柳木建材組（原版橡木重新上色） | 32x32 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 56 | `block/soul_willow/soul_willow_sign.png` | 靈柳木建材組（原版橡木重新上色） | 32x32 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 57 | `block/soul_willow/soul_willow_trapdoor.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 58 | `block/soul_willow/stripped_soul_willow_log.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 59 | `block/soul_willow/stripped_soul_willow_log_top.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 60 | `item/soul_willow_boat.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 61 | `item/soul_willow_chest_boat.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 62 | `item/soul_willow_door.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 63 | `item/soul_willow_hanging_sign.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 64 | `item/soul_willow_sign.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 65 | `entity/boat/soul_willow.png` | 靈柳木船 | 128x64 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 66 | `entity/chest_boat/soul_willow.png` | 靈柳木運輸船 | 128x128 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 67 | `block/soul_crystal_block.png` | 靈魂晶塊（取自 echo_golem 貼圖） | 16x16 | `tools/worldgen/build_soul_crystal.py` | 轉出 |
| 68 | `entity/hunter.png` | Hunter（可能已換成使用者的合併貼圖） | 64x64 | `tools/entity/build_sift_creatures.py` | 待確認 |
| 69 | `entity/trapper.png` | Trapper（可能已換成使用者的合併貼圖） | 64x64 | `tools/entity/build_sift_creatures.py` | 待確認 |
| 70 | `entity/sculk_cube.png` | 幽匿方塊 | 64x64 | `tools/entity/build_sift_creatures.py` | 待確認 |
| 71 | `block/progression/glowshade_short_grass_glow.png` | 進度內容臨時圖（詳見 texture_todo.md） | 16x16 | `tools/progression/build_progression.py` | AI |
| 72 | `block/progression/glowshade_tuft.png` | 進度內容臨時圖（詳見 texture_todo.md） | 16x16 | `tools/progression/build_progression.py` | AI |
| 73 | `block/progression/glowshade_tuft_glow.png` | 進度內容臨時圖（詳見 texture_todo.md） | 16x16 | `tools/progression/build_progression.py` | AI |
| 74 | `block/progression/starlit_shrub.png` | 進度內容臨時圖（詳見 texture_todo.md） | 16x16 | `tools/progression/build_progression.py` | AI |
| 75 | `block/progression/starlit_shrub_glow.png` | 進度內容臨時圖（詳見 texture_todo.md） | 16x16 | `tools/progression/build_progression.py` | AI |
| 76 | `block/vegetation/soul_willow_sapling.png` | 靈魂柳樹苗 貼圖 | 16x16 | 待確認 | 待確認 |
| 77 | `block/vegetation/golden_bloom.png` | 金綻花 貼圖 | 128x128 | 使用者的 Blockbench 模型 | 待確認 |
| 78 | `item/golden_bloom.png` | 金綻花 物品圖示 | 32x32 | 使用者的 Blockbench 模型 | 待確認 |
| 79 | `block/vegetation/sun_bloom.png` | 陽綻花 貼圖 | 64x64 | 使用者的 Blockbench 模型 | 待確認 |
| 80 | `item/sun_bloom.png` | 陽綻花 物品圖示 | 32x32 | 使用者的 Blockbench 模型 | 待確認 |
| 81 | `block/vegetation/rose_bloom.png` | 玫綻花 貼圖 | 64x64 | 使用者的 Blockbench 模型 | 待確認 |
| 82 | `item/rose_bloom.png` | 玫綻花 物品圖示 | 32x32 | 使用者的 Blockbench 模型 | 待確認 |
| 83 | `block/vegetation/dusk_bloom.png` | 暮綻花 貼圖 | 64x64 | 使用者的 Blockbench 模型 | 待確認 |
| 84 | `item/dusk_bloom.png` | 暮綻花 物品圖示 | 32x32 | 使用者的 Blockbench 模型 | 待確認 |
| 85 | `block/sift_orange_short_grass.png` | 裂隙橙短草 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 86 | `block/sift_orange_tall_grass_down.png` | 裂隙橙高草 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 87 | `block/sift_orange_tall_grass_top.png` | 裂隙橙高草 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 88 | `block/sift_red_tallgrass.png` | 裂隙紅短草 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 89 | `block/sift_short_grass.png` | 裂隙薄荷短草 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 90 | `block/rift_mint_tall_grass_down.png` | 裂隙薄荷高草 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 91 | `block/rift_mint_tall_grass_top.png` | 裂隙薄荷高草 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 92 | `block/vegetation/rift_yellow_short_grass.png` | 裂隙黃短草 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 93 | `block/vegetation/olive_forked_stalk.png` | 橄欖叉莖 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 94 | `block/vegetation/blue_curled_fern.png` | 藍捲蕨 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 95 | `block/vegetation/pink_curled_fern.png` | 粉捲蕨 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 96 | `block/vegetation/white_curled_fern.png` | 白捲蕨 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 97 | `block/vegetation/yellow_agave_leaf.png` | 黃龍舌蘭 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 98 | `block/vegetation/canopy_leaf_green.png` | 綠巨傘草 貼圖 | 32x32 | 匯入素材 rift_dimension_flora | 待確認 |
| 99 | `block/vegetation/canopy_stem_green.png` | 綠巨傘草 貼圖 | 32x32 | 匯入素材 rift_dimension_flora | 待確認 |
| 100 | `block/vegetation/canopy_leaf_blue.png` | 藍巨傘草 貼圖 | 32x32 | 匯入素材 rift_dimension_flora | 待確認 |
| 101 | `block/vegetation/canopy_stem_blue.png` | 藍巨傘草 貼圖 | 32x32 | 匯入素材 rift_dimension_flora | 待確認 |
| 102 | `block/vegetation/canopy_leaf_white.png` | 白巨傘草 貼圖 | 32x32 | 匯入素材 rift_dimension_flora | 待確認 |
| 103 | `block/vegetation/canopy_stem_white.png` | 白巨傘草 貼圖 | 32x32 | 匯入素材 rift_dimension_flora | 待確認 |
| 104 | `block/vegetation/yellow_flower_head.png` | 簇生黃花 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 105 | `block/vegetation/yellow_flower_stem.png` | 簇生黃花 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 106 | `block/carapace_flower.png` | 甲殼花 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 107 | `block/carapace_shortgrass.png` | 甲殼短草 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 108 | `block/carapace_vine.png` | 甲殼藤 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 109 | `item/carapace_vine.png` | 甲殼藤 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 110 | `block/white_flower_patch.png` | 白色小花叢 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 111 | `block/yellow_flower_patch.png` | 黃色小花叢 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 112 | `block/soul_bubble_flower.png` | 靈魂氣泡花 貼圖 | 32x32 | 匯入素材 sift_vegetation_assets | 待確認 |
| 113 | `item/soul_bubble_flower.png` | 靈魂氣泡花 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 114 | `block/green_sift_vine.png` | 綠篩靈藤 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 115 | `item/green_sift_vine.png` | 綠篩靈藤 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 116 | `block/orange_sift_vine.png` | 橙篩靈藤 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 117 | `item/orange_sift_vine.png` | 橙篩靈藤 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 118 | `block/souls_vine.png` | 靈魂藤 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 119 | `item/souls_vine.png` | 靈魂藤 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 120 | `block/sift_wall_leaves.png` | 篩靈攀牆葉 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 121 | `block/cleaver_plant.png` | 劈裂草 貼圖 | 32x32 | 匯入素材 sift_vegetation_assets | 待確認 |
| 122 | `item/cleaver_plant.png` | 劈裂草 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 123 | `block/soul_cleaver_plant.png` | 靈魂劈裂草 貼圖 | 32x32 | 匯入素材 sift_vegetation_assets | 待確認 |
| 124 | `item/soul_cleaver_plant.png` | 靈魂劈裂草 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 125 | `block/sift_wheat_plant2.png` | 篩靈小麥幼苗 貼圖 | 15x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 126 | `block/sift_wheat_plant.png` | 篩靈小麥植株 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 127 | `block/sift_wheat.png` | 篩靈小麥 貼圖 | 32x32 | 匯入素材 sift_vegetation_assets | 待確認 |
| 128 | `block/yellow_leaf_litter.png` | 黃色落葉 貼圖 | 32x32 | 匯入素材 sift_vegetation_assets | 待確認 |
| 129 | `item/yellow_leaf_litter.png` | 黃色落葉 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 130 | `block/sculk_grass.png` | 夜光短草 貼圖 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
