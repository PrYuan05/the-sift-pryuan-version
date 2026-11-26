<p align="center">
  <img src="https://cdn.modrinth.com/data/kXuR56K2/images/6e06c295629e493d7470e36acc1747119abbbe9a.png" alt="The Sift — PrYuan's Version" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Minecraft-26.3-2EB8A6?style=for-the-badge&logo=minecraft&logoColor=white" alt="Minecraft 26.3" />
  <img src="https://img.shields.io/badge/Loader-Fabric_0.19.5%2B-E8A33A?style=for-the-badge" alt="Fabric" />
  <img src="https://img.shields.io/badge/Java-25%2B-D9536E?style=for-the-badge" alt="Java 25+" />
  <img src="https://img.shields.io/badge/Inspired_by-Minecraft_Dungeons_2-3A2E48?style=for-the-badge" alt="Inspired by Minecraft Dungeons 2" />
  <img src="https://img.shields.io/badge/Biomes-10-8EC5F0?style=for-the-badge" alt="10 Biomes" />
  <img src="https://img.shields.io/badge/Mobs-33%2B_%7C_36_Climate_Variants-B39DDB?style=for-the-badge" alt="33+ Mobs" />
</p>

# The Sift — PrYuan's Version（隙浮）

**An unofficial fan-made Fabric dimension mod for Minecraft 26.3, inspired by *Minecraft Dungeons 2*: 10 handcrafted biomes, 33+ animated creatures with climate variants, 3 multi-phase bosses, 10 Sift enchantments, and Soulite gear beyond netherite.**

> **Inspiration & Custom Assets Note:** All in-mod mob textures (33 base mobs, 36 climate variants, 12 emissive glowmasks), model redesigns, and Singer/Mourner vocal files are custom-made, re-shaded, or DSP-synthesized specifically for this mod rather than extracted from official game files. Free CC0/Pixabay ambient layers used in select sound effects are credited in [CREDITS.md](src/main/resources/assets/pysift/sounds/CREDITS.md).

[繁體中文說明在下方](#繁體中文)

---

## ✨ Features at a Glance

| Feature | Highlights |
| :-- | :-- |
| 🌌 **10 Biomes & Landmarks** | 6 surface biomes (*Willow Grove*, *Crimson Strata Canyon*, *Violet Slate Abyss*, *Amber Dunes*, *Soul Caldera*, *Lullaby Hills*) + 4 underground layers (*Red Zone Caves*, *Withered Hollows*, *Resonant Vaults*, *Spirit Deeps*), plus *The Echo Den*, *Humbler Husks*, *Lullaby Hilltop Shrines*, ruins, and Soul Crystal geodes |
| 🐾 **33+ Animated Creatures** | Custom 6-step pixel-art shading, **12 climate-variant mobs × 3 climates (Normal / Tropical / Cold = 36 variants)**, **12 emissive glowmasks**, and **3 multi-phase bosses** (*Harmonizer*, *Monarch*, *Sculk Monstrosity*) |
| 🐑 **Nuzzle & 9 Sift Colors** | Shearable **Nuzzles** dyeable with all **16 vanilla dyes + 9 custom Sift dyes** (*Teal, Mint, Coral, Amber, Lavender, Rose, Soul Blue, Void, Dusk Gold*), adapting to Normal, Tropical (blooming flowers), and Cold (frosty winter fleece) climates |
| 🎵 **Singers & Mourners** | Interactive 8-disc Ancient City portal ritual, *Tuning Fork* choir harmonies, *Mourning Horn*, *Lullaby Censer*, and custom DSP-synthesized multi-register vocals (`B3 / F#4 / C#5`) |
| ⚔️ **Gear & Enchantments** | Siftite → boss weapons (*Sculk Hammer*, *Sonic Staff*, *Dash Charm*) → Sift Beacon → **Soulite** gear, **10 custom Sift enchantments**, and in-hand weapon physics (compatible with *Punchy!* / *Punchy! Moves*) |
| 🧭 **Helpers & Building** | **Sift Codex** (Modonomicon interactive guidebook & bestiary), Soul Compass, Homeward Stone, Soul Power machines, tameable Blubs, and **450+ blocks** |

---

## 🛠️ Building from Source

### Prerequisites
- **Java 25+** (e.g. Microsoft OpenJDK 25 or Eclipse Temurin 25)
- **Git**
- *(Optional, for regenerating procedural textures/audio)* **Python 3.10+** with `numpy`, `scipy`, `soundfile`, `pillow`

### Clone & Build
```bash
git clone https://github.com/PrYuan05/the-sift-pryuan-version.git
cd the-sift-pryuan-version

# Build the mod JAR (output: build/libs/pysift-<version>.jar)
./gradlew build        # macOS / Linux
.\gradlew.bat build    # Windows

# Launch the development Minecraft client
./gradlew runClient
```

> **Tip:** If your system's default `JAVA_HOME` is not Java 25+, set `org.gradle.java.home=/path/to/jdk-25` in your **user-level** `~/.gradle/gradle.properties` (do not commit local paths into the repository's `gradle.properties`).

