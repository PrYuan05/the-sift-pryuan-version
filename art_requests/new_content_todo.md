# 新內容的美術待辦（2026-10-26）

最近加進模組、目前用**程式畫的草稿或原版貼圖著色**頂著的東西。都能正常玩，換成你的美術會更好看。
每一項都寫了「現在是什麼」「要畫什麼」「畫好放哪裡」。

---

## 一、9 種新顏色（染料圖示、彩繪陶瓦）

現在每個顏色的方塊與染料，都是**原版白色版本的貼圖乘上顏色**（不複製原版貼圖）。羊毛、混凝土、玻璃這類單色方塊這樣就很自然；
最需要專屬美術的是**染料圖示**和**彩繪陶瓦的圖案**（現在是原版白色彩繪陶瓦的花紋染色）。

| 顏色 | 色碼 | 來源植物（配色參考） |
| :-- | :-- | :-- |
| 青碧 teal | `#2EB8A6` | 柔和青碧草、劈裂草 |
| 薄荷 mint | `#8FE3C0` | 裂隙薄荷草、夜光草 |
| 珊瑚 coral | `#F08A6C` | 珊瑚落葉、甲殼短草 |
| 琥珀 amber | `#E8A33A` | 裂隙橙草、橙隙浮藤 |
| 薰衣草 lavender | `#B39DDB` | 柔和紫晶草、粉捲蕨 |
| 赤紅玫瑰 rose | `#D9536E` | 甲殼花、柔和赤紅草 |
| 靈魂藍 soul_blue | `#8EC5F0` | 靈魂劈裂草、靈魂柳葉 |
| 虛黑 void | `#3A2E48` | 幽光菇 |
| 暮光金 dusk_gold | `#F2CF6B` | 暮綻花、黃龍舌蘭 |

### 要畫的（優先）

| 項目 | 數量 | 尺寸 | 檔案（`<顏色>` 換成上表英文 ID） |
| :-- | :-- | :-- | :-- |
| 染料圖示 | 9 | 16x16，透明背景 | `src/main/resources/assets/pysift/textures/item/<顏色>_dye.png` |
| 彩繪陶瓦圖案 | 9 | 16x16 | `src/main/resources/assets/pysift/textures/block/sift_colors/<顏色>_glazed_terracotta.png` |

- 彩繪陶瓦放在地上會依方向旋轉，四塊拼起來會組成一個大圖案（跟原版一樣），畫的時候可以考慮四塊拼接的效果。
- 染料可以畫成那個顏色的植物做成的樣子（例如虛黑是幽光菇粉末、薰衣草是紫晶草葉片），跟原版的染料球區分。

### 可以畫（選擇性）

同一個資料夾放 `<顏色>_<種類>.png` 就會取代著色版本：`wool`、`concrete`、`concrete_powder`、`terracotta`、`stained_glass`
（玻璃片另外要 `<顏色>_stained_glass_pane_top.png`）。羊毛的半磚、階梯、地毯會自動跟著羊毛的圖；混凝土的半磚、階梯跟著混凝土。

### 畫好之後

在專案根目錄跑：

```bash
python -I tools/progression/build_sift_colors.py .
```

有畫的會自動改用你的圖（而且不再染色），沒畫的維持著色版本。請**不要拿原版貼圖來改**，這樣成品才能跟模組一起發布。

---

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
