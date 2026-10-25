# art_requests：美術需求總目錄

需要畫、或可以在遊戲裡改的東西都在這個資料夾。最後整理：2026-10-26。

| 文件 | 內容 | 狀態 |
| :-- | :-- | :-- |
| `new_content_todo.md` | 最近新增的內容：9 種新顏色的染料圖示與彩繪陶瓦、地標建築草稿、Blub 的攻擊與趴下動畫 | 待畫 |
| `vegetation_todo.md` | A. 植被總表（每種植物的模型、貼圖、來源、狀態）；B. 全專案 AI／腳本產生、還沒換成正式美術的貼圖 | 進行中，腳本自動產生 |
| `projectiles/README.md` | 5 種投擲物的重繪規格（附底稿 `drafts/` 與總覽 `sheet.png`） | 待畫 |
| `structures_edit_guide.md` | 在遊戲裡修改所有建築（Boss 競技場、遺跡、到達傳送門、迴音穴、地標）並匯回模組的步驟 | 說明文件 |
| `spawn_eggs_preview.png` | 生怪蛋總覽 | 參考圖 |
| `_archive/` | 已經完成的舊清單（第 1 階段道具、方塊、盔甲貼圖：全部已換成正式美術） | 封存 |

## 更新方式

- `vegetation_todo.md` 與兩張總覽圖（`vegetation_todo_overview.png`、`ai_textures_overview.png`）由
  `python -I tools/build_art_requests.py` 產生，**不要手改**，植物或貼圖有變動後重跑即可。
- 新顏色的貼圖畫好後跑 `python -I tools/progression/build_sift_colors.py .`，有畫的會自動改用你的圖。
- 腳本產生的臨時圖都有保護：只要你用同檔名覆蓋成自己的圖，腳本重跑不會蓋回去。