### Project Structure
```text
src/
  main/java/pryuan05/pysift/    # Gameplay, entities, biomes, items, enchantments, soul power
  client/java/pryuan05/pysift/  # Renderers, glowmasks, particles, weapon animations
  main/resources/               # GeckoLib models, textures, sounds, worldgen, loot, recipes, lang
tools/
  audio/                        # Procedural DSP audio & Singer/Mourner vocal engine
  texture_pipeline/             # 6-step mob shading, climate variants, glowmasks, UV verifier
  worldgen/                     # The Sift dimension & biome spawn sync scripts
  entity/                       # Entity geometry & animation generators
docs/                           # Compatibility notes & Modrinth release docs
```

### Runtime Dependencies
- **Minecraft:** `26.3`
- **Fabric Loader:** `0.19.5+`
- **Required Mods:** [Fabric API](https://modrinth.com/mod/fabric-api), [GeckoLib](https://modrinth.com/mod/geckolib) `5.5.7+`, [Modonomicon](https://modrinth.com/mod/modonomicon) `2.20.0+`

---

## 📄 License & Credits
- Source code license: see [LICENSE](LICENSE).
- Audio credits & CC0/Pixabay attributions: see [src/main/resources/assets/pysift/sounds/CREDITS.md](src/main/resources/assets/pysift/sounds/CREDITS.md).
- Full version history: see [CHANGELOG.md](CHANGELOG.md).

---

<a id="繁體中文"></a>
## 📖 繁體中文簡介

**The Sift — PrYuan's Version（隙浮）** 是一款**參考自 *Minecraft Dungeons 2*** 世界觀與生物設定的非官方二創大型維度模組（適用 **Minecraft 26.3 / Fabric**）。

* 🌌 **10 大地表與地底生態域**：包含柳林、緋紅岩層峽谷、紫岩深淵、琥珀沙丘、靈魂火山口、搖籃曲丘陵與 4 大地底層，以及**迴音殿堂**、巨型骸骨與靈魂晶洞等地標。
* 🐾 **33+ 隻全動畫生物與 3 大多階段 Boss**：12 種生物具備**普通／熱帶／寒帶**三氣候專屬變體（共 36 種）、12 組夜光貼圖（Glowmask），以及**調和者**、**君王**與**幽匿巨怪**三大 Boss。
* 🐑 **蹭蹭怪（Nuzzle）25 色氣候適應染色**：支援全部 **16 種原版染料＋9 種隙浮專屬染料**，並依氣候保留熱帶扶桑花或呈現寒帶厚冬毛冰霜色澤。
* ⚔️ **完整裝備進度與 10 種隙浮附魔**：從**隙浮金**、三大 Boss 武器一路進階至**靈髓（Soulite）**裝備，附帶 450+ 建築方塊、靈魂動力機器與內建互動式**隙浮手記（Sift Codex）**。

### 從原始碼建置
1. 安裝 **Java 25+** 並執行 `git clone https://github.com/PrYuan05/the-sift-pryuan-version.git`。
2. 在專案根目錄執行 `.\gradlew.bat build`（Windows）或 `./gradlew build`（macOS / Linux），編譯完成的 `.jar` 會輸出於 `build/libs/`。
3. 開發測試可直接執行 `.\gradlew.bat runClient`。
