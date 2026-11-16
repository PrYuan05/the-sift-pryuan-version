"""Before/after table of every PNG the pipeline changed or generated (from recolor_manifest.json).
Usage: python -I tools/texture_pipeline/changes_report.py <project>
Writes build/texture_pipeline/out/texture_changes.png and tools/texture_pipeline/TEXTURE_CHANGES.md."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import project_paths, lj, res_path

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
HERE = Path(__file__).resolve().parent
OUT = P / "build/texture_pipeline/out"
entries = lj(HERE / "recolor_manifest.json")["entries"]


def ref_image(ref):
    """'pysift:block/x/y' or 'top band of pysift:block/x/y (vflip)' -> image of that texture."""
    r = ref.split(" of ")[-1].split(" (")[0]
    p = res_path(ASSETS, r, "textures", ".png")
    return Image.open(p).convert("RGB") if p.exists() else None


groups = {}
for e in entries:
    groups.setdefault(e["pool"], []).append(e)

tile, PAD = 64, 6
cols_per_group = lambda es: 1 + 2 * len(es)
width = 260 + max(cols_per_group(es) for es in groups.values()) * (tile + PAD) + 80
img = Image.new("RGB", (width, 30 + len(groups) * (tile + 34)), (28, 28, 32))
dr = ImageDraw.Draw(img)
dr.text((6, 6), "pool | reference (recolour) or side (generated) | each texture: before -> after", fill=(235, 235, 235))
y = 28
md = ["# 貼圖變更對照表", "",
      "由 `changes_report.py` 依 `recolor_manifest.json` 產生。recolor = 依參考貼圖的調色盤改色（原檔備份在 `backup` 欄位）；"
      "generated = 新產生的頂面／底面貼圖（由 `source` 依側面帶的顏色改色而成，原檔不變）。", "",
      "| 池 / 面 | 檔案 | 模式 | 參考 | 來源（generated） | 備份 | 日期 |", "| :-- | :-- | :-- | :-- | :-- | :-- | :-- |"]
for pool, es in groups.items():
    dr.text((6, y + tile // 2 - 6), pool[:36], fill=(250, 210, 90))
    x = 260
    ref = ref_image(es[0]["reference"])
    if ref:
        img.paste(ref.resize((tile, tile), Image.Resampling.NEAREST), (x, y))
        dr.text((x, y + tile + 2), "ref" if es[0]["mode"] != "generated" else "side", fill=(120, 230, 140))
    x += tile + PAD * 3
    for e in es:
        if e["mode"] == "generated":
            before = Image.open(res_path(ASSETS, e["source"], "textures", ".png")).convert("RGB")
            blabel = "src " + e["source"].rsplit("_", 1)[1]
        elif e.get("backup"):
            before = Image.open(P / e["backup"]).convert("RGB")
            blabel = Path(e["file"]).stem.rsplit("_", 1)[1]
        else:  # recoloured when first created: no earlier version to show
            before = Image.open(A / e["file"]).convert("RGB")
            blabel = "new file"
        after = Image.open(A / e["file"]).convert("RGB")
        for im, lab in ((before, blabel), (after, "after")):
            img.paste(im.resize((tile, tile), Image.Resampling.NEAREST), (x, y))
            dr.text((x, y + tile + 2), lab[:12], fill=(215, 215, 215))
            x += tile + PAD
        x += PAD * 2
        md.append(f"| `{pool}` | `{e['file']}` | {e['mode']}{'/' + e['method'] if e.get('method') else ''} | "
                  f"`{e['reference']}` | {('`' + e['source'] + '`') if e.get('source') else '-'} | "
                  f"{('`' + e['backup'] + '`') if e.get('backup') else '-'} | {e['date']} |")
    y += tile + 34
OUT.mkdir(parents=True, exist_ok=True)
img.save(OUT / "texture_changes.png")
(HERE / "TEXTURE_CHANGES.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"{len(entries)} files in {len(groups)} groups -> texture_changes.png, TEXTURE_CHANGES.md")
