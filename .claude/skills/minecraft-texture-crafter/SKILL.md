---
name: minecraft-texture-crafter
description: "Minecraft 原版風格（Vanilla-style / Jappa style）材質繪製與色彩學實戰 Skill。當需要為 Minecraft 模組（特別是 The Sift / pysift）繪製、重塑、調整或審查任何物品（Items）、武器工具（如參考原版重錘 mace.png 繪製 sculk_hammer.png）、方塊（Blocks）、礦石、木頭或實體貼圖時必須啟用。整合了：(0) 繪製前材質本質定義與現實／原版雙重參考表（Step 0 Material Brief）、(1) 原版壓縮檔（Loom cache Minecraft 26.3 Client JAR）提取與結構重塑法、(2) Watt 像素色彩學與色相偏移（Hue Shifting）公式、(3) Plantkillable 物品剪影／選擇性外框（Sel-Out）與方塊像素簇（Pixel Clustering）降噪法則、(4) ArtsByKev / MoreByKev 3x3 無縫拼接工作流、(5) Cotufa + Jappa 數值化色盤與原版幾何／拓撲規則（物品高對比色階 vs. 方塊「結構主色＋微紋理副色」雙層色階、反 AI 平塗塑膠感與逐階緩衝橋接、45° 對角主軸、12~14 px 置中留白、木板／磚／雕紋／砂岩／礦石拓撲、環面無縫），以及 18 項自動檢核（--kind 依材質類型）。"
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
在繪製前，執行本 Skill 隨附的檢視與檢核腳本（記得加 `-I` 旗標；Claude Code 用的副本在 `.claude/skills/minecraft-texture-crafter/`，內容相同）：
```powershell
python -I .claude/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py --search ingot          # 找原版貼圖
python -I .claude/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py item/mace.png --kind handheld
```
該腳本會自動從原版 `.jar` 提取貼圖、印出 HSV 色盤軌跡表與 ASCII 明度結構圖，並輸出放大檢核圖至 `build/previews/`。
**先拿原版同類貼圖跑一次**，記下它的色階數、ΔV、色相偏移量，當作這張新圖的目標值。

---

## 第二步（Step 2）：建構像素色盤 —— Watt 色彩學與色相偏移（Hue Shifting）

### 2.1 黃金定律：明度決定結構，色相決定氛圍
- **灰階測試（Grayscale Test）**：將貼圖轉為黑白灰階後，依然必須能清楚分辨立體結構、邊界與凹凸紋理。
- **拒絕純黑與純白**：嚴禁在色盤中使用 `#000000`（純黑）或 `#FFFFFF`（純白）。
- **控制色階數量與「方塊雙層色階架構」（每條材質色階各算）**：
  - **物品（Items）**：每種材質一條，**4 ~ 7 色**（物品在 16×16 圖示下需高對比以凸顯受光面與外框剪影）。複合物品（木柄＋金屬刃）每種材質各算一條。
  - **方塊（Blocks，關鍵反平塗法則）**：每種材質 **5 ~ 8 色**，必須採用 **「雙層色階架構（Two-Tier Palette）」**：
    1. **結構主色階（4~5 色，錨點間 $\Delta V \approx 8\% \sim 14\%$）**：負責岩縫、凹槽、切面斜角與受光亮邊；啞光岩石／沙岩／木材總明度跨度控制在 $\Delta\text{Lum} \approx 0.18 \sim 0.38$（純細沙頂面 $0.10 \sim 0.20$），**嚴禁**拉到 $> 0.45$ 的金屬級極端對比。
    2. **微紋理與緩衝副色階（1~3 色，圍繞固有色插入 $\Delta V \approx 2.5\% \sim 6\%$ / $\Delta\text{Lum} \approx 0.03 \sim 0.07$ 的近鄰色）**：用來交織出底材顆粒感並緩衝深縫與亮面。**切勿為了湊「只用 4~5 色且每階 $\ge 10\%$」而刪光微差副色，否則中間調會退化成單色平塗塑膠板！**
  - **禁止無序噴槍平滑漸層（Airbrush）**：每一格都是色盤裡明確定義的顏色；超過 9~10 色無序過渡才會變成模糊照片（Banding）。

