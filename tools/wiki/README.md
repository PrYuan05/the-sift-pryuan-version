# 隙浮 Wiki 產生器

輸出在 `docs/wiki/`，中英雙語，右上角可以切換語言：
- `index.html` 加上 `data.zh.js`、`data.en.js`，可以直接開檔，也是 GitHub Pages 發布的版本。
- `claude_page.html` 加上 `data.zh.json`、`data.en.json`，是發布到 claude.ai 用的版本。

**英文版**：
- 名稱、數值、手記原文直接讀 `en_us.json`。
- 手寫說明在 `content/en/*.md`，分段 ID 和中文版相同。
- 產生器寫出的中文介面字（標題、欄位名）由 `content/en/ui.tsv` 翻譯。如果還有沒翻到的，清單會寫在 `build/wiki_en_untranslated.txt`。

**部署**：`.github/workflows/wiki-pages.yml` 會在 main 分支的 `docs/wiki` 有變動時，自動發布到 GitHub Pages。第一次使用前，要到倉庫的 Settings > Pages 把 Source 設成 GitHub Actions。

## 重新產生
    python -I tools/wiki/build_wiki.py      # 讀模組資料與 content/*.md，重畫圖示圖集，寫出網站
    node tools/wiki/serve.js                # 本機預覽 http://127.0.0.1:8765

| 檔案 | 內容 |
|---|---|
| `build_wiki.py` | 讀取語系、配方、標籤、掉落表、生態域、結構、生物屬性 |
| `render_icons.py` | 從方塊與物品模型畫出等角圖示，輸出 `img/icons.png` |
| `crop_shots.py` | 裁切遊戲內截圖，輸出 `img/mobs/`、`img/shots/` |
| `content/*.md` | 手寫說明，用 `=== 種類:ID｜標題` 分段，內文用 `[[pysift:物品]]`、`[[mob:id]]`、`[[page:id]]` 連結 |
| `data/creative_tabs.txt` | 從遊戲匯出的創造模式分頁內容 |
| `site/` | 網站外殼：版面、搜尋、合成格 |

**不收錄的物品**：只出現在「未使用方塊」分頁、而且玩家無法取得的方塊。判斷依據是：
- 不會自然生成；
- 不會從生物身上掉落；
- 不會出現在箱子裡；
- 不能用拿得到的材料合成出來。

## 重拍遊戲內截圖
截圖用臨時的 client game test 拍，拍完要移除，不要 commit。步驟如下：
1. 把 `fabricApi { configureTests { ... enableClientGameTests.set(true) } }` 加進 `build.gradle`。
2. 把 `gametest/WikiShots.java.txt` 複製成 `src/gametest/java/pryuan05/pysift/test/WikiShots.java`。
3. 新增 `src/gametest/resources/fabric.mod.json`，把 entrypoint 設為 `fabric-client-gametest: pryuan05.pysift.test.WikiShots`。
4. 執行 `./gradlew runClientGameTest`。
   - 可以用 `WIKI_ONLY=mobs,biomes,structures,arenas` 只拍其中幾類。
   - 可以用 `WIKI_MOBS=id,...` 只重拍某幾隻生物。
5. 把 `build/run/clientGameTest/screenshots/*.png` 複製到 `build/wikishots/`，執行 `python -I tools/wiki/crop_shots.py`。
6. 測試也會寫出 `build/run/clientGameTest/wiki_tabs.txt`。把它複製到 `tools/wiki/data/creative_tabs.txt`，用來更新「不收錄的物品」名單。
7. 刪掉步驟 1 加的設定和步驟 2、3 建立的檔案，把 `build.gradle` 還原。
