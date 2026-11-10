---
name: mc-team-mob
description: "編排生物團隊（mob-ai-designer → fabric-programmer → geckolib-animator → mod-qa-tester），從設計到實作再到驗證，完成生物 AI、攻擊技能、Boss 機制與動畫綁定。使用者說「幫 X 做 AI」、「Boss 技能」、「攻擊邏輯」、「砸地／音波攻擊」、「team mob」時使用。"
argument-hint: "<mob_id> <功能描述，例如 '近戰砸地 + 遠程音波'>"
allowed-tools: Read, Glob, Grep, Write, Edit, Agent, AskUserQuestion, TaskCreate, TaskUpdate, TaskList, Bash(./gradlew*), Bash(git status*), Bash(git diff*)
---

# 生物團隊流程（mc-team-mob）

改寫自 claude-code-game-studios 的 `/team-combat`。

**參數檢查**：沒有 `<mob_id>` 或功能描述時，輸出
「用法：`/mc-team-mob <mob_id> <功能描述>`，例如 `/mc-team-mob sculk_monstrosity 近戰砸地與音波攻擊`」然後停止。

開始前說一行：「這次會用到的代理：mob-ai-designer、fabric-programmer、geckolib-animator、mod-qa-tester」。
每個階段結束都用 `AskUserQuestion` 讓使用者選擇「繼續 ／ 修改 ／ 停止」，使用者同意前不進下一階段。
用 TaskCreate 建立五個階段的待辦，邊做邊更新。

## 階段 1：設計（`mob-ai-designer`）

輸入：`design/specs/<id>.md`（沒有就先請 designer 依 `/mc-quick-design` 模板起草）、
現有 `entity/mob/<Name>Entity.java`、同類生物的數值。
產出（寫回規格的「行為」與「數值」節）：
- Goal 優先順序表（數字越小越優先），哪些放 `goalSelector`、哪些放 `targetSelector`
- 每個技能：觸發條件、冷卻 tick、傷害、範圍、前搖與判定時間點（tick）、對應動畫名稱
- Boss：階段（血量門檻）、`ServerBossEvent` 血條要不要顯示

## 階段 2：動畫需求（`geckolib-animator`）

列出需要的動畫名稱（`animation.<id>.<name>`）、長度（秒）、是否 loop、判定在第幾 tick，
檢查現有 `.animation.json` 已有哪些。缺少的動畫列給使用者在 Blockbench 製作，**不要自己生成動畫 JSON 的關鍵影格**。

## 階段 3：實作（`fabric-programmer`）

- 自訂 Goal 放 `entity/ai/`（例如 `GroundSlamGoal`），用 Mojang 映射的 `Goal`、`EnumSet<Goal.Flag>`
- 伺服器與客戶端同步：觸發動畫用 GeckoLib 的 `triggerableAnim` + `triggerAnim(controller, name)`，
  或 `SynchedEntityData`；不要在伺服器端直接呼叫客戶端類別
- 傷害走 `hurtServer(ServerLevel, DamageSource, float)` 這類 26.3 的伺服器端 API；不確定簽名時讀現有程式或反編譯來源，不要猜
- 每完成一個技能就跑 `./gradlew compileJava`

## 階段 4：驗證（`mod-qa-tester`）

依規格的驗收條件寫遊戲內測試清單（含 `/summon pysift:<id>`、和平模式、多人同時被攻擊、卸載區塊後重新載入）。
compileJava 結果附實際輸出；不能跑的項目標 NOT ASSESSED。

## 階段 5：收尾

彙整變更檔案、未完成項目、需要使用者製作的動畫，問要不要 commit（`feat(entity): <id> <功能>`）。