### 2.2 色相偏移公式（禁止直線加白加黑 Straight Ramp）
偏移量一律**相對於固有色（Base）**計算，不是把顏色拉到某個絕對色相：
- **🌞 亮部（往暖）**：色相往黃／橘方向轉 **$\Delta H \approx +10^\circ \sim +20^\circ$**，**提高明度（$\uparrow B$）**，**飽和度略降（$\downarrow S$）**，模擬強光洗白。
  $$\text{Highlight} = H_{\text{Base}} + (10^\circ \sim 20^\circ)_{\to \text{黃}} \;+\; S\downarrow \;+\; B\uparrow$$
- **🌑 暗部（往冷）**：色相往藍／紫（紅色系材質可往深紅紫）方向轉 **$\Delta H \approx 15^\circ \sim 30^\circ$**，**降低明度（$\downarrow B$）**；**飽和度依材質反光度調整**：
  - 金屬、寶石、結晶（高反光）：暗部 $S\uparrow$，保持深色仍然鮮明。
  - 啞光岩石、泥土、沙岩：暗部 $S$ 持平或微升，避免髒濁。
  - 有機、木材、布料：暗部 $S$ 微升，偏暖紅褐或紫褐。
  $$\text{Shadow} = H_{\text{Base}} + (15^\circ \sim 30^\circ)_{\to \text{藍紫／深紅}} \;+\; S_{\text{依反光度}} \;+\; B\downarrow$$
- **低飽和（灰系）材質**（石頭、鐵）：色相本身不明顯，改用「亮部帶一點暖灰、暗部帶一點冷灰」的微弱色偏。

| 色階定位 | 色相 ($H$) 變化趨勢 | 飽和度 ($S$) 趨勢 | 明度 ($V$) 趨勢 | 實戰規範 |
| :--- | :--- | :--- | :--- | :--- |
| **極亮點 (Specular)** | Base $+15^\circ \sim +20^\circ$（往黃 / 暖白） | 低 ($25\% \sim 40\%$) | 極高 ($85\% \sim 95\%$) | 高反光點，切勿使用 `#FFFFFF` |
| **亮部 (Light)** | Base $+10^\circ$（往暖） | 中低 ($45\% \sim 55\%$) | 高 ($70\% \sim 80\%$) | 左上受光面主色 |
| **固有色 (Base/Mid)** | 材質標準色相 | 中等 ($50\% \sim 65\%$) | 中等 ($50\% \sim 65\%$) | 決定物體顏色的基準點 |
| **暗部 (Shadow)** | Base 往冷 $15^\circ$（青 / 藍 / 紫） | 依反光度（金屬寶石升、岩石持平） | 低 ($30\% \sim 45\%$) | 右下背光面，帶環境冷光感 |
| **極暗/輪廓 (Outline)** | Base 往冷 $25^\circ \sim 30^\circ$（深藍 / 深紫褐） | 高 ($75\% \sim 85\%$) | 極低 ($15\% \sim 25\%$) | 外框與深縫，切勿使用 `#000000` |

#### 🌑 深色與黑系材質專項分流（當平均明度 $\overline{\text{Lum}} \le 0.25$ 或平均 $V \le 32\%$ 時強制啟用，詳見手冊第九章）
- **色相軌跡四選一（不強制亮部往 $55^\circ$ 黃色偏移）**：
  1. **無彩亮部 $\to$ 冷色深淵**（如 `deepslate`、`basalt`、`dark_slate`）：亮部與中調保持 $S \le 6\%$ 純灰，暗部轉藍紫（$H \approx 190^\circ \sim 285^\circ, S\uparrow$）。
  2. **冷亮反射 $\to$ 暖褐中調 $\to$ 深紅紫暗縫**（如 `blackstone`、`netherite`、`void_stone`）：亮部為冷紫藍灰（$215^\circ \sim 315^\circ$），中調轉暖褐，深縫收斂至暗紅紫（$310^\circ \sim 360^\circ$ 或 $0^\circ \sim 45^\circ$）。
  3. **恆定中高飽和暗色**（如 `nether_bricks`、`dark_oak`）：極低明度（$\overline{\text{Lum}} \le 0.20$）下全程維持 $S \approx 40\% \sim 80\%$ 以保住固有色調。
  4. **深淵底 ＋ 螢光高光**（如 `sculk`）：暗部佔 $>80\%$，亮部往青綠偏移且 $S$ 反向升至 $85\% \sim 96\%$。
