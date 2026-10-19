"""Read-only: comparison sheet + table of every block related to the given blocks.
Usage: python -I tools/texture_pipeline/related_blocks.py <project> <block> [<block> ...]
Related = the given blocks, blocks in the same name family (crimson_capped_* / *crimson_strata*), and blocks whose
models use any texture the given blocks use. For each block (and each blockstate value that changes the textures)
the sheet shows a 3D preview (facing=up) and its top / side / bottom textures; the table (Markdown) adds the relation,
the zh_tw name and where The Sift's worldgen uses it.
Writes build/texture_pipeline/out/related_<first block>.png and .md"""
import json, re, sys
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import project_paths, lj, entries, res_path

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
TARGETS = sys.argv[2:]
OUT = P / "build/texture_pipeline/out"
LANG = lj(A / "lang/zh_tw.json")


def model_textures(ref, depth=0):
    m = lj(res_path(ASSETS, ref, "models", ".json"))
    tex = dict(m.get("textures", {}))
    parent = m.get("parent", "")
    if parent.startswith("pysift:") and depth < 4:
        for k, v in model_textures(parent, depth + 1)[0].items():
            tex.setdefault(k, v)
    return tex, parent


def faces(tex):
    """(top, side, bottom) texture refs for cube_all / cube_bottom_top / column style models."""
    if "all" in tex:
        return tex["all"], tex["all"], tex["all"]
    if "end" in tex:
        return tex["end"], tex["side"], tex["end"]
    return tex.get("top"), tex.get("side"), tex.get("bottom")


def states(block):
    """[(state label, [model refs])] for facing=up / axis=y (or the only orientation), one per texture-relevant state."""
    var = lj(A / "blockstates" / f"{block}.json").get("variants", {})
    out = []
    for key, v in var.items():
        kv = dict(x.split("=", 1) for x in key.split(",") if x)
        if kv.get("facing", "up") != "up" or kv.get("axis", "y") != "y":
            continue
        label = ",".join(f"{k}={v2}" for k, v2 in kv.items() if k not in ("facing", "axis"))
        out.append((label, [e["model"] for e in entries(v)]))
    return out


def all_textures(block):
    refs = set()
    for _, models in states(block):
        for m in models:
            refs |= {t for t in model_textures(m)[0].values() if t.startswith("pysift:")}
    return refs


blocks = sorted(p.stem for p in (A / "blockstates").glob("*.json"))
target_tex = set().union(*(all_textures(b) for b in TARGETS))
if "crimson_capped_crimson_strata_2" in TARGETS:
    target_tex.add("pysift:block/ember_stone/ember_stone_heat2_a")
    target_tex.add("pysift:block/ember_stone/ember_stone_heat0_a")
if "crimson_capped_crimson_strata_3" in TARGETS:
    target_tex.add("pysift:block/crimson_vein_stone/crimson_vein_stone_crimson_spread4")
family = re.compile(r"crimson_capped_|crimson_strata")
related = {}
for b in blocks:
    if b.endswith(("_slab", "_stairs", "_wall")) or "brick" in b:
        continue
    reasons = []
    if b in TARGETS:
        reasons.append("目標")
    if family.search(b):
        reasons.append("同系列名稱")
    try:
        shared = all_textures(b) & target_tex
    except Exception:
        continue
    if shared and b not in TARGETS:
        reasons.append("共用貼圖：" + "、".join(sorted(t.split("/")[-1] for t in shared)))
    if reasons:
        related[b] = reasons
order = TARGETS + sorted(b for b in related if b not in TARGETS)

# where worldgen uses each block
wg_text = {p.relative_to(D).as_posix(): p.read_text(encoding="utf-8") for p in (D / "pysift/worldgen").rglob("*.json")}


def worldgen_use(b):
    hits = sorted({k.split("/")[2] + ":" + Path(k).stem for k, t in wg_text.items() if f'"pysift:{b}"' in t})
    return "、".join(hits) if hits else "-"


# ---------------- sheet
def load(ref):
    return Image.open(res_path(ASSETS, ref, "textures", ".png")).convert("RGBA").crop((0, 0, 16, 16)) if ref else None


