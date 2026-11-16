"""Move block textures / models into the folder of the block that uses them, rewriting every reference.
Usage: python -I tools/texture_pipeline/move_assets.py <project> [--apply]
Input: build/texture_pipeline/move_plan.json = [(kind, "block/<old folder>/<name>", "block/<new folder>/<name>")],
made from asset_usage.py's "misplaced" list (only files used by ONE block family, nothing shared, nothing another
session has uncommitted changes in).

A texture and a model can have the same path ("block/dark_slate/dark_slate_i" is both) while only one of them moves, so
references are rewritten by context:
  - resource JSON under assets/: "model" / "parent" values use the model map, every other string (textures, sprites)
    the texture map
  - every other text file (Java, tools, manifests, hashes): "textures/block/X.png" and "models/block/X.json" paths, and
    the bare id "pysift:block/X" / "block/X" only where X moves the same way as a model and as a texture (or only one
    of the two exists)
"""
import json, re, shutil, sys
from pathlib import Path

P = Path(sys.argv[1]).resolve()
APPLY = "--apply" in sys.argv
A = P / "src/main/resources/assets/pysift"
plan = json.loads((P / "build/texture_pipeline/move_plan.json").read_text(encoding="utf-8"))
TEX = {old: new for kind, old, new in plan if kind == "textures"}
MOD = {old: new for kind, old, new in plan if kind == "models"}
TEX_EXISTS = {p.relative_to(A / "textures").with_suffix("").as_posix() for p in (A / "textures/block").rglob("*.png")}
MOD_EXISTS = {p.relative_to(A / "models").with_suffix("").as_posix() for p in (A / "models/block").rglob("*.json")}
# a bare id is safe to rewrite when it moves identically for both kinds, or the other kind does not exist
BARE = {}
for old in set(TEX) | set(MOD):
    t, m = TEX.get(old), MOD.get(old)
    if (t and m and t == m) or (t and old not in MOD_EXISTS) or (m and old not in TEX_EXISTS):
        BARE[old] = t or m


def ref_sub(value, mapping):
    if not isinstance(value, str):
        return value
    ns, _, path = value.partition(":") if ":" in value else ("pysift", "", value)
    if ns == "pysift" and path in mapping:
        return ("pysift:" if ":" in value else "") + mapping[path]
    return value


def walk(obj, key=None):
    if isinstance(obj, dict):
        return {k: walk(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [walk(v, key) for v in obj]
    if isinstance(obj, str):
        return ref_sub(obj, MOD if key in ("model", "parent") else TEX)
    return obj


def text_sub(t):
    for old, new in TEX.items():
        t = t.replace(f"textures/{old}.png", f"textures/{new}.png")
    for old, new in MOD.items():
        t = t.replace(f"models/{old}.json", f"models/{new}.json")
    for old, new in BARE.items():
        t = re.sub(rf'(?<![a-z0-9_/]){re.escape(old)}(?![a-z0-9_/])', new, t)
    return t


def main():
    changed = []
    for f in (P / "src").rglob("*.json"):
        if A in f.parents and f.parent.name != "lang":
            d = json.loads(f.read_text(encoding="utf-8-sig"))
            nd = walk(d)
            if nd != d:
                changed.append(f)
                if APPLY:
                    f.write_text(json.dumps(nd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for root in (P / "src", P / "tools"):
        for f in root.rglob("*"):
            if not f.is_file() or f.suffix not in (".java", ".py", ".json", ".md") or (A in f.parents and f.suffix == ".json"):
                continue
            if f.resolve() == Path(__file__).resolve():
                continue
            t = f.read_text(encoding="utf-8", errors="ignore")
            lines = t.split("\n")
            nt = "\n".join(l if ".texture_backups" in l else text_sub(l) for l in lines)
            if nt != t:
                changed.append(f)
                if APPLY:
                    f.write_text(nt, encoding="utf-8")
    moved = []
    for kind, old, new in plan:
        ext = ".png" if kind == "textures" else ".json"
        src, dst = A / kind / f"{old}{ext}", A / kind / f"{new}{ext}"
        assert src.exists(), src
        assert not dst.exists(), f"{dst} already exists"
        moved.append((src, dst))
        if APPLY:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dst)
            meta = src.with_suffix(".png.mcmeta")
            if meta.exists():
                shutil.move(meta, dst.with_suffix(".png.mcmeta"))
    if APPLY:                                               # drop folders the moves emptied
        for kind in ("textures", "models"):
            for d in sorted((A / kind / "block").rglob("*"), key=lambda p: len(p.parts), reverse=True):
                if d.is_dir() and not any(d.iterdir()):
                    d.rmdir()
    print(f"{'moved' if APPLY else 'would move'} {len(moved)} files; references rewritten in {len(changed)} files")
    for f in changed:
        if A not in f.parents:
            print("  ", f.relative_to(P))


if __name__ == "__main__":
    main()