- **深色明度跨度與面積比**：深色方塊合理總跨度為 $\Delta\text{Lum} \approx 0.11 \sim 0.29$；深色物品相鄰色階允許 $\Delta V \ge 3.5\%$（最多 3 處微過渡）。極暗材質最暗 2~3 階須佔畫布 $65\% \sim 85\%$ 面積，最亮高光階控制在 $\le 10\%$ 面積內。
- **極暗區絕對彩度判定**：當 $V < 15\%$ 時，忽略因 RGB 整數步階造成的 HSV 假性 $S=100\%$ 飆升，改以絕對彩度 $C = \frac{\max-\min}{255} < 8\%$ 判定為低彩度過渡。

### 2.3 共通暗部（Shared Dark）與主從配色
- **共通暗部（Shared Dark）**：複合材質物品（如「金屬長柄 ＋ 幽匿錘頭 ＋ 骨刺護翼」）的最暗部應收斂至相近的深海藍或深紫褐色，賦予整體感。
- **80 / 20 互補焦點法則**：魔法或核心道具使用互補色時，維持 **80% 低飽和基底色 + 20% 高飽和發光焦點**。

### 2.4 數值化色盤規則（Cotufa 標準 ＋ Jappa 方塊雙層校準，檢核腳本 [10]~[14] 與 [18] 會自動檢查）
1. **低飽和中間調橋接（Desaturated Midtone Bridge）**：在暗部與亮部之間放一個**降飽和的過渡色**，或低飽和的互補色（例如紅色色階裡夾一個灰綠中間調），讓顏色有深度又不刺眼。整條色階的飽和度不要一路直線上升。
2. **飽和度上限**：任何顏色都**不要用到 $S = 100\%$**；鮮豔的材質也建議 $S \le 90\%$，發光焦點例外但面積要小（見 80 / 20 法則）。
3. **相鄰色階明度差（Value Contrast —— 區分物品單層與方塊雙層）**：
   - **物品（Items）**：全程相鄰明度差 **$\Delta B \ge 8\% \sim 15\%$**，確保 16×16 物品欄小圖示剪影銳利。
   - **方塊（Blocks）**：**結構主色階**（岩縫、凹槽、切面斜角、受光亮邊）相鄰相差 **$\Delta B \approx 8\% \sim 14\%$**；但**必須保留 1~3 個 $\Delta B \approx 2.5\% \sim 6\%$（$\Delta\text{Lum} \approx 0.03 \sim 0.07$）的微紋理／緩衝副色階**（詳見手冊第八章）。若方塊每兩色都拉開到 $\ge 10\%$，中間調只剩單一純色，會產生嚴重的「平塗塑膠感」與「色塊硬切感」！
4. **像素簇明暗與反平塗上限（Cluster-Based Shading & Anti-Flatness）**：明暗用 **2~6 px 的像素簇**表現，禁止單像素雜點、禁止棋盤格混色；方塊最大單一顏色佔比不得超過 **50%**（自然岩石／碎屑岩建議 $\le 40\%$），禁止出現大面積毫無微肌理的單色死區。
5. **原版不一定符合**：用原版校準時，原版的泥土、木板、蘋果幾乎沒有色相偏移，鐵錠也沒有留白。這些規則**比原版更嚴**，是本專案新畫貼圖的標準；改舊圖時以「不比原版差」為底線。

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
   - **嚴禁死黑外框**！外框必須使用該部位材質最深色階（冷偏），**1 px 寬**。
   - **外框跟隨受光**：左上受光側的外框明度比右下背光側外框**亮一階**，最暗的外框在右下角。
   - **邊角破框（Corner Softening）**：在骨刺尖端、刀刃頂點或轉角處，適度移除最尖端外框像素或以次暗色柔化，消除死硬貼紙感。
5. **材質專屬高光（Material-Specific Highlights）**：不要每種材質都只畫一圈邊緣亮光。
   - **寶石／結晶**：內部畫刻面（facet）——左上一小塊亮面＋對角另一側的反射亮點（折射感），中間保留飽和的固有色。
   - **金屬**：沿著物體長軸畫**拉長的異向性光澤（Anisotropic Sheen）**，1 px 寬、3~5 px 長的高光條，平行於刃身或錠的長邊。
   - **木柄、皮革、布料**：沿纖維方向的 1×2~1×3 px 暗紋，高光柔和不刺眼。

