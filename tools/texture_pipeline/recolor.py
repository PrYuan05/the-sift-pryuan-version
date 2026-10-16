"""Unify the colour tone of incoherent random pools / stages by remapping textures onto a reference palette.

  python -I tools/texture_pipeline/recolor.py <project> scan [--threshold N]
      read-only: find pools whose palette distance > N (default COHERENCE_TH), pick a reference (medoid unless overridden),
      preview the remap -> build/texture_pipeline/out/recolor_plan.json + recolor_review.png
  python -I tools/texture_pipeline/recolor.py <project> plan [--mode tone] <label> <reference-name> <target> ...
      hand-made plan for textures outside one pool (writes recolor_plan.json + review, read-only for PNGs).
      With --mode tone a target may carry options:  name[:from=<face>][:cap=<tex>+<tex>][:stone=<tex>+..][:keep_hue=300-40]
        from=      take the colour statistics from that texture (the plain stone face of the same block)
        cap=       pixels nearer to these textures' colours than to the stone palette are left untouched
        stone=     stone palette for the cap test (default: from=, else the reference)
        keep_hue=  also leave saturated pixels inside this HSV hue range untouched (e.g. red drips)
        match_l    also move the mean lightness onto the reference (pattern kept)
  python -I tools/texture_pipeline/recolor.py <project> copy <label> <source-name> <new-texture-ref>
      copy a texture into a new file (e.g. to merge a block's texture into another block); logged as generated
  python -I tools/texture_pipeline/recolor.py <project> apply [block[:state] ...]
      apply recolor_plan.json (optionally only the listed pools); backs up to .texture_backups/, logs the manifest
  python -I tools/texture_pipeline/recolor.py <project> revert <block[:state]|all>
      restore files from their backups and drop them from the manifest
  python -I tools/texture_pipeline/recolor.py <project> record <block:state> <reference-texture-name> <backup-dir>
      log a recolor that was done before this tool existed

User decisions live in recolor_overrides.json (exclude pools, pick references, skip targets, allow shared textures).
Mode "palette": stretch the source brightness range onto the reference's and take the reference colour with the
nearest brightness; transparent pixels are kept. Mode "tone": keep every pixel's lightness and move only hue and
saturation (Lab a*/b* mean and spread) onto the reference; optional masks protect caps and accents.
Shapes never change, only colours."""
import sys, json, shutil, datetime
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette_lib import (project_paths, lj, wj, entries, res_path, sha1, Tex, pdist, palette, COHERENCE_TH, remap, tone_transfer, cap_mask,
                         iter_pools, cube_all_texture)

P, RES, A, D = project_paths(sys.argv[1])
ASSETS = RES / "assets"
HERE = Path(__file__).resolve().parent
OUT = P / "build/texture_pipeline/out"
MANIFEST = HERE / "recolor_manifest.json"
OVERRIDES = HERE / "recolor_overrides.json"
PLAN = OUT / "recolor_plan.json"


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


def scan(threshold=COHERENCE_TH):
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
        if worst <= threshold:
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
        load = lambda r: Image.open(res_path(ASSETS, r, "textures", ".png"))
        img.paste(ref.image.resize((tile, tile), Image.Resampling.NEAREST), (x, y))
        dr.text((x, y + tile + 2), "* " + ref.name.rsplit("_", 1)[1], fill=(120, 230, 140))
        x += tile + PAD * 3
        for t in p["targets"]:
            src = tex(t["texture"])
            for img_, label in ((src.image, t["name"].rsplit("_", 1)[1]), (render(src.image, ref.image, p, t, load).convert("RGB"), "after")):
                img.paste(img_.resize((tile, tile), Image.Resampling.NEAREST), (x, y))
                if t["skip"]:
                    dr.rectangle([x, y, x + tile - 1, y + tile - 1], outline=(230, 60, 60), width=3)
                dr.text((x, y + tile + 2), label, fill=(220, 220, 220))
                x += tile + PAD
            x += PAD * 2
        y += tile + 34
    img.save(OUT / "recolor_review.png")


def _colours(refs, load):
    out = set()
    for r in refs:
        out.update(c for c in load(r).convert("RGBA").get_flattened_data() if c[3] > 0)
    return out


