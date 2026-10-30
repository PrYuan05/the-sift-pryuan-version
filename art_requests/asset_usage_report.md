# 方塊貼圖與模型使用清查

由 `tools/texture_pipeline/asset_usage.py` 產生（唯讀，不改任何檔案）。追蹤路徑：方塊狀態 → 模型（含父模型）→ 貼圖；物品定義與物品模型；以及 Java／其他 JSON 裡直接寫的 `block/...` 路徑。

- **未使用**：src 裡沒有任何地方引用。
- **放錯資料夾**：用到它的方塊全都不是資料夾名稱那個方塊。
- **共用**：資料夾自己的方塊和別的方塊都在用。
- **分類資料夾**：資料夾不是某個方塊的名字（sift_colors、sift_ground、templates…），不判斷。
- ✏️＝這個檔案目前有其他作業未提交的修改（整理時先不動）。

## 貼圖（共 763）

未使用 18｜放錯資料夾 39｜共用 32｜正常 426｜分類資料夾 248

### 貼圖：未使用（18）

| 檔案 | 使用者 |
| :-- | :-- |
| `block/dark_slate/dark_slate_l` | — |
| `block/sift_colors/amber_stained_glass_pane_top` | — |
| `block/sift_colors/coral_stained_glass_pane_top` | — |
| `block/sift_colors/dusk_gold_stained_glass_pane_top` | — |
| `block/sift_colors/lavender_stained_glass_pane_top` | — |
| `block/sift_colors/mint_stained_glass_pane_top` | — |
| `block/sift_colors/rose_stained_glass_pane_top` | — |
| `block/sift_colors/soul_blue_stained_glass_pane_top` | — |
| `block/sift_colors/teal_stained_glass_pane_top` | — |
| `block/sift_colors/void_stained_glass_pane_top` | — |
| `block/sift_portal_large_canvas` | — |
| `block/sift_teal_framed_panel_ctm_1` | — |
| `block/sift_teal_framed_panel_ctm_2` | — |
| `block/sift_teal_framed_panel_ctm_3` | — |
| `block/sift_teal_framed_panel_ctm_4` | — |
| `block/sift_teal_framed_panel_ctm_5` | — |
| `block/sift_teal_framed_panel_ctm_6` | — |
| `block/souls_sapling` | — |

### 貼圖：放錯資料夾（39）

