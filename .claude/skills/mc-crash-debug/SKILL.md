---
name: mc-crash-debug
description: "分析 Minecraft／Fabric 崩潰與錯誤：crash-report、latest.log、Gradle 編譯錯誤、Mixin 失敗、紫黑貼圖、隱形實體，找出根因並提出最小修正。使用者貼上錯誤訊息、stack trace、說「崩潰」、「crash」、「進不去遊戲」、「編譯失敗」時使用。"
argument-hint: "[貼上的錯誤，或 log 檔路徑，例如 run/logs/latest.log]"
allowed-tools: Read, Glob, Grep, Edit, Bash(./gradlew*), Bash(git log*), Bash(git diff*), AskUserQuestion
---

# 崩潰除錯（mc-crash-debug）

改寫自 claude-code-game-studios 的 `/bug-report` 與 `/hotfix`。

## 1. 取得證據

- 使用者貼的訊息；或 `run/crash-reports/` 最新檔、`run/logs/latest.log`。
- 找出 **第一個** `Caused by:` 與最底層的 `pryuan05.pysift` 堆疊行；Mixin 錯誤找 `MixinApplyError` / `InvalidInjectionException`。
- `git log -5` 與 `git diff`：最近改了什麼。

## 2. 常見對照（先比對再深入）

| 症狀 | 常見原因 |
| --- | --- |
| `Identifier not set` / `Block id not set` | Block 或 Item 的 Properties 少了 `.setId(key)` |
| `Duplicate registration` / `already registered` | ID 重複，或 register 被呼叫兩次 |
| 物品欄紫黑方塊 | 缺 `assets/pysift/items/<id>.json` 或模型路徑錯 |
| 放置後紫黑 | blockstate 缺 variant、模型或貼圖路徑錯、命名空間寫成 `sift:` |
| 實體隱形 | 沒註冊渲染器、geo 路徑錯、貼圖路徑錯 |
| 實體不動或 `Could not find animation` | 動畫名稱不是 `animation.<id>.idle/walk` |
| `NoClassDefFoundError: net/minecraft/client/...`（伺服器） | main 引用了 client 類別 |
| 屬性 NPE / `Unable to find attribute` | 缺 `FabricDefaultAttributeRegistry.register` |
| `cannot find symbol` 帶 Yarn 名稱 | 混用 Yarn 映射，改為 Mojang 名稱 |
| Gradle `Unsupported class file major version` | JDK 不是 25，檢查 `gradle.properties` 的 `org.gradle.java.home` |

## 3. 報告

```
症狀：…
根因：…（引用 log 行與程式碼 檔案:行號）
信心：高 / 中 / 低（低的話說還需要什麼證據）
修正：最小改動（diff）
驗證方式：…
```

## 4. 修正

使用者同意後才改；改完跑 `./gradlew compileJava`。需要遊戲內重現的步驟交給使用者，
並請他回報新的 `latest.log`。不要為了讓錯誤消失而刪除功能或吞掉例外。
