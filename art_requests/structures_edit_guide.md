# 在遊戲裡修改建築

模組裡所有的建築（26 個結構檔）都可以在遊戲裡直接改，改完存檔再匯回模組。

## 步驟

1. **開一個創造模式的世界**（建議超平坦），站到一塊空地上。高度要夠：最大的 Boss 競技場是 47×30×47。
2. **排出要改的建築**：
   ```
   /pysift_showcase              全部 26 個
   /pysift_showcase boss_arena   只排 Boss 競技場（關鍵字比對名稱）
   /pysift_showcase portal       只排到達傳送門
   ```
   每個建築的左下角（往外一格、往下一格）會有一個已經設定好的**結構方塊**：名稱、範圍、模式都設好了，模式是「儲存」。
3. **動手改**。可以加、拆、換方塊。
4. **存檔**：對那個建築的結構方塊按右鍵，按「儲存」。檔案會存到世界資料夾的 `generated/pysift/structure/`。
5. **匯回模組**（在專案根目錄執行）：
   ```
   python -I tools/worldgen/import_structures.py "run/saves/<世界名稱>"
   ```
   可以在最後加關鍵字，只匯入某幾個，例如 `boss_arena`。
   匯入的檔案會記在 `tools/worldgen/art/edited_structures.json`。之後重跑任何產生腳本，都**不會**蓋掉你改過的建築。

## 結構空位（重要）

排出來的建築範圍內，原本沒有方塊的位置會鋪滿**結構空位**（structure void，看不見，拿著它或開結構方塊的範圍框才看得到）。

- **結構空位** = 存檔時略過 = 世界生成時**不動原本的地形**。
- **空氣** = 世界生成時會**清空**那一格（例如競技場上方的空間、坑洞）。
- 想讓某格「保持原本的地形」，就放一個結構空位；想清出空間，就打掉方塊留空氣。
- 不要改結構方塊的範圍大小。Boss 競技場的中心和地面高度是照固定的尺寸對齊的。

## 有哪些建築

| 類別 | 結構檔 | 用在哪裡 |
| :-- | :-- | :-- |
| Boss 競技場 | `boss_arena/monarch`、`boss_arena/harmonizer`、`boss_arena/sculk_monstrosity` | 琥珀沙丘、柳絮林地、紫晶深板岩區的 Boss 神殿 |
| 遺跡 | `strata_shrine`、`abyss_obelisk`、`willow_hut`、`dune_tomb` | 各生態域的小遺跡（有戰利品箱） |
| 到達傳送門 | `portal/ember`、`portal/slate`、`portal/silted`、`portal/dune` | 進入篩靈界時，依落點的生態域挑一座 |
| 迴音洞窟 | `echo_den/hub`、`corridor`、`stairs`、`crossing`、`crystal_grotto`、`resonance_room`、`collapsed_room`、`vault`、`cap` | 地下的拼接式洞窟（各房間會隨機接在一起） |
| 地標 | `humbler_husk`、`lullaby_shrine`、`fossil/rib_arch`、`spine`、`skull`、`claw` | 迅從者殘骸、搖籃曲神殿、地表化石 |

## Boss 競技場的規則

- 競技場現在用結構檔生成，找不到結構檔時才用原本的程式蓋。
- 結構的**正中央那一欄**就是競技場中心；**從下往上第 6 層**是地面高度。地面以下那 5 層是地基，生成時會再往下補到實心地面。
- Boss 會站在中央那一欄**最低的落腳處**。你把王座加高或降低，Boss 也會跟著站上去。
- 世界生成時一個建築最多只能寫到中心往外 23 格，所以不要往外加寬，47×47 已經是上限。