def perspective_coeffs(dst, src):
    """Coefficients mapping output (dst) points to input (src) points for Image.transform(PERSPECTIVE)."""
    m = []
    for (x, y), (u, v) in zip(dst, src):
        m.append([x, y, 1, 0, 0, 0, -u * x, -u * y, u])
        m.append([0, 0, 0, x, y, 1, -v * x, -v * y, v])
    for col in range(8):
        piv = max(range(col, 8), key=lambda r: abs(m[r][col]))
        m[col], m[piv] = m[piv], m[col]
        for r in range(8):
            if r != col:
                f = m[r][col] / m[col][col]
                m[r] = [a - f * b for a, b in zip(m[r], m[col])]
    return [m[i][8] / m[i][i] for i in range(8)]


def iso(top, side, size=56):
    """Small 3D cube: top face plus the two front sides (shaded), 16px textures."""
    h = size / 2
    W, H = size + 2, int(size * 1.15) + 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    c = (W / 2, h / 2)                                  # centre of the top face
    top_q = [(c[0], 0), (W - 1, h / 2), (c[0], h), (0, h / 2)]
    left_q = [(0, h / 2), (c[0], h), (c[0], H - 1), (0, H - 1 - h / 2)]
    right_q = [(c[0], h), (W - 1, h / 2), (W - 1, H - 1 - h / 2), (c[0], H - 1)]
    for im, q, k in ((top, top_q, 1.0), (side, left_q, 0.8), (side, right_q, 0.62)):
        src = [(0, 0), (16, 0), (16, 16), (0, 16)]
        warped = shade(im, k).transform((W, H), Image.Transform.PERSPECTIVE, perspective_coeffs(q, src), Image.Resampling.NEAREST)
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).polygon(q, fill=255)
        img.paste(warped, (0, 0), mask)
    return img


def shade(im, k):
    rgb = Image.eval(im.convert("RGB"), lambda v: int(v * k))
    rgb.putalpha(im.getchannel("A"))
    return rgb


rows = []
for b in order:
    for label, models in states(b):
        tex, parent = model_textures(models[0])
        top, side, bottom = faces(tex)
        rows.append((b, label, len(models), parent.split("/")[-1], top, side, bottom))

T = 64
ROW_H = T + 34
img = Image.new("RGB", (1140, 34 + ROW_H * len(rows)), (30, 30, 36))
d = ImageDraw.Draw(img)
try:                                                    # CJK-capable font for the zh_tw names (Windows)
    from PIL import ImageFont
    CJK = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
except OSError:
    CJK = None
d.text((8, 8), "block (state)            3D (facing=up)   top            side           bottom        variants / template",
       fill=(235, 235, 235))
y = 30
for b, label, n, parent, top, side, bottom in rows:
    mark = b in TARGETS
    if mark:
        d.rectangle([2, y - 2, img.width - 3, y + ROW_H - 6], outline=(250, 200, 80))
    name = b + (f" [{label}]" if label else "")
    d.text((8, y + 4), name[:40], fill=(250, 210, 90) if mark else (225, 225, 225))
    d.text((8, y + 18), LANG.get(f"block.pysift.{b}", "")[:20], fill=(170, 170, 180), font=CJK)
    ti, si, bi = load(top), load(side), load(bottom)
    if ti and si:
        cube = iso(ti, si)
        img.paste(cube, (300, y), cube)
    for i, (im, ref) in enumerate(((ti, top), (si, side), (bi, bottom))):
        x = 430 + i * 150
        if im:
            img.paste(im.resize((T, T), Image.Resampling.NEAREST), (x, y), im.resize((T, T), Image.Resampling.NEAREST))
            d.text((x, y + T + 2), (ref or "").split("/")[-1][:22], fill=(190, 190, 200))
    d.text((890, y + 4), f"{n} model(s)", fill=(200, 200, 210))
    d.text((890, y + 20), parent[:30], fill=(150, 150, 160))
    y += ROW_H
OUT.mkdir(parents=True, exist_ok=True)
img.save(OUT / f"related_{TARGETS[0]}.png")

md = ["| 方塊 ID | 中文名 | 狀態 | 頂面 | 側面 | 底面 | 關係 | 世界生成使用 |", "| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |"]
for b, label, n, parent, top, side, bottom in rows:
    short = lambda r: (r or "-").split("/")[-1]
    md.append(f"| `{b}` | {LANG.get(f'block.pysift.{b}', '')} | {label or '-'} | {short(top)} | {short(side)} | {short(bottom)} | "
              f"{'；'.join(related[b])} | {worldgen_use(b)} |")
(OUT / f"related_{TARGETS[0]}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"{len(rows)} rows from {len(order)} blocks -> related_{TARGETS[0]}.png / .md")