#### A-2 原版物品幾何與剪影規則（16×16 Jappa 標準，檢核腳本 [15]~[17]）
1. **45° 對角主軸（手持工具、武器，`item/handheld`）**：
   - 握柄與刃身嚴格沿主對角線 **$y = 15 - x$**，從左下 $(0,15)$ 到右上 $(15,0)$。
   - 斜線一律 **1:1 階梯**（每往右 1 格就往上 1 格）；主軸和刃緣**禁止 2:1 或不規則的階梯**。
   - **護手（Crossguard）與鎬頭**以 $y = 15 - x$ 這條軸**左右對稱**。
2. **置中範圍與留白（一般物品，`item/generated`）**：食物、錠、寶石、染料、藥水等，主體放在中央 **12×12 ~ 14×14** 的範圍內，四周保留 **1~2 px 透明留白**。
3. **金屬錠原型（Ingot Archetype）**：用 **2:1 斜率**（每橫走 2 px 升 1 px）做出類等角視角，分成 **3 個面**：頂面（最亮）、左側短斜面（中間調）、右下長側面（暗）。
4. **無鋸齒曲線（Jaggie-Free Curves）**：曲線的階梯長度要**單調變化**，例如 **4 → 2 → 1 → 2 → 4**；不要長短段隨機交錯（如 1 → 3 → 1）。
5. **外框角對角相接（Corner-Touching Outlines）**：曲線和斜線上的 1 px 外框以**對角相接**；**嚴禁 2×2 的 L 形實心轉角（Doubled Corners）**，轉角內側多出的那一格要拿掉。

### 工法 B：自然方塊與建材 ——「Plantkillable 像素簇降噪 ＋ ArtsByKev $3 \times 3$ 無縫四部曲」
適用於：岩石、地層、鵝卵石、磚塊、木板、沙土、樹皮。

1. **消滅孤兒像素（No Orphan Pixels）與像素簇技法（Pixel Clustering）**：
   - **嚴禁隨機單像素噴點（Pixel Noise）**！
   - 將 2 ~ 6 個同色階像素聚集成**像素簇（Cluster）**，依 Step 0 的現實岩石肌理決定簇的形狀（例如：鵝卵石用圓塊簇、頁岩／板岩用水平薄層簇、查羅石用漩渦纖維簇）。
2. **對比度收斂與視覺重量均衡（消除 Grid Effect）**：
   - 方塊明度跨度要比物品更窄、更柔和，且 $16 \times 16$ 四個象限的視覺重量必須均衡，避免大面積平鋪時產生井字網格或重複斑點。
3. **無縫繪製四部曲 SOP（所有座標強制使用 `(x % 16, y % 16)` 環繞映射）**：
   - **Step 3.1 鋪設底色與暗部網格（Base & Grout）**：用**第二暗色**鋪底，再用**最暗色（冷偏）**畫出自然跨越 $16 \times 16$ 邊界的半封閉不規則縫隙網格（禁止畫出筆直十字線，也禁止在平塗底色上只畫零散漂浮短橫線）。
   - **Step 3.2 編織雙／三色微肌理主體（Blocking in Multi-Tone Grain Clusters）**：用 **2~3 個微差中間調（$\Delta\text{Lum} \approx 0.03 \sim 0.06$）** 交織填滿每個石塊／平整切面內部，徹底消滅 $\ge 4 \times 5$ 的單色平塗死區（即便是 `cut_*` 切製石或 `chiseled_*` 雕紋背景板也必須有微差砂粒斑駁！）。
   - **Step 3.3 植入左上角光影與逐階緩衝（Top-Left Lighting & 1-Step Cushioning）**：在**每一顆像素簇的左上緣**畫上**亮部色階（暖偏）**（最亮點必須托在次亮簇上，不可孤立漂浮在底色裡造成雪花麻點）；在**右下緣（緊貼深色縫隙內側）**必須補上 $1\text{ px}$ **次暗緩衝色階**，嚴禁最深裂縫直接裸露切割亮色底面或直接撞擊極亮高光！
   - **Step 3.4 $3 \times 3$ 與遠景檢視（Zoom-Out Inspection）**：觀察 $3 \times 3$（$48 \times 48$）與 $4 \times 4$（$64 \times 64$）平鋪陣列，打散任何看起來像「一排眼睛／笑臉／重複橫虛線」的搶眼結構。
