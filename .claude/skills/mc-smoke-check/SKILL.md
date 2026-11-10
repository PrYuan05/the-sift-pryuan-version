---
name: mc-smoke-check
description: "交付前的快速驗證：compileJava、build -x test、verify.py、JSON 語法、遊戲內必測清單。使用者說「跑一下檢查」、「可以 commit 了嗎」、「smoke test」、「驗證」、「build 看看」時使用。"
argument-hint: "[quick | full]"
allowed-tools: Read, Glob, Grep, Bash(./gradlew*), Bash(python -I tools/texture_pipeline/verify.py*), Bash(python -I -c*), Bash(git status*), Bash(git diff --stat*)
---

# 冒煙測試（mc-smoke-check）

改寫自 claude-code-game-studios 的 `/smoke-check`。失敗就是失敗，不能交付。

## 步驟（`quick` 做 1–3，`full` 全做）

1. **JSON 語法**：解析 `src/main/resources/**/*.json`，列出無法解析的檔案。
2. **compileJava**：`./gradlew compileJava`（Windows `.\gradlew.bat compileJava`）。
3. **verify.py**：`python -I tools/texture_pipeline/verify.py .`。
4. **完整建置**：`./gradlew build -x test`，確認 `build/libs/` 產出 jar。
5. **遊戲內清單**（交給使用者 `runClient`，依 `git diff --stat` 只列和這次改動有關的項目）：
   - 進入世界不崩潰、`latest.log` 無 `pysift` 相關 ERROR
   - 新方塊／物品：分頁可見、非紫黑、可放置與挖掘、掉落正確
   - 新生物：生怪蛋生成、看得見、有動畫、行為符合規格
   - 語系：切換 zh_tw 看名稱

## 回報

```
| 步驟 | 結果 | 備註 |
| JSON | PASS / FAIL(n) | |
| compileJava | PASS / FAIL / NOT ASSESSED（例如沒有 JDK 25） | |
| verify.py | PASS / FAIL(n) | |
| build | … | |
| 遊戲內 | 待使用者確認 | 清單 |
結論：可以 commit ／ 先修 ／ 無法判斷（缺什麼）
```
不能執行的步驟絕對不要寫成 PASS。
