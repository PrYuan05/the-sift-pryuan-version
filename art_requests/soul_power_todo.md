# 靈魂動力美術

貼圖由 `tools/progression/paint_soul_power.py` 逐像素繪製，放在 `assets/pysift/textures/block/soul_power/`。
模型由 `tools/progression/build_soul_power.py` 產生，參考 Create：每個方塊只用幾個大方塊組成，細節直接畫在貼圖上。
不開遊戲的預覽：`python -I tools/progression/preview_soul_power.py .`，輸出在 `build/soul_power_preview/`。

- 色盤：銅綠青銅（金屬、有鏽斑）、深板岩面板（嵌進機殼、有接縫和螺栓）、染色靈柳木（齒輪、軸）、靈魂光、紫龍晶、鐵。
- 只借用原版的**粒子**圖案：引擎燃燒口的火焰是 `soul_fire_flame`，晶核裡的靈魂是 `sculk_soul_5`。
- **PBR**：每張貼圖都附有 LabPBR 1.3 的 `_n.png`（法線、AO、高度）與 `_s.png`（光滑度、金屬、孔隙度、自發光），
  材質依像素的色盤決定：銅綠算銅、鑽頭算鐵，靈魂光、燈、赤紅幽匿會發光。原版看不到，需要 Iris 加上支援 LabPBR 的光影。
- 想手繪替換時，直接用同檔名覆蓋 PNG，腳本重跑也不會蓋掉（`tools/art_guard.py`）；換了底圖記得一起重畫或刪掉對應的 `_n`／`_s`。
- GUI 底圖（`textures/gui/container/spirit_engine.png`、`soul_grinder.png`）仍是從原版熔爐介面改的。