4. **巨觀與微觀平衡（Macro vs. Micro）**：一定要縮小看平鋪的整體效果（巨觀），雜紋分布要讓整面牆看起來是具顆粒體感的自然建材，既不能是滿滿的高對比雪花雜點，也不能是死平光滑的塑膠色塊。

#### B-2 原版方塊結構拓撲（`textures/block/`，檢核腳本 `--kind` 對應的 [15]~[18]）
1. **木板（`--kind planks`）**：垂直分成 **4 列，每列 4 px 高**（$y \in \{0..3, 4..7, 8..11, 12..15\}$），每列底部一條較暗的接縫；**上下兩列的直向接頭錯開**；木紋用水平 **1×3 ~ 1×6 px** 的像素簇。
2. **磚與瓷磚（`--kind bricks`）**：每層 **8 px（2 層）或 4 px（4 層）** 高，**相鄰兩層橫向錯開 50%（8 px）**；每塊磚**左上邊緣提亮**，**右下的灰縫加暗**。
3. **雕紋與切製／金屬方塊（`--kind chiseled`）**：外圍一圈 **1 px 斜面邊框**（$x=0$、$y=0$ 亮；$x=15$、$y=15$ 暗）；中央 **14×14** 至少**一軸（最好兩軸或四軸）鏡像對稱**。石質雕紋／切製內板須保留 2~3 色微差砂粒斑駁，浮雕凹槽轉角須有次亮／次暗緩衝倒角。
   - **雕紋方塊一定要有頂底面**（和側面不同，和**平滑版**一樣，照原版雕紋砂岩＝平滑砂岩的頂面）：模型用 `minecraft:block/cube_column`，`side` 是雕紋貼圖、`end` 是該石材平滑版的貼圖；沒有平滑版的石材，用 `tools/texture_pipeline/chiseled_tops.py` 依石磚色階畫一張平滑風格的 `<雕紋貼圖>_top.png`（平整石面＋1 px 斜面外框）。`building_sets.py` 新增石磚組時會自動這樣做。
   - **雕紋圖騰必須是該生態域代表生物的頭像**（如同原版雕紋砂岩刻的是沙漠的苦力怕臉）：有 Boss 的生態域用 Boss 的頭，沒有 Boss 的用當地最常見、輪廓最好認的生物；畫成左右對稱的浮雕或凹刻，抓 2~3 個辨識特徵（王冠、眼睛、角、嘴）就好，不要硬塞細節。先用 `tools/models/geo_preview3d.py` 畫出生物正面當參考。

     | 生態域（石材所屬） | 雕紋頭像 | 辨識特徵 |
     | :-- | :-- | :-- |
     | 琥珀沙丘 `amber_dunes` | Monarch（Boss） | 三尖王冠、兩道橫向眼縫（`chiseled_amber_sandstone` 已採用） |
     | 琥珀沙丘的淺沙 `pale_sand` | Scavenger（最常見） | 往外上翹的兩支彎角、兜帽、凹陷臉部裡的兩隻眼（`chiseled_pale_sandstone` 已採用） |
     | 柳絮林地 `willow_grove` | Harmonizer（Boss） | 兩側分岔觸角、中央一隻眼、寬領片（`chiseled_abyssal_strata_bricks` 已採用） |
     | 柳絮林地的青碧地層 `teal_strata` | Blub（最常見） | 兩隻兔耳、小眼與嘴（`chiseled_teal_strata_bricks` 已採用） |
     | 紫晶深板岩區 `violet_slate_abyss` | Sculk Monstrosity（Boss） | 依模型正面取特徵 |
     | 赤紅沉積峽谷 `crimson_strata_canyon` | Dartback（最常見） | 背上一排刺、寬扁身體、兩隻小眼（`chiseled_crimson_strata_bricks` 已採用） |
     | 赤紅峽谷的流紋岩 `ember_stone` | Fusefly（第二常見） | 膠囊頭、頭頂引信、兩隻大眼（`chiseled_ember_stone_bricks` 已採用） |
     | 赤紅峽谷地下的粉砂岩 `silted_strata` | Prickle（第三常見） | 兩根觸角、底下一排短腳（`chiseled_silted_strata_bricks` 已採用） |
     | 搖籃曲山丘 `lullaby_hills` | Echo Golem／Singer | 頭頂的靈魂晶塊、耳朵 |
     | 紅區洞穴 `red_zone_caves`／地底 `void_stone` | Stalker（最常見） | 方頭、兩個耳狀凸起、凹刻面罩裡兩隻眼（`chiseled_void_stone_bricks` 已採用） |
