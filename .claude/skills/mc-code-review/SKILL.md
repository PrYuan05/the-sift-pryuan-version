---
name: mc-code-review
description: "審查 pysift 的 Java 變更：Yarn 命名混入、缺 .setId、客戶端類別洩漏到 main、伺服器／客戶端邏輯沒分開、註冊遺漏、GeckoLib 用法、效能（每 tick 配置、掃描）。使用者說「review」、「看一下程式碼」、「檢查這次改動」、「code review」時使用。"
argument-hint: "[檔案或目錄；省略則審查 git diff]"
allowed-tools: Read, Glob, Grep, Bash(git diff*), Bash(git log*), Bash(git status*), Bash(./gradlew compileJava*), Agent
---

# 程式碼審查（mc-code-review）

改寫自 claude-code-game-studios 的 `/code-review`。只讀；修正要等使用者同意。

## 範圍

沒有參數 → `git diff`（含 staged）加上未追蹤的 `.java`；有參數 → 該檔案或目錄全文。

## 檢查清單（每項 PASS / FAIL / NOT ASSESSED）

1. **映射**：出現 Yarn 名稱即 FAIL —
   `AbstractBlock.Settings`、`BlockSoundGroup`、`PillarBlock`、`RegistryKey`、`RegistryKeys`、
   `new Identifier(`、`Registries.BLOCK` 當實例用、`World`（應為 `Level`）、`PlayerEntity`（`Player`）、
   `ItemStack.isOf`（`is`）、`Text.literal`（`Component.literal`）、`BlockPos.Mutable`（`MutableBlockPos`）。
2. **ResourceKey**：每個 Block / Item / EntityType 都有 `.setId(key)` 或 `.build(key)`。
3. **命名**：ID 用 `PySift.id(...)`，命名空間 `pysift`，套件 `pryuan05.pysift`。
4. **側別**：`src/main` 不可 import `net.minecraft.client.*`、`EntityRendererRegistry`、`com.geckolib.renderer.*`；
   伺服器狀態修改要在 `!level().isClientSide()` 之內。
5. **註冊完整**：新方塊在 `DEFS`；新實體有屬性註冊、生怪蛋、渲染器；新物品進創造模式分頁。
6. **GeckoLib**：動畫名稱與 `.animation.json` 一致；觸發動畫從伺服器用 triggerable anim 或同步資料。
7. **效能**：`tick()` / `aiStep()` 內沒有每 tick 的 `new` 大物件、`getEntitiesOfClass` 大範圍掃描、沒加冷卻的路徑搜尋。
8. **持久化**：新的實體欄位（例如 `ownerUUID`）有寫入與讀取存檔，否則重新載入會遺失。
9. **編譯**：可以的話跑 `./gradlew compileJava` 並附結果；不能跑就 NOT ASSESSED。

## 輸出

每個問題：`檔案:行號` — 問題 — 為什麼會壞（具體情境）— 建議修法。依嚴重度排序（崩潰 > 錯誤行為 > 效能 > 風格）。
最後一行給結論：可合併 ／ 修完再合併 ／ 需要重新設計。
