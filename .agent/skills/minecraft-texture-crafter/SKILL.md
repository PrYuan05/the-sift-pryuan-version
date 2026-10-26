---
name: minecraft-texture-crafter
description: "Minecraft 原版風格（Vanilla-style / Jappa style）材質繪製與色彩學實戰 Skill。當需要為 Minecraft 模組（特別是 The Sift / pysift）繪製、重塑、調整或審查任何物品（Items）、武器工具（如參考原版重錘 mace.png 繪製 sculk_hammer.png）、方塊（Blocks）、礦石、木頭或實體貼圖時必須啟用。整合了：(0) 繪製前材質本質定義與現實／原版雙重參考表（Step 0 Material Brief）、(1) 原版壓縮檔（Loom cache Minecraft 26.3 Client JAR）提取與結構重塑法、(2) Watt 像素色彩學與色相偏移（Hue Shifting）公式、(3) Plantkillable 物品剪影／選擇性外框（Sel-Out）與方塊像素簇（Pixel Clustering）降噪法則、(4) ArtsByKev / MoreByKev 3x3 無縫拼接工作流與 8 點隨身檢核表。"
---

# 🎨 Minecraft 材質繪製與原版參考實戰 Skill (`minecraft-texture-crafter`)

本 Skill 是製作 **Minecraft 原版風格（1.14+ Jappa Style）** 物品與方塊材質的最高準則。所有材質創作都必須同時兼顧 **「現實物理特性（Real-World Material Logic）」**、**「原版基準骨架（Vanilla Archive Reference）」** 與 **「像素色彩學（Hue Shifting & Value Contrast）」**。

> [!IMPORTANT]
> 完整理論與 Blockbench 無縫技巧請隨時參閱同目錄下的參考手冊：
> [`references/texture_art_handbook.md`](references/texture_art_handbook.md)

---

## 第零步（Step 0）：繪製前強制設定 ——【材質本質定義與現實／原版雙重參考卡】

**在動手寫任何像素生成代碼或繪製畫布之前，你必須先明確回答並向使用者（或在筆記中）輸出以下 4 點【繪製前設定卡（Material Brief）】。** 嚴禁在沒想清楚「這是什麼物質、現實中長怎樣」的情況下直接套用濾鏡或盲畫：

### 📋 【繪製前設定卡（Material Brief）】必填四問
1. **這個方塊／物品是什麼？（Identity & Lore Role）**
   - **定位與用途**：它是自然地層岩石、腐化生物組織、加工建材（磚／拋光／木板），還是特定階級（Tier）的武器／法杖／飾品？
   - **所屬環境與氛圍**：它位在哪個生態域或深度（如：表層風化沙岩、幽匿深淵層、靈魂柳木林、紫龍晶礦脈）？這決定了它的**環境光色溫**與**共通暗部（Shared Dark）**。
2. **它具備什麼物理與視覺特性？（Physical & Surface Properties）**
   - **軟硬度與肌理走向**：是堅硬致密、薄層劈理（Foliated）、柔軟多孔、黏稠有機，還是纖維交織？
   - **反光特性與明度策略（Specular & Contrast Strategy）**：
     - **高反光／金屬／結晶體**（如紫龍晶、靈魂錠、重錘金屬核）$\rightarrow$ **極高明度對比（High Contrast）**，亮部直逼最亮階、亮暗緊鄰，加入斜向高光條紋（Specular streaks）。
     - **啞光／粗糙岩石／風化沉積岩**（如篩石、頁岩、沙岩）$\rightarrow$ **柔和窄明度跨度（Soft & Narrow Contrast）**，集中於中間調，禁止刺眼單點高光，以 2~6 像素的**像素簇（Pixel Clusters）**表現凹凸。
     - **有機／角質／木材／布料**（如幽匿骨刺、真菌、靈魂柳木、皮革）$\rightarrow$ **溫潤漸層過渡**，以長條或纖維狀像素群表現紋理。
     - **自發光／能量核心**（如靈魂火、幽匿青藍晶核）$\rightarrow$ 遵守 **80% 低飽和基底 + 20% 高飽和焦點** 的互補色／冷暖對比原則。
