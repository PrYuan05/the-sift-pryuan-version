# 靈魂動力（第一階段）美術需求

目前方塊用原版貼圖當臨時圖（`tools/progression/build_soul_power.py` 的 `MACHINES` 與傳動軸模型）。畫好後放進
`assets/pysift/textures/block/`，再把產生器裡的貼圖路徑換成 `pysift:block/<名稱>` 重跑即可。
運轉中（`powered=true`）的貼圖建議做成動畫（`.png.mcmeta`），讓玩家一眼看出網路在轉。

| 方塊 | 需要的貼圖 | 說明 |
| :--- | :--- | :--- |
| 靈液引擎 `spirit_engine` | front、front_on（動畫）、side、top | 正面是燃燒口（GUI 那一面），燒的是靈液，火焰偏藍綠 |
| 靈魂傳動軸 `soul_shaft` | side、side_on（動畫，轉動感）、end | 模型是 6×6 的軸，貼圖只用中間 6 格寬 |
| 靈魂振波發送器 `soul_wave_emitter` | front、front_on（動畫）、side | 正面發出靈魂波；背面接傳動 |
| 靈魂振波接收器 `soul_wave_receiver` | front、front_on（動畫）、side | 和發送器成對，但看得出是「收」 |
| 靈魂研磨機 `soul_grinder` | top、top_on（動畫，磨盤轉動）、front、side | 上方是磨盤 |
| GUI | `textures/gui/container/spirit_engine.png`、`soul_grinder.png` | 目前是從原版熔爐介面改的 |
