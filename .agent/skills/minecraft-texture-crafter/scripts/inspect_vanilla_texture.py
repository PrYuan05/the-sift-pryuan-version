#!/usr/bin/env python3
"""
inspect_vanilla_texture.py
==========================
Minecraft 原版材質提取、結構剖析與「繪師隨身 8 點檢核表」自動化審核工具。

功能：
1. 自動定位專案 `.gradle/loom-cache` 或 `~/.gradle/caches/fabric-loom` 中的 Minecraft 26.3 Client JAR。
2. 支援搜尋 (`--search <keyword>`) 或提取原版材質（例如 `item/mace.png`、`block/deepslate.png`）。
3. 對任意原版或自訂材質執行《🎨 Minecraft 材質繪製與色彩學終極實戰手冊》第 5 章的 8 點檢核：
   - [1] 灰階結構測試 (Grayscale Value Contrast Test)
   - [2] 色相偏移軌跡分析 (HSV Hue Shifting Curve)
   - [3] 純黑 (#000000) / 純白 (#FFFFFF) 違規掃描
   - [4] 孤兒像素偵測 (Orphan Pixels Detection & Cluster Ratio)
   - [5] 左上角光源分佈檢測 (Top-Left vs Bottom-Right Luminance Delta)
   - [6] 選擇性外框檢測 (Selective Outlining / Sel-Out Analysis)
   - [7] 3x3 無縫平鋪邊界連續性預覽 (3x3 Seamless Tiling Preview)
   - [8] 4x4 遠景網格效應測試 (Zoom-Out Grid Effect Preview)
4. 自動輸出高解析度視覺化審核圖至 `build/previews/texture_audit_<name>.png`。

用法範例：
  python -I .agent/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py item/mace.png src/main/resources/assets/pysift/textures/item/sculk_hammer.png
  python -I .agent/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py --search mace
"""

from __future__ import annotations

import argparse
import colorsys
import io
import math
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw

ASCII_RAMP = " .:-=+*#%@"


def find_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here] + list(here.parents):
        if (parent / "build.gradle").exists() or (parent / "settings.gradle").exists():
            return parent
    return Path.cwd().resolve()


def find_vanilla_client_jar(root: Path) -> Path | None:
    """Locate the Minecraft 26.3 client JAR in workspace Loom cache or global Gradle cache."""
    candidates: list[Path] = []
    local_maven = root / ".gradle" / "loom-cache" / "minecraftMaven" / "net" / "minecraft"
    if local_maven.exists():
        candidates.extend(sorted(local_maven.glob("minecraft-clientOnly-*/26.3/minecraft-clientOnly-*-26.3.jar")))
        candidates.extend(sorted(local_maven.glob("minecraft-merged-*/26.3/minecraft-merged-*-26.3.jar")))

    home_loom = Path.home() / ".gradle" / "caches" / "fabric-loom" / "26.3"
    if home_loom.exists():
        candidates.extend(sorted(home_loom.glob("minecraft-client*.jar")))

    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def rgb_to_hsv_deg(r: int, g: int, b: int) -> tuple[float, float, float]:
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return h * 360.0, s * 100.0, v * 100.0


def luminance(r: int, g: int, b: int) -> float:
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def load_target_image(spec: str, root: Path, jar_path: Path | None) -> tuple[str, Image.Image]:
    """Load an image either from disk path or from the vanilla Minecraft client JAR."""
    candidate_path = Path(spec)
    if not candidate_path.is_absolute():
        candidate_path = root / candidate_path
    if candidate_path.is_file():
        return candidate_path.name, Image.open(candidate_path).convert("RGBA")

    if jar_path is None:
        raise FileNotFoundError(f"找不到檔案 '{spec}'，且未偵測到原版 Minecraft Client JAR。")

    normalized = spec.strip().lstrip("/").replace("\\", "/")
    if not normalized.endswith(".png"):
        normalized += ".png"

    jar_candidates = [
        normalized,
        f"assets/minecraft/textures/{normalized}",
        f"assets/minecraft/{normalized}",
    ]
    with zipfile.ZipFile(jar_path, "r") as zf:
        names = set(zf.namelist())
        for jc in jar_candidates:
            if jc in names:
                data = zf.read(jc)
                label = f"vanilla:{jc.replace('assets/minecraft/textures/', '')}"
                return label, Image.open(io.BytesIO(data)).convert("RGBA")

        # Fallback suffix search
        matches = [n for n in names if n.startswith("assets/minecraft/textures/") and n.endswith(normalized)]
        if matches:
            chosen = sorted(matches)[0]
            data = zf.read(chosen)
            label = f"vanilla:{chosen.replace('assets/minecraft/textures/', '')}"
            return label, Image.open(io.BytesIO(data)).convert("RGBA")

    raise FileNotFoundError(f"在檔案系統與原版 JAR ({jar_path.name}) 中皆找不到材質：{spec}")