def render(src_img, ref_img, p, t, load):
    """Recoloured image for one target. load(ref) must return the ORIGINAL image of a texture (apply snapshots
    every input first, so a side's from= face is read before that face itself is rewritten)."""
    if p.get("mode") != "tone":
        return remap(src_img, ref_img)
    spec = t.get("spec") or {}
    stats = load(spec["from"]) if spec.get("from") else None
    mask = None
    if spec.get("cap") or spec.get("keep_hue"):
        stone = spec.get("stone") or ([spec["from"]] if spec.get("from") else [p["reference"]])
        mask = cap_mask(_colours(stone, load), _colours(spec.get("cap", []), load),
                        tuple(spec["keep_hue"]) if spec.get("keep_hue") else None)
    return tone_transfer(src_img, ref_img, mask, stats, bool(spec.get("match_l")))


def manual_plan(label, ref_name, target_names):
    """Hand-made plan: recolour the named textures onto the reference's palette (used when the textures are not
    in one pool, e.g. the side of a composite block that should match its source block)."""
    def find(name):
        p = next((A / "textures/block").rglob(f"{name}.png"))
        return "pysift:" + p.relative_to(A / "textures").with_suffix("").as_posix()
    usage = texture_usage()
    ref = Tex(find(ref_name), ASSETS)
    load = lambda r: Image.open(res_path(ASSETS, r, "textures", ".png"))
    p = {"pool": label, "block": label.partition(":")[0], "state": label.partition(":")[2], "max_dist": None,
         "mode": MODE, "reference": ref.ref, "reference_auto": False, "targets": []}
    for n in target_names:
        name, *opts = n.split(":")
        spec = {}
        for o in opts:
            k, _, v = o.partition("=")
            if k == "from":
                spec["from"] = find(v)
            elif k in ("cap", "stone"):
                spec[k] = [find(x) for x in v.split("+")]
            elif k == "match_l":
                spec["match_l"] = True
            elif k == "keep_hue":
                spec["keep_hue"] = [float(x) for x in v.split("-")]
            else:
                sys.exit(f"unknown target option {k!r} in {n}")
        t = Tex(find(name), ASSETS)
        entry = {"texture": t.ref, "name": t.name, "skip": None, "spec": spec,
                 "shared_with": sorted({f"{b}[{s or '-'}] {f}" for b, s, m, f in usage.get(t.ref, ())}),
                 "dist_before": round(pdist(t.pal, ref.pal), 1)}
        after = render(t.image, ref.image, p, entry, load)
        entry["dist_after"] = round(pdist(palette(list(after.convert("RGB").get_flattened_data())), ref.pal), 1)
        before_px = list(t.image.convert("RGB").get_flattened_data())
        entry["changed"] = round(sum(x != y for x, y in zip(before_px, after.convert("RGB").get_flattened_data())) / len(before_px), 2)
        p["targets"].append(entry)
    targets = p["targets"]
    plan = [p]
    OUT.mkdir(parents=True, exist_ok=True)
    wj(PLAN, {"generated": datetime.datetime.now().isoformat(timespec="seconds"), "pools": plan})
    cache = {}
    review(plan, lambda r: cache.setdefault(r, Tex(r, ASSETS)))
    for t in targets:
        print(f"{t['name']}: {t['dist_before']} -> {t['dist_after']}  changed {t['changed']:.0%}  used by {t['shared_with']}")


def copy_texture(label, src_name, new_ref):
    """Copy a texture into a new file; the manifest logs it as generated (revert deletes it again)."""
    src = next((A / "textures/block").rglob(f"{src_name}.png"))
    dst = res_path(ASSETS, new_ref, "textures", ".png")
    if dst.exists():
        sys.exit(f"{dst.relative_to(A)} already exists")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    man = load_manifest()
    rel = dst.relative_to(A).as_posix()
    src_ref = "pysift:" + src.relative_to(A / "textures").with_suffix("").as_posix()
    man["entries"] = sorted([e for e in man["entries"] if e["file"] != rel] + [{
        "file": rel, "pool": label, "reference": src_ref, "source": src_ref, "mode": "generated",
        "method": "merged_from", "sha1_before": None, "sha1_after": sha1(dst), "backup": None,
        "date": datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}], key=lambda e: e["file"])
    wj(MANIFEST, man)
    print("copied", src.relative_to(A).as_posix(), "->", rel)


