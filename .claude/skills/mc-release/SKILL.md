---
name: mc-release
description: "發佈 pysift 新版本前的檢查：fabric.mod.json 中繼資料、版本號、依賴範圍、授權、圖示、變更紀錄、jar 內容、Modrinth／CurseForge 上架資訊。使用者說「要發佈」、「出新版」、「release」、「changelog」、「patch notes」時使用。"
argument-hint: "[version，例如 0.2.0] [checklist | changelog | all]"
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(git log*), Bash(git tag*), Bash(git describe*), Bash(./gradlew build*), Bash(unzip -l*), AskUserQuestion
---

# 發佈（mc-release）

改寫自 claude-code-game-studios 的 `/release-checklist`、`/patch-notes`、`/changelog`。
不會自動 push、打 tag 或上傳，這些由使用者決定。

## 1. 檢查清單（每項 PASS / FAIL / NOT ASSESSED）

- `gradle.properties` 的 `version`（目前 1.0.0）已更新
- `fabric.mod.json`：`name`、`description`、`authors`、`contact` 不是範本預設值（目前仍是 "This is an example description!"、"Me!"、fabric-example-mod 連結 → FAIL 直到改掉）
- `depends`：`minecraft ~26.3`、`fabricloader >=0.19.5`、`java >=25`、`fabric-api`、**`geckolib`**（目前未列出）
- `license` 與 `LICENSE` 檔一致
- `assets/pysift/icon.png` 存在
- 範例程式：`mixin/ExampleMixin.java` 是否仍在、是否需要
- `/mc-smoke-check full` 結果
- jar 內容（`unzip -l build/libs/*.jar`）：沒有 `sift_visual_corrected/`、`.zip`、`tools/`、開發用檔案
- `sift_visual_corrected/` 與 `.zip` 檔不得在未經使用者同意時改動或刪除

## 2. 變更紀錄

從上一個 tag（`git describe --tags --abbrev=0`，沒有就從第一個 commit）到 HEAD 的 `git log`，
依 conventional commit 前綴分組：新增內容（feat）、修正（fix）、貼圖與資源（style/assets）、其他。
寫成玩家看得懂的句子（中英各一份），存到 `CHANGELOG.md` 頂端，給使用者確認。

## 3. 上架文字（若使用者需要）

Modrinth／CurseForge 的摘要（一句）、說明（特色清單）、版本支援（Fabric、26.3）、相依（Fabric API、GeckoLib 5）。
