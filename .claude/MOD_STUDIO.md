# pysift Mod Studio（Claude Code 技能包）

把 [Donchitos/claude-code-game-studios](https://github.com/Donchitos/claude-code-game-studios)
(MIT, Copyright (c) 2026 Donchitos) 的工作室流程改寫成 **Fabric 26.3 / Mojang 映射 / pysift**
專用版本。原套件的技能是寫給網頁遊戲、Godot、Unity、Unreal 用的，而且依賴它自己的
`project.yaml`、`yaml-helper.sh` 與 hooks，所以這裡沒有整包複製，而是保留它的做法並改寫：

- **協作，不擅自行動**：每個階段先提案，使用者用 `AskUserQuestion` 選擇後才寫檔。
- **小規格先行**：`/mc-quick-design` 對應原版 `/quick-design`，規格寫在 `design/specs/`。
- **團隊編排**：`/mc-team-mob` 對應原版 `/team-combat`，依序叫設計、程式、動畫、QA 代理。
- **誠實回報**：檢查不能執行時回報「NOT ASSESSED」，不要回報通過（沿用原版 code-review 的規則）。

所有技能都以根目錄 `CLAUDE.md` 為最高規範（版本、映射、命名、必備檔案清單）。

## 技能（輸入 `/名稱` 使用）

| 技能 | 對應原版 | 用途 |
| :-- | :-- | :-- |
| `/mc-start` | start, help, next-step, project-stage-detect | 讀進度表與 git 狀態，建議下一步 |
| `/mc-brainstorm` | brainstorm | 發想符合 The Sift 世界觀的生物、方塊、物品、生物群系 |
| `/mc-quick-design` | quick-design, design-system | 寫一頁規格（數值、行為、資源清單、驗收條件） |
| `/mc-add-block` | dev-story（方塊） | 依 7 項必備檔案清單新增方塊 |
| `/mc-add-item` | dev-story（物品） | 新增物品／材料，含現代物品定義 |
| `/mc-add-mob` | dev-story（生物） | 新增 GeckoLib 5 生物、生怪蛋、渲染器 |
| `/mc-team-mob` | team-combat | 生物 AI／技能／動畫的完整團隊流程 |
| `/mc-worldgen` | team-level, world-builder | 維度、dimension_type、生物群系、地物 JSON |
| `/mc-asset-audit` | asset-audit, consistency-check, content-audit | 資源一致性、命名空間、缺漏檔案檢查（只讀） |
| `/mc-code-review` | code-review | Mojang 映射、`.setId`、客戶端／伺服器分離檢查 |
| `/mc-crash-debug` | bug-report, hotfix | 分析崩潰日誌與 `latest.log`，找原因並修正 |
| `/mc-smoke-check` | smoke-check, regression-suite | compileJava → build → verify.py → 遊戲內檢查清單 |
| `/mc-localize` | localize | `en_us.json` / `zh_tw.json` 鍵值同步 |
| `/mc-release` | release-checklist, patch-notes, changelog | fabric.mod.json、版本號、變更紀錄、上架檢查 |

## 代理（`.claude/agents/`，由技能呼叫，也可直接指派）

| 代理 | 對應原版 |
| :-- | :-- |
| `fabric-programmer` | gameplay-programmer, engine-programmer, lead-programmer |
| `mob-ai-designer` | ai-programmer, game-designer, systems-designer |
| `geckolib-animator` | technical-artist（實體） |
| `texture-artist` | art-director, technical-artist（方塊） |
| `worldgen-designer` | world-builder, level-designer |
| `mod-qa-tester` | qa-lead, qa-tester |

## 沒有改寫的部分

上架商店認證（console cert）、即時營運（live-ops）、網頁原型（`/prototype`）、Godot／Unity／Unreal
專家、衝刺與史詩管理（sprint / epics / stories）、原套件的 hooks 與狀態列。需要時可從原 repo 單獨移植。

## 和 `/minecraft-mod-builder` 的關係

`/minecraft-mod-builder` 不在這個 repo 裡（在你電腦上的 Claude Code 設定中）。如果想把它的內容合併進來，
把它的 `SKILL.md` 放到 `.claude/skills/minecraft-mod-builder/`，再請 Claude 比對 `/mc-add-*` 技能並合併。
