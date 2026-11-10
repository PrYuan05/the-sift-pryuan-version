---
name: mc-worldgen
description: "建立 The Sift 維度與世界生成：dimension、dimension_type、noise_settings、biome、configured/placed feature、生物生成設定與傳送方式。使用者說「做維度」、「生物群系」、「地形」、「worldgen」、「the_sift 維度」時使用。"
argument-hint: "[dimension | biome <id> | feature <id> | spawns <biome_id>]"
allowed-tools: Read, Glob, Grep, Write, Edit, Agent, AskUserQuestion, WebSearch, Bash(./gradlew*), Bash(git status*)
---

# 世界生成（mc-worldgen）

改寫自 claude-code-game-studios 的 `/team-level` 與 world-builder 代理。資料包 JSON 為主，Java 為輔。

## 0. 先確認版本格式

26.3 的 worldgen JSON 欄位會隨版本改動。動手前：
1. 讀 `gradle.properties` 確認版本。
2. 以 loom 解出的原版資料或 `~/.gradle/caches/fabric-loom/` 內的 minecraft jar 為準，
   對照原版同類檔案（例如 `data/minecraft/dimension_type/the_nether.json`）的欄位。
3. 查不到就用 WebSearch 查 Minecraft Wiki 對應版本的格式，**並告訴使用者哪些欄位是查來的、尚未在遊戲中驗證**。

## 1. 規劃（`worldgen-designer` 代理，`AskUserQuestion` 確認）

- 維度：天空、光照、是否有天花板、高度範圍、時間流動、床與重生錨行為
- 生物群系清單：每個的地表／次地表／深層方塊（只能用 `ModBlocks.DEFS` 中已存在的 `pysift:` 方塊或原版方塊）、
  顏色（天空、霧、水、草）、環境音、生成的 pysift 生物與權重
- 進入方式：傳送門、指令、或物品

## 2. 檔案位置（全部 `pysift` 命名空間）

```
data/pysift/dimension/the_sift.json
data/pysift/dimension_type/the_sift.json
data/pysift/worldgen/noise_settings/the_sift.json
data/pysift/worldgen/biome/<biome>.json
data/pysift/worldgen/configured_feature/<feature>.json
data/pysift/worldgen/placed_feature/<feature>.json
data/pysift/tags/worldgen/biome/<tag>.json
```

需要 Java 時：`ResourceKey<Level>`、`ResourceKey<Biome>` 常數放 `world/ModDimensions.java`、`world/ModBiomes.java`，
在 `PySift.onInitialize` 中呼叫；生物生成限制用 `SpawnPlacements` / Fabric `BiomeModifications`。

## 3. 驗證

- JSON 語法：逐檔解析
- `./gradlew compileJava`（無法執行 → NOT ASSESSED）
- 遊戲內清單：`/execute in pysift:the_sift run tp @s 0 100 0`、F3 看生物群系名稱、地層方塊正確、生物會生成、
  log 中沒有 `Failed to parse` / `Unbound values in registry`
