---
name: mc-localize
description: "同步 pysift 語系檔：找出 en_us.json 與 zh_tw.json 缺漏或多餘的鍵、為新方塊／物品／實體補鍵、找程式中寫死的字串（Component.literal）。使用者說「翻譯」、「語系」、「中文名稱」、「lang」、「localize」時使用。"
argument-hint: "[scan | sync | translate <key_prefix>]"
allowed-tools: Read, Glob, Grep, Edit, AskUserQuestion
---

# 語系（mc-localize）

改寫自 claude-code-game-studios 的 `/localize`。

## scan（預設，只讀）

1. 讀 `assets/pysift/lang/en_us.json`、`zh_tw.json`，列出：只在一邊的鍵、值為空、值與鍵相同（未翻譯）。
2. 從註冊來源推出應有的鍵：`ModBlocks.DEFS` → `block.pysift.<id>`；`ModItems` → `item.pysift.<id>`；
   `ModEntities` → `entity.pysift.<id>`；創造模式分頁 → `itemGroup.pysift.<tab>`。列出缺少的。
3. Grep `Component.literal(` 找寫死的玩家可見文字，建議改 `Component.translatable("…pysift…")`。

## sync / translate

- 英文名稱由 ID 轉 Title Case；中文名稱提案時沿用現有命名風格（例如生物多為音譯或意譯：布魯布、迴音傀儡）。
- 一次列出提案表（鍵 ／ en_us ／ zh_tw），`AskUserQuestion` 讓使用者確認或修改後才寫入。
- 寫入時保持原檔鍵的排序與縮排，不要重排整個檔案。
- 回覆與中文翻譯一律繁體中文（台灣用語）。
