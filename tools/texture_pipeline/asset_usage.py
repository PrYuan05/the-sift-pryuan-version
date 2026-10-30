"""Where is every block texture / block model actually used? (read-only report)
Usage: python -I tools/texture_pipeline/asset_usage.py <project>
Writes art_requests/asset_usage_report.md and build/texture_pipeline/asset_usage.json.

Usage graph: blockstates -> models (+ parent chain) -> textures, items/*.json and models/item -> models, plus any literal
"pysift:block/..." or "block/..." reference in Java / other JSON under src (fluids, renderers, particles, atlases).
For every textures/block/<folder>/<file>.png and models/block/<folder>/<file>.json:
  unused     - nothing in src references it
  misplaced  - every user is a block other than <folder> (it lives in another block's folder)
  shared     - used by <folder>'s block and by other blocks
  home       - used only by <folder>'s block (or its slab / stairs / wall / item)
Files with uncommitted changes from someone else are flagged, so a cleanup can leave them alone.
"""
import json, re, subprocess, sys
from collections import defaultdict
from pathlib import Path

P = Path(sys.argv[1]).resolve()
SRC = P / "src"
A = P / "src/main/resources/assets/pysift"


def lj(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def rid(ref, kind):
    """'pysift:block/x/y' (or 'block/x/y') -> relative path under assets/pysift/<kind>/."""
    if not isinstance(ref, str) or ref.startswith("#"):
        return None
    ns, _, path = ref.partition(":") if ":" in ref else ("pysift", "", ref)
    return f"{path}" if ns == "pysift" else None


def owner_of(block):
    """slab / stairs / wall / inventory forms belong to their base block's family."""
    return block


model_users = defaultdict(set)      # models/<path> -> blocks / items
tex_users = defaultdict(set)


def walk_model(path, user, seen=None):
    seen = seen or set()
    if path in seen:
        return
    seen.add(path)
    model_users[path].add(user)
    f = A / "models" / f"{path}.json"
    if not f.exists():
        return
    m = lj(f)
    parent = rid(m.get("parent"), "models")
    if parent:
        walk_model(parent, user, seen)
    for v in (m.get("textures") or {}).values():
        t = rid(v, "textures")
        if t:
            tex_users[t].add(user)


def models_in(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "model" and isinstance(v, str):
                yield v
            else:
                yield from models_in(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from models_in(v)


for bs in (A / "blockstates").glob("*.json"):
    for m in models_in(lj(bs)):
        p = rid(m, "models")
        if p:
            walk_model(p, bs.stem)
for it in (A / "items").glob("*.json"):
    for m in models_in(lj(it)):
        p = rid(m, "models")
        if p:
            walk_model(p, "item:" + it.stem)
for mi in (A / "models/item").rglob("*.json"):
    walk_model(f"item/{mi.relative_to(A / 'models/item').with_suffix('').as_posix()}", "item:" + mi.stem)

# literal references anywhere else in src (Java, particles, atlases, fluids ...)
text = []
for f in SRC.rglob("*"):
    if f.suffix in (".java", ".json") and "/blockstates/" not in f.as_posix() and "/models/" not in f.as_posix():
        text.append((f, f.read_text(encoding="utf-8", errors="ignore")))
literal = defaultdict(set)
for f, t in text:
    for m in re.finditer(r'"(?:pysift:)?(block/[a-z0-9_/]+)"', t):
        literal[m[1]].add(f.relative_to(P).as_posix())
    for m in re.finditer(r'id\("(block/[a-z0-9_/]+)"\)', t):
        literal[m[1]].add(f.relative_to(P).as_posix())

dirty = set()
for line in subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=P, capture_output=True, text=True,
                           encoding="utf-8").stdout.splitlines():
    dirty.add(line[3:].strip('"'))


BLOCK_IDS = {f.stem for f in (A / "blockstates").glob("*.json")}


def classify(rel, users, folder):
    blocks = {u.replace("item:", "") for u in users}
    if not users:
        return "unused"
    if folder and folder not in BLOCK_IDS and folder.replace("_bricks", "") not in BLOCK_IDS:
        return "category"                    # sift_colors, sift_ground, templates, vegetation ...: not a block's folder
    def core(b):                             # family core of a block id: forms and prefixes stripped
        b = re.sub(r"_(slab|stairs|wall|brick_slab|brick_stairs|brick_wall|tile_slab|tile_stairs|tile_wall)$", "", b)
        b = re.sub(r"^(chiseled|cracked|polished|smooth|cut)_", "", b)
        return re.sub(r"_(bricks|brick|tiles|tile)$", "", b)
    home = core(folder)

    def mine(b):
        return core(b) == home
    if any(mine(b) for b in blocks):
        return "home" if all(mine(b) for b in blocks) else "shared"
    return "misplaced"


report = {"textures": {}, "models": {}}
for png in sorted((A / "textures/block").rglob("*.png")):
    rel = png.relative_to(A / "textures").with_suffix("").as_posix()          # block/<folder>/<name>
    parts = rel.split("/")
    folder = parts[1] if len(parts) > 2 else parts[1]
    users = set(tex_users.get(rel, set())) | {"src:" + x for x in literal.get(rel, set())}
    report["textures"][rel] = {"users": sorted(users), "class": classify(rel, {u for u in users if not u.startswith("src:")}
                                                                          or ({"<code>"} if users else set()), folder if len(parts) > 2 else ""),
                               "dirty": f"src/main/resources/assets/pysift/textures/{rel}.png" in dirty}
for mj in sorted((A / "models/block").rglob("*.json")):
    rel = mj.relative_to(A / "models").with_suffix("").as_posix()
    parts = rel.split("/")
    folder = parts[1] if len(parts) > 2 else re.sub(r"_(slab_top|slab|stairs_inner|stairs_outer|stairs|wall_post|wall_side_tall|wall_side|wall_inventory|double)$", "", parts[1])
    users = set(model_users.get(rel, set())) | {"src:" + x for x in literal.get(rel, set())}
    report["models"][rel] = {"users": sorted(users), "class": classify(rel, {u for u in users if not u.startswith("src:")}
                                                                      or ({"<code>"} if users else set()), folder),
                             "dirty": f"src/main/resources/assets/pysift/models/{rel}.json" in dirty}

out = P / "build/texture_pipeline/asset_usage.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

L = ["# 方塊貼圖與模型使用清查", "", "由 `tools/texture_pipeline/asset_usage.py` 產生（唯讀，不改任何檔案）。"
     "追蹤路徑：方塊狀態 → 模型（含父模型）→ 貼圖；物品定義與物品模型；以及 Java／其他 JSON 裡直接寫的 `block/...` 路徑。", "",
     "- **未使用**：src 裡沒有任何地方引用。",
     "- **放錯資料夾**：用到它的方塊全都不是資料夾名稱那個方塊。",
     "- **共用**：資料夾自己的方塊和別的方塊都在用。",
     "- **分類資料夾**：資料夾不是某個方塊的名字（sift_colors、sift_ground、templates…），不判斷。",
     "- ✏️＝這個檔案目前有其他作業未提交的修改（整理時先不動）。", ""]
for kind, label in (("textures", "貼圖"), ("models", "模型")):
    rows = report[kind]
    counts = defaultdict(int)
    for v in rows.values():
        counts[v["class"]] += 1
    L += [f"## {label}（共 {len(rows)}）", "",
          f"未使用 {counts['unused']}｜放錯資料夾 {counts['misplaced']}｜共用 {counts['shared']}｜正常 {counts['home']}｜分類資料夾 {counts['category']}", ""]
    for cls, title in (("unused", "未使用"), ("misplaced", "放錯資料夾"), ("shared", "共用")):
        items = [(k, v) for k, v in rows.items() if v["class"] == cls]
        if not items:
            continue
        L += [f"### {label}：{title}（{len(items)}）", "", "| 檔案 | 使用者 |", "| :-- | :-- |"]
        for k, v in items:
            users = "、".join(f"`{u}`" for u in v["users"][:8]) + (f" 等 {len(v['users'])} 個" if len(v["users"]) > 8 else "")
            L.append(f"| `{k}`{' ✏️' if v['dirty'] else ''} | {users or '—'} |")
        L.append("")
(P / "art_requests/asset_usage_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
for kind in ("textures", "models"):
    c = defaultdict(int)
    for v in report[kind].values():
        c[v["class"]] += 1
    print(kind, dict(c))
