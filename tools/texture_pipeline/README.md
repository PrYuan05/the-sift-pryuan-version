# Texture pipeline (pysift)

方塊貼圖的檢查與整理工具。所有指令都在專案根目錄執行，並加上 `-I`（避免載入其他目錄的模組）。

| 工具 | 用途 | 會不會改檔 |
| :-- | :-- | :-- |
| `verify.py` | 檢查 Java 方塊表、blockstate、模型、貼圖、物品、掉落表、標籤、語言檔是否一致，並檢查隨機池色系一致性與 PNG 來源 | 只讀，有錯誤時 exit 1 |
| `recolor.py scan [--threshold N]` | 找出色系不一致（調色盤距離 > N，預設 9）的隨機池或階段，選出參考貼圖，產生改色預覽 | 只寫 `build/texture_pipeline/out/` |
| `recolor.py apply [block[:state] ...]` | 依 `recolor_plan.json` 改色，先備份再記錄到 manifest | 改 PNG |
| `recolor.py revert <block[:state]\|all>` | 從備份還原，並移除 manifest 記錄 | 改 PNG |
| `tone_groups.py`、`directional_scan.py` | 色調分群、帶狀貼圖偵測（產生對照圖與提案） | 只寫 `<out_dir>` |

## 統一色調流程

```powershell
python -I tools/texture_pipeline/recolor.py . scan
# 看 build/texture_pipeline/out/recolor_review.png：★ 是參考貼圖，紅框是預設跳過（被其他方塊共用）
# 需要調整就改 recolor_overrides.json，再 scan 一次
python -I tools/texture_pipeline/recolor.py . apply            # 或只套用某個池：apply magma_vein_slate:vein=1
python -I tools/texture_pipeline/verify.py .
```

改色方式（palette 模式）：把貼圖的亮度範圍拉到參考貼圖的亮度範圍，每個像素換成參考調色盤中亮度最接近的顏色。只換顏色、不改形狀，透明像素保留。

## 檔案

- `recolor_overrides.json`：使用者的決定。可設定 `exclude`（不處理的池）、`reference`（指定參考貼圖，取代自動選的 medoid）、`skip_targets`（某個池中保持原樣的貼圖）、`allow_shared`（允許改被其他方塊共用的貼圖）。鍵為 `block` 或 `block:state`。
- `recolor_manifest.json`：每張被流程改過的 PNG，記錄改前與改後的 sha1、參考貼圖和備份位置。`verify.py` 依此區分「流程改的」和「外部改的」。
- `texture_baseline.json`：原始貼圖的指紋，包含 plan (c) 的檔案雜湊與原始圖集的像素雜湊。
- `palette_lib.py`：共用函式（CIELAB、調色盤距離、Tex）。
- `history/`：一次性的整合腳本（295→93、帶狀方塊、第二輪回饋），留作紀錄，不要再執行。
- 備份放在專案根目錄的 `.texture_backups/`（已加入 .gitignore）。**不要放在 `build/`，`gradlew clean` 會刪掉。**
