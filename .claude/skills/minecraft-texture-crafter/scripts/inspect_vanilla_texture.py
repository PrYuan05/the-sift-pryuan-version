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
4. 進階規則檢核（Cotufa + Jappa 原版標準，依 --kind 選擇）：
   - [9] 2 的次方尺寸  [10] 每條色階組的色數（物品 4~7、方塊雙層色階 4~8）  [11] 相鄰色階明度差（物品 ≥8%；方塊雙層架構允許 1~4 處微紋理副色）
   - [12] 相對色相偏移（亮部往暖 +10~20°、暗部往冷 15~30°）  [13] 低飽和中間調橋接、飽和度上限  [14] 棋盤格混色
   - 物品：[15] 置中範圍 12~14 px 與 1~2 px 留白  [16] L 形雙角  [17] 45° 對角主軸（handheld）
   - 方塊：[15] 環面長直線 > 4 px  [16]/[17] 木板 4 列、磚塊錯縫、雕紋斜面外框與鏡像對稱、礦石外圍保留原石與礦簇陰影
   - 方塊：[18] 表面微紋理與色階過渡檢核（反 AI 平塗塑膠感：單色佔比 ≤55%、紋理變化率 ≥45%、柔和微過渡 ≥20%）
5. 自動輸出高解析度視覺化審核圖至 `build/previews/texture_audit_<name>.png`。

用法範例：
  python -I .claude/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py item/mace.png src/main/resources/assets/pysift/textures/item/sculk_hammer.png --kind handheld
  python -I .claude/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py block/iron_ore.png --kind ore --base block/stone.png
  python -I .claude/skills/minecraft-texture-crafter/scripts/inspect_vanilla_texture.py --search mace
（Antigravity 用的副本在 .agent/skills/minecraft-texture-crafter/，內容相同）
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


# =====================================================================================================================
# 進階規則檢核（Cotufa + Jappa 原版標準，SKILL.md 第 2.4 節、第 3 步 A／B 拓撲、第 4 步 9~16 項）
# =====================================================================================================================
KINDS = ("auto", "block", "item", "handheld", "planks", "bricks", "chiseled", "ore")
WARM_HUE, COOL_HUE = 55.0, 240.0       # 亮部往黃、暗部往藍紫（含深紅也算冷暗：見 _toward_cool）


