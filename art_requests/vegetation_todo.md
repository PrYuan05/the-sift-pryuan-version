# 植被總表與 AI 產生貼圖待畫清單

由 `tools/build_art_requests.py` 產生，重跑會更新（不要手動改這份）。

**怎麼替換**：畫好後用同樣的檔名覆蓋 `src/main/resources/assets/pysift/textures/` 底下的檔案即可，路徑以下都省略這段。
產生這些圖的腳本已加上臨時圖保護（`tools/art_guard.py`），只要檔案和腳本上次畫的不同，重跑就不會蓋掉你的圖。

## A. 植被總表（43 種）

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
| 10 | `dusk_bloom` | 暮綻花 | `block/vegetation/dusk_bloom/dusk_bloom` | 3D 模型（Blockbench／腳本） | `block/vegetation/dusk_bloom/dusk_bloom` 32x32 | `item/dusk_bloom` 16x16 | 使用者的 Blockbench 模型（待確認） | 已完成（來源待確認） |  |
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
| 36 | `red_sculk` | 赤紅幽匿 | `block/red_sculk/red_sculk` | 方塊（cube_all） | `block/red_sculk/red_sculk` 16x64 | （用方塊模型） | 待確認 | 尺寸異常（16x64，十字模型會被拉伸） |  |
| 37 | `red_sculk_vein` | 赤紅幽匿脈絡 | `block/red_sculk_vein/red_sculk_vein` | 3D 模型（Blockbench／腳本） | `block/red_sculk_vein/red_sculk_vein` 16x64 | `block/red_sculk_vein/red_sculk_vein` 16x64 | 待確認 | 尺寸異常（16x64，十字模型會被拉伸） |  |
| 38 | `corrupted_vine` | 腐化藤蔓 | `block/corrupted_vine/corrupted_vine_corruption0_a`<br>`block/corrupted_vine/corrupted_vine_corruption0_b`<br>`block/corrupted_vine/corrupted_vine_corruption1`<br>`block/corrupted_vine/corrupted_vine_corruption2_a`<br>`block/corrupted_vine/corrupted_vine_corruption2_b`<br>`block/corrupted_vine/corrupted_vine_corruption2_c`<br>`block/corrupted_vine/corrupted_vine_corruption2_d`<br>`block/corrupted_vine/corrupted_vine_corruption2_e`<br>`block/corrupted_vine/corrupted_vine_corruption3_a`<br>`block/corrupted_vine/corrupted_vine_corruption3_b`<br>`block/corrupted_vine/corrupted_vine_corruption3_c` | 藤（貼牆面） | `block/corrupted_vine/corrupted_vine_corruption0_a` 16x16<br>`block/corrupted_vine/corrupted_vine_corruption0_b` 16x16<br>`block/corrupted_vine/corrupted_vine_corruption1` 16x16<br>`block/corrupted_vine/corrupted_vine_corruption2_a` 16x16<br>`block/corrupted_vine/corrupted_vine_corruption2_b` 16x16<br>`block/corrupted_vine/corrupted_vine_corruption2_c` 16x16<br>`block/corrupted_vine/corrupted_vine_corruption2_d` 16x16<br>`block/corrupted_vine/corrupted_vine_corruption2_e` 16x16<br>`block/corrupted_vine/corrupted_vine_corruption3_a` 16x16<br>`block/corrupted_vine/corrupted_vine_corruption3_b` 16x16<br>`block/corrupted_vine/corrupted_vine_corruption3_c` 16x16 | `block/corrupted_vine/corrupted_vine_corruption2_a` 16x16 | 待確認 | 已完成（來源待確認） |  |
| 39 | `cleaver_plant` | 劈裂草 | `block/vegetation/cleaver_plant/cleaver_plant` | 3D 模型（Blockbench／腳本） | `block/vegetation/cleaver_plant/cleaver_plant` 32x32 | `item/cleaver_plant` 16x16 | 待確認<br>匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 40 | `soul_cleaver_plant` | 靈魂劈裂草 | `block/vegetation/soul_cleaver_plant/soul_cleaver_plant` | 3D 模型（Blockbench／腳本） | `block/vegetation/soul_cleaver_plant/soul_cleaver_plant` 32x32 | `item/soul_cleaver_plant` 16x16 | 待確認<br>匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 41 | `yellow_leaf_litter` | 黃色落葉 | `block/vegetation/yellow_leaf_litter/yellow_leaf_litter` | 3D 模型（Blockbench／腳本） | `block/vegetation/yellow_leaf_litter/yellow_leaf_litter` 32x32 | `item/yellow_leaf_litter` 16x16 | 待確認<br>匯入素材 sift_vegetation_assets（待確認） | 已完成（來源待確認） | 新匯入 |
| 42 | `glowshade_short_grass` | 夜光短草 | `block/vegetation/glowshade_short_grass/glowshade_short_grass` | 十字＋發光層 | `block/vegetation/glowshade_short_grass/sculk_grass` 16x16<br>`block/vegetation/glowshade_short_grass/glowshade_short_grass_glow` 16x16 | `block/vegetation/glowshade_short_grass/sculk_grass` 16x16 | 待確認 | 合併後換新材質（待確認） | 原 glowshade_grass，草葉改用 sculk_grass（幽匿草）貼圖，發光層重新對齊 |
| 43 | `glowshade_tuft` | 夜光草叢 | `block/vegetation/glowshade_tuft/glowshade_tuft` | 十字＋發光層 | `block/vegetation/glowshade_tuft/glowshade_tuft` 16x16<br>`block/vegetation/glowshade_tuft/glowshade_tuft_glow` 16x16 | `block/vegetation/glowshade_tuft/glowshade_tuft` 16x16 | 待確認 | 已完成（來源待確認） |  |