def apply(selectors):
    plan = lj(PLAN)["pools"]
    man = load_manifest()
    by_file = {e["file"]: e for e in man["entries"]}
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bdir = P / ".texture_backups" / f"{stamp}_recolor"
    done = []
    originals = {}

    def load(r):
        if r not in originals:
            originals[r] = Image.open(res_path(ASSETS, r, "textures", ".png")).copy()
        return originals[r]
    jobs = []
    for p in plan:
        if selectors and not any(matches(s, p["block"], p["state"]) for s in selectors):
            continue
        ref_img = load(p["reference"])
        for t in p["targets"]:
            if t["skip"]:
                continue
            spec = t.get("spec") or {}
            for r in [t["texture"]] + ([spec["from"]] if spec.get("from") else []) + spec.get("cap", []) + spec.get("stone", []):
                load(r)
            jobs.append((p, t, ref_img))
    for p, t, ref_img in jobs:          # every input was snapshotted above, so the writing order does not matter
        path = res_path(ASSETS, t["texture"], "textures", ".png")
        rel = path.relative_to(A).as_posix()
        backup = bdir / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        before = sha1(path)
        render(load(t["texture"]), ref_img, p, t, load).save(path)
        prev = by_file.get(rel)
        has_backup = bool(prev and prev.get("backup"))
        entry = {"file": rel, "pool": p["pool"], "reference": p["reference"], "mode": p["mode"],
                 "sha1_before": prev["sha1_before"] if has_backup else before, "sha1_after": sha1(path),
                 "backup": prev["backup"] if has_backup else backup.relative_to(P).as_posix(),
                 "date": stamp}
        if prev and (prev.get("mode") == "generated" or prev.get("previous")):
            # a generated file (building set / generated face) keeps its creation record; revert puts it back
            entry["previous"] = prev.get("previous") or prev
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
        path = A / e["file"]
        if e.get("mode") == "generated":
            if path.exists():
                path.unlink()
            rules = lj(HERE / "face_rules.json")
            blk, _, face = e["pool"].partition(":")
            rules.get("generated_faces", {}).get(blk, {}).pop(face, None)
            wj(HERE / "face_rules.json", rules)
            restored.append(e["file"] + " (deleted; run refit_faces.py to re-pick the face)")
            continue
        if not e.get("backup"):
            print(f"  ! {e['file']} has no backup; left as is")
            keep.append(e)
            continue
        backup = P / e["backup"]
        if sha1(path) != e["sha1_after"]:
            print(f"  ! {e['file']} changed after recolor; restoring the backup anyway")
        shutil.copy2(backup, path)
        if sha1(path) != e["sha1_before"]:
            print(f"  ! {e['file']} backup does not match sha1_before")
        restored.append(e["file"])
        if e.get("previous"):
            keep.append(e["previous"])
    man["entries"] = sorted(keep, key=lambda e: e["file"])
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


MODE = "palette"
if "--mode" in sys.argv:
    MODE = sys.argv[sys.argv.index("--mode") + 1]
    del sys.argv[sys.argv.index("--mode"):sys.argv.index("--mode") + 2]
cmd = sys.argv[2] if len(sys.argv) > 2 else "scan"
if cmd == "scan":
    scan(float(sys.argv[sys.argv.index("--threshold") + 1]) if "--threshold" in sys.argv else COHERENCE_TH)
elif cmd == "plan":
    manual_plan(sys.argv[3], sys.argv[4], sys.argv[5:])
elif cmd == "copy":
    copy_texture(sys.argv[3], sys.argv[4], sys.argv[5])
elif cmd == "apply":
    apply(sys.argv[3:])
elif cmd == "revert":
    revert(sys.argv[3])
elif cmd == "record":
    record(sys.argv[3], sys.argv[4], sys.argv[5])
else:
    sys.exit(__doc__)
