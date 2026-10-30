# 原版建材紋樣規格書（`*_bricks`、`*_tiles`、`polished_*`、`smooth_*`、`chiseled_*`）

石材升級時，**石磚系列的磚形一律從原版 `*_bricks` 裡挑一種當骨架**；`*_tiles`、`polished_*`、`smooth_*`、`chiseled_*`
也從下表的原版方塊挑，**依該石材的現實參照物決定挑哪一種**（Step 0 Material Brief 第 3、4 點）。
挑好之後只借用**結構**（層高、磚寬、錯縫、灰縫、外框、面板分割），顏色、顆粒和微紋理照本 skill 的雙層色階重畫，不是換色照抄。

對照圖：同目錄的 `vanilla_building_patterns.png`（每張原版貼圖 2×2 平鋪）。
數據由原版 26.3 Client JAR 量出（灰縫列＝整列幾乎都是暗色；接縫＝每層裡的直向暗縫 x 座標）。
重新產生：`python -I .claude/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py block/<名稱>.png --kind bricks`。

---

## 一、`*_bricks`：14 種基本磚形

| 原版方塊 | 層數 × 層高 | 磚寬／錯縫 | 灰縫 | 外觀特徵 | 適合的現實石材 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `stone_bricks` | 2 層 × 8 px（6 磚＋2 縫） | 上層 1 塊 16 px，下層錯開 8 px | 底部 2 列（暗縫＋陰影） | 大塊方整石，左上亮緣 | 一般灰岩、花崗岩、石灰岩的方整石砌 |
| `deepslate_bricks` | 2 層 × 8 px | 同上（16 px，錯 8） | 底部 2 列 | 大塊、表面有細層紋 | 板岩、玄武岩、深色緻密岩 |
| `polished_blackstone_bricks` | 2 層 × 8 px | 同上 | 底部 2 列 | 大塊、表面細密斑點 | 玄武岩、黑色火成岩 |
| `cinnabar_bricks` | 2 層 × 8 px | 同上 | 底部 2 列 | 大塊、色斑多（13~15 色） | 含礦物、色斑明顯的岩石（紅脈石、礦化岩） |
| `sulfur_bricks` | 2 層 × 8 px | 同上 | 下層 2 列、上層 1 列 | 大塊、亮色、柔和 | 淺色凝灰岩、硫華沉積 |
| `tuff_bricks` | 2 層 × 8 px（1 縫＋2 陰影） | 16 px，錯 8，接縫 2 px 寬 | 1 px＋斜面陰影 | 有斜面倒角的厚磚 | 凝灰岩、火山灰岩、軟質沉積岩 |
| `quartz_bricks` | 2 層 × 8 px（7＋1） | 上層 16 px，下層 8 px 兩塊錯 4 | 1 px、很淡 | 白、平整、幾乎無紋理 | 大理石、石英岩 |
| `end_stone_bricks` | 2 層 × 8 px（7＋1） | 8 px 磚，錯 4 | 1 px、暗 | 淺色、表面有小孔點 | 多孔淺色岩（白堊、浮石、粉砂岩） |
| `mud_bricks` | 2 層 × 8 px（7＋1） | 8 px 磚，錯 4 | 1 px、亮色灰泥 | 柔和土色、灰縫比磚亮 | 泥岩、黏土、條帶泥岩 |
| `nether_bricks` | 4 層 × 4 px（3＋1） | 8 px 磚，每層錯 4 | 1 px、最暗 | 小而密的深色磚 | 細粒深色岩、燒結岩 |
| `red_nether_bricks` | 4 層 × 4 px | 同上 | 1 px | 同上，暗紅 | 鐵質紅色細粒岩 |
| `bricks`（紅磚） | 4 層 × 4 px（3＋1） | 約 6 px 短磚，每層錯 3 | 1 px、**亮色灰泥** | 燒製黏土磚 | 只用在「燒製黏土」類（紅壤、黏土） |
| `resin_bricks` | 4 層 × 4 px | 8 px 磚，錯 4，每塊有亮紋 | 1 px | 每塊磚帶一道高光，像釉面 | 有光澤的材質（樹脂、玻璃質火山岩） |
| `prismarine_bricks` | 1 塊 × 16 px | 整面一塊，內有幾何花紋 | 右、下 1 px | 單塊大石，中間有對稱刻紋 | 海相、結晶感強的石材（片岩、綠泥石） |