3. **它可以參考現實世界的什麼物質？（Real-World Analogues）**
   - 必須指出 **1 ~ 2 種現實世界的礦物、岩石、生物組織或器物** 作為紋理結構依據：
     - *範例 1（`charoite` 紫龍晶）*：參考現實西伯利亞**查羅石（Charoite）**——特徵是漩渦狀、纖維交織的紫羅蘭絲絨光澤，夾雜深紫黑霓輝石脈紋，絕非單純把紫水晶（直線晶柱）換色。
     - *範例 2（`shale` / `schist` 頁岩／片岩）*：參考現實**沉積頁岩與雲母片岩**——特徵是水平或微傾的薄層狀劈理（Bedding / Foliation），像素簇必須呈扁平長條層疊，而非鵝卵石般的圓塊。
     - *範例 3（`sculk_hammer` 幽匿重錘）*：參考現實**中世紀破甲戰錘（Flanged Warhammer）**結合**深海生物幾丁質外骨骼／鯨骨（Chitin & Whalebone）**——中心為沉重深青金屬與能量核，兩側護翼則是具彎曲尖角、啞光鈣質色澤的古生物外骨骼骨刺。
4. **它對應的原版（Vanilla）基準材質是哪一張？（Vanilla Structural Anchor）**
   - 明確列出從原版壓縮檔提取的 1~2 張基準貼圖（如 `item/mace.png`、`block/deepslate.png`、`block/cobblestone.png`），說明**借鑑其什麼比例／密度**，以及**如何根據上述現實特性改造其結構**（嚴禁只改顏色不改結構！）。

---

## 第一步（Step 1）：定位並提取原版材質壓縮檔（Vanilla Archive Extraction）

本專案的 Minecraft 26.3 原版材質與模型皆儲存在 Fabric Loom 快取的 **Client JAR**（標準 ZIP 格式）中：

1. **首選路徑（專案內 Loom 快取，沙盒內可直接讀取）**：
   - `.gradle/loom-cache/minecraftMaven/net/minecraft/minecraft-clientOnly-*/26.3/minecraft-clientOnly-*-26.3.jar`
   - 實例：`.gradle/loom-cache/minecraftMaven/net/minecraft/minecraft-clientOnly-7e9a32a5b8/26.3/minecraft-clientOnly-7e9a32a5b8-26.3.jar`
   - 內部貼圖路徑：`assets/minecraft/textures/item/<name>.png`、`assets/minecraft/textures/block/<name>.png`、`assets/minecraft/textures/entity/<name>.png`
2. **備用路徑（全域 Loom 快取）**：
   - `~/.gradle/caches/fabric-loom/26.3/minecraft-client-only.jar`（或 `minecraft-client.jar`）
3. **專案根目錄自訂參考壓縮檔（禁止刪除）**：
   - `sift_visual_corrected.zip`、`sift_atlas_sorted.zip`、`sift_vegetation_assets.zip`、`sift_draft_rp.zip`

### 🔍 使用內建腳本快速檢視原版貼圖與色盤
在繪製前，執行本 Skill 隨附的檢視與檢核腳本（記得加 `-I` 旗標）：
```powershell
python -I .agent/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py item/mace.png
```
該腳本會自動從原版 `.jar` 提取貼圖、印出 HSV 色盤軌跡表與 ASCII 明度結構圖，並輸出放大檢核圖至 `build/previews/`。

---

## 第二步（Step 2）：建構像素色盤 —— Watt 色彩學與色相偏移（Hue Shifting）

### 2.1 黃金定律：明度決定結構，色相決定氛圍
- **灰階測試（Grayscale Test）**：將貼圖轉為黑白灰階後，依然必須能清楚分辨立體結構、邊界與凹凸紋理。
- **拒絕純黑與純白**：嚴禁在色盤中使用 `#000000`（純黑）或 `#FFFFFF`（純白）。
- **控制色階數量**：單一材質區控制在 **4 ~ 6 個色階**（極亮 Specular、亮部 Light、固有色 Base、暗部 Shadow、極暗輪廓 Outline），避免過多色階導致模糊照片感（Banding）。

### 2.2 色相偏移公式（禁止直線加白加黑 Straight Ramp）
- **🌞 亮部偏移公式（邁向溫暖與生機）**：
  $$\text{Highlight} = H_{\text{趨向暖色/黃 }(50^\circ \sim 60^\circ)} + S_{\text{降低 }(\downarrow)} + V_{\text{提高 }(\uparrow)}$$
- **🌑 暗部偏移公式（邁向深邃與環境光）**：
  $$\text{Shadow} = H_{\text{趨向冷色/藍紫 }(220^\circ \sim 280^\circ)} + S_{\text{提高 }(\uparrow)} + V_{\text{降低 }(\downarrow)}$$

