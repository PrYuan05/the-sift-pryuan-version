---
name: mc-brainstorm
description: "為 The Sift 模組發想新內容：生物、方塊家族、物品、生物群系、Boss 技能。使用者想要點子、想換方向、說「幫我想」、「brainstorm」、「有什麼可以加」時使用。"
argument-hint: "[類型：mob | block | item | biome | boss | open] [主題提示]"
allowed-tools: Read, Glob, Grep, Write, AskUserQuestion, WebSearch
---

# 內容發想（mc-brainstorm）

改寫自 claude-code-game-studios 的 `/brainstorm`。目標是得到一個使用者選定的點子，
而不是一長串清單。

## 1. 先讀世界觀（不要憑空發想）

- `MODDING_ROADMAP_AND_SPECS.md`：已有 24 款生物、方塊家族、未完成系統（戰鬥 AI、維度、音效）。
- `src/main/java/pryuan05/pysift/entity/mob/`：已有的生物名稱，避免撞名或功能重疊。
- `src/main/java/pryuan05/pysift/block/ModBlocks.java` 的 `DEFS`：已有的方塊與狀態屬性（`charge`、`rust`、`tone`…）。
- `design/specs/`：已寫過的規格。

## 2. 一輪問題（一次問完，每題都有預設答案，使用者可以回「你決定」）

用 `AskUserQuestion`，最多 4 題，依類型挑：
- **生物**：敵對／中立／被動？出現在哪個區域？玩家打倒後得到什麼？要不要可馴服？
- **方塊**：屬於哪個地層／生物群系？單一、柱狀、六向、或遞增狀態（如 `rust 0..3`）？用什麼工具挖？
- **物品**：材料、工具、食物、還是任務物品？由什麼方塊或生物掉落？
- **生物群系**：地表方塊、地下地層、會生成哪些生物、氛圍（顏色、音效）？

## 3. 給 3 個提案

每個提案用同一個格式：

```
### <名稱>（pysift:<snake_case_id>）
一句話：…
玩法：玩家會怎麼遇到它、怎麼互動、為什麼有趣
與現有內容的連結：用到哪些現有方塊／生物／物品
實作量：小 / 中 / 大（列出要新增的檔案類型）
風險：例如需要新動畫、需要 Mixin、需要自訂 worldgen
```

不要抄現有模組或原版生物的設計；可以參考原版機制（例如 Warden 的震動偵測）但要說明差異。

## 4. 選定並記錄

使用者選定後，寫入 `design/ideas/<id>.md`（上面的格式加上使用者的原話），
然後建議下一步：`/mc-quick-design <id>`。