def analyze_texture(label: str, img: Image.Image) -> dict:
    """Run the 8-point Texture Artist's Checklist analysis on the first frame (top square) of a texture."""
    w, h = img.size
    frame_h = w if (h > w and h % w == 0) else h
    frame = img.crop((0, 0, w, frame_h))
    px = frame.load()

    opaque_pixels: list[tuple[int, int, int, int, int]] = []  # (x, y, r, g, b)
    palette_counter: Counter[tuple[int, int, int]] = Counter()
    pure_black_coords: list[tuple[int, int]] = []
    pure_white_coords: list[tuple[int, int]] = []

    for y in range(frame_h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 16:
                continue
            opaque_pixels.append((x, y, r, g, b))
            palette_counter[(r, g, b)] += 1
            if (r, g, b) == (0, 0, 0):
                pure_black_coords.append((x, y))
            elif (r, g, b) == (255, 255, 255):
                pure_white_coords.append((x, y))

    total_opaque = len(opaque_pixels)
    is_full_block = total_opaque == (w * frame_h)

    # Sort palette from brightest (highest Value/Luminance) to darkest
    palette_sorted = sorted(
        palette_counter.items(),
        key=lambda kv: (luminance(*kv[0]), kv[0][0], kv[0][1], kv[0][2]),
        reverse=True,
    )

    # [Check 1] Value range (Grayscale contrast)
    lums = [luminance(r, g, b) for _, _, r, g, b in opaque_pixels] or [0.0]
    min_lum, max_lum = min(lums), max(lums)
    lum_span = max_lum - min_lum

    # [Check 4] Orphan pixel detection (8-neighborhood exact color or close luminance within 0.06)
    orphan_coords: list[tuple[int, int]] = []
    neighbors_8 = [
        (-1, -1), (0, -1), (1, -1),
        (-1, 0),           (1, 0),
        (-1, 1),  (0, 1),  (1, 1),
    ]
    for x, y, r, g, b in opaque_pixels:
        same_neighbors = 0
        for dx, dy in neighbors_8:
            nx = (x + dx) % w if is_full_block else (x + dx)
            ny = (y + dy) % frame_h if is_full_block else (y + dy)
            if 0 <= nx < w and 0 <= ny < frame_h:
                nr, ng, nb, na = px[nx, ny]
                if na >= 16:
                    if (nr, ng, nb) == (r, g, b) or abs(luminance(nr, ng, nb) - luminance(r, g, b)) < 0.055:
                        same_neighbors += 1
        if same_neighbors == 0:
            orphan_coords.append((x, y))

    # [Check 5 & 6] Outline & Top-Left lighting analysis
    outline_top_left_lums: list[float] = []
    outline_bottom_right_lums: list[float] = []
    interior_top_left_lums: list[float] = []
    interior_bottom_right_lums: list[float] = []

    if opaque_pixels:
        cx = sum(x for x, _, _, _, _ in opaque_pixels) / total_opaque
        cy = sum(y for _, y, _, _, _ in opaque_pixels) / total_opaque
    else:
        cx, cy = w / 2.0, frame_h / 2.0

    for x, y, r, g, b in opaque_pixels:
        lum = luminance(r, g, b)
        is_edge = False
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < frame_h) or px[nx, ny][3] < 16:
                is_edge = True
                break
        is_tl = (x - cx) + (y - cy) <= 0
        if is_edge and not is_full_block:
            if is_tl:
                outline_top_left_lums.append(lum)
            else:
                outline_bottom_right_lums.append(lum)
        else:
            if is_tl:
                interior_top_left_lums.append(lum)
            else:
                interior_bottom_right_lums.append(lum)

    # [Check 7] Seamless border jump score (for full blocks)
    border_diff_h = 0.0
    border_diff_v = 0.0
    if is_full_block and w >= 2 and frame_h >= 2:
        diffs_h = [
            abs(luminance(*px[w - 1, y][:3]) - luminance(*px[0, y][:3]))
            for y in range(frame_h)
        ]
        diffs_v = [
            abs(luminance(*px[x, frame_h - 1][:3]) - luminance(*px[x, 0][:3]))
            for x in range(w)
        ]
        border_diff_h = sum(diffs_h) / len(diffs_h)
        border_diff_v = sum(diffs_v) / len(diffs_v)

    return {
        "label": label,
        "size": (w, h),
        "frame_size": (w, frame_h),
        "frame": frame,
        "total_opaque": total_opaque,
        "is_full_block": is_full_block,
        "palette_sorted": palette_sorted,
        "min_lum": min_lum,
        "max_lum": max_lum,
        "lum_span": lum_span,
        "pure_black_coords": pure_black_coords,
        "pure_white_coords": pure_white_coords,
        "orphan_coords": orphan_coords,
        "outline_tl_lum": sum(outline_top_left_lums) / len(outline_top_left_lums) if outline_top_left_lums else None,
        "outline_br_lum": sum(outline_bottom_right_lums) / len(outline_bottom_right_lums) if outline_bottom_right_lums else None,
        "interior_tl_lum": sum(interior_top_left_lums) / len(interior_top_left_lums) if interior_top_left_lums else 0.0,
        "interior_br_lum": sum(interior_bottom_right_lums) / len(interior_bottom_right_lums) if interior_bottom_right_lums else 0.0,
        "border_diff_h": border_diff_h,
        "border_diff_v": border_diff_v,
    }