| 檔案 | 使用者 |
| :-- | :-- |
| `block/abyssal_strata/abyssal_strata_depth0_b` | `item:teal_capped_abyssal_strata`、`teal_capped_abyssal_strata` |
| `block/crimson_strata/crimson_strata_b` | `crimson_capped_crimson_strata`、`item:crimson_capped_crimson_strata` |
| `block/crimson_strata/crimson_strata_c` | `crimson_capped_crimson_strata_2`、`item:crimson_capped_crimson_strata_2` |
| `block/crimson_strata/crimson_strata_e` | `capped_crimson_strata`、`item:capped_crimson_strata` |
| `block/crimson_strata/crimson_strata_f` | `capped_crimson_strata`、`item:capped_crimson_strata` |
| `block/crimson_strata/crimson_strata_h` | `capped_crimson_strata`、`item:capped_crimson_strata` |
| `block/crimson_strata/crimson_strata_i` | `crimson_capped_crimson_strata_3`、`item:crimson_capped_crimson_strata_3` |
| `block/crimson_strata/crimson_strata_l` | `item:violet_capped_crimson_strata`、`violet_capped_crimson_strata` |
| `block/dark_slate/dark_slate_a` | `framed_dark_slate`、`item:framed_dark_slate` |
| `block/dark_slate/dark_slate_d` | `item:varied_dark_slate`、`src:src/main/resources/assets/pysift/items/varied_dark_slate.json`、`varied_dark_slate` |
| `block/dark_slate/dark_slate_e` | `blotched_dark_slate`、`blotched_dark_slate_slab`、`blotched_dark_slate_stairs`、`blotched_dark_slate_wall`、`item:blotched_dark_slate`、`item:blotched_dark_slate_slab`、`item:blotched_dark_slate_stairs`、`item:blotched_dark_slate_wall` |
| `block/dark_slate/dark_slate_f` | `item:olive_capped_dark_slate`、`olive_capped_dark_slate` |
| `block/dark_slate/dark_slate_g` | `item:varied_dark_slate`、`item:varied_dark_slate_slab`、`item:varied_dark_slate_stairs`、`item:varied_dark_slate_wall`、`src:src/main/resources/assets/pysift/items/varied_dark_slate.json`、`varied_dark_slate`、`varied_dark_slate_slab`、`varied_dark_slate_stairs` 等 9 個 |
| `block/dark_slate/dark_slate_h` | `varied_dark_slate`、`varied_dark_slate_slab`、`varied_dark_slate_stairs`、`varied_dark_slate_wall` |
| `block/dark_slate/dark_slate_i` | `olive_capped_dark_slate`、`varied_dark_slate`、`varied_dark_slate_slab`、`varied_dark_slate_stairs`、`varied_dark_slate_wall` |
| `block/dark_slate/dark_slate_j` | `item:varied_dark_slate`、`src:src/main/resources/assets/pysift/items/varied_dark_slate.json`、`varied_dark_slate` |
| `block/dark_slate/dark_slate_m` | `gray_capped_dark_slate`、`item:gray_capped_dark_slate` |
| `block/dark_slate/dark_slate_n` | `gray_capped_dark_slate` |
| `block/dark_slate/dark_slate_q` ✏️ | `item:violet_capped_dark_slate`、`violet_capped_dark_slate` |
| `block/ember_stone/ember_stone_heat2_a` | `crimson_capped_crimson_strata`、`crimson_capped_ember_stone`、`crimson_capped_gray_strata`、`item:crimson_capped_crimson_strata`、`item:crimson_capped_ember_stone`、`item:crimson_capped_gray_strata` |
| `block/ember_stone/ember_stone_heat3_b` | `crimson_capped_ember_stone`、`item:crimson_capped_ember_stone` |
| `block/ember_stone/ember_stone_heat3_c` | `item:warm_capped_ember_stone`、`warm_capped_ember_stone` |
| `block/gray_strata/gray_strata_a` | `crimson_capped_gray_strata`、`item:crimson_capped_gray_strata` |
| `block/gray_strata/gray_strata_h` | `item:teal_capped_gray_strata`、`teal_capped_gray_strata` |
| `block/gray_strata/gray_strata_i` | `item:teal_capped_gray_strata_2`、`teal_capped_gray_strata_2` |
| `block/sift_portal` | `item:sift_portal`、`sift_portal` |
| `block/smooth_stone_bricks/chiseled_smooth_stone_bricks` | `chiseled_smooth_stone_bricks`、`item:chiseled_smooth_stone_bricks` |
| `block/smooth_stone_bricks/chiseled_smooth_stone_bricks_top` | `chiseled_smooth_stone_bricks`、`item:chiseled_smooth_stone_bricks` |
| `block/soul_crystal_block` | `item:soul_crystal_block`、`soul_crystal_block` |
| `block/teal_strata/teal_strata_c` | `item:teal_capped_teal_strata`、`teal_capped_teal_strata` |
| `block/teal_strata/teal_strata_d` | `abyssal_strata` |
| `block/teal_strata/teal_strata_g` | `item:teal_capped_teal_strata_2`、`teal_capped_teal_strata_2` |
| `block/violet_strata/violet_strata_b` ✏️ | `crimson_capped_violet_strata`、`item:crimson_capped_violet_strata` |
| `block/violet_strata/violet_strata_c` ✏️ | `crimson_capped_violet_strata_2`、`item:crimson_capped_violet_strata_2` |
| `block/void_stone/void_stone_a` | `item:umber_void_stone`、`item:umber_void_stone_slab`、`item:umber_void_stone_stairs`、`item:umber_void_stone_wall`、`umber_void_stone`、`umber_void_stone_slab`、`umber_void_stone_stairs`、`umber_void_stone_wall` |
| `block/void_stone/void_stone_g` | `crimson_capped_violet_strata`、`gray_capped_dark_slate`、`item:gray_capped_dark_slate`、`item:speckled_void_stone`、`item:speckled_void_stone_slab`、`item:speckled_void_stone_stairs`、`item:speckled_void_stone_wall`、`speckled_void_stone` 等 11 個 |
| `block/void_stone/void_stone_h` | `item:void_stone_pillar`、`void_stone_pillar` |
| `block/void_stone/void_stone_i` | `gray_capped_void_stone`、`item:gray_capped_void_stone` |
| `block/void_stone/void_stone_pillar_top` | `item:void_stone_pillar`、`void_stone_pillar` |