4. **沉積岩／砂岩五件套（`top` / `side` / `bottom` / `cut` / `chiseled`）**：`top` 用窄跨度（$\Delta\text{Lum} \approx 0.11 \sim 0.18$）全柔和砂粒簇；`side` 上方 $y=0..3$ 為水平壓實頂蓋層、下方 $y=4..15$ 為半封閉圓潤碎屑岩塊網格；`bottom` 為滿版無高光粗糙碎屑岩塊（詳見手冊 8.3 節）。
5. **礦石嵌入（`--kind ore --base <原石>`）**：**外圍 1~2 px 保留原石的原樣**（平鋪時才不會露出礦石的接縫）；礦簇放在**中央 12×12**，每個礦簇**正下方加 1 px 的深色原石陰影**，讓礦物看起來嵌在岩石裡。
6. **環面無縫（Torus Wrapping，石頭、泥土、樹葉等自然方塊）**：越過 $x=15$ 的像素簇要從 $x=0$ 自然接回來，$y$ 方向也一樣；**不要有超過 4 px 的筆直水平／垂直邊界**，平鋪後會變成明顯的格線（木板、磚、雕紋的縫是刻意的直線，不在此限）。
7. **石材建材家族（每種石頭升級時一起做）**：
   - **石磚系列的磚形一律從原版 `*_bricks` 挑一種當骨架**（stone／deepslate／polished_blackstone／cinnabar／sulfur／tuff／quartz／end_stone／mud／nether／red_nether／bricks／resin／prismarine，共 14 種，歸成 5 種骨架）：依石材硬度與現實參照物選一張，只借層高、磚寬、錯縫、灰縫，色階與微紋理重畫。裂紋、苔蘚版與石磚的半磚／階梯／牆都沿用挑好的那一張。
   - **`*_tiles`、`polished_*`、`smooth_*`、`chiseled_*` 也從原版同類方塊挑**，依現實參照物決定做不做、用哪一款（例：板岩才做 `deepslate_tiles` 式板岩瓦；有礦物顆粒的岩石用有框的 `polished_granite` 式，層狀或極細粒岩用無框的 `polished_deepslate`／`polished_blackstone` 式；玄武岩的平滑用 `smooth_basalt` 式）。
   - **完整清單、量測數據、5 種骨架與每種 Sift 石材的建議對應，見 [`references/vanilla_building_patterns.md`](references/vanilla_building_patterns.md)**（對照圖 `vanilla_building_patterns.png`）。
   - **每個方塊都要有衍生方塊**：本體、石磚、裂紋石磚、磨製、磚瓦、裂紋磚瓦、平滑都要有**半磚、階梯、牆**（原版沒有的形式，例如裂紋磚的半磚，就用其他形式的模型、配方當範本改寫）。只有柱與浮雕石磚不做衍生。
   - 實例：虛黑岩（玄武岩）家族，`tools/worldgen/paint_void_stone.py`（貼圖）＋ `tools/worldgen/build_void_stone_family.py`（方塊資源）＋ `block/VoidStoneFamily.java`。

### 工法 C：色階排名／HLS 位移重映射法（Rank / HLS Offset Recoloring）
適用於：已有高品質原版結構（如木門、活板門、告示牌、沙岩家族衍生品），需將原版色階精準轉換為新材質色盤時（參考 [`tools/worldgen/build_soul_willow_wood.py`](../../../tools/worldgen/build_soul_willow_wood.py)、[`tools/worldgen/build_sandstone.py`](../../../tools/worldgen/build_sandstone.py)）。
- 必須確保目標色盤本身符合 **Step 2 的色相偏移（Hue Shifting）**，而非單純平移 Hue。

