---
name: mc-quick-design
description: "為一個模組功能寫一頁規格（數值、行為、資源清單、驗收條件），在實作前對齊。使用者說「寫規格」、「先設計」、「定數值」、「quick design」，或要做一隻新生物／新方塊／Boss 技能前使用。"
argument-hint: "[功能描述或 design/ideas/<id>.md]"
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion
---

# 一頁規格（mc-quick-design）

改寫自 claude-code-game-studios 的 `/quick-design`。規格寫在 `design/specs/<id>.md`，
之後的 `/mc-add-*` 與 `/mc-team-mob` 都以它為依據。

## 1. 讀資料

- 若參數是 `design/ideas/<id>.md`，讀它。
- 讀相關的現有程式（例如同類生物的 `*Entity.java`、`ModEntities.java` 的尺寸、`createAttributes()` 的數值），
  讓新數值與現有內容平衡。

## 2. 不清楚的地方一次問完

用 `AskUserQuestion` 問規格中無法從現有資料推出的部分（最多 4 題）。數值給建議值和依據
（例如「血量 40：介於 Sentinel 與 EchoGolem 之間」）。

## 3. 規格模板

```markdown
# <名稱>（pysift:<id>）
狀態：草稿 ／ 已確認

## 摘要
一段話。

## 行為
- 生成／取得方式：
- 互動：
- AI Goal（生物）：優先順序 → Goal 類別 → 觸發條件
- 技能（若有）：觸發條件、冷卻（tick）、傷害、範圍、對應動畫名稱

## 數值
| 屬性 | 值 | 依據 |
| --- | --- | --- |
| MAX_HEALTH | | |
| MOVEMENT_SPEED | | |
| ATTACK_DAMAGE | | |
| 尺寸（寬×高） | | |
| 方塊硬度／爆炸抗性（`Mat`） | | |

## 資源清單（逐項打勾）
- [ ] Java：…
- [ ] assets/pysift/…（blockstates、models、items、textures、geckolib 模型／動畫）
- [ ] data/pysift/…（loot_table、recipe、tags）
- [ ] lang：en_us、zh_tw
- [ ] 客戶端：渲染器註冊

## 邊界情況
- 和平模式、水中、被推、卸載區塊時的行為…

## 驗收條件
- [ ] `./gradlew compileJava` 通過
- [ ] `python -I tools/texture_pipeline/verify.py .` exit 0（有方塊時）
- [ ] 遊戲內：…（具體可觀察的行為）
```

## 4. 確認

把規格內容貼在對話裡，`AskUserQuestion` 問「確認 ／ 修改」。確認後狀態改為「已確認」，
建議下一步的 `/mc-add-*` 或 `/mc-team-mob` 指令。