| 色階定位 | 色相 ($H$) 變化趨勢 | 飽和度 ($S$) 趨勢 | 明度 ($V$) 趨勢 | 實戰規範 |
| :--- | :--- | :--- | :--- | :--- |
| **極亮點 (Specular)** | 偏向黃 / 暖白 | 低 ($25\% \sim 40\%$) | 極高 ($85\% \sim 95\%$) | 高反光點，切勿使用 `#FFFFFF` |
| **亮部 (Light)** | 偏向暖色調 | 中低 ($45\% \sim 55\%$) | 高 ($70\% \sim 80\%$) | 左上受光面主色 |
| **固有色 (Base/Mid)** | 材質標準色相 | 中等 ($50\% \sim 65\%$) | 中等 ($50\% \sim 65\%$) | 決定物體顏色的基準點 |
| **暗部 (Shadow)** | 偏向冷色（青/藍/紫） | 中高 ($65\% \sim 75\%$) | 低 ($30\% \sim 45\%$) | 右下背光面，帶環境冷光感 |
| **極暗/輪廓 (Outline)** | 偏向深藍 / 深紫褐 | 高 ($75\% \sim 85\%$) | 極低 ($15\% \sim 25\%$) | 外框與深縫，切勿使用 `#000000` |

### 2.3 共通暗部（Shared Dark）與主從配色
- **共通暗部（Shared Dark）**：複合材質物品（如「金屬長柄 ＋ 幽匿錘頭 ＋ 骨刺護翼」）的最暗部應收斂至相近的深海藍或深紫褐色，賦予整體感。
- **80 / 20 互補焦點法則**：魔法或核心道具使用互補色時，維持 **80% 低飽和基底色 + 20% 高飽和發光焦點**。

---

## 第三步（Step 3）：依材質類型選擇四大實戰工法

### 工法 A：物品與特殊武器 ——「重錘 (`sculk_hammer`) 式原版骨架剖析 ＋ 現實特徵重塑法」
適用於：所有自訂武器、工具、法杖、護符、核心道具（如參考 `item/mace.png` 製作 `sculk_hammer.png`）。

1. **提取原版基準骨架**：
   - 從原版 JAR 提取同類道具（例如重錘提取 `item/mace.png`、劍類提取 `item/netherite_sword.png`），觀察其**對角線握柄軸線**（左下 `(0,15)` 至右上）、**重心比例**與**握柄粗細**。
2. **剪影優先（Silhouette First）與現實結構改造**：
   - 根據 Step 0 的現實參考物改造外型輪廓，讓縮小到 $1\times$ 物品欄大小時一眼就能與原版區分（例如 `sculk_hammer` 在錘頭左上與右下兩側加上向外張開的**幽匿古生物骨刺 `#D8E0A8` ~ `#8A9668`**，中心嵌入**青藍能量核**）。
   - **消除鋸齒（Jaggies）**：確保外框斜線與曲線呈平滑規律階梯（如 `1 -> 1 -> 2 -> 2 -> 3`），禁止出現突兀的 `1 -> 3 -> 1` 跳躍。
3. **左上角光源（Top-Left Light Source）與材質分區上色**：
   - 左上緣受光、右下緣背光。
   - 金屬與晶體區採用**高對比 + 斜向高光條紋**；骨質、木柄與皮革採用**柔和過渡**。
4. **選擇性外框（Selective Outlining / Sel-Out）與邊角破框**：
   - **嚴禁死黑外框**！外框必須使用該部位材質最深色階（冷偏）。
   - **外框跟隨受光**：左上受光側的外框明度比右下背光側外框**亮一階**。
   - **邊角破框（Corner Softening）**：在骨刺尖端、刀刃頂點或轉角處，適度移除最尖端外框像素或以次暗色柔化，消除死硬貼紙感。

### 工法 B：自然方塊與建材 ——「Plantkillable 像素簇降噪 ＋ ArtsByKev $3 \times 3$ 無縫四部曲」
適用於：岩石、地層、鵝卵石、磚塊、木板、沙土、樹皮。

1. **消滅孤兒像素（No Orphan Pixels）與像素簇技法（Pixel Clustering）**：
   - **嚴禁隨機單像素噴點（Pixel Noise）**！
   - 將 2 ~ 6 個同色階像素聚集成**像素簇（Cluster）**，依 Step 0 的現實岩石肌理決定簇的形狀（例如：鵝卵石用圓塊簇、頁岩／板岩用水平薄層簇、查羅石用漩渦纖維簇）。
2. **對比度收斂與視覺重量均衡（消除 Grid Effect）**：
   - 方塊明度跨度要比物品更窄、更柔和，且 $16 \times 16$ 四個象限的視覺重量必須均衡，避免大面積平鋪時產生井字網格或重複斑點。
