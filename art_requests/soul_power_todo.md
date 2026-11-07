# 靈魂動力美術需求

機器已經做成 Create 式的「外殼＋會動的部件」（`tools/progression/build_soul_power.py`，預覽：
`python -I tools/progression/preview_soul_power.py .` → `build/soul_power_preview/`）。目前的貼圖借用模組裡的銅綠、
靈柳木、靈魂晶與原版貼圖；想換成專屬貼圖時，把新圖放進 `assets/pysift/textures/block/soul_power/`，再改產生器裡的
貼圖常數（`PATINA`、`LOG`、`TEETH`…）重跑即可。

| 部件 | 現在用的 | 想要的感覺 |
| :--- | :--- | :--- |
| 傳動軸 `shaft` | 去皮靈柳木＋兩條靈魂晶紋 | 金屬包覆的軸，紋路要看得出在轉 |
| 齒輪 `cog`、`large_cog` | 靈柳木年輪＋深板岩齒 | 木齒盤、銅綠包邊的齒 |
| 飛輪 `flywheel` | 氧化銅輪框＋靈魂晶配重 | 有輻條的鑄造飛輪 |
| 靈液引擎外殼 | 銅綠＋`spirit_engine_front(_on).png`（原版高爐正面換成藍綠靈液火，腳本畫的） | 可以重畫成更有靈液感的燃燒口 |
| 研磨機石磨 | 平滑石＋砂輪 | 有放射溝槽的石磨 |
| 淨化篩的篩網 `sieve` | 工作台頂面 | 細格子的篩網 |
| 振波天線碟 | 紫水晶／幽匿感測器 | 發送與接收看得出差別 |
| 靈壓計錶盤 | `soul_gauge_dial.png`（腳本畫的） | 可以重畫，指針 0 在左下、滿載在右下 |
| GUI | `textures/gui/container/spirit_engine.png`、`soul_grinder.png` | 從原版熔爐介面改的，淨化篩共用研磨機的介面 |
