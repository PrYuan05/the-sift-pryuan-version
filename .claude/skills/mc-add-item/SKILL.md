---
name: mc-add-item
description: "在 pysift 新增物品或材料（錠、寶石、食物、工具、任務物品），含 ModItems 註冊、現代物品定義、模型、語系、配方與創造模式分頁。使用者說「加物品」、「新材料」、「add item」、「物品變紫黑」時使用。"
argument-hint: "<item_id> [material|food|tool|misc] [描述]"
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(./gradlew*), Bash(git status*), AskUserQuestion
---

# 新增物品（mc-add-item）

## 0. 前置

- ID `snake_case`；Grep `item/ModItems.java` 確認未使用。
- 貼圖 `assets/pysift/textures/item/<id>.png` 是否存在？沒有就問使用者，不要自己產生。
- 食物、工具需要的數值（飢餓值、耐久、攻擊）沒有規格就用 `AskUserQuestion` 問，並給原版對照值當建議。

## 1. Java（`item/ModItems.java`）

照現有寫法：

```java
public static final Item <ID> = registerItem("<id>", Item::new);
```

需要自訂 `Item.Properties`（堆疊數、食物、耐久）時，沿用 `registerItem` 的模式並確保
`new Item.Properties().setId(itemKey)` —— 26.3 少了 `.setId` 會在啟動時崩潰（`Identifier not set`）。
在 `pysift_items` 分頁的 `displayItems` 中加入 `output.accept(<ID>)`。
使用 Mojang 映射名稱（`FoodProperties`、`ToolMaterial`、`DataComponents`），不要用 Yarn 名稱。

## 2. 資源

1. `assets/pysift/items/<id>.json`：`{"model":{"type":"minecraft:model","model":"pysift:item/<id>"}}`
2. `assets/pysift/models/item/<id>.json`：`{"parent":"minecraft:item/generated","textures":{"layer0":"pysift:item/<id>"}}`
   （工具用 `minecraft:item/handheld`）
3. 語系：`item.pysift.<id>` 加到 `en_us.json` 與 `zh_tw.json`
4. 配方（若有）：`data/pysift/recipe/<id>.json`，結果與材料一律用完整 ID
5. 物品標籤（若有）：`data/pysift/tags/item/` 或原版 `data/minecraft/tags/item/`

## 3. 驗證

`./gradlew compileJava`；無法執行時回報 NOT ASSESSED。遊戲內清單交給使用者：
分頁看得到、不是紫黑、名稱正確（中英）、配方可合成。