**歸納成 5 種磚形骨架**（挑磚時先選骨架，再看細節）：

| 骨架 | 代表 | 用在 |
| :-- | :-- | :-- |
| A. 大方整石（2 層，16 px 長磚錯 8） | stone / deepslate / polished_blackstone / cinnabar / sulfur | 堅硬緻密、能切大塊的岩石 |
| B. 斜面厚磚（2 層，倒角陰影） | tuff | 軟質、易風化的火山岩與沉積岩 |
| C. 中磚（2 層，8 px 磚錯 4） | quartz / end_stone / mud | 淺色、細緻或黏土質的岩石 |
| D. 小密磚（4 層，8 px 磚錯 4） | nether / red_nether / resin | 細粒深色岩、需要密集質感的地方 |
| E. 單塊刻紋石（1 塊） | prismarine | 有結晶紋理、想做成裝飾感的石材 |

衍生：`cracked_*_bricks`＝同一張磚加裂縫與缺角（原版 cracked_stone / deepslate / nether / polished_blackstone）；
`mossy_*_bricks`＝同一張磚的灰縫與下緣長苔（原版 mossy_stone_bricks）。

---

## 二、`*_tiles`：磚瓦

| 原版方塊 | 結構 | 外觀特徵 | 適合的現實石材 |
| :-- | :-- | :-- | :-- |
| `deepslate_tiles` | 4 層 × 約 4 px，每片寬 4~8 px 不等、接縫不規則 | 像一疊薄石板（板岩瓦） | **板岩、頁岩、片岩**等能劈成薄片的岩石 |
| `cracked_deepslate_tiles` | 同上，加裂縫 | — | 同上 |

原版只有深板岩有磚瓦，所以**只有能劈成薄片的石材才建議做 `*_tiles`**；不能劈片的石材做 4 px 小格會變成密網格（虛黑岩的教訓），要做就改成 2×2 的 8 px 大塊地磚。

---

## 三、`polished_*`：磨製

| 原版方塊 | 結構 | 外觀特徵 | 適合的現實石材 |
| :-- | :-- | :-- | :-- |
| `polished_andesite` | 整面一塊，1 px 斜面外框 | 灰色細斑 | 灰色中粒火成岩（安山岩、閃長岩） |
| `polished_granite` | 整面一塊，外框 | 粉紅底＋黑白礦物斑點 | **花崗岩、流紋岩**等有礦物顆粒的岩石 |
| `polished_diorite` | 整面一塊，外框 | 白底＋大塊灰斑 | **大理石**、白色岩石 |
| `polished_tuff` | 整面一塊，外框 | 灰綠、柔和 | 凝灰岩、軟質沉積岩 |
| `polished_cinnabar` | 整面一塊，下方 2 列陰影 | 色斑多 | 礦化岩、紅脈石 |
| `polished_sulfur` | 整面一塊，外框 | 亮黃、柔和 | 淺色凝灰岩 |
| `polished_deepslate` | 無外框，細長橫向片紋，有一條橫縫 | 像磨平的層狀岩 | **板岩、頁岩、層狀岩** |
| `polished_blackstone` | 無外框，滿版細斑 | 黑色、細密 | **玄武岩**、黑色火成岩 |
| `polished_basalt`（side／top） | 柱：側面直向紋、頂面同心方框 | 柱狀 | **玄武岩柱**、柱狀節理 |

兩種骨架：**有框的單塊石板**（andesite、granite、diorite、tuff、sulfur、cinnabar）與**無框的滿版紋理**（deepslate、blackstone）。
有明顯礦物顆粒的岩石用有框款；層狀或極細粒的岩石用無框款。

---

## 四、`smooth_*` 與 `cut_*`：平滑、切製

| 原版方塊 | 結構 | 外觀特徵 | 適合的現實石材 |
| :-- | :-- | :-- | :-- |
| `smooth_stone` | 整面一塊，1 px 外框（頂列暗） | 幾乎無紋理 | 一般岩石的鋸切面 |
| `smooth_stone_slab_side` | 上下兩片，各有外框 | 半磚側面 | 搭配 smooth_stone |
| `smooth_basalt` | **無外框**，斜向柔和斑紋 | 深色、斜紋 | **玄武岩**、深色火成岩 |
| `cut_sandstone`／`cut_red_sandstone` | 外框＋上方 2 px 一條切線 | 砂岩切塊 | 砂岩、粉砂岩 |

---

