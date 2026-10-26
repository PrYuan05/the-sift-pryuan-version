## 二、地標建築（程式畫的草稿）

迴音穴（9 個拼接零件）、迅從者殘骸、搖籃曲山丘神殿、4 種小化石，外型都是程式蓋的草稿。
修改方式（在遊戲裡直接改、存檔、匯回）見 **`structures_edit_guide.md`**，用 `/pysift_showcase echo_den` 這類關鍵字只排出要改的那幾個。

---

## 三、動畫草稿（Blub）

| 動畫 | 名稱 | 現在的樣子 |
| :-- | :-- | :-- |
| 攻擊 | `animation.blub.attack` | 0.55 秒：往後縮蓄力 → 撲上去 → 身體前端往下一咬；耳朵、四腳、尾巴／鰭跟著甩 |
| 趴下（坐下） | `animation.blub.sit` | 3 秒循環：肚子貼地、前腳往前伸、後腳往後伸、耳朵下垂、慢慢呼吸 |

- 檔案：`src/main/resources/assets/pysift/geckolib/animations/entity/` 底下的 `blub.animation.json`、`blub_carapace`、`blub_fungal`、`blub_meadows`、`blub_ravines`（五種變體各一份，骨架略有不同）。
- 用 Blockbench（GeckoLib 外掛）打開對應的 `.geo.json` 模型來修。**動畫名稱不要改**，程式是用名稱播放的。
- 舊的原檔備份在 `.texture_backups/blub_anim/`。

---

## 其他還在進行中的清單

- **植被與 AI 產生的貼圖**：`vegetation_todo.md`（`python -I tools/build_art_requests.py` 會重新整理）。
- **投擲物重繪**：`projectiles/README.md`。
