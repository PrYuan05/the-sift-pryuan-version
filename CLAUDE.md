# The Sift (pysift) — Claude Code 作業規範

完整規範與進度表見 `MODDING_ROADMAP_AND_SPECS.md`。本檔為每次作業都必須遵守的精簡版。

## 環境（不可擅自更改版本）
- Minecraft `26.3`、Java `25`（JDK：`C:/Users/hoeyl/.jdks/ms-25.0.4.1`，已寫在 `gradle.properties`）
- Fabric Loader `0.19.5`、Fabric Loom `1.18.4`（固定版本，`settings.gradle` 直接載入 `net.fabricmc:fabric-loom` 模組；不要改回 `1.18-SNAPSHOT`，這台電腦的 HTTPS 被攔截，SNAPSHOT 每次都要上網檢查而失敗）、fabric-api `0.162.0+26.3`
- GeckoLib 5：`com.geckolib:geckolib-fabric-26.3:5.5.7`

## 映射：只用 Mojang 官方映射，禁止 Yarn 命名
| 使用 (Mojang) | 禁止 (Yarn) |
| :--- | :--- |
| `BlockBehaviour.Properties` | `AbstractBlock.Settings` |
| `SoundType` | `BlockSoundGroup` |
| `RotatedPillarBlock` | `PillarBlock` |
| `BuiltInRegistries`（註冊表實例） | Yarn 的 `Registries` |
| `Registries`（註冊表鍵，如 `Registries.BLOCK`） | `RegistryKeys` |
| `ResourceKey` | `RegistryKey` |
| `Identifier`（`PySift.id(path)`） | `new Identifier(ns, path)` |

## 命名
- Mod ID 一律 `pysift`；禁止使用 `sift`、`custom` 作為命名空間（資源 JSON 內的 `"sift:..."` 也不行）
- Java 根套件 `pryuan05.pysift`；主類別 `PySift`（`ModInitializer`）、客戶端 `PySiftClient`（`ClientModInitializer`）
- 資源：`src/main/resources/assets/pysift/`；資料：`src/main/resources/data/pysift/`；原版標籤：`data/minecraft/tags/block/mineable/`

## 註冊（26.3 必須）
方塊與物品都要用 `.setId(key)` 綁定 ResourceKey，否則執行時會崩潰（`Identifier not set`）。
沿用 `block/ModBlocks.java` 的 `register()` / `registerPillar()`，新方塊會自動加入 `ALL_BLOCKS` 與創造模式分頁。
```java
ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, PySift.id(name));
Block block = new Block(properties.setId(blockKey));
Registry.register(BuiltInRegistries.BLOCK, blockKey, block);
```

## 新增方塊的必備檔案清單
1. `assets/pysift/blockstates/<name>.json`
2. `assets/pysift/models/block/<name>.json`、`models/item/<name>.json`
3. `assets/pysift/items/<name>.json`（現代物品定義，缺少會在物品欄顯示紫黑方塊）：
   `{"model":{"type":"minecraft:model","model":"pysift:item/<name>"}}`
4. `data/pysift/loot_table/blocks/<name>.json`（並保留複數 `loot_tables/blocks/` 相容）
5. `data/minecraft/tags/block/mineable/<tool>.json` 加入方塊 ID
   - **實心方塊還要加進 `#minecraft:blocks_motion_no_leaves`**（26.3 的 heightmap 只看這個標籤）。漏掉的話，樹木、地表生成、生物生成都會把這些方塊當成空氣，例如樹會被放到世界底部然後靜默失敗。`tools/worldgen/build_vegetation.py` 會自動把所有非植物、非流體、非 slab/stairs/wall 的 pysift 方塊加進去，新增方塊後重跑一次即可。
6. `assets/pysift/lang/` 語系檔
7. Java 註冊（`ModBlocks.java`）

## 程式結構
- `PySift.java`：主入口，註冊狀態效果、靈魂灼燒、方塊、流體、植被、靈柳木組、靈魂晶塊、粒子、世界生成特徵、實體、物品與傳送門儀式
- `block/`：`ModBlocks`（核心方塊與 38 組建材組、`SIFT_PORTAL`）、`ModVegetation`（植被）、`SoulWillowWood`（靈柳木建材組）、`SoulCrystal`、`SiftPortalBlock`、`SiftPortalRitual`
- `fluid/` & `effect/`：`ModFluids`（靈液 `spirit_liquid`）、`ModEffects`（靈魂剝奪 `soul_deprivation`）、`SoulBurn`（血量抽離、靈魂碎裂與解藥機制）
- `worldgen/`：`SoulWillowTrunkPlacer`、`SoulWillowFoliagePlacer`、`SoulWillowVineDecorator`、`StrataSpireFeature`、`BossArenaFeature`（維度與 4 個生態系 JSON 由 `tools/worldgen/build_the_sift.py` 產生）
- `item/ModItems.java`：核心材料、靈魂解藥、24 款生怪蛋、三個創造模式分頁（`pysift_blocks`、`pysift_unused_blocks`、`pysift_items`）
- `entity/`：`ModEntities`、`BossMechanics`、`ai/`（11 個技能與戰術 Goal）、`projectile/`（飛鏢、投石）、`mob/`（24 款生物，共 25 個類別含 `PysiftSwarmEntity`）
- `src/client/java/pryuan05/pysift/`：`PySiftClient`、`client/`（`PysiftUniversalGeoModel`、`PysiftUniversalGeoRenderer`、`SlabberRenderer`、`SiftPortalBlockEntityRenderer`、`SiftPortalTransition`、`SoulDeprivationVision` 等）
- 生物資源：`assets/pysift/geckolib/models/entity/`、`assets/pysift/geckolib/animations/entity/`、`assets/pysift/textures/entity/`

## 驗證（每次修改後至少跑 compileJava）
```powershell
.\gradlew.bat compileJava          # 快速檢查
.\gradlew.bat build -x test        # 完整建置
.\gradlew.bat runClient            # 遊戲內測試
python -I tools/texture_pipeline/verify.py .               # 方塊資源與色系一致性檢查（exit 1 = 有錯）
```

## 貼圖流程（詳見 `tools/texture_pipeline/README.md`）
- 改貼圖色調一律走 `recolor.py scan → 使用者看 recolor_review.png 確認 → apply`；手動改 PNG 後，`verify.py` 會把它列為「外部改的」。
- 使用者的決定（排除的池、指定參考貼圖、可改的共用貼圖）記在 `recolor_overrides.json`，不要寫死在程式裡。
- 備份放 `.texture_backups/`，不要放 `build/`（`gradlew clean` 會清掉）。
- 翻轉、旋轉只在模型 UV 處理（`models/block/templates/`），不要產生翻轉過的 PNG。

## 協作規則
- 使用者同時使用 Antigravity、IntelliJ IDEA 與 Claude Code：不要和其他 AI 同時改同一個檔案；大量修改資源前先 commit，方便還原。
- `sift_visual_corrected/` 是交付候選資源，命名空間仍為 `sift`，整合進主程式時必須全部改寫為 `pysift`。
- 未經使用者同意，不要 commit、push 或刪除 `sift_visual_corrected/` 與 `.zip` 檔。
- 回覆使用者時使用繁體中文。
