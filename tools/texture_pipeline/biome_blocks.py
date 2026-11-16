"""Read-only: which (non-plant) blocks each biome of The Sift generates, as a comparison sheet + Markdown table.
Usage: python -I tools/texture_pipeline/biome_blocks.py <project> [<biome> ...]   (default: all biomes)
Sources: the material rule branch of the biome (surface / subsoil / path) and every feature in the biome's
feature steps except vegetation (step 9): mesas, ponds, boss arenas, crystals... Each block state is shown once
per biome with its role(s), a 3D preview (facing=up) and its top / side / bottom textures.
Writes build/texture_pipeline/out/biome_blocks.png and .md"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import project_paths, lj, entries, res_path

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
WG = D / "pysift/worldgen"
OUT = P / "build/texture_pipeline/out"
LANG = lj(A / "lang/zh_tw.json")
BIOMES = sys.argv[2:] or sorted(p.stem for p in (WG / "biome").glob("*.json"))
BIOME_ZH = {"crimson_strata_canyon": "赤紅沉積峽谷", "violet_slate_abyss": "紫晶深板岩區",
            "willow_grove": "柳絮林地", "amber_dunes": "琥珀沙丘"}
VEGETATION_STEP = 9


def state_key(s):
    """('pysift:x', {props}) from a block state written as a string or {"id"/"Name", "properties"/"Properties"}."""
    if isinstance(s, str):
        return s, {}
    return s.get("id") or s.get("Name"), dict(s.get("properties") or s.get("Properties") or {})


def collect_states(node, out, role):
    """Every pysift block state in a JSON tree (feature configs, providers, predicates are all walked)."""
    if isinstance(node, dict):
        if ("id" in node or "Name" in node) and str(node.get("id") or node.get("Name")).startswith("pysift:"):
            name, props = state_key(node)
            if (A / "blockstates" / f"{name.split(':')[1]}.json").exists():
                out.append((name, props, role))
        for k, v in node.items():
            if k == "target" or any(w in k for w in ("predicate", "replace", "can_place")):
                continue                                # conditions (what may be replaced), not generated blocks
            collect_states(v, out, role)
    elif isinstance(node, list):
        for v in node:
            collect_states(v, out, role)
    elif isinstance(node, str) and node.startswith("pysift:") and (A / "blockstates" / f"{node[7:]}.json").exists():
        out.append((node, {}, role))


def material_rule_blocks(biome):
    """[(block, props, role)] from the biome's branch of the material rule; role from the condition it sits under."""
    rule = lj(WG / "material_rule/the_sift.json")
    found = []

    def walk(n, ctx):
        if isinstance(n, dict):
            t = n.get("type", "")
            if t == "minecraft:condition":
                c = n["if_true"]
                ct = c.get("type", "")
                if ct == "minecraft:biome":
                    if c.get("biome_is") != f"pysift:{biome}":
                        return
                    ctx = ctx | {"in": True}
                elif ct == "minecraft:noise_threshold" and "path" in c.get("noise", ""):
                    ctx = ctx | {"role": "小路"}
                elif ct == "minecraft:on_floor" or c == "minecraft:on_floor":
                    ctx = ctx | {"role": ctx.get("role", "地表"), "below": True}
                elif ct == "minecraft:stone_depth":
                    if ctx.get("role") != "小路":
                        ctx = ctx | {"role": ("地表以下" if ctx.get("below") else "地表起") + f" {c.get('offset')} 格內"}
                    ctx = ctx | {"below": True}
                elif ct == "minecraft:noise_threshold":
                    ctx = ctx | {"role": (ctx.get("role") or "地表") + "（雜訊斑塊）"}
                walk(n["then_run"], ctx)
                return
            if t == "minecraft:block" and ctx.get("in"):
                name, props = state_key(n["result_state"])
                found.append((name, props, ctx.get("role", "地表")))
                return
            for v in n.values():
                walk(v, ctx)
        elif isinstance(n, list):
            for v in n:
                walk(v, ctx)
        elif n == "minecraft:on_floor":
            pass

    # conditions written as plain strings ("minecraft:on_floor") need the parent: handle by normalising first
    def norm(n):
        if isinstance(n, dict):
            if n.get("type") == "minecraft:condition" and isinstance(n.get("if_true"), str):
                n = dict(n, if_true={"type": n["if_true"]})
            return {k: norm(v) for k, v in n.items()}
        if isinstance(n, list):
            return [norm(v) for v in n]
        return n

    walk(norm(rule), {})
    return found


