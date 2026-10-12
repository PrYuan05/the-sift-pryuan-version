"""Unify the colour tone of incoherent random pools / stages by remapping textures onto a reference palette.

  python -I tools/texture_pipeline/recolor.py <project> scan
      read-only: find pools whose palette distance > COHERENCE_TH, pick a reference (medoid unless overridden),
      preview the remap -> build/texture_pipeline/out/recolor_plan.json + recolor_review.png
  python -I tools/texture_pipeline/recolor.py <project> apply [block[:state] ...]
      apply recolor_plan.json (optionally only the listed pools); backs up to .texture_backups/, logs the manifest
  python -I tools/texture_pipeline/recolor.py <project> revert <block[:state]|all>
      restore files from their backups and drop them from the manifest
  python -I tools/texture_pipeline/recolor.py <project> record <block:state> <reference-texture-name> <backup-dir>
      log a recolor that was done before this tool existed

User decisions live in recolor_overrides.json (exclude pools, pick references, skip targets, allow shared textures).
Mode "palette": stretch the source brightness range onto the reference's and take the reference colour with the
nearest brightness; transparent pixels are kept. Shapes never change, only colours."""
import sys, json, shutil, datetime
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import (project_paths, lj, wj, entries, res_path, sha1, Tex, pdist, palette, COHERENCE_TH,
                         iter_pools, cube_all_texture)

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
HERE = Path(__file__).resolve().parent
OUT = P / "build/texture_pipeline/out"
MANIFEST = HERE / "recolor_manifest.json"
OVERRIDES = HERE / "recolor_overrides.json"
PLAN = OUT / "recolor_plan.json"


def lum(c): return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def remap(src_img, ref_img):
    """Palette mode: brightness-rank remap of src onto the reference palette."""
    ref_cols = sorted({c for c in ref_img.convert("RGBA").getdata() if c[3] > 0}, key=lum)
    rl = [lum(c) for c in ref_cols]
    src = src_img.convert("RGBA")
    px = list(src.getdata())
    ls = [lum(c) for c in px if c[3] > 0]
    lo, hi = min(ls), max(ls)

    def one(c):
        if c[3] == 0:
            return c
        t = (lum(c) - lo) / (hi - lo) if hi > lo else 0.5
        target = rl[0] + t * (rl[-1] - rl[0])
        r = min(ref_cols, key=lambda rc: abs(lum(rc) - target))
        return (r[0], r[1], r[2], c[3])
    out = Image.new("RGBA", src.size)
    out.putdata([one(c) for c in px])
    return out


def pool_id(block, state): return f"{block}:{state}" if state else block


def matches(selector, block, state):
    if selector == "all":
        return True
    b, _, s = selector.partition(":")
    return b == block and (not s or s == state)


def load_manifest(): return lj(MANIFEST) if MANIFEST.exists() else {"entries": []}


def texture_usage():
    """texture ref -> set of (block, state, model, face) for every blockstate-referenced model."""
    use = {}
    for block, state, models in iter_pools(A):
        for m in models:
            for face, t in lj(res_path(ASSETS, m, "models", ".json")).get("textures", {}).items():
                use.setdefault(t, set()).add((block, state, m, face))
    return use


def scan():
    ov = lj(OVERRIDES) if OVERRIDES.exists() else {}
    exclude, refs = set(ov.get("exclude", [])), ov.get("reference", {})
    skip_targets, allow_shared = ov.get("skip_targets", {}), set(ov.get("allow_shared", []))
    usage = texture_usage()
    cache = {}
    tex = lambda r: cache.setdefault(r, Tex(r, ASSETS))
    plan = []
    for block, state, models in iter_pools(A):
        pid = pool_id(block, state)
        refs_in_pool = [t for t in (cube_all_texture(ASSETS, m) for m in models) if t]
        if len(set(refs_in_pool)) < 2 or any(matches(x, block, state) for x in exclude):
            continue
        texs = [tex(r) for r in dict.fromkeys(refs_in_pool)]
        worst = max(pdist(a.pal, b.pal) for a in texs for b in texs)
        if worst <= COHERENCE_TH:
            continue
        chosen = next((v for k, v in refs.items() if matches(k, block, state)), None)
        if chosen:
            ref = next(t for t in texs if t.name == chosen)
        else:  # medoid: smallest mean distance to the rest of the pool
            ref = min(texs, key=lambda t: sum(pdist(t.pal, o.pal) for o in texs if o is not t))
        pool_models = set(models)
        targets = []
        for t in texs:
            if t is ref:
                continue
            others = sorted({f"{b}[{s or '-'}] {f}" for b, s, m, f in usage.get(t.ref, ()) if m not in pool_models})
            skip = None
            if t.name in skip_targets.get(pid, []):
                skip = "user"
            elif others and t.ref not in allow_shared and t.name not in allow_shared:
                skip = "shared"
            after = remap(t.image, ref.image)
            targets.append({"texture": t.ref, "name": t.name, "skip": skip, "shared_with": others,
                            "dist_before": round(pdist(t.pal, ref.pal), 1),
                            "dist_after": round(pdist(palette(list(after.convert("RGB").getdata())), ref.pal), 1)})
        plan.append({"pool": pid, "block": block, "state": state, "max_dist": round(worst, 1), "mode": "palette",
                     "reference": ref.ref, "reference_auto": not chosen, "targets": targets})
    OUT.mkdir(parents=True, exist_ok=True)
    wj(PLAN, {"generated": datetime.datetime.now().isoformat(timespec="seconds"), "pools": plan})
    review(plan, tex)
    for p in plan:
        print(f"{p['pool']:32s} max {p['max_dist']:5.1f}  ref={p['reference'].rsplit('/', 1)[1]}{' (auto)' if p['reference_auto'] else ''}  "
              + ", ".join(f"{t['name'].rsplit('_', 1)[1]}{'[skip:' + t['skip'] + ']' if t['skip'] else ''} {t['dist_before']}->{t['dist_after']}" for t in p["targets"]))
    if not plan:
        print("all pools are coherent")


