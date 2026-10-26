# 新內容的美術待辦（2026-10-26）

最近加進模組、目前用**程式畫的草稿或原版貼圖著色**頂著的東西。都能正常玩，換成你的美術會更好看。
每一項都寫了「現在是什麼」「要畫什麼」「畫好放哪裡」。

---

## 一、9 種新顏色 ✅ 已完成

- **染料圖示**與**彩繪陶瓦**：你畫的 18 張（`textures/item/<顏色>_dye.png`、`textures/block/sift_colors/<顏色>_glazed_terracotta.png`）。
- **其他方塊**（羊毛、混凝土、混凝土粉末、陶土、染色玻璃、玻璃片頂面；半磚、階梯、地毯跟著羊毛與混凝土）：
  由 `tools/progression/paint_sift_colors.py` 依你畫的染料色盤上色（下方的棕色盤子不算），保留原版的明暗結構；
  羊毛、粉末、玻璃直接用染料上的顏色，混凝土和陶土是啞光材質，用色盤那一段的幾個相近色階。

### 之後要改顏色

改某個顏色的染料圖，再跑下面兩行，那個顏色的所有方塊會跟著重新上色：

```bash
python -I tools/progression/paint_sift_colors.py . --preview
python -I tools/progression/build_sift_colors.py .
```

`--preview` 會產生對照圖 `build/previews/sift_colors_painted.png`。也可以直接畫 `textures/block/sift_colors/<顏色>_<種類>.png`
覆蓋單一方塊（之後重跑 paint_sift_colors.py 會蓋掉，記得先備份）。

### 床、旗幟、坐墊（2026-10-26 新增）

- **床**：`textures/block/sift_colors/<顏色>_bed_{foot,head}_<面>.png`，**坐墊**：`<顏色>_item_cushion.png`（物品）與
  `textures/entity/cushion/<顏色>_cushion.png`（實體），都由 `paint_sift_colors.py` 依染料色盤上色，只改布料（原版白床與紅床不同的像素），
  木框和枕頭保留原版。想重畫只要直接覆蓋那些 PNG（要重新產生用 `--only bed_,item_cushion,entity_cushion`，不會動到其他已上色的方塊）。
- **旗幟**：不需要貼圖，用原版白色旗幟底圖、在客戶端換成染料的代表色（`SiftColors.SiftColor` 的 RGB）。
  已知限制：旗幟套到盾牌上、或地圖上的旗幟標記，底色會是白色（原版只認 16 色）。

| 顏色 | ID | 來源植物 |
| :-- | :-- | :-- |
| 青碧 | `teal` | 柔和青碧草、劈裂草 |
| 薄荷 | `mint` | 裂隙薄荷草、夜光草 |
| 珊瑚 | `coral` | 珊瑚落葉、甲殼短草 |
| 琥珀 | `amber` | 裂隙橙草、橙隙浮藤 |
| 薰衣草 | `lavender` | 柔和紫晶草、粉捲蕨 |
| 赤紅玫瑰 | `rose` | 甲殼花、柔和赤紅草 |
| 靈魂藍 | `soul_blue` | 靈魂劈裂草、靈魂柳葉 |
| 虛黑 | `void` | 幽光菇 |
| 暮光金 | `dusk_gold` | 暮綻花、黃龍舌蘭 |
