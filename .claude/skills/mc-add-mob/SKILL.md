---
name: mc-add-mob
description: "在 pysift 新增 GeckoLib 5 生物：實體類別、EntityType 註冊、屬性、生怪蛋、客戶端渲染器、geo 模型／動畫／貼圖、語系。使用者說「加一隻生物」、「新怪物」、「add mob」、「實體看不到／隱形」時使用。"
argument-hint: "<mob_id> [CREATURE|MONSTER] [寬 高]"
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(./gradlew*), Bash(git status*), AskUserQuestion, Agent
---

# 新增生物（mc-add-mob）

只做「生物能生成、能看見、會播 idle/walk」。AI 技能與戰鬥交給 `/mc-team-mob`。

## 0. 前置

- 讀 `design/specs/<id>.md`（若有）。
- 確認 Blockbench 匯出的檔案在位：`assets/pysift/geckolib/models/<id>.geo.json`、
  `assets/pysift/geckolib/animations/`（看現有生物實際放在哪一層，照同樣位置放）、
  `assets/pysift/textures/entity/<id>.png`。缺少的列出來請使用者提供，**不要捏造骨架或動畫**。
- 動畫名稱必須是 `animation.<id>.idle`、`animation.<id>.walk`（`PysiftGeoEntity` 依此命名找動畫）。
  打開 `.animation.json` 確認。

## 1. 實體類別 `entity/mob/<Name>Entity.java`

繼承 `PysiftGeoEntity`（參考 `BlubEntity.java`）：
- 建構子 `(EntityType<? extends PathfinderMob>, Level)`
- `registerGoals()`：至少 `FloatGoal`、`WaterAvoidingRandomStrollGoal`、`LookAtPlayerGoal`、`RandomLookAroundGoal`
- `public static AttributeSupplier.Builder createAttributes()`：`MAX_HEALTH`、`MOVEMENT_SPEED`；敵對加 `ATTACK_DAMAGE`、`FOLLOW_RANGE`
- 伺服器邏輯用 `if (!this.level().isClientSide())` 包住

## 2. 註冊

1. `entity/ModEntities.java`：`register("<id>", <Name>Entity::new, MobCategory.X, w, h)`（內部已用 ResourceKey `.build(key)`），
   並在屬性註冊處加 `FabricDefaultAttributeRegistry.register(<ID>, <Name>Entity.createAttributes())`。
2. `item/ModItems.java`：`registerSpawnEgg("<id>_spawn_egg", ModEntities.<ID>)`，並加入 `SPAWN_EGGS` 陣列。
3. 生怪蛋資源：`assets/pysift/items/<id>_spawn_egg.json` 與模型（照現有生怪蛋檔案）。
4. `src/client/java/pryuan05/pysift/PySiftClient.java`：
   `EntityRendererRegistry.register(ModEntities.<ID>, context -> new PysiftUniversalGeoRenderer<>(context, "<id>"));`
   客戶端類別只能放在 `src/client/`，不可從 main 引用。
5. 語系：`entity.pysift.<id>`、`item.pysift.<id>_spawn_egg`（en_us + zh_tw）。
6. 掉落（若有）：`data/pysift/loot_table/entities/<id>.json`。

## 3. 驗證

`./gradlew compileJava`（無法執行 → NOT ASSESSED）。遊戲內清單：生怪蛋在分頁、生成後看得到（非隱形、非粉紅方塊）、
碰撞箱大小符合模型（F3+B）、會播 idle 與 walk、名稱正確。
隱形或貼圖錯誤時，到 `latest.log` 搜尋 `geckolib` 與 `<id>`，通常是檔案路徑或動畫名稱不符。