def print_analysis_report(info: dict) -> None:
    w, frame_h = info["frame_size"]
    kind_str = "方塊/滿版材質 (Full Block)" if info["is_full_block"] else "物品/透空材質 (Item / Cutout)"
    print("=" * 78)
    print(f"🎨 材質檢核報告: {info['label']}  [{w}x{frame_h}]  類型: {kind_str}")
    print("=" * 78)

    # ASCII structure preview
    frame = info["frame"]
    px = frame.load()
    print("\n📐 [結構與明度 ASCII 階層圖] (空白=透明, .=極暗, @=極亮):")
    header = "    " + "".join(f"{x:2d}" for x in range(min(w, 32)))
    print(header)
    for y in range(min(frame_h, 32)):
        row_chars = []
        for x in range(min(w, 32)):
            r, g, b, a = px[x, y]
            if a < 16:
                row_chars.append("  ")
            else:
                lum = luminance(r, g, b)
                idx = min(len(ASCII_RAMP) - 1, max(1, int(round(lum * (len(ASCII_RAMP) - 1)))))
                ch = ASCII_RAMP[idx]
                row_chars.append(f" {ch}")
        print(f"{y:2d} |{''.join(row_chars)}")

    # Palette table
    print(f"\n🎨 [色盤 HSV 軌跡表] (共 {len(info['palette_sorted'])} 色，依明度由亮至暗排序):")
    print(f"  {'#':>2}  {'HEX':<8} {'Count':>5}   {'Hue(°)':>7}  {'Sat(%)':>7}  {'Val(%)':>7}  {'Lum':>5}")
    print("  " + "-" * 54)
    for idx, ((r, g, b), cnt) in enumerate(info["palette_sorted"][:20], start=1):
        h_deg, s_pct, v_pct = rgb_to_hsv_deg(r, g, b)
        lum = luminance(r, g, b)
        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        print(f"  {idx:>2}  {hex_code:<8} {cnt:>5}   {h_deg:>6.1f}°  {s_pct:>6.1f}%  {v_pct:>6.1f}%  {lum:>5.2f}")
    if len(info["palette_sorted"]) > 20:
        print(f"  ... (其餘 {len(info['palette_sorted']) - 20} 色省略)")

    # 8-point checklist summary
    print("\n🛠️ [繪師隨身 8 點檢核表 (Texture Artist's Checklist)]:")
    # 1. Grayscale
    print(
        f"  [1] 灰階明度跨度 (Value Contrast): {info['min_lum']:.2f} ~ {info['max_lum']:.2f} "
        f"(跨度 Δ={info['lum_span']:.2f}) -> {'✅ 結構對比充足' if info['lum_span'] >= 0.22 else '⚠️ 明度跨度偏窄，請確認灰階圖是否清晰'}"
    )
    # 2. Hue shifting
    if len(info["palette_sorted"]) >= 2:
        top_rgb = info["palette_sorted"][0][0]
        bot_rgb = info["palette_sorted"][-1][0]
        th, ts, tv = rgb_to_hsv_deg(*top_rgb)
        bh, bs, bv = rgb_to_hsv_deg(*bot_rgb)
        hue_diff = min(abs(th - bh), 360.0 - abs(th - bh))
        print(
            f"  [2] 色相與飽和度偏移 (Hue Shifting): 最亮階 H={th:.0f}°/S={ts:.0f}% vs 最暗階 H={bh:.0f}°/S={bs:.0f}% "
            f"(ΔH={hue_diff:.1f}°) -> {'✅ 具備色相偏移' if hue_diff >= 8.0 else '⚠️ ΔH 較小，注意避免死板直線加白加黑'}"
        )
    # 3. Pure black / white
    pb = len(info["pure_black_coords"])
    pw = len(info["pure_white_coords"])
    status_3 = "✅ 完全排除 #000000 與 #FFFFFF" if (pb == 0 and pw == 0) else f"❌ 發現純黑 {pb} 顆、純白 {pw} 顆！"
    print(f"  [3] 拒絕純黑純白 (No #000000/#FFFFFF): {status_3}")

    # 4. Orphan pixels
    orphans = len(info["orphan_coords"])
    orphan_ratio = (orphans / info["total_opaque"] * 100.0) if info["total_opaque"] else 0.0
    print(
        f"  [4] 孤兒像素檢測 (Orphan Pixels): {orphans} 顆 ({orphan_ratio:.1f}%) "
        f"-> {'✅ 像素簇聚合良好' if orphan_ratio <= 25.0 else '⚠️ 單立像素偏多，方塊材質請整合成 2~6 像素簇'}"
    )

    # 5. Top-left lighting
    tl_in = info["interior_tl_lum"]
    br_in = info["interior_br_lum"]
    print(
        f"  [5] 左上角光源一致性 (Top-Left Light): 左上半部均亮={tl_in:.2f} vs 右下半部均亮={br_in:.2f}"
    )

    # 6. Selective outlining
    if info["outline_tl_lum"] is not None and info["outline_br_lum"] is not None:
        otl = info["outline_tl_lum"]
        obr = info["outline_br_lum"]
        print(
            f"  [6] 選擇性外框 (Sel-Out 物品檢測): 左上受光外框均亮={otl:.2f} vs 右下背光外框均亮={obr:.2f} "
            f"-> {'✅ 外框具備受光層次' if otl >= obr else 'ℹ️ 可考慮讓左上受光側外框比右下亮一階'}"
        )
    else:
        print("  [6] 選擇性外框 (Sel-Out): 滿版方塊無外框（跳過）")

    # 7 & 8. Seamless & Grid effect
    if info["is_full_block"]:
        print(
            f"  [7] 無縫邊界連續性 (3x3 Tiling): 左右接縫平均明度差={info['border_diff_h']:.3f}, "
            f"上下接縫平均明度差={info['border_diff_v']:.3f} (請檢視預覽圖中的 3x3 放大平鋪)"
        )
        print("  [8] 網格效應測試 (Grid Effect): 請檢視預覽圖右側的 4x4 遠景平鋪陣列是否視覺均衡")
    else:
        print("  [7 & 8] 無縫與網格測試: 物品材質請重點檢視預覽圖中的 1x 原尺寸剪影辨識度")
    print()