## B. AI 產生與待確認的貼圖（154 張，全專案）

總覽圖：`art_requests/ai_textures_overview.png`。類別：**AI** = 腳本從零畫的；**轉出** = 由你的圖或原版貼圖重新上色／裁切，可以沿用也可以重畫；**待確認** = 腳本畫過但可能已換成你的圖，或是匯入素材、來源不明的圖：是你畫的就保留，不是就重畫。

| # | 檔案 | 用途 | 尺寸 | 產生腳本／來源 | 類別 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | `block/pointed/pointed_crimson_vein_stone_base.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 2 | `block/pointed/pointed_crimson_vein_stone_frustum.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 3 | `block/pointed/pointed_crimson_vein_stone_middle.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 4 | `block/pointed/pointed_crimson_vein_stone_tip.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 5 | `block/pointed/pointed_crimson_vein_stone_tip_merge.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 6 | `block/pointed/pointed_dark_slate_base.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 7 | `block/pointed/pointed_dark_slate_frustum.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 8 | `block/pointed/pointed_dark_slate_middle.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 9 | `block/pointed/pointed_dark_slate_tip.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 10 | `block/pointed/pointed_dark_slate_tip_merge.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 11 | `block/pointed/pointed_violet_strata_base.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 12 | `block/pointed/pointed_violet_strata_frustum.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 13 | `block/pointed/pointed_violet_strata_middle.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 14 | `block/pointed/pointed_violet_strata_tip.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 15 | `block/pointed/pointed_violet_strata_tip_merge.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 16 | `block/pointed/pointed_void_stone_base.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 17 | `block/pointed/pointed_void_stone_frustum.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 18 | `block/pointed/pointed_void_stone_middle.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 19 | `block/pointed/pointed_void_stone_tip.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 20 | `block/pointed/pointed_void_stone_tip_merge.png` | 尖石（四種洞穴的滴水石，v2.1.0） | 16x16 | subagent（minecraft-texture-crafter） | AI |
| 21 | `item/coral_leaf_carpet.png` | 珊瑚落葉 物品圖示 | 16x16 | `tools/models/gen_batch3.py` | AI |
| 22 | `item/bloombud_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 23 | `item/blub_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 24 | `item/dartback_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 25 | `item/echo_golem_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 26 | `item/fusefly_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 27 | `item/harmonizer_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 28 | `item/hunter_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 29 | `item/hurler_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 30 | `item/lootkin_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 31 | `item/monarch_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 32 | `item/mourner_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 33 | `item/nester_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 34 | `item/nuzzle_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 35 | `item/pollinator_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 36 | `item/prickle_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 37 | `item/roamroot_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 38 | `item/scavenger_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 39 | `item/sculk_monstrosity_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 40 | `item/seedling_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 41 | `item/sentinel_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 42 | `item/sift_warden_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 43 | `item/singer_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 44 | `item/slabber_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 45 | `item/sprout_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 46 | `item/stalker_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 47 | `item/trapper_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 48 | `item/tuner_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 49 | `item/wobble_spawn_egg.png` | 生怪蛋（臉取自生物貼圖） | 16x16 | `tools/items/make_spawn_eggs.py、tools/models/hunter_trapper_assets.py` | AI |
| 50 | `mob_effect/ensnared.png` | 定身效果圖示 | 18x18 | `tools/models/hunter_trapper_assets.py` | AI |
| 51 | `mob_effect/soul_deprivation.png` | 靈魂剝奪效果圖示（只在缺檔時寫） | 18x18 | `tools/worldgen/build_vegetation.py` | 待確認 |
| 52 | `item/soul_antidote.png` | 靈魂解藥 | 16x16 | `tools/items/make_soul_burn_textures.py` | AI |
| 53 | `particle/soul_wisp.png` | 靈魂幽火粒子 | 16x16 | `tools/worldgen/make_soul_wisp_textures.py` | AI |
| 54 | `particle/soul_trail.png` | 靈魂拖尾粒子 | 8x8 | `tools/worldgen/make_soul_wisp_textures.py` | AI |
| 55 | `gui/sprites/hud/heart/soul_full.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 56 | `gui/sprites/hud/heart/soul_full_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 57 | `gui/sprites/hud/heart/soul_half.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 58 | `gui/sprites/hud/heart/soul_half_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 59 | `gui/sprites/hud/heart/soul_hardcore_full.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 60 | `gui/sprites/hud/heart/soul_hardcore_full_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 61 | `gui/sprites/hud/heart/soul_hardcore_half.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 62 | `gui/sprites/hud/heart/soul_hardcore_half_blinking.png` | 靈魂剝奪的愛心（原版愛心重新上色） | 9x9 | `tools/items/make_soul_hearts.py` | 轉出 |
| 63 | `block/soul_willow/soul_willow_door_bottom.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 64 | `block/soul_willow/soul_willow_door_top.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 65 | `block/soul_willow/soul_willow_hanging_sign.png` | 靈柳木建材組（原版橡木重新上色） | 32x32 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 66 | `block/soul_willow/soul_willow_planks.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 67 | `block/soul_willow/soul_willow_shelf.png` | 靈柳木建材組（原版橡木重新上色） | 32x32 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 68 | `block/soul_willow/soul_willow_sign.png` | 靈柳木建材組（原版橡木重新上色） | 32x32 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 69 | `block/soul_willow/soul_willow_trapdoor.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 70 | `block/soul_willow/stripped_soul_willow_log.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 71 | `block/soul_willow/stripped_soul_willow_log_top.png` | 靈柳木建材組（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 72 | `item/soul_willow_boat.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 73 | `item/soul_willow_chest_boat.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 74 | `item/soul_willow_door.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 75 | `item/soul_willow_hanging_sign.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 76 | `item/soul_willow_sign.png` | 靈柳木物品（原版橡木重新上色） | 16x16 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 77 | `entity/boat/soul_willow.png` | 靈柳木船 | 128x64 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 78 | `entity/chest_boat/soul_willow.png` | 靈柳木運輸船 | 128x128 | `tools/worldgen/build_soul_willow_wood.py` | 轉出 |
| 79 | `entity/hunter.png` | Hunter（可能已換成使用者的合併貼圖） | 64x64 | `tools/entity/build_sift_creatures.py` | 待確認 |
| 80 | `entity/trapper.png` | Trapper（可能已換成使用者的合併貼圖） | 64x64 | `tools/entity/build_sift_creatures.py` | 待確認 |
| 81 | `entity/sculk_cube.png` | 幽匿方塊 | 64x64 | `tools/entity/build_sift_creatures.py` | 待確認 |
| 82 | `block/gray_strata/gray_strata_b.png` | 灰地層 4 色調（洞穴層重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 83 | `block/gray_strata/gray_strata_c.png` | 灰地層 4 色調（洞穴層重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 84 | `block/gray_strata/gray_strata_d.png` | 灰地層 4 色調（洞穴層重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 85 | `block/gray_strata/gray_strata_e.png` | 灰地層 4 色調（洞穴層重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 86 | `block/gray_strata/gray_strata_f.png` | 灰地層 4 色調（洞穴層重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 87 | `block/gray_strata/gray_strata_g.png` | 灰地層 4 色調（洞穴層重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 88 | `block/gray_strata/gray_strata_j.png` | 灰地層 4 色調（洞穴層重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 89 | `block/gray_strata/gray_strata_k.png` | 灰地層 4 色調（洞穴層重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 90 | `block/varied_dark_slate/dark_slate_d.png` | 雜色暗板岩（洞穴層重畫；dark_slate_i 是使用者的） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 91 | `block/varied_dark_slate/dark_slate_g.png` | 雜色暗板岩（洞穴層重畫；dark_slate_i 是使用者的） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 92 | `block/varied_dark_slate/dark_slate_h.png` | 雜色暗板岩（洞穴層重畫；dark_slate_i 是使用者的） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 93 | `block/varied_dark_slate/dark_slate_j.png` | 雜色暗板岩（洞穴層重畫；dark_slate_i 是使用者的） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 94 | `block/violet_strata/violet_strata_h.png` | 紫地層變體（依 violet_strata_e 統一；e 是共用的未改） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 95 | `block/violet_strata/violet_strata_i.png` | 紫地層變體（依 violet_strata_e 統一；e 是共用的未改） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 96 | `block/void_stone/polished_void_stone.png` | 磨製虛黑岩（洞穴層重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | AI |
| 97 | `block/vegetation/hanging_vines/hanging_carapace_vine.png` | 垂掛藤蔓 3 種（本體＋尖端，依使用者的牆藤重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | 轉出 |
| 98 | `block/vegetation/hanging_vines/hanging_carapace_vine_tip.png` | 垂掛藤蔓 3 種（本體＋尖端，依使用者的牆藤重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | 轉出 |
| 99 | `block/vegetation/hanging_vines/hanging_green_sift_vine.png` | 垂掛藤蔓 3 種（本體＋尖端，依使用者的牆藤重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | 轉出 |
| 100 | `block/vegetation/hanging_vines/hanging_green_sift_vine_tip.png` | 垂掛藤蔓 3 種（本體＋尖端，依使用者的牆藤重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | 轉出 |
| 101 | `block/vegetation/hanging_vines/hanging_orange_sift_vine.png` | 垂掛藤蔓 3 種（本體＋尖端，依使用者的牆藤重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | 轉出 |
| 102 | `block/vegetation/hanging_vines/hanging_orange_sift_vine_tip.png` | 垂掛藤蔓 3 種（本體＋尖端，依使用者的牆藤重畫） | 16x16 | Claude Code 一次性腳本（未放進 repo） | 轉出 |
| 103 | `block/vegetation/soul_willow_sapling/soul_willow_sapling.png` | 靈魂柳樹苗 貼圖 | 16x16 | 待確認 | 待確認 |
| 104 | `block/vegetation/bone_spire/bone_spire.png` | 骨刺 貼圖 | 16x16 | 待確認 | 待確認 |
| 105 | `block/vegetation/puff_grass/puff_grass_bottom.png` | 蓬鬆草 貼圖 | 16x16 | 待確認 | 待確認 |
| 106 | `block/vegetation/puff_grass/puff_grass_top.png` | 蓬鬆草 貼圖 | 16x16 | 待確認 | 待確認 |
| 107 | `block/vegetation/dusk_bloom/dusk_bloom.png` | 暮綻花 貼圖 | 32x32 | 使用者的 Blockbench 模型 | 待確認 |
| 108 | `item/dusk_bloom.png` | 暮綻花 物品圖示 | 16x16 | 使用者的 Blockbench 模型 | 待確認 |
| 109 | `block/vegetation/rift_orange_short_grass/sift_orange_short_grass.png` | 裂隙橙短草 貼圖 | 16x16 | 待確認 | 待確認 |
| 110 | `block/vegetation/rift_orange_tall_grass/sift_orange_tall_grass_down.png` | 裂隙橙高草 貼圖 | 16x16 | 待確認 | 待確認 |
| 111 | `block/vegetation/rift_orange_tall_grass/sift_orange_tall_grass_top.png` | 裂隙橙高草 貼圖 | 16x16 | 待確認 | 待確認 |
| 112 | `block/vegetation/rift_mint_short_grass/sift_short_grass.png` | 裂隙薄荷短草 貼圖 | 16x16 | 待確認 | 待確認 |
| 113 | `block/vegetation/rift_mint_tall_grass/rift_mint_tall_grass_down.png` | 裂隙薄荷高草 貼圖 | 16x16 | 待確認 | 待確認 |
| 114 | `block/vegetation/rift_mint_tall_grass/rift_mint_tall_grass_top.png` | 裂隙薄荷高草 貼圖 | 16x16 | 待確認 | 待確認 |
| 115 | `block/vegetation/olive_forked_stalk/olive_forked_stalk.png` | 橄欖叉莖 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 116 | `block/vegetation/blue_curled_fern/blue_curled_fern.png` | 藍捲蕨 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 117 | `block/vegetation/pink_curled_fern/pink_curled_fern.png` | 粉捲蕨 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 118 | `block/vegetation/yellow_agave/yellow_agave_leaf.png` | 黃龍舌蘭 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 119 | `block/vegetation/blue_giant_canopy/canopy_leaf_blue.png` | 藍巨傘草 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 120 | `block/vegetation/blue_giant_canopy/canopy_stem_blue.png` | 藍巨傘草 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 121 | `block/vegetation/clustered_yellow_flowers/yellow_flower_head.png` | 簇生黃花 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 122 | `block/vegetation/clustered_yellow_flowers/yellow_flower_stem.png` | 簇生黃花 貼圖 | 16x16 | 匯入素材 rift_dimension_flora | 待確認 |
| 123 | `block/vegetation/carapace_flower/carapace_flower.png` | 甲殼花 貼圖 | 16x16 | 待確認 | 待確認 |
| 124 | `block/vegetation/carapace_short_grass/carapace_shortgrass.png` | 甲殼短草 貼圖 | 16x16 | 待確認 | 待確認 |
| 125 | `block/vegetation/carapace_vine/carapace_vine.png` | 甲殼藤 貼圖 | 16x16 | 待確認 | 待確認 |
| 126 | `item/carapace_vine.png` | 甲殼藤 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 127 | `block/vegetation/yellow_flower_patch/yellow_flower_patch.png` | 黃色小花叢 貼圖 | 16x16 | 待確認 | 待確認 |
| 128 | `block/vegetation/green_sift_vine/green_sift_vine.png` | 綠隙浮藤 貼圖 | 16x16 | 待確認 | 待確認 |
| 129 | `item/green_sift_vine.png` | 綠隙浮藤 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 130 | `block/vegetation/orange_sift_vine/orange_sift_vine.png` | 橙隙浮藤 貼圖 | 16x16 | 待確認 | 待確認 |
| 131 | `item/orange_sift_vine.png` | 橙隙浮藤 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 132 | `block/red_sculk/red_sculk.png` | 赤紅幽匿 貼圖 | 16x64 | 待確認 | 待確認 |
| 133 | `block/red_sculk_vein/red_sculk_vein.png` | 赤紅幽匿脈絡 貼圖 | 16x64 | 待確認 | 待確認 |
| 134 | `block/corrupted_vine/corrupted_vine_corruption0_a.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 135 | `block/corrupted_vine/corrupted_vine_corruption0_b.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 136 | `block/corrupted_vine/corrupted_vine_corruption1.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 137 | `block/corrupted_vine/corrupted_vine_corruption2_a.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 138 | `block/corrupted_vine/corrupted_vine_corruption2_b.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 139 | `block/corrupted_vine/corrupted_vine_corruption2_c.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 140 | `block/corrupted_vine/corrupted_vine_corruption2_d.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 141 | `block/corrupted_vine/corrupted_vine_corruption2_e.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 142 | `block/corrupted_vine/corrupted_vine_corruption3_a.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 143 | `block/corrupted_vine/corrupted_vine_corruption3_b.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 144 | `block/corrupted_vine/corrupted_vine_corruption3_c.png` | 腐化藤蔓 貼圖 | 16x16 | 待確認 | 待確認 |
| 145 | `block/vegetation/cleaver_plant/cleaver_plant.png` | 劈裂草 貼圖 | 32x32 | 待確認 | 待確認 |
| 146 | `item/cleaver_plant.png` | 劈裂草 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 147 | `block/vegetation/soul_cleaver_plant/soul_cleaver_plant.png` | 靈魂劈裂草 貼圖 | 32x32 | 待確認 | 待確認 |
| 148 | `item/soul_cleaver_plant.png` | 靈魂劈裂草 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 149 | `block/vegetation/yellow_leaf_litter/yellow_leaf_litter.png` | 黃色落葉 貼圖 | 32x32 | 待確認 | 待確認 |
| 150 | `item/yellow_leaf_litter.png` | 黃色落葉 物品圖示 | 16x16 | 匯入素材 sift_vegetation_assets | 待確認 |
| 151 | `block/vegetation/glowshade_short_grass/sculk_grass.png` | 夜光短草 貼圖 | 16x16 | 待確認 | 待確認 |
| 152 | `block/vegetation/glowshade_short_grass/glowshade_short_grass_glow.png` | 夜光短草 貼圖 | 16x16 | 待確認 | 待確認 |
| 153 | `block/vegetation/glowshade_tuft/glowshade_tuft.png` | 夜光草叢 貼圖 | 16x16 | 待確認 | 待確認 |
| 154 | `block/vegetation/glowshade_tuft/glowshade_tuft_glow.png` | 夜光草叢 貼圖 | 16x16 | 待確認 | 待確認 |