### 工法 D：CIELAB 感知空間轉換管線（`tools/texture_pipeline/recolor.py`）
適用於：需要對大量現有貼圖進行感知均勻（Perceptually Uniform）色調轉換與自動對比調整時。
- **專案規定的流程**：`recolor.py scan` → 讓使用者看 `build/texture_pipeline/out/recolor_review.png` 確認 → `apply`。使用者的決定（排除的池、指定參考貼圖、可改的共用貼圖）記在 `tools/texture_pipeline/recolor_overrides.json`，不要寫死在程式裡。
- 手動改 PNG 之後，`verify.py` 會把它列為「外部改的」；這是正常的提醒，不是錯誤。

### 工法 E：本專案（pysift，Minecraft 26.3）的特殊貼圖
1. **尺寸一律 2 的次方**（16／32／64）：非 2 的次方會讓**整個方塊圖集**的 mipmap 降級，遠處所有方塊都變閃（`dusk_bloom` 21×21 的教訓）。動畫貼圖的高度要是寬度的整數倍。
2. **模型 UV 一律在 0~16 內**：Blockbench 自動排 UV 時可能把背面排到貼圖外，Blockbench 裡看起來透明，遊戲裡會取到圖集中**別張貼圖**的像素。匯出前每一面都要檢查，Blockbench 寫錯的命名空間（專案名稱）要改回 `pysift:`。
3. **可染色貼圖（`tintindex`）畫成灰階**：例如依地板染色的草（FloorTint）和柔和草的灰色母版，顏色由遊戲或色盤腳本上色，貼圖只負責明暗；灰階的 ΔV 規則照樣適用。
4. **發光層（`_glow` 貼圖、`light_emission`）**：基底貼圖照常畫完整；發光層**只畫發光的像素**，其餘透明，兩張的發光點位置要對齊。
5. **翻轉、旋轉只在模型 UV 處理**（`models/block/templates/`），不要另存翻轉過的 PNG。
6. **物品圖示可以是 32×32**（立體植物的圖示由 `tools/worldgen/veg_models.py icon` 算繪）：32×32 時所有像素尺寸規則（留白、外框、像素簇）都乘 2。
7. **腳本產生的貼圖寫入時一律經過 `tools/art_guard.py`**，使用者用同檔名覆蓋後不會被蓋回去；臨時圖、AI 產生的圖要列進 `art_requests/`（`tools/build_art_requests.py`）。

---

## 第四步（Step 4）：檔案防護與 18 項檢核（Mandatory Verification）

### 4.1 備份與防護規範（Art Guard）
1. **寫入前備份**：覆寫任何 `src/main/resources/assets/pysift/textures/` 下的現有貼圖前，先備份至 `.texture_backups/<timestamp>_<task>/`。
2. **禁止覆寫受保護手工貼圖**：若腳本會批次產生貼圖，務必像 [`tools/art_guard.py`](../../../tools/art_guard.py) 一樣保護已定稿的精品貼圖。

### 4.2 執行自動化檢核與預覽圖生成
每完成一張或多張貼圖後，**必須執行**本 Skill 的檢核腳本，並用 `--kind` 指定材質類型（決定進階規則）：
```powershell
python -I .claude/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py src/main/resources/assets/pysift/textures/item/<物品>.png --kind item
python -I .claude/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py <手持工具或武器>.png --kind handheld
python -I .claude/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py <方塊>.png --kind block      # 或 planks / bricks / chiseled
python -I .claude/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py <礦石>.png --kind ore --base block/stone.png
```
`--kind` 可用：`auto`（預設：滿版 = block、透空 = item）、`item`、`handheld`、`block`、`planks`、`bricks`、`chiseled`、`ore`。
腳本會自動輸出 `build/previews/texture_audit_<name>.png`，你必須用 `read_file` 檢視該圖片，並逐一確認通過以下檢核。

**《繪師隨身 8 點檢核表》**（基本項目）：