def render_checkerboard(w: int, h: int, cell: int = 8) -> Image.Image:
    bg = Image.new("RGBA", (w, h), (36, 38, 44, 255))
    draw = ImageDraw.Draw(bg)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if ((x // cell) + (y // cell)) % 2 == 1:
                draw.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(48, 52, 60, 255))
    return bg


def build_audit_sheet(analyses: list[dict], out_path: Path) -> None:
    """
    Render a visual audit sheet combining:
    - Panel 1: 10x Color Zoom + 1x Silhouette
    - Panel 2: 10x Grayscale Value Test (Check #1)
    - Panel 3: 10x Orphan Pixel & Outline Map (Check #4 & #6)
    - Panel 4: 3x3 Seamless Tiling at 4x Zoom + 4x4 Zoom-Out Grid Test at 2x Zoom (Check #7 & #8)
    - Panel 5: Palette Ramp Swatches (Brightest -> Darkest)
    """
    row_h = 240
    canvas_w = 960
    canvas_h = max(1, len(analyses)) * row_h
    sheet = Image.new("RGBA", (canvas_w, canvas_h), (24, 26, 30, 255))
    draw = ImageDraw.Draw(sheet)

    for idx, info in enumerate(analyses):
        y0 = idx * row_h
        frame: Image.Image = info["frame"]
        fw, fh = info["frame_size"]
        scale_main = max(1, min(10, 160 // max(fw, fh)))
        up_w, up_h = fw * scale_main, fh * scale_main

        # Header bar
        draw.rectangle([0, y0, canvas_w, y0 + 26], fill=(38, 42, 50, 255))
        draw.text(
            (12, y0 + 6),
            f"[{idx + 1}] {info['label']} ({fw}x{fh}) | Colors: {len(info['palette_sorted'])} | "
            f"Value Span: {info['lum_span']:.2f} | Orphans: {len(info['orphan_coords'])}",
            fill=(230, 235, 245, 255),
        )

        panel_y = y0 + 36

        # --- Panel 1: 10x Color + 1x & 2x Silhouette ---
        p1_x = 16
        draw.text((p1_x, panel_y - 4), "1. Color (10x + 1x/2x)", fill=(180, 190, 205, 255))
        bg1 = render_checkerboard(up_w, up_h, cell=max(4, scale_main // 2))
        up_color = frame.resize((up_w, up_h), Image.Resampling.NEAREST)
        bg1.alpha_composite(up_color)
        sheet.paste(bg1, (p1_x, panel_y + 12))

        # 1x and 2x actual inventory size preview next to Panel 1
        s1_bg = render_checkerboard(fw, fh, cell=4)
        s1_bg.alpha_composite(frame)
        sheet.paste(s1_bg, (p1_x + up_w + 8, panel_y + 12))
        s2_bg = render_checkerboard(fw * 2, fh * 2, cell=4)
        s2_bg.alpha_composite(frame.resize((fw * 2, fh * 2), Image.Resampling.NEAREST))
        sheet.paste(s2_bg, (p1_x + up_w + 8, panel_y + 12 + fh + 8))

        # --- Panel 2: Grayscale Value Test (Check #1) ---
        p2_x = 236
        draw.text((p2_x, panel_y - 4), "2. Grayscale Value Test", fill=(180, 190, 205, 255))
        gray_frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        gpx = gray_frame.load()
        fpx = frame.load()
        for yy in range(fh):
            for xx in range(fw):
                r, g, b, a = fpx[xx, yy]
                if a >= 16:
                    gv = int(round(luminance(r, g, b) * 255))
                    gpx[xx, yy] = (gv, gv, gv, a)
        bg2 = render_checkerboard(up_w, up_h, cell=max(4, scale_main // 2))
        bg2.alpha_composite(gray_frame.resize((up_w, up_h), Image.Resampling.NEAREST))
        sheet.paste(bg2, (p2_x, panel_y + 12))

        # --- Panel 3: Orphan Pixels (Red) & Pure Black/White (Yellow) Map ---
        p3_x = 420
        draw.text((p3_x, panel_y - 4), "3. Clusters (Red=Orphan)", fill=(180, 190, 205, 255))
        bg3 = render_checkerboard(up_w, up_h, cell=max(4, scale_main // 2))
        dim_frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        dpx = dim_frame.load()
        orphan_set = set(info["orphan_coords"])
        pb_set = set(info["pure_black_coords"]) | set(info["pure_white_coords"])
        for yy in range(fh):
            for xx in range(fw):
                r, g, b, a = fpx[xx, yy]
                if a >= 16:
                    if (xx, yy) in pb_set:
                        dpx[xx, yy] = (255, 230, 0, 255)
                    elif (xx, yy) in orphan_set:
                        dpx[xx, yy] = (255, 75, 85, 255)
                    else:
                        dpx[xx, yy] = (int(r * 0.65), int(g * 0.65), int(b * 0.65), a)
        bg3.alpha_composite(dim_frame.resize((up_w, up_h), Image.Resampling.NEAREST))
        sheet.paste(bg3, (p3_x, panel_y + 12))

        # --- Panel 4: 3x3 Seamless Tiling (3x zoom) & 4x4 Zoom-Out Grid Test (2x zoom) ---
        p4_x = 604
        draw.text((p4_x, panel_y - 4), "4. 3x3 Seamless & 4x4 Grid", fill=(180, 190, 205, 255))
        tile_3x3 = Image.new("RGBA", (fw * 3, fh * 3), (0, 0, 0, 0))
        for ty in range(3):
            for tx in range(3):
                tile_3x3.paste(frame, (tx * fw, ty * fh))
        t3_scale = max(1, min(3, 144 // max(fw * 3, fh * 3)))
        t3_w, t3_h = fw * 3 * t3_scale, fh * 3 * t3_scale
        bg4 = render_checkerboard(t3_w, t3_h, cell=6)
        bg4.alpha_composite(tile_3x3.resize((t3_w, t3_h), Image.Resampling.NEAREST))
        sheet.paste(bg4, (p4_x, panel_y + 12))

        # 4x4 zoom-out grid next to 3x3
        tile_4x4 = Image.new("RGBA", (fw * 4, fh * 4), (0, 0, 0, 0))
        for ty in range(4):
            for tx in range(4):
                tile_4x4.paste(frame, (tx * fw, ty * fh))
        t4_scale = max(1, min(2, 128 // max(fw * 4, fh * 4)))
        t4_w, t4_h = fw * 4 * t4_scale, fh * 4 * t4_scale
        bg4_small = render_checkerboard(t4_w, t4_h, cell=4)
        bg4_small.alpha_composite(tile_4x4.resize((t4_w, t4_h), Image.Resampling.NEAREST))
        sheet.paste(bg4_small, (p4_x + t3_w + 12, panel_y + 12))

        # --- Palette Swatch Bar at bottom of row ---
        pal_y = y0 + row_h - 24
        draw.text((16, pal_y + 2), "Palette (Bright->Dark):", fill=(170, 180, 195, 255))
        sx = 175
        sw_w = min(28, max(10, (canvas_w - sx - 20) // max(1, len(info["palette_sorted"]))))
        for (r, g, b), _ in info["palette_sorted"][:26]:
            draw.rectangle([sx, pal_y, sx + sw_w - 2, pal_y + 16], fill=(r, g, b, 255), outline=(60, 65, 75, 255))
            sx += sw_w

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Minecraft 原版材質提取與 8 點檢核自動化工具")
    parser.add_argument("targets", nargs="*", help="原版貼圖路徑 (如 item/mace.png) 或本地貼圖檔案路徑")
    parser.add_argument("--search", "-s", help="在原版 Minecraft 26.3 Client JAR 中搜尋包含關鍵字的貼圖路徑")
    parser.add_argument("--extract-to", "-e", help="將讀取到的第一張貼圖匯出至指定路徑")
    parser.add_argument("--output", "-o", help="自訂視覺化檢核圖輸出路徑 (預設: build/previews/texture_audit_<name>.png)")
    args = parser.parse_args()

    root = find_project_root()
    jar_path = find_vanilla_client_jar(root)

    if jar_path:
        try:
            rel_jar = jar_path.relative_to(root)
        except ValueError:
            rel_jar = jar_path
        print(f"📦 已定位原版材質壓縮檔 (Client JAR): {rel_jar}")
    else:
        print("⚠️ 未找到原版 Minecraft Client JAR，僅支援讀取本地檔案。")

    if args.search:
        if not jar_path:
            print("❌ 無法搜尋：找不到原版 Client JAR。", file=sys.stderr)
            return 1
        kw = args.search.lower()
        with zipfile.ZipFile(jar_path, "r") as zf:
            hits = sorted(
                n.replace("assets/minecraft/textures/", "")
                for n in zf.namelist()
                if n.startswith("assets/minecraft/textures/") and n.endswith(".png") and kw in n.lower()
            )
        print(f"🔍 搜尋 '{args.search}' 共找到 {len(hits)} 筆原版貼圖:")
        for h in hits[:80]:
            print(f"  - {h}")
        if len(hits) > 80:
            print(f"  ... (其餘 {len(hits) - 80} 筆省略)")
        if not args.targets:
            return 0

    if not args.targets:
        parser.print_help()
        return 0

    analyses: list[dict] = []
    for spec in args.targets:
        label, img = load_target_image(spec, root, jar_path)
        if args.extract_to and len(analyses) == 0:
            ext_path = Path(args.extract_to)
            if not ext_path.is_absolute():
                ext_path = root / ext_path
            ext_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(ext_path)
            print(f"💾 已提取貼圖至: {ext_path}")
        info = analyze_texture(label, img)
        print_analysis_report(info)
        analyses.append(info)

    if analyses:
        if args.output:
            out_path = Path(args.output)
            if not out_path.is_absolute():
                out_path = root / out_path
        else:
            last_stem = Path(analyses[-1]["label"].split(":")[-1]).stem
            out_path = root / "build" / "previews" / f"texture_audit_{last_stem}.png"
        build_audit_sheet(analyses, out_path)
        try:
            rel_out = out_path.relative_to(root)
        except ValueError:
            rel_out = out_path
        print(f"🖼️ 已產生 8 點檢核視覺化對照圖: {rel_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