3. **無縫繪製四部曲 SOP（所有座標強制使用 `(x % 16, y % 16)` 環繞映射）**：
   - **Step 3.1 鋪設底色與暗部網格（Base & Grout）**：用**第二暗色**鋪底，再用**最暗色（冷偏）**畫出自然跨越 $16 \times 16$ 邊界的不規則縫隙網格（禁止畫出筆直十字線）。
   - **Step 3.2 填滿主體像素簇（Blocking in Clusters）**：用**固有色（Base）**填滿每個石塊／肌理簇內部，保留邊緣深色縫隙。
   - **Step 3.3 植入左上角光影（Applying Top-Left Lighting）**：在**每一顆像素簇的左上緣**畫上**亮部色階（暖偏）**；在**右下緣（緊貼深色縫隙內側）**補上過渡的**次暗色階**。
   - **Step 3.4 $3 \times 3$ 與遠景檢視（Zoom-Out Inspection）**：觀察 $3 \times 3$（$48 \times 48$）與 $4 \times 4$（$64 \times 64$）平鋪陣列，打散任何看起來像「一排眼睛／笑臉」的搶眼亮點。

### 工法 C：色階排名／HLS 位移重映射法（Rank / HLS Offset Recoloring）
適用於：已有高品質原版結構（如木門、活板門、告示牌、沙岩家族衍生品），需將原版色階精準轉換為新材質色盤時（參考 [`tools/worldgen/build_soul_willow_wood.py`](../../../tools/worldgen/build_soul_willow_wood.py)、[`tools/worldgen/build_sandstone.py`](../../../tools/worldgen/build_sandstone.py)）。
- 必須確保目標色盤本身符合 **Step 2 的色相偏移（Hue Shifting）**，而非單純平移 Hue。

### 工法 D：CIELAB 感知空間轉換管線（`tools/texture_pipeline/recolor.py`）
適用於：需要對大量現有貼圖進行感知均勻（Perceptually Uniform）色調轉換與自動對比調整時。

---

## 第四步（Step 4）：檔案防護與 8 點隨身檢核表（Mandatory Verification）

### 4.1 備份與防護規範（Art Guard）
1. **寫入前備份**：覆寫任何 `src/main/resources/assets/pysift/textures/` 下的現有貼圖前，先備份至 `.texture_backups/<timestamp>_<task>/`。
2. **禁止覆寫受保護手工貼圖**：若腳本會批次產生貼圖，務必像 [`tools/art_guard.py`](../../../tools/art_guard.py) 一樣保護已定稿的精品貼圖。

### 4.2 執行自動化 8 點檢核與預覽圖生成
每完成一張或多張貼圖後，**必須執行**本 Skill 的檢核腳本：
```powershell
python -I .agent/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py src/main/resources/assets/pysift/textures/item/<your_texture>.png
```
腳本會自動輸出 `build/previews/texture_audit_<name>.png`，你必須用 `read_file` 檢視該圖片，並逐一確認通過 **《繪師隨身 8 點檢核表》**：

- [ ] **1. 灰階測試（Grayscale Test）**：看預覽圖中的黑白灰階版，立體形狀與結構是否依然清晰分明？
- [ ] **2. 色相偏移檢查（Hue Shifting）**：亮部是否往暖色（黃）偏移並降飽和？暗部是否往冷色（藍/紫）偏移並升飽和？
- [ ] **3. 拒絕純黑純白（No `#000000` / `#FFFFFF`）**：檢核報告是否確認零純黑、零純白像素？
- [ ] **4. 孤兒像素清理（Orphan Pixels Cleanup）**：（特別針對方塊）是否已消除無意義的孤立單像素，整合成 2~6 像素的像素簇（Clusters）？
- [ ] **5. 光源一致性（Top-Left Light Source）**：高光是否統一集中在物體與每個結構簇的**左上方**，陰影集中在**右下方**？
- [ ] **6. 外框柔和度（Sel-Out，針對物品）**：外框是否使用材質深色系而非死黑？左上受光面外框是否比右下亮一階？尖角是否適度破框柔化？
- [ ] **7. 無縫邊界測試（$3 \times 3$ Tiling，針對方塊）**：在預覽圖的 $3 \times 3$ 平鋪視圖中，跨邊界處是否完全看不出接縫或斷裂直線？
- [ ] **8. 網格效應測試（Zoom-Out Grid Effect，針對方塊）**：在預覽圖的 $4 \times 4$ 原尺寸縮小平鋪陣列中，視覺重量是否均勻、無重複刺眼斑點？

最後，若變更了資源包內的檔案，執行專案完整性驗證：
```powershell
python -I tools/texture_pipeline/verify.py .
```
