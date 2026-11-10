---
name: mc-add-block
description: "在 pysift 新增或修改方塊，逐項完成 CLAUDE.md 的 7 項必備檔案（blockstate、模型、物品定義、掉落表、挖掘標籤、語系、Java 註冊）並驗證。使用者說「加一個方塊」、「新方塊」、「add block」、「方塊變紫黑」時使用。"
argument-hint: "<block_id> [cube|pillar|facing] [Mat: STONE|DEEPSLATE|WOOD|GRAVEL|SAND|GRASS] [狀態屬性，如 rust:0-3]"
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(./gradlew*), Bash(python -I tools/texture_pipeline/*), Bash(git status*), Bash(git diff*), AskUserQuestion, Agent
---

# 新增方塊（mc-add-block）

改寫自 claude-code-game-studios 的 `/dev-story`，針對 Fabric 26.3 方塊。

## 0. 前置檢查

- ID 必須是 `snake_case`，命名空間一律 `pysift`（不可用 `sift`、`custom`）。
- Grep `ModBlocks.java` 的 `DEFS` 確認 ID 未被使用。
- 貼圖是否已存在於 `assets/pysift/textures/block/`？沒有的話問使用者要用哪張，**不要自己畫 PNG**。
- 有 `design/specs/<id>.md` 就照它做。
- `git status` 有未 commit 的資源變更時，先請使用者 commit（其他 AI 可能也在改）。

缺少的資訊（形狀、材質、狀態屬性、工具）用一次 `AskUserQuestion` 問完。

## 1. Java 註冊（`block/ModBlocks.java`）

本專案用 `DEFS` 清單 + `Def` 建構器，**不要另外寫 `Registry.register`**，`register(Def)` 會處理
`.setId(blockKey)`、BlockItem、`ALL_BLOCKS`、`BY_NAME` 與創造模式分頁：

```java
block("<id>", Mat.STONE),                         // 單一方塊
pillar("<id>", Mat.WOOD),                          // RotatedPillarBlock，axis
facing("<id>", Mat.STONE),                         // 六向，頂面朝 facing
block("<id>", Mat.STONE).intProp("rust", 0, 3),    // 遞增狀態
block("<id>", Mat.STONE).tones("warm", "cool"),     // 色調（值需存在於 SiftStateProperties.Tone）
```

新的 `Mat` 只在使用者同意後加入 enum。

## 2. 資源檔（照現有同類方塊複製結構，例如 `rusted_dark_cobble`）

| # | 檔案 | 注意 |
| - | --- | --- |
| 1 | `assets/pysift/blockstates/<id>.json` | 每個狀態組合都要有 variant；pillar 用 `axis=x/y/z` 並以 `x`/`y` 旋轉 |
| 2 | `assets/pysift/models/block/<id>.json`（多狀態放 `models/block/<id>/<id>_<prop><n>.json`） | 翻轉／旋轉用 `models/block/templates/` 的模板與 UV，**不要產生翻轉過的 PNG** |
| 2b | `assets/pysift/models/item/<id>.json` | `parent` 指向方塊模型 |
| 3 | `assets/pysift/items/<id>.json` | 單一狀態：`{"model":{"type":"minecraft:model","model":"pysift:item/<id>"}}`；多狀態用 `minecraft:select` + `block_state_property`（照 `rusted_dark_cobble`） |
| 4 | `data/pysift/loot_table/blocks/<id>.json` **和** `data/pysift/loot_tables/blocks/<id>.json` | 有狀態屬性時加 `copy_state` modifier；`random_sequence` 為 `pysift:blocks/<id>` |
| 5 | `data/minecraft/tags/block/mineable/<pickaxe\|axe\|shovel\|hoe>.json` | 只加入 `"pysift:<id>"`，保留 `"replace": false` |
| 6 | `assets/pysift/lang/en_us.json`、`zh_tw.json` | 鍵 `block.pysift.<id>`；兩個檔案都要加 |

所有 JSON 中的資源位置都用 `pysift:`。

## 3. 驗證（全部跑，回報實際輸出）

```bash
./gradlew compileJava                              # Windows: .\gradlew.bat compileJava
python -I tools/texture_pipeline/verify.py .       # exit 1 = 有錯，逐條修
```

這個環境若沒有 JDK 25 而無法編譯，回報 **NOT ASSESSED — compileJava 無法執行（原因）**，不可說通過。
遊戲內檢查（物品欄不是紫黑方塊、可放置、正確工具可挖、掉落自己、狀態保留）交給使用者 `runClient`，
列成清單讓他勾。

## 4. 收尾

列出新增／修改的檔案，問使用者要不要 commit（訊息格式：`feat(blocks): add <id>`）。
貼圖要調色時改走 `tools/texture_pipeline/README.md` 的 `recolor.py scan → 使用者確認 → apply`。