### 貼圖：共用（32）

| 檔案 | 使用者 |
| :-- | :-- |
| `block/abyssal_strata/abyssal_strata_depth0_a` | `abyssal_strata`、`abyssal_strata_slab`、`abyssal_strata_stairs`、`abyssal_strata_wall`、`crimson_capped_gray_strata`、`item:abyssal_strata`、`item:abyssal_strata_slab`、`item:abyssal_strata_stairs` 等 11 個 |
| `block/abyssal_strata/abyssal_strata_depth1_a` | `abyssal_strata`、`item:abyssal_strata`、`src:src/main/resources/assets/pysift/items/abyssal_strata.json`、`teal_capped_teal_strata` |
| `block/abyssal_strata/abyssal_strata_depth1_b` | `abyssal_strata`、`item:teal_capped_teal_strata`、`teal_capped_teal_strata` |
| `block/abyssal_strata/abyssal_strata_depth2` | `abyssal_strata`、`item:abyssal_strata`、`item:teal_capped_abyssal_strata`、`item:teal_capped_teal_strata`、`src:src/main/resources/assets/pysift/items/abyssal_strata.json`、`teal_capped_abyssal_strata`、`teal_capped_teal_strata` |
| `block/crimson_strata/crimson_strata_d` | `crimson_capped_crimson_strata`、`crimson_strata`、`crimson_strata_slab`、`crimson_strata_stairs`、`crimson_strata_wall`、`item:crimson_capped_crimson_strata` |
| `block/crimson_strata/crimson_strata_j` | `crimson_strata`、`item:crimson_strata`、`src:src/main/resources/assets/pysift/items/crimson_strata.json`、`violet_capped_crimson_strata` |
| `block/crimson_strata/crimson_strata_k` | `crimson_strata`、`item:violet_capped_crimson_strata`、`violet_capped_crimson_strata` |
| `block/crimson_vein_stone/crimson_vein_stone_crimson_spread4` | `capped_crimson_strata`、`crimson_vein_stone`、`item:capped_crimson_strata`、`item:crimson_vein_stone`、`src:src/main/resources/assets/pysift/items/crimson_vein_stone.json` |
| `block/dark_slate_bricks/dark_slate_bricks` ✏️ | `dark_slate_brick_slab`、`dark_slate_brick_stairs`、`dark_slate_brick_wall`、`dark_slate_bricks`、`item:dark_slate_brick_slab`、`item:dark_slate_brick_stairs`、`item:dark_slate_brick_wall`、`item:dark_slate_bricks` 等 10 個 |
| `block/ember_stone/ember_stone_heat0_a` | `capped_crimson_strata`、`ember_stone`、`ember_stone_slab`、`ember_stone_stairs`、`ember_stone_wall`、`item:ember_stone`、`item:ember_stone_slab`、`item:ember_stone_stairs` 等 10 個 |
| `block/ember_stone/ember_stone_heat4` | `crimson_capped_ember_stone`、`ember_stone`、`item:crimson_capped_ember_stone`、`item:ember_stone`、`item:warm_capped_ember_stone`、`src:src/main/resources/assets/pysift/items/ember_stone.json`、`warm_capped_ember_stone` |
| `block/forest_floor/forest_floor_moss1` | `forest_floor`、`item:forest_floor`、`item:olive_capped_forest_floor`、`olive_capped_forest_floor`、`src:src/main/resources/assets/pysift/items/forest_floor.json` |
| `block/lichen_stone/lichen_stone_lichen2_b` | `item:lichen_stone`、`lichen_stone`、`olive_capped_dark_slate`、`src:src/main/resources/assets/pysift/items/lichen_stone.json` |
| `block/lichen_stone/lichen_stone_lichen2_c` | `lichen_stone`、`olive_capped_dark_slate` |
| `block/lichen_stone/lichen_stone_lichen4` | `item:lichen_stone`、`item:olive_capped_dark_slate`、`lichen_stone`、`olive_capped_dark_slate`、`src:src/main/resources/assets/pysift/items/lichen_stone.json` |
| `block/magma_vein_slate/magma_vein_slate_vein0_a` | `crimson_capped_violet_strata`、`crimson_capped_violet_strata_2`、`item:crimson_capped_violet_strata_2`、`item:magma_vein_slate`、`item:magma_vein_slate_slab`、`item:magma_vein_slate_stairs`、`item:magma_vein_slate_wall`、`magma_vein_slate` 等 12 個 |
| `block/magma_vein_slate/magma_vein_slate_vein0_h` | `crimson_capped_violet_strata`、`crimson_capped_violet_strata_2`、`item:crimson_capped_violet_strata`、`magma_vein_slate`、`magma_vein_slate_slab`、`magma_vein_slate_stairs`、`magma_vein_slate_wall` |
| `block/magma_vein_slate/magma_vein_slate_vein0_i` | `crimson_capped_violet_strata`、`crimson_capped_violet_strata_2`、`magma_vein_slate`、`magma_vein_slate_slab`、`magma_vein_slate_stairs`、`magma_vein_slate_wall` |
| `block/mossy_olive_earth/mossy_olive_earth_moss0` | `item:mossy_olive_earth`、`item:mossy_olive_earth_slab`、`item:mossy_olive_earth_stairs`、`item:mossy_olive_earth_wall`、`item:olive_capped_mossy_olive_earth`、`mossy_olive_earth`、`mossy_olive_earth_slab`、`mossy_olive_earth_stairs` 等 11 個 |
| `block/mossy_olive_earth/mossy_olive_earth_moss2` | `item:mossy_olive_earth`、`item:olive_capped_mossy_olive_earth`、`mossy_olive_earth`、`olive_capped_mossy_olive_earth`、`src:src/main/resources/assets/pysift/items/mossy_olive_earth.json` |
| `block/rich_dirt/rich_dirt_c` | `item:olive_capped_dark_slate`、`olive_capped_dark_slate`、`rich_dirt` |
| `block/rusted_dark_cobble/rusted_dark_cobble_rust1` | `gray_capped_void_stone`、`item:gray_capped_void_stone`、`item:rusted_dark_cobble`、`rusted_dark_cobble`、`src:src/main/resources/assets/pysift/items/rusted_dark_cobble.json` |
| `block/silted_strata/silted_strata_silt0_a` | `item:silted_strata`、`item:silted_strata_slab`、`item:silted_strata_stairs`、`item:silted_strata_wall`、`item:teal_capped_gray_strata`、`item:teal_capped_gray_strata_2`、`item:teal_capped_teal_strata_2`、`silted_strata` 等 15 個 |
| `block/silted_strata/silted_strata_silt0_b` | `crimson_capped_crimson_strata_3`、`silted_strata`、`silted_strata_slab`、`silted_strata_stairs`、`silted_strata_wall`、`teal_capped_gray_strata`、`teal_capped_teal_strata_2` |
| `block/silted_strata/silted_strata_silt1` | `crimson_capped_crimson_strata_3`、`item:crimson_capped_crimson_strata_3`、`item:silted_strata`、`silted_strata`、`src:src/main/resources/assets/pysift/items/silted_strata.json`、`teal_capped_gray_strata`、`teal_capped_teal_strata_2` |
| `block/sky_block/sky_block_cloud1` | `gray_capped_sky_block`、`item:gray_capped_sky_block`、`item:sky_block`、`sky_block`、`src:src/main/resources/assets/pysift/items/sky_block.json` |
| `block/sky_block/sky_block_cloud2` | `gray_capped_sky_block`、`item:gray_capped_sky_block`、`item:sky_block`、`sky_block`、`src:src/main/resources/assets/pysift/items/sky_block.json` |
| `block/teal_strata/teal_strata_a` | `capped_crimson_strata`、`crimson_capped_crimson_strata_2`、`item:capped_crimson_strata`、`item:crimson_capped_crimson_strata_2`、`item:teal_strata`、`src:src/main/resources/assets/pysift/items/teal_strata.json`、`teal_strata` |
| `block/violet_strata/violet_strata_e` ✏️ | `item:violet_capped_crimson_strata`、`item:violet_capped_dark_slate`、`item:violet_strata`、`item:violet_strata_slab`、`item:violet_strata_stairs`、`item:violet_strata_wall`、`src:src/main/resources/assets/pysift/items/violet_strata.json`、`violet_capped_crimson_strata` 等 13 個 |
| `block/void_stone/void_stone_c` | `crimson_capped_violet_strata`、`gray_capped_void_stone`、`item:crimson_capped_violet_strata`、`item:gray_capped_void_stone`、`item:void_stone`、`item:void_stone_slab`、`item:void_stone_stairs`、`item:void_stone_wall` 等 13 個 |
| `block/void_stone/void_stone_f` | `crimson_capped_violet_strata`、`gray_capped_void_stone`、`item:void_stone`、`src:src/main/resources/assets/pysift/items/void_stone.json`、`void_stone` |
| `block/wilting_foliage/wilting_foliage_wither0` | `item:olive_capped_forest_floor`、`item:wilting_foliage`、`olive_capped_forest_floor`、`src:src/main/resources/assets/pysift/items/wilting_foliage.json`、`wilting_foliage` |

