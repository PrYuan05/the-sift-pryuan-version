---
name: mc-start
description: "pysift 模組專案的起點：讀進度表、git 狀態與建置狀況，說明現在在哪個階段並建議下一步。使用者說「從哪開始」、「下一步做什麼」、「專案現在怎樣」、「start」、「next step」時使用。"
argument-hint: "[可選：想做的方向，例如 生物 / 方塊 / 維度]"
allowed-tools: Read, Glob, Grep, Bash(git status*), Bash(git log*), Bash(git branch*), AskUserQuestion
---

# 專案起點（mc-start）

改寫自 claude-code-game-studios 的 `/start` 與 `/next-step`。只讀，不改檔。

## 1. 收集現況（全部做完再回報）

1. 讀 `CLAUDE.md` 與 `MODDING_ROADMAP_AND_SPECS.md` 第二節「進度表」與第五節「待辦」。
2. `git status -sb`、`git log --oneline -10`：目前分支、未 commit 的變更、最近做了什麼。
3. 數量盤點（用 Glob 計數，不要猜）：
   - `src/main/java/pryuan05/pysift/entity/mob/*.java`（生物數）
   - `src/main/resources/assets/pysift/blockstates/*.json`（方塊數）
   - `src/main/resources/assets/pysift/items/*.json`（物品定義數）
   - `src/main/resources/data/pysift/dimension*/**`（維度是否已開始）
   - `design/specs/*.md`（已寫好的規格）
4. 有未 commit 的變更時，提醒使用者：其他 AI（Antigravity、IntelliJ）可能也在改，先 commit 再大量修改。

## 2. 回報格式

```
## 專案現況
- 分支：… ／ 未 commit：N 個檔案
- 方塊 N、物品 N、生物 N、維度：未開始／進行中
- 最近完成：…（取自 git log）

## 建議下一步（依進度表優先順序）
1. … → `/mc-xxx`
2. …
3. …
```

## 3. 讓使用者選

用 `AskUserQuestion` 給 2–4 個選項（每個對應一個 `/mc-*` 技能），第一個標 (Recommended)。
使用者選了之後，告訴他輸入哪個指令，或直接開始該技能的流程。

## 技能對照

想法還很模糊 → `/mc-brainstorm`；想法清楚但要定數值 → `/mc-quick-design`；
直接實作 → `/mc-add-block`、`/mc-add-item`、`/mc-add-mob`；生物 AI 與技能 → `/mc-team-mob`；
維度與生物群系 → `/mc-worldgen`；檢查 → `/mc-asset-audit`、`/mc-code-review`、`/mc-smoke-check`；
崩潰 → `/mc-crash-debug`；發佈 → `/mc-release`。