FEATURE_ROLE = {"spire": "圓台", "spirit_pond": "池塘邊壁", "boss_arena": "Boss 競技場", "soul_crystal": "靈魂晶塊"}


def feature_blocks(biome):
    found = []
    steps = lj(WG / f"biome/{biome}.json")["features"]
    for i, step in enumerate(steps):
        if i == VEGETATION_STEP:
            continue
        for ref in step:
            name = ref.split(":")[1]
            role = next((r for k, r in FEATURE_ROLE.items() if name.startswith(k)), name)
            placed = WG / f"placed_feature/{name}.json"
            feat_name = lj(placed)["feature"].split(":")[1] if placed.exists() else name
            feat = WG / f"feature/{feat_name}.json"
            if feat.exists():
                cfg = lj(feat)
                if role == "圓台":                      # split mesa roles by field
                    for field, sub in (("top", "圓台頂面"), ("body", "圓台主體"), ("band", "圓台色帶")):
                        if field in cfg:
                            collect_states(cfg[field], found, sub)
                elif role == "池塘邊壁":
                    collect_states(cfg.get("barrier"), found, role)
                else:
                    collect_states(cfg, found, role)
    return found


# ---------------- textures / preview (same drawing as related_blocks.py)
def model_textures(ref, depth=0):
    m = lj(res_path(ASSETS, ref, "models", ".json"))
    tex = dict(m.get("textures", {}))
    parent = m.get("parent", "")
    if parent.startswith("pysift:") and depth < 4:
        for k, v in model_textures(parent, depth + 1)[0].items():
            tex.setdefault(k, v)
    return tex, parent


def faces(tex):
    if "all" in tex:
        return tex["all"], tex["all"], tex["all"]
    if "end" in tex:
        return tex["end"], tex["side"], tex["end"]
    return tex.get("top"), tex.get("side"), tex.get("bottom")


def models_for(name, props):
    bs = lj(A / "blockstates" / f"{name.split(':')[1]}.json")
    if "multipart" in bs:                               # e.g. crystals / walls: first part is representative
        return [e["model"] for e in entries(bs["multipart"][0]["apply"])]
    var = bs.get("variants", {})
    want = {k: str(v) for k, v in props.items()} | {"facing": "up", "axis": "y"}
    for key, v in var.items():
        kv = dict(x.split("=", 1) for x in key.split(",") if x)
        if all(want.get(k, val) == val for k, val in kv.items()):
            return [e["model"] for e in entries(v)]
    first = next(iter(var.values()))
    return [e["model"] for e in entries(first)]


def load(ref):
    if not ref or ref.startswith("#"):
        return None
    return Image.open(res_path(ASSETS, ref, "textures", ".png")).convert("RGBA").crop((0, 0, 16, 16))


def perspective_coeffs(dst, src):
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


def shade(im, k):
    rgb = Image.eval(im.convert("RGB"), lambda v: int(v * k))
    rgb.putalpha(im.getchannel("A"))
    return rgb


def iso(top, side, size=56):
    h = size / 2
    W, H = size + 2, int(size * 1.15) + 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx = W / 2
    quads = (([(cx, 0), (W - 1, h / 2), (cx, h), (0, h / 2)], top, 1.0),
             ([(0, h / 2), (cx, h), (cx, H - 1), (0, H - 1 - h / 2)], side, 0.8),
             ([(cx, h), (W - 1, h / 2), (W - 1, H - 1 - h / 2), (cx, H - 1)], side, 0.62))
    for q, im, k in quads:
        warped = shade(im, k).transform((W, H), Image.Transform.PERSPECTIVE,
                                        perspective_coeffs(q, [(0, 0), (16, 0), (16, 16), (0, 16)]), Image.Resampling.NEAREST)
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).polygon(q, fill=255)
        img.paste(warped, (0, 0), mask)
    return img


