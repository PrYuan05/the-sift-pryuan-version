---
name: mc-asset-audit
description: "只讀檢查 pysift 資源一致性：錯誤命名空間（sift:、custom:）、缺少的 items/ 定義、blockstate／模型／貼圖對應、掉落表單複數、挖掘標籤、語系缺鍵、孤兒貼圖，並執行 verify.py。使用者說「檢查資源」、「紫黑方塊」、「缺貼圖」、「asset audit」、「一致性檢查」時使用。"
argument-hint: "[blocks | items | mobs | lang | all]"
allowed-tools: Read, Glob, Grep, Bash(python -I tools/texture_pipeline/verify.py*), Bash(python -I tools/texture_pipeline/consistency_report.py*), Bash(git status*)
---

# 資源檢查（mc-asset-audit）

改寫自 claude-code-game-studios 的 `/asset-audit` 與 `/consistency-check`。**只讀，不修改任何檔案。**

## 規則：沒檢查到 ≠ 通過

每一項回報 `PASS`、`FAIL (n)`、或 `NOT ASSESSED — 原因`。找不到可檢查的檔案時是 NOT ASSESSED，不是 PASS。

## 檢查項目

1. **verify.py**：`python -I tools/texture_pipeline/verify.py .`，附 exit code 與錯誤摘要（方塊、模型、貼圖、物品、掉落表、標籤、語系、色系）。
2. **命名空間**：Grep `src/main/resources` 中 `"sift:` 與 `"custom:`（排除 `sift_visual_corrected/`，那是交付候選、尚未整合）。
3. **物品定義**：每個 `models/item/*.json` 都要有 `items/*.json`；每個註冊的物品（ModItems、ModBlocks DEFS、生怪蛋）都要有。
4. **掉落表雙目錄**：`loot_table/blocks/` 與 `loot_tables/blocks/` 檔名集合一致。
5. **挖掘標籤**：每個方塊恰好出現在一個 `mineable/*.json`（除非刻意為之）。
6. **語系**：`en_us.json` 與 `zh_tw.json` 鍵集合一致；每個方塊／物品／實體都有鍵。
7. **生物資源**：每個 `ModEntities` 的 ID 都有 geo 模型、動畫、貼圖，且動畫檔含 `animation.<id>.idle` 與 `.walk`。
8. **孤兒貼圖**：`textures/` 中沒有被任何模型或 geo 引用的 PNG（列出，不刪）。

## 回報

```
| # | 項目 | 結果 | 說明 |
```
接著列出每個 FAIL 的具體檔案路徑與建議修法，並建議用 `/mc-add-block`、`/mc-localize` 等技能修。
貼圖顏色問題只能建議走 `recolor.py scan → 使用者確認 → apply`。