## 五、`chiseled_*`：雕紋（中央圖騰一律換成生態域生物頭像）

| 原版方塊 | 外框與分割 | 適合的現實石材 |
| :-- | :-- | :-- |
| `chiseled_stone_bricks` | 同心方框 | 方整石類（骨架 A） |
| `chiseled_deepslate` | 上下橫帶＋中央徽記 | 板岩、玄武岩 |
| `chiseled_polished_blackstone` | 外框＋中央浮雕臉（豬布林） | 黑色火成岩 |
| `chiseled_nether_bricks` | 小磚背景＋中央浮雕臉 | 小密磚類（骨架 D） |
| `chiseled_tuff`／`chiseled_tuff_bricks` | 橫帶＋回紋（meander） | 凝灰岩、軟岩 |
| `chiseled_resin_bricks` | 小磚背景＋浮雕臉 | 有光澤的材質 |
| `chiseled_cinnabar`／`chiseled_sulfur` | 外框＋符文圖樣 | 礦化岩、淺色凝灰岩 |
| `chiseled_sandstone`／`chiseled_red_sandstone` | 上下帶＋中央臉（苦力怕／凋零） | 砂岩 |

---

## 六、挑選流程

1. **Step 0**：寫出石材的現實參照物（例：虛黑岩＝玄武岩）。
2. **石磚**：依岩石硬度與用途從第一節選一個骨架、一張原版 `*_bricks`。
3. **磚瓦／磨製／平滑**：依第二～四節的「適合的現實石材」欄判斷**做不做、用哪一款**；現實上不會那樣加工的就不做。
4. **雕紋**：從第五節挑外框分割，中央放生態域生物頭像。
5. **衍生**：每個方塊都要有半磚、階梯、牆（柱、雕紋除外）；裂紋／苔蘚版沿用同一張磚。
6. 只借結構，色階與微紋理照 SKILL.md 第二步重畫；畫完跑 `--kind bricks`／`chiseled`／`block` 檢核。

## 七、The Sift 石材的建議對應

| 方塊（現實參照） | `*_bricks` 骨架 | `*_tiles` | `polished_*` | `smooth_*` | `chiseled_*` 外框 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `void_stone`（玄武岩） | `deepslate_bricks` 或 `polished_blackstone_bricks`（A） | 不建議（不能劈片） | `polished_blackstone`（無框細斑） | `smooth_basalt`（無框斜紋） | `chiseled_polished_blackstone` |
| `dark_slate`（紫色板岩） | `deepslate_bricks`（A） | **`deepslate_tiles`（板岩瓦）** | `polished_deepslate`（無框片紋） | `smooth_stone` | `chiseled_deepslate` |
| `violet_strata`（千枚岩） | `deepslate_bricks`（A） | `deepslate_tiles` | `polished_deepslate` | — | `chiseled_deepslate` |
| `ash_marble`（卡拉拉大理石） | `quartz_bricks`（C） | — | `polished_diorite`（有框） | `smooth_stone` | `chiseled_stone_bricks` |
| `crimson_vein_stone`（玫瑰大理石） | `quartz_bricks`（C） | — | `polished_granite`（有框） | `smooth_stone` | `chiseled_stone_bricks` |
| `ember_stone`（粉紅流紋岩） | `cinnabar_bricks`（A） | — | `polished_granite` | — | `chiseled_cinnabar` |
| `crimson_strata`（粉紅砂岩） | `tuff_bricks`（B） | — | `polished_tuff` | `cut_sandstone` 式 | `chiseled_tuff_bricks` |
| 凝灰岩類地表 | `tuff_bricks`（B） | — | `polished_tuff` | — | `chiseled_tuff` |
| `silted_strata`／`teal_strata`（粉砂岩） | `end_stone_bricks`（C） | — | `polished_tuff` | `cut_sandstone` 式 | `chiseled_tuff_bricks` |
| `banded_mudstone`（條帶泥岩） | `mud_bricks`（C） | — | — | — | `chiseled_tuff` |
| `abyssal_strata`（綠泥片岩） | `prismarine_bricks`（E）或 `deepslate_bricks` | `deepslate_tiles`（片岩可劈片） | `polished_deepslate` | — | `chiseled_deepslate` |
| `bleached_sandstone`（白砂岩） | `end_stone_bricks`（C） | — | — | `cut_sandstone` | `chiseled_sandstone` |

> 這張表是建議值，實際施工前仍要依使用者確認的參考石材調整。
