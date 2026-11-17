# 相容性：玩家動畫模組

The Sift 的武器動畫分兩塊：
- 第三人稱全身動畫：用 Player Animation Library（PAL）播放，在 `client/PlayerAnims` 註冊一層 `pysift:weapons`
- 手寫姿勢：第三人稱由 `mixin/HumanoidModelMixin`、`mixin/PlayerModelLatePoseMixin` 套上，第一人稱由 `mixin/FirstPersonHandsMixin` 套上

和其他動畫模組協調的程式都在 `client/compat/AnimCompat`。

## 設定 `config/pysift.properties`

```
animation_priority=override   # 預設。拿著 The Sift 武器時，我們的動畫優先
animation_priority=yield      # 讓其他模組優先
```

設定檔裡沒有這一行時，第一次啟動會自動補上。改完要重開遊戲才會生效。

| | override | yield |
|---|---|---|
| PAL 圖層優先度 | 5000 | 100 |
| 通知 Punchy! 讓出第一人稱 | 會 | 不會 |
| 通知 Punchy! Moves 讓出第三人稱 | 會 | 不會 |
| 手寫姿勢在 Punchy! Moves 之後再套一次 | 會 | 不會 |

## 檢查過的模組（26.3 Fabric 版）

| 模組 | 版本 | 做了什麼 | 我們怎麼處理 |
|---|---|---|---|
| **Punchy!**（`punchy`，modrinth `punchy-fpa`） | 3.2b | 只做第一人稱。它自己畫第一人稱的手和物品，原版的第一人稱繪製會被跳過，所以 `FirstPersonHandsMixin` 的姿勢不會出現 | 呼叫它公開的 `PunchyApi.leaveItemsToMinecraft` 與 `leaveHandsToMinecraft`，把 The Sift 的武器（重錘、法杖、衝刺護符、調音叉、靈魂標槍）交還給原版繪製 |
| **Punchy! Moves**（`punchy_moves`） | 1.0.9 | 第三人稱的全身移動動畫。它會在 `PlayerModel.setupAnim` 最後再改一次姿勢（mixin 優先度到 3000～4000），所以會蓋掉優先度 1000 的姿勢 | 透過它公開的 `AnimationIntent.register` 回報 `SPECIAL_ACTION`：拿著或使用我們的武器、或我們的 PAL 動畫正在播時就回報。另外用優先度 5000 的 `PlayerModelLatePoseMixin`，在它之後再把手寫姿勢套回去 |
| Better Combat | 3.2.2+26.3 | 用 PAL 系的圖層播放攻擊動畫 | 我們的 PAL 圖層優先度改成 5000，蓋過它的攻擊動畫。只有拿著我們的武器時，我們的圖層才會在播 |
| Emotecraft | 3.5.0-b179 | 用 PAL 系的圖層播放表情動作 | 同上。表情動作播放期間如果剛好在用我們的武器，以我們的動畫為準 |
| Not Enough Animations | 1.12.7 | 用自己的 mixin 改原版手臂姿勢（例如吃東西、看地圖） | 第三人稱全身動畫由 PAL 負責，蓋得過它。手寫姿勢裝在 `HumanoidModel.setupAnim` 的 TAIL，沒有額外處理 |

Punchy! 是保留所有權利（ARR）的模組，禁止反編譯。我們只看了它的 `fabric.mod.json`、mixin 設定檔裡的類別清單、mixin 的目標方法，以及公開 API 的方法簽名，並且全部用反射呼叫。`build.gradle` 沒有加它的依賴，也不打包它的任何程式碼。沒裝 Punchy! 時，這些程式碼完全不會執行。

## 尚未在遊戲內驗證

- Punchy! 的 `leaveItemsToMinecraft` 傳給判斷函式的參數，我們假設是 `ItemStack`。如果實際不是，第一人稱還是會由 Punchy! 繪製，log 裡不會出現錯誤
- 用 Better Combat 或 Emotecraft 時，左鍵揮擊是否還會觸發 `LivingEntity.swing`（我們的左鍵動畫靠它觸發）