## 模型（共 1815）

未使用 1｜放錯資料夾 11｜共用 1｜正常 1327｜分類資料夾 475

### 模型：未使用（1）

| 檔案 | 使用者 |
| :-- | :-- |
| `block/templates/cube_bottom_top_rot270` | — |

### 模型：放錯資料夾（11）

| 檔案 | 使用者 |
| :-- | :-- |
| `block/dark_slate/dark_slate_a` | `framed_dark_slate`、`item:framed_dark_slate` |
| `block/dark_slate/dark_slate_d` | `item:varied_dark_slate`、`src:src/main/resources/assets/pysift/items/varied_dark_slate.json`、`varied_dark_slate` |
| `block/dark_slate/dark_slate_e` | `blotched_dark_slate`、`blotched_dark_slate_slab`、`item:blotched_dark_slate` |
| `block/dark_slate/dark_slate_g` | `item:varied_dark_slate`、`src:src/main/resources/assets/pysift/items/varied_dark_slate.json`、`varied_dark_slate`、`varied_dark_slate_slab` |
| `block/dark_slate/dark_slate_h` | `varied_dark_slate`、`varied_dark_slate_slab` |
| `block/dark_slate/dark_slate_i` | `varied_dark_slate`、`varied_dark_slate_slab` |
| `block/dark_slate/dark_slate_j` | `item:varied_dark_slate`、`src:src/main/resources/assets/pysift/items/varied_dark_slate.json`、`varied_dark_slate` |
| `block/smooth_stone_bricks/chiseled_smooth_stone_bricks` | `chiseled_smooth_stone_bricks`、`item:chiseled_smooth_stone_bricks` |
| `block/teal_strata/teal_strata_d` | `abyssal_strata` |
| `block/void_stone/void_stone_a` | `item:umber_void_stone`、`umber_void_stone`、`umber_void_stone_slab` |
| `block/void_stone/void_stone_g` | `item:speckled_void_stone`、`speckled_void_stone`、`speckled_void_stone_slab` |

### 模型：共用（1）

| 檔案 | 使用者 |
| :-- | :-- |
| `block/soul_willow_planks` | `item:soul_willow_planks`、`soul_willow_planks`、`soul_willow_slab`、`src:src/main/resources/assets/pysift/items/soul_willow_planks.json` |