def defaults(name):
    """Default state values (first variant key) so 'dark_slate' and 'dark_slate[fade=0]' count as one."""
    var = lj(A / "blockstates" / f"{name.split(':')[1]}.json").get("variants", {})
    first = next(iter(var), "")
    return dict(x.split("=", 1) for x in first.split(",") if x)


# ---------------- gather
sections = []
for biome in BIOMES:
    merged = {}
    for name, props, role in material_rule_blocks(biome) + feature_blocks(biome):
        if name == "pysift:spirit_liquid" or name.endswith("_wall"):
            continue                                    # fluid / walls: no cube textures to compare
        props = defaults(name) | {k: str(v) for k, v in props.items()}
        key = (name, tuple(sorted((k, v) for k, v in props.items() if k not in ("facing", "axis"))))
        merged.setdefault(key, [])
        if role not in merged[key]:
            merged[key].append(role)
    rows = []
    for (name, props), roles in merged.items():
        models = models_for(name, dict(props))
        tex, parent = model_textures(models[0])
        rows.append((name.split(":")[1], ",".join(f"{k}={v}" for k, v in props), roles, len(models),
                     parent.split("/")[-1], *faces(tex)))
    sections.append((biome, rows))

# ---------------- sheet
T, ROW_H = 64, 98
n_rows = sum(len(r) for _, r in sections)
img = Image.new("RGB", (1180, 30 + 40 * len(sections) + ROW_H * n_rows), (30, 30, 36))
d = ImageDraw.Draw(img)
try:
    from PIL import ImageFont
    CJK = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 13)
    CJK_BIG = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 18)
except OSError:
    CJK = CJK_BIG = None
d.text((8, 8), "block (state) / role          3D (facing=up)    top             side            bottom          variants / template",
       fill=(235, 235, 235))
y = 30
for biome, rows in sections:
    d.text((8, y + 8), f"{BIOME_ZH.get(biome, biome)}  {biome}", fill=(250, 210, 90), font=CJK_BIG)
    y += 40
    for b, label, roles, n, parent, top, side, bottom in rows:
        d.text((8, y + 2), (b + (f" [{label}]" if label else ""))[:44], fill=(230, 230, 230))
        d.text((8, y + 18), LANG.get(f"block.pysift.{b}", ""), fill=(170, 170, 180), font=CJK)
        d.text((8, y + 38), "、".join(roles)[:30], fill=(140, 220, 160), font=CJK)
        ti, si, bi = load(top), load(side), load(bottom)
        if ti and si:
            cube = iso(ti, si)
            img.paste(cube, (330, y), cube)
        for i, (im, ref) in enumerate(((ti, top), (si, side), (bi, bottom))):
            if im:
                big = im.resize((T, T), Image.Resampling.NEAREST)
                img.paste(big, (460 + i * 160, y), big)
                d.text((460 + i * 160, y + T + 2), (ref or "").split("/")[-1][:24], fill=(190, 190, 200))
        d.text((940, y + 4), f"{n} model(s)", fill=(200, 200, 210))
        d.text((940, y + 20), parent[:30], fill=(150, 150, 160))
        y += ROW_H
OUT.mkdir(parents=True, exist_ok=True)
img.save(OUT / "biome_blocks.png")

md = []
for biome, rows in sections:
    md += [f"## {BIOME_ZH.get(biome, biome)}（`{biome}`）", "",
           "| 用途 | 方塊 ID | 中文名 | 狀態 | 頂面 | 側面 | 底面 |", "| :-- | :-- | :-- | :-- | :-- | :-- | :-- |"]
    short = lambda r: (r or "-").split("/")[-1]
    for b, label, roles, n, parent, top, side, bottom in rows:
        md.append(f"| {'、'.join(roles)} | `{b}` | {LANG.get(f'block.pysift.{b}', '')} | {label or '-'} | "
                  f"{short(top)} | {short(side)} | {short(bottom)} |")
    md.append("")
(OUT / "biome_blocks.md").write_text("\n".join(md), encoding="utf-8")
print(f"{n_rows} rows in {len(sections)} biomes -> biome_blocks.png / .md")