- [ ] **1. 灰階測試（Grayscale Test）**：一般材質跨度 $\Delta\text{Lum} \ge 0.22$；深色材質（$\overline{\text{Lum}} \le 0.25$）跨度 $\Delta\text{Lum} \ge 0.11$，黑白灰階下立體結構清晰。
- [ ] **2. 色相偏移檢查（Hue Shifting）**：亮部是否往暖色（黃）偏移並降飽和？暗部是否往冷色（藍/紫）偏移並升飽和？
- [ ] **3. 拒絕純黑純白（No `#000000` / `#FFFFFF`）**：檢核報告是否確認零純黑、零純白像素？
- [ ] **4. 孤兒像素清理（Orphan Pixels Cleanup）**：（特別針對方塊）是否已消除無意義的孤立單像素，整合成 2~6 像素的像素簇（Clusters）？
- [ ] **5. 光源一致性（Top-Left Light Source）**：高光是否統一集中在物體與每個結構簇的**左上方**，陰影集中在**右下方**？
- [ ] **6. 外框柔和度（Sel-Out，針對物品）**：外框是否使用材質深色系而非死黑？左上受光面外框是否比右下亮一階？尖角是否適度破框柔化？
- [ ] **7. 無縫邊界測試（$3 \times 3$ Tiling，針對方塊）**：在預覽圖的 $3 \times 3$ 平鋪視圖中，跨邊界處是否完全看不出接縫或斷裂直線？
- [ ] **8. 網格效應測試（Zoom-Out Grid Effect，針對方塊）**：在預覽圖的 $4 \times 4$ 原尺寸縮小平鋪陣列中，視覺重量是否均勻、無重複刺眼斑點？

**進階規則（Cotufa + Jappa 標準，腳本輸出的 🧭 區塊；⚠️ 要修，ℹ️ 是建議）**：
- [ ] **9. 2 的次方尺寸**：16／32／64；動畫貼圖高度是寬度的整數倍。
- [ ] **10. 每條色階的色數**：物品 3~7（深色物品允許至 8）；方塊 4~8（深色雙色溫方塊允許至 9）。
- [ ] **11. 相鄰色階明度差**：一般物品全程 $\Delta V \ge 8\%$（深色物品允許 $\Delta V \ge 3.5\%$ 且最多 3 處微過渡）；方塊結構主色間 $\ge 8\%$，並允許 1~4 處（深色方塊最多 6 處）$<5\%$ 的表面微紋理／緩衝副色階。
- [ ] **12. 相對色相偏移**：一般材質亮部往暖 $+10^\circ \sim +20^\circ$、暗部往冷 $15^\circ \sim 30^\circ$；深色材質符合四大深色軌跡之一（標準深色偏移／無彩亮部→冷淵暗部／冷亮→暖褐暗紅紫雙色溫／濃彩深色或螢光軌跡）。
- [ ] **13. 低飽和中間調橋接、飽和度上限**：中段有降飽和過渡色；排除極暗量化誤差（$V < 15\%, C < 8\%$）後無真實 $S \ge 98\%$ 純色。
- [ ] **14. 禁止棋盤格混色**：沒有 3×3 的兩色交錯。
- [ ] **15.**（物品）**置中 12~14 px、留白 1~2 px**（手持工具除外）／（方塊）**沒有超過 4 px 的環面直線**。
- [ ] **16.**（物品）**沒有 L 形雙角**／（方塊）**木板 4 列、磚塊錯縫、雕紋斜面外框、礦石外圍保留原石**（依 `--kind`）。
- [ ] **17.**（手持）**像素沿 $y = 15 - x$ 主軸**／（雕紋）**中央鏡像對稱，圖騰是該生態域生物的頭像**／（礦石）**礦簇下方有 1 px 陰影**。
- [ ] **18.**（方塊）**反平塗與色階過渡檢核（Anti-Flatness & Soft Transitions）**：最大單一顏色佔比 $\le 55\%$、相鄰像素紋理變化率 $\ge 45\%$，且至少 $20\%$ 的異色邊界為 $\Delta\text{Lum} < 0.10$ 的柔和緩衝過渡（徹底杜絕 AI 平塗塑膠感與跨階硬切斷層）。

> 門檻是用原版 26.3 貼圖校準過的；第 12 項（色相偏移）、第 15 項（物品留白）、第 16 項（礦石外圍）**比原版更嚴**，原版本身也常跳警告，新畫的貼圖要符合，改舊圖時以「不比原版差」為底線。

最後，若變更了資源包內的檔案，執行專案完整性驗證：
```powershell
python -I tools/texture_pipeline/verify.py .
```