def _hue_dist(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _toward(h_from: float, h_to: float, target: float) -> float:
    """h_from -> h_to 往 target 靠近了幾度（正 = 靠近，負 = 遠離）。"""
    return _hue_dist(h_from, target) - _hue_dist(h_to, target)


def _toward_cool(h_base: float, h_shadow: float) -> float:
    """暗部往冷色（藍紫 240°）或深紅紫（330°）靠近的度數，取較大者（Cotufa：shadow 偏 blue / purple / crimson）。"""
    return max(_toward(h_base, h_shadow, COOL_HUE), _toward(h_base, h_shadow, 300.0))


def material_groups(palette: list[tuple[tuple[int, int, int], int]]) -> list[list[tuple[tuple[int, int, int], int]]]:
    """把色盤分成「材質色階組」：低飽和（S < 12%）一組；其餘依色相排序後串連，相鄰色相差 ≤ 25° 的屬於同一條 ramp
    （色相偏移過的亮部、暗部會和固有色連在一起，不會被切到別組）。"""
    gray = [(rgb, c) for rgb, c in palette if rgb_to_hsv_deg(*rgb)[1] < 12.0]
    chroma = sorted(((rgb, c) for rgb, c in palette if rgb_to_hsv_deg(*rgb)[1] >= 12.0), key=lambda kv: rgb_to_hsv_deg(*kv[0])[0])
    groups: list[list] = []
    for rgb, c in chroma:
        hue = rgb_to_hsv_deg(*rgb)[0]
        if groups and _hue_dist(hue, rgb_to_hsv_deg(*groups[-1][-1][0])[0]) <= 25.0:
            groups[-1].append((rgb, c))
        else:
            groups.append([(rgb, c)])
    if len(groups) > 1 and _hue_dist(rgb_to_hsv_deg(*groups[0][0][0])[0], rgb_to_hsv_deg(*groups[-1][-1][0])[0]) <= 25.0:
        groups[0] = groups.pop() + groups[0]      # 色環頭尾（紅色 0°／360°）相接
    if gray:
        groups.append(gray)
    return sorted(groups, key=lambda g: -sum(c for _, c in g))


def _value_levels(group) -> list[float]:
    """一組色階的明度層（HSV V %），相差 < 2% 的視為同一層。"""
    vs = sorted({round(rgb_to_hsv_deg(*rgb)[2], 1) for rgb, _ in group}, reverse=True)
    levels: list[float] = []
    for v in vs:
        if not levels or levels[-1] - v >= 2.0:
            levels.append(v)
    return levels


def advanced_checks(info: dict, kind: str, base: Image.Image | None) -> list[tuple[str, str, str]]:
    """回傳 [(編號與名稱, 狀態 ✅/⚠️/ℹ️, 說明)]。"""
    frame: Image.Image = info["frame"]
    w, h = info["frame_size"]
    px = frame.load()
    full = info["is_full_block"]
    if kind == "auto":
        kind = "block" if full else "item"
    is_item = kind in ("item", "handheld")
    out: list[tuple[str, str, str]] = []
    opaque = lambda x, y: 0 <= x < w and 0 <= y < h and px[x, y][3] >= 16

    # [9] 尺寸：2 的次方（非 2 的次方會讓整個方塊圖集的 mipmap 降級）
    pow2 = lambda n: n > 0 and (n & (n - 1)) == 0
    sw, sh = info["size"]
    ok = pow2(w) and pow2(sh if sh == w else w) and (sh % w == 0)
    out.append(("[9] 2 的次方尺寸", "✅" if ok else "⚠️",
                f"{sw}x{sh}" + ("" if ok else "：方塊貼圖請用 16／32／64，動畫貼圖高度要是寬度的整數倍")))

    # [10] 每條 ramp 的色階數：物品 3~7、方塊雙層架構 4~8（4~5 結構主色 + 1~3 微紋理過渡副色）
    groups = material_groups(info["palette_sorted"])
    limit_lo, limit_hi = (3, 7) if is_item else (4, 8)
    counts = [len(_value_levels(g)) for g in groups if sum(c for _, c in g) >= max(4, info["total_opaque"] * 0.04)]
    bad = [c for c in counts if c > limit_hi]
    out.append(("[10] 每條色階組的色數", "✅" if not bad else "⚠️",
                f"{len(counts)} 組材質色階，各 {counts} 層（建議 {limit_lo}~{limit_hi}）"
                + ("" if not bad else "：色階太多會像模糊照片，請合併相近色")))

    # [11] 相鄰色階明度差 ΔV（物品全程 ≥8%；方塊採「結構主色 + 1~4 處 2~5% 表面微紋理副色」雙層架構）
    steps = []
    for g in groups:
        lv = _value_levels(g)
        steps += [round(a - b, 1) for a, b in zip(lv, lv[1:])]
    if is_item:
        tight = [s for s in steps if s < 8.0]
        out.append(("[11] 相鄰色階明度差 ΔV", "✅" if not tight else "⚠️",
                    f"最小 ΔV={min(steps) if steps else 0:.1f}%"
                    + ("（全部 ≥ 8%）" if not tight else
                       f"，有 {len(tight)} 處 < 8%：物品小圖示下會糊成一片，請拉開到 8~15%")))
    else:
        micro = [s for s in steps if s < 5.0]
        ok11 = len(micro) <= 4 and info["lum_span"] >= 0.10
        out.append(("[11] 相鄰色階明度差 ΔV (方塊雙層)", "✅" if ok11 else "⚠️",
                    f"最小 ΔV={min(steps) if steps else 0:.1f}%，含 {len(micro)} 處 <5% 微紋理／緩衝副色階（總跨度 ΔLum={info['lum_span']:.2f}）"
                    + ("" if ok11 else "：微差色階過多(>4)或總跨度過窄(<0.10)，請整理為 4~5 結構主色 + 1~3 微紋理副色")))

    # [12] 相對色相偏移：亮部往暖 +10~20°、暗部往冷 15~30°；亮部飽和度略降
    main = groups[0] if groups else []
    if len(main) >= 3:
        base_rgb = max(main, key=lambda kv: kv[1])[0]
        bh, bs, bv = rgb_to_hsv_deg(*base_rgb)
        hi = max(main, key=lambda kv: rgb_to_hsv_deg(*kv[0])[2])[0]
        lo = min(main, key=lambda kv: rgb_to_hsv_deg(*kv[0])[2])[0]
        hh, hs, hv = rgb_to_hsv_deg(*hi)
        lh, ls, lv_ = rgb_to_hsv_deg(*lo)
        warm = _toward(bh, hh, WARM_HUE) if bs >= 12 else 0.0
        cool = _toward_cool(bh, lh) if bs >= 12 else 0.0
        gray = bs < 12
        good = gray or (warm >= 5 and cool >= 8 and hs <= bs + 3)
        out.append(("[12] 相對色相偏移", "✅" if good else "⚠️",
                    "主色低飽和（灰系），色相偏移改看暖亮冷暗的微弱色偏" if gray else
                    f"亮部往暖 {warm:+.0f}°（建議 +10~20）、暗部往冷 {cool:+.0f}°（建議 15~30）、"
                    f"亮部 S {bs:.0f}%→{hs:.0f}%（應略降）"))
    else:
        out.append(("[12] 相對色相偏移", "ℹ️", "主色組少於 3 色，無法判斷"))

    # [13] 低飽和中間調橋接：ramp 中段至少一色比兩側更不飽和（或主色本身 S ≤ 65%）
    if len(main) >= 3:
        ramp = sorted(main, key=lambda kv: rgb_to_hsv_deg(*kv[0])[2])
        sats = [rgb_to_hsv_deg(*rgb)[1] for rgb, _ in ramp]
        bridge = any(sats[i] < sats[i - 1] and sats[i] < sats[i + 1] for i in range(1, len(sats) - 1)) or max(sats) <= 65
        out.append(("[13] 低飽和中間調橋接", "✅" if bridge else "ℹ️",
                    f"S 由暗到亮 {[round(s) for s in sats]}" + ("" if bridge else "：可在暗部與亮部之間插一個降飽和的過渡色")))
    max_s = max((rgb_to_hsv_deg(*rgb)[1] for rgb, _ in info["palette_sorted"]), default=0)
    if max_s >= 98:
        out.append(("[13b] 飽和度上限", "⚠️", f"有 S={max_s:.0f}% 的顏色，請避免 100% 純色"))

    # [14] 禁止棋盤格混色：3x3 範圍內兩種顏色完全交錯（自然雜點偶爾碰出的 2x2 交錯不算）
    dith = 0
    for y in range(h - 2):
        for x in range(w - 2):
            a, b = px[x, y], px[x + 1, y]
            if a[3] < 16 or b[3] < 16 or a[:3] == b[:3]:
                continue
            if all(px[x + dx, y + dy][3] >= 16 and px[x + dx, y + dy][:3] == (a if (dx + dy) % 2 == 0 else b)[:3]
                   for dx in range(3) for dy in range(3)):
                dith += 1
    out.append(("[14] 棋盤格混色 (Dithering)", "✅" if dith == 0 else "⚠️",
                f"{dith} 處 3x3 交錯" + ("" if dith == 0 else "：改用 2~4 px 像素簇做明暗，不要用棋盤格混色")))

    if is_item:
        # [15] 置中範圍與留白：一般物品 12x12~14x14、四周 1~2 px 透明
        xs = [x for x in range(w) for y in range(h) if opaque(x, y)]
        ys = [y for x in range(w) for y in range(h) if opaque(x, y)]
        if xs:
            bw, bh_ = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
            margin = min(min(xs), min(ys), w - 1 - max(xs), h - 1 - max(ys))
            scale = w / 16
            if kind == "handheld":
                ok = True
                note = f"外框 {bw}x{bh_}（手持工具可貼滿對角線）"
            else:
                ok = 12 * scale <= max(bw, bh_) <= 14 * scale and margin >= 1 * scale
                note = f"外框 {bw}x{bh_}、最小留白 {margin} px（建議 12~14、留白 1~2）"
            out.append(("[15] 置中範圍與留白", "✅" if ok else "⚠️", note))

        # [16] 2x2 L 形雙角：外框在斜線轉角多塞了一格（應該角對角相接）
        edge = {(x, y) for x in range(w) for y in range(h) if opaque(x, y)
                and any(not opaque(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        doubled = 0
        for y in range(h - 1):
            for x in range(w - 1):
                cells = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
                on = [c for c in cells if c in edge]
                off = [c for c in cells if not opaque(*c)]
                if len(on) == 3 and len(off) == 1:
                    # 三格外框排成 L、第四格透明，而且 L 的轉角那格往外沒有延伸 → 階梯上的多餘轉角
                    corner = next(c for c in on if abs(c[0] - off[0][0]) + abs(c[1] - off[0][1]) == 2)
                    ox, oy = 2 * corner[0] - off[0][0], 2 * corner[1] - off[0][1]
                    if not opaque(ox, corner[1]) or not opaque(corner[0], oy):
                        doubled += 1
        out.append(("[16] L 形雙角 (Doubled corners)", "✅" if doubled <= 2 else "⚠️",
                    f"{doubled} 處" + ("" if doubled <= 2 else "：斜線與曲線的外框要角對角相接，拿掉轉角內側多的那一格")))

        if kind == "handheld":
            # [17] 45° 主軸：像素集中在 y = 15 - x 附近（縮放到 16 格）
            scale = w / 16
            pts = [(x / scale, y / scale) for x in range(w) for y in range(h) if opaque(x, y)]
            near = sum(1 for x, y in pts if abs(x + y - 15) <= 2.5) / max(1, len(pts))
            out.append(("[17] 45° 對角主軸 y=15-x", "✅" if near >= 0.45 else "⚠️",
                        f"{near * 100:.0f}% 的像素落在主對角線 ±2 px 內（握柄、刃身應沿 1:1 對角線）"))
    else:
        # [15] 環面直線：和上方（或左方）不同色、本身同色、長度 > 4 px 的直線段（環繞掃描，跨邊界的也算；
        #      整列貫穿的縫是刻意的，不計）。平鋪後這種直線會變成明顯的格線
        long_runs = 0
        for horizontal in (True, False):
            n_lines, n_along = (h, w) if horizontal else (w, h)
            for i in range(n_lines):
                cell = (lambda j, i=i: (j % n_along, i)) if horizontal else (lambda j, i=i: (i, j % n_along))
                run, start = 0, 0
                for j in range(2 * n_along):
                    x, y = cell(j)
                    ax, ay = (x, (y - 1) % h) if horizontal else ((x - 1) % w, y)
                    c = px[x, y][:3]
                    edge = c != px[ax, ay][:3]
                    if edge and run and c == px[cell(j - 1)[0], cell(j - 1)[1]][:3]:
                        run += 1
                    elif edge:
                        run, start = 1, j
                    else:
                        if 4 < run < n_along and start < n_along:
                            long_runs += 1
                        run = 0
        out.append(("[15] 環面直線 (> 4 px)", "✅" if long_runs <= (6 if kind in ("planks", "bricks", "chiseled") else 2) else "⚠️",
                    f"{long_runs} 條" + ("（木板／磚／雕紋的縫本來就是直線，僅供參考）" if kind in ("planks", "bricks", "chiseled")
                                       else "：自然方塊避免超過 4 px 的筆直邊界，平鋪後會出現格線")))

        lum = lambda x, y: luminance(*px[x % w, y % h][:3])
        rows = [sum(lum(x, y) for x in range(w)) / w for y in range(h)]
        cols = [sum(lum(x, y) for y in range(h)) / h for x in range(w)]
        mean = sum(rows) / len(rows)
        if kind == "planks":
            # [16] 木板：4 列 × 4 px，每列底部（y=3,7,11,15）是較暗的接縫
            seam = [rows[y] for y in range(h) if y % (h // 4) == h // 4 - 1]
            ok = all(s < mean - 0.02 for s in seam)
            out.append(("[16] 木板 4 列拓撲", "✅" if ok else "⚠️",
                        f"接縫列明度 {[round(s, 2) for s in seam]} vs 平均 {mean:.2f}（每 4 px 一條較暗的接縫，相鄰列接頭錯開）"))
        if kind == "bricks":
            # [16] 磚：水平縫每 4 或 8 px 一條；上下兩層的直縫錯開 50%
            dark_rows = [y for y in range(h) if rows[y] < mean - 0.03]
            period = sorted({(b - a) for a, b in zip(dark_rows, dark_rows[1:]) if b - a > 1})
            out.append(("[16] 磚塊錯縫拓撲", "✅" if any(p in (h // 4, h // 2) for p in period) else "ℹ️",
                        f"較暗的水平縫在 y={dark_rows}（建議每 4 或 8 px 一層、層與層直縫錯開 8 px，縫的右下側較暗）"))
        if kind == "chiseled":
            # [16] 1 px 斜面外框：x=0、y=0 亮；x=15、y=15 暗
            top, left = rows[0], cols[0]
            bottom, right = rows[h - 1], cols[w - 1]
            inner = sum(lum(x, y) for x in range(1, w - 1) for y in range(1, h - 1)) / ((w - 2) * (h - 2))
            bevel = top > inner and left > inner and bottom < inner and right < inner
            out.append(("[16] 1 px 斜面外框", "✅" if bevel else "⚠️",
                        f"上 {top:.2f}／左 {left:.2f}／下 {bottom:.2f}／右 {right:.2f}，內部 {inner:.2f}（上左應比內部亮、下右應比內部暗）"))
            # [17] 中央 14x14 的鏡像對稱（左右或上下，至少一軸）
            def sym(mx: bool) -> float:
                """中央 14x14 的結構邊緣（和四周鄰居的明度差最大的 30% 格子）鏡像吻合率。左上光源讓刻痕一側亮、
                一側暗，亮暗本身不對稱，但刻痕兩側都是強邊緣，邊緣強度的位置是對稱的。"""
                grad = {(x, y): abs(lum(x, y) - (lum(x - 1, y) + lum(x + 1, y) + lum(x, y - 1) + lum(x, y + 1)) / 4)
                        for y in range(1, h - 1) for x in range(1, w - 1)}
                cut = sorted(grad.values())[int(len(grad) * 0.7)]
                edge = {k for k, v in grad.items() if v >= cut and v > 0.02}
                if not edge:
                    return 0.0
                hit = 0
                for x, y in edge:
                    x2, y2 = (w - 1 - x, y) if mx else (x, h - 1 - y)
                    hit += (x2, y2) in edge
                return hit / len(edge)

            lr, tb = sym(True), sym(False)
            # 校準（原版 26.3）：雕紋／金屬方塊較佳的一軸 47~68%，石頭、泥土、鵝卵石只有 30~37%
            out.append(("[17] 中央鏡像對稱", "✅" if max(lr, tb) >= 0.45 else "⚠️",
                        f"結構邊緣左右 {lr * 100:.0f}%、上下 {tb * 100:.0f}% 吻合（至少一軸 ≥ 45%；原版雕紋 47~68%、自然石材 30~37%）"))
        if kind == "ore":
            if base is None:
                out.append(("[16] 礦石外圍保留原石", "ℹ️", "加上 --base <原石貼圖> 才能比對（例如 --base block/stone.png）"))
            else:
                bpx = base.convert("RGBA").resize((w, h), Image.Resampling.NEAREST).load()
                ring = [(x, y) for x in range(w) for y in range(h) if min(x, y, w - 1 - x, h - 1 - y) < max(1, w // 16)]
                same = sum(px[x, y][:3] == bpx[x, y][:3] for x, y in ring) / len(ring)
                out.append(("[16] 礦石外圍保留原石", "✅" if same >= 0.85 else "⚠️",
                            f"最外圈 {same * 100:.0f}% 和原石相同（建議 ≥ 85%，平鋪時才不會露出礦石接縫）"))
                ore = {(x, y) for x in range(w) for y in range(h) if px[x, y][:3] != bpx[x, y][:3]}
                # 陰影像素本身也和原石不同色（算在變更區域裡），所以看每一欄變更區域的最下緣那格是否比原石暗
                bottom = [(x, y) for x, y in ore if (x, y + 1) not in ore]
                darker = sum(lum(x, y) < luminance(*bpx[x, y][:3]) - 0.01 for x, y in bottom) / max(1, len(bottom))
                out.append(("[17] 礦簇下方 1 px 陰影", "✅" if darker >= 0.5 else "⚠️",
                            f"礦簇最下緣 {darker * 100:.0f}% 的像素比原石暗（建議 ≥ 50%，讓礦物嵌在岩石裡）"))

        # [18] 表面微紋理與色階過渡檢核（反 AI 平塗塑膠感 & 反跨階硬切斷層，以原版 26.3 十二張 Jappa 方塊校準）
        top_cnt = max((c for _, c in info["palette_sorted"]), default=0)
        top_share = top_cnt / max(1, info["total_opaque"])
        adj_pairs = 0
        diff_pairs = 0
        soft_pairs = 0
        max_adj_dlum = 0.0
        for yy in range(h):
            for xx in range(w):
                if not opaque(xx, yy):
                    continue
                c1 = px[xx, yy][:3]
                l1 = luminance(*c1)
                for dx, dy in ((1, 0), (0, 1)):
                    nx, ny = xx + dx, yy + dy
                    if opaque(nx, ny):
                        adj_pairs += 1
                        c2 = px[nx, ny][:3]
                        if c1 != c2:
                            diff_pairs += 1
                            dl = abs(l1 - luminance(*c2))
                            if dl > max_adj_dlum:
                                max_adj_dlum = dl
                            if dl < 0.10:
                                soft_pairs += 1
        edge_density = diff_pairs / max(1, adj_pairs)
        soft_ratio = soft_pairs / max(1, diff_pairs)
        flat_ok = top_share <= 0.55 and edge_density >= 0.45
        trans_ok = soft_ratio >= 0.20
        ok18 = flat_ok and trans_ok
        hints18: list[str] = []
        if not flat_ok:
            hints18.append("過於平滑／平塗塑膠感：請圍繞固有色增設 1~2 個 ΔLum≈0.03~0.06 微差副色打散單色死區")
        if not trans_ok:
            hints18.append("顏色缺少過渡／硬切貼紙感：請在深縫與亮面間補上 1 px 次暗／中間調緩衝色階")
        out.append((
            "[18] 表面微紋理與色階過渡",
            "✅" if ok18 else "⚠️",
            f"最大單色佔比 {top_share * 100:.0f}%（≤55%）、紋理變化率 {edge_density * 100:.0f}%（≥45%）、"
            f"柔和微過渡 {soft_ratio * 100:.0f}%（≥20%，最大單步 ΔLum={max_adj_dlum:.2f}）"
            + ("" if ok18 else " → " + "；".join(hints18)),
        ))
    return out


def print_advanced_report(results: list[tuple[str, str, str]]) -> None:
    print("🧭 [進階規則檢核 (Cotufa + Jappa 原版標準)]:")
    for name, status, note in results:
        print(f"  {name}: {status} {note}")
    print()


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
            f"Value Span: {info['lum_span']:.2f} | Orphans: {len(info['orphan_coords'])} | "
            f"Rule warnings: {sum(1 for _, st, _ in info.get('advanced', []) if st == '⚠️')}",
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
    parser.add_argument("--kind", "-k", choices=KINDS, default="auto",
                        help="材質類型，決定進階檢核的規則：auto（滿版=block、透空=item）、item、handheld（手持工具／武器）、"
                             "block、planks（木板）、bricks（磚）、chiseled（雕紋／金屬）、ore（礦石，搭配 --base）")
    parser.add_argument("--base", "-b", help="礦石比對用的原石貼圖（原版路徑如 block/stone.png 或本地檔案）")
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
        base_img = load_target_image(args.base, root, jar_path)[1] if args.base else None
        info["advanced"] = advanced_checks(info, args.kind, base_img)
        print_advanced_report(info["advanced"])
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
        print(f"🖼️ 已產生檢核視覺化對照圖: {rel_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