def review(plan, tex):
    S, PAD = 6, 6
    tile = 16 * S
    width = 230 + (tile + PAD * 3) + max([len(p["targets"]) for p in plan] + [1]) * (2 * (tile + PAD) + PAD * 2) + PAD
    height = 24 + len(plan) * (tile + 34)
    img = Image.new("RGB", (width, max(height, 60)), (28, 28, 32))
    dr = ImageDraw.Draw(img)
    dr.text((PAD, 4), "pool | * reference | each target: before, after   (red frame = skipped)", fill=(235, 235, 235))
    y = 24
    for p in plan:
        dr.text((PAD, y + tile // 2 - 6), p["pool"][:34], fill=(250, 210, 90))
        x = 230
        ref = tex(p["reference"])
        img.paste(ref.image.resize((tile, tile), Image.Resampling.NEAREST), (x, y))
        dr.text((x, y + tile + 2), "* " + ref.name.rsplit("_", 1)[1], fill=(120, 230, 140))
        x += tile + PAD * 3
        for t in p["targets"]:
            src = tex(t["texture"])
            for img_, label in ((src.image, t["name"].rsplit("_", 1)[1]), (remap(src.image, ref.image).convert("RGB"), "after")):
                img.paste(img_.resize((tile, tile), Image.Resampling.NEAREST), (x, y))
                if t["skip"]:
                    dr.rectangle([x, y, x + tile - 1, y + tile - 1], outline=(230, 60, 60), width=3)
                dr.text((x, y + tile + 2), label, fill=(220, 220, 220))
                x += tile + PAD
            x += PAD * 2
        y += tile + 34
    img.save(OUT / "recolor_review.png")


def apply(selectors):
    plan = lj(PLAN)["pools"]
    man = load_manifest()
    by_file = {e["file"]: e for e in man["entries"]}
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = P / ".texture_backups" / f"{stamp}_recolor"
    done = []
    for p in plan:
        if selectors and not any(matches(s, p["block"], p["state"]) for s in selectors):
            continue
        ref_img = Image.open(res_path(ASSETS, p["reference"], "textures", ".png"))
        for t in p["targets"]:
            if t["skip"]:
                continue
            path = res_path(ASSETS, t["texture"], "textures", ".png")
            rel = path.relative_to(A).as_posix()
            backup = bdir / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
            before = sha1(path)
            remap(Image.open(path), ref_img).save(path)
            prev = by_file.get(rel)
            entry = {"file": rel, "pool": p["pool"], "reference": p["reference"], "mode": p["mode"],
                     "sha1_before": prev["sha1_before"] if prev else before, "sha1_after": sha1(path),
                     "backup": (prev["backup"] if prev else backup.relative_to(P).as_posix()),
                     "date": stamp}
            by_file[rel] = entry
            done.append(rel)
    man["entries"] = sorted(by_file.values(), key=lambda e: e["file"])
    wj(MANIFEST, man)
    print(f"recolored {len(done)} textures; backups in {bdir.relative_to(P) if done else '-'}")
    for r in done:
        print("  ", r)


def revert(selector):
    man = load_manifest()
    keep, restored = [], []
    for e in man["entries"]:
        block, _, state = e["pool"].partition(":")
        if not matches(selector, block, state):
            keep.append(e)
            continue
        path, backup = A / e["file"], P / e["backup"]
        if sha1(path) != e["sha1_after"]:
            print(f"  ! {e['file']} changed after recolor; restoring the backup anyway")
        shutil.copy2(backup, path)
        if sha1(path) != e["sha1_before"]:
            print(f"  ! {e['file']} backup does not match sha1_before")
        restored.append(e["file"])
    man["entries"] = keep
    wj(MANIFEST, man)
    print(f"restored {len(restored)} textures")
    for r in restored:
        print("  ", r)


def record(pool, ref_name, backup_dir):
    man = load_manifest()
    by_file = {e["file"]: e for e in man["entries"]}
    block, _, state = pool.partition(":")
    bdir = (P / backup_dir).resolve()
    ref = next(Path(p) for p in (A / "textures/block").rglob(f"{ref_name}.png"))
    ref_ref = "pysift:" + ref.relative_to(A / "textures").with_suffix("").as_posix()
    for b in sorted(bdir.glob("*.png")):
        cur = next((A / "textures/block").rglob(b.name))
        rel = cur.relative_to(A).as_posix()
        by_file[rel] = {"file": rel, "pool": pool, "reference": ref_ref, "mode": "palette",
                        "sha1_before": sha1(b), "sha1_after": sha1(cur), "backup": b.relative_to(P).as_posix(),
                        "date": "recorded " + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}
        print("recorded", rel)
    man["entries"] = sorted(by_file.values(), key=lambda e: e["file"])
    wj(MANIFEST, man)


cmd = sys.argv[2] if len(sys.argv) > 2 else "scan"
if cmd == "scan":
    scan()
elif cmd == "apply":
    apply(sys.argv[3:])
elif cmd == "revert":
    revert(sys.argv[3])
elif cmd == "record":
    record(sys.argv[3], sys.argv[4], sys.argv[5])
else:
    sys.exit(__doc__)
